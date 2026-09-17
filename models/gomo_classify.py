"""
GO-MO — classification harness on the Traffic4cast metric (weighted cross-entropy)
==================================================================================
3-class congestion classifiers (green/yellow/red) trained & scored with WEIGHTED
cross-entropy (rare red up-weighted), as Traffic4cast scores its core challenge.
Compares a historical class-prior baseline, LightGBM (multiclass, weighted), and
Graph WaveNet (none/adaptive). Metrics per horizon: weighted CE, macro-F1, RED recall.

macOS note: torch and lightgbm each ship their own libomp and abort if imported in
one process. So the two backends run in SEPARATE processes:
    --backend both (default): torch here, then a fresh subprocess for lightgbm
    --backend torch | lgb   : one backend only
Place in models/. Run:
    poetry run python gomo_classify.py --targets ../data_collection/go-mo/gomo/targets_2024_urb_d8.npz
"""
import os, sys, subprocess
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
from pathlib import Path
import argparse, pickle
import numpy as np
import pandas as pd
import networkx as nx
from scipy.spatial import cKDTree

DATA = Path("../data_collection/go-mo/gomo")
ap = argparse.ArgumentParser(description="GO-MO weighted-CE classification harness")
ap.add_argument("--dump-probs", type=str, default="", help="npz con probabilita float16 sulle celle valutate")
ap.add_argument("--dump-probs-val", type=str, default="",
                help="npz con le probabilita sulla partizione di validazione")
ap.add_argument("--city", type=str, default="", help="citta di appartenenza (chiave per analisi gerarchica)")
ap.add_argument("--dump-metrics", type=str, default="", help="CSV con precision/recall/F1 per classe, confusione e calibrazione")
ap.add_argument("--no-ha", action="store_true", help="rimuove il canale di media storica per nodo x slot (C_IN 9->8)")
ap.add_argument("--node-desc", type=str, default="", help="npy (K x d) di descrittori per nodo, al posto dell'embedding; richiede --emb 0")
ap.add_argument("--desc-proj", type=int, default=0, help="se >0, proiezione lineare APPRESA dal descrittore a questa dimensione, al posto della PCA")
ap.add_argument("--desc-hidden", type=int, default=0,
                help="se >0, la proiezione del descrittore diventa non lineare con questo strato nascosto")
ap.add_argument("--emb", type=int, default=8, help="dimensione embedding di identita (DEMB)")
ap.add_argument("--shift-check", action="store_true", help="divergenza train/test di r e delle frequenze di classe, poi esce")
ap.add_argument("--attach-check", action="store_true", help="wCE del priore su sensori agganciati vs esclusi, poi esce")
ap.add_argument("--prior-alpha", type=float, default=0.0, help="lisciatura di Laplace del priore (0 = storico)")
ap.add_argument("--prior-only", action="store_true", help="calcola solo hist_prior e termina")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_urb_d8.npz")
ap.add_argument("--graph",   type=Path, default=DATA / "routes-graph.pkl")
ap.add_argument("--sensors", type=Path, default=DATA / "traffic_sensors.csv")
ap.add_argument("--out",     type=Path, default=Path("classify_results.csv"))
ap.add_argument("--backend", choices=["both", "torch", "lgb"], default="both")
ap.add_argument("--modes", default="none,adaptive")
ap.add_argument("--win", type=int, default=12)
ap.add_argument("--hidden", type=int, default=32)
ap.add_argument("--blocks", type=int, default=4)
ap.add_argument("--epochs", type=int, default=35)
ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--lr", type=float, default=1e-3)
ap.add_argument("--patience", type=int, default=8)
ap.add_argument("--lgb-cap", type=int, default=1_200_000)
ap.add_argument("--weight-alpha", type=float, default=1.0,
                help="esponente della pesatura in addestramento: w prop. 1/f^alpha")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--device", default=None)
args = ap.parse_args()
np.random.seed(args.seed)
T_IN = args.win; HORIZONS = [1, 2, 4, 8]; H = len(HORIZONS); HL = {1: "15m", 2: "30m", 4: "60m", 8: "120m"}

# --------------------------------------------------- shared data (numpy) ---
z = np.load(args.targets, allow_pickle=True)
ts = pd.to_datetime(z["timestamps"])
r, flow, occ = z["r_emp"].astype("float32"), z["flow"].astype("float32"), z["occupancy"].astype("float32")
C = z["congestion_emp"].astype("int64"); sids = z["sensor_ids"].astype(str); Tn, S = r.shape

with open(args.graph, "rb") as f: rg = pickle.load(f)
sens = pd.read_csv(args.sensors, dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
tree = cKDTree(sens[["utm_x", "utm_y"]].to_numpy()); nodes = list(rg.nodes)
nxy = np.array([[rg.nodes[n]["utm_x"], rg.nodes[n]["utm_y"]] for n in nodes])
dist, idx = tree.query(nxy, k=1)
rg = nx.relabel_nodes(rg, {nodes[i]: sens["id"].to_numpy()[idx[i]] for i in range(len(nodes)) if dist[i] <= 20}, copy=True)
kept = [s for s in sids if s in rg.nodes]; posm = {s: i for i, s in enumerate(sids)}
kidx = np.array([posm[s] for s in kept]); K = len(kept)
_wattr = "distance" if any("distance" in _a for *_, _a in list(rg.edges(data=True))[:50]) else "weight"
Araw = nx.to_numpy_array(rg.subgraph(kept).copy(), nodelist=kept, weight=_wattr).astype("float32")
Araw[Araw > 0] = np.maximum(Araw[Araw > 0], 1.0)   # archi a distanza nulla: sensori coincidenti
print(f"[grafo] attributo di distanza: {_wattr} | archi {(Araw>0).sum()} | mediana {np.median(Araw[Araw>0]):.1f}")
C_full = C.copy(); sids_full = list(sids)
r, flow, occ, C = r[:, kidx], flow[:, kidx], occ[:, kidx], C[:, kidx]
print(f"aligned graph: {K} of {S} sensors")

starts = np.arange(T_IN - 1, Tn - max(HORIZONS)); n = len(starts)
tr, va, te = starts[:int(n*.7)], starts[int(n*.7):int(n*.8)], starts[int(n*.8):]
reg = slice(0, tr[-1] + 1); ctr = C[reg]
freq = np.array([(ctr == k).sum() for k in (1, 2, 3)], dtype="float64")
if args.weight_alpha == 1.0:
    Wnp = (freq.sum() / (np.maximum(freq, 1) * 3)).astype("float32")   # Traffic4cast: n/(count*3)
else:
    Wnp = ((freq.sum() / (np.maximum(freq, 1) * 3)) ** args.weight_alpha).astype("float32")
    Wnp = (Wnp * (3.0 / Wnp.sum())).astype("float32")   # somma 3 come i pesi T4c
print(f"class freq g/y/r = {(freq/freq.sum()).round(3)} | T4c weights = {Wnp.round(2)}")

slot = (ts.dayofweek.to_numpy() * 96 + ts.hour.to_numpy() * 4 + ts.minute.to_numpy() // 15)
if args.shift_check:
    from scipy.stats import wasserstein_distance
    from scipy.spatial.distance import jensenshannon
    _rng = np.random.default_rng(0)
    _trs = slice(0, tr[-1] + 1)
    _tes = slice(te[0], min(te[-1] + max(HORIZONS) + 1, r.shape[0]))
    A, B = r[_trs], r[_tes]
    def _sub(x, n=200000):
        v = x[np.isfinite(x)].ravel()
        return v if len(v) <= n else _rng.choice(v, n, replace=False)
    a, b = _sub(A), _sub(B)
    BINS = np.linspace(0, 1.5, 61)
    ha = np.histogram(a, BINS)[0].astype(float); ha /= ha.sum()
    hb = np.histogram(b, BINS)[0].astype(float); hb /= hb.sum()
    print(f"\n[shift] periodi: train {_trs.stop} righe | test {_tes.stop - _tes.start} righe | nodi {K}")
    print(f"[shift] r aggregato: media {a.mean():.4f} -> {b.mean():.4f} | "
          f"Wasserstein {wasserstein_distance(a, b):.4f} | JS(dist,base2) {jensenshannon(ha, hb, base=2):.4f}")
    ws = []
    for k in range(K):
        va_ = A[:, k][np.isfinite(A[:, k])]; vb_ = B[:, k][np.isfinite(B[:, k])]
        if len(va_) >= 100 and len(vb_) >= 100:
            ws.append(wasserstein_distance(va_, vb_))
    ws = np.array(ws)
    if len(ws):
        print(f"[shift] r per nodo (n={len(ws)}/{K}): W mediana {np.median(ws):.4f} | "
              f"IQR [{np.percentile(ws,25):.4f}; {np.percentile(ws,75):.4f}] | p90 {np.percentile(ws,90):.4f}")
    fa = np.array([(C[_trs] == k).sum() for k in (1,2,3)], float); fa /= fa.sum()
    fb = np.array([(C[_tes] == k).sum() for k in (1,2,3)], float); fb /= fb.sum()
    print(f"[shift] classi train g/y/r = {fa.round(4)}")
    print(f"[shift] classi test  g/y/r = {fb.round(4)}")
    print(f"[shift] scarto assoluto    = {np.abs(fb-fa).round(4)} | JS classi {jensenshannon(fa, fb, base=2):.4f}")
    print(f"[shift] rosso: {fa[2]*100:.2f}% -> {fb[2]*100:.2f}% ({100*(fb[2]-fa[2])/fa[2]:+.1f}% relativo)")
    raise SystemExit(0)

if args.attach_check:
    _kset = set(kept)
    _pos = {s: i for i, s in enumerate(sids_full)}
    _in = np.array([_pos[s] for s in kept])
    _out = np.array([i for i, s in enumerate(sids_full) if s not in _kset])
    _Y = np.where(C_full > 0, C_full - 1, -1)
    _ctr = C_full[reg]
    _fr = np.array([(_ctr == k).sum() for k in (1, 2, 3)], dtype="float64")
    _W = (_fr.sum() / (np.maximum(_fr, 1) * 3)).astype("float32")
    _S = C_full.shape[1]
    _hp = np.zeros((_S, 672, 3))
    for _k in range(3):
        _m = (_ctr == (_k + 1))
        _ss = np.broadcast_to(np.arange(_S), _ctr.shape)
        _sl = np.broadcast_to(slot[reg][:, None], _ctr.shape)
        np.add.at(_hp[:, :, _k], (_ss[_m], _sl[_m]), 1)
    _hp = (_hp + 1.0) / (_hp.sum(-1, keepdims=True) + 3.0)      # Laplace
    def _wce(cols):
        num = den = 0.0
        for _h in HORIZONS:
            Yv = _Y[np.ix_(te + _h, cols)].reshape(-1)
            Pv = _hp[cols][:, slot[te + _h], :].transpose(1, 0, 2).reshape(-1, 3)
            v = Yv >= 0
            if not v.any(): continue
            pt = np.clip(Pv[np.arange(len(Yv))[v], Yv[v]], 1e-7, 1)
            num += float(np.sum(_W[Yv[v]] * -np.log(pt))); den += float(np.sum(_W[Yv[v]]))
        return num / max(den, 1e-9)
    def _freq(cols):
        Yv = _Y[:, cols]; v = Yv >= 0
        return [round(float((Yv[v] == k).mean()), 3) for k in range(3)]
    print(f"\n[attach-check] agganciati n={len(_in):4d}  wCE priore={_wce(_in):.4f}  g/y/r={_freq(_in)}")
    if len(_out):
        wi, wo = _wce(_in), _wce(_out)
        print(f"[attach-check] esclusi     n={len(_out):4d}  wCE priore={wo:.4f}  g/y/r={_freq(_out)}")
        print(f"[attach-check] differenziale (esclusi - agganciati) = {wo - wi:+.4f}"
              f"   -> esclusi {'PIU FACILI' if wo < wi else 'PIU DIFFICILI'}")
    else:
        print("[attach-check] nessun sensore escluso: popolazioni identiche")
    raise SystemExit(0)
hs = np.zeros((K, 672)); hc = np.zeros((K, 672)); tt = np.arange(0, tr[-1] + 1)
rv = r[tt]; vv = np.isfinite(rv); si = np.broadcast_to(np.arange(K), rv.shape); sl = np.broadcast_to(slot[tt][:, None], rv.shape)
np.add.at(hs, (si[vv], sl[vv]), rv[vv]); np.add.at(hc, (si[vv], sl[vv]), 1)
ht = np.divide(hs, hc, out=np.full_like(hs, np.nan), where=hc > 0)
gm = float(np.nanmean(ht)); sm = np.nanmean(np.where(np.isfinite(ht), ht, np.nan), 1)
sm = np.where(np.isfinite(sm), sm, gm); HA = np.nan_to_num(np.where(np.isfinite(ht), ht, sm[:, None]), nan=gm).astype("float32")

DUMP = []
PROBS = []
VALPROBS = []
def scores(P, Y, tag=""):
    if args.dump_probs and tag and not tag.startswith("hist_prior"):
        _P = P.reshape(-1, 3); _Y = Y.reshape(-1); _v = _Y >= 0
        PROBS.append({"tag": tag, "p": _P[_v].astype("float16"),
                      "y": _Y[_v].astype("int8"), "idx": np.where(_v)[0].astype("int32")})
    P = P.reshape(-1, 3); Y = Y.reshape(-1); v = Y >= 0; P, Y = P[v], Y[v]
    pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1)
    wce = float(np.sum(Wnp[Y] * -np.log(pt)) / np.sum(Wnp[Y]))    # normalize by sum of weights
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
        pr_red = P[:, 2]; bins = np.clip((pr_red * 10).astype(int), 0, 9); ece = 0.0
        for b in range(10):
            m = bins == b
            if m.sum():
                pm, fo = float(pr_red[m].mean()), float((Y[m] == 2).mean())
                ece += m.sum()/len(Y) * abs(pm - fo)
                DUMP.append((tag, "calib", b, pm, fo, 0.0, int(m.sum())))
        DUMP.append((tag, "ece", 0, float(ece), 0.0, 0.0, len(Y)))
        thr = np.arange(0.05, 1.0, 0.05)
        pos = (Y == 2)
        for th in thr:
            sel = pr_red >= th
            tp = int((sel & pos).sum()); fp = int((sel & ~pos).sum()); fn = int((~sel & pos).sum())
            DUMP.append((tag, "pr_curve", int(round(th*100)),
                         tp/(tp+fp) if tp+fp else 0.0, tp/(tp+fn) if tp+fn else 0.0,
                         (tp+fp)/len(Y), tp+fp))
    return wce, float(np.mean(f1)), float(np.sum((pred == 2) & (Y == 2)) / max(np.sum(Y == 2), 1)), float(red_prec)

def write(rows):
    new = pd.DataFrame(rows, columns=["model", "horizon", "wCE", "macroF1", "red_recall", "red_prec"])
    if args.out.exists():
        new = pd.concat([pd.read_csv(args.out), new]).drop_duplicates(["model", "horizon"], keep="last")
    if "seed" not in new.columns:
        new.insert(0, "context", args.targets.stem); new.insert(1, "city", args.city)
        new.insert(2, "seed", args.seed); new.insert(3, "config", args.modes)
    new.to_csv(args.out, index=False)
    if args.dump_probs_val and VALPROBS:
        _d = {"context": args.targets.stem, "city": args.city, "seed": args.seed,
              "config": args.modes, "n_nodi": K, "split": "validation"}
        for _i, _b in enumerate(VALPROBS):
            _d[f"tag{_i}"] = _b["tag"]; _d[f"p{_i}"] = _b["p"]
            _d[f"y{_i}"] = _b["y"]; _d[f"idx{_i}"] = _b["idx"]
        np.savez_compressed(args.dump_probs_val, **_d)
        print(f"[probs-val] -> {args.dump_probs_val} ({len(VALPROBS)} blocchi)")
    if args.dump_probs and PROBS:
        _d = {"context": args.targets.stem, "city": args.city, "seed": args.seed,
              "config": args.modes, "n_nodi": K}
        for _i, _b in enumerate(PROBS):
            _d[f"tag{_i}"] = _b["tag"]; _d[f"p{_i}"] = _b["p"]; _d[f"y{_i}"] = _b["y"]; _d[f"idx{_i}"] = _b["idx"]
        np.savez_compressed(args.dump_probs, **_d)
        print(f"[probs] -> {args.dump_probs} ({len(PROBS)} blocchi)")
    if args.dump_metrics and DUMP:
        pd.DataFrame(DUMP, columns=["tag","kind","idx","a","b","c","n"]).to_csv(args.dump_metrics, index=False)
        print(f"[metrics] -> {args.dump_metrics}")
    return new

# ----------------------------------------------------------- torch backend ---
def run_torch():
    import torch, torch.nn as nn, torch.nn.functional as F
    torch.manual_seed(args.seed)
    DEV = (torch.device(args.device) if args.device else
           torch.device("mps" if torch.backends.mps.is_available()
                        else "cuda" if torch.cuda.is_available() else "cpu"))
    print("device:", DEV)
    def zst(a): v = a[reg][np.isfinite(a[reg])]; return float(v.mean()), float(v.std() + 1e-6)
    fmu, fsd = zst(flow); omu, osd = zst(occ)
    def T_(a): return torch.tensor(a, device=DEV)
    Rfill = T_(np.where(np.isfinite(r), r, 1.0)); FLn = T_(np.where(np.isfinite(flow), (flow-fmu)/fsd, 0.0))
    OCn = T_(np.where(np.isfinite(occ), (occ-omu)/osd, 0.0))
    q = (ts.hour.to_numpy()*4 + ts.minute.to_numpy()//15)/96.0
    TODs = T_(np.sin(2*np.pi*q).astype("float32")); TODc = T_(np.cos(2*np.pi*q).astype("float32"))
    DOWs = T_(np.sin(2*np.pi*ts.dayofweek.to_numpy()/7).astype("float32"))
    DOWc = T_(np.cos(2*np.pi*ts.dayofweek.to_numpy()/7).astype("float32"))
    WKND = T_((ts.dayofweek.to_numpy() >= 5).astype("float32"))
    HAser = T_(HA[:, slot].T.copy()); SLOT = torch.tensor(slot, device=DEV, dtype=torch.long)
    Cy = T_(np.where(C > 0, C - 1, 0).astype("int64")); Cm = T_((C > 0).astype("float32")); Wt = T_(Wnp)
    mask = Araw > 0; sg = Araw[mask].std()
    Aff = np.where(mask, np.exp(-(Araw/sg)**2), 0.0).astype("float32"); np.fill_diagonal(Aff, 0.0)
    Aff = Aff + np.eye(K, dtype="float32"); dd = Aff.sum(1); dinv = 1/np.sqrt(np.maximum(dd, 1e-6))
    A_fixed = T_((Aff*dinv[:, None])*dinv[None, :]); DEMB = args.emb; C_IN = 8 if args.no_ha else 9
    NDESC = None
    if args.node_desc:
        _nd = np.load(args.node_desc).astype("float32")
        assert _nd.shape[0] == K, f"descrittore {_nd.shape} incompatibile con K={K}"
        assert DEMB == 0, "--node-desc richiede --emb 0: sostituisce l'embedding, non lo affianca"
        NDESC = T_(_nd); C_IN += _nd.shape[1]
        print(f"[descrittore] {_nd.shape[1]} statistiche per nodo"
              + (f", proiettate su {args.desc_proj} dimensioni apprese -> canali {C_IN-_nd.shape[1]+args.desc_proj}"
                 if args.desc_proj > 0 else f" usate direttamente -> C_IN={C_IN}"))

    def make_batch(bt):
        bt = torch.as_tensor(bt, device=DEV)
        def wn(M): return torch.stack([M[bt-k] for k in reversed(range(T_IN))], -1)
        def wg(g):
            wi = torch.stack([g[bt-k] for k in reversed(range(T_IN))], -1); return wi.unsqueeze(1).expand(-1, K, -1)
        _ch = [wn(Rfill), wn(FLn), wn(OCn)] + ([] if args.no_ha else [wn(HAser)]) + \
              [wg(TODs), wg(TODc), wg(DOWs), wg(DOWc), wg(WKND)]
        x = torch.stack(_ch, 1)
        y = torch.stack([Cy[bt+h] for h in HORIZONS], -1); m = torch.stack([Cm[bt+h] for h in HORIZONS], -1)
        return x, y, m

    class GTCN(nn.Module):
        def __init__(s, c, k, d): super().__init__(); s.pad = (k-1)*d; s.f = nn.Conv2d(c, c, (1, k), dilation=(1, d)); s.g = nn.Conv2d(c, c, (1, k), dilation=(1, d))
        def forward(s, x): x = F.pad(x, (s.pad, 0)); return torch.tanh(s.f(x))*torch.sigmoid(s.g(x))
    class GCN(nn.Module):
        def __init__(s, c, ns, order=2): super().__init__(); s.order = order; s.mlp = nn.Conv2d(c*(order*ns+1), c, (1, 1))
        def forward(s, x, sup):
            out = [x]
            for A in sup:
                xk = x
                for _ in range(s.order): xk = torch.einsum("nm,bcmt->bcnt", A, xk); out.append(xk)
            return s.mlp(torch.cat(out, 1))
    class Block(nn.Module):
        def __init__(s, c, d, ns): super().__init__(); s.tcn = GTCN(c, 2, d); s.gcn = GCN(c, ns) if ns > 0 else None; s.skip = nn.Conv2d(c, c, (1, 1)); s.bn = nn.BatchNorm2d(c)
        def forward(s, x, sup):
            res = x; x = s.tcn(x); sk = s.skip(x)
            if s.gcn is not None: x = s.gcn(x, sup)
            return s.bn(x + res), sk
    class STIDNet(nn.Module):
        def __init__(s):
            super().__init__()
            s.emb = nn.Parameter(torch.randn(K, DEMB)*0.05) if DEMB > 0 else None
            s.net = nn.Sequential(nn.Conv2d(C_IN*T_IN+DEMB, args.hidden, (1,1)), nn.ReLU(),
                                  nn.Conv2d(args.hidden, args.hidden, (1,1)), nn.ReLU(),
                                  nn.Conv2d(args.hidden, args.hidden, (1,1)), nn.ReLU())
            s.head = nn.Conv2d(args.hidden, H*3, (1,1))
        def forward(s, x):
            B = x.shape[0]
            z = x.permute(0,1,3,2).reshape(B, C_IN*T_IN, K, 1)
            if DEMB > 0:
                e = s.emb.t().unsqueeze(0).unsqueeze(-1).expand(B, -1, -1, 1)
                z = torch.cat([z, e], 1)
            o = s.head(s.net(z))
            return o.squeeze(-1).permute(0, 2, 1).contiguous().reshape(B, K, H, 3)

    class GWN(nn.Module):
        def __init__(s, mode):
            super().__init__(); s.mode = mode; s.ns = (mode in ("fixed", "both")) + (mode in ("adaptive", "both"))
            s.emb = nn.Parameter(torch.randn(K, DEMB)*0.05) if DEMB > 0 else None
            s.proj = (nn.Sequential(nn.Linear(NDESC.shape[1], args.desc_hidden), nn.ReLU(),
                                    nn.Linear(args.desc_hidden, args.desc_proj))
                      if args.desc_hidden > 0 else nn.Linear(NDESC.shape[1], args.desc_proj, bias=False)) \
                     if (NDESC is not None and args.desc_proj > 0) else None
            _extra = args.desc_proj - NDESC.shape[1] if s.proj is not None else 0
            s.start = nn.Conv2d(C_IN+DEMB+_extra, args.hidden, (1, 1))
            if mode in ("adaptive", "both"): s.E1 = nn.Parameter(torch.randn(K, 10)*0.05); s.E2 = nn.Parameter(torch.randn(K, 10)*0.05)
            d = 1; s.blocks = nn.ModuleList()
            for _ in range(args.blocks): s.blocks.append(Block(args.hidden, d, s.ns)); d *= 2
            s.e1 = nn.Conv2d(args.hidden, args.hidden, (1, 1)); s.e2 = nn.Conv2d(args.hidden, H*3, (1, 1))
        def sup(s):
            Sx = []
            if s.mode in ("fixed", "both"): Sx.append(A_fixed)
            if s.mode in ("adaptive", "both"): Sx.append(F.softmax(F.relu(s.E1 @ s.E2.t()), dim=1))
            return Sx
        def forward(s, x):
            B, _, N, T = x.shape
            if DEMB > 0:
                e = s.emb.t().view(1, DEMB, N, 1).expand(B, DEMB, N, T)
                x = s.start(torch.cat([x, e], 1))
            elif NDESC is not None:
                _nd = s.proj(NDESC) if s.proj is not None else NDESC
                d = _nd.t().view(1, -1, N, 1).expand(B, _nd.shape[1], N, T)
                x = s.start(torch.cat([x, d], 1))
            else:
                x = s.start(x)
            sup = s.sup(); skip = 0
            for b in s.blocks: x, sk = b(x, sup); skip = skip + sk[..., -1:]
            h = F.relu(s.e1(F.relu(skip)))
            return s.e2(h).squeeze(-1).permute(0, 2, 1).contiguous().reshape(B, N, H, 3)
    def loss_fn(lg, y, m):
        lp = F.log_softmax(lg, -1); nll = -lp.gather(-1, y.unsqueeze(-1)).squeeze(-1)
        return (nll * Wt[y] * m).sum() / (Wt[y] * m).sum().clamp_min(1)   # sum-of-weights norm

    rows = []
    # historical class prior baseline (numpy)
    hp = np.zeros((K, 672, 3))
    for k in range(3):
        mm = (ctr == (k+1)); ss = np.broadcast_to(np.arange(K), ctr.shape); slT = np.broadcast_to(slot[reg][:, None], ctr.shape)
        np.add.at(hp[:, :, k], (ss[mm], slT[mm]), 1)
    if args.prior_alpha > 0:
        hp = (hp + args.prior_alpha) / (hp.sum(-1, keepdims=True) + 3 * args.prior_alpha)
    else:
        hp = hp / np.clip(hp.sum(-1, keepdims=True), 1, None); hp[hp.sum(-1) == 0] = 1/3
    for h in HORIZONS:
        Yt = np.where(C[te+h] > 0, C[te+h]-1, -1); Pt = hp[:, slot[te+h], :].transpose(1, 0, 2)
        rows.append(("hist_prior", HL[h], *scores(Pt, Yt, tag=str("hist_prior") + "|" + str(HL[h]))))

    if args.prior_only:
        import pandas as _pd
        _pd.DataFrame(rows, columns=["model","horizon","wCE","macroF1","red_recall","red_prec"]).to_csv(args.out, index=False)
        print(f"[prior-only] alpha={args.prior_alpha} -> {args.out}"); raise SystemExit(0)

    for mode in [m.strip() for m in args.modes.split(",")]:
        net = (STIDNet() if mode == "stid" else GWN(mode)).to(DEV)
        print(f"[{mode}] parametri totali = {sum(p.numel() for p in net.parameters()):,} | K={K} DEMB={DEMB} hidden={args.hidden}"); opt = torch.optim.Adam(net.parameters(), lr=args.lr)
        best = 1e9; bs = {k: v.detach().clone() for k, v in net.state_dict().items()}; bad = 0
        for ep in range(args.epochs):
            net.train(); perm = np.random.permutation(tr)
            for i in range(0, len(perm), args.batch):
                x, y, m = make_batch(perm[i:i+args.batch]); opt.zero_grad(); loss_fn(net(x), y, m).backward(); opt.step()
            net.eval(); num = den = 0.0
            with torch.no_grad():
                for i in range(0, len(va), 256):
                    x, y, m = make_batch(va[i:i+256]); num += loss_fn(net(x), y, m).item()*m.sum().item(); den += m.sum().item()
            v = num/max(den, 1)
            if v < best-1e-5: best, bs, bad = v, {k: vv.detach().clone() for k, vv in net.state_dict().items()}, 0
            else: bad += 1
            print(f"[{mode}] epoch {ep+1:02d}  val wCE={v:.4f}  best={best:.4f}")
            if bad >= args.patience: print(f"[{mode}] early stop"); break
        net.load_state_dict(bs); net.eval(); P, Y = [], []
        with torch.no_grad():
            for i in range(0, len(te), 256):
                x, y, m = make_batch(te[i:i+256]); P.append(F.softmax(net(x), -1).cpu().numpy()); Y.append(np.where(m.cpu().numpy() > 0, y.cpu().numpy(), -1))
        P = np.concatenate(P); Y = np.concatenate(Y)
        for j, h in enumerate(HORIZONS): rows.append((f"gwn_{mode}", HL[h], *scores(P[..., j, :], Y[..., j], tag=f"gwn_{mode}|{HL[h]}")))
        if args.dump_probs_val:
            Pv, Yv = [], []
            with torch.no_grad():
                for i in range(0, len(va), 256):
                    x, y, m = make_batch(va[i:i+256])
                    Pv.append(F.softmax(net(x), -1).cpu().numpy())
                    Yv.append(np.where(m.cpu().numpy() > 0, y.cpu().numpy(), -1))
            Pv = np.concatenate(Pv); Yv = np.concatenate(Yv)
            for j, h in enumerate(HORIZONS):
                _p = Pv[..., j, :].reshape(-1, 3); _y = Yv[..., j].reshape(-1); _v = _y >= 0
                VALPROBS.append({"tag": f"gwn_{mode}|{HL[h]}", "p": _p[_v].astype("float16"),
                                 "y": _y[_v].astype("int8"), "idx": np.where(_v)[0].astype("int32")})
    return rows

# ------------------------------------------------------------- lgb backend ---
def run_lgb():
    import lightgbm as lgb
    def feats(idxs, h):
        N = len(idxs); bc = lambda a: np.broadcast_to(a[idxs+h][:, None], (N, K))
        cols = {"r_t": r[idxs], "r1": r[idxs-1], "r2": r[idxs-2], "r3": r[idxs-3], "flow": flow[idxs], "occ": occ[idxs],
                "ha": HA[:, slot[idxs+h]].T, "hour": bc(ts.hour.to_numpy()).astype("float32"),
                "dow": bc(ts.dayofweek.to_numpy()).astype("float32"),
                "sid": np.broadcast_to(np.arange(K)[None, :], (N, K)).astype("float32")}
        X = pd.DataFrame({k: v.reshape(-1) for k, v in cols.items()})
        for c in ("hour", "dow", "sid"): X[c] = X[c].astype("int32")
        return X, (C[idxs+h]-1).reshape(-1)
    rows = []
    for h in HORIZONS:
        Xtr, ytr = feats(tr, h); k = ytr >= 0; Xtr, ytr = Xtr[k], ytr[k]
        if len(ytr) > args.lgb_cap:
            s = np.random.default_rng(0).choice(len(ytr), args.lgb_cap, replace=False); Xtr, ytr = Xtr.iloc[s], ytr[s]
        ds = lgb.Dataset(Xtr, ytr, weight=Wnp[ytr], categorical_feature=["hour", "dow", "sid"])
        model = lgb.train(dict(objective="multiclass", num_class=3, learning_rate=0.05, num_leaves=63,
                               feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, verbose=-1, seed=0),
                          ds, num_boost_round=250)
        Xte, yte = feats(te, h); rows.append(("lightgbm", HL[h], *scores(model.predict(Xte), np.where(yte >= 0, yte, -1), tag="lightgbm|" + str(HL[h]))))
    return rows

# ------------------------------------------------------------------ main ----
if args.backend in ("both", "torch"):
    write(run_torch())
if args.backend == "lgb":
    write(run_lgb())
if args.backend == "both":
    _extra = ["--dump-metrics", str(args.dump_metrics) + ".lgb"] if args.dump_metrics else []
    subprocess.run([sys.executable, __file__, "--backend", "lgb", "--targets", str(args.targets),
                    "--graph", str(args.graph), "--sensors", str(args.sensors), "--out", str(args.out)]
                   + _extra, check=True)

final = pd.read_csv(args.out); pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== Weighted-CE classification results (test set) ==="); print(final.to_string(index=False))
print(f"\nsaved -> {args.out}")
