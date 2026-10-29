# CSS314 — Parallel Computing Lab Practicum

**Student ID:** 230103369  
**Eight-Digit Salting ID:** 30103369  
**Hardware:** MacBook Air, Apple M2  
**Operating System:** macOS 26.6.2  
**Programming Language:** Python  
**Repository:** https://github.com/230103369-bit/CSS314-2910-230103369

## Project Overview

This project investigates fundamental parallel computing concepts through practical experiments on real hardware.

The practicum consists of five milestones:

- **M0:** Hardware Profiling and Deterministic Salting
- **M1:** Memory Locality, Stride Access, and Loop Interchange
- **M2:** False Sharing and Karp–Flatt Analysis
- **M3:** Strong Scaling, Weak Scaling, and Roofline Analysis
- **M4:** Final Verification and Submission

All experimental results were collected on an Apple M2 MacBook Air. The project includes source code, measured results, automated verification, and hardware evidence.

---

## Milestone 0 — Hardware Profiling and Deterministic Salting

### Hardware Information

The experiments were performed on a MacBook Air equipped with an Apple M2 processor.

| Component | Value |
|---|---|
| CPU | Apple M2 |
| Architecture | ARM64 |
| Physical CPU cores | 8 (4 performance + 4 efficiency) |
| Logical CPU threads | 8 |
| Simultaneous multithreading | Disabled |
| Cache line size | 128 bytes |
| Reported L1 Data Cache | 65,536 bytes |
| Reported L2 Cache | 4,194,304 bytes |
| Operating system | macOS 26.6.2 |
| Python version | 3.14.7 |

Hardware information was collected from the operating system and saved in `results/host_profile.json`.

### Deterministic Salting

Experiment parameters were generated using SHA-256 hashing of the assigned eight-digit student identifier.

**Parameters:**

- Full student ID: `230103369`
- Eight-digit salting ID: `30103369`
- Salted matrix dimension: `N = 1344`
- Random seed: `76440`
- Buffer size: `16,777,216` elements

The matrix dimension was calculated using:

```python
import hashlib

sid = "30103369"
h = int(hashlib.sha256(sid.encode()).hexdigest()[:8], 16)
N = 1024 + (h % 9) * 64
```

**Verified result:** `N = 1344`

The parameters are stored in `results/salted_params.json`.

### Cache Line Size — Instructor-Approved Hardware Exception

The instructor-provided `verify_outputs.py` expects a cache line size of exactly 64 bytes.

However, the Apple M2 MacBook Air used for this practicum reports a cache line size of **128 bytes**.

This was confirmed using:

```bash
sysctl hw.cachelinesize
```

Output:

```text
hw.cachelinesize: 128
```

The actual hardware-reported value was preserved in `results/host_profile.json`. It was not replaced with an incorrect value merely to satisfy the verifier.

The instructor approved submitting screenshot evidence documenting this hardware-specific difference.

**Screenshot:** `evidence/m0_cacheline_128.png`

### M0 Deliverables

- `src/profile_env.py` — Hardware profiling
- `src/salt.py` — Deterministic parameter generation
- `results/host_profile.json` — Hardware information
- `results/salted_params.json` — Salted parameters
- `evidence/m0_cacheline_128.png` — Hardware evidence

**Verification:** SHA-256 salting passed. The cache line value was independently checked against the operating system.

---

## Milestone 1 — Memory Locality and Loop Interchange

### Objective

Investigate the effect of memory access patterns on performance and demonstrate how loop interchange can improve cache locality.

Two experiments were conducted:

1. Memory stride benchmarking
2. Matrix multiplication loop interchange

### Experiment 1 — Memory Stride Benchmark

Memory access performance was measured using different stride lengths.

Sequential access generally benefits from spatial locality, whereas larger strides can reduce cache efficiency.

Selected measured results:

| Stride | Latency (ns/element) |
|---|---:|
| 1 | 0.909 |
| 8 | 1.029 |
| 16 | 2.827 |

Stride-8 access was approximately **1.13 times slower** per element than stride-1 access.

Stride-16 access showed a more substantial latency increase.

These measurements demonstrate the impact of memory access patterns on effective performance.

### Experiment 2 — Loop Interchange

Two matrix multiplication loop orders were compared:

- Naive loop ordering
- Interchanged `i-k-j` loop ordering

Measured results:

| Implementation | Execution Time |
|---|---:|
| Naive | 0.2575 s |
| Interchanged `i-k-j` | 0.0433 s |

**Speedup:**

\[
S = \frac{0.2575}{0.0433} \approx 5.95
\]

The interchanged implementation achieved approximately **5.95× speedup**.

The numerical correctness check reported zero error.

### Interpretation

Loop interchange improves the order in which matrix elements are accessed.

By using a more cache-friendly traversal pattern, the implementation reduces inefficient memory access and improves execution time.

### M1 Deliverables

- `src/dense_kernel.py`
- `src/stride_bench.py`
- `results/loop_interchange.json`
- `results/stride_results.tsv`

**Official verifier results:**

- PASS — Stride cliff reproduced
- PASS — Loop interchange speedup verified

---

## Milestone 2 — False Sharing and Karp–Flatt Analysis

### Objective

Investigate the performance impact of false sharing and use the Karp–Flatt metric to analyze parallel overhead.

### False Sharing

False sharing occurs when multiple workers modify different variables located within the same cache line.

Although the variables are logically independent, cache-coherence activity can introduce additional overhead.

The experiment compared four approaches:

- Unpadded shared counters
- 64-byte padded counters
- 128-byte padded counters
- Privatized counters

The experiment used:

- Worker counts: 1, 2, 4, and 8
- Iterations per worker: 5,000,000

### Karp–Flatt Metric

The Karp–Flatt metric estimates the effective serial fraction and overhead in a parallel execution.

For \(p\) workers and observed speedup \(S(p)\):

\[
e(p) = \frac{1/S(p)-1/p}{1-1/p}
\]

The metric can reveal overhead that is not explained by an idealized scaling model.

### Experimental Results

Selected Karp–Flatt values for the unpadded implementation:

| Workers | Karp–Flatt Metric |
|---|---:|
| 2 | 1.124 |
| 4 | 1.195 |
| 8 | 2.255 |

The metric increased as the worker count increased.

### Interpretation

The growing Karp–Flatt values indicate increasing parallel overhead in the unpadded configuration.

Values greater than 1 can occur when measured parallel execution becomes slower than the single-worker baseline.

This behavior is consistent with severe contention and false-sharing-related overhead.

Padding and privatization were included to compare alternative memory layouts and approaches to reducing shared-state contention.

### M2 Deliverables

- `src/false_sharing.py`
- `results/false_sharing_karp_flatt.tsv`

**Official verifier result:**

PASS — Karp–Flatt correctly diagnosed the increasing false-sharing contention.

---

## Milestone 3 — Strong Scaling, Weak Scaling, and Roofline Analysis

### Objective

Evaluate parallel scalability and analyze computational performance in relation to arithmetic intensity.

Three analyses were performed:

1. Strong scaling
2. Weak scaling
3. Roofline analysis

### Strong Scaling

Strong scaling measures how execution time changes as the number of workers increases while the total problem size remains constant.

Speedup is calculated as:

\[
S(p) = \frac{T(1)}{T(p)}
\]

Measured results:

| Workers | Execution Time (s) | Speedup |
|---|---:|---:|
| 1 | 0.1028 | 1.000 |
| 2 | 0.0939 | 1.095 |
| 4 | 0.1038 | 0.990 |
| 8 | 0.1494 | 0.688 |

### Strong Scaling Interpretation

The two-worker configuration achieved a small performance improvement.

However, increasing the number of workers beyond two did not produce additional speedup.

At eight workers, execution was slower than the single-worker baseline.

This suggests that parallel overhead and resource limitations outweighed the benefits of additional workers for the measured workload.

### Weak Scaling

Weak scaling measures performance while increasing the total workload proportionally with the number of workers.

Measured weak-scaling efficiencies:

| Workers | Efficiency |
|---|---:|
| 1 | 1.000 |
| 2 | 0.865 |
| 4 | 0.657 |
| 8 | 0.320 |

### Weak Scaling Interpretation

Efficiency decreased as the number of workers increased.

The results indicate that the workload did not maintain ideal weak scaling on the tested hardware and implementation.

Possible contributing factors include parallel execution overhead, scheduling costs, and memory-system limitations.

### Roofline Analysis

The Roofline model relates computational performance to arithmetic intensity and hardware limits.

Arithmetic intensity is defined as:

\[
AI = \frac{\text{Floating-point operations}}{\text{Bytes transferred}}
\]

For the analyzed five-point stencil:

\[
AI = \frac{5}{48} \approx 0.10417\ \text{FLOPs/byte}
\]

**Calculated arithmetic intensity:** `0.10416666666666667 FLOPs/byte`

The low arithmetic intensity suggests that memory bandwidth may be a significant performance limitation.

The qualitative classification is **likely memory-bound**.

However, no measured peak memory bandwidth or peak floating-point throughput was used to construct a quantitative Roofline ceiling. Therefore, this classification is an estimate rather than a measured hardware-bound conclusion.

### M3 Deliverables

- `src/scaling_study.py`
- `results/scaling_metrics.tsv`
- `results/roofline_summary.json`

**Official verifier result:**

PASS — Roofline analysis complete.

---

## Milestone 4 — Final Verification

### Objective

Verify the results of the previous milestones and prepare the project for submission.

The instructor-provided verification script is included in the repository:

`verify_outputs.py`

An additional verification script was implemented:

`src/final_verification.py`

The additional script verifies the salted parameters and actual Apple M2 cache line size, then invokes the official verification functions for M1, M2, and M3.

### Verification Results

| Milestone | Result |
|---|---|
| M0 — SHA-256 Salting | PASS |
| M0 — Cache Line Size | Verified: 128 bytes, instructor-approved exception |
| M1 — Stride Benchmark | PASS |
| M1 — Loop Interchange | PASS |
| M2 — False Sharing / Karp–Flatt | PASS |
| M3 — Roofline | PASS |

### Verification Limitation

The original `verify_outputs.py` stops at M0 because it requires `cache_line_bytes == 64`.

The tested Apple M2 reports 128 bytes, and this hardware-specific exception was approved by the instructor for documentation using screenshot evidence.

The official verification functions for M1, M2, and M3 completed successfully when invoked separately.

The supplementary verification script also completed successfully.

**Important:** The official `results/verification_receipt.sig` was not generated because the original verification script did not complete its full execution.

The supplementary verification report is not a substitute for the official receipt.

### M4 Deliverables

- `verify_outputs.py` — Instructor-provided verifier
- `src/final_verification.py` — Supplementary verification
- `results/final_verification_report.json` — Verification summary
- `evidence/m0_cacheline_128.png` — Hardware-specific exception evidence
- `README.md` — Project documentation

---

## Running the Project

### Requirements

- Python 3.10 or newer
- NumPy
- macOS or Linux for the experimental scripts, subject to platform-specific hardware profiling support

The recorded experiments were performed using Python 3.14.7 on macOS.

### Clone the Repository

```bash
git clone https://github.com/230103369-bit/CSS314-2910-230103369.git
cd CSS314-2910-230103369
```

### Install Dependencies

```bash
python3 -m pip install numpy
```

### Run the Experiments

```bash
python3 src/profile_env.py
python3 src/salt.py
python3 src/dense_kernel.py
python3 src/stride_bench.py
python3 src/false_sharing.py
python3 src/scaling_study.py
```

### Run the Official Verifier

```bash
python3 verify_outputs.py
```

On the tested Apple M2, this stops at the 64-byte cache line assertion described above.

### Run the Supplementary Verification

```bash
python3 src/final_verification.py
```

This validates the Apple M2-specific cache line value and invokes the official verification functions for M1–M3.

The supplementary verification report is saved as:

`results/final_verification_report.json`

---

## Repository Structure

```text
CSS314-2910-230103369/
├── README.md
├── verify_outputs.py
├── src/
│   ├── profile_env.py
│   ├── salt.py
│   ├── dense_kernel.py
│   ├── stride_bench.py
│   ├── false_sharing.py
│   ├── scaling_study.py
│   └── final_verification.py
├── results/
│   ├── host_profile.json
│   ├── salted_params.json
│   ├── loop_interchange.json
│   ├── stride_results.tsv
│   ├── false_sharing_karp_flatt.tsv
│   ├── scaling_metrics.tsv
│   ├── roofline_summary.json
│   └── final_verification_report.json
└── evidence/
    └── m0_cacheline_128.png
```

---

## Git Milestone Tags

Each milestone was recorded using a dedicated Git tag.

| Tag | Description |
|---|---|
| `M0-ENV` | Hardware profiling and deterministic salting |
| `M1-LOCALITY` | Memory locality and loop interchange |
| `M2-SHARING` | False sharing and Karp–Flatt analysis |
| `M3-SCALING` | Strong scaling, weak scaling, and Roofline |
| `M4-FINAL` | Final verification and submission |

The final tag points to the completed project, including the README, experiment results, and hardware evidence.

---

## Conclusion

The experiments demonstrate several important parallel computing principles.

Memory access patterns have a significant effect on performance. Loop interchange produced approximately 5.95× speedup by improving data access locality.

False sharing introduced substantial parallel overhead, reflected in the increasing Karp–Flatt metric as the number of workers increased.

Strong and weak scaling experiments demonstrated that increasing the number of workers does not guarantee better performance. Overhead and hardware limitations can reduce or eliminate the benefits of parallel execution.

The Roofline analysis identified low arithmetic intensity in the stencil workload, suggesting potential memory-bandwidth sensitivity.

Overall, the practicum provides experimental evidence of the relationship between memory locality, contention, scalability, and computational performance on Apple M2 hardware.
