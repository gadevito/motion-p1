#!/usr/bin/env python3
"""
Adattamento F: copie INDIPENDENTI dal punto di controllo E congelato.
======================================================================

    Checkpoint E congelato
    ├── copia per F1 sui nodi di validazione
    ├── copia per F2 sui nodi di validazione
    ├── …
    ├── copia per F6 sui nodi di validazione
    └── copia NUOVA per F sul test, con la configurazione selezionata

I CINQUE VINCOLI BLOCCANTI:

    1. ogni combinazione della griglia RIPARTE da E: nessun adattamento
       cumulativo fra candidati;
    2. ottimizzatore NUOVO per ogni candidato;
    3. la selezione trasferisce al test i soli IPERPARAMETRI, non gli embedding
       adattati sulla validazione;
    4. il punto di controllo E originale resta IMMUTATO;
    5. nodi di validazione e test hanno REGISTRI DISTINTI.

Le copie si eseguono in sequenza: **non devono risiedere tutte in memoria**.

F NON CARICA L'ARTEFATTO CANONICO INIZIALE: parte da E gia' addestrato, di cui
mantiene backbone, statiche e teste. Caricarvi lo stato iniziale cancellerebbe
l'addestramento.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import torch
import torch.nn.functional as F

from evoluzione.componente.identita import (
    AdaptedNodeEmbedding, LearnedNodeEmbedding)
from evoluzione.componente.predittore import ORIZZONTI, PredittorePerNodo


class AdattamentoViolato(RuntimeError):
    """Un vincolo dell'adattamento non e' rispettato."""


def impronta_stato(m) -> str:
    h = hashlib.sha256()
    for k, v in sorted(m.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()[:16]


def carica_E(percorso: Path, d_stat: int):
    """Il punto di controllo E, con la sua mappa nodo-riga.

    Restituisce (stato, nodi_iniziali, impronta): **lo stato non si modifica**,
    e l'impronta serve a verificarlo alla fine.
    """
    d = torch.load(percorso, map_location="cpu", weights_only=False)
    for k in ("state_dict", "nodi_iniziali"):
        if k not in d:
            raise AdattamentoViolato(
                f"{Path(percorso).name}: manca «{k}». Senza la mappa nodo-riga "
                f"i pesi non sono interpretabili.")
    h = hashlib.sha256()
    for k, v in sorted(d["state_dict"].items()):
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return d, list(d["nodi_iniziali"]), h.hexdigest()[:16]


def copia_da_E(d_E: dict, nodi_iniziali, nodi_nuovi, d_stat: int,
               sorgente: str = "traffic4cast"):
    """Una copia INDIPENDENTE di E, con embedding nuovi per l'episodio.

    Gli iniziali sono copiati e **congelati**; i nuovi partono dalla **media**
    degli iniziali, come regola deterministica.
    """
    base = LearnedNodeEmbedding(nodi_iniziali)
    # le righe di E, non un'inizializzazione casuale
    with torch.no_grad():
        base.embedding.copy_(d_E["state_dict"]["identita.embedding"])
    forn = AdaptedNodeEmbedding(base, nodi_nuovi)
    m = PredittorePerNodo(0, d_stat, sorgente=sorgente, identita=forn)
    # i moduli COMUNI vengono da E: backbone, statiche, teste
    sd = m.state_dict()
    comuni = {k: v for k, v in d_E["state_dict"].items()
              if not k.startswith("identita.")}
    mancanti = [k for k in comuni if k not in sd]
    if mancanti:
        raise AdattamentoViolato(f"E non accoglie i comuni: {mancanti[:4]}")
    with torch.no_grad():
        for k, v in comuni.items():
            sd[k].copy_(v)
    return m, forn


def adatta(m, forn: AdaptedNodeEmbedding, lotti, pesi, passo: float,
           aggiornamenti: int, registro: list | None = None):
    """L'adattamento: Adam, nessun decadimento, nessun arresto anticipato.

    **Ciascun aggiornamento usa tutti gli esempi ammissibili del nodo.** Se non
    ve ne sono, non si esegue alcun aggiornamento e lo si registra.
    """
    if not lotti:
        if registro is not None:
            registro.append({"eseguito": False,
                             "motivo": "adattamento non eseguibile per assenza "
                                       "di esempi"})
        return 0
    m.eval()                       # BatchNorm e buffer fermi
    for p in m.parameters():
        p.requires_grad_(False)
    for p in forn.parametri_adattabili():
        p.requires_grad_(True)
    # OTTIMIZZATORE NUOVO, e solo sui parametri adattabili
    opt = torch.optim.Adam(forn.parametri_adattabili(), lr=passo,
                           weight_decay=0.0)
    fatti = 0
    for _ in range(aggiornamenti):
        opt.zero_grad()
        perdite = []
        for X, nodi, Y, M, S in lotti:          # LOTTO COMPLETO per nodo
            out = m(X, node_ids=nodi, static_inputs=S)
            for h in range(len(ORIZZONTI)):
                mm = M[..., h].reshape(-1)
                if not bool(mm.any()):
                    continue
                o = out[..., h, :].reshape(-1, 3)[mm]
                y = Y[..., h].reshape(-1)[mm]
                perdite.append(F.cross_entropy(o, y, weight=pesi))
        if not perdite:
            break
        L = torch.stack(perdite).mean()
        L.backward()
        opt.step()
        fatti += 1
    if registro is not None:
        registro.append({"eseguito": True, "aggiornamenti": fatti,
                         "passo": passo, "richiesti": aggiornamenti})
    return fatti


def verifica_vincoli(m, forn, d_E, impronta_E_prima, iniziali_prima,
                     percorso_E: Path) -> dict:
    """I cinque vincoli, verificati DOPO l'adattamento."""
    guai = []
    # 4. il punto di controllo E originale resta immutato
    _, _, dopo = carica_E(percorso_E, 0)
    if dopo != impronta_E_prima:
        guai.append("il punto di controllo E e' stato modificato su disco")
    # gli embedding iniziali non si muovono
    if not torch.equal(forn.iniziali, iniziali_prima):
        guai.append("gli embedding INIZIALI sono stati modificati")
    # i moduli comuni non si muovono
    sd = m.state_dict()
    mossi = [k for k, v in d_E["state_dict"].items()
             if not k.startswith("identita.") and k in sd
             and not torch.equal(sd[k], v)]
    if mossi:
        guai.append(f"moduli comuni modificati: {mossi[:4]}")
    if guai:
        raise AdattamentoViolato("; ".join(guai))
    return {"conforme": True, "impronta_E": dopo,
            "nuovi_adattati": int(forn.nuovi.numel())}


def seleziona(candidati: dict, ordine) -> tuple:
    """La combinazione migliore; a parita', la prima dell'ordine dichiarato.

    **Trasferisce al test i soli IPERPARAMETRI**: gli embedding adattati sulla
    validazione non si riusano.
    """
    if not candidati:
        return None
    migliore = min(candidati.values())
    for k in ordine:
        if k in candidati and candidati[k] - migliore <= 1e-9:
            return k
    return None
