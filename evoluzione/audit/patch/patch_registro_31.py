#!/usr/bin/env python3
"""
Voce 31 del registro delle correzioni (richiesta del revisore, 3/11/2026, 12:40): la descrizione della soglia di
congestione nel manoscritto non corrisponde al codice. Errore di testo, nessun effetto sui risultati.
Sostituzioni letterali in protocol/REGISTRO_CORREZIONI.md; si ferma se un testo atteso non compare esattamente una
volta o se la voce 31 esiste gia'. Dalla radice OR3/:  python3 evoluzione/audit/patch/patch_registro_31.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[3]
REG = R / "protocol" / "REGISTRO_CORREZIONI.md"
VOCE = ("| 31 | la descrizione della soglia di congestione nel manoscritto non corrisponde al codice: su Traffic4cast il "
        "riferimento di flusso libero e' per segmento (`free_flow_kph` dell'anagrafica, `evoluzione/esperimenti/costruisci_maschere.py` "
        "r. 26 e 146) e le classi sono 0,8/0,4 sul rapporto velocita'/riferimento (`data_collection/traffic4cast/t4c22_adapter.py` r. 11); "
        "su PEMS04 e PEMS08 il riferimento e' uno per partizione, il 95° percentile delle velocita' aggregate dei soli nodi iniziali nel "
        "periodo di addestramento, e le classi sono 0,8/0,5 (`evoluzione/esperimenti/estrai_pems04.py` r. 63-64, 119, 122) | errore di "
        "testo, nessun effetto sui risultati (3/11/2026): correzione del testo del manoscritto a cura della stesura; convenzioni dichiarate "
        "in `protocol/E18quater.md` (parte B) e nella didascalia della tabella delle classi per sensore (E18-quater) | "
        "`protocol/E18quater.md`, `CONGELAMENTO_E18QUATER.md` |")


def main() -> int:
    t = REG.read_text()
    if "\n| 31 |" in t:
        print("FERMO: la voce 31 esiste gia'"); return 1
    righe = t.rstrip("\n").split("\n")
    i30 = [i for i, l in enumerate(righe) if l.startswith("| 30 |")]
    if len(i30) != 1:
        print(f"FERMO: riga 30 trovata {len(i30)} volte"); return 1
    righe.insert(i30[0] + 1, VOCE)
    t2 = "\n".join(righe) + "\n"
    v, n = "e al manoscritto (17b, 18)", "e al manoscritto (17b, 18, 31)"
    if t2.count(v) != 1:
        print(f"FERMO: intestazione: «{v}» compare {t2.count(v)} volte"); return 1
    REG.write_text(t2.replace(v, n, 1))
    print("  protocol/REGISTRO_CORREZIONI.md: voce 31 dopo la 30; intestazione aggiornata")
    return 0


if __name__ == "__main__":
    sys.exit(main())
