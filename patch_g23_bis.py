#!/usr/bin/env python3
"""
G23 (`tab:suppG6`) sporge ancora di 16 pt: `\\tiny` come G21, intestazioni abbreviate (g = gated, «camp.», «sensor»,
«observed») e nomi di campagna corti nelle righe («E4/E2», «E6-bis A»), legenda in didascalia. Valori invariati.
Sostituzioni letterali in analysis/tabelle_suppl.py; si ferma se un testo atteso non compare esattamente una volta.
Dalla radice OR3/:  python3 patch_g23_bis.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
F = R / "analysis" / "tabelle_suppl.py"

SOST = [
    ('''        camp = X["campagna"].replace("campagna principale", "main campaign").replace("parte A", "part A")''',
     '''        camp = X["campagna"].replace(" (campagna principale)", "").replace(" (parte A)", " A")   # corto: la tabella e' larga'''),
    ('''        "confirmation. Two reading scales: " + SCALE_EN + f"; {NOTA}. Abbreviations: fav./unf./inc.; $\\\\delta$: y/n." + fonte,
        "Context & campaign & gated$(1\\\\,\\\\mathrm{wk},0)-F_0'$ & sign & $\\\\delta$ & sensor-level & sign & $\\\\delta$ & "
        "gated$(1\\\\,\\\\mathrm{wk},0)-$gated$(\\\\tau,N)$ & sign & $\\\\delta$ & first observed", righe, "tab:suppG6")
               .replace("{\\\\footnotesize\\\\setlength{\\\\tabcolsep}{3pt}", "{\\\\scriptsize\\\\setlength{\\\\tabcolsep}{1.5pt}", 1))''',
     '''        "confirmation. Two reading scales: " + SCALE_EN + f"; {NOTA}. Abbreviations: g = gated; fav./unf./inc.; $\\\\delta$: y/n; "
        "camp.: campaign (E4/E2 = main campaign; E6-bis A = E6-bis, part A); sensor: sensor-level interval; observed: first observed." + fonte,
        "Context & camp. & g$(1\\\\,\\\\mathrm{wk},0)-F_0'$ & sign & $\\\\delta$ & sensor & sign & $\\\\delta$ & "
        "g$(1\\\\,\\\\mathrm{wk},0)-$g$(\\\\tau,N)$ & sign & $\\\\delta$ & observed", righe, "tab:suppG6")
               .replace("{\\\\footnotesize\\\\setlength{\\\\tabcolsep}{3pt}", "{\\\\tiny\\\\setlength{\\\\tabcolsep}{1.5pt}", 1))'''),
]


def main() -> int:
    t = F.read_text()
    for v, _ in SOST:
        if t.count(v) != 1:
            print(f"FERMO: il testo atteso compare {t.count(v)} volte:\n{v[:200]}"); return 1
    for v, n in SOST:
        t = t.replace(v, n)
    F.write_text(t)
    import py_compile
    py_compile.compile(str(F), doraise=True)
    print("  analysis/tabelle_suppl.py: G6 in \\\\tiny, intestazioni e campagne abbreviate; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
