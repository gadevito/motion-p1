#!/usr/bin/env python3
"""
E13B — B0 controls and B1 of protocol `protocol/paper4/E13B.md`: the GF variant (p4b.GWN without graph convolution plus two
input channels computed from the input nodes of the batch — F, the input nodes' factor propagated along the kernel adjacency of
G1 for HOPS steps and divided exactly by the propagated mass; R, the reach indicator), arms D1 (readings available) and D0
(readings and their derivatives zeroed), regime I0, f = 0.20. `p4b.py`, `e9.py`, `e11.py` and `e13.py` are imported unchanged.

Structure. (1) Constants of E13B. (2) A DERIVED BLOCK: the functions of e13.py reused by E13B, copied mechanically with the
substitution table SUBST (identifiers E13 -> E13B, file names, the setup/training/adjacency entry points, the tag pattern);
`derived_block_matches()` regenerates the block from e13.py and compares it with this file, and the self-test and the
preflight assert it. `train_gf` is e13.train_e13 after the same substitutions with the backbone forced to graph=False and the
arm recorded on the setup (`train_gf_source()` regenerates it; asserted likewise). (3) E13B-specific code: SetupGF,
adjacency_gf, gate, test, analysis, b0-synth, b0-accept, p4r-revision, struct, preflight (no model update), pre (E13Bpre.md:
B0.1 and the benchmark), main. Every B1 command refuses to run unless the E13B gate passes (E13B.md, Files).

Commands: preflight · struct · pre · b0-synth · b0-accept --by --note-commit · p4r-revision --commit --receipt-commit --by ·
dev/final --city --seed --arm [--regime I0] · extend --city --arm · campaign --phase dev|final · adequacy · test · analysis
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9   # noqa: E402
import e13  # noqa: E402
from e11 import Log, cadence_ok  # noqa: E402

# ---------------------------------------------------------------- constants of E13B ----------------------
ROOT = p4b.ROOT
RUNS = ROOT / "paper4" / "runs"
E13B = RUNS / "e13b"
PREREG = ROOT / "protocol" / "paper4" / "E13B.md"
PREPRE = ROOT / "protocol" / "paper4" / "E13Bpre.md"
CITIES, SEEDS, F = e13.CITIES, e13.SEEDS, e13.F
ARMS = ("D1", "D0")                 # D1: readings available; D0: readings and their derivatives zeroed (VARIANT_SPEC_E13B.md)
REGIMES = ("I0",)                   # I0 only; I1 outside the perimeter (collegial decision of 2026-11-19)
CAP0, CAP1, CK_EVERY, CONFIGS, K_DEV_INIT = e13.CAP0, e13.CAP1, e13.CK_EVERY, e13.CONFIGS, e13.K_DEV_INIT
BOOT_SEED = 20261119
B_REPS, MARGIN, REPRO_TOL = e13.B_REPS, e13.MARGIN, e13.REPRO_TOL
HOPS = e13.RECEPTIVE_HOPS           # 6: receptive field of the predictions of p4b.GWN (E13.md, note of 2026-11-18)
SYNTH_SEEDS = {"dependent": 20261119, "independent": 20261120}      # B0.2: new realisations, fixed in E13B.md, never used before
D0_ZEROED = [0, 1, 2, 3, 11]        # r, flow, occupancy, historical average, F
FROZEN_PATHS = e13.FROZEN_PATHS + ["paper4/code/e13b.py", "protocol/paper4/E13B.md"]

# ---------------------------------------------------------------- derivation from e13.py -----------------
DERIVED = ['_git', 'git_describe', 'frozen_tag', 'frozen_unchanged', 'head_commit', 'git_clean', 'git_committed_unchanged', 'environment', '_report_matches_version', 'record13', 'cell_id', 'group_id', 'adequacy_of', '_index', '_append', '_next_attempt', 'latest_dev', 'latest_final', 'extension_status', 'group_cap', 'all_cells', '_dev_run', 'dev', 'extend', 'final', 'final_up_to_date', 'campaign', 'compute_adequacy', 'adequacy', 'per_horizon_mean', '_week_index', '_perturbed_copy']
SUBST = [('paper4-E13-*', 'paper4-E13B-*'), ('E13.md', 'E13B.md'), ('e13_adequacy.json', 'e13b_adequacy.json'), ('"e13.py": p4b.sha256(Path(__file__), 16)', '"e13.py": p4b.sha256(Path(e13.__file__), 16), "e13b.py": p4b.sha256(Path(__file__), 16)'), ('SetupE13(', 'SetupGF('), ('train_e13(', 'train_gf('), ('e9.adjacency(', 'adjacency_gf('), ('(?<![A-Za-z0-9_])E13(?![A-Za-z0-9_])', 'E13B')]                  # applied in order; the last entry is a regular expression on the identifier E13
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


def train_gf_source(e13_path=None):
    """e13.train_e13 after SUBST, backbone forced to graph=False, arm recorded on the setup."""
    src = substitute(function_sources(e13_path or e13.__file__)["train_e13"])
    old = '    graph = arm != "G0"\n'
    assert src.count(old) == 1
    return src.replace(old, '    assert arm in ARMS; su.arm = arm; graph = False          # GF: no graph convolution in either arm\n').rstrip("\n") + "\n"


def derived_block_matches(e13_path=None):
    me = Path(__file__).read_text()
    block = me.split(BEGIN_MARK + "\n")[1].split(END_MARK)[0]
    fs = function_sources(__file__)
    return block == derived_block(e13_path) and fs["train_gf"] == train_gf_source(e13_path)


# ---- BEGIN DERIVED FROM e13.py ----
def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)

def git_describe():
    """Exact tag of HEAD, if any (kept for the records)."""
    return _git("describe", "--tags", "--exact-match").stdout.strip()

def frozen_tag():
    """The E13B tag that froze code and protocol: the nearest `paper4-E13B-*` tag reachable from HEAD. HEAD may be
    later than the tag (commits that deposit records), but the frozen files must be identical to the tag."""
    return _git("describe", "--tags", "--abbrev=0", "--match", "paper4-E13B-*").stdout.strip()

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
                                                  "e13.py": p4b.sha256(Path(e13.__file__), 16), "e13b.py": p4b.sha256(Path(__file__), 16)},
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
    """Minimum not at the cap; improvement between the last two checkpoints ≤ 0.5 % of the validation wCE."""
    v = [t["val_wce"] for t in traj]; u = [t["update"] for t in traj]
    i = int(np.argmin(v)); impr = (v[-2] - v[-1]) / v[-2] if len(v) > 1 else 0.0
    return {"min_update": u[i], "min_at_cap": bool(u[i] == cap), "last_improvement_frac": float(impr),
            "pass": bool(u[i] != cap and impr <= 0.005)}

def _index(name):
    p = E13B / name
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []

def _append(name, row):
    (E13B / name).open("a").write(json.dumps(row) + "\n")

def _next_attempt(cid):
    """Attempt counter per cell, incremented before a folder is created: an interrupted attempt (folder without
    run.json, never indexed) does not block the next one; the E11 rule still blocks an identical (cell, cap, attempt)."""
    p = E13B / "attempts.json"; a = json.loads(p.read_text()) if p.exists() else {}
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
    p = E13B / f"extension_{gid}.json"
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
    su = SetupGF(city, seed, regime)
    A, info = adjacency_gf(su, arm)
    cid = cell_id(city, seed, arm, regime)
    d = p4b.run_dir(E13B / "dev", {"protocol": "E13B", "phase": "dev", "cell": cid, "cap": cap, "configs": CONFIGS, "f": F,
                                  "grid": su.G, "fingerprints": su.fingerprints(), "extension_of": reproduce_from["dir"] if reproduce_from else None,
                                  "attempt": attempt, "deviation": deviation})
    log = Log(d / "log.txt"); log(f"E13B dev {cid} cap {cap} -> {d}")
    out, repro = {}, {}
    for name, cfg in CONFIGS.items():
        o = train_gf(su, arm, A, cap, cfg, K_DEV_INIT, log=log if log_print else None, save_states=False)
        assert o["hidden_in_batches"] == 0
        out[name] = {"trajectory": o["trajectory"], "selected_checkpoint": o["selected"],
                     "selected_val_wce": min(t["val_wce"] for t in o["trajectory"]), "updates": o["updates"],
                     "seconds": o["seconds"], "init_seed": o["init_seed"], "adequacy": adequacy_of(o["trajectory"], cap)}
        if reproduce_from is not None:                 # the first 10 000 updates must reproduce the earlier curve
            old = reproduce_from["configs"][name]["trajectory"]; new = o["trajectory"][:len(old)]
            dmax = max(abs(a["val_wce"] - b["val_wce"]) for a, b in zip(old, new))
            repro[name] = {"max_abs_diff_val_wce": dmax, "ok": bool(dmax <= REPRO_TOL)}
            log(f"[{name}] reproduction of the {reproduce_from['cap']} curve: max |Δ| = {dmax:.3e} ({'ok' if dmax <= REPRO_TOL else 'NOT reproduced'})")
    sel = min(out.items(), key=lambda kv: (kv[1]["selected_val_wce"], kv[1]["selected_checkpoint"], kv[0]))
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
    """Extension of E13B.md: every cell of the group to 20 000, all four configurations, reproduction checked."""
    gate("extend")
    gid = group_id(args.city, args.arm, args.regime); sp = E13B / f"extension_{gid}.json"
    st = extension_status(gid)
    if st and st["status"] == "complete":
        raise PermissionError(f"group {gid} already extended once: a second failure is a feasibility limit (E13B.md)")
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
    su = SetupGF(args.city, args.seed, args.regime)
    A, info = adjacency_gf(su, args.arm)
    d = p4b.run_dir(E13B / "final", {"protocol": "E13B", "phase": "final", "cell": cid, "cap": cap, "config": dv["selected_config"], "dev_dir": dv["dir"]})
    log = Log(d / "log.txt"); log(f"E13B final {cid} config {dv['selected_config']} cap {cap} -> {d}")
    o = train_gf(su, args.arm, A, cap, cfg, p4b.K_INIT, log=log, save_states=True)
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
    exts = {p.stem.replace("extension_", ""): json.loads(p.read_text())["status"] for p in E13B.glob("extension_*.json")}
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
    (RUNS / "e13b_adequacy.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: rep[k] for k in ("missing_dev", "missing_final", "final_stale", "dev_failures_pending",
                                          "dev_failures_after_extension", "final_failures", "excluded_from_adequacy_statements", "lock", "lock_sha16")}, indent=1))
    print("dev_failures_pending: run `extend` for their groups, then `final` again; "
          "dev_failures_after_extension and final_failures: feasibility limit / inconclusive, excluded from adequacy-conditioned statements")
    return 0 if rep["lock"] else 1

def per_horizon_mean(num, den):
    """Mean over horizons of the per-horizon weighted ratios (E13B.md, Unit of analysis): NOT the pooled ratio."""
    num = np.asarray(num, dtype="float64"); den = np.maximum(np.asarray(den, dtype="float64"), 1e-12)
    return float(np.mean(num / den))

def _week_index(ts):
    iso = pd.DatetimeIndex(ts).isocalendar()
    return (iso.year.to_numpy() * 100 + iso.week.to_numpy())

def _perturbed_copy(su, nz, perturb_val_labels):
    """Noise on the dynamic values of every hidden node; classes of test-hidden nodes (and, if asked, of
    validation-hidden nodes) replaced. Validation labels are kept when the validation score is compared."""
    pert = copy.copy(su)
    for k in ("r", "flow", "occ"):
        a_ = getattr(su, k).copy(); a_[:, ~su.obs] = nz.normal(size=a_[:, ~su.obs].shape); setattr(pert, k, a_)
    C2 = su.C.copy(); who = ~su.obs if perturb_val_labels else su.test
    C2[:, who] = nz.integers(1, 4, size=C2[:, who].shape); pert.C = C2
    pert._stats(); pert._tensors(); pert._fix_cin()
    return pert
# ---- END DERIVED FROM e13.py ----

# ====================================================================================================
# E13B-specific code (hand-written; the derived block above is a mechanical copy of e13.py functions)
# ====================================================================================================

class SetupGF(p4b.Setup):
    """E9 setup at f = 0.20, regime I0, with the two feature channels of the GF variant (VARIANT_SPEC_E13B.md):
    F = input nodes' factor r propagated along the kernel adjacency of G1 for HOPS steps, divided exactly by the propagated
    mass of the input nodes (double precision on the CPU, as the frozen R2 code of I2), 0 where no input node is reachable;
    R = indicator of a positive mass. Both computed from the input nodes of the batch only. The arm is set by the training
    wrapper (`s.arm`): in D0 the channels 0 (r), 1 (flow), 2 (occupancy), 3 (historical average) and F are zero for every
    node and step. `static` is always False (max_speed channel zero)."""

    def __init__(s, city, seed, regime="I0", device=None):
        if regime != "I0":
            raise ValueError("E13B runs regime I0 only")
        super().__init__(city, p4b.CITY[city]["roads"], seed=seed, grid=e9.GRID[city], targets=e9.targets(F), device=device)
        s.regime = "I0"; s.arm = None
        A, s.sigma = p4b.kernel_adjacency(s.al["graph"], s.kept); s.A_kernel = np.asarray(A, dtype="float64")
        M = np.zeros_like(s.A_kernel); P = np.eye(s.K)
        for _ in range(HOPS):
            P = P @ s.A_kernel; M = M + P
        s.M64 = M
        s._fix_cin()

    def _fix_cin(s):
        s.c_in = 13

    def feature64(s, r_in, inp):
        """Unconverted numerator and denominator (float64): num (B, K, T), den (K,)."""
        r64 = r_in.detach().cpu().double().numpy(); om = np.asarray(inp, dtype="float64")
        num = np.tensordot(s.M64, r64, axes=([1], [1])).transpose(1, 0, 2); den = s.M64 @ om
        return num, den

    def feature(s, r_in, inp):
        num, den = s.feature64(r_in, inp); reach = den > 0
        feat = np.zeros_like(num); feat[:, reach, :] = num[:, reach, :] / den[reach][None, :, None]
        return torch.tensor(feat.astype("float32"), device=s.dev), torch.tensor(reach.astype("float32"), device=s.dev)

    def batch(s, origins, inp, tgt, static=False):
        if static:
            raise ValueError("E13B: static=False always")
        if s.arm not in ARMS:
            raise RuntimeError("SetupGF.batch: the arm (D1 or D0) must be set before building a batch")
        x, y, m = super().batch(origins, inp, tgt, False)
        B, _, K, T = x.shape
        Fc, R = s.feature(x[:, 0], inp)
        x = torch.cat([x, Fc.unsqueeze(1), R.view(1, 1, K, 1).expand(B, 1, K, T)], 1)
        if s.arm == "D0":
            x = x.clone(); x[:, D0_ZEROED] = 0.0
        return x, y, m

    def inject(s, r, flow, occ, C):
        """B0.2: replace the target processes by synthetic ones (same shapes and timestamps) and rebuild."""
        s.r, s.flow, s.occ, s.C = r.astype("float32"), flow.astype("float32"), occ.astype("float32"), C.astype("int64")
        s._stats(); s._tensors(); s._fix_cin()


def adjacency_gf(su, arm):
    """The GF variant uses no graph convolution: no adjacency is passed to the model (the neighbourhood enters through the
    feature channels of SetupGF). Replaces `e9.adjacency` in the derived code."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}")
    return None, {"variant": "GF", "arm": arm, "graph_convolution": False, "feature_hops": HOPS, "kernel_sigma": float(su.sigma)}


TRAIN_GF_SOURCE_NOTE = "train_gf is e13.train_e13 after the substitution table, with the backbone forced to graph=False and the arm recorded on the setup (asserted by the self-test)."

def train_gf(su, arm, A, cap, cfg, init_stream, log=None, ck_every=CK_EVERY, save_states=True, keep_losses=False):
    """p4b.train with weight decay, an initialisation stream and checkpoints every `ck_every` up to `cap`.
    Returns trajectory, states at every checkpoint (CPU), the per-step training losses if asked, counters.
    Never touches test origins."""
    assert arm in ARMS; su.arm = arm; graph = False          # GF: no graph convolution in either arm
    s_init = int(p4b.rng(su.seed, init_stream).integers(2 ** 31))
    torch.manual_seed(s_init)
    net = p4b.GWN(su.c_in, graph, dropout=cfg["dropout"]).to(su.dev)
    opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    At = torch.tensor(A, device=su.dev) if graph else None
    r_mask, r_order = p4b.rng(su.seed, p4b.K_MASKS), p4b.rng(su.seed, p4b.K_ORDER)
    perm, pi = r_order.permutation(su.tr), 0
    traj, states, steps, t0, run_loss, losses, seen_hidden = [], {}, 0, time.perf_counter(), [], [], 0
    cks = set(range(0, cap + 1, ck_every))

    def checkpoint():
        P, Y = p4b.predict(net, su, At, su.va, su.obs, su.val)
        v = p4b.wce_np(P, Y, su.W)
        tl = float(np.mean(run_loss)) if run_loss else None
        run_loss.clear()
        traj.append({"update": steps, "val_wce": v, "train_loss": tl, "seconds": time.perf_counter() - t0})
        if save_states:
            states[steps] = {k: t.detach().cpu().clone() for k, t in net.state_dict().items()}
        if log:
            log(f"[{arm} {su.regime}] update {steps:6d}  val wCE {v:.5f}  train {tl if tl is None else round(tl, 4)}")
    checkpoint()
    while steps < cap:
        if pi + 32 > len(perm):
            perm, pi = r_order.permutation(su.tr), 0
        bt = perm[pi:pi + 32]; pi += 32
        inp, tgt, _ = su.batch_mask(r_mask)
        seen_hidden += int(inp[~su.obs].sum() + tgt[~su.obs].sum())
        x, y, m = su.batch(bt, inp, tgt)
        net.train(); opt.zero_grad()
        loss = p4b.loss_fn(net(x, At), y, m, su.Wt); loss.backward(); opt.step(); steps += 1
        lv = float(loss.item()); run_loss.append(lv)
        if keep_losses:
            losses.append(lv)
        if steps in cks:
            checkpoint()
    best = min(traj, key=lambda d: (d["val_wce"], d["update"]))
    return {"net": net, "A": At, "states": states, "trajectory": traj, "selected": best["update"], "updates": steps,
            "hidden_in_batches": seen_hidden, "seconds": time.perf_counter() - t0, "init_seed": s_init, "losses": losses}


def gate(phase):
    """Launch constraints of E13B (E13B.md, Order and B0): an E13B tag reachable from HEAD, the frozen files (E13's plus
    e13b.py and E13B.md) identical to it, clean working tree, signature line filled; for B1 commands: the B0.2 report of
    this frozen version with BOTH realisations valid and the dependent control passed (no acceptance route), the independent
    control passed or its anomaly accepted (acceptance bound to the same report fingerprint and frozen tag), and the signed
    P4R revision recorded (`e13b_p4r_revision.json`, committed, matching the committed P4R.md)."""
    tag = frozen_tag()
    if not tag.startswith("paper4-E13B-"):
        raise PermissionError(f"no E13B tag reachable from HEAD (git describe --match paper4-E13B-*: {tag!r})")
    if not frozen_unchanged(tag):
        raise PermissionError(f"code or protocol differ from the frozen tag {tag} ({', '.join(FROZEN_PATHS)}): a new signed tag is required")
    if not git_clean():
        raise PermissionError("working tree not clean (modified tracked files or untracked files): the run would not be from the frozen version")
    p4b.require_signed(PREREG)
    if phase in ("dev", "extend", "final", "test", "analysis"):
        b0 = RUNS / "e13b_b0_synth.json"
        if not b0.exists():
            raise PermissionError("B0.2 (b0-synth) has not been run")
        z = json.loads(b0.read_text())
        if not _report_matches_version(z, tag):
            raise PermissionError("the B0.2 report was produced by another version (tag, code or protocol fingerprint differ)")
        cc = z.get("control_check", {})
        if not (cc.get("dependent", {}).get("valid") and cc.get("independent", {}).get("valid")):
            raise PermissionError("B0.2: a synthetic realisation is invalid on the diagnostic: B1 cannot start (stopping rule)")
        kinds = z.get("kinds", {})
        if kinds.get("dependent", {}).get("verdict") != "pass":
            raise PermissionError("B0.2 dependent control not passed: B1 cannot start; no acceptance route exists for this condition (E13B.md)")
        if kinds.get("independent", {}).get("verdict") != "pass":
            acc = RUNS / "e13b_b0_resolution.json"
            if not acc.exists():
                raise PermissionError("B0.2 independent control shows an anomaly: explain it in a dated note and record b0-accept")
            r = json.loads(acc.read_text())
            if r.get("b0_synth_sha16") != p4b.sha256(b0, 16) or r.get("frozen_tag") != tag or r.get("scope") != "independent anomaly":
                raise PermissionError("b0-accept refers to another B0.2 report or version, or is not limited to the independent anomaly")
        rev = RUNS / "e13b_p4r_revision.json"
        if not rev.exists():
            raise PermissionError("the signed P4R revision is not recorded (p4r-revision): B1 cannot start (E13B.md, Order 4(d))")
        if not git_committed_unchanged(rev.relative_to(ROOT)):
            raise PermissionError("e13b_p4r_revision.json is not committed unchanged")
        rv = json.loads(rev.read_text()); p4r = ROOT / "protocol" / "paper4" / "P4R.md"
        if rv.get("p4r_sha16") != p4b.sha256(p4r, 16) or not git_committed_unchanged(p4r.relative_to(ROOT)):
            raise PermissionError("P4R.md differs from the recorded signed revision, or is not committed unchanged")
    return tag


def p4r_revision(args):
    """The responsible author records that the P4R revision (comparisons kept or withdrawn, statistical family and
    correction, budget, order of blocks) is signed, deposited and committed."""
    p4r = ROOT / "protocol" / "paper4" / "P4R.md"
    if not git_committed_unchanged(p4r.relative_to(ROOT)):
        raise PermissionError("P4R.md is not committed unchanged")
    rec = {"p4r_commit": args.commit, "p4r_sha16": p4b.sha256(p4r, 16), "receipt_commit": args.receipt_commit, "by": args.by,
           "written": datetime.now(timezone.utc).isoformat(), "frozen_tag": frozen_tag()}
    (RUNS / "e13b_p4r_revision.json").write_text(json.dumps(rec, indent=1)); print(json.dumps(rec, indent=1)); return 0


def test(args):
    gate("test")
    lock_path = RUNS / "e13b_adequacy.json"
    saved = json.loads(lock_path.read_text())
    now = compute_adequacy()
    if not saved.get("lock") or saved.get("lock_sha16") != now["lock_sha16"]:
        raise PermissionError("the lock file does not match the current records, or the lock is not satisfied: run `adequacy` and commit it")
    if not git_committed_unchanged(lock_path.relative_to(ROOT)):
        raise PermissionError("e13b_adequacy.json is not committed unchanged (git add -f, commit) — the protocol requires the committed report")
    for c, s, a, r in all_cells():
        cid = cell_id(c, s, a, r); fn = latest_final(cid); d = Path(fn["dir"])
        if (d / "test_cells.npz").exists():
            old = np.load(d / "test_cells.npz")
            if str(old["lock_sha16"]) != now["lock_sha16"]:
                raise PermissionError(f"{d / 'test_cells.npz'} was produced under another lock ({old['lock_sha16']}); move it aside, it is not overwritten")
            continue
        su = SetupGF(c, s, r); su.arm = a
        net = p4b.GWN(su.c_in, False, dropout=fn["cfg"]["dropout"]).to(su.dev)
        net.load_state_dict(torch.load(d / "selected_state.pt"))
        reach = (su.M64 @ su.obs.astype("float64")) > 0                           # test-hidden nodes with a path from an observed node
        P, Y = p4b.predict(net, su, None, su.te, su.obs, su.test)
        np.savez_compressed(d / "test_cells.npz", p=P.astype("float32"), y=Y.astype("int8"), origins=su.te, cells=su.cells,
                            test_nodes=su.test, reach=reach, W=su.W, ts=su.ts[su.te].astype("datetime64[m]"), lock_sha16=now["lock_sha16"])
        print(cid, "test wCE (mean over horizons)", round(float(np.mean([p4b.wce_np(P[:, :, h], Y[:, :, h], su.W) for h in range(P.shape[2])])), 5), flush=True)
    return 0


def analysis(args):
    """E13.analysis adapted to arms D1/D0 and regime I0: primary V_D1 per city; secondary V_D1 on reached (R = 1) and
    unreached (R = 0) test-hidden nodes; shared multiplicities across splits and arms; per-horizon metric; sup-t band over the
    three primary contrasts; statement always PROVISIONAL (the family-wise correction belongs to the campaign-wide analysis)."""
    gate("analysis")
    adeq = json.loads((RUNS / "e13b_adequacy.json").read_text())
    if adeq["lock_sha16"] != compute_adequacy()["lock_sha16"]:
        raise PermissionError("records changed since the lock")
    excluded = set(adeq["excluded_from_adequacy_statements"])
    out = {"written": datetime.now(timezone.utc).isoformat(), "B": B_REPS, "seed": BOOT_SEED, "metric": "mean over horizons of per-horizon wCE on test-hidden nodes",
           "environment": environment(), "cities": {}}
    for ci, city in enumerate(CITIES):
        LM, WM, cellof, weekof, RE = {}, {}, {}, {}, {}; blocks = weeks = None
        for s in SEEDS:
            for a in ARMS:
                z = np.load(Path(latest_final(cell_id(city, s, a, "I0"))["dir"]) / "test_cells.npz")
                if str(z["lock_sha16"]) != adeq["lock_sha16"]:
                    raise PermissionError(f"test file of {cell_id(city, s, a, 'I0')} belongs to another lock")
                if blocks is None:
                    blocks, weeks = np.unique(z["cells"]), np.unique(_week_index(z["ts"]))
                P, Y, W = z["p"].astype("float64"), z["y"].astype("int64"), z["W"].astype("float64")
                v = Y >= 0; Yc = np.clip(Y, 0, 2)
                pt = np.clip(np.take_along_axis(P, Yc[..., None], -1)[..., 0], 1e-7, 1)
                w = np.where(v, W[Yc], 0.0)
                LM[(s, a)] = w * -np.log(pt); WM[(s, a)] = w
                cellof[(s, a)] = np.searchsorted(blocks, z["cells"]); weekof[(s, a)] = np.searchsorted(weeks, _week_index(z["ts"])); RE[(s, a)] = z["reach"].astype(bool)
        nb, nw = len(blocks), len(weeks); rng = np.random.default_rng([BOOT_SEED, ci])

        def wce_with(key, mb, mw, nodes=None):
            wn = (mb[cellof[key]][None, :] * mw[weekof[key]][:, None])
            if nodes is not None:
                wn = wn * nodes[None, :]
            wn = wn[..., None]
            return per_horizon_mean((LM[key] * wn).sum((0, 1)), (WM[key] * wn).sum((0, 1)))

        def contrasts(mb, mw):
            res = {}
            for name, sel in (("V_D1", None), ("V_D1_reached", True), ("V_D1_unreached", False)):
                vs = []
                for s in SEEDS:
                    nodes = None if sel is None else (RE[(s, "D0")] == sel).astype("float64")
                    w0 = wce_with((s, "D0"), mb, mw, nodes); w1 = wce_with((s, "D1"), mb, mw, nodes)
                    vs.append(100.0 * (w0 - w1) / w0 if w0 > 0 else float("nan"))        # empty subset in a replicate: undefined, dropped
                res[name] = float(np.nanmean(vs)); res[f"{name}_by_seed"] = vs
            return res
        obs = contrasts(np.ones(nb), np.ones(nw)); keys = [k for k in obs if not k.endswith("_by_seed")]
        reps = {k: np.empty(B_REPS) for k in keys}
        for b in range(B_REPS):
            mb = np.bincount(rng.integers(0, nb, nb), minlength=nb).astype("float64")
            mw = np.bincount(rng.integers(0, nw, nw), minlength=nw).astype("float64")
            cb = contrasts(mb, mw)
            for k in keys:
                reps[k][b] = cb[k]
        res = {"n_blocks": int(nb), "n_weeks": int(nw), "observed": obs,
               "unreached_test_hidden_share_by_seed": {str(s): float((~RE[(s, "D0")][np.load(Path(latest_final(cell_id(city, s, "D0", "I0"))["dir"]) / "test_cells.npz")["test_nodes"]]).mean()) for s in SEEDS}}
        for k in keys:
            lo, hi = np.nanpercentile(reps[k], [2.5, 97.5]); centred = reps[k] - np.nanmean(reps[k])
            res[k] = {"estimate": obs[k], "ci95": [float(lo), float(hi)], "p_centred": float(np.nanmean(np.abs(centred) >= abs(obs[k]))),
                      "p_one_sided_positive": float(np.nanmean(centred >= obs[k])), "replicates_undefined": int(np.isnan(reps[k]).sum()),
                      "sign": "favourable" if lo > 0 else ("unfavourable" if hi < 0 else "inconclusive"),
                      "margin": "reached" if lo >= MARGIN else ("advantage>=3 excluded" if hi < MARGIN else "not excluded")}
        cells_c = {cell_id(city, s, a, "I0") for s in SEEDS for a in ARMS}
        res["V_D1"]["eligible_for_adequacy_statements"] = not (cells_c & excluded); res["V_D1"]["excluded_cells"] = sorted(cells_c & excluded)
        res["_reps"] = reps["V_D1"]
        out["cities"][city] = res
    R = np.stack([out["cities"][c]["_reps"] for c in CITIES], 1); est = np.array([out["cities"][c]["V_D1"]["estimate"] for c in CITIES])
    sd = np.nanstd(R, 0) + 1e-12; T = np.nanmax(np.abs((R - np.nanmean(R, 0)) / sd), 1); q = float(np.nanpercentile(T, 95))
    out["supt_95"] = {f"{c}:V_D1": [float(e - q * s_), float(e + q * s_)] for c, e, s_ in zip(CITIES, est, sd)}
    for c in CITIES:
        out["cities"][c].pop("_reps")
    el = {c: out["cities"][c]["V_D1"]["eligible_for_adequacy_statements"] for c in CITIES}
    cand = [c for c in CITIES if el[c] and out["cities"][c]["V_D1"]["sign"] == "favourable" and out["cities"][c]["V_D1"]["estimate"] >= MARGIN]
    at_least_3 = [c for c in cand if out["supt_95"][f"{c}:V_D1"][0] >= MARGIN]
    below = all(el[c] and out["supt_95"][f"{c}:V_D1"][1] < MARGIN for c in CITIES)
    raw = ("candidate: observed-site readings, delivered through the normalised neighbourhood feature, help at 20 % under adequate training "
           "(marginal evidence in >= 2 cities; condition (a) of E13B.md requires the corrected positive test of the pre-registered family)" if len(cand) >= 2 else
           "gain below the prespecified 3-point margin at 20 % under adequate training" if below else "undetermined")
    out["confirmatory"] = False
    out["statement"] = f"PROVISIONAL (marginal intervals; the family-wise correction belongs to the campaign-wide analysis of the revised P4R family): {raw}"
    out["statement_counts"] = {"cities_candidate": cand, "cities_lower_simultaneous_bound_ge_3": at_least_3, "eligible": el, "excluded_cells": sorted(excluded)}
    (RUNS / "e13b_analysis.json").write_text(json.dumps(out, indent=1, default=float))
    for c in CITIES:
        for k in ("V_D1", "V_D1_reached", "V_D1_unreached"):
            r = out["cities"][c][k]
            print(f"{c:9s} {k:15s} {r['estimate']:7.3f}  CI {r['ci95'][0]:7.3f} {r['ci95'][1]:7.3f}  p {r['p_centred']:.4f}  {r['sign']} / {r['margin']}")
    print("sup-t 95 %:", {k: [round(v[0], 2), round(v[1], 2)] for k, v in out["supt_95"].items()})
    print("statement:", out["statement"], out["statement_counts"])
    return 0


def b0_synth(args):
    """B0.2 of E13B.md: new realisations (seeds fixed in SYNTH_SEEDS), validity of BOTH on the graph diagnostic before the
    first fit, then D1 and D0 with C1 for 2 000 updates, validation every 250; best checkpoint on D1; verdicts as E13B.md."""
    gate("b0")
    path = RUNS / "e13b_b0_synth.json"
    if path.exists():
        raise FileExistsError(f"{path} exists")
    out = {"protocol": "E13B B0.2", "generator_version": 2, "generator_seeds": SYNTH_SEEDS, "generator": e13.synth_processes.__doc__, "kinds": {}, "trainings": 0}
    gens = {}
    for kind in ("dependent", "independent"):
        su = SetupGF("madrid", 0); z, flow, occ, C = e13.synth_processes(su, kind, SYNTH_SEEDS[kind]); su.inject(z, flow, occ, C)
        dg = e13.tabular_diagnostic(su, z, C, A=su.A_kernel); shares = (np.bincount(C.ravel(), minlength=4)[1:] / C.size).tolist()
        valid = dg["mean_V"] >= 10 if kind == "dependent" else abs(dg["mean_V"]) <= 1
        print(kind, "seed", SYNTH_SEEDS[kind], "tabular diagnostic, graph feature: V per horizon", {h: round(dg[h]["V"], 1) for h in ("1", "2", "4", "8")},
              "mean", round(dg["mean_V"], 1), "| class shares", np.round(shares, 3), "->", "valid" if valid else "INVALID")
        gens[kind] = (su, dg, shares, valid)
    out["control_check"] = {k: {"tabular_diagnostic": v[1], "class_shares": v[2], "valid": v[3], "seed": SYNTH_SEEDS[k]} for k, v in gens.items()}
    if not all(v[3] for v in gens.values()):
        out["verdict"] = "synthetic control invalid on the graph diagnostic: no neural-network training performed (stopping rule)"
        out["written"] = datetime.now(timezone.utc).isoformat(); out["environment"] = environment()
        path.write_text(json.dumps(out, indent=1)); print("->", path, p4b.sha256(path, 16), "control invalid, stopped before training"); return 1
    for kind in ("dependent", "independent"):
        su = gens[kind][0]; res = {}
        for arm in ARMS:
            o = train_gf(su, arm, None, 2000, CONFIGS["C1"], p4b.K_INIT, ck_every=250, save_states=False, log=print); out["trainings"] += 1
            res[arm] = [{"update": t["update"], "val_wce": t["val_wce"], "train_loss": t["train_loss"]} for t in o["trajectory"]]
        V = [(a["update"], 100 * (a["val_wce"] - b["val_wce"]) / a["val_wce"]) for a, b in zip(res["D0"], res["D1"])]
        d1 = [t for t in res["D1"] if t["update"] >= 500]; ub = min(d1, key=lambda t: (t["val_wce"], t["update"]))["update"]
        v_best = next(v for u, v in V if u == ub); after500 = [v for u, v in V if u >= 500]
        if kind == "dependent":
            verdict = "pass" if v_best >= 3 else "FAIL: the dependent control is not passed (V(D1) < +3 at the best checkpoint); B1 blocked, no acceptance route"
            note = None
        else:
            verdict = "anomaly: V(D1) > +3 at a checkpoint >= 500 — explain in a dated note; b0-accept limited to this anomaly" if max(after500) > 3 else "pass"
            note = "D1 worse than D0 by > 3 at some checkpoint — reported and investigated, not a block" if min(after500) < -3 else None
        out["kinds"][kind] = {"trajectories": res, "V_D1_by_checkpoint": V, "best_checkpoint_D1": ub, "V_at_best": v_best, "verdict": verdict, "note": note}
        print(kind, "best checkpoint of D1", ub, "V", round(v_best, 2), "->", verdict)
    out["written"] = datetime.now(timezone.utc).isoformat(); out["environment"] = environment(); c, dirty = p4b.git_commit(); out["commit"] = c; out["code_dirty"] = dirty
    path.write_text(json.dumps(out, indent=1)); print("->", path, p4b.sha256(path, 16))
    return 0 if out["kinds"]["dependent"]["verdict"] == "pass" and out["kinds"]["independent"]["verdict"] == "pass" else 1


def b0_accept(args):
    """Acceptance limited to the independent anomaly of B0.2, bound to the report fingerprint and the frozen tag."""
    b0 = RUNS / "e13b_b0_synth.json"; z = json.loads(b0.read_text())
    if z["kinds"]["dependent"]["verdict"] != "pass":
        raise PermissionError("the dependent control is not passed: it cannot be accepted (E13B.md)")
    if z["kinds"]["independent"]["verdict"] == "pass":
        raise PermissionError("the independent control shows no anomaly: nothing to accept")
    rec = {"scope": "independent anomaly", "accepted_by": args.by, "note_commit": args.note_commit, "b0_synth_sha16": p4b.sha256(b0, 16),
           "frozen_tag": frozen_tag(), "independent_verdict": z["kinds"]["independent"]["verdict"], "written": datetime.now(timezone.utc).isoformat()}
    (RUNS / "e13b_b0_resolution.json").write_text(json.dumps(rec, indent=1)); print(json.dumps(rec, indent=1)); return 0


def _hop_dist(A, inp):
    n = len(A); fwd = [np.flatnonzero(A[:, m] > 0) for m in range(n)]; d = np.full(n, -1); q = deque()
    for m in np.flatnonzero(inp):
        d[m] = 0; q.append(m)
    while q:
        m = q.popleft()
        for k in fwd[m]:
            if d[k] < 0:
                d[k] = d[m] + 1; q.append(k)
    return d


def _mass_summary(den):
    den = np.asarray(den, dtype="float64")
    return {"n": int(den.size), "median": float(np.median(den)), "p25": float(np.percentile(den, 25)), "p75": float(np.percentile(den, 75)),
            "share_gt_0.1": float((den > 0.1).mean()), "share_gt_0.01": float((den > 0.01).mean()),
            "share_tiny_0_to_1e-6": float(((den > 0) & (den <= 1e-6)).mean()), "share_exact_zero": float((den == 0).mean())}


def struct_measure(city, seed, su=None, draws=20):
    """Reproduction of the I3 measurement (reachability and reference mass within HOPS steps) for one (city, seed), on the
    quantities shared with `e13_a0_struct.json`: hop-distance counts of the validation-hidden nodes and the 6-step mass
    summaries of validation-hidden, test-hidden (node sets only), sampled training targets (20 masks) and observed nodes."""
    su = su or SetupGF(city, seed)
    hd = _hop_dist(su.A_kernel, su.obs); mo = su.M64 @ su.obs.astype("float64")
    r = p4b.rng(su.seed, p4b.K_MASKS); tr = np.concatenate([(su.M64 @ inp.astype("float64"))[tgt] for inp, tgt, _ in (su.batch_mask(r) for _ in range(draws))])
    return {"hop_distance_validation_hidden": {str(k): int(v) for k, v in zip(*np.unique(hd[su.val], return_counts=True))},
            f"mass_{HOPS}hops": {"validation_hidden": _mass_summary(mo[su.val]), "test_hidden": _mass_summary(mo[su.test]),
                                 "training_targets": _mass_summary(tr), "observed_self": _mass_summary(mo[su.obs])}}


def struct(args):
    """`struct`: the I3 reproduction for all (city, seed), compared with `paper4/runs/e13_a0_struct.json` where present."""
    out = {"hops": HOPS, "draws": 20, "cities": {}, "environment": environment(), "written": None}; ref_p = RUNS / "e13_a0_struct.json"
    ref = json.loads(ref_p.read_text()) if ref_p.exists() else None; agree = True
    for city in CITIES:
        out["cities"][city] = {}
        for s in SEEDS:
            m = struct_measure(city, s); out["cities"][city][str(s)] = m
            if ref is not None:
                r = ref["cities"][city]["seeds"][str(s)]
                same = r["hop_distance_validation_hidden"] == m["hop_distance_validation_hidden"] and all(
                    abs(r[f"mass_{HOPS}hops"][g][k] - m[f"mass_{HOPS}hops"][g][k]) <= 1e-9 for g in m[f"mass_{HOPS}hops"] for k in m[f"mass_{HOPS}hops"][g])
                agree &= same; print(city, s, "agrees with e13_a0_struct.json" if same else "DIFFERS from e13_a0_struct.json")
    out["agrees_with_I3"] = agree if ref is not None else None; out["written"] = datetime.now(timezone.utc).isoformat()
    (RUNS / "e13b_struct.json").write_text(json.dumps(out, indent=1)); print("->", RUNS / "e13b_struct.json", p4b.sha256(RUNS / "e13b_struct.json", 16))
    return 0 if agree else 1


def preflight(args):
    """Deterministic preflight of E13B (no update of any model): E11/E9 assertions at f = 20 % for the 13-channel setup, B0.3,
    B0.4, B0.5 (static check and I3 reproduction), run-dir and guard checks. B0.1 and the benchmark run under E13Bpre.md (`pre`)."""
    RUNS.mkdir(parents=True, exist_ok=True); E13B.mkdir(exist_ok=True)
    log = Log(RUNS / "e13b_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E13B preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty}) — tag {git_describe()!r}")
    log(f"code p4b.py {p4b.sha256(Path(p4b.__file__), 16)} · e9.py {p4b.sha256(Path(e9.__file__), 16)} · e13.py {p4b.sha256(Path(e13.__file__), 16)} · e13b.py {p4b.sha256(Path(__file__), 16)} · torch {torch.__version__}")
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
    log.check("B0.4", "London data files differ from Madrid's", all(fm[k] != fl[k] for k in fm), json.dumps({"madrid": fm, "london": fl}))
    su = SetupGF("madrid", 0); su.arm = "D1"
    whole = all(len(np.unique(su.lab[su.cells == c_])) == 1 for c_ in np.unique(su.cells))
    log.check("1a", "node sets disjoint, non-empty, whole cells", whole and su.obs.any() and su.val.any() and su.test.any())
    r = p4b.rng(0, p4b.K_MASKS); bm = bt_ = 0; hidden = torch.as_tensor(~su.obs, device=su.dev)
    for _ in range(100):
        inp, tgt, _ = su.batch_mask(r); bm += int((inp & ~su.obs).sum() + (tgt & ~su.obs).sum())
        x, y, m = su.batch(su.tr[:32], inp, tgt)
        bt_ += int(x[:, :4][:, :, hidden].abs().sum().item() > 0) + int(x[:, 10][:, hidden].abs().sum().item() > 0) + int(m[:, hidden].abs().sum().item() > 0)
    log.check("1b", "no hidden index in input mask or loss of 100 batches", bm == 0)
    log.check("1c", "hidden nodes zero in their own dynamic channels (0-3), the input indicator and the loss tensor (F and R are admitted inputs)", bt_ == 0)
    log.check("ch", "input channels = 13 (11 + F + R)", x.shape[1] == 13)
    allo = np.concatenate([su.tr, su.va, su.te]); gap = max(p4b.HORIZONS) + p4b.T_IN - 1
    log.check("2a", "every origin admissible", all(cadence_ok(su.ts, int(t)) for t in allo))
    log.check("2b", "no target of a period overlaps an input of the next", bool(su.tr.max() + gap < su.va.min() and su.va.max() + gap < su.te.min()))
    bt = su.tr[100:132]; inp, tgt, _ = su.batch_mask(p4b.rng(0, 99)); x0, _, _ = su.batch(bt, inp, tgt)
    sv = {k: getattr(su, k).clone() for k in ("Rf", "FL", "OC", "HAs")}; tmax = int(bt.max()); gen = torch.Generator(device="cpu").manual_seed(7)
    for k in sv:
        t_ = getattr(su, k); t_[tmax + 1:] = torch.randn(t_[tmax + 1:].shape, generator=gen).to(su.dev)
    x1, _, _ = su.batch(bt, inp, tgt)
    for k, v in sv.items():
        setattr(su, k, v)
    log.check("2c", "causality: noise after the origin leaves the 13 input channels identical to the bit (F included)", bool(torch.equal(x0, x1)))
    pert_all = _perturbed_copy(su, np.random.default_rng(11), perturb_val_labels=True)
    log.check("2d", "noise on hidden nodes (all) leaves class weights, normalisation and historical average identical",
              bool(np.array_equal(pert_all.W, su.W) and [pert_all.fmu, pert_all.fsd, pert_all.omu, pert_all.osd] == [su.fmu, su.fsd, su.omu, su.osd] and np.array_equal(pert_all.HA, su.HA)))
    f_ = np.bincount(su.C[:su.reg_end][:, su.obs].ravel(), minlength=4)[1:].astype("float64")
    log.check("3", "class weights recomputed independently from observed training cells", bool(np.array_equal((f_.sum() / (np.maximum(f_, 1) * 3)).astype("float32"), su.W)))
    pert = _perturbed_copy(su, np.random.default_rng(12), perturb_val_labels=False); pert.arm = "D1"
    xa, ya, ma = su.batch(bt, inp, tgt); xb, yb, mb_ = pert.batch(bt, inp, tgt)
    log.check("B0.1-batch", "noise on hidden nodes' readings: the 13 input channels, loss masks and masked labels of a training batch identical to the bit",
              bool(torch.equal(xa, xb) and torch.equal(ma, mb_) and torch.equal(ya * ma.long(), yb * mb_.long())))
    # B0.3 — feature equality (a) validation origins, all observed as inputs, whole window; (b) 20 training masks; (c) R; (d) D0 zeroing
    def reference(su_, origins, inp_):
        """Independent reference in double precision: einsum over the window of Rf masked by the input indicator."""
        om = inp_.astype("float64"); Rw = np.stack([su_.Rf.cpu().double().numpy()[np.asarray(origins) - k] for k in reversed(range(p4b.T_IN))], -1) * om[None, :, None]
        num = np.einsum("nm,bmt->bnt", su_.M64, Rw); den = su_.M64 @ om
        return np.where(den[None, :, None] > 0, num / np.where(den > 0, den, 1.0)[None, :, None], 0.0), den
    va64 = su.va[:64]; xv, _, _ = su.batch(va64, su.obs, su.val); ref, den = reference(su, va64, su.obs)
    d_a = float(np.abs(xv[:, 11].cpu().double().numpy() - ref).max())
    Mo = su.M64[:, su.obs]; dsum = Mo.sum(1); zn = np.where(dsum > 0, (su.Rf.cpu().double().numpy()[va64][:, su.obs] @ Mo.T) / np.where(dsum > 0, dsum, 1.0), 0.0)
    d_diag = float(np.abs(xv[:, 11, :, -1].cpu().double().numpy() - zn).max())
    log.check("B0.3a", "F on 64 validation origins (inputs = observed) equals the double-precision reference over the whole window within 1e-4, and the diagnostic's propagated mean at the origin",
              d_a <= 1e-4 and d_diag <= 1e-4, f"max |diff| window {d_a:.2e}, origin vs diagnostic formula {d_diag:.2e}")
    rmask = p4b.rng(0, p4b.K_MASKS); d_b = d_b64 = 0.0; tiny = 0; unreached_ok = True; r_ok = True
    for i in range(20):
        inp_i, tgt_i, _ = su.batch_mask(rmask); bt_i = su.tr[32 * i:32 * i + 32]
        xi, _, _ = su.batch(bt_i, inp_i, tgt_i); ref_i, den_i = reference(su, bt_i, inp_i); num64, den64 = su.feature64(xi[:, 0], inp_i)
        f64 = np.where(den64[None, :, None] > 0, num64 / np.where(den64 > 0, den64, 1.0)[None, :, None], 0.0)
        d_b = max(d_b, float(np.abs(xi[:, 11].cpu().double().numpy() - ref_i).max())); d_b64 = max(d_b64, float(np.abs(f64 - ref_i).max()))
        tiny += int(((den_i > 0) & (den_i <= 1e-6)).sum()); un = den_i == 0
        unreached_ok &= bool((xi[:, 11][:, torch.as_tensor(un, device=su.dev)].abs().sum() == 0) and (xi[:, 12][:, torch.as_tensor(un, device=su.dev)].abs().sum() == 0))
        r_ok &= bool(np.array_equal(xi[:, 12, :, 0].cpu().numpy()[0], (den_i > 0).astype("float32")))
    log.check("B0.3b", "F on 20 training masks equals the reference over the whole window, both unconverted (float64) and as the float32 tensor the network receives, within 1e-4; unreachable nodes F = 0 and R = 0 in the tensor",
              d_b <= 1e-4 and d_b64 <= 1e-12 and unreached_ok, f"max |diff| float32 tensor {d_b:.2e}, float64 {d_b64:.2e}; nodes with mass in (0, 1e-6]: {tiny} over 20 masks")
    log.check("B0.3c", "R equals the indicator of a positive propagated mass in every mask", r_ok)
    su0 = SetupGF("madrid", 0); su0.arm = "D0"; x_d0, _, _ = su0.batch(bt, inp, tgt); x_d1, _, _ = su.batch(bt, inp, tgt)
    xv0, _, _ = su0.batch(va64, su.obs, su.val)
    keep = [i for i in range(13) if i not in D0_ZEROED]
    log.check("B0.3d", "D0: channels 0-3 and F exactly zero in a training batch and a validation batch; the other channels identical to D1's",
              bool(x_d0[:, D0_ZEROED].abs().sum() == 0 and xv0[:, D0_ZEROED].abs().sum() == 0 and torch.equal(x_d0[:, keep], x_d1[:, keep]) and torch.equal(xv0[:, keep], xv[:, keep])))
    log.check("6", "node sets, origins, class weights, normalisation and historical average identical across arms", su0.fingerprints() == su.fingerprints())
    src = Path(__file__).read_text(); body = src.split("def _dev_run(")[1].split("def final_up_to_date(")[0]
    log.check("B0.5", "no reference to test origins or test nodes in the development, extension and final code", "su.te" not in body and "su.test" not in body)
    log.check("derived", "the derived block equals the mechanical derivation from e13.py (substitution table)", derived_block_matches())
    try:
        rc = struct(argparse.Namespace()); log.check("B0.5-struct", "I3 reproduction agrees with e13_a0_struct.json on the shared quantities", rc == 0)
    except Exception as e:  # noqa: BLE001
        log.check("B0.5-struct", f"I3 reproduction failed: {e}", False)
    cfg = {"preflight": "E13B run-dir test", "stamp": datetime.now(timezone.utc).isoformat()}
    p4b.run_dir(RUNS / "e13b_preflight_dirs", cfg)
    try:
        p4b.run_dir(RUNS / "e13b_preflight_dirs", cfg); blocked = False
    except FileExistsError:
        blocked = True
    log.check("9", "an existing run folder blocks the launch", blocked)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test metrics refused while the E13B signature line is blank", guard)
    try:
        gate("dev"); gated = False
    except PermissionError as e:
        gated = True; log(f"[INFO] gate refuses dev now: {e}")
    log.check("gate", "the launch gate refuses `dev` before signature / tag / B0.2 / P4R revision", gated)
    log(f"PREFLIGHT: {log.fail} failure(s) — no model update was performed"); log.save()
    return 0 if log.fail == 0 else 1


def pre(args):
    """E13Bpre.md: the authorised preflight updates — B0.1 (four trajectories of 50 updates: D1 and D0, original and perturbed,
    each arm compared with its own perturbed copy bit for bit) and the benchmark (D1 and D0, 60 updates, three repetitions,
    seconds per update as (t60 - t10)/50, median). Refuses unless E13Bpre.md is signed, its tag reachable and the tree clean."""
    pre_tag = _git("describe", "--tags", "--abbrev=0", "--match", "paper4-E13Bpre-*").stdout.strip()
    if not pre_tag:
        raise PermissionError("no E13Bpre tag reachable from HEAD")
    if _git("diff", "--quiet", pre_tag, "HEAD", "--", *FROZEN_PATHS, "protocol/paper4/E13Bpre.md").returncode != 0 or not git_clean():
        raise PermissionError("frozen files, E13Bpre.md or the working tree differ from the E13Bpre tag")
    p4b.require_signed(PREPRE)
    path = RUNS / "e13b_pre.json"
    if path.exists():
        raise FileExistsError(f"{path} exists")
    out = {"protocol": "E13Bpre", "tag": pre_tag, "started": datetime.now(timezone.utc).isoformat(), "B0.1": {}, "benchmark": {}, "updates": 0}
    su = SetupGF("madrid", 0); pert = _perturbed_copy(su, np.random.default_rng(12), perturb_val_labels=False)
    for arm in ARMS:
        o0 = train_gf(su, arm, None, 50, CONFIGS["C1"], p4b.K_INIT, ck_every=50, save_states=True, keep_losses=True)
        o1 = train_gf(pert, arm, None, 50, CONFIGS["C1"], p4b.K_INIT, ck_every=50, save_states=True, keep_losses=True); out["updates"] += 100
        same_loss = o0["losses"] == o1["losses"]; same_par = all(torch.equal(o0["states"][50][k], o1["states"][50][k]) for k in o0["states"][50])
        Pa, _ = p4b.predict(o0["net"], su, None, su.va[:64], su.obs, su.val); Pb, _ = p4b.predict(o1["net"], pert, None, su.va[:64], su.obs, su.val)
        same_pred = bool(np.array_equal(Pa, Pb))
        out["B0.1"][arm] = {"same_losses": same_loss, "same_parameters": same_par, "same_validation_predictions": same_pred, "pass": same_loss and same_par and same_pred,
                            "hidden_in_batches": o0["hidden_in_batches"] + o1["hidden_in_batches"]}
        print(f"B0.1 {arm}: losses {same_loss} parameters {same_par} predictions {same_pred}")
    for arm in ARMS:
        spu = []
        for rep in range(3):
            o = train_gf(su, arm, None, 60, CONFIGS["C1"], p4b.K_INIT, ck_every=10, save_states=False); out["updates"] += 60
            t = {d["update"]: d["seconds"] for d in o["trajectory"]}; spu.append((t[60] - t[10]) / 50)
        out["benchmark"][arm] = {"seconds_per_update": spu, "median": float(np.median(spu)), "device": str(su.dev)}
        print(f"benchmark {arm}: s/update {[round(v, 4) for v in spu]} median {np.median(spu):.4f}")
    out["environment"] = environment(); out["load_avg"] = list(os.getloadavg()); out["written"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(out, indent=1)); print("->", path, p4b.sha256(path, 16))
    return 0 if all(v["pass"] for v in out["B0.1"].values()) else 1


def main():
    ap = argparse.ArgumentParser(description="E13B — B0 and B1 (GF variant, arms D1/D0, regime I0)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("preflight", "pre", "struct", "b0-synth", "adequacy", "test", "analysis"):
        sp.add_parser(n)
    acc = sp.add_parser("b0-accept"); acc.add_argument("--by", required=True); acc.add_argument("--note-commit", required=True)
    pr = sp.add_parser("p4r-revision"); pr.add_argument("--commit", required=True); pr.add_argument("--receipt-commit", required=True); pr.add_argument("--by", required=True)
    for n in ("dev", "final"):
        q = sp.add_parser(n); q.add_argument("--city", required=True, choices=CITIES); q.add_argument("--seed", type=int, required=True)
        q.add_argument("--arm", required=True, choices=ARMS); q.add_argument("--regime", default="I0", choices=REGIMES)
        if n == "dev":
            q.add_argument("--deviation", default=None, help="commit of the dated deviation note authorising a deliberate re-run")
    x = sp.add_parser("extend"); x.add_argument("--city", required=True, choices=CITIES); x.add_argument("--arm", required=True, choices=ARMS); x.add_argument("--regime", default="I0", choices=REGIMES)
    c = sp.add_parser("campaign"); c.add_argument("--phase", required=True, choices=("dev", "final"))
    a = ap.parse_args()
    E13B.mkdir(parents=True, exist_ok=True)
    return {"preflight": preflight, "pre": pre, "struct": struct, "b0-synth": b0_synth, "b0-accept": b0_accept, "p4r-revision": p4r_revision, "dev": dev,
            "extend": extend, "final": final, "adequacy": adequacy, "test": test, "analysis": analysis, "campaign": campaign}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
