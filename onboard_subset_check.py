"""
Verifica della "facilita'" del sottoinsieme tenuto fuori (onboarding, §8.4)
===========================================================================
Domanda: il sottoinsieme di sensori tenuto fuori dall'addestramento (partizione
casuale di gomo_onboard.py) e' intrinsecamente piu' facile di quello visto?

Metodo, senza alcun modello: si valuta il PRIORE STORICO DI CLASSE (per nodo e
momento-tipo, stimato sul 70% train) separatamente sui due sottoinsiemi, sul
test set, con la stessa entropia pesata T4c. Il priore e' privo di parametri
appresi: ogni differenza fra i due sottoinsiemi riflette solo la loro
difficolta' intrinseca, non il modello.

Replica ESATTAMENTE la partizione di gomo_onboard.py:
  rng = np.random.default_rng(seed); perm = rng.permutation(N)
  held = ultimi round(0.3*N) nodi di perm.

Uso:
  poetry run python onboard_subset_check.py --targets <targets_t4clon.npz> --label Londra
  poetry run python onboard_subset_check.py --targets <targets_t4cmad.npz> --label Madrid
(aggiungere --held-frac/--seeds se diversi dai default di gomo_onboard.py)
"""
import argparse
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--targets", required=True, help="npz con array 'r' (T x N) usato da gomo_onboard")
ap.add_argument("--label", default="")
ap.add_argument("--held-frac", type=float, default=0.3)
ap.add_argument("--seeds", default="0,1,2")
ap.add_argument("--out-csv", default="subset_diff.csv")
ap.add_argument("--train-frac", type=float, default=0.7)
ap.add_argument("--val-frac", type=float, default=0.1)
args = ap.parse_args()

d = np.load(args.targets, allow_pickle=True)
# stesse chiavi usate da gomo_onboard.py: congestion_emp (classi, T x S), timestamps
C = d["congestion_emp"].astype(np.int16)          # T x S: 0=non valido, 1/2/3=verde/giallo/rosso
Y = np.where(C > 0, C - 1, -1).astype(np.int8)    # -> -1=non valido, 0/1/2 (convenzione di gomo_onboard)
T, N = Y.shape
print(f"[{args.label}] classi congestion_emp: {T} x {N}")
print("NOTA: gomo_onboard.py permuta i nodi DOPO l'aggancio al grafo; per i contesti")
print(f"t4c l'aggancio conserva tutti i sensori, quindi la partizione qui replicata e'")
print(f"identica se nel log di onboarding compariva 'node holdout: {N - int(round(args.held_frac*N))} seen (train), {int(round(args.held_frac*N))} held-out'.")

t_tr = int(T*args.train_frac); t_va = int(T*(args.train_frac+args.val_frac))
slot = (np.arange(T) % (96*7))                    # momento-tipo settimanale

def prior_wce_on(nodes):
    """wCE del priore storico di classe sui nodi dati, test set."""
    # priore: distribuzione delle 3 classi per (slot, nodo) stimata sul train
    P = np.full((96*7, len(nodes), 3), np.nan, dtype="float64")
    for si in range(96*7):
        rows = np.where(slot[:t_tr] == si)[0]
        yy = Y[rows][:, nodes]
        for c in range(3):
            P[si, :, c] = np.sum((yy == c) & (yy >= 0), 0)
    tot = P.sum(-1, keepdims=True); tot[tot == 0] = 1
    P = (P + 1.0) / (tot + 3.0)                    # smoothing di Laplace
    # pesi T4c dalle frequenze del train sugli stessi nodi (convenzione degli script)
    yy = Y[:t_tr][:, nodes]; freq = np.array([(yy == c).sum() for c in range(3)], "float64")
    W = freq.sum() / (freq * 3.0)
    # valutazione sul test
    num = den = 0.0
    for t in range(t_va, T):
        yt = Y[t][nodes]; ok = yt >= 0
        if not ok.any(): continue
        pt = P[slot[t]][ok, yt[ok]]
        num += np.sum(W[yt[ok]] * -np.log(np.clip(pt, 1e-7, 1))); den += np.sum(W[yt[ok]])
    return num/den

_pairs = []
def prior_wce_per_node():
    """wCE del priore per ciascun nodo separatamente, pesi globali del train."""
    P = np.full((96*7, N, 3), np.nan, dtype="float64")
    for si in range(96*7):
        rows = np.where(slot[:t_tr] == si)[0]
        yy = Y[rows]
        for c in range(3):
            P[si, :, c] = np.sum((yy == c) & (yy >= 0), 0)
    tot = P.sum(-1, keepdims=True); tot[tot == 0] = 1
    P = (P + 1.0) / (tot + 3.0)
    yy = Y[:t_tr]; freq = np.array([(yy == c).sum() for c in range(3)], "float64")
    W = freq.sum() / (freq * 3.0)
    num = np.zeros(N); den = np.zeros(N)
    for t in range(t_va, T):
        yt = Y[t]; idx = np.where(yt >= 0)[0]
        if not len(idx): continue
        pt = P[slot[t]][idx, yt[idx]]; w = W[yt[idx]]
        num[idx] += w * -np.log(np.clip(pt, 1e-7, 1)); den[idx] += w
    return num / np.maximum(den, 1e-9)

_pn = prior_wce_per_node()
_v = _pn[np.isfinite(_pn) & (_pn > 0)]
print(f"\n[eterogeneita] difficolta per nodo (priore): n={len(_v)}  media {_v.mean():.4f}  "
      f"sd {_v.std(ddof=1):.4f}  CV {_v.std(ddof=1)/_v.mean():.4f}")
print(f"[eterogeneita] percentili 10/50/90: {np.percentile(_v,10):.3f} / "
      f"{np.percentile(_v,50):.3f} / {np.percentile(_v,90):.3f}  "
      f"| rapporto p90/p10 {np.percentile(_v,90)/np.percentile(_v,10):.2f}")

print(f"{'seme':>5} | {'wCE priore (visti)':>19} | {'wCE priore (tenuti fuori)':>25} | piu' facile?")
diffs = []
for seed in [int(s) for s in args.seeds.split(",")]:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(N); nh = int(round(args.held_frac*N)); ns = N - nh
    seen, held = perm[:ns], perm[ns:]
    a, b = prior_wce_on(seen), prior_wce_on(held)
    diffs.append(a - b); _pairs.append((a, b))
    print(f"{seed:>5} | {a:>19.4f} | {b:>25.4f} | {'SI (tenuti fuori)' if b < a else 'no'}")
import pandas as _pd
_semi = [int(s) for s in args.seeds.split(",")]
_pd.DataFrame({"seed": _semi, "wce_seen": [x[0] for x in _pairs], "wce_held": [x[1] for x in _pairs],
               "D_held_minus_seen": [x[1]-x[0] for x in _pairs]}).to_csv(args.out_csv, index=False)
print(f"[salvato] -> {args.out_csv}")
m = float(np.mean(diffs)); sd = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.0
print(f"\ndifferenza media (visti - tenuti fuori): {m:+.4f} ± {sd:.4f}")
print("Lettura: differenza positiva = il sottoinsieme tenuto fuori e' intrinsecamente")
print("piu' facile (il priore, privo di parametri, vi ottiene wCE piu' bassa).")
