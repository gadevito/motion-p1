#!/usr/bin/env python3
"""
E14 stadio B — `ricostruisci_predizioni.py` sotto una variante della statica.
==============================================================================
Il controllo di `ricostruisci_predizioni` confronta la wCE ricalcolata con quella
CONSERVATA nel manifesto d'addestramento, che fu calcolata con la statica non
causale. Con `OR3_STATICA` diversa da `congelata` quel confronto non e' una
verifica della pipeline ma la misura dell'effetto della variante: lo scarto si
REGISTRA per ogni esecuzione (come oggi) ma non e' un'anomalia e non ferma i
generatori a valle. Con `OR3_STATICA` assente nulla cambia (asserito qui).

Uso (dalla radice OR3/):

    poetry run python patch_e14b_ricostruzione.py
"""
import py_compile
import sys
from pathlib import Path

F = Path("evoluzione/esperimenti/ricostruisci_predizioni.py")
SOST = [(
    '''from evoluzione.esperimenti.inserimento import _modello_da_ck, statica_cella, statiche  # noqa
''',
    '''from evoluzione.esperimenti.inserimento import (  # noqa
    _modello_da_ck, statica_cella, statiche, variante_statica)
'''), (
    '''                if rel > TOLLERANZA or rel_h > TOLLERANZA:
                    guai.append(f"{ck.name}: scarto {rel:.2e} (orizzonti "
                                f"{rel_h:.2e}) oltre la tolleranza")
''',
    '''                if (rel > TOLLERANZA or rel_h > TOLLERANZA) and variante_statica() == "congelata":
                    guai.append(f"{ck.name}: scarto {rel:.2e} (orizzonti "
                                f"{rel_h:.2e}) oltre la tolleranza")
'''), (
    '''        {"tolleranza": TOLLERANZA, "esecuzioni": righe, "anomalie": guai,
''',
    '''        {"tolleranza": TOLLERANZA, "esecuzioni": righe, "anomalie": guai,
         "statica": variante_statica(),
         "nota_statica": ("con una variante della statica (E14, stadio B) lo scarto "
                          "dall'aggregato conservato e' l'effetto della variante, "
                          "non un'anomalia della pipeline"),
''')]


def main() -> int:
    t = F.read_text()
    for vecchio, nuovo in SOST:
        assert t.count(vecchio) == 1, f"{F}: atteso una volta:\n{vecchio}"
        t = t.replace(vecchio, nuovo)
    F.write_text(t)
    py_compile.compile(str(F), doraise=True)
    print(f"  {F}: {len(SOST)} sostituzioni, compila")
    return 0


if __name__ == "__main__":
    sys.exit(main())
