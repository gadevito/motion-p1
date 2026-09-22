#!/usr/bin/env python3
"""
Prerequisiti delle tre fasi, verificati all'AVVIO e bloccanti.
===============================================================
Le dipendenze diventano esplicite nei comandi anziche' in una macchina a stati,
ma **ciascuna fase verifica i propri prerequisiti**: senza, il sequenziamento
resterebbe a carico di chi lancia.

    E            artefatti canonici, dati, calendario
    selezione F  punti di controllo E attesi, completi e leggibili
    prova        punti di controllo E e configurazione F selezionata e congelata

**Se mancano, la fase si interrompe con un messaggio esplicito**, non produce
risultati parziali.

Il costo si misura dalla PRIMA fase e si riporta separatamente per addestramenti
completi e adattamenti: la stima complessiva va confermata dai tempi osservati,
non assunta.
"""
from __future__ import annotations

import json
from pathlib import Path

CONTESTI = ("Madrid", "Londra", "Melbourne")
PARTIZIONI = (0, 1, 2)
BRACCI = ("C", "P", "E", "A", "R", "F")
# le popolazioni e i corpus, dichiarati: A ed R condividono l'esecutore
POPOLAZIONE = {
    "C": "nodi iniziali",
    "P": "nodi iniziali",
    "E": "nodi iniziali",
    "A": "nodi iniziali + nodi che simulano le nuove installazioni",
    "R": "nodi iniziali + nodi nuovi",
    "F": "nodi iniziali (da E) + nodi nuovi registrati separatamente",
}
CORPUS = {
    "C": "addestramento originario",
    "P": "addestramento originario",
    "E": "addestramento originario",
    "A": "addestramento originario ESTESO, con la storia anteriore a t0 dei "
         "nodi privilegiati",
    "R": "addestramento originario + esempi ammissibili delle prime 24 ore "
         "dei nodi nuovi, SENZA storia anteriore a t0",
    "F": "esempi ammissibili delle prime 24 ore dei soli nodi nuovi",
}


class PrerequisitoMancante(RuntimeError):
    """Una fase e' stata avviata senza i suoi prerequisiti."""


def _elenco(mancanti, quanti=6):
    x = sorted(mancanti)
    return f"{x[:quanti]}{'…' if len(x) > quanti else ''} ({len(x)} in tutto)"


def chiave_E(contesto, partizione, seme) -> str:
    return f"E_{contesto}_p{partizione}_s{seme}"


def percorso_E(dir_E: Path, contesto, partizione, seme) -> Path:
    return Path(dir_E) / f"ck_{chiave_E(contesto, partizione, seme)}.pt"


def verifica_E(dir_canonico: Path, dir_maschere: Path, dir_pesi: Path,
               semi, contesti=CONTESTI, campagna: str = "inserimento") -> dict:
    """Prerequisiti della fase E: canonico, maschere, pesi.

    **Il registro canonico e' uno per campagna** (`registro_canonico_<campagna>
    .json`): quello unico veniva sovrascritto da ogni preparazione.
    """
    guai = []
    reg = Path(dir_canonico) / f"registro_canonico_{campagna}.json"
    if not reg.exists():
        guai.append(f"registro canonico assente: {reg}. Eseguire prima "
                    f"`prepara_canonico.py`.")
    else:
        d = json.loads(reg.read_text())
        att = {int(x["seme"]) for x in d.get("artefatti", [])}
        manca = {int(s) for s in semi} - att
        if manca:
            guai.append(f"artefatti canonici mancanti per i semi "
                        f"{_elenco(manca)}")
        for x in d.get("artefatti", []):
            f = Path(dir_canonico) / x["file"]
            if not f.exists():
                guai.append(f"artefatto dichiarato ma assente: {f.name}")
    for c in contesti:
        if not (Path(dir_maschere) / f"maschere_{c}.npz").exists():
            guai.append(f"maschere assenti per {c}")
        for p in PARTIZIONI:
            if not (Path(dir_pesi) / f"pesi_{c}_p{p}.json").exists():
                guai.append(f"pesi assenti per {c} p{p}")
    if guai:
        raise PrerequisitoMancante(
            "fase E non avviabile:\n  " + "\n  ".join(guai[:10]))
    return {"fase": "E", "contesti": list(contesti), "semi": len(list(semi)),
            "conforme": True}


def verifica_selezione_F(dir_E: Path, semi, contesti=CONTESTI) -> dict:
    """Prerequisiti della selezione: i punti di controllo E attesi.

    **Completi e leggibili**, non soltanto presenti: un file troncato darebbe
    un errore a meta' della griglia.
    """
    import torch
    attesi, manca, rotti = [], [], []
    for c in contesti:
        for p in PARTIZIONI:
            for s in semi:
                f = percorso_E(dir_E, c, p, int(s))
                attesi.append(f)
                if not f.exists():
                    manca.append(f.name)
                    continue
                try:
                    d = torch.load(f, map_location="cpu", weights_only=False)
                    for k in ("state_dict", "nodi_iniziali"):
                        if k not in d:
                            rotti.append(f"{f.name}: manca «{k}»")
                except Exception as e:                      # noqa: BLE001
                    rotti.append(f"{f.name}: {type(e).__name__}")
    if manca or rotti:
        raise PrerequisitoMancante(
            f"selezione di F non avviabile:\n"
            f"  punti di controllo E attesi: {len(attesi)}\n"
            f"  mancanti: {_elenco(manca)}\n"
            f"  illeggibili o incompleti: {_elenco(rotti)}\n"
            f"  Eseguire prima `esegui_E.py`.")
    return {"fase": "selezione_F", "punti_di_controllo": len(attesi),
            "conforme": True}


def verifica_prova(dir_E: Path, dir_sel: Path, semi,
                   contesti=CONTESTI) -> dict:
    """Prerequisiti della prova: E, e la configurazione F CONGELATA."""
    r = verifica_selezione_F(dir_E, semi, contesti)
    f = Path(dir_sel) / "configurazione_F.json"
    if not f.exists():
        raise PrerequisitoMancante(
            f"prova non avviabile: configurazione F assente ({f}). Eseguire "
            f"prima `seleziona_F.py`, che la congela.")
    d = json.loads(f.read_text())
    if not d.get("congelata"):
        raise PrerequisitoMancante(
            f"la configurazione F esiste ma NON e' congelata: la prova non "
            f"parte su una scelta ancora modificabile.")
    manca = [c for c in contesti if c not in d.get("scelte", {})]
    if manca:
        raise PrerequisitoMancante(
            f"configurazione F mancante per {manca}: una per citta'.")
    return {**r, "fase": "prova", "scelte_F": d["scelte"], "conforme": True}


def descrivi_braccio(b: str) -> dict:
    """Popolazione e corpus dichiarati, da registrare nel manifesto."""
    if b not in BRACCI:
        raise ValueError(f"braccio ignoto: {b}")
    return {"braccio": b, "popolazione": POPOLAZIONE[b], "corpus": CORPUS[b],
            "carica_canonico": b != "F",
            "nota": ("F parte dal punto di controllo E gia' addestrato"
                     if b == "F" else
                     "carica l'artefatto canonico prima dell'ottimizzatore")}


def controlli_A_R(braccio: str, nodi_addestramento, nodi_nuovi,
                  istanti_addestramento, t0: int) -> dict:
    """I controlli bloccanti che distinguono A da R.

    **A** include la storia anteriore a t0 dei nodi privilegiati; **R** no.
    L'esecutore e' condiviso, il parametro e' esplicito.
    """
    na = {int(x) for x in nodi_addestramento}
    nn = {int(x) for x in nodi_nuovi}
    guai = []
    if braccio == "A":
        if not nn <= na:
            guai.append("A deve includere i nodi nuovi nella popolazione di "
                        "addestramento")
        if min(istanti_addestramento) >= t0:
            guai.append("A deve poter usare la storia anteriore a t0")
    elif braccio == "R":
        if not nn <= na:
            guai.append("R deve includere i nodi nuovi nella popolazione")
        anteriori = [int(x) for x in istanti_addestramento if int(x) < t0]
        if not anteriori:
            guai.append("R non ha istanti anteriori a t0 per i nodi iniziali: "
                        "il corpus originario manca")
    else:
        if nn & na:
            guai.append(f"{braccio} non deve avere nodi nuovi in "
                        f"addestramento: {sorted(nn & na)[:4]}")
    if guai:
        raise PrerequisitoMancante(
            f"popolazione o corpus non conformi per {braccio}:\n  "
            + "\n  ".join(guai))
    return {"braccio": braccio, "n_addestramento": len(na),
            "n_nuovi": len(nn), "conforme": True,
            **descrivi_braccio(braccio)}
