#!/usr/bin/env python3
"""
R1 — calibrazione, dissociazione metrica e incertezza (§8.2, Tabelle 24, 25, 26).
=================================================================================
Nessun addestramento: tutto si ricava dai dump di probabilita' gia' salvati.
Serve pero' che la campagna sia stata lanciata con `--dump-probs` E
`--dump-probs-val` su ENTRAMBI i rami, perche' la convenzione canonica stima
il calibratore sulla validazione.

Che cosa produce.

  Tabella 24 - R1 sotto tre convenzioni di calibrazione:
      * grezzo       : nessuno dei due rami calibrato;
      * dispiegabile : entrambi calibrati, calibratore stimato sulla
                       VALIDAZIONE. E' l'unico confronto simmetrico ed
                       eseguibile in esercizio, ed e' la misura canonica;
      * oracolo      : calibratore stimato sul TEST. Non produce un esito:
                       serve a misurare il termine di affidabilita' (§5.3.1).
    Il calibratore e' isotonico pesato, stimato per orizzonte e per classe
    vera, con `sample_weight` pari ai pesi di classe della metrica.

  Tabella 25 - R1 letto con tre metriche: entropia pesata, entropia NON
    pesata e F1-macro, accanto alla frequenza della classe critica. Sotto
    entropia non pesata il segno si inverte quasi ovunque. Se l'ampiezza
    dipendesse dalla difficolta' di apprendere una classe rara non
    cambierebbe segno cambiando il modo di pesare le classi in valutazione:
    la dipendenza e' quindi una proprieta' dello schema di pesatura, non
    dell'apprendibilita'.

  Tabella 26 - R1 con intervallo di ricampionamento congiunto di semi e
    blocchi di sensori. Richiede che i due rami operino sulla STESSA
    popolazione: sui contesti primari il riferimento va quindi preso dalla
    campagna a popolazione ristretta (§6.2.1), non da quella piena.

  Termine di affidabilita' per ramo, cioe' la caduta di entropia pesata
    prodotta dalla ricalibrazione. E' la grandezza su cui poggia
    l'affermazione che circa meta' del vantaggio del ramo neurale sia
    calibrazione del riferimento.

Uso (dalla radice OR3/):

    poetry run python analisi/r1_calibrazione.py
    poetry run python analisi/r1_calibrazione.py --tabelle 24 26
"""
from pathlib import Path
import argparse
import glob as globmod
import math

import numpy as np
from scipy.stats import spearmanr
from sklearn.isotonic import IsotonicRegression

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


# --------------------------------------------------------------- utilita' ---
def pesi(percorso: Path) -> np.ndarray:
    """w_k = n / (3 n_k) sulle frequenze del solo periodo di addestramento."""
    z = np.load(percorso, allow_pickle=True)
    C = z["congestion_emp"]
    T = C.shape[0]
    fr = np.array([(C[: int((T - 8) * 0.7)] == k).sum() for k in (1, 2, 3)], dtype=float)
    return (fr.sum() / (np.maximum(fr, 1) * 3)).astype("float64")


def blocchi(percorso: str, tag: str, K: int = 0):
    """Legge i quattro blocchi (uno per orizzonte) di un dump di probabilita'."""
    if not globmod.glob(percorso):
        return None
    z = np.load(percorso, allow_pickle=True)
    out = []
    for h in ORIZZONTI:
        chiavi = [k[3:] for k in z.files
                  if k.startswith("tag") and str(z[k]) == f"{tag}|{h}"]
        if not chiavi:
            return None
        i = chiavi[0]
        nodo = (z[f"idx{i}"] % K) if K else None
        out.append((z[f"p{i}"].astype("float32"), z[f"y{i}"].astype(int), nodo))
    return out


def wce(blocco, w, sel=None) -> float:
    v = []
    for P, Y, nodo in blocco:
        m = np.isin(nodo, sel) if sel is not None and nodo is not None else slice(None)
        yy, pp = Y[m], P[m]
        pt = np.clip(pp[np.arange(len(yy)), yy], 1e-7, 1)
        v.append(np.sum(w[yy] * -np.log(pt)) / np.sum(w[yy]))
    return float(np.mean(v))


def ce_non_pesata(blocco) -> float:
    v = []
    for P, Y, _ in blocco:
        pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1)
        v.append(np.mean(-np.log(pt)))
    return float(np.mean(v))


def f1_macro(blocco) -> float:
    v = []
    for P, Y, _ in blocco:
        pred = P.argmax(1)
        f = []
        for k in range(3):
            tp = np.sum((pred == k) & (Y == k))
            fp = np.sum((pred == k) & (Y != k))
            fn = np.sum((pred != k) & (Y == k))
            pr = tp / (tp + fp) if tp + fp else 0.0
            rc = tp / (tp + fn) if tp + fn else 0.0
            f.append(2 * pr * rc / (pr + rc) if pr + rc else 0.0)
        v.append(np.mean(f))
    return float(np.mean(v))


def calibra(blocco_stima, blocco_applica, w):
    """Isotonica pesata, per orizzonte e per classe vera. `blocco_stima` e'
    la validazione nella convenzione dispiegabile e il test in quella oracolo."""
    fuori = []
    for (Pv, Yv, _), (Pt, Yt, nodo) in zip(blocco_stima, blocco_applica):
        Q = np.empty((len(Pt), 3), dtype="float32")
        for k in range(3):
            ir = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
            ir.fit(Pv[:, k], (Yv == k).astype(float), sample_weight=w[Yv])
            Q[:, k] = ir.predict(Pt[:, k])
        Q = np.clip(Q, 1e-7, None)
        fuori.append((Q / Q.sum(1, keepdims=True), Yt, nodo))
    return fuori


def st(v):
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


# --------------------------------------------------------------- tabelle ----
def tabella_24(args):
    print("=" * 96)
    print("TABELLA 24 - R1 sotto tre convenzioni di calibrazione (cinque semi)")
    print("=" * 96)
    print(f"{'contesto':10s} | {'grezzo':>9} | {'dispiegabile (canonico)':>25} | {'oracolo':>9} | "
          f"{'affidabilita rete':>17} {'gbdt':>7}")
    for c, (tp, nome, K) in CONTESTI.items():
        if not tp.exists():
            print(f"{nome:10s} target non trovato")
            continue
        w = pesi(tp)
        gz, dp, orc, af_n, af_g = [], [], [], [], []
        for s in range(args.semi):
            nt = blocchi(f"{args.probsval}/nn_test_{c}_s{s}.npz", "gwn_none")
            nv = blocchi(f"{args.probsval}/nn_{c}_s{s}.npz", "gwn_none")
            gt = blocchi(f"{args.probsval}/gb_test_{c}_s{s}.npz", "lgb_fair")
            gv = blocchi(f"{args.probsval}/gb_{c}_s{s}.npz", "lgb_fair")
            if not all([nt, nv, gt, gv]):
                break
            n0, g0 = wce(nt, w), wce(gt, w)
            n1 = wce(calibra(nv, nt, w), w)
            g1 = wce(calibra(gv, gt, w), w)
            n2 = wce(calibra(nt, nt, w), w)
            g2 = wce(calibra(gt, gt, w), w)
            gz.append(100 * (g0 - n0) / g0)
            dp.append(100 * (g1 - n1) / g1)
            orc.append(100 * (g2 - n2) / g2)
            af_n.append(100 * (n0 - n1) / n0)
            af_g.append(100 * (g0 - g1) / g0)
        if len(gz) < args.semi:
            print(f"{nome:10s} dump incompleti ({len(gz)}/{args.semi}) — servono nn_/gb_ e nn_test_/gb_test_")
            continue
        md, sd = st(dp)
        print(f"{nome:10s} | {st(gz)[0]:+8.2f}% | {md:+11.2f}% ± {sd:5.2f}{'':6} | "
              f"{st(orc)[0]:+8.2f}% | {st(af_n)[0]:16.2f}% {st(af_g)[0]:6.2f}%")
    print("\nIl calibratore stimato sulla validazione si trasferisce al test: se le colonne")
    print("dispiegabile e oracolo coincidono entro pochi decimi, la mal-calibrazione del")
    print("riferimento e' un artefatto sistematico della perdita pesata, non una deriva")
    print("temporale. La colonna canonica e' la dispiegabile: e' l'unica in cui i due rami")
    print("ricevono lo stesso trattamento e in cui l'operazione e' eseguibile in esercizio.\n")


def tabella_25(args):
    print("=" * 96)
    print("TABELLA 25 - dipendenza di R1 dalla metrica di lettura")
    print("=" * 96)
    print(f"{'contesto':10s} {'rosso':>7} | {'R1 in wCE':>18} {'R1 in CE non pesata':>22} "
          f"{'R1 in F1-macro':>18}")
    righe = []
    for c, (tp, nome, K) in CONTESTI.items():
        if not tp.exists():
            continue
        w = pesi(tp)
        z = np.load(tp, allow_pickle=True)
        C = z["congestion_emp"]
        rosso = 100 * (C[C > 0] == 3).mean()
        a, b, d = [], [], []
        for s in range(args.semi):
            nt = blocchi(f"{args.probs}/classify_{c}_s{s}.npz", "gwn_none")
            gt = blocchi(f"{args.probs}/lgbristr_{c}_s{s}.npz", "lgb_fair")
            if not (nt and gt):
                break
            a.append(100 * (wce(gt, w) - wce(nt, w)) / wce(gt, w))
            b.append(100 * (ce_non_pesata(gt) - ce_non_pesata(nt)) / ce_non_pesata(gt))
            d.append(100 * (f1_macro(nt) - f1_macro(gt)) / f1_macro(gt))
        if len(a) < args.semi:
            print(f"{nome:10s} dump incompleti ({len(a)}/{args.semi})")
            continue
        q = lambda v: f"{st(v)[0]:+8.2f}% ± {st(v)[1]:5.2f}"
        print(f"{nome:10s} {rosso:6.2f}% | {q(a):>18} {q(b):>22} {q(d):>18}")
        righe.append((rosso, st(a)[0], st(b)[0], st(d)[0]))
    if len(righe) >= 4:
        r = np.array(righe)
        print(f"\ncorrelazione di rango con la frequenza della classe critica:")
        for j, eti in ((1, "wCE"), (2, "CE non pesata"), (3, "F1-macro")):
            print(f"  {eti:16s} {spearmanr(r[:, 0], r[:, j]).statistic:+.3f}")
        print("  (ordinamenti su sei contesti, non stime con incertezza)")
    print("\nSe l'ampiezza dipendesse dalla difficolta' di apprendere una classe rara, non")
    print("cambierebbe segno cambiando il modo di pesare le classi in VALUTAZIONE. La")
    print("dipendenza e' quindi una proprieta' dello schema di pesatura, e il vantaggio va")
    print("enunciato come condizionato alla scelta di pesare le classi.\n")


def tabella_26(args):
    rng = np.random.default_rng(0)
    print("=" * 96)
    print("TABELLA 26 - R1 grezzo con intervallo di ricampionamento a livello di dato")
    print("=" * 96)
    print(f"{'contesto':10s} {'celle':>11} | {'stima':>8} {'± semi':>7} | "
          f"{'IC 95%':>22} | soglia 10%")
    for c, (tp, nome, K) in CONTESTI.items():
        if not tp.exists():
            continue
        w = pesi(tp)
        D = {}
        for s in range(args.semi):
            nt = blocchi(f"{args.probs}/classify_{c}_s{s}.npz", "gwn_none", K)
            gt = blocchi(f"{args.probs}/lgbristr_{c}_s{s}.npz", "lgb_fair", K)
            if nt and gt:
                D[s] = (nt, gt)
        if len(D) < args.semi:
            print(f"{nome:10s} dump incompleti ({len(D)}/{args.semi}) — "
                  f"il riferimento deve venire dalla campagna a popolazione ristretta")
            continue
        primo = D[list(D)[0]]
        nodi = np.unique(primo[0][0][2])
        n_celle = len(primo[0][0][1])
        camp = [100 * (wce(D[s][1], w) - wce(D[s][0], w)) / wce(D[s][1], w) for s in D]
        rep = []
        for _ in range(args.repliche):
            s = list(D)[rng.integers(len(D))]
            sel = rng.choice(nodi, len(nodi), replace=True)
            g = wce(D[s][1], w, sel)
            rep.append(100 * (g - wce(D[s][0], w, sel)) / g)
        m, sd = st(camp)
        mr = float(np.mean(rep))
        lo = m + float(np.percentile(rep, 2.5)) - mr
        hi = m + float(np.percentile(rep, 97.5)) - mr
        esito = "superata" if lo > 10 else ("MANCATA" if hi < 10 else "attraversa")
        print(f"{nome:10s} {n_celle:11,} | {m:+7.2f}% {sd:7.2f} | "
              f"[{lo:+8.2f}; {hi:+8.2f}] | {esito}")
    print("\nL'ampiezza degli intervalli NON e' confrontabile fra righe: il numero di")
    print("sensori varia da 384 a 828 e la dispersione fra semi da 0,23 a 0,73.")
    print("Quando l'intervallo attraversa la soglia, il disegno non consente di")
    print("discriminare fra le due condizioni: e' la terza categoria di lettura di §7.3,")
    print("distinta tanto dal superamento quanto dal mancato superamento.\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="R1: calibrazione, metriche e incertezza")
    ap.add_argument("--probs", default="replication/probs",
                    help="dump di test della campagna appaiata")
    ap.add_argument("--probsval", default="replication/probsval",
                    help="dump di test e validazione della campagna di calibrazione")
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--repliche", type=int, default=300)
    ap.add_argument("--tabelle", nargs="*", default=["24", "25", "26"])
    args = ap.parse_args()

    if "24" in args.tabelle:
        tabella_24(args)
    if "25" in args.tabelle:
        tabella_25(args)
    if "26" in args.tabelle:
        tabella_26(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
