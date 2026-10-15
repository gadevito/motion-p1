#!/usr/bin/env python3
"""
E14 stadio B, correzione — `adatta_F` riceve la statica della cella.
=====================================================================
`inserimento.adatta_F` costruiva la statica da se' (`statiche(D)`, non causale) e non passava
da `statica_cella`: in `ricostruisci_predizioni --braccio F` l'adattamento avveniva con la
statica congelata e la valutazione con quella della variante, e il controllo 3 di E4 (F(24 h)
di E4 contro `predizioni_fase3/F`) falliva con scarti 1e-4…1e-3 sotto la variante (c).

Qui: `adatta_F(..., stat=None)`; se `stat` manca si comporta come prima (`statiche(D)`), i
chiamanti della fase 3 (`esegui_inserimento`) non cambiano; `ricostruisci_predizioni` passa la
statica della cella. Con `OR3_STATICA` assente nulla cambia (collaudi).

Uso (dalla radice OR3/):

    poetry run python patch_e14b_adatta_F.py
"""
import py_compile
import sys
from pathlib import Path

SOST = {
    "evoluzione/esperimenti/inserimento.py": [(
        '''def adatta_F(c, p, seme_torch, out: Path, D, nodi, ist, o_acq, reg):
    """F: parte dal punto E della pipeline corretta, muove SOLO i nuovi
    embedding, con la configurazione appena congelata."""
''',
        '''def adatta_F(c, p, seme_torch, out: Path, D, nodi, ist, o_acq, reg, stat=None):
    """F: parte dal punto E della pipeline corretta, muove SOLO i nuovi
    embedding, con la configurazione appena congelata. `stat`: la statica della
    cella (E14, `statica_cella`); assente = `statiche(D)`, come nella fase 3."""
'''), (
        '''    x = _canali(D, nr, nv)
    stat = statiche(D)
    m, forn = copia_da_E(dE, nodi_in, nodi["prova"], D_STAT)
''',
        '''    x = _canali(D, nr, nv)
    stat = statiche(D) if stat is None else stat
    m, forn = copia_da_E(dE, nodi_in, nodi["prova"], D_STAT)
''')],
    "evoluzione/esperimenti/ricostruisci_predizioni.py": [(
        '''                    m, _ = adatta_F(c, p, st_, a.out, D, nodi, ist, o_acq, rg)
''',
        '''                    m, _ = adatta_F(c, p, st_, a.out, D, nodi, ist, o_acq, rg, stat=stat)   # E14
''')],
}


def main() -> int:
    for f, coppie in SOST.items():
        p = Path(f); t = p.read_text()
        for vecchio, nuovo in coppie:
            assert t.count(vecchio) == 1, f"{f}: atteso una volta:\n{vecchio}"
            t = t.replace(vecchio, nuovo)
        p.write_text(t); py_compile.compile(f, doraise=True)
        print(f"  {f}: {len(coppie)} sostituzioni, compila")
    return 0


if __name__ == "__main__":
    sys.exit(main())
