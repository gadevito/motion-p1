#!/usr/bin/env python3
"""
La tabella unica delle proprieta' del braccio.
===============================================
Fino a qui i bracci erano dichiarati in SEI punti diversi del codice: il
fornitore in `_fornitore`, chi carica l'artefatto canonico in
`canonico.CARICANO`, chi non usa descrittori in un elenco dentro
`addestra_una`, chi e' preparatorio in un altro, il prefisso del punto di
controllo in un terzo, popolazione e corpus in `fasi`. Aggiungendo E1 ne sono
stati dimenticati quattro, e ogni volta il difetto e' emerso solo eseguendo —
una volta dopo 108 esecuzioni fallite, una volta dopo un'ora e mezza di
calcolo.

**Da ora un braccio si dichiara QUI, una volta, con tutte le sue proprieta'.**
I moduli che prima confrontavano stringhe interrogano la tabella. Un braccio
non dichiarato solleva subito, con il nome, non a meta' campagna.

Questo modulo non importa torch: i collaudi della tabella girano ovunque.

    C        nessuna identita'                    NoIdentity
    P        descrittore osservabile              ObservableIdentityEncoder
    E        embedding appreso, preparatorio      LearnedNodeEmbedding
    E1       E con token ignoto e dropout rho     LearnedNodeEmbedding(token)
    A        E sulla rete ampliata, privilegiato  LearnedNodeEmbedding
    R        riaddestramento, uniforme per NODO   LearnedNodeEmbedding
    R-orig   riaddestramento, uniforme per ORIGINE (E3)
    R-mon    R-orig con selezione che sorveglia i nodi nuovi (E3)
    F        adattamento locale da E, non addestra

**Cambiare una riga di questa tabella cambia il protocollo**: le righe dei
bracci congelati (C, P, E, E1, A, R, F) sono verificate da
`collauda_bracci.py` contro i predicati che le hanno sostituite.
"""
from __future__ import annotations

from dataclasses import dataclass, fields

# i valori ammessi, per rifiutare refusi nella tabella stessa
FORNITORI = ("nessuna", "descrittore", "embedding", "embedding_token",
             "adattato_da_E")
POPOLAZIONI = ("iniziale", "ampliata", "nessuna")
CORPUS = ("originario", "privilegiato", "post_installazione", "acquisizione")
CAMPIONAMENTI = ("uniforme_istanti", "uniforme_nodo", "uniforme_origine",
                 "nessuno")
SELEZIONI = ("initial_network", "initial_network_piu_nuovi_6h", "nessuna")


@dataclass(frozen=True)
class Braccio:
    nome: str
    fornitore: str
    usa_descrittore: bool       # il modello riceve un descrittore per nodo
    carica_canonico: bool       # carica l'artefatto dei moduli comuni
    preparatorio: bool          # l'uscita e' il punto di controllo, nessuna
                                # valutazione interna sui nodi di prova
    prefisso_ck: bool           # nome ck_<braccio>_<citta>_p<n>_s<seme>
    addestra: bool              # passa da `addestra_una`
    popolazione: str            # nodi in addestramento
    corpus: str                 # periodi e nodi ammessi
    campionamento: str          # come si estraggono le finestre
    selezione_ck: str           # su quali nodi si sceglie il punto
    costo_all_inserimento: bool  # l'addestramento avviene DOPO t0
    attende_acquisizione: bool  # pronto solo dopo le 24 h
    richiede_rho: bool          # identity dropout dichiarato
    variante: str | None        # schema del descrittore, se lo usa
    descrizione_popolazione: str
    descrizione_corpus: str
    parete_attesa_min: tuple    # (min, max) minuti di parete per esecuzione,
                                # misura compresa, anche in concorrenza a 8:
                                # un'esecuzione fuori intervallo FERMA il lancio

    def __post_init__(self):
        guai = []
        if self.fornitore not in FORNITORI:
            guai.append(f"fornitore «{self.fornitore}»")
        if self.popolazione not in POPOLAZIONI:
            guai.append(f"popolazione «{self.popolazione}»")
        if self.corpus not in CORPUS:
            guai.append(f"corpus «{self.corpus}»")
        if self.campionamento not in CAMPIONAMENTI:
            guai.append(f"campionamento «{self.campionamento}»")
        if self.selezione_ck not in SELEZIONI:
            guai.append(f"selezione «{self.selezione_ck}»")
        if self.usa_descrittore != (self.fornitore == "descrittore"):
            guai.append("usa_descrittore incoerente col fornitore")
        if self.usa_descrittore and not self.variante:
            guai.append("usa descrittori senza variante")
        if self.richiede_rho != (self.fornitore == "embedding_token"):
            guai.append("rho incoerente col fornitore")
        if not self.addestra and (self.carica_canonico or self.preparatorio):
            guai.append("non addestra ma carica il canonico o e' preparatorio")
        lo, hi = self.parete_attesa_min
        if not (0 < lo < hi):
            guai.append(f"intervallo di parete incoerente {self.parete_attesa_min}")
        if guai:
            raise ValueError(f"braccio {self.nome}: " + "; ".join(guai))


def _b(nome, fornitore, *, canonico=True, preparatorio=False, prefisso=False,
       addestra=True, popolazione="iniziale", corpus="originario",
       campionamento="uniforme_istanti", selezione="initial_network",
       costo_inserimento=False, attesa=False, variante=None,
       pop_descr="nodi iniziali", corpus_descr="addestramento originario",
       parete=None):
    # TEMPO DI PARETE ATTESO per esecuzione, in minuti. Chi addestra: 2.290
    # aggiornamenti, 40-50 min isolato, fino a ~90 in concorrenza a 8;
    # chi adatta: secondi di adattamento piu' la valutazione. E' il controllo
    # che avrebbe fermato i 216 adattamenti usciti col nome di un
    # riaddestramento (un minuto l'uno).
    if parete is None:
        parete = (15.0, 180.0) if addestra else (0.1, 20.0)
    return Braccio(
        nome=nome, fornitore=fornitore,
        usa_descrittore=(fornitore == "descrittore"),
        carica_canonico=canonico, preparatorio=preparatorio,
        prefisso_ck=prefisso, addestra=addestra, popolazione=popolazione,
        corpus=corpus, campionamento=campionamento, selezione_ck=selezione,
        costo_all_inserimento=costo_inserimento, attende_acquisizione=attesa,
        richiede_rho=(fornitore == "embedding_token"), variante=variante,
        descrizione_popolazione=pop_descr, descrizione_corpus=corpus_descr,
        parete_attesa_min=tuple(float(z) for z in parete))


_AMPLIATA_A = "nodi iniziali + nodi che simulano le nuove installazioni"
_AMPLIATA_R = "nodi iniziali + nodi nuovi"
_CORPUS_A = ("addestramento originario ESTESO, con la storia anteriore a t0 "
             "dei nodi privilegiati")
_CORPUS_R = ("addestramento originario + esempi ammissibili delle prime 24 ore "
             "dei nodi nuovi, SENZA storia anteriore a t0")

TABELLA = {b.nome: b for b in (
    _b("C", "nessuna"),
    _b("P", "descrittore", variante="BASE-CORRECTED", attesa=True),
    _b("E", "embedding", preparatorio=True, prefisso=True),
    _b("E1", "embedding_token", preparatorio=True, prefisso=True),
    _b("A", "embedding", popolazione="ampliata", corpus="privilegiato",
       pop_descr=_AMPLIATA_A, corpus_descr=_CORPUS_A),
    _b("R", "embedding", popolazione="ampliata", corpus="post_installazione",
       campionamento="uniforme_nodo", costo_inserimento=True, attesa=True,
       pop_descr=_AMPLIATA_R, corpus_descr=_CORPUS_R),
    # E3 — dichiarati qui, dalla pre-registrazione protocol/E3.md. Gli
    # esecutori del campionamento per origine e della selezione con i nodi
    # nuovi NON esistono ancora: `addestra_una` rifiuta i valori che non
    # conosce, con il nome, e non parte.
    _b("R-orig", "embedding", popolazione="ampliata",
       corpus="post_installazione", campionamento="uniforme_origine",
       costo_inserimento=True, attesa=True,
       pop_descr=_AMPLIATA_R, corpus_descr=_CORPUS_R),
    _b("R-mon", "embedding", popolazione="ampliata",
       corpus="post_installazione", campionamento="uniforme_origine",
       selezione="initial_network_piu_nuovi_6h",
       costo_inserimento=True, attesa=True,
       pop_descr=_AMPLIATA_R, corpus_descr=_CORPUS_R),
    _b("F", "adattato_da_E", canonico=False, addestra=False,
       popolazione="nessuna", corpus="acquisizione", campionamento="nessuno",
       selezione="nessuna", attesa=True,
       pop_descr="nodi iniziali (da E) + nodi nuovi registrati separatamente",
       corpus_descr="esempi ammissibili delle prime 24 ore dei soli nodi nuovi"),
)}


class BraccioIgnoto(ValueError):
    """Un braccio non dichiarato nella tabella."""


def proprieta(nome: str) -> Braccio:
    """Le proprieta' del braccio. **Solleva se non e' dichiarato**: un nome
    sbagliato deve fermarsi qui, non in un KeyError a meta' campagna."""
    try:
        return TABELLA[str(nome)]
    except KeyError:
        raise BraccioIgnoto(
            f"braccio «{nome}» non dichiarato in componente/bracci.py; "
            f"dichiarati: {list(TABELLA)}") from None


def bracci_con(**cond) -> tuple:
    """I nomi dei bracci le cui proprieta' valgono `cond`, nell'ordine della
    tabella. Es. `bracci_con(carica_canonico=True)`."""
    nomi_campi = {f.name for f in fields(Braccio)}
    ignoti = set(cond) - nomi_campi
    if ignoti:
        raise ValueError(f"proprieta' inesistenti: {sorted(ignoti)}")
    return tuple(b.nome for b in TABELLA.values()
                 if all(getattr(b, k) == v for k, v in cond.items()))


# le viste che i moduli usavano come costanti, ora DERIVATE
CARICANO = bracci_con(carica_canonico=True)
PREPARATORI = bracci_con(preparatorio=True)
SENZA_DESCRITTORE = bracci_con(usa_descrittore=False)
ADDESTRANO = bracci_con(addestra=True)


def tabella_markdown() -> str:
    """La tabella, per i documenti di congelamento."""
    col = ("nome", "fornitore", "usa_descrittore", "carica_canonico",
           "preparatorio", "addestra", "popolazione", "corpus", "campionamento",
           "selezione_ck", "costo_all_inserimento", "attende_acquisizione",
           "richiede_rho")
    r = ["| " + " | ".join(col) + " |", "|" + "---|" * len(col)]
    for b in TABELLA.values():
        r.append("| " + " | ".join(
            ("sì" if v is True else "no" if v is False else str(v))
            for v in (getattr(b, c) for c in col)) + " |")
    return "\n".join(r)


if __name__ == "__main__":
    print(tabella_markdown())
