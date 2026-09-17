#!/usr/bin/env python3
"""
Quanti semi servirebbero a decidere il test di equivalenza nella fascia di testa.
=================================================================================
Nessuna esecuzione: il calcolo discende dalla dispersione gia' misurata.

IL PUNTO CHE DECIDE. L'intervallo di equivalenza deve stare per intero dentro il
margine, e la sua semiampiezza vale t(n-1) · s / radice(n). Aumentare i semi
riduce il secondo fattore ma NON sposta la stima puntuale: se il valore assoluto
della differenza gia' eccede il margine, nessuna numerosita' rende decidibile
l'equivalenza — il limite non e' nel disegno ma nella grandezza dell'effetto.

Lo script distingue quindi tre esiti:

  * differenza dentro il margine e pochi semi in piu' bastano: lacuna colmabile,
    e il numero va dichiarato;
  * dentro il margine ma con numerosita' elevata: il limite resta e diventa
    quantificato;
  * differenza fuori dal margine: nessuna numerosita' basta, e il limite va
    dichiarato come proprieta' del confronto e non del disegno.

SULLA COMPONENTE DI VARIABILITA'. La cautela sollevata sul ricampionamento e'
pertinente: dove l'incertezza risiede nella dispersione fra semi, aumentare le
replicazioni allarga l'intervallo anziche' restringerlo, e i semi sono la sola
leva. Lo script lavora percio' direttamente sulla dispersione fra semi, che e' la
componente che la numerosita' effettivamente riduce.

Uso (dalla radice OR3/):

    poetry run python semi_equivalenza.py
    poetry run python semi_equivalenza.py --margine 1.0 --confidenza 0.90
"""
import argparse
import glob as globmod
import itertools
import math

import numpy as np
import pandas as pd
from scipy import stats

ORIZZONTI = ["15m", "30m", "60m", "120m"]
NOME = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
        "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023"}
# fascia di testa come §7.2.1 la definisce: identita' di nodo appresa
FASCIA = {"gwn_adaptive": ["fix_classify", "classify", "camp_classify"],
          "gwn_none":     ["fix_classify", "classify", "camp_classify"],
          "staeformer":   ["fixgraph_sota", "prec_sota", "sota"],
          "agcrn":        ["fixgraph_rnn", "prec_rnn", "rnn"]}


def serie(c, modello, schemi, semi, orizzonte=None):
    """Entropia per seme: media sui quattro orizzonti, o su uno solo."""
    for p in schemi:
        v = []
        for s in range(semi):
            f = sorted(globmod.glob(f"replication/*/{p}_{c}_s{s}.csv"))
            if not f:
                break
            d = pd.read_csv(f[0])
            cm = "model" if "model" in d.columns else "mode"
            q = d[d[cm] == modello]
            if orizzonte and "horizon" in q.columns:
                q = q[q.horizon == orizzonte]
            if not len(q):
                break
            v.append(float(q.wCE.mean()))
        if len(v) == semi:
            return v
    return None


def semi_necessari(diff, margine, conf, massimo=200):
    """Minima numerosita' per cui l'intervallo sta dentro il margine.

    Restituisce None se la stima puntuale eccede gia' il margine: in tal caso
    l'intervallo non vi rientra per alcuna numerosita', poiche' il suo centro
    e' fuori.
    """
    m = float(np.mean(diff))
    s = float(np.std(diff, ddof=1))
    if abs(m) >= margine:
        return None, m, s
    for n in range(3, massimo + 1):
        t = stats.t.ppf(1 - (1 - conf) / 2, n - 1)
        if abs(m) + t * s / math.sqrt(n) <= margine:
            return n, m, s
    return massimo + 1, m, s


def main() -> int:
    ap = argparse.ArgumentParser(description="numerosita' per decidere l'equivalenza")
    ap.add_argument("--margine", type=float, default=1.0,
                    help="semiampiezza del margine di equivalenza, in punti percentuali")
    ap.add_argument("--confidenza", type=float, default=0.90,
                    help="0.90 e' la convenzione dei due test unilaterali")
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--escludi", nargs="*", default=[],
                    help="modelli da togliere dalla fascia. Serve a verificare se "
                         "l'indistinguibilita' regga su un sottoinsieme: se un solo "
                         "modello e' responsabile del superamento del margine, "
                         "l'affermazione va ristretta anziche' abbandonata")
    a = ap.parse_args()
    for m in a.escludi:
        FASCIA.pop(m, None)
    if a.escludi:
        print(f"fascia ristretta a: {', '.join(FASCIA)}\n")

    print(f"margine ±{a.margine:.1f}%, intervallo al {100*a.confidenza:.0f}%, "
          f"{a.semi} semi disponibili\n")
    print(f"{'contesto':10s} {'coppia estrema':26s} {'differenza':>10} "
          f"{'disp.':>7} {'semiamp.':>9} {'semi necessari':>16}")

    DISP = {}
    for c, n in NOME.items():
        S = {}
        for m, sch in FASCIA.items():
            v = serie(c, m, sch, a.semi)
            if v:
                S[m] = v
        if len(S) < 2:
            print(f"{n:10s} modelli insufficienti ({len(S)})")
            continue
        # CONVENZIONE della tabella: il modello con entropia maggiore al
        # numeratore, normalizzato sul migliore, sicche' la differenza e'
        # positiva. Invertire l'ordine cambia il segno e sposta il modulo di
        # circa l'uno per cento del valore stesso, perche' cambia il denominatore.
        coppie = []
        for u, v in itertools.combinations(S, 2):
            p1, p2 = (u, v) if np.mean(S[u]) > np.mean(S[v]) else (v, u)
            coppie.append((p1, p2,
                           [100*(S[p1][i]-S[p2][i])/S[p2][i] for i in range(a.semi)]))
        x, y, d = max(coppie, key=lambda q: abs(np.mean(q[2])))
        nn, m, s = semi_necessari(d, a.margine, a.confidenza)
        t = stats.t.ppf(1 - (1 - a.confidenza) / 2, a.semi - 1)
        hw = t * s / math.sqrt(a.semi)
        DISP[c] = (m, s, hw, nn)
        esito = ("MAI" if nn is None else
                 f">{200}" if nn > 200 else f"{nn}")
        dec = "  decidibile" if (nn is not None and nn <= a.semi) else ""
        print(f"{n:10s} {x[:12]+' / '+y[:11]:26s} {m:+9.2f}% {s:6.2f} "
              f"{hw:8.2f} {esito:>16}{dec}")

    print("\n  «MAI» significa che la differenza media eccede gia' il margine: "
          "l'intervallo\n  non vi rientra per alcuna numerosita', poiche' e' il "
          "centro a essere fuori.")

    # ------------------------------------------------- effetto dell'aggregazione
    print(f"\n{'contesto':10s} {'disp. a 15 min':>15} {'disp. sui 4 orizz.':>20} "
          f"{'rapporto':>9}")
    for c, n in NOME.items():
        S1, S4 = {}, {}
        for m, sch in FASCIA.items():
            v1 = serie(c, m, sch, a.semi, "15m")
            v4 = serie(c, m, sch, a.semi)
            if v1 and v4:
                S1[m], S4[m] = v1, v4
        if len(S4) < 2:
            continue
        r = []
        for D in (S1, S4):
            best = max(itertools.combinations(D, 2),
                       key=lambda p: abs(np.mean([100*(D[p[0]][i]-D[p[1]][i])/D[p[1]][i]
                                                  for i in range(a.semi)])))
            x, y = best
            r.append(float(np.std([100*(D[x][i]-D[y][i])/D[y][i]
                                   for i in range(a.semi)], ddof=1)))
        print(f"{n:10s} {r[0]:14.2f} {r[1]:19.2f} {r[1]/max(r[0],1e-9):8.2f}x")
    print("\n  Un rapporto inferiore all'unita' indica che l'aggregazione sui quattro")
    print("  orizzonti riduce la dispersione fra semi, e che l'effetto e' quindi gia'")
    print("  incorporato negli intervalli del criterio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
