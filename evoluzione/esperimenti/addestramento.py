#!/usr/bin/env python3
"""
Addestramento di una esecuzione del raccordo.
=============================================
Il lavoro vero, che l'orchestratore chiama. Conserva il protocollo:

  * nodi e periodi ammessi all'addestramento;
  * selezione del punto di controllo sulla VALIDAZIONE INDUTTIVA;
  * valutazione del punto SELEZIONATO, in modalita' congelata;
  * salvataggio delle predizioni e controllo delle chiavi;
  * configurazione effettiva e manifesti per tentativo.

DUE FINESTRE DISTINTE, da non confondere:

    storia del DESCRITTORE     96 passi, ventiquattro ore
    finestra dinamica recente  12 passi, tre ore

IL CONTRATTO SULLE ECCEZIONI.

    perdita non finita o divergenza        -> FallimentoMetodo
    errore tecnico riconoscibile           -> propagato al gestore dei tentativi
    ogni altro, `NotImplementedError` incluso -> propagato e SOSPENDE

I GENERATORI ARRIVANO DALL'ORCHESTRATORE, distinti per partizione e
inizializzazione, e vengono REINIZIALIZZATI a ogni variante: la seconda non
eredita lo stato consumato dalla prima.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import (  # noqa: E402
    SCHEMI_T4C, Osservazioni, estrai_diretto)
from evoluzione.componente.normalizzazione import verifica_contratto  # noqa: E402
from evoluzione.componente.predittore import (  # noqa: E402
    CANALI_T4C, FINESTRA, ORIZZONTI, PredittorePerNodo)

L_STORIA = 96
COSTANTI = frozenset({"occupazione", "conteggio"})
T4 = "data_collection/traffic4cast"
CTX = {"Madrid": (f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz", "Madrid"),
       "Londra": (f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz", "Londra"),
       "Melbourne": (f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
                     "Melbourne")}


class FallimentoMetodo(RuntimeError):
    """Perdita non finita, divergenza, risorse superate in modo riproducibile.

    Definita QUI e importata dall'orchestratore: due classi distinte con lo
    stesso nome non verrebbero riconosciute da `isinstance`, e l'eccezione
    sospenderebbe le esecuzioni invece di essere registrata come fallimento del
    metodo.
    """


def _carica(contesto, dir_masc: Path):
    tp, eti = CTX[contesto]
    M = np.load(dir_masc / f"maschere_{eti}.npz", allow_pickle=True)
    B = np.load(tp, allow_pickle=True)
    if not np.array_equal(M["sensor_ids"].astype(str),
                          B["sensor_ids"].astype(str)):
        raise ValueError(f"{contesto}: maschere e bersagli disallineati")
    ts = pd.to_datetime(M["timestamps"])
    rif = np.asarray(M["riferimento_risolto"], "float64")
    return {"sid": M["sensor_ids"].astype(str), "ts": ts,
            "ore": ts.hour.to_numpy(), "dow": ts.dayofweek.to_numpy(),
            "r": np.asarray(M["speed_grezza"], "float64") / rif[None, :],
            "vol": np.asarray(M["volume_class_grezza"], "float64"),
            "m_r": M["maschera_r"], "m_v": M["maschera_volume_class"],
            "classe": np.asarray(B["congestion_emp"], "int64"), "rif": rif}


def _partizioni(D, gen):
    """Nodi 70/15/15 dal generatore di PARTIZIONE, periodi cronologici."""
    K = D["r"].shape[1]
    p = gen["partizione"].permutation(K)
    a, b = int(K * .70), int(K * .85)
    T = D["r"].shape[0]
    e = T - max(ORIZZONTI)
    return ({"addestramento": np.sort(p[:a]), "validazione": np.sort(p[a:b]),
             "prova": np.sort(p[b:])},
            {"addestramento": np.arange(FINESTRA - 1, int(e * .70)),
             "validazione": np.arange(int(e * .70), int(e * .85)),
             "prova": np.arange(int(e * .85), e)})


def _normalizzazione(D, nodi, ist):
    """Dai SOLI nodi di addestramento nel periodo di addestramento."""
    reg = np.ix_(ist["addestramento"], nodi["addestramento"])
    rv = D["r"][reg][D["m_r"][reg]]
    vv = D["vol"][reg][D["m_v"][reg]]
    if not len(rv) or not len(vv):
        raise FallimentoMetodo("nessuna osservazione valida nel perimetro di "
                               "addestramento")
    nr = (float(rv.mean()), float(rv.std()) + 1e-6)
    nv = (float(vv.mean()), float(vv.std()) + 1e-6)
    return {"media_r": nr, "media_volume_class": nv,
            "media_conteggio": nv, "media_occupazione": (0.0, 1e-6)}, nr, nv


def _canali(D, nr, nv):
    T, K = D["r"].shape
    x = np.zeros((T, len(CANALI_T4C), K), dtype="float32")
    x[:, 0] = (np.where(D["m_r"], D["r"], 0.0) - nr[0]) / nr[1]
    x[:, 1] = (np.where(D["m_v"], D["vol"], 0.0) - nv[0]) / nv[1]
    x[:, 2] = D["m_r"]; x[:, 3] = D["m_v"]
    o, w = D["ore"], D["dow"]
    for i, c in enumerate([np.sin(2 * np.pi * o / 24), np.cos(2 * np.pi * o / 24),
                           np.sin(2 * np.pi * w / 7), np.cos(2 * np.pi * w / 7),
                           (w >= 5).astype("float64")]):
        x[:, 4 + i] = c[:, None]
    if not np.isfinite(x).all():
        raise FallimentoMetodo("ingressi non finiti dopo la preparazione")
    return x


def _descrittori(D, nodi, t_rif, variante, norm):
    S = SCHEMI_T4C[variante]
    d = len(S["statistiche"]) + len(S["disponibilita"])
    T = D["r"].shape[0]
    Z = np.zeros((len(nodi), d), dtype="float32")
    for i, k in enumerate(nodi):
        oss = Osservazioni(
            istanti=np.arange(T),
            r=np.where(D["m_r"][:, k], D["r"][:, k], np.nan),
            f=np.where(D["m_v"][:, k], D["vol"][:, k], np.nan),
            o=np.full(T, np.nan), classe=D["classe"][:, k],
            ora_locale=D["ore"], t0=max(t_rif - L_STORIA, 0))
        e = estrai_diretto(oss, t=t_rif, L=L_STORIA, sensor_id=str(k),
                           schema=variante, norm=norm, sorgente="traffic4cast",
                           canali_costanti=COSTANTI)
        Z[i] = np.concatenate([e.statistics, e.availability])
    if not np.isfinite(Z).all():
        raise FallimentoMetodo("descrittori non finiti")
    return torch.as_tensor(Z)


def _lotto(x, classe, istanti, nodi):
    X = np.stack([x[t - FINESTRA + 1:t + 1] for t in istanti])   # (B,T,C,K)
    X = torch.as_tensor(X).permute(0, 2, 3, 1)[:, :, nodi]       # (B,C,K,T)
    Y = torch.as_tensor(np.stack(
        [np.stack([classe[t + h] for h in ORIZZONTI], -1) for t in istanti]
    )[:, nodi]) - 1
    return X, Y.clamp(0, 2)


def addestra_una(E, reg, cfg, gen, radice: Path) -> Path:
    """Una esecuzione. Restituisce il percorso delle predizioni salvate."""
    dir_masc = radice / "maschere"
    D = _carica(E.contesto, dir_masc)
    nodi, ist = _partizioni(D, gen)
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    S = SCHEMI_T4C[E.variante]
    verifica_contratto(S["statistiche"], S["disponibilita"], NORM,
                       f"{E.variante}/traffic4cast", canali_costanti=COSTANTI)
    x = _canali(D, nr, nv)
    K = D["r"].shape[1]
    d_desc = len(S["statistiche"]) + len(S["disponibilita"])

    reg.dati(partizione_nodi=np.concatenate([nodi[k] for k in nodi]),
             partizione_temporale={k: [int(v[0]), int(v[-1])]
                                   for k, v in ist.items()},
             preprocessing={"storia_descrittore_passi": L_STORIA,
                            "finestra_dinamica_passi": FINESTRA},
             normalizzazione=np.array([nr, nv]))
    reg.artefatto("riferimento", oggetto=D["rif"], politica="external_fixed_resolved")

    # -- il modello: generatore di INIZIALIZZAZIONE, reinizializzato ---------
    seme_i = int(gen["inizializzazione"].integers(0, 2**31 - 1))
    torch.manual_seed(seme_i)
    m = PredittorePerNodo(d_desc, 5, sorgente="traffic4cast")
    opt = torch.optim.Adam(m.parameters(), lr=cfg["passo"])
    stat = torch.as_tensor(np.stack([
        D["m_r"].mean(0), np.zeros(K), np.ones(K), np.zeros(K), np.ones(K)],
        1).astype("float32"))
    dtr = _descrittori(D, nodi["addestramento"],
                       int(ist["addestramento"][-1]), E.variante, NORM)
    dva = _descrittori(D, nodi["validazione"],
                       int(ist["validazione"][0]), E.variante, NORM)
    reg.modello(m, n_nodi=K, **{k: cfg[k] for k in
                                ("epoche", "lotto", "passo", "pazienza")})

    migliore, epoca, pazienza, ck = float("inf"), -1, 0, radice / "raccordo" / \
        f"ck_{E.contesto}_p{E.partizione}_s{E.inizializzazione}_{E.variante}.pt"
    ck.parent.mkdir(parents=True, exist_ok=True)
    g = np.random.default_rng(seme_i)
    for ep in range(cfg["epoche"]):
        m.train()
        idx = g.choice(ist["addestramento"], size=min(cfg["lotto"],
                                                      len(ist["addestramento"])),
                       replace=False)
        X, Y = _lotto(x, D["classe"], np.sort(idx), nodi["addestramento"])
        out = m(X, dtr, stat[nodi["addestramento"]])
        L = F.cross_entropy(out.reshape(-1, 3), Y.reshape(-1))
        if not torch.isfinite(L):
            raise FallimentoMetodo(f"perdita non finita all'epoca {ep}")
        opt.zero_grad(); L.backward(); opt.step()
        m.eval()
        with torch.inference_mode():
            Xv, Yv = _lotto(x, D["classe"], ist["validazione"][:cfg["lotto"]],
                            nodi["validazione"])
            pv = float(F.cross_entropy(
                m(Xv, dva, stat[nodi["validazione"]]).reshape(-1, 3),
                Yv.reshape(-1)))
        if not np.isfinite(pv):
            raise FallimentoMetodo(f"validazione non finita all'epoca {ep}")
        if pv < migliore:                       # a parita', la PRIMA
            migliore, epoca, pazienza = pv, ep, 0
            torch.save({"state_dict": m.state_dict(), "epoca": ep,
                        "validazione": pv}, ck)
        else:
            pazienza += 1
            if pazienza >= cfg["pazienza"]:
                reg.evento(f"arresto anticipato all'epoca {ep}: non e' un "
                           f"fallimento")
                break
    if epoca < 0:
        raise FallimentoMetodo("nessuna epoca ha migliorato la validazione")

    # -- valutazione del punto SELEZIONATO, in modalita' congelata ----------
    m2 = PredittorePerNodo(d_desc, 5, sorgente="traffic4cast")
    m2.load_state_dict(torch.load(ck, weights_only=False)["state_dict"])
    m2.eval()
    reg.artefatto("punto_di_controllo", percorso=ck, epoca=epoca,
                  validazione=migliore)
    dpr = _descrittori(D, nodi["prova"], int(ist["prova"][0]), E.variante, NORM)
    righe = []
    with torch.inference_mode():
        for t in ist["prova"]:
            X, Y = _lotto(x, D["classe"], [int(t)], nodi["prova"])
            o = torch.softmax(m2(X, dpr, stat[nodi["prova"]])[0], -1).numpy()
            for i, k in enumerate(nodi["prova"]):
                for h, hz in enumerate(ORIZZONTI):
                    righe.append((E.contesto, E.partizione, E.inizializzazione,
                                  int(k), int(t), int(hz), int(Y[0, i, h]),
                                  *o[i, h]))
    P = pd.DataFrame(righe, columns=[
        "contesto", "partizione", "inizializzazione", "nodo", "istante",
        "orizzonte", "vero", "p1", "p2", "p3"])
    if P.duplicated(["nodo", "istante", "orizzonte"]).any():
        raise ValueError("chiavi duplicate nelle predizioni")
    out = ck.with_name(ck.name.replace("ck_", "pred_").replace(".pt", ".csv"))
    P.to_csv(out, index=False)
    reg.evento(f"epoca selezionata {epoca}, validazione {migliore:.6f}, "
               f"{len(P):,} predizioni")
    return out
