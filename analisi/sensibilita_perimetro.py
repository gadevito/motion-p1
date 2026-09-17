#!/usr/bin/env python3
"""
Sensibilita' del vantaggio medio al perimetro di richiamo (§8.6.7).
====================================================================
Nessun addestramento: riaggrega i dump di probabilita' gia' salvati.

L'OBIEZIONE A CUI RISPONDE. La statistica sintetica «vantaggio medio nel regime
operativo» e' la media dei vantaggi di precisione a richiamo appaiato ai livelli
0,60, 0,70 e 0,80 — cioe' proprio i tre livelli dove il vantaggio e' maggiore.
Va mostrato che il risultato non dipende da dove e' stata messa la soglia.

Lo script calcola la stessa statistica su TRE PERIMETRI progressivamente piu'
larghi, e su ENTRAMBE le aggregazioni temporali che il documento usa:

  perimetri     >= 0,60 (dichiarato) | >= 0,50 | >= 0,30 (tutti i livelli)
  aggregazioni  solo 15 minuti | media sui quattro orizzonti

Riporta anche il valore a OGNI livello, perche' e' cio' che consente di vedere
quali contesti cambiano segno e a quale livello. Il livello 0,50 e' quello che
decide fra le due letture, essendo il primo escluso dalla soglia dichiarata.

COME SI LEGGE, nell'ordine chiesto:

  1. se il vantaggio medio resta positivo in tutti e sei i contesti allargando
     il perimetro, la soglia dichiarata e' CONSERVATIVA e il risultato non
     dipende dalla sua collocazione;
  2. un calo modesto e uniforme dice che i livelli aggiunti sono meno
     favorevoli ma non ribaltano nulla; un calo forte concentrato su un
     contesto dice che quel contesto regge solo nel perimetro stretto;
  3. un contesto che cambia segno va riportato con il livello a cui accade.

DUE AVVERTENZE SULLA STATISTICA, da riportare accanto ai numeri.

La media fra livelli e' NON PESATA: ogni livello di richiamo pesa uguale,
benche' i punti di lavoro corrispondenti abbiano prevalenze molto diverse. E'
una scelta di lettura, non una proprieta' dei dati, e allargare il perimetro
aumenta il peso relativo dei punti a bassa precisione.

Ai richiami bassi il confronto e' fra punti di lavoro in cui ENTRAMBI i modelli
predicono pochi positivi: la precisione vi e' alta per costruzione e le
differenze relative si comprimono. Un vantaggio minore a 0,30 non significa
quindi che il modello sia peggiore in quel regime.

Uso (dalla radice OR3/):

    poetry run python analisi/sensibilita_perimetro.py
    poetry run python analisi/sensibilita_perimetro.py --livelli 0.3 0.4 0.5 0.6 0.7 0.8
"""
from pathlib import Path
import argparse
import glob as globmod
import math

import numpy as np

BASE = Path("data_collection")
GOMO = BASE / "go-mo" / "gomo"
T4C = BASE / "traffic4cast"
ORIZZONTI = ("15m", "30m", "60m", "120m")

CONTESTI = {
    "d8_2024": (GOMO / "targets_2024_urb_d8.npz", "d8/2024"),
    "d15_2024": (GOMO / "targets_2024_urb_d15.npz", "d15/2024"),
    "d8_2023": (GOMO / "targets_2023_urb_d8.npz", "d8/2023"),
    "t4cmad": (T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz", "Madrid"),
    "t4clon": (T4C / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz", "Londra"),
    "t4cmel": (T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz", "Melbourne"),
}


def st(v):
    v = [x for x in v if np.isfinite(x)]
    if not v:
        return float("nan"), float("nan")
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


def blocchi(percorso, tag):
    if not globmod.glob(percorso):
        return None
    z = np.load(percorso, allow_pickle=True)
    out = {}
    for h in ORIZZONTI:
        ch = [k[3:] for k in z.files if k.startswith("tag") and str(z[k]) == f"{tag}|{h}"]
        if not ch:
            return None
        i = ch[0]
        out[h] = (z[f"p{i}"].astype("float32"), z[f"y{i}"].astype(int))
    return out


def precisione_a_richiamo(P, Y, bersaglio):
    """Precisione della curva PR nel primo punto in cui il richiamo raggiunge
    il bersaglio. Ordinando per punteggio decrescente, il richiamo e' monotono
    non decrescente, quindi la ricerca binaria e' lecita."""
    ordine = np.argsort(-P[:, 2])
    y = (Y[ordine] == 2).astype(np.int64)
    tp = np.cumsum(y)
    tot = int(y.sum())
    if tot == 0:
        return float("nan")
    rec = tp / tot
    pre = tp / np.arange(1, len(y) + 1)
    i = int(np.searchsorted(rec, bersaglio))
    return float(pre[i]) if i < len(pre) else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description="sensibilita' al perimetro di richiamo")
    ap.add_argument("--probs", default="replication/probs")
    ap.add_argument("--nn-schema", nargs="*", default=["fix_classify_{c}_s{s}.npz",
                                                       "classify_{c}_s{s}.npz"])
    ap.add_argument("--gb-schema", default="lgbristr_{c}_s{s}.npz")
    ap.add_argument("--nn-tag", default="gwn_adaptive")
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--livelli", type=float, nargs="+",
                    default=[0.30, 0.50, 0.60, 0.70, 0.80])
    ap.add_argument("--perimetri", type=float, nargs="+", default=[0.60, 0.50, 0.30])
    a = ap.parse_args()

    D = {}
    for c in CONTESTI:
        for s in range(a.semi):
            nn = None
            for sch in a.nn_schema:
                nn = blocchi(f"{a.probs}/{sch.format(c=c, s=s)}", a.nn_tag)
                if nn:
                    break
            gb = blocchi(f"{a.probs}/{a.gb_schema.format(c=c, s=s)}", "lgb_fair")
            if nn and gb:
                D[(c, s)] = (nn, gb)

    # vantaggio[(contesto, seme, orizzonte, livello)] = differenza relativa
    van = {}
    for (c, s), (nn, gb) in D.items():
        for h in ORIZZONTI:
            Pn, Yn = nn[h]
            Pg, Yg = gb[h]
            for L in a.livelli:
                pn = precisione_a_richiamo(Pn, Yn, L)
                pg = precisione_a_richiamo(Pg, Yg, L)
                van[(c, s, h, L)] = (100 * (pn - pg) / pg
                                     if np.isfinite(pn) and np.isfinite(pg) and pg > 0
                                     else float("nan"))

    for agg, orizz in (("solo 15 minuti", ("15m",)),
                       ("media sui quattro orizzonti", ORIZZONTI)):
        print("=" * 104)
        print(f"VANTAGGIO MEDIO PER PERIMETRO — aggregazione: {agg}")
        print("=" * 104)
        print(f"{'contesto':10s} " + "".join(
            f"{'>= ' + format(p, '.2f'):>22}" for p in a.perimetri))
        for c, (tp, nome) in CONTESTI.items():
            semi = sorted({s for (cc, s) in D if cc == c})
            if len(semi) < a.semi:
                print(f"{nome:10s} dump incompleti ({len(semi)}/{a.semi})")
                continue
            celle = []
            for P in a.perimetri:
                liv = [L for L in a.livelli if L >= P - 1e-9]
                per_seme = []
                for s in semi:
                    v = [van[(c, s, h, L)] for h in orizz for L in liv]
                    v = [x for x in v if np.isfinite(x)]
                    if v:
                        per_seme.append(sum(v) / len(v))
                m, sd = st(per_seme)
                celle.append(f"{m:+11.1f}% ± {sd:5.1f}  ")
            print(f"{nome:10s} " + "".join(celle))
        print()

    print("=" * 104)
    print("VALORE A CIASCUN LIVELLO (media sui quattro orizzonti e sui semi)")
    print("=" * 104)
    print(f"{'contesto':10s} " + "".join(f"{format(L, '.2f'):>14}" for L in a.livelli))
    cambi = []
    for c, (tp, nome) in CONTESTI.items():
        semi = sorted({s for (cc, s) in D if cc == c})
        if len(semi) < a.semi:
            continue
        celle, valori = [], {}
        for L in a.livelli:
            per_seme = []
            for s in semi:
                v = [van[(c, s, h, L)] for h in ORIZZONTI]
                v = [x for x in v if np.isfinite(x)]
                if v:
                    per_seme.append(sum(v) / len(v))
            m, sd = st(per_seme)
            valori[L] = m
            celle.append(f"{m:+8.1f} ±{sd:4.1f}")
        print(f"{nome:10s} " + "".join(f"{x:>14}" for x in celle))
        neg = [L for L in a.livelli if valori[L] < 0]
        if neg:
            cambi.append((nome, neg, valori))
    print()

    if cambi:
        print("CONTESTI CON VANTAGGIO NEGATIVO A QUALCHE LIVELLO")
        for nome, neg, valori in cambi:
            liv = ", ".join(f"{L:.2f} ({valori[L]:+.1f}%)" for L in neg)
            print(f"   {nome:10s} negativo a: {liv}")
        print("   La domanda che conta e' se la MEDIA sul perimetro allargato resti")
        print("   positiva: un singolo livello negativo non ribalta la conclusione.")
    else:
        print("Nessun contesto ha vantaggio negativo a nessuno dei livelli esaminati.")

    print()
    print("=" * 104)
    print("IL LIVELLO 0,50, primo escluso dalla soglia dichiarata")
    print("=" * 104)
    L = min(a.livelli, key=lambda x: abs(x - 0.50))
    print(f"{'contesto':10s} {'15 minuti':>22} {'media 4 orizzonti':>24}")
    for c, (tp, nome) in CONTESTI.items():
        semi = sorted({s for (cc, s) in D if cc == c})
        if len(semi) < a.semi:
            continue
        riga = []
        for orizz in (("15m",), ORIZZONTI):
            per_seme = []
            for s in semi:
                v = [van[(c, s, h, L)] for h in orizz]
                v = [x for x in v if np.isfinite(x)]
                if v:
                    per_seme.append(sum(v) / len(v))
            m, sd = st(per_seme)
            riga.append(f"{m:+13.1f}% ± {sd:5.1f}")
        print(f"{nome:10s} {riga[0]:>22} {riga[1]:>24}")

    print()
    print("Due avvertenze da riportare accanto ai numeri.")
    print("  La media fra livelli e' NON PESATA: ogni livello pesa uguale, benche' i")
    print("  punti di lavoro corrispondenti abbiano prevalenze molto diverse. Allargare")
    print("  il perimetro aumenta il peso relativo dei punti a bassa precisione.")
    print("  Ai richiami bassi entrambi i modelli predicono pochi positivi: la precisione")
    print("  vi e' alta per costruzione e le differenze relative si comprimono. Un")
    print("  vantaggio minore a 0,30 non significa che il modello sia peggiore li'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
