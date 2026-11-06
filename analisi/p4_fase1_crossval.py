#!/usr/bin/env python3
"""
Paper 4, fase 1, punto 2 (richiesta del revisore, 6/11/2026): le tre esecuzioni di `data_collection/t4c_crossval.py`
di `README.it.md` §7.11 (base, `--exclude-empty`, `--max-dist 30`), con le uscite a video conservate, le impronte dei
tre CSV e degli ingressi, e il confronto con le Tabelle 64-65 del deliverable UC-04 v1 (pag. 127-128). Tabella 66
(rapporti) non rigenerata, come richiesto. Nessun modello. Scrive in `protocol/paper4/fase1/crossval/` i tre CSV e i
tre log, e `protocol/paper4/fase1/CROSSVAL_rigenerato.md`.

    poetry run python analisi/p4_fase1_crossval.py --or3 ../OR3
"""
import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
VARIANTI = (("base", [], "crossval_results.csv"),
            ("noempty", ["--exclude-empty"], "crossval_results_noempty.csv"),
            ("d30", ["--max-dist", "30"], "crossval_results_d30.csv"))
# Tabelle 64-65 del deliverable (pag. 127-128) e sensibilita' nel testo (pag. 127): trascrizione.
DELIV = [
    ("64", "coppie con correlazione definibile", "base", r"coppie valide:\s*(\d+)", "399"),
    ("64", "correlazione istantanea, mediana", "base", r"correlazione r:\s*mediana\s*([-+]?\d*\.\d+)", "0.04 (testo: 0.0405)"),
    ("64", "correlazione del profilo settimanale medio, mediana", "base", r"profilo settimanale medio[^:]*:\s*(?:mediana\s*)?([-+]?\d*\.\d+)", "0.13"),
    ("64", "concordanza di classe (3 classi)", "base", r"concordanza di classe[^:]*:\s*([\d.]+%)", "44%"),
    ("64", "richiamo giallo+rosso", "base", r"recall della congestione ricostruita[^:]*:\s*([\d.]+%)", "16,7%"),
    ("64", "distribuzione classi, ricostruito (spire)", "base", r"ricostruito \(spire\)[^=]*=\s*([^\n]+)", "85% / 11% / 3%"),
    ("64", "distribuzione classi, misurato (sonde)", "base", r"misurato\s+\(sonde\)[^=]*=\s*([^\n]+)", "43% / 44% / 13%"),
    ("testo p. 127", "raggio 30 m: mediana e coppie", "d30", r"coppie valide:\s*(\d+)\s*\|\s*correlazione r:\s*mediana\s*([-+]?\d*\.\d+)", "0,0452 su 181 coppie"),
    ("65", "r ricostruito, insieme completo", "base", r"^\s*(?:r[_ ]?ricostr\S*|ricostruito|r)\s+scost\. ottimo[^|]*\|\s*([^\n]+)$", "+0,0397"),
    ("65", "occupazione grezza, insieme completo", "base", r"^\s*occup\S*\s+scost\. ottimo[^|]*\|\s*([^\n]+)$", "-0,1252"),
    ("65", "flusso grezzo, insieme completo", "base", r"^\s*fluss\S*\s+scost\. ottimo[^|]*\|\s*([^\n]+)$", "-0,1410"),
    ("65", "r ricostruito, sole celle trafficate", "noempty", r"^\s*(?:r[_ ]?ricostr\S*|ricostruito|r)\s+scost\. ottimo[^|]*\|\s*([^\n]+)$", "+0,0157 (276 coppie)"),
    ("65", "occupazione grezza, sole celle trafficate", "noempty", r"^\s*occup\S*\s+scost\. ottimo[^|]*\|\s*([^\n]+)$", "-0,0689"),
    ("65", "flusso grezzo, sole celle trafficate", "noempty", r"^\s*fluss\S*\s+scost\. ottimo[^|]*\|\s*([^\n]+)$", "-0,0712"),
]


def _sha(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def _sha_dir(d: Path):
    h, n = hashlib.sha256(), 0
    for f in sorted(p for p in d.rglob("*") if p.is_file()):
        h.update(f"{f.relative_to(d)}:{f.stat().st_size}:".encode()); h.update(hashlib.sha256(f.read_bytes()).digest()); n += 1
    return h.hexdigest()[:16], n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--or3", type=Path, required=True, help="radice di OR3 (con data_collection/)")
    ap.add_argument("--dest", type=Path, default=RADICE / "protocol" / "paper4" / "fase1")
    a = ap.parse_args()
    dc = (a.or3 / "data_collection").resolve()
    t4 = Path("traffic4cast/MADRID_2022")
    ARG = ["--gomo-targets", "go-mo/gomo/targets_2021_urb_d8.npz", "--gomo-sensors", "go-mo/gomo/traffic_sensors.csv",
           "--t4c-nodes", str(t4 / "road_graph_nodes_osm.parquet"), "--t4c-edges", str(t4 / "road_graph_edges_district.parquet"),
           "--speed-dir", str(t4 / "speed_classes/madrid")]
    for p in ARG[1::2]:
        if not (dc / p).exists():
            print(f"FERMO: ingresso mancante {dc / p}"); return 1
    out = a.dest / "crossval"; out.mkdir(parents=True, exist_ok=True)
    log, imp = {}, {}
    for nome, extra, csv in VARIANTI:
        cmd = [sys.executable, "t4c_crossval.py", *extra, *ARG, "--out", str(out / csv)]
        print(f"[{nome}] {' '.join(cmd[1:])}", flush=True)
        r = subprocess.run(cmd, cwd=dc, capture_output=True, text=True)
        (out / f"log_{nome}.txt").write_text("$ " + " ".join(cmd[1:]) + "\n" + r.stdout + ("\n[stderr]\n" + r.stderr if r.stderr.strip() else "") + f"\n[codice di uscita {r.returncode}]\n")
        if r.returncode != 0 or not (out / csv).exists():
            print(f"FERMO: {nome} fallita (codice {r.returncode}); vedi {out / f'log_{nome}.txt'}"); print(r.stderr[-2000:]); return 1
        log[nome] = r.stdout
        imp[csv] = (_sha(out / csv), sum(1 for _ in open(out / csv)) - 1)
        print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "", flush=True)
    ingressi = {p: _sha(dc / p) for p in ARG[1::2] if (dc / p).is_file()}
    sd, n = _sha_dir(dc / t4 / "speed_classes/madrid"); ingressi[str(t4 / "speed_classes/madrid") + f"/ ({n} file)"] = sd
    ingressi["t4c_crossval.py"] = _sha(dc / "t4c_crossval.py")
    L = ["# Paper 4, fase 1 — validazione co-localizzata (`t4c_crossval.py`) rigenerata: base, `--exclude-empty`, `--max-dist 30`", "",
         f"Generato da `analisi/p4_fase1_crossval.py` il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} (non modificare a mano). "
         f"Comandi di `README.it.md` §7.11 eseguiti in `{dc}`; CSV e uscite a video in `protocol/paper4/fase1/crossval/`. "
         "Confronto con le Tabelle 64-65 del deliverable UC-04 v1 (pag. 127-128) e con la sensibilita' al raggio (testo, pag. 127). "
         "Tabella 66 (rapporti fra correlazioni) non rigenerata: nessuno script la calcola. **Solo registro.**", "",
         "## CSV rigenerati", "", "| file | righe (coppie) | sha256 |", "|---|---:|---|"]
    L += [f"| `{k}` | {v[1]} | `{v[0]}` |" for k, v in imp.items()]
    base_prev = a.or3 / "data_collection" / "crossval_results.csv"
    if base_prev.exists():
        L += ["", f"`crossval_results.csv` gia' presente in `OR3/data_collection/` (sha256 `{_sha(base_prev)}`, "
              f"{sum(1 for _ in open(base_prev)) - 1} coppie): " + ("**identico** al rigenerato" if _sha(base_prev) == imp['crossval_results.csv'][0] else "**diverso** dal rigenerato") + "."]
    L += ["", "## Confronto con il deliverable", "", "| tabella | grandezza | variante | rigenerato (dall'uscita a video) | deliverable |", "|---|---|---|---|---|"]
    for tab, gr, var, rx, dev in DELIV:
        m = re.search(rx, log[var], flags=re.M | re.I)
        val = " | ".join(g.strip() for g in m.groups()) if m else "non estratto (vedi uscita integrale)"
        L.append(f"| {tab} | {gr} | {var} | {val} | {dev} |")
    L += ["", "Nota: l'uscita a video e' l'unico posto in cui lo script stampa gli indicatori (il CSV contiene solo le coppie "
          "`gomo_sensor, t4c_segment, dist_m, corr`); i valori «non estratti» vanno letti nelle uscite integrali qui sotto.", ""]
    for nome, _, _ in VARIANTI:
        L += [f"## Uscita integrale — {nome}", "", "```", log[nome].rstrip(), "```", ""]
    L += ["## Ingressi (impronte sha256, 16 esadecimali)", ""] + [f"- `{k}` `{v}`" for k, v in ingressi.items()]
    L += ["", f"Script: `analisi/p4_fase1_crossval.py` `{_sha(Path(__file__))}`.", ""]
    md = a.dest / "CROSSVAL_rigenerato.md"; md.write_text("\n".join(L))
    print(f"  -> {md} ({_sha(md)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
