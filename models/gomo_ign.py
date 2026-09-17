"""
GO-MO — IGN: Inductive-identity Graph Network (research prototype v1)
====================================================================
Replaces the transductive per-node embedding table of AGCRN/GWN with a SHARED
encoder that GENERATES a node's identity embedding from its static road features
(max-speed, lanes, capacity, coordinates, degree) and graph context (neighbour-mean
static). A never-seen sensor gets an embedding on the fly -> no retraining.

Decisive test: split sensors into SEEN (train) and HELD-OUT (never in training, not
even as neighbours). Train on seen only; evaluate on held-out. Compare:
  ign          : inductive encoder -> embedding for any node
  transductive : learned lookup table; held-out nodes fall back to the mean embedding
If IGN on held-out approx IGN on seen and beats transductive on held-out -> SOTA+inductive.

Metric: Traffic4cast weighted CE + red recall. Place in models/. Run:
    poetry run python gomo_ign.py --model both \
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
ap = argparse.ArgumentParser(description="IGN inductive-identity graph network")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_urb_d8.npz")
ap.add_argument("--graph",   type=Path, default=DATA / "routes-graph.pkl")
ap.add_argument("--sensors", type=Path, default=DATA / "traffic_sensors.csv")
ap.add_argument("--out",     type=Path, default=Path("ign_results.csv"))
ap.add_argument("--model", choices=["ign", "transductive", "both"], default="both")
ap.add_argument("--held-frac", type=float, default=0.3, help="fraction of sensors held out (never trained)")
ap.add_argument("--win", type=int, default=12)
ap.add_argument("--hidden", type=int, default=32)
ap.add_argument("--emb", type=int, default=10)
ap.add_argument("--blocks", type=int, default=4)
ap.add_argument("--epochs", type=int, default=30)
ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--lr", type=float, default=1e-3)
ap.add_argument("--patience", type=int, default=8)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--statics", default="all",
                help="lista di statiche separate da virgola, oppure 'all'. "
                     "Disponibili: max_speed,lanes,max_capacity,x,y,degree,road_class,oneway,speed_limit")
ap.add_argument("--device", default=None)
args = ap.parse_args()
torch.manual_seed(args.seed); np.random.seed(args.seed)
DEV = (torch.device(args.device) if args.device else
       torch.device("mps" if torch.backends.mps.is_available()
                    else "cuda" if torch.cuda.is_available() else "cpu"))
print("device:", DEV)
T_IN = args.win; HORIZONS = [1, 2, 4, 8]; H = len(HORIZONS); HL = {1: "15m", 2: "30m", 4: "60m", 8: "120m"}
DEMB = args.emb

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
smeta = sens.set_index("id")
coords = smeta.loc[kept, ["utm_x", "utm_y"]].to_numpy(float)
maxspd = pd.to_numeric(smeta.loc[kept, "max_speed"], errors="coerce").to_numpy()
lanes = pd.to_numeric(smeta.loc[kept, "lanes"], errors="coerce").to_numpy()
cap = pd.to_numeric(smeta.loc[kept, "max_capacity"], errors="coerce").to_numpy()
degree = (Araw > 0).sum(1).astype("float64")
# colonne statiche opzionali (presenti negli artefatti t4c con attributi OSM)
EXTRA, EXTRA_NAMES = [], []
for col in ("road_class", "oneway", "speed_limit"):
    if col in smeta.columns:
        EXTRA.append(pd.to_numeric(smeta.loc[kept, col], errors="coerce").to_numpy()); EXTRA_NAMES.append(col)
if EXTRA: print(f"feature statiche extra da OSM: {', '.join(EXTRA_NAMES)}")
print(f"aligned graph: {N} of {S} sensors")

# --- node holdout: reorder [seen..., held...] -------------------------------
rng = np.random.default_rng(args.seed)
perm = rng.permutation(N); nh = int(round(args.held_frac * N)); ns = N - nh
seen_pos, held_pos = perm[:ns], perm[ns:]
order = np.concatenate([seen_pos, held_pos])                          # new node order
r, flow, occ, C = r[:, order], flow[:, order], occ[:, order], C[:, order]
Araw = Araw[np.ix_(order, order)]
coords, maxspd, lanes, cap, degree = coords[order], maxspd[order], lanes[order], cap[order], degree[order]
EXTRA = [e[order] for e in EXTRA]        # BUGFIX: anche le statiche extra vanno permutate
SEEN = slice(0, ns); HELD = slice(ns, N)
print(f"node holdout: {ns} seen (train), {nh} held-out (never trained)")

def norm_adj(A):
    m = A > 0; sg = A[m].std() if m.any() else 1.0
    Aff = np.where(m, np.exp(-(A/sg)**2), 0.0).astype("float32"); np.fill_diagonal(Aff, 1.0)
    d = Aff.sum(1); di = 1/np.sqrt(np.maximum(d, 1e-6)); return (Aff*di[:, None])*di[None, :]
A_full = torch.tensor(norm_adj(Araw), device=DEV)
A_seen = torch.tensor(norm_adj(Araw[:ns, :ns]), device=DEV)

# static features (z-scored on SEEN nodes only, to avoid leakage)
def zsc(a):
    mu, sd = np.nanmean(a[:ns]), np.nanstd(a[:ns]) + 1e-6
    return np.nan_to_num((a - mu)/sd, nan=0.0).astype("float32")
_named = {"max_speed": maxspd, "lanes": lanes, "max_capacity": cap,
          "x": coords[:, 0], "y": coords[:, 1], "degree": degree}
for nm, arr in zip(EXTRA_NAMES, EXTRA): _named[nm] = arr
_use = [c.strip() for c in args.statics.split(",")] if args.statics != "all" else list(_named)
_missing = [c for c in _use if c not in _named]
if _missing: raise SystemExit(f"statiche non disponibili: {_missing}. Disponibili: {list(_named)}")
print(f"statiche usate ({len(_use)}): {', '.join(_use)}")
_cols = [zsc(_named[c]) for c in _use]
STATIC = torch.tensor(np.stack(_cols, 1), device=DEV)                # (N, 6+extra)
SDIM = STATIC.shape[1]

starts = np.arange(T_IN - 1, Tn - max(HORIZONS)); n = len(starts)
tr, va, te = starts[:int(n*.7)], starts[int(n*.7):int(n*.8)], starts[int(n*.8):]
reg = slice(0, tr[-1] + 1); ctr = C[reg, :ns]
freq = np.array([(ctr == k).sum() for k in (1, 2, 3)], dtype="float64")
Wnp = (freq.sum() / (np.maximum(freq, 1)*3)).astype("float32")
print(f"class freq g/y/r (seen) = {(freq/freq.sum()).round(3)} | T4c weights = {Wnp.round(2)}")

def zst(a): v = a[reg][np.isfinite(a[reg])]; return float(v.mean()), float(v.std() + 1e-6)
fmu, fsd = zst(flow[:, :ns]); omu, osd = zst(occ[:, :ns])
def T_(a): return torch.tensor(a, device=DEV)
Rfill = T_(np.where(np.isfinite(r), r, 1.0)); FLn = T_(np.where(np.isfinite(flow), (flow-fmu)/fsd, 0.0))
OCn = T_(np.where(np.isfinite(occ), (occ-omu)/osd, 0.0))
q = (ts.hour.to_numpy()*4 + ts.minute.to_numpy()//15)/96.0
TODs = T_(np.sin(2*np.pi*q).astype("float32")); TODc = T_(np.cos(2*np.pi*q).astype("float32"))
DOWs = T_(np.sin(2*np.pi*ts.dayofweek.to_numpy()/7).astype("float32"))
DOWc = T_(np.cos(2*np.pi*ts.dayofweek.to_numpy()/7).astype("float32"))
WKND = T_((ts.dayofweek.to_numpy() >= 5).astype("float32"))
Cy = T_(np.where(C > 0, C - 1, 0).astype("int64")); Cm = T_((C > 0).astype("float32")); Wt = T_(Wnp)
C_DYN = 8                                                             # r,flow,occ + 5 temporal (NO HAser: held-out have no history)

def make_batch(bt, nodes):                                           # nodes: slice/array of node indices
    bt = torch.as_tensor(bt, device=DEV); B = len(bt); nn_ = (nodes.stop - nodes.start) if isinstance(nodes, slice) else len(nodes)
    def wn(M): return torch.stack([M[bt-k][:, nodes] for k in reversed(range(T_IN))], -1)   # (B,n,T)
    def wg(g):
        wi = torch.stack([g[bt-k] for k in reversed(range(T_IN))], -1); return wi.unsqueeze(1).expand(-1, nn_, -1)
    x = torch.stack([wn(Rfill), wn(FLn), wn(OCn), wg(TODs), wg(TODc), wg(DOWs), wg(DOWc), wg(WKND)], 1)  # (B,8,n,T)
    y = torch.stack([Cy[bt+h][:, nodes] for h in HORIZONS], -1); m = torch.stack([Cm[bt+h][:, nodes] for h in HORIZONS], -1)
    return x, y, m

# ------------------------------------------------------------- shared backbone ---
class GTCN(nn.Module):
    def __init__(s, c, k, d): super().__init__(); s.pad=(k-1)*d; s.f=nn.Conv2d(c, c, (1, k), dilation=(1, d)); s.g=nn.Conv2d(c, c, (1, k), dilation=(1, d))
    def forward(s, x): x=F.pad(x, (s.pad, 0)); return torch.tanh(s.f(x))*torch.sigmoid(s.g(x))
class GCN(nn.Module):
    def __init__(s, c, order=2): super().__init__(); s.order=order; s.mlp=nn.Conv2d(c*(order*2+1), c, (1, 1))
    def forward(s, x, sup):
        out=[x]
        for A in sup:
            xk=x
            for _ in range(s.order): xk=torch.einsum("nm,bcmt->bcnt", A, xk); out.append(xk)
        return s.mlp(torch.cat(out, 1))
class Block(nn.Module):
    def __init__(s, c, d): super().__init__(); s.tcn=GTCN(c, 2, d); s.gcn=GCN(c); s.skip=nn.Conv2d(c, c, (1, 1)); s.bn=nn.BatchNorm2d(c)
    def forward(s, x, sup): res=x; x=s.tcn(x); sk=s.skip(x); x=s.gcn(x, sup); return s.bn(x+res), sk
class Backbone(nn.Module):
    def __init__(s):
        super().__init__(); s.start=nn.Conv2d(C_DYN+DEMB, args.hidden, (1, 1))
        d=1; s.blocks=nn.ModuleList()
        for _ in range(args.blocks): s.blocks.append(Block(args.hidden, d)); d*=2
        s.e1=nn.Conv2d(args.hidden, args.hidden, (1, 1)); s.e2=nn.Conv2d(args.hidden, H*3, (1, 1))
    def forward(s, x, A, E):                                          # x (B,C,n,T), A (n,n), E (n,DEMB)
        B, _, nnodes, T = x.shape
        ech = E.t().view(1, DEMB, nnodes, 1).expand(B, DEMB, nnodes, T)
        x = s.start(torch.cat([x, ech], 1))
        Aadp = F.softmax(F.relu(E @ E.t()), dim=1); sup = [A, Aadp]; skip = 0
        for b in s.blocks: x, sk = b(x, sup); skip = skip + sk[..., -1:]
        h = F.relu(s.e1(F.relu(skip)))
        return s.e2(h).squeeze(-1).permute(0, 2, 1).contiguous().reshape(B, nnodes, H, 3)

class InductiveEncoder(nn.Module):                                   # static + neighbour-mean -> embedding
    def __init__(s): super().__init__(); s.l1=nn.Linear(SDIM*2, 64); s.l2=nn.Linear(64, DEMB)
    def forward(s, static, A): nbr = A @ static; return s.l2(F.relu(s.l1(torch.cat([static, nbr], -1))))

def loss_fn(lg, y, m):
    lp = F.log_softmax(lg, -1); nll = -lp.gather(-1, y.unsqueeze(-1)).squeeze(-1)
    return (nll*Wt[y]*m).sum()/(Wt[y]*m).sum().clamp_min(1)

def scores(P, Y):
    P = P.reshape(-1, 3); Y = Y.reshape(-1); v = Y >= 0; P, Y = P[v], Y[v]
    if len(Y) == 0: return np.nan, np.nan, np.nan
    pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1); wce = float(np.sum(Wnp[Y]*-np.log(pt))/np.sum(Wnp[Y]))
    pred = P.argmax(1); f1 = []
    for k in range(3):
        tp = np.sum((pred == k) & (Y == k)); fp = np.sum((pred == k) & (Y != k)); fn = np.sum((pred != k) & (Y == k))
        pr = tp/(tp+fp) if tp+fp else 0; rc = tp/(tp+fn) if tp+fn else 0
        f1.append(2*pr*rc/(pr+rc) if pr+rc else 0)
    return wce, float(np.mean(f1)), float(np.sum((pred == 2) & (Y == 2))/max(np.sum(Y == 2), 1))

def train_eval(mode):
    bb = Backbone().to(DEV)
    enc = InductiveEncoder().to(DEV) if mode == "ign" else None
    emb = None if mode == "ign" else nn.Parameter(torch.randn(ns, DEMB, device=DEV)*0.05)
    params = list(bb.parameters()) + (list(enc.parameters()) if enc else [emb])
    opt = torch.optim.Adam(params, lr=args.lr)
    def E_seen():  return enc(STATIC[:ns], A_seen) if mode == "ign" else emb
    def E_full():
        if mode == "ign": return enc(STATIC, A_full)
        return torch.cat([emb, emb.mean(0, keepdim=True).expand(nh, DEMB)], 0)   # held-out -> mean fallback
    best = 1e9; bs = None; bad = 0
    for ep in range(args.epochs):
        bb.train();
        if enc: enc.train()
        perm_ = np.random.permutation(tr)
        for i in range(0, len(perm_), args.batch):
            x, y, m = make_batch(perm_[i:i+args.batch], SEEN)
            opt.zero_grad(); loss_fn(bb(x, A_seen, E_seen()), y, m).backward()
            torch.nn.utils.clip_grad_norm_(params, 5.0); opt.step()
        bb.eval();
        if enc: enc.eval()
        num = den = 0.0
        with torch.no_grad():
            for i in range(0, len(va), 128):
                x, y, m = make_batch(va[i:i+128], SEEN); num += loss_fn(bb(x, A_seen, E_seen()), y, m).item()*m.sum().item(); den += m.sum().item()
        v = num/max(den, 1)
        state = {"bb": {k: t.detach().clone() for k, t in bb.state_dict().items()}}
        if enc: state["enc"] = {k: t.detach().clone() for k, t in enc.state_dict().items()}
        else: state["emb"] = emb.detach().clone()
        if v < best-1e-5: best, bs, bad = v, state, 0
        else: bad += 1
        print(f"[{mode}] epoch {ep+1:02d}  val wCE(seen)={v:.4f}  best={best:.4f}")
        if bad >= args.patience: print(f"[{mode}] early stop"); break
    bb.load_state_dict(bs["bb"]);
    if enc: enc.load_state_dict(bs["enc"])
    else: emb.data = bs["emb"]
    bb.eval();
    if enc: enc.eval()
    # eval on FULL node set, split seen-test vs held-out
    Ps, Ph, Ys, Yh = [], [], [], []
    with torch.no_grad():
        Ef = E_full()
        for i in range(0, len(te), 128):
            x, y, m = make_batch(te[i:i+128], slice(0, N))
            P = F.softmax(bb(x, A_full, Ef), -1).cpu().numpy(); Yv = np.where(m.cpu().numpy() > 0, y.cpu().numpy(), -1)
            Ps.append(P[:, :ns]); Ph.append(P[:, ns:]); Ys.append(Yv[:, :ns]); Yh.append(Yv[:, ns:])
    return (np.concatenate(Ps), np.concatenate(Ys)), (np.concatenate(Ph), np.concatenate(Yh))

rows = []
for mode in (["ign", "transductive"] if args.model == "both" else [args.model]):
    (Ps, Ys), (Ph, Yh) = train_eval(mode)
    for split, (P, Y) in [("seen", (Ps, Ys)), ("held-out", (Ph, Yh))]:
        for j, h in enumerate(HORIZONS):
            rows.append((mode, split, HL[h], *scores(P[..., j, :], Y[..., j])))
res = pd.DataFrame(rows, columns=["model", "split", "horizon", "wCE", "macroF1", "red_recall"])
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== IGN vs transductive — weighted-CE (seen vs HELD-OUT sensors) ===")
print(res.to_string(index=False))
# headline: held-out gap
for mode in res["model"].unique():
    h = res[(res.model == mode) & (res.split == "held-out")]["wCE"].mean()
    s = res[(res.model == mode) & (res.split == "seen")]["wCE"].mean()
    print(f"{mode:12s}  seen wCE={s:.4f}  held-out wCE={h:.4f}  gap={h-s:+.4f}")
res.to_csv(args.out, index=False); print(f"saved -> {args.out}")
