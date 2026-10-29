#!/usr/bin/env python3
"""
E18 in `analysis/main.py`: due fasi (analisi, parti C-A-B-D, e congelamento) ed «E18» fra gli esperimenti.
Patch letterale: si ferma se il testo atteso non compare esattamente una volta.

Dalla radice OR3/:  python3 patch_e18_main.py
"""
import sys
from pathlib import Path

F = Path(__file__).resolve().parent / "analysis" / "main.py"
VECCHIO_FASI = (
    "    F(\"E15\", [\"genera_congelamento_e15.py\"], [R_ + \"congelamento_e15.json\", \"CONGELAMENTO_E15.md\"]),\n"
    "]\n")
NUOVO_FASI = (
    "    F(\"E15\", [\"genera_congelamento_e15.py\"], [R_ + \"congelamento_e15.json\", \"CONGELAMENTO_E15.md\"]),\n"
    "    # E18 (seconda revisione esterna, sola analisi): C (correzione 27 di E16, con controllo), A (ROC empirica,\n"
    "    # pAUC, richiami a FA fissi: ~1 h a 16 lavoratori), B (bootstrap per sensore fisico), D (date da git log)\n"
    "    F(\"E18\", [A + \"analizza_e18.py\", \"--parte\", \"tutte\", \"--lavoratori\", \"16\"], [R_ + \"e18_risultati.json\"]),\n"
    "    F(\"E18\", [\"genera_congelamento_e18.py\"], [R_ + \"congelamento_e18.json\", \"CONGELAMENTO_E18.md\"]),\n"
    "]\n")
VECCHIO_ESP = 'ESPERIMENTI = ["ARCH", "E2", "E3", "E4", "E3bis", "E5", "E6", "E7", "E8", "E14", "E16", "E15"]'
NUOVO_ESP = 'ESPERIMENTI = ["ARCH", "E2", "E3", "E4", "E3bis", "E5", "E6", "E7", "E8", "E14", "E16", "E15", "E18"]'


def main() -> int:
    src = F.read_text()
    for a in (VECCHIO_FASI, VECCHIO_ESP):
        if src.count(a) != 1:
            print(f"FERMO: testo atteso presente {src.count(a)} volte in {F}:\n{a[:200]}")
            return 1
    F.write_text(src.replace(VECCHIO_FASI, NUOVO_FASI).replace(VECCHIO_ESP, NUOVO_ESP))
    print("  analysis/main.py: fase E18 aggiunta (2 sostituzioni)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
