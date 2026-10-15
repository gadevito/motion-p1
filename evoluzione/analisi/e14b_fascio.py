#!/usr/bin/env python3
"""
E14 stadio B — il fascio dei json rigenerati con una variante della statica.
=============================================================================
Nella copia (`~/OR3_<variante>`), dopo `esegui_e14b.sh`: raccoglie i json di
`results/evoluzione/` scritti DOPO la preparazione della copia (`--dopo`, istante in
`_e14b/preparata`), piu' i `controllo_*.json` delle cartelle di predizioni; verifica che
l'elenco atteso sia completo e che nessun file atteso sia piu' vecchio della preparazione
(sarebbe un congelato scambiato per rigenerato); scrive `manifesto.json` (variante, commit,
impronta di ogni file) e `e14b_fascio_<variante>.tar.gz` con tutto sotto `e14b/<variante>/`.

Sul Mac il fascio si scompatta in `results/evoluzione/` (→ `results/evoluzione/e14b/<variante>/`)
e la copia da committare va in `protocol/e14b/<variante>/`; `genera_congelamento_e14b.py`
legge da li'.

Uso (dalla radice della copia):

    python evoluzione/analisi/e14b_fascio.py --variante c --dopo 2026-10-13T20:00:00Z
"""
import argparse
import hashlib
import json
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ATTESI = [
    "analisi_e3.json", "veterani_e3.json", "riselezione_rmon_test.json", "e3bis_risultati.json",
    "e4_scelta_gated.json", "e4_risultati.json", "e4_griglia_test.json", "copertura_e4.json",
    "e5_k_secondaria.json", "e5_risultati.json", "e5_settimana_vs_A.json",
    "e6_scelta_gated.json", "e6_risultati.json", "e6bis_risultati.json", "e6_origini_comuni.json",
    "e6a_scelta_gated.json", "e6a_risultati.json",
    "e7_stadio1.json", "e7_posthoc.json",
    "e8_soglie.json", "e8_risultati.json", "e8bis_risultati.json", "curve_e8bis_punti.json",
    "congelamento_e2.json", "congelamento_e3.json", "congelamento_e3bis.json", "congelamento_e4.json",
    "congelamento_e5.json", "congelamento_e7.json",      # E6 ed E8 non scrivono json: solo il .md
]
CONTROLLI = [("predizioni_f0", "controllo_f0.json"), ("predizioni_e2", "controllo_e2.json"),
             ("predizioni_fase3_672", "controllo_R-orig.json")] + \
            [("predizioni_fase3", f"controllo_{b}.json") for b in ("C", "P", "A", "R", "F", "R-orig", "R-mon")]


def _impronta(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--variante", required=True, choices=("a", "b", "c"))
    ap.add_argument("--dopo", required=True, help="istante ISO (UTC) della preparazione della copia")
    a = ap.parse_args()
    dopo = datetime.fromisoformat(a.dopo.replace("Z", "+00:00")).timestamp()
    attesi = [a.out / f for f in ATTESI] + [a.out / f"e14b_livelli_{a.variante}.json"] \
        + [a.out / d / f for d, f in CONTROLLI]
    guai = []
    for f in attesi:
        if not f.exists():
            guai.append(f"manca {f}")
        elif f.stat().st_mtime < dopo:
            guai.append(f"{f} e' piu' vecchio della preparazione della copia")
    if guai:
        for g in guai:
            print("  " + g)
        raise SystemExit(f"{len(guai)} problemi: fascio non scritto")
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    man = {"variante": a.variante, "commit": commit, "preparata": a.dopo,
           "istante": datetime.now(timezone.utc).isoformat(),
           "file": {str(f.relative_to(a.out)): _impronta(f) for f in attesi}}
    pref = Path("e14b") / a.variante
    f_tar = a.out / f"e14b_fascio_{a.variante}.tar.gz"
    with tarfile.open(f_tar, "w:gz") as t:
        for f in attesi:
            t.add(f, arcname=str(pref / f.relative_to(a.out)))
        fm = a.out / f"manifesto_e14b_{a.variante}.json"
        fm.write_text(json.dumps(man, indent=1, ensure_ascii=False))
        t.add(fm, arcname=str(pref / "manifesto.json"))
    print(f"  {len(attesi)} file nel fascio {f_tar} (variante {a.variante}, commit {commit}, "
          f"impronta {_impronta(f_tar)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
