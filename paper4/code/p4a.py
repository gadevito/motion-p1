#!/usr/bin/env python3
"""
P4A — what does a loop detector measure of congestion? (`protocol/paper4/P4A.md`). No training.
==============================================================================================
Imports `analisi/validazione_colocalizzata.py` unchanged and runs the fingerprinted copy of
`OR3/data_collection/t4c_crossval.py` (`paper4/code/deliverable/t4c_crossval.py`) unchanged.

    selftest   weighted ranks and areas under the curve against the expanded data; threshold selection on a
               synthetic sensor set; bootstrap with unit multiplicities
    preflight  controls 1-9 of P4A.md, reading no measured class
    cost       loading of Austin, 100 bootstrap replicates of a 4.2-million-cell figure (synthetic), scaled
    run        after the signature: step 0 (deliverable scripts, screen outputs), Tables 64-69 recomputed,
               correction 1 (thresholds on half A saved with fingerprint, then half B), corrections 2 and 3
    freeze     CONGELAMENTO_4A.md and p4a_risultati.json from paper4/runs/p4a/

Usage: $PYA paper4/code/p4a.py selftest | selftest-e2e <tmpdir> | preflight | cost | run | freeze\n(PYA: the environment of the root poetry.lock, with scikit-learn)
"""
import argparse
import contextlib
import io
import json
import re
import resource
import runpy
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402

ROOT = p4b.ROOT
OR3 = ROOT.parent / "OR3"
OLD = ROOT.parent / "OR3_vecchia_storia"
DC = OR3 / "data_collection"
GOMO = DC / "go-mo" / "gomo"
MAD = DC / "traffic4cast" / "MADRID_2022"
PREREG = ROOT / "protocol" / "paper4" / "P4A.md"
RUNS = ROOT / "paper4" / "runs" / "p4a"
CSV = ROOT / "paper4" / "analysis" / "4A"
OUT = ROOT / "paper4" / "congelamenti"
LOGP = ROOT / "paper4" / "runs" / "p4a_preflight.log"
B = 2000
SEED = 20261109
RED = 0.4
OCC_EMPTY = 5.0
GRID = np.round(np.arange(1, 101) * 0.01, 2).astype("float32")      # 0.01 ... 1.00, compared as float32
VAL_END = np.datetime64("2024-04-01T00:00")                          # secondary reading: Jan-Mar / Apr-Dec

INPUTS = {   # path -> first 16 hex digits of SHA-256 (P4A.md, Data)
    GOMO / "targets_2021_urb_d8.npz": "b5db8261fd295077",
    GOMO / "traffic_sensors.csv": "63cf54c05e4b380e",
    MAD / "road_graph_nodes_osm.parquet": "26045de9b9b22b68",
    MAD / "road_graph_edges_district.parquet": "f2027534873a5715",
    GOMO / "tensors_2024_m30.npz": "3780d3aa589c51f5",
    GOMO / "targets_2024_m30.npz": "b41779dd51923c31",
    OLD / "austin" / "radar" / "radar_completo.json": "46f68813cf8a4839",
}
SPEED_DIR = MAD / "speed_classes" / "madrid"
SPEED_DIR_FP = "7eb5fcf855edae1f"
SCRIPTS = {
    DC / "t4c_crossval.py": "0320018785d5658d",
    Path(__file__).resolve().parent / "deliverable" / "t4c_crossval.py": "0320018785d5658d",
    ROOT / "analisi" / "validazione_colocalizzata.py": "f1f6340779b612d5",
    ROOT / "analisi" / "p4_fase1_crossval.py": "14386205ee2698d1",
}
PHASE1_CSV = {"base": "57e7b139cca39693", "noempty": "d958ff99f618437f", "d30": "6c2f37dbb4c20d89"}
AUSTIN_TABLE69 = {2: 22, 3: 6, 4: 2}


# ---------------------------------------------------------------- fingerprints ------------------------------

def dir_fp(d):
    """Fingerprint of a directory: SHA-256 of the `shasum -a 256 *.parquet` listing (sorted names)."""
    import hashlib
    lines = "".join(f"{p4b.sha256(f)}  {f.name}\n" for f in sorted(Path(d).glob("*.parquet")))
    return hashlib.sha256(lines.encode()).hexdigest()[:16]


def check_fingerprints():
    bad = [str(p) for p, fp in {**INPUTS, **SCRIPTS}.items() if not p.exists() or p4b.sha256(p, 16) != fp]
    if dir_fp(SPEED_DIR) != SPEED_DIR_FP:
        bad.append(str(SPEED_DIR))
    return bad


def require_fingerprints():
    bad = check_fingerprints()
    if bad:
        raise SystemExit("STOP: input or script fingerprint differs: " + ", ".join(bad))


# ---------------------------------------------------------------- weighted statistics -----------------------

class Ranked:
    """Precomputed sort and tie groups of a vector, for weighted mid-ranks in O(n) per replicate.
    With integer weights w, the mid-ranks equal the average ranks of the data with each value repeated w times."""
    def __init__(self, x):
        x = np.asarray(x, dtype="float64")
        self.order = np.argsort(x, kind="stable")
        xs = x[self.order]
        new = np.r_[True, xs[1:] != xs[:-1]]
        gid_sorted = np.cumsum(new) - 1
        self.gid = np.empty(len(x), np.int64); self.gid[self.order] = gid_sorted
        self.ng = int(gid_sorted[-1]) + 1 if len(x) else 0

    def midranks(self, w):
        G = np.bincount(self.gid, weights=w, minlength=self.ng)
        start = np.cumsum(G) - G
        return (start + (G + 1) / 2)[self.gid]


def wpearson(x, y, w):
    sw = w.sum()
    mx, my = (w * x).sum() / sw, (w * y).sum() / sw
    dx, dy = x - mx, y - my
    v = np.sqrt((w * dx * dx).sum() * (w * dy * dy).sum())
    return float((w * dx * dy).sum() / v) if v > 0 else float("nan")


class WSpearman:
    def __init__(self, x, y):
        self.rx, self.ry = Ranked(x), Ranked(y)

    def __call__(self, w):
        m = w > 0
        return wpearson(self.rx.midranks(w)[m], self.ry.midranks(w)[m], w[m])


class WAUC:
    """Area under the curve of label y (1 = positive) against score s (higher = positive), ties counted 1/2;
    with integer weights it equals sklearn's roc_auc_score on the expanded data."""
    def __init__(self, y, s):
        self.y = np.asarray(y, dtype="float64"); self.r = Ranked(s)

    def __call__(self, w):
        P = np.bincount(self.r.gid, weights=w * self.y, minlength=self.r.ng)
        N = np.bincount(self.r.gid, weights=w * (1 - self.y), minlength=self.r.ng)
        tp, tn = P.sum(), N.sum()
        if tp == 0 or tn == 0:
            return float("nan")
        below = np.cumsum(N) - N
        return float((P * (below + 0.5 * N)).sum() / (tp * tn))


def gini(auc):
    return 2 * auc - 1


def multiplicities(rng, n):
    return np.bincount(rng.integers(0, n, n), minlength=n).astype("float64")


def wmedian(v, w):
    return float(np.median(np.repeat(np.asarray(v, float), np.asarray(w, int)))) if w.sum() else float("nan")


def ci(rep):
    rep = np.asarray(rep, float); rep = rep[np.isfinite(rep)]
    if not len(rep):
        return None, None
    lo, hi = np.percentile(rep, [2.5, 97.5])
    return float(lo), float(hi)


def fig(value, rep=None, n=None, note=None):
    out = {"value": None if value is None or not np.isfinite(value) else float(value)}
    if rep is not None:
        out["lo"], out["hi"] = ci(rep)
    if n is not None:
        out["n"] = int(n)
    if note:
        out["note"] = note
    return out


# ---------------------------------------------------------------- correction 1: thresholds ------------------

def sensor_counts(score, red, sensor, nsens, grid=GRID):
    """Per sensor and per grid threshold t: TP, FP, FN, TN of 'predict red if score < t'."""
    k = np.searchsorted(grid, score, side="right")                 # score < grid[m]  <=>  k <= m
    H = np.zeros((nsens, len(grid) + 1, 2))
    np.add.at(H, (sensor, k, red.astype(int)), 1)
    C = np.cumsum(H, 1)[:, :len(grid), :]                          # cells with k <= m
    pos_tot, neg_tot = H[:, :, 1].sum(1), H[:, :, 0].sum(1)
    TP, FP = C[:, :, 1], C[:, :, 0]
    return {"TP": TP, "FP": FP, "FN": pos_tot[:, None] - TP, "TN": neg_tot[:, None] - FP}


def rates(c, w):
    """Precision, recall, F1, false-alarm rate per grid threshold, for sensor weights w."""
    TP, FP, FN, TN = (np.tensordot(w, c[k], 1) for k in ("TP", "FP", "FN", "TN"))
    with np.errstate(invalid="ignore", divide="ignore"):
        p = TP / np.maximum(TP + FP, 1); r = TP / np.maximum(TP + FN, 1)
        f1 = np.where(p + r > 0, 2 * p * r / np.maximum(p + r, 1e-12), 0.0); fa = FP / np.maximum(FP + TN, 1)
    return p, r, f1, fa


def choose(c, wA):
    p, r, f1, fa = rates(c, wA)
    i_f1 = int(np.argmax(f1))
    ok = np.where(fa <= 0.05)[0]
    i_fa = int(ok.max()) if len(ok) else 0
    return {"F1": round(float(GRID[i_f1]), 2), "FA": round(float(GRID[i_fa]), 2), "i_F1": i_f1, "i_FA": i_fa}


def splits(n=279):
    out = []
    for s in range(5):
        perm = np.random.default_rng([SEED, s]).permutation(n)
        out.append((np.sort(perm[: n // 2]), np.sort(perm[n // 2:])))
    return out


# ---------------------------------------------------------------- self-test ----------------------------------

def selftest():
    from scipy.stats import spearmanr
    from sklearn.metrics import roc_auc_score
    g = np.random.default_rng(0); ok = True
    x = np.round(g.normal(size=400), 1); y = np.round(x + g.normal(size=400), 1); w = g.integers(0, 4, 400).astype(float)
    xe, ye = np.repeat(x, w.astype(int)), np.repeat(y, w.astype(int))
    ok &= abs(WSpearman(x, y)(w) - spearmanr(xe, ye).statistic) < 1e-10
    lab = (y > 0.3).astype(int); le = np.repeat(lab, w.astype(int))
    ok &= abs(WAUC(lab, -x)(w) - roc_auc_score(le, -xe)) < 1e-10
    ok &= abs(WSpearman(x, y)(np.ones(400)) - spearmanr(x, y).statistic) < 1e-10
    ok &= abs(WAUC(lab, -x)(np.ones(400)) - roc_auc_score(lab, -x)) < 1e-10
    # threshold selection: score < 0.3 is red with noise; F1 must choose 0.30 +- 0.02
    S = 60; sensor = np.repeat(np.arange(S), 2000); sc = g.uniform(0, 1.2, len(sensor)).astype("float32")
    red = (sc < 0.3) ^ (g.uniform(size=len(sc)) < 0.03)
    c = sensor_counts(sc, red, sensor, S)
    ch = choose(c, np.ones(S))
    ok &= abs(ch["F1"] - 0.30) <= 0.02
    p, r, f1, fa = rates(c, np.ones(S)); m = ch["i_F1"]
    pred = sc < GRID[m]; tp = (pred & red).sum(); fp = (pred & ~red).sum(); fn = (~pred & red).sum()
    ok &= abs(p[m] - tp / (tp + fp)) < 1e-12 and abs(r[m] - tp / (tp + fn)) < 1e-12
    ok &= bool(fa[ch["i_FA"]] <= 0.05)
    A, Bh = splits()[0]; ok &= len(np.intersect1d(A, Bh)) == 0 and len(A) + len(Bh) == 279
    ok &= all(np.array_equal(a, b) for (a, _), (b, _) in zip(splits(), splits()))
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- loading -----------------------------------

def deliverable_module():
    sys.path.insert(0, str(ROOT / "analisi"))
    import validazione_colocalizzata as vc
    vc.GOMO = GOMO
    vc.T4C = MAD / "gomo_fmt"
    vc.AUSTIN = OLD / "austin" / "radar" / "radar_completo.json"
    return vc


def m30_counts(vc):
    d = vc.carica_m30()
    tot = np.isfinite(d["r_tr"]) & (d["sp"] > 0)
    v = np.isfinite(d["r_pr"]) & tot
    return d, {"sensors": len(d["sub"]), "timestamps": int(d["r_tr"].shape[0]), "valid_cells": int(tot.sum()),
               "imputed_share": float(d["imputate"][tot].mean()), "non_imputed_cells": int(v.sum())}


def austin_counts(x):
    cps = x.groupby("sez").corsia.nunique()
    return {"cells": int(len(x)), "lanes": int(x.corsia.nunique()), "sections": int(x.sez.nunique()),
            "sections_by_lanes": {int(k): int(v) for k, v in cps.value_counts().sort_index().items()}}


# ---------------------------------------------------------------- preflight ---------------------------------

class Log:
    def __init__(self, path):
        self.path, self.lines, self.fail = path, [], 0

    def __call__(self, s):
        print(s); self.lines.append(s)

    def check(self, k, text, ok):
        self.fail += not ok; self(f"[{'PASS' if ok else 'FAIL'}] {k:6s} {text}")

    def save(self):
        self.path.write_text("\n".join(self.lines) + "\n")


def preflight(args):
    log = Log(LOGP); c, dirty = p4b.git_commit()
    log(f"P4A preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(f"code p4a.py {p4b.sha256(Path(__file__), 16)} · p4b.py {p4b.sha256(Path(p4b.__file__), 16)}")
    bad = check_fingerprints()
    log.check("1", f"fingerprints of the {len(INPUTS) + 1} inputs and {len(SCRIPTS)} scripts as in P4A.md" +
              (f" (differ: {bad})" if bad else ""), not bad)
    vc = deliverable_module()
    d, cm = m30_counts(vc)
    log.check("2", f"M30: {cm['sensors']} aligned sensors, {cm['timestamps']:,} timestamps; valid cells "
              f"{cm['valid_cells']:,}, imputed share {100 * cm['imputed_share']:.2f}%, non-imputed {cm['non_imputed_cells']:,} "
              f"(compared with the deliverable, p. 130, in the frozen record) — counts only",
              cm["sensors"] == 279 and cm["timestamps"] == 35093)
    ph = ROOT / "protocol" / "paper4" / "fase1" / "crossval" / "crossval_results.csv"
    log.check("3", "arterials: fingerprinted copy of t4c_crossval.py identical to the original; Phase 1 base CSV present "
              "(57e7b139cca39693); the script itself runs only in `run`",
              ph.exists() and p4b.sha256(ph, 16) == PHASE1_CSV["base"] and not bad)
    t0 = time.perf_counter(); x = vc.carica_austin(); t_load = time.perf_counter() - t0
    ac = austin_counts(x)
    lv = {k: v for k, v in ac["sections_by_lanes"].items() if k >= 2}
    log.check("4", f"Austin: {ac['cells']:,} cells, {ac['lanes']} lanes, {ac['sections']} sections; sections by lanes "
              f"{ac['sections_by_lanes']} (Table 69 per lane level, AUSTIN_TABLE69) — counts only",
              all(lv.get(k) == v for k, v in AUSTIN_TABLE69.items()))
    sp = splits(); A0, B0 = sp[0]
    per = (np.asarray(d["r_tr"].shape[0]) > 0)
    ts = np.load(GOMO / "tensors_2024_m30.npz", allow_pickle=True)["timestamps"].astype("datetime64[m]")
    val, tst = ts < VAL_END, ts >= VAL_END
    log.check("5", f"splits: 5 × ({len(A0)}, {len(B0)}) sensors, disjoint and covering 279, identical on two calls; "
              f"periods {int(val.sum()):,} / {int(tst.sum()):,} timestamps, disjoint",
              all(len(np.intersect1d(a, b)) == 0 and len(np.union1d(a, b)) == 279 for a, b in sp)
              and all(np.array_equal(a, b) for (a, _), (b, _) in zip(sp, splits())) and not (val & tst).any() and bool(per))
    log.check("6", "weighted rank correlation and area under the curve equal the expanded data; unit multiplicities "
              "give the point; threshold selection recovers a planted threshold (selftest)", selftest() == 0)
    log.check("7", "no deliverable number copied into the computation: every deliverable value with decimals appears "
              "only in the comparison table DELIVERABLE of the frozen-record generator", no_copied_numbers())
    guard = True
    try:
        require_thresholds(RUNS / "nonexistent"); guard = False
    except SystemExit:
        pass
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        pass
    log.check("8", "no metric of half B without the fingerprinted threshold file; nothing while the signature line "
              "is blank", guard)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30
    t_rep = bootstrap_cost()
    log.check("9", f"cost: Austin loaded in {t_load:.0f} s, peak memory {rss:.1f} GB; one bootstrap replicate of a "
              f"4.2-million-cell figure {t_rep:.2f} s (synthetic)", True)
    log(f"PREFLIGHT: {log.fail} failure(s)")
    LOGP.parent.mkdir(parents=True, exist_ok=True); log.save()
    return 0 if log.fail == 0 else 1


def no_copied_numbers():
    src = Path(__file__).read_text()
    i = src.index("\nDELIVERABLE = {"); j = src.index("\n}\n", i)
    rest = src[:i] + src[j:]
    vals = {s for _, s in DELIVERABLE.values() if "," in s}
    hits = [s for s in vals if s.lstrip("+-") in rest or s.lstrip("+-").replace(",", ".") in rest]
    if hits:
        print("deliverable values found outside DELIVERABLE:", hits)
    return not hits


def bootstrap_cost(n=4_200_000, reps=10):
    g = np.random.default_rng(1)
    a = g.uniform(0, 1.5, n).astype("float32"); b = (a + g.normal(0, 0.3, n)).astype("float32")
    sens = g.integers(0, 279, n); s, u = WSpearman(a, b), WAUC((b < 0.4).astype(int), -a)
    t0 = time.perf_counter()
    for k in range(reps):
        w = multiplicities(np.random.default_rng([k]), 279)[sens]
        s(w); u(w)
    return (time.perf_counter() - t0) / reps


def cost(args):
    t = bootstrap_cost()
    est = {"seconds_per_replicate_one_figure": round(t, 3),
           "figures_M30": 7 + 4 * 2 + 2, "hours_M30_tables_67_68": round(t * (7 + 8 + 2) * B / 3600, 2),
           "written": datetime.now(timezone.utc).isoformat(), "commit": p4b.git_commit()[0]}
    path = ROOT / "paper4" / "runs" / "p4a_costo.json"
    if path.exists():
        raise SystemExit(f"STOP: {path} exists")
    path.write_text(json.dumps(est, indent=1)); print(json.dumps(est, indent=1)); print(f"-> {path} ({p4b.sha256(path, 16)})")
    return 0


# ---------------------------------------------------------------- run: step 0 -------------------------------

def capture(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = fn(*a, **k)
    return buf.getvalue(), res


def run_crossval(variant):
    out = RUNS / f"crossval_{variant}.csv"
    argv = ["t4c_crossval.py", "--gomo-targets", str(GOMO / "targets_2021_urb_d8.npz"),
            "--gomo-sensors", str(GOMO / "traffic_sensors.csv"), "--t4c-nodes", str(MAD / "road_graph_nodes_osm.parquet"),
            "--t4c-edges", str(MAD / "road_graph_edges_district.parquet"), "--speed-dir", str(SPEED_DIR), "--out", str(out)]
    argv += {"base": [], "noempty": ["--exclude-empty"], "d30": ["--max-dist", "30"]}[variant]
    old = sys.argv; sys.argv = argv
    try:
        text, g = capture(runpy.run_path, str(Path(__file__).resolve().parent / "deliverable" / "t4c_crossval.py"),
                          run_name="__main__")
    finally:
        sys.argv = old
    (RUNS / f"crossval_{variant}.txt").write_text(text)
    if p4b.sha256(out, 16) != PHASE1_CSV[variant]:
        raise SystemExit(f"STOP: crossval {variant} CSV differs from Phase 1 ({p4b.sha256(out, 16)})")
    return text, g


def parse_crossval(text):
    num = r"([+-]?\d+\.\d+)"
    def one(pat, cast=float):
        m = re.search(pat, text)
        return cast(m.group(1).replace(",", "")) if m else None
    out = {"pairs_valid": one(r"coppie valide: (\d+)", int), "corr_median": one(r"correlazione r: mediana " + num),
           "class_agreement": one(r"concordanza di classe \(3 classi\): ([\d.]+)%"),
           "recall_yellow_red": one(r"recall della congestione ricostruita \(giallo\+rosso\): ([\d.]+)%"),
           "profile_median": one(r"profilo settimanale medio.*?mediana " + num)}
    for who, key in (("ricostruito", "reconstructed"), ("misurato", "measured")):
        m = re.search(who + r" \((?:spire|sonde)\)\s+verde/giallo/rosso = ([\d.]+)% / ([\d.]+)% / ([\d.]+)%", text)
        out[f"classes_{key}"] = [float(v) for v in m.groups()] if m else None
    for nm, key in (("r ricostruito", "r"), ("occupazione", "occupancy"), ("flusso", "flow")):
        m = re.search(re.escape(nm) + r"\s+scost\. ottimo.*?Pearson ([+-][\d.]+) \| Spearman ([+-][\d.]+) \| coppie (\d+)", text)
        out[f"spearman_{key}"] = float(m.group(2)) if m else None
        out[f"pairs_{key}"] = int(m.group(3)) if m else None
    return out


# ---------------------------------------------------------------- run: tables ---------------------------------

def table67_68(d, res, XY=None):
    """Tables 67 and 68 on M30: points and the bootstrap over sensors (one draw shared per table)."""
    S = len(d["sub"]); T = d["r_tr"].shape[0]
    v = np.isfinite(d["r_pr"]) & np.isfinite(d["r_tr"]) & (d["sp"] > 0)
    sens_all = np.broadcast_to(np.arange(S), (T, S))
    a, b, sv, oc = d["r_pr"][v], d["r_tr"][v], sens_all[v], d["oc"][v]
    figs67 = {"overall": (np.ones(len(a), bool), "spearman")}
    for lo, hi in ((5, 10), (10, 20), (20, 40), (40, 100)):
        figs67[f"band {lo}-{hi}%"] = ((oc >= lo) & (oc < hi), "spearman")
    for lo, hi, nm in ((0.8, 1.6, "green"), (0.4, 0.8, "yellow"), (0.0, 0.4, "red")):
        figs67[f"class {nm}"] = ((b >= lo) & (b < hi), "spearman")
    stats = {}
    for k, (m, _) in figs67.items():
        stats[k] = (WSpearman(a[m], b[m]), sv[m], int(m.sum()))
    auc_red = WAUC((b < RED).astype(int), -a); auc_yr = WAUC((b < 0.8).astype(int), -a)
    reps = {k: [] for k in list(stats) + ["auc red", "auc yellow+red"]}
    rng = np.random.default_rng([SEED, 67])
    for _ in range(B):
        ws = multiplicities(rng, S)
        for k, (f, s_, _n) in stats.items():
            reps[k].append(f(ws[s_]))
        w = ws[sv]; reps["auc red"].append(auc_red(w)); reps["auc yellow+red"].append(auc_yr(w))
    one = np.ones(S)
    t67 = {k: fig(f(one[s_]), reps[k], n) for k, (f, s_, n) in stats.items()}
    t67["auc red"] = fig(auc_red(one[sv]), reps["auc red"]); t67["auc yellow+red"] = fig(auc_yr(one[sv]), reps["auc yellow+red"])
    y = b < RED
    t67["deliverable rule, in sample"] = {f"{s:.2f}": prf(a < np.float32(s), y) for s in (0.20, 0.30, 0.40, 0.50)}
    t67["random precision"] = float(y.mean())
    res["table67"] = t67
    # Table 68: same sensor and neighbour bands, joint draw over sensors i
    if XY is None:
        s_ = pd.read_csv(GOMO / "traffic_sensors.csv", dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
        s_["id"] = s_["id"].astype(str)
        XY = s_.set_index("id").reindex(d["sub"])[["utm_x", "utm_y"]].to_numpy()
    D = np.sqrt(((XY[:, None, :] - XY[None, :, :]) ** 2).sum(-1)); np.fill_diagonal(D, np.inf)
    rows = {"same sensor": (WSpearman(a, b), WAUC(y.astype(int), -a), sv, 0.0, S)}
    for lo, hi in ((0, 20), (19, 72), (20, 60), (60, 200)):
        A_, B_, I_, dd = [], [], [], []
        for i in range(S):
            cnd = np.where((D[i] >= lo) & (D[i] < hi))[0]
            if not len(cnd):
                continue
            j = cnd[np.argmin(np.abs(D[i][cnd] - 33.0))]
            m = (np.isfinite(d["r_pr"][:, i]) & np.isfinite(d["r_tr"][:, j]) & (d["sp"][:, j] > 0) & (d["oc"][:, i] >= OCC_EMPTY))
            if m.sum() > 50:
                A_.append(d["r_pr"][m, i]); B_.append(d["r_tr"][m, j]); I_.append(np.full(int(m.sum()), i)); dd.append(D[i, j])
        if len(A_) < 20:
            rows[f"neighbour {lo}-{hi} m"] = None; continue
        A_, B_, I_ = np.concatenate(A_), np.concatenate(B_), np.concatenate(I_)
        yy = (B_ < RED).astype(int)
        rows[f"neighbour {lo}-{hi} m"] = (WSpearman(A_, B_), WAUC(yy, -A_) if 50 < yy.sum() < len(yy) - 50 else None,
                                         I_, float(np.median(dd)), len(dd))
    rng = np.random.default_rng([SEED, 68]); rep68 = {k: ([], []) for k, r in rows.items() if r}
    for _ in range(B):
        ws = multiplicities(rng, S)
        for k, r in rows.items():
            if r:
                w = ws[r[2]]; rep68[k][0].append(r[0](w)); rep68[k][1].append(r[1](w) if r[1] else np.nan)
    t68 = {}
    for k, r in rows.items():
        if not r:
            t68[k] = {"note": "fewer than 20 sensors"}; continue
        w1 = np.ones(len(r[2]))
        au = r[1](w1) if r[1] else float("nan")
        t68[k] = {"median_distance_m": r[3], "sensors": r[4], "spearman": fig(r[0](w1), rep68[k][0]),
                  "auc": fig(au, rep68[k][1]), "gini": fig(gini(au), gini(np.array(rep68[k][1])))}
    res["table68"] = t68
    return rep68


def prf(pred, y):
    tp = int((pred & y).sum()); fp = int((pred & ~y).sum()); fn = int((~pred & y).sum())
    p = tp / max(tp + fp, 1); r = tp / max(tp + fn, 1)
    return {"precision": p, "recall": r, "F1": 2 * p * r / max(p + r, 1e-12)}


def arterials(g, res):
    """Recomputed arterial row of Table 68 from the base run of t4c_crossval.py (pairs at its chosen shift)."""
    from sklearn.metrics import roc_auc_score
    from scipy.stats import spearmanr
    G, M, shift = g["G"], g["M"], int(g["shift"]); P = G.shape[1]
    auc_p, sp_p, cells = np.full(P, np.nan), np.full(P, np.nan), []
    for j in range(P):
        m = np.isfinite(G[:, j]) & np.isfinite(M[:, j])
        yy = M[m, j] < RED
        if yy.sum() >= 20 and (~yy).sum() >= 20:
            auc_p[j] = roc_auc_score(yy, -G[m, j])
        if m.sum() >= 200 and G[m, j].std() > 1e-6 and M[m, j].std() > 1e-6:
            sp_p[j] = spearmanr(G[m, j], M[m, j]).statistic
        cells.append((G[m, j], M[m, j], np.full(int(m.sum()), j)))
    a = np.concatenate([c[0] for c in cells]); b = np.concatenate([c[1] for c in cells]); pid = np.concatenate([c[2] for c in cells])
    pooled_auc, pooled_sp = WAUC((b < RED).astype(int), -a), WSpearman(a, b)
    rng = np.random.default_rng([SEED, 268]); rep = {k: [] for k in ("auc_median", "sp_median", "auc_pooled", "sp_pooled")}
    fa, fs = np.isfinite(auc_p), np.isfinite(sp_p)
    for _ in range(B):
        w = multiplicities(rng, P)
        rep["auc_median"].append(wmedian(auc_p[fa], w[fa])); rep["sp_median"].append(wmedian(sp_p[fs], w[fs]))
        rep["auc_pooled"].append(pooled_auc(w[pid])); rep["sp_pooled"].append(pooled_sp(w[pid]))
    one = np.ones(len(a))
    res["arterials"] = {"shift_quarter_hours": shift, "pairs": P, "pairs_with_auc": int(fa.sum()), "pairs_with_spearman": int(fs.sum()),
                        "auc_median": fig(float(np.median(auc_p[fa])), rep["auc_median"]),
                        "spearman_median": fig(float(np.median(sp_p[fs])), rep["sp_median"]),
                        "auc_pooled": fig(pooled_auc(one), rep["auc_pooled"]), "spearman_pooled": fig(pooled_sp(one), rep["sp_pooled"]),
                        "cells": int(len(a))}
    return rep


def gini_split(res, rep68, rep_art):
    out = {}
    same = res["table68"]["same sensor"]["auc"]["value"]; near = res["table68"]["neighbour 19-72 m"]["auc"]["value"]
    rs, rn = np.array(rep68["same sensor"][1]), np.array(rep68["neighbour 19-72 m"][1])
    for k, key in (("primary", "auc_median"), ("secondary", "auc_pooled")):
        art = res["arterials"][key]["value"]; ra = np.array(rep_art[key])
        share = (gini(same) - gini(near)) / (gini(same) - gini(art))
        rep = (gini(rs) - gini(rn)) / (gini(rs) - gini(ra))
        out[k] = {"G_same": gini(same), "G_19_72": gini(near), "G_arterials": gini(art), "share_matching": fig(share, rep)}
    res["gini_split"] = out


def austin(x, res):
    from sklearn.metrics import roc_auc_score
    from scipy.stats import spearmanr
    secs = sorted(x.sez.unique()); sidx = {s: i for i, s in enumerate(secs)}; NS = len(secs)
    lanes = x.groupby("corsia").agg(sez=("sez", "first"), n=("r_pr", "size"))
    lane_sp, lane_auc, lane_sec_sp, lane_sec_auc = [], [], [], []
    for c, q in x.groupby("corsia"):
        if len(q) >= 200:
            v = spearmanr(q.r_pr, q.r_tr).statistic
            if np.isfinite(v):
                lane_sp.append(v); lane_sec_sp.append(sidx[q.sez.iloc[0]])
        if q.rosso.sum() > 20 and (~q.rosso).sum() > 20:
            lane_auc.append(roc_auc_score(q.rosso, -q.r_pr)); lane_sec_auc.append(sidx[q.sez.iloc[0]])
    lane_sp, lane_auc = np.array(lane_sp), np.array(lane_auc)
    lane_sec_sp, lane_sec_auc = np.array(lane_sec_sp), np.array(lane_sec_auc)
    cps = x.groupby("sez").corsia.nunique()
    x = x.copy(); x["una_rossa"] = x.rosso
    agg = x.groupby(["sez", "ist"], as_index=False).agg(volume=("volume", "sum"), occupancy=("occupancy", "mean"),
                                                     speed=("speed", "mean"), una_rossa=("una_rossa", "max"))
    agg = agg[(agg.volume > 0) & (agg.occupancy > 0) & (agg.speed > 0)].copy()
    agg["p"] = agg.volume / agg.occupancy
    agg["r_pr"] = np.clip(agg.p / agg.groupby("sez").p.transform(lambda s: s.quantile(.85)), 0, 1.5)
    agg["r_tr"] = np.clip(agg.speed / agg.groupby("sez").speed.transform(lambda s: s.quantile(.85)), 0, 1.5)
    agg["rosso_sez"] = agg.r_tr < RED
    sec_auc, sec_lanes, sec_n, sec_one, sec_sez = {}, {}, {}, {}, {}
    for s, g_ in agg.groupby("sez"):
        sec_n[s] = len(g_); sec_one[s] = float(g_.una_rossa.sum()); sec_sez[s] = float(g_.rosso_sez.sum())
        sec_lanes[s] = int(cps[s])
        if g_.una_rossa.sum() > 20 and (~g_.una_rossa).sum() > 20:
            sec_auc[s] = roc_auc_score(g_.una_rossa, -g_.r_pr)
    # volume-occupancy, sections with >= 3 lanes (declared definition, item 16)
    big = set(cps[cps >= 3].index)
    xl = x[x.sez.isin(big)]; al = agg[agg.sez.isin(big)]
    vo_lane = WSpearman(xl.volume.to_numpy(), xl.occupancy.to_numpy()); vo_sec = WSpearman(al.volume.to_numpy(), al.occupancy.to_numpy())
    xl_s = xl.sez.map(sidx).to_numpy(); al_s = al.sez.map(sidx).to_numpy()
    rng = np.random.default_rng([SEED, 169]); rep = {k: [] for k in ("lane_sp", "lane_auc", "vo_lane", "vo_sec")}
    levels = sorted(k for k in cps.unique() if k >= 2)
    lev_secs = {k: [s for s in secs if sec_lanes.get(s) == k] for k in levels}
    rep_lev = {k: ([], []) for k in levels}
    for _ in range(B):
        w = multiplicities(rng, NS)
        rep["lane_sp"].append(wmedian(lane_sp, w[lane_sec_sp])); rep["lane_auc"].append(wmedian(lane_auc, w[lane_sec_auc]))
        rep["vo_lane"].append(vo_lane(w[xl_s])); rep["vo_sec"].append(vo_sec(w[al_s]))
        for k in levels:
            ss = lev_secs[k]; ww = multiplicities(rng, len(ss))
            au = [(sec_auc[s], wi) for s, wi in zip(ss, ww) if s in sec_auc]
            rep_lev[k][0].append(wmedian([a_ for a_, _ in au], np.array([wi for _, wi in au])) if au else np.nan)
            n = sum(sec_n[s] * wi for s, wi in zip(ss, ww))
            rep_lev[k][1].append(100 * (sum(sec_one[s] * wi for s, wi in zip(ss, ww)) - sum(sec_sez[s] * wi for s, wi in zip(ss, ww))) / n if n else np.nan)
    t69 = {}
    for k in levels:
        ss = lev_secs[k]; cells = sum(sec_n[s] for s in ss)
        au = [sec_auc[s] for s in ss if s in sec_auc]
        note = None if len(ss) >= 5 else "fewer than 5 sections: no interval"
        t69[str(k)] = {"sections": len(ss), "cells": int(cells), "listed_by_script": cells >= 1000,
                       "auc_median": fig(float(np.median(au)) if au else None, rep_lev[k][0] if not note else None, len(au), note),
                       "auc_iqr": [float(np.percentile(au, 25)), float(np.percentile(au, 75))] if au else None,
                       "prevalence_difference_points": fig(100 * (sum(sec_one[s] for s in ss) - sum(sec_sez[s] for s in ss)) / cells,
                                                           rep_lev[k][1] if not note else None, note=note)}
    one_l, one_a = np.ones(len(xl)), np.ones(len(al))
    res["austin"] = {"counts": austin_counts(x),
                     "within_lane_spearman_median": fig(float(np.median(lane_sp)), rep["lane_sp"], len(lane_sp)),
                     "within_lane_spearman_iqr": [float(np.percentile(lane_sp, 25)), float(np.percentile(lane_sp, 75))],
                     "within_lane_auc_median": fig(float(np.median(lane_auc)), rep["lane_auc"], len(lane_auc)),
                     "within_lane_auc_iqr": [float(np.percentile(lane_auc, 25)), float(np.percentile(lane_auc, 75))],
                     "volume_occupancy_lane": fig(vo_lane(one_l), rep["vo_lane"], len(xl)),
                     "volume_occupancy_section": fig(vo_sec(one_a), rep["vo_sec"], len(al)),
                     "sections_3plus_lanes": len(big), "table69": t69}
    # correction 3: lanes against section AUC, sections with >= 2 lanes
    ss = [s for s in secs if sec_lanes.get(s, 0) >= 2 and s in sec_auc]
    L = np.array([sec_lanes[s] for s in ss], float); Au = np.array([sec_auc[s] for s in ss])
    f = WSpearman(L, Au); rng = np.random.default_rng([SEED, 300])
    rep3 = [f(multiplicities(rng, len(ss))) for _ in range(B)]
    res["correction3"] = {"sections": len(ss), "spearman_lanes_auc": fig(f(np.ones(len(ss))), rep3),
                          "by_lanes": {str(k): int((L == k).sum()) for k in sorted(set(L.astype(int)))}}


def correction1(d, res, ts=None):
    S = len(d["sub"]); T = d["r_tr"].shape[0]
    v = np.isfinite(d["r_pr"]) & np.isfinite(d["r_tr"]) & (d["sp"] > 0)
    if ts is None:
        ts = np.load(GOMO / "tensors_2024_m30.npz", allow_pickle=True)["timestamps"].astype("datetime64[m]")
    tt = np.broadcast_to(ts[:, None], (T, S))[v]; sens = np.broadcast_to(np.arange(S), (T, S))[v]
    a, red = d["r_pr"][v], d["r_tr"][v] < RED
    readings = {"between_sensors": (np.ones(len(a), bool), np.ones(len(a), bool)),
                "in_time": (tt < VAL_END, tt >= VAL_END)}
    counts = {k: (sensor_counts(a[m0], red[m0], sens[m0], S), sensor_counts(a[m1], red[m1], sens[m1], S))
              for k, (m0, m1) in readings.items()}
    th = {}
    for k in readings:
        th[k] = []
        for si, (A, Bh) in enumerate(splits(S)):
            wA = np.zeros(S); wA[A] = 1
            th[k].append(choose(counts[k][0], wA))
    d_ = RUNS / "thresholds"; d_.mkdir(parents=True, exist_ok=True)
    (d_ / "thresholds.json").write_text(json.dumps(th, indent=1))
    (d_ / "thresholds.fingerprint").write_text(json.dumps({"sha256": p4b.sha256(d_ / "thresholds.json", 16),
                                                          "written": datetime.now(timezone.utc).isoformat()}))
    th = require_thresholds(d_)
    out = {}
    for ri, k in enumerate(readings):
        cB = counts[k][1]; per, rep = [], {"F1": [], "precision": [], "recall": [], "recall_FA": [], "fa_FA": []}
        for si, (A, Bh) in enumerate(splits(S)):
            c = th[k][si]; wB = np.zeros(S); wB[Bh] = 1
            p, r, f1, fa = rates(cB, wB)
            per.append({"threshold_F1": c["F1"], "F1": f1[c["i_F1"]], "precision": p[c["i_F1"]], "recall": r[c["i_F1"]],
                        "threshold_FA": c["FA"], "recall_FA": r[c["i_FA"]], "fa_FA": fa[c["i_FA"]]})
            rng = np.random.default_rng([SEED, 200 + si, ri])
            for _ in range(B):
                w = np.zeros(S); w[Bh] = multiplicities(rng, len(Bh))
                p, r, f1, fa = rates(cB, w)
                rep["F1"].append(f1[c["i_F1"]]); rep["precision"].append(p[c["i_F1"]]); rep["recall"].append(r[c["i_F1"]])
                rep["recall_FA"].append(r[c["i_FA"]]); rep["fa_FA"].append(fa[c["i_FA"]])
        out[k] = {"per_split": [{kk: float(vv) for kk, vv in s.items()} for s in per],
                  **{m: fig(float(np.mean([s[m] for s in per])), rep[m]) for m in rep}}
    res["correction1"] = out
    res["thresholds_sha256"] = p4b.sha256(d_ / "thresholds.json", 16)


def require_thresholds(d):
    p = Path(d) / "thresholds.json"
    if not p.exists():
        raise SystemExit(f"STOP: {p} missing: no metric of half B without the thresholds")
    if p4b.sha256(p, 16) != json.loads((Path(d) / "thresholds.fingerprint").read_text())["sha256"]:
        raise SystemExit(f"STOP: {p} fingerprint differs")
    return json.loads(p.read_text())


def run(args):
    p4b.require_signed(PREREG); require_fingerprints()
    if (RUNS / "results.json").exists():
        raise SystemExit(f"STOP: {RUNS}/results.json exists")
    RUNS.mkdir(parents=True, exist_ok=True); CSV.mkdir(parents=True, exist_ok=True)
    res = {"started": datetime.now(timezone.utc).isoformat()}
    t0 = time.perf_counter()
    cv = {}
    for variant in ("base", "noempty", "d30"):
        text, g = run_crossval(variant)
        cv[variant] = parse_crossval(text)
        cv[variant]["corr_median_csv"] = float(pd.read_csv(RUNS / f"crossval_{variant}.csv")["corr"].median())
        if variant == "base":
            g_base = {k: g[k] for k in ("G", "M", "shift")}
        print(f"[step 0] crossval {variant} done ({time.perf_counter() - t0:.0f} s)", flush=True)
    res["crossval"] = cv
    vc = deliverable_module()
    d = vc.carica_m30()
    txt, _ = capture(vc.sez_anello, d); (RUNS / "script_anello.txt").write_text(txt)
    txt, _ = capture(vc.sez_accoppiamento, d, None); (RUNS / "script_accoppiamento.txt").write_text(txt)
    print(f"[step 0] script M30 sections done ({time.perf_counter() - t0:.0f} s)", flush=True)
    res["m30_counts"] = m30_counts(vc)[1]
    rep68 = table67_68(d, res); print(f"[tables 67-68] done ({time.perf_counter() - t0:.0f} s)", flush=True)
    rep_art = arterials(g_base, res); gini_split(res, rep68, rep_art)
    print(f"[arterials, Gini split] done ({time.perf_counter() - t0:.0f} s)", flush=True)
    correction1(d, res); print(f"[correction 1] done ({time.perf_counter() - t0:.0f} s)", flush=True)
    del d
    x = vc.carica_austin()
    txt, _ = capture(vc.sez_austin, x.copy()); (RUNS / "script_austin.txt").write_text(txt)
    austin(x, res); print(f"[Austin, correction 3] done ({time.perf_counter() - t0:.0f} s)", flush=True)
    res["screen_outputs"] = {p.name: p4b.sha256(p, 16) for p in sorted(RUNS.glob("*.txt"))}
    res["inputs"] = {str(p.relative_to(ROOT.parent)): fp for p, fp in INPUTS.items()}
    res["inputs"][str(SPEED_DIR.relative_to(ROOT.parent))] = SPEED_DIR_FP
    res["code"] = {"p4a.py": p4b.sha256(Path(__file__), 16), "p4b.py": p4b.sha256(Path(p4b.__file__), 16)}
    res["commit"], res["code_dirty"] = p4b.git_commit(); res["finished"] = datetime.now(timezone.utc).isoformat()
    res["seconds"] = time.perf_counter() - t0
    (RUNS / "results.json").write_text(json.dumps(res, indent=1, default=float))
    print(f"-> {RUNS / 'results.json'} ({p4b.sha256(RUNS / 'results.json', 16)})")
    return 0


# ---------------------------------------------------------------- freeze -------------------------------------

# Deliverable UC-04 v1, values typed from the PDF for the comparison only (page, table, printed string).
DELIVERABLE = {
    "T64 pairs": ("p. 127, Table 64", "399"), "T64 corr median": ("p. 127, Table 64", "0,04"),
    "T64 profile median": ("p. 127, Table 64", "0,13"), "T64 class agreement %": ("p. 127, Table 64", "44"),
    "T64 recall yellow+red %": ("p. 127, Table 64", "16,7"),
    "T65 Spearman r": ("p. 128, Table 65", "+0,0397"), "T65 Spearman occupancy": ("p. 128, Table 65", "-0,1252"),
    "T65 Spearman flow": ("p. 128, Table 65", "-0,1410"), "T65 Spearman r, trafficked": ("p. 128, Table 65", "+0,0157"),
    "T65 pairs, trafficked": ("p. 128, Table 65", "276"), "T65 Spearman occupancy, trafficked": ("p. 128, Table 65", "-0,0689"),
    "T65 Spearman flow, trafficked": ("p. 128, Table 65", "-0,0712"), "T64 corr median, 30 m": ("p. 127, text", "0,0452"),
    "T64 pairs, 30 m": ("p. 127, text", "181"),
    "M30 sensors": ("p. 130, text", "279"), "M30 imputed %": ("p. 130, text", "54,33"),
    "T67 overall": ("p. 130, text", "+0,255"),
    "T67 band 5-10%": ("p. 130, Table 67", "-0,112"), "T67 band 10-20%": ("p. 130, Table 67", "+0,068"),
    "T67 band 20-40%": ("p. 130, Table 67", "+0,266"), "T67 band 40-100%": ("p. 130, Table 67", "+0,463"),
    "T67 class green": ("p. 130, Table 67", "+0,033"), "T67 class yellow": ("p. 130, Table 67", "+0,458"),
    "T67 class red": ("p. 130, Table 67", "+0,632"),
    "T67 cells band 5-10%": ("p. 130, Table 67", "2677304"), "T67 cells band 10-20%": ("p. 130, Table 67", "1179952"),
    "T67 cells band 20-40%": ("p. 130, Table 67", "269809"), "T67 cells band 40-100%": ("p. 130, Table 67", "71949"),
    "T67 cells class green": ("p. 130, Table 67", "2989877"), "T67 cells class yellow": ("p. 130, Table 67", "622758"),
    "T67 cells class red": ("p. 130, Table 67", "143440"),
    "T67 auc red": ("p. 131, text", "0,984"), "T67 auc yellow+red": ("p. 131, text", "0,752"),
    "T67 precision at 0.30": ("p. 131, text", "0,498"), "T67 recall at 0.30": ("p. 131, text", "0,891"),
    "T67 random precision": ("p. 131, text", "0,034"),
    "T68 same spearman": ("p. 132, Table 68", "+0,255"), "T68 same auc": ("p. 132, Table 68", "0,984"),
    "T68 same gini": ("p. 132, Table 68", "0,968"),
    "T68 0-20 distance": ("p. 132, Table 68", "14"), "T68 0-20 spearman": ("p. 132, Table 68", "+0,086"),
    "T68 0-20 auc": ("p. 132, Table 68", "0,789"), "T68 0-20 gini": ("p. 132, Table 68", "0,578"),
    "T68 19-72 distance": ("p. 132, Table 68", "31"), "T68 19-72 spearman": ("p. 132, Table 68", "+0,076"),
    "T68 19-72 auc": ("p. 132, Table 68", "0,726"), "T68 19-72 gini": ("p. 132, Table 68", "0,452"),
    "T68 20-60 distance": ("p. 132, Table 68", "31"), "T68 20-60 spearman": ("p. 132, Table 68", "+0,080"),
    "T68 20-60 auc": ("p. 132, Table 68", "0,761"), "T68 20-60 gini": ("p. 132, Table 68", "0,522"),
    "T68 60-200 distance": ("p. 132, Table 68", "96"), "T68 60-200 spearman": ("p. 132, Table 68", "+0,037"),
    "T68 60-200 auc": ("p. 132, Table 68", "0,598"), "T68 60-200 gini": ("p. 132, Table 68", "0,196"),
    "T68 arterials spearman (table)": ("p. 132, Table 68", "+0,001"), "T68 arterials spearman (text)": ("p. 131, text", "+0,071"),
    "T68 arterials auc": ("p. 132, Table 68", "0,542"), "T68 arterials gini": ("p. 132, Table 68", "0,084"),
    "T68 share matching %": ("p. 132, text", "58"),
    "Austin within-lane spearman": ("p. 131, text", "+0,7066"), "Austin within-lane auc": ("p. 131, text", "0,990"),
    "Austin within-lane auc q1": ("p. 131, text", "0,959"), "Austin within-lane auc q3": ("p. 131, text", "0,999"),
    "Austin volume-occupancy lane": ("p. 133, text", "+0,7241"), "Austin volume-occupancy section": ("p. 133, text", "+0,2999"),
    "T69 2 sections": ("p. 133, Table 69", "22"), "T69 2 cells": ("p. 133, Table 69", "1432457"),
    "T69 2 auc": ("p. 133, Table 69", "0,990"), "T69 2 prevalence": ("p. 133, Table 69", "+0,19"),
    "T69 3 sections": ("p. 133, Table 69", "6"), "T69 3 cells": ("p. 133, Table 69", "433660"),
    "T69 3 auc": ("p. 133, Table 69", "0,755"), "T69 3 prevalence": ("p. 133, Table 69", "+18,35"),
    "T69 4 sections": ("p. 133, Table 69", "2"), "T69 4 cells": ("p. 133, Table 69", "154380"),
    "T69 4 auc": ("p. 133, Table 69", "0,664"), "T69 4 prevalence": ("p. 133, Table 69", "+9,93"),
}


def regenerated(r):
    """Regenerated value for every key of DELIVERABLE, read from results.json only."""
    cv, t67, t68, au = r["crossval"], r["table67"], r["table68"], r["austin"]
    v = lambda e: e["value"] if e else None  # noqa: E731
    out = {"T64 pairs": cv["base"]["pairs_valid"], "T64 corr median": cv["base"]["corr_median_csv"],
           "T64 profile median": cv["base"]["profile_median"], "T64 class agreement %": cv["base"]["class_agreement"],
           "T64 recall yellow+red %": cv["base"]["recall_yellow_red"], "T65 Spearman r": cv["base"]["spearman_r"],
           "T65 Spearman occupancy": cv["base"]["spearman_occupancy"], "T65 Spearman flow": cv["base"]["spearman_flow"],
           "T65 Spearman r, trafficked": cv["noempty"]["spearman_r"], "T65 pairs, trafficked": cv["noempty"]["pairs_r"],
           "T65 Spearman occupancy, trafficked": cv["noempty"]["spearman_occupancy"],
           "T65 Spearman flow, trafficked": cv["noempty"]["spearman_flow"], "T64 corr median, 30 m": cv["d30"]["corr_median_csv"],
           "T64 pairs, 30 m": cv["d30"]["pairs_valid"],
           "M30 sensors": r["m30_counts"]["sensors"], "M30 imputed %": 100 * r["m30_counts"]["imputed_share"],
           "T67 overall": v(t67["overall"]), "T67 auc red": v(t67["auc red"]), "T67 auc yellow+red": v(t67["auc yellow+red"]),
           "T67 precision at 0.30": t67["deliverable rule, in sample"]["0.30"]["precision"],
           "T67 recall at 0.30": t67["deliverable rule, in sample"]["0.30"]["recall"], "T67 random precision": t67["random precision"]}
    for k in ("band 5-10%", "band 10-20%", "band 20-40%", "band 40-100%", "class green", "class yellow", "class red"):
        out[f"T67 {k}"] = v(t67[k]); out[f"T67 cells {k}"] = t67[k].get("n")
    out["T68 same spearman"] = v(t68["same sensor"]["spearman"]); out["T68 same auc"] = v(t68["same sensor"]["auc"])
    out["T68 same gini"] = v(t68["same sensor"]["gini"])
    for lab, k in (("0-20", "neighbour 0-20 m"), ("19-72", "neighbour 19-72 m"), ("20-60", "neighbour 20-60 m"), ("60-200", "neighbour 60-200 m")):
        e = t68.get(k) or {}
        out[f"T68 {lab} distance"] = e.get("median_distance_m"); out[f"T68 {lab} spearman"] = v(e.get("spearman"))
        out[f"T68 {lab} auc"] = v(e.get("auc")); out[f"T68 {lab} gini"] = v(e.get("gini"))
    ar = r["arterials"]
    out["T68 arterials spearman (table)"] = v(ar["spearman_median"]); out["T68 arterials spearman (text)"] = v(ar["spearman_median"])
    out["T68 arterials auc"] = v(ar["auc_median"]); out["T68 arterials gini"] = gini(v(ar["auc_median"]))
    out["T68 share matching %"] = 100 * v(r["gini_split"]["primary"]["share_matching"])
    out["Austin within-lane spearman"] = v(au["within_lane_spearman_median"]); out["Austin within-lane auc"] = v(au["within_lane_auc_median"])
    out["Austin within-lane auc q1"], out["Austin within-lane auc q3"] = au["within_lane_auc_iqr"]
    out["Austin volume-occupancy lane"] = v(au["volume_occupancy_lane"]); out["Austin volume-occupancy section"] = v(au["volume_occupancy_section"])
    for k in ("2", "3", "4"):
        e = au["table69"].get(k, {})
        out[f"T69 {k} sections"] = e.get("sections"); out[f"T69 {k} cells"] = e.get("cells")
        out[f"T69 {k} auc"] = v(e.get("auc_median")); out[f"T69 {k} prevalence"] = v(e.get("prevalence_difference_points"))
    return out


def compare(key, reg):
    where, s = DELIVERABLE[key]
    dv = float(s.replace(",", ".")); dec = len(s.split(",")[1]) if "," in s else 0
    if reg is None:
        return where, s, "—", "not regenerated"
    rr = round(float(reg), dec)
    same = abs(rr - dv) < 10 ** (-dec) / 2 + 1e-12
    return where, s, f"{float(reg):.{max(dec, 0) + 1}f}", "identical" if same else f"differs ({rr - dv:+.{dec}f})"


def readings(r):
    c1 = r["correction1"]["between_sensors"]; t67 = r["table67"]
    rho, f1, auc = t67["overall"], c1["F1"], t67["auc red"]
    if rho["hi"] < 0.5 and f1["lo"] >= 0.5 and auc["lo"] >= 0.9:
        diss = "reconstruction measures occurrence, not level"
    elif f1["hi"] < 0.5 or auc["hi"] < 0.75:
        diss = "reconstruction measures neither"
    elif rho["lo"] >= 0.5 and f1["lo"] >= 0.5 and auc["lo"] >= 0.9:
        diss = "it measures both"
    else:
        diss = "undetermined"
    sh = r["gini_split"]["primary"]["share_matching"]
    match = ("matching explains most of the arterial gap" if sh["lo"] > 0.5 else
             "matching explains less than half of the arterial gap" if sh["hi"] < 0.5 else "undetermined")
    l3 = r["correction3"]["spearman_lanes_auc"]
    lanes = "aggregating lanes hides single-lane episodes" if l3["hi"] is not None and l3["hi"] < 0 else "no relation detected"
    return {"dissociation": diss, "matching": match, "lanes": lanes}


def freeze(args):
    if (OUT / "CONGELAMENTO_4A.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_4A.md exists; regenerate only on purpose, after moving it")
    rp = RUNS / "results.json"; r = json.loads(rp.read_text())
    for name, fp in r["screen_outputs"].items():
        if p4b.sha256(RUNS / name, 16) != fp:
            raise SystemExit(f"STOP: {name} fingerprint differs")
    reg = regenerated(r); comp = {k: compare(k, reg.get(k)) for k in DELIVERABLE}
    st = readings(r)
    c, dirty = p4b.git_commit()
    res = {"results_sha256": p4b.sha256(rp, 16), "results": r, "comparison": comp, "readings": st, "commit": c,
           "code_dirty": dirty, "prereg_fingerprint": p4b.sha256(PREREG, 16), "generator_fingerprint": p4b.sha256(Path(__file__), 16),
           "written": datetime.now(timezone.utc).isoformat()}
    OUT.mkdir(parents=True, exist_ok=True)
    jp = OUT / "p4a_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    write_md(res)
    return 0


def fv(e, n=3):
    if not e or e.get("value") is None:
        return "—"
    s = f"{e['value']:+.{n}f}"
    if e.get("lo") is not None:
        s += f" [{e['lo']:+.{n}f}; {e['hi']:+.{n}f}]"
    return s + (" *" if e.get("note") else "")


def write_md(res):
    r = res["results"]; t67, t68, ar, au = r["table67"], r["table68"], r["arterials"], r["austin"]
    L = ["# CONGELAMENTO_4A — what a loop detector measures\n",
         f"Generated by `paper4/code/p4a.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit "
         f"{res['commit']} (code dirty: {res['code_dirty']}). Pre-registration `protocol/paper4/P4A.md` ({res['prereg_fingerprint']}). "
         f"Input `paper4/runs/p4a/results.json` ({res['results_sha256']}). Intervals: 95%, {B} replicates, block bootstrap "
         f"over sensors (arterials: loops; Austin: sections). **Descriptive**: the reading rules of P4A.md were fixed knowing "
         f"the deliverable's in-sample values.\n",
         "## Readings (declared reading rules, descriptive)\n"] + [f"- **{k}:** {v}" for k, v in res["readings"].items()]
    L += ["\n## Correction 1 — M30 threshold out of sample (mean over 5 splits [interval])\n",
          "| Reading | Rule F1: threshold per split | F1 | Precision | Recall | Rule FA: threshold per split | Recall | Realised false-alarm rate |",
          "|---|---|---|---|---|---|---|---|"]
    for k, lab in (("between_sensors", "between sensors, whole year (primary)"), ("in_time", "in time, Jan–Mar → Apr–Dec (secondary)")):
        e = r["correction1"][k]
        L.append(f"| {lab} | {' / '.join(f'{s['threshold_F1']:.2f}' for s in e['per_split'])} | {fv(e['F1'])} | {fv(e['precision'])} | "
                 f"{fv(e['recall'])} | {' / '.join(f'{s['threshold_FA']:.2f}' for s in e['per_split'])} | {fv(e['recall_FA'])} | {fv(e['fa_FA'])} |")
    L += ["\n## Table 67 — M30, reconstructed against measured factor (non-imputed cells)\n",
          "| Figure | Cells | Value [interval] |", "|---|---|---|"]
    for k in ("overall", "band 5-10%", "band 10-20%", "band 20-40%", "band 40-100%", "class green", "class yellow", "class red"):
        L.append(f"| rank correlation, {k} | {t67[k].get('n', 0):,} | {fv(t67[k])} |")
    L += [f"| area under the curve, red against rest | | {fv(t67['auc red'])} |",
          f"| area under the curve, yellow+red against green | | {fv(t67['auc yellow+red'])} |",
          f"| deliverable rule at 0.30, in sample: precision / recall / F1 | | {t67['deliverable rule, in sample']['0.30']['precision']:.3f} / "
          f"{t67['deliverable rule, in sample']['0.30']['recall']:.3f} / {t67['deliverable rule, in sample']['0.30']['F1']:.3f} |",
          f"| random precision | | {t67['random precision']:.3f} |"]
    L += ["\n## Table 68 — matching error, M30 reference replaced by a neighbour\n",
          "| Reference | Sensors | Median distance (m) | Rank correlation | Area under the curve | Gini |", "|---|---|---|---|---|---|"]
    for k, e in t68.items():
        if "note" in e:
            L.append(f"| {k} | — | — | {e['note']} | | |"); continue
        L.append(f"| {k}{' (built a posteriori)' if '19-72' in k else ''} | {e['sensors']} | {e['median_distance_m']:.0f} | "
                 f"{fv(e['spearman'])} | {fv(e['auc'])} | {fv(e['gini'])} |")
    L.append(f"| arterials, median over pairs (primary) | {ar['pairs_with_auc']} pairs | — | {fv(ar['spearman_median'])} | {fv(ar['auc_median'])} | "
             f"{2 * ar['auc_median']['value'] - 1:+.3f} |")
    L.append(f"| arterials, pooled cells (secondary) | {ar['pairs']} pairs | — | {fv(ar['spearman_pooled'])} | {fv(ar['auc_pooled'])} | "
             f"{2 * ar['auc_pooled']['value'] - 1:+.3f} |")
    gs = r["gini_split"]
    L.append(f"\nShare of the arterial gap due to matching, (G_same − G_19–72 m) / (G_same − G_arterials): primary "
             f"{fv(gs['primary']['share_matching'])}; secondary {fv(gs['secondary']['share_matching'])}. Shift of the arterial "
             f"pairs: {ar['shift_quarter_hours']} quarter-hours.\n")
    L += ["## Table 69 and correction 3 — Austin, lanes\n",
          f"Cells {au['counts']['cells']:,}; lanes {au['counts']['lanes']}; sections {au['counts']['sections']}. Within-lane rank "
          f"correlation, median {fv(au['within_lane_spearman_median'], 4)} (interquartile range {au['within_lane_spearman_iqr'][0]:+.3f}; "
          f"{au['within_lane_spearman_iqr'][1]:+.3f}); within-lane area under the curve, median {fv(au['within_lane_auc_median'])} "
          f"(interquartile range {au['within_lane_auc_iqr'][0]:.3f}; {au['within_lane_auc_iqr'][1]:.3f}). Volume–occupancy rank "
          f"correlation, sections with ≥ 3 lanes ({au['sections_3plus_lanes']}): lane level {fv(au['volume_occupancy_lane'], 4)}, "
          f"section level {fv(au['volume_occupancy_section'], 4)}.\n",
          "| Lanes per section | Sections | Cells | Median area under the curve [interval] | Interquartile range | Difference of prevalence (points) |",
          "|---|---|---|---|---|---|"]
    for k, e in au["table69"].items():
        iq = e["auc_iqr"]
        L.append(f"| {k} | {e['sections']} | {e['cells']:,} | {fv(e['auc_median'])} | {f'{iq[0]:.3f}; {iq[1]:.3f}' if iq else '—'} | "
                 f"{fv(e['prevalence_difference_points'], 2)} |")
    c3 = r["correction3"]
    L.append(f"\nCorrection 3: rank correlation between lanes and section area under the curve over {c3['sections']} sections "
             f"(by lanes: {c3['by_lanes']}): {fv(c3['spearman_lanes_auc'])}.\n\n\\* fewer than 5 sections: no interval.\n")
    L += ["## Comparison with the deliverable (every regenerated value read from `results.json`)\n",
          "| Quantity | Where | Deliverable | Regenerated | Outcome |", "|---|---|---|---|---|"]
    for k, (where, s, rg, oc) in res["comparison"].items():
        L.append(f"| {k} | {where} | {s} | {rg} | {oc} |")
    L += ["\n## Controls, deviations and defects\n",
          "1. Inputs and scripts checked against the fingerprints of P4A.md before the run; the three base CSVs of "
          "`t4c_crossval.py` identical to Phase 1.",
          "2. The thresholds of correction 1 were chosen on half A and saved with fingerprint before any metric of half B.",
          "3. The arterial values of Table 68 and the Austin volume–occupancy correlations are recomputed "
          "(register of corrections, items 14–16); the deliverable's brackets of Austin are interquartile ranges (item 17).",
          "4. The 19–72 m band was built a posteriori by the deliverable and is kept because the Gini split uses it."]
    mp = OUT / "CONGELAMENTO_4A.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {OUT / 'p4a_risultati.json'} "
          f"({p4b.sha256(OUT / 'p4a_risultati.json', 16)})")


def selftest_e2e(args):
    """Every step of `run` after the deliverable scripts, and `freeze`, on synthetic data, with 20 replicates.
    Reads no real measured class: M30, arterials and Austin are simulated; Table 64-65 outputs are the Phase 1
    screen logs, already public."""
    import shutil
    global RUNS, OUT, B
    tmp = Path(args.tmpdir)
    if tmp.exists():
        shutil.rmtree(tmp)
    RUNS, OUT, B = tmp / "p4a", tmp / "congelamenti", 20; RUNS.mkdir(parents=True)
    g = np.random.default_rng(3); S, T = 279, 3000
    truth = np.clip(g.beta(5, 1.5, (T, S)) * 1.2, 0, 1.5).astype("float32")
    oc = g.uniform(0, 60, (T, S)).astype("float32")
    r_pr = np.clip(truth + g.normal(0, 0.03, (T, S)), 0, 1.5).astype("float32"); r_pr[oc < OCC_EMPTY] = np.nan
    d = {"r_pr": r_pr, "r_tr": truth, "oc": oc, "sp": np.full((T, S), 50.0, "float32"), "sub": [str(i) for i in range(S)],
         "imputate": oc < OCC_EMPTY}
    XY = np.c_[np.repeat(np.arange(S // 3 + 1) * 500.0, 3)[:S], np.tile([0.0, 30.0, 90.0], S // 3 + 1)[:S]]
    ts = np.datetime64("2024-01-01T00:00") + np.arange(T) * np.timedelta64(140, "m")
    res = {"m30_counts": {"sensors": S, "imputed_share": float((oc < OCC_EMPTY).mean())}}
    rep68 = table67_68(d, res, XY=XY)
    P = 60; Mt = np.clip(g.beta(4, 2, (2000, P)) * 1.2, 0, 1.5).astype("float32")
    Gt = np.clip(Mt + g.normal(0, 0.6, Mt.shape), 0, 1.5).astype("float32")
    rep_art = arterials({"G": Gt, "M": Mt, "shift": 1}, res); gini_split(res, rep68, rep_art)
    correction1(d, res, ts=ts)
    rows = []
    for sec in range(12):
        k = 1 + sec % 4
        for lane in range(k):
            n = 600; sp_ = g.uniform(5, 60, n); rows.append(pd.DataFrame({
                "sez": f"s{sec}", "corsia": f"s{sec}|l{lane}", "ist": np.arange(n).astype(str), "volume": g.uniform(1, 50, n),
                "occupancy": g.uniform(1, 60, n), "speed": sp_, "r_pr": np.clip(sp_ / 50 + g.normal(0, 0.1, n), 0, 1.5),
                "r_tr": np.clip(sp_ / 50, 0, 1.5)}))
    x = pd.concat(rows, ignore_index=True); x["rosso"] = x.r_tr < RED
    austin(x, res)
    cv = {k: parse_crossval((ROOT / "protocol" / "paper4" / "fase1" / "crossval" / f"log_{k}.txt").read_text())
          for k in ("base", "noempty", "d30")}
    for k in cv:
        cv[k]["corr_median_csv"] = float(pd.read_csv(ROOT / "protocol" / "paper4" / "fase1" / "crossval" /
                                                    {"base": "crossval_results.csv", "noempty": "crossval_results_noempty.csv",
                                                     "d30": "crossval_results_d30.csv"}[k])["corr"].median())
    res["crossval"] = cv
    (RUNS / "screen.txt").write_text("synthetic"); res["screen_outputs"] = {"screen.txt": p4b.sha256(RUNS / "screen.txt", 16)}
    (RUNS / "results.json").write_text(json.dumps(res, indent=1, default=float))
    freeze(argparse.Namespace())
    out = json.loads((OUT / "p4a_risultati.json").read_text())
    ok = (OUT / "CONGELAMENTO_4A.md").exists() and set(out["readings"]) == {"dissociation", "matching", "lanes"}
    ok &= out["comparison"]["T64 pairs"][3] == "identical" and out["comparison"]["T65 Spearman r"][3] == "identical"
    ok &= out["comparison"]["T64 corr median, 30 m"][3] == "identical"
    c1 = out["results"]["correction1"]["between_sensors"]
    ok &= all(abs(s_["threshold_F1"] - 0.4) <= 0.15 for s_ in c1["per_split"]) and c1["F1"]["lo"] is not None
    ok &= (RUNS / "thresholds" / "thresholds.fingerprint").exists()
    print(f"synthetic readings: {out['readings']}; thresholds F1 {[s_['threshold_F1'] for s_ in c1['per_split']]}")
    if not getattr(args, "keep", False):
        shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="P4A")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for c in ("selftest", "preflight", "cost", "run", "freeze"):
        sp.add_parser(c)
    e2 = sp.add_parser("selftest-e2e"); e2.add_argument("tmpdir")
    a = ap.parse_args()
    return {"selftest": lambda a: selftest(), "preflight": preflight, "cost": cost, "run": run, "freeze": freeze,
            "selftest-e2e": selftest_e2e}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
