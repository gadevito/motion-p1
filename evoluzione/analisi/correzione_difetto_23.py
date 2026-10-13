#!/usr/bin/env python3
"""
Difetto 23 (registro) — correzione datata della tabella «la classe rossa, dichiarata prima».
=============================================================================================
La tabella firmata in `protocol/E6.md` fu derivata da `frequenze_classi.py` che leggeva
`pesi/` (campagna precedente) per le citta'; gli esecutori leggono `pesi_griglia/`. Questo
script legge il `frequenze_classi.json` rigenerato dagli artefatti usati e AGGIUNGE in coda a
`protocol/E6.md` una sezione datata con la tabella corretta, le impronte degli artefatti e
l'elenco dei numeri che cambiano rispetto alla tabella firmata (che resta al suo posto, come
prescrive il protocollo: correzione datata, non riscrittura). Idempotente: se la sezione con
la stessa impronta del json esiste gia', non fa nulla.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/correzione_difetto_23.py
"""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

GRUPPI = (("Londra", "pesi_griglia/Londra/"), ("Madrid", "pesi_griglia/Madrid/"), ("Melbourne", "pesi_griglia/Melbourne/"),
          ("PEMS04", "pesi_pems04/"), ("PEMS08", "pesi_pems08/"))
# la tabella firmata (protocol/E6.md, «La classe rossa, dichiarata prima»), trascritta per il confronto
FIRMATA = {"Londra": ("43,6–45,0", "39,8–40,7", "15,2–15,7", "2,1–2,2"),
           "Madrid": ("45,6–46,8", "44,0–45,1", "9,0–9,4", "3,5–3,7"),
           "Melbourne": ("74,1–75,3", "20,1–21,0", "4,6–4,9", "6,8–7,3"),
           "PEMS04": ("90,6–91,8", "6,0–6,9", "2,3–2,6", "13,0–14,6"),
           "PEMS08": ("93,4–94,2", "4,4–5,2", "0,9–1,4", "23,8–37,2")}


def _it(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",")


def _intervallo(v, dec=1):
    lo, hi = min(v), max(v)
    return _it(lo, dec) if _it(lo, dec) == _it(hi, dec) else f"{_it(lo, dec)}–{_it(hi, dec)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--protocollo", type=Path, default=Path("protocol/E6.md"))
    a = ap.parse_args()
    fj = a.out / "frequenze_classi.json"
    J = json.loads(fj.read_text())
    imp_json = hashlib.sha256(fj.read_bytes()).hexdigest()[:16]
    if set(J["_cartelle"]) != {"pesi_griglia", "pesi_pems04", "pesi_pems08"}:
        raise SystemExit(f"{fj} non viene dalla versione corretta di frequenze_classi.py: cartelle {J['_cartelle']}")
    testo = a.protocollo.read_text()
    marca = f"impronta `{imp_json}`"
    if marca in testo:
        print(f"  {a.protocollo}: correzione gia' presente ({marca})"); return 0
    righe, cambi = [], []
    for nome, pref in GRUPPI:
        kk = sorted(k for k in J if k.startswith(pref))
        fr = [J[k]["frequenze"] for k in kk]; pr = [J[k]["pesi"][2] for k in kk]
        col = (_intervallo([100 * f[0] for f in fr]), _intervallo([100 * f[1] for f in fr]),
               _intervallo([100 * f[2] for f in fr]), _intervallo(pr, 2))
        et = f"{nome} (p0–p{len(kk) - 1})" if len(kk) > 3 or nome == "Londra" else nome
        righe.append(f"| {et} | {col[0]} % | {col[1]} % | {col[2]} % | {col[3]} |")
        vecchia = FIRMATA[nome]
        for i, (c_, v_) in enumerate(zip(col, vecchia)):
            # il peso firmato ha una cifra: si confronta a una cifra
            cn = c_ if i < 3 else _intervallo(pr, 1)
            if cn != v_:
                cambi.append(f"{nome}, {('scorrevole', 'moderato', 'congestionato', 'peso della rossa')[i]}: {v_} → {cn}")
    p8 = [J[k]["pesi"][2] for k in sorted(k for k in J if k.startswith("pesi_pems08/"))]
    oggi = date.today().isoformat()
    S = [f"\n## Correzione {oggi} — difetto 23 (provenienza degli artefatti dei pesi)\n",
         "La tabella «la classe rossa, dichiarata prima» (sopra) fu derivata da `frequenze_classi.py` "
         "che per le citta' leggeva `pesi/` (campagna precedente) e per PEMS08 le sole p0–p2; gli "
         "esecutori leggono `pesi_griglia/` (citta'), `pesi_pems04/` e `pesi_pems08/` p0–p5 "
         "(`evoluzione.analisi.pesi.carica`). Trovato durante la stesura del manoscritto generando la tabella C.8 dagli "
         "artefatti usati. **Nessun effetto sui risultati**: ogni addestramento ha usato i propri pesi. "
         "Qui la tabella rigenerata dagli artefatti usati (`frequenze_classi.py` corretto, "
         f"`results/evoluzione/frequenze_classi.json` impronta `{imp_json}`); la tabella firmata resta "
         "sopra, come prescritto (correzione datata, non riscrittura).\n",
         "| contesto | scorrevole | moderato | congestionato | peso della rossa |", "|---|---|---|---|---|",
         *righe, "",
         "Pesi della rossa su PEMS08, sei partizioni: " + " / ".join(_it(x, 1) for x in p8) + ".",
         "Impronte delle cartelle (sha256 delle impronte dei file, in ordine): "
         + ", ".join(f"`{c}` `{v}`" for c, v in J["_impronte_cartelle"].items()) + ".",
         "", "Numeri che cambiano rispetto alla tabella firmata: "
         + ("; ".join(cambi) + "." if cambi else "nessuno."), ""]
    a.protocollo.write_text(testo.rstrip("\n") + "\n" + "\n".join(S))
    print("\n".join(S))
    print(f"  aggiunto a {a.protocollo}; {len(cambi)} estremi cambiati")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
