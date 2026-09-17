"""
GO-MO — weather value-of-information ablation
=============================================
Best model (temporal + node-identity classifier, weighted CE) with vs without weather
input channels. Scored on weighted CE + red recall, OVERALL and split RAIN vs DRY
(by is_rain at the target time). Answers the paper's core question: does exogenous
weather help, and specifically *when it rains*? No graph here (it is ~neutral for the
per-sensor task) → torch only, no libomp conflict.

Run from models/ :
    poetry run python gomo_weather_ablation.py \
        --targets ../data_collection/go-mo/gomo/targets_2024_urb_d8.npz \
        --weather ../data_collection/go-mo/gomo/weather_2024_d8.npz
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

DATA = Path("../data_collection/go-mo/gomo")
ap = argparse.ArgumentParser(description="Weather value-of-information ablation")
ap.add_argument("--targets", type=Path, default=DATA / "targets_2024_urb_d8.npz")
ap.add_argument("--weather", type=Path, default=DATA / "weather_2024_d8.npz")
ap.add_argument("--dump-probs", type=str, default="",
                help="prefisso npz: salva le probabilita alle epoche di valutazione")
ap.add_argument("--eval-epochs", type=str, default="25,30",
                help="epoche a cui valutare sul test e salvare le probabilita")
ap.add_argument("--wx-permuta", action="store_true",
                help="permuta le giornate meteo entro (mese, feriale/festivo)")
ap.add_argument("--out", type=Path, default=Path("weather_ablation_results.csv"))
ap.add_argument("--win", type=int, default=12)
ap.add_argument("--hidden", type=int, default=32)
ap.add_argument("--blocks", type=int, default=4)
ap.add_argument("--epochs", type=int, default=35)
ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--lr", type=float, default=1e-3)
ap.add_argument("--patience", type=int, default=8)
ap.add_argument("--no-time", action="store_true",
                help="rimuove le 5 codifiche temporali (ora, giorno, fine settimana)")
ap.add_argument("--no-ha", action="store_true",
                help="rimuove anche il canale di media storica per nodo x momento-tipo")
ap.add_argument("--gate", action="store_true",
                help="condizionamento FiLM sui canali meteo invece della concatenazione: "
                     "C_IN resta 9, il meteo modula scala e traslazione delle attivazioni")
ap.add_argument("--placebo", action="store_true",
                help="sostituisce i canali meteo con surrogati a fase randomizzata "
                     "(stesso spettro di potenza => stessa autocorrelazione e varianza, nessuna relazione col traffico)")
ap.add_argument("--placebo-seed", type=int, default=12345, help="seme dedicato ai surrogati")
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
C = z["congestion_emp"].astype("int64"); Tn, K = r.shape

wz = np.load(args.weather, allow_pickle=True)
Wraw = wz["weather"].astype("float32"); VARS = [str(v) for v in wz["variables"]]; is_rain = wz["is_rain"].astype(bool)
if args.wx_permuta:
    import pandas as _pd
    _wt = _pd.to_datetime(wz["timestamps"])
    _gi = _pd.DataFrame({"d": _wt.date,
                         "b": _wt.to_period("M").astype(str) + "|" + (_wt.dayofweek < 5).astype(str)})
    _rng = np.random.default_rng(args.seed + 7717); _map = {}
    for _b, _q in _gi.drop_duplicates("d").groupby("b"):
        _g = list(_q.d)
        if len(_g) > 1:
            _p = list(_rng.permutation(_g))
            for _ in range(30):
                if all(a != b for a, b in zip(_g, _p)): break
                _p = list(_rng.permutation(_g))
            _map.update(dict(zip(_g, _p)))
        else: _map[_g[0]] = _g[0]
    _pos = {}
    for _i, _d in enumerate(_gi.d): _pos.setdefault(_d, []).append(_i)
    _idx = np.arange(len(Wraw))
    for _d, _r in _pos.items():
        _s = _pos.get(_map.get(_d, _d), _r)
        for _k, _j in enumerate(_r): _idx[_j] = _s[_k] if _k < len(_s) else _j
    Wraw = Wraw[_idx].copy(); is_rain = is_rain[_idx].copy()
    print(f"[meteo PERMUTATO] {len(_map)} giornate, "
          f"{sum(1 for _d in _map if _map[_d] == _d)} invariate")
V = Wraw.shape[1]
assert Wraw.shape[0] == Tn, "weather/targets timestamp mismatch — re-run 6_gomo_weather.py on this targets file"
print(f"sensors={K}  weather vars={VARS}  rain fraction={is_rain.mean():.1%}")

starts = np.arange(T_IN - 1, Tn - max(HORIZONS)); n = len(starts)
tr, va, te = starts[:int(n*.7)], starts[int(n*.7):int(n*.8)], starts[int(n*.8):]
reg = slice(0, tr[-1] + 1); ctr = C[reg]
freq = np.array([(ctr == k).sum() for k in (1, 2, 3)], dtype="float64")
Wt_np = (freq.sum() / (np.maximum(freq, 1) * 3)).astype("float32")
print(f"class freq g/y/r = {(freq/freq.sum()).round(3)} | T4c weights = {Wt_np.round(2)}")

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
# weather normalized (train stats), one (T,) series per variable
if args.placebo:
    _S = np.empty_like(Wraw)
    for _k in range(Wraw.shape[1]):
        _x = Wraw[:, _k].astype("float64")
        _F = np.fft.rfft(_x - _x.mean())
        _best, _bc = None, 9.9
        for _try in range(200):                      # scelta del surrogato meno correlato
            _rp = np.random.default_rng(args.placebo_seed + 1000*_try + _k)
            _ph = _rp.uniform(0, 2*np.pi, len(_F)); _ph[0] = 0.0
            if len(_x) % 2 == 0: _ph[-1] = 0.0
            _cand = np.fft.irfft(np.abs(_F)*np.exp(1j*_ph), n=len(_x)) + _x.mean()
            _c = abs(np.corrcoef(_x, _cand)[0, 1])
            if _c < _bc: _best, _bc = _cand, _c
            if _bc < 0.02: break
        _S[:, _k] = _best.astype("float32")
    print(f"[placebo] surrogati a fase randomizzata, seme {args.placebo_seed}")
    for _k in range(Wraw.shape[1]):
        _a, _b = Wraw[:, _k], _S[:, _k]
        _c1 = np.corrcoef(_a[:-1], _a[1:])[0,1]; _c2 = np.corrcoef(_b[:-1], _b[1:])[0,1]
        print(f"[placebo] {VARS[_k]:<14s} sd {_a.std():.4f}->{_b.std():.4f} | "
              f"autocorr(1) {_c1:.4f}->{_c2:.4f} | corr con originale {np.corrcoef(_a,_b)[0,1]:+.4f}")
    Wraw = _S
wmu = Wraw[reg].mean(0); wsd = Wraw[reg].std(0) + 1e-6
Wn = [T_(((Wraw[:, k]-wmu[k])/wsd[k]).astype("float32")) for k in range(V)]
slot = (ts.dayofweek.to_numpy()*96 + ts.hour.to_numpy()*4 + ts.minute.to_numpy()//15)
hs = np.zeros((K, 672)); hc = np.zeros((K, 672)); tt = np.arange(0, tr[-1] + 1)
rv = r[tt]; vv = np.isfinite(rv); si = np.broadcast_to(np.arange(K), rv.shape); sl = np.broadcast_to(slot[tt][:, None], rv.shape)
np.add.at(hs, (si[vv], sl[vv]), rv[vv]); np.add.at(hc, (si[vv], sl[vv]), 1)
ht = np.divide(hs, hc, out=np.full_like(hs, np.nan), where=hc > 0)
gm = float(np.nanmean(ht)); sm = np.nanmean(np.where(np.isfinite(ht), ht, np.nan), 1)
sm = np.where(np.isfinite(sm), sm, gm); HA = np.nan_to_num(np.where(np.isfinite(ht), ht, sm[:, None]), nan=gm).astype("float32")
HAser = T_(HA[:, slot].T.copy())
Cy = T_(np.where(C > 0, C - 1, 0).astype("int64")); Cm = T_((C > 0).astype("float32")); Wt = T_(Wt_np)
DEMB = 8; BASE_C = 9 - (5 if args.no_time else 0) - (1 if args.no_ha else 0)
if args.no_time or args.no_ha:
    print(f"[ablazione temporale] no_time={args.no_time} no_ha={args.no_ha} -> BASE_C={BASE_C}")

def make_batch(bt, with_w):
    bt = torch.as_tensor(bt, device=DEV); B = len(bt)
    def wn(M): return torch.stack([M[bt-k] for k in reversed(range(T_IN))], -1)
    def wg(g):
        wi = torch.stack([g[bt-k] for k in reversed(range(T_IN))], -1); return wi.unsqueeze(1).expand(-1, K, -1)
    chans = [wn(Rfill), wn(FLn), wn(OCn)]
    if not args.no_ha: chans.append(wn(HAser))
    if not args.no_time: chans += [wg(TODs), wg(TODc), wg(DOWs), wg(DOWc), wg(WKND)]
    if with_w:
        if not args.gate:
            chans += [wg(Wn[k]) for k in range(V)]                 # weather: area-level, broadcast to nodes
    x = torch.stack(chans, 1)
    y = torch.stack([Cy[bt+h] for h in HORIZONS], -1); m = torch.stack([Cm[bt+h] for h in HORIZONS], -1)
    wv = torch.stack([Wn[k][bt] for k in range(V)], -1) if (args.gate and with_w) else None
    return (x, y, m, wv) if args.gate else (x, y, m)

# ------------------------------------------------------------------ model ---
class GTCN(nn.Module):
    def __init__(s, c, k, d): super().__init__(); s.pad=(k-1)*d; s.f=nn.Conv2d(c, c, (1, k), dilation=(1, d)); s.g=nn.Conv2d(c, c, (1, k), dilation=(1, d))
    def forward(s, x): x=F.pad(x, (s.pad, 0)); return torch.tanh(s.f(x))*torch.sigmoid(s.g(x))
class Block(nn.Module):
    def __init__(s, c, d): super().__init__(); s.tcn=GTCN(c, 2, d); s.skip=nn.Conv2d(c, c, (1, 1)); s.bn=nn.BatchNorm2d(c)
    def forward(s, x): res=x; x=s.tcn(x); return s.bn(x+res), s.skip(x)
class Net(nn.Module):
    def __init__(s, c_in):
        super().__init__(); s.emb=nn.Parameter(torch.randn(K, DEMB)*0.05); s.start=nn.Conv2d(c_in+DEMB, args.hidden, (1, 1))
        d=1; s.blocks=nn.ModuleList()
        for _ in range(args.blocks): s.blocks.append(Block(args.hidden, d)); d*=2
        s.e1=nn.Conv2d(args.hidden, args.hidden, (1, 1)); s.e2=nn.Conv2d(args.hidden, H*3, (1, 1))
        s.film = nn.Sequential(nn.Linear(V, args.hidden), nn.ReLU(),
                               nn.Linear(args.hidden, 2*args.hidden)) if args.gate else None
    def forward(s, x, wv=None):
        B, _, N, T = x.shape; x=torch.cat([x, s.emb.t().view(1, DEMB, N, 1).expand(B, DEMB, N, T)], 1)
        x=s.start(x)
        if s.film is not None and wv is not None:
            g = s.film(wv)                                   # (B, 2*hidden)
            sc, sh = g.chunk(2, -1)
            x = x*(1 + sc.view(B, -1, 1, 1)) + sh.view(B, -1, 1, 1)
        skip=0
        for b in s.blocks: x, sk=b(x); skip=skip+sk[..., -1:]
        h=F.relu(s.e1(F.relu(skip)))
        return s.e2(h).squeeze(-1).permute(0, 2, 1).contiguous().reshape(B, N, H, 3)
def loss_fn(lg, y, m):
    lp=F.log_softmax(lg, -1); nll=-lp.gather(-1, y.unsqueeze(-1)).squeeze(-1)
    return (nll*Wt[y]*m).sum()/(Wt[y]*m).sum().clamp_min(1)

def train_eval(with_w):
    c_in = BASE_C + (V if (with_w and not args.gate) else 0)   # con --gate il meteo condiziona, non entra fra i canali
    net = Net(c_in).to(DEV); opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    best=1e9; bs={k: v.detach().clone() for k, v in net.state_dict().items()}; bad=0
    tag = ("placebo" if args.placebo else "weather") if with_w else "base"
    for ep in range(args.epochs):
        net.train(); perm=np.random.permutation(tr)
        for i in range(0, len(perm), args.batch):
            _b=make_batch(perm[i:i+args.batch], with_w)
            if args.gate: x,y,m,wv=_b
            else: x,y,m=_b; wv=None
            opt.zero_grad(); loss_fn(net(x, wv), y, m).backward(); opt.step()
        net.eval(); num=den=0.0
        with torch.no_grad():
            for i in range(0, len(va), 256):
                _b=make_batch(va[i:i+256], with_w)
                if args.gate: x,y,m,wv=_b
                else: x,y,m=_b; wv=None
                num+=loss_fn(net(x, wv), y, m).item()*m.sum().item(); den+=m.sum().item()
        v=num/max(den, 1)
        if v<best-1e-5: best, bs, bad=v, {k: vv.detach().clone() for k, vv in net.state_dict().items()}, 0
        else: bad+=1
        _ev = [int(_e) for _e in args.eval_epochs.split(",") if _e.strip()]
        _Pt = _Yt = None
        _Pt, _Yt = _valuta_test(net, with_w)
        _w, _r = scores(_Pt, _Yt)
        CURVA.append((tag, ep+1, v, _w, _r))
        if (ep+1) in _ev: SNAP[(tag, ep+1)] = (_Pt.copy(), _Yt.copy())
        print(f"[{tag}] epoch {ep+1:02d}  val wCE={v:.4f}  best={best:.4f}  test wCE={_w:.4f}")
        if bad>=args.patience: print(f"[{tag}] early stop"); break
    net.load_state_dict(bs); net.eval()
    return _valuta_test(net, with_w)

CURVA = []      # (tag, epoca, val_wCE, test_wCE, test_recall)
SNAP = {}       # (tag, epoca) -> (P, Y)

def _valuta_test(net, with_w):
    P, Y = [], []
    with torch.no_grad():
        for i in range(0, len(te), 256):
            _b=make_batch(te[i:i+256], with_w)
            if args.gate: x,y,m,wv=_b
            else: x,y,m=_b; wv=None
            P.append(F.softmax(net(x, wv), -1).cpu().numpy()); Y.append(np.where(m.cpu().numpy()>0, y.cpu().numpy(), -1))
    return np.concatenate(P), np.concatenate(Y)

# ---------------------------------------------------------------- metrics ---
def scores(P, Y):
    P=P.reshape(-1, 3); Y=Y.reshape(-1); v=Y>=0; P, Y=P[v], Y[v]
    if len(Y)==0: return np.nan, np.nan
    pt=np.clip(P[np.arange(len(Y)), Y], 1e-7, 1); wce=float(np.sum(Wt_np[Y]*-np.log(pt))/np.sum(Wt_np[Y]))
    pred=P.argmax(1); rr=float(np.sum((pred==2)&(Y==2))/max(np.sum(Y==2), 1))
    return wce, rr

rain_te = np.stack([is_rain[te+h] for h in HORIZONS], -1)            # (Nte, H)
rows = []
for with_w in (False, True):
    P, Y = train_eval(with_w)
    tag = ("placebo" if args.placebo else "weather") if with_w else "base"
    rb = np.broadcast_to(rain_te[:, None, :], Y.shape)
    for subset, Ysub in [("all", Y), ("rain", np.where(rb, Y, -1)), ("dry", np.where(~rb, Y, -1))]:
        wce, rr = scores(P, Ysub)
        rows.append((tag, subset, wce, rr))

_ctx = Path(args.targets).stem
_chiavi = dict(context=_ctx, seed=args.seed, epochs=args.epochs,
               variante=("permutato" if args.wx_permuta else ("placebo" if args.placebo else "reale")),
               n_canali_meteo=V, celle_test=int((np.concatenate([Y.reshape(-1)]) >= 0).sum()) if "Y" in dir() else -1)
_cur = pd.DataFrame(CURVA, columns=["model","epoca","val_wCE","test_wCE","test_recall"])
for _k,_v in _chiavi.items(): _cur[_k]=_v
_cur["subset"]="all"; _cur["riga"]="curva"
res = pd.DataFrame(rows, columns=["model", "subset", "wCE", "red_recall"])
for _k,_v in _chiavi.items(): res[_k]=_v
res["riga"]="finale"; res["epoca"]=args.epochs
_tutto = pd.concat([res, _cur], ignore_index=True, sort=False)
_tutto.to_csv(args.out, index=False)
print(f"scritto {args.out}: {len(res)} righe finali + {len(_cur)} righe di curva")
if args.dump_probs:
    for (_tag,_ep),(_P,_Y) in SNAP.items():
        _p=_P.reshape(-1,3); _y=_Y.reshape(-1); _v=_y>=0
        np.savez_compressed(f"{args.dump_probs}_{_tag}_e{_ep}.npz",
            p=_p[_v].astype("float16"), y=_y[_v].astype("int8"),
            idx=np.where(_v)[0].astype("int32"), **{k:str(x) for k,x in _chiavi.items()})
    print(f"[probs] {len(SNAP)} dump con prefisso {args.dump_probs}")
pv = res.pivot(index="subset", columns="model", values=["wCE", "red_recall"]).reindex(["all", "rain", "dry"])
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n=== Weather value-of-information (test set; wCE lower=better) ===")
print(pv.to_string())
# headline: weather gain (base - weather), where positive = weather helps
for subset in ["all", "rain", "dry"]:
    b = res[(res.model=="base") & (res.subset==subset)]["wCE"].values[0]
    _tg = "placebo" if args.placebo else "weather"
    w = res[(res.model==_tg) & (res.subset==subset)]["wCE"].values[0]
    print(f"{_tg} wCE gain [{subset:4s}]: {(b-w):+.4f} ({(b-w)/b:+.1%})")
print(f"\nsaved -> {args.out}")   # il file e gia scritto sopra con curva e chiavi
