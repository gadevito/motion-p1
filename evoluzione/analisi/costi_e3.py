#!/usr/bin/env python3
"""
E3, controllo 3 — la tabella dei costi con R-orig e R-mon.
============================================================
**Soltanto dal campione isolato** (un processo, macchina libera): 3 citta',
partizione 0, semi 201-203. I tempi in concorrenza non entrano.

Per i bracci della fase 3 si leggono i manifesti isolati gia' esistenti; per
R-orig e R-mon quelli della rimisura (`esegui_inserimento.py --isolato
--rimisura --braccio R-orig R-mon`), che riportano anche la wCE concorrente
riprodotta.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/costi_e3.py --out results/evoluzione/costi_e3.json
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

BRACCI = ("C", "P", "A", "R", "R-orig", "R-mon", "F")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/inserimento_griglia"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    iso = defaultdict(list)
    for f in sorted(a.dir.glob("*.json")):
        if f.name.startswith("esito_"):
            continue
        d = json.loads(f.read_text())
        if d.get("modalita_misura") == "isolata":
            iso[d["braccio"]].append(d)
    print("=" * 84)
    print("TABELLA DEI COSTI — campione isolato, un processo")
    print("=" * 84)
    print(f"  {'braccio':8s} {'n':>3} {'addestr.':>10} {'inserim.':>11} "
          f"{'attesa dati':>12} {'disponibile':>12} {'riprod.':>8}")
    fuori = {}
    for b in BRACCI:
        ci = iso.get(b, [])
        if not ci:
            print(f"  {b:8s}   0  (nessuna misura isolata)")
            fuori[b] = {"esecuzioni_isolate": 0}
            continue
        med = lambda g: float(np.median([g(x) for x in ci]))  # noqa: E731
        rip = [x["rimisura_di"]["wce"] for x in ci if "rimisura_di" in x]
        fuori[b] = {
            "esecuzioni_isolate": len(ci),
            "addestramento_s": med(lambda x: x["costo"]["addestramento_s"]),
            "inserimento_s": med(lambda x: x["costo"]["inserimento_s"]),
            "attesa_dati_s": med(lambda x: x["tempo_disponibilita"]["attesa_dati_s"]),
            "disponibilita_s": med(lambda x: x["tempo_disponibilita"]["disponibilita_s"]),
            "rimisure_che_riproducono_la_concorrente": len(rip),
            "celle": [(x["contesto"], x["partizione"], x["seme"]) for x in ci]}
        q = fuori[b]
        print(f"  {b:8s} {len(ci):3d} {q['addestramento_s']/60:9.1f}m "
              f"{q['inserimento_s']:10.1f}s {q['attesa_dati_s']/3600:11.0f}h "
              f"{q['disponibilita_s']/3600:11.1f}h {len(rip):>8}")
    print("\n  addestramento = prima dell'installazione; inserimento = dopo "
          "(R e derivati: tutto il riaddestramento; F: l'adattamento; P: il "
          "descrittore)")
    if a.out:
        a.out.write_text(json.dumps(fuori, indent=2, ensure_ascii=False))
        print(f"  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
