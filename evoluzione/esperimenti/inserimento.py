#!/usr/bin/env python3
"""
Composizione della fase 3: configurazioni, adattamento di F, valutazione.
=========================================================================
**Nessun percorso alternativo**: qui si compongono soltanto i costruttori gia'
collaudati — `addestra_una`, `adattamento`, `valutazione.valuta` — con le
configurazioni dei cinque bracci.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import torch

from evoluzione.componente import griglia as GR
from evoluzione.componente.adattamento import adatta, carica_E, copia_da_E, \
    verifica_vincoli
from evoluzione.componente.bracci import proprieta as proprieta_braccio
from evoluzione.componente.episodio import lotti_episodio
from evoluzione.componente.predittore import ORIZZONTI
from evoluzione.componente.valutazione import valuta
from evoluzione.esperimenti.fasi import percorso_E

ETICHETTA = "inserimento_griglia"
D_STAT = 5


def statiche(D):
    K = D["r"].shape[1]
    return np.stack([D["m_r"].mean(0), np.zeros(K), np.ones(K), np.zeros(K),
                     np.ones(K)], 1).astype("float32")


VARIANTI_STATICA = ("congelata", "causale", "espansiva", "a", "b", "c")
# dopo E15: `espansiva` (causale, finestra da t0 all'origine corrente, minimo 24 h);
# `causale` e' la finestra fissa di 24 h (variante (a) di E14); `congelata` riproduce la campagna
STATICA_PREDEFINITA = "espansiva"
L24_STATICA = 96


def variante_statica() -> str:
    """La variante della statica, da `OR3_STATICA`; assente = `espansiva` (E15: causale a finestra
    espansiva). `causale` e' la finestra fissa di 24 h (variante (a) di E14); `congelata` e' la
    statica non causale della campagna del Paper 1 (difetto 21)."""
    v = os.environ.get("OR3_STATICA", "") or STATICA_PREDEFINITA
    if v not in VARIANTI_STATICA:
        raise ValueError(f"OR3_STATICA={v!r}: ammessi {VARIANTI_STATICA}")
    return v


def argomento_statica(ap):
    """`--statica`: l'interruttore degli esecutori; assente, vale l'ambiente e poi la predefinita."""
    ap.add_argument("--statica", choices=VARIANTI_STATICA, default=None,
                    help=f"statica per nodo: congelata (campagna Paper 1, non causale); espansiva "
                         f"(predefinita, E15: finestra da t0 all'origine, minimo 24 h); causale "
                         f"(finestra fissa di 24 h, E14); a, b, c = varianti di E14 (OR3_STATICA)")
    return ap


def applica_statica(valore):
    """Scrive `OR3_STATICA` per il processo e per i figli (`spawn` eredita l'ambiente)."""
    if valore:
        os.environ["OR3_STATICA"] = valore
    return variante_statica()


def t0_installazione(contesto: str, fine_periodo=None) -> int:
    """Il t0 dell'episodio: `fine_periodo` se dato (E5 episodi 2 e 3, E6: il periodo finisce a t0),
    altrimenti il calendario di prova del contesto."""
    if fine_periodo is not None:
        return int(fine_periodo)
    if contesto.startswith("PEMS08"):
        from evoluzione.esperimenti.esegui_e6 import T0_PROVA
        return int(T0_PROVA)
    if contesto.startswith("PEMS04"):
        from evoluzione.esperimenti.esegui_e6a import T0_PROVA
        return int(T0_PROVA)
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    return int(CALENDARIO[contesto][0])


def nodi_davvero_nuovi(braccio: str, nn):
    """E15 (lettura 1 del revisore, 27/10): per i bracci a corpus PRIVILEGIATO (A, C_A) i nodi
    "nuovi" sono iniziali a tutti gli effetti — hanno la storia su [0, t0) — e la loro copertura
    si calcola su [0, t0) come per gli altri: nessun nodo nuovo per la statica. Per gli altri
    bracci la finestra (minima 24 h, poi espansiva) vale dove il sensore e' davvero nuovo."""
    if proprieta_braccio(braccio).corpus == "privilegiato":
        return np.zeros(0, dtype="int64")
    return np.asarray(nn, dtype="int64")


def statica_addestramento(D, nodi, cfg, contesto):
    """La statica dell'ADDESTRAMENTO (addestramento.py): `statiche(D)` passata da `statica_cella`
    con i nodi nuovi dichiarati dalla configurazione (vuoti per E, E') e il t0 dell'episodio.
    Per A e C_A (corpus privilegiato) i nodi nuovi non sono nuovi: copertura su [0, t0)."""
    nn = nodi_davvero_nuovi(cfg.get("braccio", "P"), cfg.get("nodi_nuovi", []))
    t0 = t0_installazione(contesto, cfg.get("fine_periodo"))
    return statica_cella(statiche(D), D, nodi, nn, t0, int(cfg.get("seme_dichiarato", 0)))


def statica_cella(stat, D, nodi, nn, t0, seme):
    """E14: la statica della cella secondo la variante (`protocol/E14.md`).

    `stat` e' `statiche(D)`; `nn` sono i nodi inseriti nell'episodio (prova, o
    validazione in un episodio di validazione), `nodi["addestramento"]` gli
    iniziali; `t0` l'installazione; `seme` quello DICHIARATO della cella.
        congelata   `stat` com'e' (bit per bit; la campagna del Paper 1, non causale)
        espansiva   iniziali: media di m_r su [0, t0); nn: FINESTRA ESPANSIVA (E15),
                    all'origine t la media su (t0, max(t, t0 + 24 h)]. L'oggetto
                    restituito e' un vettore (K, 5) alla finestra MINIMA, identico a
                    `causale` (chi non valuta per origine — addestramento, selezione
                    del punto — vede quello), e porta `alle_origini(nodi, istanti)`
                    per chi valuta per origine (`valuta`, `lotti_episodio`)
        causale, a  iniziali: media di m_r su [0, t0); nn: media su (t0, t0 + 24 h]
        b           iniziali: idem; nn: media delle coperture causali degli iniziali
        c           iniziali: non causale; nn: coperture non causali permutate fra
                    i nn, una permutazione per seme
    """
    v = variante_statica()
    if v == "congelata":
        return stat
    stat = np.array(stat, copy=True)
    m = D["m_r"].astype("float64"); t0 = int(t0)
    nn = np.asarray(nn, dtype="int64")
    ini = np.asarray(nodi["addestramento"], dtype="int64")
    cov_nc = stat[:, 0].astype("float64")
    if v in ("causale", "espansiva", "a", "b"):
        cov_c = m[:t0].mean(0)
        stat[:, 0] = cov_c.astype("float32")
        if v == "espansiva":
            return StaticaEspansiva.costruisci(stat, m, nn, t0)
        if v in ("causale", "a"):
            stat[nn, 0] = m[t0 + 1:t0 + L24_STATICA + 1, :].mean(0)[nn].astype("float32")
        else:
            stat[nn, 0] = np.float32(cov_c[ini].mean())
    else:
        rng = np.random.default_rng(int(seme))
        stat[nn, 0] = cov_nc[nn][rng.permutation(len(nn))].astype("float32")
    return stat


class StaticaEspansiva(np.ndarray):
    """La statica per nodo a FINESTRA ESPANSIVA (E15, `protocol/E15.md`).

    Come array e' la statica alla finestra minima: nodi nuovi con la copertura
    media su (t0, t0 + 24 h], iniziali su [0, t0). `alle_origini(nodi, istanti)`
    da' la statica per origine, (B, n, 5): per i nodi nuovi la copertura media su
    (t0, max(t, t0 + 24 h)], per gli altri il vettore fisso. **Solo l'oggetto
    costruito da `costruisci` porta la finestra**: una vista o una copia
    (`stat[nodi]`, `np.array(stat)`) e' un array e basta, e chiederle le origini
    solleva, anziche' rispondere con la finestra minima in silenzio.
    """

    def __array_finalize__(self, obj):
        self._esp = None

    @classmethod
    def costruisci(cls, stat, m, nn, t0):
        m = np.asarray(m, dtype="float64"); t0 = int(t0); t1 = t0 + L24_STATICA
        nn = np.asarray(nn, dtype="int64")
        if t1 + 1 > m.shape[0]:
            raise ValueError(f"finestra minima oltre la serie: t0 {t0}, T {m.shape[0]}")
        # somme cumulate (una riga di zeri in testa): cs[t + 1] - cs[t0 + 1] = somma su (t0, t]
        cs = np.concatenate([np.zeros((1, len(nn))), np.cumsum(m[:, nn], 0)], 0)
        stat = np.array(stat, dtype="float32", copy=True)
        stat[nn, 0] = ((cs[t1 + 1] - cs[t0 + 1]) / (t1 - t0)).astype("float32")
        s = stat.view(cls)
        s._esp = {"cs": cs, "t0": t0, "t1": t1, "nn": nn,
                  "posizione": {int(n): j for j, n in enumerate(nn)}}
        return s

    def alle_origini(self, nodi, istanti):
        if self._esp is None:
            raise RuntimeError("statica espansiva senza finestra: l'oggetto e' una vista o una "
                               "copia; passare quello restituito da `statica_cella`")
        e = self._esp
        nodi = np.asarray(nodi, dtype="int64"); ist = np.asarray(istanti, dtype="int64")
        S = np.repeat(np.asarray(self)[nodi][None], len(ist), 0)           # (B, n, 5)
        col = [i for i, n in enumerate(nodi) if int(n) in e["posizione"]]
        if col and len(ist):
            j = [e["posizione"][int(nodi[i])] for i in col]
            tt = np.maximum(ist, e["t1"])
            if int(tt.max()) + 1 >= e["cs"].shape[0]:
                raise ValueError(f"origine {int(tt.max())} oltre la serie")
            cov = (e["cs"][tt + 1][:, j] - e["cs"][e["t0"] + 1][j]) / (tt - e["t0"])[:, None]
            S[:, col, 0] = cov.astype("float32")
        return S


def statica_alle_origini(stat, nodi, istanti):
    """(B, n, 5) se `stat` e' la statica espansiva di `statica_cella`, altrimenti None: chi
    valuta per origine la chiama e, con None, usa `stat[nodi]` come prima (bit per bit)."""
    if isinstance(stat, StaticaEspansiva):
        return stat.alle_origini(nodi, istanti)
    return None


def impronta_nodi(ids) -> str:
    """L'impronta dell'insieme ORDINATO: due insiemi di pari numerosita'
    possono essere diversi."""
    a = np.sort(np.asarray(ids, dtype="int64"))
    return hashlib.sha256(a.tobytes()).hexdigest()[:16]


# le ULTIME 6 ORE dell'acquisizione, in passi da 15 minuti: le origini che
# R-mon usa per la selezione, e SOLO quelle (protocol/E3.md)
PASSI_6H = 24


def origini_selezione_nuovi(o_acq, t1: int) -> list:
    """Le origini d'acquisizione nelle ultime 6 ore prima di t1: i bersagli
    maturano entro t1 per costruzione di `origini_acquisizione`."""
    return [int(t) for t in o_acq if int(t) > int(t1) - PASSI_6H]


def cfg_braccio(b: str, c: str, p: int, s: int, out: Path, nodi,
                o_acq, t1=None) -> dict:
    """La configurazione del braccio: popolazione, corpus, campionamento,
    selezione del punto di controllo. Tutto dalla tabella unica."""
    cfg = {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
           "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
           "orizzonti": list(ORIZZONTI), "sorgente": "traffic4cast",
           "etichetta": ETICHETTA, "braccio": b,
           "training_protocol": "principale", "griglia_temporale": "reale",
           "checkpoint_selection_population": "initial_network",
           "dir_pesi": str(out / "pesi_griglia"),
           "dir_canonico": str(out / "canonico"),
           "dir_stati_completi": str(out / f"stati_completi_{ETICHETTA}"),
           "nodi_rete_iniziale": [int(z) for z in nodi["addestramento"]],
           "nodi_nuovi": [int(z) for z in nodi["prova"]],
           # la valutazione della fase e' `valuta_prova`, col descrittore a t1
           "valutazione_interna": False,
           "popolazione": "iniziale", "campionamento": "uniforme_istanti",
           # UN FILE PER ESECUZIONE: il nome storico userebbe `variante` e
           # `inizializzazione`, costanti qui, e tutte le esecuzioni di uno
           # stesso braccio scriverebbero sullo stesso punto di controllo
           "nome_ck": f"ck_{b}_{c}_p{p}_s{s}.pt",
           "variante": None}
    # popolazione, campionamento e variante vengono dalla TABELLA UNICA
    # (`componente/bracci.py`): qui non si confrontano nomi
    # **Anche F passa di qui**: la sua configurazione va nel manifesto, e
    # `addestra_una` non la vede. Per chi non addestra restano i predefiniti
    # («iniziale», «uniforme_istanti», nessuna variante), come prima.
    pb = proprieta_braccio(b)
    if pb.addestra:
        cfg["variante"] = pb.variante
        cfg["popolazione"] = pb.popolazione
        cfg["campionamento"] = pb.campionamento
    if pb.addestra and pb.campionamento != "uniforme_istanti":
        # il contratto di R e dei suoi derivati: budget invariato, 32 x K
        # iniziali finestre per aggiornamento, origini nuove dichiarate
        cfg["nodi_iniziali_R"] = [int(z) for z in nodi["addestramento"]]
        cfg["origini_nuovi"] = [int(z) for z in o_acq]
    if pb.addestra and pb.selezione_ck != "initial_network":
        if t1 is None:
            raise ValueError(f"{b}: la selezione «{pb.selezione_ck}» richiede t1")
        cfg["checkpoint_selection_population"] = pb.selezione_ck
        cfg["origini_selezione_nuovi"] = origini_selezione_nuovi(o_acq, t1)
        if not cfg["origini_selezione_nuovi"]:
            raise ValueError(f"{b}: nessuna origine nelle ultime 6 ore")
    return cfg


def _modello_da_ck(ck: Path, D, nodi, cfg):
    """Ricostruisce il modello dal punto di controllo, con gli STESSI
    costruttori dell'addestramento."""
    from evoluzione.componente.predittore import PredittorePerNodo
    from evoluzione.esperimenti.addestramento import _fornitore
    from evoluzione.esperimenti.addestramento import sorgente_di
    d = torch.load(ck, map_location="cpu", weights_only=False)
    nodi_add = np.asarray(d["nodi_iniziali"], dtype="int64")
    forn, _ = _fornitore(d["braccio"], d["d_descrittore"], nodi_add)
    # **LA SORGENTE VIENE DAL PUNTO DI CONTROLLO**: costruirne uno a nove
    # canali per pesi che ne hanno undici fallirebbe, ed e' quanto accadeva.
    m = PredittorePerNodo(d["d_descrittore"], D_STAT,
                          sorgente=sorgente_di(d.get("contesto", "")),
                          identita=forn)
    m.load_state_dict(d["state_dict"], strict=True)
    m.eval()
    return m, d


def adatta_F(c, p, seme_torch, out: Path, D, nodi, ist, o_acq, reg, stat=None):
    """F: parte dal punto E della pipeline corretta, muove SOLO i nuovi
    embedding, con la configurazione appena congelata. `stat`: la statica della
    cella (E14, `statica_cella`); assente = `statiche(D)`, come nella fase 3."""
    cfgF = json.loads((out / "selezione_F_griglia" / "configurazione_F.json")
                      .read_text())
    if not cfgF.get("congelata"):
        raise RuntimeError("la configurazione di F non e' congelata")
    s = cfgF["scelte"][c]
    fE = percorso_E(out / "E_inserimento_griglia", c, p, int(seme_torch))
    dE, nodi_in, imp_E = carica_E(fE, D_STAT)
    from evoluzione.analisi.pesi import carica as carica_pesi
    w = torch.as_tensor(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                        dtype=torch.float32)
    from evoluzione.esperimenti.addestramento import _canali, _normalizzazione
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    if stat is None:
        stat = statica_cella(statiche(D), D, nodi, nodi["prova"], t0_installazione(c), int(seme_torch))
    m, forn = copia_da_E(dE, nodi_in, nodi["prova"], D_STAT)
    # UN SOLO LOTTO, non uno per nodo: l'adattamento e' vettorizzato e la
    # perdita totale e' la somma di quelle per nodo, sicche' il gradiente di
    # ciascun embedding coincide con quello dell'adattamento separato
    # (collauda_vettorizzazione.py). Un lotto per nodo fa 135 passaggi in
    # avanti per aggiornamento, ed e' quanto costava 493 s invece di 4.
    lotti = lotti_episodio(x, D["classe"], stat, nodi["prova"], o_acq)
    t0 = time.time()
    reg_ad = []
    n = adatta(m, forn, lotti, w, s["passo"], s["aggiornamenti"], reg_ad)
    costo = {"addestramento_s": 0.0, "inserimento_s": time.time() - t0}
    verifica_vincoli(m, forn, dE, imp_E, dE["state_dict"]["identita.embedding"],
                     fE)
    reg.artefatto("adattamento_F", punto_E=fE.name, impronta_E=imp_E,
                  aggiornamenti_richiesti=s["aggiornamenti"],
                  aggiornamenti_eseguiti=n, passo=s["passo"],
                  nodi_adattati=len(lotti), registro=reg_ad,
                  parametri_mossi="solo i nuovi embedding")
    m.eval()
    return m, costo


def valuta_prova(b, c, p, s, out: Path, D, nodi, ist, t1, ok, reg, ck, mod,
                 fasce):
    """Le STESSE chiavi di prova per tutti i bracci, sul perimetro approvato.

    Perimetro primario: tutte le origini ammissibili dopo l'acquisizione, con
    bersagli entro il periodo di prova. Si riportano anche la prima giornata e
    le fasce di tempo dall'installazione.
    """
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.esperimenti.addestramento import (_canali, _descrittori,
                                                      _normalizzazione)
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    # E15: per A e C_A i nodi di prova sono iniziali (copertura su [0, t0)); per gli altri sono nuovi
    stat = statica_cella(statiche(D), D, nodi, nodi_davvero_nuovi(b, nodi["prova"]),
                         t0_installazione(c), int(s))
    w = torch.as_tensor(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                        dtype=torch.float32)
    fine = D["r"].shape[0] - max(ORIZZONTI)
    per = GR.origini_dopo(ok, t1, fine)
    if not per:
        raise RuntimeError("perimetro di valutazione vuoto")
    t_desc = 0.0
    if mod is None:
        m, d = _modello_da_ck(ck, D, nodi, None)
        desc = None
        if d["d_descrittore"]:
            # IL DESCRITTORE DI P SI COSTRUISCE ALL'INSERIMENTO, dalle 24 ore
            # di acquisizione: il suo costo appartiene all'inserimento, non
            # all'addestramento iniziale
            GR.verifica_finestra_descrittore(ok, int(t1))
            t_ = time.time()
            desc = _descrittori(D, nodi["prova"], int(t1), "BASE-CORRECTED",
                                NORM)
            t_desc = time.time() - t_
    else:
        m, desc = mod, None
    t_inf = time.time()
    fuori = {"perimetro_primario": valuta(m, x, D["classe"], stat,
                                          nodi["prova"], per, w, desc)}
    fuori["perimetro_primario"]["origini"] = len(per)
    for a_, b_, nome in fasce:
        sel = [t for t in per if a_ <= t - t1 < b_]
        if sel:
            fuori[nome] = valuta(m, x, D["classe"], stat, nodi["prova"], sel,
                                 w, desc)
            fuori[nome]["origini"] = len(sel)
    reg.artefatto("valutazione_prova", nodi=len(nodi["prova"]),
                  impronta_chiavi=impronta_nodi(nodi["prova"]),
                  origini_perimetro=len(per), t1=int(t1), **fuori)
    fuori["impronta_chiavi"] = impronta_nodi(nodi["prova"])
    return {"metriche": fuori,
            "costo": {"inferenza_s": time.time() - t_inf,
                      "costruzione_descrittore_s": t_desc,
                      "origini_valutate": len(per)}}
