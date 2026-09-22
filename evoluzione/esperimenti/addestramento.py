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
from evoluzione.componente.identita import (  # noqa: E402
    LearnedNodeEmbedding, NoIdentity, ObservableIdentityEncoder)
from evoluzione.componente.canonico import (  # noqa: E402
    CARICANO, CanonicoViolato, applica as applica_canonico,
    carica as carica_canonico, stato_iniziale_completo,
    verifica as verifica_canonico)
from evoluzione.analisi.pesi import (  # noqa: E402
    ClasseAssente, calcola as calcola_pesi, carica as carica_pesi,
    media_orizzonti, percorso as percorso_pesi, salva as salva_pesi)

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
    """(X, Y, M) con la MASCHERA di validita' del bersaglio.

    `classe` vale ZERO dove il bersaglio non e' assegnato, 1/2/3 per le classi.
    Sottrarre uno e troncare a [0, 2] porterebbe i non assegnati alla classe
    VERDE: il modello imparerebbe a prevedere verde dove non c'e' misura, e la
    metrica lo premierebbe — mentre i pesi sono stimati sulle sole celle valide.

    Sui tre contesti i non assegnati sono il 14,1%, il 40,0% e il 19,6% del
    periodo di prova: su Londra due bersagli su cinque sarebbero inventati.

    La maschera si restituisce e si USA: la perdita e la valutazione escludono
    quelle celle, non le trattano come verdi.
    """
    X = np.stack([x[t - FINESTRA + 1:t + 1] for t in istanti])   # (B,T,C,K)
    X = torch.as_tensor(X).permute(0, 2, 3, 1)[:, :, nodi]       # (B,C,K,T)
    C = np.stack([np.stack([classe[t + h] for h in ORIZZONTI], -1)
                  for t in istanti])[:, nodi]                    # (B,K,H)
    M = torch.as_tensor(C > 0)
    Y = torch.as_tensor(np.where(C > 0, C - 1, 0))
    return X, Y, M


def _perdita(out, Y, M, wt):
    """Perdita pesata sui SOLI bersagli assegnati, per orizzonte e poi media.

    Un orizzonte senza bersagli validi nel lotto NON contribuisce: sostituirlo
    con zero abbasserebbe la perdita, con la media degli altri la inventerebbe.
    """
    perdite = []
    for h in range(len(ORIZZONTI)):
        m = M[..., h].reshape(-1)
        if not bool(m.any()):
            continue
        o = out[..., h, :].reshape(-1, 3)[m]
        y = Y[..., h].reshape(-1)[m]
        perdite.append(F.cross_entropy(o, y, weight=wt))
    if not perdite:
        raise FallimentoMetodo("nessun bersaglio valido nel lotto")
    return torch.stack(perdite).mean(), len(perdite)


def _pesi(E, D, nodi, ist, radice: Path, versione: str):
    """L'artefatto dei pesi, UNO per citta' e partizione.

    Si calcola la prima volta e si riusa: le tre inizializzazioni e le due
    varianti devono consumare lo STESSO vettore, altrimenti il confronto
    appaiato non ha la medesima metrica ai due lati.
    """
    dir_pesi = radice / "pesi"
    f = percorso_pesi(dir_pesi, E.contesto, E.partizione)
    if f.exists():
        return carica_pesi(dir_pesi, E.contesto, E.partizione)
    P = calcola_pesi(E.contesto, E.partizione, D["classe"],
                     nodi["addestramento"], ist["addestramento"], ORIZZONTI,
                     versione_codice=versione)
    salva_pesi(P, dir_pesi)
    return P


def _fornitore(braccio: str, d_desc: int, nodi_addestramento):
    """Il fornitore di identita', scelto dal BRACCIO dichiarato.

    **Non si deduce dalla presenza di un descrittore**: il braccio e' un
    parametro del protocollo, e dedurlo renderebbe un errore di configurazione
    indistinguibile da una scelta.

        C        NoIdentity                  nessun parametro per nodo
        P        ObservableIdentityEncoder   encoder condiviso
        E, A, R  LearnedNodeEmbedding        una riga per nodo AMMESSO
        F        costruito altrove, da E gia' addestrato
    """
    if braccio == "C":
        return NoIdentity(), False
    if braccio == "P":
        return ObservableIdentityEncoder(d_desc), True
    if braccio in ("E", "A", "R"):
        return LearnedNodeEmbedding(nodi_addestramento), False
    raise ValueError(
        f"braccio «{braccio}» non costruibile qui: F parte dal punto di "
        f"controllo E gia' addestrato, tramite `adattamento.copia_da_E`")


PUNTI_PRINCIPALE = (35, 229, 458, 687, 916, 1145, 1374, 1603, 1832, 2061,
                    2290)
AGGIORNAMENTI_PRINCIPALE = 2290


def _ciclo_principale(m, opt, g, x, D, ist, nodi, nodi_ck, ist_ck, stat, dtr,
                      dva, wt, cfg, reg, ck, forn, braccio_, d_desc, E, seme_i):
    """Il ciclo della campagna principale. CONGELAMENTO_BUDGET.md.

        max_optimizer_updates           2.290
        punti di controllo              35, 229, 458, ..., 2290
        checkpoint_selection            minimo di V-FULL, a parita' il PRECEDENTE
        arresto anticipato              NESSUNO
        campionamento                   INVARIATO: 32 istanti distinti per
                                        aggiornamento, nuove estrazioni ai
                                        successivi

    **Il costo riportato e' quello dell'intera procedura**, non fino al punto
    selezionato. Le esposizioni si registrano.
    """
    import time as _t
    from evoluzione.componente.valutazione import valuta
    stat_np = stat.numpy() if hasattr(stat, "numpy") else stat
    tetto = int(cfg.get("max_optimizer_updates", AGGIORNAMENTI_PRINCIPALE))
    punti = tuple(cfg.get("punti", PUNTI_PRINCIPALE))
    if punti[-1] != tetto:
        raise ValueError(f"l'ultimo punto {punti[-1]} deve essere il tetto "
                         f"{tetto}")
    migliore, u_mig, curve, visti = float("inf"), -1, [], []
    t0, t_val = _t.time(), 0.0
    for u in range(1, tetto + 1):
        m.train()
        idx = g.choice(ist["addestramento"], size=min(cfg["lotto"],
                                                      len(ist["addestramento"])),
                       replace=False)
        visti.append(idx)
        X, Y, Mk = _lotto(x, D["classe"], np.sort(idx), nodi["addestramento"])
        out = m(X, node_ids=nodi["addestramento"], descriptor=dtr,
                static_inputs=stat[nodi["addestramento"]])
        L, _ = _perdita(out, Y, Mk, wt)
        if not torch.isfinite(L):
            raise FallimentoMetodo(f"perdita non finita all'aggiornamento {u}")
        opt.zero_grad(); L.backward(); opt.step()
        if u in punti:
            tv = _t.time()
            r = valuta(m, x, D["classe"], stat_np, nodi_ck, ist_ck, wt,
                       descrittore=dva)
            t_val += _t.time() - tv
            pv = r["perdita"]
            if not np.isfinite(pv):
                raise FallimentoMetodo(f"V-full non finita all'aggiornamento {u}")
            curve.append({"aggiornamento": u, "training": float(L.detach()),
                          "V-full": pv, "celle": r["celle_totali"]})
            reg.evento(f"u{u}: training {float(L.detach()):.5f}, "
                       f"V-full {pv:.5f}")
            if pv < migliore:                   # a parita', il PRECEDENTE
                migliore, u_mig = pv, u
                torch.save({"state_dict": m.state_dict(), "epoca": u,
                            "aggiornamento": u, "validazione": pv,
                            "criterio": "minimum_full_validation_wCE",
                            "training_protocol": "principale",
                            "braccio": braccio_,
                            "fornitore": type(forn).__name__,
                            "nodi_iniziali": [int(z) for z in nodi["addestramento"]],
                            "nodi_validazione": [int(z) for z in nodi["validazione"]],
                            "nodi_prova": [int(z) for z in nodi["prova"]],
                            "d_descrittore": d_desc,
                            "contesto": E.contesto, "partizione": E.partizione,
                            "seme_inizializzazione": seme_i}, ck)
    dur = _t.time() - t0
    tutte = np.concatenate(visti)
    uu, cc = np.unique(tutte, return_counts=True)
    reg.artefatto("protocollo_principale",
                  aggiornamenti=tetto, punti=list(punti),
                  aggiornamento_selezionato=u_mig, V_full_selezionata=migliore,
                  curve=curve, secondi_totali=dur, secondi_valutazione=t_val,
                  origini_distinte=int(len(uu)),
                  origini_disponibili=int(len(ist["addestramento"])),
                  esposizioni_per_origine={"minimo": int(cc.min()),
                                           "mediana": float(np.median(cc)),
                                           "massimo": int(cc.max())},
                  finestre_per_aggiornamento=int(cfg["lotto"] *
                                                 len(nodi["addestramento"])))
    reg.evento(f"protocollo principale: {tetto} aggiornamenti, selezionato "
               f"u{u_mig} (V-full {migliore:.5f}), {dur/60:.1f} min di cui "
               f"{t_val/60:.1f} di valutazione")
    return u_mig, migliore


def addestra_una(E, reg, cfg, gen, radice: Path) -> Path:
    """Una esecuzione. Restituisce il percorso delle predizioni salvate."""
    dir_masc = radice / "maschere"
    D = _carica(E.contesto, dir_masc)
    nodi, ist = _partizioni(D, gen)
    NORM, nr, nv = _normalizzazione(D, nodi, ist)

    # **La RETE INIZIALE non e' la popolazione di addestramento.** Per A ed R
    # quest'ultima e' ampliata coi nodi nuovi, che NON devono entrare nella
    # metrica di selezione.
    nodi_rete_iniziale = np.asarray(
        cfg.get("nodi_rete_iniziale", nodi["addestramento"]), dtype="int64")
    nuovi_dichiarati = set(int(x) for x in cfg.get("nodi_nuovi", []))
    intrusi = [int(x) for x in nodi_rete_iniziale if int(x) in nuovi_dichiarati]
    if intrusi:
        raise ValueError(
            f"nodi nuovi nella rete iniziale usata per la selezione: "
            f"{intrusi[:6]}. La metrica del punto di controllo non deve "
            f"vederli.")

    # -- i PESI: stesso artefatto per addestramento e analisi ---------------
    PZ = _pesi(E, D, nodi, ist, radice, cfg.get("etichetta", ""))
    w = PZ.vettore()
    wt = torch.as_tensor(w, dtype=torch.float32)
    reg.metrica(nome="wCE", pesi=w,
                aggregazione=PZ.regola_aggregazione,
                ordine_classi=PZ.ordine_classi, conteggi=PZ.conteggi,
                n_train=PZ.n_train,
                nodi_stima=f"{len(PZ.nodi_addestramento)} di addestramento",
                periodo_stima=PZ.periodo_addestramento,
                riduzione=PZ.regola_riduzione,
                conteggio_per_orizzonte=PZ.conteggio_per_orizzonte,
                versione_pesi=PZ.versione_pesi, impronta_pesi=PZ.impronta)
    # VARIANTE e BRACCIO sono cose diverse: la prima e' lo schema del
    # descrittore (LEGACY, BASE-CORRECTED, EXTENDED), il secondo la strategia
    # di identita' (C, P, E, A, R, F). **I bracci che non usano descrittori non
    # hanno variante**, e chiederne lo schema sarebbe un errore di
    # configurazione mascherato da KeyError.
    braccio_ = cfg.get("braccio", "P")
    # POLITICA DI SELEZIONE DEL PUNTO DI CONTROLLO, esplicita.
    #
    #   initial_network      wCE sui nodi della RETE INIZIALE, nel periodo di
    #                        validazione: la regola dell'inserimento, §5bis
    #   inductive_validation wCE sui nodi di validazione induttiva: la regola
    #                        delle campagne del raccordo, gia' congelate
    #
    # **Non si riusa una variabile generica `validation_nodes`**: la selezione
    # del punto di controllo e la selezione degli iperparametri di F usano
    # popolazioni diverse, e confonderle e' il difetto appena corretto.
    politica_ck = cfg.get("checkpoint_selection_population",
                          "inductive_validation")
    if politica_ck not in ("initial_network", "inductive_validation"):
        raise ValueError(f"politica ignota: {politica_ck}")
    if braccio_ in ("C", "E", "A", "R"):
        S = {"statistiche": [], "disponibilita": []}
    elif E.variante not in SCHEMI_T4C:
        raise ValueError(
            f"variante «{E.variante}» ignota per il braccio {braccio_}, che usa "
            f"descrittori. Ammesse: {list(SCHEMI_T4C)}")
    else:
        S = SCHEMI_T4C[E.variante]
    if S["statistiche"]:
        verifica_contratto(S["statistiche"], S["disponibilita"], NORM,
                           f"{E.variante}/traffic4cast",
                           canali_costanti=COSTANTI)
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
    # SI COSTRUISCE COMUNQUE nell'ordine consueto, anche quando lo stato verra'
    # sovrascritto: cosi' il generatore avanza esattamente come nella campagna
    # precedente, e l'ordine dei campionamenti successivi non cambia. Caricare
    # uno `state_dict` non ripristinerebbe il generatore.
    forn, usa_desc = _fornitore(braccio_, d_desc, nodi["addestramento"])
    m = PredittorePerNodo(d_desc, 5, sorgente="traffic4cast", identita=forn)
    reg.evento(f"braccio {braccio_}: fornitore {type(forn).__name__}, "
               f"descrittori {'usati' if usa_desc else 'NON usati'}")
    reg.evento(f"checkpoint_selection_population = {politica_ck}")

    # ---- ARTEFATTO CANONICO: obbligatorio, PRIMA dell'ottimizzatore --------
    # C, P, E, A e R lo caricano. **F e' l'eccezione**: parte dal punto di
    # controllo E gia' addestrato, di cui mantiene backbone, statiche e teste,
    # sicche' caricarvi lo stato iniziale cancellerebbe l'addestramento.
    braccio = cfg.get("braccio", "P")
    cfg_comuni = {"c_in": 9, "nascosti": 32, "blocchi": 4, "d_statiche": 5,
                  "d_statiche_uscita": 8, "n_orizzonti": len(ORIZZONTI),
                  "n_classi": 3}
    if braccio in CARICANO and cfg.get("canonico", True):
        art = carica_canonico(seme_i, cfg_comuni,
                              Path(cfg.get("dir_canonico",
                                           radice / "canonico")))
        r_app = applica_canonico(m, art)
        r_ver = verifica_canonico(m, art, f"{braccio}/{E.contesto}")   # BLOCCA
        reg.artefatto("canonico", chiave=art["chiave"],
                      impronta=art["impronta"], tensori=r_ver["tensori"],
                      braccio=braccio, identita_intatta=r_app["identita_intatta"])
        reg.evento(f"artefatto canonico {art['chiave']} applicato e verificato: "
                   f"{r_ver['tensori']} tensori comuni identici")
    elif braccio == "F":
        reg.evento("braccio F: NON carica l'artefatto iniziale, parte dal "
                   "punto di controllo E gia' addestrato")

    # lo stato iniziale COMPLETO del modello risultante, registrato
    f_ini = stato_iniziale_completo(
        m, seme_i, cfg_comuni, braccio,
        Path(cfg.get("dir_stati_completi", radice / "stati_completi")),
        extra={"contesto": E.contesto, "partizione": E.partizione,
               "inizializzazione": E.inizializzazione, "variante": E.variante})
    reg.artefatto("stato_iniziale_completo", percorso=f_ini)

    impronta_iniziale = None
    if cfg.get("appaiamento") and E.variante == "BASE-CORRECTED":
        from evoluzione.esperimenti.prepara_stati_iniziali import (
            chiave as chiave_stato, impronta_stato)
        k = chiave_stato("BASE-CORRECTED", seme_i, d_desc, True)
        f = Path(cfg.get("stati_iniziali",
                         "results/evoluzione/stati_iniziali")) / f"{k}.pt"
        if not f.exists():
            raise ValueError(
                f"stato iniziale allineato assente: {f}. Eseguire prima "
                f"`prepara_stati_iniziali.py`: l'addendum richiede che gli "
                f"stati siano SALVATI, non identificati dal solo seme.")
        d = torch.load(f, map_location="cpu", weights_only=False)
        m.load_state_dict(d["state_dict"])
        impronta_iniziale = d["impronta"]
        reg.evento(f"stato iniziale ALLINEATO caricato da {f.name}, impronta "
                   f"{impronta_iniziale}: `stat`, `e1` ed `e2` presi da LEGACY")
    elif cfg.get("appaiamento"):
        from evoluzione.esperimenti.prepara_stati_iniziali import impronta_stato
        impronta_iniziale = impronta_stato(m.state_dict())
        reg.evento(f"stato iniziale originario di LEGACY, impronta "
                   f"{impronta_iniziale}: invariato")
    opt = torch.optim.Adam(m.parameters(), lr=cfg["passo"])
    stat = torch.as_tensor(np.stack([
        D["m_r"].mean(0), np.zeros(K), np.ones(K), np.zeros(K), np.ones(K)],
        1).astype("float32"))
    # i descrittori si calcolano SOLO per P: per gli altri bracci sarebbero
    # un costo inutile, e passarli farebbe sollevare il fornitore
    # I NODI DELLA METRICA DI SELEZIONE, secondo la politica dichiarata
    nodi_ck = (nodi_rete_iniziale if politica_ck == "initial_network"
               else nodi["validazione"])
    ist_ck = ist["validazione"]          # il PERIODO e' quello di validazione

    dtr = dva = None
    if usa_desc:
        dtr = _descrittori(D, nodi["addestramento"],
                           int(ist["addestramento"][-1]), E.variante, NORM)
        dva = _descrittori(D, nodi_ck, int(ist_ck[0]), E.variante, NORM)
    reg.modello(m, n_nodi=K, **{k: cfg[k] for k in
                                ("epoche", "lotto", "passo", "pazienza")})
    if impronta_iniziale:
        reg.artefatto("stato_iniziale", impronta=impronta_iniziale,
                      appaiamento=True,
                      campagna_precedente=cfg.get("campagna_precedente"),
                      versione_addendum=cfg.get("versione_addendum"))

    # LA CARTELLA SEGUE L'ETICHETTA: scrivere in "raccordo" fisso
    # sovrascriverebbe la campagna congelata
    dir_camp = radice / cfg.get("etichetta", "raccordo")
    # il NOME segue la convenzione della fase: per E, `ck_E_<citta>_p<n>_s<seme>`
    nome_ck = (f"ck_E_{E.contesto}_p{E.partizione}_s{seme_i}.pt"
               if braccio_ == "E" else
               f"ck_{E.contesto}_p{E.partizione}_s{E.inizializzazione}_"
               f"{E.variante}.pt")
    migliore, epoca, pazienza, ck = float("inf"), -1, 0, dir_camp / nome_ck
    ck.parent.mkdir(parents=True, exist_ok=True)
    g = np.random.default_rng(seme_i)
    # IL PROTOCOLLO DI ADDESTRAMENTO, esplicito.
    #
    #   storico     al massimo `epoche` AGGIORNAMENTI, validazione dopo ognuno
    #               sui primi `lotto` istanti, pazienza su aggiornamenti.
    #               E' il percorso delle campagne congelate, e NON si tocca:
    #               deve poterle riprodurre.
    #   principale  2.290 aggiornamenti, undici punti, selezione su V-FULL,
    #               nessun arresto anticipato. CONGELAMENTO_BUDGET.md.
    protocollo = cfg.get("training_protocol", "storico")
    if protocollo not in ("storico", "principale"):
        raise ValueError(f"protocollo di addestramento ignoto: {protocollo}")
    reg.evento(f"training_protocol = {protocollo}")
    if protocollo == "principale":
        epoca, migliore = _ciclo_principale(
            m, opt, g, x, D, ist, nodi, nodi_ck, ist_ck, stat, dtr, dva, wt,
            cfg, reg, ck, forn, braccio_, d_desc, E, seme_i)
    for ep in (range(cfg["epoche"]) if protocollo == "storico" else ()):
        m.train()
        idx = g.choice(ist["addestramento"], size=min(cfg["lotto"],
                                                      len(ist["addestramento"])),
                       replace=False)
        X, Y, Mk = _lotto(x, D["classe"], np.sort(idx), nodi["addestramento"])
        out = m(X, node_ids=nodi["addestramento"], descriptor=dtr,
                static_inputs=stat[nodi["addestramento"]])
        # PESATA e sui SOLI bersagli assegnati
        L, _ = _perdita(out, Y, Mk, wt)
        if not torch.isfinite(L):
            raise FallimentoMetodo(f"perdita non finita all'epoca {ep}")
        opt.zero_grad(); L.backward(); opt.step()
        m.eval()
        with torch.inference_mode():
            Xv, Yv, Mv = _lotto(x, D["classe"], ist_ck[:cfg["lotto"]], nodi_ck)
            lv, _ = _perdita(
                m(Xv, node_ids=nodi_ck, descriptor=dva,
                  static_inputs=stat[nodi_ck]), Yv, Mv, wt)
            pv = float(lv)
        if not np.isfinite(pv):
            raise FallimentoMetodo(f"validazione non finita all'epoca {ep}")
        if pv < migliore:                       # a parita', la PRIMA
            migliore, epoca, pazienza = pv, ep, 0
            # LA MAPPA NODO-RIGA SI SALVA COI PESI: senza, i pesi di un
            # embedding non sono interpretabili, e `carica_E` la richiede.
            torch.save({"state_dict": m.state_dict(), "epoca": ep,
                        "validazione": pv, "braccio": braccio_,
                        "fornitore": type(forn).__name__,
                        "nodi_iniziali": [int(x) for x in nodi["addestramento"]],
                        "nodi_validazione": [int(x) for x in nodi["validazione"]],
                        "nodi_prova": [int(x) for x in nodi["prova"]],
                        "d_descrittore": d_desc,
                        "contesto": E.contesto, "partizione": E.partizione,
                        "seme_inizializzazione": seme_i}, ck)
        else:
            pazienza += 1
            if pazienza >= cfg["pazienza"]:
                reg.evento(f"arresto anticipato all'epoca {ep}: non e' un "
                           f"fallimento")
                break
    if epoca < 0:
        raise FallimentoMetodo("nessuna epoca ha migliorato la validazione")

    # -- valutazione del punto SELEZIONATO, in modalita' congelata ----------
    forn2, _ = _fornitore(braccio_, d_desc, nodi["addestramento"])
    m2 = PredittorePerNodo(d_desc, 5, sorgente="traffic4cast", identita=forn2)
    m2.load_state_dict(torch.load(ck, weights_only=False)["state_dict"])
    m2.eval()
    reg.artefatto("punto_di_controllo", percorso=ck, epoca=epoca,
                  validazione=migliore)
    # E E' PREPARATORIO e NON si valuta sui nodi di prova: la sua tabella
    # contiene i soli nodi di addestramento, e chiedere una riga per un nodo
    # nuovo solleverebbe. **E' il punto dell'esperimento**: E non sa prevedere
    # su chi non ha visto, e F nasce proprio per questo.
    if braccio_ == "E":
        reg.evento("braccio E preparatorio: nessuna valutazione sui nodi di "
                   "prova, che non sono registrati nella tabella degli "
                   "embedding. Il punto di controllo e' l'uscita della fase.")
        reg.uscita(ck)
        return ck

    dpr = (_descrittori(D, nodi["prova"], int(ist["prova"][0]), E.variante,
                        NORM) if usa_desc else None)
    righe = []
    scartate = 0
    with torch.inference_mode():
        for t in ist["prova"]:
            X, Y, Mk = _lotto(x, D["classe"], [int(t)], nodi["prova"])
            o = torch.softmax(
                m2(X, node_ids=nodi["prova"], descriptor=dpr,
                   static_inputs=stat[nodi["prova"]])[0], -1).numpy()
            for i, k in enumerate(nodi["prova"]):
                for h, hz in enumerate(ORIZZONTI):
                    if not bool(Mk[0, i, h]):
                        scartate += 1      # bersaglio NON assegnato: si esclude
                        continue
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
    # CONTROLLO BLOCCANTE: la popolazione valutata deve coincidere con quella
    # su cui i pesi sono stimati. Senza, i non assegnati rientrerebbero come
    # classe verde e la metrica peserebbe una popolazione diversa.
    if (P.vero < 0).any() or (P.vero > 2).any():
        raise ValueError("classi fuori intervallo nelle predizioni")
    # Il confronto NON e' con la distribuzione di addestramento — le due
    # differiscono legittimamente fra periodi — ma con quella delle celle VALIDE
    # del periodo e dei nodi di PROVA, calcolata qui dai bersagli grezzi. Ogni
    # scarto e' allora un difetto della selezione, non deriva temporale.
    att = np.zeros(3, dtype="float64")
    for h in ORIZZONTI:
        tt = ist["prova"] + h
        tt = tt[tt < D["classe"].shape[0]]
        y = D["classe"][np.ix_(tt, nodi["prova"])]
        for k in (1, 2, 3):
            att[k - 1] += float((y == k).sum())
    if att.sum() == 0:
        raise ValueError("nessun bersaglio valido nel periodo di prova")
    att /= att.sum()
    oss = np.array([(P.vero == k).mean() for k in range(3)])
    scarto = float(np.abs(oss - att).max())
    if scarto > 1e-6:
        raise ValueError(
            f"la distribuzione valutata {np.round(oss, 6).tolist()} non "
            f"coincide con quella delle celle VALIDE di prova "
            f"{np.round(att, 6).tolist()} (scarto {scarto:.2e}): la "
            f"popolazione della metrica non e' quella dichiarata")
    reg.evento(f"epoca selezionata {epoca}, validazione {migliore:.6f}, "
               f"{len(P):,} predizioni, {scartate:,} celle senza bersaglio "
               f"assegnate ESCLUSE")
    return out
