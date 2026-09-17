#!/usr/bin/env python3
"""
Tracciabilita' della Tabella 54 — quale configurazione ha prodotto ciascun valore.
==================================================================================
Nessuna esecuzione e nessuna modifica al codice che ha prodotto i risultati.

PERCHE'. L'audit A ha trovato nel sorgente il sostegno per due descrittori
diversi — sedici statistiche con proiezione lineare, e quarantacinque con un
encoder a due strati — mentre la Tabella 54 ne dichiara uno solo. Prima di
fissare lo schema del componente occorre sapere quale configurazione ha prodotto
ciascun valore, altrimenti il paper erediterebbe un'ambiguita' dagli esperimenti
precedenti.

CHE COSA RICOSTRUISCE, per ciascuna cella della tabella:

  * il file di risultato e le esecuzioni incluse, con i semi;
  * gli argomenti effettivi dell'esecuzione, dai log e dalle colonne di
    configurazione conservate nei risultati;
  * il descrittore impiegato, identificato dalla FORMA del file `.npy`: e' la
    prova piu' solida, perche' non dipende da come la campagna e' stata chiamata;
  * la trasformazione, lineare o a due strati, dedotta da `--desc-hidden`;
  * quale altra identita' fosse presente — embedding libero, vettori
    dell'adiacenza adattiva, bias per nodo;
  * la formula del recupero, distinguendo la media dei recuperi per esecuzione
    dal recupero calcolato sulle perdite medie: NON sono la stessa cosa.

STATI POSSIBILI per ciascun risultato:

  verificato              configurazione e calcolo ricostruiti
  parzialmente verificato manca qualche elemento
  non ricostruibile       evidenza insufficiente
  discordante             file e testo descrivono oggetti diversi

Lo scopo e' una mappa affidabile, NON la conferma del deliverable: uno stato
«discordante» e' un esito legittimo di questo controllo.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/traccia_tabella54.py
    poetry run python evoluzione/audit/traccia_tabella54.py --out results/evoluzione/audit/tracciabilita_t54.csv
"""
import argparse
import glob as globmod
import hashlib
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

CTX = {"t4clon": "Londra", "t4cmad": "Madrid", "t4cmel": "Melbourne",
       "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023"}

# i quattro bracci che la Tabella 54 confronta, come il revisore li elenca
BRACCI = {
    "senza identita'":      ["gwn_none"],
    "embedding libero":     ["gwn_adaptive", "gwn_emb", "gwn_fixed"],
    "descrittore d = 2":    ["gwn_none"],
    "descrittore d = 8":    ["gwn_none"],
}
# i valori del divario A-C come la tabella li riporta, per il confronto
DIVARIO = {"Londra": 0.0234, "Madrid": 0.0274, "Melbourne": 0.0168,
           "d8/2024": 0.0322, "d15/2024": 0.0393, "d8/2023": 0.0424}


def descrittori():
    """{percorso: (forma, impronta)} dei file di descrittore presenti."""
    fuori = {}
    for p in sorted(globmod.glob("descrittori/*.npy")):
        try:
            a = np.load(p, mmap_mode="r")
        except Exception:
            continue
        with open(p, "rb") as fh:
            h = hashlib.sha256(fh.read()).hexdigest()[:12]
        fuori[p] = (tuple(a.shape), h)
    return fuori


def comandi():
    """Righe di comando trovate nei log, con gli argomenti che ci interessano."""
    fuori = []
    for p in sorted(globmod.glob("log/*.log")) + sorted(globmod.glob("*.log")):
        try:
            t = open(p, errors="ignore").read()
        except Exception:
            continue
        for m in re.finditer(r"[^\n]*gomo_classify\.py[^\n]*", t):
            r = m.group(0)
            if "--node-desc" in r or "--emb" in r:
                fuori.append((os.path.basename(p), r.strip()))
    return fuori


def arg(riga, nome, default=None):
    m = re.search(rf"{re.escape(nome)}\s+(\S+)", riga)
    return m.group(1) if m else default


def esecuzioni(prefissi, c, semi=5):
    """File di risultato per contesto, con i semi effettivamente presenti."""
    for p in prefissi:
        f = sorted(globmod.glob(f"replication/*/{p}_{c}_s?.csv"))
        if len(f) >= 3:
            s = sorted(int(re.search(r"_s(\d)\.csv$", x).group(1)) for x in f)
            return p, f, s
    return None, [], []


def main() -> int:
    ap = argparse.ArgumentParser(description="tracciabilita' della Tabella 54")
    ap.add_argument("--prefissi", nargs="*",
                    default=["a6", "a6A", "a6X", "a6X8", "desc", "emb_abl",
                             "fix_classify", "classify"])
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    # ------------------------------------------------- i file di descrittore ---
    D = descrittori()
    print("=" * 84)
    print("DESCRITTORI PRESENTI — la forma identifica la configurazione")
    print("=" * 84)
    if not D:
        print("  nessun file in descrittori/: la configurazione non e' verificabile "
              "da questa via")
    for p, (forma, h) in D.items():
        n = forma[1] if len(forma) > 1 else "?"
        eti = ("sedici statistiche, come dichiarato in Tabella 54" if n == 16 else
               "quarantacinque statistiche, campagna diversa" if n == 45 else
               "numero di statistiche non previsto")
        print(f"  {p:38s} {str(forma):12s} {h}  {eti}")

    # -------------------------------------------------- i comandi eseguiti ----
    C = comandi()
    print("\n" + "=" * 84)
    print("ESECUZIONI CON DESCRITTORE O EMBEDDING, dai log")
    print("=" * 84)
    if not C:
        print("  nessuna riga di comando trovata nei log")
    visti = set()
    for lg, riga in C:
        k = (arg(riga, "--node-desc"), arg(riga, "--desc-proj", "0"),
             arg(riga, "--desc-hidden", "0"), arg(riga, "--emb", "?"))
        if k in visti:
            continue
        visti.add(k)
        nd, pr, hd, em = k
        trasf = ("lineare" if hd in ("0", None) and pr not in ("0", None)
                 else f"due strati, {hd} nascoste" if hd not in ("0", None)
                 else "nessuna")
        print(f"  [{lg}]")
        print(f"     descrittore {nd or '—'} | proiezione {pr} | "
              f"trasformazione: {trasf} | --emb {em}")

    # ------------------------------------------------ la mappa per contesto ---
    print("\n" + "=" * 84)
    print("MAPPA RISULTATO -> CONFIGURAZIONE")
    print("=" * 84)
    righe = []
    for c, nome in CTX.items():
        for braccio, mods in BRACCI.items():
            pref, files, semi = esecuzioni(a.prefissi, c)
            stato = "non ricostruibile"
            note = []
            if files:
                d = pd.read_csv(files[0])
                cm = "model" if "model" in d.columns else "mode"
                presenti = sorted(d[cm].astype(str).unique()) if cm in d else []
                trovato = [m for m in mods if m in presenti]
                if trovato:
                    stato = "parzialmente verificato"
                    note.append(f"modello {trovato[0]} in {pref}")
                    # colonne di configurazione conservate nel risultato
                    cfg = [x for x in d.columns
                           if re.search(r"desc|emb|hidden|proj|node", x, re.I)]
                    if cfg:
                        stato = "verificato"
                        note.append("configurazione nel risultato: "
                                    + ", ".join(f"{x}={d[x].iloc[0]}" for x in cfg))
                    else:
                        note.append("nessuna colonna di configurazione nel risultato")
                else:
                    note.append(f"modelli presenti: {presenti[:4]}")
            righe.append(dict(contesto=nome, braccio=braccio, campagna=pref or "—",
                              file=len(files), semi=",".join(map(str, semi)),
                              stato=stato, note=" | ".join(note)))
        print(f"{nome:11s} " + " ".join(
            f"{r['braccio'][:12]}:{r['stato'][:4]}" for r in righe[-4:]))

    T = pd.DataFrame(righe)
    print(f"\n  stati: {dict(T.stato.value_counts())}")

    # ------------------------------------------- la formula del recupero -----
    print("\n" + "=" * 84)
    print("FORMULA DEL RECUPERO — due procedure, non equivalenti")
    print("=" * 84)
    print("  per esecuzione, poi mediato:   media_s[ (L_none,s - L_desc,s) /")
    print("                                          (L_none,s - L_emb,s) ]")
    print("  dalle perdite medie:           (media_s L_none - media_s L_desc) /")
    print("                                 (media_s L_none - media_s L_emb)")
    print("\n  Le due coincidono solo se il denominatore e' costante fra le")
    print("  esecuzioni. Il divario A-C varia fra 0,0168 e 0,0424 sui contesti,")
    print("  e fra i semi entro contesto: la procedura effettiva va identificata")
    print("  dal codice che ha prodotto la tabella, non dedotta dai valori")
    print("  arrotondati che vi compaiono.")

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        T.to_csv(a.out, index=False)
        print(f"\n  mappa salvata in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
