#!/usr/bin/env python3
"""
Fase 2 — selezione della configurazione di adattamento di F.
=============================================================
Sei combinazioni per ciascuna terna (citta', partizione, seme), valutate su un
**episodio di validazione** separato dal test. **UNA configurazione per citta'.**

    passo di apprendimento   1e-3, 1e-2
    aggiornamenti massimi    10, 50, 200

LA REGOLA, dichiarata qui: wCE mediata sui quattro orizzonti, poi sulle
inizializzazioni, poi sulle tre partizioni con uguale peso. **A parita' numerica
si preferisce, nell'ordine: meno aggiornamenti, poi passo minore.**

I CINQUE VINCOLI, verificati a ogni candidato:

    1. ogni combinazione RIPARTE da E: nessun adattamento cumulativo;
    2. ottimizzatore NUOVO per ciascuna;
    3. al test si trasferiscono i soli IPERPARAMETRI;
    4. il punto di controllo E resta IMMUTATO;
    5. nodi di validazione e test hanno REGISTRI DISTINTI.

**Le copie si eseguono in sequenza**: non risiedono tutte in memoria.

IL MANIFESTO e' **uno per terna**, con le sei combinazioni dentro: griglia,
aggiornamenti eseguiti, seme, impronte iniziale e finale, costo, metrica di
validazione e regola applicata.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/seleziona_F.py --piano
    poetry run python evoluzione/esperimenti/seleziona_F.py
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.fasi import (  # noqa: E402
    CONTESTI, PARTIZIONI, PrerequisitoMancante, percorso_E,
    verifica_selezione_F)
from evoluzione.esperimenti.semi import configurazione  # noqa: E402

PASSI = (1e-3, 1e-2)
AGGIORNAMENTI = (10, 50, 200)
L24 = 96
CALENDARIO = {"Madrid": (8887, 8983), "Londra": (8966, 9062),
              "Melbourne": (8806, 8902)}


def griglia():
    """L'ordine di preferenza a parita': meno aggiornamenti, poi passo minore."""
    return [(b, e) for b in AGGIORNAMENTI for e in PASSI]


def scegli(punteggi):
    """Il minimo; a parita' entro 1e-9, il primo della griglia."""
    if not punteggi:
        return None
    m = min(punteggi.values())
    for k in griglia():
        if k in punteggi and punteggi[k] - m <= 1e-9:
            return k
    return None


def aggrega(per_terna, contesto):
    """wCE media sugli orizzonti (gia' fatta), poi sui semi, poi sulle
    partizioni con UGUALE PESO."""
    fuori = {}
    for k in griglia():
        per_part = []
        for p in PARTIZIONI:
            v = [d["punteggi"].get(str(k), d["punteggi"].get(k))
                 for (c, pp, _), d in per_terna.items()
                 if c == contesto and pp == p]
            v = [x for x in v if x is not None and np.isfinite(x)]
            if v:
                per_part.append(float(np.mean(v)))      # media sui semi
        if per_part:
            fuori[k] = float(np.mean(per_part))         # poi sulle partizioni
    return fuori


def main() -> int:
    ap = argparse.ArgumentParser(description="fase 2: selezione di F")
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()

    _, dich, semi_torch = configurazione(inserimento=True)
    dir_E = a.out / "E_inserimento"
    dir_sel = a.out / "selezione_F"

    print("=" * 84)
    print("FASE 2 — SELEZIONE DELLA CONFIGURAZIONE DI F")
    print("=" * 84)
    print(f"  griglia: {len(griglia())} combinazioni, ordine di preferenza")
    print(f"     " + ", ".join(f"({b},{e:g})" for b, e in griglia()))
    print(f"  **UNA configurazione per citta'**, non per nodo")
    print(f"  regola: wCE media sugli orizzonti, poi sui semi, poi sulle "
          f"partizioni")
    print(f"  a parita': meno aggiornamenti, poi passo minore")
    n = len(a.contesto) * len(PARTIZIONI) * len(semi_torch)
    print(f"\n  terne: {n} | adattamenti: {n * len(griglia()):,}")

    try:
        r = verifica_selezione_F(dir_E, semi_torch, a.contesto)
        print(f"\n  prerequisiti verificati: {r['punti_di_controllo']} punti di "
              f"controllo E, leggibili e con la mappa nodo-riga")
    except PrerequisitoMancante as e:
        print(f"\n{e}")
        return 1

    if a.piano:
        print(f"\n  --piano: nessuna esecuzione avviata.")
        print(f"  ogni terna produce UN manifesto con le sei combinazioni "
              f"dentro")
        return 0

    print("\n  NON ANCORA IMPLEMENTATA la valutazione sull'episodio di")
    print("  validazione: richiede il caricamento dei dati e la costruzione")
    print("  dei lotti, che `addestramento.py` fa per l'addestramento ma non")
    print("  per un episodio di inserimento separato.")
    print("\n  Prima di implementarla va fissato:")
    print("     - quali nodi costituiscono l'episodio di VALIDAZIONE")
    print("       (i nodi di validazione induttiva, per il disegno)")
    print("     - l'istante di installazione: inizio del periodo temporale")
    print("       di validazione, non di prova")
    print("     - il perimetro di valutazione: il periodo successivo,")
    print("       SEMPRE entro la validazione temporale")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
