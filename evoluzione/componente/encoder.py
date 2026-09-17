#!/usr/bin/env python3
"""
Encoder condiviso dell'identita' osservabile.
=============================================
    z_i = W2 · ReLU(W1 u_i + b1) + b2,     z_i in R^8

CONFIGURAZIONE UNICA, fissata e non ottimizzata:

    64 unita' nascoste, scelta iniziale prefissata
    nessun dropout
    nessuna normalizzazione con statistiche mobili
    parametri CONDIVISI fra tutti i sensori
    anagrafica statica in un RAMO SEPARATO, comune alle strategie

La dimensione d'ingresso differisce fra varianti — LEGACY 16, BASE-CORRECTED 29,
EXTENDED 35 — mentre struttura nascosta e dimensione d'uscita restano uguali.

PRIMA DELL'ENCODER si sostituiscono i valori non stimabili con il valore neutro
dichiarato, si conservano gli indicatori di disponibilita', e si verifica che non
arrivino valori non finiti. La verifica e' attiva sempre, non solo in collaudo:
un `nan` che attraversi l'encoder propaga silenziosamente a tutte le uscite.

UN'IDENTITA' PREDEFINITA CONDIVISA NON E' UN EMBEDDING. Con bias appresi, una
storia interamente indisponibile produce `W2 · ReLU(b1) + b2`, che e' un vettore
non nullo ma IDENTICO per ogni sensore in quello stato: e' il comportamento
predefinito della rappresentazione, non un parametro specifico per nodo.

L'ANAGRAFICA NON PASSA DI QUI. Entra nella previsione come ramo separato,
disponibile a tutte le strategie: mescolarla al descrittore impedirebbe di
isolare il valore dell'identita' osservabile nel confronto fra S0 e S1.
"""
from __future__ import annotations

import numpy as np

NASCOSTE = 64          # prefissate, non ottimizzate
USCITA = 8
NEUTRO = 0.0           # valore dichiarato per le statistiche non stimabili


def prepara_ingresso(statistiche, disponibilita, non_stimabili=None,
                     nomi=None, neutro: float = NEUTRO):
    """Concatena statistiche e disponibilita', sostituendo i non stimabili.

    Restituisce (u, sostituiti). Solleva se resta un valore non finito: un
    `nan` che attraversi l'encoder propagherebbe a tutte le uscite senza
    segnalarsi.
    """
    s = np.asarray(statistiche, dtype="float64").copy()
    q = np.asarray(disponibilita, dtype="float64").copy()
    sostituiti = []
    if non_stimabili and nomi:
        pos = {n: i for i, n in enumerate(nomi)}
        for n in non_stimabili:
            if n in pos:
                s[pos[n]] = neutro
                sostituiti.append(n)
    # una statistica non finita che non figuri fra i non stimabili e' un difetto
    # dell'estrattore, non un dato mancante: si sostituisce e si segnala
    resto = ~np.isfinite(s)
    if resto.any():
        s[resto] = neutro
        sostituiti += [f"NON DICHIARATO: indice {i}" for i in np.where(resto)[0]]
    if not np.isfinite(q).all():
        raise ValueError("disponibilita' non finita: e' un difetto, non un "
                         "dato mancante")
    u = np.concatenate([s, q])
    if not np.isfinite(u).all():
        raise ValueError("ingresso non finito dopo la sostituzione")
    return u, sostituiti


def n_parametri(d_ingresso: int, nascoste: int = NASCOSTE,
                uscita: int = USCITA) -> dict:
    """Il conteggio, da registrare: dipende dalla sola dimensione d'ingresso,
    non dal numero di sensori."""
    w1, b1 = d_ingresso * nascoste, nascoste
    w2, b2 = nascoste * uscita, uscita
    return {"W1": w1, "b1": b1, "W2": w2, "b2": b2,
            "totale": w1 + b1 + w2 + b2,
            "d_ingresso": d_ingresso, "nascoste": nascoste, "uscita": uscita}


# ------------------------------------------------------- riferimento numpy --
class EncoderRiferimento:
    """Propagazione in avanti in numpy, per collaudare le proprieta'
    matematiche senza dipendere dall'ambiente di addestramento.

    Non e' l'implementazione di esercizio: serve a verificare indipendenza dal
    lotto, equivarianza alla permutazione e comportamento sui non stimabili.
    """

    def __init__(self, d_ingresso: int, nascoste: int = NASCOSTE,
                 uscita: int = USCITA, seme: int = 0):
        rng = np.random.default_rng(seme)
        # inizializzazione alla Kaiming, coerente con il valore predefinito di
        # `nn.Linear`: serve solo a rendere il riferimento confrontabile
        self.W1 = rng.normal(0, np.sqrt(2 / d_ingresso), (nascoste, d_ingresso))
        self.b1 = rng.normal(0, 0.1, nascoste)
        self.W2 = rng.normal(0, np.sqrt(2 / nascoste), (uscita, nascoste))
        self.b2 = rng.normal(0, 0.1, uscita)
        self.d_ingresso, self.nascoste, self.uscita = d_ingresso, nascoste, uscita

    def __call__(self, U):
        U = np.atleast_2d(np.asarray(U, dtype="float64"))
        if U.shape[1] != self.d_ingresso:
            raise ValueError(f"attesa dimensione {self.d_ingresso}, "
                             f"ricevuta {U.shape[1]}")
        if not np.isfinite(U).all():
            raise ValueError("ingresso non finito")
        H = np.maximum(U @ self.W1.T + self.b1, 0.0)
        return H @ self.W2.T + self.b2

    @property
    def identita_predefinita(self):
        """L'uscita per una storia interamente indisponibile: identica per ogni
        sensore in quello stato."""
        return self(np.zeros((1, self.d_ingresso)))[0]

    def n_parametri(self):
        return n_parametri(self.d_ingresso, self.nascoste, self.uscita)


# ----------------------------------------------------------- torch ----------
def costruisci_torch(d_ingresso: int, nascoste: int = NASCOSTE,
                     uscita: int = USCITA):
    """L'encoder di esercizio. Nessun dropout, nessuna normalizzazione con
    statistiche mobili: due strati lineari e una ReLU."""
    import torch.nn as nn
    return nn.Sequential(
        nn.Linear(d_ingresso, nascoste),
        nn.ReLU(),
        nn.Linear(nascoste, uscita),
    )


def inventario_per_nodo(modello, n_nodi: int) -> list:
    """I parametri il cui primo asse ha lunghezza pari al numero di nodi.

    E' la verifica dell'audit B applicata all'INTERO modello, non al solo
    encoder: un parametro con quella forma e' specifico per sensore, e dopo
    un'espansione dovrebbe cambiare dimensione.
    """
    fuori = []
    for nome, p in modello.named_parameters():
        f = tuple(p.shape)
        if f and f[0] == n_nodi:
            fuori.append({"nome": nome, "forma": list(f), "numel": int(p.numel())})
    return fuori
