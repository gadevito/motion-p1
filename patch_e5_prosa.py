#!/usr/bin/env python3
"""
Patch per la voce 20 del registro — `CONGELAMENTO_E5.md`, riga di prosa su E3-bis.
=====================================================================================
Il congelamento di E5 (6/10) scriveva «E3-bis non eseguito prima di questo congelamento»;
la frase dipende da quali esperimenti esistevano al momento della generazione, e
`analysis/main.py` (11/10) la trova diversa rigenerando: i numeri sono identici. Una
sostituzione letterale: la frase diventa stabile nel tempo (dice che cosa valeva il 6/10 e
che E3-bis e' arrivato il 7/10) e porta la correzione datata.

Uso (dalla radice OR3/):

    poetry run python patch_e5_prosa.py
    poetry run python genera_congelamento_e5.py
"""
from pathlib import Path

F = Path("genera_congelamento_e5.py")
S = F.read_text()
VECCHIO = '''    e3bis = (OUT / "e3bis_risultati.json").exists()
    a("- **E3-bis**: " + ("eseguito, vedi il suo congelamento." if e3bis else
                        "**non eseguito** prima di questo congelamento: nel paper il confronto dei costi "
                        "fra R-orig (24 h di dati) e F′ (1 settimana) e' dichiarato **a dati asimmetrici**."))
'''
NUOVO = '''    a("- **E3-bis**: non eseguito al momento del primo congelamento di E5 (2026-10-06); eseguito e "
      "congelato il 2026-10-07 (`CONGELAMENTO_E3bis.md`), che porta il confronto dei costi fra R-orig e F′ "
      "a dati simmetrici.")
    a("- **Correzione del 2026-10-11 (voce 20 del registro, documentazione)**: la frase precedente su E3-bis "
      "dipendeva da quali esperimenti esistevano al momento della generazione; `analysis/main.py` l'ha "
      "trovata diversa rigenerando (numeri identici, impronta dei numeri `52cdd962ff9888f6` da entrambe le "
      "parti). Resa stabile nel tempo; documento rigenerato, non modificato a mano.")
'''
n = S.count(VECCHIO)
assert n == 1, f"testo atteso trovato {n} volte, non 1"
S = S.replace(VECCHIO, NUOVO)
compile(S, str(F), "exec")
F.write_text(S)
print(f"  {F}: 1 sostituzione, compila")
