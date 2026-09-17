"""
GO-MO — final SOTA comparison: STAEformer (compact) + Traffic4cast-style GNN
============================================================================
STAEformer (Liu et al., CIKM 2023) is still the standard SOTA reference for
spatio-temporal forecasting as of 2025-26. Its thesis — "spatio-temporal adaptive
EMBEDDING makes a vanilla transformer SOTA" — is independently our central finding
(node identity dominates), so it is the ideal final comparison. Implemented compact
but faithful: per-node adaptive embedding + time-of-day + day-of-week embeddings,
temporal self-attention then spatial self-attention, classification head.

t4c_gnn: a Traffic4cast-style plain GCN baseline — 4-step input (past hour, as in
the competition), stacked graph convolutions, NO node embeddings, 15-min horizon
only — closing the loop with the original competition setup.

Same task/metric as everything else (URB d8, Traffic4cast weighted CE + red recall).
Place in baselines/. Run:
    poetry run python gomo_sota_baselines.py --model both \
        --targets ../data_collection/go-mo/gomo/targets_2024_urb_d8.npz
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
ap = argparse.ArgumentParser(description="STAEformer + Traffic4cast-style GNN baselines")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_urb_d8.npz")
ap.add_argument("--graph",   type=Path, default=DATA / "routes-graph.pkl")
ap.add_argument("--sensors", type=Path, default=DATA / "traffic_sensors.csv")
ap.add_argument("--dump-probs", type=str, default="")
ap.add_argument("--city", type=str, default="")
ap.add_argument("--out",     type=Path, default=Path("sota_baseline_results.csv"))
ap.add_argument("--model", choices=["staeformer", "t4c_gnn", "both"], default="both")
ap.add_argument("--win", type=int, default=12)
ap.add_argument("--dim", type=int, default=16, help="per-embedding dim (model dim = 4x)")
ap.add_argument("--layers", type=int, default=2, help="temporal and spatial attn layers each")
ap.add_argument("--heads", type=int, default=4)
ap.add_argument("--epochs", type=int, default=25)
ap.add_argument("--batch", type=int, default=16)
ap.add_argument("--lr", type=float, default=1e-3)
ap.add_argument("--patience", type=int, default=6)
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

m = Araw > 0; sg = Araw[m].std()
Aff = np.where(m, np.exp(-(Araw/sg)**2), 0.0).astype("float32"); np.fill_diagonal(Aff, 1.0)
d = Aff.sum(1); di = 1/np.sqrt(np.maximum(d, 1e-6))
Ahat = torch.tensor((Aff*di[:, None])*di[None, :], device=DEV)

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
quart = ts.hour.to_numpy()*4 + ts.minute.to_numpy()//15
TOD = torch.tensor(quart, device=DEV, dtype=torch.long)           # 0..95
DOW = torch.tensor(ts.dayofweek.to_numpy(), device=DEV, dtype=torch.long)
TODs = T_(np.sin(2*np.pi*quart/96).astype("float32")); TODc = T_(np.cos(2*np.pi*quart/96).astype("float32"))
Cy = T_(np.where(C > 0, C - 1, 0).astype("int64")); Cm = T_((C > 0).astype("float32")); Wt = T_(Wnp)

def make_batch(bt, w):
    btt = torch.as_tensor(bt, device=DEV)
    def wn(M): return torch.stack([M[btt-k] for k in reversed(range(w))], 1)     # (B,w,N)
    x = torch.stack([wn(Rfill), wn(FLn), wn(OCn)], -1)                            # (B,w,N,3)
    tod = torch.stack([TOD[btt-k] for k in reversed(range(w))], 1)                # (B,w)
    dow = torch.stack([DOW[btt-k] for k in reversed(range(w))], 1)
    y = torch.stack([Cy[btt+h] for h in HORIZONS], -1)
    mk = torch.stack([Cm[btt+h] for h in HORIZONS], -1)
    return x, tod, dow, y, mk

def loss_fn(lg, y, mk):
    lp = F.log_softmax(lg, -1); nll = -lp.gather(-1, y.unsqueeze(-1)).squeeze(-1)
    return (nll*Wt[y]*mk).sum()/(Wt[y]*mk).sum().clamp_min(1)

# --------------------------------------------------------- STAEformer -------
class Attn(nn.Module):
    def __init__(s, d): super().__init__(); s.a = nn.MultiheadAttention(d, args.heads, batch_first=True); s.n1 = nn.LayerNorm(d); s.ff = nn.Sequential(nn.Linear(d, d*2), nn.ReLU(), nn.Linear(d*2, d)); s.n2 = nn.LayerNorm(d)
    def forward(s, x):
        h, _ = s.a(x, x, x); x = s.n1(x + h); return s.n2(x + s.ff(x))
class STAEformer(nn.Module):
    def __init__(s):
        super().__init__(); D = args.dim
        s.proj = nn.Linear(3, D)
        s.tod = nn.Embedding(96, D); s.dow = nn.Embedding(7, D)
        s.adp = nn.Parameter(torch.randn(N, D)*0.05)              # node-adaptive embedding
        s.d = 4*D
        s.tlayers = nn.ModuleList(Attn(s.d) for _ in range(args.layers))
        s.slayers = nn.ModuleList(Attn(s.d) for _ in range(args.layers))
        s.head = nn.Linear(s.d*T_IN, H*3)
    def forward(s, x, tod, dow):                                   # x (B,T,N,3)
        B, T, Nn, _ = x.shape
        e = torch.cat([s.proj(x),
                       s.tod(tod).unsqueeze(2).expand(B, T, Nn, -1),
                       s.dow(dow).unsqueeze(2).expand(B, T, Nn, -1),
                       s.adp.view(1, 1, Nn, -1).expand(B, T, Nn, -1)], -1)   # (B,T,N,4D)
        h = e.permute(0, 2, 1, 3).reshape(B*Nn, T, s.d)            # temporal attention
        for l in s.tlayers: h = l(h)
        h = h.reshape(B, Nn, T, s.d).permute(0, 2, 1, 3).reshape(B*T, Nn, s.d)  # spatial attention
        for l in s.slayers: h = l(h)
        h = h.reshape(B, T, Nn, s.d).permute(0, 2, 1, 3).reshape(B, Nn, T*s.d)
        return s.head(h).reshape(B, Nn, H, 3)

# ------------------------------------------- Traffic4cast-style plain GCN ---
class T4CGNN(nn.Module):
    """4-step input (past hour, as in the competition), stacked GCN, no node emb, 15m only."""
    def __init__(s, hid=64):
        super().__init__(); s.inp = nn.Linear(4*3+2, hid)          # 4 steps x 3 feats + tod sin/cos
        s.g1 = nn.Linear(hid, hid); s.g2 = nn.Linear(hid, hid); s.g3 = nn.Linear(hid, hid)
        s.head = nn.Linear(hid, 3)
    def forward(s, x, todsc):                                      # x (B,4,N,3), todsc (B,2)
        B, _, Nn, _ = x.shape
        h = torch.cat([x.permute(0, 2, 1, 3).reshape(B, Nn, 12),
                       todsc.unsqueeze(1).expand(B, Nn, 2)], -1)
        h = F.relu(s.inp(h))
        for g in (s.g1, s.g2, s.g3):
            h = F.relu(g(torch.einsum("nm,bmi->bni", Ahat, h))) + h
        return s.head(h)                                           # (B,N,3) — 15m only

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
todo = ["staeformer", "t4c_gnn"] if args.model == "both" else [args.model]

if "staeformer" in todo:
    net = STAEformer().to(DEV); opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    best = 1e9; bs = {k: v.detach().clone() for k, v in net.state_dict().items()}; bad = 0
    for ep in range(args.epochs):
        net.train(); perm = np.random.permutation(tr)
        for i in range(0, len(perm), args.batch):
            x, tod, dow, y, mk = make_batch(perm[i:i+args.batch], T_IN)
            opt.zero_grad(); loss_fn(net(x, tod, dow), y, mk).backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0); opt.step()
        net.eval(); num = den = 0.0
        with torch.no_grad():
            for i in range(0, len(va), 64):
                x, tod, dow, y, mk = make_batch(va[i:i+64], T_IN)
                num += loss_fn(net(x, tod, dow), y, mk).item()*mk.sum().item(); den += mk.sum().item()
        v = num/max(den, 1)
        if v < best-1e-5: best, bs, bad = v, {k: t.detach().clone() for k, t in net.state_dict().items()}, 0
        else: bad += 1
        print(f"[staeformer] epoch {ep+1:02d}  val wCE={v:.4f}  best={best:.4f}")
        if bad >= args.patience: print("[staeformer] early stop"); break
    net.load_state_dict(bs); net.eval(); P, Y = [], []
    with torch.no_grad():
        for i in range(0, len(te), 64):
            x, tod, dow, y, mk = make_batch(te[i:i+64], T_IN)
            P.append(F.softmax(net(x, tod, dow), -1).cpu().numpy()); Y.append(np.where(mk.cpu().numpy() > 0, y.cpu().numpy(), -1))
    P, Y = np.concatenate(P), np.concatenate(Y)
    for j, h in enumerate(HORIZONS): rows.append(("staeformer", HL[h], *scores(P[..., j, :], Y[..., j], tag=f"staeformer|{HL[h]}")))

if "t4c_gnn" in todo:
    net = T4CGNN().to(DEV); opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    best = 1e9; bs = {k: v.detach().clone() for k, v in net.state_dict().items()}; bad = 0
    for ep in range(args.epochs):
        net.train(); perm = np.random.permutation(tr)
        for i in range(0, len(perm), 64):
            x, _, _, y, mk = make_batch(perm[i:i+64], 4)
            todsc = torch.stack([TODs[torch.as_tensor(perm[i:i+64], device=DEV)],
                                 TODc[torch.as_tensor(perm[i:i+64], device=DEV)]], -1)
            opt.zero_grad(); loss_fn(net(x, todsc), y[..., 0], mk[..., 0]).backward(); opt.step()
        net.eval(); num = den = 0.0
        with torch.no_grad():
            for i in range(0, len(va), 128):
                x, _, _, y, mk = make_batch(va[i:i+128], 4)
                todsc = torch.stack([TODs[torch.as_tensor(va[i:i+128], device=DEV)],
                                     TODc[torch.as_tensor(va[i:i+128], device=DEV)]], -1)
                num += loss_fn(net(x, todsc), y[..., 0], mk[..., 0]).item()*mk[..., 0].sum().item(); den += mk[..., 0].sum().item()
        v = num/max(den, 1)
        if v < best-1e-5: best, bs, bad = v, {k: t.detach().clone() for k, t in net.state_dict().items()}, 0
        else: bad += 1
        print(f"[t4c_gnn] epoch {ep+1:02d}  val wCE(15m)={v:.4f}  best={best:.4f}")
        if bad >= args.patience: print("[t4c_gnn] early stop"); break
    net.load_state_dict(bs); net.eval(); P, Y = [], []
    with torch.no_grad():
        for i in range(0, len(te), 128):
            x, _, _, y, mk = make_batch(te[i:i+128], 4)
            todsc = torch.stack([TODs[torch.as_tensor(te[i:i+128], device=DEV)],
                                 TODc[torch.as_tensor(te[i:i+128], device=DEV)]], -1)
            P.append(F.softmax(net(x, todsc), -1).cpu().numpy()); Y.append(np.where(mk[..., 0].cpu().numpy() > 0, y[..., 0].cpu().numpy(), -1))
    P, Y = np.concatenate(P), np.concatenate(Y)
    rows.append(("t4c_gnn", "15m", *scores(P, Y, tag="t4c_gnn|15m")))

res = pd.DataFrame(rows, columns=["model", "horizon", "wCE", "macroF1", "red_recall", "red_prec"])
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== SOTA comparison — weighted-CE classification (test) ===")
print(res.to_string(index=False))
print("\nreference: GWN ~0.63-0.70 (red ~0.70) | AGCRN 0.63-0.71 | DCRNN 0.65-0.75 | fair LGB 0.84-0.92")
res.insert(1, "seed", args.seed); res.insert(2, "city", args.city)
res.to_csv(args.out, index=False); print(f"saved -> {args.out}")
if args.dump_probs and PROBS:
    _d = {"context": Path(args.targets).stem, "city": args.city, "seed": args.seed, "n_nodi": N}
    for _i, _b in enumerate(PROBS):
        _d[f"tag{_i}"] = _b["tag"]; _d[f"p{_i}"] = _b["p"]
        _d[f"y{_i}"] = _b["y"]; _d[f"idx{_i}"] = _b["idx"]
    np.savez_compressed(args.dump_probs, **_d)
    print(f"[probs] -> {args.dump_probs} ({len(PROBS)} blocchi)")
