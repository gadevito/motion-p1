#!/usr/bin/env python3
"""
Priore storico di classe, con e senza calibrazione (§8.1, Tabella 21).
======================================================================
Nessun addestramento: il priore e' un riferimento non addestrato e si
ricostruisce dai soli target.

Per ciascun sensore e ciascuno dei 672 momenti-tipo della settimana
(7 giorni x 96 intervalli) si stima la distribuzione storica delle tre
classi sul solo periodo di ADDESTRAMENTO, e la si usa come previsione per
quel momento-tipo. Le due varianti differiscono per come la distribuzione
e' convertita in probabilita':

  * Laplace, alpha = 1 : (conteggi + 1) normalizzati. E' la frequenza
    empirica lisciata, che minimizza l'entropia NON pesata.
  * calibrata          : (conteggi + 1) moltiplicati per i pesi di classe
    e poi normalizzati, cioe' p ~ w * f. E' l'argmin dell'entropia PESATA,
    ed e' la stessa correzione applicata ai cinque interpolatori spaziali
    di §6.1.

L'asimmetria conta: il priore e' l'unico riferimento della suite a non
essere calibrato rispetto alla metrica su cui viene giudicato, ed e' anche
il piu' informato, perche' usa la storia del nodo da prevedere. Senza
calibrazione risulta peggiore del predittore uniforme in cinque contesti
su sei; con la calibrazione lo batte in tutti e sei. La differenza e'
calibrazione, non informazione.

Nota su §5.2. Il teorema di §5.2 dice che, sotto pesi inversamente
proporzionali alla frequenza, un predittore che riproduce le frequenze
storiche e' necessariamente peggiore del predittore uniforme. La versione
calibrata NON riproduce piu' quelle frequenze: il teorema non spiegava
quindi il risultato empirico sul priore, lo produceva.

Uso (dalla radice OR3/):

    poetry run python analisi/priore_calibrato.py
"""
from pathlib import Path
import argparse

import numpy as np
import pandas as pd

BASE = Path("data_collection")
GOMO = BASE / "go-mo" / "gomo"
T4C = BASE / "traffic4cast"

CONTESTI = {
    "d8/2024":   GOMO / "targets_2024_urb_d8.npz",
    "d15/2024":  GOMO / "targets_2024_urb_d15.npz",
    "d8/2023":   GOMO / "targets_2023_urb_d8.npz",
    "Madrid":    T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "Melbourne": T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
    "Londra":    T4C / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
}
ORIZZONTI = (1, 2, 4, 8)          # 15, 30, 60, 120 minuti
ORIZZONTE_MAX = 8
QUOTA_ADDESTRAMENTO = 0.7
N_SLOT = 672                       # 7 giorni x 96 intervalli da 15 minuti


def slot_settimanale(ts) -> np.ndarray:
    return (ts.dayofweek.to_numpy() * 96
            + ts.hour.to_numpy() * 4
            + ts.minute.to_numpy() // 15)


def pesi_classe(C, tr) -> np.ndarray:
    """w_k = n / (3 n_k) sulle frequenze del solo addestramento."""
    fr = np.array([(C[tr] == k).sum() for k in (1, 2, 3)], dtype=float)
    return (fr.sum() / (np.maximum(fr, 1) * 3)).astype("float64")


def conta_priore(C, tr, slot, K) -> np.ndarray:
    """Conteggi (K, 672, 3) delle classi osservate in addestramento."""
    hp = np.zeros((K, N_SLOT, 3), dtype="float64")
    for k in range(3):
        righe, colonne = np.where(C[tr] == k + 1)
        np.add.at(hp[:, :, k], (colonne, slot[tr][righe]), 1.0)
    return hp


def valuta(tab, C, te, slot, w):
    """Entropia pesata e richiamo sulla classe critica, mediati sugli orizzonti."""
    wce, rec = [], []
    for h in ORIZZONTI:
        Y = np.where(C[te + h] > 0, C[te + h] - 1, -1)
        P = tab[:, slot[te + h], :].transpose(1, 0, 2)
        Pf, Yf = P.reshape(-1, 3), Y.reshape(-1)
        ok = Yf >= 0
        Pf, Yf = Pf[ok], Yf[ok]
        pt = np.clip(Pf[np.arange(len(Yf)), Yf], 1e-7, 1)
        wce.append(float(np.sum(w[Yf] * -np.log(pt)) / np.sum(w[Yf])))
        pred = Pf.argmax(1)
        rec.append(float(np.sum((pred == 2) & (Yf == 2)) / max(np.sum(Yf == 2), 1)))
    return float(np.mean(wce)), float(np.mean(rec))


def main() -> int:
    ap = argparse.ArgumentParser(description="priore storico con e senza calibrazione")
    ap.add_argument("--alpha", type=float, default=1.0, help="lisciatura di Laplace")
    args = ap.parse_args()

    uniforme = float(np.log(3))
    print(f"{'contesto':10s} | {'Laplace a=%.0f' % args.alpha:>22} | "
          f"{'calibrato p ~ w*f':>22} | {'uniforme':>9} | rosso")
    print(f"{'':10s} | {'wCE':>10} {'richiamo':>11} | {'wCE':>10} {'richiamo':>11} | "
          f"{'wCE':>9} |")

    for nome, p in CONTESTI.items():
        if not p.exists():
            print(f"{nome:10s} target non trovato: {p}")
            continue
        z = np.load(p, allow_pickle=True)
        C = z["congestion_emp"]
        ts = pd.to_datetime(z["timestamps"])
        T, K = C.shape
        slot = slot_settimanale(ts)
        n_start = T - ORIZZONTE_MAX
        tr = slice(0, int(n_start * QUOTA_ADDESTRAMENTO))
        te = np.arange(int(n_start * 0.8), n_start)

        w = pesi_classe(C, tr)
        hp = conta_priore(C, tr, slot, K)

        lap = (hp + args.alpha) / (hp.sum(-1, keepdims=True) + 3 * args.alpha)
        cal = (hp + args.alpha) * w[None, None, :]
        cal = cal / cal.sum(-1, keepdims=True)

        a = valuta(lap, C, te, slot, w)
        b = valuta(cal, C, te, slot, w)
        rosso = 100 * (C[C > 0] == 3).mean()
        print(f"{nome:10s} | {a[0]:10.4f} {a[1]:11.4f} | {b[0]:10.4f} {b[1]:11.4f} | "
              f"{uniforme:9.4f} | {rosso:5.2f}%")

    print()
    print("Lettura. La calibrazione corregge una distorsione che CRESCE con lo")
    print("sbilanciamento della distribuzione. Sul contesto con la classe critica piu'")
    print("frequente (Londra, 15,2%) la correzione peggiora leggermente il priore: e' il")
    print("comportamento atteso della procedura all'estremo bilanciato, non un'eccezione,")
    print("e vale identicamente per i cinque interpolatori spaziali che la ricevono.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
