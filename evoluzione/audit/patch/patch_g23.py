#!/usr/bin/env python3
"""
G23 (`tab:suppG6`, provenienza della politica): con le due scale la tabella supera la pagina di 17,7 pt. Rimedio nel
generatore, senza cambiare i valori: abbreviazioni nelle tre coppie di colonne di categoria (fav./unf./inc. e y/n al
posto di favourable/unfavourable/inconclusive e yes/no), `\\tabcolsep` 1,5 pt, legenda in didascalia.
Sostituzioni letterali in analysis/tabelle_suppl.py; si ferma se un testo atteso non compare esattamente una volta.
Dalla radice OR3/:  python3 patch_g23.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
F = R / "analysis" / "tabelle_suppl.py"

SOST = [
    ('''        righe.append(f"{_ctx_e18(c)} & {camp} & " + _ic_lista(a["media"], a["ic_attuale"]) + f" & {' & '.join(_scale(a['ic_attuale']))} & "
                     f"{{\\\\tiny$[{a['ic_per_sensore'][0]:+.4f},{a['ic_per_sensore'][1]:+.4f}]$}} & {' & '.join(_scale(a['ic_per_sensore']))} & "
                     + _ic_lista(b["media"], b["ic_attuale"]) + f" & {' & '.join(_scale(b['ic_attuale']))} & {o['data']} \\\\\\\\")''',
     '''        br = lambda ic: "{} & {}".format(_scale(ic, breve=True)[0], "y" if _scale(ic, breve=True)[1] == "yes" else "n")   # abbreviato: la tabella e' larga
        righe.append(f"{_ctx_e18(c)} & {camp} & " + _ic_lista(a["media"], a["ic_attuale"]) + f" & {br(a['ic_attuale'])} & "
                     f"{{\\\\tiny$[{a['ic_per_sensore'][0]:+.4f},{a['ic_per_sensore'][1]:+.4f}]$}} & {br(a['ic_per_sensore'])} & "
                     + _ic_lista(b["media"], b["ic_attuale"]) + f" & {br(b['ic_attuale'])} & {o['data']} \\\\\\\\")'''),
    ('''        "confirmation. Two reading scales: " + SCALE_EN + f"; {NOTA}." + fonte,''',
     '''        "confirmation. Two reading scales: " + SCALE_EN + f"; {NOTA}. Abbreviations: fav./unf./inc.; $\\\\delta$: y/n." + fonte,'''),
    ('''        "gated$(1\\\\,\\\\mathrm{wk},0)-$gated$(\\\\tau,N)$ & sign & $\\\\delta$ & first observed", righe, "tab:suppG6")
               .replace("{\\\\footnotesize\\\\setlength{\\\\tabcolsep}{3pt}", "{\\\\scriptsize\\\\setlength{\\\\tabcolsep}{2pt}", 1))''',
     '''        "gated$(1\\\\,\\\\mathrm{wk},0)-$gated$(\\\\tau,N)$ & sign & $\\\\delta$ & first observed", righe, "tab:suppG6")
               .replace("{\\\\footnotesize\\\\setlength{\\\\tabcolsep}{3pt}", "{\\\\scriptsize\\\\setlength{\\\\tabcolsep}{1.5pt}", 1))'''),
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
    print("  analysis/tabelle_suppl.py: G6 con abbreviazioni e tabcolsep 1.5pt; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
