#!/usr/bin/env python3
"""
Ripartizione di `results/evoluzione/` per il deposito (Zenodo).
================================================================
Quattro gruppi, decisi per cartella di primo livello (o file):

    rigenerazione   cio' che `analysis/main.py` legge per rigenerare: dai nomi (predizioni_* aggregate, maschere,
                    pesi_*, selezioni, json congelati e di scelta). L'elenco degli ingressi dell'ultimo giro
                    (`rapporto.json` → `impronte_ingressi`) e' l'istantanea d'integrita' di tutto results/evoluzione
                    e NON distingue i gruppi: si usa solo senza `--per-nomi`, per confronto
    probabilita     le probabilita' per cella di E16 e la ricostruzione PEMS04 di E18 (`predizioni_e16*`,
                    `predizioni_e18_pems04`)
    punti           punti di controllo e stati dei modelli (cartelle con `.pt`: `*inserimento*`, `stati_*`,
                    `E*_e6_*`, `e6_pems08*`, `rmon_punti`, `pems04`, `canonico`, `stati_iniziali`, `e14b`)
    altro           il resto (campagne precedenti `raccordo*`, `predizioni_refresh`, sensibilita', adeguatezza,
                    quarantene, registri, log, piloti, collaudi, `predizioni_pems04` della ricostruzione preliminare)

Scrive una tabella Markdown (cartella, gruppo, MB, file) e i totali per gruppo; `--md` per il percorso.

Dalla radice OR3/:  python3 evoluzione/audit/ripartizione_results.py [--md protocol/zenodo/RIPARTIZIONE_RESULTS.md]
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PROB = ("predizioni_e16", "predizioni_e16_spark_sostituite", "predizioni_e18_pems04")
ALTRO = re.compile(r"^(.*collaudo.*|.*pilota.*|.*prova_e3|.*adeguatezza.*|stati_completi|prova_inserimento|stati_prova_inserimento|"
                   r"_quarantena.*|registro.*|raccordo.*|predizioni_refresh|predizioni_sensibilita_rho|predizioni_pems04|audit.*|predizioni)$")  # solo cartelle
PUNTI = re.compile(r"^(stati_.*|.*inserimento.*|E1?_e6_.*|e6_pems08.*|e6_(costi|sessione)_.*|E1_costi_sessione|rmon_punti|pems04|canonico|stati_iniziali|e14b)$")
RIGEN = re.compile(r"^(predizioni_(fase3|fase3_672|e2|f0|e4|e5|e6|e6a|e6bis|e8|e14|e15|veterani_e3)|maschere|pesi(_[a-z0-9]+)*|selezione_F.*|e15_controllo_congelata|"
                   r"frequenze_classi\.json|.*_risultati\.json|.*_scelta_gated\.json|congelamento_.*\.json|e15_k_secondaria\.json|"
                   r"e15_preflight\.json|e5_k_secondaria\.json|preparazione_e5\.json|costi_.*\.json|architettura_ck\.json|.*\.json)$")


def dim(p: Path):
    if p.is_file():
        return p.stat().st_size, 1
    n = b = 0
    for f in p.rglob("*"):
        if f.is_file():
            b += f.stat().st_size; n += 1
    return b, n


def ingressi_main(radice: Path):
    """Le cartelle/file di primo livello citati dagli ingressi dell'ultimo giro di main.py, se c'e'."""
    giri = sorted((radice / "analysis" / "rigenerazione").glob("2026*/rapporto.json"))
    if not giri:
        return None, None
    J = json.loads(giri[-1].read_text())
    voci = J.get("meta", J).get("impronte_ingressi") or J.get("impronte_ingressi") or {}
    primi = set()
    for k in voci:
        primi.add(str(k).split("/")[0])
    return primi, giri[-1].parent.name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--md", type=Path, default=None)
    ap.add_argument("--per-nomi", action="store_true",
                    help="gruppo «rigenerazione» dai nomi anche se esiste un giro di main.py (il cui elenco degli ingressi "
                         "e' l'istantanea d'integrita' di TUTTO results/evoluzione e non distingue i gruppi)")
    a = ap.parse_args()
    radice = Path(__file__).resolve().parents[2]
    primi, giro = (None, None) if a.per_nomi else ingressi_main(radice)
    righe, tot = [], {}
    for p in sorted(a.out.iterdir()):
        nome = p.name
        if nome in PROB:
            g = "probabilita"
        elif nome.endswith(".log") or (p.is_dir() and ALTRO.match(nome)):
            g = "altro"
        elif primi is not None and nome in primi:
            g = "rigenerazione"
        elif PUNTI.match(nome) and not nome.startswith("predizioni"):
            g = "punti"
        elif primi is None and RIGEN.match(nome):
            g = "rigenerazione"
        elif nome.endswith(".json") and (nome.endswith("_risultati.json") or nome.startswith("congelamento_") or nome.endswith("_scelta_gated.json")):
            g = "rigenerazione"
        else:
            g = "altro"
        b, n = dim(p)
        righe.append((nome, g, b / 2 ** 20, n))
        t = tot.setdefault(g, [0.0, 0]); t[0] += b / 2 ** 20; t[1] += n
    L = ["# Ripartizione di `results/evoluzione/` per il deposito", "",
         f"Generata da `evoluzione/audit/ripartizione_results.py` il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}; "
         + (f"gruppo «rigenerazione» = ingressi dell'ultimo giro di `main.py` (`analysis/rigenerazione/{giro}/rapporto.json`)."
            if primi is not None else "gruppo «rigenerazione» deciso dai nomi (nessun giro di `main.py` trovato in `analysis/rigenerazione/`)."), "",
         "| gruppo | MB | file |", "|---|---:|---:|"]
    for g in ("rigenerazione", "probabilita", "punti", "altro"):
        if g in tot:
            L.append(f"| {g} | {tot[g][0]:,.0f} | {tot[g][1]:,} |")
    L.append(f"| **totale** | **{sum(t[0] for t in tot.values()):,.0f}** | **{sum(t[1] for t in tot.values()):,}** |")
    L += ["", "| cartella / file | gruppo | MB | file |", "|---|---|---:|---:|"]
    for nome, g, mb, n in sorted(righe, key=lambda r: (-r[2], r[0])):
        L.append(f"| `{nome}` | {g} | {mb:,.1f} | {n:,} |")
    testo = "\n".join(L) + "\n"
    print(testo if a.md is None else "\n".join(L[:12]))
    if a.md is not None:
        a.md.parent.mkdir(parents=True, exist_ok=True); a.md.write_text(testo); print(f"  -> {a.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
