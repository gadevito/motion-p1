#!/usr/bin/env python3
"""
E13-pre — microbenchmark of training cost (`protocol/paper4/E13pre.md`). Cost only: no test metric.
===================================================================================================
Uses `p4b.py` and `e9.py` unchanged. For G0 and G1 on Madrid, f = 0.20, seed 0: time of `Setup`,
time of one checkpoint, and seconds per update as (t(60 updates) - t(10 updates)) / 50, three
repetitions; peak RSS and device memory, reported separately. Records environment, commit, load
averages and data fingerprints (Madrid files, and the London files named in e9.py, which must differ).
The validation values that the pipeline computes at its checkpoints are NOT read nor written here.

Usage (from the worktree root, no other heavy process running):
    $PY paper4/code/e13pre.py --device mps --out paper4/runs/e13pre_<host>
    $PY paper4/code/e13pre.py --device cuda --out paper4/runs/e13pre_<host>
    $PY paper4/code/e13pre.py --device cpu --out paper4/runs/e13pre_<host>
"""
import argparse, json, os, platform, resource, statistics, sys, time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9   # noqa: E402  (registers London in p4b.CITY, provides setup/adjacency)

CITY, F, SEED = "madrid", 0.20, 0
U_SHORT, U_LONG, REPS = 10, 60, 3


def rss_mb():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / (1024 * 1024) if platform.system() == "Darwin" else r / 1024


def dev_mem_mb(dev):
    if dev.type == "cuda":
        return torch.cuda.max_memory_allocated() / 2 ** 20
    if dev.type == "mps":
        return torch.mps.current_allocated_memory() / 2 ** 20
    return None


def sync(dev):
    if dev.type == "cuda": torch.cuda.synchronize()
    elif dev.type == "mps": torch.mps.synchronize()


def load_avg():
    try: return os.getloadavg()
    except OSError: return None


def fingerprints():
    out = {}
    for city in ("madrid", "london"):
        for k, p in p4b.CITY[city].items():
            p = Path(p); out[f"{city}:{k}"] = {"path": str(p), "exists": p.exists(),
                                               "sha256_16": p4b.sha256(p, 16) if p.exists() else None}
    same = any(out[f"madrid:{k}"]["sha256_16"] == out[f"london:{k}"]["sha256_16"] and out[f"london:{k}"]["exists"]
               for k in p4b.CITY["madrid"])
    return out, same


def timed_train(su, arm, A, U, dev):
    sync(dev); t0 = time.perf_counter()
    res = p4b.train(su, arm, A, U, checkpoints=[U], log=None)   # one checkpoint at the end, as a fixed cost
    sync(dev); t = time.perf_counter() - t0
    del res
    return t


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--device", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    dev = torch.device(a.device)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    commit, dirty = p4b.git_commit()
    rep = {"protocol": "E13pre", "started_utc": datetime.now(timezone.utc).isoformat(), "host": platform.node(),
           "platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0],
           "torch": torch.__version__, "numpy": np.__version__, "device": a.device,
           "mps_available": torch.backends.mps.is_available(), "cuda_available": torch.cuda.is_available(),
           "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "commit": commit, "code_dirty": dirty, "load_avg_before": load_avg(),
           "code_sha_16": {"p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e9.py": p4b.sha256(Path(e9.__file__), 16),
                           "e13pre.py": p4b.sha256(Path(__file__), 16)},
           "city": CITY, "f": F, "seed": SEED, "batch": 32, "u_short": U_SHORT, "u_long": U_LONG, "reps": REPS}
    rep["data_fingerprints"], rep["london_equals_madrid"] = fingerprints()

    t0 = time.perf_counter()
    su = e9.setup(CITY, F, SEED)
    su.dev = dev                                              # device of the campaign on this machine
    su._tensors()                                             # rebuild tensors on the chosen device
    rep["setup_seconds"] = time.perf_counter() - t0
    rep["nodes_kept_K"] = int(su.K); rep["n_observed"] = int(su.obs.sum()); rep["n_val"] = int(su.val.sum())
    rep["n_test"] = int(su.test.sum()); rep["train_origins"] = int(len(su.tr)); rep["grid"] = int(su.G)

    rep["arms"] = {}
    for arm in ("G0", "G1"):
        A, _ = e9.adjacency(su, arm)
        if dev.type == "cuda": torch.cuda.reset_peak_memory_stats()
        per_update, t_short, t_long = [], [], []
        for r in range(REPS):
            ts = timed_train(su, arm, A, U_SHORT, dev); tl = timed_train(su, arm, A, U_LONG, dev)
            t_short.append(ts); t_long.append(tl); per_update.append((tl - ts) / (U_LONG - U_SHORT))
        rep["arms"][arm] = {"seconds_per_update_median": statistics.median(per_update),
                            "seconds_per_update_all": per_update, "t_short_all": t_short, "t_long_all": t_long,
                            "checkpoint_plus_fixed_seconds_est": statistics.median(t_short) - U_SHORT * statistics.median(per_update),
                            "rss_peak_mb_so_far": rss_mb(), "device_mem_mb": dev_mem_mb(dev)}
        print(f"[{arm}] {a.device}: {statistics.median(per_update):.4f} s/update (reps {', '.join(f'{x:.4f}' for x in per_update)})", flush=True)

    rep["load_avg_after"] = load_avg(); rep["finished_utc"] = datetime.now(timezone.utc).isoformat()
    for U in (1000, 5000, 10000):
        rep[f"A1_hours_on_this_device_U{U}"] = {arm: round(300 / 4 * 2 * (U * v["seconds_per_update_median"] + 11 * v["checkpoint_plus_fixed_seconds_est"]) / 3600, 1)
                                                for arm, v in rep["arms"].items()}   # 300 fits = 150 per arm family (G0 vs G1), each U updates + 11 checkpoints
    (out / f"report_{a.device}.json").write_text(json.dumps(rep, indent=1))
    md = [f"# E13-pre report — {rep['host']} — {a.device}", "",
          f"commit {commit} (dirty {dirty}); torch {rep['torch']}; K = {rep['nodes_kept_K']} nodes; grid {rep['grid']}; Setup {rep['setup_seconds']:.1f} s; load avg before/after {rep['load_avg_before']} / {rep['load_avg_after']}", "",
          "| arm | s/update (median) | reps | fixed+checkpoint (s) | RSS peak (MB) | device mem (MB) |", "| --- | --- | --- | --- | --- | --- |"]
    for arm, v in rep["arms"].items():
        md.append(f"| {arm} | {v['seconds_per_update_median']:.4f} | {', '.join(f'{x:.4f}' for x in v['seconds_per_update_all'])} | {v['checkpoint_plus_fixed_seconds_est']:.1f} | {v['rss_peak_mb_so_far']:.0f} | {v['device_mem_mb'] if v['device_mem_mb'] is None else round(v['device_mem_mb'])} |")
    md += ["", "A1 hours on this device (150 fits per arm, U updates + 11 checkpoints): " +
           "; ".join(f"U={U}: " + ", ".join(f"{k} {h}" for k, h in rep[f'A1_hours_on_this_device_U{U}'].items()) for U in (1000, 5000, 10000)),
           "", f"London files equal to Madrid files: **{rep['london_equals_madrid']}** (must be False)."]
    (out / f"report_{a.device}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
