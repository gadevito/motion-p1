#!/usr/bin/env python3
"""
E11 — diagnostic pilot (internal review, 2026-11-06 16:45). Validation only, no test metric.
==============================================================================================
Madrid comp_q5050, seed 0, 7x7 grid, 8,000 updates, validation every 250 updates (33 points). Variants:

    D0      G0 and G1 as in the pilot (reference)
    D1      G0 and G1 without max_speed (no static attribute)
    D2      G1 with the validation-hidden nodes in input, never in the loss (as written by the review)
    D2-bis  G1 with the validation-hidden nodes in the loss, never in input (the deliverable's condition)
    D3      G0 and G1 with lr 1e-4
    D4      G0 and G1 without max_speed, dropout 0.3 on the hidden features output by each of the four blocks
            (training only). Declared before launch (review, 2026-11-06 17:00): dropout, not weight decay.
            Adoption rule, fixed before launch: D4 enters the perimeter only if (i) the validation minimum of
            G1 is at least 0.011 below that of D1-G1 (1.0706, `e11_diagnosi.json`), i.e. <= 1.0596, and
            (ii) the curve does not diverge within 2,000 updates: no checkpoint between the minimum and
            update 2,000 exceeds the minimum by more than 1%. Otherwise the perimeter stays that of D1.

Each run also records the mean training loss on the masked observed nodes between checkpoints.
Usage (from the worktree root):  $PY paper4/code/e11_diagnosi.py [--d4]
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
from e11 import PILOT, PREREG, RUNS, adjacency, graph_path  # noqa: E402

VARIANTS = [
    ("D0", "G0", {"static": True}), ("D0", "G1", {"static": True}),
    ("D1", "G0", {"static": False}), ("D1", "G1", {"static": False}),   # as run on 2026-11-06 (default then True)
    ("D2", "G1", {"static": True, "input_extra": "val"}),
    ("D2-bis", "G1", {"static": True, "target_extra": "val"}),
    ("D3", "G0", {"static": True, "lr": 1e-4}), ("D3", "G1", {"static": True, "lr": 1e-4}),
]
D4 = [("D4", "G0", {"static": False, "dropout": 0.3}), ("D4", "G1", {"static": False, "dropout": 0.3})]
D1_G1_MIN = 1.0706


def main():
    only_d4 = "--d4" in sys.argv
    variants = D4 if only_d4 else VARIANTS
    path = RUNS / ("e11_diagnosi_D4.json" if only_d4 else "e11_diagnosi.json")
    if path.exists():
        raise FileExistsError(f"{path} exists")
    city, tag = PILOT
    L = 8000; cks = list(range(0, L + 1, 250))
    out = {"protocol": "protocol/paper4/E11.md", "prereg_fingerprint": p4b.sha256(PREREG, 16),
           "configuration": f"{city} {tag}", "seed": 0, "length": L, "evaluation_every": 250, "runs": []}
    for name, arm, opt in variants:
        su = p4b.Setup(city, graph_path(city, tag), seed=0)
        kw = dict(opt)
        for k in ("input_extra", "target_extra"):
            if kw.get(k) == "val":
                kw[k] = su.val.copy()
        A = adjacency(su, arm)[0]
        o = p4b.train(su, arm, A, U=L, checkpoints=cks, log=lambda m: print(f"{name} {m}", flush=True), **kw)
        t = o["trajectory"]; best = min(t, key=lambda d: d["val_wce"])
        out["runs"].append({"variant": name, "arm": arm, "options": {k: (v if not isinstance(v, np.ndarray) else "validation-hidden")
                                                                     for k, v in opt.items()},
                            "val_min": best["val_wce"], "val_min_update": best["update"],
                            "val_at_8000": t[-1]["val_wce"], "train_loss_at_8000": t[-1]["train_loss"],
                            "seconds": o["seconds"], "trajectory": t})
        print(f"== {name} {arm}: min {best['val_wce']:.4f} at {best['update']}, at 8000 {t[-1]['val_wce']:.4f}, "
              f"train loss at 8000 {t[-1]['train_loss']:.4f}", flush=True)
    if only_d4:
        g1 = next(r for r in out["runs"] if r["arm"] == "G1")
        t = g1["trajectory"]; m, mu = g1["val_min"], g1["val_min_update"]
        window = [d["val_wce"] for d in t if mu <= d["update"] <= 2000]
        cond_i = m <= D1_G1_MIN - 0.011
        cond_ii = bool(window) and max(window) <= 1.01 * m and mu <= 2000
        out["adoption"] = {"G1_min": m, "threshold": round(D1_G1_MIN - 0.011, 4), "improves_by_0.011": cond_i,
                           "no_divergence_within_2000": cond_ii, "adopted": bool(cond_i and cond_ii)}
        print("adoption:", out["adoption"], flush=True)
    c, dirty = p4b.git_commit()
    out.update({"commit": c, "code_dirty": dirty, "written": datetime.now(timezone.utc).isoformat()})
    path.write_text(json.dumps(out, indent=1))
    print(f"diagnostic -> {path} ({p4b.sha256(path, 16)})")


if __name__ == "__main__":
    main()
