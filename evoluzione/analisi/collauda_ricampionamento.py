#!/usr/bin/env python3
"""
Collaudo del ricampionamento con molteplicita'.
===============================================
Nessun addestramento.

LA VERIFICA CHE CONTA. Il calcolo per aggregati di nodo deve dare lo stesso
risultato della DUPLICAZIONE ESPLICITA delle celle: se un nodo e' estratto tre
volte, le sue celle devono comparire tre volte nel calcolo diretto. Confrontare i
due su un esempio piccolo e' l'unico modo per stabilire che il prodotto scalare
non sia un'approssimazione.

GLI AGGREGATI RESTANO SEPARATI PER ORIZZONTE. La metrica principale e' la media
delle quattro perdite, non la perdita delle somme complessive: sommare tutto prima
di dividere darebbe una media pesata sui denominatori degli orizzonti, che non e'
la stessa cosa. Il collaudo lo verifica esplicitamente.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/collauda_ricampionamento.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.ricampionamento import (  # noqa: E402
    termini_per_nodo, wce_da_molteplicita)

ESITI = []


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def wce_diretta(P, Y, w):
    """L'entropia pesata calcolata cella per cella, senza aggregati."""
    pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1.0)
    wy = w[Y]
    return float(np.sum(wy * -np.log(pt)) / np.sum(wy))


def main() -> int:
    rng = np.random.default_rng(0)
    K, per_nodo = 7, 5          # piccolo: la duplicazione esplicita e' fattibile
    n = K * per_nodo
    nodo = np.repeat(np.arange(K), per_nodo)
    Y = rng.integers(0, 3, n)
    P = rng.random((n, 3)) + 0.05
    P /= P.sum(1, keepdims=True)
    w = np.array([1.0, 3.5, 11.0])

    print("[1] aggregati contro duplicazione esplicita delle celle")
    S, W = termini_per_nodo(P, Y, nodo, w, K)
    for prova, c in (("tutti una volta", np.ones(K)),
                     ("uno assente", np.array([0., 1, 1, 1, 1, 1, 1])),
                     ("uno triplicato", np.array([3., 1, 1, 1, 1, 1, 1])),
                     ("molteplicita' varie", np.array([2., 0, 3, 1, 0, 4, 1]))):
        # duplicazione esplicita: le celle del nodo j compaiono c_j volte
        idx = np.concatenate([np.where(nodo == j)[0].repeat(int(c[j]))
                              for j in range(K)]) if c.sum() else np.array([], int)
        atteso = wce_diretta(P[idx], Y[idx], w) if len(idx) else np.nan
        ottenuto = wce_da_molteplicita(S, W, c)
        d = abs(atteso - ottenuto)
        verifica(f"1-{prova[:12]}", prova, d < 1e-12,
                 f"esplicito {atteso:.10f}  aggregati {ottenuto:.10f}  "
                 f"scarto {d:.2e}")

    print("\n[2] gli aggregati restano separati per orizzonte")
    H = ("15m", "30m", "60m", "120m")
    pre = {}
    dirette = []
    for h in H:
        Yh = rng.integers(0, 3, n)
        Ph = rng.random((n, 3)) + 0.05
        Ph /= Ph.sum(1, keepdims=True)
        pre[h] = termini_per_nodo(Ph, Yh, nodo, w, K)
        dirette.append(wce_diretta(Ph, Yh, w))
    uno = np.ones(K)
    # la media delle quattro perdite
    media_perdite = float(np.mean([wce_da_molteplicita(*pre[h], uno) for h in H]))
    # la perdita delle somme complessive: NON e' la stessa cosa
    Stot = sum(pre[h][0] for h in H)
    Wtot = sum(pre[h][1] for h in H)
    perdita_somme = wce_da_molteplicita(Stot, Wtot, uno)
    verifica(2, "la media delle quattro perdite coincide con il calcolo diretto",
             abs(media_perdite - float(np.mean(dirette))) < 1e-12,
             f"{media_perdite:.10f} contro {np.mean(dirette):.10f}")
    verifica("2b", "sommare prima di dividere da' un valore DIVERSO",
             abs(media_perdite - perdita_somme) > 1e-9,
             f"media delle perdite {media_perdite:.6f}, perdita delle somme "
             f"{perdita_somme:.6f}: scarto {abs(media_perdite-perdita_somme):.2e}")

    print("\n[3] la maschera booleana perde le molteplicita'")
    c = np.array([3., 1, 1, 1, 1, 1, 1])
    m = (c > 0).astype(float)
    verifica(3, "presenza e molteplicita' danno valori diversi",
             abs(wce_da_molteplicita(S, W, c)
                 - wce_da_molteplicita(S, W, m)) > 1e-9,
             "e' il difetto della procedura pubblicata")

    print("\n[4] quota attesa di nodi distinti con reinserimento")
    for Kp in (7, 400, 828):
        sel = np.random.default_rng(1).choice(Kp, Kp, replace=True)
        oss = len(np.unique(sel)) / Kp
        att = 1 - (1 - 1 / Kp) ** Kp
        verifica(f"4-{Kp}", f"K = {Kp}: osservata contro attesa",
                 abs(oss - att) < 0.06,
                 f"osservata {100*oss:.2f}%, attesa {100*att:.2f}% "
                 f"(il limite e' 1 - 1/e = 63,21%)")

    print("\n" + "=" * 64)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 64)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
