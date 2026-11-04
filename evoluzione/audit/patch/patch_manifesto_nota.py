#!/usr/bin/env python3
"""
`manifesto_zenodo.py`: opzione `--nota`, una riga `# nota: ...` in testa al manifesto dopo quella del tag (richiesta
del revisore, 4/11/2026: al tag q «results tree identical to tag p; q changes only evoluzione/audit/ripartizione_results.py»).
Le righe dei file e l'impronta dell'elenco non cambiano. Sostituzioni letterali; si ferma se un testo atteso non
compare esattamente una volta. Dalla radice OR3/:
    python3 evoluzione/audit/patch/patch_manifesto_nota.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[3]
F = R / "evoluzione" / "audit" / "manifesto_zenodo.py"

SOST = [
    ('''    ap.add_argument("--lavoratori", type=int, default=8)
''',
     '''    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--nota", default=None, help="riga aggiuntiva in testa al manifesto (dopo quella del tag)")
'''),
    ('''         f"# tag: {a.tag}  commit: {testa}  generato: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  macchina: {platform.node()}",
''',
     '''         f"# tag: {a.tag}  commit: {testa}  generato: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  macchina: {platform.node()}",
         *([f"# nota: {a.nota}"] if a.nota else []),
'''),
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
    print(f"  evoluzione/audit/manifesto_zenodo.py: {len(SOST)} sostituzioni; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
