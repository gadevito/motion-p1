# E13-pre report — MacBook-Pro-di-gabriele-2.local — cpu

commit 032752eb9ff602934789d876a38a03797cc6ee4d (dirty False); torch 2.12.1; K = 828 nodes; grid 11; Setup 0.6 s; load avg before/after (3.90869140625, 3.80908203125, 3.50048828125) / (4.7197265625, 4.65625, 4.31298828125)

| arm | s/update (median) | reps | fixed+checkpoint (s) | RSS peak (MB) | device mem (MB) |
| --- | --- | --- | --- | --- | --- |
| G0 | 0.8591 | 0.8486, 0.8591, 0.8951 | 10.2 | 6036 | None |
| G1 | 1.6000 | 1.6000, 1.6053, 1.5872 | 17.3 | 6952 | None |

A1 hours on this device (150 fits per arm, U updates + 11 checkpoints): U=1000: G0 40.5, G1 74.6; U=5000: G0 183.6, G1 341.3; U=10000: G0 362.6, G1 674.6

London files equal to Madrid files: **False** (must be False).
