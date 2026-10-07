#!/usr/bin/env python3
"""
Frequenze delle tre classi (scorrevole / moderato / congestionato) sul periodo
di ADDESTRAMENTO, per contesto e partizione, lette dagli artefatti dei pesi
(`conteggi`): citta' (`pesi/`), PEMS04 (`pesi_pems04/`), PEMS08 (`pesi_pems08/`).
**Sola lettura**: la tabella va in `protocol/E6.md` prima della firma, come
chiesto dal revisore (la classe rara e' una proprieta' del dato, si dichiara
prima e non quando si vedono gli intervalli).

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/frequenze_classi.py
"""
import argparse
import json
from pathlib import Path

CARTELLE = ("pesi", "pesi_pems04", "pesi_pems08")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    print(f"{'cartella':12s} {'contesto':12s} {'p':>2s} {'origini':>8s} "
          f"{'scorrevole':>11s} {'moderato':>9s} {'congest.':>9s}   pesi")
    R = {}
    for cart in CARTELLE:
        d = a.out / cart
        if not d.exists():
            print(f"{cart:12s} (assente)"); continue
        for f in sorted(d.glob("pesi_*.json")):
            P = json.loads(f.read_text())
            cnt = [float(x) for x in P["conteggi"]]
            tot = sum(cnt)
            if tot <= 0:
                continue
            fr = [x / tot for x in cnt]
            k = f"{cart}/{P['contesto']}/p{P['partizione']}"
            R[k] = {"frequenze": fr, "pesi": P["pesi"], "n_train": P.get("n_train"),
                    "ordine_classi": P.get("ordine_classi")}
            print(f"{cart:12s} {P['contesto']:12s} {P['partizione']:2d} {P.get('n_train', 0):8d} "
                  + " ".join(f"{x:10.2%}" for x in fr)
                  + "   " + ", ".join(f"{w:.2f}" for w in P["pesi"]))
    (a.out / "frequenze_classi.json").write_text(json.dumps(R, indent=2))
    print(f"\n  salvato in {a.out / 'frequenze_classi.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
