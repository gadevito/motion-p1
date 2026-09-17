#!/usr/bin/env python3
"""
R3 letto in RICHIAMO, con incertezza a livello di dato.
========================================================
Nessun addestramento: riaggrega i dump di probabilita' gia' salvati. Adotta la
medesima procedura di `r1_ricampionamento.py` e `r23_ricampionamento.py`, cosi'
che la lettura in richiamo sia omogenea alle altre tre.

PERCHE' SERVE. La lettura in richiamo oggi ha le sole stime puntuali, quindi non
si puo' dire se le differenze siano distinguibili da zero. E' rilevante perche'
su Melbourne il richiamo cambia SEGNO rispetto all'entropia: il grafo dato
migliora l'entropia e peggiora il richiamo, e senza intervallo non si sa se quel
cambio sia reale.

DUE COSE CHE RENDONO IL RICHIAMO DIVERSO DALL'ENTROPIA.

  Il richiamo si calcola sulla SOLA classe critica, che vale fra il 2,9 e il
  15,2 per cento delle celle: la numerosita' effettiva e' quindi molto minore, e
  gli intervalli sono per costruzione piu' ampi. Un esito non decidibile qui NON
  e' confrontabile con un esito deciso sull'entropia.

  E il rapporto fra i due richiami esplode dove il denominatore e' piccolo: sui
  contesti a spire il modello privo di grafo intercetta pochissimi episodi, e la
  variazione relativa supera il cento per cento senza che l'effetto assoluto sia
  proporzionalmente grande. Si riportano quindi anche i richiami assoluti.

LE TRE CONVENZIONI, identiche alle altre:

  * stima puntuale dai dump (il richiamo non e' nei file di risultato in forma
    appaiata per ramo), larghezza dal ricampionamento, intervallo centrato;
  * si ricampionano i soli nodi effettivamente valutati;
  * il numero di sensori si legge dal contesto, non si deduce dai dump del
    regime severo dove meta' delle posizioni e' vuota.

Uso (dalla radice OR3/):

    poetry run python r3_richiamo.py
    poetry run python r3_richiamo.py --repliche 300
"""
import argparse
import glob as globmod

import numpy as np

H = ("15m", "30m", "60m", "120m")
NOME = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
        "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023"}
# Numero totale di sensori, dedotto sui dump del compito denso dove ogni classe
# di resto e' popolata. Nel regime severo si valuta poco piu' della meta' dei
# nodi, e la deduzione automatica restituirebbe un valore che non corrisponde
# ad alcun sensore.
NODI = {"t4cmad": 828, "t4clon": 774, "t4cmel": 587,
        "d8_2024": 445, "d15_2024": 384, "d8_2023": 444}
SCHEMI = ["fix_sparse", "sparse", "camp_sparse"]


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


def richiamo(b, K=None, sel=None):
    """Richiamo sulla classe critica alla regola della classe piu' probabile,
    mediato sui quattro orizzonti."""
    v = []
    for P, Y, idx in b:
        m = np.isin(idx % K, sel) if sel is not None else slice(None)
        y = Y[m]
        p = P[m]
        crit = (y == 2)
        if not crit.sum():
            continue
        v.append(float(((p.argmax(1) == 2) & crit).sum() / crit.sum()))
    return float(np.mean(v)) if v else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description="R3 in richiamo, incertezza a livello di dato")
    ap.add_argument("--probs", default="replication/probs")
    ap.add_argument("--repliche", type=int, default=1000)
    ap.add_argument("--semi", type=int, default=5)
    a = ap.parse_args()
    rng = np.random.default_rng(0)

    print(f"{'contesto':10s} {'fonte':13s} {'nodi':>5} {'senza grafo':>11} "
          f"{'grafo dato':>11} {'R3 richiamo':>10} {'IC ricampionamento':>24}")
    for c, n in NOME.items():
        usato = None
        for p in SCHEMI:
            if all(blocchi(f"{a.probs}/{p}_{c}_s{s}.npz", "gwn_none")
                   and blocchi(f"{a.probs}/{p}_{c}_s{s}.npz", "gwn_fixed")
                   for s in range(a.semi)):
                usato = p
                break
        if usato is None:
            print(f"{n:10s} nessuno schema completo su {a.semi} semi")
            continue
        S = [(blocchi(f"{a.probs}/{usato}_{c}_s{s}.npz", "gwn_none"),
              blocchi(f"{a.probs}/{usato}_{c}_s{s}.npz", "gwn_fixed"))
             for s in range(a.semi)]

        K = NODI[c]
        nodi = np.unique(S[0][0][0][2] % K)          # soli nodi valutati
        rn = np.mean([richiamo(b, K) for b, _ in S])
        rf = np.mean([richiamo(t, K) for _, t in S])
        pt = [100 * (richiamo(t, K) - richiamo(b, K)) / richiamo(b, K) for b, t in S]
        m = float(np.mean(pt))

        B = []
        for _ in range(a.repliche):
            i = rng.integers(0, a.semi, a.semi)
            sel = rng.choice(nodi, len(nodi), replace=True)
            v = []
            for k in i:
                rb = richiamo(S[k][0], K, sel)
                rt = richiamo(S[k][1], K, sel)
                if np.isfinite(rb) and rb > 0:
                    v.append(100 * (rt - rb) / rb)
            if v:
                B.append(np.mean(v))
        lo, hi = np.percentile(B, [2.5, 97.5])
        lo, hi = m + (lo - np.mean(B)), m + (hi - np.mean(B))
        segno = "" if lo * hi > 0 else "   TOCCA LO ZERO"
        print(f"{n:10s} {usato:13s} {len(nodi):5d} {rn:11.3f} {rf:11.3f} "
              f"{m:+9.2f}% [{lo:+10.2f};{hi:+9.2f}]{segno}")

    print("\n  Il richiamo si calcola sulla sola classe critica, che vale fra il 2,9 e")
    print("  il 15,2 per cento delle celle: la numerosita' effettiva e' molto minore")
    print("  che sull'entropia e gli intervalli sono per costruzione piu' ampi. Un")
    print("  esito non decidibile qui NON e' confrontabile con uno deciso sull'entropia.")
    print("\n  Dove il richiamo del ramo privo di grafo e' molto basso, la variazione")
    print("  relativa supera il cento per cento senza che l'effetto assoluto sia")
    print("  proporzionalmente grande: si riportano percio' anche i richiami assoluti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
