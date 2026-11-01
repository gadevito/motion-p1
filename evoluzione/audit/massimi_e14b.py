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

# etichette delle varianti dalla STESSA fonte del generatore di D7/D8 (analysis/tabelle_suppl.VAR_EN):
# (c) = copertura permutata fra sensori, (a) = statica causale, (b) = causale-b (protocol/E14.md, emendamento 12/10).
# Nella versione del 30/10 le etichette erano invertite (le cifre no): corretto il 2026-11-01.
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from analysis.tabelle_suppl import VAR_EN  # noqa: E402
NOMI_VAR = {v: {"permuted": "permutata", "causal": "causale", "causal-b": "causale-b"}.get(e, e) for v, e in VAR_EN.items()}


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
    # livelli e differenze: tutti i bracci di D8 (`livelli`: C, A, F0, F0p, Fp_96) e tutte le `differenze` del
    # congelamento, Δ = variante − congelato sulle medie; il dizionario `delta_<v>` copre solo C, A, F0, A-C, F0-C e
    # serve da controllo (fino al 2026-11-01 lo script leggeva solo quello: F0' e F'(24 h) mancavano).
    bracci, differ = [], []
    for key, x in R["livelli"].items():
        if not key.endswith("/congelato"):
            continue
        c = key.split("/")[0]
        for v in vv:
            y, ctrl = R["livelli"][f"{c}/({v})"], R["livelli"].get(f"{c}/delta_{v}", {})
            for fam_n, campo, elenco in (("livelli_assoluti", "livelli", bracci), ("livelli_diff", "differenze", differ)):
                for n, z in y[campo].items():
                    d = z["media"] - x[campo][n]["media"]
                    if n in ctrl and abs(d - ctrl[n]) > 1e-9:
                        raise SystemExit(f"FERMO: {c}/{v}/{n}: Δ dalle medie {d:+.6f} ≠ delta_{v} {ctrl[n]:+.6f}")
                    agg(v, fam_n, f"{c}/{n}", d)
                    if n not in elenco:
                        elenco.append(n)
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
         "Δ = variante − congelato, in wCE (il rapporto (F₀ − C)/(A − C) e le AUC di E8-bis sono esclusi: non sono wCE). "
         "Etichette delle varianti da `analysis/tabelle_suppl.py` (`VAR_EN`, la stessa fonte delle tabelle D7/D8): "
         + "; ".join(f"({v}) = {NOMI_VAR[v]}" for v in vv) + ". **Nota del 2026-11-01**: nella versione del 30/10 le etichette "
         "«permutata» e «causale» erano invertite rispetto al protocollo E14 (emendamento 12/10: (c) permutata, (a) causale); "
         "le cifre e i «dove» erano gia' corretti.", "",
         "Famiglie: `dichiarazioni` = le cinque dichiarazioni (a)–(e) per contesto ed episodio; `livelli_assoluti` = wCE "
         "assoluta dei bracci " + ", ".join(f"`{b}`" for b in bracci) + " (episodio 1, i bracci della tabella D8); "
         "`livelli_diff` = differenze " + ", ".join(f"`{b}`" for b in differ) + "; `altre` = altre dichiarazioni (E3, "
         "E3-bis, E4, E8, E8-bis) con Δ in wCE; `e8_wce` = wCE delle soglie E8. Δ dei livelli e delle differenze = media "
         "della variante − media congelata (`<città>/(v)` contro `<città>/congelato`), controllata contro `delta_<v>` "
         "dove questo esiste. **Nota del 2026-11-01 (seconda)**: fino a questa data `livelli_assoluti` e `livelli_diff` "
         "leggevano solo `delta_<v>` (C, A, F0; A-C, F0-C): mancavano F0' e F'(24 h).", "",
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
