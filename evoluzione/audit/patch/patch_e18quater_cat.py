#!/usr/bin/env python3
"""
`scrivi_E18quater` (tab:suppE18quater): le due scale di lettura del paper — segno dell'intervallo (favourable /
unfavourable / inconclusive) e margine (within delta: yes/no), da `_scale(ic)` — al posto della categoria
superiority / non-inferiority. Richiesta del revisore del 3/11/2026, 16:54. Solo presentazione: il congelamento
(`congelamento_e18quater.json`, `CONGELAMENTO_E18QUATER.md`) non cambia.
Sostituzioni letterali in analysis/tabelle_suppl.py; si ferma se un testo atteso non compare esattamente una volta.
Dalla radice OR3/:  python3 evoluzione/audit/patch/patch_e18quater_cat.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[3]
F = R / "analysis" / "tabelle_suppl.py"

SOST = [
    ('''            righe.append(" & ".join([CTX_EN[c] if j == 0 else "", DIFF_Q_EN[k], _ic(d, scala=1.0, cifre=4),
                                     CAT_EN.get(d["categoria"], d["categoria"]),''',
     '''            righe.append(" & ".join([CTX_EN[c] if j == 0 else "", DIFF_Q_EN[k], _ic(d, scala=1.0, cifre=4),
                                     *_scale(d["ic_con_nodi"]),'''),
    ('''        "@{}l l c l c@{}",
        "E18-quater: the frozen $C_A$ of the causal campaign re-evaluated''',
     '''        "@{}l l c l l c@{}",
        "E18-quater: the frozen $C_A$ of the causal campaign re-evaluated'''),
    ('''        "interval from 4{,}000 joint resamples (partitions, seeds, sensor positions), the same draws as the causal campaign; "
        "category as in Section~III of the paper." + _fonte_e18quater(),
        "City & Difference & wCE & Category & Share of $C_A-C$ due to coverage", righe, "tab:suppE18quater"))''',
     '''        "interval from 4{,}000 joint resamples (partitions, seeds, sensor positions), the same draws as the causal campaign. "
        "Two reading scales as in the main paper: " + SCALE_EN + "." + _fonte_e18quater(),
        "City & Difference & wCE & Sign & Within $\\\\delta$ & Share of $C_A-C$ due to coverage", righe, "tab:suppE18quater"))'''),
]


def main() -> int:
    t = F.read_text()
    for v, _ in SOST:
        if t.count(v) != 1:
            print(f"FERMO: il testo atteso compare {t.count(v)} volte:\\n{v[:160]}"); return 1
    for v, n in SOST:
        t = t.replace(v, n)
    F.write_text(t)
    import py_compile
    py_compile.compile(str(F), doraise=True)
    print(f"  analysis/tabelle_suppl.py: {len(SOST)} sostituzioni; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
