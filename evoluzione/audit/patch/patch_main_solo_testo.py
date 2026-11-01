#!/usr/bin/env python3
"""
Giro 20261101T092004Z al tag paper1-freeze-20261101m NON CONCLUSO: `AttributeError: 'list' object has no attribute
'paper'` (analysis/main.py, riga 738). Causa: il commit 94d8807 (`--solo-testo`) definisce una seconda funzione
`solo_testo(a)` con lo stesso nome della funzione esistente `solo_testo(righe: list) -> bool` (riga 361), usata
dal confronto delle fasi (`if rr and solo_testo(rr)`); la seconda definizione sostituisce la prima e il confronto
chiama la funzione nuova con una lista. Le 15 fasi concluse prima dell'errore coincidono (0 differenze).
Correzione: la funzione nuova si chiama `verifica_testo` (definizione e unica chiamata). Nessun numero cambia.
Collaudo: compilazione e nessun nome definito due volte al livello superiore del modulo.
Sostituzioni letterali; si ferma se un testo atteso non compare esattamente una volta. Dalla radice OR3/:
    python3 evoluzione/audit/patch/patch_main_solo_testo.py
"""
import ast
import sys
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parents[3]
F = R / "analysis" / "main.py"

SOST = [
    ('''def solo_testo(a) -> int:''',
     '''def verifica_testo(a) -> int:   # nome diverso da solo_testo(righe) del confronto delle fasi (corretto il 2026-11-01)'''),
    ('''        return solo_testo(a)''',
     '''        return verifica_testo(a)'''),
]


def main() -> int:
    t = F.read_text()
    for v, _ in SOST:
        if t.count(v) != 1:
            print(f"FERMO: il testo atteso compare {t.count(v)} volte:\n{v}"); return 1
    for v, n in SOST:
        t = t.replace(v, n)
    F.write_text(t)
    import py_compile
    py_compile.compile(str(F), doraise=True)
    nomi = Counter(n.name for n in ast.parse(t).body if isinstance(n, (ast.FunctionDef, ast.ClassDef)))
    doppi = sorted(k for k, c in nomi.items() if c > 1)
    if doppi:
        print(f"FERMO: nomi ancora definiti due volte: {doppi}"); return 1
    print(f"  analysis/main.py: {len(SOST)} sostituzioni; compilazione ok; {len(nomi)} definizioni al livello superiore, nessuna doppia")
    return 0


if __name__ == "__main__":
    sys.exit(main())
