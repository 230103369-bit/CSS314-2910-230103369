# CSS314 — Parallel Computing Lab Practicum

**Student ID:** 230103369  
**Salted Student ID:** 30103369  
**Hardware:** MacBook Air, Apple M2  
**Operating System:** macOS 26.6.2

## Milestone 0 — Hardware Profiling and Deterministic Salting

### Hardware Information

The experiments were performed on a MacBook Air equipped with an Apple M2 processor.

- Physical CPU cores: 8 (4 performance + 4 efficiency cores)
- Logical CPU threads: 8
- Cache line size: 128 bytes
- L1 Data Cache: 65,536 bytes
- L2 Cache: 4,194,304 bytes

The hardware information was collected directly from the operating system.

### Deterministic Salting

The experiment parameters were generated using SHA-256 hashing and the assigned student identifier.

- Student ID: 230103369
- Eight-digit salting ID: 30103369
- Salted matrix dimension (N): 1344
- Random seed: 76440
- Buffer size: 16,777,216 elements

The generated parameters are stored in `results/salted_params.json`.

### Cache Line Size — Hardware-Specific Exception

The provided `verify_outputs.py` script expects a cache line size of exactly 64 bytes.

However, my Apple M2 MacBook Air reports a cache line size of **128 bytes**, confirmed using the following terminal command:

`sysctl hw.cachelinesize`

Output:

`hw.cachelinesize: 128`

Therefore, the actual hardware-reported value of 128 bytes has been preserved in `results/host_profile.json` rather than replacing it with 64 bytes.

The instructor has approved submitting a screenshot as evidence of this hardware-specific difference.

**Screenshot:** `evidence/m0_cacheline_128.png`

### Milestone 0 Deliverables

- `src/profile_env.py` — Hardware profiling implementation
- `src/salt.py` — Deterministic SHA-256 parameter generation
- `results/host_profile.json` — Hardware profile
- `results/salted_params.json` — Salted experiment parameters
- `evidence/m0_cacheline_128.png` — Cache line size confirmation
