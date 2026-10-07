#!/usr/bin/env python3
"""
Fattibilita' di PEMS04 come verifica esterna. **Sola ricognizione.**
=====================================================================
Requisiti da accertare, con numeri e non con aspettative:

    lunghezza della serie e struttura della griglia
    grandezze osservate: flusso, occupazione, velocita'
    copertura per sensore
    definizione CAUSALE del flusso libero e delle classi
    nodi utilizzabili per il disegno 70/15/15
    costo di C e P

SCELTE DA DICHIARARE, fissate qui prima di guardare qualunque prestazione:

    aggregazione     da 5 a 15 minuti: media della velocita', somma del flusso
    flusso libero    percentile 95 della velocita' di CIASCUN sensore, calcolato
                     SOLTANTO sul periodo di addestramento
    classi           rapporto velocita'/flusso libero: >= 0,8 scorrevole,
                     0,5-0,8 moderato, < 0,5 congestionato
    mancanti         velocita' o flusso pari a zero contemporaneamente

**Le soglie non si ritoccano dopo aver visto i risultati.**

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/fattibilita_pems04.py \\
        --file data_collection/pems04/pems04.npz
"""
import argparse
from pathlib import Path

import numpy as np

PASSI_ORA = 12          # 5 minuti
AGG = 3                 # 3 x 5 = 15 minuti
SOGLIE = (0.8, 0.5)
PERC_FF = 95


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, required=True)
    a = ap.parse_args()
    z = np.load(a.file)
    k = "data" if "data" in z else list(z.keys())[0]
    X = z[k]
    print("=" * 80)
    print(f"FATTIBILITA' PEMS04 — {a.file}")
    print("=" * 80)
    print(f"  forma {X.shape}  (istanti, sensori, grandezze)")
    T, N, C = X.shape
    print(f"  {T} istanti a 5 minuti = {T / 288:.1f} giorni, {N} sensori, "
          f"{C} grandezze")
    nomi = ("flusso", "occupazione", "velocita'")[:C]
    for i, n in enumerate(nomi):
        v = X[..., i]
        print(f"     {n:12s} min {v.min():8.2f} max {v.max():8.2f} "
              f"media {v.mean():8.2f}  zeri {np.mean(v == 0):6.2%}")
    if C < 3:
        print("\n  **manca la velocita' o il flusso**: il descrittore non e'")
        print("  ricostruibile per intero. Verifica fermata.")
        return 1

    # ---- aggregazione a 15 minuti -------------------------------------
    Tq = (T // AGG) * AGG
    fl = X[:Tq, :, 0].reshape(-1, AGG, N).sum(1)
    ve = X[:Tq, :, 2].reshape(-1, AGG, N).mean(1)
    oc = X[:Tq, :, 1].reshape(-1, AGG, N).mean(1)
    Tg = fl.shape[0]
    print(f"\n  aggregati: {Tg} istanti a 15 minuti = {Tg / 96:.1f} giorni")
    # ---- mancanti ------------------------------------------------------
    manc = (ve <= 0) & (fl <= 0)
    print(f"  mancanti (velocita' e flusso nulli): {manc.mean():.2%}")
    cop = 1 - manc.mean(0)
    print(f"  copertura per sensore: mediana {np.median(cop):.1%}, "
          f"minimo {cop.min():.1%}")
    for s in (0.5, 0.8, 0.95):
        print(f"     sensori con copertura >= {s:.0%}: {int((cop >= s).sum())} "
              f"su {N}")

    # ---- confini e flusso libero --------------------------------------
    e = Tg - 8
    a_tr, a_va, a_te = 11, int(e * .70), int(e * .85)
    print(f"\n  confini 70/15/15: addestramento 11-{a_va}, validazione "
          f"{a_va}-{a_te}, prova {a_te}-{e}")
    print(f"  giorni: addestramento {(a_va - 11) / 96:.1f}, validazione "
          f"{(a_te - a_va) / 96:.1f}, **prova {(e - a_te) / 96:.1f}**")
    v_tr = np.where(manc[11:a_va], np.nan, ve[11:a_va])
    ff = np.nanpercentile(v_tr, PERC_FF, axis=0)
    print(f"  flusso libero (percentile {PERC_FF} sul solo addestramento): "
          f"mediana {np.median(ff):.1f}, min {np.nanmin(ff):.1f}, "
          f"max {np.nanmax(ff):.1f}")
    rap = np.where(manc, np.nan, ve / np.maximum(ff, 1e-6))
    cl = np.where(np.isnan(rap), 0,
                  np.where(rap >= SOGLIE[0], 1,
                           np.where(rap >= SOGLIE[1], 2, 3)))
    tot = (cl > 0).sum()
    print(f"\n  classi con soglie {SOGLIE}:")
    for i, n in ((1, "scorrevole"), (2, "moderato"), (3, "congestionato")):
        print(f"     {n:15s} {np.mean(cl == i):7.2%}  "
              f"({(cl == i).sum() / max(tot, 1):7.2%} delle celle assegnate)")
    print(f"     non assegnate {np.mean(cl == 0):7.2%}")

    # ---- nodi utilizzabili --------------------------------------------
    usab = cop >= 0.5
    K = int(usab.sum())
    print(f"\n  nodi utilizzabili (copertura >= 50%): {K} su {N}")
    # stessa formula di addestramento._partizioni: a = int(K*.70), b = int(K*.85)
    ka, kb = int(K * .70), int(K * .85)
    print(f"     70/15/15 -> iniziali {ka}, validazione {kb - ka}, **nuovi {K - kb}** "
          f"(formula di `_partizioni`)")
    print(f"\n  costo di C e P: 3 partizioni x 12 semi x 2 bracci = 72 "
          f"addestramenti")
    print(f"\n  LIMITI DA DICHIARARE")
    print(f"     nessuna marca temporale nel file: la griglia si assume "
          f"regolare, non verificabile")
    print(f"     flusso libero e classi definiti da noi, non nativi")
    print(f"     periodo di prova di {(e - a_te) / 96:.0f} giorni, inferiore ai "
          f"21 richiesti per la conferma temporale")
    print(f"     una sola citta': il verdetto congiunto su tre non si applica")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
