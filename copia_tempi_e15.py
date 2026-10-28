#!/usr/bin/env python3
"""
E15 — i registri dei tempi come ingresso congelato (revisore, 28/10).
=====================================================================
Copia in `protocol/e15/tempi/<braccio>/` i marcatori `.fatto` dei 270 addestramenti (nomi da
`esegui_e15.marcatore_di`, quindi esattamente quelli attesi: si ferma se uno manca), piu'
`esito_e15.json` e `E_pilota_e15/pilota_tempi_16.json`. Non tocca i risultati.

Dalla radice OR3/:  python3 copia_tempi_e15.py [--out results/evoluzione]
"""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evoluzione.esperimenti.esegui_e15 import (  # noqa: E402
    BRACCI_ADDESTRATI, ET, celle, marcatore_di, semi_torch_di)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    dst = Path("protocol/e15/tempi")
    st = semi_torch_di()
    mancanti, n = [], 0
    for b in BRACCI_ADDESTRATI:
        (dst / b).mkdir(parents=True, exist_ok=True)
        for c, p, s in celle():
            f = marcatore_di(b, c, p, s, a.out, st)
            if not f.exists():
                mancanti.append(str(f)); continue
            shutil.copy2(f, dst / b / f.name); n += 1
    for f in (a.out / ET["ins"] / "esito_e15.json", a.out / "E_pilota_e15" / "pilota_tempi_16.json"):
        if not f.exists():
            mancanti.append(str(f)); continue
        shutil.copy2(f, dst / f.name); n += 1
    if mancanti:
        print(f"FERMO: {len(mancanti)} file mancanti nei risultati, es. {mancanti[:4]}")
        return 1
    tutti = sorted(dst.rglob("*.*"))
    insieme = hashlib.sha256(b"".join(hashlib.sha256(f.read_bytes()).digest() for f in tutti)).hexdigest()[:16]
    print(f"  copiati {n} file in {dst} ({len(tutti)} presenti); impronta d'insieme {insieme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
