#!/usr/bin/env python3
"""
Patch per il difetto 19 — il conteggio delle riviste di E3 contava anche le rimisure.
=======================================================================================
`analizza_e3.riviste()` prendeva dal registro ogni esecuzione completata con etichetta
`inserimento_griglia/<braccio>`, comprese le 9 rimisure isolate di R-orig e R-mon del
2026-10-02 fatte per la tabella dei costi (117 esecuzioni invece di 108). Tre sostituzioni
letterali (se un testo atteso non c'e' una volta sola, si ferma senza toccare nulla):

  1. `esegui_inserimento.py`: una rimisura si registra come `<etichetta>/<braccio>/rimisura`;
  2. `analizza_e3.py`: il lancio di E3 e' definito dai 108 manifesti per braccio di
     `inserimento_griglia/`, elencati per impronta; di ogni cella si tiene la sola esecuzione
     del registro che ha prodotto la wCE registrata (per una cella rimisurata, la concorrente);
     108 per braccio, altrimenti si ferma;
  3. `genera_congelamento_e3.py`: dichiarazione corretta, datata.

Uso (dalla radice OR3/):

    poetry run python patch_e3_riviste.py
"""
from pathlib import Path

SOSTITUZIONI = {
    "evoluzione/esperimenti/esegui_inserimento.py": [(
        '''    reg = Registro.avvia(f"{et}/{b}",
                         note=f"{c} p{p} seme {s} braccio {b} [{modalita}]",
''',
        '''    # una RIMISURA ha un'etichetta propria nel registro: non e' un'esecuzione del
    # lancio e non entra nei conteggi (difetto 19)
    reg = Registro.avvia(f"{et}/{b}" + ("/rimisura" if precedente is not None else ""),
                         note=f"{c} p{p} seme {s} braccio {b} [{modalita}]",
''')],
    "evoluzione/analisi/analizza_e3.py": [(
        '''import argparse
import json
import sys
from pathlib import Path
''',
        '''import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
'''), (
        '''def riviste(radice: Path) -> dict:
    """Riviste per origine, iniziali contro nuovi, per R, R-orig, R-mon: dai
    manifesti completati del registro. Mediana sulle esecuzioni."""
    per_b = {b: [] for b in ("R", "R-orig", "R-mon")}
    for f in sorted((radice / "registro").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        exp = d.get("esperimento", "")
        if not exp.startswith("inserimento_griglia/") or \\
                d.get("run_status") != "completato":
            continue
        b = exp.split("/", 1)[1]
        if b not in per_b:
            continue
''',
        '''BRACCI_RIVISTE = ("R", "R-orig", "R-mon")
CELLE_PER_BRACCIO = 108                       # 3 citta' x 6 partizioni x 6 semi
_NOTA = re.compile(r"^(?P<c>\\S+) p(?P<p>\\d+) seme (?P<s>\\d+) braccio (?P<b>\\S+) \\[(?P<m>\\w+)\\]$")


def lancio_e3(radice: Path, bracci=BRACCI_RIVISTE) -> dict:
    """Le celle del lancio di E3, dai manifesti per cella di `inserimento_griglia/`,
    **elencate per impronta**, con la modalita' dell'esecuzione che ha prodotto la wCE
    registrata: una cella rimisurata in isolamento (`rimisura_di`) appartiene al lancio
    con la sua esecuzione concorrente; la rimisura non conta (difetto 19)."""
    celle = {}
    for b in bracci:
        n = 0
        for f in sorted((radice / "inserimento_griglia").glob(f"{b}_*_p*_s*.json")):
            d = json.loads(f.read_text())
            if d.get("braccio") != b:
                continue
            mod = d.get("modalita_misura", "concorrente")
            if "rimisura_di" in d:
                mod = d["rimisura_di"].get("modalita") or "concorrente"
            celle[(b, str(d["contesto"]), int(d["partizione"]), int(d["seme"]))] = {
                "file": f.name, "impronta": hashlib.sha256(f.read_bytes()).hexdigest()[:16],
                "modalita": mod}
            n += 1
        if n != CELLE_PER_BRACCIO:
            raise RuntimeError(f"lancio E3, braccio {b}: {n} manifesti di cella, attesi {CELLE_PER_BRACCIO}")
    return celle


def riviste(radice: Path) -> dict:
    """Riviste per origine, iniziali contro nuovi, per R, R-orig, R-mon: dai
    manifesti completati del registro **del solo lancio di E3** (`lancio_e3`).
    Mediana sulle esecuzioni; esattamente 108 per braccio."""
    celle = lancio_e3(radice)
    per_b = {b: [] for b in BRACCI_RIVISTE}
    viste = set()
    for f in sorted((radice / "registro").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        exp = d.get("esperimento", "")
        if not exp.startswith("inserimento_griglia/") or \\
                d.get("run_status") != "completato":
            continue
        b = exp.split("/", 1)[1]
        if b not in per_b:
            continue
        m = _NOTA.match(d.get("note", ""))
        if not m:
            continue
        chiave = (b, m["c"], int(m["p"]), int(m["s"]))
        if chiave not in celle or celle[chiave]["modalita"] != m["m"] or chiave in viste:
            continue                                   # rimisura, o cella fuori lancio
        viste.add(chiave)
''' ), (
        '''    fuori = {}
    for b, v in per_b.items():
        if not v:
            fuori[b] = {"esecuzioni": 0}
            continue
        fuori[b] = {"esecuzioni": len(v)}
''',
        '''    fuori = {}
    for b, v in per_b.items():
        if len(v) != CELLE_PER_BRACCIO:
            raise RuntimeError(f"riviste, braccio {b}: {len(v)} esecuzioni del lancio nel registro, "
                               f"attese {CELLE_PER_BRACCIO}")
        fuori[b] = {"esecuzioni": len(v),
                    "lancio": {f"{k[1]}_p{k[2]}_s{k[3]}": z for k, z in sorted(celle.items()) if k[0] == b}}
''')],
    "genera_congelamento_e3.py": [(
        '''    a("- I 117 manifesti di R nel registro comprendono le 9 misure isolate della fase 3; "
      "il conteggio delle riviste le include (stessa numerica).")
''',
        '''    a("- **Correzione del 2026-10-10 (difetto 19 del registro)**: il conteggio delle riviste "
      "prendeva dal registro ogni esecuzione completata di R, R-orig e R-mon, comprese le 9 "
      "rimisure isolate di R-orig e R-mon fatte per la tabella dei costi (117 invece di 108). "
      "Ora il lancio di E3 e' definito dai 108 manifesti per braccio di `inserimento_griglia/`, "
      "elencati per impronta in `analisi_e3.json` (`riviste/<braccio>/lancio`), e di ogni cella "
      "conta la sola esecuzione che ha prodotto la wCE registrata; le rimisure future hanno "
      "etichetta propria nel registro (`…/rimisura`). Documento rigenerato, non modificato a mano.")
''')],
}

for f, subs in SOSTITUZIONI.items():
    p = Path(f); s = p.read_text()
    for vecchio, nuovo in subs:
        n = s.count(vecchio)
        assert n == 1, f"{f}: testo atteso trovato {n} volte, non 1:\\n{vecchio[:100]}"
        s = s.replace(vecchio, nuovo)
    compile(s, f, "exec")
    p.write_text(s)
    print(f"  {f}: {len(subs)} sostituzioni, compila")
