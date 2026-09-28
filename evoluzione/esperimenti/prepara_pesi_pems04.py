#!/usr/bin/env python3
"""
Pesi delle classi per PEMS04, sul NUOVO bersaglio.
===================================================
**I pesi non si trasferiscono.** Il bersaglio e' una classificazione della
velocita' rispetto al riferimento empirico di rete: le frequenze sono altre, e
si ricalcolano sulle sole origini ammissibili del periodo di ADDESTRAMENTO.

**Non si usano le frequenze del test** per modificare la definizione delle
classi: le soglie restano quelle dichiarate prima della ricognizione.

Su PEMS04 **ogni contesto e' una partizione**, quindi tre contesti con
partizione 0, 1, 2 rispettivamente.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prepara_pesi_pems04.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.pesi import (  # noqa: E402
    calcola as calcola_pesi, salva as salva_pesi)
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    ORIZZONTI, _carica, _partizioni)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE  # noqa: E402

OUT = Path("results/evoluzione")
NUOVA = OUT / "pesi_pems04"


def main() -> int:
    NUOVA.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("PESI DELLE CLASSI — PEMS04, nuovo bersaglio")
    print("=" * 78)
    rapp = {}
    for p in (0, 1, 2):
        c = f"PEMS04_p{p}"
        D = _carica(c, OUT / "maschere")
        amm = GR.maschera_origini(GR.passi_regolari(D["ts"]))
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[p])})
        orig = GR.filtra(ist["addestramento"], amm)
        P = calcola_pesi(c, p, D["classe"], nodi["addestramento"], orig,
                         ORIZZONTI, versione_codice="pems04_riferimento_rete")
        salva_pesi(P, NUOVA)
        freq = [float(np.mean(D["classe"][np.ix_(orig + h, nodi["addestramento"])]
                              == k)) for h in (1,) for k in (1, 2, 3)]
        rapp[c] = {"origini": int(len(orig)),
                   "origini_nominali": int(len(ist["addestramento"])),
                   "pesi": P.pesi, "frequenze_orizzonte_1": freq}
        print(f"  {c}  origini {len(orig)}/{len(ist['addestramento'])}  "
              f"pesi {np.round(P.pesi, 4).tolist()}")
        print(f"     frequenze a 15 min: "
              + ", ".join(f"{x:.2%}" for x in freq))
    (NUOVA / "rapporto_pesi_pems04.json").write_text(json.dumps(rapp, indent=2))
    print(f"\n  3 artefatti in {NUOVA}")
    print(f"  **le soglie delle classi non sono state toccate**: restano quelle")
    print(f"  dichiarate prima della ricognizione del dato")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
