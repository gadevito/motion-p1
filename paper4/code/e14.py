#!/usr/bin/env python3
"""
E14 — C0 controls and C1 of protocol `protocol/paper4/E14.md`: the dedicated model MoGERNN (commit 86b153fb4bf9) adapted to
the E11 perimeter by `mogernn_adapter.py` (`protocol/paper4/rafforzamento/ADAPTER_SPEC_E14.md`, binding), regression task (continuous factor r
at the hidden sites, MAE in factor units at horizons 1, 2, 4, 8), four cell types = regime S0 / S1 (without / with coordinates)
× arm full / nodyn (factor history on / zeroed), f = 0.20, three cities, five splits: 60 cells. `p4b.py`, `e9.py`, `e11.py` and
`e13.py` are imported unchanged.

Structure. (1) Constants of E14; the active grid read from `paper4/runs/e14_grid.json` (the budget decision, committed before
the tag). (2) A DERIVED BLOCK: the functions of e13.py reused by E14 (git helpers, environment, indices, development /
extension / final / campaign / adequacy machinery), copied mechanically with the substitution table SUBST (identifiers E13 ->
E14, file names, the setup / training / adjacency entry points, the tag pattern, the selection metric key val_wce -> val_mae);
`derived_block_matches()` regenerates the block from e13.py and compares it with this file (asserted by the self-test and the
preflight). (3) E14-specific code: SetupE14 (tensors of ADAPTER_SPEC §1, factor scaler, the method's graph with cached random
walks), train_e14 (AdamW, MSE on the target entries, validation MAE, plateau policy of C3), the calendar baseline, the
privileged MAE diagnostic and C0.2 (`c0-synth`), the sensitivity diagnostic C0.5(b), the budget rule (`budget`), the gate,
test, analysis (provisional, replicates saved for the campaign-wide F2 band), C0.5(a) (`struct`), the deterministic preflight
(no model update) and `pre` (E14pre.md: C0.1 and the benchmark on Spark).

Commands: preflight [--mogernn-repo PATH] · struct · pre · budget --h-cal H --by NAME · c0-synth · c0-accept --by --note-commit ·
sensitivity [--origins N] · dev/final --city --seed --arm full|nodyn --regime S0|S1 · extend --city --arm --regime ·
campaign --phase dev|final · adequacy · test · analysis
"""
import argparse
import ast
import copy
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import torch

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")        # deterministic cuBLAS workspace (before any CUDA initialisation)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9   # noqa: E402
import e13  # noqa: E402
import mogernn_adapter as mga  # noqa: E402
from e11 import Log, cadence_ok  # noqa: E402

# ---------------------------------------------------------------- constants of E14 -----------------------
ROOT = p4b.ROOT
RUNS = ROOT / "paper4" / "runs"
E14 = RUNS / "e14"
PREREG = ROOT / "protocol" / "paper4" / "E14.md"
PREPRE = ROOT / "protocol" / "paper4" / "E14pre.md"
SPEC = ROOT / "protocol" / "paper4" / "rafforzamento" / "ADAPTER_SPEC_E14.md"
GRID_FILE = RUNS / "e14_grid.json"
CITIES, SEEDS, F = e13.CITIES, e13.SEEDS, e13.F
ARMS = ("full", "nodyn")            # factor history of the input nodes on / zeroed (every other tensor identical)
REGIMES = ("S0", "S1")              # S0: no coordinates; S1: two standardised UTM channels (ADAPTER_SPEC §0, §3)
CAP0, CAP1 = 12_000, 24_000         # U_max fixed by E14.md (ADAPTER_SPEC §9); extension to 2·U_max
CK_EVERY = 500
TRAIN_DEVICE = "cuda"               # the Spark assignment: every model update refuses another backend (E14pre.md, E14.md)
CONFIGS_FULL = {"C1": dict(lr=1e-3, wd=1e-4, sched=None),          # the original training script's settings (AdamW, no scheduler)
                "C2": dict(lr=3e-4, wd=1e-4, sched=None),
                "C3": dict(lr=1e-3, wd=1e-4, sched="plateau"),     # declared adaptation: ReduceLROnPlateau, policy in train_e14
                "C4": dict(lr=1e-3, wd=0.0, sched=None)}
REDUCED = ("C1", "C2")              # uniform reduction of P4R §8 if the budget rule applies
K_DEV_INIT = e13.K_DEV_INIT         # development initialisation stream 7; the final uses p4b.K_INIT = 6
BOOT_SEED = 20261120
B_REPS, REPRO_TOL = e13.B_REPS, e13.REPRO_TOL
HSTEPS = 8                          # decoder steps t+1 … t+8; the protocol horizons are read among them
HORIZONS, T_IN = p4b.HORIZONS, p4b.T_IN
REF_HOPS = 14                       # declared reference operator Σ_{k≤14}(A_q)^k of C0.2 (not the model's propagation)
RADII = (14, 21)                    # declared radii of the descriptive hop-distance shares (C0.5a)
SYNTH_SEEDS = {"dependent": 20261121, "independent": 20261122}       # C0.2: new realisations, fixed in E14.md, never used before
FITS_PER_TYPE = {"full": 75, "reduced": 45}
MIN_DEFINED_FRAC = 0.95
FROZEN_PATHS = e13.FROZEN_PATHS + ["paper4/code/e14.py", "paper4/code/mogernn_adapter.py", "protocol/paper4/E14.md",
                                   "protocol/paper4/rafforzamento/ADAPTER_SPEC_E14.md", "paper4/runs/e14_grid.json"]


def active_configs():
    """The grid in force: the full grid unless `e14_grid.json` (the budget decision of ADAPTER_SPEC §9, committed before the tag)
    records the reduction to C1 + C2; None when it records a scope to be renegotiated (every launch is then refused by the gate)."""
    if not GRID_FILE.exists():
        return dict(CONFIGS_FULL)
    g = json.loads(GRID_FILE.read_text()).get("grid")
    if g == "full":
        return dict(CONFIGS_FULL)
    if g == "reduced":
        return {k: CONFIGS_FULL[k] for k in REDUCED}
    return None


CONFIGS = active_configs()

# ---------------------------------------------------------------- derivation from e13.py -----------------
DERIVED = ['_git', 'git_describe', 'frozen_tag', 'frozen_unchanged', 'head_commit', 'git_clean', 'git_committed_unchanged', 'environment', '_report_matches_version', 'record13', 'cell_id', 'group_id', 'adequacy_of', '_index', '_append', '_next_attempt', 'latest_dev', 'latest_final', 'extension_status', 'group_cap', 'all_cells', '_dev_run', 'dev', 'extend', 'final', 'final_up_to_date', 'campaign', 'compute_adequacy', 'adequacy', 'per_horizon_mean', '_week_index']
SUBST = [('paper4-E13-*', 'paper4-E14-*'), ('E13.md', 'E14.md'), ('e13_adequacy.json', 'e14_adequacy.json'), ('"e13.py": p4b.sha256(Path(__file__), 16)', '"e13.py": p4b.sha256(Path(e13.__file__), 16), "e14.py": p4b.sha256(Path(__file__), 16), "mogernn_adapter.py": p4b.sha256(Path(mga.__file__), 16)'), ('SetupE13(', 'SetupE14('), ('train_e13(', 'train_e14('), ('e9.adjacency(', 'adjacency_e14('), ('val_wce', 'val_mae'), ('validation wCE', 'validation MAE'), ('(?<![A-Za-z0-9_])E13(?![A-Za-z0-9_])', 'E14')]                  # applied in order; the last entry is a regular expression on the identifier E13
BEGIN_MARK, END_MARK = "# ---- BEGIN DERIVED FROM e13.py ----", "# ---- END DERIVED FROM e13.py ----"


def function_sources(path):
    src = Path(path).read_text(); tree = ast.parse(src); lines = src.splitlines(keepends=True); out = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            out[node.name] = "".join(lines[node.lineno - 1:node.end_lineno])
    return out


def substitute(text):
    for a, b in SUBST[:-1]:
        text = text.replace(a, b)
    return re.sub(SUBST[-1][0], SUBST[-1][1], text)


def derived_block(e13_path=None):
    fs = function_sources(e13_path or e13.__file__)
    return "\n\n".join(substitute(fs[n]).rstrip("\n") for n in DERIVED) + "\n"


def derived_block_matches(e13_path=None):
    me = Path(__file__).read_text()
    block = me.split(BEGIN_MARK + "\n")[1].split(END_MARK)[0]
    return block == derived_block(e13_path)


# ---- BEGIN DERIVED FROM e13.py ----
def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)

def git_describe():
    """Exact tag of HEAD, if any (kept for the records)."""
    return _git("describe", "--tags", "--exact-match").stdout.strip()

def frozen_tag():
    """The E14 tag that froze code and protocol: the nearest `paper4-E14-*` tag reachable from HEAD. HEAD may be
    later than the tag (commits that deposit records), but the frozen files must be identical to the tag."""
    return _git("describe", "--tags", "--abbrev=0", "--match", "paper4-E14-*").stdout.strip()

def frozen_unchanged(tag):
    """Code and protocol identical to the tag (committed content) — the working tree is checked by git_clean()."""
    return bool(tag) and _git("diff", "--quiet", tag, "HEAD", "--", *FROZEN_PATHS).returncode == 0

def head_commit():
    return _git("rev-parse", "--short", "HEAD").stdout.strip()

def git_clean():
    """No modified tracked file and no untracked file (ignored files, e.g. paper4/runs, are not listed)."""
    r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip() == ""

def git_committed_unchanged(path):
    """True if `path` is tracked and identical to HEAD."""
    a = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], capture_output=True, text=True, cwd=ROOT)
    if a.returncode != 0:
        return False
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(path)], capture_output=True, text=True, cwd=ROOT)
    return b.returncode == 0

def environment():
    return {"host": platform.node(), "platform": platform.platform(), "python": sys.version.split()[0], "torch": torch.__version__,
            "numpy": np.__version__, "pandas": pd.__version__, "networkx": nx.__version__,
            "mps": torch.backends.mps.is_available(), "cuda": torch.cuda.is_available(),
            "tag": git_describe(), "frozen_tag": frozen_tag(), "head": head_commit(), "code_sha16": {"p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e9.py": p4b.sha256(Path(e9.__file__), 16),
                                                  "e13.py": p4b.sha256(Path(e13.__file__), 16), "e14.py": p4b.sha256(Path(__file__), 16), "mogernn_adapter.py": p4b.sha256(Path(mga.__file__), 16)},
            "prereg_sha16": p4b.sha256(PREREG, 16) if PREREG.exists() else None, "load_avg": list(os.getloadavg())}

def _report_matches_version(report, tag):
    """A report belongs to this frozen version: same frozen tag, same fingerprints of the code files and of the protocol."""
    env = report.get("environment", {}); mine = environment()
    return env.get("frozen_tag") == tag and env.get("code_sha16") == mine["code_sha16"] and env.get("prereg_sha16") == mine["prereg_sha16"]

def record13(d, payload):
    rec = p4b.record(d, {"environment": environment(), **payload})
    return rec

def cell_id(city, seed, arm, regime):
    return f"{city}_s{seed}_{arm}_{regime}"

def group_id(city, arm, regime):
    return f"{city}_{arm}_{regime}"

def adequacy_of(traj, cap):
    """Minimum not at the cap; improvement between the last two checkpoints ≤ 0.5 % of the validation MAE."""
    v = [t["val_mae"] for t in traj]; u = [t["update"] for t in traj]
    i = int(np.argmin(v)); impr = (v[-2] - v[-1]) / v[-2] if len(v) > 1 else 0.0
    return {"min_update": u[i], "min_at_cap": bool(u[i] == cap), "last_improvement_frac": float(impr),
            "pass": bool(u[i] != cap and impr <= 0.005)}

def _index(name):
    p = E14 / name
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []

def _append(name, row):
    (E14 / name).open("a").write(json.dumps(row) + "\n")

def _next_attempt(cid):
    """Attempt counter per cell, incremented before a folder is created: an interrupted attempt (folder without
    run.json, never indexed) does not block the next one; the E11 rule still blocks an identical (cell, cap, attempt)."""
    p = E14 / "attempts.json"; a = json.loads(p.read_text()) if p.exists() else {}
    a[cid] = a.get(cid, 0) + 1; p.write_text(json.dumps(a, indent=1, sort_keys=True)); return a[cid]

def latest_dev(cid, usable_only=True):
    rows = [r for r in _index("index_dev.jsonl") if r["cell"] == cid and (r.get("usable", True) or not usable_only)]
    if not rows:
        return None
    return json.loads((Path(rows[-1]["dir"]) / "run.json").read_text()) | {"dir": rows[-1]["dir"], "usable": rows[-1].get("usable", True)}

def latest_final(cid):
    rows = [r for r in _index("index_final.jsonl") if r["cell"] == cid]
    if not rows:
        return None
    return json.loads((Path(rows[-1]["dir"]) / "run.json").read_text()) | {"dir": rows[-1]["dir"]}

def extension_status(gid):
    p = E14 / f"extension_{gid}.json"
    return json.loads(p.read_text()) if p.exists() else None

def group_cap(city, arm, regime):
    st = extension_status(group_id(city, arm, regime))
    return CAP1 if st else CAP0

def all_cells():
    return [(c, s, a, r) for c in CITIES for s in SEEDS for a in ARMS for r in REGIMES]

def _dev_run(city, seed, arm, regime, cap, reproduce_from=None, log_print=False, attempt=1, deviation=None):
    """One development run (four configurations). `attempt` enters the folder fingerprint, so that a run
    interrupted before its record was written leaves a folder without run.json (never indexed) and the
    resumed attempt gets its own folder; the E11 rule 'an existing folder blocks the launch' still holds
    for an identical (cell, cap, attempt)."""
    su = SetupE14(city, seed, regime)
    A, info = adjacency_e14(su, arm)
    cid = cell_id(city, seed, arm, regime)
    d = p4b.run_dir(E14 / "dev", {"protocol": "E14", "phase": "dev", "cell": cid, "cap": cap, "configs": CONFIGS, "f": F,
                                  "grid": su.G, "fingerprints": su.fingerprints(), "extension_of": reproduce_from["dir"] if reproduce_from else None,
                                  "attempt": attempt, "deviation": deviation})
    log = Log(d / "log.txt"); log(f"E14 dev {cid} cap {cap} -> {d}")
    out, repro = {}, {}
    for name, cfg in CONFIGS.items():
        o = train_e14(su, arm, A, cap, cfg, K_DEV_INIT, log=log if log_print else None, save_states=False)
        assert o["hidden_in_batches"] == 0
        out[name] = {"trajectory": o["trajectory"], "selected_checkpoint": o["selected"],
                     "selected_val_mae": min(t["val_mae"] for t in o["trajectory"]), "updates": o["updates"],
                     "seconds": o["seconds"], "init_seed": o["init_seed"], "adequacy": adequacy_of(o["trajectory"], cap)}
        if reproduce_from is not None:                 # the first 10 000 updates must reproduce the earlier curve
            old = reproduce_from["configs"][name]["trajectory"]; new = o["trajectory"][:len(old)]
            dmax = max(abs(a["val_mae"] - b["val_mae"]) for a, b in zip(old, new))
            repro[name] = {"max_abs_diff_val_mae": dmax, "ok": bool(dmax <= REPRO_TOL)}
            log(f"[{name}] reproduction of the {reproduce_from['cap']} curve: max |Δ| = {dmax:.3e} ({'ok' if dmax <= REPRO_TOL else 'NOT reproduced'})")
    sel = min(out.items(), key=lambda kv: (kv[1]["selected_val_mae"], kv[1]["selected_checkpoint"], kv[0]))
    rec = {"cell": cid, "city": city, "seed": seed, "arm": arm, "regime": regime, "cap": cap, "attempt": attempt, "deviation": deviation,
           "selected_config": sel[0], "selected_checkpoint": sel[1]["selected_checkpoint"],
           "selected_adequacy": sel[1]["adequacy"], "configs": out, "graph_info": info, "K": su.K,
           "shares": su.shares(), "geometry": su.geometry(), "fingerprints": su.fingerprints(),
           "extension_of": reproduce_from["dir"] if reproduce_from else None, "reproduction": repro}
    usable = all(v["ok"] for v in repro.values()) if repro else True
    rec["usable"] = usable
    record13(d, rec); log.save()
    _append("index_dev.jsonl", {"cell": cid, "dir": str(d), "cap": cap, "usable": usable})
    if not usable:
        log(f"reproduction failed: this run is kept but not usable for selection, final or lock")
    return rec | {"dir": str(d), "usable": usable}

def dev(args):
    gate("dev")
    cap = group_cap(args.city, args.arm, args.regime)
    if cap != CAP0:
        raise PermissionError(f"group {group_id(args.city, args.arm, args.regime)} is extended: use `extend`, not `dev`")
    cid = cell_id(args.city, args.seed, args.arm, args.regime)
    done = latest_dev(cid)
    if done is not None and done["cap"] == CAP0 and not getattr(args, "deviation", None):
        raise PermissionError(f"{cid}: a usable development run exists ({done['dir']}); a deliberate re-run requires a registered deviation (--deviation <note commit>)")
    rec = _dev_run(args.city, args.seed, args.arm, args.regime, CAP0, log_print=True, attempt=_next_attempt(cid), deviation=getattr(args, "deviation", None))
    print(json.dumps({k: rec[k] for k in ("cell", "selected_config", "selected_checkpoint", "selected_adequacy")}))
    return 0

def extend(args):
    """Extension of E14.md: every cell of the group to 20 000, all four configurations, reproduction checked."""
    gate("extend")
    gid = group_id(args.city, args.arm, args.regime); sp = E14 / f"extension_{gid}.json"
    st = extension_status(gid)
    if st and st["status"] == "complete":
        raise PermissionError(f"group {gid} already extended once: a second failure is a feasibility limit (E14.md)")
    if st is None:
        base = {}
        for s in SEEDS:
            dv = latest_dev(cell_id(args.city, s, args.arm, args.regime))
            if dv is None or dv["cap"] != CAP0:
                raise PermissionError(f"group {gid}: development at {CAP0} missing for seed {s}")
            base[s] = dv["dir"]
        failing = [s for s in SEEDS if not json.loads((Path(base[s]) / "run.json").read_text())["selected_adequacy"]["pass"]]
        if not failing:
            raise PermissionError(f"group {gid}: no development cell fails the adequacy rule; extension not allowed")
        st = {"group": gid, "status": "started", "started": datetime.now(timezone.utc).isoformat(), "cap": CAP1,
              "failing_seeds_at_10000": failing, "base_dirs": {str(s): base[s] for s in SEEDS}, "seeds": {},
              "attempts": {str(s): 0 for s in SEEDS}, "reproduction_failures": {str(s): 0 for s in SEEDS}}
        sp.write_text(json.dumps(st, indent=1))
    for s in SEEDS:
        done = st["seeds"].get(str(s))
        if done and done.get("usable"):
            continue                                                        # resume: keep the usable runs already produced
        if st["reproduction_failures"][str(s)] >= 2:
            continue                                                        # two completed runs that did not reproduce: left incomplete, reported
        base_rec = json.loads((Path(st["base_dirs"][str(s)]) / "run.json").read_text()) | {"dir": st["base_dirs"][str(s)]}
        st["attempts"][str(s)] += 1; st["status"] = "incomplete"; sp.write_text(json.dumps(st, indent=1))
        rec = _dev_run(args.city, s, args.arm, args.regime, CAP1, reproduce_from=base_rec, log_print=True, attempt=_next_attempt(cell_id(args.city, s, args.arm, args.regime)))
        st["seeds"][str(s)] = {"dir": rec["dir"], "usable": rec["usable"], "selected_config": rec["selected_config"],
                               "selected_checkpoint": rec["selected_checkpoint"], "adequacy": rec["selected_adequacy"], "reproduction": rec["reproduction"]}
        if not rec["usable"]:
            st["reproduction_failures"][str(s)] += 1
        sp.write_text(json.dumps(st, indent=1))
    complete = all(st["seeds"].get(str(s), {}).get("usable") for s in SEEDS)
    st["status"] = "complete" if complete else "incomplete"
    st["environment"] = environment(); st["written"] = datetime.now(timezone.utc).isoformat()
    sp.write_text(json.dumps(st, indent=1))
    print(json.dumps({"group": gid, "status": st["status"], "seeds": {k: {"usable": v["usable"], "config": v["selected_config"]} for k, v in st["seeds"].items()}}, indent=1))
    if not complete:
        print("extension incomplete: seeds without a usable reproduced run:", [s for s in SEEDS if not st["seeds"].get(str(s), {}).get("usable")],
              "— re-run `extend` to resume (an interruption is not a failure; two completed runs that do not reproduce are a reported failure)")
    return 0 if complete else 1

def final(args):
    gate("final")
    cid = cell_id(args.city, args.seed, args.arm, args.regime)
    dv = latest_dev(cid)
    if dv is None:
        raise FileNotFoundError(f"no development run for {cid}")
    if dv["cap"] != group_cap(args.city, args.arm, args.regime):
        raise PermissionError(f"{cid}: latest development cap {dv['cap']} differs from the group's cap; extension incomplete")
    cfg = CONFIGS[dv["selected_config"]]; cap = dv["cap"]
    su = SetupE14(args.city, args.seed, args.regime)
    A, info = adjacency_e14(su, args.arm)
    d = p4b.run_dir(E14 / "final", {"protocol": "E14", "phase": "final", "cell": cid, "cap": cap, "config": dv["selected_config"], "dev_dir": dv["dir"]})
    log = Log(d / "log.txt"); log(f"E14 final {cid} config {dv['selected_config']} cap {cap} -> {d}")
    o = train_e14(su, args.arm, A, cap, cfg, p4b.K_INIT, log=log, save_states=True)
    assert o["hidden_in_batches"] == 0 and o["init_seed"] != dv["configs"][dv["selected_config"]]["init_seed"]
    torch.save(o["states"][o["selected"]], d / "selected_state.pt")
    rec = {"cell": cid, "city": args.city, "seed": args.seed, "arm": args.arm, "regime": args.regime, "cap": cap,
           "config": dv["selected_config"], "cfg": cfg, "dev_dir": dv["dir"], "dev_run_sha16": p4b.sha256(Path(dv["dir"]) / "run.json", 16),
           "selected_checkpoint": o["selected"], "trajectory": o["trajectory"], "adequacy": adequacy_of(o["trajectory"], cap),
           "updates": o["updates"], "seconds": o["seconds"], "init_seed": o["init_seed"],
           "dev_init_seed": dv["configs"][dv["selected_config"]]["init_seed"], "fingerprints": su.fingerprints(),
           "graph_info": info, "state_sha16": p4b.sha256(d / "selected_state.pt", 16)}
    record13(d, rec); log.save()
    _append("index_final.jsonl", {"cell": cid, "dir": str(d)})
    print(json.dumps({k: rec[k] for k in ("cell", "config", "selected_checkpoint", "adequacy")}))
    return 0

def final_up_to_date(cid, city, arm, regime):
    dv, fn = latest_dev(cid), latest_final(cid)
    if dv is None or fn is None:
        return False, dv, fn
    ok = (fn["dev_dir"] == dv["dir"] and fn["config"] == dv["selected_config"] and fn["cap"] == dv["cap"] == group_cap(city, arm, regime)
          and fn["dev_run_sha16"] == p4b.sha256(Path(dv["dir"]) / "run.json", 16)
          and (Path(fn["dir"]) / "selected_state.pt").exists() and fn["state_sha16"] == p4b.sha256(Path(fn["dir"]) / "selected_state.pt", 16))
    return ok, dv, fn

def campaign(args):
    gate(args.phase)
    for c, s, a, r in all_cells():
        cid = cell_id(c, s, a, r); ns = argparse.Namespace(city=c, seed=s, arm=a, regime=r)
        if args.phase == "dev":
            dv = latest_dev(cid)
            if dv is not None and dv["cap"] == group_cap(c, a, r):
                continue
            if group_cap(c, a, r) != CAP0:
                print("skip", cid, "group extended: run `extend`"); continue
            dev(argparse.Namespace(**vars(ns), deviation=None))
        else:
            ok, dv, fn = final_up_to_date(cid, c, a, r)
            if ok:
                continue
            if dv is None:
                print("skip", cid, "no development"); continue
            final(ns)
    return 0

def compute_adequacy():
    exts = {p.stem.replace("extension_", ""): json.loads(p.read_text())["status"] for p in E14.glob("extension_*.json")}
    rep = {"cells": {}, "missing_dev": [], "missing_final": [], "final_stale": [], "dev_failures_pending": [],
           "dev_failures_after_extension": [], "final_failures": [], "extensions": exts,
           "extensions_incomplete": sorted(g for g, s_ in exts.items() if s_ != "complete")}
    for c, s, a, r in all_cells():
        cid = cell_id(c, s, a, r); ok, dv, fn = final_up_to_date(cid, c, a, r)
        if dv is None:
            rep["missing_dev"].append(cid); continue
        row = {"dev_dir": dv["dir"], "dev_run_sha16": p4b.sha256(Path(dv["dir"]) / "run.json", 16), "dev_cap": dv["cap"],
               "dev_selected_config": dv["selected_config"], "dev_selected_checkpoint": dv["selected_checkpoint"],
               "dev_adequacy": dv["selected_adequacy"], "group_cap": group_cap(c, a, r)}
        if not dv["selected_adequacy"]["pass"]:
            (rep["dev_failures_after_extension"] if dv["cap"] == CAP1 else rep["dev_failures_pending"]).append(cid)
        if fn is None:
            rep["missing_final"].append(cid)
        else:
            row |= {"final_dir": fn["dir"], "final_config": fn["config"], "final_cap": fn["cap"], "final_selected_checkpoint": fn["selected_checkpoint"],
                    "final_adequacy": fn["adequacy"], "state_sha16": fn["state_sha16"], "final_up_to_date": ok}
            if not ok:
                rep["final_stale"].append(cid)
            if not fn["adequacy"]["pass"]:
                rep["final_failures"].append(cid)
        rep["cells"][cid] = row
    rep["excluded_from_adequacy_statements"] = sorted(set(rep["dev_failures_after_extension"]) | set(rep["final_failures"]))
    rep["lock"] = not (rep["missing_dev"] or rep["missing_final"] or rep["final_stale"] or rep["dev_failures_pending"] or rep["extensions_incomplete"])
    rep["lock_sha16"] = hashlib.sha256(json.dumps({k: v for k, v in rep.items() if k != "lock_sha16"}, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return rep

def adequacy(args):
    rep = compute_adequacy() | {"written": datetime.now(timezone.utc).isoformat(), "environment": environment()}
    (RUNS / "e14_adequacy.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: rep[k] for k in ("missing_dev", "missing_final", "final_stale", "dev_failures_pending",
                                          "dev_failures_after_extension", "final_failures", "excluded_from_adequacy_statements", "lock", "lock_sha16")}, indent=1))
    print("dev_failures_pending: run `extend` for their groups, then `final` again; "
          "dev_failures_after_extension and final_failures: feasibility limit / inconclusive, excluded from adequacy-conditioned statements")
    return 0 if rep["lock"] else 1

def per_horizon_mean(num, den):
    """Mean over horizons of the per-horizon weighted ratios (E14.md, Unit of analysis): NOT the pooled ratio."""
    num = np.asarray(num, dtype="float64"); den = np.maximum(np.asarray(den, dtype="float64"), 1e-12)
    return float(np.mean(num / den))

def _week_index(ts):
    iso = pd.DatetimeIndex(ts).isocalendar()
    return (iso.year.to_numpy() * 100 + iso.week.to_numpy())
# ---- END DERIVED FROM e13.py ----

# ====================================================================================================
# E14-specific code (hand-written; the derived block above is a mechanical copy of e13.py functions)
# ====================================================================================================

def device_default():
    """CUDA (the Spark assignment of E14) when present, else the CPU for the checks that are explicitly allowed there (deterministic
    preflight, structural measures, the float64 sensitivity diagnostic). Never a silent third backend."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def _require_training_device(su):
    """Every command that updates a model runs on the assigned backend (TRAIN_DEVICE, CUDA on Spark); no fallback."""
    if su.dev.type != TRAIN_DEVICE:
        raise PermissionError(f"E14 trains on {TRAIN_DEVICE!r} (Spark); the setup is on {su.dev} — no fallback to another backend")


def teq(a, b):
    """Bitwise equality of two tensors with NaN equal to NaN at the same position (the raw targets carry NaN where missing)."""
    if a is None or b is None:
        return a is b
    return a.shape == b.shape and bool(((a == b) | (torch.isnan(a) & torch.isnan(b))).all())


class SetupE14(p4b.Setup):
    """E9 setup at f = 0.20 for the regression task (ADAPTER_SPEC_E14.md §1, §4, §6). Regime S0 (no coordinates) or S1
    (two standardised UTM channels). Adds to p4b.Setup: the factor scaler (mean and standard deviation of the valid factor
    values of the observed nodes over the training period, sd floored at 1e-6); the standardised factor series `RZ`
    (NaN → 0), its validity `RV`, the raw target series `RY` (NaN kept; `r_tgt` replaces it in the perturbed copies of C0.1),
    its standardised copy `RYZ` and validity `RYV`; the method's graph `A_method` with its cached random walks `Aq`, `Ah`;
    the coordinates `XY` standardised on the observed nodes. The arm (`full` / `nodyn`) is set by the training wrapper or
    passed to `batch`: in `nodyn` the factor history `r_in` is zero for every node and step and nothing else changes."""
    r_tgt = None

    def __init__(s, city, seed, regime, device=None):
        if regime not in REGIMES:
            raise ValueError(f"regime {regime!r} not in {REGIMES}")
        s.regime = regime; s.arm = None
        super().__init__(city, p4b.CITY[city]["roads"], seed=seed, grid=e9.GRID[city], targets=e9.targets(F), device=device or device_default())
        s.A_method, s.sigma_method, s.D_road, s.graph_stats = mga.method_graph(s.al["graph"], s.kept)
        s.At = torch.tensor(s.A_method, device=s.dev)
        s.Aq, s.Ah = mga.random_walk_matrix(s.At), mga.random_walk_matrix(s.At.T)
        xy = np.asarray(s.al["coords"], dtype="float64")
        mu, sd = xy[s.obs].mean(0), xy[s.obs].std(0) + 1e-6
        s.XY = torch.tensor(((xy - mu) / sd).astype("float32"), device=s.dev)

    def _stats(s):
        super()._stats()
        reg, o = slice(0, s.reg_end), s.obs
        v = s.r[reg][:, o].astype("float64"); v = v[np.isfinite(v)]
        s.rmu, s.rsd = float(v.mean()), float(max(v.std(), 1e-6))

    def _tensors(s):
        super()._tensors()
        T = lambda a: torch.tensor(a, device=s.dev)  # noqa: E731
        r64 = s.r.astype("float64"); valid = np.isfinite(r64)
        s.RZ = T(np.where(valid, (r64 - s.rmu) / s.rsd, 0.0).astype("float32")); s.RV = T(valid.astype("float32"))
        rt = (s.r if s.r_tgt is None else s.r_tgt).astype("float64"); vt = np.isfinite(rt)
        s.RY = T(rt.astype("float32")); s.RYZ = T(np.where(vt, (rt - s.rmu) / s.rsd, 0.0).astype("float32")); s.RYV = T(vt.astype("float32"))
        s._fix_cin()

    def _fix_cin(s):
        s.c_in = 1 + mga.exo_channels(s.regime)

    def fingerprints(s):
        return super().fingerprints() | {"factor_scaler": p4b.fingerprint([s.rmu, s.rsd]), "method_graph": p4b.fingerprint(s.A_method),
                                         "coordinates": p4b.fingerprint(s.XY.cpu().numpy())}

    def batch(s, origins, inp, tgt, arm=None, static=False):
        """Tensors of ADAPTER_SPEC §1 for B origins. inp, tgt: boolean node masks (numpy). Returns a dict: r_in, m_in (B, T, K, 1);
        node_in (K,); cal_in (B, T, K, 5); cal_out (B, H, K, 5); xy (K, 2) or None; y_z, y_raw, m_y (B, H, K, 1)."""
        if static:
            raise ValueError("E14: no static channel")
        arm = arm or s.arm
        if arm not in ARMS:
            raise RuntimeError("SetupE14.batch: the arm (full or nodyn) must be given or set before building a batch")
        bt = torch.as_tensor(np.asarray(origins), device=s.dev); B, K = len(bt), s.K
        node_in = torch.as_tensor(inp.astype("float32"), device=s.dev)
        tm = torch.as_tensor(tgt.astype("float32"), device=s.dev)
        idx_in = torch.stack([bt - k for k in reversed(range(T_IN))], 1)
        idx_out = torch.stack([bt + h for h in range(1, HSTEPS + 1)], 1)
        r_in = (s.RZ[idx_in] * node_in.view(1, 1, K)).unsqueeze(-1)
        m_in = (s.RV[idx_in] * node_in.view(1, 1, K)).unsqueeze(-1)
        if arm == "nodyn":
            r_in = torch.zeros_like(r_in)
        cal_in = torch.stack([g[idx_in] for g in s.TIME], -1).unsqueeze(2).expand(B, T_IN, K, 5)
        cal_out = torch.stack([g[idx_out] for g in s.TIME], -1).unsqueeze(2).expand(B, HSTEPS, K, 5)
        y_z = s.RYZ[idx_out].unsqueeze(-1); y_raw = s.RY[idx_out].unsqueeze(-1)
        m_y = (s.RYV[idx_out] * tm.view(1, 1, K)).unsqueeze(-1)
        return {"r_in": r_in, "m_in": m_in, "node_in": node_in, "cal_in": cal_in, "cal_out": cal_out,
                "xy": s.XY if s.regime == "S1" else None, "y_z": y_z, "y_raw": y_raw, "m_y": m_y}

    def inject(s, r, flow, occ, C):
        """C0.2: replace the target processes by synthetic ones (same shapes and timestamps) and rebuild; the graph is untouched."""
        s.r, s.flow, s.occ, s.C = r.astype("float32"), flow.astype("float32"), occ.astype("float32"), C.astype("int64")
        s.r_tgt = None
        s._stats(); s._tensors()


def _perturbed_copy(su, nz, perturb_val_labels):
    """C0.1 copy: the readings (input side) of every hidden node replaced by noise, flow and occupancy likewise (unused by
    S0/S1, perturbed as E13 did), the target series of the test-hidden nodes replaced (and of the validation-hidden nodes too
    when `perturb_val_labels`); validation labels kept otherwise, so the validation predictions can be compared."""
    pert = copy.copy(su)
    for k in ("r", "flow", "occ"):
        a_ = getattr(su, k).copy(); a_[:, ~su.obs] = nz.normal(size=a_[:, ~su.obs].shape); setattr(pert, k, a_)
    tgt = su.r.copy(); who = ~su.obs if perturb_val_labels else su.test
    tgt[:, who] = nz.normal(size=tgt[:, who].shape); pert.r_tgt = tgt
    C2 = su.C.copy(); C2[:, who] = nz.integers(1, 4, size=C2[:, who].shape); pert.C = C2
    pert._stats(); pert._tensors()
    return pert


def adjacency_e14(su, arm):
    """The method's graph lives on the setup (ADAPTER_SPEC §6); this entry point replaces `e9.adjacency` in the derived code and
    records the graph's description."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}")
    return su.A_method, {"graph": "method: Gaussian kernel on road-network distance within the declared road radius, kappa 0.1, zero diagonal (ADAPTER_SPEC_E14 §6)",
                         **su.graph_stats, "arm": arm, "regime": su.regime}


# ---------------------------------------------------------------- version-bound records (as E13B) ----------

_latest_dev_any_version, _latest_final_any_version = latest_dev, latest_final
OTHER_VERSION = {"dev": [], "final": []}


def _same_version(rec):
    return _report_matches_version(rec, frozen_tag())


def latest_dev(cid, usable_only=True):                                  # noqa: F811  (version-bound view of the derived function)
    rec = _latest_dev_any_version(cid, usable_only)
    if rec is not None and not _same_version(rec):
        if cid not in OTHER_VERSION["dev"]:
            OTHER_VERSION["dev"].append(cid)
        return None
    return rec


def latest_final(cid):                                                  # noqa: F811
    rec = _latest_final_any_version(cid)
    if rec is not None and not _same_version(rec):
        if cid not in OTHER_VERSION["final"]:
            OTHER_VERSION["final"].append(cid)
        return None
    return rec


_compute_adequacy_derived = compute_adequacy


def compute_adequacy():                                                 # noqa: F811  (version-bound view of the derived function)
    OTHER_VERSION["dev"].clear(); OTHER_VERSION["final"].clear()
    rep = _compute_adequacy_derived()
    rep["records_of_another_version"] = {"dev": sorted(OTHER_VERSION["dev"]), "final": sorted(OTHER_VERSION["final"])}
    rep["frozen_tag"] = frozen_tag(); rep["grid"] = sorted(CONFIGS) if CONFIGS else None
    rep["lock_sha16"] = hashlib.sha256(json.dumps({k: v for k, v in rep.items() if k != "lock_sha16"}, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return rep


# ---------------------------------------------------------------- training, prediction, metrics ----------

def mse_masked(pred, y_z, m_y):
    """Training loss (ADAPTER_SPEC §5): MSE on standardised values over the target entries (m_y = 1), all decoder steps."""
    return ((pred - y_z) ** 2 * m_y).sum() / m_y.sum().clamp_min(1)


def predict_e14(net, su, origins, inp, tgt, arm, bs=32):
    """Predictions in factor units (n, K, H) and raw targets (NaN where not a target or missing)."""
    net.eval(); P, Y = [], []
    with torch.no_grad():
        for i in range(0, len(origins), bs):
            b = su.batch(origins[i:i + bs], inp, tgt, arm)
            out, _ = net(b["r_in"], b["m_in"], b["node_in"], b["cal_in"], b["cal_out"], su.Aq, su.Ah, su.At, b["xy"])
            P.append((out[..., 0].float().cpu().numpy().astype("float64") * su.rsd + su.rmu).astype("float32").transpose(0, 2, 1))
            y = b["y_raw"][..., 0].cpu().numpy(); m = b["m_y"][..., 0].cpu().numpy() > 0
            Y.append(np.where(m, y, np.nan).astype("float32").transpose(0, 2, 1))
    return np.concatenate(P), np.concatenate(Y)


def mae_by_horizon(P, Y, horizons=None):
    """MAE in factor units per protocol horizon over the valid target entries (NaN if none)."""
    out = {}
    for h in (horizons or HORIZONS):
        e = np.abs(P[:, :, h - 1].astype("float64") - Y[:, :, h - 1].astype("float64")); v = np.isfinite(e)
        out[h] = float(e[v].mean()) if v.any() else float("nan")
    return out


def contrast_value(mae_a, mae_b):
    """Mean over the four horizons of the per-horizon ratios 100·(a_h − b_h)/a_h (the aggregation of the primary contrasts);
    NaN if some a_h is 0 or undefined."""
    vals = [100.0 * (mae_a[h] - mae_b[h]) / mae_a[h] if np.isfinite(mae_a[h]) and mae_a[h] > 0 and np.isfinite(mae_b[h]) else float("nan") for h in HORIZONS]
    return float(np.mean(vals))


def train_e14(su, arm, A, cap, cfg, init_stream, log=None, ck_every=CK_EVERY, save_states=True, keep_losses=False):
    """One training of the adapter on the setup's regime and the given arm: AdamW (lr, weight decay of `cfg`), batch 32, one
    update per batch, MSE on the target entries; validation MAE in factor units on the validation-hidden nodes (inputs = all
    observed nodes) every `ck_every` updates up to `cap`; configuration C3 steps a ReduceLROnPlateau (factor 0.5, patience 1
    checkpoint, min lr 1e-5) once after each validation checkpoint except the one at 0, in the order evaluate → step → save.
    No dropout, no gradient clipping, no teacher forcing. Returns trajectory (val_mae = mean over the four horizons, val_mae_h
    per horizon), states at every checkpoint (CPU) if asked, per-step losses if asked, counters. Never touches test origins."""
    assert arm in ARMS; su.arm = arm; _require_training_device(su)
    s_init = int(p4b.rng(su.seed, init_stream).integers(2 ** 31))
    torch.manual_seed(s_init)
    if su.dev.type == "cuda":
        torch.use_deterministic_algorithms(True, warn_only=True)         # deterministic kernels where they exist; C0.1 and the benchmark repetitions test the result
    net = mga.build(su.regime, HSTEPS, T_IN).to(su.dev)
    opt = torch.optim.AdamW(net.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="min", factor=0.5, patience=1, min_lr=1e-5) if cfg.get("sched") == "plateau" else None
    r_mask, r_order = p4b.rng(su.seed, p4b.K_MASKS), p4b.rng(su.seed, p4b.K_ORDER)
    perm, pi = r_order.permutation(su.tr), 0
    traj, states, steps, t0, run_loss, losses, seen_hidden = [], {}, 0, time.perf_counter(), [], [], 0
    cks = set(range(0, cap + 1, ck_every))

    def checkpoint():
        tv = time.perf_counter()
        P, Y = predict_e14(net, su, su.va, su.obs, su.val, arm)
        mh = mae_by_horizon(P, Y); v = float(np.mean([mh[h] for h in HORIZONS]))
        val_seconds = time.perf_counter() - tv
        tl = float(np.mean(run_loss)) if run_loss else None
        run_loss.clear()
        if sched is not None and steps > 0:
            sched.step(v)
        traj.append({"update": steps, "val_mae": v, "val_mae_h": {str(h): mh[h] for h in HORIZONS}, "train_loss": tl,
                     "seconds": time.perf_counter() - t0, "val_seconds": val_seconds, "lr": float(opt.param_groups[0]["lr"])})
        if save_states:
            states[steps] = {k: t.detach().cpu().clone() for k, t in net.state_dict().items()}
        if log:
            log(f"[{arm} {su.regime}] update {steps:6d}  val MAE {v:.5f}  train {tl if tl is None else round(tl, 5)}  lr {opt.param_groups[0]['lr']:.2e}")
    checkpoint()
    while steps < cap:
        if pi + 32 > len(perm):
            perm, pi = r_order.permutation(su.tr), 0
        bt = perm[pi:pi + 32]; pi += 32
        inp, tgt, _ = su.batch_mask(r_mask)
        seen_hidden += int(inp[~su.obs].sum() + tgt[~su.obs].sum())
        b = su.batch(bt, inp, tgt, arm)
        net.train(); opt.zero_grad()
        out, _ = net(b["r_in"], b["m_in"], b["node_in"], b["cal_in"], b["cal_out"], su.Aq, su.Ah, su.At, b["xy"])
        loss = mse_masked(out, b["y_z"], b["m_y"]); loss.backward(); opt.step(); steps += 1
        lv = float(loss.item()); run_loss.append(lv)
        if keep_losses:
            losses.append(lv)
        if steps in cks:
            checkpoint()
    best = min(traj, key=lambda d: (d["val_mae"], d["update"]))
    return {"net": net, "A": A, "states": states, "trajectory": traj, "selected": best["update"], "updates": steps,
            "hidden_in_batches": seen_hidden, "seconds": time.perf_counter() - t0, "init_seed": s_init, "losses": losses,
            "parameters": net.parameter_count()}


# ---------------------------------------------------------------- calendar baseline (no fit) -------------

def calendar_tables(su, min_count=5):
    """Per weekly slot (weekday × 15-min slot, 672): median (primary) and mean (secondary, for RMSE) of the observed-training
    sites' valid factor values; a slot with fewer than `min_count` values takes the global observed-training median / mean.
    Uses no value of any hidden node."""
    reg = slice(0, su.reg_end); rv = su.r[reg][:, su.obs].astype("float64"); sl = np.broadcast_to(su.slot[reg][:, None], rv.shape)
    v = np.isfinite(rv); vals, keys = rv[v], sl[v]
    gmed, gmean = float(np.median(vals)), float(vals.mean())
    med, mean, cnt = np.full(672, gmed), np.full(672, gmean), np.zeros(672, dtype="int64")
    order = np.argsort(keys, kind="stable"); ks, vs = keys[order], vals[order]
    bounds = np.flatnonzero(np.diff(ks)) + 1; groups = np.split(vs, bounds); uniq = ks[np.concatenate([[0], bounds])]
    for k, g in zip(uniq, groups):
        cnt[k] = len(g)
        if len(g) >= min_count:
            med[k], mean[k] = float(np.median(g)), float(g.mean())
    return {"median": med, "mean": mean, "count": cnt, "global_median": gmed, "global_mean": gmean, "slots_fallback": int((cnt < min_count).sum())}


def calendar_predict(su, origins, table):
    """(n, H) predictions at the target times t + 1 … t + H from a per-slot table."""
    idx = np.asarray(origins)[:, None] + np.arange(1, HSTEPS + 1)[None, :]
    return table[su.slot[idx]]


# ---------------------------------------------------------------- C0.2: diagnostic and synthetic control ---

def tabular_mae_diagnostic(su, z, hops=REF_HOPS, min_count=5, slot=None, n_slots=672):
    """ADAPTER_SPEC §7, MAE version of `e13.tabular_diagnostic`. PRIVILEGED: both tables are estimated on the validation-hidden
    nodes' own training-origin targets (which the model never sees) and read on validation origins; this measures how much
    a tabular predictor gains from the spatial feature, not a bound on the model. Table A: median of z per weekly slot (672)
    of the target time, fallback to the global median when a slot has < `min_count` values. Table B: median within (slot ×
    bin of the spatial feature at the origin), the feature being the input (observed) nodes' z at the origin propagated by the
    REFERENCE operator Σ_{k≤hops}(A_q)^k and divided by the propagated mass, 32 equal-width bins over [0, 1.6] plus the
    unreachable bin; fallback to Table A's slot median. gain_h = 100·(MAE_A − MAE_B)/MAE_A; the diagnostic gain is the mean.
    `slot`/`n_slots` override the weekly slot (development calibration only, `diag-dev`); the protocol uses su.slot (672)."""
    z = np.asarray(z, dtype="float64"); slot = su.slot if slot is None else np.asarray(slot); obs, hid = su.obs, su.val; tr, va = np.asarray(su.tr), np.asarray(su.va)
    den, Mo = mga.reference_mass(su.Aq.cpu().numpy(), obs, hops); reached = den > 0
    num = z[:, obs] @ Mo.T
    feat = np.where(reached[None, :], num / np.where(reached, den, 1.0)[None, :], -1.0)
    zb = np.where(feat < 0, 0, np.digitize(feat, np.linspace(0, 1.6, 33)) + 1)          # 0 = unreachable, 1..34
    out = {"feature": f"reference_mass_{hops}hops", "hidden_reached_share": float(reached[hid].mean()), "privileged": True}

    def table(keys, vals, n_keys, fallback):
        """Median per key over the pooled (origin, node) entries; fallback vector (n_keys,) where the count is < min_count.
        Returns the table and the number of keys estimated from their own values."""
        med = np.array(fallback, dtype="float64").copy(); filled = 0
        order = np.argsort(keys, kind="stable"); ks, vs = keys[order], vals[order]
        bounds = np.flatnonzero(np.diff(ks)) + 1; groups = np.split(vs, bounds); uniq = ks[np.concatenate([[0], bounds])] if len(ks) else []
        for k, g in zip(uniq, groups):
            if len(g) >= min_count:
                med[k] = np.median(g); filled += 1
        return med, filled
    gains = []
    for h in HORIZONS:
        Ytr, Yva = z[tr + h][:, hid], z[va + h][:, hid]
        str_, sva = slot[tr + h], slot[va + h]
        tA, fa = table(np.broadcast_to(str_[:, None], Ytr.shape).ravel(), Ytr.ravel(), n_slots, np.full(n_slots, np.median(Ytr)))
        kB_tr = (zb[tr][:, hid] * n_slots + str_[:, None]).ravel(); kB_va = zb[va][:, hid] * n_slots + sva[:, None]
        tB, fb = table(kB_tr, Ytr.ravel(), 35 * n_slots, np.tile(tA, 35))
        PA = np.broadcast_to(tA[sva][:, None], Yva.shape); PB = tB[kB_va]
        a, b = float(np.abs(PA - Yva).mean()), float(np.abs(PB - Yva).mean())
        out[str(h)] = {"mae_calendar": a, "mae_calendar_feature": b, "gain": 100 * (a - b) / a, "entries": int(Ytr.size),
                       "table_A_slots_estimated": int(fa), "table_B_cells_estimated": int(fb), "table_B_cells_used_on_validation": int(len(np.unique(kB_va)))}
        gains.append(out[str(h)]["gain"])
    out["mean_gain"] = float(np.mean(gains))
    return out


def diag_dev(args):
    """Development calibration of the privileged MAE diagnostic (no training, no C0.2 seed, nothing written into the repository):
    both kinds of `e13.synth_processes` on Madrid seed 0 with a development seed, gains for the declared setting (weekly slots,
    reference operator of 14 hops) and, for comparison only, 6 hops and daily slots (96). Written to --out. The thresholds and
    the setting of C0.2 are fixed by E14.md / ADAPTER_SPEC; a change requires a revision before the signature."""
    if int(args.seed) in SYNTH_SEEDS.values():
        raise PermissionError("the C0.2 seeds are reserved: use a development seed")
    su = SetupE14("madrid", 0, "S0", device="cpu"); daily = su.slot % 96
    out = {"purpose": "development calibration of the C0.2 diagnostic (not a protocol record)", "seed": int(args.seed), "settings": {}, "environment": environment()}
    for kind in ("dependent", "independent"):
        z, flow, occ, C = e13.synth_processes(su, kind, int(args.seed)); su.inject(z, flow, occ, C)
        for label, hops, sl, ns in (("weekly672_hops14 (declared)", REF_HOPS, None, 672), ("weekly672_hops6", 6, None, 672), ("daily96_hops14", REF_HOPS, daily, 96), ("daily96_hops6", 6, daily, 96)):
            d = tabular_mae_diagnostic(su, z, hops=hops, slot=sl, n_slots=ns)
            out["settings"].setdefault(label, {})[kind] = d
            print(f"{kind:12s} {label:28s} gain {d['mean_gain']:7.2f}  per horizon {[round(d[str(h)]['gain'], 1) for h in HORIZONS]}  "
                  f"entries {d['1']['entries']}  table B cells estimated {d['1']['table_B_cells_estimated']} / used {d['1']['table_B_cells_used_on_validation']}  reached {d['hidden_reached_share']:.3f}", flush=True)
    Path(args.out).write_text(json.dumps(out, indent=1)); print("->", args.out)
    return 0


def c0_synth(args):
    """C0.2 of E14.md: realisations of `e13.synth_processes` with the seeds fixed in SYNTH_SEEDS (Madrid seed 0), the latent
    factor z as the continuous target; validity of BOTH on the privileged MAE diagnostic before the first fit; then S0-full and
    S0-nodyn, configuration C1, 2 000 updates, validation every 250, stream-7 initialisation; V at the best checkpoint (≥ 500,
    minimal validation MAE of S0-full) = mean over the four horizons of the per-horizon ratios. Saves the S0-full states at 0
    and at the best checkpoint (dependent) for the sensitivity diagnostic. Verdicts as E14.md."""
    gate("c0")
    path = RUNS / "e14_c0_synth.json"
    if path.exists():
        st = json.loads(path.read_text()).get("status", "complete")
        raise FileExistsError(f"{path} exists (status {st!r}): C0.2 is recorded once; an incomplete attempt stays identifiable and is not repeated without a dated note")
    out = {"protocol": "E14 C0.2", "status": "started", "generator_version": 2, "generator_seeds": SYNTH_SEEDS, "generator": e13.synth_processes.__doc__,
           "diagnostic": tabular_mae_diagnostic.__doc__, "init_stream": K_DEV_INIT, "kinds": {}, "trainings": 0,
           "started": datetime.now(timezone.utc).isoformat(), "environment": environment()}
    path.write_text(json.dumps(out, indent=1))
    gens = {}
    for kind in ("dependent", "independent"):
        su = SetupE14("madrid", 0, "S0"); z, flow, occ, C = e13.synth_processes(su, kind, SYNTH_SEEDS[kind]); su.inject(z, flow, occ, C)
        dg = tabular_mae_diagnostic(su, z)
        valid = dg["mean_gain"] >= 10 if kind == "dependent" else abs(dg["mean_gain"]) <= 1
        print(kind, "seed", SYNTH_SEEDS[kind], "privileged MAE diagnostic: gain per horizon", {h: round(dg[h]["gain"], 2) for h in ("1", "2", "4", "8")},
              "mean", round(dg["mean_gain"], 2), "| hidden reached", round(dg["hidden_reached_share"], 3), "->", "valid" if valid else "INVALID")
        gens[kind] = (su, dg, valid)
    out["control_check"] = {k: {"diagnostic": v[1], "valid": v[2], "seed": SYNTH_SEEDS[k]} for k, v in gens.items()}
    path.write_text(json.dumps(out, indent=1))
    if not all(v[2] for v in gens.values()):
        out["status"] = "complete"; out["verdict"] = "synthetic control invalid on the diagnostic: no training performed (stopping rule)"
        out["written"] = datetime.now(timezone.utc).isoformat(); path.write_text(json.dumps(out, indent=1))
        print("->", path, p4b.sha256(path, 16), "control invalid, stopped before training"); return 1
    sdir = RUNS / "e14_c0_states"; sdir.mkdir(exist_ok=True)
    for kind in ("dependent", "independent"):
        su = gens[kind][0]; res = {}
        for arm in ARMS:
            out["status"] = f"incomplete: training {kind} {arm}"; path.write_text(json.dumps(out, indent=1))
            o = train_e14(su, arm, su.A_method, 2000, CONFIGS_FULL["C1"], K_DEV_INIT, ck_every=250, save_states=(arm == "full"), log=print); out["trainings"] += 1
            res[arm] = [{"update": t["update"], "val_mae": t["val_mae"], "val_mae_h": t["val_mae_h"], "train_loss": t["train_loss"]} for t in o["trajectory"]]
            out.setdefault("partial", {})[f"{kind}:{arm}"] = res[arm]; path.write_text(json.dumps(out, indent=1))
            if arm == "full":
                full_states, init_seed = o["states"], o["init_seed"]
        V = [(a["update"], contrast_value({h: a["val_mae_h"][str(h)] for h in HORIZONS}, {h: b["val_mae_h"][str(h)] for h in HORIZONS}))
             for a, b in zip(res["nodyn"], res["full"])]
        fl = [t for t in res["full"] if t["update"] >= 500 and np.isfinite(t["val_mae"])]
        after500 = [v for u, v in V if u >= 500]
        if not fl or not all(np.isfinite(after500)):
            ub, v_best = None, None
            verdict = "undefined: a validation MAE or a contrast is not finite at a checkpoint >= 500 — the control cannot be evaluated; procedure stopped (no pass, no acceptance route)"
            note = None
        else:
            ub = min(fl, key=lambda t: (t["val_mae"], t["update"]))["update"]; v_best = next(v for u, v in V if u == ub)
            if kind == "dependent":
                verdict = "pass" if v_best >= 3 else "FAIL: the dependent control is not passed (V < +3 at the best checkpoint); C1 blocked, no acceptance route"
                note = None
            else:
                verdict = "anomaly: V > +3 at a checkpoint >= 500 — explain in a dated note; c0-accept limited to this anomaly" if max(after500) > 3 else "pass"
                note = "S0-full worse than S0-nodyn by > 3 at some checkpoint — reported, not a block" if min(after500) < -3 else None
        torch.save(full_states[0], sdir / f"{kind}_full_init.pt"); states_rec = {"init": p4b.sha256(sdir / f"{kind}_full_init.pt", 16)}
        if ub is not None:
            torch.save(full_states[ub], sdir / f"{kind}_full_best.pt"); states_rec["best"] = p4b.sha256(sdir / f"{kind}_full_best.pt", 16)
        out["kinds"][kind] = {"trajectories": res, "V_by_checkpoint": V, "best_checkpoint_full": ub, "V_at_best": v_best, "verdict": verdict, "note": note,
                              "init_seed_full": init_seed, "states": states_rec}
        print(kind, "best checkpoint of S0-full", ub, "V", None if v_best is None else round(v_best, 2), "->", verdict)
    out.pop("partial", None); out["status"] = "complete"
    out["written"] = datetime.now(timezone.utc).isoformat(); c, dirty = p4b.git_commit(); out["commit"] = c; out["code_dirty"] = dirty
    path.write_text(json.dumps(out, indent=1)); print("->", path, p4b.sha256(path, 16))
    return 0 if out["kinds"]["dependent"]["verdict"] == "pass" and out["kinds"]["independent"]["verdict"] == "pass" else 1


def c0_accept(args):
    """Acceptance limited to the independent anomaly of C0.2, bound to the report fingerprint and the frozen tag."""
    c0 = RUNS / "e14_c0_synth.json"; z = json.loads(c0.read_text())
    if z["kinds"]["dependent"]["verdict"] != "pass":
        raise PermissionError("the dependent control is not passed: it cannot be accepted (E14.md)")
    if z["kinds"]["independent"]["verdict"] == "pass":
        raise PermissionError("the independent control shows no anomaly: nothing to accept")
    if not z["kinds"]["independent"]["verdict"].startswith("anomaly"):
        raise PermissionError("the independent control is undefined (not evaluable): it cannot be accepted, the procedure is stopped")
    rec = {"scope": "independent anomaly", "accepted_by": args.by, "note_commit": args.note_commit, "c0_synth_sha16": p4b.sha256(c0, 16),
           "frozen_tag": frozen_tag(), "independent_verdict": z["kinds"]["independent"]["verdict"], "written": datetime.now(timezone.utc).isoformat()}
    (RUNS / "e14_c0_resolution.json").write_text(json.dumps(rec, indent=1)); print(json.dumps(rec, indent=1)); return 0


def sensitivity(args):
    """C0.5(b): local numerical sensitivity on the C0.2 state (Madrid seed 0, dependent realisation, arm S0-full) at the best
    checkpoint and at the stream-7 initialisation: the gradient of each decoder output at the validation-hidden targets with
    respect to every input node's factor series, float64 on the CPU, on the first `--origins` validation origins (inputs = all
    observed nodes). Reported: the share of hidden targets (node × origin × horizon) whose largest |gradient| over the input
    nodes exceeds 1e-12, and the distribution of log10 of that maximum. A property of weights, activations and inputs — not a
    reachability classification (a sub-threshold gradient does not make a node structurally unreachable)."""
    gate("c0")
    c0p = RUNS / "e14_c0_synth.json"
    if not c0p.exists():
        raise PermissionError("C0.2 (c0-synth) has not been run")
    z = json.loads(c0p.read_text())
    if z.get("status") != "complete" or "dependent" not in z.get("kinds", {}):
        raise PermissionError("C0.2 incomplete or stopped before training: no state for the sensitivity diagnostic")
    if not _report_matches_version(z, frozen_tag()):
        raise PermissionError("the C0.2 report belongs to another version")
    path = RUNS / "e14_sensitivity.json"
    if path.exists():
        raise FileExistsError(f"{path} exists")
    su = SetupE14("madrid", 0, "S0", device="cpu"); zz, flow, occ, C = e13.synth_processes(su, "dependent", SYNTH_SEEDS["dependent"]); su.inject(zz, flow, occ, C)
    n_or = int(getattr(args, "origins", 4)); origins = su.va[:n_or]; b = su.batch(origins, su.obs, su.val, "full")
    b = {k: (v.double() if torch.is_tensor(v) else v) for k, v in b.items()}
    Aq, Ah, At = su.Aq.double(), su.Ah.double(), su.At.double()
    out = {"protocol": "E14 C0.5(b)", "c0_synth_sha16": p4b.sha256(c0p, 16), "origins": int(n_or), "threshold": 1e-12, "states": {}, "environment": environment(),
           "started": datetime.now(timezone.utc).isoformat()}
    hid = np.flatnonzero(su.val); obs = torch.as_tensor(su.obs)
    for label in ("init", "best"):
        sp_ = RUNS / "e14_c0_states" / f"dependent_full_{label}.pt"
        if p4b.sha256(sp_, 16) != z["kinds"]["dependent"]["states"][label]:
            raise PermissionError(f"{sp_} differs from the state recorded by C0.2")
        net = mga.build("S0", HSTEPS, T_IN).double(); net.load_state_dict({k: v.double() for k, v in torch.load(sp_).items()}); net.eval()
        r_in = b["r_in"].clone().requires_grad_(True)
        outp, _ = net(r_in, b["m_in"], b["node_in"], b["cal_in"], b["cal_out"], Aq, Ah, At, None)
        gmax = np.zeros((len(hid), n_or, len(HORIZONS)))
        for j, h in enumerate(HORIZONS):
            for i, n in enumerate(hid):
                g = torch.autograd.grad(outp[:, h - 1, n, 0].sum(), r_in, retain_graph=True)[0][..., 0]      # (B, T, K): origins are independent
                gmax[i, :, j] = g.abs().sum(1)[:, obs].max(1).values.numpy()
        pos = gmax[gmax > 0]; lg = np.log10(np.maximum(gmax, 1e-300))
        out["states"][label] = {"state_sha16": p4b.sha256(sp_, 16), "share_above_threshold": float((gmax > 1e-12).mean()),
                                "share_above_threshold_by_horizon": {str(h): float((gmax[:, :, j] > 1e-12).mean()) for j, h in enumerate(HORIZONS)},
                                "log10_max_gradient_quantiles": {q: float(np.percentile(lg, q)) for q in (0, 5, 25, 50, 75, 95, 100)},
                                "exact_zero_share": float((gmax == 0).mean()), "n_targets": int(gmax.size)}
        print(label, json.dumps(out["states"][label]))
    out["written"] = datetime.now(timezone.utc).isoformat(); path.write_text(json.dumps(out, indent=1)); print("->", path, p4b.sha256(path, 16))
    return 0


# ---------------------------------------------------------------- budget rule (before the tag) ------------

def budget_cost(bench, n_fits):
    """Hours = Σ over cell types of n_fits × (U_max × s/update + 24 × s/validation) / 3600 (ADAPTER_SPEC §9), each counted once:
    s/update is the benchmark's time per update NET of the validation passes, s/validation the median validation pass."""
    return float(sum(n_fits * (CAP0 * bench[ct]["seconds_per_update_net_median"] + 24 * bench[ct]["seconds_per_validation_median"]) / 3600 for ct in bench))


def budget_decision(bench, h_cal):
    full, red = budget_cost(bench, FITS_PER_TYPE["full"]), budget_cost(bench, FITS_PER_TYPE["reduced"])
    grid = "full" if full <= 0.8 * h_cal else ("reduced" if red <= 0.8 * h_cal else "renegotiate")
    return {"h_cal": float(h_cal), "reserve_included": "H_cal includes the 20 % reserve stated by the responsible author", "usable_h": 0.8 * float(h_cal),
            "cost_full_h": full, "cost_reduced_h": red, "fits": {"full": 4 * FITS_PER_TYPE["full"], "reduced": 4 * FITS_PER_TYPE["reduced"]},
            "grid": grid, "configs": list(CONFIGS_FULL) if grid == "full" else (list(REDUCED) if grid == "reduced" else None), "u_max": CAP0}


PRE_CODE_PATHS = ["paper4/code/p4b.py", "paper4/code/e9.py", "paper4/code/e11.py", "paper4/code/e13.py", "paper4/code/e14.py", "paper4/code/mogernn_adapter.py"]


def _git_blob_sha16(ref, path):
    r = _git("show", f"{ref}:{path}")
    return hashlib.sha256(r.stdout.encode()).hexdigest()[:16] if r.returncode == 0 else None


def _pre_report_ok(z, pre_path):
    """The E14-pre report usable for the budget and re-verified by the gate: complete; C0.1 passed for the four cell types (explicit
    verdicts); produced by this code (fingerprints); its E14pre tag reachable from HEAD with the code files, E14pre.md and the
    specification identical to it; the recorded fingerprints of E14pre.md and of the specification equal to the present files;
    the recorded fingerprint of E14.md equal to E14.md AT THE E14pre TAG (the signature of E14 changes it afterwards, as the
    sequence provides); the four benchmark medians present."""
    if z.get("status") != "complete":
        raise PermissionError(f"E14-pre incomplete ({z.get('status')!r})")
    tag = z.get("tag", "")
    if not tag.startswith("paper4-E14pre-") or _git("merge-base", "--is-ancestor", tag, "HEAD").returncode != 0:
        raise PermissionError(f"the E14-pre report's tag {tag!r} is not an E14pre tag reachable from HEAD")
    if _git("diff", "--quiet", tag, "HEAD", "--", *PRE_CODE_PATHS, "protocol/paper4/E14pre.md", SPEC.relative_to(ROOT).as_posix()).returncode != 0:
        raise PermissionError(f"code files, E14pre.md or the specification differ from the E14pre tag {tag}")
    ps = z.get("prereg_sha16", {})
    if ps.get("E14pre.md") != p4b.sha256(PREPRE, 16) or ps.get("ADAPTER_SPEC_E14.md") != p4b.sha256(SPEC, 16):
        raise PermissionError("the E14-pre report records other fingerprints of E14pre.md or of the specification")
    if ps.get("E14.md") != _git_blob_sha16(tag, "protocol/paper4/E14.md"):
        raise PermissionError(f"the E14-pre report records another fingerprint of E14.md than the one at its tag {tag}")
    c01 = z.get("C0.1", {}); cts = [f"{r}-{a}" for r in REGIMES for a in ARMS]
    if set(c01) != set(cts) or not all(c01[ct].get("pass") is True for ct in cts) or z.get("c0_1_pass") is not True:
        raise PermissionError("C0.1 not passed for the four cell types (or verdicts missing): no budget decision, E14 is not signed until the cause is corrected")
    if z.get("environment", {}).get("code_sha16") != environment()["code_sha16"]:
        raise PermissionError("the E14-pre report was produced by other code (fingerprints differ)")
    bench = z.get("benchmark", {})
    if set(bench) != set(cts) or not all("seconds_per_update_net_median" in bench[ct] and "seconds_per_validation_median" in bench[ct] for ct in cts):
        raise PermissionError("benchmark medians missing for some cell type")
    return True


def budget(args):
    """`budget --h-cal H --by NAME`: applies the budget rule to the E14-pre benchmark and writes `e14_grid.json`, to be committed
    (git add -f) before the tag; the active grid of every later command is read from it."""
    pre = RUNS / "e14_pre.json"
    if not pre.exists():
        raise PermissionError("e14_pre.json missing: the benchmark of E14-pre is required")
    z = json.loads(pre.read_text())
    _pre_report_ok(z, pre)
    if GRID_FILE.exists():
        raise FileExistsError(f"{GRID_FILE} exists: the budget decision is recorded once")
    dec = budget_decision(z["benchmark"], args.h_cal) | {"by": args.by, "pre_sha16": p4b.sha256(pre, 16), "written": datetime.now(timezone.utc).isoformat(),
                                                           "rule": "full grid if cost <= 0.8 H_cal; else C1 + C2 if its cost <= 0.8 H_cal; else collegial renegotiation; U_max never lowered"}
    GRID_FILE.write_text(json.dumps(dec, indent=1)); print(json.dumps(dec, indent=1))
    return 0 if dec["grid"] != "renegotiate" else 1


# ---------------------------------------------------------------- gate ------------------------------------

def gate(phase):
    """Launch constraints of E14 (E14.md, Order and Files): an E14 tag reachable from HEAD, the frozen files (E13's plus e14.py,
    mogernn_adapter.py, E14.md, ADAPTER_SPEC_E14.md, e14_grid.json) identical to it, clean working tree, signature line filled,
    the budget decision committed with an active grid; for C1 commands: the C0.2 report of this frozen version with BOTH
    realisations valid and the dependent control passed (no acceptance route), the independent control passed or its anomaly
    accepted (acceptance bound to the report fingerprint and the frozen tag), the sensitivity report of this version, and the
    signed P4R revision recorded by E13B (`e13b_p4r_revision.json`, committed, matching the committed P4R.md)."""
    tag = frozen_tag()
    if not tag.startswith("paper4-E14-"):
        raise PermissionError(f"no E14 tag reachable from HEAD (git describe --match paper4-E14-*: {tag!r})")
    if not frozen_unchanged(tag):
        raise PermissionError(f"code or protocol differ from the frozen tag {tag} ({', '.join(FROZEN_PATHS)}): a new signed tag is required")
    if not git_clean():
        raise PermissionError("working tree not clean (modified tracked files or untracked files): the run would not be from the frozen version")
    p4b.require_signed(PREREG)
    if not SPEC.exists():
        raise PermissionError(f"{SPEC} missing")
    if not GRID_FILE.exists() or not git_committed_unchanged(GRID_FILE.relative_to(ROOT)):
        raise PermissionError("e14_grid.json (budget decision) missing or not committed unchanged: run `budget` after E14-pre and commit it (git add -f) before the tag")
    if CONFIGS is None:
        raise PermissionError("e14_grid.json records a scope to be renegotiated: no grid is active")
    gd = json.loads(GRID_FILE.read_text()); pre_p = RUNS / "e14_pre.json"
    if not pre_p.exists() or gd.get("pre_sha16") != p4b.sha256(pre_p, 16):
        raise PermissionError("e14_grid.json is not bound to the present e14_pre.json (fingerprint differs or report missing)")
    _pre_report_ok(json.loads(pre_p.read_text()), pre_p)
    if budget_decision(json.loads(pre_p.read_text())["benchmark"], gd["h_cal"])["grid"] != gd.get("grid"):
        raise PermissionError("e14_grid.json does not reproduce the budget rule on the present benchmark")
    if phase in ("dev", "extend", "final", "test", "analysis"):
        c0 = RUNS / "e14_c0_synth.json"
        if not c0.exists():
            raise PermissionError("C0.2 (c0-synth) has not been run")
        z = json.loads(c0.read_text())
        if not _report_matches_version(z, tag):
            raise PermissionError("the C0.2 report was produced by another version (tag, code or protocol fingerprint differ)")
        cc = z.get("control_check", {})
        if not (cc.get("dependent", {}).get("valid") and cc.get("independent", {}).get("valid")):
            raise PermissionError("C0.2: a synthetic realisation is invalid on the diagnostic: C1 cannot start (stopping rule)")
        kinds = z.get("kinds", {})
        if kinds.get("dependent", {}).get("verdict") != "pass":
            raise PermissionError("C0.2 dependent control not passed: C1 cannot start; no acceptance route exists for this condition (E14.md)")
        if kinds.get("independent", {}).get("verdict") != "pass":
            acc = RUNS / "e14_c0_resolution.json"
            if not acc.exists():
                raise PermissionError("C0.2 independent control shows an anomaly: explain it in a dated note and record c0-accept")
            r = json.loads(acc.read_text())
            if r.get("c0_synth_sha16") != p4b.sha256(c0, 16) or r.get("frozen_tag") != tag or r.get("scope") != "independent anomaly":
                raise PermissionError("c0-accept refers to another C0.2 report or version, or is not limited to the independent anomaly")
        sens = RUNS / "e14_sensitivity.json"
        if not sens.exists():
            raise PermissionError("the sensitivity diagnostic (C0.5b, `sensitivity`) has not been run: it precedes C1 (E14.md, Order 5; no criterion attached)")
        zs = json.loads(sens.read_text())
        if not _report_matches_version(zs, tag) or zs.get("c0_synth_sha16") != p4b.sha256(c0, 16):
            raise PermissionError("the sensitivity report belongs to another version or another C0.2 report")
        rev = RUNS / "e13b_p4r_revision.json"
        if not rev.exists() or not git_committed_unchanged(rev.relative_to(ROOT)):
            raise PermissionError("the signed P4R revision record (e13b_p4r_revision.json) is missing or not committed unchanged")
        rv = json.loads(rev.read_text()); p4r = ROOT / "protocol" / "paper4" / "P4R.md"
        if rv.get("p4r_sha16") != p4b.sha256(p4r, 16) or not git_committed_unchanged(p4r.relative_to(ROOT)):
            raise PermissionError("P4R.md differs from the recorded signed revision, or is not committed unchanged")
    return tag


# ---------------------------------------------------------------- test and analysis -----------------------

def test(args):
    gate("test")
    lock_path = RUNS / "e14_adequacy.json"
    saved = json.loads(lock_path.read_text())
    now = compute_adequacy()
    if not saved.get("lock") or saved.get("lock_sha16") != now["lock_sha16"]:
        raise PermissionError("the lock file does not match the current records, or the lock is not satisfied: run `adequacy` and commit it")
    if not git_committed_unchanged(lock_path.relative_to(ROOT)):
        raise PermissionError("e14_adequacy.json is not committed unchanged (git add -f, commit) — the protocol requires the committed report")
    hz = [h - 1 for h in HORIZONS]; cache = {}
    for c, s, a, r in all_cells():
        cid = cell_id(c, s, a, r); fn = latest_final(cid); d = Path(fn["dir"])
        if (d / "test_cells.npz").exists():
            old = np.load(d / "test_cells.npz")
            if str(old["lock_sha16"]) != now["lock_sha16"]:
                raise PermissionError(f"{d / 'test_cells.npz'} was produced under another lock ({old['lock_sha16']}); move it aside, it is not overwritten")
            continue
        su = SetupE14(c, s, r); su.arm = a
        net = mga.build(r, HSTEPS, T_IN).to(su.dev); net.load_state_dict(torch.load(d / "selected_state.pt")); net.to(su.dev)
        if (c, s) not in cache:
            tabs = calendar_tables(su); rows, _ = mga.dependency_rows(su.A_method, su.obs, T_IN, HSTEPS, 2, completed=missing_in_period(su, su.te))
            cache[(c, s)] = (calendar_predict(su, su.te, tabs["median"])[:, hz].astype("float32"), calendar_predict(su, su.te, tabs["mean"])[:, hz].astype("float32"),
                             rows[0].any(1), tabs["slots_fallback"])
        cal_med, cal_mean, dep_possible, fb = cache[(c, s)]
        P, Y = predict_e14(net, su, su.te, su.obs, su.test, a)
        np.savez_compressed(d / "test_cells.npz", p=P[:, :, hz].astype("float32"), y=Y[:, :, hz].astype("float32"), horizons=np.array(HORIZONS), origins=su.te,
                            cells=su.cells, test_nodes=su.test, dep_possible=dep_possible, cal_median=cal_med, cal_mean=cal_mean, calendar_slots_fallback=fb,
                            ts=su.ts[su.te].astype("datetime64[m]"), lock_sha16=now["lock_sha16"], scaler=np.array([su.rmu, su.rsd]))
        mh = mae_by_horizon(P, Y)
        print(cid, "test MAE (factor units, mean over horizons)", round(float(np.mean([mh[h] for h in HORIZONS])), 5), flush=True)
    return 0


def missing_in_period(su, origins):
    """Nodes with at least one missing reading in the input windows of `origins` (t − 11 … t): on these input nodes the completion
    intervenes somewhere in the period; the structural bound of C0.5(a) gives them the completion support."""
    o = np.asarray(origins); lo, hi = int(o.min()) - T_IN + 1, int(o.max())
    return ~np.isfinite(su.r[lo:hi + 1]).all(0)


def summarise_replicates(obs, reps):
    """Interval, centred p-values and the sign reading from the FINITE replicates only (no regression margin: F2 reads the sign).
    Undefined if the observed value is not finite or fewer than MIN_DEFINED_FRAC of the replicates are finite."""
    reps = np.asarray(reps, dtype="float64"); fin = reps[np.isfinite(reps)]; n_undef = int(reps.size - fin.size)
    base = {"estimate": float(obs) if np.isfinite(obs) else None, "replicates_undefined": n_undef, "replicates_used": int(fin.size)}
    if not np.isfinite(obs):
        return base | {"defined": False, "undefined_reason": "observed contrast undefined (empty subset or zero denominator in a split)", "ci95": None, "p_centred": None, "p_one_sided_positive": None, "sign": "undefined"}
    if fin.size < MIN_DEFINED_FRAC * reps.size:
        return base | {"defined": False, "undefined_reason": f"only {fin.size} of {reps.size} replicates defined", "ci95": None, "p_centred": None, "p_one_sided_positive": None, "sign": "undefined"}
    lo, hi = np.percentile(fin, [2.5, 97.5]); centred = fin - fin.mean()
    return base | {"defined": True, "ci95": [float(lo), float(hi)], "p_centred": float(np.mean(np.abs(centred) >= abs(obs))),
                   "p_one_sided_positive": float(np.mean(centred >= obs)), "sign": "favourable" if lo > 0 else ("unfavourable" if hi < 0 else "inconclusive")}


PRIMARY = ("H2.1_dedicated_vs_calendar_S0", "H2.2_dynamic_benefit_S0", "H2.3_dynamic_benefit_S1", "H2.4_interaction")


def analysis(args):
    """Per city: the four contrasts of F2 (H2.1–H2.4) as paired per-split values (mean over the four horizons of the per-horizon
    MAE ratio) averaged over the five splits; secondary: static benefit at fixed dynamics, dynamic benefit on the test-hidden nodes
    whose dependency on the inputs is structurally possible / excluded (C0.5a bound at horizon 1), per-horizon values, RMSE (median and mean calendar variants). Two-way block bootstrap (grid cells × ISO
    weeks), multiplicities shared across splits and cell types, 4 000 replicates, generator default_rng([20261120, city]).
    Marginal intervals and unadjusted p-values only, PROVISIONAL: the F2 band (sup-t, twelve contrasts, level 0.98) and every
    confirmatory statement belong to the campaign-wide analysis, for which the replicates are saved."""
    gate("analysis")
    adeq = json.loads((RUNS / "e14_adequacy.json").read_text())
    if adeq["lock_sha16"] != compute_adequacy()["lock_sha16"]:
        raise PermissionError("records changed since the lock")
    excluded = set(adeq["excluded_from_adequacy_statements"])
    out = {"written": datetime.now(timezone.utc).isoformat(), "B": B_REPS, "seed": BOOT_SEED, "metric": "mean over the four horizons of the per-horizon MAE ratio, factor units, test-hidden nodes",
           "environment": environment(), "cities": {}}
    saved_reps = {}
    nh = len(HORIZONS)
    for ci, city in enumerate(CITIES):
        AE, WM, SE, cellof, weekof, RE, CAL, CALm = {}, {}, {}, {}, {}, {}, {}, {}; blocks = weeks = None
        for s in SEEDS:
            for a in ARMS:
                for r in REGIMES:
                    cid = cell_id(city, s, a, r); z = np.load(Path(latest_final(cid)["dir"]) / "test_cells.npz")
                    if str(z["lock_sha16"]) != adeq["lock_sha16"]:
                        raise PermissionError(f"test file of {cid} belongs to another lock")
                    if blocks is None:
                        blocks, weeks = np.unique(z["cells"]), np.unique(_week_index(z["ts"]))
                    P, Y = z["p"].astype("float64"), z["y"].astype("float64"); v = np.isfinite(Y)
                    AE[(s, a, r)] = np.where(v, np.abs(P - Y), 0.0); SE[(s, a, r)] = np.where(v, (P - Y) ** 2, 0.0); WM[(s, a, r)] = v.astype("float64")
                    cellof[(s, a, r)] = np.searchsorted(blocks, z["cells"]); weekof[(s, a, r)] = np.searchsorted(weeks, _week_index(z["ts"])); RE[(s, a, r)] = z["dep_possible"].astype(bool)
                    if a == "full" and r == "S0":
                        CAL[s] = np.where(v, np.abs(z["cal_median"].astype("float64")[:, None, :] - Y), 0.0); CALm[s] = np.where(v, (z["cal_mean"].astype("float64")[:, None, :] - Y) ** 2, 0.0)
        nb, nw = len(blocks), len(weeks); rng = np.random.default_rng([BOOT_SEED, ci])

        def mae_with(key, mb, mw, nodes=None, num=None):
            wn = (mb[cellof[key]][None, :] * mw[weekof[key]][:, None])
            if nodes is not None:
                wn = wn * nodes[None, :]
            wn = wn[..., None]; den = (WM[key] * wn).sum((0, 1)); nm = ((AE[key] if num is None else num) * wn).sum((0, 1))
            return {h: (float(nm[i] / den[i]) if den[i] > 0 else float("nan")) for i, h in enumerate(HORIZONS)}

        def contrasts(mb, mw):
            res = {}

            def add(name, pairs):
                vs = [contrast_value(x, y) for x, y in pairs]; res[name] = float(np.mean(vs)); res[f"{name}_by_seed"] = vs
            add(PRIMARY[0], [(mae_with((s, "full", "S0"), mb, mw, num=CAL[s]), mae_with((s, "full", "S0"), mb, mw)) for s in SEEDS])
            add(PRIMARY[1], [(mae_with((s, "nodyn", "S0"), mb, mw), mae_with((s, "full", "S0"), mb, mw)) for s in SEEDS])
            add(PRIMARY[2], [(mae_with((s, "nodyn", "S1"), mb, mw), mae_with((s, "full", "S1"), mb, mw)) for s in SEEDS])
            res[PRIMARY[3]] = res[PRIMARY[1]] - res[PRIMARY[2]]; res[f"{PRIMARY[3]}_by_seed"] = [x - y for x, y in zip(res[f"{PRIMARY[1]}_by_seed"], res[f"{PRIMARY[2]}_by_seed"])]
            for a in ARMS:
                add(f"static_benefit_{a}", [(mae_with((s, a, "S0"), mb, mw), mae_with((s, a, "S1"), mb, mw)) for s in SEEDS])
            for name, sel in (("H2.2_dynamic_benefit_S0_dependency_possible", True), ("H2.2_dynamic_benefit_S0_dependency_excluded", False)):
                add(name, [(mae_with((s, "nodyn", "S0"), mb, mw, (RE[(s, "nodyn", "S0")] == sel).astype("float64")), mae_with((s, "full", "S0"), mb, mw, (RE[(s, "full", "S0")] == sel).astype("float64"))) for s in SEEDS])
            return res
        ones = (np.ones(nb), np.ones(nw)); obs = contrasts(*ones); keys = [k for k in obs if not k.endswith("_by_seed")]
        reps = {k: np.empty(B_REPS) for k in keys}
        for b in range(B_REPS):
            mb = np.bincount(rng.integers(0, nb, nb), minlength=nb).astype("float64")
            mw = np.bincount(rng.integers(0, nw, nw), minlength=nw).astype("float64")
            cb = contrasts(mb, mw)
            for k in keys:
                reps[k][b] = cb[k]
        res = {"n_blocks": int(nb), "n_weeks": int(nw), "observed": obs}
        for k in keys:
            res[k] = summarise_replicates(obs[k], reps[k])
        # per-horizon observed values and RMSE (secondary, no bootstrap)
        ph = {}
        for s in SEEDS:
            row = {f"{a}_{r}": mae_with((s, a, r), *ones) for a in ARMS for r in REGIMES}
            row["calendar_median"] = mae_with((s, "full", "S0"), *ones, num=CAL[s])
            rm = {f"{a}_{r}": {h: float(np.sqrt(v)) for h, v in mae_with((s, a, r), *ones, num=SE[(s, a, r)]).items()} for a in ARMS for r in REGIMES}
            rm["calendar_mean"] = {h: float(np.sqrt(v)) for h, v in mae_with((s, "full", "S0"), *ones, num=CALm[s]).items()}
            ph[str(s)] = {"mae": {k: {str(h): v for h, v in d.items()} for k, d in row.items()}, "rmse": {k: {str(h): v for h, v in d.items()} for k, d in rm.items()}}
        res["per_split_per_horizon"] = ph
        res["dependency_excluded_test_hidden_share_by_seed"] = {str(s): float((~RE[(s, "full", "S0")][np.load(Path(latest_final(cell_id(city, s, "full", "S0"))["dir"]) / "test_cells.npz")["test_nodes"]]).mean()) for s in SEEDS}
        res["selected_configurations"] = {cell_id(city, s, a, r): latest_final(cell_id(city, s, a, r))["config"] for s in SEEDS for a in ARMS for r in REGIMES}
        cells_c = {cell_id(city, s, a, r) for s in SEEDS for a in ARMS for r in REGIMES}
        res["eligible_for_adequacy_statements"] = not (cells_c & excluded); res["excluded_cells"] = sorted(cells_c & excluded)
        for k in PRIMARY:
            saved_reps[f"{city}:{k}"] = reps[k]
        out["cities"][city] = res
    np.savez_compressed(RUNS / "e14_analysis_replicates.npz", **saved_reps, B=B_REPS, seed=BOOT_SEED, lock_sha16=adeq["lock_sha16"])
    out["replicates_file"] = {"file": str(RUNS / "e14_analysis_replicates.npz"), "sha16": p4b.sha256(RUNS / "e14_analysis_replicates.npz", 16),
                              "contents": "4 000 replicates of the twelve F2 contrasts (3 cities × H2.1–H2.4), for the campaign-wide sup-t band at 0.98"}
    out["confirmatory"] = False
    out["statement"] = ("PROVISIONAL: marginal 95 % intervals and unadjusted p-values only; the F2 band (sup-t over the twelve contrasts at level 0.98) and every "
                        "confirmatory sign statement are produced by the campaign-wide analysis from the saved replicates")
    out["lock_sha16"] = adeq["lock_sha16"]
    (RUNS / "e14_analysis.json").write_text(json.dumps(out, indent=1, default=float))
    for c in CITIES:
        for k in PRIMARY + ("static_benefit_full", "static_benefit_nodyn", "H2.2_dynamic_benefit_S0_dependency_possible", "H2.2_dynamic_benefit_S0_dependency_excluded"):
            r = out["cities"][c][k]
            print(f"{c:9s} {k:36s} " + (f"{r['estimate']:7.3f}  CI {r['ci95'][0]:7.3f} {r['ci95'][1]:7.3f}  p {r['p_centred']:.4f}  {r['sign']} (marginal, provisional)" if r["defined"] else f"undefined ({r['undefined_reason']})"))
    print("statement:", out["statement"])
    return 0


# ---------------------------------------------------------------- C0.5(a): structural dependency (upper bound) ---

def _mass_summary(den):
    den = np.asarray(den, dtype="float64")
    return {"n": int(den.size), "median": float(np.median(den)), "p25": float(np.percentile(den, 25)), "p75": float(np.percentile(den, 75)),
            "share_gt_0.1": float((den > 0.1).mean()), "share_gt_0.01": float((den > 0.01).mean()),
            "share_tiny_0_to_1e-6": float(((den > 0) & (den <= 1e-6)).mean()), "share_exact_zero": float((den == 0).mean())}


def _rows_summary(D, nodes):
    """Share of nodes with a non-empty dependency row and the row sizes (number of input nodes a target can depend on)."""
    sizes = D[nodes].sum(1)
    return {"n": int(nodes.sum()), "share_nonempty": float((sizes > 0).mean()) if nodes.any() else None,
            "row_size": {"min": int(sizes.min()), "median": float(np.median(sizes)), "max": int(sizes.max())} if nodes.any() else None}


def struct_measure(su, draws=20):
    """C0.5(a) for one (city, seed): boolean dependency rows D_h (inputs = observed nodes) for the validation-hidden and
    test-hidden nodes, and for the targets of `draws` training masks (inputs = the mask's input cells); hop distance to the
    nearest input node on A ∪ Aᵀ of the method's graph with the shares within the declared radii; the reference linear mass
    Σ_{k≤14}(A_q)^k over the input nodes (I3-style summaries, clearly distinct); and, for the comparison with the I3 record,
    the hop-distance counts of the validation-hidden nodes on the E9 kernel adjacency."""
    A = su.A_method
    rows_v, _ = mga.dependency_rows(A, su.obs, T_IN, HSTEPS, 2, completed=missing_in_period(su, su.va))
    rows_t, _ = mga.dependency_rows(A, su.obs, T_IN, HSTEPS, 2, completed=missing_in_period(su, su.te))
    miss_tr = missing_in_period(su, su.tr)
    hd = mga.hop_distance_undirected(A, su.obs)
    mass, _ = mga.reference_mass(su.Aq.cpu().numpy(), su.obs, REF_HOPS)
    rec = {"observed": int(su.obs.sum()), "validation_hidden": int(su.val.sum()), "test_hidden": int(su.test.sum()), "sigma_m": float(su.sigma_method),
           "graph": dict(su.graph_stats),
           "dependency_bound": "upper bound: an empty row excludes a dependence on the inputs' readings, a non-empty row does not demonstrate one (mogernn_adapter.dependency_rows)",
           "input_nodes_with_missing_readings": {"validation_period": int((missing_in_period(su, su.va) & su.obs).sum()), "test_period": int((missing_in_period(su, su.te) & su.obs).sum()), "training_period": int((miss_tr & su.obs).sum())},
           "dependency": {str(h + 1): {"validation_hidden": _rows_summary(rows_v[h], su.val), "test_hidden": _rows_summary(rows_t[h], su.test)} for h in range(HSTEPS)},
           "hop_distance_method_graph": {"validation_hidden": {str(k): int(v) for k, v in zip(*np.unique(hd[su.val], return_counts=True))},
                                         "test_hidden": {str(k): int(v) for k, v in zip(*np.unique(hd[su.test], return_counts=True))},
                                         "share_within_radius": {str(rd): {"validation_hidden": float(((hd[su.val] >= 0) & (hd[su.val] <= rd)).mean()),
                                                                           "test_hidden": float(((hd[su.test] >= 0) & (hd[su.test] <= rd)).mean())} for rd in RADII}},
           f"reference_mass_{REF_HOPS}hops": {"validation_hidden": _mass_summary(mass[su.val]), "test_hidden": _mass_summary(mass[su.test]), "observed_self": _mass_summary(mass[su.obs])}}
    r = p4b.rng(su.seed, p4b.K_MASKS); tr_rows = {str(h + 1): [] for h in range(HSTEPS)}; tr_mass = []
    for _ in range(draws):
        inp, tgt, _ = su.batch_mask(r); rows_i, _ = mga.dependency_rows(A, inp, T_IN, HSTEPS, 2, completed=miss_tr)
        for h in range(HSTEPS):
            tr_rows[str(h + 1)].append(rows_i[h][tgt].sum(1))
        tr_mass.append(mga.reference_mass(su.Aq.cpu().numpy(), inp, REF_HOPS)[0][tgt])
    for h in range(HSTEPS):
        sizes = np.concatenate(tr_rows[str(h + 1)])
        rec["dependency"][str(h + 1)]["training_targets"] = {"n": int(sizes.size), "share_nonempty": float((sizes > 0).mean()),
                                                              "row_size": {"min": int(sizes.min()), "median": float(np.median(sizes)), "max": int(sizes.max())}}
    rec[f"reference_mass_{REF_HOPS}hops"]["training_targets"] = _mass_summary(np.concatenate(tr_mass))
    Ak, _ = p4b.kernel_adjacency(su.al["graph"], su.kept); hk = e13b_hop_dist(np.asarray(Ak, dtype="float64"), su.obs)
    rec["hop_distance_kernel_adjacency_validation_hidden"] = {str(k): int(v) for k, v in zip(*np.unique(hk[su.val], return_counts=True))}
    return rec


def e13b_hop_dist(A, inp):
    """BFS along the propagation direction of the kernel adjacency (A[k, m] > 0: m feeds k), as e13_a0_struct.py."""
    n = len(A); fwd = [np.flatnonzero(A[:, m] > 0) for m in range(n)]; d = np.full(n, -1); q = deque()
    for m in np.flatnonzero(inp):
        d[m] = 0; q.append(m)
    while q:
        m = q.popleft()
        for k in fwd[m]:
            if d[k] < 0:
                d[k] = d[m] + 1; q.append(k)
    return d


def struct(args):
    """`struct`: C0.5(a) for all 15 (city, seed), no trained state; the node-set counts and the kernel hop distances are compared
    with `paper4/runs/e13_a0_struct.json` (the shared quantities); the method's graph is new, its measures are reported."""
    ref_p = RUNS / "e13_a0_struct.json"
    if not ref_p.exists():
        print(f"{ref_p} missing: the I3 reference is required"); return 1
    ref = json.loads(ref_p.read_text()); agree = True
    out = {"protocol": "E14 C0.5(a)", "radii": RADII, "reference_hops": REF_HOPS, "draws": 20, "layers": 2, "T_in": T_IN, "H": HSTEPS, "cities": {},
           "method": mga.dependency_rows.__doc__, "completion_support": mga.completion_support.__doc__, "cell_support": mga.cell_support.__doc__,
           "reference": {"file": str(ref_p), "sha16": p4b.sha256(ref_p, 16), "committed_unchanged": git_committed_unchanged(ref_p.relative_to(ROOT))},
           "environment": environment(), "written": None}
    for city in CITIES:
        out["cities"][city] = {}
        for s in SEEDS:
            su = SetupE14(city, s, "S0", device="cpu"); m = struct_measure(su); out["cities"][city][str(s)] = m
            r = ref["cities"][city]["seeds"][str(s)]
            same = all(r[k] == m[k] for k in ("observed", "validation_hidden", "test_hidden")) and r["hop_distance_validation_hidden"] == m["hop_distance_kernel_adjacency_validation_hidden"]
            agree &= same
            d1 = m["dependency"]["1"]
            print(f"{city} seed {s}: sigma {m['sigma_m']:.0f} m, pairs {m['graph']['nonzero_pairs']}, density {m['graph']['density']:.3f}, isolated {m['graph']['isolated_nodes']}; dependency possible (non-empty row, bound) at h=1: "
                  f"val {d1['validation_hidden']['share_nonempty']:.3f} test {d1['test_hidden']['share_nonempty']:.3f} train {d1['training_targets']['share_nonempty']:.3f}; "
                  f"within 14 hops val {m['hop_distance_method_graph']['share_within_radius']['14']['validation_hidden']:.3f}; shared quantities "
                  f"{'agree' if same else 'DIFFER'} with e13_a0_struct.json", flush=True)
    out["agrees_with_I3_shared_quantities"] = agree; out["written"] = datetime.now(timezone.utc).isoformat()
    (RUNS / "e14_struct.json").write_text(json.dumps(out, indent=1)); print("->", RUNS / "e14_struct.json", p4b.sha256(RUNS / "e14_struct.json", 16))
    return 0 if agree else 1


# ---------------------------------------------------------------- preflight (no update) -------------------

def _original_model(repo):
    """Import the original `model.MoGERNN.Model` from a local checkout of the reference repository; returns the class, the
    checkout's commit and the fingerprints of the six source files."""
    if not repo:
        raise FileNotFoundError("path of the original MoGERNN checkout not given (--mogernn-repo or MOGERNN_REPO)")
    repo = Path(repo).resolve()
    files = ["model/MoGERNN.py", "layers/DCRNNCell.py", "layers/GRUCell.py", "layers/agg.py", "layers/gnn.py", "args.py"]
    shas = {f: p4b.sha256(repo / f, 16) for f in files}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=repo).stdout.strip()
    sys.path.insert(0, str(repo))
    import importlib
    Model = importlib.import_module("model.MoGERNN").Model
    return Model, commit, shas


def _synthetic_graph_batch(N=40, B=4, T=12, H=8, seed=5, isolated=7, unknown=(3, 11)):
    r = np.random.default_rng(seed)
    W = (r.random((N, N)) * (r.random((N, N)) < 0.15)).astype("float32"); np.fill_diagonal(W, 0.0)
    W[isolated, :] = 0.0; W[:, isolated] = 0.0
    x = r.normal(size=(B, T, N, 1)).astype("float32"); x[:, :, list(unknown), :] = 0.0; x[0, 2, 5, 0] = 0.0; x[1, 7, 9, 0] = 0.0
    xd = r.normal(size=(B, H, N, 1)).astype("float32")
    return torch.tensor(W), torch.tensor(x), torch.tensor(xd)


def _preflight_record():
    log_p = RUNS / "e14_preflight.log"
    if not log_p.exists():
        raise PermissionError("e14_preflight.log missing: run and review the deterministic preflight first")
    txt = log_p.read_text()
    if "PREFLIGHT: 0 failure(s)" not in txt:
        raise PermissionError("the deterministic preflight did not pass (or its log is incomplete)")
    me = environment()["code_sha16"]
    for name, sha in me.items():
        if f"{name} {sha}" not in txt:
            raise PermissionError(f"the preflight log was produced with another {name} ({sha} not in the log)")
    return {"file": str(log_p), "sha16": p4b.sha256(log_p, 16)}


def _require_cuda(su):
    if not torch.cuda.is_available() or su.dev.type != "cuda":
        raise PermissionError(f"E14pre.md requires CUDA (Spark); device is {su.dev} (no silent fallback)")


def preflight(args):
    """Deterministic preflight of E14 (no update of any model): E11/E9 set controls, C0.4, the adapter's equivalence with the
    original on the original configuration, the mask-driven checks of C0.3, scaler and graph invariances, C0.5 static check and
    C0.5(a) on all 15 (city, seed), derived block, run-dir and guard checks. C0.1 and the benchmark run under E14pre.md (`pre`)."""
    RUNS.mkdir(parents=True, exist_ok=True); E14.mkdir(exist_ok=True)
    log = Log(RUNS / "e14_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E14 preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty}) — tag {git_describe()!r}")
    cs = environment()["code_sha16"]
    log("code " + " · ".join(f"{k} {v}" for k, v in cs.items()) + f" · ADAPTER_SPEC_E14.md {p4b.sha256(SPEC, 16) if SPEC.exists() else None} · torch {torch.__version__}")
    log.check("const", "T_IN = 12 and horizons (1, 2, 4, 8) within the 8 decoder steps", T_IN == 12 and tuple(HORIZONS) == (1, 2, 4, 8) and max(HORIZONS) == HSTEPS)
    log.check("spec", "ADAPTER_SPEC_E14.md present in protocol/paper4/rafforzamento/", SPEC.exists())
    bad, g_ok = 0, True
    for city in CITIES:
        al = p4b.align_graph(city, p4b.CITY[city]["roads"]); g_ok &= nx.is_connected(al["graph"])
        cells = p4b.grid_cells(al["coords"], e9.GRID[city])
        for s in SEEDS:
            lab = p4b.node_sets(cells, s, targets=tuple(e9.targets(F))); n = np.bincount(lab, minlength=3)
            tb = len(np.unique(cells[lab == 2]))
            bad += int((n == 0).any() or np.abs(n / n.sum() - np.array(e9.targets(F))).max() > 0.15 or tb < e9.MIN_TEST_BLOCKS)
    log.check("graph", "road graph connected after alignment in the three cities", g_ok)
    log.check("sets", "f = 20 %: no empty set, shares within ±15, ≥ 8 test blocks (15 pairs)", bad == 0)
    fm = {k: p4b.sha256(Path(v), 16) for k, v in p4b.CITY["madrid"].items()}; fl = {k: p4b.sha256(Path(v), 16) for k, v in p4b.CITY["london"].items()}
    log.check("C0.4", "London data files differ from Madrid's", all(fm[k] != fl[k] for k in fm), json.dumps({"madrid": fm, "london": fl}))
    # ---- equivalence with the original (original configuration) --------------------------------------------
    try:
        Model, commit, shas = _original_model(getattr(args, "mogernn_repo", None) or os.environ.get("MOGERNN_REPO"))
        log(f"[INFO] original checkout commit {commit} (reference {mga.ORIGINAL_COMMIT}); files {json.dumps(shas)}")
        log.check("eq-commit", "the original checkout is at the reference commit", commit == mga.ORIGINAL_COMMIT, commit)
        import types as _types
        cfg = _types.SimpleNamespace(input_len=12, pred_len=8, look_back=0, d_model=64, e_layers=2, k_hop=1, enc_in=1, num_experts=5, num_used_experts=3,
                                     mean_expert=True, weight_expert=True, max_expert=True, min_expert=True, diffusion_expert=True)
        torch.manual_seed(0); orig = Model(cfg); mine = mga.build_original(8, 12); mine.load_state_dict(orig.state_dict(), strict=True)
        log(f"[INFO] parameters: original configuration (T 12, H 8) {sum(p.numel() for p in orig.parameters())}; adapter S0 {mga.build('S0').parameter_count()}, S1 {mga.build('S1').parameter_count()}")
        W, x, xd = _synthetic_graph_batch()
        diffs = {}
        for label, train_mode, epoch in (("eval", False, 40), ("train-tf0", True, 40), ("train-tf1", True, 0)):
            orig.train(train_mode); mine.train(train_mode)
            with torch.no_grad():
                o1 = orig(W, x, None, None, xd, epoch); o2 = mine.forward_original(W, x, xd, epoch)
            diffs[label] = float((o1 - o2).abs().max())
        log.check("eq-forward", "adapter (original mode) forward equals the original Model within 1e-6: eval, train with teacher forcing ratio 0 (epoch 40) and 1 (epoch 0)",
                  all(v <= 1e-6 for v in diffs.values()), json.dumps(diffs))
        mine.eval()
        with torch.no_grad():
            full = mine.forward_original(W, x, xd, 40)
            keep = [i for i in range(W.shape[0]) if i != 7]
            red = mine.forward_original(W[keep][:, keep], x[:, :, keep], xd[:, :, keep], 40)
            d_iso = float((full[:, :, keep] - red).abs().max())
            perm = torch.tensor(np.random.default_rng(3).permutation(W.shape[0]))
            pp = mine.forward_original(W[perm][:, perm], x[:, :, perm], xd[:, :, perm], 40)
            d_perm = float((full[:, :, perm] - pp).abs().max())
            sd0 = {k: v.clone() for k, v in mine.state_dict().items()}; again = mine.forward_original(W, x, xd, 40)
            same_state = all(torch.equal(sd0[k], v) for k, v in mine.state_dict().items()) and torch.equal(full, again)
        log.check("eq-isolated", "removing an isolated node leaves the other nodes' outputs identical (within 1e-5)", d_iso <= 1e-5, f"max |diff| {d_iso:.2e}")
        log.check("eq-perm", "a consistent permutation of nodes permutes the outputs (within 1e-5)", d_perm <= 1e-5, f"max |diff| {d_perm:.2e}")
        log.check("eq-state", "evaluation leaves the state unchanged and is repeatable", same_state)
    except Exception as e:  # noqa: BLE001
        log.check("eq-forward", f"equivalence with the original could not be asserted: {e}", False)
    # ---- Madrid seed 0: C0.3 and invariances ---------------------------------------------------------------
    sus = {r: SetupE14("madrid", 0, r) for r in REGIMES}; su = sus["S0"]
    whole = all(len(np.unique(su.lab[su.cells == c_])) == 1 for c_ in np.unique(su.cells))
    log.check("1a", "node sets disjoint, non-empty, whole cells", whole and su.obs.any() and su.val.any() and su.test.any())
    log.check("rw", "cached random walks equal the ones recomputed from the method's graph (bit for bit)",
              bool(torch.equal(su.Aq, mga.random_walk_matrix(su.At)) and torch.equal(su.Ah, mga.random_walk_matrix(su.At.T))))
    log(f"[INFO] factor scaler madrid s0: mean {su.rmu:.4f} sd {su.rsd:.4f}")
    for city in CITIES:
        al_ = p4b.align_graph(city, p4b.CITY[city]["roads"]); _, _, _, gs = mga.method_graph(al_["graph"], al_["kept"])
        log(f"[INFO] method graph {city}: road radius {gs['radius_m']:.0f} m, sigma {gs['sigma_m']:.0f} m, effective radius {gs['effective_radius_m']:.0f} m, longest surviving edge {gs['max_edge_m']:.0f} m, "
            f"density {gs['density']:.3f}, degree median {gs['degree_median']:.0f} min {gs['degree_min']}, isolated nodes {gs['isolated_nodes']} of {gs['nodes']}")
    log.check("graph-radius", "the method's graph respects the declared road radius (no surviving edge longer than it) in the three cities",
              all(mga.method_graph(p4b.align_graph(c, p4b.CITY[c]["roads"])["graph"], p4b.align_graph(c, p4b.CITY[c]["roads"])["kept"])[3]["max_edge_m"] <= mga.ROAD_RADIUS_M for c in CITIES))
    hidden = torch.as_tensor(~su.obs, device=su.dev); r = p4b.rng(0, p4b.K_MASKS); bm = bt_ = 0; missing = 0; mono = True; binary = True
    for i in range(100):
        inp, tgt, _ = su.batch_mask(r); bm += int((inp & ~su.obs).sum() + (tgt & ~su.obs).sum())
        if i < 20:
            b = su.batch(su.tr[32 * i:32 * i + 32], inp, tgt, "full")
            bt_ += int(b["r_in"][:, :, hidden].abs().sum().item() > 0) + int(b["m_in"][:, :, hidden].abs().sum().item() > 0) + int(b["node_in"][hidden].abs().sum().item() > 0) + int(b["m_y"][:, :, hidden].abs().sum().item() > 0)
            missing += int(((b["m_in"][..., 0] == 0) & (b["node_in"].view(1, 1, -1) == 1)).sum().item())
            mono &= bool((b["m_in"][..., 0] <= b["node_in"].view(1, 1, -1)).all())
            binary &= all(bool(((t == 0) | (t == 1)).all()) for t in (b["m_in"], b["node_in"], b["m_y"]))
    log.check("1b", "no hidden index in input mask or loss of 100 batches", bm == 0)
    log.check("1c", "hidden nodes zero in r_in, m_in, node_in and the target mask of 20 batches", bt_ == 0)
    log.check("C0.3-notions", "three notions distinct and consistent: m_in ≤ node_in (missing reading only on admitted nodes), masks binary", mono and binary,
              f"entries with node_in = 1 and m_in = 0 (missing readings) over 20 batches: {missing}")
    allo = np.concatenate([su.tr, su.va, su.te]); gap = max(HORIZONS) + T_IN - 1
    log.check("2a", "every origin admissible", all(cadence_ok(su.ts, int(t)) for t in allo))
    log.check("2b", "no target of a period overlaps an input of the next", bool(su.tr.max() + gap < su.va.min() and su.va.max() + gap < su.te.min()))
    bt = su.tr[100:132]; inp, tgt, _ = su.batch_mask(p4b.rng(0, 99)); b0 = su.batch(bt, inp, tgt, "full")
    sv = {k: getattr(su, k).clone() for k in ("RZ", "RV")}; tmax = int(bt.max()); gen = torch.Generator(device="cpu").manual_seed(7)
    for k in sv:
        t_ = getattr(su, k); t_[tmax + 1:] = torch.randn(t_[tmax + 1:].shape, generator=gen).to(su.dev)
    b1 = su.batch(bt, inp, tgt, "full")
    for k, v in sv.items():
        setattr(su, k, v)
    log.check("2c", "causality: noise after the origin leaves r_in, m_in, cal_in identical to the bit", all(torch.equal(b0[k], b1[k]) for k in ("r_in", "m_in", "cal_in")))
    # independent validity: m_in equals node_in × isfinite(r) over the window
    idx = np.asarray(bt)[:, None] - np.arange(T_IN)[::-1][None, :]; v_ind = (np.isfinite(su.r)[idx] * inp[None, None, :].astype("float32"))
    log.check("C0.3-mask", "m_in equals node_in × validity of the series recomputed independently", bool(np.array_equal(b0["m_in"][..., 0].cpu().numpy(), v_ind.astype("float32"))))
    pert_all = _perturbed_copy(su, np.random.default_rng(11), perturb_val_labels=True)
    log.check("2d", "noise on hidden nodes (all) leaves the factor scaler, the coordinates' standardisation and the method's graph identical",
              [pert_all.rmu, pert_all.rsd] == [su.rmu, su.rsd] and np.array_equal(pert_all.A_method, su.A_method) and torch.equal(pert_all.XY, su.XY))
    su_inj = SetupE14("madrid", 0, "S0"); A_before = su_inj.A_method.copy(); zr = np.random.default_rng(13).random(su_inj.r.shape).astype("float32")
    su_inj.inject(zr, zr, zr, np.ones_like(su_inj.C)); log.check("graph-topology", "the method's graph is unchanged by a replacement of every series (built from topology only)", np.array_equal(A_before, su_inj.A_method))
    pert = _perturbed_copy(su, np.random.default_rng(12), perturb_val_labels=False)
    bp = pert.batch(bt, inp, tgt, "full")
    log.check("C0.1-batch", "noise on hidden nodes' readings (test labels replaced, validation labels kept): every input tensor, the target mask and the masked targets of a training batch identical to the bit",
              all(torch.equal(b0[k], bp[k]) for k in ("r_in", "m_in", "node_in", "cal_in", "cal_out", "m_y")) and torch.equal(b0["y_z"] * b0["m_y"], bp["y_z"] * bp["m_y"]))
    # C0.3: nodyn vs full; S1 vs S0; coordinates; no inference from values
    bn = su.batch(bt, inp, tgt, "nodyn"); va64 = su.va[:64]; bv = su.batch(va64, su.obs, su.val, "full"); bvn = su.batch(va64, su.obs, su.val, "nodyn")
    same_rest = all(teq(b0[k], bn[k]) and teq(bv[k], bvn[k]) for k in ("m_in", "node_in", "cal_in", "cal_out", "y_z", "y_raw", "m_y"))
    log.check("C0.3-nodyn", "S0-nodyn: r_in exactly zero in a training and a validation batch; every other tensor identical to S0-full's",
              bool(bn["r_in"].abs().sum() == 0 and bvn["r_in"].abs().sum() == 0 and same_rest and bn["xy"] is None))
    s1 = sus["S1"]; b1s = s1.batch(bt, inp, tgt, "full"); bv1 = s1.batch(va64, su.obs, su.val, "full")
    log.check("C0.3-S1", "S1 cells differ from S0 cells only in the coordinate channels (xy present in S1, None in S0; every other tensor identical)",
              all(teq(b0[k], b1s[k]) and teq(bv[k], bv1[k]) for k in b0 if k != "xy") and b0["xy"] is None and b1s["xy"] is not None and b1s["xy"].shape == (su.K, 2))
    obs_t = torch.as_tensor(su.obs, device=su.dev); pc = copy.copy(s1); zxy = s1.XY.clone(); zxy[~obs_t] += 3.0; pc.XY = zxy; bpc = pc.batch(bt, inp, tgt, "full")
    log.check("C0.3-coords", "perturbing hidden nodes' coordinates leaves the observed nodes' coordinates and every other channel identical; hidden coordinates are the true ones otherwise",
              bool(torch.equal(bpc["xy"][obs_t], b1s["xy"][obs_t]) and all(teq(bpc[k], b1s[k]) for k in b1s if k != "xy") and torch.equal(s1.XY, torch.tensor(((np.asarray(s1.al["coords"]) - np.asarray(s1.al["coords"])[s1.obs].mean(0)) / (np.asarray(s1.al["coords"])[s1.obs].std(0) + 1e-6)).astype("float32"), device=s1.dev))))
    non_inp = int(np.flatnonzero(tgt)[0]); sc = copy.copy(su); rz = su.RZ.clone(); rz[:, non_inp] = 0.7; sc.RZ = rz; bsc = sc.batch(bt, inp, tgt, "full")
    log.check("C0.3-values", "a non-input node whose series is set to a non-zero constant yields identical inputs and masks (no inference of presence from values)",
              all(torch.equal(b0[k], bsc[k]) for k in ("r_in", "m_in", "node_in", "cal_in", "cal_out", "m_y")))
    # completion rule on the real batch and on a forced exact zero
    net0 = mga.build("S0", HSTEPS, T_IN).to(su.dev); net0.eval()
    with torch.no_grad():
        r_c, comb = net0.complete_masked(su.At, b0["r_in"], b0["m_in"], b0["node_in"])
        m1 = b0["m_in"] > 0
        rule = bool(torch.equal(r_c[m1], b0["r_in"][m1]) and torch.equal(r_c[~m1], comb[~m1]))
        j = int(np.flatnonzero(inp)[0]); rz0 = b0["r_in"].clone(); rz0[0, 3, j, 0] = 0.0; mi0 = b0["m_in"].clone(); mi0[0, 3, j, 0] = 1.0
        r_c0, comb0 = net0.complete_masked(su.At, rz0, mi0, b0["node_in"])
        zero_kept = bool(r_c0[0, 3, j, 0] == 0.0 and comb0.abs().sum() > 0)
        out0, _ = net0(b0["r_in"], b0["m_in"], b0["node_in"], b0["cal_in"], b0["cal_out"], su.Aq, su.Ah, su.At, None)
        net1 = mga.build("S1", HSTEPS, T_IN).to(su.dev); net1.eval(); out1, _ = net1(b1s["r_in"], b1s["m_in"], b1s["node_in"], b1s["cal_in"], b1s["cal_out"], s1.Aq, s1.Ah, s1.At, b1s["xy"])
    log.check("C0.3-completion", "mask-driven completion: entries with m_in = 1 unchanged, entries with m_in = 0 replaced by the experts' combination; a valid value exactly 0 is kept", rule and zero_kept)
    log.check("ch", f"encoder input channels: S0 {1 + mga.exo_channels('S0')}, S1 {1 + mga.exo_channels('S1')}; forward shapes (B, 8, K, 1)",
              tuple(out0.shape) == (32, HSTEPS, su.K, 1) and tuple(out1.shape) == (32, HSTEPS, su.K, 1) and su.c_in == 7 and s1.c_in == 9)
    log.check("fp", "node sets, origins, factor scaler, method graph and coordinates identical across the four cell types", sus["S0"].fingerprints() == sus["S1"].fingerprints())
    # calendar baseline sanity
    tabs = calendar_tables(su); log(f"[INFO] calendar baseline madrid s0: {tabs['slots_fallback']} of 672 slots on the global fallback; global median {tabs['global_median']:.4f}")
    log.check("cal", "calendar table has 672 slots and uses observed-training values only (identical under the perturbation of hidden nodes)",
              len(tabs["median"]) == 672 and np.array_equal(calendar_tables(pert_all)["median"], tabs["median"]))
    src = Path(__file__).read_text(); body = src.split("def _dev_run(")[1].split("def final_up_to_date(")[0]
    log.check("C0.5-static", "no reference to test origins or test nodes in the development, extension and final code", "su.te" not in body and "su.test" not in body)
    log.check("derived", "the derived block equals the mechanical derivation from e13.py (substitution table)", derived_block_matches())
    try:
        rc = struct(argparse.Namespace()); log.check("C0.5a", "structural dependency bound computed on all 15 (city, seed); shared quantities agree with e13_a0_struct.json", rc == 0)
    except Exception as e:  # noqa: BLE001
        log.check("C0.5a", f"structural dependency bound failed: {e}", False)
    cfg_ = {"preflight": "E14 run-dir test", "stamp": datetime.now(timezone.utc).isoformat()}
    p4b.run_dir(RUNS / "e14_preflight_dirs", cfg_)
    try:
        p4b.run_dir(RUNS / "e14_preflight_dirs", cfg_); blocked = False
    except FileExistsError:
        blocked = True
    log.check("9", "an existing run folder blocks the launch", blocked)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test metrics refused while the E14 signature line is blank", guard)
    try:
        gate("dev"); gated = False
    except PermissionError as e:
        gated = True; log(f"[INFO] gate refuses dev now: {e}")
    log.check("gate", "the launch gate refuses `dev` before signature / tag / budget / C0.2", gated)
    log(f"PREFLIGHT: {log.fail} failure(s) — no model update was performed"); log.save()
    return 0 if log.fail == 0 else 1


def pre(args):
    """E14pre.md: the authorised preflight updates on Spark (CUDA) — C0.1 (eight trajectories of 50 updates: the four cell types,
    original and perturbed, compared per cell type bit for bit) and the benchmark (four cell types × 3 repetitions × 60 updates,
    seconds per update as (t60 − t10)/50, seconds per validation as the median validation time, memory peak). Refuses unless
    E14pre.md is signed, its tag reachable, the tree clean and the deterministic preflight recorded with these fingerprints."""
    pre_tag = _git("describe", "--tags", "--abbrev=0", "--match", "paper4-E14pre-*").stdout.strip()
    if not pre_tag:
        raise PermissionError("no E14pre tag reachable from HEAD")
    frozen_now = [p for p in FROZEN_PATHS if p != "paper4/runs/e14_grid.json"]
    if _git("diff", "--quiet", pre_tag, "HEAD", "--", *frozen_now, "protocol/paper4/E14pre.md").returncode != 0 or not git_clean():
        raise PermissionError("frozen files, E14pre.md or the working tree differ from the E14pre tag")
    p4b.require_signed(PREPRE)
    path = RUNS / "e14_pre.json"
    if path.exists():
        st = json.loads(path.read_text()).get("status", "complete")
        raise FileExistsError(f"{path} exists (status {st!r}): E14-pre is recorded once; an incomplete attempt stays identifiable")
    pf = _preflight_record()
    sus = {r: SetupE14("madrid", 0, r) for r in REGIMES}; _require_cuda(sus["S0"])
    out = {"protocol": "E14pre", "status": "started", "tag": pre_tag, "started": datetime.now(timezone.utc).isoformat(), "C0.1": {}, "benchmark": {}, "updates": 0,
           "preflight": pf, "prereg_sha16": {"E14pre.md": p4b.sha256(PREPRE, 16), "E14.md": p4b.sha256(PREREG, 16), "ADAPTER_SPEC_E14.md": p4b.sha256(SPEC, 16)}, "device": str(sus["S0"].dev),
           "gpu": torch.cuda.get_device_name(0), "environment": environment(), "parameters": {r: mga.build(r).parameter_count() for r in REGIMES}}
    path.write_text(json.dumps(out, indent=1))
    for r in REGIMES:
        su = sus[r]; pert = _perturbed_copy(su, np.random.default_rng(12), perturb_val_labels=False)
        for a in ARMS:
            ct = f"{r}-{a}"; out["status"] = f"incomplete: C0.1 {ct}"; path.write_text(json.dumps(out, indent=1))
            o0 = train_e14(su, a, su.A_method, 50, CONFIGS_FULL["C1"], p4b.K_INIT, ck_every=50, save_states=True, keep_losses=True)
            o1 = train_e14(pert, a, pert.A_method, 50, CONFIGS_FULL["C1"], p4b.K_INIT, ck_every=50, save_states=True, keep_losses=True); out["updates"] += 100
            same_loss = o0["losses"] == o1["losses"]; same_par = all(torch.equal(o0["states"][50][k], o1["states"][50][k]) for k in o0["states"][50])
            Pa, _ = predict_e14(o0["net"], su, su.va[:64], su.obs, su.val, a); Pb, _ = predict_e14(o1["net"], pert, su.va[:64], su.obs, su.val, a)
            same_pred = bool(np.array_equal(Pa, Pb)); same_setup = [pert.rmu, pert.rsd] == [su.rmu, su.rsd] and np.array_equal(pert.A_method, su.A_method)
            out["C0.1"][ct] = {"same_losses": same_loss, "same_parameters": same_par, "same_validation_predictions": same_pred, "same_scaler_and_graph": same_setup,
                               "pass": same_loss and same_par and same_pred and same_setup, "hidden_in_batches": o0["hidden_in_batches"] + o1["hidden_in_batches"]}
            print(f"C0.1 {ct}: losses {same_loss} parameters {same_par} predictions {same_pred} scaler/graph {same_setup}"); path.write_text(json.dumps(out, indent=1))
    for r in REGIMES:
        su = sus[r]
        for a in ARMS:
            ct = f"{r}-{a}"; spu, spu_net, spv, mem = [], [], [], []; out["status"] = f"incomplete: benchmark {ct}"; path.write_text(json.dumps(out, indent=1))
            finals = []
            for rep in range(3):
                torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize()
                o = train_e14(su, a, su.A_method, 60, CONFIGS_FULL["C1"], p4b.K_INIT, ck_every=10, save_states=True); torch.cuda.synchronize(); out["updates"] += 60
                t = {d["update"]: d["seconds"] for d in o["trajectory"]}; vt = {d["update"]: d["val_seconds"] for d in o["trajectory"]}
                spu.append((t[60] - t[10]) / 50); spu_net.append((t[60] - t[10] - sum(vt[u] for u in range(20, 61, 10))) / 50); finals.append(o["states"][60])
                spv.append(float(np.median([d["val_seconds"] for d in o["trajectory"]]))); mem.append(int(torch.cuda.max_memory_allocated()))
                dmax = max(float((finals[0][k].float() - finals[-1][k].float()).abs().max()) for k in finals[0]) if len(finals) > 1 else 0.0
                out["benchmark"][ct] = {"seconds_per_update_gross": spu, "seconds_per_update_gross_median": float(np.median(spu)),
                                        "seconds_per_update_net": spu_net, "seconds_per_update_net_median": float(np.median(spu_net)), "seconds_per_validation": spv,
                                        "seconds_per_validation_median": float(np.median(spv)), "memory_peak_bytes": mem, "device": str(su.dev),
                                        "identical_repetitions_max_abs_param_diff": dmax, "identical_repetitions_bitwise": dmax == 0.0}
                path.write_text(json.dumps(out, indent=1))
            print(f"benchmark {ct}: s/update net of validations {[round(v, 4) for v in spu_net]} median {np.median(spu_net):.4f} (gross {np.median(spu):.4f}); s/validation median {np.median(spv):.2f}; peak {max(mem) / 2 ** 30:.2f} GiB; "
                  f"identical repetitions max |Δ parameter| {out['benchmark'][ct]['identical_repetitions_max_abs_param_diff']:.3e}")
    out["c0_1_pass"] = all(v["pass"] for v in out["C0.1"].values())
    out["status"] = "complete"; out["load_avg"] = list(os.getloadavg()); out["written"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(out, indent=1)); print("->", path, p4b.sha256(path, 16), "C0.1", "passed" if out["c0_1_pass"] else "FAILED: E14 is not signed, no budget decision")
    return 0 if out["c0_1_pass"] else 1


def main():
    ap = argparse.ArgumentParser(description="E14 — C0 controls and C1 (MoGERNN adapter, cell types S0/S1 × full/nodyn)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    pf = sp.add_parser("preflight"); pf.add_argument("--mogernn-repo", default=None, help="local checkout of the original MoGERNN (or env MOGERNN_REPO)")
    for n in ("pre", "struct", "c0-synth", "adequacy", "test", "analysis"):
        sp.add_parser(n)
    se = sp.add_parser("sensitivity"); se.add_argument("--origins", type=int, default=4)
    dd = sp.add_parser("diag-dev"); dd.add_argument("--seed", type=int, required=True); dd.add_argument("--out", required=True)
    acc = sp.add_parser("c0-accept"); acc.add_argument("--by", required=True); acc.add_argument("--note-commit", required=True)
    bu = sp.add_parser("budget"); bu.add_argument("--h-cal", type=float, required=True, help="Spark hours available for E14, 20 %% reserve included"); bu.add_argument("--by", required=True)
    for n in ("dev", "final"):
        q = sp.add_parser(n); q.add_argument("--city", required=True, choices=CITIES); q.add_argument("--seed", type=int, required=True)
        q.add_argument("--arm", required=True, choices=ARMS); q.add_argument("--regime", required=True, choices=REGIMES)
        if n == "dev":
            q.add_argument("--deviation", default=None, help="commit of the dated deviation note authorising a deliberate re-run")
    x = sp.add_parser("extend"); x.add_argument("--city", required=True, choices=CITIES); x.add_argument("--arm", required=True, choices=ARMS); x.add_argument("--regime", required=True, choices=REGIMES)
    c = sp.add_parser("campaign"); c.add_argument("--phase", required=True, choices=("dev", "final"))
    a = ap.parse_args()
    E14.mkdir(parents=True, exist_ok=True)
    return {"preflight": preflight, "pre": pre, "struct": struct, "c0-synth": c0_synth, "diag-dev": diag_dev, "c0-accept": c0_accept, "sensitivity": sensitivity, "budget": budget,
            "dev": dev, "extend": extend, "final": final, "adequacy": adequacy, "test": test, "analysis": analysis, "campaign": campaign}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
