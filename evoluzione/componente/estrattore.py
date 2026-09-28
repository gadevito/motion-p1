#!/usr/bin/env python3
"""
Estrattore unificato — schemi e calcolo DIRETTO di riferimento.
===============================================================
Il calcolo diretto e' l'ORACOLO di correttezza, non necessariamente
l'implementazione di esercizio: seleziona esplicitamente le osservazioni nella
finestra, applica le maschere e calcola ogni statistica per intero.

L'aggiornamento incrementale vive in un modulo separato e **non riusa questa
logica di accumulazione**: se la condividessero, condividerebbero anche
l'eventuale errore.

BASE ed EXTENDED sono schemi ESPLICITI E VERSIONATI, non rami scelti in base
all'esperimento. La stessa implementazione serve il compito denso e
l'inserimento: cambia il parametro della chiamata, non l'estrattore.

LA FINESTRA e' (t-L, t] intersecata con [t0, t], dove t0 e' l'installazione. Il
limite inferiore lo applica l'estrattore, non il chiamante.

ACCUMULATORI IN DOPPIA PRECISIONE. Le statistiche si calcolano in `float64`.
Questo non tocca la convenzione in precisione singola gia' fissata per la
costruzione del rapporto e delle classi, che riguarda il bersaglio.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from evoluzione.componente.normalizzazione import applica, verifica_contratto

SCHEMA_VERSIONE = "1.2"
# LA VERSIONE DI IMPLEMENTAZIONE E' DISTINTA DA QUELLA DI SCHEMA. Lo schema
# elenca nomi e ordine delle caratteristiche; l'implementazione dice come sono
# calcolate. Una correzione che non tocchi l'elenco lascia lo schema invariato e
# incrementa questa.
#
#   1.0  prima stesura
#   1.1  soglie valutate in precisione singola; ordine delle operazioni sul
#        rapporto; accumulatori traslati per la stabilita' della varianza
#   1.2  schemi per sorgente; deviazione scalata e non centrata
#   1.3  `copertura_coppie` spostata nel blocco CONDIVISO: era calcolata solo
#        dentro il ramo EXTENDED e restava a zero su BASE-CORRECTED, sicche' le
#        due varianti non condividevano davvero le informazioni di
#        disponibilita'. Aggiunte due verifiche: che sia calcolata, e che tutte
#        e quattordici le componenti coincidano fra le due varianti.
#   1.4  sorgente `pems04`, con identificazione propria: stessa struttura di
#        GO-MO — velocita' relativa, conteggio CONTINUO, occupazione — ma
#        distinta nello schema versionato.
VERSIONE_IMPLEMENTAZIONE = "1.4"

# I CANALI DIPENDONO DALLA SORGENTE, non dai dati. Lo schema e' DICHIARATO: il
# componente non deve decidere quali caratteristiche rimuovere osservando se un
# canale sia costante, perche' un canale realmente misurato puo' legittimamente
# esserlo.
#
#   traffic4cast   fornisce velocita' mediana e `volume_class`, una classe di
#                  volume discretizzata a tre livelli (1, 3, 5). NON fornisce
#                  occupazione: il canale e' assente dalla sorgente, non mancante.
#   gomo           fornisce conteggio veicolare e occupazione percentuale, e il
#                  fattore di congestione vi e' RICOSTRUITO, non misurato.
#
# `volume_class` e conteggio veicolare non condividono il nome, perche' non sono
# la stessa grandezza fisica: media e deviazione della prima sono sommari della
# CODIFICA discretizzata, e la loro interpretazione dipende dai livelli 1/3/5.
#   pems04         flusso veicolare CONTINUO e occupazione: la stessa struttura
#                  di GO-MO, ma con **identificazione propria**, perche' la
#                  provenienza, la risoluzione e il riferimento di velocita'
#                  sono diversi e lo schema versionato deve poterlo distinguere.
#                  Il flusso NON si discretizza: i terzili sono una proposta
#                  scartata prima del test.
SORGENTI = {
    "traffic4cast": ("r", "volume_class"),
    "gomo": ("r", "conteggio", "occupazione"),
    "pems04": ("r", "conteggio", "occupazione"),
}
# mappa nome di canale -> attributo di `Osservazioni`
ATTRIBUTO = {"r": "r", "volume_class": "f", "conteggio": "f", "occupazione": "o"}
CANALI = SORGENTI["gomo"]      # predefinito storico, per compatibilita'
N_BANDE = 8                 # otto fasce di tre ore dell'ORA LOCALE
TAU = 0.005                 # soglia convenzionale sulle variazioni
L_MAX = 2688                # ventotto giorni a quindici minuti
NON_STIMABILE = 0.0         # valore convenzionale: la disponibilita' lo dichiara


# --------------------------------------------------------------- schemi -----
def nomi_statistiche(schema: str, sorgente: str = "gomo") -> list[str]:
    n = [f"{op}_{c}" for c in SORGENTI[sorgente] for op in ("media", "dev")]
    n += [f"banda_{b}" for b in range(N_BANDE)]
    if schema == "EXTENDED":
        n += [f"freq_classe_{k}" for k in (1, 2, 3)]
        n += ["autocorr_1"]
        n += ["quota_incremento", "quota_decremento"]
    return n


def nomi_disponibilita(schema: str, sorgente: str = "gomo") -> list[str]:
    """LEGACY conserva le due sole componenti storiche — quota di validi e
    codice di durata — perche' riprodurre la rappresentazione precedente
    significa anche riprodurne l'assenza di maschere.

    BASE-CORRECTED ed EXTENDED condividono invece il blocco PER INTERO: se
    cambiassero anche le informazioni di disponibilita', il confronto fra le due
    misurerebbe il beneficio complessivo della rappresentazione anziche' quello
    delle sole statistiche aggiuntive.
    """
    if schema == "LEGACY":
        return ["quota_validi", "codice_durata"]
    return (["durata_nominale", "durata_effettiva", "n_valide"]
            + [f"copertura_{c}" for c in SORGENTI[sorgente]]
            + [f"disponibilita_banda_{b}" for b in range(N_BANDE)]
            + ["copertura_coppie"])


def schema_di(variante: str, sorgente: str = "gomo") -> dict:
    """Lo schema DICHIARATO per una variante e una sorgente.

    LEGACY conserva i tre canali e le due sole disponibilita' storiche
    indipendentemente dalla sorgente: la sua funzione e' la fedelta' alle
    funzioni precedenti, non la coerenza con il dato.
    """
    if variante == "LEGACY":
        return {"statistiche": nomi_statistiche(variante, "gomo"),
                "disponibilita": nomi_disponibilita(variante, "gomo"),
                "sorgente": "storica"}
    return {"statistiche": nomi_statistiche(variante, sorgente),
            "disponibilita": nomi_disponibilita(variante, sorgente),
            "sorgente": sorgente}


SCHEMI = {s: schema_di(s, "gomo")
          for s in ("LEGACY", "BASE-CORRECTED", "EXTENDED")}
SCHEMI_T4C = {s: schema_di(s, "traffic4cast")
              for s in ("LEGACY", "BASE-CORRECTED", "EXTENDED")}
SCHEMI_PEMS04 = {s: schema_di(s, "pems04")
                 for s in ("LEGACY", "BASE-CORRECTED", "EXTENDED")}


# ---------------------------------------------------------- osservazioni ----
@dataclass
class Osservazioni:
    """Le osservazioni di UN sensore su una griglia temporale regolare.

    `istanti` sono indici di passo crescenti e **senza duplicati**: questa prima
    versione rifiuta esplicitamente duplicati e fuori ordine anziche' gestirli
    implicitamente, perche' ignorarli senza registrazione nasconde un difetto
    della pipeline a monte.
    """
    istanti: np.ndarray
    r: np.ndarray
    f: np.ndarray
    o: np.ndarray
    classe: np.ndarray
    ora_locale: np.ndarray
    t0: int = 0                     # istante di installazione
    reference_version: str = ""

    def __post_init__(self):
        self.istanti = np.asarray(self.istanti, dtype="int64")
        # gli ATTRIBUTI restano r, f, o; il nome logico del canale dipende dalla
        # sorgente ed e' risolto da ATTRIBUTO al momento dell'estrazione
        for c in ("r", "f", "o"):
            setattr(self, c, np.asarray(getattr(self, c), dtype="float64"))
        self.classe = np.asarray(self.classe, dtype="int64")
        self.ora_locale = np.asarray(self.ora_locale, dtype="int64")
        n = len(self.istanti)
        for nome in ("r", "f", "o", "classe", "ora_locale"):
            if len(getattr(self, nome)) != n:
                raise ValueError(f"`{nome}` ha lunghezza diversa da `istanti`")
        d = np.diff(self.istanti)
        if (d <= 0).any():
            dup = int((d == 0).sum())
            raise ValueError(
                f"istanti non strettamente crescenti: {dup} duplicati, "
                f"{int((d < 0).sum())} fuori ordine. Questa versione li rifiuta.")


@dataclass
class Estrazione:
    """Il contratto minimo: ogni campo e' sempre presente."""
    sensor_id: str
    schema_version: str
    implementation_version: str
    schema_name: str
    feature_names_and_order: list
    statistics: np.ndarray
    availability_names_and_order: list
    availability: np.ndarray
    requested_duration: int
    effective_duration: int
    window_start: int | None
    window_end: int | None
    reference_version: str
    n_osservazioni_finestra: int
    note: str = ""
    non_stimabili: list = field(default_factory=list)

    def as_dict(self):
        d = {k: v for k, v in self.__dict__.items()}
        d["statistics"] = np.asarray(self.statistics).tolist()
        d["availability"] = np.asarray(self.availability).tolist()
        return d


# ------------------------------------------------------ calcolo diretto -----
def finestra(oss: Osservazioni, t: int, L: int, l_max: int = L_MAX):
    """(indici, inizio, fine, durata effettiva, troncata) della finestra ammessa.

    SEMANTICA DELL'INSTALLAZIONE. `t0` e' il PRIMO istante ammissibile: la
    finestra e' (t-L, t] intersecata con [t0, t], sicche' l'osservazione a t0
    entra. Il codice usa `istanti > t0 - 1`, equivalente a `>= t0`, in ogni
    ramo: la prima stesura escludeva t0 con L = -1 e lo includeva con L > 0.

    SEMANTICA DI L = -1. Significa «tutta la storia dall'installazione, fino
    alla capacita' del buffer»: oltre `l_max` la finestra e' TRONCATA, e il
    troncamento viene dichiarato. Una storia illimitata non e' rappresentabile
    con un buffer limitato, e tacerlo darebbe una durata effettiva falsa.

    L = 0 e' la finestra vuota.
    """
    if L == 0:
        return np.array([], dtype="int64"), None, None, 0, False
    span = (t - oss.t0 + 1) if L < 0 else L
    troncata = bool(L < 0 and span > l_max)
    span = min(span, l_max)
    basso = max(t - span, oss.t0 - 1)
    m = (oss.istanti > basso) & (oss.istanti <= t)
    idx = np.where(m)[0]
    eff = int(max(min(span, t - oss.t0 + 1), 0))
    if not len(idx):
        return idx, None, None, eff, troncata
    return (idx, int(oss.istanti[idx[0]]), int(oss.istanti[idx[-1]]),
            eff, troncata)


def _coppie_consecutive(istanti, idx):
    """Posizioni (i, j) di coppie con ENTRAMBI gli estremi nella finestra e
    distanti esattamente un passo. Una coppia a cavallo di un'interruzione non
    e' consecutiva e non entra."""
    if len(idx) < 2:
        return np.array([], dtype="int64"), np.array([], dtype="int64")
    a, b = idx[:-1], idx[1:]
    ok = (istanti[b] - istanti[a]) == 1
    return a[ok], b[ok]


def estrai_diretto(oss: Osservazioni, t: int, L: int, sensor_id: str = "",
                   schema: str = "EXTENDED", norm: dict | None = None,
                   l_max: int = L_MAX, sorgente: str = "gomo",
                   canali_costanti=frozenset()) -> Estrazione:
    """L'oracolo: calcola ogni statistica dalla finestra selezionata.

    `sorgente` decide quali canali esistono: e' DICHIARATA, non dedotta dai dati.
    """
    if schema not in SCHEMI:
        raise ValueError(f"schema ignoto: {schema}; ammessi {list(SCHEMI)}")
    if sorgente not in SORGENTI:
        raise ValueError(f"sorgente ignota: {sorgente}; ammesse {list(SORGENTI)}")
    if L > l_max:
        raise ValueError(f"finestra richiesta {L} oltre la capacita' {l_max}")
    sch = schema_di(schema, sorgente)
    canali = SORGENTI["gomo"] if schema == "LEGACY" else SORGENTI[sorgente]
    ns, nq = sch["statistiche"], sch["disponibilita"]
    # CONTRATTO BLOCCANTE: una caratteristica che richiede normalizzazione e non
    # trova i propri parametri solleva, non salta la trasformazione
    if norm:
        # `canali_costanti` va propagato fin qui: dichiararlo una volta a monte
        # non basta, perche' il contratto si verifica a ogni estrazione
        verifica_contratto(ns, nq, norm, etichetta=f"{schema}/{sorgente}",
                           canali_costanti=canali_costanti)
    s = np.full(len(ns), NON_STIMABILE, dtype="float64")
    q = np.zeros(len(nq), dtype="float64")
    idx, inizio, fine, eff, troncata = finestra(oss, t, L, l_max)
    mancanti = []
    S = {k: i for i, k in enumerate(ns)}
    Q = {k: i for i, k in enumerate(nq)}
    norm = norm or {}

    def std(nome, x, centra=None):
        """Standardizzazione secondo il CONTRATTO.

        La chiave e la centratura le decide `normalizzazione.py` dal nome della
        caratteristica: la media si centra e si scala, la deviazione si scala
        soltanto, una banda usa i parametri di `r`. Senza `norm` si restituisce
        il valore grezzo, ma con `norm` una chiave assente SOLLEVA.
        """
        return applica(nome, x, norm) if norm else x

    passi = max(len(idx), 0)
    legacy = schema == "LEGACY"
    # LEGACY riproduce le convenzioni storiche: denominatore protetto a uno,
    # fascia non osservata riempita con la media globale, nessun elenco di non
    # stimabili. Non e' la soluzione di esercizio: serve al raccordo con i
    # risultati gia' pubblicati, e va dichiarata come tale.
    # il riempimento storico delle fasce non osservate usa la media GLOBALE di
    # addestramento, non quella della finestra: dopo la standardizzazione vale
    # quindi esattamente zero, ed e' indistinguibile da una fascia osservata che
    # coincida con la media di addestramento
    mu_glob = float(norm.get("media_r", (0.0, 1.0))[0]) if legacy else 0.0

    # ---- gruppo 1: livello e dispersione, denominatore per CANALE ---------
    for c in canali:
        v = getattr(oss, ATTRIBUTO[c])[idx] if passi else np.array([])
        val = v[np.isfinite(v)]
        if f"copertura_{c}" in Q:
            q[Q[f"copertura_{c}"]] = len(val) / passi if passi else 0.0
        if c == "r" and "copertura_r" in Q:
            q[Q["copertura_r"]] = len(val) / passi if passi else 0.0
        if legacy:
            # denominatore protetto: con zero osservazioni valide la somma e'
            # nulla e la media risulta zero, indistinguibile da una media
            # osservata che vi coincida
            den = max(len(val), 1)
            m = float(val.sum()) / den
            vv = float(np.sqrt(max((val ** 2).sum() / den - m * m, 0.0)))
            s[S[f"media_{c}"]] = std(f"media_{c}", m)
            s[S[f"dev_{c}"]] = std(f"dev_{c}", vv)
        elif len(val) >= 1:
            s[S[f"media_{c}"]] = std(f"media_{c}", float(val.mean()))
            if len(val) >= 2:
                s[S[f"dev_{c}"]] = std(f"dev_{c}", float(val.std(ddof=0)))
            else:
                mancanti.append(f"dev_{c}")
        else:
            mancanti += [f"media_{c}", f"dev_{c}"]

    # ---- gruppo 2: profilo sulle otto fasce dell'ORA LOCALE ---------------
    if passi:
        ore = oss.ora_locale[idx]
        rr = oss.r[idx]
        for b in range(N_BANDE):
            inb = (ore // 3) == b
            v = rr[inb & np.isfinite(rr)]
            att = int(inb.sum())
            if f"disponibilita_banda_{b}" in Q:
                q[Q[f"disponibilita_banda_{b}"]] = len(v) / att if att else 0.0
            if len(v):
                s[S[f"banda_{b}"]] = std(f"banda_{b}", float(v.mean()))
            elif legacy:
                # fascia mai osservata riempita con la media globale: senza
                # maschera resta indistinguibile da una fascia osservata che
                # coincida con essa
                s[S[f"banda_{b}"]] = std(f"banda_{b}", mu_glob)
            else:
                mancanti.append(f"banda_{b}")
    elif not legacy:
        mancanti += [f"banda_{b}" for b in range(N_BANDE)]

    # ---- copertura delle coppie: appartiene al blocco CONDIVISO ------------
    # BASE-CORRECTED non ha le statistiche sulle coppie ma NE HA LA
    # DISPONIBILITA': calcolarla solo dentro il ramo EXTENDED la lasciava a zero,
    # e le due varianti non condividevano davvero il blocco.
    if "copertura_coppie" in Q:
        ca, cb = _coppie_consecutive(oss.istanti, idx)
        if len(ca):
            ok_c = np.isfinite(oss.r[ca]) & np.isfinite(oss.r[cb])
            m_c = int(ok_c.sum())
        else:
            m_c = 0
        q[Q["copertura_coppie"]] = m_c / max(passi - 1, 1) if passi > 1 else 0.0

    if schema == "EXTENDED":
        # ---- gruppo 3: frequenze di classe, denominatore = celle classificate
        cl = oss.classe[idx] if passi else np.array([], dtype="int64")
        cl = cl[cl > 0]
        for k in (1, 2, 3):
            if len(cl):
                s[S[f"freq_classe_{k}"]] = float((cl == k).mean())
            else:
                mancanti.append(f"freq_classe_{k}")

        # ---- gruppi 4 e 5: sulle sole coppie consecutive valide ------------
        a, b = _coppie_consecutive(oss.istanti, idx)
        if len(a):
            x, y = oss.r[a], oss.r[b]
            ok = np.isfinite(x) & np.isfinite(y)
            x, y = x[ok], y[ok]
        else:
            x = y = np.array([])
        m = len(x)
        if m >= 2 and x.std(ddof=0) > 0 and y.std(ddof=0) > 0:
            s[S["autocorr_1"]] = float(np.corrcoef(x, y)[0, 1])
        else:
            mancanti.append("autocorr_1")
        if m >= 1:
            d = y - x
            s[S["quota_incremento"]] = float((d > TAU).mean())
            s[S["quota_decremento"]] = float((d < -TAU).mean())
        else:
            mancanti += ["quota_incremento", "quota_decremento"]

    # ---- disponibilita' -------------------------------------------------
    if legacy:
        nv = int(np.isfinite(oss.r[idx]).sum()) if passi else 0
        q[Q["quota_validi"]] = nv / passi if passi else 0.0
        q[Q["codice_durata"]] = (1.0 if L < 0 else
                                 np.log1p(L) / np.log1p(672))
        mancanti = []          # la storica non dichiara nulla come non stimabile
    if "durata_nominale" in Q:
        # con L = -1 la durata nominale richiesta coincide con quella effettiva:
        # non si chiede una finestra fissa ma tutta la storia disponibile
        nl = eff if L < 0 else L
        q[Q["durata_nominale"]] = np.log1p(min(nl, l_max)) / np.log1p(l_max)
    if "durata_effettiva" in Q:
        q[Q["durata_effettiva"]] = np.log1p(eff) / np.log1p(l_max)
    if "n_valide" in Q:
        nv = int(np.isfinite(oss.r[idx]).sum()) if passi else 0
        q[Q["n_valide"]] = np.log1p(nv) / np.log1p(l_max)

    return Estrazione(
        sensor_id=sensor_id, schema_version=SCHEMA_VERSIONE,
        implementation_version=VERSIONE_IMPLEMENTAZIONE, schema_name=schema,
        feature_names_and_order=ns, statistics=s,
        availability_names_and_order=nq, availability=q,
        requested_duration=L, effective_duration=eff,
        window_start=inizio, window_end=fine,
        reference_version=oss.reference_version,
        n_osservazioni_finestra=passi, non_stimabili=mancanti,
        note=("finestra vuota: nessuna statistica stimabile" if not passi else
              f"storia troncata alla capacita' del buffer ({l_max} passi)"
              if troncata else ""))
