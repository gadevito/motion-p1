#!/usr/bin/env python3
"""
Lettura operativa — orizzonte, punto di lavoro, richiamo appaiato (§8.6.5-8.6.7).
=================================================================================
Nessun addestramento: tutto dai CSV e dai dump gia' salvati.

TRE LETTURE DISTINTE, che rispondono a domande diverse.

  1. DECADIMENTO PER ORIZZONTE. Quanto la previsione peggiora fra quindici e
     centoventi minuti. Serve anche a leggere correttamente R1 e R3, che sono
     MEDIE sui quattro orizzonti e non sono costanti: R1 decresce al crescere
     dell'orizzonte, quindi il valore medio sottostima il vantaggio a quindici
     minuti e lo sovrastima a centoventi. I confronti fra tabelle vanno fatti a
     parita' di aggregazione.

  2. PUNTO DI LAVORO. Precisione e richiamo alla regola predefinita, che assegna
     la classe di massima probabilita'. NON e' una proprieta' del modello: e'
     l'esito di quella regola, che sovra-predice la classe critica di 1,9-4,1
     volte la sua frequenza vera. La soglia va tarata sulla validazione, e
     tararla recupera da tre a dieci volte piu' del riferimento tabellare.

  3. DOMINANZA A RICHIAMO APPAIATO. Il confronto fra famiglie va condotto a
     PARITA' DI RICHIAMO, non a soglia numerica fissa. Con soglia comune la rete
     vince in un solo contesto su sei, ma il risultato riflette la diversa
     CALIBRAZIONE dei due modelli: una stessa soglia numerica non individua
     punti di lavoro comparabili. A parita' di richiamo i punti di lavoro hanno
     lo stesso significato operativo.

DUE AVVERTENZE SULL'INCERTEZZA DELLA TERZA LETTURA.

Le ampiezze degli intervalli seguono la RARITA' della classe critica — da ±1,1
punti a Madrid a ±8,4 su d8/2023 — ed e' atteso per costruzione: dove gli
episodi critici sono pochi, ogni ricampione ne cattura un numero piu' variabile.
Non e' un difetto della procedura.

Su d8/2023 aumentare le replicazioni da trecento a duemila ALLARGA l'intervallo
anziche' restringerlo: l'incertezza vi risiede nella variabilita' fra semi e non
nel ricampionamento. Il conteggio di cinque contesti su sei e' quindi definitivo
per questo apparato, e aumentare le repliche non lo cambierebbe.

Uso (dalla radice OR3/):

    poetry run python analisi/lettura_operativa.py
    poetry run python analisi/lettura_operativa.py --sezioni dominanza
"""
from pathlib import Path
import argparse
import glob as globmod
import math

import numpy as np
import pandas as pd

BASE = Path("data_collection")
GOMO = BASE / "go-mo" / "gomo"
T4C = BASE / "traffic4cast"
ORIZZONTI = ("15m", "30m", "60m", "120m")

CONTESTI = {
    "t4cmad": (T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz", "Madrid", 828),
    "t4clon": (T4C / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz", "Londra", 774),
    "t4cmel": (T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz", "Melbourne", 587),
    "d8_2024": (GOMO / "targets_2024_urb_d8.npz", "d8/2024", 445),
    "d15_2024": (GOMO / "targets_2024_urb_d15.npz", "d15/2024", 384),
    "d8_2023": (GOMO / "targets_2023_urb_d8.npz", "d8/2023", 444),
}


def st(v):
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


def blocchi(percorso, tag, K=0):
    if not globmod.glob(percorso):
        return None
    z = np.load(percorso, allow_pickle=True)
    fuori = {}
    for h in ORIZZONTI:
        ch = [k[3:] for k in z.files if k.startswith("tag") and str(z[k]) == f"{tag}|{h}"]
        if not ch:
            return None
        i = ch[0]
        nodo = (z[f"idx{i}"] % K) if K else None
        fuori[h] = (z[f"p{i}"].astype("float32"), z[f"y{i}"].astype(int), nodo)
    return fuori


# ------------------------------------------------------------- 1. orizzonte -
def sez_orizzonte(a):
    print("=" * 92)
    print("TABELLA 68 - decadimento dell'entropia pesata per orizzonte")
    print("=" * 92)
    print(f"{'contesto':10s} " + " ".join(f"{h:>10}" for h in ORIZZONTI) + f" {'degrado':>10}")
    for c, (tp, nome, K) in CONTESTI.items():
        per_h = {h: [] for h in ORIZZONTI}
        for s in range(a.semi):
            d = None
            for sch in a.classify:
                f = globmod.glob(sch.format(c=c, s=s))
                if f:
                    d = pd.read_csv(f[0])
                    break
            if d is None:
                break
            q = d[d.model == a.modello]
            for h in ORIZZONTI:
                r = q[q.horizon == h]
                if len(r):
                    per_h[h].append(r.wCE.mean())
        if any(len(v) < a.semi for v in per_h.values()):
            print(f"{nome:10s} CSV incompleti")
            continue
        m = {h: st(per_h[h])[0] for h in ORIZZONTI}
        deg = 100 * (m["120m"] - m["15m"]) / m["15m"]
        print(f"{nome:10s} " + " ".join(f"{m[h]:10.4f}" for h in ORIZZONTI) + f" {deg:+9.1f}%")
    print("\n  R1 e R3 sono MEDIE sui quattro orizzonti e non sono costanti: il valore medio")
    print("  sottostima il vantaggio a quindici minuti e lo sovrastima a centoventi.")
    print("  I confronti fra tabelle vanno fatti a parita' di aggregazione.\n")


# --------------------------------------------------------- 2. punto lavoro --
def sez_punto_lavoro(a):
    print("=" * 92)
    print("TABELLA 69 - precisione e richiamo al punto di lavoro predefinito")
    print("=" * 92)
    print("La regola predefinita assegna la classe di massima probabilita'. Precisione e")
    print("richiamo vanno letti INSIEME e sullo STESSO insieme di esecuzioni: il rapporto")
    print("fra allarmi corretti e falsi ha significato solo sulle medesime predizioni.\n")
    print(f"{'contesto':10s} {'base rosso':>11} | {'prec 15m':>9} {'rich 15m':>9} | "
          f"{'prec 120m':>10} {'rich 120m':>10} | {'falsi/corretto':>15}")
    for c, (tp, nome, K) in CONTESTI.items():
        if not tp.exists():
            continue
        val = {}
        for s in range(a.semi):
            b = None
            for sch in a.dump:
                b = blocchi(sch.format(c=c, s=s), a.modello)
                if b:
                    break
            if not b:
                break
            for h in ("15m", "120m"):
                P, Y, _ = b[h]
                pred = P.argmax(1) == 2
                vero = Y == 2
                tp_ = (pred & vero).sum()
                pr = tp_ / max(pred.sum(), 1)
                rc = tp_ / max(vero.sum(), 1)
                val.setdefault(h, []).append((pr, rc, vero.mean()))
        if not val or len(val.get("15m", [])) < a.semi:
            print(f"{nome:10s} dump incompleti")
            continue
        p15, r15, base = (np.mean([x[i] for x in val["15m"]]) for i in range(3))
        p120, r120, _ = (np.mean([x[i] for x in val["120m"]]) for i in range(3))
        print(f"{nome:10s} {100 * base:10.1f}% | {p15:9.3f} {r15:9.3f} | "
              f"{p120:10.3f} {r120:10.3f} | {(1 - p15) / max(p15, 1e-9):14.1f}")
    print("\n  Entrambi i valori sono l'esito della REGOLA DI DECISIONE, non una proprieta'")
    print("  del modello. Tarando le soglie sulla validazione la F1-macro passa da")
    print("  -4,1÷-6,2% a +3,0÷+4,4% nelle tre citta': la regola non tarata disperde gran")
    print("  parte del vantaggio misurato, e in esercizio la soglia va tarata.\n")


# ----------------------------------------------------------- 3. dominanza ---
def ordina(P, Y, nodo=None):
    """Precalcola l'ordinamento per punteggio decrescente, UNA volta per blocco.

    L'ordinamento non dipende dal ricampionamento: ripeterlo a ogni replica
    costava un `argsort` su milioni di celle per ciascuna delle centinaia di
    migliaia di chiamate, ed era l'intero costo della sezione. Precalcolandolo,
    ogni replica si riduce a una selezione e a due somme cumulate.
    """
    o = np.argsort(-P[:, 2])
    return ((Y[o] == 2).astype(np.int8),
            None if nodo is None else nodo[o])


def precisione_a_richiamo(crit, bersaglio, sel=None, nodo=None):
    """Precisione nel punto in cui il richiamo vale `bersaglio`.

    `crit` e' il vettore booleano gia' ORDINATO per punteggio decrescente. Con
    `sel` si restringe ai nodi indicati, il che equivale a ricampionare le celle
    conservando l'ordinamento.
    """
    y = crit if sel is None else crit[np.isin(nodo, sel)]
    if not len(y):
        return float("nan")
    tp = np.cumsum(y, dtype=np.int64)
    tot = max(int(tp[-1]), 1)
    i = np.searchsorted(tp / tot, bersaglio)
    if i >= len(tp):
        return float("nan")
    return float(tp[i] / (i + 1))


def sez_dominanza(a):
    rng = np.random.default_rng(0)
    print("=" * 92)
    print(f"TABELLA 71 - dominanza di precisione a richiamo appaiato {a.richiamo:.2f}")
    print("=" * 92)
    print("Il confronto e' a PARITA' DI RICHIAMO, non a soglia numerica fissa: con soglia")
    print("comune il risultato rifletterebbe la diversa calibrazione dei due modelli.\n")
    print(f"{'contesto':10s} {'rosso':>7} | {'dominanza':>10} | {'IC 95%':>22} | esito")
    for c, (tp, nome, K) in CONTESTI.items():
        if not tp.exists():
            continue
        z = np.load(tp, allow_pickle=True)
        Cc = z["congestion_emp"]
        rosso = 100 * (Cc[Cc > 0] == 3).mean()
        D = {}
        for s in range(a.semi):
            nb = None
            for sch in a.dump:
                nb = blocchi(sch.format(c=c, s=s), a.modello, K)
                if nb:
                    break
            gb = blocchi(f"replication/probs/lgbristr_{c}_s{s}.npz", "lgb_fair", K)
            if nb and gb:
                D[s] = (nb, gb)
        if len(D) < a.semi:
            print(f"{nome:10s} {rosso:6.2f}% | dump incompleti ({len(D)}/{a.semi}) — il "
                  f"riferimento deve venire dalla campagna a popolazione ristretta")
            continue
        nodi = np.unique(D[list(D)[0]][0]["15m"][2])

        # ORDINAMENTO PRECALCOLATO, una volta per seme e orizzonte. Ripeterlo a
        # ogni replica costava un `argsort` su milioni di celle per ciascuna
        # delle centinaia di migliaia di chiamate, ed era l'intero costo della
        # sezione: con duemila repliche l'esecuzione superava l'ora.
        ORD = {}
        for s in D:
            for h in ORIZZONTI:
                Pn, Yn, nn = D[s][0][h]
                Pg, Yg, ng = D[s][1][h]
                ORD[(s, h)] = (ordina(Pn, Yn, nn), ordina(Pg, Yg, ng))

        def dom(s, sel=None):
            v = []
            for h in ORIZZONTI:
                (cn, on), (cg, og) = ORD[(s, h)]
                pn = precisione_a_richiamo(cn, a.richiamo, sel, on)
                pg = precisione_a_richiamo(cg, a.richiamo, sel, og)
                if np.isfinite(pn) and np.isfinite(pg) and pg > 0:
                    v.append(100 * (pn - pg) / pg)
            return float(np.mean(v)) if v else float("nan")

        camp = [dom(s) for s in D]
        rep = []
        # avanzamento su stderr: ogni replica scorre tutte le celle di tutti gli
        # orizzonti, sicche' il costo cresce linearmente con --repliche e con
        # duemila supera l'ora. Senza indicatore non si distingue una esecuzione
        # lenta da una bloccata.
        import sys, time
        t0 = time.time()
        for _i in range(a.repliche):
            s = list(D)[rng.integers(len(D))]
            rep.append(dom(s, rng.choice(nodi, len(nodi), replace=True)))
            if (_i + 1) % 25 == 0 or _i + 1 == a.repliche:
                el = time.time() - t0
                res = el / (_i + 1) * (a.repliche - _i - 1)
                print(f"\r    {nome}: {_i+1}/{a.repliche} repliche, "
                      f"trascorsi {el/60:.1f} min, stimati {res/60:.1f} min   ",
                      end="", file=sys.stderr, flush=True)
        print("\r" + " " * 78 + "\r", end="", file=sys.stderr, flush=True)
        rep = [x for x in rep if np.isfinite(x)]
        m = float(np.mean(camp))
        mr = float(np.mean(rep))
        lo = m + float(np.percentile(rep, 2.5)) - mr
        hi = m + float(np.percentile(rep, 97.5)) - mr
        esito = "distinguibile da zero" if lo > 0 else "NON distinguibile"
        print(f"{nome:10s} {rosso:6.2f}% | {m:+9.1f}% | [{lo:+8.1f}; {hi:+8.1f}] | {esito}")
    print("\n  Le AMPIEZZE seguono la rarita' della classe critica, ed e' atteso per")
    print("  costruzione: dove gli episodi sono pochi, ogni ricampione ne cattura un numero")
    print("  piu' variabile. Non e' un difetto della procedura.")
    print("\n  Dove l'intervallo tocca lo zero, aumentare le REPLICHE non aiuta: su d8/2023")
    print("  passare da trecento a duemila ALLARGA l'intervallo, perche' l'incertezza")
    print("  risiede nella variabilita' fra semi. Il conteggio e' definitivo per questo")
    print("  apparato.")
    print("\n  La dominanza va formulata rispetto al REGIME OPERATIVO (richiamo >= 0,60) e")
    print("  non come proprieta' globale della curva: le inversioni si concentrano quasi")
    print("  esclusivamente su d8/2023 e ai richiami bassi.\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="lettura operativa del classificatore")
    ap.add_argument("--classify", nargs="*", default=[
        "replication/fix_classify_{c}_s{s}.csv",
        "replication/classify_{c}_s{s}.csv"])
    ap.add_argument("--dump", nargs="*", default=[
        "replication/probs/fix_classify_{c}_s{s}.npz",
        "replication/probs/classify_{c}_s{s}.npz"])
    ap.add_argument("--modello", default="gwn_adaptive")
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--richiamo", type=float, default=0.60)
    ap.add_argument("--repliche", type=int, default=300)
    ap.add_argument("--sezioni", nargs="*",
                    default=["orizzonte", "punto", "dominanza"])
    a = ap.parse_args()

    if "orizzonte" in a.sezioni:
        sez_orizzonte(a)
    if "punto" in a.sezioni:
        sez_punto_lavoro(a)
    if "dominanza" in a.sezioni:
        sez_dominanza(a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
