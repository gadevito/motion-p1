#!/usr/bin/env python3
"""
Dopo la riscrittura della storia (voce 30): il limite storico della parte D di E18 (`LIMITE_D` in
`evoluzione/analisi/analizza_e18.py`) era il commit `964e4f5` (firma del protocollo E18), che nella storia
pubblicata e' `923c02e` (`protocol/RISCRITTURA_STORIA.md`); con il vecchio hash `git log` fallisce e la parte D
si ferma. Unico punto del codice che usa un hash di commit. Il manoscritto non e' riscritto: `ae12921` resta.
Nessun numero cambia; nel giro di rigenerazione la differenza e' solo nel metadato `limite_storia/OR3/commit` e
in un hash del documento, entrambi mascherati: il congelamento di E18 non si rigenera.
Sostituzioni letterali; si ferma se un testo atteso non compare esattamente una volta. Dalla radice OR3/:
    python3 patch_limite_d.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
AN = R / "evoluzione" / "analisi" / "analizza_e18.py"
GEN = R / "genera_congelamento_e18.py"

SOST = {AN: [
    ('''LIMITE_D = {"OR3": "964e4f5", "manoscritto": "ae12921"}''',
     '''LIMITE_D = {"OR3": "923c02e", "manoscritto": "ae12921"}   # OR3: era 964e4f5 prima della riscrittura della storia (voce 30,
#                                                            protocol/RISCRITTURA_STORIA.md); il manoscritto non e' riscritto'''),
], GEN: [
    ('''          "- 29/10/2026, parte D: ricerca storica limitata ai commit fino alla firma del protocollo (OR3 `964e4f5`, manoscritto "''',
     '''          "- 29/10/2026, parte D: ricerca storica limitata ai commit fino alla firma del protocollo (OR3 `964e4f5`, = `923c02e` "
          "dopo la riscrittura della storia del 31/10/2026, voce 30; manoscritto "'''),
]}


def main() -> int:
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, _ in coppie:
            if t.count(v) != 1:
                print(f"FERMO: in {f.relative_to(R)} il testo atteso compare {t.count(v)} volte:\n{v[:150]}"); return 1
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, n in coppie:
            t = t.replace(v, n)
        f.write_text(t); print(f"  {f.relative_to(R)}: {len(coppie)} sostituzioni")
    import py_compile
    for f in SOST:
        py_compile.compile(str(f), doraise=True)
    print("  compilazione: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
