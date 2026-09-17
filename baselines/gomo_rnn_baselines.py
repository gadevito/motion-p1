"""
GO-MO — AGCRN & DCRNN neural baselines (weighted-CE classification)
==================================================================
Two SOTA spatio-temporal RNNs as neural baselines next to our Graph WaveNet, on the
same URB district-8 task, same 9-channel 12-step input, same Traffic4cast weighted CE
(weights n/(count*3), sum-of-weights norm) + red recall. Encoder GRU whose matrix
products are graph convolutions, then a multi-horizon classification head.
  AGCRN : learned adjacency + node-adaptive params (native node embeddings)
  DCRNN : diffusion convolution on the routes graph (bidirectional random walk)
Both get HAser (per-node seasonal identity) in input, for a fair comparison.

Place in models/. Run:
    poetry run python gomo_rnn_baselines.py --model both \
        --targets ../data_collection/go-mo/gomo/targets_2024_urb_d8.npz
Needs: torch, networkx, scipy
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
from pathlib import Path
import argparse, pickle
import numpy as np
import pandas as pd
import networkx as nx
from scipy.spatial import cKDTree
import torch
import torch.nn as nn
import torch.nn.functional as F

DATA = Path("../data_collection/go-mo/gomo")
ap = argparse.ArgumentParser(description="AGCRN & DCRNN baselines")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_urb_d8.npz")
ap.add_argument("--graph",   type=Path, default=DATA / "routes-graph.pkl")
ap.add_argument("--sensors", type=Path, default=DATA / "traffic_sensors.csv")
ap.add_argument("--dump-probs", type=str, default="")
ap.add_argument("--city", type=str, default="")
ap.add_argument("--out",     type=Path, default=Path("rnn_baseline_results.csv"))
ap.add_argument("--model", choices=["agcrn", "dcrnn", "both"], default="both")
ap.add_argument("--win", type=int, default=12)
ap.add_argument("--hidden", type=int, default=32)
ap.add_argument("--emb", type=int, default=10)
ap.add_argument("--epochs", type=int, default=30)
ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--lr", type=float, default=3e-3)
ap.add_argument("--patience", type=int, default=8)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--device", default=None)
args = ap.parse_args()
torch.manual_seed(args.seed); np.random.seed(args.seed)
DEV = (torch.device(args.device) if args.device else
       torch.device("mps" if torch.backends.mps.is_available()
                    else "cuda" if torch.cuda.is_available() else "cpu"))
print("device:", DEV)
T_IN = args.win; HORIZONS = [1, 2, 4, 8]; H = len(HORIZONS); HL = {1: "15m", 2: "30m", 4: "60m", 8: "120m"}

# ------------------------------------------------------------------- data ---
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
kidx = np.array([posm[s] for s in kept]); N = len(kept)
_wattr = "distance" if any("distance" in _a for *_, _a in list(rg.edges(data=True))[:50]) else "weight"
Araw = nx.to_numpy_array(rg.subgraph(kept).copy(), nodelist=kept, weight=_wattr).astype("float32")
Araw[Araw > 0] = np.maximum(Araw[Araw > 0], 1.0)
print(f"[grafo] attributo: {_wattr} | archi {(Araw>0).sum()} | mediana {np.median(Araw[Araw>0]):.1f}")
r, flow, occ, C = r[:, kidx], flow[:, kidx], occ[:, kidx], C[:, kidx]
print(f"aligned graph: {N} of {S} sensors")

# DCRNN transition matrices (row-normalized affinity, forward + backward)
m = Araw > 0; sg = Araw[m].std()
Aff = np.where(m, np.exp(-(Araw/sg)**2), 0.0).astype("float32"); np.fill_diagonal(Aff, 1.0)
Pf = Aff / np.clip(Aff.sum(1, keepdims=True), 1e-6, None)
Pb = Aff.T / np.clip(Aff.T.sum(1, keepdims=True), 1e-6, None)
Pf = torch.tensor(Pf, device=DEV); Pb = torch.tensor(Pb, device=DEV)

starts = np.arange(T_IN - 1, Tn - max(HORIZONS)); n = len(starts)
tr, va, te = starts[:int(n*.7)], starts[int(n*.7):int(n*.8)], starts[int(n*.8):]
reg = slice(0, tr[-1] + 1); ctr = C[reg]
freq = np.array([(ctr == k).sum() for k in (1, 2, 3)], dtype="float64")
Wnp = (freq.sum() / (np.maximum(freq, 1)*3)).astype("float32")
print(f"class freq g/y/r = {(freq/freq.sum()).round(3)} | T4c weights = {Wnp.round(2)}")

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
slot = (ts.dayofweek.to_numpy()*96 + ts.hour.to_numpy()*4 + ts.minute.to_numpy()//15)
hs = np.zeros((N, 672)); hc = np.zeros((N, 672)); tt = np.arange(0, tr[-1] + 1)
rv = r[tt]; vv = np.isfinite(rv); si = np.broadcast_to(np.arange(N), rv.shape); sl = np.broadcast_to(slot[tt][:, None], rv.shape)
np.add.at(hs, (si[vv], sl[vv]), rv[vv]); np.add.at(hc, (si[vv], sl[vv]), 1)
ht = np.divide(hs, hc, out=np.full_like(hs, np.nan), where=hc > 0)
gm = float(np.nanmean(ht)); sm = np.nanmean(np.where(np.isfinite(ht), ht, np.nan), 1)
sm = np.where(np.isfinite(sm), sm, gm); HA = np.nan_to_num(np.where(np.isfinite(ht), ht, sm[:, None]), nan=gm).astype("float32")
HAser = T_(HA[:, slot].T.copy())
Cy = T_(np.where(C > 0, C - 1, 0).astype("int64")); Cm = T_((C > 0).astype("float32")); Wt = T_(Wnp)
C_IN = 9

def make_batch(bt):
    bt = torch.as_tensor(bt, device=DEV); B = len(bt)
    ix = [bt - k for k in reversed(range(T_IN))]
    def ns(M): return torch.stack([M[i] for i in ix], 1)                 # (B,T,N)
    def gs(g): return torch.stack([g[i] for i in ix], 1).unsqueeze(-1).expand(B, T_IN, N)
    x = torch.stack([ns(Rfill), ns(FLn), ns(OCn), ns(HAser),
                     gs(TODs), gs(TODc), gs(DOWs), gs(DOWc), gs(WKND)], -1)   # (B,T,N,C)
    y = torch.stack([Cy[bt+h] for h in HORIZONS], -1)
    mk = torch.stack([Cm[bt+h] for h in HORIZONS], -1)
    return x, y, mk

# --------------------------------------------------------------- DCRNN -------
class DiffConv(nn.Module):
    def __init__(s, cin, cout, K=2): super().__init__(); s.K = K; s.lin = nn.Linear(cin*(2*K+1), cout)
    def forward(s, x):                                                  # x (B,N,cin)
        out = [x]
        for P in (Pf, Pb):
            xk = x
            for _ in range(s.K): xk = torch.einsum("nm,bmi->bni", P, xk); out.append(xk)
        return s.lin(torch.cat(out, -1))
class DCGRU(nn.Module):
    def __init__(s, cin, hid): super().__init__(); s.g = DiffConv(cin+hid, 2*hid); s.c = DiffConv(cin+hid, hid)
    def forward(s, x, h):
        rz = torch.sigmoid(s.g(torch.cat([x, h], -1))); rr, zz = rz.chunk(2, -1)
        c = torch.tanh(s.c(torch.cat([x, rr*h], -1))); return zz*h + (1-zz)*c
class DCRNN(nn.Module):
    def __init__(s): super().__init__(); s.cell = DCGRU(C_IN, args.hidden); s.head = nn.Linear(args.hidden, H*3)
    def forward(s, x):
        B, T, n_, _ = x.shape; h = torch.zeros(B, n_, args.hidden, device=x.device)
        for t in range(T): h = s.cell(x[:, t], h)
        return s.head(h).reshape(B, n_, H, 3)

# --------------------------------------------------------------- AGCRN -------
class AVWGCN(nn.Module):
    def __init__(s, cin, cout, emb): super().__init__(); s.Wp = nn.Parameter(torch.randn(emb, 2, cin, cout)*0.05); s.bp = nn.Parameter(torch.zeros(emb, cout))
    def forward(s, x, E, A):                                            # x (B,N,cin), E (N,emb), A (N,N)
        xg = torch.stack([x, torch.einsum("nm,bmi->bni", A, x)], 1)     # (B,2,N,cin)
        W = torch.einsum("nd,dkio->nkio", E, s.Wp); b = E @ s.bp
        return torch.einsum("bkni,nkio->bno", xg, W) + b
class AGCRNCell(nn.Module):
    def __init__(s, cin, hid, emb): super().__init__(); s.g = AVWGCN(cin+hid, 2*hid, emb); s.c = AVWGCN(cin+hid, hid, emb)
    def forward(s, x, h, E, A):
        rz = torch.sigmoid(s.g(torch.cat([x, h], -1), E, A)); rr, zz = rz.chunk(2, -1)
        c = torch.tanh(s.c(torch.cat([x, rr*h], -1), E, A)); return zz*h + (1-zz)*c
class AGCRN(nn.Module):
    def __init__(s): super().__init__(); s.E = nn.Parameter(torch.randn(N, args.emb)*0.05); s.cell = AGCRNCell(C_IN, args.hidden, args.emb); s.head = nn.Linear(args.hidden, H*3)
    def forward(s, x):
        B, T, n_, _ = x.shape; A = F.softmax(F.relu(s.E @ s.E.t()), dim=1); h = torch.zeros(B, n_, args.hidden, device=x.device)
        for t in range(T): h = s.cell(x[:, t], h, s.E, A)
        return s.head(h).reshape(B, n_, H, 3)

def loss_fn(lg, y, mk):
    lp = F.log_softmax(lg, -1); nll = -lp.gather(-1, y.unsqueeze(-1)).squeeze(-1)
    return (nll*Wt[y]*mk).sum()/(Wt[y]*mk).sum().clamp_min(1)

def train_eval(name):
    net = (AGCRN() if name == "agcrn" else DCRNN()).to(DEV)
    opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    best = 1e9; bs = {k: v.detach().clone() for k, v in net.state_dict().items()}; bad = 0
    for ep in range(args.epochs):
        net.train(); perm = np.random.permutation(tr)
        for i in range(0, len(perm), args.batch):
            x, y, mk = make_batch(perm[i:i+args.batch]); opt.zero_grad(); loss_fn(net(x), y, mk).backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0); opt.step()
        net.eval(); num = den = 0.0
        with torch.no_grad():
            for i in range(0, len(va), 128):
                x, y, mk = make_batch(va[i:i+128]); num += loss_fn(net(x), y, mk).item()*mk.sum().item(); den += mk.sum().item()
        v = num/max(den, 1)
        if v < best-1e-5: best, bs, bad = v, {k: vv.detach().clone() for k, vv in net.state_dict().items()}, 0
        else: bad += 1
        print(f"[{name}] epoch {ep+1:02d}  val wCE={v:.4f}  best={best:.4f}")
        if bad >= args.patience: print(f"[{name}] early stop"); break
    net.load_state_dict(bs); net.eval(); P, Y = [], []
    with torch.no_grad():
        for i in range(0, len(te), 128):
            x, y, mk = make_batch(te[i:i+128])
            P.append(F.softmax(net(x), -1).cpu().numpy()); Y.append(np.where(mk.cpu().numpy() > 0, y.cpu().numpy(), -1))
    return np.concatenate(P), np.concatenate(Y)

PROBS = []
def scores(P, Y, tag=""):
    if args.dump_probs and tag:
        _P = P.reshape(-1, 3); _Y = Y.reshape(-1); _v = _Y >= 0
        PROBS.append({"tag": tag, "p": _P[_v].astype("float16"),
                      "y": _Y[_v].astype("int8"), "idx": np.where(_v)[0].astype("int32")})
    P = P.reshape(-1, 3); Y = Y.reshape(-1); v = Y >= 0; P, Y = P[v], Y[v]
    pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1); wce = float(np.sum(Wnp[Y]*-np.log(pt))/np.sum(Wnp[Y]))
    pred = P.argmax(1); f1 = []
    for k in range(3):
        tp = np.sum((pred == k) & (Y == k)); fp = np.sum((pred == k) & (Y != k)); fn = np.sum((pred != k) & (Y == k))
        pr = tp/(tp+fp) if tp+fp else 0; rc = tp/(tp+fn) if tp+fn else 0
        f1.append(2*pr*rc/(pr+rc) if pr+rc else 0)
        if k == 2: red_prec = pr
    return wce, float(np.mean(f1)), float(np.sum((pred == 2) & (Y == 2))/max(np.sum(Y == 2), 1)), float(red_prec)

rows = []
for name in (["agcrn", "dcrnn"] if args.model == "both" else [args.model]):
    P, Y = train_eval(name)
    for j, h in enumerate(HORIZONS): rows.append((name, HL[h], *scores(P[..., j, :], Y[..., j], tag=f"{name}|{HL[h]}")))
res = pd.DataFrame(rows, columns=["model", "horizon", "wCE", "macroF1", "red_recall", "red_prec"])
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== AGCRN / DCRNN — weighted-CE classification (test) ===")
print(res.to_string(index=False))
print("\ncompare: GWN wCE ~0.63-0.70 (red ~0.70) | fair LightGBM ~0.84-0.92 (red ~0.59)")
res.insert(1, "seed", args.seed); res.insert(2, "city", args.city)
res.to_csv(args.out, index=False); print(f"saved -> {args.out}")
if args.dump_probs and PROBS:
    _d = {"context": Path(args.targets).stem, "city": args.city, "seed": args.seed, "n_nodi": N}
    for _i, _b in enumerate(PROBS):
        _d[f"tag{_i}"] = _b["tag"]; _d[f"p{_i}"] = _b["p"]
        _d[f"y{_i}"] = _b["y"]; _d[f"idx{_i}"] = _b["idx"]
    np.savez_compressed(args.dump_probs, **_d)
    print(f"[probs] -> {args.dump_probs} ({len(PROBS)} blocchi)")
