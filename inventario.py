#!/usr/bin/env python3
"""
Inventario del repository: che cosa serve e che cosa no.
=========================================================
NON CANCELLA NULLA. Classifica i file in categorie e stampa che cosa farebbe,
cosi' che la decisione resti tua.

LE CATEGORIE, in ordine di certezza decrescente:

  ESSENZIALE   script, dati sorgente, artefatti costruiti, risultati citati dal
               README. Non si tocca.
  RISULTATO    CSV e npz nella cartella dei risultati. Vanno tenuti: sono la
               fonte delle tabelle, e rigenerarli costa ore macchina.
  LOG          .log e .txt di esecuzione. Tenerli e' utile per tracciabilita' ma
               non servono a riprodurre nulla: comprimibili.
  ARCHIVIO     .tgz e .zip. Quasi sempre spedizioni gia' consegnate.
  DERIVATO     file rigenerabili in minuti da uno script del README.
  ORFANO       non citato dal README, non prodotto da alcuno script noto, non
               letto da nulla. E' la categoria da guardare con attenzione.
  DUPLICATO    copie con nome alterato dal download: « 2.py », « (1).csv »,
               « 20.05.59.py ».

REGOLA CHE LO SCRIPT APPLICA. Un file e' ORFANO solo se: non e' citato nel
README, non corrisponde a uno schema di uscita noto, e nessuno script del
repository ne contiene il nome. E' una regola conservativa: preferisce
classificare come essenziale qualcosa di inutile piuttosto che il contrario.

Uso (dalla radice OR3/):

    poetry run python inventario.py
    poetry run python inventario.py --dettaglio orfano
    poetry run python inventario.py --genera-script pulizia.sh
"""
from pathlib import Path
import argparse
import re
import shlex
import sys
from collections import defaultdict

CARTELLE_IGNORATE = {".git", "__pycache__", ".venv", "node_modules", "__MACOSX",
                     ".ipynb_checkpoints", ".pytest_cache"}

# file e cartelle che non si toccano mai
ESSENZIALI_ESATTI = {"README.md", "pyproject.toml", "poetry.lock", ".gitignore",
                     "build_results.sh", "LICENSE", "LICENSE.txt"}
CARTELLE_DATI = {"data_collection", "austin", "descrittori", "models", "baselines",
                 "analisi", "prereg", "papers"}
CARTELLE_RISULTATI = {"replication", "results", "geo_sweep", "kit_archivio"}

# schemi delle uscite prodotte dagli script del README
SCHEMI_RISULTATO = [
    r"^(classify|lgb|sparse|rnn|sota)_.+_s\d+\.csv$",
    r"^(prec|lgbristr|fix_sparse|fix_classify|camp_sparse)_.+\.csv$",
    r"^(a6[A-Z0-9]+|ident|alpha[NG]|lgbreg|wx_(reale|permutato))_.+\.csv$",
    r"^(geo|stid|winabl|stae_full|val_(nn|gb))_.+\.csv$",
    r"^onboard[A-E]?_.+\.csv$", r"^ign_.+\.csv$", r"^placement_.+\.csv$",
    r"^covariate_.+\.csv$", r"^crossval.*\.csv$",
    r"^(ALL_results|MODEL_leaderboard|FINDINGS_check)\.csv$",
    r"\.npz$", r"\.npy$", r"\.pkl$", r"\.parquet$",
]
ESTENSIONI_LOG = {".log"}
ESTENSIONI_ARCHIVIO = {".tgz", ".tar", ".gz", ".zip", ".bz2", ".xz"}
ESTENSIONI_DOC = {".docx", ".pdf", ".md", ".tex", ".png", ".jpg", ".svg"}

# rigenerabili in minuti dagli script del README
SCHEMI_DERIVATO = [
    r"^imputazione_(aggregato|per_ora|per_sensore)\.csv$",
    r"^stats_report.*\.txt$", r"^geo_criteri_printout\.txt$",
    r"^tabella_verifiche_preregistrate\.csv$", r"^copertura_realizzata\.csv$",
]
SCHEMI_DUPLICATO = [
    r" \d+\.[a-z]+$",              # « file 2.py »
    r"\(\d+\)\.[a-z]+$",           # « file (1).csv »
    r" \d\d\.\d\d\.\d\d\.[a-z]+$", # « file 20.05.59.py »
    r"^~\$",                       # file temporanei di Word
    r"^\._",                       # risorse macOS
    r"\.INVALID$",
]


def classifica(p: Path, radice: Path, citati: set, nominati: set) -> str:
    nome = p.name
    rel = p.relative_to(radice)
    parti = set(rel.parts[:-1])

    for s in SCHEMI_DUPLICATO:
        if re.search(s, nome):
            return "DUPLICATO"
    if nome in ESSENZIALI_ESATTI or nome.endswith(".py"):
        return "ESSENZIALE"
    if p.suffix in ESTENSIONI_ARCHIVIO:
        return "ARCHIVIO"
    if p.suffix in ESTENSIONI_LOG:
        return "LOG"
    if parti & CARTELLE_DATI:
        return "ESSENZIALE"
    if parti & CARTELLE_RISULTATI:
        return "RISULTATO"
    for s in SCHEMI_DERIVATO:
        if re.match(s, nome):
            return "DERIVATO"
    for s in SCHEMI_RISULTATO:
        if re.search(s, nome):
            return "RISULTATO"
    if p.suffix in ESTENSIONI_DOC:
        return "DOCUMENTO"
    if nome in citati or nome in nominati:
        return "ESSENZIALE"
    if p.suffix == ".txt":
        return "LOG"
    return "ORFANO"


def main() -> int:
    ap = argparse.ArgumentParser(description="inventario del repository")
    ap.add_argument("--radice", type=Path, default=Path("."))
    ap.add_argument("--dettaglio", default=None,
                    help="categoria di cui elencare tutti i file")
    ap.add_argument("--genera-script", type=Path, default=None,
                    help="scrive uno script di archiviazione DA RILEGGERE prima di eseguire")
    a = ap.parse_args()

    radice = a.radice.resolve()
    if not radice.is_dir():
        print(f"ERRORE: {radice} non e' una cartella", file=sys.stderr)
        return 1

    readme = radice / "README.md"
    citati = set(re.findall(r"[\w./-]+\.\w+", readme.read_text())) if readme.exists() else set()
    citati = {Path(c).name for c in citati}

    nominati = set()
    for s in radice.rglob("*.py"):
        if any(x in s.parts for x in CARTELLE_IGNORATE):
            continue
        try:
            nominati |= {Path(c).name for c in
                         re.findall(r"[\w./-]+\.\w+", s.read_text(errors="ignore"))}
        except OSError:
            pass

    gruppi = defaultdict(list)
    for p in radice.rglob("*"):
        if not p.is_file() or any(x in p.parts for x in CARTELLE_IGNORATE):
            continue
        gruppi[classifica(p, radice, citati, nominati)].append(p)

    print(f"radice: {radice}\n")
    print(f"{'categoria':12s} {'file':>7} {'spazio':>11}   cosa farne")
    print("-" * 78)
    AZIONE = {
        "ESSENZIALE": "tenere",
        "RISULTATO": "tenere: rigenerarli costa ore macchina",
        "DOCUMENTO": "tenere",
        "LOG": "comprimere in un unico archivio",
        "ARCHIVIO": "spostare fuori dal repository",
        "DERIVATO": "rigenerabile in minuti dal README",
        "DUPLICATO": "cancellabile dopo confronto con l'originale",
        "ORFano": "", "ORFANO": "DA GUARDARE: non citato e non prodotto",
    }
    tot = 0
    for k in ("ESSENZIALE", "RISULTATO", "DOCUMENTO", "DERIVATO", "LOG",
              "ARCHIVIO", "DUPLICATO", "ORFANO"):
        f = gruppi.get(k, [])
        if not f:
            continue
        b = sum(x.stat().st_size for x in f)
        tot += b
        print(f"{k:12s} {len(f):7d} {b / 1e6:10.1f}M   {AZIONE[k]}")
    print("-" * 78)
    print(f"{'totale':12s} {sum(len(v) for v in gruppi.values()):7d} {tot / 1e6:10.1f}M")

    for k in ("DUPLICATO", "ORFANO"):
        f = sorted(gruppi.get(k, []), key=lambda x: -x.stat().st_size)
        if not f:
            continue
        print(f"\n{k} — {len(f)} file")
        for p in f[:25]:
            print(f"   {p.stat().st_size / 1e3:9.0f}K  {p.relative_to(radice)}")
        if len(f) > 25:
            print(f"   ... e altri {len(f) - 25}")

    if a.dettaglio:
        k = a.dettaglio.upper()
        f = sorted(gruppi.get(k, []), key=lambda x: -x.stat().st_size)
        print(f"\n{k} — elenco completo ({len(f)} file)")
        for p in f:
            print(f"   {p.stat().st_size / 1e3:9.0f}K  {p.relative_to(radice)}")

    if a.genera_script:
        righe = ["#!/bin/bash",
                 "# GENERATO DA inventario.py — RILEGGERE PRIMA DI ESEGUIRE.",
                 "# Non cancella nulla: raccoglie i log in log/, sposta il resto in _archivio/.",
                 "set -e", 'mkdir -p log _archivio/spedizioni _archivio/duplicati', ""]
        for p in gruppi.get("LOG", []):
            r = p.relative_to(radice)
            if r.parts[0] == "log":
                continue
            righe.append(f"mv -n {shlex.quote(str(r))} log/ 2>/dev/null || true")
        righe += ["",
                  "# I log restano LEGGIBILI in log/. Per comprimerli, decommentare:",
                  "# tar czf log.tgz log && rm -rf log",
                  ""]
        for p in gruppi.get("ARCHIVIO", []):
            if "_archivio" in str(p):
                continue
            righe.append(f"mv -n {shlex.quote(str(p.relative_to(radice)))} "
                         f"_archivio/spedizioni/ 2>/dev/null || true")
        righe.append("")
        for p in gruppi.get("DUPLICATO", []):
            righe.append(f"mv -n {shlex.quote(str(p.relative_to(radice)))} "
                         f"_archivio/duplicati/ 2>/dev/null || true")
        righe += ["", 'echo "fatto. Log in log/, resto in _archivio/. Nulla cancellato."',
                  'echo "I CSV NON sono toccati: usare censimento_csv.py."']
        a.genera_script.write_text("\n".join(righe) + "\n")
        a.genera_script.chmod(0o755)
        print(f"\nscritto {a.genera_script} — RILEGGERLO prima di eseguirlo.")
        print("Raccoglie i log in log/ e sposta archivi e duplicati in _archivio/.")
        print("I CSV non sono toccati: per quelli serve censimento_csv.py.")

    print("\nNota. La categoria ORFANO e' conservativa: contiene file che nessuno")
    print("script nomina e che il README non cita. Prima di toccarli, cercarli con")
    print("  grep -rl NOME . --include='*.py' --include='*.md' --include='*.sh'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
