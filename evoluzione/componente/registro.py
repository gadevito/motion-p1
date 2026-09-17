#!/usr/bin/env python3
"""
Registro delle esecuzioni.
==========================
Ogni esecuzione della campagna scrive un manifesto che ne descrive la provenienza
completa. Non modifica gli script originari: e' un modulo che gli esperimenti
importano.

DUE REQUISITI CHE DECIDONO LA PROGETTAZIONE.

  * La configurazione registrata deve essere quella EFFETTIVA, inclusi i valori
    predefiniti. La riga di comando non basta: due esecuzioni con comandi diversi
    possono avere configurazione identica, e due con lo stesso comando possono
    differire se il predefinito e' cambiato nel frattempo.

  * Le impronte sono degli ARTEFATTI CARICATI, non dei percorsi. Un percorso dice
    quale file era inteso; l'impronta del contenuto dice quale file c'era davvero.
    Per gli oggetti in memoria — matrici di descrittori, adiacenze — si impronta
    il contenuto, che e' l'unica prova di cosa il modello abbia visto.

LO STATO PREDEFINITO E' «INTERROTTO». Diventa «completato» solo per chiamata
esplicita, sicche' un'esecuzione che fallisca o venga interrotta resta identificata
come incompleta senza che occorra ricordarsene.

Uso negli esperimenti:

    from evoluzione.componente.registro import Registro

    reg = Registro.avvia("E1", note="inserimento a quattro orizzonti")
    reg.configurazione(vars(args))            # con i predefiniti risolti
    reg.semi(dati=0, inizializzazione=3)
    reg.artefatto("descrittore", percorso=p, oggetto=D,
                  schema="1.0", nomi=NOMI, politica_finestra="(t-L,t] n [t0,t]")
    reg.artefatto("grafo", percorso=g)
    reg.modello(net, n_nodi=K)                # inventario dei parametri per nodo
    reg.metrica(nome="wCE", pesi=w, aggregazione="media sui 4 orizzonti, poi sui semi")
    ...
    reg.uscita(percorso_csv)
    reg.completa()

Per i risultati storici:

    Registro.retrospettivo("Tabella 54", campi_noti={...}, campi_mancanti=[...])
"""
from __future__ import annotations

import atexit
import getpass
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path("results/evoluzione/registro")
VERSIONE_REGISTRO = "1.0"


# --------------------------------------------------------------- impronte ---
def impronta_file(p) -> str | None:
    """Impronta del contenuto di un file, a blocchi: i descrittori possono
    essere grandi e non vanno caricati in memoria per essere improntati."""
    p = Path(p)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blocco in iter(lambda: fh.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


def impronta_oggetto(x) -> str | None:
    """Impronta del CONTENUTO di un oggetto in memoria.

    E' l'unica prova di cosa il modello abbia effettivamente visto: un file puo'
    essere stato modificato dopo il caricamento, o il codice puo' averne
    trasformato il contenuto prima dell'uso.
    """
    if x is None:
        return None
    try:
        import numpy as np
        if isinstance(x, np.ndarray):
            a = np.ascontiguousarray(x)
            h = hashlib.sha256(a.tobytes())
            h.update(str((a.shape, a.dtype.str)).encode())
            return h.hexdigest()
    except ImportError:
        pass
    try:
        import torch
        if torch.is_tensor(x):
            return impronta_oggetto(x.detach().cpu().numpy())
    except ImportError:
        pass
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()


# ------------------------------------------------------------- ambiente -----
def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True,
                              timeout=10).stdout.strip() or None
    except Exception:
        return None


def ambiente() -> dict:
    pacchetti = {}
    for m in ("numpy", "torch", "pandas", "scipy", "networkx", "lightgbm"):
        try:
            pacchetti[m] = __import__(m).__version__
        except Exception:
            pass
    sporco = _git("status", "--porcelain")
    return {
        "code_commit": _git("rev-parse", "HEAD"),
        "working_tree_status": ("pulito" if sporco == "" else
                                f"SPORCO: {len(sporco.splitlines())} file modificati"
                                if sporco else "repository assente"),
        "code_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "python": sys.version.split()[0],
        "piattaforma": platform.platform(),
        "pacchetti": pacchetti,
        "utente": getpass.getuser(),
        "riga_di_comando": " ".join(sys.argv),
    }


# -------------------------------------------------------------- registro ----
class Registro:
    """Un manifesto per esecuzione, scritto su disco a ogni aggiornamento."""

    def __init__(self, d: dict, percorso: Path):
        self._d = d
        self._p = percorso
        self._t0 = time.time()
        self._scrivi()
        atexit.register(self._alla_uscita)

    # -- creazione ----------------------------------------------------------
    @classmethod
    def avvia(cls, esperimento: str, note: str = "", radice: Path = RADICE):
        rid = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}"
        radice = Path(radice)
        radice.mkdir(parents=True, exist_ok=True)
        d = {
            "versione_registro": VERSIONE_REGISTRO,
            "run_id": rid,
            "esperimento": esperimento,
            "note": note,
            "timestamp_avvio": datetime.now(timezone.utc).isoformat(),
            "run_status": "interrotto",     # diventa «completato» solo esplicitamente
            "ambiente": ambiente(),
            "resolved_configuration": None,
            "random_seeds": {},
            "dati": {},
            "descrittore": {},
            "modello": {},
            "grafo": {},
            "metrica": {},
            "uscite": [],
            "eventi": [],
        }
        return cls(d, radice / f"{rid}.json")

    @classmethod
    def retrospettivo(cls, etichetta: str, campi_noti: dict,
                      campi_mancanti: list, radice: Path = RADICE):
        """Manifesto per un risultato STORICO.

        Marcato come ricostruzione: i campi che non sono stati accertati restano
        esplicitamente mancanti e NON si compilano assumendo che il codice
        corrente coincida con quello che ha prodotto il risultato.
        """
        # nome di file conservativo: le etichette contengono trattini lunghi,
        # apostrofi e barre, che rendono i percorsi scomodi da manipolare
        import re as _re
        _slug = _re.sub(r"[^a-z0-9]+", "_",
                        etichetta.lower().replace("'", "")).strip("_")[:60]
        rid = f"retro-{_slug}"
        radice = Path(radice)
        radice.mkdir(parents=True, exist_ok=True)
        d = {
            "versione_registro": VERSIONE_REGISTRO,
            "run_id": rid,
            "tipo": "ricostruzione retrospettiva",
            "avvertenza": ("I campi elencati in campi_mancanti non sono stati "
                           "accertati. Non sono stati compilati assumendo che il "
                           "codice corrente coincida con quello originario."),
            "etichetta": etichetta,
            "timestamp_ricostruzione": datetime.now(timezone.utc).isoformat(),
            "run_status": "ricostruito",
            "campi_noti": campi_noti,
            "campi_mancanti": campi_mancanti,
        }
        p = radice / f"{rid}.json"
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False, default=str))
        return p

    # -- registrazione ------------------------------------------------------
    def configurazione(self, cfg: dict):
        """La configurazione EFFETTIVA, con i predefiniti gia' risolti.

        Passare `vars(args)` dopo `parse_args()`: contiene anche le opzioni non
        indicate sulla riga di comando, con il valore che hanno assunto.
        """
        self._d["resolved_configuration"] = {k: _serializzabile(v)
                                             for k, v in sorted(cfg.items())}
        self._scrivi()
        return self

    def semi(self, **kw):
        """I semi, distinti per ruolo: partizione dei nodi e inizializzazione
        hanno semi separati, e confonderli sottostima la dispersione."""
        self._d["random_seeds"].update(kw)
        self._scrivi()
        return self

    def dati(self, manifesto=None, partizione_nodi=None, partizione_temporale=None,
             preprocessing=None, normalizzazione=None):
        self._d["dati"] = {
            "dataset_manifest_hash": (impronta_file(manifesto)
                                      if isinstance(manifesto, (str, Path))
                                      else impronta_oggetto(manifesto)),
            "dataset_manifest_path": str(manifesto) if manifesto is not None else None,
            "node_split_hash": impronta_oggetto(partizione_nodi),
            "temporal_split": _serializzabile(partizione_temporale),
            "preprocessing_configuration": _serializzabile(preprocessing),
            "normalization_artifact_hash": impronta_oggetto(normalizzazione),
        }
        self._scrivi()
        return self

    def artefatto(self, tipo: str, percorso=None, oggetto=None, **extra):
        """Registra un artefatto con l'impronta del CONTENUTO caricato.

        Per il descrittore, `nomi` e' l'elenco ORDINATO delle caratteristiche: un
        cambiamento nell'ordine deve essere rilevabile, e lo e' perche' l'elenco
        e' improntato come sequenza, non come insieme.
        """
        v = {
            "percorso": str(percorso) if percorso is not None else None,
            "impronta_file": impronta_file(percorso) if percorso else None,
            "impronta_contenuto_caricato": impronta_oggetto(oggetto),
            "forma": list(getattr(oggetto, "shape", []) or []) or None,
        }
        for k, x in extra.items():
            v[k] = _serializzabile(x)
        if "nomi" in extra:
            v["impronta_ordine_caratteristiche"] = hashlib.sha256(
                "\u0000".join(map(str, extra["nomi"])).encode()).hexdigest()
            v["n_caratteristiche"] = len(extra["nomi"])
        self._d.setdefault(tipo, {}).update(v)
        self._scrivi()
        return self

    def modello(self, rete=None, n_nodi: int | None = None, **extra):
        """Configurazione del modello e INVENTARIO dei parametri per nodo.

        Un parametro il cui primo asse ha lunghezza pari al numero di nodi e'
        specifico per sensore: dopo un'espansione dovrebbe cambiare forma, e un
        modello che si dichiara a pesi congelati non deve averne.
        """
        inv = []
        if rete is not None:
            try:
                for nome, p in rete.named_parameters():
                    f = tuple(p.shape)
                    if n_nodi and f and f[0] == n_nodi:
                        inv.append({"nome": nome, "forma": list(f),
                                    "numel": int(p.numel())})
            except Exception as e:
                inv = [{"errore": f"inventario non eseguibile: {e}"}]
        tot = None
        try:
            tot = int(sum(p.numel() for p in rete.parameters()))
        except Exception:
            pass
        self._d["modello"] = {
            "model_configuration": _serializzabile(extra) or None,
            "parametri_totali": tot,
            "node_specific_parameters_inventory": inv,
            "n_parametri_per_nodo": sum(x.get("numel", 0) for x in inv),
            "impronta_stato": _impronta_stato(rete),
        }
        self._scrivi()
        return self

    def metrica(self, nome: str, pesi=None, aggregazione: str = "", **extra):
        self._d["metrica"] = {
            "metric_configuration": {"nome": nome, **_serializzabile(extra)},
            "impronta_pesi": impronta_oggetto(pesi),
            "pesi": _serializzabile(pesi),
            "aggregation_definition": aggregazione,
        }
        self._scrivi()
        return self

    def uscita(self, percorso):
        """Registra un file prodotto, con la sua impronta: e' cio' che lega senza
        ambiguita' ciascun risultato alla propria esecuzione."""
        self._d["uscite"].append({
            "percorso": str(percorso),
            "impronta": impronta_file(percorso),
            "istante": datetime.now(timezone.utc).isoformat(),
        })
        self._scrivi()
        return self

    def evento(self, testo: str):
        self._d["eventi"].append({
            "istante": datetime.now(timezone.utc).isoformat(), "testo": testo})
        self._scrivi()
        return self

    def completa(self, stato: str = "completato"):
        self._d["run_status"] = stato
        self._d["timestamp_fine"] = datetime.now(timezone.utc).isoformat()
        self._d["durata_secondi"] = round(time.time() - self._t0, 1)
        self._scrivi()
        return self

    # -- interno ------------------------------------------------------------
    def _scrivi(self):
        tmp = self._p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._d, indent=2, ensure_ascii=False,
                                  default=str))
        os.replace(tmp, self._p)      # scrittura atomica: niente file a meta'

    def _alla_uscita(self):
        if self._d.get("run_status") == "interrotto":
            self._d["timestamp_fine"] = datetime.now(timezone.utc).isoformat()
            self._d["durata_secondi"] = round(time.time() - self._t0, 1)
            self._d["eventi"].append({
                "istante": self._d["timestamp_fine"],
                "testo": "processo terminato senza chiamata a completa(): "
                         "l'esecuzione resta marcata come interrotta"})
            self._scrivi()

    @property
    def percorso(self):
        return self._p

    @property
    def run_id(self):
        return self._d["run_id"]


# --------------------------------------------------------------- ausiliari --
def _serializzabile(x):
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, dict):
        return {str(k): _serializzabile(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_serializzabile(v) for v in x]
    try:
        import numpy as np
        if isinstance(x, np.ndarray):
            return x.tolist() if x.size <= 64 else {"forma": list(x.shape),
                                                    "dtype": x.dtype.str}
        if isinstance(x, np.generic):
            return x.item()
    except ImportError:
        pass
    return str(x)


def _impronta_stato(rete):
    """Impronta dello stato completo: pesi, buffer e statistiche di
    normalizzazione. Serve all'audit D, che richiede che l'inserimento non
    modifichi nulla di tutto cio'."""
    if rete is None:
        return None
    try:
        h = hashlib.sha256()
        for k, v in sorted(rete.state_dict().items()):
            h.update(k.encode())
            h.update(v.detach().cpu().numpy().tobytes())
        return h.hexdigest()
    except Exception:
        return None
