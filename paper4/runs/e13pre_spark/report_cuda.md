# E13-pre report — spark-9809 — cuda

commit 032752eb9ff602934789d876a38a03797cc6ee4d (dirty False); torch 2.12.1+cu130; K = 828 nodes; grid 11; Setup 0.8 s; load avg before/after (1.6171875, 0.5, 0.3642578125) / (1.244140625, 0.58642578125, 0.40185546875)

| arm | s/update (median) | reps | fixed+checkpoint (s) | RSS peak (MB) | device mem (MB) |
| --- | --- | --- | --- | --- | --- |
| G0 | 0.0762 | 0.0428, 0.0785, 0.0762 | 0.9 | 2366 | 2465 |
| G1 | 0.1163 | 0.1178, 0.1163, 0.1102 | 1.6 | 2373 | 3567 |

A1 hours on this device (150 fits per arm, U updates + 11 checkpoints): U=1000: G0 3.6, G1 5.6; U=5000: G0 16.3, G1 25.0; U=10000: G0 32.1, G1 49.2

London files equal to Madrid files: **False** (must be False).
