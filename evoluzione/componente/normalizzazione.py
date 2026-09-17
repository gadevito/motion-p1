#!/usr/bin/env python3
"""
Contratto di normalizzazione.
=============================
Una caratteristica che richiede normalizzazione ma non trova i propri parametri
**solleva un errore**, non salta la trasformazione.

PERCHE'. Nel confronto con le funzioni storiche le chiavi erano `media_f` mentre
lo schema le aveva rinominate in `media_conteggio`: con la chiave sbagliata la
standardizzazione non si applicava, e le statistiche uscivano GREZZE. Lo scarto
era di 155 su valori che dovrebbero stare attorno a uno — visibile solo perche' il
confronto era per componente. Un fallback silenzioso su una caratteristica sola
sarebbe passato inosservato.

QUALI CARATTERISTICHE RICHIEDONO NORMALIZZAZIONE.

  media_<canale>   si centra e si scala con i parametri di quel canale
  dev_<canale>     si scala soltanto, con la stessa scala
  banda_<b>        e' una media del canale `r`: usa i parametri di `r`

QUALI NE SONO ESENTI, e l'esenzione e' DICHIARATA, non dedotta:

  freq_classe_*    gia' in [0, 1]
  autocorr_1       gia' in [-1, 1]
  quota_*          gia' in [0, 1]
  ogni disponibilita'   gia' in [0, 1], e le maschere non si standardizzano

Un nome che non ricada in nessuna delle due categorie e' un errore: significa che
lo schema e' stato esteso senza dichiarare come trattare la nuova caratteristica.
"""
from __future__ import annotations

import math
import re

# esenzioni DICHIARATE: nessuna di queste si standardizza
ESENTI = (
    re.compile(r"^freq_classe_\d+$"),
    re.compile(r"^autocorr_\d+$"),
    re.compile(r"^quota_(incremento|decremento|validi)$"),
    re.compile(r"^(durata_nominale|durata_effettiva|n_valide|codice_durata)$"),
    re.compile(r"^copertura_"),
    re.compile(r"^disponibilita_"),
    re.compile(r"^maschera_"),
)
# richiedono normalizzazione, con la chiave che indicano
RICHIEDONO = (
    (re.compile(r"^media_(?P<c>.+)$"), lambda m: f"media_{m.group('c')}", True),
    (re.compile(r"^dev_(?P<c>.+)$"), lambda m: f"media_{m.group('c')}", False),
    (re.compile(r"^banda_\d+$"), lambda m: "media_r", True),
)


class ContrattoViolato(ValueError):
    """Sollevata quando la normalizzazione non e' applicabile come dichiarato."""


def chiave_e_centratura(nome: str):
    """(chiave, centra) per una caratteristica, o None se esente.

    Solleva se il nome non ricade in nessuna categoria: uno schema esteso senza
    dichiarare il trattamento della nuova caratteristica e' un difetto, non un
    caso da trattare per difetto.
    """
    for p in ESENTI:
        if p.match(nome):
            return None
    for p, chiave, centra in RICHIEDONO:
        m = p.match(nome)
        if m:
            return chiave(m), centra
    raise ContrattoViolato(
        f"caratteristica «{nome}» non classificata: va dichiarata fra quelle che "
        f"richiedono normalizzazione o fra quelle esenti")


# sotto questa scala la normalizzazione e' convenzionale, non stimata: va
# DICHIARATA. La convenzione storica somma 1e-6 alla deviazione, sicche' un
# canale costante produce esattamente questa soglia.
SCALA_MINIMA = 1e-5


def verifica_contratto(nomi_statistiche, nomi_disponibilita, norm: dict,
                       etichetta: str = "",
                       canali_costanti=frozenset()) -> dict:
    """Verifica la corrispondenza fra schema e normalizzazione. BLOCCANTE.

    `canali_costanti` elenca i canali DICHIARATI costanti per assenza dalla
    sorgente: per essi una scala minuscola e' la gestione convenzionale attesa —
    la convenzione storica somma 1e-6 alla deviazione — e viene registrata come
    tale anziche' rifiutata.

    Due situazioni che i numeri non distinguono e la dichiarazione si':

        scala accidentalmente nulla o invalida       -> ERRORE
        canale costante, esplicitamente dichiarato   -> ammesso e REGISTRATO

    Una scala pari a uno darebbe lo stesso risultato quando il valore centrato e'
    zero, ma non e' universalmente equivalente: la convenzione non si cambia.

    Restituisce il riepilogo, da registrare nel manifesto.
    """
    norm = norm or {}
    costanti = {str(c) for c in canali_costanti}
    richieste, esenti, mancanti, guaste, convenzionali = {}, [], [], [], {}
    for nome in list(nomi_statistiche) + list(nomi_disponibilita):
        esito = chiave_e_centratura(nome)
        if esito is None:
            esenti.append(nome)
            continue
        chiave, centra = esito
        richieste[nome] = {"chiave": chiave, "centra": centra}
        if chiave not in norm:
            mancanti.append((nome, chiave))
            continue
        v = norm[chiave]
        try:
            mu, sd = float(v[0]), float(v[1])
        except (TypeError, IndexError, ValueError):
            guaste.append((chiave, "non e' una coppia (media, scala)"))
            continue
        canale = chiave[len("media_"):] if chiave.startswith("media_") else chiave
        if not (math.isfinite(mu) and math.isfinite(sd)):
            guaste.append((chiave, f"non finita: ({mu}, {sd})"))
        elif sd <= 0:
            guaste.append((chiave, f"scala non positiva: {sd}"))
        elif sd < SCALA_MINIMA:
            if canale in costanti:
                convenzionali[chiave] = {
                    "scala": sd, "media": mu, "canale": canale,
                    "motivo": "canale dichiarato costante: assente dalla "
                              "sorgente. La componente risulta costante a zero."}
            else:
                guaste.append(
                    (chiave, f"scala {sd:g} sotto {SCALA_MINIMA:g} senza che "
                             f"«{canale}» sia dichiarato costante: se lo e', va "
                             f"elencato in `canali_costanti`; altrimenti la "
                             f"scala e' accidentale"))

    if mancanti or guaste:
        righe = [f"contratto di normalizzazione violato{f' [{etichetta}]' if etichetta else ''}:"]
        for nome, chiave in mancanti:
            righe.append(f"  «{nome}» richiede la chiave «{chiave}», assente")
        # una chiave serve a piu' caratteristiche — `media_x` a `media_x` e a
        # `dev_x` — sicche' il guasto va riportato UNA volta, con quante ne
        # dipendono
        visti = {}
        for chiave, perche in guaste:
            visti.setdefault((chiave, perche), 0)
            visti[(chiave, perche)] += 1
        for (chiave, perche), n in visti.items():
            quali = sorted(k for k, v in richieste.items()
                           if v["chiave"] == chiave)
            righe.append(f"  la chiave «{chiave}» {perche}")
            righe.append(f"     ne dipendono {len(quali)} caratteristiche: "
                         f"{', '.join(quali)}")
        righe.append(f"  chiavi fornite: {sorted(norm)}")
        righe.append("  una caratteristica che richiede normalizzazione e non "
                     "trova i propri parametri NON salta la trasformazione")
        raise ContrattoViolato("\n".join(righe))

    return {"normalizzate": richieste, "esenti": esenti,
            "chiavi_usate": sorted({v["chiave"] for v in richieste.values()}),
            "n_normalizzate": len(richieste), "n_esenti": len(esenti),
            "convenzionali": convenzionali,
            "n_costanti_dichiarate": len(convenzionali),
            # DUE CONTEGGI DIVERSI, che e' bene non confondere: uno riguarda le
            # sole caratteristiche normalizzate, l'altro l'intero schema.
            "normalizzate_variabili": len(richieste) - 2 * len(convenzionali),
            "nominali_totali": len(richieste) + len(esenti),
            "variabili_totali": (len(richieste) + len(esenti)
                                 - 2 * len(convenzionali)),
            "nota_dimensione": (
                "«nominali» comprende le componenti costanti, «variabili» no. Un "
                "canale dichiarato costante contribuisce due componenti — media e "
                "deviazione — entrambe nulle. Eliminarle cambierebbe "
                "parametrizzazione e inizializzazione del primo strato.")}


def applica(nome: str, x: float, norm: dict) -> float:
    """Standardizza una caratteristica secondo il contratto.

    Presuppone che `verifica_contratto` sia gia' passata: qui un'assenza e'
    comunque un errore, mai un valore restituito com'e'.
    """
    esito = chiave_e_centratura(nome)
    if esito is None:
        return x
    chiave, centra = esito
    if chiave not in norm:
        raise ContrattoViolato(
            f"«{nome}» richiede «{chiave}», assente al momento dell'uso")
    mu, sd = norm[chiave]
    return (x - mu) / sd if centra else x / sd
