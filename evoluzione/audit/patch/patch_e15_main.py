#!/usr/bin/env python3
"""
E15 in `analysis/main.py`: due fasi (analisi dagli aggregati per cella e congelamento) ed «E15» fra gli
esperimenti. Patch letterale: si ferma se il testo atteso non compare esattamente una volta.

Dalla radice OR3/:  python3 patch_e15_main.py
"""
import sys
from pathlib import Path

F = Path(__file__).resolve().parent / "analysis" / "main.py"

VECCHIO_FASI = (
    "    # E16 (calibrazione): il congelamento da e16_risultati.json (le probabilita' per cella non si ricostruiscono qui)\n"
    "    F(\"E16\", [\"genera_congelamento_e16.py\"], [R_ + \"congelamento_e16.json\", \"CONGELAMENTO_E16.md\"]),\n"
    "]\n")
NUOVO_FASI = (
    "    # E16 (calibrazione): il congelamento da e16_risultati.json (le probabilita' per cella non si ricostruiscono qui)\n"
    "    F(\"E16\", [\"genera_congelamento_e16.py\"], [R_ + \"congelamento_e16.json\", \"CONGELAMENTO_E16.md\"]),\n"
    "    # E15 (campagna causale): l'analisi dagli aggregati per cella di predizioni_e15/ (addestramenti e adattamenti\n"
    "    # non si rifanno qui; e15_k_secondaria.json e' un ingresso congelato), poi il congelamento\n"
    "    F(\"E15\", [E + \"esegui_e15.py\", \"--fase\", \"analizza\"], [R_ + \"e15_risultati.json\"]),\n"
    "    F(\"E15\", [\"genera_congelamento_e15.py\"], [R_ + \"congelamento_e15.json\", \"CONGELAMENTO_E15.md\"]),\n"
    "]\n")
VECCHIO_ESP = 'ESPERIMENTI = ["ARCH", "E2", "E3", "E4", "E3bis", "E5", "E6", "E7", "E8", "E14", "E16"]'
NUOVO_ESP = 'ESPERIMENTI = ["ARCH", "E2", "E3", "E4", "E3bis", "E5", "E6", "E7", "E8", "E14", "E16", "E15"]'


def main() -> int:
    src = F.read_text()
    for a in (VECCHIO_FASI, VECCHIO_ESP):
        if src.count(a) != 1:
            print(f"FERMO: testo atteso presente {src.count(a)} volte in {F}:\n{a[:200]}")
            return 1
    src = src.replace(VECCHIO_FASI, NUOVO_FASI).replace(VECCHIO_ESP, NUOVO_ESP)
    F.write_text(src)
    print("  analysis/main.py: fase E15 aggiunta (2 sostituzioni)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
