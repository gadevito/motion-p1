#!/usr/bin/env python3
"""
R3 — propagazione a rete incompleta (§8.3, Tabelle 28, 29 e scomposizione).
============================================================================
Nessun addestramento: tutto dai CSV e dai dump della campagna nel regime
severo, lanciata con `--inductive --no-coords --mask structured --obs-frac 0.4`
e `--modes none,fixed,adaptive`.

DUE MISURE, STATUTO DIVERSO E NON INTERCAMBIABILE.

  * variante a GRAFO DATO (`fixed`) — e' la misura DICHIARATA di R3. Non ha
    parametri indicizzati sul singolo nodo, quindi e' l'unica dispiegabile:
    il vincolo di §2.2 esclude vettori appresi per nodo su un tratto mai
    sensorizzato. E' quella che dimostra la tesi del regime rado.

  * variante ADATTIVA — e' un limite superiore NON dispiegabile. I vettori
    E1/E2 che generano l'adiacenza sono parametri per nodo e ricevono
    gradiente solo dai bersagli del periodo di addestramento: sono
    trasduttivi, non contaminati, ma non applicabili a sensori nuovi. Cio'
    che dimostrano e' che vettori appresi per nodo aiutano, che e' una tesi
    sull'IDENTITA' e non sulla propagazione.

Lo script riporta entrambe, etichettate, e non seleziona la piu' favorevole.

CHE COSA RICEVE LA VARIANTE PRIVA DI GRAFO. Per un nodo nascosto anche la
media storica del momento-tipo e' mascherata, con la stessa maschera di r,
flusso e occupazione. Quel ramo riceve quindi solo calendario, attributi
statici e flusso libero: e' una climatologia di citta' condizionata agli
attributi, non un predittore di quel nodo. Da qui la sua capacita' residua,
e R3 va letto in questa luce.

LETTURA IN RICHIAMO. Sui contesti a spire il bersaglio e' in larga parte
imposto dalla regola di strada vuota, ma nessuna cella imputata ha etichetta
diversa da verde (verificabile con `analisi/imputazione_gomo.py`): il
richiamo sulla classe critica e' quindi calcolato interamente su celle non
imputate. Su quella misura il punto di ARRIVO e' comune fra i contesti e il
punto di PARTENZA no: R3 misura quanto e' povero il modello privo di grafo,
non quanto e' ricco il grafo.

Uso (dalla radice OR3/):

    poetry run python analisi/r3_propagazione.py
    poetry run python analisi/r3_propagazione.py --sezioni tabella scomposizione
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
    "d8_2024":  (GOMO / "targets_2024_urb_d8.npz",  "d8/2024",   445),
    "d15_2024": (GOMO / "targets_2024_urb_d15.npz", "d15/2024",  384),
    "d8_2023":  (GOMO / "targets_2023_urb_d8.npz",  "d8/2023",   444),
    "t4cmad":   (T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",    "Madrid",    828),
    "t4clon":   (T4C / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",    "Londra",    774),
    "t4cmel":   (T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz", "Melbourne", 587),
}
FAMIGLIA = {"d8_2024": "spire", "d15_2024": "spire", "d8_2023": "spire",
            "t4cmad": "citta", "t4clon": "citta", "t4cmel": "citta"}


def st(v):
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


def serie(modelli, c, semi, schemi):
    """Per ciascun seme, la media sui quattro orizzonti di ogni modello richiesto.
    Restituisce None se un solo seme manca: le serie parziali non vanno mediate."""
    fuori = {m: [] for m in modelli}
    for s in range(semi):
        d = None
        for schema in schemi:
            f = globmod.glob(schema.format(c=c, s=s))
            if f:
                d = pd.read_csv(f[0])
                break
        if d is None:
            return None
        for m in modelli:
            q = d[d.model == m]
            if not len(q):
                return None
            fuori[m].append(q.wCE.mean())
    return fuori


def serie_richiamo(modelli, c, semi, schemi):
    fuori = {m: [] for m in modelli}
    for s in range(semi):
        d = None
        for schema in schemi:
            f = globmod.glob(schema.format(c=c, s=s))
            if f:
                d = pd.read_csv(f[0])
                break
        if d is None:
            return None
        for m in modelli:
            q = d[d.model == m]
            if not len(q) or "red_recall" not in q.columns:
                return None
            fuori[m].append(q.red_recall.mean())
    return fuori


# ------------------------------------------------------------------ blocchi --
def blocchi(percorso, tag, K):
    if not globmod.glob(percorso):
        return None
    z = np.load(percorso, allow_pickle=True)
    fuori = []
    for h in ORIZZONTI:
        ch = [k[3:] for k in z.files if k.startswith("tag") and str(z[k]) == f"{tag}|{h}"]
        if not ch:
            return None
        i = ch[0]
        fuori.append((z[f"p{i}"].astype("float32"), z[f"y{i}"].astype(int),
                      z[f"idx{i}"] % K))
    return fuori


def pesi(percorso):
    z = np.load(percorso, allow_pickle=True)
    C = z["congestion_emp"]
    T = C.shape[0]
    fr = np.array([(C[: int((T - 8) * 0.7)] == k).sum() for k in (1, 2, 3)], dtype=float)
    return (fr.sum() / (np.maximum(fr, 1) * 3)).astype("float64")


def wce(blocco, w, sel=None):
    v = []
    for P, Y, nodo in blocco:
        m = np.isin(nodo, sel) if sel is not None else slice(None)
        yy, pp = Y[m], P[m]
        pt = np.clip(pp[np.arange(len(yy)), yy], 1e-7, 1)
        v.append(np.sum(w[yy] * -np.log(pt)) / np.sum(w[yy]))
    return float(np.mean(v))


# ------------------------------------------------------------------ sezioni --
def sez_tabella(a):
    print("=" * 100)
    print("TABELLA 28 - R3 nel regime severo, entrambe le varianti")
    print("=" * 100)
    print(f"{'contesto':10s} | {'senza grafo':>16} | {'GRAFO DATO (dichiarata)':>32} | "
          f"{'adattiva (limite sup.)':>30}")
    for c, (tp, nome, K) in CONTESTI.items():
        d = serie(["gwn_none", "gwn_fixed", "gwn_adaptive"], c, a.semi, a.sparse)
        if d is None:
            d2 = serie(["gwn_none", "gwn_adaptive"], c, a.semi, a.sparse)
            if d2 is None:
                print(f"{nome:10s} CSV incompleti")
                continue
            n, ad = st(d2["gwn_none"]), st(d2["gwn_adaptive"])
            r = st([100 * (d2["gwn_none"][i] - d2["gwn_adaptive"][i]) / d2["gwn_none"][i]
                    for i in range(a.semi)])
            print(f"{nome:10s} | {n[0]:8.3f} ± {n[1]:5.3f} | "
                  f"{'braccio fixed assente':>32} | {ad[0]:8.3f} ± {ad[1]:5.3f}"
                  f"  {r[0]:+6.2f}%")
            continue
        n = st(d["gwn_none"])
        rf = st([100 * (d["gwn_none"][i] - d["gwn_fixed"][i]) / d["gwn_none"][i]
                 for i in range(a.semi)])
        ra = st([100 * (d["gwn_none"][i] - d["gwn_adaptive"][i]) / d["gwn_none"][i]
                 for i in range(a.semi)])
        f, ad = st(d["gwn_fixed"]), st(d["gwn_adaptive"])
        print(f"{nome:10s} | {n[0]:8.3f} ± {n[1]:5.3f} | "
              f"{f[0]:8.3f} ± {f[1]:5.3f}  {rf[0]:+7.2f}% ± {rf[1]:4.2f} | "
              f"{ad[0]:8.3f} ± {ad[1]:5.3f}  {ra[0]:+6.2f}%")
    print("\nLa misura DICHIARATA di R3 e' la colonna a grafo dato: e' l'unica dispiegabile,")
    print("perche' non ha parametri indicizzati sul singolo nodo. La colonna adattiva e' un")
    print("limite superiore trasduttivo, e cio' che dimostra e' che vettori appresi per nodo")
    print("aiutano — una tesi sull'identita', non sulla propagazione.\n")


def sez_richiamo(a):
    print("=" * 100)
    print("TABELLA 29 - R3 letto in richiamo sulla classe critica")
    print("=" * 100)
    print("Prerequisito: nessuna cella imputata ha etichetta diversa da verde.")
    print("Verificarlo con  poetry run python analisi/imputazione_gomo.py\n")
    print(f"{'contesto':10s} {'famiglia':9s} | {'senza grafo':>12} {'con grafo':>11} | "
          f"{'differenza':>20}")
    per_fam = {"spire": [], "citta": []}
    for c, (tp, nome, K) in CONTESTI.items():
        d = serie_richiamo(["gwn_none", "gwn_adaptive"], c, a.semi, a.sparse)
        if d is None:
            print(f"{nome:10s} CSV incompleti o privi di red_recall")
            continue
        diff = [d["gwn_adaptive"][i] - d["gwn_none"][i] for i in range(a.semi)]
        m, sd = st(diff)
        per_fam[FAMIGLIA[c]].append(m)
        print(f"{nome:10s} {FAMIGLIA[c]:9s} | {st(d['gwn_none'])[0]:12.3f} "
              f"{st(d['gwn_adaptive'])[0]:11.3f} | {m:+11.4f} ± {sd:6.4f}")
    if all(per_fam.values()):
        ms, mc = np.mean(per_fam["spire"]), np.mean(per_fam["citta"])
        print(f"\nmedia per famiglia: spire {ms:+.4f}  citta {mc:+.4f}  "
              f"rapporto {ms / max(mc, 1e-9):.1f}x")
    print("\nIl punto di ARRIVO e' comune fra i contesti, il punto di PARTENZA no: il divario")
    print("sta interamente nella partenza. R3 misura quindi quanto e' povero il modello privo")
    print("di grafo, non quanto e' ricco il grafo — coerente con cio' che quel modello riceve")
    print("per un nodo nascosto, cioe' una climatologia di citta' condizionata agli attributi.\n")


def sez_scomposizione(a):
    print("=" * 100)
    print("SCOMPOSIZIONE - propagazione su grafo dato contro componente adattiva")
    print("=" * 100)
    print("Su scala di skill = 1 - wCE/ln3, dove i guadagni sono SOMMABILI perche' la")
    print("scala e' affine nella wCE: skill(b) - skill(a) = (wCE_a - wCE_b)/ln3.\n")
    L3 = float(np.log(3))
    print(f"{'contesto':10s} | {'senza grafo':>11} {'grafo dato':>11} {'adattiva':>9} | "
          f"{'none->fixed':>12} {'fixed->adatt':>13}")
    for c, (tp, nome, K) in CONTESTI.items():
        d = serie(["gwn_none", "gwn_fixed", "gwn_adaptive"], c, a.semi, a.sparse)
        if d is None:
            print(f"{nome:10s} braccio fixed assente: rieseguire con --modes none,fixed,adaptive")
            continue
        sk = {k: 100 * (1 - st(v)[0] / L3) for k, v in d.items()}
        print(f"{nome:10s} | {sk['gwn_none']:10.1f}% {sk['gwn_fixed']:10.1f}% "
              f"{sk['gwn_adaptive']:8.1f}% | {sk['gwn_fixed'] - sk['gwn_none']:+11.1f} "
              f"{sk['gwn_adaptive'] - sk['gwn_fixed']:+13.1f}")
    print("\nI tre bracci vanno prodotti nella STESSA invocazione (--modes none,fixed,adaptive).")
    print("Confrontare bracci di esecuzioni separate fa entrare nella differenza anche la")
    print("versione dello script, oltre all'effetto studiato (§7.3).\n")


def sez_intervalli(a):
    rng = np.random.default_rng(0)
    print("=" * 100)
    print("INTERVALLI DI RICAMPIONAMENTO sulla variante a GRAFO DATO")
    print("=" * 100)
    print(f"{'contesto':10s} {'celle':>11} | {'stima':>8} | {'IC 95%':>22} | soglia 10%")
    for c, (tp, nome, K) in CONTESTI.items():
        if not tp.exists():
            continue
        w = pesi(tp)
        D = {}
        for s in range(a.semi):
            for schema in a.dump:
                nb = blocchi(schema.format(c=c, s=s), "gwn_none", K)
                fb = blocchi(schema.format(c=c, s=s), "gwn_fixed", K)
                if nb and fb:
                    D[s] = (nb, fb)
                    break
        if len(D) < a.semi:
            print(f"{nome:10s} dump incompleti ({len(D)}/{a.semi}) — servono i blocchi "
                  f"gwn_none E gwn_fixed nello stesso npz")
            continue
        primo = D[list(D)[0]]
        nodi = np.unique(primo[0][0][2])
        camp = [100 * (wce(D[s][0], w) - wce(D[s][1], w)) / wce(D[s][0], w) for s in D]
        rep = []
        for _ in range(a.repliche):
            s = list(D)[rng.integers(len(D))]
            sel = rng.choice(nodi, len(nodi), replace=True)
            n = wce(D[s][0], w, sel)
            rep.append(100 * (n - wce(D[s][1], w, sel)) / n)
        m = float(np.mean(camp))
        mr = float(np.mean(rep))
        lo = m + float(np.percentile(rep, 2.5)) - mr
        hi = m + float(np.percentile(rep, 97.5)) - mr
        esito = ("superata" if lo > 10 else "MANCATA" if hi < 10 else "non decidibile")
        if lo < 0 < hi:
            esito += ", compatibile con zero"
        print(f"{nome:10s} {len(primo[0][0][1]):11,} | {m:+7.2f}% | "
              f"[{lo:+8.2f}; {hi:+8.2f}] | {esito}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description="R3: propagazione nel regime severo")
    ap.add_argument("--sparse", nargs="*", default=[
        "replication/fix_sparse_{c}_s{s}.csv",
        "replication/camp_sparse_{c}_s{s}.csv",
        "replication/sparse_{c}_s{s}.csv"],
        help="schemi dei CSV, provati in ordine")
    ap.add_argument("--dump", nargs="*", default=[
        "replication/probs/fix_sparse_{c}_s{s}.npz",
        "replication/probs/sparse_{c}_s{s}.npz"])
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--repliche", type=int, default=300)
    ap.add_argument("--sezioni", nargs="*",
                    default=["tabella", "richiamo", "scomposizione", "intervalli"])
    a = ap.parse_args()

    if "tabella" in a.sezioni:
        sez_tabella(a)
    if "richiamo" in a.sezioni:
        sez_richiamo(a)
    if "scomposizione" in a.sezioni:
        sez_scomposizione(a)
    if "intervalli" in a.sezioni:
        sez_intervalli(a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
