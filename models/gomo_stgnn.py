"""
GO-MO M30 — STGNN harness (PyTorch, Apple-Silicon / MPS ready)  — v2 (HA-residual)
==================================================================================
Trains, on the same inputs and the same chronological split as the baselines:
  * temporal : per-node temporal model, NO graph mixing   (control)
  * graph    : same encoder + graph convolution on the M30 route graph (STGNN)
The difference between the two isolates the value of spatial propagation.

v2: the historical-average (HA) seasonal prior is given to BOTH models as an input,
and (default) the network predicts the RESIDUAL over HA — final = HA + residual.
This levels the field with the LightGBM baseline (which had HA as a feature) and
makes the graph's contribution stand out against the periodic background.

Target: cleaned congestion factor r, horizons [15/30/60/120 min], masked-L1 loss.
Metrics MAE_r / RMSE_r / Traffic4cast macro-F1 / acc — comparable to baselines.

Place in models/. Run:  poetry run python gomo_stgnn.py --model both
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

DATA = Path("../data_collection/go-mo/gomo")
ap = argparse.ArgumentParser(description="GO-MO M30 STGNN harness")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_m30.npz")
ap.add_argument("--graph",   type=Path, default=DATA / "routes-graph.pkl")
ap.add_argument("--sensors", type=Path, default=DATA / "traffic_sensors.csv")
ap.add_argument("--out",     type=Path, default=Path("stgnn_results.csv"))
ap.add_argument("--model", choices=["temporal", "graph", "both"], default="both")
ap.add_argument("--epochs", type=int, default=40)
ap.add_argument("--batch",  type=int, default=64)
ap.add_argument("--hidden", type=int, default=64)
ap.add_argument("--layers", type=int, default=2)
ap.add_argument("--lr", type=float, default=1e-3)
ap.add_argument("--patience", type=int, default=8)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--residual", action="store_true", default=True,
                help="predict residual over the historical-average prior (default)")
ap.add_argument("--no-residual", dest="residual", action="store_false")
ap.add_argument("--device", default=None, help="mps / cpu / cuda (auto if unset)")
args = ap.parse_args()

torch.manual_seed(args.seed); np.random.seed(args.seed)
DEV = (torch.device(args.device) if args.device else
       torch.device("mps" if torch.backends.mps.is_available()
                    else "cuda" if torch.cuda.is_available() else "cpu"))
print("device:", DEV, "| residual:", args.residual)

T_IN = 4
HORIZONS = [1, 2, 4, 8]
H = len(HORIZONS)
T4C_GREEN, T4C_RED = 0.8, 0.4

# ------------------------------------------------------------------- data ---
z = np.load(args.targets, allow_pickle=True)
ts   = pd.to_datetime(z["timestamps"])
r    = z["r_emp"].astype("float32")
flow = z["flow"].astype("float32")
occ  = z["occupancy"].astype("float32")
ff   = z["ff_emp"].astype("float32")
sids = z["sensor_ids"].astype(str)
Tn, S = r.shape

# --- align route graph to target sensors (coordinate match, 20 m) -----------
with open(args.graph, "rb") as f:
    rg = pickle.load(f)
sens = pd.read_csv(args.sensors, dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
tree = cKDTree(sens[["utm_x", "utm_y"]].to_numpy())
nodes = list(rg.nodes)
nxy = np.array([[rg.nodes[n]["utm_x"], rg.nodes[n]["utm_y"]] for n in nodes])
dist, idx = tree.query(nxy, k=1)
node_to_sid = {nodes[i]: sens["id"].to_numpy()[idx[i]] for i in range(len(nodes)) if dist[i] <= 20}
rg = nx.relabel_nodes(rg, node_to_sid, copy=True)

kept = [s for s in sids if s in rg.nodes]
pos = {s: i for i, s in enumerate(sids)}
kidx = np.array([pos[s] for s in kept])
K = len(kept)
_wattr = "distance" if any("distance" in _a for *_, _a in list(rg.edges(data=True))[:50]) else "weight"
A = nx.to_numpy_array(rg.subgraph(kept).copy(), nodelist=kept, weight=_wattr).astype("float32")
A[A > 0] = np.maximum(A[A > 0], 1.0)
print(f"[grafo] attributo: {_wattr} | archi {(A>0).sum()} | mediana {np.median(A[A>0]):.1f}")
print(f"aligned graph: {K} of {S} sensors | adjacency {A.shape}")
r, flow, occ, ff = r[:, kidx], flow[:, kidx], occ[:, kidx], ff[kidx]

# --- normalized affinity  Â ------------------------------------------------
mask = A > 0
sigma = A[mask].std()
Aff = np.where(mask, np.exp(-(A / sigma) ** 2), 0.0).astype("float32")
np.fill_diagonal(Aff, 0.0)
Aff = Aff + np.eye(K, dtype="float32")
d = Aff.sum(1); dinv = 1.0 / np.sqrt(np.maximum(d, 1e-6))
Ahat = torch.tensor((Aff * dinv[:, None]) * dinv[None, :], device=DEV)

# --- split + normalization (train stats) -----------------------------------
starts = np.arange(T_IN - 1, Tn - max(HORIZONS))
n = len(starts)
tr, va, te = starts[:int(n*.7)], starts[int(n*.7):int(n*.8)], starts[int(n*.8):]
tr_region = slice(0, tr[-1] + 1)
def zstats(a):
    v = a[tr_region][np.isfinite(a[tr_region])]
    return float(v.mean()), float(v.std() + 1e-6)
f_mu, f_sd = zstats(flow); o_mu, o_sd = zstats(occ); ff_mu, ff_sd = zstats(ff[None, :])

def T_(a): return torch.tensor(a, device=DEV)
Rvalid = T_(np.isfinite(r).astype("float32"))
Rfill  = T_(np.where(np.isfinite(r), r, 1.0))
FLn    = T_(np.where(np.isfinite(flow), (flow - f_mu) / f_sd, 0.0))
OCn    = T_(np.where(np.isfinite(occ), (occ - o_mu) / o_sd, 0.0))
FFn    = T_(np.nan_to_num((ff - ff_mu) / ff_sd, nan=0.0).astype("float32"))
TF = T_(np.stack([np.sin(2*np.pi*(ts.hour.to_numpy()*4+ts.minute.to_numpy()//15)/96),
                  np.cos(2*np.pi*(ts.hour.to_numpy()*4+ts.minute.to_numpy()//15)/96),
                  np.sin(2*np.pi*ts.dayofweek.to_numpy()/7),
                  np.cos(2*np.pi*ts.dayofweek.to_numpy()/7),
                  (ts.dayofweek.to_numpy() >= 5).astype("float32")], 1).astype("float32"))

# --- historical-average prior (train only), per (sensor, time-of-week slot) --
slot_np = (ts.dayofweek.to_numpy()*96 + ts.hour.to_numpy()*4 + ts.minute.to_numpy()//15)
ha_sum = np.zeros((K, 672)); ha_cnt = np.zeros((K, 672))
tt = np.arange(0, tr[-1] + 1)
rv = r[tt]; v = np.isfinite(rv)
si = np.broadcast_to(np.arange(K), rv.shape); sl = np.broadcast_to(slot_np[tt][:, None], rv.shape)
np.add.at(ha_sum, (si[v], sl[v]), rv[v]); np.add.at(ha_cnt, (si[v], sl[v]), 1)
ha_tab = np.divide(ha_sum, ha_cnt, out=np.full_like(ha_sum, np.nan), where=ha_cnt > 0)
gmean = float(np.nanmean(ha_tab))                              # global fallback
smean = np.nanmean(np.where(np.isfinite(ha_tab), ha_tab, np.nan), 1)
smean = np.where(np.isfinite(smean), smean, gmean)             # sensors empty in train
ha_tab = np.where(np.isfinite(ha_tab), ha_tab, smean[:, None])
ha_tab = np.nan_to_num(ha_tab, nan=gmean).astype("float32")   # safety
HA   = T_(ha_tab)                                   # (K, 672)
SLOT = torch.tensor(slot_np, device=DEV, dtype=torch.long)

DIN = T_IN * 4 + 1 + TF.shape[1] + H                # window + ff + time + HA(per-horizon)

def make_batch(bt):
    bt = torch.as_tensor(bt, device=DEV)
    win = torch.stack([torch.stack([Rfill[bt-k], FLn[bt-k], OCn[bt-k], Rvalid[bt-k]], -1)
                       for k in reversed(range(T_IN))], 1)        # (B,T_IN,K,4)
    B = win.shape[0]
    x = win.permute(0, 2, 1, 3).reshape(B, K, T_IN * 4)
    ha = torch.stack([HA[:, SLOT[bt + h]].transpose(0, 1) for h in HORIZONS], -1)   # (B,K,H)
    x = torch.cat([x, FFn.view(1, K, 1).expand(B, K, 1),
                   TF[bt].view(B, 1, -1).expand(B, K, TF.shape[1]), ha], -1)
    y = torch.stack([Rfill[bt + h] for h in HORIZONS], -1)
    m = torch.stack([Rvalid[bt + h] for h in HORIZONS], -1)
    return x, y, m, ha

# ------------------------------------------------------------------ model ---
class Net(nn.Module):
    def __init__(self, use_graph):
        super().__init__()
        self.use_graph = use_graph
        self.enc = nn.Linear(DIN, args.hidden)
        self.mix = nn.ModuleList(nn.Linear(args.hidden, args.hidden) for _ in range(args.layers))
        self.self_ = nn.ModuleList(nn.Linear(args.hidden, args.hidden) for _ in range(args.layers))
        self.head = nn.Linear(args.hidden, H)
        self.act = nn.ReLU()

    def forward(self, x):
        h = self.act(self.enc(x))
        for mix, slf in zip(self.mix, self.self_):
            upd = slf(h)
            if self.use_graph:
                upd = upd + mix(torch.matmul(Ahat, h))
            h = h + self.act(upd)
        return self.head(h)                                       # (B,K,H) residual or full

def masked_l1(pred, y, m):
    return (torch.abs(pred - y) * m).sum() / m.sum().clamp_min(1)

def train_eval(use_graph, name):
    net = Net(use_graph).to(DEV)
    opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
    best, bad = 1e9, 0
    for ep in range(args.epochs):
        tr_perm = np.random.permutation(tr)
        net.train()
        for i in range(0, len(tr_perm), args.batch):
            x, y, m, ha = make_batch(tr_perm[i:i+args.batch])
            pred = net(x) + ha if args.residual else net(x)
            opt.zero_grad(); masked_l1(pred, y, m).backward(); opt.step()
        net.eval(); num = den = 0.0
        with torch.no_grad():
            for i in range(0, len(va), 256):
                x, y, m, ha = make_batch(va[i:i+256])
                p = net(x) + ha if args.residual else net(x)
                num += (torch.abs(p - y) * m).sum().item(); den += m.sum().item()
        vmae = num / max(den, 1)
        if vmae < best - 1e-5:
            best, best_state, bad = vmae, {k: v.detach().clone() for k, v in net.state_dict().items()}, 0
        else:
            bad += 1
        print(f"[{name}] epoch {ep+1:02d}  val MAE_r={vmae:.4f}  best={best:.4f}")
        if bad >= args.patience:
            print(f"[{name}] early stop"); break
    net.load_state_dict(best_state); net.eval()
    P, Y = [], []
    with torch.no_grad():
        for i in range(0, len(te), 256):
            x, y, m, ha = make_batch(te[i:i+256])
            p = net(x) + ha if args.residual else net(x)
            P.append(p.cpu().numpy()); Y.append(np.where(m.cpu().numpy() > 0, y.cpu().numpy(), np.nan))
    return np.concatenate(P), np.concatenate(Y)

# ---------------------------------------------------------------- metrics ---
def to_cls(rv):
    c = np.full(rv.shape, -1, np.int8); v = np.isfinite(rv)
    c[v & (rv >= T4C_GREEN)] = 1
    c[v & (rv < T4C_GREEN) & (rv >= T4C_RED)] = 2
    c[v & (rv < T4C_RED)] = 3
    return c
def macro_f1(yt, yp):
    out = []
    for k in (1, 2, 3):
        tp = np.sum((yp == k) & (yt == k)); fp = np.sum((yp == k) & (yt != k)); fn = np.sum((yp != k) & (yt == k))
        p = tp/(tp+fp) if tp+fp else 0.0; rc = tp/(tp+fn) if tp+fn else 0.0
        out.append(2*p*rc/(p+rc) if p+rc else 0.0)
    return float(np.mean(out))
def score(yt, yp):
    m = np.isfinite(yt) & np.isfinite(yp); yt, yp = yt[m], np.clip(yp[m], 0, 1.5)
    ct, cp = to_cls(yt), to_cls(yp); vv = (ct > 0) & (cp > 0)
    return (float(np.mean(np.abs(yt-yp))), float(np.sqrt(np.mean((yt-yp)**2))),
            macro_f1(ct[vv], cp[vv]), float(np.mean(ct[vv] == cp[vv])))

# ------------------------------------------------------------------- run ----
runs = {"temporal": False, "graph": True}
todo = runs if args.model == "both" else {args.model: runs[args.model]}
rows = []
for name, ug in todo.items():
    P, Y = train_eval(ug, name)
    for j, h in enumerate(HORIZONS):
        rows.append((name, {1:"15m",2:"30m",4:"60m",8:"120m"}[h],
                     *score(Y[..., j].ravel(), P[..., j].ravel())))

res = pd.DataFrame(rows, columns=["model", "horizon", "MAE_r", "RMSE_r", "macroF1", "acc"])
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== STGNN results (test set) ===")
print(res.to_string(index=False))
res.to_csv(args.out, index=False)
print(f"\nsaved -> {args.out}")
