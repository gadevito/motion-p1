#!/usr/bin/env python3
"""
Confronto fra la campagna congelata e quella appaiata.
=======================================================
Nessun addestramento. Risponde ai punti 4 e 5 dell'analisi fissata
nell'addendum:

    4. confronto DESCRITTIVO della struttura per colonna, prima e dopo
    5. differenze fra la VECCHIA e la NUOVA LEGACY

**IL SECONDO E' QUELLO CHE QUALIFICA IL PRIMO.** Se la nuova LEGACY si muove
quanto la differenza fra le varianti, un eventuale miglioramento non e'
attribuibile all'allineamento: si sarebbe spostato tutto, non solo cio' che
l'intervento tocca.

LA VECCHIA LEGACY E LA NUOVA hanno lo STESSO stato iniziale — l'audit lo ha
verificato, impronte `0c7e65475b66992a`, `7fdc15521658bffe`, `0fd3d4a851c7a5d4` —
e gli stessi dati, partizioni, semi e iperparametri. **Ogni differenza fra loro e'
variabilita' numerica di esecuzione**, non effetto dell'intervento: l'intervento
tocca la sola BASE-CORRECTED.

Se le due LEGACY differiscono, il backend non e' deterministico su questa
macchina, e la cosa va dichiarata.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/confronta_campagne.py
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.analizza_raccordo import (  # noqa: E402
    CONTESTI, aggregati, carica, controlla, perdita, pesi_classe)


def matrice_delta(dir_camp: Path, dir_pesi: Path, contesto):
    """delta[p, s] e le perdite delle due varianti."""
    G = np.full((3, 3), np.nan)
    LA = np.full((3, 3), np.nan)
    LB = np.full((3, 3), np.nan)
    for p in (0, 1, 2):
        w = pesi_classe(contesto, p, dir_pesi).vettore()
        for s in (0, 1, 2):
            D = carica(dir_camp, contesto, p, s)
            if D is None:
                continue
            controlla(D, contesto, p, s)
            _, Sa, Wa = aggregati(D["LEGACY"], w)
            _, Sb, Wb = aggregati(D["BASE-CORRECTED"], w)
            u = np.ones(len(Sa))
            la, lb = perdita(Sa, Wa, u), perdita(Sb, Wb, u)
            LA[p, s], LB[p, s] = la, lb
            if np.isfinite(la) and la > 0:
                G[p, s] = 100 * (lb - la) / la
    return G, LA, LB


def struttura(G):
    """Dispersione fra partizioni e fra inizializzazioni."""
    mp = np.nanmean(G, 1)
    ms = np.nanmean(G, 0)
    fra_p = float(np.nanstd(mp, ddof=1))
    fra_s = float(np.nanstd(ms, ddof=1))
    entro = float(np.nanmean([np.nanstd(G[p], ddof=1) for p in range(3)]))
    return {"media": float(np.nanmean(G)), "fra_partizioni": fra_p,
            "fra_inizializzazioni": fra_s, "entro_partizione": entro,
            "rapporto": fra_p / max(entro, 1e-9), "per_seme": ms.tolist()}


def main() -> int:
    ap = argparse.ArgumentParser(description="confronto fra le campagne")
    ap.add_argument("--congelata", type=Path,
                    default=Path("results/evoluzione/raccordo"))
    ap.add_argument("--appaiata", type=Path,
                    default=Path("results/evoluzione/raccordo_appaiato"))
    ap.add_argument("--pesi", type=Path,
                    default=Path("results/evoluzione/pesi"))
    a = ap.parse_args()

    print("=" * 88)
    print("CONFRONTO FRA LE CAMPAGNE — congelata contro appaiata")
    print("=" * 88)
    print(f"  congelata {a.congelata}")
    print(f"  appaiata  {a.appaiata}")
    print("\n  L'intervento tocca la SOLA BASE-CORRECTED: `stat`, `e1` ed `e2`")
    print("  presi dallo stato iniziale di LEGACY. La nuova LEGACY dovrebbe")
    print("  quindi coincidere con la vecchia.")

    for c in CONTESTI:
        print(f"\n{'=' * 88}\n{c}\n{'=' * 88}")
        try:
            Go, LAo, LBo = matrice_delta(a.congelata, a.pesi, c)
            Gn, LAn, LBn = matrice_delta(a.appaiata, a.pesi, c)
        except Exception as e:                          # noqa: BLE001
            print(f"  non confrontabile: {type(e).__name__}: {e}")
            continue

        # ---- [5] la VECCHIA e la NUOVA LEGACY ---------------------------
        d = LAn - LAo
        rel = 100 * d / LAo
        print(f"\n  [5] il controllo LEGACY: vecchia contro nuova")
        print(f"     {'':6s} " + "".join(f"{'s'+str(s):>13}" for s in (0, 1, 2)))
        for p in (0, 1, 2):
            print(f"     p{p}    " + "".join(
                f"{rel[p, s]:+12.4f}%" for s in (0, 1, 2)))
        mx = float(np.nanmax(np.abs(rel)))
        identiche = mx < 1e-9
        print(f"\n     scarto relativo massimo {mx:.2e}%")
        if identiche:
            print(f"     LE DUE LEGACY COINCIDONO: il backend e' deterministico")
            print(f"     e l'intervento non ha toccato il controllo.")
        else:
            print(f"     LE DUE LEGACY DIFFERISCONO. L'intervento tocca la sola")
            print(f"     BASE-CORRECTED, sicche' questa e' VARIABILITA' NUMERICA")
            print(f"     DI ESECUZIONE: il backend non e' deterministico qui.")
            print(f"     Va confrontata con la differenza fra le varianti prima")
            print(f"     di attribuire un miglioramento all'allineamento.")

        # ---- [4] la struttura per colonna, prima e dopo -----------------
        so, sn = struttura(Go), struttura(Gn)
        print(f"\n  [4] struttura della dispersione")
        print(f"     {'':22s} {'congelata':>12} {'appaiata':>12}  variazione")
        for k, eti in (("media", "delta medio"),
                       ("fra_partizioni", "fra partizioni"),
                       ("fra_inizializzazioni", "fra inizializzazioni"),
                       ("entro_partizione", "entro partizione")):
            v = sn[k] - so[k]
            print(f"     {eti:22s} {so[k]:12.4f} {sn[k]:12.4f}  {v:+11.4f}")
        print(f"     {'rapporto p/s':22s} {so['rapporto']:12.3f} "
              f"{sn['rapporto']:12.3f}")

        print(f"\n     delta medio per SEME (la struttura per colonna)")
        print(f"     {'':10s} " + "".join(f"{'s'+str(s):>12}" for s in (0, 1, 2)))
        print(f"     {'congelata':10s} "
              + "".join(f"{so['per_seme'][s]:+11.3f}%" for s in (0, 1, 2)))
        print(f"     {'appaiata':10s} "
              + "".join(f"{sn['per_seme'][s]:+11.3f}%" for s in (0, 1, 2)))
        amp_o = max(so["per_seme"]) - min(so["per_seme"])
        amp_n = max(sn["per_seme"]) - min(sn["per_seme"])
        print(f"     escursione fra i semi: {amp_o:.3f} -> {amp_n:.3f} "
              f"({'attenuata' if amp_n < amp_o else 'invariata o accresciuta'})")

    print(f"\n{'=' * 88}")
    print("  COME NON LEGGERE QUESTO CONFRONTO. Se la struttura per colonna si")
    print("  attenua, e' evidenza di SENSIBILITA' all'inizializzazione comune,")
    print("  non una spiegazione esaustiva. Se sopravvive, l'allineamento di")
    print("  questi moduli e' escluso come spiegazione SUFFICIENTE.")
    print("\n  E in nessun caso si dichiara che il disallineamento «spiegava il")
    print("  deterioramento»: va valutato anche quanto si muove il controllo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
