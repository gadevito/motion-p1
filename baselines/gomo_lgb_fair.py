"""
GO-MO — FAIR LightGBM baseline (matched to the GWN classifier)
==============================================================
The earlier LightGBM saw only 4 lags; the GWN sees a 12-step window. To isolate
model vs information, this LightGBM gets the SAME window and features as the GWN:
12 lags of r/flow/occupancy + rolling stats + historical-average prior + temporal +
sensor id. It is a weighted multiclass classifier scored with the IDENTICAL
Traffic4cast weighted cross-entropy (sum-of-weights norm, weights n/(count*3)) and
red recall, so results drop straight next to gomo_classify.py's GWN rows.

Place in baselines/. Run:
    poetry run python gomo_lgb_fair.py \
        --targets ../data_collection/go-mo/gomo/targets_2024_urb_d8.npz
Needs: lightgbm
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
from pathlib import Path
import argparse, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore", category=RuntimeWarning)

DATA = Path("../data_collection/go-mo/gomo")
ap = argparse.ArgumentParser(description="Fair (12-window) LightGBM classifier baseline")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_urb_d8.npz")
ap.add_argument("--out", type=Path, default=Path("lgb_fair_results.csv"))
ap.add_argument("--win", type=int, default=12)
ap.add_argument("--train-cap", type=int, default=999_999_999)   # dati completi (storico: 1_500_000)
ap.add_argument("--dump-probs", type=str, default="")
ap.add_argument("--dump-probs-val", type=str, default="",
                help="npz con le probabilita sulla partizione di validazione")
ap.add_argument("--city", type=str, default="")
ap.add_argument("--dump-metrics", type=str, default="", help="CSV con precision/recall/F1 per classe, confusione, calibrazione, curva PR")
ap.add_argument("--num-threads", type=int, default=0, help="0 = tutti i logici; su Apple Silicon usare i soli core performance")
ap.add_argument("--lr", type=float, default=0.05)
ap.add_argument("--feature-fraction", type=float, default=0.8)
ap.add_argument("--bagging-fraction", type=float, default=0.8)
ap.add_argument("--bagging-freq", type=int, default=1)
ap.add_argument("--lambda-l1", type=float, default=0.0)
ap.add_argument("--lambda-l2", type=float, default=0.0)
ap.add_argument("--min-data-in-leaf", type=int, default=20)
ap.add_argument("--num-leaves", type=int, default=5000, help="63 = storico; migliaia = regime T4c22 (Lumiste & Ilie 2022)")
ap.add_argument("--early-stop", type=int, default=50, help="patience early stopping (0 = storico: rounds fissi)")
ap.add_argument("--val-frac", type=float, default=0.15, help="coda temporale del train usata come validazione")
ap.add_argument("--rounds", type=int, default=5000)   # tetto: taglia l'early stopping
ap.add_argument("--graph", type=Path, default=None,
                help="se dato con --sensors, restringe ai sensori agganciabili entro 20 m: "
                     "stessa popolazione dei modelli neurali")
ap.add_argument("--sensors", type=Path, default=None)
ap.add_argument("--weight-alpha", type=float, default=1.0,
                help="esponente della pesatura in addestramento: w prop. 1/f^alpha")
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()
rng = np.random.default_rng(args.seed)
T_IN = args.win; HORIZONS = [1, 2, 4, 8]; HL = {1: "15m", 2: "30m", 4: "60m", 8: "120m"}

z = np.load(args.targets, allow_pickle=True)
ts = pd.to_datetime(z["timestamps"])
r, flow, occ = z["r_emp"].astype("float32"), z["flow"].astype("float32"), z["occupancy"].astype("float32")
C = z["congestion_emp"].astype("int64"); ff = z["ff_emp"].astype("float32"); T, K = r.shape
sids = z["sensor_ids"].astype(str)
if args.graph and args.sensors:
    import pickle, networkx as nx
    from scipy.spatial import cKDTree
    with open(args.graph, "rb") as _f: _rg = pickle.load(_f)
    _sens = pd.read_csv(args.sensors, dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
    _tree = cKDTree(_sens[["utm_x", "utm_y"]].to_numpy()); _nodes = list(_rg.nodes)
    _nxy = np.array([[_rg.nodes[n]["utm_x"], _rg.nodes[n]["utm_y"]] for n in _nodes])
    _d, _i = _tree.query(_nxy, k=1)
    _rg = nx.relabel_nodes(_rg, {_nodes[k]: _sens["id"].to_numpy()[_i[k]]
                                 for k in range(len(_nodes)) if _d[k] <= 20}, copy=True)
    _kept = [s for s in sids if s in _rg.nodes]
    _pos = {s: i for i, s in enumerate(sids)}
    _kidx = np.array([_pos[s] for s in _kept])
    r, flow, occ, C, ff = r[:, _kidx], flow[:, _kidx], occ[:, _kidx], C[:, _kidx], (
        ff[:, _kidx] if ff.ndim == 2 else ff[_kidx])
    print(f"aligned graph: {len(_kept)} of {len(sids)} sensors")
    sids = np.array(_kept); K = len(_kept)

dow = ts.dayofweek.to_numpy(); quart = ts.hour.to_numpy()*4 + ts.minute.to_numpy()//15
slot = dow*96 + quart; hour = ts.hour.to_numpy(); wknd = (dow >= 5).astype("float32")
tod_sin = np.sin(2*np.pi*quart/96).astype("float32"); tod_cos = np.cos(2*np.pi*quart/96).astype("float32")

starts = np.arange(T_IN-1, T - max(HORIZONS)); n = len(starts)
tr, va, te = starts[:int(n*.7)], starts[int(n*.7):int(n*.8)], starts[int(n*.8):]
reg = slice(0, tr[-1]+1); ctr = C[reg]
freq = np.array([(ctr == k).sum() for k in (1, 2, 3)], dtype="float64")
if args.weight_alpha == 1.0:
    Wnp = (freq.sum() / (np.maximum(freq, 1)*3)).astype("float32")
else:
    Wnp = ((freq.sum() / (np.maximum(freq, 1)*3)) ** args.weight_alpha).astype("float32")
    Wnp = (Wnp * (3.0 / Wnp.sum())).astype("float32")   # somma 3 come i pesi T4c
print(f"sensors={K} | class freq g/y/r = {(freq/freq.sum()).round(3)} | T4c weights = {Wnp.round(2)}")

hs = np.zeros((K, 672)); hc = np.zeros((K, 672)); tt = np.arange(0, tr[-1]+1)
rv = r[tt]; vv = np.isfinite(rv); si = np.broadcast_to(np.arange(K), rv.shape); sl = np.broadcast_to(slot[tt][:, None], rv.shape)
np.add.at(hs, (si[vv], sl[vv]), rv[vv]); np.add.at(hc, (si[vv], sl[vv]), 1)
ht = np.divide(hs, hc, out=np.full_like(hs, np.nan), where=hc > 0)
gm = float(np.nanmean(ht)); sm = np.nanmean(np.where(np.isfinite(ht), ht, np.nan), 1)
sm = np.where(np.isfinite(sm), sm, gm); HA = np.nan_to_num(np.where(np.isfinite(ht), ht, sm[:, None]), nan=gm).astype("float32")

def build(idx, h):
    N = len(idx); bc = lambda a: np.broadcast_to(a[idx+h][:, None], (N, K))
    cols = {}
    for k in range(T_IN):
        cols[f"r_{k}"] = r[idx-k]; cols[f"fl_{k}"] = flow[idx-k]; cols[f"oc_{k}"] = occ[idx-k]
    win = np.stack([r[idx-k] for k in range(T_IN)], 0)
    cols["r_mean"] = np.nanmean(win, 0); cols["r_std"] = np.nanstd(win, 0)
    cols["r_min"] = np.nanmin(win, 0); cols["r_max"] = np.nanmax(win, 0)
    cols["ha"] = HA[:, slot[idx+h]].T
    cols["hour"] = bc(hour); cols["dow"] = bc(dow); cols["wknd"] = bc(wknd)
    cols["tod_sin"] = bc(tod_sin); cols["tod_cos"] = bc(tod_cos)
    cols["ff"] = np.broadcast_to(ff[None, :], (N, K))
    cols["sid"] = np.broadcast_to(np.arange(K, dtype="float32")[None, :], (N, K))
    X = pd.DataFrame({k: v.reshape(-1) for k, v in cols.items()})
    for c in ("hour", "dow", "sid"): X[c] = X[c].astype("int32")
    return X, (C[idx+h]-1).reshape(-1)

def run(h):
    import lightgbm as lgb
    n_idx = max(1, args.train_cap // K)
    if args.early_stop > 0:
        cut = int(len(tr) * (1 - args.val_frac))          # split TEMPORALE: coda del train
        tr_pool, va_idx = tr[:cut], tr[cut:]
        tr_sub = rng.choice(tr_pool, min(len(tr_pool), n_idx), replace=False)
    else:
        tr_sub = rng.choice(tr, min(len(tr), n_idx), replace=False)
    Xtr, ytr = build(tr_sub, h); keep = ytr >= 0; Xtr, ytr = Xtr[keep], ytr[keep]
    ds = lgb.Dataset(Xtr, ytr, weight=Wnp[ytr], categorical_feature=["hour", "dow", "sid"])
    params = dict(objective="multiclass", num_class=3, learning_rate=args.lr,
                  num_leaves=args.num_leaves, feature_fraction=args.feature_fraction,
                  bagging_fraction=args.bagging_fraction, bagging_freq=args.bagging_freq,
                  lambda_l1=args.lambda_l1, lambda_l2=args.lambda_l2,
                  min_data_in_leaf=args.min_data_in_leaf, verbose=-1, seed=args.seed,
                  num_threads=args.num_threads)
    if args.early_stop > 0:
        Xva, yva = build(va_idx, h); kv = yva >= 0
        dv = lgb.Dataset(Xva[kv], yva[kv], weight=Wnp[yva[kv]], reference=ds)   # stessi pesi: multi_logloss == wCE T4c
        model = lgb.train(params, ds, num_boost_round=args.rounds, valid_sets=[dv],
                          callbacks=[lgb.early_stopping(args.early_stop, verbose=False)])
        print(f"[lgb h={h}] best_iteration={model.best_iteration}")
    else:
        model = lgb.train(params, ds, num_boost_round=args.rounds)
    Xte, yte = build(te, h)
    if args.dump_probs_val:
        _Xv, _yv = build(va, h)      # partizione di validazione cronologica (riga 82), non
                                     # va_idx che e la coda del training usata per l'arresto
        globals().setdefault("VALRAW", {})[h] = (model.predict(_Xv), _yv)
    return model.predict(Xte), yte

DUMP = []
PROBS = []
VALRAW = {}
def scores(P, Y, tag=""):
    if args.dump_probs and tag:
        _v = Y >= 0
        PROBS.append({"tag": tag, "p": P[_v].astype("float16"),
                      "y": Y[_v].astype("int8"), "idx": np.where(_v)[0].astype("int32")})
    v = Y >= 0; P, Y = P[v], Y[v]
    pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1); wce = float(np.sum(Wnp[Y]*-np.log(pt))/np.sum(Wnp[Y]))
    pred = P.argmax(1); f1 = []
    for k in range(3):
        tp = np.sum((pred == k) & (Y == k)); fp = np.sum((pred == k) & (Y != k)); fn = np.sum((pred != k) & (Y == k))
        pr = tp/(tp+fp) if tp+fp else 0; rc = tp/(tp+fn) if tp+fn else 0
        f1.append(2*pr*rc/(pr+rc) if pr+rc else 0)
        if k == 2: red_prec = pr
        if args.dump_metrics and tag:
            DUMP.append((tag, "class", k, float(pr), float(rc), float(f1[-1]), int((Y == k).sum())))
    if args.dump_metrics and tag:
        for i in range(3):
            for j in range(3):
                DUMP.append((tag, "conf", i*3+j, float(((Y == i) & (pred == j)).sum()), i, j, 0))
        pr_red = P[:, 2]; bins = np.clip((pr_red*10).astype(int), 0, 9); ece = 0.0
        for b in range(10):
            m = bins == b
            if m.sum():
                pm, fo = float(pr_red[m].mean()), float((Y[m] == 2).mean())
                ece += m.sum()/len(Y)*abs(pm-fo)
                DUMP.append((tag, "calib", b, pm, fo, 0.0, int(m.sum())))
        DUMP.append((tag, "ece", 0, float(ece), 0.0, 0.0, len(Y)))
        pos = (Y == 2)
        for th in np.arange(0.05, 1.0, 0.05):
            sel = pr_red >= th
            tp2 = int((sel & pos).sum()); fp2 = int((sel & ~pos).sum()); fn2 = int((~sel & pos).sum())
            DUMP.append((tag, "pr_curve", int(round(th*100)),
                         tp2/(tp2+fp2) if tp2+fp2 else 0.0, tp2/(tp2+fn2) if tp2+fn2 else 0.0,
                         (tp2+fp2)/len(Y), tp2+fp2))
    rr = float(np.sum((pred == 2) & (Y == 2))/max(np.sum(Y == 2), 1))
    return wce, float(np.mean(f1)), rr, float(red_prec)

rows = []
for h in HORIZONS:
    P, Y = run(h); rows.append(("lgb_fair", HL[h], *scores(P, Y, tag="lgb_fair|" + str(HL[h]))))
res = pd.DataFrame(rows, columns=["model", "horizon", "wCE", "macroF1", "red_recall", "red_prec"])
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== Fair LightGBM (12-window) — weighted-CE classification (test) ===")
print(res.to_string(index=False))
print("\ncompare to GWN (gomo_classify): gwn_none wCE ~0.63-0.70, red_recall ~0.66-0.72")
res.insert(1, "seed", args.seed); res.insert(2, "city", args.city)
res.to_csv(args.out, index=False); print(f"saved -> {args.out}")
if args.dump_probs_val and VALRAW:
    _d = {"context": Path(args.targets).stem, "city": args.city, "seed": args.seed,
          "n_nodi": K, "split": "validation"}
    for _i, _h in enumerate(sorted(VALRAW)):
        _P, _Y = VALRAW[_h]; _v = _Y >= 0
        _d[f"tag{_i}"] = f"lgb_fair|{HL[_h]}"; _d[f"p{_i}"] = _P[_v].astype("float16")
        _d[f"y{_i}"] = _Y[_v].astype("int8"); _d[f"idx{_i}"] = np.where(_v)[0].astype("int32")
    np.savez_compressed(args.dump_probs_val, **_d)
    print(f"[probs-val] -> {args.dump_probs_val} ({len(VALRAW)} blocchi)")
if args.dump_probs and PROBS:
    _d = {"context": args.targets.stem, "city": args.city, "seed": args.seed, "n_nodi": K}
    for _i, _b in enumerate(PROBS):
        _d[f"tag{_i}"] = _b["tag"]; _d[f"p{_i}"] = _b["p"]; _d[f"y{_i}"] = _b["y"]; _d[f"idx{_i}"] = _b["idx"]
    np.savez_compressed(args.dump_probs, **_d)
    print(f"[probs] -> {args.dump_probs} ({len(PROBS)} blocchi)")
if args.dump_metrics and DUMP:
    pd.DataFrame(DUMP, columns=["tag","kind","idx","a","b","c","n"]).to_csv(args.dump_metrics, index=False)
    print(f"[metrics] -> {args.dump_metrics}")
