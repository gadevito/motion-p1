#!/usr/bin/env python3
"""
Investigation I1 of the second A0.2 failure (E13, dated note of 2026-11-18): does G1 show an advantage over G0 on the
dependent synthetic control (version 2) with a larger training budget? G0 and G1 are trained on the dependent process of
Madrid seed 0, regime I0, configuration C1, for 10 000 updates with a checkpoint every 500, from the same initialisation
stream as `a0-synth` (p4b.K_INIT); nothing else differs from A0.2 (budget and checkpoint frequency only). Criterion, the
one of A0.2: the best checkpoint is the checkpoint >= 500 at which G1's validation wCE is minimal; V(G1) = 100 (wCE_G0 -
wCE_G1)/wCE_G0 is read there. Outcomes fixed before the run (note): 'advantage emerged with the larger budget' if V >= +3 at
the best checkpoint; 'failure still unexplained' otherwise. The whole trajectory of both arms is reported. An advantage is
evidence compatible with an insufficient A0.2 budget, not a demonstration of the cause; its absence does not establish that
the information path is interrupted. No test node, no real target process, no A1 cell; the gate of `e13.py` is not
involved. Writes paper4/runs/e13_a0_invest_I1.json and refuses to run if that file exists. Run from the repository root:
PYTHONPATH=paper4/code python3 paper4/code/e13_a0_invest.py
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import p4b, e9, e13

OUT = Path("paper4/runs/e13_a0_invest_I1.json")
if OUT.exists():
    sys.exit(f"{OUT} exists: the investigation run is recorded once")
CAP, CK = 10_000, 500
out = {"investigation": "I1 (A0.2 budget)", "cap": CAP, "ck_every": CK, "config": "C1", "init_stream": p4b.K_INIT, "generator_version": 2,
       "started": datetime.now(timezone.utc).isoformat(), "arms": {}}
su = e13.SetupE13("madrid", 0, "I0"); z, flow, occ, C = e13.synth_processes(su, "dependent", 20261118); su.inject(z, flow, occ, C)
for arm in e13.ARMS:
    A, _ = e9.adjacency(su, arm)
    o = e13.train_e13(su, arm, A, CAP, e13.CONFIGS["C1"], p4b.K_INIT, ck_every=CK, save_states=False, log=print)
    assert o["hidden_in_batches"] == 0
    out["arms"][arm] = {"trajectory": [{"update": t["update"], "val_wce": t["val_wce"], "train_loss": t["train_loss"]} for t in o["trajectory"]],
                        "seconds": o["seconds"], "init_seed": o["init_seed"]}
g0 = {t["update"]: t["val_wce"] for t in out["arms"]["G0"]["trajectory"]}; g1 = {t["update"]: t["val_wce"] for t in out["arms"]["G1"]["trajectory"]}
V = {u: 100 * (g0[u] - g1[u]) / g0[u] for u in sorted(g0) if u >= 500}
best = min((u for u in g1 if u >= 500), key=lambda u: (g1[u], u))                    # A0.2 best-checkpoint rule
out["V_by_checkpoint"] = V; out["best_checkpoint_G1"] = best; out["V_at_best"] = V[best]
out["outcome"] = "advantage emerged with the larger budget" if V[best] >= 3 else "failure still unexplained"
out["written"] = datetime.now(timezone.utc).isoformat(); out["environment"] = e13.environment(); c, dirty = p4b.git_commit(); out["commit"] = c; out["code_dirty"] = dirty
OUT.write_text(json.dumps(out, indent=1))
print("V(G1) by checkpoint:", {u: round(v, 2) for u, v in V.items()})
print("best checkpoint of G1:", best, "V at best:", round(V[best], 2), "| outcome:", out["outcome"], "->", OUT, p4b.sha256(OUT, 16))
