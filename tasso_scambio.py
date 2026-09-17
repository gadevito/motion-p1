#!/usr/bin/env python3
"""
Tasso di scambio fra richiamo ed entropia pesata, stimato dal priore storico.
=============================================================================
Nessun addestramento: il priore di classe si calcola dai soli bersagli.

CHE COSA STIMA. Quanto richiamo sulla classe critica si guadagna per ogni punto
percentuale di entropia pesata, sotto uno spostamento infinitesimo della
distribuzione predittiva. E' la quantificazione che il margine di equivalenza di
±3% presuppone, e che oggi proviene dai risultati: qui si ottiene PRIMA di
addestrare alcunche', quindi indipendentemente da essi.

COME. Si perturba il logaritmo della probabilita' della classe critica di una
quantita' `eps` e si misurano le due variazioni:

  d(entropia pesata)  al primo ordine vale, a meno del fattore di
                      normalizzazione, la somma di -w_c(1-p_c) sulle celle
                      critiche e di +w_y p_c sulle altre. I due termini si
                      COMPENSANO quasi esattamente quando il prodotto fra peso e
                      frequenza e' costante, che e' la convenzione adottata: e'
                      l'argomento strutturale del disegno, qui verificato
                      numericamente anziche' asserito.

  d(richiamo)         dipende dalla sola DENSITA' del margine decisionale
                      m = p_c - max(p_altre) in prossimita' dello zero: solo le
                      celle prossime alla soglia cambiano classificazione. E' la
                      grandezza che il priore consente di stimare senza
                      addestrare.

PERCHE' LA STIMA E' CONSERVATIVA. Il priore e' molto piu' disperso di un modello
addestrato: assegna alla stessa combinazione di sensore e momento-tipo la
medesima distribuzione, quindi concentra massa vicino alla soglia. Ne discende
che SOVRASTIMA la variazione di richiamo per punto di entropia. Se anche con
questa sovrastima il tasso resta sotto un episodio su cento, il margine e'
giustificato a priori, e lo e' in senso conservativo.

DUE COSE CHE LO SCRIPT RIPORTA E CHE VANNO LETTE INSIEME AL NUMERO. Il valore
per ciascun contesto, perche' la densita' alla soglia dipende dalla
distribuzione delle classi e i contesti differiscono molto. E la stabilita'
rispetto ad `eps`: se il tasso varia molto al variare della perturbazione, la
derivata non e' ben definita e il numero non va usato.

Uso (dalla radice OR3/):

    poetry run python tasso_scambio.py
    poetry run python tasso_scambio.py --eps 0.02 0.05 0.10 0.20
"""
from pathlib import Path
import argparse

import numpy as np

BASE = Path("data_collection")
GOMO = BASE / "go-mo" / "gomo"
T4C = BASE / "traffic4cast"
CONTESTI = {
    "t4cmad": (T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz", "Madrid"),
    "t4clon": (T4C / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz", "Londra"),
    "t4cmel": (T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz", "Melbourne"),
    "d8_2024": (GOMO / "targets_2024_urb_d8.npz", "d8/2024"),
    "d15_2024": (GOMO / "targets_2024_urb_d15.npz", "d15/2024"),
    "d8_2023": (GOMO / "targets_2023_urb_d8.npz", "d8/2023"),
}


def priore(percorso: Path, alpha: float, quota_tr: float):
    """Distribuzione delle tre classi per sensore e momento-tipo, stimata sul
    solo insieme di addestramento con lisciatura di Laplace.

    Il momento-tipo e' la coppia (giorno della settimana, ora): e' la
    granularita' che cattura sia il ciclo giornaliero sia la distinzione fra
    feriale e festivo senza frammentare eccessivamente il campione.
    """
    z = np.load(percorso, allow_pickle=True)
    C = z["congestion_emp"]                      # (T, K) con valori 1, 2, 3 e -1
    ts = z["timestamps"]
    T, K = C.shape
    n_tr = int((T - 8) * quota_tr)

    import pandas as pd
    s = pd.to_datetime(ts)
    bucket = (s.dayofweek * 24 + s.hour).to_numpy()
    NB = 7 * 24

    conta = np.full((K, NB, 3), alpha, dtype="float64")
    for t in range(n_tr):
        b = bucket[t]
        c = C[t]
        for k in (1, 2, 3):
            conta[c == k, b, k - 1] += 1
    P = conta / conta.sum(2, keepdims=True)      # priore normalizzato

    # celle del periodo di prova
    n_te = int((T - 8) * 0.85)
    righe, col = np.where(C[n_te:] > 0)
    y = C[n_te:][righe, col] - 1                 # 0, 1, 2
    p = P[col, bucket[n_te:][righe]]
    fr = np.array([(C[:n_tr] == k).sum() for k in (1, 2, 3)], float)
    w = fr.sum() / (np.maximum(fr, 1) * 3)
    return p, y, w


def misure(p, y, w, eps=0.0):
    """Entropia pesata e richiamo dopo uno spostamento `eps` del logaritmo
    della probabilita' della classe critica."""
    q = p.copy()
    if eps:
        q = q * np.array([1.0, 1.0, np.exp(eps)])
        q = q / q.sum(1, keepdims=True)
    pt = np.clip(q[np.arange(len(y)), y], 1e-12, 1)
    ce = float(np.sum(w[y] * -np.log(pt)) / np.sum(w[y]))
    crit = (y == 2)
    rec = float(((q.argmax(1) == 2) & crit).sum() / max(crit.sum(), 1))
    return ce, rec


def main() -> int:
    ap = argparse.ArgumentParser(description="tasso di scambio richiamo/entropia")
    ap.add_argument("--alpha", type=float, default=1.0, help="lisciatura di Laplace")
    ap.add_argument("--quota-tr", type=float, default=0.70)
    ap.add_argument("--eps", type=float, nargs="+", default=[0.05, 0.10, 0.20, 0.40])
    ap.add_argument("--misurato", type=float, default=0.009,
                    help="tasso misurato sui modelli addestrati, per confronto")
    a = ap.parse_args()

    print("Richiamo guadagnato per ogni punto percentuale di entropia pesata,")
    print("stimato dal priore storico. Valori maggiori indicano uno scambio piu'")
    print("favorevole al richiamo, quindi un margine meno difendibile.\n")
    print(f"{'contesto':10s} {'rosso':>6} {'celle':>11} " +
          "".join(f"{'eps=' + format(e, '.2f'):>12}" for e in a.eps) +
          f"{'mediana':>10}{'entropia':>9}{'per unita':>11}")

    tutti, dens = [], []
    for c, (tp, n) in CONTESTI.items():
        if not tp.exists():
            print(f"{n:10s} bersagli non trovati")
            continue
        p, y, w = priore(tp, a.alpha, a.quota_tr)
        ce0, rec0 = misure(p, y, w)
        rosso = 100 * (y == 2).mean()
        celle, ass = [], []
        for e in a.eps:
            ce1, rec1 = misure(p, y, w, e)
            d_ce = 100 * (ce1 - ce0) / ce0          # variazione percentuale
            d_re = rec1 - rec0
            celle.append(abs(d_re / d_ce) if abs(d_ce) > 1e-9 else float("nan"))
            ass.append(abs(d_re / (ce1 - ce0)) if abs(ce1 - ce0) > 1e-12 else float("nan"))
        m = float(np.nanmedian(celle))
        tutti.append(m)
        # densita' del margine decisionale: e' la grandezza da cui dipende la
        # derivata del richiamo, e ne spiega la stabilita' o l'assenza
        crit = (y == 2)
        marg = p[crit][:, 2] - p[crit][:, :2].max(1)
        dens.append((n, float(np.mean(np.abs(marg) < 0.05)),
                     float(np.median(marg)), float((marg > 0).mean())))
        print(f"{n:10s} {rosso:5.2f}% {len(y):11,} " +
              "".join(f"{x:12.4f}" for x in celle) + f"{m:10.4f}"
              + f"{ce0:9.4f}{float(np.nanmedian(ass)):11.4f}")

    if tutti:
        print(f"\n  intervallo fra i contesti: {min(tutti):.4f} ÷ {max(tutti):.4f} "
              f"di richiamo per punto di entropia")
        print(f"  soglia di rilevanza dichiarata: un episodio su cento, cioe' 0,0100")
        print(f"  valore misurato sui modelli addestrati: {a.misurato:.4f}")
        esito = ("sotto la soglia in tutti i contesti" if max(tutti) < 0.01
                 else "SOPRA la soglia in almeno un contesto")
        print(f"  -> la stima dal priore e' {esito}")

    if dens:
        print(f"\n{'contesto':10s} {'|margine| < 0,05':>18} {'margine mediano':>17} "
              f"{'gia\' sopra soglia':>18}")
        for n, q, me, so in dens:
            print(f"{n:10s} {100 * q:17.2f}% {me:+17.3f} {100 * so:17.2f}%")
        print("\n  Il margine e' p(critica) meno la massima fra le altre due: le celle")
        print("  che cambiano classificazione sotto una perturbazione sono quelle con")
        print("  margine prossimo a zero. Se la quota entro 0,05 e' molto piccola, la")
        print("  derivata del richiamo e' quasi nulla e il tasso stimato non e' una")
        print("  sovrastima ma una SOTTOSTIMA: il priore non e' disperso attorno alla")
        print("  soglia, e' concentrato lontano da essa perche' predice quasi sempre")
        print("  la classe dominante. La stima non fornisce quindi la giustificazione")
        print("  conservativa attesa, e va dichiarato.")

    print("\n  La stabilita' rispetto a `eps` va guardata prima del valore: se il")
    print("  tasso varia molto fra le colonne, la derivata non e' ben definita e il")
    print("  numero non va usato. Il priore assegna la medesima distribuzione a tutte")
    print("  le celle con uguale sensore e momento-tipo, quindi il margine decisionale")
    print("  assume pochi valori distinti e il richiamo varia a scatti.")
    print("\n  ATTENZIONE alla direzione della distorsione. Ci si attende che il priore,")
    print("  essendo piu' disperso di un modello addestrato, concentri piu' massa presso")
    print("  la soglia e quindi SOVRASTIMI il richiamo guadagnato. La diagnostica del")
    print("  margine dice se sia cosi': se la quota di celle critiche prossime alla")
    print("  soglia e' minima e il margine mediano e' ampiamente negativo, il priore e'")
    print("  concentrato LONTANO dalla soglia — predice quasi sempre la classe dominante —")
    print("  e la stima e' una sottostima. In quel caso non fornisce la giustificazione")
    print("  conservativa cercata, e il numero non va usato a quel fine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
