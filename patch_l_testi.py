#!/usr/bin/env python3
"""
Ramo esecutore/l-testi (richiesta del revisore, 30/10, 18:15), solo testo e generatori:
  - Tabella V (`scrivi_tabella_replica`): segni separati come nella colonna «Signs» di C3 (`tab:suppC1`): `$(+, +, 0)$`
    per episodio, e la riga «within delta» come `(n, n, y)`. Valori invariati.
  - G18 «all distinct scores of a cell» → «of a run»: gia' nel ramo g18-21 (verificato qui: si ferma se manca).
Sostituzioni letterali in analysis/tabelle_paper1.py; si ferma se un testo atteso non compare esattamente una volta.
Dalla radice OR3/:  python3 patch_l_testi.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
P1 = R / "analysis" / "tabelle_paper1.py"
SUPP = R / "analysis" / "tabelle_suppl.py"

SOST = [
    ('''            segni.append("$" + "\\\\,".join(s for s, _ in ss) + "$"); delta.append("\\\\,".join(d for _, d in ss))''',
     '''            segni.append("$(" + ", ".join(s for s, _ in ss) + ")$"); delta.append("(" + ", ".join(d for _, d in ss) + ")")'''),
    ('''    scale di lettura dagli stessi intervalli congelati — riga dei segni (−/+/0: intervallo sotto / sopra zero / lo
    include; verificati contro il campo `segno` dei json, si ferma se differiscono) e riga «within delta» (y: limite
    superiore sotto 0.005).''',
     '''    scale di lettura dagli stessi intervalli congelati — riga dei segni (−/+/0: intervallo sotto / sopra zero / lo
    include; verificati contro il campo `segno` dei json, si ferma se differiscono; per episodio, separati da virgole
    come la colonna «Signs» di C1) e riga «within delta» (y: limite superiore sotto 0.005).'''),
]


def main() -> int:
    t = P1.read_text()
    for v, _ in SOST:
        if t.count(v) != 1:
            print(f"FERMO: in analysis/tabelle_paper1.py il testo atteso compare {t.count(v)} volte:\n{v[:160]}"); return 1
    ts = SUPP.read_text()
    if "distinct scores of a run as thresholds" not in ts or "scores of a cell" in ts:
        print("FERMO: la didascalia G18 non porta «of a run» (ramo g18-21 non fuso?)"); return 1
    for v, n in SOST:
        t = t.replace(v, n)
    P1.write_text(t)
    import py_compile
    py_compile.compile(str(P1), doraise=True)
    print("  analysis/tabelle_paper1.py: Tabella V con i segni separati; G18 «of a run» verificato; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
