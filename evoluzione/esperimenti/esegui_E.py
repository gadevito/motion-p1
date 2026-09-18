#!/usr/bin/env python3
"""
Fase 1 — addestramento dei punti di controllo E, preparatori.
==============================================================
3 citta' x 3 partizioni x 12 semi = **108 addestramenti**, con embedding liberi a
otto dimensioni **sui soli nodi iniziali**.

**E non e' un braccio di valutazione**: e' il punto di partenza di F, e la
famiglia architetturale di R.

I PREREQUISITI SI VERIFICANO ALL'AVVIO e sono bloccanti: artefatti canonici,
maschere, pesi. **Senza, la fase si interrompe** anziche' produrre risultati
parziali.

IL COSTO SI MISURA DA QUI. I tempi osservati vanno riportati separatamente per
addestramenti completi e adattamenti, e servono a confermare la stima delle fasi
successive — che **non si assume**.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_E.py --piano
    poetry run python evoluzione/esperimenti/esegui_E.py
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.fasi import (  # noqa: E402
    CONTESTI, PARTIZIONI, chiave_E, descrivi_braccio, percorso_E,
    PrerequisitoMancante, verifica_E)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

BRACCIO = "E"


def piano(contesti, semi, semi_torch):
    """L'ordine, salvato prima del lancio e non modificabile dopo.

    Contesti intercalati e partizioni ruotate, come nella campagna approvata:
    una lunga interruzione non si concentra su una sola citta'.
    """
    fuori = []
    for i, (s, st) in enumerate(zip(semi, semi_torch)):
        for j, p in enumerate(PARTIZIONI):
            r = (i * len(PARTIZIONI) + j) % len(contesti)
            for c in contesti[r:] + contesti[:r]:
                    fuori.append({"contesto": c, "partizione": p,
                              "seme": int(s), "seme_torch": int(st),
                              "braccio": BRACCIO})
    return fuori


def main() -> int:
    ap = argparse.ArgumentParser(description="fase 1: punti di controllo E")
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--riparti", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--epoche", type=int, default=35)
    ap.add_argument("--lotto", type=int, default=32)
    ap.add_argument("--passo", type=float, default=1e-3)
    ap.add_argument("--pazienza", type=int, default=8)
    a = ap.parse_args()

    # I SEMI DICHIARATI, non quelli gia' derivati. `addestra_una` deriva il
    # seme di torch da questo generatore, esattamente come `esegui_raccordo.py`:
    # seminare col derivato lo deriverebbe DUE volte, e la chiave dell'artefatto
    # canonico non corrisponderebbe. E' gia' accaduto.
    _, dich, semi_torch = configurazione(inserimento=True)
    semi = dich
    dir_E = a.out / "E_inserimento"
    P = [x for x in piano(list(a.contesto), semi, semi_torch)
         if x["contesto"] in a.contesto]

    print("=" * 84)
    print(f"FASE 1 — PUNTI DI CONTROLLO E  ({len(P)} addestramenti)")
    print("=" * 84)
    d = descrivi_braccio(BRACCIO)
    print(f"  popolazione: {d['popolazione']}")
    print(f"  corpus:      {d['corpus']}")
    print(f"  {d['nota']}")
    print(f"\n  selezione del punto di controllo: **initial_network**")
    print(f"     wCE sui nodi della RETE INIZIALE, nel periodo di validazione")
    print(f"     i nodi di validazione induttiva restano riservati alla")
    print(f"     selezione degli iperparametri di F")
    print(f"\n  semi dichiarati {list(dich)}  <- si semina con QUESTI")
    print(f"  semi di torch   {[int(x) for x in semi_torch][:4]}…  "
          f"<- derivati da `addestra_una`")
    print(f"  partizioni {list(PARTIZIONI)}, semi {SEME_PARTIZIONE}")

    # ---- PREREQUISITI, bloccanti ------------------------------------------
    try:
        # le chiavi degli artefatti usano i semi di TORCH
        r = verifica_E(a.out / "canonico", a.out / "maschere", a.out / "pesi",
                       semi_torch, a.contesto)
        print(f"\n  prerequisiti verificati: canonico, maschere, pesi per "
              f"{len(r['contesti'])} contesti e {r['semi']} semi")
    except PrerequisitoMancante as e:
        print(f"\n{e}")
        return 1

    if a.piano:
        print(f"\n  --piano: nessuna esecuzione avviata.")
        for x in P[:6]:
            print(f"     {x['contesto']:11s} p{x['partizione']} "
                  f"seme {x['seme']}")
        print(f"     … e altre {max(len(P) - 6, 0)}")
        return 0

    dir_E.mkdir(parents=True, exist_ok=True)
    f_ord = dir_E / "ordine_E.json"
    f_ord.write_text(json.dumps(
        {"istante": datetime.now(timezone.utc).isoformat(),
         "regola": "seme -> partizione -> contesti intercalati",
         "avvertenza": "NON modificabile in funzione dei risultati",
         "ordine": P}, indent=2, ensure_ascii=False))
    print(f"  ordine salvato in {f_ord}\n")

    from evoluzione.esperimenti.addestramento import addestra_una
    from evoluzione.componente.registro import Registro

    class Esec:
        def __init__(s, c, p, i, v):
            s.contesto, s.partizione = c, p
            s.inizializzazione, s.variante = i, v

    cfg = {"epoche": a.epoche, "lotto": a.lotto, "passo": a.passo,
           "pazienza": a.pazienza, "storia_descrittore_passi": 96,
           "finestra_dinamica_passi": 12, "orizzonti": [1, 2, 4, 8],
           "sorgente": "traffic4cast", "etichetta": "E_inserimento",
           "braccio": BRACCIO,
           # §5bis: la RETE INIZIALE, non i nodi di validazione induttiva.
           # Quelli restano riservati alla selezione degli iperparametri di F.
           "checkpoint_selection_population": "initial_network",
           "dir_canonico": str(a.out / "canonico"),
           "dir_stati_completi": str(a.out / "stati_completi")}

    fatte, tempi, guai = [], [], []
    for i, x in enumerate(P, 1):
        # il nome usa il seme di TORCH, che `addestra_una` deriva
        f = percorso_E(dir_E, x["contesto"], x["partizione"],
                       x["seme_torch"])
        if f.exists() and not a.riparti:
            continue
        print(f"  [{i:3d}/{len(P)}] {x['contesto']:11s} p{x['partizione']} "
              f"seme {x['seme']:4d}->{x['seme_torch']:11d}",
              end=" ", flush=True)
        t0 = time.time()
        # VARIANTE e BRACCIO sono cose diverse. E non usa descrittori, sicche'
        # la variante non gli si applica: si passa `None`, e `addestra_una`
        # non ne chiede lo schema.
        E = Esec(x["contesto"], x["partizione"], 0, None)
        gen = {"partizione": np.random.default_rng(
                   SEME_PARTIZIONE[x["partizione"]]),
               "inizializzazione": np.random.default_rng(x["seme"])}
        reg = Registro.avvia(f"E_inserimento/{BRACCIO}",
                             note=f"{x['contesto']} p{x['partizione']} "
                                  f"seme {x['seme']}",
                             radice=a.out / "registro")
        reg.configurazione({**cfg, **x})
        try:
            addestra_una(E, reg, cfg, gen, a.out)
            reg.completa()
            dt = time.time() - t0
            tempi.append(dt)
            fatte.append(x)
            print(f"-> {dt:5.1f}s")
        except Exception as exc:                            # noqa: BLE001
            reg.evento(f"{type(exc).__name__}: {exc}")
            reg.completa("fallita")
            guai.append({**x, "errore": f"{type(exc).__name__}: {exc}"[:200]})
            print(f"-> FALLISCE: {type(exc).__name__}")
            break

    print(f"\n{'=' * 84}")
    print(f"  {len(fatte)} completate, {len(guai)} fallite")
    if tempi:
        t = np.array(tempi)
        print(f"\n  COSTO MISURATO, addestramenti completi:")
        print(f"     mediana {np.median(t):6.1f}s | minimo {t.min():5.1f}s | "
              f"massimo {t.max():6.1f}s | totale {t.sum()/60:.1f} min")
        print(f"     proiezione per le 108: {108*np.median(t)/60:.1f} minuti")
        print(f"\n  **La stima delle fasi successive va confermata dai tempi**")
        print(f"  osservati, non assunta: gli adattamenti non sono ancora stati")
        print(f"  cronometrati.")
    (dir_E / "esito_E.json").write_text(json.dumps(
        {"completate": len(fatte), "fallite": guai,
         "tempi_s": tempi, "mediana_s": float(np.median(tempi)) if tempi else None,
         "istante": datetime.now(timezone.utc).isoformat()},
        indent=2, ensure_ascii=False))
    return 0 if not guai else 1


if __name__ == "__main__":
    raise SystemExit(main())
