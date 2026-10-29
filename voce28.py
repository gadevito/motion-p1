#!/usr/bin/env python3
"""
Voce 28 del registro delle correzioni: nomi di ruolo nelle note sulle correzioni.
===================================================================================
In un solo passo, dalla radice OR3/ (ramo `esecutore/voce28`), con l'interprete dell'ambiente:

    python3 voce28.py --python <interprete con numpy>

1. Sostituzioni letterali (si ferma se il testo non compare esattamente una volta):
   protocol/E6.md r. 265, protocol/E14.md r. 15, evoluzione/analisi/correzione_difetto_23.py r. 76,
   genera_congelamento_e14b.py r. 357: «trovato/a da revisione interna» → «trovato/a durante la stesura del manoscritto».
2. Nota datata nell'intestazione del generatore di E14-B e rigenerazione di CONGELAMENTO_E14B.md
   (nessun numero cambia: il generatore legge gli stessi file).
3. Riga 28 in protocol/REGISTRO_CORREZIONI.md con le impronte prima/dopo di E6.md, E14.md,
   CONGELAMENTO_E14B.md (sha256, 16 esadecimali), calcolate qui.
4. Riga datata in evoluzione/ADDENDUM_PEMS04.md §7 su `distance.csv` (non usato).
"""
import argparse
import hashlib
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent
OGGI = date.today().isoformat()


def imp(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


SOST = [
    ("protocol/E6.md", "Trovato durante la stesura del manoscritto generando la tabella C.8", "Trovato durante la stesura del manoscritto generando la tabella C.8"),
    ("protocol/E14.md", "Trovato durante la stesura del manoscritto leggendo i pesi", "Trovato durante la stesura del manoscritto leggendo i pesi"),
    ("evoluzione/analisi/correzione_difetto_23.py", "Trovato durante la stesura del manoscritto generando la tabella C.8", "Trovato durante la stesura del manoscritto generando la tabella C.8"),
    ("genera_congelamento_e14b.py", "trovata durante la stesura del manoscritto", "trovata durante la stesura del manoscritto"),
    # nota datata nell'intestazione del congelamento di E14-B
    ("genera_congelamento_e14b.py",
     '''    L.append("Letture dichiarate. (1) La configurazione di F′ (`selezione_F_*`, fase 2 della campagna, fuori da "''',
     '''    L.append("Rigenerato il 2026-10-29 (registro, voce 28): nelle note sulle correzioni chi aveva trovato un difetto e' "
             "indicato con il ruolo («durante la stesura del manoscritto»), non con il nome di uno strumento di lavoro; "
             "nessun numero cambia.\\n")
    L.append("Letture dichiarate. (1) La configurazione di F′ (`selezione_F_*`, fase 2 della campagna, fuori da "'''),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", default=sys.executable, help="interprete con l'ambiente del progetto (numpy)")
    a = ap.parse_args()
    reg = R / "protocol" / "REGISTRO_CORREZIONI.md"; add = R / "evoluzione" / "ADDENDUM_PEMS04.md"
    cong = R / "CONGELAMENTO_E14B.md"
    for f, vecchio, nuovo in SOST:
        if (R / f).read_text().count(vecchio) != 1:
            print(f"FERMO: in {f} il testo atteso compare {(R / f).read_text().count(vecchio)} volte:\n{vecchio[:120]}"); return 1
    if "| 28 |" in reg.read_text() or "voce 28" in add.read_text():
        print("FERMO: la voce 28 e' gia' presente"); return 1
    prima = {"protocol/E6.md": imp(R / "protocol/E6.md"), "protocol/E14.md": imp(R / "protocol/E14.md"), "CONGELAMENTO_E14B.md": imp(cong)}
    for f, vecchio, nuovo in SOST:
        p = R / f; p.write_text(p.read_text().replace(vecchio, nuovo)); print(f"  {f}: sostituito")
    r = subprocess.run([a.python, str(R / "genera_congelamento_e14b.py")], cwd=str(R), capture_output=True, text=True)
    print(r.stdout[-400:]);
    if r.returncode != 0:
        print(r.stderr[-1500:]); print("FERMO: il generatore di E14-B e' fallito"); return 1
    if "revisione interna" in cong.read_text():
        print("FERMO: CONGELAMENTO_E14B.md contiene ancora il nome dello strumento"); return 1
    dopo = {"protocol/E6.md": imp(R / "protocol/E6.md"), "protocol/E14.md": imp(R / "protocol/E14.md"), "CONGELAMENTO_E14B.md": imp(cong)}
    # 3. voce 28
    riga = ("| 28 | nelle note sulle correzioni (`protocol/E6.md` r. 265, `protocol/E14.md` r. 15, `genera_congelamento_e14b.py` r. 357, "
            "`evoluzione/analisi/correzione_difetto_23.py` r. 76) chi aveva trovato il difetto era indicato con il nome di uno strumento "
            "di lavoro anziche' con il ruolo | solo documentazione, nessun numero cambia: «trovato durante la stesura del manoscritto» nei "
            "quattro punti; `CONGELAMENTO_E14B.md` rigenerato dallo script con nota datata (" + OGGI + "). Impronte prima → dopo: "
            + "; ".join(f"`{k}` `{prima[k]}` → `{dopo[k]}`" for k in prima) + ". Regola permanente dal " + OGGI + ": nessun riferimento a "
            "strumenti di lavoro in file, commenti, messaggi di commit e note; dove serve, «revisione interna» o «stesura del manoscritto» "
            "| `protocol/REGISTRO_CORREZIONI.md`; `CONGELAMENTO_E14B.md` |")
    t = reg.read_text()
    righe = t.rstrip("\n").split("\n")
    i27 = max(i for i, l in enumerate(righe) if l.startswith("| 27 |"))
    righe.insert(i27 + 1, riga)
    t = "\n".join(righe) + "\n"
    t = t.replace("alla pipeline (voci 1–16, 17a, 19–27)", "alla pipeline (voci 1–16, 17a, 19–27) e alla documentazione (28)", 1)
    reg.write_text(t); print("  protocol/REGISTRO_CORREZIONI.md: voce 28 aggiunta")
    # 4. ADDENDUM_PEMS04 §7: distance.csv
    nota = ("\n**Nota del " + OGGI + "** (seconda revisione esterna, punto su `distance.csv`): la cartella scaricata contiene anche "
            "`data_collection/pems04/distance.csv` (la matrice delle distanze fra sensori dell'artefatto ASTGCN). **Non e' stato usato**: "
            "nessuno script di `evoluzione/` lo legge (`estrai_pems04.py`, `fattibilita_pems04.py`, `provenienza_pems04.py` leggono il solo "
            "`pems04.npz`; la parola «distance» compare in `evoluzione/` solo nel codice di terzi `MoGERNN-main`, non eseguito) e il "
            "predittore e' per nodo, senza grafo. Nessuno SHA-256 da registrare come ingresso.\n")
    ta = add.read_text()
    k = ta.find("## 8. Perimetro")
    if k < 0:
        print("FERMO: §8 non trovato in ADDENDUM_PEMS04.md"); return 1
    add.write_text(ta[:k].rstrip("\n") + "\n" + nota + "\n---\n\n" + ta[k:]); print("  evoluzione/ADDENDUM_PEMS04.md: nota su distance.csv in §7")
    print("  impronte prima:", prima); print("  impronte dopo: ", dopo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
