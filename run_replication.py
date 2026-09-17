"""
MOTION — Replication orchestrator (multi-context, multi-seed, per-project Poetry envs)
======================================================================================

This script runs the three key experiments for each context (target file) and seed,
then aggregates mean ± std and checks whether each main finding HOLDS across contexts:

  F1  neural family > fair gradient boosting   (wCE: gwn_none vs lgb_fair)
  F2  graph ~ null on the dense task           (gwn_adaptive ~ gwn_none, classify)
  F3  graph decisive in severe sparse-to-dense test (adaptive << none, sparse severe)

Experiments per (context, seed):
  classify : models/gomo_classify.py  --backend torch   (gwn none+adaptive)
  lgb      : baselines/gomo_lgb_fair.py
  sparse   : models/gomo_sparse.py --inductive --no-coords --mask structured

Important:
- Each script is executed with the Poetry environment of its own project folder.
- The working directory is changed to the folder containing the script.
- All filesystem paths passed to subprocesses are converted to absolute paths.

Example usage from the project root:
  poetry run python run_replication.py \
      --context d8_2024=data_collection/go-mo/gomo/targets_2024_urb_d8.npz \
      --context d15_2024=data_collection/go-mo/gomo/targets_2024_urb_d15.npz \
      --context d8_2023=data_collection/go-mo/gomo/targets_2023_urb_d8.npz \
      --seeds 0 1 2

Resume behavior:
- Existing output CSV files in --outdir are not re-run.
- Use --aggregate-only to only recompute aggregation from existing CSVs.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def abspath(p: Path | str) -> Path:
    """Return an absolute normalized path."""
    return Path(p).expanduser().resolve()


ap = argparse.ArgumentParser(description="Multi-context, multi-seed replication runner")
ap.add_argument(
    "--context",
    action="append",
    required=False,
    default=[],
    help="name=/absolute/or/relative/path/to_targets.npz (repeatable)",
)
ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
ap.add_argument("--outdir", type=Path, default=Path("replication"))
ap.add_argument("--models-dir", type=Path, default=Path("models"))
ap.add_argument("--baselines-dir", type=Path, default=Path("baselines"))
ap.add_argument("--graph", type=Path, default=Path("data_collection/go-mo/gomo/routes-graph.pkl"))
ap.add_argument("--sensors", type=Path, default=Path("data_collection/go-mo/gomo/traffic_sensors.csv"))
ap.add_argument("--experiments", nargs="+", default=["classify", "lgb", "sparse"])
ap.add_argument("--aggregate-only", action="store_true")
ap.add_argument("--poetry-bin", default="poetry", help="Poetry executable name or path")
args = ap.parse_args()

# Normalize all directory/file arguments to absolute paths because subprocesses
# will run with different working directories.
args.outdir = abspath(args.outdir)
args.models_dir = abspath(args.models_dir)
args.baselines_dir = abspath(args.baselines_dir)
args.graph = abspath(args.graph)
args.sensors = abspath(args.sensors)
args.outdir.mkdir(parents=True, exist_ok=True)

# Parse and normalize contexts.
contexts: dict[str, Path] = {}
for c in args.context:
    if "=" not in c:
        raise ValueError(f"Invalid --context value: {c!r}. Expected name=path")
    name, path = c.split("=", 1)
    contexts[name] = abspath(path)


def run_poetry_script(project_dir: Path, script_name: str, script_args: list, out_csv: Path) -> None:
    """
    Run a Python script with 'poetry run python' inside its own project directory.

    Parameters
    ----------
    project_dir : Path
        Directory containing the Poetry project and the script.
    script_name : str
        Script filename relative to project_dir.
    script_args : list
        Command-line arguments to pass to the script.
    out_csv : Path
        Expected output file; if it already exists, execution is skipped.
    """
    if out_csv.exists():
        print(f"[skip] {out_csv.name} already exists")
        return

    script_path = project_dir / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    cmd = [args.poetry_bin, "run", "python", script_name, *map(str, script_args)]
    print(f"[run ] cwd={project_dir} :: {' '.join(map(str, cmd))}")
    subprocess.run(cmd, cwd=project_dir, check=True)


if not args.aggregate_only:
    for ctx, tpath in contexts.items():
        if not tpath.exists():
            print(f"[warn] Missing targets for {ctx}: {tpath} -- skipping this context")
            continue

        common = [
            "--targets", str(tpath),
            "--graph", str(args.graph),
            "--sensors", str(args.sensors),
        ]

        for seed in args.seeds:
            if "classify" in args.experiments:
                out = args.outdir / f"classify_{ctx}_s{seed}.csv"
                run_poetry_script(
                    project_dir=args.models_dir,
                    script_name="gomo_classify.py",
                    script_args=[
                        "--backend", "torch",
                        "--modes", "none,adaptive",
                        "--seed", str(seed),
                        "--out", str(out),
                        *common,
                    ],
                    out_csv=out,
                )

            if "lgb" in args.experiments:
                out = args.outdir / f"lgb_{ctx}_s{seed}.csv"
                run_poetry_script(
                    project_dir=args.baselines_dir,
                    script_name="gomo_lgb_fair.py",
                    script_args=[
                        "--seed", str(seed),
                        "--out", str(out),
                        "--targets", str(tpath),
                    ],
                    out_csv=out,
                )

            if "sparse" in args.experiments:
                out = args.outdir / f"sparse_{ctx}_s{seed}.csv"
                run_poetry_script(
                    project_dir=args.models_dir,
                    script_name="gomo_sparse.py",
                    script_args=[
                        "--inductive",
                        "--no-coords",
                        "--mask", "structured",
                        "--modes", "none,adaptive",
                        "--seed", str(seed),
                        "--out", str(out),
                        *common,
                    ],
                    out_csv=out,
                )

# ---------------------------------------------------------------- aggregate --

# Only collect per-run CSVs, not summary CSVs such as ALL_results.csv.
run_file_re = re.compile(r"^(?P<experiment>[^_]+)_(?P<context>.+)_s(?P<seed>\d+)$")

frames = []
for f in sorted(args.outdir.glob("*.csv")):
    m = run_file_re.match(f.stem)
    if not m:
        continue

    exp = m.group("experiment")
    ctx = m.group("context")
    seed = m.group("seed")

    df = pd.read_csv(f)
    df["experiment"] = exp
    df["context"] = ctx
    df["seed"] = seed
    frames.append(df)

if not frames:
    print("No results found to aggregate.")
    sys.exit(0)

allr = pd.concat(frames, ignore_index=True)


def agg(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Aggregate wCE by the given keys."""
    g = df.groupby(keys)["wCE"].agg(["mean", "std", "count"]).reset_index()
    g["std"] = g["std"].fillna(0.0)
    return g


pd.set_option("display.float_format", lambda x: f"{x:.4f}")

print("\n================ AGGREGATED RESULTS (mean ± std over seeds) ================")
for exp in sorted(allr["experiment"].unique()):
    sub = allr[allr["experiment"] == exp]
    keys = ["context", "model", "horizon"] if "horizon" in sub.columns else ["context", "model"]
    print(f"\n--- {exp} ---")
    print(agg(sub, keys).to_string(index=False))

# ----------------------------------------------------------- finding checks --

print("\n================ FINDING CHECKS BY CONTEXT ================")
rows = []

for ctx in sorted(allr["context"].unique()):
    a = allr[allr["context"] == ctx]

    def mwce(exp: str, model: str) -> tuple[float, float]:
        s = a[(a["experiment"] == exp) & (a["model"] == model)]["wCE"]
        if len(s) == 0:
            return (np.nan, 0.0)
        return (float(s.mean()), float(s.std() if len(s) > 1 else 0.0))

    gnone, gnone_sd = mwce("classify", "gwn_none")
    gadp, _ = mwce("classify", "gwn_adaptive")
    lgb, _ = mwce("lgb", "lgb_fair")
    snone, snone_sd = mwce("sparse", "gwn_none")
    sadp, sadp_sd = mwce("sparse", "gwn_adaptive")

    # F1 > 0 means the neural model beats fair GBDT.
    f1 = (lgb - gnone) / lgb if np.isfinite(lgb) and np.isfinite(gnone) and lgb != 0 else np.nan

    # F2 close to 0 means graph contribution is negligible on the dense task.
    f2 = (gnone - gadp) / gnone if np.isfinite(gnone) and np.isfinite(gadp) and gnone != 0 else np.nan

    # F3 >> 0 means graph is decisive on the severe sparse setting.
    f3 = (snone - sadp) / snone if np.isfinite(snone) and np.isfinite(sadp) and snone != 0 else np.nan

    rows.append(
        (
            ctx,
            f1,
            f2,
            f3,
            "OK" if (np.isfinite(f1) and f1 > 0.10) else "??",
            "OK" if (np.isfinite(f2) and abs(f2) < 0.03) else "??",
            "OK" if (np.isfinite(f3) and f3 > 0.10) else "??",
        )
    )

chk = pd.DataFrame(
    rows,
    columns=[
        "context",
        "F1 neural>GBDT",
        "F2 graph~0 (dense)",
        "F3 graph>>0 (severe)",
        "F1",
        "F2",
        "F3",
    ],
)

print(chk.to_string(index=False))
print("\nCriterion: a finding is considered replicated if it preserves sign and order of magnitude")
print("in ALL contexts (F1 > +10%, |F2| < 3%, F3 > +10%). '??' means it should be examined.")

allr.to_csv(args.outdir / "ALL_results.csv", index=False)
chk.to_csv(args.outdir / "FINDINGS_check.csv", index=False)

print(f"\nSaved -> {args.outdir / 'ALL_results.csv'}, {args.outdir / 'FINDINGS_check.csv'}")