#!/usr/bin/env python3
"""
Self-test of the control paths of e13.py with fake data (no real training, no real data) in a temporary Git
repository created by the test. Exercises: gate refusals (no E13 tag, unsigned protocol, code or protocol changed
after the tag, dirty tree, A0 reports missing or of another version, anomaly without acceptance); HEAD advanced
beyond the tag by record commits (allowed); dev interrupted and re-run; dev refused on a completed cell unless a
deviation is registered; pending adequacy failure; extension interrupted and resumed; reproduction failure kept
but unusable; stale final detected; lock; test refused with an uncommitted or modified lock and with a foreign npz;
analysis provisional statement; per-horizon metric. Run: python3 e13_selftest.py <path to e13.py>
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

E13_PATH = Path(sys.argv[1]).resolve()
TMP = Path(tempfile.mkdtemp(prefix="e13_selftest_"))
ROOT = TMP / "root"; (ROOT / "paper4" / "runs").mkdir(parents=True); (ROOT / "paper4" / "code").mkdir(parents=True); (ROOT / "protocol" / "paper4").mkdir(parents=True)
PREREG = ROOT / "protocol" / "paper4" / "E13.md"
PREREG.write_text("# E13\n\n**Pre-registration.** Date ______ · signed: ______\n\nbody\n")
CODE = ROOT / "paper4" / "code"
for n in ("p4b.py", "e9.py", "e11.py", "e13.py"):
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
class _GWN(torch.nn.Module):
    def __init__(s, c_in, graph, dropout=0.0):
        super().__init__(); s.l = torch.nn.Linear(2, 2)
    def state_dict(s): return {"l.weight": torch.zeros(2, 2)}
    def load_state_dict(s, sd): pass
    def to(s, dev): return s
p4b.GWN = _GWN
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
e9.adjacency = lambda su, arm: (None if arm == "G0" else np.eye(K, dtype="float32"), {})
e9.MIN_TEST_BLOCKS = 8; e9.__file__ = str(CODE / "e9.py"); sys.modules["e9"] = e9
e11 = types.ModuleType("e11")
class Log:
    def __init__(s, path): s.path = Path(path); s.lines = []; s.fail = 0
    def __call__(s, msg): s.lines.append(msg)
    def check(s, n, label, ok, detail=""): s.fail += 0 if ok else 1; s.lines.append(f"[{'ok' if ok else 'FAIL'}] {n} {label} {detail}")
    def save(s): s.path.write_text("\n".join(s.lines) + "\n")
e11.Log = Log; e11.cadence_ok = lambda ts, t: True; sys.modules["e11"] = e11
p4b.__file__ = str(CODE / "p4b.py")

spec = importlib.util.spec_from_file_location("e13", E13_PATH); e13 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e13)

# ------------------------------------------------------------------ fakes inside e13 -----------------------
class FakeSetup:
    def __init__(s, city, seed, regime, perm_seed=None, device=None):
        s.city, s.seed, s.regime, s.K, s.G = city, seed, regime, K, 11; s.dev = torch.device("cpu")
        r = np.random.default_rng(seed); lab = r.integers(0, 3, K); s.obs, s.val, s.test = lab == 0, lab == 1, lab == 2
        s.cells = r.integers(0, 10, K); s.tr = np.arange(20, 200); s.va = np.arange(220, 260); s.te = np.arange(280, 380)
        s.ts = np.array(["2021-06-01T00:00"], dtype="datetime64[m]") + np.arange(NT) * np.timedelta64(15, "m")
        s.W = np.array([1.0, 2.0, 3.0], dtype="float32"); s.c_in = 13 if regime == "I1" else 11
    def fingerprints(s): return {"node_sets": f"ns{s.seed}"}
    def shares(s): return {}
    def geometry(s): return {}
e13.SetupE13 = FakeSetup
e13.CITIES = ("madrid",); e13.SEEDS = (0, 1); e13.B_REPS = 30
STATE = {"min_at_cap": set(), "repro_fail": set(), "interrupt_at": None, "calls": 0}
TAG = "paper4-E13-20261121"
def fake_train(su, arm, A, cap, cfg, init_stream, log=None, ck_every=500, save_states=True, keep_losses=False):
    STATE["calls"] += 1
    if STATE["interrupt_at"] is not None and STATE["calls"] >= STATE["interrupt_at"]:
        STATE["interrupt_at"] = None; raise KeyboardInterrupt("simulated interruption")
    cid = e13.cell_id(su.city, su.seed, arm, su.regime); n = cap // ck_every + 1
    u = np.arange(n) * ck_every
    knee = 15000 if cid in STATE["min_at_cap"] else 3000            # same curve whatever the cap: reproducible by construction
    base = 1.08 - 0.00002 * np.minimum(u, knee) + 0.000001 * np.maximum(u - knee, 0)
    base = base + {"C1": 0.0, "C2": 0.001, "C3": 0.002, "C4": 0.003}[next(k for k, v in e13.CONFIGS.items() if v == cfg)]
    if cid in STATE["repro_fail"] and cap == e13.CAP1:
        base = base + 1e-6                                         # breaks the reproduction of the 10 000 curve
    traj = [{"update": int(x), "val_wce": float(b), "train_loss": 1.0, "seconds": 0.0} for x, b in zip(u, base)]
    best = min(traj, key=lambda d: (d["val_wce"], d["update"]))
    states = {int(x): {"l.weight": torch.zeros(2, 2)} for x in u} if save_states else {}   # tensors: torch.load (weights_only) rejects numpy
    return {"net": _GWN(1, True), "A": A, "states": states, "trajectory": traj, "selected": best["update"], "updates": cap,
            "hidden_in_batches": 0, "seconds": 0.0, "init_seed": 100 + init_stream, "losses": []}
e13.train_e13 = fake_train
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
RUNS = e13.RUNS; E13D = e13.E13; E13D.mkdir(parents=True, exist_ok=True)
# 1. gate in a real repository: tag, frozen files, clean tree, signature, A0 reports
git("tag", "paper4-E11-20261101")
ok("gate: refuses without an E13 tag reachable from HEAD", "no E13 tag" in expect_error(e13.gate, "dev"))
git("tag", "paper4-E13-20261120")                                   # a tag set by mistake on the unsigned protocol
ok("gate: refuses before signature", "signature" in expect_error(e13.gate, "dev"))
PREREG.write_text("# E13\n\n**Pre-registration.** Date 2026-11-21 · signed: X\n\nbody\n")
ok("gate: refuses an uncommitted change of the protocol (dirty tree)", "clean" in expect_error(e13.gate, "dev"))
git("add", "-A"); git("commit", "-q", "-m", "E13 signed")
ok("gate: refuses a protocol changed after the tag (new signed tag required)", "differ from the frozen tag paper4-E13-20261120" in expect_error(e13.gate, "dev"))
git("tag", TAG)
ok("frozen_tag: nearest E13 tag", e13.frozen_tag() == TAG)
(CODE / "p4b.py").write_text("# fake p4b, edited\n"); git("add", "-A"); git("commit", "-q", "-m", "edit code after tag")
ok("gate: refuses code changed after the tag", f"differ from the frozen tag {TAG}" in expect_error(e13.gate, "dev"))
git("revert", "--no-edit", "HEAD")
(ROOT / "RECORDS.md").write_text("records\n"); git("add", "-A"); git("commit", "-q", "-m", "a record commit after the tag")
ok("HEAD advanced beyond the tag by record commits: frozen files unchanged", e13.frozen_unchanged(TAG) and e13.head_commit() != git("rev-parse", "--short", TAG))
(ROOT / "stray.txt").write_text("x")
ok("gate: refuses an untracked file", "clean" in expect_error(e13.gate, "dev")); (ROOT / "stray.txt").unlink()
ok("gate: refuses without A0.2", "A0.2" in expect_error(e13.gate, "dev"))
env = e13.environment()
synth = {"kinds": {"dependent": {"verdict": "pass"}, "independent": {"verdict": "pass"}}, "environment": env}
(RUNS / "e13_a0_synth.json").write_text(json.dumps(synth))
ok("gate: refuses without A0.3", "A0.3" in expect_error(e13.gate, "dev"))
(RUNS / "e13_a0_identifier.json").write_text(json.dumps({"curves": {}, "environment": env | {"frozen_tag": "paper4-E13-20261120"}}))
ok("gate: refuses an A0 report of another frozen tag", "another version" in expect_error(e13.gate, "dev"))
env2 = json.loads(json.dumps(env)); env2["code_sha16"]["e13.py"] = "0" * 16
(RUNS / "e13_a0_identifier.json").write_text(json.dumps({"curves": {}, "environment": env2}))
ok("gate: refuses an A0 report with another code fingerprint", "another version" in expect_error(e13.gate, "dev"))
(RUNS / "e13_a0_identifier.json").write_text(json.dumps({"curves": {}, "environment": env}))
ok("gate: passes with A0 reports of this frozen version", e13.gate("dev") == TAG)
synth["kinds"]["independent"]["verdict"] = "anomaly: unexpected gain"; (RUNS / "e13_a0_synth.json").write_text(json.dumps(synth))
ok("gate: anomaly without acceptance refused", "a0-accept" in expect_error(e13.gate, "dev"))
e13.a0_accept(NS(by="GDV", note_commit="abc1234")); ok("gate: anomaly with acceptance passes", e13.gate("dev") == TAG)

# 2a. development interrupted, then re-run (attempt counter); completed cell refused unless a deviation is registered
STATE["interrupt_at"] = STATE["calls"] + 2
try:
    e13.dev(NS(city="madrid", seed=0, arm="G0", regime="I0", deviation=None))
except KeyboardInterrupt:
    pass
ok("dev: interrupted attempt leaves no index entry", e13.latest_dev("madrid_s0_G0_I0") is None)
e13.dev(NS(city="madrid", seed=0, arm="G0", regime="I0", deviation=None))
d1 = e13.latest_dev("madrid_s0_G0_I0")
ok("dev: re-run after interruption succeeds (attempt 2, no folder collision)", d1 is not None and d1["attempt"] == 2)
ok("dev: refuses a completed cell without a registered deviation", "deviation" in expect_error(e13.dev, NS(city="madrid", seed=0, arm="G0", regime="I0", deviation=None)))
e13.dev(NS(city="madrid", seed=0, arm="G0", regime="I0", deviation="abc1234"))
d2 = e13.latest_dev("madrid_s0_G0_I0")
ok("dev: re-run with --deviation recorded (attempt 3, deviation stored)", d2["attempt"] == 3 and d2["deviation"] == "abc1234")

# 2. development; one cell fails adequacy (min at cap) -> pending; final blocked for its group; lock False
STATE["min_at_cap"] = {"madrid_s1_G1_I0"}
e13.campaign(NS(phase="dev"))
ok("dev: 8 cells developed (campaign skips the completed one)", len({r["cell"] for r in e13._index("index_dev.jsonl")}) == 8 and len(e13._index("index_dev.jsonl")) == 9)
rep = e13.compute_adequacy()
ok("adequacy: pending failure detected, lock False", rep["dev_failures_pending"] == ["madrid_s1_G1_I0"] and not rep["lock"])

# 3. extension interrupted at the second seed, then resumed; reproduction failure on seed 1 kept but unusable
STATE["interrupt_at"] = STATE["calls"] + 5                      # inside the second seed's four configurations
try:
    e13.extend(NS(city="madrid", arm="G1", regime="I0"))
except KeyboardInterrupt:
    pass
st = e13.extension_status("madrid_G1_I0")
ok("extend: interrupted state recorded as incomplete/started, not complete", st["status"] in ("incomplete", "started") and "0" in st["seeds"])
STATE["repro_fail"] = {"madrid_s1_G1_I0"}
rc = e13.extend(NS(city="madrid", arm="G1", regime="I0"))
st = e13.extension_status("madrid_G1_I0")
ok("extend: resumed; seed 0 kept, seed 1 reproduction failed -> unusable, status incomplete, exit 1", rc == 1 and st["status"] == "incomplete" and st["seeds"]["0"]["usable"] and not st["seeds"]["1"]["usable"])
ok("latest_dev ignores the unusable extended run", e13.latest_dev("madrid_s1_G1_I0")["cap"] == e13.CAP0)
rep = e13.compute_adequacy()
ok("adequacy: incomplete extension blocks the lock", "madrid_G1_I0" in rep["extensions_incomplete"] and not rep["lock"])
STATE["repro_fail"] = set()
rc = e13.extend(NS(city="madrid", arm="G1", regime="I0")); st = e13.extension_status("madrid_G1_I0")
ok("extend: retry reproduces, group complete", rc == 0 and st["status"] == "complete" and st["reproduction_failures"]["1"] == 1 and st["attempts"]["1"] == 3)
ok("extend: a third call is refused (once per group)", "already extended" in expect_error(e13.extend, NS(city="madrid", arm="G1", regime="I0")))
ok("dev: refuses a cell of an extended group", "extended" in expect_error(e13.dev, NS(city="madrid", seed=0, arm="G1", regime="I0")))

# 4. finals; a final made from a superseded development is stale
e13.campaign(NS(phase="final"))
rep = e13.compute_adequacy()
ok("final: all 8 up to date, lock True", rep["lock"] and not rep["final_stale"] and not rep["missing_final"])
# simulate a newer development for one cell -> final becomes stale
e13._dev_run("madrid", 0, "G0", "I1", e13.CAP0, attempt=2)
rep = e13.compute_adequacy(); ok("lock: stale final detected after a new development", "madrid_s0_G0_I1" in rep["final_stale"] and not rep["lock"])
e13.campaign(NS(phase="final")); rep = e13.compute_adequacy(); ok("campaign final: only the stale cell re-run; lock True again", rep["lock"])

# 5. test: refused without committed lock; refused with foreign npz; analysis provisional
e13.adequacy(NS()); LOCK = RUNS / "e13_adequacy.json"
ok("test: refused when the lock file is not committed", "committed" in expect_error(e13.test, NS()))
git("add", "-f", str(LOCK.relative_to(ROOT))); git("commit", "-q", "-m", "adequacy lock")
ok("gate still passes after the lock commit (HEAD beyond the tag)", e13.gate("test") == TAG)
lock_txt = LOCK.read_text(); LOCK.write_text(lock_txt + "\n")
ok("test: refused when the committed lock is modified in the tree", "clean" in expect_error(e13.test, NS()) or "committed" in expect_error(e13.test, NS()))
LOCK.write_text(lock_txt)
fn = e13.latest_final("madrid_s0_G0_I0"); np.savez_compressed(Path(fn["dir"]) / "test_cells.npz", p=np.zeros(1), y=np.zeros(1), lock_sha16="0000")
ok("test: refuses a foreign test file, does not overwrite", "another lock" in expect_error(e13.test, NS()))
(Path(fn["dir"]) / "test_cells.npz").unlink()
e13.test(NS()); ok("test: 8 files written with the current lock", all((Path(e13.latest_final(e13.cell_id(*c))["dir"]) / "test_cells.npz").exists() for c in e13.all_cells()))
e13.analysis(NS()); an = json.loads((RUNS / "e13_analysis.json").read_text())
ok("analysis: statement provisional before Holm", an["statement"].startswith("PROVISIONAL") and an["confirmatory"] is False)
ok("analysis: metric declared per horizon", "per-horizon" in an["metric"])
# 6. per-horizon aggregation: numerators [1, 9], denominators [1, 3] -> per-horizon mean (1 + 3)/2 = 2; pooled 10/4 = 2.5
ok("metric: per-horizon mean 2.0, not pooled 2.5", abs(e13.per_horizon_mean([1.0, 9.0], [1.0, 3.0]) - 2.0) < 1e-12)
ok("metric: analysis uses per_horizon_mean", "per_horizon_mean(" in E13_PATH.read_text().split("def wce_with")[1].split("\n\n")[0])

print("\n%d checks, %d failed" % (len(passed), sum(1 for _, c in passed if not c)))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if all(c for _, c in passed) else 1)
