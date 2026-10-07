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
    poetry run python evoluzione/esperimenti/prepara_pesi_pems04.py \\
        --nome PEMS08 --fine-periodo 3840         # E6 parte B: pesi_pems08

Con `--fine-periodo t0` le origini di addestramento sono quelle di
`_partizioni(fine=t0)`, cioe' [11, int(t0·0,70/0,85)): le stesse del
riferimento stimato dall'estrattore.
"""
import argparse
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nome", default="PEMS04", help="PEMS04 o PEMS08")
    ap.add_argument("--fine-periodo", type=int, default=None)
    ap.add_argument("--partizioni", type=int, default=3, help="E6 parte B: 6")
    a = ap.parse_args()
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE_E6
    semi_part = SEME_PARTIZIONE_E6 if a.partizioni == 6 else SEME_PARTIZIONE
    if a.partizioni not in (3, 6):
        raise SystemExit("--partizioni: 3 o 6")
    nome, pref = a.nome, a.nome.lower()
    NUOVA = OUT / f"pesi_{pref}"
    NUOVA.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print(f"PESI DELLE CLASSI — {nome}, nuovo bersaglio"
          + (f" (fine del periodo {a.fine_periodo})" if a.fine_periodo is not None else ""))
    print("=" * 78)
    rapp = {}
    for p in range(a.partizioni):
        c = f"{nome}_p{p}"
        D = _carica(c, OUT / "maschere")
        amm = GR.maschera_origini(GR.passi_regolari(D["ts"]))
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
            semi_part[p])}, a.fine_periodo)
        orig = GR.filtra(ist["addestramento"], amm)
        P = calcola_pesi(c, p, D["classe"], nodi["addestramento"], orig,
                         ORIZZONTI, versione_codice=f"{pref}_riferimento_rete")
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
    rapp["_scelte"] = {"nome": nome, "fine_periodo": a.fine_periodo}
    (NUOVA / f"rapporto_pesi_{pref}.json").write_text(json.dumps(rapp, indent=2))
    print(f"\n  3 artefatti in {NUOVA}")
    print(f"  **le soglie delle classi non sono state toccate**: restano quelle")
    print(f"  dichiarate prima della ricognizione del dato")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
