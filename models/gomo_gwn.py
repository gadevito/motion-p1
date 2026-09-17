"""
GO-MO — Graph WaveNet harness (PyTorch, MPS)   — the real spatial-model test
============================================================================
Upgrades over the toy STGNN: dilated gated temporal convolutions over a LONGER
window, and a LEARNED adaptive adjacency (Graph WaveNet). Runs several graph modes
on the same input/split so any gain is attributed to the graph:
    none      : dilated-TCN only (no spatial mixing)      — strong temporal control
    fixed     : + distance-based route-graph adjacency
    adaptive  : + learned adjacency (node embeddings)
    both      : fixed + adaptive
Keeps the HA-residual target (final = HA + residual) and the same metrics as the
baselines / STGNN, so results drop straight into the comparison tables.

Place in models/. Run:
    poetry run python gomo_gwn.py --targets ../data_collection/go-mo/gomo/targets_2024_urb_d8.npz
Needs: torch, networkx, scipy
"""
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
ap = argparse.ArgumentParser(description="GO-MO Graph WaveNet harness")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_m30.npz")
ap.add_argument("--graph",   type=Path, default=DATA / "routes-graph.pkl")
ap.add_argument("--sensors", type=Path, default=DATA / "traffic_sensors.csv")
ap.add_argument("--out",     type=Path, default=Path("gwn_results.csv"))
ap.add_argument("--modes", default="none,fixed,adaptive",
                help="comma list of graph modes to run: none/fixed/adaptive/both")
ap.add_argument("--win", type=int, default=12)          # input steps (3 h)
ap.add_argument("--hidden", type=int, default=32)
ap.add_argument("--blocks", type=int, default=4)
ap.add_argument("--epochs", type=int, default=50)
ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--lr", type=float, default=1e-3)
ap.add_argument("--patience", type=int, default=10)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--device", default=None)
args = ap.parse_args()

torch.manual_seed(args.seed); np.random.seed(args.seed)
DEV = (torch.device(args.device) if args.device else
       torch.device("mps" if torch.backends.mps.is_available()
                    else "cuda" if torch.cuda.is_available() else "cpu"))
print("device:", DEV)

T_IN = args.win
HORIZONS = [1, 2, 4, 8]; H = len(HORIZONS)
T4C_GREEN, T4C_RED = 0.8, 0.4

# ------------------------------------------------------------------- data ---
z = np.load(args.targets, allow_pickle=True)
ts = pd.to_datetime(z["timestamps"])
r, flow, occ = z["r_emp"].astype("float32"), z["flow"].astype("float32"), z["occupancy"].astype("float32")
sids = z["sensor_ids"].astype(str); Tn, S = r.shape

with open(args.graph, "rb") as f:
    rg = pickle.load(f)
sens = pd.read_csv(args.sensors, dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
tree = cKDTree(sens[["utm_x", "utm_y"]].to_numpy())
nodes = list(rg.nodes)
nxy = np.array([[rg.nodes[n]["utm_x"], rg.nodes[n]["utm_y"]] for n in nodes])
dist, idx = tree.query(nxy, k=1)
rg = nx.relabel_nodes(rg, {nodes[i]: sens["id"].to_numpy()[idx[i]] for i in range(len(nodes)) if dist[i] <= 20}, copy=True)
kept = [s for s in sids if s in rg.nodes]; pos = {s: i for i, s in enumerate(sids)}
kidx = np.array([pos[s] for s in kept]); K = len(kept)
_wattr = "distance" if any("distance" in _a for *_, _a in list(rg.edges(data=True))[:50]) else "weight"
Araw = nx.to_numpy_array(rg.subgraph(kept).copy(), nodelist=kept, weight=_wattr).astype("float32")
Araw[Araw > 0] = np.maximum(Araw[Araw > 0], 1.0)
print(f"[grafo] attributo: {_wattr} | archi {(Araw>0).sum()} | mediana {np.median(Araw[Araw>0]):.1f}")
print(f"aligned graph: {K} of {S} sensors")
r, flow, occ = r[:, kidx], flow[:, kidx], occ[:, kidx]

# fixed normalized affinity
mask = Araw > 0; sigma = Araw[mask].std()
Aff = np.where(mask, np.exp(-(Araw / sigma) ** 2), 0.0).astype("float32"); np.fill_diagonal(Aff, 0.0)
Aff = Aff + np.eye(K, dtype="float32"); d = Aff.sum(1); di = 1 / np.sqrt(np.maximum(d, 1e-6))
A_fixed = torch.tensor((Aff * di[:, None]) * di[None, :], device=DEV)

# split + norm
starts = np.arange(T_IN - 1, Tn - max(HORIZONS))
n = len(starts); tr, va, te = starts[:int(n*.7)], starts[int(n*.7):int(n*.8)], starts[int(n*.8):]
reg = slice(0, tr[-1] + 1)
def zst(a): v = a[reg][np.isfinite(a[reg])]; return float(v.mean()), float(v.std() + 1e-6)
fmu, fsd = zst(flow); omu, osd = zst(occ)

def T_(a): return torch.tensor(a, device=DEV)
Rval = T_(np.isfinite(r).astype("float32"))
Rfill = T_(np.where(np.isfinite(r), r, 1.0))
FLn = T_(np.where(np.isfinite(flow), (flow - fmu) / fsd, 0.0))
OCn = T_(np.where(np.isfinite(occ), (occ - omu) / osd, 0.0))
q = (ts.hour.to_numpy() * 4 + ts.minute.to_numpy() // 15) / 96.0
TODs = T_(np.sin(2 * np.pi * q).astype("float32")); TODc = T_(np.cos(2 * np.pi * q).astype("float32"))

# HA prior (train only)
slot = (ts.dayofweek.to_numpy() * 96 + ts.hour.to_numpy() * 4 + ts.minute.to_numpy() // 15)
hs = np.zeros((K, 672)); hc = np.zeros((K, 672)); tt = np.arange(0, tr[-1] + 1)
rv = r[tt]; vv = np.isfinite(rv)
si = np.broadcast_to(np.arange(K), rv.shape); sl = np.broadcast_to(slot[tt][:, None], rv.shape)
np.add.at(hs, (si[vv], sl[vv]), rv[vv]); np.add.at(hc, (si[vv], sl[vv]), 1)
ht = np.divide(hs, hc, out=np.full_like(hs, np.nan), where=hc > 0)
gm = float(np.nanmean(ht)); sm = np.nanmean(np.where(np.isfinite(ht), ht, np.nan), 1)
sm = np.where(np.isfinite(sm), sm, gm); ht = np.nan_to_num(np.where(np.isfinite(ht), ht, sm[:, None]), nan=gm)
HA = T_(ht.astype("float32")); SLOT = torch.tensor(slot, device=DEV, dtype=torch.long)
HAser = HA[:, SLOT].transpose(0, 1).contiguous()            # (T,K) seasonal prior trajectory
DOWs = T_(np.sin(2*np.pi*ts.dayofweek.to_numpy()/7).astype("float32"))
DOWc = T_(np.cos(2*np.pi*ts.dayofweek.to_numpy()/7).astype("float32"))
WKND = T_((ts.dayofweek.to_numpy() >= 5).astype("float32"))
DEMB = 8                                                     # per-node identity embedding
C_IN = 9                                                     # r,flow,occ,HAser,tod_s,tod_c,dow_s,dow_c,wknd

def make_batch(bt):
    bt = torch.as_tensor(bt, device=DEV); B = len(bt)
    def wn(M):   # per-node (T,K) -> (B,K,T)
        return torch.stack([M[bt - k] for k in reversed(range(T_IN))], -1)
    def wg(g):   # global (T,) -> (B,K,T)
        win = torch.stack([g[bt - k] for k in reversed(range(T_IN))], -1)           # (B,T)
        return win.unsqueeze(1).expand(-1, K, -1)
    x = torch.stack([wn(Rfill), wn(FLn), wn(OCn), wn(HAser),
                     wg(TODs), wg(TODc), wg(DOWs), wg(DOWc), wg(WKND)], 1)           # (B,9,K,T)
    ha = torch.stack([HA[:, SLOT[bt + h]].transpose(0, 1) for h in HORIZONS], -1)    # (B,K,H)
    y = torch.stack([Rfill[bt + h] for h in HORIZONS], -1)
    m = torch.stack([Rval[bt + h] for h in HORIZONS], -1)
    return x, y, m, ha

# ------------------------------------------------------------- Graph WaveNet ---
class GTCN(nn.Module):
    def __init__(self, c, k, dil):
        super().__init__(); self.pad = (k - 1) * dil
        self.f = nn.Conv2d(c, c, (1, k), dilation=(1, dil))
        self.g = nn.Conv2d(c, c, (1, k), dilation=(1, dil))
    def forward(self, x):
        x = F.pad(x, (self.pad, 0))
        return torch.tanh(self.f(x)) * torch.sigmoid(self.g(x))

class GCN(nn.Module):
    def __init__(self, c, n_sup, order=2):
        super().__init__(); self.order = order
        self.mlp = nn.Conv2d(c * (order * n_sup + 1), c, (1, 1))
    def forward(self, x, sup):
        out = [x]
        for A in sup:
            xk = x
            for _ in range(self.order):
                xk = torch.einsum("nm,bcmt->bcnt", A, xk); out.append(xk)
        return self.mlp(torch.cat(out, 1))

class Block(nn.Module):
    def __init__(self, c, dil, n_sup):
        super().__init__(); self.tcn = GTCN(c, 2, dil)
        self.gcn = GCN(c, n_sup) if n_sup > 0 else None
        self.skip = nn.Conv2d(c, c, (1, 1)); self.bn = nn.BatchNorm2d(c)
    def forward(self, x, sup):
        res = x; x = self.tcn(x); s = self.skip(x)
        x = self.gcn(x, sup) if self.gcn is not None else x
        return self.bn(x + res), s

class GWN(nn.Module):
    def __init__(self, mode):
        super().__init__(); self.mode = mode
        self.n_sup = (mode in ("fixed", "both")) + (mode in ("adaptive", "both"))
        self.emb = nn.Parameter(torch.randn(K, DEMB) * 0.05)         # node identity (all modes)
        self.start = nn.Conv2d(C_IN + DEMB, args.hidden, (1, 1))
        if mode in ("adaptive", "both"):
            self.E1 = nn.Parameter(torch.randn(K, 10) * 0.05)
            self.E2 = nn.Parameter(torch.randn(K, 10) * 0.05)
        dil = 1; self.blocks = nn.ModuleList()
        for _ in range(args.blocks):
            self.blocks.append(Block(args.hidden, dil, self.n_sup)); dil *= 2
        self.e1 = nn.Conv2d(args.hidden, args.hidden, (1, 1))
        self.e2 = nn.Conv2d(args.hidden, H, (1, 1))
    def supports(self):
        S = []
        if self.mode in ("fixed", "both"): S.append(A_fixed)
        if self.mode in ("adaptive", "both"):
            S.append(F.softmax(F.relu(self.E1 @ self.E2.t()), dim=1))
        return S
    def forward(self, x):
        B, _, N, T = x.shape
        e = self.emb.t().view(1, DEMB, N, 1).expand(B, DEMB, N, T)
        x = self.start(torch.cat([x, e], 1)); sup = self.supports(); skip = 0
        for b in self.blocks:
            x, s = b(x, sup); skip = skip + s[..., -1:]
        h = F.relu(self.e1(F.relu(skip)))
        return self.e2(h).squeeze(-1).permute(0, 2, 1)      # (B,K,H) residual

def train_eval(mode):
    net = GWN(mode).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    best = 1e9; best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}; bad = 0
    for ep in range(args.epochs):
        net.train(); perm = np.random.permutation(tr)
        for i in range(0, len(perm), args.batch):
            x, y, m, ha = make_batch(perm[i:i + args.batch])
            loss = (torch.abs(net(x) + ha - y) * m).sum() / m.sum().clamp_min(1)
            opt.zero_grad(); loss.backward(); opt.step()
        net.eval(); num = den = 0.0
        with torch.no_grad():
            for i in range(0, len(va), 256):
                x, y, m, ha = make_batch(va[i:i + 256]); p = net(x) + ha
                num += (torch.abs(p - y) * m).sum().item(); den += m.sum().item()
        vmae = num / max(den, 1)
        if vmae < best - 1e-5: best, best_state, bad = vmae, {k: v.detach().clone() for k, v in net.state_dict().items()}, 0
        else: bad += 1
        print(f"[{mode}] epoch {ep+1:02d}  val MAE_r={vmae:.4f}  best={best:.4f}")
        if bad >= args.patience: print(f"[{mode}] early stop"); break
    net.load_state_dict(best_state); net.eval()
    P, Y = [], []
    with torch.no_grad():
        for i in range(0, len(te), 256):
            x, y, m, ha = make_batch(te[i:i + 256]); p = net(x) + ha
            P.append(p.cpu().numpy()); Y.append(np.where(m.cpu().numpy() > 0, y.cpu().numpy(), np.nan))
    return np.concatenate(P), np.concatenate(Y)

# ---------------------------------------------------------------- metrics ---
def cls(rv):
    c = np.full(rv.shape, -1, np.int8); v = np.isfinite(rv)
    c[v & (rv >= T4C_GREEN)] = 1; c[v & (rv < T4C_GREEN) & (rv >= T4C_RED)] = 2; c[v & (rv < T4C_RED)] = 3
    return c
def f1(yt, yp):
    o = []
    for k in (1, 2, 3):
        tp = np.sum((yp == k) & (yt == k)); fp = np.sum((yp == k) & (yt != k)); fn = np.sum((yp != k) & (yt == k))
        p = tp/(tp+fp) if tp+fp else 0; rc = tp/(tp+fn) if tp+fn else 0
        o.append(2*p*rc/(p+rc) if p+rc else 0)
    return float(np.mean(o))
def score(yt, yp):
    m = np.isfinite(yt) & np.isfinite(yp); yt, yp = yt[m], np.clip(yp[m], 0, 1.5)
    ct, cp = cls(yt), cls(yp); vv = (ct > 0) & (cp > 0)
    return float(np.mean(np.abs(yt-yp))), float(np.sqrt(np.mean((yt-yp)**2))), f1(ct[vv], cp[vv]), float(np.mean(ct[vv] == cp[vv]))

rows = []
for mode in [m.strip() for m in args.modes.split(",")]:
    P, Y = train_eval(mode)
    for j, h in enumerate(HORIZONS):
        rows.append((mode, {1:"15m",2:"30m",4:"60m",8:"120m"}[h], *score(Y[..., j].ravel(), P[..., j].ravel())))
res = pd.DataFrame(rows, columns=["mode", "horizon", "MAE_r", "RMSE_r", "macroF1", "acc"])
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== Graph WaveNet results (test set) ===")
print(res.to_string(index=False))
res.to_csv(args.out, index=False); print(f"\nsaved -> {args.out}")
