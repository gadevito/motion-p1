#!/usr/bin/env python3
"""
E9 — isolated cost of one arm (internal review, 2026-11-07): Madrid, f = 40%, seed 0, 1,000 updates, 11
checkpoints, one process. Records `uptime` and the five heaviest processes before and after. Validation only;
imports `p4b.py` and `e9.py` unchanged.

Usage: $PY paper4/code/e9_costo_braccio.py --arm "G1-rand(deg)"     (writes paper4/runs/e9_costo_<arm>.json)
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9  # noqa: E402


def state():
    up = subprocess.check_output(["uptime"], text=True).strip()
    top = subprocess.check_output("ps -axo %cpu,comm | sort -nr | head -5", shell=True, text=True).strip().splitlines()
    return {"uptime": up, "top": [ln.strip()[:100] for ln in top]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", required=True, choices=e9.ARMS); a = ap.parse_args()
    tag = a.arm.replace("(", "_").replace(")", "")
    path = e9.RUNS / f"e9_costo_{tag}.json"
    if path.exists():
        raise SystemExit(f"STOP: {path} exists")
    before = state(); print(before["uptime"], flush=True)
    U = 1000; cks = [round(U * i / 11) for i in range(1, 12)]
    su = e9.setup("madrid", 0.4, 0)
    o = p4b.train(su, a.arm, e9.adjacency(su, a.arm)[0], U=U, checkpoints=cks)
    after = state(); print(after["uptime"], flush=True)
    c, dirty = p4b.git_commit()
    out = {"arm": a.arm, "K": su.K, "updates": U, "seconds": round(o["seconds"], 1), "seconds_per_update": o["seconds"] / U,
           "before": before, "after": after, "machine": "Mac M3 Max, MPS, one process", "commit": c, "code_dirty": dirty,
           "written": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(out, indent=1))
    print(f"{a.arm}: {out['seconds']} s -> {path} ({p4b.sha256(path, 16)})")


if __name__ == "__main__":
    main()
