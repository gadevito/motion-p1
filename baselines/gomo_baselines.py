"""
GO-MO M30 — Baseline harness
============================
Three baselines on the cleaned congestion factor r (primary = regression):
  * Persistence      : r_hat(t+h) = r(t)
  * Historical Avg   : mean r per (sensor, time-of-week slot), from TRAIN only
  * LightGBM         : tabular GBDT, one model per horizon
Reports regression metrics (MAE, RMSE on r) and Traffic4cast 3-class metrics
(macro-F1, accuracy via the 0.4/0.8 thresholds) for comparability.

Run:  poetry run python gomo_baselines.py       (needs: lightgbm)
      poetry add lightgbm    # if missing
"""
from pathlib import Path
import argparse
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)

ap = argparse.ArgumentParser(description="GO-MO M30 baseline harness")
ap.add_argument("--targets", type=Path, default=Path("gomo/targets_2024_m30.npz"),
                help="path to the targets_YYYY_m30.npz file")
ap.add_argument("--out", type=Path, default=None,
                help="output CSV path (default: <targets dir>/baseline_results.csv)")
ap.add_argument("--train-cap", type=int, default=1_500_000,
                help="max LightGBM training rows (subsampled for speed)")
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()
OUT = args.out or args.targets.parent / "baseline_results.csv"

T_IN = 4
HORIZONS = [1, 2, 4, 8]                 # 15 / 30 / 60 / 120 min
T4C_GREEN, T4C_RED = 0.8, 0.4
TRAIN_ROW_CAP = args.train_cap          # subsample cap for LightGBM training rows
SEED = args.seed
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- load ------
z = np.load(args.targets, allow_pickle=True)
ts   = pd.to_datetime(z["timestamps"])
r    = z["r_emp"].astype("float32")     # (T,S) cleaned; NaN = masked
flow = z["flow"].astype("float32")
occ  = z["occupancy"].astype("float32")
spd  = z["speed"].astype("float32")
ff   = z["ff_emp"].astype("float32")    # (S,)
T, S = r.shape

dow   = ts.dayofweek.to_numpy()
quart = ts.hour.to_numpy() * 4 + ts.minute.to_numpy() // 15      # 0..95
slot  = dow * 96 + quart                                         # 0..671
hour  = ts.hour.to_numpy()
wknd  = (dow >= 5).astype("float32")
tod_sin = np.sin(2 * np.pi * quart / 96).astype("float32")
tod_cos = np.cos(2 * np.pi * quart / 96).astype("float32")

starts = np.arange(T_IN - 1, T - max(HORIZONS))
n = len(starts)
tr, va, te = starts[:int(n*.7)], starts[int(n*.7):int(n*.8)], starts[int(n*.8):]
print(f"present idx: train={len(tr)} val={len(va)} test={len(te)}  sensors={S}")

# ------------------------------------------------------------- helpers ------
def to_class(rv):
    c = np.full(rv.shape, -1, np.int8); v = np.isfinite(rv)
    c[v & (rv >= T4C_GREEN)] = 1
    c[v & (rv < T4C_GREEN) & (rv >= T4C_RED)] = 2
    c[v & (rv < T4C_RED)] = 3
    return c

def macro_f1(yt, yp):
    f1 = []
    for k in (1, 2, 3):
        tp = np.sum((yp == k) & (yt == k))
        fp = np.sum((yp == k) & (yt != k))
        fn = np.sum((yp != k) & (yt == k))
        p = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f1.append(2 * p * rc / (p + rc) if p + rc else 0.0)
    return float(np.mean(f1))

def score(yt, yp):
    m = np.isfinite(yt) & np.isfinite(yp)
    yt, yp = yt[m], np.clip(yp[m], 0, 1.5)
    mae = float(np.mean(np.abs(yt - yp)))
    rmse = float(np.sqrt(np.mean((yt - yp) ** 2)))
    ct, cp = to_class(yt), to_class(yp)
    vv = (ct > 0) & (cp > 0)
    return mae, rmse, macro_f1(ct[vv], cp[vv]), float(np.mean(ct[vv] == cp[vv]))

# ---------------------------------------- Historical Average (train only) ---
ha_sum = np.zeros((S, 672)); ha_cnt = np.zeros((S, 672))
tt = np.arange(0, tr[-1] + 1)                      # train time region
rv = r[tt]; v = np.isfinite(rv)
si = np.broadcast_to(np.arange(S), rv.shape)
sl = np.broadcast_to(slot[tt][:, None], rv.shape)
np.add.at(ha_sum, (si[v], sl[v]), rv[v])
np.add.at(ha_cnt, (si[v], sl[v]), 1)
ha_table = np.divide(ha_sum, ha_cnt, out=np.full_like(ha_sum, np.nan), where=ha_cnt > 0)
sensor_mean = np.nanmean(ha_table, axis=1)
ha_table = np.where(np.isfinite(ha_table), ha_table, sensor_mean[:, None]).astype("float32")

# --------------------------------------------- baseline predict functions ---
def predict_persistence(idx, h):  # (N,S)
    return r[idx]                                   # r(t) for target t+h
def predict_ha(idx, h):
    return ha_table[:, slot[idx + h]].T             # (N,S)

# ----------------------------------------------- LightGBM feature builder ---
def build(idx, h):
    N = len(idx)
    win = np.stack([r[idx-3], r[idx-2], r[idx-1], r[idx]], 0)
    bc = lambda a: np.broadcast_to(a[:, None], (N, S))
    cols = {
        "r_t": r[idx], "r_t1": r[idx-1], "r_t2": r[idx-2], "r_t3": r[idx-3],
        "flow": flow[idx], "occ": occ[idx], "spd": spd[idx],
        "r_mean": np.nanmean(win, 0), "r_std": np.nanstd(win, 0),
        "ha": ha_table[:, slot[idx + h]].T,
        "hour": bc(hour[idx + h]).astype("float32"),
        "dow": bc(dow[idx + h]).astype("float32"),
        "wknd": bc(wknd[idx + h]),
        "tod_sin": bc(tod_sin[idx + h]), "tod_cos": bc(tod_cos[idx + h]),
        "ff": np.broadcast_to(ff[None, :], (N, S)),
        "sid": np.broadcast_to(np.arange(S, dtype="float32")[None, :], (N, S)),
    }
    X = pd.DataFrame({k: v.reshape(-1) for k, v in cols.items()})
    for c in ("hour", "dow", "sid"):
        X[c] = X[c].astype("int32")
    return X, r[idx + h].reshape(-1)

def run_lightgbm(h):
    import lightgbm as lgb
    Xtr, ytr = build(tr, h)
    Xte, yte = build(te, h)
    keep = np.isfinite(ytr)
    Xtr, ytr = Xtr[keep], ytr[keep]
    if len(ytr) > TRAIN_ROW_CAP:                    # subsample for speed
        sub = rng.choice(len(ytr), TRAIN_ROW_CAP, replace=False)
        Xtr, ytr = Xtr.iloc[sub], ytr[sub]
    ds = lgb.Dataset(Xtr, ytr, categorical_feature=["hour", "dow", "sid"])
    params = dict(objective="regression_l1", num_leaves=63, learning_rate=0.05,
                  feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
                  verbose=-1, seed=SEED)
    model = lgb.train(params, ds, num_boost_round=300)
    return yte, model.predict(Xte)

# ------------------------------------------------------------- evaluate -----
rows = []
for h in HORIZONS:
    yt = r[te + h]                                   # (N,S) truth for this horizon
    rows.append(("persistence", h, *score(yt.reshape(-1), predict_persistence(te, h).reshape(-1))))
    rows.append(("hist_avg",    h, *score(yt.reshape(-1), predict_ha(te, h).reshape(-1))))
    ytl, ypl = run_lightgbm(h)
    rows.append(("lightgbm",    h, *score(ytl, ypl)))

res = pd.DataFrame(rows, columns=["model", "h_steps", "MAE_r", "RMSE_r", "macroF1", "acc"])
res["horizon"] = res["h_steps"].map({1: "15m", 2: "30m", 4: "60m", 8: "120m"})
res = res[["model", "horizon", "MAE_r", "RMSE_r", "macroF1", "acc"]]
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== Baseline results (test set) ===")
print(res.to_string(index=False))
res.to_csv(OUT, index=False)
print(f"\nsaved -> {OUT}")
