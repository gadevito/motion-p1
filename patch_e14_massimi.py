#!/usr/bin/env python3
"""
Ramo esecutore/e14-massimi (richiesta del revisore, 1/11, 09:45).
1. `evoluzione/audit/massimi_e14b.py`: le etichette delle varianti erano invertite (a → «permutata», c → «causale»);
   il protocollo E14 (emendamento 12/10) definisce (c) = copertura permutata, (a) = statica causale, come
   `VAR_EN` del generatore di D7/D8. Lo script ora prende le etichette da `analysis.tabelle_suppl.VAR_EN` (una sola
   fonte) e scrive una nota datata. Le cifre non cambiano; cambiano i nomi. D7/D8 corrette: nessuna rigenerazione.
2. Didascalie G18–G21: «the cell (seed × partition × sensor) is the resampling unit» → «Intervals use the crossed
   resampling of partitions, seeds and sensor positions described in Section G.» (solo testo).
Sostituzioni letterali; si ferma se un testo atteso non compare esattamente una volta. Dalla radice OR3/:
    python3 patch_e14_massimi.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
MASS = R / "evoluzione" / "audit" / "massimi_e14b.py"
SUPP = R / "analysis" / "tabelle_suppl.py"

SOST = {MASS: [
    ('''NOMI_VAR = {"a": "permutata", "c": "causale", "b": "b"}''',
     '''# etichette delle varianti dalla STESSA fonte del generatore di D7/D8 (analysis/tabelle_suppl.VAR_EN):
# (c) = copertura permutata fra sensori, (a) = statica causale, (b) = causale-b (protocol/E14.md, emendamento 12/10).
# Nella versione del 30/10 le etichette erano invertite (le cifre no): corretto il 2026-11-01.
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from analysis.tabelle_suppl import VAR_EN  # noqa: E402
NOMI_VAR = {v: {"permuted": "permutata", "causal": "causale", "causal-b": "causale-b"}.get(e, e) for v, e in VAR_EN.items()}'''),
    ('''         "Δ = variante − congelato, in wCE (il rapporto (F₀ − C)/(A − C) e le AUC di E8-bis sono esclusi: non sono wCE).", "",''',
     '''         "Δ = variante − congelato, in wCE (il rapporto (F₀ − C)/(A − C) e le AUC di E8-bis sono esclusi: non sono wCE). "
         "Etichette delle varianti da `analysis/tabelle_suppl.py` (`VAR_EN`, la stessa fonte delle tabelle D7/D8): "
         + "; ".join(f"({v}) = {NOMI_VAR[v]}" for v in vv) + ". **Nota del 2026-11-01**: nella versione del 30/10 le etichette "
         "«permutata» e «causale» erano invertite rispetto al protocollo E14 (emendamento 12/10: (c) permutata, (a) causale); "
         "le cifre e i «dove» erano gia' corretti.", "",'''),
], SUPP: [
    ('''UNITA_E18 = ("run (seed $\\\\times$ partition) = unit, mean over runs; the cell (seed $\\\\times$ partition $\\\\times$ sensor) "
             "is the resampling unit")''',
     '''UNITA_E18 = ("run (seed $\\\\times$ partition) = unit, mean over runs. Intervals use the crossed resampling of partitions, "
             "seeds and sensor positions described in Section G")'''),
]}


def main() -> int:
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, _ in coppie:
            if t.count(v) != 1:
                print(f"FERMO: in {f.relative_to(R)} il testo atteso compare {t.count(v)} volte:\n{v[:160]}"); return 1
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, n in coppie:
            t = t.replace(v, n)
        f.write_text(t); print(f"  {f.relative_to(R)}: {len(coppie)} sostituzioni")
    import py_compile
    for f in SOST:
        py_compile.compile(str(f), doraise=True)
    print("  compilazione: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
