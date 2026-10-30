#!/usr/bin/env python3
"""
Didascalie G18–G21 (`tab:suppG1`–`G4`, generatore `scrivi_E18`): unita' dichiarata come chiede il revisore (30/10,
10:00) — «run (seed x partition) = unit, mean over runs; the cell (seed x partition x sensor) is the resampling unit»
al posto di «cell = unit, mean over cells»; «36 runs» dove compare (gia' cosi'). Solo testo; nessun valore cambia.
Sostituzioni letterali in analysis/tabelle_suppl.py; si ferma se un testo atteso non compare esattamente una volta.
Dalla radice OR3/:  python3 patch_g18_21.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
F = R / "analysis" / "tabelle_suppl.py"
UNITA = ("run (seed $\\\\times$ partition) = unit, mean over runs; the cell (seed $\\\\times$ partition $\\\\times$ sensor) "
         "is the resampling unit")

SOST = [
    # G18
    ('''        "distinct scores of a cell as thresholds, cell = unit, mean over cells and 95\\\\% interval from 4{,}000 joint "''',
     '''        "distinct scores of a run as thresholds, " + UNITA + "; 95\\\\% interval from 4{,}000 joint "'''),
    # G19
    ('''        "E18, part A: differences between arms on the empirical ROC (same resampling indices for both arms): "''',
     '''        "E18, part A: differences between arms on the empirical ROC (same resampling indices for both arms; " + UNITA + "): "'''),
    # G20
    ('''        "recall; all origins after $t_1$. A share above 1 (PEMS08) means that at 5\\\\% false alarms $F_0$ recalls more "''',
     '''        "recall; all origins after $t_1$; " + UNITA + ". A share above 1 (PEMS08) means that at 5\\\\% false alarms $F_0$ recalls more "'''),
    # G21
    ('''        "arms, partitions and seeds; 4{,}000 replicates. Two reading scales as in the main paper: " + SCALE_EN + f"; {NOTA}. "''',
     '''        "arms, partitions and seeds; 4{,}000 replicates; " + UNITA + ". Two reading scales as in the main paper: " + SCALE_EN + f"; {NOTA}. "'''),
]


def main() -> int:
    t = F.read_text()
    if "UNITA_E18 = " in t:
        print("FERMO: patch gia' applicata"); return 1
    for v, _ in SOST:
        if t.count(v) != 1:
            print(f"FERMO: il testo atteso compare {t.count(v)} volte:\n{v[:200]}"); return 1
    for v, n in SOST:
        t = t.replace(v, n)
    # la costante UNITA accanto a GRUPPI_E18
    anc = '''GRUPPI_E18 = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")'''
    if t.count(anc) != 1:
        print("FERMO: ancora GRUPPI_E18 non univoca"); return 1
    t = t.replace(anc, anc + '''
UNITA_E18 = ("run (seed $\\\\times$ partition) = unit, mean over runs; the cell (seed $\\\\times$ partition $\\\\times$ sensor) "
             "is the resampling unit")''').replace(' + UNITA + ', ' + UNITA_E18 + ')
    F.write_text(t)
    import py_compile
    py_compile.compile(str(F), doraise=True)
    print("  analysis/tabelle_suppl.py: didascalie G18–G21 con l'unita' dichiarata; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
