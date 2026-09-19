#!/usr/bin/env python3
"""
Episodio di inserimento: origini ammissibili e lotti.
======================================================
**Riusa `_canali` e `_lotto` di `addestramento.py`**, anziche' duplicarli: la
costruzione degli ingressi e la maschera dei bersagli sono gia' collaudate, e
una seconda implementazione divergerebbe in silenzio.

    ACQUISIZIONE   [t0, t1], ventiquattro ore di DURATA
    VALUTAZIONE    il periodo successivo, SEMPRE entro i confini del periodo

AMMISSIBILITA', come fissata: **l'orizzonte massimo non supera t1; le celle
bersaglio mancanti sono escluse dalla perdita; l'esempio contribuisce se
contiene ALMENO UN target valido.** Non si richiedono quattro target su quattro:
selezionerebbe le finestre piu' coperte e penalizzerebbe i sensori piu'
incompleti.

**Nessuna strategia aggiorna il modello usando i target del periodo di
valutazione.**
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.predittore import FINESTRA, ORIZZONTI  # noqa: E402
from evoluzione.esperimenti.addestramento import _lotto  # noqa: E402

MAX_ORIZZ = max(ORIZZONTI)
ORE_VALUTAZIONE = 24


class EpisodioVuoto(RuntimeError):
    """Nessuna origine ammissibile per l'adattamento o per la valutazione."""


def origini_adattamento(t0: int, t1: int) -> list:
    """Le origini con TUTTI i bersagli maturati entro t1.

    Maturazione temporale e validita' della misura sono cose distinte: qui si
    filtra la sola maturazione, e le celle mancanti sono escluse a valle.
    """
    return [t for t in range(t0 + FINESTRA - 1, t1 + 1) if t + MAX_ORIZZ <= t1]


def giornata_valutazione(ts, t1: int, confine: int):
    """La GIORNATA successiva all'acquisizione, per DURATA di calendario.

    **Non «tutte le origini disponibili nel resto della validazione»**: la
    regola vigente fissa ventiquattro ore di valutazione dopo le ventiquattro
    di acquisizione, e usarne di piu' sarebbe un'estensione dell'emendamento,
    non un riallineamento.
    """
    import pandas as pd
    fine_g = ts[t1] + pd.Timedelta(hours=ORE_VALUTAZIONE)
    j = int(np.searchsorted(ts.values, np.datetime64(fine_g), side="right")) - 1
    return min(j, confine - 1)


def origini_valutazione(ts, t1: int, confine: int) -> list:
    """Le origini della giornata di valutazione.

    **ORIGINE = TIMESTAMP previsionale distinto.** Ogni origine genera |nodi|
    istanze nodo-timestamp e |nodi| x 4 celle, una per orizzonte: il manifesto
    le riporta separatamente.

    Ammissibili le sole origini i cui bersagli, fino a due ore, ricadano
    **entro la giornata di valutazione**.
    """
    fine = giornata_valutazione(ts, t1, confine)
    return [t for t in range(t1 + 1, fine + 1) if t + MAX_ORIZZ <= fine]


def lotti_episodio(x, classe, statiche, nodi, origini, per_nodo=False):
    """I lotti (X, nodi, Y, M, S).

    `x` sono i canali gia' costruiti da `_canali`, `classe` la matrice dei
    bersagli: gli stessi oggetti che l'addestramento usa.

    Con `per_nodo=True` un lotto per ciascun nodo — la forma che l'adattamento
    di F richiede, perche' **ciascun aggiornamento usa tutti gli esempi
    ammissibili del SINGOLO nodo**. I nodi senza alcun target valido **non
    producono lotto**, e a valle `adatta` registra l'assenza.
    """
    if not origini:
        raise EpisodioVuoto("nessuna origine ammissibile")
    nodi = np.asarray(nodi, dtype="int64")
    X, Y, M = _lotto(x, classe, origini, nodi)
    S = torch.as_tensor(statiche[nodi].astype("float32"))
    if not per_nodo:
        return [(X, [int(v) for v in nodi], Y, M, S)]
    fuori = []
    for i, n in enumerate(nodi):
        if not bool(M[:, i].any()):
            continue
        fuori.append((X[:, :, i:i + 1], [int(n)], Y[:, i:i + 1],
                      M[:, i:i + 1], S[i:i + 1]))
    return fuori


def riepilogo(classe, nodi, origini, t0, t1) -> dict:
    """Che cosa l'episodio contiene, da registrare nel manifesto."""
    nodi = np.asarray(nodi, dtype="int64")
    validi = np.zeros(len(nodi), dtype="int64")
    for t in origini:
        for o in ORIZZONTI:
            validi += (classe[t + o][nodi] > 0).astype("int64")
    tot = max(len(nodi) * len(origini) * len(ORIZZONTI), 1)
    return {"timestamp_distinti": len(origini), "nodi": len(nodi),
            "istanze_nodo_timestamp": int(len(nodi) * len(origini)),
            "celle_attese": int(len(nodi) * len(origini) * len(ORIZZONTI)),
            "celle_per_orizzonte": int(len(nodi) * len(origini)),
            "celle_valide": int(validi.sum()),
            "quota_valide": float(validi.sum() / tot),
            "nodi_senza_alcun_target": int((validi == 0).sum()),
            "t0": int(t0), "t1": int(t1)}
