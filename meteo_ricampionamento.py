#!/usr/bin/env python3
"""
Controllo a permutazione sul meteo: intervalli per ricampionamento congiunto.
=============================================================================
Nessun addestramento: legge i dump di probabilita' della campagna di
permutazione, salvati per epoca di valutazione.

LA CONVENZIONE, che va dichiarata in didascalia perche' i valori non sono
altrimenti ricostruibili:

  * EPOCA 25, non la migliore in validazione ne' l'ultima. I file di risultato
    contengono, per ciascun modello e sottoinsieme, una riga di riepilogo alla
    migliore epoca in validazione e trenta righe di traccia: aggregazioni diverse
    danno valori diversi. Sul contesto primario di Madrid la riga di riepilogo
    da' +0,52 per cento, la media sulle tre epoche di valutazione +0,76, il
    minimo della curva +0,50, e l'epoca 25 il +0,93 che il documento riporta;
  * SOTTOINSIEME COMPLESSIVO, non quello dei giorni di pioggia ne' quello degli
    asciutti. La permutazione riordina anche l'indicatore di pioggia, sicche' i
    sottoinsiemi condizionati contengono giornate diverse nelle due corse e non
    sono confrontabili;
  * segno POSITIVO quando il meteo reale e' PEGGIORE del permutato.

IL COLLAUDO. Lo script di ablazione addestra entrambi i rami in un'unica
esecuzione, sicche' il ramo privo di meteo e' prodotto due volte per seme e a
parita' di seme deve coincidere. Sul sottoinsieme complessivo lo scarto e' nullo
alla sesta cifra; sui sottoinsiemi condizionati non lo e', per la ragione detta.

Uso (dalla radice OR3/):

    poetry run python meteo_ricampionamento.py
    poetry run python meteo_ricampionamento.py --epoca 30 --repliche 300
"""
import argparse
import glob as globmod

import numpy as np

NOME = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
        "d8_2024": "d8/2024"}
# numero totale di sensori per contesto, dedotto sui dump del compito denso
NODI = {"t4cmad": 828, "t4clon": 774, "t4cmel": 587, "d8_2024": 445}


def carica(percorso):
    """Restituisce (probabilita', bersagli, indici) dal dump indicato."""
    f = globmod.glob(percorso)
    if not f:
        return None
    z = np.load(f[0], allow_pickle=True)
    chiavi = {k: k for k in z.files}
    # i dump della campagna meteo salvano un solo blocco per file
    p = next((z[k] for k in ("p", "p0", "probs") if k in chiavi), None)
    y = next((z[k] for k in ("y", "y0", "labels") if k in chiavi), None)
    i = next((z[k] for k in ("idx", "idx0", "indices") if k in chiavi), None)
    if p is None or y is None:
        return None
    return (p.astype("float32"), y.astype(int),
            i.astype(int) if i is not None else None)


TARGETS = {
    "t4cmad": "data_collection/traffic4cast/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4clon": "data_collection/traffic4cast/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4cmel": "data_collection/traffic4cast/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
    "d8_2024": "data_collection/go-mo/gomo/targets_2024_urb_d8.npz",
}


def pesi_da(c):
    """Pesi calcolati sulle frequenze del PERIODO DI ADDESTRAMENTO, come da §7.1.

    Ricostruirli dalle frequenze osservate nel dump, che sono quelle del periodo
    di prova, produce entropie diverse da quelle dei file di risultato: le due
    distribuzioni non coincidono, e su tre contesti su quattro lo scarto e'
    dell'ordine di due decimi di punto sulla differenza fra i rami.
    """
    z = np.load(TARGETS[c], allow_pickle=True)
    C = z["congestion_emp"]
    T = C.shape[0]
    fr = np.array([(C[: int((T - 8) * 0.7)] == k).sum() for k in (1, 2, 3)], float)
    return fr.sum() / (np.maximum(fr, 1) * 3)


def wce(d, w, K=None, sel=None):
    P, Y, idx = d
    m = np.isin(idx % K, sel) if (sel is not None and idx is not None) else slice(None)
    y = Y[m]
    p = np.clip(P[m][np.arange(len(y)), y], 1e-7, 1)
    return float(np.sum(w[y] * -np.log(p)) / np.sum(w[y]))


def main() -> int:
    ap = argparse.ArgumentParser(description="permutazione meteo, intervalli di ricampionamento")
    ap.add_argument("--dir", default="replication/probs_wx")
    ap.add_argument("--epoca", type=int, default=25)
    ap.add_argument("--repliche", type=int, default=1000)
    ap.add_argument("--semi", type=int, default=5)
    a = ap.parse_args()
    rng = np.random.default_rng(0)

    print(f"differenza di entropia pesata fra meteo REALE e PERMUTATO, "
          f"epoca {a.epoca}")
    print("(positivo = il reale e' peggiore; sottoinsieme complessivo)\n")
    print(f"{'contesto':10s} {'reale':>9} {'permutato':>10} {'differenza':>10} "
          f"{'IC ricampionamento':>24} {'collaudo':>10}")

    for c, n in NOME.items():
        S = []
        collaudo = []
        for s in range(a.semi):
            b = f"{a.dir}/wx_%s_{c}_s{s}_%s_e{a.epoca}.npz"
            rr = carica(b % ("reale", "weather"))
            pp = carica(b % ("permutato", "weather"))
            br = carica(b % ("reale", "base"))
            bp = carica(b % ("permutato", "base"))
            if not all(x is not None for x in (rr, pp, br, bp)):
                S = []
                break
            S.append((rr, pp, br, bp))
        if len(S) < a.semi:
            print(f"{n:10s} dump incompleti")
            continue

        w = pesi_da(c)
        K = NODI.get(c)
        nodi = (np.unique(S[0][0][2] % K)
                if (K and S[0][0][2] is not None) else None)

        # collaudo: il ramo privo di meteo deve coincidere fra le due corse
        for rr, pp, br, bp in S:
            collaudo.append(abs(wce(br, w) - wce(bp, w)))

        pt = [100 * (wce(rr, w) - wce(pp, w)) / wce(pp, w) for rr, pp, _, _ in S]
        m = float(np.mean(pt))

        if nodi is None:
            print(f"{n:10s} {'':9} {'':10} {m:+9.2f}% "
                  f"{'indici assenti':>24} {max(collaudo):10.6f}")
            continue

        B = []
        for _ in range(a.repliche):
            i = rng.integers(0, a.semi, a.semi)
            sel = rng.choice(nodi, len(nodi), replace=True)
            B.append(np.mean([
                100 * (wce(S[k][0], w, K, sel) - wce(S[k][1], w, K, sel))
                / wce(S[k][1], w, K, sel) for k in i]))
        lo, hi = np.percentile(B, [2.5, 97.5])
        lo, hi = m + (lo - np.mean(B)), m + (hi - np.mean(B))
        esito = "" if lo * hi > 0 else "   tocca lo zero"
        print(f"{n:10s} {np.mean([wce(x[0], w) for x in S]):9.4f} "
              f"{np.mean([wce(x[1], w) for x in S]):10.4f} {m:+9.2f}% "
              f"[{lo:+10.2f};{hi:+9.2f}] {max(collaudo):10.6f}{esito}")

    print("\n  La colonna di collaudo riporta lo scarto massimo, fra i semi, del ramo")
    print("  privo di meteo fra le due corse: deve essere nullo, poiche' e' il")
    print("  medesimo addestramento. Uno scarto non nullo indica che il confronto")
    print("  non isola l'effetto della permutazione.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
