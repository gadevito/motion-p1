# E13-pre report — spark-9809 — cpu

commit 032752eb9ff602934789d876a38a03797cc6ee4d (dirty False); torch 2.12.1+cu130; K = 828 nodes; grid 11; Setup 0.6 s; load avg before/after (0.81884765625, 0.53857421875, 0.3896484375) / (9.85986328125, 8.74951171875, 4.53759765625)

| arm | s/update (median) | reps | fixed+checkpoint (s) | RSS peak (MB) | device mem (MB) |
| --- | --- | --- | --- | --- | --- |
| G0 | 0.5680 | 0.5445, 0.5727, 0.5680 | 3.8 | 7498 | None |
| G1 | 1.0671 | 1.0671, 1.0673, 1.0656 | 8.7 | 8247 | None |

A1 hours on this device (150 fits per arm, U updates + 11 checkpoints): U=1000: G0 25.4, G1 48.4; U=5000: G0 120.1, G1 226.3; U=10000: G0 238.4, G1 448.6

London files equal to Madrid files: **False** (must be False).
