#!/usr/bin/env python3
"""
Campionamento uniforme per NODO, per il braccio R.
===================================================
    si estrae uniformemente un NODO della rete ampliata,
    poi un'ORIGINE ammissibile per quel nodo

**Non e' un bilanciamento a meta' fra vecchi e nuovi**: attribuisce la stessa
probabilita' a ciascun nodo, **indipendentemente dalla lunghezza della sua
storia**.

LA PROBABILITA' DI UNA SPECIFICA ORIGINE:

    Pr(i, t) = 1/K_ammissibili x 1/n_i

dove n_i e' il numero **effettivo** di origini ammissibili di quel nodo.

**Il reciproco della media NON equivale alla media dei reciproci**: un nodo
londinese con 26 origini ripete ciascuna piu' spesso di uno con 78, e anche i
nodi iniziali hanno numerosita' diverse. **Si registrano le distribuzioni, non
un rapporto complessivo.**

I NODI SENZA ESEMPI:

    non si inventano esempi
    non entrano nel campionamento
    l'embedding si inizializza secondo la regola dichiarata
    restano nella VALUTAZIONE quando hanno bersagli validi

**La probabilita' uniforme riguarda i soli nodi con almeno un esempio
utilizzabile.**

IL BUDGET NOMINALE NON CAMBIA: stesso numero di estrazioni per epoca, stessa
dimensione del lotto, stesse epoche massime, stessa regola di arresto. Il
generatore e' **dedicato** al campionamento.
"""
from __future__ import annotations

import numpy as np

ORIZZONTI = (1, 2, 4, 8)
FINESTRA = 12
MAX_ORIZZ = max(ORIZZONTI)


class CampionamentoViolato(RuntimeError):
    """La popolazione ammissibile e' vuota, o il budget e' incoerente."""


def origini_ammissibili(classe, nodi, istanti) -> dict:
    """Le origini con almeno un bersaglio valido, **per ciascun nodo**."""
    nodi = np.asarray(nodi, dtype="int64")
    ist = np.asarray(istanti, dtype="int64")
    fuori = {}
    for i, n in enumerate(nodi):
        ok = np.zeros(len(ist), dtype=bool)
        for o in ORIZZONTI:
            ok |= classe[ist + o, n] > 0
        fuori[int(n)] = ist[ok]
    return fuori


def prepara(classe, nodi_iniziali, ist_iniziali, nodi_nuovi, ist_nuovi) -> dict:
    """La popolazione ammissibile e le sue numerosita'.

    **I nodi senza alcuna origine ammissibile sono ESCLUSI dal campionamento**,
    e registrati: non si inventano esempi per loro.
    """
    A = origini_ammissibili(classe, nodi_iniziali, ist_iniziali)
    B = origini_ammissibili(classe, nodi_nuovi, ist_nuovi)
    tutte = {**A, **B}
    ammessi = [n for n, v in tutte.items() if len(v)]
    esclusi = sorted(n for n, v in tutte.items() if not len(v))
    if not ammessi:
        raise CampionamentoViolato("nessun nodo con origini ammissibili")
    nuovi = set(int(x) for x in nodi_nuovi)
    return {"origini": {n: tutte[n] for n in ammessi},
            "ammessi": np.array(sorted(ammessi), dtype="int64"),
            "esclusi": esclusi,
            "nuovi": nuovi,
            "n_i": {n: int(len(tutte[n])) for n in ammessi},
            "ammessi_nuovi": sorted(n for n in ammessi if n in nuovi),
            "ammessi_iniziali": sorted(n for n in ammessi if n not in nuovi)}


def esposizione_attesa(pop: dict, estrazioni: int) -> dict:
    """L'esposizione ATTESA per nodo e per origine, dalle numerosita' reali.

    Per nodo:    estrazioni / K
    Per origine: estrazioni / (K x n_i)   **diverso per ciascun nodo**

    Si riportano le DISTRIBUZIONI, non un rapporto complessivo: usare il
    reciproco della media darebbe un numero che nessun nodo sperimenta.
    """
    K = len(pop["ammessi"])
    per_nodo = estrazioni / K
    e_orig = {n: per_nodo / max(v, 1) for n, v in pop["n_i"].items()}
    ini = np.array([e_orig[n] for n in pop["ammessi_iniziali"]])
    nuo = np.array([e_orig[n] for n in pop["ammessi_nuovi"]])
    n_ini = np.array([pop["n_i"][n] for n in pop["ammessi_iniziali"]])
    n_nuo = np.array([pop["n_i"][n] for n in pop["ammessi_nuovi"]])

    def d(a):
        if not len(a):
            return {}
        return {"minimo": float(a.min()), "mediana": float(np.median(a)),
                "massimo": float(a.max()), "media": float(a.mean())}

    return {"nodi_ammessi": K, "estrazioni": estrazioni,
            "attese_per_nodo": per_nodo,
            "quota_attesa_nuovi": len(pop["ammessi_nuovi"]) / K,
            "n_i_iniziali": d(n_ini), "n_i_nuovi": d(n_nuo),
            "esposizione_per_origine_iniziali": d(ini),
            "esposizione_per_origine_nuovi": d(nuo),
            "rapporto_mediane": (float(np.median(nuo) / np.median(ini))
                                 if len(ini) and len(nuo) else None),
            "nota": ("il reciproco della media NON equivale alla media dei "
                     "reciproci: si riportano le distribuzioni")}


def campiona(pop: dict, quante: int, rng) -> tuple:
    """`quante` coppie (nodo, origine), uniformi sul NODO.

    `rng` e' il generatore **dedicato** al campionamento, distinto da quelli di
    partizione e inizializzazione.
    """
    K = len(pop["ammessi"])
    idx = rng.integers(0, K, size=quante)
    nodi = pop["ammessi"][idx]
    orig = np.empty(quante, dtype="int64")
    for j, n in enumerate(nodi):
        v = pop["origini"][int(n)]
        orig[j] = v[rng.integers(0, len(v))]
    return nodi, orig


# ------------------------------------------------------- PER ORIGINE (E3) --
# R-orig e R-mon: si estrae uniformemente una COPPIA (nodo, origine) fra tutte
# quelle ammissibili della rete ampliata.
#
#     Pr(i, t) = 1 / N,   N = somma_i n_i
#
# Ogni origine ha la stessa probabilita', quindi un nodo pesa quanto la sua
# storia: un nodo nuovo con 77 origini pesa 77/N, uno iniziale con 7.000 pesa
# 7.000/N. **Il rapporto atteso fra le riviste di un'origine nuova e di una
# iniziale e' 1**: e' il controllo obbligatorio di E3. Stesso budget, stesso
# generatore dedicato, stessi nodi esclusi di `prepara`.


def _coppie(pop: dict) -> tuple:
    """Le coppie ammissibili appiattite, costruite UNA volta e conservate."""
    if "coppie_nodo" not in pop:
        nn = np.concatenate([np.full(len(pop["origini"][int(n)]), int(n),
                                     dtype="int64") for n in pop["ammessi"]])
        oo = np.concatenate([np.asarray(pop["origini"][int(n)], dtype="int64")
                             for n in pop["ammessi"]])
        pop["coppie_nodo"], pop["coppie_orig"] = nn, oo
    return pop["coppie_nodo"], pop["coppie_orig"]


def campiona_per_origine(pop: dict, quante: int, rng) -> tuple:
    """`quante` coppie (nodo, origine), uniformi sulla COPPIA."""
    nn, oo = _coppie(pop)
    idx = rng.integers(0, len(nn), size=quante)
    return nn[idx], oo[idx]


def esposizione_attesa_per_origine(pop: dict, estrazioni: int) -> dict:
    """Esposizione attesa: `estrazioni / N` per OGNI origine, iniziale o
    nuova; per nodo, proporzionale a n_i."""
    nn, _ = _coppie(pop)
    N = int(len(nn))
    per_orig = estrazioni / N
    n_ini = np.array([pop["n_i"][n] for n in pop["ammessi_iniziali"]])
    n_nuo = np.array([pop["n_i"][n] for n in pop["ammessi_nuovi"]])

    def d(a):
        if not len(a):
            return {}
        return {"minimo": float(a.min()), "mediana": float(np.median(a)),
                "massimo": float(a.max()), "media": float(a.mean())}

    return {"nodi_ammessi": int(len(pop["ammessi"])), "coppie_ammesse": N,
            "estrazioni": estrazioni,
            "attese_per_origine": per_orig,
            "quota_attesa_nuovi": float(n_nuo.sum() / N) if len(n_nuo) else 0.0,
            "n_i_iniziali": d(n_ini), "n_i_nuovi": d(n_nuo),
            "esposizione_per_origine_iniziali": d(np.full(len(n_ini), per_orig)),
            "esposizione_per_origine_nuovi": d(np.full(len(n_nuo), per_orig)),
            "rapporto_mediane": 1.0 if len(n_ini) and len(n_nuo) else None,
            "nota": ("uniforme per origine: ogni coppia (nodo, origine) ha la "
                     "stessa probabilita'; il rapporto atteso nuovi/iniziali "
                     "e' 1 per costruzione, quello realizzato va verificato")}


def esposizione_realizzata(pop: dict, nodi, origini) -> dict:
    """Che cosa il campionamento ha DAVVERO prodotto.

    Frequenza di campionamento e contributo all'apprendimento sono cose
    distinte: qui si misura la prima, e si riportano le grandezze che
    permettono di stimare la seconda.
    """
    nodi = np.asarray(nodi, dtype="int64")
    origini = np.asarray(origini, dtype="int64")
    est, dist, rip = {}, {}, {}
    for n in pop["ammessi"]:
        m = nodi == n
        est[int(n)] = int(m.sum())
        o = origini[m]
        dist[int(n)] = int(len(np.unique(o)))
        rip[int(n)] = float(len(o) / max(len(np.unique(o)), 1))
    nuovi = pop["ammessi_nuovi"]
    tot = int(len(nodi))
    q = sum(est[n] for n in nuovi) / max(tot, 1)

    def d(v):
        a = np.array(v, dtype="float64")
        return {"minimo": float(a.min()), "mediana": float(np.median(a)),
                "massimo": float(a.max()), "media": float(a.mean())} if len(a) \
            else {}

    return {"estrazioni_totali": tot,
            "quota_realizzata_nuovi": q,
            "quota_attesa_nuovi": len(nuovi) / len(pop["ammessi"]),
            "estrazioni_per_nodo": {
                "iniziali": d([est[n] for n in pop["ammessi_iniziali"]]),
                "nuovi": d([est[n] for n in nuovi])},
            "origini_distinte_visitate": {
                "iniziali": d([dist[n] for n in pop["ammessi_iniziali"]]),
                "nuovi": d([dist[n] for n in nuovi])},
            "ripetizioni_per_origine": {
                "iniziali": d([rip[n] for n in pop["ammessi_iniziali"]]),
                "nuovi": d([rip[n] for n in nuovi])},
            "nodi_esclusi_dal_campionamento": pop["esclusi"]}
