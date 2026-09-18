#!/usr/bin/env python3
"""
Selezione della configurazione di adattamento di F, sulla VALIDAZIONE.
=======================================================================
**L'unica esecuzione autorizzata prima della campagna di prova.**

Sei combinazioni, valutate su un **episodio di validazione** separato dal test:

    passo di apprendimento   1e-3, 1e-2
    aggiornamenti massimi    10, 50, 200

**UNA configurazione per citta'**, applicata poi a tutti i nodi nuovi, le
partizioni e le inizializzazioni della prova. **Non una per nodo**: cambierebbe il
metodo e richiederebbe un'ulteriore validazione locale.

LA REGOLA DI SCELTA, dichiarata qui: wCE mediata sui quattro orizzonti, poi sulle
inizializzazioni, poi sulle tre partizioni con uguale peso. **A parita' numerica si
preferisce, nell'ordine: meno aggiornamenti, poi passo minore.**

CHE COSA SIGNIFICA «AGGIORNAMENTO»:

    ottimizzatore            Adam
    decadimento dei pesi     nessuno
    arresto anticipato       nessuno durante l'adattamento
    ciascun aggiornamento    usa TUTTI gli esempi ammissibili del singolo nodo

Un aggiornamento a lotto completo per nodo rende il budget interpretabile e
indipendente dall'ordine dei minilotti.

SI AGGIORNA SOLTANTO IL NUOVO EMBEDDING. Restano congelati backbone, ramo statico,
teste, embedding dei nodi esistenti, statistiche e buffer della BatchNorm.

**L'inizializzazione del nuovo embedding e' la MEDIA degli embedding dei nodi
iniziali**, calcolata sul punto di controllo E: regola deterministica che non usa
dati futuri ne' sceglie un nodo favorevole.

AMMISSIBILITA' DI UN ESEMPIO: l'orizzonte massimo non supera t1. Le celle bersaglio
mancanti sono escluse dalla perdita; **l'esempio contribuisce se contiene almeno un
target valido**. Non si richiedono quattro target validi su quattro.

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
from evoluzione.esperimenti.semi import configurazione  # noqa: E402

PASSI = (1e-3, 1e-2)
AGGIORNAMENTI = (10, 50, 200)
L24 = 96
ORIZZONTI = (1, 2, 4, 8)
CALENDARIO = {"Madrid": (8887, 8983), "Londra": (8966, 9062),
              "Melbourne": (8806, 8902)}


def griglia():
    """Le sei combinazioni, nell'ordine di preferenza a parita'.

    L'ordinamento e' dichiarato QUI: a parita' numerica vince chi viene prima,
    cioe' meno aggiornamenti e poi passo minore.
    """
    return sorted([(b, e) for e in PASSI for b in AGGIORNAMENTI],
                  key=lambda x: (x[0], x[1]))


def scegli(punteggi):
    """La combinazione con la wCE minore; a parita', la prima della griglia.

    `punteggi` = {(aggiornamenti, passo): wCE}. La tolleranza di parita' e'
    dichiarata: due valori entro 1e-9 si considerano pari, e decide l'ordine.
    """
    if not punteggi:
        return None
    ordine = griglia()
    migliore = min(punteggi.values())
    pari = [k for k in ordine
            if k in punteggi and punteggi[k] - migliore <= 1e-9]
    return pari[0] if pari else None


def main() -> int:
    ap = argparse.ArgumentParser(description="selezione di F")
    ap.add_argument("--piano", action="store_true",
                    help="mostra il piano e si ferma")
    ap.add_argument("--contesto", nargs="*", default=list(CALENDARIO))
    ap.add_argument("--out", type=Path,
                    default=Path("results/evoluzione/E1_inserimento/"
                                 "selezione_F.json"))
    a = ap.parse_args()

    ini, dich, torch_semi = configurazione(inserimento=True)
    print("=" * 84)
    print("SELEZIONE DELLA CONFIGURAZIONE DI ADATTAMENTO DI F")
    print("=" * 84)
    print(f"  griglia: passo {list(PASSI)} x aggiornamenti "
          f"{list(AGGIORNAMENTI)} = {len(griglia())} combinazioni")
    print(f"  ordine di preferenza a parita': " +
          ", ".join(f"({b},{e:g})" for b, e in griglia()))
    print(f"  UNA configurazione per citta', non per nodo")
    print(f"\n  inizializzazioni {list(dich)}")
    print(f"  calendario (t0, t1): {CALENDARIO}")
    print(f"\n  episodio di VALIDAZIONE: installazione all'inizio del periodo")
    print(f"  temporale di validazione, adattamento sui soli nodi di")
    print(f"  validazione induttiva, valutazione nel periodo successivo,")
    print(f"  sempre ENTRO la validazione temporale.")
    print(f"\n  regola: wCE media sugli orizzonti, poi sulle inizializzazioni,")
    print(f"  poi sulle partizioni con uguale peso.")

    if a.piano:
        n = len(a.contesto) * 3 * len(dich) * len(griglia())
        print(f"\n  --piano: nessuna esecuzione avviata.")
        print(f"  adattamenti da eseguire: {len(a.contesto)} citta' x 3 "
              f"partizioni x {len(dich)} inizializzazioni x {len(griglia())} "
              f"combinazioni = {n:,}")
        print(f"  piu' {len(a.contesto) * 3 * len(dich)} punti di controllo E, "
              f"da addestrare prima.")
        return 0

    print("\n  NON IMPLEMENTATA: la selezione richiede i punti di controllo E,")
    print("  che non esistono ancora. Vanno addestrati prima, sui soli nodi")
    print("  iniziali, con embedding liberi a otto dimensioni.")
    print("\n  Ordine delle attivita':")
    print("     1. addestrare E — 3 citta' x 3 partizioni x 12 semi = 108")
    print("     2. eseguire questa selezione sulle sei combinazioni")
    print("     3. congelare le tre configurazioni cittadine")
    print("     4. solo allora, la campagna di prova")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
