#!/usr/bin/env python3
"""
E18-ter: generatore della Tabella V del manoscritto (`tab:replication`, le cinque dichiarazioni pre-registrate su
ogni contesto) con le due scale di lettura, in `analysis/tabelle_paper1.py` (`scrivi_tabella_replica`, file
`figures/table_replication.tex`), chiamato da `analysis/main.py` nella fase del manoscritto accanto a G7.
Dagli stessi intervalli congelati: E5 (citta', episodi 1–3: `e5_risultati.json` → `affermazioni/<citta>/ep<n>/<a..e>`),
E6 (PEMS08: `e6_risultati.json` → `affermazioni`), E6-bis parte A (PEMS04: `e6a_risultati.json`; la (e) non e' riportabile).
Riga dei segni: −/+/0 (intervallo sotto / sopra zero / lo include), calcolati dagli intervalli e verificati contro il
campo `segno` congelato (si ferma se differiscono); riga «within delta»: y se il limite superiore e' sotto 0.005.
Presentazione cambiata il 2026-10-30, analisi invariata. Sostituzioni letterali; si ferma se un testo atteso non
compare esattamente una volta. Dalla radice OR3/:  python3 patch_e18ter_tabellaV.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
P1 = R / "analysis" / "tabelle_paper1.py"
MAIN = R / "analysis" / "main.py"

NUOVO_P1 = '''

def scrivi_tabella_replica(ris: Path, f: Path) -> None:
    """Tabella V del testo (`tab:replication`): le cinque dichiarazioni pre-registrate su ogni contesto, con le due
    scale di lettura dagli stessi intervalli congelati — riga dei segni (−/+/0: intervallo sotto / sopra zero / lo
    include; verificati contro il campo `segno` dei json, si ferma se differiscono) e riga «within delta» (y: limite
    superiore sotto 0.005). Citta': E5, episodi 1–3; PEMS08: E6; PEMS04: E6-bis parte A ((e) non riportabile).
    Presentazione cambiata il 2026-10-30, analisi invariata."""
    e5 = json.loads((ris / "e5_risultati.json").read_text())["affermazioni"]
    e6 = json.loads((ris / "e6_risultati.json").read_text())["affermazioni"]
    e6a = json.loads((ris / "e6a_risultati.json").read_text())["affermazioni"]
    ETIC = (("a", r"(a) $\\Fzp-\\C$"), ("b", r"(b) gated$-\\Fzp$"), ("c", r"(c) $\\Fp{\\wk}-\\C$"),
            ("d", r"(d) $\\Fp{24\\,h}-\\C$"), ("e", r"(e) $\\Fp{\\wk}-\\A$"))

    def scale(r, dove):
        lo, hi = r["ic_con_nodi"]
        s = "-" if hi < 0 else ("+" if lo > 0 else "0")
        if r.get("segno") is not None and r["segno"] != s:
            raise RuntimeError(f"Tabella V, {dove}: segno dall'intervallo {s!r} diverso dal campo congelato {r['segno']!r}")
        return s, ("y" if hi < 0.005 else "n")
    righe = []
    for k, et in ETIC:
        segni, delta = [], []
        for c, _ in CITTA:
            ss = [scale(e5[f"{c}/ep{n}/{k}"], f"{c}/ep{n}/{k}") for n in (1, 2, 3)]
            segni.append("$" + "\\\\,".join(s for s, _ in ss) + "$"); delta.append("\\\\,".join(d for _, d in ss))
        for src, nome in ((e6a, "PEMS04"), (e6, "PEMS08")):
            if k in src:
                s, d = scale(src[k], f"{nome}/{k}"); segni.append(f"${s}$" if s != "0" else "0"); delta.append(d)
            else:
                segni.append("n.r."); delta.append("n.r.")
        righe.append(et + " & " + " & ".join(segni) + " \\\\\\\\")
        righe.append("\\\\quad within $\\\\delta$ & " + " & ".join(delta) + " \\\\\\\\")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("% generato da OR3/analysis/main.py (tabelle_paper1.scrivi_tabella_replica): non modificare a mano\\n"
                 + "\\n".join(righe) + "\\n\\\\bottomrule\\n")
'''

SOST_MAIN = [
    ('''                scrivi_E18ter(radice / RIS, dfig / "tableG_e18ter.tex")''',
     '''                scrivi_E18ter(radice / RIS, dfig / "tableG_e18ter.tex")
                from analysis.tabelle_paper1 import scrivi_tabella_replica
                scrivi_tabella_replica(radice / RIS, dfig / "table_replication.tex")   # Tabella V del testo, due scale'''),
]


def main() -> int:
    t1 = P1.read_text()
    if "def scrivi_tabella_replica" in t1:
        print("FERMO: scrivi_tabella_replica esiste gia'"); return 1
    if not t1.rstrip().endswith("# \\\\bottomrule qui: dopo \\\\input darebbe Misplaced \\\\noalign") and "Misplaced" not in t1[-200:]:
        print("FERMO: la fine attesa di tabelle_paper1.py (scrivi_tabella_politiche) non c'e'"); return 1
    tm = MAIN.read_text()
    for v, _ in SOST_MAIN:
        if tm.count(v) != 1:
            print(f"FERMO: in analysis/main.py il testo atteso compare {tm.count(v)} volte"); return 1
    P1.write_text(t1.rstrip("\n") + "\n" + NUOVO_P1)
    for v, n in SOST_MAIN:
        tm = tm.replace(v, n)
    MAIN.write_text(tm)
    import py_compile
    py_compile.compile(str(P1), doraise=True); py_compile.compile(str(MAIN), doraise=True)
    print("  analysis/tabelle_paper1.py: scrivi_tabella_replica aggiunta; analysis/main.py: chiamata nella fase del manoscritto; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
