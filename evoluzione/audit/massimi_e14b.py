#!/usr/bin/env python3
"""
Massimo |Δ| in E14-B per variante e per famiglia, dal congelamento (`results/evoluzione/congelamento_e14b.json`).
======================================================================================================================
Serve al testo di §III-C del manoscritto («at most … wCE»): il dominio esatto dell'affermazione. Famiglie:
    dichiarazioni     le cinque dichiarazioni (a)–(e) per contesto ed episodio (Δ = variante − congelato, wCE)
    livelli_assoluti  livelli di C, A, F₀ per citta' (Δ wCE)
    livelli_diff      A − C e F₀ − C per citta' (Δ wCE)
    altre             altre dichiarazioni (E3, E3-bis, veterani, E4), Δ wCE
    e8_wce            confronti di E8 in wCE (Δ)
Scrive `protocol/e14b/MASSIMI_DELTA.md` (tabella variante × famiglia: max |Δ|, dove, n) e stampa la tabella.

Dalla radice OR3/:  python3 evoluzione/audit/massimi_e14b.py [--md protocol/e14b/MASSIMI_DELTA.md]
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

NOMI_VAR = {"a": "permutata", "c": "causale", "b": "b"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--md", type=Path, default=Path("protocol/e14b/MASSIMI_DELTA.md"))
    a = ap.parse_args()
    fj = a.out / "congelamento_e14b.json"
    R = json.loads(fj.read_text())
    vv = R["varianti"]
    fam = {v: {} for v in vv}

    def agg(v, famiglia, dove, d):
        if d is None:
            return
        f = fam[v].setdefault(famiglia, {"max": 0.0, "dove": None, "n": 0})
        f["n"] += 1
        if abs(d) > f["max"]:
            f["max"], f["dove"], f["valore"] = abs(d), dove, d
    for key, z in R["dichiarazioni"].items():
        if key == "stesso_segno" or "varianti" not in z:
            continue
        for v, cf in z["varianti"].items():
            agg(v, "dichiarazioni", key, cf.get("delta"))
    for key, z in R["livelli"].items():
        if "/delta_" not in key:
            continue
        c, v = key.split("/delta_")
        for n in ("C", "A", "F0"):
            agg(v, "livelli_assoluti", f"{c}/{n}", z.get(n))
        for n in ("A-C", "F0-C"):
            agg(v, "livelli_diff", f"{c}/{n}", z.get(n))
    for key, cf in R.get("altre", {}).items():
        if not isinstance(cf, dict) or "delta" not in cf:
            continue
        v = key.rsplit("/", 1)[-1]
        if v in fam:
            agg(v, "altre", key.rsplit("/", 1)[0], cf["delta"])
    for key, z in R.get("e8", {}).items():
        v = key.rsplit("/", 1)[-1]
        if v in fam and isinstance(z.get("wce"), dict):
            agg(v, "e8_wce", key.rsplit("/", 1)[0], z["wce"].get("delta"))
    FAM = ("dichiarazioni", "livelli_assoluti", "livelli_diff", "altre", "e8_wce")
    L = ["# E14-B — massimo |Δ| per variante e per famiglia", "",
         f"Derivato da `evoluzione/audit/massimi_e14b.py` da `results/evoluzione/congelamento_e14b.json` (impronta "
         f"`{hashlib.sha256(fj.read_bytes()).hexdigest()[:16]}`) il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
         "Δ = variante − congelato, in wCE (il rapporto (F₀ − C)/(A − C) e le AUC di E8-bis sono esclusi: non sono wCE).", "",
         "| variante | famiglia | n | max \\|Δ\\| | Δ | dove |", "|---|---|---:|---:|---:|---|"]
    for v in vv:
        for f in FAM:
            z = fam[v].get(f)
            if z:
                L.append(f"| {NOMI_VAR.get(v, v)} ({v}) | {f} | {z['n']} | {z['max']:.4f} | {z['valore']:+.4f} | `{z['dove']}` |")
        tutti = max((z["max"] for z in fam[v].values()), default=0.0)
        L.append(f"| {NOMI_VAR.get(v, v)} ({v}) | **tutte** | {sum(z['n'] for z in fam[v].values())} | **{tutti:.4f}** | | |")
    testo = "\n".join(L) + "\n"
    a.md.parent.mkdir(parents=True, exist_ok=True); a.md.write_text(testo)
    print(testo); print(f"  -> {a.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
