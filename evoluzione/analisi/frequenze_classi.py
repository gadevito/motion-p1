#!/usr/bin/env python3
"""
Frequenze delle tre classi (scorrevole / moderato / congestionato) sul periodo
di ADDESTRAMENTO, per contesto e partizione, lette dagli artefatti dei pesi
(`conteggi`) EFFETTIVAMENTE usati dagli esecutori (`evoluzione.analisi.pesi.carica`):
citta' `pesi_griglia/` (non la cartella storica `pesi/` della campagna vecchia:
difetto 23 del registro, 13/10), PEMS04 `pesi_pems04/`, PEMS08 `pesi_pems08/` (p0–p5).
**Sola lettura.** Per ogni artefatto si scrive l'impronta del file (sha256, 16 cifre)
e l'impronta dei pesi registrata dentro l'artefatto, cosi' la tabella del protocollo
e' tracciabile al file che gli addestramenti hanno letto.

Scrive `results/evoluzione/frequenze_classi.json`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/frequenze_classi.py
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CARTELLE = ("pesi_griglia", "pesi_pems04", "pesi_pems08")
ATTESI = {"pesi_griglia": 9, "pesi_pems04": 3, "pesi_pems08": 6}


def _impronta(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    print(f"{'cartella':12s} {'contesto':12s} {'p':>2s} {'celle':>9s} "
          f"{'scorrevole':>11s} {'moderato':>9s} {'congest.':>9s}   pesi               impronta file")
    R, imp = {}, {}
    for cart in CARTELLE:
        d = a.out / cart
        if not d.exists():
            raise SystemExit(f"{d} assente: e' la cartella usata dagli esecutori, deve esistere")
        file = sorted(f for f in d.glob("pesi_*.json") if not f.name.startswith("rapporto"))
        if len(file) != ATTESI[cart]:
            raise SystemExit(f"{d}: {len(file)} artefatti, attesi {ATTESI[cart]}")
        for f in file:
            P = json.loads(f.read_text())
            cnt = [float(x) for x in P["conteggi"]]
            tot = sum(cnt)
            if tot <= 0:
                raise SystemExit(f"{f}: conteggi nulli")
            fr = [x / tot for x in cnt]
            k = f"{cart}/{P['contesto']}/p{P['partizione']}"
            R[k] = {"file": str(f.relative_to(a.out)), "impronta_file": _impronta(f),
                    "impronta_pesi": P.get("impronta"), "frequenze": fr, "conteggi": P["conteggi"],
                    "pesi": P["pesi"], "n_train": P.get("n_train"), "ordine_classi": P.get("ordine_classi")}
            print(f"{cart:12s} {P['contesto']:12s} {P['partizione']:2d} {P.get('n_train', 0):9d} "
                  + " ".join(f"{x:10.2%}" for x in fr)
                  + "   " + ", ".join(f"{w:5.2f}" for w in P["pesi"]) + f"   {R[k]['impronta_file']}")
        imp[cart] = hashlib.sha256("".join(R[k]["impronta_file"] for k in sorted(R) if k.startswith(cart + "/"))
                                   .encode()).hexdigest()[:16]
    doc = {"_cartelle": list(CARTELLE), "_impronte_cartelle": imp,
           "_istante": datetime.now(timezone.utc).isoformat(),
           "_nota": "artefatti letti dagli esecutori (evoluzione.analisi.pesi.carica); frequenze = conteggi / somma, "
                    "sul periodo di addestramento, per orizzonte (conteggio ripetuto dichiarato in pesi.py)",
           **R}
    f = a.out / "frequenze_classi.json"
    f.write_text(json.dumps(doc, indent=2))
    print("\n  impronte per cartella: " + ", ".join(f"{c} {v}" for c, v in imp.items()))
    print(f"  salvato in {f} (impronta {_impronta(f)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
