#!/usr/bin/env python3
"""
Risoluzione del riferimento di velocita', con provenienza e stato espliciti.
============================================================================
Separa la gestione del riferimento dall'aggiornamento della rappresentazione,
come il revisore senior richiede: `update_representation` riceve il riferimento
gia' risolto e non lo stima.

CHE COSA FA, E CHE COSA NON FA.

  * valida FINITEZZA e POSITIVITA';
  * verifica l'UNICITA' dei valori validi per il sensore;
  * **non media** valori conflittuali: restituisce uno stato di conflitto e
    lascia la decisione a chi chiama. La mediana nasconde il conflitto anziche'
    risolverlo, ed e' cio' che la pipeline originaria faceva;
  * restituisce sorgente, versione e stato, sempre;
  * conserva «disponibilita' all'inserimento non verificata» come informazione
    esplicita, e **non assegna retrospettivamente una data di disponibilita' che
    non conosciamo**.

DUE POLITICHE, da non mescolare.

  `esterno_fisso`      il riferimento viene dall'anagrafica della sorgente ed e'
                       costante per l'intera valutazione, indipendente da L. E'
                       la politica della campagna principale.
  `locale_online_p85`  il riferimento e' stimato sulla finestra osservata del
                       nodo. E' una VARIANTE separata: il bersaglio di
                       valutazione resta comunque quello costruito con il
                       riferimento fisso, e la stima locale modifica soltanto gli
                       ingressi.

LO STATO NON E' UN VALORE MANCANTE. Un sensore senza riferimento valido non ha
riferimento zero: ha stato `mancante`, e chi lo riceve deve decidere se escluderlo
dalla valutazione sul bersaglio scelto.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

POLITICHE = ("esterno_fisso", "locale_online_p85")
STATI = ("valido", "mancante", "non_positivo", "non_finito", "conflitto",
         "sensore_sconosciuto", "politica_non_implementata")


@dataclass
class Riferimento:
    """L'esito della risoluzione. Tutti i campi sono sempre presenti."""
    reference_value: float | None
    reference_source: str
    reference_version: str | None
    status: str
    valid_count: int
    distinct_values: list = field(default_factory=list)
    available_at: str | None = None            # mai dedotto: solo se documentato
    availability_verified: bool = False
    estimation_window: tuple | None = None     # solo per la politica online
    note: str = ""

    def as_dict(self):
        return asdict(self)

    @property
    def utilizzabile(self):
        return self.status == "valido" and self.reference_value is not None


class AnagraficaRiferimenti:
    """I riferimenti per sensore, con la versione dell'artefatto da cui vengono.

    Costruita dai valori VALIDI distinti osservati per ciascun sensore: se ne
    esiste piu' di uno la risoluzione restituisce conflitto, non la mediana.
    """

    def __init__(self, per_sensore: dict, versione: str, sorgente: str):
        self._v = {str(k): sorted(set(float(x) for x in v))
                   for k, v in per_sensore.items()}
        self.versione = versione
        self.sorgente = sorgente

    # -- costruzione --------------------------------------------------------
    @classmethod
    def da_artefatto(cls, percorso, campo="ff_emp", campo_id="sensor_ids"):
        """Dall'artefatto dei bersagli, dove il vettore usato e' conservato.

        La versione e' l'impronta del solo vettore, non del file: due artefatti
        con metadati diversi e riferimenti identici hanno la stessa versione.
        """
        p = Path(percorso)
        z = np.load(p, allow_pickle=True)
        if campo not in z.files:
            raise KeyError(f"{p.name}: campo `{campo}` assente "
                           f"(presenti: {[k for k in z.files][:8]})")
        v = np.asarray(z[campo], dtype="float64")
        sid = (z[campo_id].astype(str) if campo_id in z.files
               else np.array([str(i) for i in range(len(v))]))
        h = hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest()[:16]
        # dall'artefatto ogni sensore ha un solo valore: il conflitto, se
        # c'era, e' gia' stato risolto a monte e non e' piu' osservabile qui
        per = {}
        for s, x in zip(sid, v):
            per[s] = [x] if np.isfinite(x) else []
        return cls(per, f"artefatto:{h}", f"{p.parent.name}/{p.name}:{campo}")

    @classmethod
    def da_valori(cls, per_sensore: dict, versione: str, sorgente: str):
        """Dai valori distinti osservati nella sorgente, dove il conflitto e'
        ancora visibile."""
        return cls(per_sensore, versione, sorgente)

    # -- risoluzione --------------------------------------------------------
    def risolvi(self, sensor_id, as_of_time=None,
                reference_policy="esterno_fisso") -> Riferimento:
        s = str(sensor_id)
        comune = dict(reference_source=self.sorgente,
                      reference_version=self.versione,
                      available_at=None, availability_verified=False)

        if reference_policy not in POLITICHE:
            return Riferimento(None, "sconosciuta", None,
                               "politica_non_implementata", 0,
                               note=f"politiche ammesse: {POLITICHE}")
        if reference_policy == "locale_online_p85":
            return Riferimento(
                None, "stima locale", None, "politica_non_implementata", 0,
                note=("variante separata: il riferimento si stima sulla finestra "
                      "osservata e il bersaglio resta quello fisso. Non "
                      "implementata in questo modulo."),
                **{k: v for k, v in comune.items()
                   if k in ("available_at", "availability_verified")})

        if s not in self._v:
            return Riferimento(None, self.sorgente, self.versione,
                               "sensore_sconosciuto", 0, **{
                                   k: v for k, v in comune.items()
                                   if k not in ("reference_source",
                                                "reference_version")})

        val = self._v[s]
        fin = [x for x in val if np.isfinite(x)]
        pos = [x for x in fin if x > 0]

        if not val:
            st, v = "mancante", None
        elif not fin:
            st, v = "non_finito", None
        elif not pos:
            st, v = "non_positivo", None
        elif len(pos) > 1:
            st, v = "conflitto", None
        else:
            st, v = "valido", pos[0]

        return Riferimento(
            reference_value=v, status=st, valid_count=len(pos),
            distinct_values=val,
            note=("piu' valori validi distinti: la risoluzione non li media, "
                  "la decisione spetta a chi chiama"
                  if st == "conflitto" else
                  "disponibilita' all'inserimento non verificata"
                  if st == "valido" else ""),
            **comune)

    def __len__(self):
        return len(self._v)


# ---------------------------------------------------------------------------
def resolve_reference(anagrafica: AnagraficaRiferimenti, sensor_id,
                      as_of_time=None, reference_policy="esterno_fisso") -> dict:
    """L'interfaccia nella forma richiesta, come dizionario."""
    return anagrafica.risolvi(sensor_id, as_of_time, reference_policy).as_dict()


def riepilogo(anagrafica: AnagraficaRiferimenti, sensori=None) -> dict:
    """Conteggio degli stati sull'intera anagrafica o su un sottoinsieme."""
    da = sensori if sensori is not None else list(anagrafica._v)
    c = {}
    for s in da:
        st = anagrafica.risolvi(s).status
        c[st] = c.get(st, 0) + 1
    return dict(sorted(c.items(), key=lambda x: -x[1]))
