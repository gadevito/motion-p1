#!/usr/bin/env python3
"""
Quarantena del primo lancio di E3 (30/9/2026), che non era E3.
================================================================
`esegui_inserimento` instradava R-orig e R-mon nel ramo di F: i 216 file
`R-orig_*.json` / `R-mon_*.json` in `inserimento_griglia/` sono adattamenti
di F con il nome sbagliato, e i loro manifesti nel registro lo stesso. Non si
cancellano: si spostano in una cartella di quarantena, con un indice, cosi'
che il difetto resti documentato e i marcatori `.fatto` non facciano saltare
le esecuzioni vere.

Sposta anche `esito_concorrente.json`, che quel lancio ha SOVRASCRITTO: il
riepilogo originale della fase 3 e' perso (i numeri restano nei manifesti e
in CONGELAMENTO_E_F_GRIGLIA.md).

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/quarantena_e3_falso.py --piano
    poetry run python evoluzione/esperimenti/quarantena_e3_falso.py
"""
import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

BRACCI = ("R-orig", "R-mon")
DIR_C = "inserimento_griglia"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--piano", action="store_true")
    a = ap.parse_args()
    q = a.out / "_quarantena_e3_falso_20260930"
    da_spostare = []
    for b in BRACCI:
        for f in sorted((a.out / DIR_C).glob(f"{b}_*")):
            da_spostare.append((f, q / DIR_C / f.name))
    esito = a.out / DIR_C / "esito_concorrente.json"
    if esito.exists():
        d = json.loads(esito.read_text())
        # e' quello del lancio falso se ha 216 completate in meno di un'ora
        if d.get("completate") == 216 and d.get("ore_calendario", 9) < 1:
            da_spostare.append((esito, q / DIR_C / "esito_concorrente_FALSO.json"))
    for f in sorted((a.out / "registro").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if d.get("esperimento") in {f"{DIR_C}/{b}" for b in BRACCI}:
            # solo quelli senza addestramento: l'evento «esecutore:» non c'era
            ev = " ".join(e.get("testo", "") for e in d.get("eventi", []))
            if "esecutore: addestra_una" not in ev:
                da_spostare.append((f, q / "registro" / f.name))
    print(f"  da spostare in {q}: {len(da_spostare)} file")
    for f, _ in da_spostare[:8]:
        print(f"     {f}")
    if a.piano:
        print("  --piano: nessuno spostamento.")
        return 0
    for f, g in da_spostare:
        g.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(f), str(g))
    (q / "INDICE.json").write_text(json.dumps(
        {"motivo": ("primo lancio di E3: R-orig e R-mon instradati nel ramo "
                    "di F da `esegui_inserimento._lavora` (ADDESTRANO derivato "
                    "dai soli cinque bracci della fase 3). Adattamenti di F "
                    "con nome sbagliato, un minuto l'uno."),
         "corretto_in": "esegui_inserimento.esecutore(), dalla tabella unica",
         "perso": ("esito_concorrente.json della fase 3, sovrascritto; numeri "
                   "in CONGELAMENTO_E_F_GRIGLIA.md e nei manifesti"),
         "file": [str(f) for f, _ in da_spostare],
         "istante": datetime.now(timezone.utc).isoformat()},
        indent=2, ensure_ascii=False))
    resti = [f for b in BRACCI for f in (a.out / DIR_C).glob(f"{b}_*")]
    print(f"  spostati {len(da_spostare)}; rimasti in {DIR_C}: {len(resti)}")
    return 0 if not resti else 1


if __name__ == "__main__":
    raise SystemExit(main())
