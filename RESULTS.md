# Karp–Flatt Practice Lab — Results

Student ID: 230103369
Hardware: Apple M2, 8 logical cores
Python: multiprocessing
Branch: practice-230103369

## Summary

| Experiment | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Diagnosis |
|---|---:|---:|---:|---:|---:|---|
| A: Serial Tail | 3.317 | 1.887 | 1.218 | 0.1381 | 0.1563 | Approximately flat e(p); fixed serial delay |
| B: Lock Contention | 4.085 | 11.669 | 11.794 | 4.7131 | 3.5162 | Severe contention and negative speedup |
| C: Privatized State | 0.425 | 0.220 | 0.147 | 0.0353 | 0.1278 | Improved scalability after removing shared state |

## Experiment A

The fixed 0.40-second sequential delay limits scalability.

Measured e(4)/e(2) = 1.1316, within the instructor's
required interval [0.80, 1.25].

Result: PASS.

## Experiment B

The shared counter is protected by a multiprocessing.Lock.
Adding workers introduces severe synchronization overhead.

Three independent runs were recorded. In all runs,
T4 > T1, demonstrating negative speedup.

The instructor's final rubric expects e(4) >> e(2).
However, e(4) < e(2) in all three measured runs.

This deviation was reproduced and documented.
The original workload and implementation were preserved.

A supplementary single-lock variant was also tested,
with the same qualitative result.

Result: Negative speedup confirmed; final Karp-Flatt
growth criterion not met.

## Experiment C

Each worker maintains a private local counter.
Worker results are combined after computation.

Three recorded runs show T4 < T1.

Four-worker efficiencies:
- Run 1: 72.37%
- Run 2: 69.30%
- Run 3: 74.73%

The required E4 > 70% criterion passed in two
of the three recorded runs.

The expected near-zero Karp-Flatt value was not
consistently reproduced. Recorded e(4) values:
0.1272, 0.1476, and 0.1127.

Result: Privatization substantially improves scalability,
but the numerical rubric is not consistently satisfied.

## Evidence

- evidence/experiment_a.txt
- evidence/experiment_b.txt
- evidence/experiment_c.txt

Terminal screenshots are maintained separately
in the evidence directory.

All reported measurements are empirical.
No benchmark results were fabricated or adjusted.
