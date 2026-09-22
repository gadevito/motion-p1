#!/usr/bin/env python3
"""
Pesi delle classi sulle ORIGINI AMMISSIBILI della griglia reale.
=================================================================
I pesi contano le classi dei bersagli `classe[t + h]` per ogni origine t di
addestramento: **dipendono dalla selezione delle origini**, e con la regola
della griglia vanno ricalcolati.

**In una cartella nuova**, `pesi_griglia`: i pesi delle campagne storiche
restano dove sono. Si preparano PRIMA dell'addestramento, una volta sola:
calcolarli durante il training, con piu' processi, produrrebbe scritture
concorrenti.

La normalizzazione NON cambia: usa le righe del periodo come osservazioni.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prepara_pesi_griglia.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.pesi import (  # noqa: E402
    calcola as calcola_pesi, carica as carica_pesi, salva as salva_pesi)
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    ORIZZONTI, _carica, _partizioni)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE  # noqa: E402

OUT = Path("results/evoluzione")
NUOVA, VECCHIA = OUT / "pesi_griglia", OUT / "pesi"


def main() -> int:
    NUOVA.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("PESI DELLE CLASSI SULLE ORIGINI AMMISSIBILI")
    print("=" * 78)
    rapp = {}
    for c in ("Madrid", "Londra", "Melbourne"):
        D = _carica(c, OUT / "maschere")
        amm = GR.maschera_origini(GR.passi_regolari(D["ts"]))
        for p in (0, 1, 2):
            nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
                SEME_PARTIZIONE[p])})
            orig = GR.filtra(ist["addestramento"], amm)
            P = calcola_pesi(c, p, D["classe"], nodi["addestramento"], orig,
                             ORIZZONTI, versione_codice="griglia_reale")
            salva_pesi(P, NUOVA)
            V = carica_pesi(VECCHIA, c, p)
            rapp[f"{c}/p{p}"] = {
                "origini": len(orig), "origini_storiche": len(ist["addestramento"]),
                "pesi": P.pesi, "pesi_storici": V.pesi,
                "scarto_massimo": float(np.abs(np.array(P.pesi) -
                                               np.array(V.pesi)).max())}
            print(f"  {c:10s} p{p}  origini {len(orig):5d}/{len(ist['addestramento'])}"
                  f"  pesi {np.round(P.pesi, 4).tolist()}  "
                  f"scarto dai storici {rapp[f'{c}/p{p}']['scarto_massimo']:.4f}")
    (NUOVA / "rapporto_pesi_griglia.json").write_text(json.dumps(rapp, indent=2))
    print(f"\n  9 artefatti in {NUOVA}; i pesi storici in {VECCHIA} non sono toccati")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
