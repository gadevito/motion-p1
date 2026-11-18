# E13-pre report — MacBook-Pro-di-gabriele-2.local — mps

commit 032752eb9ff602934789d876a38a03797cc6ee4d (dirty False); torch 2.12.1; K = 828 nodes; grid 11; Setup 0.5 s; load avg before/after (2.994140625, 3.37255859375, 3.30322265625) / (3.7451171875, 3.74951171875, 3.4638671875)

| arm | s/update (median) | reps | fixed+checkpoint (s) | RSS peak (MB) | device mem (MB) |
| --- | --- | --- | --- | --- | --- |
| G0 | 0.0616 | 0.0557, 0.0636, 0.0616 | 0.8 | 1307 | 232 |
| G1 | 0.1305 | 0.1503, 0.1305, 0.1303 | 2.0 | 1388 | 232 |

A1 hours on this device (150 fits per arm, U updates + 11 checkpoints): U=1000: G0 2.9, G1 6.4; U=5000: G0 13.2, G1 28.1; U=10000: G0 26.0, G1 55.3

London files equal to Madrid files: **False** (must be False).
