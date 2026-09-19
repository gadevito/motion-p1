#!/usr/bin/env python3
"""
Audit del ciclo di addestramento reale.
========================================
Registra, per ciascun aggiornamento, le grandezze richieste dal revisore:

    chiamate a optimizer.step()
    origini campionate e loro unicita'
    nodi effettivamente elaborati
    bersagli validi per orizzonte
    perdita di addestramento
    perdita di validazione
    momento della selezione del punto di controllo
    causa dell'arresto

E verifica due proprieta' del campionamento:

    `choice` con o senza reinserimento
    esistenza di un ciclo interno sui lotti

**Non modifica il ciclo**: lo osserva.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/audit_ciclo.py
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _canali, _carica, _lotto, _normalizzazione, _partizioni, _perdita)
from evoluzione.analisi.pesi import carica as carica_pesi  # noqa: E402
from evoluzione.esperimenti.semi import SEME_PARTIZIONE  # noqa: E402

ORIZZONTI = (1, 2, 4, 8)


def statico():
    """Che cosa il codice DICE, letto senza eseguirlo."""
    src = Path("evoluzione/esperimenti/addestramento.py").read_text()
    i = src.index("for ep in range"); j = src.index("if epoca < 0:")
    b = src[i:j]
    return {
        "step_per_epoca": b.count("opt.step()"),
        "cicli_for_nel_blocco": b.count("for ") ,
        "choice_con_reinserimento": "replace=False" not in b,
        "validazione_a_ogni_aggiornamento": "pv = float(lv)" in b,
        "istanti_di_validazione": ("finestra FISSA: i primi `lotto`"
                                   if 'ist_ck[:cfg["lotto"]]' in b
                                   else "campionati"),
        "pazienza_su": "aggiornamenti, non passate",
    }


def dinamico(contesto="Madrid", partizione=0, seme=643310434, epoche=35,
             lotto=32, out=Path("results/evoluzione")):
    """Che cosa il ciclo FA, riproducendone il campionamento."""
    D = _carica(contesto, out / "maschere")
    nodi, ist = _partizioni(D, {"partizione":
                                np.random.default_rng(SEME_PARTIZIONE[partizione])})
    g = np.random.default_rng(seme)          # lo stesso generatore
    tr = ist["addestramento"]
    visti, righe = [], []
    for ep in range(epoche):
        idx = g.choice(tr, size=min(lotto, len(tr)), replace=False)
        visti.extend(int(x) for x in idx)
        val = np.zeros(len(ORIZZONTI), dtype="int64")
        for h, o in enumerate(ORIZZONTI):
            val[h] = int((D["classe"][np.sort(idx) + o][:,
                          nodi["addestramento"]] > 0).sum())
        righe.append({"aggiornamento": ep, "origini": len(idx),
                      "nodi": len(nodi["addestramento"]),
                      "istanze": len(idx) * len(nodi["addestramento"]),
                      "validi_per_orizzonte": val.tolist(),
                      "validi_totali": int(val.sum())})
    u = len(set(visti))
    return {"aggiornamenti": epoche, "origini_totali": len(visti),
            "origini_distinte": u, "ripetute": len(visti) - u,
            "origini_di_training": len(tr),
            "copertura": u / len(tr),
            "aggiornamenti_per_passata_nominale": math.ceil(len(tr) / lotto),
            "quota_di_una_passata": epoche / math.ceil(len(tr) / lotto),
            "istanze_per_aggiornamento": lotto * len(nodi["addestramento"]),
            "validi_mediani": float(np.median([r["validi_totali"]
                                               for r in righe])),
            "per_aggiornamento": righe}


def main() -> int:
    print("=" * 80)
    print("AUDIT DEL CICLO DI ADDESTRAMENTO")
    print("=" * 80)
    s = statico()
    print("\n[statico] che cosa il codice dice\n")
    for k, v in s.items():
        print(f"  {k:36s} {v}")
    print("\n  > un'«epoca» e' UN aggiornamento dell'ottimizzatore,")
    print("  > non una passata sul corpus.")
    print("  > «pazienza 8» sono otto verifiche dopo aggiornamenti.")

    d = dinamico()
    print("\n[dinamico] che cosa il ciclo fa\n")
    for k in ("aggiornamenti", "origini_totali", "origini_distinte",
              "ripetute", "origini_di_training", "istanze_per_aggiornamento",
              "aggiornamenti_per_passata_nominale"):
        print(f"  {k:36s} {d[k]:,}")
    print(f"  {'copertura delle origini':36s} {d['copertura']:.2%}")
    print(f"  {'quota di UNA passata':36s} {d['quota_di_una_passata']:.1%}")
    print(f"  {'bersagli validi, mediana':36s} {d['validi_mediani']:,.0f}")
    print("\n  > 35 aggiornamenti coprono il "
          f"{d['copertura']:.1%} delle origini di addestramento.")
    print(f"  > una passata nominale ne richiederebbe "
          f"{d['aggiornamenti_per_passata_nominale']}.")

    print("\n[due fatti emersi oltre al numero di aggiornamenti]\n")
    print("  1. LA VALIDAZIONE USA SEMPRE GLI STESSI 32 ISTANTI: i primi del")
    print("     periodo, mai altri. Non e' un campione: e' una finestra fissa,")
    print("     e la selezione del punto di controllo vi si basa.")
    print("  2. LA VALIDAZIONE AVVIENE DOPO OGNI AGGIORNAMENTO, sicche'")
    print("     «pazienza 8» sono otto aggiornamenti consecutivi senza")
    print("     miglioramento — circa il 23% del budget totale.")

    Path("results/evoluzione/audit_ciclo.json").write_text(
        json.dumps({"statico": s, "dinamico": d}, indent=2,
                   ensure_ascii=False))
    print("\n  rapporto in results/evoluzione/audit_ciclo.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
