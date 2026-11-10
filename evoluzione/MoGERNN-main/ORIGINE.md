# MoGERNN (third-party code, not included in this repository)

Source: https://github.com/ZJU-TSELab/MoGERNN (Zhou et al., MoGERNN: An inductive traffic predictor for unobserved locations, Transp. Res. Part C, 2025).
The copy used by the audits is identical to upstream commit e80f6ca5818d80ebdf4e712cd9489b29f9393a33 (38 files; checked on 2026-11-10 on `main.py` f10b657052c8c216a85d1a52f406433aa3ee7705c5ca1e304979fd6f4079cb1a, `model/MoGERNN.py` d9eef73bf1249344b0644a7aec2572f10531553171a67fb125fca326382da2af, `args.py` 684e4d03b225410af1d1df5ed55406047be714097ee70c6524d0c717568fea5d).
The upstream repository declares no licence, so its code is not redistributed here.

The audits in `evoluzione/audit/` (`audit_mogernn_runtime.py`, `benchmark_mogernn.py`, `profila_mogernn.py`) expect the upstream tree unpacked in this folder. Their outputs are the three files of `results/evoluzione/audit_mogernn/`. No number of Paper 1 or Paper 4 is regenerated from this code.

The audit of 2026-09-22 (supplement of Paper 1, section B) used upstream commit 86b153fb of 2025-05-29; commit e80f6ca of 2026-10-29 changes only the README, the code is identical.
