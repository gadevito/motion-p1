#!/usr/bin/env python3
"""
Paper 4, fase 1 (richiesta del revisore, 6/11/2026): `analisi/geometria_criteri.py` non trovava i CSV conservati.
Due difetti di nomi, nessun numero toccato:
  1. i CSV di `replication/geo/` si chiamano `geo_<citta>_<grafo>_s<s>.csv` (README §7.7: tag = nome del pkl,
     `<citta>_<grafo>`), ma lo script cercava `geo_<grafo>_s<s>.csv` (blocco principale, r. 142, e criterio 4);
  2. il criterio 4 (r. 202-203) accoppiava i grafi cercando «knn» nel NOME del grafo, mentre «knn» sta nella
     colonna `modo`: i nomi sono `comp_q<xy>` (vero) e `neg_rand_q<xy>` (randomizzato). Nessuna coppia, mai.
Correzione: `_csv_tag(citta, grafo)` cerca prima `geo_<citta>_<grafo>`, poi `geo_<grafo>`; il criterio 4 accoppia
`comp_q<xy>` con `neg_rand_q<xy>` della stessa citta'. Sostituzioni letterali; si ferma se un testo atteso non
compare esattamente una volta. Dalla radice del repository:
    python3 evoluzione/audit/patch/patch_p4_criterio4.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[3]
F = R / "analisi" / "geometria_criteri.py"

SOST = [
    ('''def regressione(x, y, gruppo=None):''',
     '''def _csv_tag(geo_dir, citta, grafo, semi):
    """Nome dei CSV di un grafo: `geo_<citta>_<grafo>_s<s>.csv` (README §7.7, tag = nome del pkl); ripiego sul
    nome senza citta'. Corretto il 2026-11-06 (Paper 4, fase 1): prima si cercava solo il nome senza citta'."""
    for tag in (f"{citta}_{grafo}", grafo):
        if vantaggio(str(geo_dir / f"geo_{tag}_s{{s}}.csv"), semi) is not None:
            return tag
    return f"{citta}_{grafo}"


def regressione(x, y, gruppo=None):'''),
    ('''        tag = r["grafo"]
        v = vantaggio(str(a.geo_dir / f"geo_{tag}_s{{s}}.csv"), a.semi)''',
     '''        tag = r["grafo"]
        v = vantaggio(str(a.geo_dir / f"geo_{_csv_tag(a.geo_dir, r['citta'], tag, a.semi)}_s{{s}}.csv"), a.semi)'''),
    ('''    coppie = [(r["grafo"], r["grafo"].replace("knn", "rand"))
              for _, r in cov.iterrows() if "knn" in str(r["grafo"])]
    trovata = False
    for vero, casuale in coppie:
        vv = vantaggio(str(a.geo_dir / f"geo_{vero}_s{{s}}.csv"), a.semi)
        vc = vantaggio(str(a.geo_dir / f"geo_{casuale}_s{{s}}.csv"), a.semi)''',
     '''    # coppie vero/randomizzato: `comp_q<xy>` (modo knn) e `neg_rand_q<xy>` della stessa citta' (make_geo_sweep.py);
    # fino al 2026-11-06 si cercava «knn» nel nome del grafo, che sta invece nella colonna `modo`: nessuna coppia
    # (la riga di covariate del randomizzato puo' mancare: make_geo_sweep.py ne scrive uno solo per citta')
    coppie = [(r["citta"], r["grafo"], "neg_rand_" + str(r["grafo"]).split("_", 1)[1])
              for _, r in cov.iterrows() if str(r["grafo"]).startswith("comp_q")]
    trovata = False
    for citta, vero, casuale in coppie:
        vv = vantaggio(str(a.geo_dir / f"geo_{_csv_tag(a.geo_dir, citta, vero, a.semi)}_s{{s}}.csv"), a.semi)
        vc = vantaggio(str(a.geo_dir / f"geo_{_csv_tag(a.geo_dir, citta, casuale, a.semi)}_s{{s}}.csv"), a.semi)'''),
    ('''        arco_v = float(cov.loc[cov.grafo == vero, "arco_medio"].iloc[0])
        arco_c = float(cov.loc[cov.grafo == casuale, "arco_medio"].iloc[0]) \\
            if (cov.grafo == casuale).any() else float("nan")''',
     '''        arco_v = float(cov.loc[(cov.citta == citta) & (cov.grafo == vero), "arco_medio"].iloc[0])
        arco_c = float(cov.loc[(cov.citta == citta) & (cov.grafo == casuale), "arco_medio"].iloc[0]) \\
            if ((cov.citta == citta) & (cov.grafo == casuale)).any() else float("nan")'''),
    ('''        print(f"4 controllo negativo  {vero} contro {casuale}")''',
     '''        print(f"4 controllo negativo  {citta} {vero} contro {casuale}")'''),
    ('''        print("4 controllo negativo  nessuna coppia knn/rand trovata in", a.geo_dir)''',
     '''        print("4 controllo negativo  nessuna coppia comp_q/neg_rand_q trovata in", a.geo_dir)'''),
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
    print(f"  analisi/geometria_criteri.py: {len(SOST)} sostituzioni; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
