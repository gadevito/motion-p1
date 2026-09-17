"""Diagnostica: da dove viene l'ampiezza degli intervalli.

NON cambia il protocollo ne' il criterio: scompone la dispersione gia' misurata
per capire quale livello domini. E' una lettura, non una nuova analisi.
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from evoluzione.analisi.analizza_raccordo import (
    CONTESTI, VARIANTI, aggregati, carica, pesi_classe, perdita)

D = Path("results/evoluzione/raccordo")
PZ = Path("results/evoluzione/pesi")
print(f"{'citta':11s} {'delta[p,s] per partizione e inizializzazione':>52}")
for c in CONTESTI:
    G = np.full((3, 3), np.nan)
    for p in range(3):
        # i pesi vengono dall'ARTEFATTO, e sono per PARTIZIONE
        w = pesi_classe(c, p, PZ).vettore()
        for s in range(3):
            X = carica(D, c, p, s)
            if X is None: continue
            _, Sa, Wa = aggregati(X["LEGACY"], w)
            _, Sb, Wb = aggregati(X["BASE-CORRECTED"], w)
            u = np.ones(len(Sa))
            la, lb = perdita(Sa, Wa, u), perdita(Sb, Wb, u)
            G[p, s] = 100 * (lb - la) / la
    mp = np.nanmean(G, 1)                       # media per partizione
    print(f"\n{c}")
    for p in range(3):
        print(f"  p{p}  " + "  ".join(f"{G[p,s]:+7.3f}" for s in range(3))
              + f"   media {mp[p]:+7.3f}")
    fra_part = float(np.nanstd(mp, ddof=1))
    entro = float(np.nanmean([np.nanstd(G[p], ddof=1) for p in range(3)]))
    print(f"  dispersione FRA partizioni {fra_part:6.3f}  "
          f"ENTRO (fra inizializzazioni) {entro:6.3f}  "
          f"rapporto {fra_part/max(entro,1e-9):5.2f}x")
