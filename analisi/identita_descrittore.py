#!/usr/bin/env python3
"""
Provenienza dell'identita' di nodo — descrittore osservabile (§8.6.1, Tabella 52).
==================================================================================
Nessun addestramento: legge i CSV della griglia a due fattori e delle varianti
con descrittore.

LA DOMANDA, nella forma esatta. La media storica per nodo e momento-tipo e' gia'
un profilo temporale esplicito per nodo, ed e' presente in TUTTE le varianti. La
cella che la conserva rimuovendo i vettori appresi per nodo e' peggiore della
cella completa fra il 2,95% e il 5,39%. Il profilo medio quindi c'e' gia' e non
basta: cio' che i parametri liberi aggiungono e' un RESIDUO del 3-5% sopra un
profilo settimanale gia' disponibile.

La domanda non e' se l'identita' coincida con il profilo, ma se quel residuo sia
raggiungibile da statistiche OSSERVABILI del nodo oppure richieda parametri
liberi. La prima risposta rende il modello dispiegabile su un tratto mai
sensorizzato, la seconda no.

LA SCALA. Il divario A-C e' la distanza in entropia pesata fra la cella completa
(embedding libero) e quella priva di vettori appresi per nodo. Il recupero e' la
quota di quel divario colmata dalla variante con descrittore:

    recupero = (wCE_C - wCE_variante) / (wCE_C - wCE_A)

E' un RAPPORTO: dove il divario e' piccolo la frazione e' poco informativa, e un
valore oltre il 100% non indica superiorita'. Lo script riporta sempre il
residuo assoluto accanto alla quota, ed e' quello il numero da mettere in
copertina.

LA PROIEZIONE E' APPRESA, non calcolata a priori. Una compressione non
supervisionata massimizzerebbe la varianza del descrittore anziche' la sua
rilevanza predittiva, e nel confronto svantaggerebbe il descrittore rispetto a un
embedding appreso per il compito.

CELLE DELLA GRIGLIA (`gomo_classify.py`):

    A  --emb 8                              embedding libero: cella completa
    C  --emb 0                              nessun vettore appreso per nodo
    P2 --emb 0 --node-desc <npy> --desc-proj 2      proiezione lineare, 2 dim.
    P8 --emb 0 --node-desc <npy> --desc-proj 8      proiezione lineare, 8 dim.
    N8 --emb 0 --node-desc <npy> --desc-proj 8 --desc-hidden 32   non lineare

I descrittori si generano con `analisi/genera_descrittori.py` e sono calcolati
SUL SOLO PERIODO DI ADDESTRAMENTO.

Uso (dalla radice OR3/):

    poetry run python analisi/identita_descrittore.py
"""
from pathlib import Path
import argparse
import glob as globmod
import math

import numpy as np
import pandas as pd

CONTESTI = {
    "t4clon": "Londra", "t4cmad": "Madrid", "t4cmel": "Melbourne",
    "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023",
}
VARIANTI = {
    "a6P2": "lineare d=2",
    "a6P8": "lineare d=8",
    "a6N8": "non lineare d=8",
    "a6X8": "non lineare, descrittore esteso",
}


def st(v):
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


def serie(prefisso, c, semi, cartella: Path):
    """wCE media sui quattro orizzonti, per seme. None se un seme manca:
    serie parziali non vanno mediate."""
    v = []
    for s in range(semi):
        f = globmod.glob(str(cartella / f"{prefisso}_{c}_s{s}.csv"))
        if not f:
            return None
        d = pd.read_csv(f[0])
        q = d[d.model.astype(str).str.startswith("gwn")]
        if not len(q):
            return None
        v.append(q.wCE.mean())
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description="identita' da descrittore osservabile")
    ap.add_argument("--dir", type=Path, default=Path("replication"))
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--criterio", type=float, default=70.0,
                    help="quota di recupero richiesta, in percentuale")
    a = ap.parse_args()

    t = 2.776 if a.semi == 5 else 4.303        # t di Student al 95%, gl = semi-1

    print("=" * 108)
    print("TABELLA 52 - recupero del divario di identita' da statistiche osservabili")
    print("=" * 108)
    print(f"{'contesto':11s} {'divario A-C':>12} | " +
          " ".join(f"{e:>26}" for e in VARIANTI.values()))

    riepilogo = {}
    for c, nome in CONTESTI.items():
        A = serie("a6A", c, a.semi, a.dir)
        C = serie("a6C", c, a.semi, a.dir)
        if A is None or C is None:
            print(f"{nome:11s} celle A/C incomplete: rieseguire la griglia a due fattori")
            continue
        divario = st([C[i] - A[i] for i in range(a.semi)])[0]
        celle = []
        for pref, eti in VARIANTI.items():
            V = serie(pref, c, a.semi, a.dir)
            if V is None:
                celle.append(f"{'—':>26}")
                continue
            rec = [100 * (C[i] - V[i]) / (C[i] - A[i]) for i in range(a.semi)]
            res = st([V[i] - A[i] for i in range(a.semi)])[0]
            m, sd = st(rec)
            hw = t * sd / math.sqrt(a.semi)
            celle.append(f"{m:6.1f}% [{m - hw:5.1f};{m + hw:6.1f}] r={res:+.4f}")
            riepilogo.setdefault(pref, []).append((nome, m, m - hw, res, divario))
        print(f"{nome:11s} {divario:12.4f} | " + " ".join(celle))

    print("\nIl RESIDUO ASSOLUTO (r=) e' la grandezza da riportare in copertina: la quota e'")
    print("un rapporto con denominatore piccolo e stimato, e diventa instabile agli estremi.")
    print("Dove il divario e' minimo la frazione non e' interpretabile, e un valore oltre il")
    print("100% non indica superiorita'.\n")

    print("=" * 108)
    print(f"CRITERIO: recupero sopra il {a.criterio:.0f}% in almeno quattro contesti")
    print("=" * 108)
    for pref, eti in VARIANTI.items():
        if pref not in riepilogo:
            continue
        r = riepilogo[pref]
        sopra = sum(1 for _, m, _, _, _ in r if m > a.criterio)
        esclude = sum(1 for _, _, lo, _, _ in r if lo > a.criterio)
        esito = "soddisfatto" if sopra >= 4 else "non soddisfatto"
        print(f"  {eti:32s} stime sopra la soglia {sopra}/{len(r)}, "
              f"intervallo che la esclude {esclude}/{len(r)} -> {esito}")

    print("\n" + "=" * 108)
    print("PARSIMONIA — conteggio dei parametri")
    print("=" * 108)
    print("La mappa dal descrittore e' CONDIVISA fra tutti i nodi, l'embedding no.")
    print("L'argomento va enunciato come proprieta' di scala, non come rapporto a un N:\n")
    print(f"  {'configurazione':44s} {'parametri':>12} {'cresce con N?':>15}")
    print(f"  {'mappa lineare 16 -> 8 (senza termine costante)':44s} {16 * 8:12d} {'no':>15}")
    print(f"  {'mappa non lineare 16 -> 32 -> 8':44s} "
          f"{16 * 32 + 32 + 32 * 8 + 8:12d} {'no':>15}")
    print(f"  {'mappa non lineare 45 -> 32 -> 8':44s} "
          f"{45 * 32 + 32 + 32 * 8 + 8:12d} {'no':>15}")
    for K, citta in ((828, "Madrid"), (99, "rete di dispiegamento")):
        print(f"  {'embedding 8 dim. su ' + str(K) + ' nodi (' + citta + ')':44s} "
              f"{K * 8:12d} {'SI':>15}")
    print("\n  Il costo del descrittore e' O(1) nei nodi, quello dell'embedding O(N):")
    print("  su una rete piccola il rapporto si inverte. L'argomento portante non e'")
    print("  comunque il conteggio, ma che la mappa si applichi a un nodo mai visto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
