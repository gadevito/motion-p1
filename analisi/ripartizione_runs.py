#!/usr/bin/env python3
"""
Ripartizione di `paper4/runs/` per il deposito (Zenodo) — richiesta del revisore, 8/11/2026.
=========================================================================================
`paper4/runs/` e' fuori dal repository (`.gitignore` r. 119, salvo `MANIFEST.tsv`). I record congelati in
`paper4/congelamenti/` sono prodotti dai generatori di `paper4/code/` leggendo `runs/`; `paper4/analysis/main.py`
verifica i record e il testo e non legge `runs/`. Gruppi, decisi file per file dal percorso relativo a `paper4/runs/`:

    predizioni_e9    `e9/<run>/*.npz`   (test_hidden, val_hidden, test_observed per cella: 180 esecuzioni)
    predizioni_e11   `e11/<run>/*.npz`  (idem, 240 esecuzioni)
                     Sono INGRESSI di `genera_congelamento_e9.py` / `genera_congelamento_e11.py` (somme per nodo
                     dagli .npz, r. 307-324 e 226-246) e, per E12/E12-bis/E12-ter, dei `run` (G0 e G1 di E9):
                     senza di essi i record di E9, E11 ed E12* si verificano ma non si rigenerano.
    rigenerazione    tutto il resto che i generatori leggono o che li documenta: `e9|e11/<run>/run.json`,
                     `e12|e12bis|e12ter/<run>/*` (run.json, sums.npz, thresholds.json, thresholds.fingerprint),
                     `e10geo/results.json`, `p4a/**`, `MANIFEST.tsv`, `*_costo*.json`, `*_costi*` (json, log,
                     processi.txt), `*_insiemi_geometria.json`
    pilota           piloti, preflight, diagnosi, potenza e log di lancio: `*_pilota*`, `*_preflight*` (comprese le
                     cartelle `*_preflight_cells`, `*_preflight_dirs`), `*_diagnosi*`, `*_potenza*`, `*_lancio*.log`,
                     `*/campagna_shard*.log`, `p4a_run.log`
    altro            cio' che nessuna regola prende (deve restare vuoto; se no, va deciso)

Scrive una tabella Markdown (totali per gruppo; per esperimento; ogni voce di primo livello con i gruppi dei suoi
file) e la stampa. Sola lettura.

Dalla radice di repo-paper4:  python3 analisi/ripartizione_runs.py [--runs paper4/runs] [--md protocol/paper4/zenodo/RIPARTIZIONE_RUNS.md]
"""
import argparse
import hashlib
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
PILOTA = re.compile(r"^([^/]*_(pilota|preflight|diagnosi|potenza|lancio).*|[^/]+/campagna_shard[^/]*\.log|p4a_run\.log)$")
RIGEN = re.compile(r"^((e9|e11)/[^/]+/run\.json|(e12|e12bis|e12ter)/[^/]+/[^/]+|e10geo/results\.json|p4a/.*|MANIFEST\.tsv|"
                   r"[^/]*_costo[^/]*\.json|[^/]*_costi[^/]*|[^/]*_insiemi_geometria\.json)$")
PRED = re.compile(r"^(e9|e11)/[^/]+/[^/]+\.npz$")
ORDINE = ("rigenerazione", "predizioni_e9", "predizioni_e11", "pilota", "altro")


def gruppo(rel: str) -> str:
    if PILOTA.match(rel):
        return "pilota"
    m = PRED.match(rel)
    if m:
        return f"predizioni_{m.group(1)}"
    if RIGEN.match(rel):
        return "rigenerazione"
    return "altro"


def esperimento(rel: str) -> str:
    m = re.match(r"^(e9|e11|e12bis|e12ter|e12|e10geo|p4a)(?=[/_.]|$)", rel)
    return m.group(1) if m else "—"


def mb(b):
    return b / 2 ** 20


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, default=RADICE / "paper4" / "runs")
    ap.add_argument("--md", type=Path, default=RADICE / "protocol" / "paper4" / "zenodo" / "RIPARTIZIONE_RUNS.md")
    a = ap.parse_args()
    tot = defaultdict(lambda: [0, 0]); esp = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    primo = defaultdict(lambda: defaultdict(lambda: [0, 0])); altro = []
    for f in sorted(a.runs.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(a.runs).as_posix(); g = gruppo(rel); b = f.stat().st_size
        tot[g][0] += b; tot[g][1] += 1
        esp[esperimento(rel)][g][0] += b; esp[esperimento(rel)][g][1] += 1
        primo[rel.split("/")[0]][g][0] += b; primo[rel.split("/")[0]][g][1] += 1
        if g == "altro":
            altro.append(rel)
    T = sum(t[0] for t in tot.values()); N = sum(t[1] for t in tot.values())
    L = ["# Ripartizione di `paper4/runs/` per il deposito", "",
         f"Generata da `analisi/ripartizione_runs.py` il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} su `{a.runs}` "
         f"({N:,} file, {T:,} byte = {mb(T) / 1024:.2f} GiB). Regole per nome nel preambolo dello script; sola lettura. "
         "I gruppi «predizioni» sono ingressi dei generatori di E9 ed E11 (somme per nodo dagli `.npz`) e dei `run` di "
         "E12/E12-bis/E12-ter (G0 e G1 di E9): senza di essi quei record si verificano per impronta ma non si rigenerano.", "",
         "## Totali per gruppo", "", "| gruppo | byte | MB | GiB | file |", "|---|---:|---:|---:|---:|"]
    for g in ORDINE:
        if g in tot:
            L.append(f"| {g} | {tot[g][0]:,} | {mb(tot[g][0]):,.1f} | {mb(tot[g][0]) / 1024:.2f} | {tot[g][1]:,} |")
    L.append(f"| **totale** | **{T:,}** | **{mb(T):,.1f}** | **{mb(T) / 1024:.2f}** | **{N:,}** |")
    L += ["", "## Per esperimento e gruppo", "", "| esperimento | gruppo | MB | file |", "|---|---|---:|---:|"]
    for e in sorted(esp, key=lambda k: -sum(v[0] for v in esp[k].values())):
        for g in ORDINE:
            if g in esp[e]:
                L.append(f"| {e} | {g} | {mb(esp[e][g][0]):,.1f} | {esp[e][g][1]:,} |")
    L += ["", "## Voci di primo livello", "", "| voce | gruppo | MB | file |", "|---|---|---:|---:|"]
    for v in sorted(primo, key=lambda k: (-sum(x[0] for x in primo[k].values()), k)):
        for g in ORDINE:
            if g in primo[v]:
                L.append(f"| `{v}` | {g} | {mb(primo[v][g][0]):,.1f} | {primo[v][g][1]:,} |")
    if altro:
        L += ["", "## File senza regola («altro»): da decidere", ""] + [f"- `{r}`" for r in altro]
    else:
        L += ["", "Nessun file senza regola."]
    L.append("")
    testo = "\n".join(L)
    print(testo)
    a.md.parent.mkdir(parents=True, exist_ok=True); a.md.write_text(testo)
    print(f"  -> {a.md} ({hashlib.sha256(a.md.read_bytes()).hexdigest()[:16]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
