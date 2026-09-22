#!/usr/bin/env python3
"""
Valutazione sull'intero perimetro di validazione.
==================================================
**Non la media delle perdite dei lotti**: numerosita' e massa dei pesi validi
differiscono fra lotti, e mediarle darebbe un numero che non corrisponde alla
perdita sull'insieme.

Si accumulano, per ciascun orizzonte:

    A_h = somma su celle valide di  w_y x [-log p(y)]
    B_h = somma su celle valide di  w_y

e poi

    L = (1/4) x somma_h  A_h / B_h

che e' la medesima formula del raccordo, calcolata su tutte le origini.

I TRE PERIMETRI, che differiscono SOLTANTO per gli istanti:

    V-prefix   i primi `lotto` istanti — cio' che il codice usava
    V-full     TUTTE le origini ammissibili del periodo
    V-rest     tutte tranne le prime — diagnostica, NON indipendente da V-full

**La popolazione dei nodi resta la stessa**: i nodi della rete iniziale nel
periodo di validazione. Confrontare il prefisso su una popolazione con il
periodo intero su un'altra cambierebbe due dimensioni.

LA VALUTAZIONE NON DEVE:

    modificare i buffer della BatchNorm  -> `eval()` e `inference_mode()`
    consumare il generatore del training -> non ne usa alcuno
    lasciare il modello in valutazione   -> `train()` si ripristina fuori
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F

ORIZZONTI = (1, 2, 4, 8)


class ValutazioneViolata(RuntimeError):
    """Il perimetro o le chiavi non sono quelli attesi."""


def perimetri(istanti, prefisso: int) -> dict:
    """I tre perimetri, sugli stessi nodi.

    `V-rest` **non e' indipendente da V-full**: ne e' un sottoinsieme, e serve a
    rendere visibile cio' che accade fuori dalla finestra storicamente usata.
    """
    ist = np.asarray(istanti, dtype="int64")
    if len(ist) <= prefisso:
        raise ValutazioneViolata(
            f"il periodo ha {len(ist)} istanti, il prefisso ne chiede "
            f"{prefisso}: V-rest sarebbe vuoto")
    return {"V-prefix": ist[:prefisso], "V-full": ist,
            "V-rest": ist[prefisso:]}


def valuta(m, x, classe, statiche, nodi, istanti, pesi, descrittore=None,
           lotto: int = 256) -> dict:
    """La perdita sull'intero perimetro, per accumulo.

    `m` viene messo in valutazione e **lasciato tale**: il ripristino di
    `train()` spetta al chiamante, prima dell'aggiornamento successivo.
    """
    from evoluzione.esperimenti.addestramento import _lotto
    nodi = np.asarray(nodi, dtype="int64")
    ist = np.asarray(istanti, dtype="int64")
    A = np.zeros(len(ORIZZONTI))
    B = np.zeros(len(ORIZZONTI))
    n_celle = np.zeros(len(ORIZZONTI), dtype="int64")
    m.eval()
    S = torch.as_tensor(statiche[nodi].astype("float32"))
    with torch.inference_mode():
        for i in range(0, len(ist), lotto):
            blocco = ist[i:i + lotto]
            X, Y, M = _lotto(x, classe, blocco, nodi)
            out = m(X, node_ids=[int(v) for v in nodi],
                    descriptor=descrittore, static_inputs=S)
            for h in range(len(ORIZZONTI)):
                mm = M[..., h].reshape(-1)
                if not bool(mm.any()):
                    continue
                o = out[..., h, :].reshape(-1, out.shape[-1])[mm]
                y = Y[..., h].reshape(-1)[mm]
                # `cross_entropy` con `weight` e `reduction="none"`
                # restituisce gia' w_y x [-log p(y)]: e' il numeratore A_h.
                ce = F.cross_entropy(o, y, weight=pesi, reduction="none")
                # **SOMMA IN DOPPIA PRECISIONE**: i tensori sono a 32 bit, e
                # sommarli in quella precisione rende il risultato dipendente
                # dalla dimensione del lotto, con scarti relativi ~1e-8.
                A[h] += float(ce.double().sum())
                B[h] += float(pesi[y].double().sum())
                n_celle[h] += int(mm.sum())
    validi = B > 0
    if not validi.any():
        raise ValutazioneViolata("nessuna cella valida nel perimetro")
    per_h = np.where(validi, A / np.maximum(B, 1e-12), np.nan)
    return {"perdita": float(np.nanmean(per_h)),
            "per_orizzonte": per_h.tolist(),
            "orizzonti_contribuenti": int(validi.sum()),
            "celle_valide": n_celle.tolist(),
            "celle_totali": int(n_celle.sum()),
            "istanti": len(ist), "nodi": len(nodi),
            "massa_pesi": B.tolist()}


def valuta_scomposto(m, x, classe, statiche, nodi, istanti, pesi,
                     prefisso: int, descrittore=None, lotto: int = 256) -> dict:
    """I TRE perimetri con UNA SOLA inferenza sull'intera validazione.

    Si accumulano numeratori e denominatori **separatamente** per i primi
    `prefisso` istanti e per i rimanenti; V-full si ottiene sommandoli.

        A_full = A_prefix + A_rest        B_full = B_prefix + B_rest

    E' esatto, non approssimato: A_h e B_h sono somme, e sommare due
    sottoinsiemi disgiunti da' la somma dell'unione. **Costa 405 passaggi
    invece di 1.215.**
    """
    from evoluzione.esperimenti.addestramento import _lotto
    nodi = np.asarray(nodi, dtype="int64")
    ist = np.asarray(istanti, dtype="int64")
    if len(ist) <= prefisso:
        raise ValutazioneViolata(
            f"il periodo ha {len(ist)} istanti, il prefisso ne chiede "
            f"{prefisso}")
    soglia = int(ist[prefisso - 1])        # l'ultimo istante del prefisso
    H = len(ORIZZONTI)
    acc = {k: {"A": np.zeros(H), "B": np.zeros(H),
               "n": np.zeros(H, dtype="int64")}
           for k in ("V-prefix", "V-rest")}
    m.eval()
    S = torch.as_tensor(statiche[nodi].astype("float32"))
    with torch.inference_mode():
        for i in range(0, len(ist), lotto):
            blocco = ist[i:i + lotto]
            X, Y, M = _lotto(x, classe, blocco, nodi)
            out = m(X, node_ids=[int(v) for v in nodi],
                    descriptor=descrittore, static_inputs=S)
            # la partizione del LOTTO fra prefisso e resto
            e_pre = torch.as_tensor(blocco <= soglia)
            for k, sel in (("V-prefix", e_pre), ("V-rest", ~e_pre)):
                if not bool(sel.any()):
                    continue
                for h in range(H):
                    mm = (M[..., h] & sel[:, None]).reshape(-1)
                    if not bool(mm.any()):
                        continue
                    o = out[..., h, :].reshape(-1, out.shape[-1])[mm]
                    y = Y[..., h].reshape(-1)[mm]
                    ce = F.cross_entropy(o, y, weight=pesi, reduction="none")
                    acc[k]["A"][h] += float(ce.double().sum())
                    acc[k]["B"][h] += float(pesi[y].double().sum())
                    acc[k]["n"][h] += int(mm.sum())

    def perdita_da(A, B, n):
        validi = B > 0
        if not validi.any():
            raise ValutazioneViolata("nessuna cella valida")
        per_h = np.where(validi, A / np.maximum(B, 1e-12), np.nan)
        return {"perdita": float(np.nanmean(per_h)),
                "per_orizzonte": per_h.tolist(),
                "orizzonti_contribuenti": int(validi.sum()),
                "celle_valide": n.tolist(), "celle_totali": int(n.sum())}

    fuori = {k: perdita_da(v["A"], v["B"], v["n"]) for k, v in acc.items()}
    fuori["V-full"] = perdita_da(
        acc["V-prefix"]["A"] + acc["V-rest"]["A"],
        acc["V-prefix"]["B"] + acc["V-rest"]["B"],
        acc["V-prefix"]["n"] + acc["V-rest"]["n"])
    fuori["_nota"] = ("V-full e' ottenuto sommando i numeratori e i "
                      "denominatori dei due sottoinsiemi: e' ESATTO, non "
                      "approssimato. V-rest non e' indipendente da V-full.")
    return fuori


def confronta_perimetri(m, x, classe, statiche, nodi, istanti, pesi,
                        prefisso: int, descrittore=None) -> dict:
    """Le tre valutazioni con TRE inferenze separate.

    **Serve a collaudare `valuta_scomposto`**, non a usarlo in produzione:
    costa il triplo e dovrebbe dare gli stessi numeri.
    """
    P = perimetri(istanti, prefisso)
    fuori = {}
    for nome, ist in P.items():
        fuori[nome] = valuta(m, x, classe, statiche, nodi, ist, pesi,
                             descrittore)
    fuori["_nota"] = ("tre inferenze separate: il riferimento contro cui si "
                      "verifica la scomposizione")
    return fuori
