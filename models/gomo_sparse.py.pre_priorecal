"""
GO-MO — sparse-to-dense spatial inference (the deployment-faithful task)
=======================================================================
Install a FINITE set of sensors; infer the congestion of the UN-sensored rest of
the city. We observe a subset of nodes, mask the dynamic features of the rest, and
train/score ONLY on the unobserved nodes with Traffic4cast weighted cross-entropy.
For an unobserved node the ONLY live signal is what the graph propagates from
observed neighbours — so this is where spatial propagation should finally matter.

Coverage masking (parameter):
    random     : a random subset of nodes is observed
    structured : whole spatial grid-cells are observed (realistic install patterns,
                 large spatial holes, harder — the graph's real test)
Models: historical class-prior (seasonal, no live data), GWN none (no graph),
GWN adaptive (graph). No LightGBM here (no libomp conflict → no subprocess).

Place in models/. Run:
    poetry run python gomo_sparse.py --mask structured --obs-frac 0.4 \
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
ap = argparse.ArgumentParser(description="GO-MO sparse-to-dense spatial inference")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_urb_d8.npz")
ap.add_argument("--graph",   type=Path, default=DATA / "routes-graph.pkl")
ap.add_argument("--sensors", type=Path, default=DATA / "traffic_sensors.csv")
ap.add_argument("--dump-probs", type=str, default="")
ap.add_argument("--city", type=str, default="")
ap.add_argument("--out",     type=Path, default=Path("sparse_results.csv"))
ap.add_argument("--modes", default="none,adaptive",
                help="gwn: none|fixed|adaptive|both. Riferimenti spaziali: idw, knn, nbr_prior")
ap.add_argument("--calib-mode", choices=["weighted","empirical"], default="weighted",
                help="weighted: p ∝ W·f (ottimale per wCE). empirical: p = f")
ap.add_argument("--calib-bins", type=int, default=25, help="intervalli della mappa di calibrazione")
ap.add_argument("--idw-power", type=float, default=2.0, help="esponente di 1/d")
ap.add_argument("--knn-k", type=int, default=5, help="vicini per knn e nbr_prior (pre-registrato: 5)")
ap.add_argument("--hard-eps", type=float, default=0.05,
                help="massa sulle classi non predette per i riferimenti a valore puntuale (pre-registrato)")
ap.add_argument("--mask", choices=["random", "structured"], default="structured")
ap.add_argument("--obs-frac", type=float, default=0.4, help="fraction of sensors observed at eval")
ap.add_argument("--train-lo", type=float, default=0.15)
ap.add_argument("--train-hi", type=float, default=0.6)
ap.add_argument("--grid", type=int, default=6, help="grid resolution for structured masking")
ap.add_argument("--inductive", action="store_true",
                help="drop per-node identity embeddings; use static road features only (deployment-true)")
ap.add_argument("--no-coords", action="store_true",
                help="(inductive only) also drop coordinates -> road-type features only (severe test)")
ap.add_argument("--win", type=int, default=12)
ap.add_argument("--hidden", type=int, default=32)
ap.add_argument("--blocks", type=int, default=4)
ap.add_argument("--epochs", type=int, default=35)
ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--lr", type=float, default=1e-3)
ap.add_argument("--patience", type=int, default=8)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--device", default=None)
args = ap.parse_args()
torch.manual_seed(args.seed); np.random.seed(args.seed)
DEV = (torch.device(args.device) if args.device else
       torch.device("mps" if torch.backends.mps.is_available()
                    else "cuda" if torch.cuda.is_available() else "cpu"))
print("device:", DEV, "| mask:", args.mask, "| obs_frac:", args.obs_frac)
T_IN = args.win; HORIZONS = [1, 2, 4, 8]; H = len(HORIZONS); HL = {1: "15m", 2: "30m", 4: "60m", 8: "120m"}

# --------------------------------------------------------------------- data ---
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
r, flow, occ, C = r[:, kidx], flow[:, kidx], occ[:, kidx], C[:, kidx]
smeta = sens.set_index("id")
coords = smeta.loc[kept, ["utm_x", "utm_y"]].to_numpy()
maxspd = pd.to_numeric(smeta.loc[kept, "max_speed"], errors="coerce").to_numpy()
lanes  = pd.to_numeric(smeta.loc[kept, "lanes"], errors="coerce").to_numpy()
cap    = pd.to_numeric(smeta.loc[kept, "max_capacity"], errors="coerce").to_numpy()
print(f"aligned graph: {K} of {S} sensors")

# grid cells for structured masking
xs, ys = coords[:, 0], coords[:, 1]
gx = np.clip(((xs-xs.min())/(np.ptp(xs)+1e-9)*args.grid).astype(int), 0, args.grid-1)
gy = np.clip(((ys-ys.min())/(np.ptp(ys)+1e-9)*args.grid).astype(int), 0, args.grid-1)
cell_id = gx*args.grid + gy

def sample_obs(mode, frac, rng):
    k_obs = max(1, int(round(frac*K)))
    if mode == "random":
        obs = np.zeros(K, bool); obs[rng.choice(K, k_obs, replace=False)] = True; return obs
    cells = np.unique(cell_id).copy(); rng.shuffle(cells)
    obs = np.zeros(K, bool); cnt = 0
    for c in cells:
        sel = np.where(cell_id == c)[0]; obs[sel] = True; cnt += len(sel)
        if cnt >= k_obs: break
    return obs

starts = np.arange(T_IN - 1, Tn - max(HORIZONS)); n = len(starts)
tr, va, te = starts[:int(n*.7)], starts[int(n*.7):int(n*.8)], starts[int(n*.8):]
reg = slice(0, tr[-1] + 1); ctr = C[reg]
freq = np.array([(ctr == k).sum() for k in (1, 2, 3)], dtype="float64")
Wnp = (freq.sum() / (np.maximum(freq, 1) * 3)).astype("float32")     # Traffic4cast weights
print(f"class freq g/y/r = {(freq/freq.sum()).round(3)} | T4c weights = {Wnp.round(2)}")

def zst(a): v = a[reg][np.isfinite(a[reg])]; return float(v.mean()), float(v.std() + 1e-6)
fmu, fsd = zst(flow); omu, osd = zst(occ)
mmu, msd = np.nanmean(maxspd), np.nanstd(maxspd) + 1e-6
def T_(a): return torch.tensor(a, device=DEV)
Rfill = T_(np.where(np.isfinite(r), r, 1.0)); FLn = T_(np.where(np.isfinite(flow), (flow-fmu)/fsd, 0.0))
OCn = T_(np.where(np.isfinite(occ), (occ-omu)/osd, 0.0))
q = (ts.hour.to_numpy()*4 + ts.minute.to_numpy()//15)/96.0
TODs = T_(np.sin(2*np.pi*q).astype("float32")); TODc = T_(np.cos(2*np.pi*q).astype("float32"))
DOWs = T_(np.sin(2*np.pi*ts.dayofweek.to_numpy()/7).astype("float32"))
DOWc = T_(np.cos(2*np.pi*ts.dayofweek.to_numpy()/7).astype("float32"))
WKND = T_((ts.dayofweek.to_numpy() >= 5).astype("float32"))
def _z(a): return np.nan_to_num((a - np.nanmean(a)) / (np.nanstd(a) + 1e-6), nan=0.0).astype("float32")
MAXSP = T_(_z(maxspd)); XN = T_(_z(coords[:, 0])); YN = T_(_z(coords[:, 1]))
LANES = T_(_z(lanes)); CAP = T_(_z(cap))                    # (K,) static road features (known for any segment)
slot = (ts.dayofweek.to_numpy()*96 + ts.hour.to_numpy()*4 + ts.minute.to_numpy()//15)
hs = np.zeros((K, 672)); hc = np.zeros((K, 672)); tt = np.arange(0, tr[-1] + 1)
rv = r[tt]; vv = np.isfinite(rv); si = np.broadcast_to(np.arange(K), rv.shape); sl = np.broadcast_to(slot[tt][:, None], rv.shape)
np.add.at(hs, (si[vv], sl[vv]), rv[vv]); np.add.at(hc, (si[vv], sl[vv]), 1)
ht = np.divide(hs, hc, out=np.full_like(hs, np.nan), where=hc > 0)
gm = float(np.nanmean(ht)); sm = np.nanmean(np.where(np.isfinite(ht), ht, np.nan), 1)
sm = np.where(np.isfinite(sm), sm, gm); HA = np.nan_to_num(np.where(np.isfinite(ht), ht, sm[:, None]), nan=gm).astype("float32")
HAser = T_(HA[:, slot].T.copy())
Cy = T_(np.where(C > 0, C - 1, 0).astype("int64")); Cm = T_((C > 0).astype("float32")); Wt = T_(Wnp)
mask = Araw > 0; sg = Araw[mask].std()
Aff = np.where(mask, np.exp(-(Araw/sg)**2), 0.0).astype("float32"); np.fill_diagonal(Aff, 0.0)
Aff = Aff + np.eye(K, dtype="float32"); dd = Aff.sum(1); dinv = 1/np.sqrt(np.maximum(dd, 1e-6))
A_fixed = T_((Aff*dinv[:, None])*dinv[None, :])
INDUCTIVE = args.inductive; COORDS = not args.no_coords; DEMB = 8
C_IN = 11 + ((4 if COORDS else 2) if INDUCTIVE else 0)   # inductive: lanes+cap (+coords unless --no-coords)
print("mode:", ("INDUCTIVE " + ("road-type+coords" if COORDS else "road-type ONLY (severe)"))
      if INDUCTIVE else "transductive (node embeddings)")

def make_batch(bt, obs_t):                       # obs_t: float tensor (K,) 1=observed
    bt = torch.as_tensor(bt, device=DEV); B = len(bt); om = obs_t.view(1, K, 1)
    def wn(M): return torch.stack([M[bt-k] for k in reversed(range(T_IN))], -1)
    def wg(g):
        wi = torch.stack([g[bt-k] for k in reversed(range(T_IN))], -1); return wi.unsqueeze(1).expand(-1, K, -1)
    obs_ch = obs_t.view(1, K, 1).expand(B, K, T_IN)
    st = lambda v: v.view(1, K, 1).expand(B, K, T_IN)
    chans = [wn(Rfill)*om, wn(FLn)*om, wn(OCn)*om, wn(HAser)*om,               # dynamic: 0 if unobserved
             wg(TODs), wg(TODc), wg(DOWs), wg(DOWc), wg(WKND),                 # temporal (always)
             st(MAXSP), obs_ch]                                                # static maxspeed + observed flag
    if INDUCTIVE:
        chans += [st(LANES), st(CAP)]                                          # road-type features (shared)
        if COORDS:
            chans += [st(XN), st(YN)]                                          # + coordinates (soft node id)
    x = torch.stack(chans, 1)
    y = torch.stack([Cy[bt+h] for h in HORIZONS], -1)
    m = torch.stack([Cm[bt+h] for h in HORIZONS], -1) * (1 - obs_t).view(1, K, 1)   # unobserved only
    return x, y, m

# ------------------------------------------------------------- Graph WaveNet ---
class GTCN(nn.Module):
    def __init__(s, c, k, d): super().__init__(); s.pad=(k-1)*d; s.f=nn.Conv2d(c, c, (1, k), dilation=(1, d)); s.g=nn.Conv2d(c, c, (1, k), dilation=(1, d))
    def forward(s, x): x=F.pad(x, (s.pad, 0)); return torch.tanh(s.f(x))*torch.sigmoid(s.g(x))
class GCN(nn.Module):
    def __init__(s, c, ns, order=2): super().__init__(); s.order=order; s.mlp=nn.Conv2d(c*(order*ns+1), c, (1, 1))
    def forward(s, x, sup):
        out=[x]
        for A in sup:
            xk=x
            for _ in range(s.order): xk=torch.einsum("nm,bcmt->bcnt", A, xk); out.append(xk)
        return s.mlp(torch.cat(out, 1))
class Block(nn.Module):
    def __init__(s, c, d, ns): super().__init__(); s.tcn=GTCN(c, 2, d); s.gcn=GCN(c, ns) if ns>0 else None; s.skip=nn.Conv2d(c, c, (1, 1)); s.bn=nn.BatchNorm2d(c)
    def forward(s, x, sup):
        res=x; x=s.tcn(x); sk=s.skip(x)
        if s.gcn is not None: x=s.gcn(x, sup)
        return s.bn(x+res), sk
class GWN(nn.Module):
    def __init__(s, mode):
        super().__init__(); s.mode=mode; s.ns=(mode in ("fixed", "both"))+(mode in ("adaptive", "both"))
        s.emb = None if INDUCTIVE else nn.Parameter(torch.randn(K, DEMB)*0.05)
        s.start = nn.Conv2d(C_IN + (0 if INDUCTIVE else DEMB), args.hidden, (1, 1))
        if mode in ("adaptive", "both"): s.E1=nn.Parameter(torch.randn(K, 10)*0.05); s.E2=nn.Parameter(torch.randn(K, 10)*0.05)
        d=1; s.blocks=nn.ModuleList()
        for _ in range(args.blocks): s.blocks.append(Block(args.hidden, d, s.ns)); d*=2
        s.e1=nn.Conv2d(args.hidden, args.hidden, (1, 1)); s.e2=nn.Conv2d(args.hidden, H*3, (1, 1))
    def sup(s):
        Sx=[]
        if s.mode in ("fixed", "both"): Sx.append(A_fixed)
        if s.mode in ("adaptive", "both"): Sx.append(F.softmax(F.relu(s.E1@s.E2.t()), dim=1))
        return Sx
    def forward(s, x):
        B, _, N, T = x.shape
        if s.emb is not None:
            x = torch.cat([x, s.emb.t().view(1, DEMB, N, 1).expand(B, DEMB, N, T)], 1)
        x = s.start(x); sup = s.sup(); skip = 0
        for b in s.blocks: x, sk=b(x, sup); skip=skip+sk[..., -1:]
        h=F.relu(s.e1(F.relu(skip)))
        return s.e2(h).squeeze(-1).permute(0, 2, 1).contiguous().reshape(B, N, H, 3)
def loss_fn(lg, y, m):
    lp=F.log_softmax(lg, -1); nll=-lp.gather(-1, y.unsqueeze(-1)).squeeze(-1)
    return (nll*Wt[y]*m).sum()/(Wt[y]*m).sum().clamp_min(1)

# fixed evaluation coverage (seeded)
eval_obs_np = sample_obs(args.mask, args.obs_frac, np.random.default_rng(args.seed))
eval_obs = T_(eval_obs_np.astype("float32"))
print(f"eval coverage: {eval_obs_np.mean():.0%} observed, predicting {(~eval_obs_np).sum()} unobserved nodes")

PROBS = []
def scores(P, Y, tag=""):
    if args.dump_probs and tag and not tag.startswith("hist_prior"):
        _P = P.reshape(-1, 3); _Y = Y.reshape(-1); _v = _Y >= 0
        PROBS.append({"tag": tag, "p": _P[_v].astype("float16"),
                      "y": _Y[_v].astype("int8"), "idx": np.where(_v)[0].astype("int32")})
    P=P.reshape(-1, 3); Y=Y.reshape(-1); v=Y>=0; P, Y=P[v], Y[v]
    if len(Y)==0: return 0, 0, 0
    pt=np.clip(P[np.arange(len(Y)), Y], 1e-7, 1); wce=float(np.sum(Wnp[Y]*-np.log(pt))/np.sum(Wnp[Y]))
    pred=P.argmax(1); f1=[]
    for k in range(3):
        tp=np.sum((pred==k)&(Y==k)); fp=np.sum((pred==k)&(Y!=k)); fn=np.sum((pred!=k)&(Y==k))
        pr=tp/(tp+fp) if tp+fp else 0; rc=tp/(tp+fn) if tp+fn else 0
        f1.append(2*pr*rc/(pr+rc) if pr+rc else 0)
    return wce, float(np.mean(f1)), float(np.sum((pred==2)&(Y==2))/max(np.sum(Y==2), 1))

def train_gwn(mode):
    net=GWN(mode).to(DEV); opt=torch.optim.Adam(net.parameters(), lr=args.lr)
    best=1e9; bs={k: v.detach().clone() for k, v in net.state_dict().items()}; bad=0
    rng=np.random.default_rng(args.seed+1)
    for ep in range(args.epochs):
        net.train(); perm=np.random.permutation(tr)
        for i in range(0, len(perm), args.batch):
            frac=rng.uniform(args.train_lo, args.train_hi)               # random coverage each batch
            obs=T_(sample_obs(args.mask, frac, rng).astype("float32"))
            x, y, m=make_batch(perm[i:i+args.batch], obs)
            if m.sum()==0: continue
            opt.zero_grad(); loss_fn(net(x), y, m).backward(); opt.step()
        net.eval(); num=den=0.0
        with torch.no_grad():
            for i in range(0, len(va), 256):
                x, y, m=make_batch(va[i:i+256], eval_obs); num+=loss_fn(net(x), y, m).item()*m.sum().item(); den+=m.sum().item()
        v=num/max(den, 1)
        if v<best-1e-5: best, bs, bad=v, {k: vv.detach().clone() for k, vv in net.state_dict().items()}, 0
        else: bad+=1
        print(f"[{mode}] epoch {ep+1:02d}  val wCE={v:.4f}  best={best:.4f}")
        if bad>=args.patience: print(f"[{mode}] early stop"); break
    net.load_state_dict(bs); net.eval(); P, Y=[], []
    with torch.no_grad():
        for i in range(0, len(te), 256):
            x, y, m=make_batch(te[i:i+256], eval_obs)
            P.append(F.softmax(net(x), -1).cpu().numpy()); Y.append(np.where(m.cpu().numpy()>0, y.cpu().numpy(), -1))
    return np.concatenate(P), np.concatenate(Y)

# ------------------------------------------------------------------- run ----
rows = []
# historical class-prior baseline (unobserved nodes only)
hp = np.zeros((K, 672, 3))
for k in range(3):
    mm=(ctr==(k+1)); ss=np.broadcast_to(np.arange(K), ctr.shape); slT=np.broadcast_to(slot[reg][:, None], ctr.shape)
    np.add.at(hp[:, :, k], (ss[mm], slT[mm]), 1)
hp=(hp+1.0)/(hp.sum(-1, keepdims=True)+3.0)   # Laplace (era clip(...,1,None): celle degeneri)
unobs = ~eval_obs_np
for h in HORIZONS:
    Yt=np.where((C[te+h] > 0) & unobs[None, :], C[te+h]-1, -1); Pt=hp[:, slot[te+h], :].transpose(1, 0, 2)
    rows.append(("hist_prior", HL[h], *scores(Pt, Yt)))
# ---- riferimenti spaziali (nessun addestramento) ---------------------------
_SPAT = {"idw", "knn", "nbr_prior", "idw_dist", "nbr_idw"}
_req = [m.strip() for m in args.modes.split(",")]
if _SPAT & set(_req):
    _obs = np.where(eval_obs_np)[0]; _uno = np.where(~eval_obs_np)[0]
    _D = np.sqrt(((coords[_uno, None, :] - coords[None, _obs, :])**2).sum(-1))   # (n_unobs, n_obs)
    _D = np.maximum(_D, 1.0)
    _Widw = 1.0 / _D**args.idw_power
    _kk = min(args.knn_k, len(_obs))
    _nn = np.argsort(_D, 1)[:, :_kk]
    _Wknn = np.zeros_like(_D); np.put_along_axis(_Wknn, _nn, 1.0, 1)
    _Wnbr = np.zeros_like(_D)
    np.put_along_axis(_Wnbr, _nn, 1.0/np.take_along_axis(_D, _nn, 1)**2, 1)
    _CAL = {}
    print(f"[riferimenti] {len(_obs)} osservati, {len(_uno)} da stimare | k={_kk} | eps={args.hard_eps}")

    def _interp(Wm, h):
        """valori dei nodi osservati all'istante t (non t+h): persistenza + interpolazione."""
        Ro = r[te][:, _obs]                                  # (Nte, n_obs)
        ok = np.isfinite(Ro)
        num = np.where(ok, Ro, 0.0) @ Wm.T                   # (Nte, n_unobs)
        den = ok.astype("float64") @ Wm.T
        return np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0)

    _EDGES = np.linspace(0.0, 1.25, args.calib_bins + 1)

    def _interp_on(idx, Wm):
        Ro = r[idx][:, _obs]; ok = np.isfinite(Ro)
        num = np.where(ok, Ro, 0.0) @ Wm.T; den = ok.astype("float64") @ Wm.T
        return np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0)

    def _fit_calib(Wm, h):
        """P(classe a t+h | valore interpolato a t), stimata sul TRAIN, nodi non osservati."""
        rh = _interp_on(tr, Wm); Ch = C[tr + h][:, _uno]
        Yt = np.where(Ch > 0, Ch - 1, -1)
        b = np.digitize(rh, _EDGES) - 1
        tab = np.ones((len(_EDGES)+1, 3))                      # Laplace
        v = (Yt >= 0) & np.isfinite(rh)
        np.add.at(tab, (np.clip(b[v], -1, len(_EDGES)-1)+1, Yt[v]), 1.0)
        # calibrazione OTTIMALE per la metrica pesata: argmin wCE => p ∝ W·f
        # (la frequenza empirica minimizza la CE NON pesata, non questa)
        if args.calib_mode == "weighted": tab = tab * Wnp[None, :]
        return tab / tab.sum(1, keepdims=True)

    def _to_prob(rh, cal):
        b = np.clip(np.digitize(rh, _EDGES) - 1, -1, len(_EDGES)-1) + 1
        b = np.where(np.isfinite(rh), b, 0)
        P = np.full((rh.shape[0], K, 3), 1/3.0)
        P[:, _uno, :] = cal[b]
        return P

    for _m in _req:
        if _m not in _SPAT: continue
        for h in HORIZONS:
            Yt = np.where((C[te+h] > 0) & (~eval_obs_np)[None, :], C[te+h]-1, -1)
            if _m == "idw_dist":
                Wn = _Widw / np.maximum(_Widw.sum(1, keepdims=True), 1e-12)
                Co = C[te][:, _obs]
                acc = np.stack([(Co == kk+1).astype("float64") @ Wn.T for kk in range(3)], -1)
                acc = acc + 1e-3
                if args.calib_mode == "weighted": acc = acc * Wnp[None, None, :]
                Pt = np.full((len(te), K, 3), 1/3.0)
                Pt[:, _uno, :] = acc / acc.sum(-1, keepdims=True)
            elif _m == "nbr_idw":
                Wn = _Wnbr / np.maximum(_Wnbr.sum(1, keepdims=True), 1e-12)
                hpn = np.einsum("uo,ost->ust", Wn, hp[_obs])
                Pp = hpn[:, slot[te+h], :].transpose(1, 0, 2)
                Wi = _Widw / np.maximum(_Widw.sum(1, keepdims=True), 1e-12)
                Co = C[te][:, _obs]
                dev = np.stack([(Co == kk+1).astype("float64") @ Wi.T for kk in range(3)], -1) + 1e-3
                dev = dev / dev.sum(-1, keepdims=True)
                comb = np.sqrt(Pp * dev)                       # media geometrica prior x scarto
                if args.calib_mode == "weighted": comb = comb * Wnp[None, None, :]
                Pt = np.full((len(te), K, 3), 1/3.0)
                Pt[:, _uno, :] = comb / comb.sum(-1, keepdims=True)
            elif _m == "nbr_prior":
                Wn = _Wnbr / np.maximum(_Wnbr.sum(1, keepdims=True), 1e-12)
                hpn = np.einsum("uo,ost->ust", Wn, hp[_obs])      # (n_unobs, 672, 3)
                hpn = hpn * Wnp[None, None, :]                    # stessa calibrazione di idw/knn
                hpn = hpn / hpn.sum(-1, keepdims=True)
                Pt = np.full((len(te), K, 3), 1/3.0)
                Pt[:, _uno, :] = hpn[:, slot[te+h], :].transpose(1, 0, 2)
            else:
                Wm = _Widw if _m == "idw" else _Wknn
                if (_m, h) not in _CAL: _CAL[(_m, h)] = _fit_calib(Wm, h)
                Pt = _to_prob(_interp(Wm, h), _CAL[(_m, h)])
            rows.append((_m, HL[h], *scores(Pt, Yt)))

for mode in [m.strip() for m in args.modes.split(",")]:
    if mode in _SPAT: continue
    P, Y=train_gwn(mode)
    for j, h in enumerate(HORIZONS): rows.append((f"gwn_{mode}", HL[h], *scores(P[..., j, :], Y[..., j], tag=f"gwn_{mode}|{HL[h]}")))

res=pd.DataFrame(rows, columns=["model", "horizon", "wCE", "macroF1", "red_recall"])
res.insert(0, "setup", ("inductive-nocoords" if not COORDS else "inductive") if INDUCTIVE else "transductive")
res.insert(1, "mask", args.mask); res.insert(2, "obs_frac", args.obs_frac)
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print(f"\n=== Sparse-to-dense results ({args.mask}, {args.obs_frac:.0%} observed; scored on unobserved) ===")
print(res.to_string(index=False))
if args.out.exists():
    res=pd.concat([pd.read_csv(args.out), res]).drop_duplicates(["setup", "mask", "obs_frac", "model", "horizon"], keep="last")
res.insert(3, "cov_frac", float(eval_obs_np.mean()))
res.insert(4, "n_nodi_val", int((~eval_obs_np).sum()))
res.insert(5, "seed", args.seed); res.insert(6, "city", args.city)
res.to_csv(args.out, index=False); print(f"\nsaved -> {args.out}")
if args.dump_probs and PROBS:
    _d = {"context": args.targets.stem, "city": args.city, "seed": args.seed,
          "cov_frac": float(eval_obs_np.mean()), "n_nodi_val": int((~eval_obs_np).sum()), "n_nodi": K}
    for _i, _b in enumerate(PROBS):
        _d[f"tag{_i}"] = _b["tag"]; _d[f"p{_i}"] = _b["p"]; _d[f"y{_i}"] = _b["y"]; _d[f"idx{_i}"] = _b["idx"]
    np.savez_compressed(args.dump_probs, **_d)
    print(f"[probs] -> {args.dump_probs} ({len(PROBS)} blocchi)")
