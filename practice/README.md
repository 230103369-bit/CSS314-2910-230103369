# Karp–Flatt Practice Lab

Student ID: 230103369
Hardware: Apple M2, 8 logical cores

## Experiment A — Serial Tail

- T1: 3.317 s
- T2: 1.887 s
- T4: 1.218 s
- e(2): 0.1381
- e(4): 0.1563
- e(4)/e(2): 1.1316
- Rubric: PASS

## Experiment B — Lock Contention

Three independent runs were performed using the original
implementation from the assignment.

| Metric | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| T1 (s) | 4.107 | 4.059 | 4.085 |
| T2 (s) | 11.896 | 11.669 | 11.149 |
| T4 (s) | 12.229 | 11.794 | 11.600 |
| e(2) | 4.7937 | 4.7496 | 4.4580 |
| e(4) | 3.6371 | 3.5408 | 3.4524 |

### Rubric Deviation

T4 > T1 in all three runs, demonstrating negative speedup
and significant lock contention.

However, the final rubric expects e(4) >> e(2).
Our measurements consistently show e(4) < e(2).

The original implementation and workload were preserved.
No measurements were modified.

A supplementary single-lock experiment confirmed
the same behavior.


## Experiment C — Privatization Fix

The implementation uses private local counters with
a single final reduction and no shared counter lock.

Three recorded runs:

| Metric | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| T1 (s) | 0.425 | 0.404 | 0.443 |
| T2 (s) | 0.220 | 0.218 | 0.225 |
| T4 (s) | 0.147 | 0.146 | 0.148 |
| e(2) | 0.0369 | 0.0798 | 0.0183 |
| e(4) | 0.1272 | 0.1476 | 0.1127 |
| E4 | 72.37% | 69.30% | 74.73% |

All runs show T4 < T1, confirming improved scalability.

The instructor's E4 > 70% criterion passed in two
of three runs. The expected near-zero e(4) was
not consistently observed.

These variations are documented without changing
the original experiment parameters.

Full results: RESULTS.md
Evidence: evidence/experiment_c.txt
