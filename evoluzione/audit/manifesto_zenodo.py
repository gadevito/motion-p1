#!/usr/bin/env python3
"""
Manifesto del record Zenodo: elenco dei file di `results/evoluzione/` che entrano nel deposito, con SHA-256 e
dimensione in byte.
===================================================================================================================
Il record comprende i gruppi «rigenerazione» (cio' che `analysis/main.py` legge), «probabilita» (E16 ed E18
PEMS04) e «punti» (punti di controllo e stati dei modelli), secondo la stessa regola di
`ripartizione_results.py` (`gruppo`); «altro» resta fuori. Da produrre al tag `k`, sulla macchina con `results/`
completo (la Spark).

Scrive `protocol/zenodo/MANIFEST.txt`:
    # intestazione (tag, commit, data, macchina, gruppi, totali)
    <sha256>  <byte>  <gruppo>  <percorso relativo a results/evoluzione/>
    ...
    # totali per gruppo e impronta dell'elenco (sha256 delle righe dei file)

Dalla radice OR3/, con l'albero al tag:
    python3 evoluzione/audit/manifesto_zenodo.py --tag paper1-freeze-<data>k [--lavoratori 8]
Si ferma se HEAD non e' il commit del tag o se l'albero ha modifiche tracciate.
"""
import argparse
import hashlib
import platform
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ripartizione_results import gruppo  # noqa: E402

INCLUSI = ("rigenerazione", "probabilita", "punti")


def sha_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


def git(*args, radice: Path) -> str:
    return subprocess.run(["git", *args], cwd=radice, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--md", type=Path, default=Path("protocol/zenodo/MANIFEST.txt"))
    ap.add_argument("--lavoratori", type=int, default=8)
    a = ap.parse_args()
    radice = Path(__file__).resolve().parents[2]
    testa = git("rev-parse", "HEAD", radice=radice)
    try:
        commit_tag = git("rev-parse", f"{a.tag}^{{commit}}", radice=radice)
    except subprocess.CalledProcessError:
        print(f"FERMO: il tag {a.tag} non esiste"); return 1
    if commit_tag != testa:
        print(f"FERMO: HEAD {testa[:7]} non e' il commit del tag {a.tag} ({commit_tag[:7]})"); return 1
    sporco = [l for l in git("status", "--porcelain", radice=radice).splitlines() if not l.startswith("??")]
    if sporco:
        print("FERMO: l'albero ha modifiche tracciate:\n  " + "\n  ".join(sporco[:10])); return 1
    voci = []
    for p in sorted(a.out.iterdir()):
        g = gruppo(p)
        if g not in INCLUSI:
            continue
        files = [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.is_file())
        voci += [(g, f) for f in files]
    print(f"  {len(voci)} file in {len(INCLUSI)} gruppi; sha256 con {a.lavoratori} lavoratori...", flush=True)
    with ProcessPoolExecutor(a.lavoratori) as ex:
        shas = list(ex.map(sha_file, [str(f) for _, f in voci], chunksize=16))
    righe, tot = [], {g: [0, 0] for g in INCLUSI}
    for (g, f), h in zip(voci, shas):
        b = f.stat().st_size
        righe.append(f"{h}  {b}  {g}  {f.relative_to(a.out).as_posix()}")
        tot[g][0] += b; tot[g][1] += 1
    corpo = "\n".join(righe) + "\n"
    imp_elenco = hashlib.sha256(corpo.encode()).hexdigest()
    tb, tn = sum(v[0] for v in tot.values()), sum(v[1] for v in tot.values())
    L = ["# MANIFEST del record Zenodo — OR3, results/evoluzione/",
         f"# tag: {a.tag}  commit: {testa}  generato: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  macchina: {platform.node()}",
         "# gruppi inclusi: " + ", ".join(INCLUSI) + " (regola di evoluzione/audit/ripartizione_results.py); escluso: altro",
         "# formato: sha256  byte  gruppo  percorso (relativo a results/evoluzione/)",
         *(f"# {g}: {tot[g][1]:,} file, {tot[g][0]:,} byte ({tot[g][0] / 2**30:.2f} GiB)" for g in INCLUSI),
         f"# totale: {tn:,} file, {tb:,} byte ({tb / 2**30:.2f} GiB)",
         f"# sha256 dell'elenco (solo le righe dei file): {imp_elenco}",
         corpo.rstrip("\n")]
    a.md.parent.mkdir(parents=True, exist_ok=True)
    a.md.write_text("\n".join(L) + "\n")
    print("\n".join(L[:8])); print(f"  -> {a.md} (sha256 {hashlib.sha256(a.md.read_bytes()).hexdigest()[:16]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
