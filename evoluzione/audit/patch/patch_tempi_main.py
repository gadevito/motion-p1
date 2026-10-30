#!/usr/bin/env python3
"""
I tempi misurati di E18 (`e18_risultati.json` → `A/tempi/<gruppo>/{parete_s, macchina_s, per_cella_s}`) sono registri
d'orologio: cambiano a ogni giro e non sono risultati. `analysis/main.py` tratta gia' come metadati le chiavi dei tempi
(`durata`, `secondi_parete`, `macchina`...): si riportano se differiscono, non fanno fallire il confronto. Qui si
aggiunge la chiave `tempi` (esatta) all'espressione, cosi' tutto il sottoalbero dei tempi di E18 segue la stessa regola.
Sostituzione letterale; si ferma se il testo atteso non compare esattamente una volta.

Dalla radice OR3/:  python3 patch_tempi_main.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
F = R / "analysis" / "main.py"
VECCHIO = '''                      r"durata|secondi_parete|^ora$|macchina|python|versione)", re.I)'''
NUOVO = '''                      r"durata|secondi_parete|^tempi$|^ora$|macchina|python|versione)", re.I)'''


def main() -> int:
    t = F.read_text()
    if t.count(VECCHIO) != 1:
        print(f"FERMO: il testo atteso compare {t.count(VECCHIO)} volte in analysis/main.py"); return 1
    F.write_text(t.replace(VECCHIO, NUOVO))
    import py_compile
    py_compile.compile(str(F), doraise=True)
    # collaudo della regola, senza eseguire nulla
    src = t.replace(VECCHIO, NUOVO)
    ns = {}
    exec("import re\n" + src[src.index("METADATI = re.compile"):src.index("# nei documenti")], ns)
    casi = {"/A/tempi/Madrid/parete_s": True, "/A/tempi/Madrid/per_cella_s/mediana": True, "/A/tempi/PEMS08/macchina_s": True,
            "/A/gruppi/Londra/argmax/A/richiamo": False, "/C/gruppi/Madrid/medie_settimana/C/grezzo/logloss": False,
            "/B/contesti/x/tempistica": False}
    for p, atteso in casi.items():
        if ns["e_metadato"](p) != atteso:
            print(f"FERMO: e_metadato({p!r}) = {not atteso}, atteso {atteso}"); return 1
    print(f"  analysis/main.py: `^tempi$` fra i metadati; collaudo della regola su {len(casi)} percorsi: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
