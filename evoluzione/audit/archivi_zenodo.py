#!/usr/bin/env python3
"""
Archivi tar del record Zenodo dai tre gruppi di `protocol/zenodo/MANIFEST.txt`.
=================================================================================
Tre archivi non compressi (i file sono gia' compatti), con percorsi relativi alla radice di OR3
(`results/evoluzione/...`), cosi' che `analysis/main.py` li legga dopo `tar -xf <archivio> -C <radice OR3>`:

    zenodo_rigenerazione.tar          gruppo «rigenerazione»
    zenodo_probabilita.tar            gruppo «probabilita»
    zenodo_punti_di_controllo.tar     gruppo «punti»

I membri sono aggiunti in ordine di percorso. Per ciascun archivio: byte, SHA-256, numero di file, e la verifica
che l'elenco dei membri coincida con il manifesto (0 mancanti, 0 in piu') e che le dimensioni coincidano.
Scrive `ARCHIVI.md` (predefinito `protocol/zenodo/ARCHIVI.md` sotto la radice). Si ferma, con codice 1, se una
verifica fallisce o se un file del manifesto manca sul disco.

    python3 archivi_zenodo.py --radice ~/OR3 --manifesto ~/zenodo_k/MANIFEST.txt --dest ~/zenodo_k
"""
import argparse
import hashlib
import platform
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ARCHIVI = {"rigenerazione": "zenodo_rigenerazione.tar", "probabilita": "zenodo_probabilita.tar", "punti": "zenodo_punti_di_controllo.tar"}
PREFISSO = "results/evoluzione"


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def leggi_manifesto(p: Path):
    voci, testa = {}, {}
    for riga in p.read_text().splitlines():
        if riga.startswith("#"):
            if riga.startswith("# tag:"):
                for pezzo in riga[2:].split("  "):
                    k, _, v = pezzo.partition(": ")
                    testa[k.strip()] = v.strip()
            continue
        if not riga.strip():
            continue
        sha, byte, gruppo, percorso = riga.split("  ", 3)
        voci.setdefault(gruppo, {})[percorso] = (sha, int(byte))
    return voci, testa


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radice", type=Path, required=True, help="radice di OR3 (contiene results/evoluzione)")
    ap.add_argument("--manifesto", type=Path, required=True)
    ap.add_argument("--dest", type=Path, required=True, help="cartella degli archivi, fuori dal repo")
    ap.add_argument("--md", type=Path, default=None, help="predefinito <radice>/protocol/zenodo/ARCHIVI.md")
    a = ap.parse_args()
    md = a.md or (a.radice / "protocol" / "zenodo" / "ARCHIVI.md")
    voci, testa = leggi_manifesto(a.manifesto)
    if set(voci) != set(ARCHIVI):
        print(f"FERMO: gruppi nel manifesto {sorted(voci)} diversi da {sorted(ARCHIVI)}"); return 1
    a.dest.mkdir(parents=True, exist_ok=True)
    base = a.radice / PREFISSO
    righe, errori = [], []
    for gruppo, nome in ARCHIVI.items():
        attesi = voci[gruppo]
        mancanti_disco = [p for p in attesi if not (base / p).is_file()]
        if mancanti_disco:
            print(f"FERMO: {len(mancanti_disco)} file del gruppo {gruppo} mancano sul disco, p.es. {mancanti_disco[:3]}"); return 1
        out = a.dest / nome
        print(f"  {nome}: {len(attesi):,} file...", flush=True)
        with tarfile.open(out, "w", format=tarfile.PAX_FORMAT) as tar:
            for p in sorted(attesi):
                tar.add(base / p, arcname=f"{PREFISSO}/{p}", recursive=False)
        # verifica: membri (nome e dimensione) contro il manifesto
        with tarfile.open(out, "r") as tar:
            membri = {m.name[len(PREFISSO) + 1:]: m.size for m in tar.getmembers() if m.isfile()}
        mancanti = sorted(set(attesi) - set(membri)); in_piu = sorted(set(membri) - set(attesi))
        dim_diverse = sorted(p for p in attesi if p in membri and membri[p] != attesi[p][1])
        byte = out.stat().st_size; sha = sha_file(out)
        if mancanti or in_piu or dim_diverse:
            errori.append(f"{nome}: mancanti {len(mancanti)}, in piu' {len(in_piu)}, dimensioni diverse {len(dim_diverse)}")
        righe.append((nome, gruppo, byte, sha, len(membri), len(mancanti), len(in_piu), len(dim_diverse)))
        print(f"    {byte:,} byte, sha256 {sha}, {len(membri):,} membri; mancanti {len(mancanti)}, in piu' {len(in_piu)}, "
              f"dimensioni diverse {len(dim_diverse)}", flush=True)
    tot_b = sum(r[2] for r in righe); tot_n = sum(r[4] for r in righe)
    L = ["# Archivi del record Zenodo", "",
         f"Generati da `evoluzione/audit/archivi_zenodo.py` il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} su "
         f"`{platform.node()}`, dal manifesto `protocol/zenodo/MANIFEST.txt` (tag `{testa.get('tag', '?')}`, commit "
         f"`{testa.get('commit', '?')}`, sha256 del manifesto `{sha_file(a.manifesto)[:16]}`). Tre archivi tar **non compressi**, "
         "membri in ordine di percorso, percorsi relativi alla radice di OR3 (`results/evoluzione/...`): si estraggono nella "
         "radice con `tar -xf <archivio> -C <radice OR3>` e `analysis/main.py` li legge dove li attende.", "",
         "| archivio | gruppo | byte | SHA-256 | file | mancanti rispetto al manifesto | in piu' | dimensioni diverse |",
         "|---|---|---:|---|---:|---:|---:|---:|"]
    for nome, gruppo, byte, sha, n, mm, ip, dd in righe:
        L.append(f"| `{nome}` | {gruppo} | {byte:,} | `{sha}` | {n:,} | {mm} | {ip} | {dd} |")
    L += [f"| **totale** | | **{tot_b:,}** ({tot_b / 2**30:.2f} GiB) | | **{tot_n:,}** | | | |", "",
          "Verifica: l'elenco dei membri di ciascun archivio (nome e dimensione) coincide con le righe del gruppo nel manifesto"
          + (" — **superata** per i tre archivi." if not errori else " — **FALLITA**: " + "; ".join(errori) + "."),
          "", "Controllo dopo la copia: `shasum -a 256 zenodo_*.tar` deve dare gli SHA-256 della tabella."]
    md.parent.mkdir(parents=True, exist_ok=True); md.write_text("\n".join(L) + "\n")
    print(f"  -> {md}")
    if errori:
        print("FERMO: " + "; ".join(errori)); return 1
    print(f"  tre archivi: {tot_n:,} file, {tot_b:,} byte; verifica contro il manifesto superata")
    return 0


if __name__ == "__main__":
    sys.exit(main())
