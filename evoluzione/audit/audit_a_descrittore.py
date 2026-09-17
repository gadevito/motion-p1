#!/usr/bin/env python3
"""
Audit A — il descrittore e' lo stesso nei due esperimenti?
==========================================================
Nessuna esecuzione: ispeziona il codice.

PERCHE' E' IL PRIMO CONTROLLO. Il paper sostiene una catena diretta —
rappresentazione proposta, componente software, inserimento, espansioni
successive. Se il descrittore che sostituisce gli embedding nel compito denso
non e' il medesimo oggetto usato per l'inserimento dei sensori, quella catena
non esiste e ogni esperimento successivo misurerebbe due cose diverse.

CHE COSA CONFRONTA.

  * la SORGENTE di ciascuna componente: osservazioni del sensore, anagrafica
    statica, grafo, calendario;
  * il PERIODO su cui e' calcolata, che decide la causalita';
  * la TRASFORMAZIONE applicata prima di entrare nel modello, appresa o fissa;
  * la DIMENSIONE, che decide se il confronto con l'embedding sia a parita' di
    capacita'.

Due descrittori che usino sorgenti diverse non sono lo stesso oggetto anche se
producono vettori della stessa lunghezza. L'anagrafica statica, in particolare,
non e' disponibile per un sensore appena installato allo stesso titolo delle sue
osservazioni: e' nota prima, e usarla nell'inserimento senza dichiararlo
confonde cio' che si sa per progetto con cio' che si osserva.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/audit_a_descrittore.py
"""
import argparse
import re
from pathlib import Path

# quel che si cerca nei sorgenti, con l'etichetta della sorgente corrispondente
SORGENTI = {
    "osservazioni del sensore": [
        r"\br_emp\b", r"\bnanmean\b", r"\bnanquantile\b", r"\bcorrcoef\b",
        r"\bnp\.diff\(", r"autocorr", r"\bprof\b",
    ],
    "anagrafica statica": [
        r"\blanes\b", r"max_speed", r"max_capacity", r"\bcapacity\b",
        r"road[_ ]type", r"element_type",
    ],
    "grafo": [r"\bdegree\b", r"betwe", r"\badj\b", r"neighbou?r", r"routes-graph"],
    "calendario": [r"day_of_week", r"\bdow\b", r"\bhour\b", r"\bslot\b", r"momento"],
    "identita' appresa": [
        r"nn\.Parameter", r"\bemb\b\s*=", r"\bE1\b", r"\bE2\b", r"Embedding\(",
    ],
}
# opzioni che dichiarano come il descrittore entra nel modello
OPZIONI = [r"--node-desc", r"--desc-proj", r"--desc-hidden", r"--emb\b",
           r"--history", r"--hist-", r"--onboard"]


def sezione(testo, chiave, prima=40, dopo=40):
    """Le righe attorno alla prima occorrenza della chiave."""
    righe = testo.split("\n")
    for i, r in enumerate(righe):
        if re.search(chiave, r):
            return "\n".join(righe[max(0, i - prima):i + dopo])
    return ""


def esamina(p: Path):
    if not p.exists():
        return None
    t = p.read_text(errors="ignore")
    fuori = {"righe": len(t.split("\n")), "sorgenti": {}, "opzioni": [], "npy": []}
    for nome, pat in SORGENTI.items():
        n = sum(len(re.findall(x, t)) for x in pat)
        if n:
            fuori["sorgenti"][nome] = n
    for o in OPZIONI:
        if re.search(o, t):
            fuori["opzioni"].append(o.replace("\\b", ""))
    # solo percorsi plausibili: niente a capo, estensione nota
    fuori["npy"] = sorted({x for x in re.findall(r'["\']([^"\'\n]{3,80})["\']', t)
                           if "descrittor" in x and x.endswith((".npy", ".npz", "/"))})
    return fuori


def main() -> int:
    ap = argparse.ArgumentParser(description="audit A — descrittore unico")
    ap.add_argument("--denso", type=Path, default=Path("models/gomo_classify.py"))
    ap.add_argument("--inserimento", type=Path, default=Path("models/gomo_onboard.py"))
    ap.add_argument("--dettaglio", action="store_true",
                    help="stampa il blocco di codice che costruisce il descrittore")
    a = ap.parse_args()

    E = {}
    for eti, p in (("compito denso", a.denso), ("inserimento", a.inserimento)):
        r = esamina(p)
        if r is None:
            print(f"{eti}: sorgente non trovato in {p}")
            continue
        E[eti] = r
        print(f"=== {eti}  ({p}, {r['righe']:,} righe) ===")
        print("  sorgenti del descrittore:")
        for k, v in sorted(r["sorgenti"].items(), key=lambda x: -x[1]):
            print(f"     {k:26s} {v:4d} riferimenti")
        print(f"  opzioni: {', '.join(r['opzioni']) or 'nessuna fra quelle cercate'}")
        if r["npy"]:
            print(f"  file di descrittori citati: {r['npy']}")
        print()

    if len(E) == 2:
        a_, b_ = E["compito denso"], E["inserimento"]
        sa, sb = set(a_["sorgenti"]), set(b_["sorgenti"])
        print("=" * 72)
        print("CONFRONTO")
        print("=" * 72)
        print(f"  sorgenti comuni:              {sorted(sa & sb) or 'nessuna'}")
        print(f"  solo nel compito denso:       {sorted(sa - sb) or 'nessuna'}")
        print(f"  solo nell'inserimento:        {sorted(sb - sa) or 'nessuna'}")
        oa, ob = set(a_["opzioni"]), set(b_["opzioni"])
        print(f"  opzioni solo nel denso:       {sorted(oa - ob) or 'nessuna'}")
        print(f"  opzioni solo nell'inserimento:{sorted(ob - oa) or 'nessuna'}")
        esito = (sa == sb) and bool(sa)
        print(f"\n  ESITO AUDIT A: {'SUPERATO' if esito else 'NON SUPERATO'}")
        if not esito:
            print("\n  I due esperimenti non usano il medesimo descrittore. Prima di")
            print("  progettare il componente va deciso QUALE dei due diventa la")
            print("  rappresentazione proposta, e l'altro va rifatto su quella.")
            if "anagrafica statica" in sb - sa:
                print("\n  In particolare l'inserimento usa l'anagrafica statica, che il")
                print("  compito denso non usa: e' informazione nota PRIMA di installare")
                print("  il sensore, non osservata da esso. Va dichiarato se faccia parte")
                print("  della rappresentazione o sia un ingresso separato.")

    if a.dettaglio:
        for eti, p in (("compito denso", a.denso), ("inserimento", a.inserimento)):
            if not p.exists():
                continue
            t = p.read_text(errors="ignore")
            for chiave in (r"node.?desc", r"descrittor", r"def .*desc"):
                s = sezione(t, chiave, 10, 45)
                if s:
                    print(f"\n{'='*72}\n{eti}: blocco attorno a /{chiave}/\n{'='*72}")
                    print(s)
                    break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
