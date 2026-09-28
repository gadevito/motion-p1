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
    SCHEMI_PEMS04, SCHEMI_T4C, Osservazioni, estrai_diretto)
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
# I CANALI DICHIARATI COSTANTI dipendono dalla SORGENTE. Su Traffic4cast
# occupazione e conteggio non sono misurati; **su PEMS04 lo sono entrambi**, e
# dichiararli costanti farebbe saltare la loro normalizzazione.
COSTANTI = frozenset({"occupazione", "conteggio"})
COSTANTI_PEMS04 = frozenset()


def costanti_di(sorgente: str) -> frozenset:
    return COSTANTI_PEMS04 if sorgente == "pems04" else COSTANTI
T4 = "data_collection/traffic4cast"
CTX = {"Madrid": (f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz", "Madrid"),
       "Londra": (f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz", "Londra"),
       "Melbourne": (f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
                     "Melbourne")}

# VERIFICA ESTERNA SU PEMS04. **Ogni contesto e' UNA partizione**: il
# riferimento empirico di rete e' stimato sui soli nodi iniziali di quella
# partizione ed e' congelato dentro l'artefatto, sicche' contesto e partizione
# non sono piu' indipendenti. `_coerenza_pems04` lo impone.
PEMS = "data_collection/pems04"
CTX.update({f"PEMS04_p{k}": (f"{PEMS}/bersagli_PEMS04_p{k}.npz",
                             f"PEMS04_p{k}") for k in (0, 1, 2)})


def sorgente_di(contesto) -> str:
    """La SORGENTE del contesto: decide canali, schema e dimensioni.

    PEMS04 ha tre grandezze dinamiche e tre maschere — undici ingressi col
    calendario — contro le due e due di Traffic4cast. **Punti di controllo e
    artefatti canonici non sono confrontabili fra le due sorgenti.**
    """
    return "pems04" if str(contesto).startswith("PEMS04_p") else "traffic4cast"


def canali_di(sorgente: str) -> tuple:
    return (("r", "conteggio", "occupazione", "m_r", "m_conteggio",
             "m_occupazione") if sorgente == "pems04"
            else tuple(CANALI_T4C[:4])) + ("sin_ora", "cos_ora", "sin_dow",
                                           "cos_dow", "fine_settimana")


def _coerenza_pems04(contesto, partizione: int) -> None:
    """Su PEMS04 il contesto DICHIARA la propria partizione.

    Eseguire `PEMS04_p0` con `partizione=1` darebbe nodi iniziali diversi da
    quelli su cui il riferimento e' stato stimato, **senza alcun errore**: il
    riferimento e le classi resterebbero quelli del file, e il confronto
    sarebbe silenziosamente sbagliato.
    """
    if not str(contesto).startswith("PEMS04_p"):
        return
    atteso = int(str(contesto).rsplit("_p", 1)[1])
    if int(partizione) != atteso:
        raise ValueError(
            f"{contesto} richiede partizione {atteso}, ricevuta {partizione}: "
            f"il riferimento empirico di rete e' stimato sui nodi iniziali di "
            f"quella partizione e congelato nell'artefatto")


class FallimentoMetodo(RuntimeError):
    """Perdita non finita, divergenza, risorse superate in modo riproducibile.

    Definita QUI e importata dall'orchestratore: due classi distinte con lo
    stesso nome non verrebbero riconosciute da `isinstance`, e l'eccezione
    sospenderebbe le esecuzioni invece di essere registrata come fallimento del
    metodo.
    """


from evoluzione.componente.griglia import (  # noqa: E402
    filtra as _filtra_griglia, maschera_origini as _maschera_origini,
    passi_regolari as _passi_regolari,
    verifica_finestra_descrittore as _verifica_finestra)


def _carica(contesto, dir_masc: Path):
    tp, eti = CTX[contesto]
    M = np.load(dir_masc / f"maschere_{eti}.npz", allow_pickle=True)
    B = np.load(tp, allow_pickle=True)
    if not np.array_equal(M["sensor_ids"].astype(str),
                          B["sensor_ids"].astype(str)):
        raise ValueError(f"{contesto}: maschere e bersagli disallineati")
    ts = pd.to_datetime(M["timestamps"])
    rif = np.asarray(M["riferimento_risolto"], "float64")
    if sorgente_di(contesto) == "pems04":
        # tre grandezze e tre maschere: il conteggio e' CONTINUO, non una classe
        return {"sid": M["sensor_ids"].astype(str), "ts": ts,
                "ore": ts.hour.to_numpy(), "dow": ts.dayofweek.to_numpy(),
                "r": np.asarray(M["speed_grezza"], "float64") / rif[None, :],
                "vol": np.asarray(M["conteggio_grezzo"], "float64"),
                "occ": np.asarray(M["occupazione_grezza"], "float64"),
                "m_r": M["maschera_r"], "m_v": M["maschera_conteggio"],
                "m_o": M["maschera_occupazione"],
                "classe": np.asarray(B["congestion_emp"], "int64"),
                "rif": rif, "sorgente": "pems04"}
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
    if D.get("sorgente") == "pems04":
        ov = D["occ"][reg][D["m_o"][reg]]
        if not len(ov):
            raise FallimentoMetodo("nessuna occupazione valida nel perimetro")
        no = (float(ov.mean()), float(ov.std()) + 1e-6)
        # la si ripone in D: i chiamanti di `_canali` passano tre argomenti, e
        # cambiarne la firma ovunque moltiplicherebbe i punti di rottura
        D["norm_occ"] = no
        return {"media_r": nr, "media_conteggio": nv,
                "media_occupazione": no}, nr, nv
    return {"media_r": nr, "media_volume_class": nv,
            "media_conteggio": nv, "media_occupazione": (0.0, 1e-6)}, nr, nv


def _canali(D, nr, nv, no=None):
    T, K = D["r"].shape
    pems = D.get("sorgente") == "pems04"
    n_din = 6 if pems else 4
    x = np.zeros((T, n_din + 5, K), dtype="float32")
    x[:, 0] = (np.where(D["m_r"], D["r"], 0.0) - nr[0]) / nr[1]
    x[:, 1] = (np.where(D["m_v"], D["vol"], 0.0) - nv[0]) / nv[1]
    if pems:
        # **l'occupazione e' la terza grandezza**, e la sua maschera la terza
        no = no or D.get("norm_occ")
        if no is None:
            raise FallimentoMetodo(
                "statistica dell'occupazione assente: `_normalizzazione` va "
                "eseguita prima di `_canali` su PEMS04")
        x[:, 2] = (np.where(D["m_o"], D["occ"], 0.0) - no[0]) / no[1]
        x[:, 3] = D["m_r"]; x[:, 4] = D["m_v"]; x[:, 5] = D["m_o"]
    else:
        x[:, 2] = D["m_r"]; x[:, 3] = D["m_v"]
    o, w = D["ore"], D["dow"]
    for i, c in enumerate([np.sin(2 * np.pi * o / 24), np.cos(2 * np.pi * o / 24),
                           np.sin(2 * np.pi * w / 7), np.cos(2 * np.pi * w / 7),
                           (w >= 5).astype("float64")]):
        x[:, n_din + i] = c[:, None]
    if not np.isfinite(x).all():
        raise FallimentoMetodo("ingressi non finiti dopo la preparazione")
    return x


def _descrittori(D, nodi, t_rif, variante, norm):
    # LA SORGENTE decide schema, canali e chiavi di normalizzazione: passarne
    # una fissa farebbe cercare all'estrattore parametri che non esistono.
    srg = "pems04" if D.get("sorgente") == "pems04" else "traffic4cast"
    S = (SCHEMI_PEMS04 if srg == "pems04" else SCHEMI_T4C)[variante]
    d = len(S["statistiche"]) + len(S["disponibilita"])
    T = D["r"].shape[0]
    Z = np.zeros((len(nodi), d), dtype="float32")
    for i, k in enumerate(nodi):
        oss = Osservazioni(
            istanti=np.arange(T),
            r=np.where(D["m_r"][:, k], D["r"][:, k], np.nan),
            f=np.where(D["m_v"][:, k], D["vol"][:, k], np.nan),
            # su PEMS04 l'occupazione e' MISURATA: non e' un canale assente
            o=(np.where(D["m_o"][:, k], D["occ"][:, k], np.nan)
               if srg == "pems04" else np.full(T, np.nan)),
            classe=D["classe"][:, k],
            ora_locale=D["ore"], t0=max(t_rif - L_STORIA, 0))
        e = estrai_diretto(oss, t=t_rif, L=L_STORIA, sensor_id=str(k),
                           schema=variante, norm=norm, sorgente=srg,
                           canali_costanti=costanti_di(srg))
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


def _lotto_coppie(x, classe, coppie_t, coppie_n):
    """Un lotto di COPPIE (nodo, origine), non di istanti per tutti i nodi.

    Il campionamento uniforme per nodo di R estrae coppie: rappresentarle nel
    lotto denso [istanti x nodi] richiederebbe migliaia di origini per
    aggiornamento. **Il predittore e' per nodo e non usa il grafo**, quindi
    ogni coppia e' indipendente e il contratto dei tensori resta lo stesso, con
    un solo nodo per colonna.

    Restituisce X [P, C, 1, FINESTRA], Y [P, 1, H], M [P, 1, H].
    """
    tt = np.asarray(coppie_t, dtype="int64")
    nn = np.asarray(coppie_n, dtype="int64")
    idx = tt[:, None] + np.arange(-FINESTRA + 1, 1)          # [P, FINESTRA]
    # x e' [T, C, K]: la finestra di CIASCUNA coppia, in UNA SOLA
    # indicizzazione. Indicizzare prima sul tempo e poi ridurre costruirebbe
    # un intermedio [P, FINESTRA, C, K] — 6,7 GB per aggiornamento con 20.160
    # coppie e 765 nodi — per poi scartarne quasi tutto.
    X = x[idx[:, :, None],
          np.arange(x.shape[1])[None, None, :],
          nn[:, None, None]]                                 # [P, FINESTRA, C]
    # **Le coppie occupano l'asse dei NODI, non quello del lotto**: il contratto
    # dell'identita' richiede un identificativo per colonna del tensore, e ogni
    # coppia ha il proprio nodo. Con [1, C, P, FINESTRA] i due coincidono.
    X = torch.from_numpy(np.ascontiguousarray(
        X.transpose(2, 0, 1)[None]))                         # [1, C, P, FIN]
    Y = np.zeros((1, len(tt), len(ORIZZONTI)), dtype="int64")
    M = np.zeros((1, len(tt), len(ORIZZONTI)), dtype=bool)
    for h, o in enumerate(ORIZZONTI):
        c = classe[tt + o, nn]
        M[0, :, h] = c > 0
        Y[0, :, h] = np.clip(c - 1, 0, 2)
    return X, torch.from_numpy(Y), torch.from_numpy(M)


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


def _pesi(E, D, nodi, ist, radice: Path, versione: str, dir_pesi=None,
          solo_carica: bool = False):
    """L'artefatto dei pesi, UNO per citta' e partizione.

    Si calcola la prima volta e si riusa: le tre inizializzazioni e le due
    varianti devono consumare lo STESSO vettore, altrimenti il confronto
    appaiato non ha la medesima metrica ai due lati.
    """
    dir_pesi = Path(dir_pesi) if dir_pesi else radice / "pesi"
    f = percorso_pesi(dir_pesi, E.contesto, E.partizione)
    if f.exists():
        return carica_pesi(dir_pesi, E.contesto, E.partizione)
    if solo_carica:
        # Con la griglia reale i pesi si PREPARANO prima, una volta: calcolarli
        # qui, con piu' processi in parallelo, produrrebbe scritture
        # concorrenti sullo stesso file.
        raise FallimentoMetodo(
            f"pesi assenti in {dir_pesi}: eseguire prima prepara_pesi_griglia.py")
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
    # IL CAMPIONAMENTO, dichiarato.
    #   uniforme_istanti  32 istanti distinti per aggiornamento, tutti i nodi
    #   uniforme_nodo     il contratto di R: si estrae uniformemente un NODO
    #                     della rete ampliata, poi un'origine ammissibile per
    #                     quel nodo. **Budget invariato**: 32 x K_iniziali
    #                     finestre nodo-origine per aggiornamento.
    camp = cfg.get("campionamento", "uniforme_istanti")
    if camp not in ("uniforme_istanti", "uniforme_nodo"):
        raise ValueError(f"campionamento ignoto: {camp}")
    pop = n_estrazioni = None
    if camp == "uniforme_nodo":
        from evoluzione.componente.campionamento import (
            campiona, esposizione_attesa, esposizione_realizzata, prepara)
        pop = prepara(D["classe"], cfg["nodi_iniziali_R"], ist["addestramento"],
                      cfg["nodi_nuovi"], cfg["origini_nuovi"])
        n_estrazioni = int(cfg["lotto"]) * len(cfg["nodi_iniziali_R"])
        reg.evento(f"campionamento uniforme per nodo: {n_estrazioni} finestre "
                   f"per aggiornamento, {len(pop['ammessi'])} nodi ammessi, "
                   f"{len(pop['esclusi'])} esclusi")
    migliore, u_mig, curve, visti = float("inf"), -1, [], []
    estratti_n, estratti_o = [], []
    t0, t_val = _t.time(), 0.0
    for u in range(1, tetto + 1):
        m.train()
        if camp == "uniforme_nodo":
            nn_, oo_ = campiona(pop, n_estrazioni, g)
            estratti_n.append(nn_); estratti_o.append(oo_)
            visti.append(np.unique(oo_))
            X, Y, Mk = _lotto_coppie(x, D["classe"], oo_, nn_)
            out = m(X, node_ids=[int(z) for z in nn_], descriptor=dtr,
                    static_inputs=stat[nn_])
        else:
            idx = g.choice(ist["addestramento"],
                           size=min(cfg["lotto"], len(ist["addestramento"])),
                           replace=False)
            visti.append(idx)
            X, Y, Mk = _lotto(x, D["classe"], np.sort(idx),
                              nodi["addestramento"])
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
    if camp == "uniforme_nodo":
        att = esposizione_attesa(pop, n_estrazioni * tetto)
        rea = esposizione_realizzata(pop, np.concatenate(estratti_n),
                                     np.concatenate(estratti_o))
        reg.artefatto("campionamento_uniforme_nodo", attesa=att, realizzata=rea)
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
    _coerenza_pems04(E.contesto, E.partizione)
    D = _carica(E.contesto, dir_masc)
    nodi, ist = _partizioni(D, gen)
    NORM, nr, nv = _normalizzazione(D, nodi, ist)

    # LA GRIGLIA TEMPORALE. `ist` resta l'insieme delle RIGHE del periodo — la
    # normalizzazione, appena calcolata, le usa come osservazioni e non dipende
    # dalla regola. `orig` sono le ORIGINI: con la griglia reale, soltanto
    # quelle la cui finestra e i cui bersagli non attraversano salti.
    #   indice  il percorso storico, INVARIATO: le origini sono le righe
    #   reale   la regola approvata, in tutte le fasi
    griglia = cfg.get("griglia_temporale", "indice")
    if griglia not in ("indice", "reale"):
        raise ValueError(f"griglia temporale ignota: {griglia}")
    ok_griglia = None
    if griglia == "reale":
        ok_griglia = _passi_regolari(D["ts"])
        amm = _maschera_origini(ok_griglia)
        orig = {k: _filtra_griglia(v, amm) for k, v in ist.items()}
    else:
        orig = ist

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
    PZ = _pesi(E, D, nodi, orig, radice, cfg.get("etichetta", ""),
               dir_pesi=cfg.get("dir_pesi"), solo_carica=(griglia == "reale"))
    reg.evento(f"griglia_temporale = {griglia}: origini ammissibili "
               + ", ".join(f"{k} {len(orig[k])}/{len(ist[k])}" for k in ist))
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
        S = (SCHEMI_PEMS04 if sorgente_di(E.contesto) == "pems04"
             else SCHEMI_T4C)[E.variante]
    if S["statistiche"]:
        srg_ = sorgente_di(E.contesto)
        verifica_contratto(S["statistiche"], S["disponibilita"], NORM,
                           f"{E.variante}/{srg_}",
                           canali_costanti=costanti_di(srg_))
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
    # LA POPOLAZIONE DI ADDESTRAMENTO, dichiarata.
    #   iniziale  i soli nodi iniziali: C, P, E
    #   ampliata  nodi iniziali PIU' i nodi nuovi: A e R, che li hanno in rete
    # La RETE INIZIALE, su cui si seleziona il punto di controllo, resta quella
    # di prima in entrambi i casi.
    popolazione = cfg.get("popolazione", "iniziale")
    if popolazione not in ("iniziale", "ampliata"):
        raise ValueError(f"popolazione ignota: {popolazione}")
    nodi_nuovi = np.asarray(cfg.get("nodi_nuovi", []), dtype="int64")
    if popolazione == "ampliata":
        if not len(nodi_nuovi):
            raise ValueError("popolazione ampliata senza nodi nuovi")
        nodi_add = np.concatenate([nodi["addestramento"], nodi_nuovi])
    else:
        nodi_add = np.asarray(nodi["addestramento"], dtype="int64")
    reg.evento(f"popolazione {popolazione}: {len(nodi_add)} nodi "
               f"({len(nodi_nuovi)} nuovi)")
    forn, usa_desc = _fornitore(braccio_, d_desc, nodi_add)
    m = PredittorePerNodo(d_desc, 5, sorgente=sorgente_di(E.contesto), identita=forn)
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
    ist_ck = orig["validazione"]         # le ORIGINI del periodo di validazione
    # il riferimento del descrittore resta l'INIZIO DEL PERIODO, non la prima
    # origine ammissibile: filtrare le origini non deve spostarlo
    t_desc_va = int(ist["validazione"][0])
    t_desc_tr = int(ist["addestramento"][-1])
    if ok_griglia is not None:
        _verifica_finestra(ok_griglia, t_desc_tr)
        _verifica_finestra(ok_griglia, t_desc_va)

    dtr = dva = None
    if usa_desc:
        dtr = _descrittori(D, nodi_add, t_desc_tr, E.variante, NORM)
        dva = _descrittori(D, nodi_ck, t_desc_va, E.variante, NORM)
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
    # Il nome puo' essere DICHIARATO dalla fase: nella campagna di inserimento
    # `inizializzazione` e `variante` sono costanti, e il nome storico farebbe
    # scrivere tutte le esecuzioni di uno stesso braccio sullo STESSO file.
    nome_ck = cfg.get("nome_ck") or (
        f"ck_E_{E.contesto}_p{E.partizione}_s{seme_i}.pt"
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
            m, opt, g, x, D, orig, {**nodi, "addestramento": nodi_add},
            nodi_ck, ist_ck, stat, dtr, dva, wt,
            cfg, reg, ck, forn, braccio_, d_desc, E, seme_i)
    for ep in (range(cfg["epoche"]) if protocollo == "storico" else ()):
        m.train()
        idx = g.choice(orig["addestramento"],
                       size=min(cfg["lotto"], len(orig["addestramento"])),
                       replace=False)
        X, Y, Mk = _lotto(x, D["classe"], np.sort(idx), nodi_add)
        out = m(X, node_ids=nodi_add, descriptor=dtr,
                static_inputs=stat[nodi_add])
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
                        "nodi_iniziali": [int(x) for x in nodi_add],
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
    forn2, _ = _fornitore(braccio_, d_desc, nodi_add)
    m2 = PredittorePerNodo(d_desc, 5, sorgente=sorgente_di(E.contesto), identita=forn2)
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

    # LA VALUTAZIONE INTERNA e' quella del RACCORDO: valuta sul periodo di
    # prova con il descrittore riferito all'INIZIO del periodo. La fase di
    # inserimento ha la propria valutazione, con il descrittore a t1, e non la
    # usa: richiederla costringerebbe a un riferimento che non e' quello
    # dell'episodio.
    if not cfg.get("valutazione_interna", True):
        reg.evento("valutazione interna del raccordo NON eseguita: la fase la "
                   "sostituisce con la propria")
        return ck
    if ok_griglia is not None and usa_desc:
        _verifica_finestra(ok_griglia, int(ist["prova"][0]))
    dpr = (_descrittori(D, nodi["prova"], int(ist["prova"][0]), E.variante,
                        NORM) if usa_desc else None)
    righe = []
    scartate = 0
    with torch.inference_mode():
        for t in orig["prova"]:
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
        tt = orig["prova"] + h
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
