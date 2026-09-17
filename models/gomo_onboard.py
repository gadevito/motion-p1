"""
GO-MO — Amortized sensor onboarding (research prototype v2)
===========================================================
v1 (gomo_ign.py) measured the zero-history point: static features alone recover
almost none of a node's identity (held-out wCE ~1.0 vs ~0.7 seen). The identity is
HISTORICAL. v2 therefore generates the embedding from statics + a SUMMARY OF THE
NODE'S OBSERVED HISTORY (0h .. weeks), trained with history-length dropout so ONE
model covers the whole spectrum. Zero gradient steps at deployment: a new sensor
streams, and after L hours the encoder produces its identity from those L hours.

Output: the ONBOARDING CURVE — held-out wCE / red recall at L in {0h,1h,4h,24h,1wk}.
Success criterion (pre-registered): at 24h the held-out gap to veteran level must
close by >=70%; otherwise the model line is dropped.

Place in models/. Run:
    poetry run python gomo_onboard.py \
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
ap = argparse.ArgumentParser(description="Amortized sensor onboarding (history-encoder)")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_urb_d8.npz")
ap.add_argument("--graph",   type=Path, default=DATA / "routes-graph.pkl")
ap.add_argument("--sensors", type=Path, default=DATA / "traffic_sensors.csv")
ap.add_argument("--out",     type=Path, default=Path("onboard_results.csv"))
ap.add_argument("--held-frac", type=float, default=0.3)
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
ap.add_argument("--hist-dim", type=int, default=0, help="override di HDIM (0 = default del modo): controllo di capacita")
ap.add_argument("--hist-mode", choices=["summary", "profile", "both"], default="summary",
                help="profile = mini-profilo orario della finestra (esperimento B)")
args = ap.parse_args()
torch.manual_seed(args.seed); np.random.seed(args.seed)
DEV = (torch.device(args.device) if args.device else
       torch.device("mps" if torch.backends.mps.is_available()
                    else "cuda" if torch.cuda.is_available() else "cpu"))
print("device:", DEV)
T_IN = args.win; HORIZONS = [1, 2, 4, 8]; H = len(HORIZONS); HL = {1: "15m", 2: "30m", 4: "60m", 8: "120m"}
DEMB = args.emb
LSET = [0, 4, 16, 96, 672, -1]                 # history lengths for dropout (-1 = full)
LCURVE = [(0, "0h"), (4, "1h"), (16, "4h"), (96, "24h"), (672, "1wk")]

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
if not (set(map(str, rg.nodes)) >= set(map(str, sids))):
    rg = nx.relabel_nodes(rg, {nodes[i]: sens["id"].to_numpy()[idx[i]] for i in range(len(nodes)) if dist[i] <= 20}, copy=True)
else:
    print("nodi del grafo = id sensore: aggancio spaziale saltato")
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

# node holdout: [seen..., held...]
rngg = np.random.default_rng(args.seed)
perm = rngg.permutation(N); nh = int(round(args.held_frac*N)); ns = N - nh
order = np.concatenate([perm[:ns], perm[ns:]])
r, flow, occ, C = r[:, order], flow[:, order], occ[:, order], C[:, order]
Araw = Araw[np.ix_(order, order)]
coords, maxspd, lanes, cap, degree = coords[order], maxspd[order], lanes[order], cap[order], degree[order]
EXTRA = [e[order] for e in EXTRA]        # BUGFIX: anche le statiche extra vanno permutate
SEEN = slice(0, ns)
print(f"node holdout: {ns} seen (train), {nh} held-out (never trained)")

def norm_adj(A):
    m = A > 0; sg = A[m].std() if m.any() else 1.0
    Aff = np.where(m, np.exp(-(A/sg)**2), 0.0).astype("float32"); np.fill_diagonal(Aff, 1.0)
    d = Aff.sum(1); di = 1/np.sqrt(np.maximum(d, 1e-6)); return (Aff*di[:, None])*di[None, :]
A_full = torch.tensor(norm_adj(Araw), device=DEV)
A_seen = torch.tensor(norm_adj(Araw[:ns, :ns]), device=DEV)
A_row = norm_adj(Araw)                                             # numpy, for neighbour-mean statics

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
STAT = np.stack(_cols, 1)                                            # (N, 6+extra)
NBR = (A_row @ STAT).astype("float32")
SDIM = STAT.shape[1]; HDIM = args.hist_dim if args.hist_dim > 0 else {"summary": 8, "profile": 10, "both": 16}[args.hist_mode]   # hist dims
ENC_IN = SDIM*2 + HDIM

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
C_DYN = 8

# --- padded cumsums for O(1) windowed history summaries (numpy, CPU) ---------
def padcs(a, msk):
    a0 = np.where(msk, a, 0.0).astype("float64")
    return (np.concatenate([np.zeros((1, N)), np.cumsum(a0, 0)]),
            np.concatenate([np.zeros((1, N)), np.cumsum(a0**2, 0)]),
            np.concatenate([np.zeros((1, N)), np.cumsum(msk.astype("float64"), 0)]))
CSr, CSr2, CNr = padcs(r, np.isfinite(r))
CSf, CSf2, CNf = padcs(flow, np.isfinite(flow))
CSo, CSo2, CNo = padcs(occ, np.isfinite(occ))
if args.hist_mode in ("profile", "both"):
    _hb = (ts.hour.to_numpy() // 3)                       # 8 fasce da 3 ore
    CSB, CNB = [], []
    for _k in range(8):
        _mk = np.isfinite(r) & (_hb[:, None] == _k)
        _a0 = np.where(_mk, r, 0.0)
        CSB.append(np.concatenate([np.zeros((1, N)), np.cumsum(_a0, 0)]))
        CNB.append(np.concatenate([np.zeros((1, N)), np.cumsum(_mk.astype("float64"), 0)]))

def hist_profile(bt, L):
    B = len(bt); b = bt + 1
    a = np.zeros_like(b) if L == -1 else np.maximum(b - L, 0)
    out = np.zeros((B, N, 10), dtype="float32")
    mu, sd = F_MU["r"]
    sr = CSr[b] - CSr[a]; cr = np.maximum(CNr[b] - CNr[a], 1)
    out[..., 0] = (((sr / cr) - mu) / sd).astype("float32")
    Lw = (b - a).astype("float64")[:, None]
    out[..., 1] = ((CNr[b] - CNr[a]) / np.maximum(Lw, 1)).astype("float32")
    for k in range(8):
        sb = CSB[k][b] - CSB[k][a]; cb = CNB[k][b] - CNB[k][a]
        mband = np.where(cb > 0, sb / np.maximum(cb, 1), mu)      # fascia non osservata -> media globale
        out[..., 2 + k] = ((mband - mu) / sd).astype("float32")
    return out

def hist_bands(bt, L):
    """(B,N,8): mini-profilo orario di r sulla finestra (8 fasce da 3 ore)."""
    B = len(bt); b = bt + 1
    a = np.zeros_like(b) if L == -1 else np.maximum(b - L, 0)
    mu, sd = F_MU["r"]
    out = np.zeros((B, N, 8), dtype="float32")
    for k in range(8):
        sb = CSB[k][b] - CSB[k][a]; cb = CNB[k][b] - CNB[k][a]
        mband = np.where(cb > 0, sb / np.maximum(cb, 1), mu)
        out[..., k] = ((mband - mu) / sd).astype("float32")
    return out
F_MU = {"r": (np.nanmean(r[reg, :ns]), np.nanstd(r[reg, :ns]) + 1e-6),
        "f": (fmu, fsd), "o": (omu, osd)}

def hist_summary(bt, L):
    """(B,N,8) summary of window (t-L, t] per node. L=0 -> zeros; L=-1 -> full."""
    B = len(bt)
    if L == 0: return np.zeros((B, N, HDIM), dtype="float32")
    if args.hist_mode == "profile": return hist_profile(bt, L)
    b = bt + 1; a = np.zeros_like(b) if L == -1 else np.maximum(b - L, 0)
    out = np.zeros((B, N, HDIM), dtype="float32")
    for j, (CS, CS2, CN, key) in enumerate([(CSr, CSr2, CNr, "r"), (CSf, CSf2, CNf, "f"), (CSo, CSo2, CNo, "o")]):
        s = CS[b] - CS[a]; s2 = CS2[b] - CS2[a]; c = np.maximum(CN[b] - CN[a], 1)
        mu, sd = F_MU[key]
        m = s / c; v = np.sqrt(np.maximum(s2/c - m**2, 0))
        out[..., 2*j] = ((m - mu)/sd).astype("float32")
        out[..., 2*j+1] = (v/sd).astype("float32")
    Lw = (b - a).astype("float64")[:, None]                        # (B,1) broadcast over nodes
    out[..., 6] = ((CNr[b] - CNr[a]) / np.maximum(Lw, 1)).astype("float32")   # valid fraction
    if args.hist_mode == "both": out[..., 8:16] = hist_bands(bt, L)
    out[..., 7] = np.float32(np.log1p(0 if L == -1 else L) / np.log1p(672))   # length code
    if L == -1: out[..., 7] = 1.0
    return out

def make_batch(bt, nodes_sl):
    btt = torch.as_tensor(bt, device=DEV); B = len(bt)
    nn_ = nodes_sl.stop - nodes_sl.start
    def wn(M): return torch.stack([M[btt-k][:, nodes_sl] for k in reversed(range(T_IN))], -1)
    def wg(g):
        wi = torch.stack([g[btt-k] for k in reversed(range(T_IN))], -1); return wi.unsqueeze(1).expand(-1, nn_, -1)
    x = torch.stack([wn(Rfill), wn(FLn), wn(OCn), wg(TODs), wg(TODc), wg(DOWs), wg(DOWc), wg(WKND)], 1)
    y = torch.stack([Cy[btt+h][:, nodes_sl] for h in HORIZONS], -1)
    m = torch.stack([Cm[btt+h][:, nodes_sl] for h in HORIZONS], -1)
    return x, y, m

# ------------------------------------------------------------------ model ---
class GTCN(nn.Module):
    def __init__(s, c, k, d): super().__init__(); s.pad=(k-1)*d; s.f=nn.Conv2d(c, c, (1, k), dilation=(1, d)); s.g=nn.Conv2d(c, c, (1, k), dilation=(1, d))
    def forward(s, x): x=F.pad(x, (s.pad, 0)); return torch.tanh(s.f(x))*torch.sigmoid(s.g(x))
class GCN(nn.Module):
    def __init__(s, c, order=2): super().__init__(); s.order=order; s.mlp=nn.Conv2d(c*(order+1), c, (1, 1))
    def forward(s, x, A):
        out=[x]; xk=x
        for _ in range(s.order): xk=torch.einsum("nm,bcmt->bcnt", A, xk); out.append(xk)
        return s.mlp(torch.cat(out, 1))
class Block(nn.Module):
    def __init__(s, c, d): super().__init__(); s.tcn=GTCN(c, 2, d); s.gcn=GCN(c); s.skip=nn.Conv2d(c, c, (1, 1)); s.bn=nn.BatchNorm2d(c)
    def forward(s, x, A): res=x; x=s.tcn(x); sk=s.skip(x); x=s.gcn(x, A); return s.bn(x+res), sk
class Backbone(nn.Module):
    def __init__(s):
        super().__init__(); s.start=nn.Conv2d(C_DYN+DEMB, args.hidden, (1, 1))
        d=1; s.blocks=nn.ModuleList()
        for _ in range(args.blocks): s.blocks.append(Block(args.hidden, d)); d*=2
        s.e1=nn.Conv2d(args.hidden, args.hidden, (1, 1)); s.e2=nn.Conv2d(args.hidden, H*3, (1, 1))
    def forward(s, x, A, E):                                        # E (B,n,DEMB) time-varying identity
        B, _, nnodes, T = x.shape
        ech = E.permute(0, 2, 1).unsqueeze(-1).expand(B, DEMB, nnodes, T)
        x = s.start(torch.cat([x, ech], 1)); skip = 0
        for b in s.blocks: x, sk = b(x, A); skip = skip + sk[..., -1:]
        h = F.relu(s.e1(F.relu(skip)))
        return s.e2(h).squeeze(-1).permute(0, 2, 1).contiguous().reshape(B, nnodes, H, 3)

class OnboardEncoder(nn.Module):
    def __init__(s): super().__init__(); s.l1=nn.Linear(ENC_IN, 64); s.l2=nn.Linear(64, DEMB)
    def forward(s, static_nbr, hist):                               # (n,12), (B,n,8)
        B = hist.shape[0]
        z = torch.cat([static_nbr.unsqueeze(0).expand(B, -1, -1), hist], -1)
        return s.l2(F.relu(s.l1(z)))

SN = torch.tensor(np.concatenate([STAT, NBR], 1), device=DEV)      # (N,12)

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

# ------------------------------------------------------------------- train ---
bb = Backbone().to(DEV); enc = OnboardEncoder().to(DEV)
params = list(bb.parameters()) + list(enc.parameters())
opt = torch.optim.Adam(params, lr=args.lr)
best = 1e9; bs = None; bad = 0
for ep in range(args.epochs):
    bb.train(); enc.train(); perm_ = np.random.permutation(tr)
    for i in range(0, len(perm_), args.batch):
        bt = perm_[i:i+args.batch]
        L = LSET[np.random.randint(len(LSET))]                     # history-length dropout
        hist = torch.tensor(hist_summary(bt, L)[:, :ns], device=DEV)
        E = enc(SN[:ns], hist)
        x, y, m = make_batch(bt, SEEN)
        opt.zero_grad(); loss_fn(bb(x, A_seen, E), y, m).backward()
        torch.nn.utils.clip_grad_norm_(params, 5.0); opt.step()
    bb.eval(); enc.eval(); num = den = 0.0
    with torch.no_grad():
        for i in range(0, len(va), 128):
            bt = va[i:i+128]
            hist = torch.tensor(hist_summary(bt, -1)[:, :ns], device=DEV)
            x, y, m = make_batch(bt, SEEN)
            l = loss_fn(bb(x, A_seen, enc(SN[:ns], hist)), y, m)
            num += l.item()*m.sum().item(); den += m.sum().item()
    v = num/max(den, 1)
    st = {"bb": {k: t.detach().clone() for k, t in bb.state_dict().items()},
          "enc": {k: t.detach().clone() for k, t in enc.state_dict().items()}}
    if v < best-1e-5: best, bs, bad = v, st, 0
    else: bad += 1
    print(f"[onboard] epoch {ep+1:02d}  val wCE(seen,full-hist)={v:.4f}  best={best:.4f}")
    if bad >= args.patience: print("[onboard] early stop"); break
bb.load_state_dict(bs["bb"]); enc.load_state_dict(bs["enc"]); bb.eval(); enc.eval()

# ------------------------------------------------- onboarding curve (test) ---
rows = []
rows_node = []
with torch.no_grad():
    for L, name in LCURVE:
        Ps, Ph, Ys, Yh = [], [], [], []
        for i in range(0, len(te), 128):
            bt = te[i:i+128]
            hist_full = hist_summary(bt, -1); hist_L = hist_summary(bt, L)
            hist = np.concatenate([hist_full[:, :ns], hist_L[:, ns:]], 1)   # seen=veteran, held=L hours
            E = enc(SN, torch.tensor(hist, device=DEV))
            x, y, m = make_batch(bt, slice(0, N))
            P = F.softmax(bb(x, A_full, E), -1).cpu().numpy(); Yv = np.where(m.cpu().numpy() > 0, y.cpu().numpy(), -1)
            Ps.append(P[:, :ns]); Ph.append(P[:, ns:]); Ys.append(Yv[:, :ns]); Yh.append(Yv[:, ns:])
        Ps, Ph, Ys, Yh = map(np.concatenate, (Ps, Ph, Ys, Yh))
        for split, (P, Y) in [("seen", (Ps, Ys)), ("held-out", (Ph, Yh))]:
            w = f = rr = 0.0; cnt = 0
            for j in range(H):
                wj, fj, rj = scores(P[..., j, :], Y[..., j]); w += wj; f += fj; rr += rj; cnt += 1
            rows.append((name, split, w/cnt, f/cnt, rr/cnt))
        # --- per-nodo (solo tenuti fuori): wCE del nodo su tutti gli orizzonti ---
        if split == "held-out":
            _ids = None
            for _nm in ("ids", "sids", "sensor_ids", "kept", "kept_ids"):
                if _nm in globals(): _ids = globals()[_nm]; break
            for k in range(P.shape[1]):
                Pk = P[:, k].reshape(-1, 3); Yk = Y[:, k].reshape(-1)
                vk = Yk >= 0
                if vk.sum() == 0: continue
                ptk = np.clip(Pk[vk][np.arange(vk.sum()), Yk[vk]], 1e-7, 1)
                wk = float(np.sum(Wnp[Yk[vk]] * -np.log(ptk)) / np.sum(Wnp[Yk[vk]]))
                sid = str(_ids[ns + k]) if _ids is not None and len(_ids) > ns + k else ""
                rows_node.append((name, ns + k, sid, wk, int(vk.sum())))
# --- ESPERIMENTO A: permutation importance della storia (held-out, 24h) ---
with torch.no_grad():
    L24 = [L for L, nm in LCURVE if nm == "24h"][0]
    perm = np.random.default_rng(12345).permutation(N - ns)
    Php, Yhp = [], []
    for i in range(0, len(te), 128):
        bt = te[i:i+128]
        hist_full = hist_summary(bt, -1); hist_L = hist_summary(bt, L24)
        hist = np.concatenate([hist_full[:, :ns], hist_L[:, ns:][:, perm]], 1)
        E = enc(SN, torch.tensor(hist, device=DEV))
        x, y, m = make_batch(bt, slice(0, N))
        P = F.softmax(bb(x, A_full, E), -1).cpu().numpy()
        Yv = np.where(m.cpu().numpy() > 0, y.cpu().numpy(), -1)
        Php.append(P[:, ns:]); Yhp.append(Yv[:, ns:])
    Php, Yhp = np.concatenate(Php), np.concatenate(Yhp)
    wp = np.mean([scores(Php[..., j, :], Yhp[..., j])[0] for j in range(H)])
w24 = [r[2] for r in rows if r[0] == "24h" and r[1] == "held-out"][0]
w0h = [r[2] for r in rows if r[0] == "0h" and r[1] == "held-out"][0]
gain = w0h - w24
print("\n=== PERMUTATION CHECK (held-out, 24h; storia permutata fra i nodi) ===")
print(f"wCE 24h={w24:.4f} | permutata={wp:.4f} | degrado assoluto D={wp-w24:+.4f}")
print(f"guadagno 0h->24h={gain:+.4f} | quota del guadagno distrutta={(wp-w24)/gain if abs(gain)>1e-6 else float('nan'):.0%}")
res = pd.DataFrame(rows, columns=["history", "split", "wCE", "macroF1", "red_recall"])
pd.DataFrame(rows_node, columns=["history", "node_pos", "sensor_id", "wCE", "n_valid"]).to_csv(
    str(args.out).replace(".csv", "_pernode.csv"), index=False)
print(f"per-nodo -> {str(args.out).replace('.csv', '_pernode.csv')}")
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== ONBOARDING CURVE (mean over horizons) ===")
print(res.to_string(index=False))
# (nessun riferimento costante: seen_ref e h0 sono calcolati sul contesto corrente)
seen_ref = res[(res.split == "seen") & (res.history == "1wk")]["wCE"].values[0]
h0 = res[(res.split == "held-out") & (res.history == "0h")]["wCE"].values[0]
for _, row in res[res.split == "held-out"].iterrows():
    closed = (h0 - row.wCE) / max(h0 - seen_ref, 1e-6)
    print(f"held-out @ {row.history:>3s}: wCE={row.wCE:.4f}  gap-to-veteran closed: {closed:+.0%}")
res.to_csv(args.out, index=False); print(f"saved -> {args.out}")
