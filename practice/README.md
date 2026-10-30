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

Pending.
