#!/usr/bin/env python3
"""
Griglia temporale: UN solo modulo per tutte le fasi e tutti i bracci.
======================================================================
Le serie hanno salti: circa meta' dei giorni manca, e le righe consecutive
possono distare giorni. **Un offset di indice non e' un offset di tempo.**

REGOLA APPROVATA per le origini:

    un'origine t e' ammissibile soltanto se la sequenza temporale, dal primo
    passo della finestra dinamica (t - FINESTRA + 1) all'ultimo bersaglio
    (t + max orizzonte), rispetta la cadenza reale di 15 minuti SENZA SALTI

Si applica a addestramento, selezione del punto di controllo, adattamento e
selezione di F, corpus e campionatore di R, test: **tutti i bracci**.

**Le misure mancanti del singolo sensore NON c'entrano**: restano alle
maschere. Qui si correggono i salti della GRIGLIA, non la copertura locale.

CONVENZIONE DEGLI ESTREMI: l'acquisizione e' (t0, t1], i 96 intervalli
t0 + 15 min, ..., t0 + 24 h. **La riga t0 non appartiene all'acquisizione**:
ne' il descrittore ne' l'adattamento ne' il corpus di R la usano.

LE RIGHE DEL PERIODO restano un'altra cosa: la normalizzazione le usa come
osservazioni, e non dipende da questa regola.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PASSO = pd.Timedelta(minutes=15)
FINESTRA = 12
ORIZZONTI = (1, 2, 4, 8)
MAX_ORIZZ = max(ORIZZONTI)
L_DESCRITTORE = 96


class GrigliaViolata(RuntimeError):
    """Una finestra richiesta attraversa un salto della griglia temporale."""


def passi_regolari(ts) -> np.ndarray:
    """`ok[i]` vero se fra la riga i e la i+1 passano esattamente 15 minuti.

    Lunghezza len(ts) - 1.
    """
    return np.asarray(pd.Series(pd.DatetimeIndex(ts)).diff().iloc[1:] == PASSO)


def _salti_cumulati(ok: np.ndarray) -> np.ndarray:
    """c[j] = numero di salti fra le righe 0..j; c[0] = 0."""
    return np.concatenate([[0], np.cumsum(~ok)])


def contigue(ok: np.ndarray, a: int, b: int) -> bool:
    """Righe a..b (incluse) su griglia regolare."""
    if a < 0 or b > len(ok) or b < a:
        return False
    return bool(ok[a:b].all())


def maschera_origini(ok: np.ndarray, finestra: int = FINESTRA,
                     max_orizz: int = MAX_ORIZZ) -> np.ndarray:
    """amm[t] vero se le righe t-finestra+1 .. t+max_orizz sono contigue.

    Vettorizzata: un'origine e' ammissibile se il numero di salti cumulati non
    cambia fra il primo e l'ultimo estremo della sua finestra.
    """
    T = len(ok) + 1
    c = _salti_cumulati(ok)
    t = np.arange(T)
    a, b = t - finestra + 1, t + max_orizz
    val = (a >= 0) & (b <= T - 1)
    amm = np.zeros(T, dtype=bool)
    amm[val] = c[b[val]] == c[a[val]]
    return amm


def filtra(origini, amm: np.ndarray) -> np.ndarray:
    """Le sole origini ammissibili, nell'ordine dato."""
    o = np.asarray(origini, dtype="int64")
    o = o[(o >= 0) & (o < len(amm))]
    return o[amm[o]]


def verifica_finestra_descrittore(ok: np.ndarray, t: int,
                                  L: int = L_DESCRITTORE) -> None:
    """La finestra (t - L, t] deve coprire L intervalli REALI.

    **Controllo bloccante**: selezionare per righe comprimerebbe i giorni
    assenti, e la copertura avrebbe il denominatore sbagliato.
    """
    if not contigue(ok, t - L + 1, t):
        raise GrigliaViolata(
            f"la finestra del descrittore (t-{L}, t] con t={t} attraversa un "
            f"salto della griglia: non copre {L} intervalli reali")


def origini_acquisizione(ok: np.ndarray, t0: int, t1: int,
                         finestra: int = FINESTRA,
                         max_orizz: int = MAX_ORIZZ) -> list:
    """Le origini d'adattamento nell'acquisizione (t0, t1].

    **La riga t0 non si usa**: la prima origine e' t0 + finestra, la cui
    finestra comincia a t0 + 1. Tutti i bersagli maturano entro t1.
    """
    amm = maschera_origini(ok, finestra, max_orizz)
    return [t for t in range(t0 + finestra, t1 + 1)
            if t + max_orizz <= t1 and amm[t]]


def origini_dopo(ok: np.ndarray, t1: int, fine: int,
                 finestra: int = FINESTRA, max_orizz: int = MAX_ORIZZ) -> list:
    """Le origini successive all'acquisizione, con bersagli entro `fine`."""
    amm = maschera_origini(ok, finestra, max_orizz)
    return [t for t in range(t1 + 1, fine) if t + max_orizz < fine and amm[t]]


def primo_t0(ts, ok: np.ndarray, a: int, b: int, giornata_dopo: bool,
             L: int = L_DESCRITTORE):
    """REGOLA APPROVATA per il calendario.

    Il primo t0 in [a, b) tale che (t0, t0 + 24 h] contenga TUTTI i 96
    intervalli attesi — righe t0..t0+96 contigue — e, se `giornata_dopo`,
    anche la giornata successiva (t1, t1 + 24 h] completa, entro il periodo.
    **Nessuna soglia parziale.**
    """
    ts = pd.DatetimeIndex(ts)
    for t0 in range(a, b):
        t1 = t0 + L
        if t1 >= b or not contigue(ok, t0, t1):
            continue
        if ts[t1] - ts[t0] != L * PASSO:
            continue
        if giornata_dopo and (t1 + L >= b or not contigue(ok, t1, t1 + L)):
            continue
        return t0
    return None


def riepilogo(ok: np.ndarray, periodi: dict) -> dict:
    """Origini nominali e ammissibili per periodo, per i manifesti."""
    amm = maschera_origini(ok)
    T = len(ok) + 1
    fuori = {}
    for n, (a, b) in periodi.items():
        nom = [t for t in range(max(a, FINESTRA - 1), b) if t + MAX_ORIZZ < T]
        am = int(amm[np.asarray(nom, dtype="int64")].sum()) if nom else 0
        fuori[n] = {"nominali": len(nom), "ammissibili": am,
                    "escluse": len(nom) - am}
    return fuori
