#!/usr/bin/env python3
"""
Metadati dell'audit di MoGERNN, derivati — per la lettera agli autori e l'Appendice B.
========================================================================================
Nessun valore e' scritto a mano:

    commit esaminato      dall'intestazione di `AUDIT_MoGERNN.md` (espressione regolare)
    data dell'audit       dalla storia git dei file dell'audit (primo e ultimo commit)
    file dell'audit       con impronta sha256 (16 esadecimali)
    repository remoto     se la rete c'e': data del commit esaminato e HEAD attuale del
                          ramo predefinito, dall'API di GitHub; altrimenti «non raggiunto»

Scrive `evoluzione/audit/METADATI_AUDIT.md`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/metadati_audit.py
"""
import hashlib
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
DIR = Path("evoluzione/audit")
FILE = ["AUDIT_MoGERNN.md", "audit_mogernn_runtime.py", "benchmark_mogernn.py", "prova_nas.py",
        "traccia_nas.py", "profila_mogernn.py"]
REPO = "ZJU-TSELab/MoGERNN"


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=RADICE).stdout.strip()


def api(url: str):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "OR3-audit"}), timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:                                   # noqa: BLE001
        return {"errore": f"{type(e).__name__}: {e}"[:120]}


def main() -> int:
    testa = (RADICE / DIR / "AUDIT_MoGERNN.md").read_text()
    m = re.search(r"\*\*Commit esaminato\*\*: `([0-9a-f]{40})`", testa)
    if not m:
        raise SystemExit("commit esaminato non trovato nell'intestazione dell'audit")
    commit = m.group(1)
    presenti = [f for f in FILE if (RADICE / DIR / f).exists()]
    storia = git("log", "--format=%h %ad", "--date=short", "--", *[str(DIR / f) for f in presenti]).splitlines()
    if not storia:
        raise SystemExit("nessun commit per i file dell'audit")
    primo, ultimo = storia[-1].split(), storia[0].split()
    impronte = {f: hashlib.sha256((RADICE / DIR / f).read_bytes()).hexdigest()[:16] for f in presenti}
    remoto = api(f"https://api.github.com/repos/{REPO}/commits/{commit}")
    testa_remota = api(f"https://api.github.com/repos/{REPO}/commits?per_page=1")
    data_commit = remoto.get("commit", {}).get("author", {}).get("date", "non raggiunto")
    head = (testa_remota[0]["sha"] if isinstance(testa_remota, list) and testa_remota else "non raggiunto")
    A = ["# Metadati dell'audit di MoGERNN (derivati)", "",
         f"Generato da `evoluzione/audit/metadati_audit.py` il {datetime.now(timezone.utc).date().isoformat()}, "
         f"commit OR3 `{git('rev-parse', '--short=12', 'HEAD')}`.", "",
         "| voce | valore | fonte |", "|---|---|---|",
         f"| repository | `github.com/{REPO}` | intestazione dell'audit |",
         f"| commit esaminato | `{commit}` | intestazione dell'audit (commento dell'archivio zip; la copia "
         f"`evoluzione/MoGERNN-main` e' senza storia git) |",
         f"| data del commit esaminato | {data_commit} | API GitHub |",
         f"| HEAD attuale del ramo predefinito | `{head}` {'(= commit esaminato)' if head == commit else '(**diverso**: le verifiche vanno rieseguite prima della sottomissione)' if head != 'non raggiunto' else ''} | API GitHub |",
         f"| audit nel repo OR3 | dal {primo[1]} ({primo[0]}) al {ultimo[1]} ({ultimo[0]}), {len(storia)} commit | `git log` dei file dell'audit |",
         f"| articolo | Transportation Research Part C 174 (2025) 105080 | intestazione dell'audit |", "",
         "| file dell'audit | impronta |", "|---|---|"]
    A += [f"| `{DIR / f}` | `{h}` |" for f, h in impronte.items()]
    out = RADICE / DIR / "METADATI_AUDIT.md"
    out.write_text("\n".join(A) + "\n")
    print("\n".join(A[4:12]))
    print(f"\n  scritto {out.relative_to(RADICE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
