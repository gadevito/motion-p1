#!/usr/bin/env python3
"""
Verifica della copia sul Mac degli ingressi di E18 (probabilita' di E16, ricostruzione PEMS04, celle sostituite).
=====================================================================================================================
Confronta ogni file citato in `results/evoluzione/e18_risultati.json` → `impronte_ingressi` (parte A: `predizioni_e16/
prova_*`, `predizioni_e18_pems04/*`; parte C: `predizioni_e16/prova_*`) con l'impronta sha256 (16 esadecimali) del file
copiato; elenca i file copiati non citati (validazione di E16, celle sostituite) con la loro impronta. Si ferma, con
codice 1, se un file citato manca o ha impronta diversa. Scrive un resoconto in `protocol/e18/COPIA_INGRESSI_MAC.md`.

Dalla radice OR3/:  python3 evoluzione/audit/verifica_ingressi_e18.py
"""
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("results/evoluzione")
CARTELLE = ("predizioni_e16", "predizioni_e18_pems04", "predizioni_e16_spark_sostituite")


def imp(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def main() -> int:
    R = json.loads((OUT / "e18_risultati.json").read_text())
    citati = {}
    for k, v in R["A"]["impronte_ingressi"].items():
        citati.setdefault(k, set()).add(v)
    for nome, v in R["C"]["impronte_ingressi"]["predizioni_e16"].items():
        citati.setdefault(f"predizioni_e16/{nome}", set()).add(v)
    incoerenti = {k: v for k, v in citati.items() if len(v) != 1}
    if incoerenti:
        print(f"FERMO: {len(incoerenti)} file con impronte diverse fra parte A e parte C nel json: {sorted(incoerenti)[:5]}"); return 1
    citati = {k: next(iter(v)) for k, v in citati.items()}
    mancanti, diversi, uguali = [], [], 0
    print(f"  {len(citati)} file citati in e18_risultati.json (parti A e C); impronte in corso...", flush=True)
    impronte = {}
    for k in sorted(citati):
        p = OUT / k
        if not p.exists():
            mancanti.append(k); continue
        impronte[k] = imp(p)
        if impronte[k] != citati[k]:
            diversi.append((k, citati[k], impronte[k]))
        else:
            uguali += 1
    non_citati = {}
    for c in CARTELLE:
        d = OUT / c
        if not d.is_dir():
            mancanti.append(c + "/"); continue
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.relative_to(OUT).as_posix() not in citati:
                non_citati[p.relative_to(OUT).as_posix()] = (imp(p), p.stat().st_size)
    byte = sum(p.stat().st_size for c in CARTELLE if (OUT / c).is_dir() for p in (OUT / c).rglob("*") if p.is_file())
    L = ["# Copia sul Mac degli ingressi di E18 — verifica", "",
         f"Eseguita da `evoluzione/audit/verifica_ingressi_e18.py` il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} "
         f"su `{platform.node()}`. Cartelle: {', '.join(f'`{c}/`' for c in CARTELLE)}; {byte / 2**20:,.0f} MB in tutto.", "",
         f"- File citati in `e18_risultati.json` (`impronte_ingressi` delle parti A e C): **{len(citati)}**; impronta uguale: **{uguali}**; "
         f"diversa: **{len(diversi)}**; mancanti: **{len(mancanti)}**.",
         f"- File copiati non citati (validazione di E16 e celle sostituite, non ingressi di E18): {len(non_citati)}.", ""]
    if diversi:
        L += ["| file | impronta citata | impronta del file copiato |", "|---|---|---|"] + [f"| `{k}` | `{a}` | `{b}` |" for k, a, b in diversi] + [""]
    if mancanti:
        L += ["Mancanti: " + ", ".join(f"`{m}`" for m in mancanti), ""]
    L += ["## File citati (impronta sha256, 16 esadecimali)", "", "| file | impronta |", "|---|---|"]
    L += [f"| `{k}` | `{impronte[k]}` |" for k in sorted(impronte)]
    L += ["", "## File copiati non citati", "", "| file | impronta | byte |", "|---|---|---:|"]
    L += [f"| `{k}` | `{v[0]}` | {v[1]:,} |" for k, v in sorted(non_citati.items())]
    out = Path("protocol/e18/COPIA_INGRESSI_MAC.md"); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    print("\n".join(L[4:6])); print(f"  -> {out}")
    if diversi or mancanti:
        print(f"FERMO: {len(diversi)} impronte diverse, {len(mancanti)} mancanti"); return 1
    print("  copia verificata: tutte le impronte citate coincidono")
    return 0


if __name__ == "__main__":
    sys.exit(main())
