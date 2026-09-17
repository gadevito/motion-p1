#!/usr/bin/env python3
"""
R2 e R3 con incertezza a livello di dato (ricampionamento congiunto).
======================================================================
Nessun addestramento: legge i dump di probabilita' gia' salvati. Adotta la
MEDESIMA procedura di `r1_ricampionamento.py`, cosi' che le tre colonne del
quadro degli effetti abbiano intervalli della stessa natura.

PERCHE' SERVE. Mescolare intervalli a t e di ricampionamento nella stessa
tabella e' peggio che mescolare numerosita' diverse: il lettore confronta
larghezze che misurano cose diverse senza avere modo di accorgersene. Gli
intervalli a t descrivono la sola dispersione fra inizializzazioni, quelli di
ricampionamento incorporano anche l'incertezza a livello di dato.

LE TRE CONVENZIONI, identiche a quelle di R1:

  * la STIMA PUNTUALE viene dai file di risultato, la LARGHEZZA dal
    ricampionamento sui dump, e l'intervallo e' centrato sulla stima. Le due
    fonti valutano popolazioni che differiscono dell'ordine del per mille, e su
    un rapporto fra grandezze vicine lo scarto si amplifica;
  * il NODO si decodifica come `idx % n_nodi`, con `n_nodi` dedotto come
    divisore MINIMO che raggiunge il novanta per cento della varianza massima
    della quota di classe critica fra gruppi. Prendere l'argmax restituisce un
    multiplo, perche' con K = 2n ogni sensore si divide in due gruppi;
  * lo SCHEMA della campagna si sceglie una volta per contesto e non seme per
    seme, altrimenti una campagna incompleta ne mescolerebbe due senza dirlo.

R2 e' il contributo dell'adiacenza appresa nel compito denso, R3 quello del
grafo dato nel regime severo: la misura dichiarata, l'unica dispiegabile su un
tratto mai sensorizzato.

Uso (dalla radice OR3/):

    poetry run python r23_ricampionamento.py
    poetry run python r23_ricampionamento.py --repliche 300
"""
from pathlib import Path
import argparse
import glob as globmod

import numpy as np
import pandas as pd

H = ("15m", "30m", "60m", "120m")
T4 = "data_collection/traffic4cast"
GO = "data_collection/go-mo/gomo"
TARGETS = {
    "t4cmad": f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4clon": f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4cmel": f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
    "d8_2024": f"{GO}/targets_2024_urb_d8.npz",
    "d15_2024": f"{GO}/targets_2024_urb_d15.npz",
    "d8_2023": f"{GO}/targets_2023_urb_d8.npz",
}
NOME = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
        "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023"}

# R2: compito denso, `none` contro `adaptive`. R3: regime severo, `none` contro `fixed`.
OBIETTIVI = {
    "R2": (["fix_classify", "classify", "camp_classify"], "gwn_none", "gwn_adaptive"),
    "R3": (["fix_sparse", "sparse", "camp_sparse"], "gwn_none", "gwn_fixed"),
}


# Numero totale di sensori per contesto, dedotto sui dump del COMPITO DENSO
# dove ogni classe di resto e' popolata e la deduzione e' affidabile. Nel regime
# severo si valuta poco piu' della meta' dei nodi, quindi meta' delle classi
# resta vuota e la deduzione automatica restituisce un valore piu' piccolo che
# NON corrisponde ad alcun sensore: su Madrid dava 276 con 250 gruppi popolati,
# mentre il valore corretto e' 828 con 447 popolati — che coincide con il
# `n_nodi_val` dichiarato nei file di risultato.
NODI = {"t4cmad": 828, "t4clon": 774, "t4cmel": 587,
        "d8_2024": 445, "d15_2024": 384, "d8_2023": 444}


def n_nodi(idx, y, lo=200, hi=1000, soglia=0.90):
    v = {}
    for K in range(lo, hi):
        n = idx % K
        c = np.maximum(np.bincount(n, minlength=K), 1)
        q = np.bincount(n, weights=(y == 2), minlength=K) / c
        v[K] = q.std()
    lim = soglia * max(v.values())
    return min(K for K, s in v.items() if s >= lim)


def blocchi(percorso, tag):
    if not globmod.glob(percorso):
        return None
    z = np.load(percorso, allow_pickle=True)
    out = []
    for h in H:
        k = [x[3:] for x in z.files
             if x.startswith("tag") and str(z[x]) == f"{tag}|{h}"]
        if not k:
            return None
        i = k[0]
        out.append((z[f"p{i}"].astype("float32"), z[f"y{i}"].astype(int),
                    z[f"idx{i}"].astype(int)))
    return out


def pesi(c):
    z = np.load(TARGETS[c], allow_pickle=True)
    C = z["congestion_emp"]
    T = C.shape[0]
    fr = np.array([(C[: int((T - 8) * 0.7)] == k).sum() for k in (1, 2, 3)], float)
    return fr.sum() / (np.maximum(fr, 1) * 3)


def wce(b, w, K=None, sel=None):
    v = []
    for P, Y, idx in b:
        m = np.isin(idx % K, sel) if sel is not None else slice(None)
        y = Y[m]
        p = np.clip(P[m][np.arange(len(y)), y], 1e-7, 1)
        v.append(float(np.sum(w[y] * -np.log(p)) / np.sum(w[y])))
    return float(np.mean(v))


def main() -> int:
    ap = argparse.ArgumentParser(description="R2 e R3 con incertezza a livello di dato")
    ap.add_argument("--probs", default="replication/probs")
    ap.add_argument("--repliche", type=int, default=1000)
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--obiettivi", nargs="*", default=["R2", "R3"])
    a = ap.parse_args()
    rng = np.random.default_rng(0)

    for ob in a.obiettivi:
        schemi, base, trattato = OBIETTIVI[ob]
        print("=" * 96)
        print(f"{ob}: {base} contro {trattato}")
        print("=" * 96)
        print(f"{'contesto':10s} {'fonte':14s} {'nodi':>5} {'stima':>9} "
              f"{'IC ricampionamento':>24} {'IC a t':>20} {'rapp.':>7}")
        for c, n in NOME.items():
            w = pesi(c)
            usato = None
            for p in schemi:
                if all(blocchi(f"{a.probs}/{p}_{c}_s{s}.npz", base)
                       and blocchi(f"{a.probs}/{p}_{c}_s{s}.npz", trattato)
                       for s in range(a.semi)):
                    usato = p
                    break
            if usato is None:
                print(f"{n:10s} nessuno schema completo su {a.semi} semi")
                continue
            S = [(blocchi(f"{a.probs}/{usato}_{c}_s{s}.npz", base),
                  blocchi(f"{a.probs}/{usato}_{c}_s{s}.npz", trattato))
                 for s in range(a.semi)]

            # stima puntuale dai file di risultato
            mc = []
            for s in range(a.semi):
                f = globmod.glob(f"replication/*/{usato}_{c}_s{s}.csv")
                if not f:
                    mc = []
                    break
                d = pd.read_csv(f[0])
                cm = "model" if "model" in d.columns else "mode"
                vb = d[d[cm] == base].wCE.mean()
                vt = d[d[cm] == trattato].wCE.mean()
                mc.append(100 * (vb - vt) / vb)

            K = NODI.get(c) or n_nodi(S[0][0][0][2], S[0][0][0][1])
            # si ricampionano i soli nodi POPOLATI: includere le classi vuote
            # diluirebbe il ricampionamento con blocchi privi di celle
            pres = np.unique(S[0][0][0][2] % K)
            nodi = pres
            pt = [100 * (wce(b, w) - wce(t, w)) / wce(b, w) for b, t in S]
            B = []
            for _ in range(a.repliche):
                i = rng.integers(0, a.semi, a.semi)
                sel = rng.choice(nodi, len(nodi), replace=True)
                B.append(np.mean([
                    100 * (wce(S[k][0], w, K, sel) - wce(S[k][1], w, K, sel))
                    / wce(S[k][0], w, K, sel) for k in i]))
            lo, hi = np.percentile(B, [2.5, 97.5])
            m = np.mean(mc) if mc else np.mean(pt)
            centro = np.mean(B)
            lo, hi = m + (lo - centro), m + (hi - centro)
            sd = np.std(mc if mc else pt, ddof=1)
            hwt = 2.776 * sd / np.sqrt(a.semi)
            rap = (hi - lo) / max(2 * hwt, 1e-9)
            print(f"{n:10s} {usato:14s} {len(nodi):5d} {m:+8.2f}% "
                  f"[{lo:+10.2f};{hi:+9.2f}] [{m - hwt:+8.2f};{m + hwt:+7.2f}] "
                  f"{rap:6.1f}x")
        print()

    print("  Le tre colonne del quadro degli effetti devono avere intervalli della")
    print("  MEDESIMA natura: se R1 e' di ricampionamento, lo devono essere anche")
    print("  R2 e R3, altrimenti si confrontano larghezze che misurano cose diverse.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
