#!/usr/bin/env python3
"""
Costruttori del corpus: A privilegiato, R post-installazione.
=============================================================
**Due costruttori espliciti**, non un booleano generico: la differenza
informativa fra i due bracci e' scientifica, e nasconderla dietro un parametro
la renderebbe invisibile nei manifesti.

    costruisci_corpus_privilegiato        A
    costruisci_corpus_post_installazione  R
    costruisci_corpus_iniziale            C, P, E

IL MANIFESTO DEL CORPUS descrive nodi ammessi, intervalli temporali, finestre e
bersagli utilizzabili, politica di campionamento, conteggi delle istanze e
identificativo del braccio.

I CONTROLLI SPECIFICI, bloccanti:

    A   la storia dei nodi nuovi nel training originario e' PRESENTE, e si
        dichiara come informazione privilegiata
    R   NESSUNA osservazione locale dei nodi nuovi anteriore a t0, e nessun
        bersaglio successivo a t1
    entrambi  i dati riservati alla validazione sono esclusi dalla perdita di
        addestramento

**A non e' una strategia disponibile in esercizio**: e' il livello raggiungibile
avendo il nodo fin dall'inizio, non all'inserimento.
"""
from __future__ import annotations

import numpy as np

ORIZZONTI = (1, 2, 4, 8)
FINESTRA = 12
MAX_ORIZZ = max(ORIZZONTI)


class CorpusViolato(RuntimeError):
    """Il corpus contiene informazione che il braccio non deve ricevere."""


def _istanze(istanti, nodi) -> int:
    return int(len(istanti) * len(nodi))


def _manifesto(braccio, nodi_add, nodi_nuovi, istanti, note, **extra) -> dict:
    return {"braccio": braccio,
            "nodi_ammessi": len(nodi_add),
            "nodi_nuovi_inclusi": len([x for x in nodi_nuovi
                                       if int(x) in set(int(y) for y in nodi_add)]),
            "istanti": len(istanti),
            "intervallo": [int(min(istanti)), int(max(istanti))] if len(istanti) else [],
            "istanze": _istanze(istanti, nodi_add),
            "finestra": FINESTRA, "orizzonti": list(ORIZZONTI),
            "politica_campionamento": "nessun sovracampionamento",
            "note": note, **extra}


def costruisci_corpus_iniziale(nodi_iniziali, ist_addestramento) -> dict:
    """C, P, E — i soli nodi iniziali, corpus originario."""
    return {"nodi": np.asarray(nodi_iniziali, dtype="int64"),
            "istanti": np.asarray(ist_addestramento, dtype="int64"),
            "manifesto": _manifesto(
                "iniziale", nodi_iniziali, [], ist_addestramento,
                "corpus di addestramento originario, soli nodi iniziali")}


def costruisci_corpus_privilegiato(nodi_iniziali, nodi_nuovi,
                                   ist_addestramento, t0: int) -> dict:
    """A — il nodo era PRESENTE nell'addestramento iniziale.

    Riceve la storia dei nodi nuovi **anteriore a t0**: e' precisamente
    l'informazione che lo rende privilegiato, e che in esercizio non esiste.
    """
    nodi = np.concatenate([np.asarray(nodi_iniziali, dtype="int64"),
                           np.asarray(nodi_nuovi, dtype="int64")])
    ist = np.asarray(ist_addestramento, dtype="int64")
    anteriori = int((ist < t0).sum())
    if anteriori == 0:
        raise CorpusViolato(
            f"A senza storia anteriore a t0={t0}: non sarebbe privilegiato, e "
            f"il braccio perderebbe la sua funzione di riferimento")
    return {"nodi": nodi, "istanti": ist,
            "manifesto": _manifesto(
                "A", nodi, nodi_nuovi, ist,
                "corpus PRIVILEGIATO: i nodi nuovi erano presenti "
                "nell'addestramento iniziale, con la loro storia anteriore a t0",
                privilegiato=True, t0=int(t0),
                istanti_anteriori_a_t0=anteriori,
                avvertenza=("A non e' una strategia disponibile in esercizio: "
                            "e' il livello raggiungibile AVENDO il nodo fin "
                            "dall'inizio, non all'inserimento"))}


def costruisci_corpus_post_installazione(nodi_iniziali, nodi_nuovi,
                                         ist_addestramento, t0: int,
                                         t1: int) -> dict:
    """R — riaddestramento completo dopo l'installazione.

    Il corpus originario dei nodi iniziali **piu'** gli esempi ammissibili delle
    prime ventiquattro ore dei nodi nuovi. **Nessuna storia anteriore a t0** per
    questi ultimi, e **nessun bersaglio successivo a t1**.
    """
    ini = np.asarray(nodi_iniziali, dtype="int64")
    nuo = np.asarray(nodi_nuovi, dtype="int64")
    ist_ini = np.asarray(ist_addestramento, dtype="int64")
    # le origini dei nodi NUOVI: solo dentro l'episodio, con bersagli entro t1
    ist_nuo = np.array([t for t in range(t0 + FINESTRA - 1, t1 + 1)
                        if t + MAX_ORIZZ <= t1], dtype="int64")
    if not len(ist_nuo):
        raise CorpusViolato(
            f"R senza esempi ammissibili per i nodi nuovi in [{t0}; {t1}]")
    fuori = ist_nuo[(ist_nuo < t0) | (ist_nuo + MAX_ORIZZ > t1)]
    if len(fuori):
        raise CorpusViolato(
            f"R con istanti fuori dall'episodio: {fuori[:4].tolist()}")
    return {"nodi_iniziali": ini, "istanti_iniziali": ist_ini,
            "nodi_nuovi": nuo, "istanti_nuovi": ist_nuo,
            "manifesto": _manifesto(
                "R", np.concatenate([ini, nuo]), nuo, ist_ini,
                "corpus POST-INSTALLAZIONE: corpus originario dei nodi "
                "iniziali piu' gli esempi ammissibili delle prime 24 ore dei "
                "nodi nuovi",
                privilegiato=False, t0=int(t0), t1=int(t1),
                istanti_nodi_nuovi=len(ist_nuo),
                istanze_vecchie=_istanze(ist_ini, ini),
                istanze_nuove=_istanze(ist_nuo, nuo),
                quota_nuove=float(_istanze(ist_nuo, nuo) /
                                  max(_istanze(ist_ini, ini) +
                                      _istanze(ist_nuo, nuo), 1)),
                nota_quota=("se la quota e' molto piccola, e' un limite della "
                            "strategia R cosi' definita, NON la prova che ogni "
                            "riaddestramento completo sia inefficace"))}


def verifica_corpus(corpus: dict, nodi_nuovi, t0: int) -> dict:
    """I controlli specifici, bloccanti, dopo la costruzione."""
    m = corpus["manifesto"]
    b = m["braccio"]
    nuo = set(int(x) for x in nodi_nuovi)
    guai = []
    if b == "A":
        if not m.get("privilegiato"):
            guai.append("A deve essere marcato privilegiato")
        if m.get("istanti_anteriori_a_t0", 0) == 0:
            guai.append("A deve avere storia anteriore a t0")
        if m["nodi_nuovi_inclusi"] != len(nuo):
            guai.append(f"A deve includere tutti i {len(nuo)} nodi nuovi")
    elif b == "R":
        ist = corpus["istanti_nuovi"]
        if len(ist) and int(ist.min()) < t0:
            guai.append(f"R ha istanti dei nodi nuovi anteriori a t0: "
                        f"{int(ist.min())} < {t0}")
        if m.get("privilegiato"):
            guai.append("R non deve essere marcato privilegiato")
    elif b == "iniziale":
        if m["nodi_nuovi_inclusi"]:
            guai.append("il corpus iniziale non deve contenere nodi nuovi")
    if guai:
        raise CorpusViolato(f"corpus {b} non conforme:\n  " + "\n  ".join(guai))
    return {"braccio": b, "conforme": True, **m}
