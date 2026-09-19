#!/usr/bin/env python3
"""
Fase 3 — la campagna di prova, cinque bracci.
==============================================
    C  modello condiviso senza descrittore storico
    P  identita' osservabile BASE-CORRECTED
    A  riferimento storico PRIVILEGIATO
    R  riaddestramento completo, campionamento uniforme per NODO
    F  adattamento del solo embedding, da E gia' addestrato

    432 addestramenti (C, P, A, R)
    108 gruppi di adattamento F, tutti con la configurazione congelata
    540 valutazioni

I PREREQUISITI SONO BLOCCANTI: punti di controllo E leggibili, e la
configurazione di F **congelata**. Senza, la fase non parte.

BUDGET DI R. Il numero nominale di estrazioni per epoca e' **lo stesso degli
altri bracci** — `len(istanti) // lotto` iterazioni — sicche' la differenza sta
soltanto in COME le istanze sono estratte, che e' cio' che l'emendamento cambia.
La precedente configurazione di R non e' mai stata eseguita, quindi il
riferimento e' quello dei bracci gia' collaudati.

**Nessun accesso ai risultati di prova modifica la selezione di F.**

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_inserimento.py --piano
    poetry run python evoluzione/esperimenti/esegui_inserimento.py
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
    CONTESTI, PARTIZIONI, PrerequisitoMancante, descrivi_braccio, percorso_E,
    verifica_prova)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

BRACCI = ("C", "P", "A", "R", "F")
ADDESTRANO = ("C", "P", "A", "R")          # F adatta, non addestra
CALENDARIO = {"Madrid": (8887, 8983), "Londra": (8966, 9062),
              "Melbourne": (8806, 8902)}


def piano(contesti, semi_dich, semi_torch):
    """Bracci ADIACENTI per la stessa combinazione, ordine alternato.

    I cinque bracci della medesima combinazione si eseguono vicini, sicche' una
    lunga interruzione non lascia combinazioni con alcuni bracci soltanto.
    L'ordine interno ruota, perche' nessun braccio sia sempre primo.
    """
    fuori = []
    for i, (s, st) in enumerate(zip(semi_dich, semi_torch)):
        for j, p in enumerate(PARTIZIONI):
            r = (i * len(PARTIZIONI) + j) % len(contesti)
            for c in contesti[r:] + contesti[:r]:
                k = (i * len(PARTIZIONI) + j) % len(BRACCI)
                for b in BRACCI[k:] + BRACCI[:k]:
                    fuori.append({"contesto": c, "partizione": p,
                                  "seme": int(s), "seme_torch": int(st),
                                  "braccio": b})
    return fuori


def main() -> int:
    ap = argparse.ArgumentParser(description="fase 3: cinque bracci")
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--braccio", nargs="*", default=list(BRACCI))
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--epoche", type=int, default=35)
    ap.add_argument("--lotto", type=int, default=32)
    ap.add_argument("--passo", type=float, default=1e-3)
    ap.add_argument("--pazienza", type=int, default=8)
    a = ap.parse_args()

    _, dich, semi_torch = configurazione(inserimento=True)
    dir_camp = a.out / "inserimento"
    P = [x for x in piano(list(a.contesto), dich, semi_torch)
         if x["contesto"] in a.contesto and x["braccio"] in a.braccio]

    print("=" * 84)
    print(f"FASE 3 — CAMPAGNA DI PROVA  ({len(P)} esecuzioni)")
    print("=" * 84)
    for b in BRACCI:
        d = descrivi_braccio(b)
        print(f"  {b}  {d['popolazione'][:44]:44s} "
              f"{'adatta' if b == 'F' else 'addestra'}")
    print(f"\n  budget di R: stesso numero nominale di estrazioni per epoca")
    print(f"  degli altri bracci; cambia SOLO come le istanze sono estratte")

    # ---- PREREQUISITI, bloccanti ------------------------------------------
    try:
        r = verifica_prova(a.out / "E_inserimento", a.out / "selezione_F",
                           semi_torch, a.contesto)
        print(f"\n  prerequisiti verificati: {r['punti_di_controllo']} punti E")
        for c, s in r["scelte_F"].items():
            print(f"     F su {c:11s} ({s['aggiornamenti']}, {s['passo']:g}) "
                  f"— congelata")
    except PrerequisitoMancante as e:
        print(f"\n{e}")
        return 1

    if a.piano:
        from collections import Counter
        print(f"\n  --piano: nessuna esecuzione avviata.")
        print(f"  per braccio:  {dict(Counter(x['braccio'] for x in P))}")
        print(f"  per contesto: {dict(Counter(x['contesto'] for x in P))}")
        print(f"  addestramenti: "
              f"{sum(1 for x in P if x['braccio'] in ADDESTRANO)}")
        print(f"  adattamenti:   {sum(1 for x in P if x['braccio'] == 'F')}")
        print(f"\n  primi otto:")
        for x in P[:8]:
            print(f"     {x['contesto']:11s} p{x['partizione']} "
                  f"s{x['seme']} {x['braccio']}")
        return 0

    print("\n  NON ANCORA INTEGRATA l'esecuzione dei cinque bracci.")
    print("  Manca il collegamento fra `addestra_una` e i corpus espliciti di")
    print("  A ed R, e fra `adattamento` e il punto di controllo E per F.")
    print("\n  Va eseguita PRIMA la prova tecnica ridotta:")
    print("     poetry run python evoluzione/esperimenti/prova_inserimento.py")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
