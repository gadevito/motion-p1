#!/usr/bin/env python3
"""
Fase 3 — la campagna di prova, cinque bracci, attraverso gli STESSI esecutori.
==============================================================================
    C  nessuna identita'                     addestra, popolazione iniziale
    P  descrittore BASE-CORRECTED da 24 ore  addestra, popolazione iniziale
    A  riferimento PRIVILEGIATO              addestra, popolazione ampliata
    R  riaddestramento post-installazione    addestra, ampliata, campionamento
                                             uniforme per NODO
    F  adatta il solo embedding nuovo        parte dal punto E, non addestra

**Nessun percorso semplificato**: C, P, A ed R passano da `addestra_una`, F da
`adattamento.py`, la valutazione da `valutazione.valuta`. La regola della
griglia temporale e la convenzione (t0, t1] valgono per tutti.

PERIMETRO DI VALUTAZIONE, approvato: **tutte le origini ammissibili successive
all'acquisizione**, con bersagli entro il periodo di prova. Si riportano anche
la prima giornata e le fasce di tempo trascorso dall'installazione, fissate
qui, prima dell'analisi.

COSTI. Due misure distinte, come prescritto:

    concorrente  la campagna, con parallelismo registrato -> PRESTAZIONI
    isolata      un processo alla volta, macchina libera  -> COSTI

Il campione isolato e' prefissato: tre citta', partizione 1000, semi 201, 202,
203, tutti i bracci. Le sue esecuzioni sono le stesse della campagna,
programmate in una finestra senza altri carichi.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_inserimento.py --piano
    poetry run python evoluzione/esperimenti/esegui_inserimento.py --isolato
    poetry run python evoluzione/esperimenti/esegui_inserimento.py --lavoratori 8
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

BRACCI = ("C", "P", "A", "R", "F")
ADDESTRANO = ("C", "P", "A", "R")
ETICHETTA = "inserimento_griglia"
CALENDARIO = {"Madrid": (8887, 8983), "Londra": (8966, 9062),
              "Melbourne": (8806, 8902)}
# le fasce di tempo dall'installazione, in passi da 15 minuti: FISSATE ORA
FASCE = ((0, 96, "prima giornata"), (96, 672, "fino a una settimana"),
         (672, 10 ** 9, "oltre una settimana"))
ISOLATO = {"partizione": 0, "semi": (201, 202, 203)}


class Esec:
    def __init__(self, c, p, variante=None):
        self.contesto, self.partizione = c, p
        self.inizializzazione, self.variante = 0, variante


def marcatore(f: Path) -> Path:
    return f.with_name(f.name + ".fatto")


def scrivi_atomico(f: Path, testo: str):
    import os
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".tmp")
    with open(tmp, "w") as h:
        h.write(testo); h.flush(); os.fsync(h.fileno())
    os.replace(tmp, f)


def piano(contesti, dich, torchsemi, partizioni):
    """I cinque bracci della stessa combinazione ADIACENTI, ordine ruotato."""
    fuori = []
    for i, (s, st) in enumerate(zip(dich, torchsemi)):
        for j, p in enumerate(partizioni):
            r = (i * len(partizioni) + j) % len(contesti)
            for c in contesti[r:] + contesti[:r]:
                k = (i * len(partizioni) + j) % len(BRACCI)
                for b in BRACCI[k:] + BRACCI[:k]:
                    fuori.append({"contesto": c, "partizione": p,
                                  "seme": int(s), "seme_torch": int(st),
                                  "braccio": b})
    return fuori


# LE VENTIQUATTRO ORE DI ACQUISIZIONE, in secondi: sono attesa di DATI, non
# calcolo, e vanno nel tempo di disponibilita' di chi le richiede.
ACQUISIZIONE_S = 24 * 3600


def costo_addestramento(b: str, dt: float) -> dict:
    """Dove va il tempo di addestramento, secondo QUANDO avviene.

        C, P  il modello si addestra PRIMA dell'installazione: costo iniziale
        A     idem, ma con informazione non disponibile in esercizio
        R     **riaddestra DOPO l'installazione**: e' costo di INSERIMENTO

    Attribuire a R un inserimento a costo zero rovescerebbe il confronto.
    """
    if b == "R":
        return {"addestramento_s": 0.0, "inserimento_s": dt}
    return {"addestramento_s": dt, "inserimento_s": 0.0}


def tempo_disponibilita(b: str, costo: dict) -> dict:
    """Quando la configurazione e' pronta, dall'installazione: **attesa dei
    dati** e **calcolo**, distinti."""
    attesa = ACQUISIZIONE_S if b in ("P", "F", "R") else 0.0
    calcolo = costo.get("inserimento_s", 0.0)
    return {"attesa_dati_s": attesa, "calcolo_inserimento_s": calcolo,
            "disponibilita_s": attesa + calcolo,
            "nota": ("A non e' disponibile in esercizio: e' il livello "
                     "raggiungibile avendo il nodo fin dall'inizio"
                     if b == "A" else "")}


def nel_campione_isolato(x) -> bool:
    return (x["partizione"] == ISOLATO["partizione"]
            and x["seme"] in ISOLATO["semi"])


def _lavora(args):
    """UNA esecuzione: addestra o adatta, poi valuta sulle chiavi di prova."""
    x, out, fili, modalita = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.corpus import (
        costruisci_corpus_iniziale, costruisci_corpus_post_installazione,
        costruisci_corpus_privilegiato, verifica_corpus)
    from evoluzione.componente.registro import Registro
    from evoluzione.esperimenti.addestramento import _carica, _partizioni
    from evoluzione.esperimenti.inserimento import (
        adatta_F, cfg_braccio, valuta_prova)
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    out = Path(out)
    c, p, s, b = x["contesto"], x["partizione"], x["seme"], x["braccio"]
    t0, t1 = CALENDARIO[c]
    f_out = out / ETICHETTA / f"{b}_{c}_p{p}_s{s}.json"
    t_avvio = time.time()
    reg = Registro.avvia(f"{ETICHETTA}/{b}",
                         note=f"{c} p{p} seme {s} braccio {b} [{modalita}]",
                         radice=out / "registro")
    try:
        D = _carica(c, out / "maschere")
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[p])})
        ok = GR.passi_regolari(D["ts"])
        o_acq = GR.origini_acquisizione(ok, t0, t1)
        # I CORPUS, con i loro controlli bloccanti
        if b in ("C", "P"):
            corp = costruisci_corpus_iniziale(nodi["addestramento"],
                                              ist["addestramento"])
        elif b == "A":
            corp = costruisci_corpus_privilegiato(
                nodi["addestramento"], nodi["prova"], ist["addestramento"],
                t0, ok=ok)
        elif b == "R":
            corp = costruisci_corpus_post_installazione(
                nodi["addestramento"], nodi["prova"], ist["addestramento"],
                t0, t1, ok=ok)
        else:
            corp = None
        if corp is not None:
            reg.artefatto("corpus", **verifica_corpus(corp, nodi["prova"], t0))
        cfg = cfg_braccio(b, c, p, s, out, nodi, o_acq)
        reg.configurazione({**cfg, **x, "modalita_misura": modalita,
                            "fili_torch": fili})
        if b in ADDESTRANO:
            from evoluzione.esperimenti.addestramento import addestra_una
            gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE[p]),
                   "inizializzazione": np.random.default_rng(s)}
            t_tr = time.time()
            pred = addestra_una(Esec(c, p, cfg.get("variante")), reg, cfg,
                                gen, out)
            # il punto di controllo e' quello dichiarato; il valore restituito
            # e' il file delle predizioni interne all'esecutore
            ck = out / cfg["etichetta"] / cfg["nome_ck"]
            reg.evento(f"predizioni interne in {Path(pred).name}")
            costo = costo_addestramento(b, time.time() - t_tr)
            mod = None
        else:
            mod, costo = adatta_F(c, p, x["seme_torch"], out, D, nodi, ist,
                                  o_acq, reg)
            ck = None
        r = valuta_prova(b, c, p, s, out, D, nodi, ist, t1, ok, reg, ck, mod,
                         FASCE)
        costo_tot = {**costo, **r["costo"]}
        # il descrittore di P si costruisce all'inserimento
        costo_tot["inserimento_s"] = (costo_tot.get("inserimento_s", 0.0)
                                      + costo_tot.get(
                                          "costruzione_descrittore_s", 0.0))
        man = {**x, "modalita_misura": modalita, "fili_torch": fili,
               "costo": costo_tot,
               "tempo_disponibilita": tempo_disponibilita(b, costo_tot), "valutazione": r["metriche"],
               "corpus": (corp["manifesto"] if corp is not None else None),
               "origini_acquisizione": len(o_acq),
               "istante": datetime.now(timezone.utc).isoformat()}
        scrivi_atomico(f_out, json.dumps(man, indent=2, ensure_ascii=False,
                                         default=str))
        scrivi_atomico(marcatore(f_out), json.dumps(
            {**x, "secondi": time.time() - t_avvio, "modalita": modalita}))
        reg.completa()
        return {**x, "esito": "completata", "secondi": time.time() - t_avvio}
    except Exception as e:                                   # noqa: BLE001
        reg.evento(f"{type(e).__name__}: {e}")
        reg.completa("fallita")
        return {**x, "esito": "fallita", "secondi": time.time() - t_avvio,
                "errore": f"{type(e).__name__}: {e}"[:300]}


def main() -> int:
    from evoluzione.esperimenti.fasi import (CONTESTI, PARTIZIONI,
                                             PrerequisitoMancante,
                                             verifica_prova)
    from evoluzione.esperimenti.semi import configurazione
    ap = argparse.ArgumentParser(description="fase 3: cinque bracci")
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--braccio", nargs="*", default=list(BRACCI))
    ap.add_argument("--isolato", action="store_true",
                    help="solo il campione prefissato, UN processo alla volta")
    ap.add_argument("--lavoratori", type=int, default=1)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    _, dich, semi_torch = configurazione(inserimento=True)
    dir_c = a.out / ETICHETTA
    P = [x for x in piano(list(a.contesto), dich, semi_torch, PARTIZIONI)
         if x["contesto"] in a.contesto and x["braccio"] in a.braccio]
    if a.isolato:
        P = [x for x in P if nel_campione_isolato(x)]
        if a.lavoratori != 1:
            print("  il campione isolato richiede UN processo: forzo 1")
            a.lavoratori = 1
    modalita = "isolata" if a.isolato else "concorrente"

    print("=" * 84)
    print(f"FASE 3 — {len(P)} esecuzioni, misura {modalita.upper()}")
    print("=" * 84)
    print(f"  bracci {list(a.braccio)} | {a.lavoratori} processi x {a.fili} filo")
    if a.isolato:
        print(f"  campione prefissato: partizione {ISOLATO['partizione']}, "
              f"semi {list(ISOLATO['semi'])}, tutte le citta'")
        print(f"  **nessun altro addestramento deve girare durante la misura**")

    try:
        r = verifica_prova(a.out / "E_inserimento_griglia",
                           a.out / "selezione_F_griglia", semi_torch,
                           a.contesto)
        print(f"\n  prerequisiti: {r['punti_di_controllo']} punti E, "
              f"configurazione di F congelata")
        for c, s in r["scelte_F"].items():
            print(f"     F su {c:11s} ({s['aggiornamenti']}, {s['passo']:g})")
    except PrerequisitoMancante as e:
        print(f"\n{e}")
        return 1

    fatte = [x for x in P if marcatore(
        dir_c / f"{x['braccio']}_{x['contesto']}_p{x['partizione']}"
                f"_s{x['seme']}.json").exists()]
    da_fare = [x for x in P if x not in fatte]
    print(f"\n  completate: {len(fatte)} | da eseguire: {len(da_fare)}")
    if a.piano:
        from collections import Counter
        print(f"  per braccio: {dict(Counter(x['braccio'] for x in da_fare))}")
        print(f"  nel campione isolato: "
              f"{sum(nel_campione_isolato(x) for x in P)} su {len(P)}")
        for x in da_fare[:5]:
            print(f"     {x['contesto']:11s} p{x['partizione']} s{x['seme']} "
                  f"{x['braccio']}")
        return 0

    dir_c.mkdir(parents=True, exist_ok=True)
    ctx = mp.get_context("spawn")
    esiti, t_in = [], time.time()
    lavori = [(x, str(a.out), a.fili, modalita) for x in da_fare]
    with ctx.Pool(a.lavoratori) as pool:
        for i, res in enumerate(pool.imap_unordered(_lavora, lavori), 1):
            esiti.append(res)
            tr = time.time() - t_in
            print(f"  [{i:3d}/{len(lavori)}] {res['contesto']:11s} "
                  f"p{res['partizione']} s{res['seme']} {res['braccio']}  "
                  f"{res['esito']:10s} {res['secondi']/60:5.1f} min | "
                  f"{tr/3600:4.1f} h, restano ~{tr/i*(len(lavori)-i)/3600:4.1f} h"
                  + (f"\n        {res['errore']}"
                     if res["esito"] == "fallita" else ""), flush=True)
    falliti = [r for r in esiti if r["esito"] == "fallita"]
    scrivi_atomico(dir_c / f"esito_{modalita}.json", json.dumps(
        {"modalita": modalita, "lavoratori": a.lavoratori, "fili": a.fili,
         "completate": len(esiti) - len(falliti), "fallite": falliti,
         "ore_calendario": (time.time() - t_in) / 3600,
         "somma_tempi_parete_ore": sum(r["secondi"] for r in esiti) / 3600,
         "istante": datetime.now(timezone.utc).isoformat()}, indent=2))
    print(f"\n  {len(esiti) - len(falliti)} completate, {len(falliti)} fallite")
    return 0 if not falliti else 1


if __name__ == "__main__":
    raise SystemExit(main())
