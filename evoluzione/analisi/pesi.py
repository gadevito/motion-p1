#!/usr/bin/env python3
"""
Artefatto dei pesi di classe: uno per citta' e partizione.
==========================================================
NOVE VETTORI, uno per ciascuna combinazione citta' × partizione dei nodi.
Ciascuno e' CONDIVISO fra le tre inizializzazioni, le due varianti,
addestramento, validazione e prova, e tutte le repliche del ricampionamento.

    w_k = N_train / (3 * n_k,train)

**STIMATI SUI SOLI NODI E PERIODO DI ADDESTRAMENTO.** Non si stimano ne' si
aggiornano sui nodi esclusi, sulla validazione, sulla prova o sul campione
ricampionato.

LE DIFFERENZE FRA PARTIZIONI SONO PREVISTE E CORRETTE: entro ciascuna coppia la
metrica e' identica, sicche' il confronto appaiato non ne e' viziato.
L'aggregazione fra partizioni rappresenta il protocollo che stima i pesi dai dati
di addestramento disponibili, non una singola funzione di perdita globale.

LA POPOLAZIONE DI CONTEGGIO E' DICHIARATA, non lasciata implicita nel caricatore.
Contribuiscono a N_train e n_k,train i BERSAGLI VALIDI delle celle (nodo,
istante) che soddisfano tutte queste condizioni:

    il nodo appartiene alla partizione di ADDESTRAMENTO;
    l'istante di previsione appartiene al periodo di ADDESTRAMENTO;
    la classe del bersaglio e' assegnata, cioe' maggiore di zero.

**Ogni cella conta UNA VOLTA PER ORIZZONTE**: un istante con quattro orizzonti
contribuisce quattro bersagli, perche' quattro sono le previsioni su cui la
perdita e' calcolata. Il conteggio ripetuto e' voluto e dichiarato.

LA RIDUZIONE DELLA PERDITA, per ciascun orizzonte:

    L_h = somma_j w[y_j] * (-log p_j(y_j))  /  somma_j w[y_j]

sui soli j VALIDI, e poi la media sui quattro orizzonti. **Un orizzonte senza
bersagli validi in un lotto non contribuisce a quella media**, e il fatto viene
registrato: sostituirlo con zero abbasserebbe la perdita, sostituirlo con la
media degli altri la inventerebbe.

SE UNA CLASSE MANCA DALL'ADDESTRAMENTO la configurazione si INTERROMPE. Non si
introducono pesi infiniti, lisciamento o semi sostitutivi senza una decisione
esplicita.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

VERSIONE_PESI = "1.0"
CLASSI = (1, 2, 3)          # verde, intermedia, critica
N_ORIZZONTI = 4


class ClasseAssente(RuntimeError):
    """Una classe manca dal periodo e dai nodi di addestramento."""


@dataclass
class Pesi:
    contesto: str
    partizione: int
    ordine_classi: list
    conteggi: list
    pesi: list
    n_train: int
    nodi_addestramento: list
    periodo_addestramento: list
    conteggio_per_orizzonte: bool
    regola_riduzione: str
    regola_aggregazione: str
    versione_pesi: str
    versione_codice: str
    impronta: str
    istante: str

    def vettore(self) -> np.ndarray:
        """Il vettore indicizzato per classe 0..2, come i bersagli."""
        return np.asarray(self.pesi, dtype="float64")

    def as_dict(self):
        return asdict(self)


def _impronta(v) -> str:
    h = hashlib.sha256(np.ascontiguousarray(
        np.asarray(v, dtype="float64")).tobytes())
    return h.hexdigest()[:16]


def calcola(contesto: str, partizione: int, classe: np.ndarray,
            nodi_addestramento, istanti_addestramento, orizzonti,
            versione_codice: str = "") -> Pesi:
    """I pesi, dai SOLI nodi e periodo di addestramento.

    `classe` ha forma (T, S) con 0 dove il bersaglio non e' assegnato.
    `orizzonti` sono i passi, e ogni cella conta una volta per ciascuno.
    """
    nodi = np.asarray(nodi_addestramento, dtype="int64")
    ist = np.asarray(istanti_addestramento, dtype="int64")
    conteggi = np.zeros(len(CLASSI), dtype="int64")
    for h in orizzonti:
        t = ist + h
        t = t[t < classe.shape[0]]
        if not len(t):
            continue
        y = classe[np.ix_(t, nodi)]
        for i, k in enumerate(CLASSI):
            conteggi[i] += int((y == k).sum())
    N = int(conteggi.sum())
    if N == 0:
        raise ClasseAssente(
            f"{contesto} p{partizione}: nessun bersaglio valido "
            f"nell'addestramento")
    manca = [k for i, k in enumerate(CLASSI) if conteggi[i] == 0]
    if manca:
        raise ClasseAssente(
            f"{contesto} p{partizione}: le classi {manca} mancano "
            f"dall'addestramento. La configurazione si interrompe: non si "
            f"introducono pesi infiniti, lisciamento o semi sostitutivi senza "
            f"una decisione esplicita.")
    w = N / (len(CLASSI) * conteggi.astype("float64"))
    return Pesi(
        contesto=contesto, partizione=partizione, ordine_classi=list(CLASSI),
        conteggi=conteggi.tolist(), pesi=w.tolist(), n_train=N,
        nodi_addestramento=nodi.tolist(),
        periodo_addestramento=[int(ist[0]), int(ist[-1])],
        conteggio_per_orizzonte=True,
        regola_riduzione=("L_h = somma w[y]*(-log p(y)) / somma w[y], sui soli "
                          "bersagli validi"),
        regola_aggregazione=("media aritmetica sui quattro orizzonti; un "
                             "orizzonte senza bersagli validi non contribuisce "
                             "e il fatto viene registrato"),
        versione_pesi=VERSIONE_PESI, versione_codice=versione_codice,
        impronta=_impronta(w),
        istante=datetime.now(timezone.utc).isoformat())


def percorso(dir_pesi: Path, contesto: str, partizione: int) -> Path:
    return dir_pesi / f"pesi_{contesto}_p{partizione}.json"


def salva(P: Pesi, dir_pesi: Path) -> Path:
    dir_pesi.mkdir(parents=True, exist_ok=True)
    f = percorso(dir_pesi, P.contesto, P.partizione)
    f.write_text(json.dumps(P.as_dict(), indent=2, ensure_ascii=False))
    return f


def carica(dir_pesi: Path, contesto: str, partizione: int) -> Pesi:
    """Lo STESSO artefatto che l'addestramento ha consumato.

    Addestramento e analisi non ricalcolano i pesi per conto proprio: due
    calcoli indipendenti possono divergere, ed e' precisamente cio' che e'
    accaduto nella prima campagna.
    """
    f = percorso(dir_pesi, contesto, partizione)
    if not f.exists():
        raise FileNotFoundError(
            f"artefatto dei pesi assente: {f}. Addestramento e analisi devono "
            f"consumare lo stesso artefatto, non ricalcolarlo.")
    return Pesi(**json.loads(f.read_text()))


# ---------------------------------------------------------- riduzione -------
def perdita_pesata(logit_o_prob, y, w, gia_probabilita=False, eps=1e-7):
    """L_h su un insieme di bersagli validi. Restituisce `nan` se vuoto."""
    if len(y) == 0:
        return float("nan")
    p = np.asarray(logit_o_prob, dtype="float64")
    if not gia_probabilita:
        p = p - p.max(1, keepdims=True)
        p = np.exp(p)
        p = p / p.sum(1, keepdims=True)
    pt = np.clip(p[np.arange(len(y)), y], eps, 1.0)
    wy = np.asarray(w, dtype="float64")[y]
    den = wy.sum()
    return float((wy * -np.log(pt)).sum() / den) if den > 0 else float("nan")


def media_orizzonti(perdite) -> tuple:
    """(media, quanti orizzonti hanno contribuito).

    Un orizzonte senza bersagli validi NON contribuisce: sostituirlo con zero
    abbasserebbe la perdita, con la media degli altri la inventerebbe.
    """
    v = [x for x in perdite if np.isfinite(x)]
    if not v:
        return float("nan"), 0
    return float(np.mean(v)), len(v)
