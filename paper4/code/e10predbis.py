#!/usr/bin/env python3
"""
E10-pred-bis — the placement comparison of E10-pred under common class weights (`protocol/paper4/E10predbis.md`).
=================================================================================================================
No training. Imports `e10pred.py`, `e12bis.py`, `genera_congelamento_e11.py`, `genera_congelamento_e9.py`, `p4b.py` and
`e9.py` unchanged. E10-pred scored each design with the class weights of its own configuration; here both designs are
scored with one weight vector per city:

  w_k = N / (3·N_k), N_k = cells of class k over the training period (t < reg_end), ALL segments of the city

Quantities (same common segments, seeds × blocks and replicate draws as E10-pred):
  Δ_G0, Δ_G1   100·(wCE_blocks − wCE_uniform)/wCE_blocks on the common test-hidden segments, common weights (primary)
  V(G1)        per design on its own test-hidden segments, common weights (control)
  check        with the design weights, Δ and V equal the frozen record of E10-pred to the bit, else STOP

    selftest      synthetic checks of the scoring (control 4)
    preflight     controls 1-5 of E10predbis.md, reading no test target
    freeze        after the signature: CONGELAMENTO_E10predbis.md and e10predbis_risultati.json (the executor runs it)
    selftest-e2e  freeze end to end on synthetic predictions

Usage: $PY paper4/code/e10predbis.py selftest | preflight | freeze | selftest-e2e <tmpdir>
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9  # noqa: E402
import e10pred  # noqa: E402
from e12bis import v_cell, summary  # noqa: E402
from genera_congelamento_e9 import runs_by_key, B, BOOT  # noqa: E402
from genera_congelamento_e11 import node_sums  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E10predbis.md"
OUT = p4b.ROOT / "paper4" / "congelamenti"
E10REC = OUT / "e10pred_risultati.json"
F, ARMS = e10pred.F, e10pred.ARMS


# ---------------------------------------------------------------- weights and scoring ------------------

def common_weights(C, reg_end):
    """w_k = N / (3·N_k) from the classes 1-3 of every segment over the training period (cells 0..reg_end-1)."""
    c = C[:reg_end]
    n = np.array([(c == k).sum() for k in (1, 2, 3)], dtype="float64")
    return n.sum() / (3 * np.maximum(n, 1)), n


def cell_weighted(data, city, design_arms, W, nodes_of=None, cells=None):
    """As e10pred.cell_for, with the weights W (None: each run's own class_weights)."""
    cells = e10pred.city_cells(city) if cells is None else cells
    cell = {"seeds": {}}
    for s in e9.SEEDS:
        arms = {}; keep = None
        for name, (design, arm) in design_arms.items():
            rec, p, y, nodes = data[(design, city, s, arm)]
            k = nodes if nodes_of is None else np.intersect1d(nodes, nodes_of(s))
            if keep is not None and not np.array_equal(k, keep):
                raise SystemExit(f"STOP: {city} s{s}: arms of one cell on different nodes")
            keep = k
            S, Wn, *_ = node_sums(p, y, keep, rec["class_weights"] if W is None else W)
            arms[name] = (S, Wn)
        cell["seeds"][s] = {"blocks": cells[keep], "arms": arms}
    return cell


def compare(data, city, ci, W, cells=None):
    """V(G1) per design and Δ on the common segments, with weights W (None = design weights), E10-pred's draws."""
    g = [BOOT, 100 + ci]
    cu = cell_weighted(data, city, {"G0": ("uniform", "G0"), "G1": ("uniform", "G1")}, W, cells=cells)
    cb = cell_weighted(data, city, {"G0": ("blocks", "G0"), "G1": ("blocks", "G1")}, W, cells=cells)
    common = lambda s: np.intersect1d(data[("uniform", city, s, "G1")][3], data[("blocks", city, s, "G1")][3])  # noqa: E731
    cc = cell_weighted(data, city, {"G1u": ("uniform", "G1"), "G1b": ("blocks", "G1"), "G0u": ("uniform", "G0"),
                                    "G0b": ("blocks", "G0")}, W, nodes_of=common, cells=cells)
    nb = [len(np.unique(cc["seeds"][s]["blocks"])) for s in e9.SEEDS]
    return {"V_uniform": summary(*v_cell(cu, np.random.default_rng(g), "G1")),
            "V_blocks": summary(*v_cell(cb, np.random.default_rng(g), "G1")),
            "delta_G1": summary(*v_cell(cc, np.random.default_rng(g + [1]), "G1u", ref="G1b")),
            "delta_G0": summary(*v_cell(cc, np.random.default_rng(g + [1]), "G0u", ref="G0b")),
            "min_blocks": int(min(nb))}


def reading(e):
    if e["L"] > 0:
        return "uniform placement forecasts the common segments better"
    if e["U"] < 0:
        return "uniform placement forecasts the common segments worse"
    return "no difference detected"


# ---------------------------------------------------------------- self-test ----------------------------

def synthetic_data(diff_weights=True, same_pred=False, seed=0):
    """Two designs on 60 nodes in 15 blocks, 40 origins, 4 horizons; hidden sets overlap on 30 nodes."""
    g = np.random.default_rng(seed); K, T, H = 60, 40, 4
    cells = np.repeat(np.arange(15), 4); data = {}
    for city in e9.CITIES:
        for s in e9.SEEDS:
            y = g.integers(0, 3, (T, K, H)); y[g.random(y.shape) < 0.05] = -1
            base = g.dirichlet([1, 1, 1], (T, K, H)).astype("float32")
            for design, nodes in (("uniform", np.arange(0, 40)), ("blocks", np.arange(10, 50))):
                for arm in ARMS:
                    p = base if same_pred else g.dirichlet([1, 1, 1], (T, K, H)).astype("float32")
                    w = [0.5, 1.5, 6.5] if (design == "uniform" or not diff_weights) else [0.5, 1.4, 5.0]
                    data[(design, city, s, arm)] = ({"class_weights": w}, p, y, nodes)
    return data, cells


def selftest():
    ok = True
    data, cells = synthetic_data(same_pred=True)
    r = compare(data, "madrid", 0, np.array([0.6, 1.3, 4.0]), cells=cells)
    ok &= abs(r["delta_G0"]["V"]) < 1e-12 and abs(r["delta_G1"]["V"]) < 1e-12
    print(f"identical predictions, common weights: Δ_G0 {r['delta_G0']['V']:.2e}, Δ_G1 {r['delta_G1']['V']:.2e}")
    data, cells = synthetic_data()
    old_cells = e10pred.city_cells
    e10pred.city_cells = lambda city: cells
    try:
        ref = e10pred.cell_for(data, "madrid", {"G0": ("uniform", "G0"), "G1": ("uniform", "G1")})
    finally:
        e10pred.city_cells = old_cells
    new = cell_weighted(data, "madrid", {"G0": ("uniform", "G0"), "G1": ("uniform", "G1")}, None, cells=cells)
    same = all(np.array_equal(ref["seeds"][s]["arms"][a_][i], new["seeds"][s]["arms"][a_][i])
               for s in e9.SEEDS for a_ in ARMS for i in (0, 1))
    ok &= same
    print(f"design weights: scoring equal to e10pred.cell_for to the bit: {same}")
    r0 = compare(data, "madrid", 0, None, cells=cells)
    data2 = {k: (({"class_weights": [0.5, 1.5, 9.0]} if k[0] == "blocks" else v[0]),) + v[1:] for k, v in data.items()}
    r1 = compare(data2, "madrid", 0, None, cells=cells)
    vb_same = abs(r0["V_uniform"]["V"] - r1["V_uniform"]["V"]) < 1e-12
    d_moves = abs(r0["delta_G0"]["V"] - r1["delta_G0"]["V"]) > 1e-6
    ok &= vb_same and d_moves
    print(f"weights of one design changed: V(G1) uniform unchanged {vb_same}; Δ_G0 changes {d_moves} "
          f"({r0['delta_G0']['V']:+.3f} -> {r1['delta_G0']['V']:+.3f})")
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- preflight ----------------------------

def code_fp():
    return {k: p4b.sha256(Path(m.__file__), 16) for k, m in
            (("p4b.py", p4b), ("e9.py", e9), ("e10pred.py", e10pred), ("e10predbis.py", sys.modules[__name__]))}


def preflight(args):
    from e11 import Log
    log = Log(e9.RUNS / "e10predbis_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E10-pred-bis preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(" · ".join(f"{k} {v}" for k, v in code_fp().items()))
    _, byu = runs_by_key(e10pred.RUNS); _, by9 = runs_by_key(e10pred.E9RUNS)
    files_ok = setup_ok = same_ok = causal_ok = dw_ok = True; info = {}
    for city in e9.CITIES:
        ref_reg = ref_w = None
        for s in e9.SEEDS:
            sb = e9.setup(city, F, s); su = e10pred.uniform_setup(city, s)
            for design, by, base, st in (("uniform", byu, e10pred.RUNS, su), ("blocks", by9, e10pred.E9RUNS, sb)):
                for arm in ARMS:
                    rec = by[(city, F, s)][arm]; f_ = Path(base) / rec["config_fingerprint"] / "test_hidden.npz"
                    files_ok &= f_.exists() and p4b.sha256(f_, 16) == rec["files"]["test_hidden"]["sha256"]
                    setup_ok &= rec["setup"] == st.fingerprints()
                    dw_ok &= bool(np.array_equal(np.asarray(rec["class_weights"], dtype="float32"), st.W))
            for st in (su, sb):
                w, n = common_weights(st.C, st.reg_end)
                if ref_reg is None:
                    ref_reg, ref_w = st.reg_end, w
                same_ok &= st.reg_end == ref_reg and bool(np.array_equal(w, ref_w))
            C2 = sb.C.copy(); C2[sb.reg_end:] = 1
            causal_ok &= bool(np.array_equal(common_weights(C2, sb.reg_end)[0], ref_w))
            if s == 0:
                info[city] = {"common": ref_w, "counts": n, "uniform_s0": su.W, "blocks_s0": sb.W}
        causal_ok &= bool(np.all(np.isfinite(ref_w)) and np.all(ref_w > 0))
    log.check("1", "60 run records present (30 E10-pred, 30 E9 at f = 20%), test_hidden.npz fingerprints equal to the "
              "records (contents not read); setups equal to E10-pred's uniform rule and to E9's blocks", files_ok and setup_ok)
    log.check("2", "reg_end and the common weights identical for the 5 seeds and the 2 designs of each city; noise after "
              "reg_end leaves the weights identical; weights positive and finite", same_ok and causal_ok)
    log.check("3", "design weights in the 60 run records equal those recomputed by p4b for each design", dw_ok)
    log.check("4", "synthetic: identical predictions give Δ = 0 under any weights; with design weights the scoring equals "
              "e10pred.cell_for to the bit; changing one design's weights moves Δ and leaves the other design's V(G1) unchanged "
              "(selftest)",
              selftest() == 0)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("5", "test metrics refused while the E10-pred-bis signature line is blank", guard)
    log("class weights (free flow, slowed, congested), no target read:")
    for city, d in info.items():
        f3 = lambda w: "(" + ", ".join(f"{x:.3f}" for x in w) + ")"  # noqa: E731
        log(f"  {city}: common {f3(d['common'])} from {int(d['counts'].sum()):,} training cells; seed 0, uniform "
            f"{f3(d['uniform_s0'])}, blocks {f3(d['blocks_s0'])}")
    log(f"PREFLIGHT: {log.fail} failure(s)"); log.save()
    return 0 if log.fail == 0 else 1


# ---------------------------------------------------------------- freeze (after the signature) ---------

def freeze(args, runs_dir=None, e9_dir=None, check=True):
    p4b.require_signed(PREREG)
    if (OUT / "CONGELAMENTO_E10predbis.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E10predbis.md exists; regenerate only on purpose, after moving it")
    if e9_dir is not None:
        e10pred.E9RUNS = Path(e9_dir)
    data = e10pred.load(Path(runs_dir or e10pred.RUNS))
    frozen = json.loads(E10REC.read_text())["rows"] if check else None
    rows = {}
    for ci, city in enumerate(e9.CITIES):
        reg_end = {e9.setup(city, F, s).reg_end for s in e9.SEEDS}
        if len(reg_end) != 1:
            raise SystemExit(f"STOP: {city}: training period differs between seeds")
        su = e9.setup(city, F, 0)
        W, n = common_weights(su.C, su.reg_end)
        dw = compare(data, city, ci, None)
        if check:
            fr = frozen[city]
            pairs = [(dw["V_uniform"], fr["V_uniform"]), (dw["V_blocks"], fr["V_blocks"]),
                     (dw["delta_G1"], fr["common"]["delta_G1"]), (dw["delta_G0"], fr["common"]["delta_G0"])]
            if any(a[k] != b[k] for a, b in pairs for k in ("V", "L", "U")):
                raise SystemExit(f"STOP: {city}: with the design weights the numbers differ from the frozen E10-pred record")
        cw = compare(data, city, ci, W)
        rows[city] = {"weights_common": W.tolist(), "training_cells_by_class": n.tolist(),
                      "weights_design_seed0": {d: list(map(float, data[(d, city, 0, "G1")][0]["class_weights"]))
                                               for d in ("uniform", "blocks")},
                      "common_weights": cw, "design_weights": dw,
                      "readings": {m: reading(cw[f"delta_{m}"]) for m in ARMS}}
    write(rows)
    return 0


def write(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    res = {"rows": rows, "commit": c, "code_dirty": dirty, "prereg_fingerprint": p4b.sha256(PREREG, 16),
           "generator_fingerprint": p4b.sha256(Path(__file__), 16), "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e10predbis_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    fm = lambda x: f"{x:+.2f}"  # noqa: E731
    cv = lambda e: f"{fm(e['V'])} [{fm(e['L'])}; {fm(e['U'])}]"  # noqa: E731
    f3 = lambda w: "(" + ", ".join(f"{x:.3f}" for x in w) + ")"  # noqa: E731
    L = ["# CONGELAMENTO_E10predbis — the placement comparison of E10-pred under common class weights\n",
         f"Generated by `paper4/code/e10predbis.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit {c} "
         f"(code dirty: {dirty}). Pre-registration `protocol/paper4/E10predbis.md` ({res['prereg_fingerprint']}). Inputs: the saved "
         f"predictions of the 30 runs of E10-pred and the 30 runs of E9 at f = 20%, fingerprints checked; with the design weights "
         f"every V, L and U equals the frozen record of E10-pred. Common weights: w_k = N/(3·N_k) over the training period, all "
         f"segments of the city. Intervals: 95%, {B} replicates, seeds × blocks, E10-pred's draws. **Descriptive**: no criterion.\n",
         "## Δ on the common test-hidden segments (primary)\n",
         "Δ = 100·(wCE_blocks − wCE_uniform)/wCE_blocks, positive when uniform placement forecasts them better.\n",
         "| City | Δ G0, common weights | Reading | Δ G1, common weights | Reading | Δ G0 / Δ G1, design weights (E10-pred) |",
         "|---|---|---|---|---|---|"]
    for city, r in rows.items():
        cw, dw = r["common_weights"], r["design_weights"]
        L.append(f"| {city} | {cv(cw['delta_G0'])} | {r['readings']['G0']} | {cv(cw['delta_G1'])} | {r['readings']['G1']} | "
                 f"{fm(dw['delta_G0']['V'])} / {fm(dw['delta_G1']['V'])} |")
    L += ["\n## Control: V(G1) per design, on each design's test-hidden segments\n",
          "| City | Uniform, common weights | Blocks, common weights | Uniform / blocks, design weights (E10-pred) |",
          "|---|---|---|---|"]
    for city, r in rows.items():
        cw, dw = r["common_weights"], r["design_weights"]
        L.append(f"| {city} | {cv(cw['V_uniform'])} | {cv(cw['V_blocks'])} | {fm(dw['V_uniform']['V'])} / {fm(dw['V_blocks']['V'])} |")
    L += ["\n## Class weights (free flow, slowed, congested)\n", "| City | Common | Uniform, seed 0 | Blocks, seed 0 | Min common blocks |",
          "|---|---|---|---|---|"]
    for city, r in rows.items():
        L.append(f"| {city} | {f3(r['weights_common'])} | {f3(r['weights_design_seed0']['uniform'])} | "
                 f"{f3(r['weights_design_seed0']['blocks'])} | {r['common_weights']['min_blocks']} |")
    L += ["\n## Controls, deviations and defects\n",
          "1. The common weights use the training-period labels of every segment, hidden ones included: they enter only the "
          "score, never a model; they do not depend on the design, the seed or any validation or test cell.",
          "2. Register of corrections, item 23: E10-pred scored each design with its own class weights."]
    mp = OUT / "CONGELAMENTO_E10predbis.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)})")


def selftest_e2e(args):
    """freeze end to end on synthetic predictions (signature and the check against E10-pred bypassed): the record is
    written, Δ with common weights differs from Δ with design weights, readings are among the three declared."""
    import shutil
    global OUT, PREREG
    tmp = Path(args.tmpdir)
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    data, cells = synthetic_data()
    old = (e10pred.load, e10pred.city_cells, e9.setup, OUT, PREREG)

    class Su:
        def __init__(s, city, f, seed):
            g = np.random.default_rng(1); s.C = g.integers(0, 4, (200, 60)); s.reg_end = 140
    e10pred.load = lambda d: data; e10pred.city_cells = lambda city: cells; e9.setup = Su
    OUT = tmp; PREREG = tmp / "prereg.md"; PREREG.write_text("# x\n\nsigned: test\n")
    try:
        freeze(None, check=False)
    finally:
        e10pred.load, e10pred.city_cells, e9.setup, OUT, PREREG = old[0], old[1], old[2], old[3], old[4]
    res = json.loads((tmp / "e10predbis_risultati.json").read_text())
    r = res["rows"]["madrid"]
    moved = abs(r["common_weights"]["delta_G0"]["V"] - r["design_weights"]["delta_G0"]["V"]) > 1e-6
    ok = moved and all(v in ("uniform placement forecasts the common segments better",
                             "uniform placement forecasts the common segments worse", "no difference detected")
                       for v in r["readings"].values()) and (tmp / "CONGELAMENTO_E10predbis.md").exists()
    print(f"synthetic: Δ_G0 design weights {r['design_weights']['delta_G0']['V']:+.3f}, common weights "
          f"{r['common_weights']['delta_G0']['V']:+.3f}; readings {r['readings']}")
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E10-pred-bis")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for cmd in ("selftest", "preflight", "freeze"):
        sp.add_parser(cmd)
    e2 = sp.add_parser("selftest-e2e"); e2.add_argument("tmpdir")
    a = ap.parse_args()
    return {"selftest": lambda a: selftest(), "preflight": preflight, "freeze": freeze, "selftest-e2e": selftest_e2e}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
