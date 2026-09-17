#!/usr/bin/env python3
"""
R1 con incertezza a livello di dato (ricampionamento congiunto).
================================================================
Nessun addestramento: legge i dump di probabilita' gia' salvati.

DUE COSE CHE LO SCRIPT RISOLVE E CHE NON SONO OVVIE.

  1. LA DECODIFICA DEL NODO. I dump salvano `idx`, che e' l'indice PIATTO della
     matrice (tempo x nodi): `nodo = idx % n_nodi`. Il numero di nodi non e'
     pero' salvato, e va dedotto. Il criterio e' la varianza fra gruppi della
     quota di classe critica: con il divisore giusto i gruppi sono i sensori, e
     le loro frequenze differiscono molto perche' alcuni tratti sono
     cronicamente congestionati e altri quasi mai.

     ATTENZIONE AI MULTIPLI. Con un divisore pari al doppio del numero di nodi
     ogni sensore si divide in due gruppi e la varianza resta alta, o cresce
     perche' i gruppi sono piu' piccoli. Prendere l'argmax restituisce quindi un
     multiplo: su d8/2024 dava 890 anziche' 445. Si prende invece il divisore
     MINIMO fra quelli che raggiungono il novanta per cento della varianza
     massima.

  2. LA PROVENIENZA. Il ramo neurale sta in campagne con nomi diversi a seconda
     del contesto: `fix_classify` sui contesti a velocita' ricostruita,
     `classify` sulle tre citta'. Cercare un solo schema fa concludere che i
     dump manchino quando invece esistono. Lo script prova gli schemi in ordine
     e STAMPA quale ha usato, perche' la provenienza fa parte del risultato.

CHE COSA ASPETTARSI. L'intervallo di ricampionamento incorpora l'incertezza a
livello di dato e quello a t la sola dispersione fra inizializzazioni: il primo
dovrebbe risultare piu' ampio. Sui tre contesti a velocita' ricostruita lo e' di
un fattore fra due e cinque; sulle tre citta' le due larghezze sono invece
comparabili, perche' i nodi sono quasi il doppio e il ricampionamento a livello
di nodo si comprime. NON e' un difetto del calcolo: e' una proprieta' dei
contesti, e va riportata come tale anziche' dichiarare un fattore uniforme.

Uso (dalla radice OR3/):

    poetry run python r1_ricampionamento.py
    poetry run python r1_ricampionamento.py --repliche 1000
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
SCHEMI_NN = ["fix_classify", "classify", "camp_classify", "prec_classify"]


def n_nodi(idx, y, lo=200, hi=1000, soglia=0.90):
    """Divisore MINIMO che raggiunge la soglia della varianza massima."""
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
    ap = argparse.ArgumentParser(description="R1 con incertezza a livello di dato")
    ap.add_argument("--probs", default="replication/probs")
    ap.add_argument("--repliche", type=int, default=1000)
    ap.add_argument("--semi", type=int, default=5)
    a = ap.parse_args()
    rng = np.random.default_rng(0)

    print(f"{'contesto':10s} {'fonte':14s} {'nodi':>5} {'R1':>9} "
          f"{'IC ricampionamento':>24} {'IC a t':>20} {'rapporto':>9}")
    for c, n in NOME.items():
        w = pesi(c)
        # Lo schema si sceglie UNA VOLTA per contesto, non seme per seme: con una
        # campagna a meta' il ciclo interno mescolerebbe due campagne diverse
        # senza segnalarlo, e la variabile `usato` riporterebbe solo l'ultima.
        S, usato = [], None
        for p in SCHEMI_NN:
            if all(blocchi(f"{a.probs}/{p}_{c}_s{s}.npz", "gwn_none")
                   for s in range(a.semi)):
                usato = p
                break
        if usato is None:
            print(f"{n:10s} nessuno schema completo su {a.semi} semi")
            continue
        for s in range(a.semi):
            nn = blocchi(f"{a.probs}/{usato}_{c}_s{s}.npz", "gwn_none")
            gb = blocchi(f"{a.probs}/lgbristr_{c}_s{s}.npz", "lgb_fair")
            if nn and gb:
                S.append((nn, gb))
        if len(S) < a.semi:
            print(f"{n:10s} dump incompleti ({len(S)}/{a.semi})")
            continue

        # STIMA PUNTUALE DAL CSV, larghezza dal ricampionamento. Il dump valuta
        # una popolazione leggermente piu' ampia di quella su cui il CSV media —
        # su Madrid 1.488.297 celle contro un filtro ulteriore che il CSV applica —
        # e lo scarto, di dodici o quattordici decimillesimi sulle entropie,
        # si amplifica a due decimi su R1, che e' un rapporto fra grandezze vicine.
        # Del ricampionamento si usa quindi la sola LARGHEZZA.
        mc = []
        for s in range(a.semi):
            fn = globmod.glob(f"replication/*/{usato}_{c}_s{s}.csv")
            fg = globmod.glob(f"replication/*/lgbristr_{c}_s{s}.csv")
            if not (fn and fg):
                mc = []
                break
            dn = pd.read_csv(fn[0]); dg = pd.read_csv(fg[0])
            vn = dn[dn.model == "gwn_none"].wCE.mean()
            vg = dg[dg.model == "lgb_fair"].wCE.mean()
            mc.append(100 * (vg - vn) / vg)
        K = n_nodi(S[0][0][0][2], S[0][0][0][1])
        nodi = np.arange(K)
        pt = [100 * (wce(g, w) - wce(x, w)) / wce(g, w) for x, g in S]
        B = []
        for _ in range(a.repliche):
            i = rng.integers(0, a.semi, a.semi)
            sel = rng.choice(nodi, K, replace=True)
            B.append(np.mean([
                100 * (wce(S[k][1], w, K, sel) - wce(S[k][0], w, K, sel))
                / wce(S[k][1], w, K, sel) for k in i]))
        # L'intervallo va CENTRATO sulla stima puntuale, non sulla media delle
        # repliche: sui contesti primari il dump e il CSV differiscono di pochi
        # decimillesimi sulle entropie, e su un rapporto fra grandezze vicine
        # quello scarto si amplifica fino a due decimi di punto su R1.
        lo, hi = np.percentile(B, [2.5, 97.5])
        m = np.mean(mc) if mc else np.mean(pt)
        centro = np.mean(B)
        lo, hi = m + (lo - centro), m + (hi - centro)
        hwt = 2.776 * np.std(mc if mc else pt, ddof=1) / np.sqrt(a.semi)
        rap = (hi - lo) / max(2 * hwt, 1e-9)
        print(f"{n:10s} {usato:14s} {K:5d} {m:+8.2f}% "
              f"[{lo:+10.2f};{hi:+9.2f}] [{m - hwt:+8.2f};{m + hwt:+7.2f}] "
              f"{rap:8.1f}x")

    print("\n  L'ultima colonna e' il rapporto fra le due larghezze. Un valore sopra")
    print("  l'unita' significa che l'incertezza a livello di dato eccede quella fra")
    print("  semi; sotto l'unita' che le due sono comparabili o invertite, il che")
    print("  accade dove i nodi sono molti e il ricampionamento si comprime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
