#!/usr/bin/env python3
"""
Registro dei tempi di E18 (parte A) fuori dal confronto del giro, come per E15.
==================================================================================
Il giro `--solo E18` sulla Spark (29/10, 20261029T111750Z) coincide su tutti i 12 299 numeri; `CONGELAMENTO_E18.md`
differisce solo perche' stampa i tempi misurati della parte A (tabella di §2 e «Totale: … ore-macchina»), che
cambiano a ogni esecuzione. Rimedio, identico a E15 (registri dei tempi sotto `protocol/`):

1. `protocol/e18/tempi_parte_A.json`: copia del blocco `A/tempi` di `results/evoluzione/e18_risultati.json`
   (prima esecuzione, 28/10, invariata da E18-bis), con data, commit e impronta del json d'origine.
2. `genera_congelamento_e18.py` legge i tempi da quel registro (si ferma se manca) e lo dichiara in §2 e in §6;
   i tempi del giro corrente restano in `e18_risultati.json` → `A/tempi` (metadati per `main.py`).
3. Rigenera `CONGELAMENTO_E18.md` e `congelamento_e18.json` (sul Mac: il generatore legge solo json).
4. Riga 29 del registro: aggiunta datata con la nuova impronta.

Sostituzioni letterali: si ferma se un testo atteso non compare esattamente una volta.
Dalla radice OR3/ (ramo esecutore/e18-tempi):  python3 e18_tempi.py --python <interprete>
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent
OGGI = date.today().isoformat()
GEN = R / "genera_congelamento_e18.py"
REG = R / "protocol" / "REGISTRO_CORREZIONI.md"
TEMPI = R / "protocol" / "e18" / "tempi_parte_A.json"
CONG = R / "CONGELAMENTO_E18.md"


def imp(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


SOST = [
    ('''        A = R["A"]; T = A["tempi"]''',
     '''        A = R["A"]
        f_t = Path("protocol/e18/tempi_parte_A.json")
        if not f_t.exists():
            raise SystemExit("FERMO: manca protocol/e18/tempi_parte_A.json (registro dei tempi della parte A)")
        RT = json.loads(f_t.read_text()); T = RT["tempi"]'''),
    ('''        L += ["", f"Totale: {tot_m:.1f} ore-macchina; sotto le 6 h per citta' del protocollo, quindi 4.000 repliche ovunque.", "",''',
     '''        L += ["", f"Totale: {tot_m:.1f} ore-macchina; sotto le 6 h per citta' del protocollo, quindi 4.000 repliche ovunque. "
              f"Tempi dal registro `protocol/e18/tempi_parte_A.json` (prima esecuzione, {RT['data']}, impronta `{imp(f_t)}`), "
              f"come per E15: i tempi dell'esecuzione corrente sono in `e18_risultati.json` → `A/tempi` e non entrano in questo documento.", "",'''),
    ('''          "A, B, D non sono state rieseguite e i loro numeri sono invariati).", ""]''',
     '''          "A, B, D non sono state rieseguite e i loro numeri sono invariati).",
          "- 29/10/2026, tempi: il giro `--solo E18` sulla Spark coincideva su tutti i numeri ma non sul documento, che stampava i "
          "tempi misurati della parte A (diversi a ogni esecuzione). Come per E15, i tempi della prima esecuzione (28/10) sono "
          "copiati nel registro `protocol/e18/tempi_parte_A.json` e il documento li legge da li'; `main.py` tratta `A/tempi` del "
          "json come metadati.", ""]'''),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    t = GEN.read_text()
    for v, _ in SOST:
        if t.count(v) != 1:
            print(f"FERMO: in genera_congelamento_e18.py il testo atteso compare {t.count(v)} volte:\n{v[:120]}"); return 1
    if TEMPI.exists():
        print("FERMO: protocol/e18/tempi_parte_A.json esiste gia'"); return 1
    if "| 29 |" not in REG.read_text():
        print("FERMO: riga 29 assente nel registro"); return 1
    prima = imp(CONG)
    # 1. registro dei tempi
    fj = R / "results" / "evoluzione" / "e18_risultati.json"
    J = json.loads(fj.read_text())
    tempi = J["A"]["tempi"]
    if sorted(tempi) != ["Londra", "Madrid", "Melbourne", "PEMS04", "PEMS08"]:
        print(f"FERMO: gruppi inattesi in A/tempi: {sorted(tempi)}"); return 1
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=R, capture_output=True, text=True).stdout.strip()
    TEMPI.parent.mkdir(parents=True, exist_ok=True)
    TEMPI.write_text(json.dumps({"nota": "Registro dei tempi della parte A di E18 (prima esecuzione sulla Spark, 28/10/2026): copia "
                                         "del blocco A/tempi di e18_risultati.json, letto da genera_congelamento_e18.py al posto dei "
                                         "tempi dell'esecuzione corrente, come per E15. Parete e ore-macchina per gruppo, s per cella.",
                                 "data": "2026-10-28", "copiato_il": OGGI, "commit": commit, "origine": "results/evoluzione/e18_risultati.json",
                                 "impronta_origine": imp(fj), "tempi": tempi}, indent=1, ensure_ascii=False) + "\n")
    print(f"  {TEMPI.relative_to(R)}: scritto (impronta {imp(TEMPI)}); Madrid parete {tempi['Madrid']['parete_s']:.0f} s")
    # 2. generatore
    for v, n in SOST:
        t = t.replace(v, n)
    GEN.write_text(t); print("  genera_congelamento_e18.py: 3 sostituzioni")
    # 3. rigenerazione
    r = subprocess.run([a.python, str(GEN)], cwd=R, capture_output=True, text=True)
    print(r.stdout[-300:])
    if r.returncode != 0:
        print(r.stderr[-1500:]); print("FERMO: il generatore e' fallito"); return 1
    dopo = imp(CONG)
    if "Tempi dal registro" not in CONG.read_text() or "Madrid | 36 | 135 | 20.2 | 4.88 | 466" not in CONG.read_text():
        print("FERMO: il congelamento rigenerato non porta la nota o i tempi del 28/10"); return 1
    # 4. riga 29
    tr = REG.read_text()
    righe = tr.rstrip("\n").split("\n")
    i29 = [i for i, l in enumerate(righe) if l.startswith("| 29 |")]
    if len(i29) != 1:
        print("FERMO: riga 29 non univoca"); return 1
    l = righe[i29[0]]
    k = l.rfind(" | ")
    agg = (f". Rigenerato di nuovo il {OGGI}: i tempi della parte A nel documento vengono dal registro `protocol/e18/tempi_parte_A.json` "
           f"(prima esecuzione, 28/10), come per E15, perche' il giro di rigenerazione coincideva su tutti i numeri ma non sui tempi "
           f"stampati; impronta `CONGELAMENTO_E18.md` `{prima}` → `{dopo}`")
    righe[i29[0]] = l[:k].rstrip() + agg + l[k:]
    REG.write_text("\n".join(righe) + "\n")
    print(f"  registro: riga 29 integrata; CONGELAMENTO_E18.md {prima} → {dopo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
