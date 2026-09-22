#!/usr/bin/env python3
"""
Artefatto canonico dei moduli comuni.
======================================
Lo stato iniziale dei soli moduli condivisi fra i bracci — componente temporale,
ramo statico, fusione, teste, parametri e buffer iniziali della BatchNorm — con
configurazione, versione e impronta.

**NON E' UNA FUNZIONE DI COLLAUDO.** `addestramento.py` lo carica
OBBLIGATORIAMENTE per C, P, E, A e R, **prima della creazione
dell'ottimizzatore**, e un controllo bloccante verifica che i tensori comuni
coincidano.

    presenza di tutte le chiavi comuni previste
    uguaglianza ESATTA dei relativi tensori con l'artefatto
    assenza di modifiche accidentali al fornitore di identita'

**F E' L'ECCEZIONE FONDAMENTALE**: non carica l'artefatto iniziale, perche' parte
dal punto di controllo E **gia' addestrato**, di cui mantiene backbone, statiche e
teste. Caricarvi lo stato iniziale cancellerebbe l'addestramento.

LA CHIAVE comprende seme e configurazione dei moduli comuni. **Non si duplica per
partizione**: i moduli comuni non dipendono dalla partizione dei nodi.

I fornitori di identita' mantengono inizializzazioni PROPRIE, con regola esplicita,
generatore separato e stato iniziale salvato: l'artefatto canonico non li tocca.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import torch

VERSIONE_CANONICO = "1.0"
MODULI_COMUNI = ("start", "blocchi", "stat", "e1", "e2")
# i bracci che CARICANO l'artefatto iniziale; F ne e' escluso per costruzione
CARICANO = ("C", "P", "E", "A", "R")


class CanonicoViolato(RuntimeError):
    """I moduli comuni non coincidono con l'artefatto, o l'artefatto manca."""


def e_comune(chiave: str) -> bool:
    return chiave.split(".")[0] in MODULI_COMUNI


def impronta(sd) -> str:
    h = hashlib.sha256()
    for k, v in sorted(sd.items()):
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()[:16]


def chiave(seme: int, cfg: dict) -> str:
    """Seme e configurazione dei MODULI COMUNI, non della partizione."""
    parti = [f"seme{int(seme)}"]
    for k in ("c_in", "nascosti", "blocchi", "d_statiche", "d_statiche_uscita",
              "n_orizzonti", "n_classi"):
        if k in cfg:
            parti.append(f"{k}{cfg[k]}")
    return "canonico_" + "_".join(parti)


def estrai(modello) -> dict:
    """I soli tensori dei moduli comuni, parametri e buffer."""
    return {k: v.detach().clone()
            for k, v in modello.state_dict().items() if e_comune(k)}


def percorso(dir_can: Path, k: str) -> Path:
    return Path(dir_can) / f"{k}.pt"


def salva(modello, seme: int, cfg: dict, dir_can: Path) -> Path:
    sd = estrai(modello)
    k = chiave(seme, cfg)
    f = percorso(dir_can, k)
    f.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": sd, "chiave": k, "seme": int(seme),
                "configurazione": dict(cfg),
                "moduli_comuni": list(MODULI_COMUNI),
                "versione_canonico": VERSIONE_CANONICO,
                "impronta": impronta(sd), "n_tensori": len(sd),
                "istante": datetime.now(timezone.utc).isoformat()}, f)
    return f


def carica(seme: int, cfg: dict, dir_can: Path) -> dict:
    """L'artefatto. **Solleva se manca**: non si ricostruisce al volo."""
    k = chiave(seme, cfg)
    f = percorso(dir_can, k)
    if not f.exists():
        raise CanonicoViolato(
            f"artefatto canonico assente: {f}. Va PREPARATO prima "
            f"dell'addestramento: ricostruirlo qui consumerebbe numeri casuali "
            f"e cambierebbe l'inizializzazione dei fornitori.")
    return torch.load(f, map_location="cpu", weights_only=False)


def applica(modello, art: dict) -> dict:
    """Copia i moduli comuni nel modello. Restituisce il riepilogo.

    **Non tocca il fornitore di identita'**: le sue inizializzazioni sono
    proprie, e sovrascriverle renderebbe l'artefatto una fonte di identita'.
    """
    sd = modello.state_dict()
    att = art["state_dict"]
    mancanti = [k for k in att if k not in sd]
    forme = [k for k in att if k in sd and sd[k].shape != att[k].shape]
    if mancanti or forme:
        raise CanonicoViolato(
            f"il modello non accoglie l'artefatto: mancanti {mancanti[:4]}, "
            f"forme diverse {forme[:4]}")
    prima_id = {k: v.detach().clone() for k, v in sd.items()
                if not e_comune(k)}
    with torch.no_grad():
        for k, v in att.items():
            sd[k].copy_(v)
    # il fornitore NON deve essere cambiato
    dopo = modello.state_dict()
    tocchi = [k for k, v in prima_id.items()
              if k in dopo and not torch.equal(dopo[k], v)]
    if tocchi:
        raise CanonicoViolato(
            f"l'applicazione ha modificato il fornitore di identita': "
            f"{tocchi[:4]}")
    return {"applicati": len(att), "identita_intatta": True,
            "impronta_artefatto": art["impronta"]}


def verifica(modello, art: dict, etichetta: str = "") -> dict:
    """CONTROLLO BLOCCANTE, da eseguire prima di creare l'ottimizzatore.

    Verifica presenza delle chiavi comuni previste e uguaglianza ESATTA dei
    tensori.
    """
    sd = modello.state_dict()
    att = art["state_dict"]
    comuni_modello = {k for k in sd if e_comune(k)}
    mancanti = sorted(set(att) - comuni_modello)
    inattese = sorted(comuni_modello - set(att))
    diversi = [k for k in att
               if k in sd and not torch.equal(sd[k], att[k])]
    if mancanti or inattese or diversi:
        raise CanonicoViolato(
            f"moduli comuni non conformi{f' [{etichetta}]' if etichetta else ''}:"
            f"\n  chiavi mancanti nel modello: {mancanti[:6]}"
            f"\n  chiavi comuni non nell'artefatto: {inattese[:6]}"
            f"\n  tensori diversi: {diversi[:6]}"
            f"\n  l'artefatto ha {len(att)} tensori, il modello "
            f"{len(comuni_modello)} comuni")
    return {"conforme": True, "tensori": len(att),
            "impronta": art["impronta"], "chiave": art["chiave"]}


def stato_iniziale_completo(modello, seme: int, cfg: dict, braccio: str,
                            dir_stati: Path, extra: dict | None = None) -> Path:
    """Lo stato iniziale COMPLETO del modello risultante, da registrare."""
    sd = {k: v.detach().clone() for k, v in modello.state_dict().items()}
    # IL NOME DEVE IDENTIFICARE L'ESECUZIONE, non solo seme e configurazione:
    # per E, A, R la tabella degli embedding dipende dai nodi, quindi da citta'
    # e partizione. Col nome di prima, nove esecuzioni con lo stesso seme
    # scrivevano contenuti DIVERSI nello STESSO file, e il manifesto puntava a
    # un file che non conteneva piu' cio' che registrava.
    ex = extra or {}
    parti = [str(ex[k]) for k in ("contesto", "partizione", "inizializzazione")
             if k in ex]
    suff = ("_" + "_".join(parti)) if parti else ""
    f = Path(dir_stati) / f"iniziale_{braccio}{suff}_{chiave(seme, cfg)}.pt"
    if f.exists():
        # un TENTATIVO ripetuto della stessa esecuzione produce lo stesso stato:
        # si accetta. Un contenuto DIVERSO sotto lo stesso nome e' una
        # collisione, e si rifiuta.
        pre = torch.load(f, map_location="cpu", weights_only=False)
        if pre.get("impronta") != impronta(sd):
            raise CanonicoViolato(
                f"collisione su {f.name}: esiste con impronta "
                f"{pre.get('impronta')}, il nuovo stato ha {impronta(sd)}. "
                f"Sovrascriverlo renderebbe falsa l'impronta gia' registrata.")
        return f
    f.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": sd, "braccio": braccio, "seme": int(seme),
                "configurazione": dict(cfg),
                "impronta": impronta(sd),
                "impronta_comuni": impronta(
                    {k: v for k, v in sd.items() if e_comune(k)}),
                "versione_canonico": VERSIONE_CANONICO,
                "istante": datetime.now(timezone.utc).isoformat(),
                **(extra or {})}, f)
    return f


def prepara(costruttore, semi, cfg: dict, dir_can: Path,
            campagna: str = "") -> list:
    """Costruisce e salva l'artefatto per ciascun seme, UNA volta.

    `costruttore(seme)` restituisce un modello qualunque con i moduli comuni
    nella configurazione dichiarata: l'artefatto non dipende dal fornitore.
    """
    fuori = []
    for s in semi:
        m = costruttore(int(s))
        f = salva(m, int(s), cfg, dir_can)
        d = torch.load(f, map_location="cpu", weights_only=False)
        fuori.append({"seme": int(s), "chiave": d["chiave"],
                      "impronta": d["impronta"], "n_tensori": d["n_tensori"],
                      "file": f.name})
    # UN REGISTRO PER CAMPAGNA: scriverne uno solo sovrascriverebbe quello
    # precedente, e i suoi artefatti sparirebbero dalla documentazione pur
    # restando su disco. E' gia' accaduto con gli stati iniziali.
    nome = (f"registro_canonico_{campagna}.json" if campagna
            else "registro_canonico.json")
    (Path(dir_can) / nome).write_text(json.dumps(
        {"versione_canonico": VERSIONE_CANONICO, "campagna": campagna,
         "moduli_comuni": list(MODULI_COMUNI),
         "bracci_che_caricano": list(CARICANO),
         "eccezione": ("F NON carica l'artefatto iniziale: parte dal punto di "
                       "controllo E gia' addestrato, di cui mantiene backbone, "
                       "statiche e teste"),
         "configurazione": dict(cfg), "artefatti": fuori,
         "istante": datetime.now(timezone.utc).isoformat()},
        indent=2, ensure_ascii=False))
    return fuori
