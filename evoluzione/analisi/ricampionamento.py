#!/usr/bin/env python3
"""
Ricampionamento: molteplicita' conservate e variante gerarchica.
================================================================
Nessun addestramento: opera sui dump di probabilita' gia' salvati.

IL DIFETTO DELLA PROCEDURA PUBBLICATA. Le repliche estraggono i nodi con
reinserimento, ma la selezione avviene con `np.isin`, che produce una maschera
booleana: un nodo estratto due volte contribuisce UNA volta sola. Ogni replica usa
quindi circa il 63 per cento delle celle — che e' 1 - 1/e, la quota attesa di
elementi distinti — anziche' il cento per cento, e la dispersione risulta
sottostimata.

L'IMPLEMENTAZIONE CORRETTA NON COSTRUISCE GLI INDICI. L'entropia pesata e' un
rapporto di somme, sicche' basta precalcolare per ciascun nodo la somma pesata dei
suoi termini e la somma dei suoi pesi; ogni replica diventa allora un prodotto
scalare con il vettore delle molteplicita'. E' esatto, e non richiede di
materializzare milioni di indici per replica.

    wCE = sum_j c_j S_j / sum_j c_j W_j

TRE PROCEDURE, riportate affiancate perche' la differenza sia visibile:

  storica       maschera booleana, un solo seme per replica
  molteplicita' molteplicita' conservate, un solo seme per replica
  gerarchica    semi estratti con reinserimento E nodi con molteplicita'

LA GERARCHICA RISPETTA LO STIMATORE. La stima e' una media sui semi: una procedura
che ne estragga uno solo per replica descrive la variabilita' di una esecuzione,
non la distribuzione campionaria della media. La gerarchica estrae S semi con
reinserimento e, per ciascuno, i nodi con molteplicita'.

I VALORI PUBBLICATI NON SI SOSTITUISCONO. Si riportano entrambi, dichiarando quale
procedura ha prodotto ciascuno.
"""
from __future__ import annotations

import glob as globmod

import numpy as np

H = ("15m", "30m", "60m", "120m")


def termini_per_nodo(P, Y, nodo, w, K):
    """(S, W) per nodo: somma pesata dei termini e somma dei pesi.

    Con queste due quantita' ogni replica si riduce a un prodotto scalare, e la
    molteplicita' di un nodo entra come fattore intero anziche' come presenza.
    """
    pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1.0)
    wy = w[Y]
    S = np.bincount(nodo, weights=wy * -np.log(pt), minlength=K)
    W = np.bincount(nodo, weights=wy, minlength=K)
    return S, W


def wce_da_molteplicita(S, W, c):
    """Entropia pesata su una replica descritta dalle molteplicita' `c`."""
    den = float(c @ W)
    return float(c @ S) / den if den > 0 else float("nan")


def wce_da_maschera(S, W, sel):
    """La procedura STORICA: presenza anziche' molteplicita'."""
    m = np.zeros(len(S))
    m[np.unique(sel)] = 1.0
    return wce_da_molteplicita(S, W, m)


def blocchi(percorso, tag, K):
    f = globmod.glob(percorso, recursive=True)
    if not f:
        return None
    z = np.load(f[0], allow_pickle=True)
    o = {}
    for h in H:
        i = [k[3:] for k in z.files
             if k.startswith("tag") and str(z[k]) == f"{tag}|{h}"]
        if not i:
            return None
        j = i[0]
        o[h] = (z[f"p{j}"].astype("float32"), z[f"y{j}"].astype(int),
                z[f"idx{j}"] % K)
    return o


def prepara(dump, w, K):
    """{seme: {orizzonte: (S, W)}} — il precalcolo, fatto una volta sola."""
    fuori = {}
    for s, b in dump.items():
        fuori[s] = {h: termini_per_nodo(*b[h], w, K) for h in H}
    return fuori


def _wce_medio(pre, s, c, quale=wce_da_molteplicita):
    """Entropia di un seme, media sui quattro orizzonti."""
    return float(np.mean([quale(*pre[s][h], c) for h in H]))


def intervalli(pre_a, pre_b, nodi, K, repliche=1000, seme=0,
               procedura="molteplicita", livello=0.95):
    """Intervallo per la differenza relativa fra due configurazioni.

    `pre_a` e `pre_b` sono i precalcoli delle due configurazioni, indicizzati
    per seme. La stima puntuale e' la media dei rapporti appaiati per seme.
    """
    rng = np.random.default_rng(seme)
    semi = sorted(set(pre_a) & set(pre_b))
    if len(semi) < 2:
        return None

    def punto(sel_semi, c):
        v = []
        for s in sel_semi:
            a = _wce_medio(pre_a, s, c)
            b = _wce_medio(pre_b, s, c)
            # CONVENZIONE DEL DELIVERABLE: il vantaggio si normalizza sulla
            # configurazione di RIFERIMENTO, non su quella migliorata, e ha
            # segno positivo quando la seconda e' migliore. Normalizzare sul
            # denominatore sbagliato cambia il valore, non solo il segno:
            # 22,10 diventa 28,48 sullo stesso confronto.
            if np.isfinite(a) and np.isfinite(b) and a > 0:
                v.append(100.0 * (a - b) / a)
        return float(np.mean(v)) if v else float("nan")

    uno = np.ones(K)
    stima = punto(semi, uno)
    rep = []
    for _ in range(repliche):
        if procedura == "storica":
            s = [semi[rng.integers(len(semi))]]
            sel = rng.choice(nodi, len(nodi), replace=True)
            c = np.zeros(K); c[np.unique(sel)] = 1.0
        elif procedura == "molteplicita":
            s = [semi[rng.integers(len(semi))]]
            sel = rng.choice(nodi, len(nodi), replace=True)
            c = np.bincount(sel, minlength=K).astype("float64")
        elif procedura == "gerarchica":
            # i semi entrano con reinserimento: la stima e' una media su di essi
            s = [semi[i] for i in rng.integers(len(semi), size=len(semi))]
            sel = rng.choice(nodi, len(nodi), replace=True)
            c = np.bincount(sel, minlength=K).astype("float64")
        else:
            raise ValueError(f"procedura ignota: {procedura}")
        x = punto(s, c)
        if np.isfinite(x):
            rep.append(x)
    if len(rep) < 20:
        return None
    rep = np.array(rep)
    a = (1 - livello) / 2
    lo = stima + np.percentile(rep, 100 * a) - rep.mean()
    hi = stima + np.percentile(rep, 100 * (1 - a)) - rep.mean()
    return dict(stima=stima, lo=float(lo), hi=float(hi),
                semiampiezza=float((hi - lo) / 2), repliche=len(rep),
                procedura=procedura)
