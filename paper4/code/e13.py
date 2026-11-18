#!/usr/bin/env python3
"""
E13 — A0 correctness checks and A1: training adequacy and coordinates (`protocol/paper4/E13.md`).
=================================================================================================
`p4b.py` and `e9.py` are imported unchanged. This file adds: the coordinate channels of regime I1
(a subclass of `p4b.Setup`), a training loop with weight decay and a checkpoint every 500 updates up
to the cap, the nested selection per split, the final trajectory, the A0 checks, the launch gate, the
group extension, the global lock and the two-way block bootstrap with multiplicities shared across
splits, arms and regimes.

Commands (from a clean worktree of the E13 tag; $PY = the interpreter of paper4/ENV.txt):

  preflight                       E11/E9 assertions at f = 20 % + A0.1, A0.4, A0.5; no training beyond
                                  50 bitwise-compared updates. The only command allowed before the signature.
  a0-synth                        A0.2 synthetic dependent / independent processes. Exit 1 on failure or anomaly.
  a0-accept --by NAME --note-commit H
                                  the responsible author records that an A0.2 anomaly was explained in a dated
                                  note (commit H) and A1 may start; refused if A0.2 'dependent' failed.
  a0-identifier                   A0.3 coordinate sensitivities (descriptive).
  dev   --city C --seed S --arm A --regime R
                                  four development trajectories C1–C4 to the group's cap, selection on
                                  validation-hidden of the same split. Requires A0.2 pass or a0-accept.
  extend --city C --arm A --regime R
                                  E13 extension: cap 20 000 for every cell of the group (all seeds, all four
                                  configurations), reproduction of the 10 000 curve checked, selection repeated.
  final --city C --seed S --arm A --regime R
                                  final trajectory with the selected configuration and cap; new initialisation.
  adequacy                        adequacy report and lock over the 60 cells; writes e13_adequacy.json.
  test                            test predictions for the 60 final runs; refused unless the lock recomputed now
                                  equals the committed lock file and the signature line is filled.
  analysis                        per-horizon wCE, V, intervals, centred p-values, sup-t band, eligibility.
  campaign --phase dev|final      every cell of a phase in the E13 order, skipping only cells that are up to date.

No test origin is read by any command except `test`.
"""
import argparse
import copy
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9   # noqa: E402  (registers London; GRID; targets; adjacency)
from e11 import Log, cadence_ok  # noqa: E402

ROOT = p4b.ROOT
RUNS = ROOT / "paper4" / "runs"
E13 = RUNS / "e13"
PREREG = ROOT / "protocol" / "paper4" / "E13.md"
CITIES = ("madrid", "london", "melbourne")
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("G0", "G1")
REGIMES = ("I0", "I1")
F = 0.20
CAP0, CAP1 = 10_000, 20_000
CK_EVERY = 500
CONFIGS = {"C1": dict(lr=1e-3, dropout=0.0, wd=0.0),      # historical optimiser configuration (Adam, no weight decay)
           "C2": dict(lr=1e-3, dropout=0.3, wd=1e-4),
           "C3": dict(lr=3e-4, dropout=0.0, wd=1e-4),
           "C4": dict(lr=3e-4, dropout=0.3, wd=1e-4)}
K_DEV_INIT = 7                      # development initialisation stream; the final uses p4b.K_INIT = 6
BOOT_SEED = 20261118
B_REPS = 4000
MARGIN = 3.0
REPRO_TOL = 1e-9                    # reproduction of the 10 000 curve by the extended run (declared)


# ---------------------------------------------------------------- environment, gate, records -------------

FROZEN_PATHS = ["paper4/code/p4b.py", "paper4/code/e9.py", "paper4/code/e11.py", "paper4/code/e13.py", "protocol/paper4/E13.md"]


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)


def git_describe():
    """Exact tag of HEAD, if any (kept for the records)."""
    return _git("describe", "--tags", "--exact-match").stdout.strip()


def frozen_tag():
    """The E13 tag that froze code and protocol: the nearest `paper4-E13-*` tag reachable from HEAD. HEAD may be
    later than the tag (commits that deposit records), but the frozen files must be identical to the tag."""
    return _git("describe", "--tags", "--abbrev=0", "--match", "paper4-E13-*").stdout.strip()


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
                                                  "e13.py": p4b.sha256(Path(__file__), 16)},
            "prereg_sha16": p4b.sha256(PREREG, 16) if PREREG.exists() else None, "load_avg": list(os.getloadavg())}


def _report_matches_version(report, tag):
    """A report belongs to this frozen version: same frozen tag, same fingerprints of the code files and of the protocol."""
    env = report.get("environment", {}); mine = environment()
    return env.get("frozen_tag") == tag and env.get("code_sha16") == mine["code_sha16"] and env.get("prereg_sha16") == mine["prereg_sha16"]


def gate(phase):
    """Launch constraints common to every command after the signature (E13.md, Order and A0): an E13 tag reachable
    from HEAD with code and protocol identical to it (later commits may deposit records), clean working tree, signature
    line filled, and for A1 commands the A0 reports produced by this same frozen version (tag, code and protocol
    fingerprints)."""
    tag = frozen_tag()
    if not tag.startswith("paper4-E13-"):
        raise PermissionError(f"no E13 tag reachable from HEAD (git describe --match paper4-E13-*: {tag!r})")
    if not frozen_unchanged(tag):
        raise PermissionError(f"code or protocol differ from the frozen tag {tag} ({', '.join(FROZEN_PATHS)}): a new signed tag is required")
    if not git_clean():
        raise PermissionError("working tree not clean (modified tracked files or untracked files): the run would not be from the frozen version")
    p4b.require_signed(PREREG)
    if phase in ("dev", "extend", "final", "test", "analysis"):
        a0 = RUNS / "e13_a0_synth.json"; a3 = RUNS / "e13_a0_identifier.json"
        if not a0.exists():
            raise PermissionError("A0.2 (a0-synth) has not been run")
        if not a3.exists():
            raise PermissionError("A0.3 (a0-identifier) has not been run: it is required before A1 (no performance criterion attached)")
        z = json.loads(a0.read_text()); z3 = json.loads(a3.read_text())
        if not _report_matches_version(z, tag) or not _report_matches_version(z3, tag):
            raise PermissionError("the A0 reports were produced by another version (tag, e13.py or protocol fingerprint differ)")
        kinds = z["kinds"]
        if kinds["dependent"]["verdict"] != "pass":
            raise PermissionError("A0.2 dependent condition failed: A1 cannot start (E13.md A0.2)")
        if kinds["independent"]["verdict"] != "pass":
            acc = RUNS / "e13_a0_resolution.json"
            if not acc.exists():
                raise PermissionError("A0.2 independent condition shows an anomaly: explain it in a dated note and record a0-accept")
            r = json.loads(acc.read_text())
            if r.get("a0_synth_sha16") != p4b.sha256(a0, 16):
                raise PermissionError("a0-accept refers to another A0.2 report")
    return tag


def record13(d, payload):
    rec = p4b.record(d, {"environment": environment(), **payload})
    return rec


# ---------------------------------------------------------------- setup with coordinates ---------------

class SetupE13(p4b.Setup):
    """E9 setup at f = 0.20 with regime I0 (E9 inputs, 11 channels) or I1 (+2 standardised UTM channels)."""

    def __init__(s, city, seed, regime, perm_seed=None, device=None):
        super().__init__(city, p4b.CITY[city]["roads"], seed=seed, grid=e9.GRID[city], targets=e9.targets(F), device=device)
        s.regime = regime
        xy = np.asarray(s.al["coords"], dtype="float64")                     # (K, 2) UTM
        mu, sd = xy[s.obs].mean(0), xy[s.obs].std(0) + 1e-6                   # observed nodes of the split only
        z = ((xy - mu) / sd).astype("float32")
        s.coord_perm = None
        if perm_seed is not None:                                            # A0.3b: pairs permuted among observed nodes, fixed
            idx = np.flatnonzero(s.obs); r = np.random.default_rng([int(perm_seed), 13])
            z = z.copy(); z[idx] = z[r.permutation(idx)]; s.coord_perm = int(perm_seed)
        s.XY = torch.tensor(z, device=s.dev)
        s._fix_cin()

    def _fix_cin(s):
        s.c_in = 13 if s.regime == "I1" else 11

    def batch(s, origins, inp, tgt, static=False):
        x, y, m = super().batch(origins, inp, tgt, static)
        if s.regime == "I1":
            B, _, K, T = x.shape
            x = torch.cat([x, s.XY.T.view(1, 2, K, 1).expand(B, 2, K, T)], 1)
        return x, y, m

    def inject(s, r, flow, occ, C):
        """A0.2: replace the target processes by synthetic ones (same shapes and timestamps) and rebuild."""
        s.r, s.flow, s.occ, s.C = r.astype("float32"), flow.astype("float32"), occ.astype("float32"), C.astype("int64")
        s._stats(); s._tensors(); s._fix_cin()


def cell_id(city, seed, arm, regime):
    return f"{city}_s{seed}_{arm}_{regime}"


def group_id(city, arm, regime):
    return f"{city}_{arm}_{regime}"


# ---------------------------------------------------------------- training loop --------------------------

def train_e13(su, arm, A, cap, cfg, init_stream, log=None, ck_every=CK_EVERY, save_states=True, keep_losses=False):
    """p4b.train with weight decay, an initialisation stream and checkpoints every `ck_every` up to `cap`.
    Returns trajectory, states at every checkpoint (CPU), the per-step training losses if asked, counters.
    Never touches test origins."""
    graph = arm != "G0"
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


def adequacy_of(traj, cap):
    """Minimum not at the cap; improvement between the last two checkpoints ≤ 0.5 % of the validation wCE."""
    v = [t["val_wce"] for t in traj]; u = [t["update"] for t in traj]
    i = int(np.argmin(v)); impr = (v[-2] - v[-1]) / v[-2] if len(v) > 1 else 0.0
    return {"min_update": u[i], "min_at_cap": bool(u[i] == cap), "last_improvement_frac": float(impr),
            "pass": bool(u[i] != cap and impr <= 0.005)}


# ---------------------------------------------------------------- indices --------------------------------

def _index(name):
    p = E13 / name
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def _append(name, row):
    (E13 / name).open("a").write(json.dumps(row) + "\n")


def _next_attempt(cid):
    """Attempt counter per cell, incremented before a folder is created: an interrupted attempt (folder without
    run.json, never indexed) does not block the next one; the E11 rule still blocks an identical (cell, cap, attempt)."""
    p = E13 / "attempts.json"; a = json.loads(p.read_text()) if p.exists() else {}
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
    p = E13 / f"extension_{gid}.json"
    return json.loads(p.read_text()) if p.exists() else None


def group_cap(city, arm, regime):
    st = extension_status(group_id(city, arm, regime))
    return CAP1 if st else CAP0


def all_cells():
    return [(c, s, a, r) for c in CITIES for s in SEEDS for a in ARMS for r in REGIMES]


# ---------------------------------------------------------------- dev / extend / final -------------------

def _dev_run(city, seed, arm, regime, cap, reproduce_from=None, log_print=False, attempt=1, deviation=None):
    """One development run (four configurations). `attempt` enters the folder fingerprint, so that a run
    interrupted before its record was written leaves a folder without run.json (never indexed) and the
    resumed attempt gets its own folder; the E11 rule 'an existing folder blocks the launch' still holds
    for an identical (cell, cap, attempt)."""
    su = SetupE13(city, seed, regime)
    A, info = e9.adjacency(su, arm)
    cid = cell_id(city, seed, arm, regime)
    d = p4b.run_dir(E13 / "dev", {"protocol": "E13", "phase": "dev", "cell": cid, "cap": cap, "configs": CONFIGS, "f": F,
                                  "grid": su.G, "fingerprints": su.fingerprints(), "extension_of": reproduce_from["dir"] if reproduce_from else None,
                                  "attempt": attempt, "deviation": deviation})
    log = Log(d / "log.txt"); log(f"E13 dev {cid} cap {cap} -> {d}")
    out, repro = {}, {}
    for name, cfg in CONFIGS.items():
        o = train_e13(su, arm, A, cap, cfg, K_DEV_INIT, log=log if log_print else None, save_states=False)
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
    """Extension of E13.md: every cell of the group to 20 000, all four configurations, reproduction checked."""
    gate("extend")
    gid = group_id(args.city, args.arm, args.regime); sp = E13 / f"extension_{gid}.json"
    st = extension_status(gid)
    if st and st["status"] == "complete":
        raise PermissionError(f"group {gid} already extended once: a second failure is a feasibility limit (E13.md)")
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
    su = SetupE13(args.city, args.seed, args.regime)
    A, info = e9.adjacency(su, args.arm)
    d = p4b.run_dir(E13 / "final", {"protocol": "E13", "phase": "final", "cell": cid, "cap": cap, "config": dv["selected_config"], "dev_dir": dv["dir"]})
    log = Log(d / "log.txt"); log(f"E13 final {cid} config {dv['selected_config']} cap {cap} -> {d}")
    o = train_e13(su, args.arm, A, cap, cfg, p4b.K_INIT, log=log, save_states=True)
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


# ---------------------------------------------------------------- adequacy / lock / test -----------------

def compute_adequacy():
    exts = {p.stem.replace("extension_", ""): json.loads(p.read_text())["status"] for p in E13.glob("extension_*.json")}
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
    (RUNS / "e13_adequacy.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: rep[k] for k in ("missing_dev", "missing_final", "final_stale", "dev_failures_pending",
                                          "dev_failures_after_extension", "final_failures", "excluded_from_adequacy_statements", "lock", "lock_sha16")}, indent=1))
    print("dev_failures_pending: run `extend` for their groups, then `final` again; "
          "dev_failures_after_extension and final_failures: feasibility limit / inconclusive, excluded from adequacy-conditioned statements")
    return 0 if rep["lock"] else 1


def test(args):
    gate("test")
    lock_path = RUNS / "e13_adequacy.json"
    saved = json.loads(lock_path.read_text())
    now = compute_adequacy()
    if not saved.get("lock") or saved.get("lock_sha16") != now["lock_sha16"]:
        raise PermissionError("the lock file does not match the current records, or the lock is not satisfied: run `adequacy` and commit it")
    if not git_committed_unchanged(lock_path.relative_to(ROOT)):
        raise PermissionError("e13_adequacy.json is not committed unchanged (git add -f, commit) — the protocol requires the committed report")
    for c, s, a, r in all_cells():
        cid = cell_id(c, s, a, r); fn = latest_final(cid); d = Path(fn["dir"])
        if (d / "test_cells.npz").exists():
            old = np.load(d / "test_cells.npz")
            if str(old["lock_sha16"]) != now["lock_sha16"]:
                raise PermissionError(f"{d / 'test_cells.npz'} was produced under another lock ({old['lock_sha16']}); move it aside, it is not overwritten")
            continue
        su = SetupE13(c, s, r); A, _ = e9.adjacency(su, a)
        net = p4b.GWN(su.c_in, a != "G0", dropout=fn["cfg"]["dropout"]).to(su.dev)
        net.load_state_dict(torch.load(d / "selected_state.pt"))
        At = torch.tensor(A, device=su.dev) if a != "G0" else None
        P, Y = p4b.predict(net, su, At, su.te, su.obs, su.test)
        np.savez_compressed(d / "test_cells.npz", p=P.astype("float32"), y=Y.astype("int8"), origins=su.te, cells=su.cells,
                            test_nodes=su.test, W=su.W, ts=su.ts[su.te].astype("datetime64[m]"), lock_sha16=now["lock_sha16"])
        print(cid, "test wCE (mean over horizons)", round(float(np.mean([p4b.wce_np(P[:, :, h], Y[:, :, h], su.W) for h in range(P.shape[2])])), 5), flush=True)
    return 0


# ---------------------------------------------------------------- analysis -------------------------------

def per_horizon_mean(num, den):
    """Mean over horizons of the per-horizon weighted ratios (E13.md, Unit of analysis): NOT the pooled ratio."""
    num = np.asarray(num, dtype="float64"); den = np.maximum(np.asarray(den, dtype="float64"), 1e-12)
    return float(np.mean(num / den))


def _week_index(ts):
    iso = pd.DatetimeIndex(ts).isocalendar()
    return (iso.year.to_numpy() * 100 + iso.week.to_numpy())


def analysis(args):
    gate("analysis")
    adeq = json.loads((RUNS / "e13_adequacy.json").read_text())
    if adeq["lock_sha16"] != compute_adequacy()["lock_sha16"]:
        raise PermissionError("records changed since the lock")
    excluded = set(adeq["excluded_from_adequacy_statements"])
    out = {"written": datetime.now(timezone.utc).isoformat(), "B": B_REPS, "seed": BOOT_SEED, "metric": "mean over horizons of per-horizon wCE on test-hidden nodes",
           "environment": environment(), "cities": {}}
    H = len(p4b.HORIZONS)
    for ci, city in enumerate(CITIES):
        LM, WM, cellof, weekof = {}, {}, {}, {}; blocks = weeks = None
        for s in SEEDS:
            for a in ARMS:
                for r in REGIMES:
                    z = np.load(Path(latest_final(cell_id(city, s, a, r))["dir"]) / "test_cells.npz")
                    if str(z["lock_sha16"]) != adeq["lock_sha16"]:
                        raise PermissionError(f"test file of {cell_id(city, s, a, r)} belongs to another lock")
                    if blocks is None:
                        blocks, weeks = np.unique(z["cells"]), np.unique(_week_index(z["ts"]))
                    P, Y, W = z["p"].astype("float64"), z["y"].astype("int64"), z["W"].astype("float64")
                    v = Y >= 0; Yc = np.clip(Y, 0, 2)
                    pt = np.clip(np.take_along_axis(P, Yc[..., None], -1)[..., 0], 1e-7, 1)
                    w = np.where(v, W[Yc], 0.0)
                    LM[(s, a, r)] = w * -np.log(pt); WM[(s, a, r)] = w                     # (origins, nodes, H), per horizon
                    cellof[(s, a, r)] = np.searchsorted(blocks, z["cells"]); weekof[(s, a, r)] = np.searchsorted(weeks, _week_index(z["ts"]))
        nb, nw = len(blocks), len(weeks); rng = np.random.default_rng([BOOT_SEED, ci])

        def wce_with(key, mb, mw):                      # mean over horizons of per-horizon weighted ratios
            wn = (mb[cellof[key]][None, :] * mw[weekof[key]][:, None])[..., None]
            return per_horizon_mean((LM[key] * wn).sum((0, 1)), (WM[key] * wn).sum((0, 1)))

        def contrasts(mb, mw):
            res = {}
            for r in REGIMES:
                vs = [100.0 * (wce_with((s, "G0", r), mb, mw) - wce_with((s, "G1", r), mb, mw)) / wce_with((s, "G0", r), mb, mw) for s in SEEDS]
                res[f"V_G1_{r}"] = float(np.mean(vs)); res[f"V_G1_{r}_by_seed"] = vs
            res["Delta_I1_minus_I0"] = res["V_G1_I1"] - res["V_G1_I0"]
            for a in ARMS:
                vs = [100.0 * (wce_with((s, a, "I0"), mb, mw) - wce_with((s, a, "I1"), mb, mw)) / wce_with((s, a, "I0"), mb, mw) for s in SEEDS]
                res[f"static_benefit_{a}"] = float(np.mean(vs))
            return res
        obs = contrasts(np.ones(nb), np.ones(nw)); keys = [k for k in obs if not k.endswith("_by_seed")]
        reps = {k: np.empty(B_REPS) for k in keys}
        for b in range(B_REPS):                        # one multiplicity vector per unit type, shared by all splits, arms, regimes
            mb = np.bincount(rng.integers(0, nb, nb), minlength=nb).astype("float64")
            mw = np.bincount(rng.integers(0, nw, nw), minlength=nw).astype("float64")
            cb = contrasts(mb, mw)
            for k in keys:
                reps[k][b] = cb[k]
        res = {"n_blocks": int(nb), "n_weeks": int(nw), "observed": obs}
        for k in keys:
            lo, hi = np.percentile(reps[k], [2.5, 97.5]); centred = reps[k] - reps[k].mean()
            res[k] = {"estimate": obs[k], "ci95": [float(lo), float(hi)], "p_centred": float(np.mean(np.abs(centred) >= abs(obs[k]))),
                      "sign": "favourable" if lo > 0 else ("unfavourable" if hi < 0 else "inconclusive"),
                      "margin": "reached" if lo >= MARGIN else ("advantage>=3 excluded" if hi < MARGIN else "not excluded")}
        for r in REGIMES:                               # eligibility: no cell of the contrast excluded
            cells_r = {cell_id(city, s, a, r) for s in SEEDS for a in ARMS}
            res[f"V_G1_{r}"]["eligible_for_adequacy_statements"] = not (cells_r & excluded)
            res[f"V_G1_{r}"]["excluded_cells"] = sorted(cells_r & excluded)
        res["_reps"] = {k: reps[k] for k in ("V_G1_I0", "V_G1_I1")}
        out["cities"][city] = res
    names, est, R = [], [], []
    for city in CITIES:
        for k in ("V_G1_I0", "V_G1_I1"):
            names.append(f"{city}:{k}"); est.append(out["cities"][city][k]["estimate"]); R.append(out["cities"][city]["_reps"][k])
    R = np.stack(R, 1); sd = R.std(0) + 1e-12; T = np.abs((R - R.mean(0)) / sd).max(1); q = float(np.percentile(T, 95))
    out["supt_95"] = {n: [float(e - q * s_), float(e + q * s_)] for n, e, s_ in zip(names, est, sd)}
    for city in CITIES:
        out["cities"][city].pop("_reps")
    # mechanical statements on the primary I0 contrasts, conditioned on eligibility
    el = {c: out["cities"][c]["V_G1_I0"]["eligible_for_adequacy_statements"] for c in CITIES}
    helps = sum(1 for c in CITIES if el[c] and out["cities"][c]["V_G1_I0"]["sign"] == "favourable" and out["cities"][c]["V_G1_I0"]["estimate"] >= MARGIN)
    below = all(el[c] and out["supt_95"][f"{c}:V_G1_I0"][1] < MARGIN for c in CITIES)
    raw = ("spatial exchange helps at 20 % under adequate training" if helps >= 2 else
           "gain below the prespecified 3-point margin at 20 % under adequate training" if below else "undetermined")
    out["confirmatory"] = False                                          # always: the confirmatory statement is produced by the
    out["statement"] = f"PROVISIONAL (marginal intervals, before Holm over the P4R family of 24): {raw}"   # campaign-wide analysis after Holm
    if helps >= 2:
        out["statement"] += " — candidate only; the confirmatory positive statement is produced after the family-wise correction"
    out["statement_counts"] = {"cities_helps": helps, "eligible": el, "excluded_cells": sorted(excluded)}
    out["note"] = "Holm over the P4R family of 24 is applied when A2/A3 are in; the six p_centred values are unadjusted until then."
    (RUNS / "e13_analysis.json").write_text(json.dumps(out, indent=1, default=float))
    for city in CITIES:
        for k in ("V_G1_I0", "V_G1_I1", "Delta_I1_minus_I0"):
            r = out["cities"][city][k]
            print(f"{city:9s} {k:18s} {r['estimate']:7.3f}  CI {r['ci95'][0]:7.3f} {r['ci95'][1]:7.3f}  p {r['p_centred']:.4f}  {r['sign']} / {r['margin']}")
    print("sup-t 95 %:", {k: [round(v[0], 2), round(v[1], 2)] for k, v in out["supt_95"].items()})
    print("statement:", out["statement"], out["statement_counts"])
    return 0


# ---------------------------------------------------------------- A0 -------------------------------------

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


def preflight(args):
    RUNS.mkdir(parents=True, exist_ok=True); E13.mkdir(exist_ok=True)
    log = Log(RUNS / "e13_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E13 preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty}) — tag {git_describe()!r}")
    log(f"code p4b.py {p4b.sha256(Path(p4b.__file__), 16)} · e9.py {p4b.sha256(Path(e9.__file__), 16)} · e13.py {p4b.sha256(Path(__file__), 16)} · torch {torch.__version__}")
    # E9 controls at f = 0.20
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
    log.check("A0.4", "London data files differ from Madrid's", all(fm[k] != fl[k] for k in fm), json.dumps({"madrid": fm, "london": fl}))
    fps_all = {}
    for regime in REGIMES:
        su = SetupE13("madrid", 0, regime)
        whole = all(len(np.unique(su.lab[su.cells == c_])) == 1 for c_ in np.unique(su.cells))
        log.check(f"1a-{regime}", "node sets disjoint, non-empty, whole cells", whole and su.obs.any() and su.val.any() and su.test.any())
        r = p4b.rng(0, p4b.K_MASKS); bm = bt_ = 0; hidden = torch.as_tensor(~su.obs, device=su.dev)
        for _ in range(100):
            inp, tgt, _ = su.batch_mask(r); bm += int((inp & ~su.obs).sum() + (tgt & ~su.obs).sum())
            x, y, m = su.batch(su.tr[:32], inp, tgt)
            bt_ += int(x[:, :4][:, :, hidden].abs().sum().item() > 0) + int(x[:, 10][:, hidden].abs().sum().item() > 0) + int(m[:, hidden].abs().sum().item() > 0)
        log.check(f"1b-{regime}", "no hidden index in input mask or loss of 100 batches", bm == 0)
        log.check(f"1c-{regime}", "hidden nodes zero in dynamic channels, flag channel and loss tensor", bt_ == 0)
        log.check(f"ch-{regime}", f"input channels = {11 if regime == 'I0' else 13}", x.shape[1] == (11 if regime == "I0" else 13))
        allo = np.concatenate([su.tr, su.va, su.te]); gap = max(p4b.HORIZONS) + p4b.T_IN - 1
        log.check(f"2a-{regime}", "every origin admissible", all(cadence_ok(su.ts, int(t)) for t in allo))
        log.check(f"2b-{regime}", "no target of a period overlaps an input of the next", bool(su.tr.max() + gap < su.va.min() and su.va.max() + gap < su.te.min()))
        # 2c causality
        bt = su.tr[100:132]; inp, tgt, _ = su.batch_mask(p4b.rng(0, 99)); x0, _, _ = su.batch(bt, inp, tgt)
        sv = {k: getattr(su, k).clone() for k in ("Rf", "FL", "OC", "HAs")}; tmax = int(bt.max()); gen = torch.Generator(device="cpu").manual_seed(7)
        for k in sv:
            t_ = getattr(su, k); t_[tmax + 1:] = torch.randn(t_[tmax + 1:].shape, generator=gen).to(su.dev)
        x1, _, _ = su.batch(bt, inp, tgt)
        for k, v in sv.items():
            setattr(su, k, v)
        log.check(f"2c-{regime}", "causality: noise after the origin leaves the inputs identical to the bit", bool(torch.equal(x0, x1)))
        # 2d / 3 statistics from observed training cells only
        pert_all = _perturbed_copy(su, np.random.default_rng(11), perturb_val_labels=True)
        log.check(f"2d-{regime}", "noise on hidden nodes (all) leaves class weights, normalisation and historical average identical",
                  bool(np.array_equal(pert_all.W, su.W) and [pert_all.fmu, pert_all.fsd, pert_all.omu, pert_all.osd] == [su.fmu, su.fsd, su.omu, su.osd] and np.array_equal(pert_all.HA, su.HA)))
        f_ = np.bincount(su.C[:su.reg_end][:, su.obs].ravel(), minlength=4)[1:].astype("float64")
        log.check(f"3-{regime}", "class weights recomputed independently from observed training cells", bool(np.array_equal((f_.sum() / (np.maximum(f_, 1) * 3)).astype("float32"), su.W)))
        # A0.1: dynamic noise on all hidden nodes, classes replaced on test-hidden only (validation labels kept) ->
        #       identical inputs/loss masks, identical per-step training losses and parameters after 50 updates, identical validation predictions
        pert = _perturbed_copy(su, np.random.default_rng(12), perturb_val_labels=False)
        xa, ya, ma = su.batch(bt, inp, tgt); xb, yb, mb_ = pert.batch(bt, inp, tgt)
        same_in = bool(torch.equal(xa, xb) and torch.equal(ma, mb_) and torch.equal(ya * ma.long(), yb * mb_.long()))
        A1 = e9.adjacency(su, "G1")[0]
        o0 = train_e13(su, "G1", A1, 50, CONFIGS["C1"], p4b.K_INIT, ck_every=50, save_states=True, keep_losses=True)
        o1 = train_e13(pert, "G1", A1, 50, CONFIGS["C1"], p4b.K_INIT, ck_every=50, save_states=True, keep_losses=True)
        same_loss = o0["losses"] == o1["losses"]
        same_par = all(torch.equal(o0["states"][50][k], o1["states"][50][k]) for k in o0["states"][50])
        Pa, _ = p4b.predict(o0["net"], su, o0["A"], su.va[:64], su.obs, su.val); Pb, _ = p4b.predict(o1["net"], pert, o1["A"], su.va[:64], su.obs, su.val)
        same_pred = bool(np.array_equal(Pa, Pb))
        log.check(f"A0.1-{regime}", "noise on hidden nodes: inputs, loss masks, 50 per-step losses, parameters and validation predictions identical",
                  same_in and same_loss and same_par and same_pred, f"inputs {same_in} losses {same_loss} params {same_par} preds {same_pred}")
        if regime == "I1":
            # hidden coordinates perturbed: observed nodes' own channels identical; permuted copy changes only the coordinate channels
            pc = copy.copy(su); z = su.XY.clone(); z[~torch.as_tensor(su.obs, device=su.dev)] += 3.0; pc.XY = z
            xo, _, _ = su.batch(bt, inp, tgt); xp, _, _ = pc.batch(bt, inp, tgt); obs_t = torch.as_tensor(su.obs, device=su.dev)
            log.check("A0.1-I1-coords", "perturbing hidden nodes' coordinates leaves every channel of the observed nodes identical",
                      bool(torch.equal(xo[:, :, obs_t], xp[:, :, obs_t])))
            pm = SetupE13("madrid", 0, "I1", perm_seed=0)
            log.check("A0.3-perm", "permuted coordinates change only the two coordinate channels, among observed nodes",
                      bool(torch.equal(su.batch(bt, inp, tgt)[0][:, :11], pm.batch(bt, inp, tgt)[0][:, :11])) and not torch.equal(su.XY, pm.XY)
                      and bool(torch.equal(su.XY[~obs_t], pm.XY[~obs_t])))
        # 6 fingerprints identical across arms and regimes; 7; 8; determinism; initialisation streams
        for arm in ARMS:
            s_arm = SetupE13("madrid", 0, regime); e9.adjacency(s_arm, arm); fps_all[(regime, arm)] = s_arm.fingerprints()
        log.check(f"7-{regime}", "updates equal the cap exactly; no hidden node in any batch", o0["updates"] == 50 and o0["hidden_in_batches"] == 0)
        P, Y = p4b.predict(o0["net"], su, o0["A"], su.va, su.obs, su.val)
        d8 = RUNS / "e13_preflight_cells"; d8.mkdir(exist_ok=True); np.savez_compressed(d8 / f"val_G1_s0_{regime}.npz", p=P, y=Y)
        z8 = np.load(d8 / f"val_G1_s0_{regime}.npz")
        log.check(f"8-{regime}", "per-cell file reconstructs the aggregate validation wCE within 1e-9", abs(p4b.wce_np(z8["p"], z8["y"], su.W) - o0["trajectory"][-1]["val_wce"]) < 1e-9)
        o2 = train_e13(su, "G1", A1, 50, CONFIGS["C1"], p4b.K_INIT, ck_every=50, save_states=True)
        dmax = max(float((o0["states"][50][k].float() - o2["states"][50][k].float()).abs().max()) for k in o0["states"][50])
        log(f"[INFO] det-{regime} two identical runs (50 updates): max |Δ parameter| = {dmax:.3e}" + (" (bitwise identical)" if dmax == 0 else " (residual non-determinism, declared)"))
        od = train_e13(su, "G1", A1, 50, CONFIGS["C1"], K_DEV_INIT, ck_every=50, save_states=False)
        log.check(f"init-{regime}", "development and final initialisation seeds differ", od["init_seed"] != o0["init_seed"])
    log.check("6", "node sets, origins, class weights, normalisation and historical average identical across arms and regimes",
              all(v == list(fps_all.values())[0] for v in fps_all.values()))
    # A0.5: the development/selection/final code reads no test origin (static); test sets per seed listed
    src = Path(__file__).read_text(); body = src.split("def _dev_run(")[1].split("def final_up_to_date(")[0]
    log.check("A0.5", "no reference to test origins or test nodes in the development, extension and final code", "su.te" not in body and "su.test" not in body)
    sets = {city: {s: int(p4b.node_sets(p4b.grid_cells(p4b.align_graph(city, p4b.CITY[city]["roads"])["coords"], e9.GRID[city]), s, targets=tuple(e9.targets(F))).tolist().count(2)) for s in SEEDS} for city in CITIES}
    log(f"[INFO] test-hidden nodes per (city, seed): {json.dumps(sets)}")
    cfg = {"preflight": "E13 run-dir test", "stamp": datetime.now(timezone.utc).isoformat()}
    p4b.run_dir(RUNS / "e13_preflight_dirs", cfg)
    try:
        p4b.run_dir(RUNS / "e13_preflight_dirs", cfg); blocked = False
    except FileExistsError:
        blocked = True
    log.check("9", "an existing run folder blocks the launch", blocked)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test metrics refused while the E13 signature line is blank", guard)
    try:
        gate("dev"); gated = False
    except PermissionError as e:
        gated = True; log(f"[INFO] gate refuses dev now: {e}")
    log.check("gate", "the launch gate refuses `dev` before signature / tag / A0.2", gated)
    log(f"PREFLIGHT: {log.fail} failure(s)"); log.save()
    return 0 if log.fail == 0 else 1


def synth_processes(su, kind, seed):
    """A0.2 generators (fixed before the tag). Both keep the real timestamps and calendar. Classes from thresholds
    0.8/0.4 on a latent factor z in [0, 1.6]. 'dependent': z_t = 0.7·(A_norm z_{t−1}) + 0.3·profile_t + noise, with
    A_norm the row-normalised kernel adjacency of G1 (information travels along the graph with lag one step).
    'independent': z_t = 0.6·z_{t−1} + 0.4·profile_t + noise, node by node. Information absent by construction in
    'independent': any dependence between nodes beyond the shared calendar profile and the node amplitudes."""
    r = np.random.default_rng([seed, 2]); T, K = len(su.ts), su.K
    q = (pd.DatetimeIndex(su.ts).hour.to_numpy() * 4 + pd.DatetimeIndex(su.ts).minute.to_numpy() // 15) / 96.0
    prof = 1.0 - 0.45 * np.exp(-((q - 0.35) ** 2) / 0.004) - 0.45 * np.exp(-((q - 0.73) ** 2) / 0.004)
    base = prof[:, None] * r.uniform(0.6, 1.2, K)[None, :]
    A, _ = p4b.kernel_adjacency(su.al["graph"], su.kept); An = A / np.maximum(A.sum(1, keepdims=True), 1e-9)
    z = np.empty((T, K)); z[0] = base[0]; eps = r.normal(0, 0.08, (T, K))
    for t in range(1, T):
        z[t] = 0.7 * (An @ z[t - 1]) + 0.3 * base[t] + eps[t] if kind == "dependent" else 0.6 * z[t - 1] + 0.4 * base[t] + eps[t]
    z = np.clip(z, 0.0, 1.6)
    C = np.where(z >= 0.8, 1, np.where(z >= 0.4, 2, 3)).astype("int64")
    flow = (300 * (1.6 - z) + r.normal(0, 20, (T, K))).astype("float32"); occ = (60 * (1.6 - z) / 1.6 + r.normal(0, 3, (T, K))).astype("float32")
    return z.astype("float32"), flow, occ, C


def a0_synth(args):
    gate("a0")
    path = RUNS / "e13_a0_synth.json"
    if path.exists():
        raise FileExistsError(f"{path} exists")
    out = {"protocol": "E13 A0.2", "generator_seed": 20261118, "generator": synth_processes.__doc__, "kinds": {}, "trainings": 0}
    for kind in ("dependent", "independent"):
        su = SetupE13("madrid", 0, "I0"); z, flow, occ, C = synth_processes(su, kind, 20261118); su.inject(z, flow, occ, C)
        res = {}
        for arm in ARMS:
            A, _ = e9.adjacency(su, arm)
            o = train_e13(su, arm, A, 2000, CONFIGS["C1"], p4b.K_INIT, ck_every=250, save_states=False, log=print); out["trainings"] += 1
            res[arm] = [{"update": t["update"], "val_wce": t["val_wce"]} for t in o["trajectory"]]
        V = [(a["update"], 100 * (a["val_wce"] - b["val_wce"]) / a["val_wce"]) for a, b in zip(res["G0"], res["G1"])]
        # 'best checkpoint' = the checkpoint ≥ 500 at which G1's validation wCE is minimal (E13.md A0.2)
        g1 = [t for t in res["G1"] if t["update"] >= 500]; ub = min(g1, key=lambda t: (t["val_wce"], t["update"]))["update"]
        v_best = next(v for u, v in V if u == ub); after500 = [v for u, v in V if u >= 500]
        if kind == "dependent":
            verdict = "pass" if v_best >= 3 else "FAIL: the full model does not exploit an available spatial signal"
        else:
            verdict = ("anomaly: unexpected gain > 3 at a checkpoint ≥ 500 — investigate generator, information paths and sampling variability; not by itself evidence of leakage"
                       if max(after500) > 3 else ("pass (note: G1 worse than G0 by > 3 at some checkpoint — reported, investigated, not a block)" if min(after500) < -3 else "pass"))
        out["kinds"][kind] = {"trajectories": res, "V_G1_by_checkpoint": V, "best_checkpoint_G1": ub, "V_at_best": v_best, "verdict": verdict}
        print(kind, "best checkpoint", ub, "V", round(v_best, 2), "->", verdict)
    out["written"] = datetime.now(timezone.utc).isoformat(); out["environment"] = environment(); c, dirty = p4b.git_commit(); out["commit"] = c; out["code_dirty"] = dirty
    path.write_text(json.dumps(out, indent=1)); print("->", path, p4b.sha256(path, 16))
    ok = out["kinds"]["dependent"]["verdict"] == "pass" and out["kinds"]["independent"]["verdict"].startswith("pass")
    # normalise the independent 'pass (note…)' to 'pass' for the gate; keep the note in a separate field
    if out["kinds"]["independent"]["verdict"].startswith("pass"):
        out["kinds"]["independent"]["note"] = out["kinds"]["independent"]["verdict"]; out["kinds"]["independent"]["verdict"] = "pass"
        path.write_text(json.dumps(out, indent=1))
    return 0 if ok else 1


def a0_accept(args):
    """The responsible author records that an A0.2 anomaly (independent condition) was explained in a dated note."""
    a0 = RUNS / "e13_a0_synth.json"; z = json.loads(a0.read_text())
    if z["kinds"]["dependent"]["verdict"] != "pass":
        raise PermissionError("the dependent condition failed: it cannot be accepted, it must be corrected")
    rec = {"accepted_by": args.by, "note_commit": args.note_commit, "a0_synth_sha16": p4b.sha256(a0, 16),
           "independent_verdict": z["kinds"]["independent"]["verdict"], "written": datetime.now(timezone.utc).isoformat()}
    (RUNS / "e13_a0_resolution.json").write_text(json.dumps(rec, indent=1)); print(json.dumps(rec, indent=1))
    return 0


def a0_identifier(args):
    gate("a0")
    path = RUNS / "e13_a0_identifier.json"
    if path.exists():
        raise FileExistsError(f"{path} exists")
    out = {"protocol": "E13 A0.3 (descriptive)", "curves": {}, "trainings": 0}
    for label, su in (("I0", SetupE13("madrid", 0, "I0")), ("I1", SetupE13("madrid", 0, "I1")), ("I1-permuted", SetupE13("madrid", 0, "I1", perm_seed=0))):
        for arm in ARMS:
            A, _ = e9.adjacency(su, arm)
            o = train_e13(su, arm, A, 2000, CONFIGS["C1"], p4b.K_INIT, ck_every=250, save_states=False, log=print); out["trainings"] += 1
            out["curves"][f"{label}:{arm}"] = [{"update": t["update"], "val_wce": t["val_wce"], "train_loss": t["train_loss"]} for t in o["trajectory"]]
    out["note"] = ("Similar validation performance with true and permuted coordinates does not establish that coordinates act as "
                   "identifiers; the control measures sensitivity to the coordinate-node association and is read jointly with I0 "
                   "and with the training and validation curves. Validation-hidden coordinates are true in all runs.")
    out["written"] = datetime.now(timezone.utc).isoformat(); out["environment"] = environment(); c, dirty = p4b.git_commit(); out["commit"] = c; out["code_dirty"] = dirty
    path.write_text(json.dumps(out, indent=1)); print("->", path, p4b.sha256(path, 16))
    return 0


def main():
    ap = argparse.ArgumentParser(description="E13 — A0 and A1")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("preflight", "a0-synth", "a0-identifier", "adequacy", "test", "analysis"):
        sp.add_parser(n)
    acc = sp.add_parser("a0-accept"); acc.add_argument("--by", required=True); acc.add_argument("--note-commit", required=True)
    for n in ("dev", "final"):
        q = sp.add_parser(n); q.add_argument("--city", required=True, choices=CITIES); q.add_argument("--seed", type=int, required=True)
        q.add_argument("--arm", required=True, choices=ARMS); q.add_argument("--regime", required=True, choices=REGIMES)
        if n == "dev":
            q.add_argument("--deviation", default=None, help="commit of the dated deviation note authorising a deliberate re-run")
    x = sp.add_parser("extend"); x.add_argument("--city", required=True, choices=CITIES); x.add_argument("--arm", required=True, choices=ARMS); x.add_argument("--regime", required=True, choices=REGIMES)
    c = sp.add_parser("campaign"); c.add_argument("--phase", required=True, choices=("dev", "final"))
    a = ap.parse_args()
    E13.mkdir(parents=True, exist_ok=True)
    return {"preflight": preflight, "a0-synth": a0_synth, "a0-accept": a0_accept, "a0-identifier": a0_identifier, "dev": dev,
            "extend": extend, "final": final, "adequacy": adequacy, "test": test, "analysis": analysis, "campaign": campaign}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
