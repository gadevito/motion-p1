"""
MOTION — Orchestratore della SUITE COMPLETA dei modelli (contesto x seme)
========================================================================
Esegue i modelli SOTA che ancora mancano su alcuni contesti — AGCRN, DCRNN
(gomo_rnn_baselines) e STAEformer, GCN-stile-Traffic4cast (gomo_sota_baselines) —
su ogni contesto e seme, in modo ripristinabile. Poi aggrega una classifica
UNICA per contesto combinandoli con Graph WaveNet (dai file classify_*) e
LightGBM equo (dai file lgb_*) gia' calcolati dalla replica.

Cosi' ogni modello gira su OGNI contesto (ricostruiti + misurati), come richiesto
dal nuovo design sperimentale.

Uso (dalla radice OR3/):
  poetry run python run_model_suite.py \
      --ctx d8_2024  data_collection/go-mo/gomo/targets_2024_urb_d8.npz \
                     data_collection/go-mo/gomo/routes-graph.pkl \
                     data_collection/go-mo/gomo/traffic_sensors.csv \
      --ctx t4cmad   data_collection/traffic4cast/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz \
                     data_collection/traffic4cast/MADRID_2022/gomo_fmt/t4cmad_routes-graph.pkl \
                     data_collection/traffic4cast/MADRID_2022/gomo_fmt/t4cmad_sensors.csv \
      --ctx t4clon   data_collection/traffic4cast/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz \
                     data_collection/traffic4cast/LONDON_2022/gomo_fmt/t4cmad_routes-graph.pkl \
                     data_collection/traffic4cast/LONDON_2022/gomo_fmt/t4cmad_sensors.csv \
      --seeds 0 1 2
Solo aggregazione:  --aggregate-only
"""
import argparse, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser(description="Suite completa dei modelli, multi-contesto")
ap.add_argument("--ctx", action="append", nargs=4, metavar=("NAME", "TARGETS", "GRAPH", "SENSORS"),
                default=[], help="un contesto: nome targets.npz graph.pkl sensors.csv (ripetibile)")
ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
ap.add_argument("--outdir", type=Path, default=Path("replication"))
ap.add_argument("--baselines-dir", type=Path, default=Path("baselines"))
ap.add_argument("--experiments", nargs="+", default=["rnn", "sota"],
                help="quali gruppi eseguire: rnn (AGCRN+DCRNN), sota (STAEformer+GCN-t4c)")
ap.add_argument("--aggregate-only", action="store_true")
args = ap.parse_args()
args.outdir.mkdir(exist_ok=True)

def run(cmd, out_csv):
    if out_csv.exists():
        print(f"[skip] {out_csv.name}"); return
    print("[run ]", " ".join(map(str, cmd)))
    subprocess.run(list(map(str, cmd)), check=True)

if not args.aggregate_only:
    for name, tgt, graph, sens in args.ctx:
        common = ["--targets", tgt, "--graph", graph, "--sensors", sens]
        for seed in args.seeds:
            if "rnn" in args.experiments:
                out = args.outdir / f"rnn_{name}_s{seed}.csv"
                run([sys.executable, args.baselines_dir / "gomo_rnn_baselines.py",
                     "--model", "both", "--seed", seed, "--out", out] + common, out)
            if "sota" in args.experiments:
                out = args.outdir / f"sota_{name}_s{seed}.csv"
                run([sys.executable, args.baselines_dir / "gomo_sota_baselines.py",
                     "--model", "both", "--seed", seed, "--out", out] + common, out)

# ------------------------------------------------------------- aggregate ----
DISPLAY = {"hist_prior": "prior storico", "lgb_fair": "LightGBM equo", "t4c_gnn": "GCN stile-T4c",
           "dcrnn": "DCRNN", "agcrn": "AGCRN", "gwn_none": "Graph WaveNet (no grafo)",
           "gwn_adaptive": "Graph WaveNet (nostro)", "staeformer": "STAEformer"}
frames = []
for f in sorted(args.outdir.glob("*.csv")):
    stem = f.stem.split("_")
    if stem[0] not in ("classify", "lgb", "rnn", "sota"): continue
    exp, ctx, seed = stem[0], "_".join(stem[1:-1]), stem[-1]
    df = pd.read_csv(f)
    if "model" not in df or "wCE" not in df: continue
    df = df[["model", "wCE"] + [c for c in ("horizon", "red_recall") if c in df]].copy()
    df["context"], df["seed"] = ctx, seed
    frames.append(df)
if not frames:
    print("nessun risultato da aggregare."); sys.exit(0)
allr = pd.concat(frames, ignore_index=True)

# media sugli orizzonti dentro ogni (contesto,modello,seme), poi media/dev sui semi
per_seed = allr.groupby(["context", "model", "seed"]).agg(
    wCE=("wCE", "mean"), red=("red_recall", "mean") if "red_recall" in allr else ("wCE", "mean")).reset_index()
if "horizon" in allr.columns:
    per_seed = per_seed.merge(allr.groupby(["context","model","seed"]).horizon.nunique()
                              .rename("n_h").reset_index(), on=["context","model","seed"], how="left")
else:
    per_seed["n_h"] = 1
lead = per_seed.groupby(["context", "model"]).agg(
    wCE_mean=("wCE", "mean"), wCE_std=("wCE", "std"), red=("red", "mean"), seeds=("seed", "nunique"), orizzonti=("n_h", "min")).reset_index()
H_FULL = int(lead.orizzonti.max())
lead["confrontabile"] = lead.orizzonti == H_FULL
lead["wCE_std"] = lead["wCE_std"].fillna(0.0)
lead["modello"] = lead["model"].map(lambda m: DISPLAY.get(m, m))

# --- hist_prior: sostituzione con il priore smussato (Laplace alpha=1), fonte dichiarata
for _i, _r in lead[lead.model == "hist_prior"].iterrows():
    _p = args.outdir / f"prior_{_r['context']}_a1.csv"
    if _p.exists():
        _d = pd.read_csv(_p)
        lead.loc[_i, "wCE_mean"] = _d.wCE.mean()
        lead.loc[_i, "wCE_std"] = 0.0
        if "red_recall" in _d: lead.loc[_i, "red"] = _d.red_recall.mean()
        lead.loc[_i, "modello"] = "prior storico (Laplace a=1)"
        lead.loc[_i, "fonte"] = _p.name
    else:
        lead.loc[_i, "modello"] = "prior storico (NON smussato - manca prior_a1)"
        lead.loc[_i, "fonte"] = "classify_* (alpha=0)"
lead["fonte"] = lead["fonte"].fillna("") if "fonte" in lead else ""

pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n================ CLASSIFICA DEI MODELLI PER CONTESTO ================")
for ctx in sorted(lead["context"].unique()):
    sub = lead[(lead.context == ctx) & lead.confrontabile].sort_values("wCE_mean")
    par = lead[(lead.context == ctx) & ~lead.confrontabile]
    print(f"\n--- {ctx} ---")
    for _, r in sub.iterrows():
        print(f"  {r['modello']:<28s} wCE={r.wCE_mean:.4f} ± {r.wCE_std:.4f}   red_recall={r.red:.3f}   (n_semi={int(r.seeds)})")
    for _, r in par.iterrows():
        print(f"  [{r['modello']}] wCE={r.wCE_mean:.4f} su {int(r.orizzonti)}/{H_FULL} orizzonti "
              f"-> ESCLUSO dal ranking (non confrontabile)")
lead.sort_values(["context", "confrontabile", "wCE_mean"], ascending=[True, False, True]).to_csv(args.outdir / "MODEL_leaderboard.csv", index=False)
print(f"\nsalvato -> {args.outdir/'MODEL_leaderboard.csv'}")
print("\nNota: 'Graph WaveNet (nostro)' = gwn_adaptive dai file classify_*; "
      "LightGBM dai file lgb_*. Persistenza/media storica sono nei baseline separati.")
