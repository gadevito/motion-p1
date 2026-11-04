#!/usr/bin/env python3
"""
Regola di ripartizione di results/evoluzione/ per il record Zenodo (richiesta del revisore, 4/11/2026): la cartella
`predizioni_e18quater` (54 celle di E18-quater, ingresso del giro come `predizioni_e15`) entra nel gruppo
«rigenerazione». `RIGEN` elenca le cartelle di predizioni per nome: aggiunto `e18quater`. Nota datata nella
docstring. Sostituzioni letterali; si ferma se un testo atteso non compare esattamente una volta. Dalla radice OR3/:
    python3 evoluzione/audit/patch/patch_zenodo_regola.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[3]
F = R / "evoluzione" / "audit" / "ripartizione_results.py"

SOST = [
    ('''RIGEN = re.compile(r"^(predizioni_(fase3|fase3_672|e2|f0|e4|e5|e6|e6a|e6bis|e8|e14|e15|veterani_e3)|maschere|''',
     '''RIGEN = re.compile(r"^(predizioni_(fase3|fase3_672|e2|f0|e4|e5|e6|e6a|e6bis|e8|e14|e15|e18quater|veterani_e3)|maschere|'''),
    ('''Dalla radice OR3/:  python3 evoluzione/audit/ripartizione_results.py [--md protocol/zenodo/RIPARTIZIONE_RESULTS.md]
"""''',
     '''Dalla radice OR3/:  python3 evoluzione/audit/ripartizione_results.py [--md protocol/zenodo/RIPARTIZIONE_RESULTS.md]

Nota del 2026-11-04: `predizioni_e18quater` (celle di E18-quater, ingresso del giro come `predizioni_e15`) aggiunta
al gruppo «rigenerazione»; al tag p era classificata «altro» e il manifesto la escludeva.
"""'''),
]


def main() -> int:
    t = F.read_text()
    for v, _ in SOST:
        if t.count(v) != 1:
            print(f"FERMO: il testo atteso compare {t.count(v)} volte:\\n{v[:120]}"); return 1
    for v, n in SOST:
        t = t.replace(v, n)
    F.write_text(t)
    import py_compile
    py_compile.compile(str(F), doraise=True)
    print(f"  evoluzione/audit/ripartizione_results.py: {len(SOST)} sostituzioni; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
