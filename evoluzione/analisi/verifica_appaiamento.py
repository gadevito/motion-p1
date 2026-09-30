#!/usr/bin/env python3
"""
I confronti appaiati sono davvero appaiati?
============================================
Il ricampionamento dei NODI usa l'indice di riga di `A_per_nodo`. Se due bracci
avessero nodi diversi, o gli stessi in ordine diverso, confronterebbe entita'
diverse **senza errore**.

Verifica, per ogni cella (citta', partizione, seme) e ogni coppia di bracci:

    [1] stessi nodi, nello stesso ORDINE
    [2] stesse origini di valutazione
    [3] stessi t0 e t1
    [4] la wCE dagli aggregati per nodo coincide con quella ricalcolata
        dalle probabilita' cella per cella

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/verifica_appaiamento.py
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.ricostruisci_predizioni import (  # noqa: E402
    aggregati_per_nodo, wce_da_predizioni)

CITTA = ("Madrid", "Londra", "Melbourne")
BRACCI = {"F0p": "predizioni_e2", "F0meanp": "predizioni_e2",
          "Fp": "predizioni_e2", "F0": "predizioni_f0",
          "F": "predizioni_fase3", "C": "predizioni_fase3"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radice", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    guai, celle, ric = [], 0, 0
    from evoluzione.analisi.pesi import carica as carica_pesi
    print("=" * 80)
    print("APPAIAMENTO DEI CONFRONTI")
    print("=" * 80)
    for c in CITTA:
        for f in sorted((a.radice / "predizioni_e2").glob(f"F0p_{c}_p*_s*.npz")):
            p = int(f.stem.split("_p")[1].split("_")[0])
            s = int(f.stem.split("_s")[1])
            rif = None
            for b, dd in BRACCI.items():
                g = a.radice / dd / f"{b}_{c}_p{p}_s{s}.npz"
                if not g.exists():
                    guai.append(f"{g.name}: assente"); continue
                z = np.load(g, allow_pickle=True)
                chiave = (tuple(z["nodi"].tolist()), tuple(z["origini"].tolist()),
                          int(z["t0"]), int(z["t1"]))
                if rif is None:
                    rif, nome_rif = chiave, b
                elif chiave != rif:
                    quale = ("nodi" if chiave[0] != rif[0] else
                             "origini" if chiave[1] != rif[1] else "t0/t1")
                    guai.append(f"{c} p{p} s{s}: {b} differisce da {nome_rif} "
                                f"per {quale}")
            celle += 1
            # [4] su un campione: gli aggregati riproducono la wCE per cella?
            if celle % 20 == 1:
                pesi = np.asarray(carica_pesi(a.radice / "pesi_griglia", c, p)
                                  .vettore(), dtype="float64")
                z = np.load(a.radice / "predizioni_e2" /
                            f"F0p_{c}_p{p}_s{s}.npz", allow_pickle=True)
                w1, _ = wce_da_predizioni(z["prob"], z["y"], z["m"], pesi)
                A, Bm, _ = aggregati_per_nodo(z["prob"], z["y"], z["m"], pesi)
                num, den = A.sum(0), Bm.sum(0)
                w2 = float(np.nanmean(np.where(den > 0, num / np.maximum(den, 1e-12),
                                               np.nan)))
                ric += 1
                if abs(w1 - w2) > 1e-9:
                    guai.append(f"{c} p{p} s{s}: aggregati contro celle "
                                f"{w1:.12f} vs {w2:.12f}")
                # e gli aggregati salvati coincidono con quelli ricalcolati?
                if not np.allclose(A, z["A_per_nodo"], atol=0, rtol=1e-12):
                    guai.append(f"{c} p{p} s{s}: A_per_nodo salvato diverso")
    print(f"  {celle} celle controllate, {ric} ricalcoli cella per cella")
    print(f"  **{len(guai)} anomalie**")
    for g in guai[:10]:
        print(f"     {g}")
    return 0 if not guai else 1


if __name__ == "__main__":
    raise SystemExit(main())
