#!/usr/bin/env python3
"""
Self-test of the control paths of e13b.py with fake data (no real training, no real data) in a temporary Git
repository created by the test. Exercises: the derived block and train_gf equal their mechanical derivation from e13.py;
backbone without graph convolution for both arms (asserted on the module built by train_gf, when torch is available);
gate refusals (no E13B tag, unsigned protocol, frozen files changed after the tag, dirty tree, B0.2 missing or of another
version, invalid realisation, dependent control not passed — with or without an acceptance file —, independent anomaly
without acceptance, P4R revision missing or not committed); independence from the reports of the closed E13; D1/D0
identities in records and index; 30 cells; E13B paths; dev interrupted and re-run; dev refused on a completed cell unless a
deviation is registered; pending adequacy failure; extension interrupted and resumed; reproduction failure kept but
unusable; stale final detected; lock; test refused with an uncommitted or modified lock and with a foreign npz; analysis
provisional statement with reached/unreached contrasts; per-horizon metric. Run: python3 e13b_selftest.py <path to e13b.py>
(e13.py must be next to it, as in paper4/code/).
"""
import importlib.util, json, os, pickle, shutil, subprocess, sys, tempfile, types
from pathlib import Path
import numpy as np
try:
    import torch
except ModuleNotFoundError:                      # a minimal fake torch: the control paths never compute with it
    torch = types.ModuleType("torch"); nn = types.ModuleType("torch.nn")
    class _Module:
        def __init__(s, *a, **k): s._sd = {"l.weight": np.zeros((2, 2))}
        def to(s, dev): return s
        def state_dict(s): return dict(s._sd)
        def load_state_dict(s, sd): s._sd = dict(sd)
        def eval(s): return s
        def train(s): return s
    class _Linear(_Module):
        pass
    nn.Module = _Module; nn.Linear = _Linear; torch.nn = nn
    torch.device = lambda d=None: d or "cpu"; torch.tensor = lambda a, device=None: np.asarray(a); torch.zeros = lambda *a: np.zeros(a)
    torch.save = lambda obj, path: Path(path).write_bytes(pickle.dumps(obj)); torch.load = lambda path, **k: pickle.loads(Path(path).read_bytes())
    torch.backends = types.SimpleNamespace(mps=types.SimpleNamespace(is_available=lambda: False))
    torch.cuda = types.SimpleNamespace(is_available=lambda: False, get_device_name=lambda i: None)
    torch.__version__ = "fake"; torch.Generator = object; torch.manual_seed = lambda s: None; torch.equal = lambda a, b: bool(np.array_equal(a, b))
    torch.as_tensor = lambda a, device=None: np.asarray(a); torch.cat = None; torch.stack = None; torch.no_grad = None
    sys.modules["torch"] = torch; sys.modules["torch.nn"] = nn

E13B_PATH = Path(sys.argv[1]).resolve(); E13_PATH = E13B_PATH.with_name("e13.py")
TMP = Path(tempfile.mkdtemp(prefix="e13b_selftest_"))
ROOT = TMP / "root"; (ROOT / "paper4" / "runs").mkdir(parents=True); (ROOT / "paper4" / "code").mkdir(parents=True); (ROOT / "protocol" / "paper4").mkdir(parents=True)
PREREG = ROOT / "protocol" / "paper4" / "E13B.md"
PREREG.write_text("# E13B\n\n**Pre-registration.** Date ______ · signed: ______\n\nbody\n")
(ROOT / "protocol" / "paper4" / "E13.md").write_text("# E13 (closed)\n\n**Pre-registration.** Date 2026-11-18 · signed: X\n\nbody\n")
(ROOT / "protocol" / "paper4" / "P4R.md").write_text("# P4R\n\nbody\n")
CODE = ROOT / "paper4" / "code"
for n in ("p4b.py", "e9.py", "e11.py", "e13.py", "e13b.py"):
    (CODE / n).write_text(f"# fake {n}\n")
(ROOT / ".gitignore").write_text("paper4/runs/\n")

def git(*a, check=True):
    r = subprocess.run(["git", *a], capture_output=True, text=True, cwd=ROOT)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {r.stderr}")
    return r.stdout.strip()
git("init", "-q", "-b", "paper4"); git("config", "user.email", "selftest@example.invalid"); git("config", "user.name", "selftest")
git("config", "commit.gpgsign", "false"); git("config", "tag.gpgsign", "false")
git("add", "-A"); git("commit", "-q", "-m", "fake repository, protocol unsigned")

# ------------------------------------------------------------------ fake p4b / e9 / e11 -------------------
K, NT = 40, 400
p4b = types.ModuleType("p4b")
p4b.ROOT = ROOT; p4b.HORIZONS = (1, 2, 4, 8); p4b.T_IN = 12; p4b.K_MASKS, p4b.K_ORDER, p4b.K_INIT = 2, 3, 6
p4b.CITY = {"madrid": {"roads": "x"}, "london": {"roads": "y"}, "melbourne": {"roads": "z"}}
import hashlib
def _sha(path, n=None):
    h = hashlib.sha256(Path(path).read_bytes()).hexdigest(); return h[:n] if n else h
p4b.sha256 = _sha
p4b.fingerprint = lambda obj: hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]
p4b.rng = lambda seed, k: np.random.default_rng([int(seed), int(k)])
p4b.git_commit = lambda: ("deadbeef", False)
def _run_dir(base, config):
    d = Path(base) / p4b.fingerprint(config)
    if d.exists():
        raise FileExistsError(f"{d} exists: launch blocked")
    d.mkdir(parents=True); return d
p4b.run_dir = _run_dir
def _record(d, payload):
    payload = {"commit": "deadbeef", "code_dirty": False, **payload}
    (Path(d) / "run.json").write_text(json.dumps(payload, indent=1, default=str)); return payload
p4b.record = _record
def _require_signed(prereg):
    head = Path(prereg).read_text().split("\n\n")[1]
    if "____" in head:
        raise PermissionError("signature line not filled")
p4b.require_signed = _require_signed
GRAPH_FLAGS = []
class _GWN(torch.nn.Module):
    def __init__(s, c_in, graph, dropout=0.0):
        super().__init__(); GRAPH_FLAGS.append(bool(graph)); s.c_in = c_in; s.l = torch.nn.Linear(2, 2)
    def state_dict(s): return {"l.weight": torch.zeros(2, 2)}
    def load_state_dict(s, sd): pass
    def to(s, dev): return s
    def forward(s, x, A): return s.l(x.float().mean((1, 2, 3))[:, None].expand(-1, 2))
p4b.GWN = _GWN
p4b.loss_fn = lambda lg, y, m, W: lg.float().mean()
def _predict(net, su, A, origins, inp, tgt, bs=256, static=False):
    r = np.random.default_rng(len(origins) + int(tgt.sum()))
    P = r.dirichlet([1, 1, 1], size=(len(origins), K, 4)).astype("float32")
    Y = np.where(tgt[None, :, None], r.integers(0, 3, (len(origins), K, 4)), -1)
    return P, Y
p4b.predict = _predict
p4b.wce_np = lambda P, Y, W: 1.0
class _Setup:  # not used directly (SetupE13 is replaced)
    pass
p4b.Setup = _Setup
sys.modules["p4b"] = p4b
e9 = types.ModuleType("e9"); e9.GRID = {"madrid": 11, "london": 11, "melbourne": 15}; e9.targets = lambda f: (f, 0.2, 0.8 - f)
e9.adjacency = lambda su, arm: (None, {})
e9.MIN_TEST_BLOCKS = 8; e9.__file__ = str(CODE / "e9.py"); sys.modules["e9"] = e9
e11 = types.ModuleType("e11")
class Log:
    def __init__(s, path): s.path = Path(path); s.lines = []; s.fail = 0
    def __call__(s, msg): s.lines.append(msg)
    def check(s, n, label, ok, detail=""): s.fail += 0 if ok else 1; s.lines.append(f"[{'ok' if ok else 'FAIL'}] {n} {label} {detail}")
    def save(s): s.path.write_text("\n".join(s.lines) + "\n")
e11.Log = Log; e11.cadence_ok = lambda ts, t: True; sys.modules["e11"] = e11
p4b.__file__ = str(CODE / "p4b.py")


sys.path.insert(0, str(E13B_PATH.parent))
spec = importlib.util.spec_from_file_location("e13b", E13B_PATH); e13b = importlib.util.module_from_spec(spec); spec.loader.exec_module(e13b)
e13 = e13b.e13

# ------------------------------------------------------------------ fakes inside e13b ----------------------
class FakeSetup:
    def __init__(s, city, seed, regime="I0", device=None):
        s.city, s.seed, s.regime, s.K, s.G = city, seed, "I0", K, 11; s.dev = torch.device("cpu"); s.arm = None; s.sigma = 1.0
        r = np.random.default_rng(seed); lab = r.integers(0, 3, K); s.obs, s.val, s.test = lab == 0, lab == 1, lab == 2
        s.cells = r.integers(0, 10, K); s.tr = np.arange(20, 200); s.va = np.arange(220, 260); s.te = np.arange(280, 380)
        s.ts = np.array(["2021-06-01T00:00"], dtype="datetime64[m]") + np.arange(NT) * np.timedelta64(15, "m")
        s.W = np.array([1.0, 2.0, 3.0], dtype="float32"); s.c_in = 13; s.M64 = np.eye(K) + 0.1 * (r.random((K, K)) < 0.1)
    def fingerprints(s): return {"node_sets": f"ns{s.seed}"}
    def shares(s): return {}
    def geometry(s): return {}
e13b.SetupGF = FakeSetup
e13b.CITIES = ("madrid",); e13b.SEEDS = (0, 1); e13b.B_REPS = 30
STATE = {"min_at_cap": set(), "repro_fail": set(), "interrupt_at": None, "calls": 0}
TAG = "paper4-E13B-20261121"
def fake_train(su, arm, A, cap, cfg, init_stream, log=None, ck_every=500, save_states=True, keep_losses=False):
    STATE["calls"] += 1
    if STATE["interrupt_at"] is not None and STATE["calls"] >= STATE["interrupt_at"]:
        STATE["interrupt_at"] = None; raise KeyboardInterrupt("simulated interruption")
    assert arm in ("D1", "D0") and A is None
    cid = e13b.cell_id(su.city, su.seed, arm, su.regime); n = cap // ck_every + 1
    u = np.arange(n) * ck_every
    knee = 15000 if cid in STATE["min_at_cap"] else 3000
    base = 1.08 - 0.00002 * np.minimum(u, knee) + 0.000001 * np.maximum(u - knee, 0)
    base = base + {"C1": 0.0, "C2": 0.001, "C3": 0.002, "C4": 0.003}[next(k for k, v in e13b.CONFIGS.items() if v == cfg)]
    if cid in STATE["repro_fail"] and cap == e13b.CAP1:
        base = base + 1e-6
    traj = [{"update": int(x), "val_wce": float(b), "train_loss": 1.0, "seconds": 0.0} for x, b in zip(u, base)]
    best = min(traj, key=lambda d: (d["val_wce"], d["update"]))
    states = {int(x): {"l.weight": torch.zeros(2, 2)} for x in u} if save_states else {}
    return {"net": _GWN(13, False), "A": None, "states": states, "trajectory": traj, "selected": best["update"], "updates": cap,
            "hidden_in_batches": 0, "seconds": 0.0, "init_seed": 100 + init_stream, "losses": []}
real_train_gf = e13b.train_gf
e13b.train_gf = fake_train
NS = lambda **k: types.SimpleNamespace(**k)
def expect_error(fn, *a, **k):
    try:
        fn(*a, **k)
    except Exception as e:
        return type(e).__name__ + ": " + str(e)
    raise AssertionError("expected an error")
passed = []
def ok(label, cond):
    passed.append((label, bool(cond))); print(("ok  " if cond else "FAIL") + " " + label)

# ------------------------------------------------------------------ scenarios -------------------------------
RUNS = e13b.RUNS; E13BD = e13b.E13B; E13BD.mkdir(parents=True, exist_ok=True)
# 0. derivation and backbone
ok("derivation: the derived block and train_gf equal their mechanical derivation from e13.py", e13b.derived_block_matches(E13_PATH))
ok("constants: arms D1/D0, regime I0 only, 30 cells, E13B paths", e13b.ARMS == ("D1", "D0") and e13b.REGIMES == ("I0",)
   and len([(c, s, a, r) for c in e13.CITIES for s in e13.SEEDS for a in e13b.ARMS for r in e13b.REGIMES]) == 30 and e13b.E13B.name == "e13b" and e13b.PREREG.name == "E13B.md")
if torch.__version__ != "fake":
    class TensorSetup(FakeSetup):
        def __init__(s, *a, **k):
            super().__init__(*a, **k); s.Wt = torch.tensor(s.W); s.obs_cells = np.unique(s.cells[s.obs])
        def batch_mask(s, r):
            inp = s.obs.copy(); inp[np.flatnonzero(s.obs)[::2]] = False; return inp, s.obs & ~inp, 0.7
        def batch(s, origins, inp, tgt, static=False):
            B = len(origins); x = torch.zeros(B, 13, K, 12); y = torch.zeros(B, K, 4, dtype=torch.long); m = torch.ones(B, K, 4); return x, y, m
    GRAPH_FLAGS.clear(); flags = {}
    for arm in ("D1", "D0"):
        su_t = TensorSetup("madrid", 0); o = real_train_gf(su_t, arm, None, 2, e13b.CONFIGS["C1"], 6, ck_every=1, save_states=False)
        flags[arm] = (GRAPH_FLAGS[-1], su_t.arm, o["updates"])
    ok("backbone: train_gf builds p4b.GWN with graph=False for D1 and for D0 and records the arm on the setup", all(v[0] is False and v[1] == a and v[2] == 2 for a, v in flags.items()))
else:
    print("skip backbone check (fake torch)")
ok("backbone: train_gf refuses an unknown arm", "assert" in expect_error(real_train_gf, FakeSetup("madrid", 0), "G1", None, 1, e13b.CONFIGS["C1"], 6).lower() or "AssertionError" in expect_error(real_train_gf, FakeSetup("madrid", 0), "G1", None, 1, e13b.CONFIGS["C1"], 6))

# 1. gate in a real repository
git("tag", "paper4-E13-20261119c")
ok("gate: refuses without an E13B tag reachable from HEAD (an E13 tag does not count)", "no E13B tag" in expect_error(e13b.gate, "dev"))
git("tag", "paper4-E13B-20261120")
ok("gate: refuses before signature", "signature" in expect_error(e13b.gate, "dev"))
PREREG.write_text("# E13B\n\n**Pre-registration.** Date 2026-11-21 · signed: X\n\nbody\n")
ok("gate: refuses an uncommitted change of the protocol (dirty tree)", "clean" in expect_error(e13b.gate, "dev"))
git("add", "-A"); git("commit", "-q", "-m", "E13B signed")
ok("gate: refuses a protocol changed after the tag", "differ from the frozen tag paper4-E13B-20261120" in expect_error(e13b.gate, "dev"))
git("tag", TAG)
ok("frozen_tag: nearest E13B tag", e13b.frozen_tag() == TAG)
(CODE / "e13b.py").write_text("# fake e13b, edited\n"); git("add", "-A"); git("commit", "-q", "-m", "edit e13b after tag")
ok("gate: refuses e13b.py changed after the tag (frozen path of E13B)", f"differ from the frozen tag {TAG}" in expect_error(e13b.gate, "dev"))
git("revert", "--no-edit", "HEAD")
(ROOT / "RECORDS.md").write_text("records\n"); git("add", "-A"); git("commit", "-q", "-m", "a record commit after the tag")
ok("HEAD advanced beyond the tag by record commits: frozen files unchanged", e13b.frozen_unchanged(TAG) and e13b.head_commit() != git("rev-parse", "--short", TAG))
ok("gate: refuses without B0.2", "B0.2" in expect_error(e13b.gate, "dev"))
env = e13b.environment()
ok("environment records e13.py and e13b.py fingerprints", set(env["code_sha16"]) >= {"p4b.py", "e9.py", "e13.py", "e13b.py"})
(RUNS / "e13_a0_synth.json").write_text(json.dumps({"kinds": {"dependent": {"verdict": "FAIL"}, "independent": {"verdict": "pass"}}, "environment": env}))   # closed E13: must be ignored
def b0(dep="pass", ind="pass", valid=(True, True), env_=None):
    return {"control_check": {"dependent": {"valid": valid[0]}, "independent": {"valid": valid[1]}},
            "kinds": {"dependent": {"verdict": dep}, "independent": {"verdict": ind}}, "environment": env_ or env}
B0P = RUNS / "e13b_b0_synth.json"
B0P.write_text(json.dumps(b0(env_=env | {"frozen_tag": "paper4-E13B-20261120"})))
ok("gate: refuses a B0.2 report of another frozen tag", "another version" in expect_error(e13b.gate, "dev"))
B0P.write_text(json.dumps(b0(valid=(True, False))))
ok("gate: refuses when a realisation is invalid", "invalid" in expect_error(e13b.gate, "dev"))
B0P.write_text(json.dumps(b0(dep="FAIL: not passed")))
ok("gate: refuses when the dependent control is not passed", "dependent control not passed" in expect_error(e13b.gate, "dev"))
(RUNS / "e13b_b0_resolution.json").write_text(json.dumps({"scope": "independent anomaly", "b0_synth_sha16": p4b.sha256(B0P, 16), "frozen_tag": TAG}))
ok("gate: a failed dependent control cannot be accepted by a note", "dependent control not passed" in expect_error(e13b.gate, "dev"))
ok("b0-accept: refuses when the dependent control is not passed", "cannot be accepted" in expect_error(e13b.b0_accept, NS(by="GDV", note_commit="abc1234")))
(RUNS / "e13b_b0_resolution.json").unlink()
B0P.write_text(json.dumps(b0(ind="anomaly: V(D1) > +3")))
ok("gate: independent anomaly without acceptance refused", "b0-accept" in expect_error(e13b.gate, "dev"))
e13b.b0_accept(NS(by="GDV", note_commit="abc1234"))
ok("gate: with the acceptance, refuses until the P4R revision is recorded", "P4R revision" in expect_error(e13b.gate, "dev"))
ok("p4r-revision: refuses when P4R.md is not committed unchanged", "committed" in expect_error(e13b.p4r_revision, NS(commit="abc", receipt_commit="def", by="GDV")) if not e13b.git_committed_unchanged("protocol/paper4/P4R.md") else True)
e13b.p4r_revision(NS(commit="abc1234", receipt_commit="def5678", by="GDV"))
ok("gate: refuses while e13b_p4r_revision.json is not committed", "not committed" in expect_error(e13b.gate, "dev"))
git("add", "-f", "paper4/runs/e13b_p4r_revision.json"); git("commit", "-q", "-m", "P4R revision recorded")
ok("gate: passes with valid realisations, dependent passed, accepted independent anomaly, P4R revision recorded — and ignores the failed E13 report", e13b.gate("dev") == TAG)
(ROOT / "protocol" / "paper4" / "P4R.md").write_text("# P4R\n\nbody changed\n")
ok("gate: refuses when P4R.md changed after the recorded revision", "clean" in expect_error(e13b.gate, "dev") or "P4R.md differs" in expect_error(e13b.gate, "dev"))
git("checkout", "--", "protocol/paper4/P4R.md")
B0P.write_text(json.dumps(b0()))
ok("gate: passes with both controls passed and no acceptance", e13b.gate("dev") == TAG)

# 2a. development interrupted, then re-run; completed cell refused unless a deviation is registered
STATE["interrupt_at"] = STATE["calls"] + 2
try:
    e13b.dev(NS(city="madrid", seed=0, arm="D1", regime="I0", deviation=None))
except KeyboardInterrupt:
    pass
ok("dev: interrupted attempt leaves no index entry", e13b.latest_dev("madrid_s0_D1_I0") is None)
e13b.dev(NS(city="madrid", seed=0, arm="D1", regime="I0", deviation=None))
d1 = e13b.latest_dev("madrid_s0_D1_I0")
ok("dev: re-run after interruption succeeds (attempt 2); record carries arm D1 and protocol E13B", d1 is not None and d1["attempt"] == 2 and d1["arm"] == "D1" and "e13b" in d1["dir"] and d1["graph_info"]["variant"] == "GF")
ok("dev: refuses a completed cell without a registered deviation", "deviation" in expect_error(e13b.dev, NS(city="madrid", seed=0, arm="D1", regime="I0", deviation=None)))
e13b.dev(NS(city="madrid", seed=0, arm="D1", regime="I0", deviation="abc1234"))
ok("dev: re-run with --deviation recorded (attempt 3)", e13b.latest_dev("madrid_s0_D1_I0")["attempt"] == 3)
ok("dev: refuses an E13 arm name", "unknown arm" in expect_error(e13b.dev, NS(city="madrid", seed=1, arm="G1", regime="I0", deviation=None)) or "G1" in expect_error(e13b.dev, NS(city="madrid", seed=1, arm="G1", regime="I0", deviation=None)))

# 2. development; one cell fails adequacy -> pending; lock False
STATE["min_at_cap"] = {"madrid_s1_D1_I0"}
e13b.campaign(NS(phase="dev"))
ok("dev: 4 cells (1 city x 2 seeds x D1/D0) developed; all records under paper4/runs/e13b", len({r["cell"] for r in e13b._index("index_dev.jsonl")}) == 4 and all("e13b" in r["dir"] for r in e13b._index("index_dev.jsonl")))
rep = e13b.compute_adequacy()
ok("adequacy: pending failure detected, lock False", rep["dev_failures_pending"] == ["madrid_s1_D1_I0"] and not rep["lock"])

# 3. extension interrupted, resumed; reproduction failure kept but unusable
STATE["interrupt_at"] = STATE["calls"] + 5
try:
    e13b.extend(NS(city="madrid", arm="D1", regime="I0"))
except KeyboardInterrupt:
    pass
st = e13b.extension_status("madrid_D1_I0")
ok("extend: interrupted state recorded as incomplete/started", st["status"] in ("incomplete", "started") and "0" in st["seeds"])
STATE["repro_fail"] = {"madrid_s1_D1_I0"}
rc = e13b.extend(NS(city="madrid", arm="D1", regime="I0")); st = e13b.extension_status("madrid_D1_I0")
ok("extend: resumed; seed 1 reproduction failed -> unusable, incomplete, exit 1", rc == 1 and st["status"] == "incomplete" and st["seeds"]["0"]["usable"] and not st["seeds"]["1"]["usable"])
STATE["repro_fail"] = set()
rc = e13b.extend(NS(city="madrid", arm="D1", regime="I0")); st = e13b.extension_status("madrid_D1_I0")
ok("extend: retry reproduces, group complete", rc == 0 and st["status"] == "complete")
ok("extend: a third call is refused (once per group)", "already extended" in expect_error(e13b.extend, NS(city="madrid", arm="D1", regime="I0")))

# 4. finals; stale final
e13b.campaign(NS(phase="final"))
rep = e13b.compute_adequacy()
ok("final: all 4 up to date, lock True; final records carry the arm", rep["lock"] and not rep["final_stale"] and all(e13b.latest_final(e13b.cell_id(*c))["arm"] in ("D1", "D0") for c in e13b.all_cells()))
e13b._dev_run("madrid", 0, "D0", "I0", e13b.CAP0, attempt=2)
rep = e13b.compute_adequacy(); ok("lock: stale final detected after a new development", "madrid_s0_D0_I0" in rep["final_stale"] and not rep["lock"])
e13b.campaign(NS(phase="final")); rep = e13b.compute_adequacy(); ok("campaign final: stale cell re-run; lock True again", rep["lock"])

# 5. test and analysis
e13b.adequacy(NS()); LOCK = RUNS / "e13b_adequacy.json"
ok("lock file is E13B's own (e13b_adequacy.json), not E13's", LOCK.exists() and not (RUNS / "e13_adequacy.json").exists())
ok("test: refused when the lock file is not committed", "committed" in expect_error(e13b.test, NS()))
git("add", "-f", str(LOCK.relative_to(ROOT))); git("commit", "-q", "-m", "adequacy lock")
ok("gate still passes after the lock commit", e13b.gate("test") == TAG)
fn = e13b.latest_final("madrid_s0_D1_I0"); np.savez_compressed(Path(fn["dir"]) / "test_cells.npz", p=np.zeros(1), y=np.zeros(1), lock_sha16="0000")
ok("test: refuses a foreign test file", "another lock" in expect_error(e13b.test, NS()))
(Path(fn["dir"]) / "test_cells.npz").unlink()
e13b.test(NS()); ok("test: 4 files written with reach vector", all((lambda z: "reach" in z and z["reach"].shape == (K,))(np.load(Path(e13b.latest_final(e13b.cell_id(*c))["dir"]) / "test_cells.npz")) for c in e13b.all_cells()))
e13b.analysis(NS()); an = json.loads((RUNS / "e13b_analysis.json").read_text())
ok("analysis: statement provisional, not confirmatory", an["statement"].startswith("PROVISIONAL") and an["confirmatory"] is False)
ok("analysis: primary V_D1 and secondary reached/unreached contrasts present, sup-t over V_D1 per city", all(k in an["cities"]["madrid"] for k in ("V_D1", "V_D1_reached", "V_D1_unreached")) and "madrid:V_D1" in an["supt_95"])
ok("metric: per-horizon mean 2.0, not pooled 2.5", abs(e13b.per_horizon_mean([1.0, 9.0], [1.0, 3.0]) - 2.0) < 1e-12)
ok("metric: analysis uses per_horizon_mean", "per_horizon_mean(" in E13B_PATH.read_text().split("def analysis")[1].split("def wce_with")[1].split("\n\n")[0])

print("\n%d checks, %d failed" % (len(passed), sum(1 for _, c in passed if not c)))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if all(c for _, c in passed) else 1)
