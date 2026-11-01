#!/usr/bin/env python3
"""
Ramo esecutore/e14-massimi-2 (richiesta del revisore, 1/11, 12:56). In `evoluzione/audit/massimi_e14b.py` le famiglie
«livelli_assoluti» e «livelli_diff» leggevano il dizionario `delta_<v>` del congelamento, che copre solo C, A, F0 e
A-C, F0-C: mancavano F0' (il token) e F'(24 h), che D8 stampa (F0' Madrid +0.0053, Melbourne +0.0052 per la permutata).
Ora Δ = variante − congelato sulle medie di TUTTI i bracci di `livelli` e di TUTTE le `differenze` del congelamento
(`<città>/(v)` contro `<città>/congelato`); `delta_<v>` resta come controllo (lo script si ferma se C, A, F0, A-C, F0-C
non coincidono entro 1e-9); l'elenco dei bracci inclusi e' scritto nel MD con nota datata.
Sostituzioni letterali; si ferma se un testo atteso non compare esattamente una volta. Dalla radice OR3/:
    python3 evoluzione/audit/patch/patch_e14_massimi_2.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[3]
F = R / "evoluzione" / "audit" / "massimi_e14b.py"

SOST = [
    ('''    for key, z in R["livelli"].items():
        if "/delta_" not in key:
            continue
        c, v = key.split("/delta_")
        for n in ("C", "A", "F0"):
            agg(v, "livelli_assoluti", f"{c}/{n}", z.get(n))
        for n in ("A-C", "F0-C"):
            agg(v, "livelli_diff", f"{c}/{n}", z.get(n))
''',
     '''    # livelli e differenze: tutti i bracci di D8 (`livelli`: C, A, F0, F0p, Fp_96) e tutte le `differenze` del
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
'''),
    ('''         "le cifre e i «dove» erano gia' corretti.", "",''',
     '''         "le cifre e i «dove» erano gia' corretti.", "",
         "Famiglie: `dichiarazioni` = le cinque dichiarazioni (a)–(e) per contesto ed episodio; `livelli_assoluti` = wCE "
         "assoluta dei bracci " + ", ".join(f"`{b}`" for b in bracci) + " (episodio 1, i bracci della tabella D8); "
         "`livelli_diff` = differenze " + ", ".join(f"`{b}`" for b in differ) + "; `altre` = altre dichiarazioni (E3, "
         "E3-bis, E4, E8, E8-bis) con Δ in wCE; `e8_wce` = wCE delle soglie E8. Δ dei livelli e delle differenze = media "
         "della variante − media congelata (`<città>/(v)` contro `<città>/congelato`), controllata contro `delta_<v>` "
         "dove questo esiste. **Nota del 2026-11-01 (seconda)**: fino a questa data `livelli_assoluti` e `livelli_diff` "
         "leggevano solo `delta_<v>` (C, A, F0; A-C, F0-C): mancavano F0' e F'(24 h).", "",'''),
]


def main() -> int:
    t = F.read_text()
    for v, _ in SOST:
        if t.count(v) != 1:
            print(f"FERMO: il testo atteso compare {t.count(v)} volte:\n{v[:200]}"); return 1
    for v, n in SOST:
        t = t.replace(v, n)
    F.write_text(t)
    import py_compile
    py_compile.compile(str(F), doraise=True)
    print(f"  evoluzione/audit/massimi_e14b.py: {len(SOST)} sostituzioni; compilazione ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
