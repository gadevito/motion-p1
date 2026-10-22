#!/usr/bin/env python3
"""
E15 — pilota dei tempi: addestramenti E su Londra, in parallelo, per stimare i 270 della campagna.
====================================================================================================
Usa `esegui_E._lavora` (lo STESSO esecutore della fase 1) con la configurazione della griglia
(protocollo `griglia`, braccio E), in una cartella propria (`E_pilota_e15/`): nessun punto di
controllo della campagna viene toccato. Statica: quella predefinita del codice (causale).

Misura i minuti per addestramento con `--lavoratori` processi concorrenti (il tempo di parete di
un addestramento sotto carico e' quello che conta per la stima) e stima la campagna:
270 addestramenti / lavoratori × mediana dei minuti.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/pilota_tempi_e15.py --n 16 --lavoratori 16
    poetry run python evoluzione/esperimenti/pilota_tempi_e15.py --n 5 --lavoratori 5
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ETICHETTA = "E_pilota_e15"
N_CAMPAGNA = 270


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contesto", default="Londra")
    ap.add_argument("--n", type=int, default=16)
    ap.add_argument("--lavoratori", type=int, default=16)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    from evoluzione.esperimenti.inserimento import applica_statica, argomento_statica
    argomento_statica(ap)
    a = ap.parse_args()
    print(f"  statica: {applica_statica(a.statica)}")
    from evoluzione.esperimenti.esegui_E import _lavora, ambiente, piano
    from evoluzione.esperimenti.fasi import PARTIZIONI
    from evoluzione.esperimenti.semi import configurazione
    _, dich, semi_torch = configurazione(inserimento=True)
    P = piano([a.contesto], dich, semi_torch, PARTIZIONI, braccio="E")[:a.n]
    cfg = {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
           "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
           "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
           "etichetta": ETICHETTA, "braccio": "E",
           "training_protocol": "principale", "griglia_temporale": "reale",
           "dir_pesi": str(a.out / "pesi_griglia"),
           "checkpoint_selection_population": "initial_network",
           "dir_canonico": str(a.out / "canonico"),
           "dir_stati_completi": str(a.out / f"stati_completi_{ETICHETTA}")}
    print("=" * 84)
    print(f"PILOTA DEI TEMPI E15 — {len(P)} addestramenti E su {a.contesto}, {a.lavoratori} lavoratori x {a.fili} filo/i")
    print(f"  ambiente: {json.dumps(ambiente(a.fili))}")
    print("=" * 84)
    (a.out / ETICHETTA).mkdir(parents=True, exist_ok=True)
    ctx = mp.get_context("spawn"); t0 = time.time(); esiti = []
    with ctx.Pool(a.lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_lavora, [(x, cfg, str(a.out), a.fili) for x in P]), 1):
            esiti.append(r)
            print(f"  [{i:2d}/{len(P)}] p{r['partizione']} s{r['seme']} {r['esito']:10s} {r['secondi']/60:5.1f} min"
                  + (f"  {r['errore']}" if r["esito"] == "fallita" else ""), flush=True)
    parete = time.time() - t0
    ok = [r["secondi"] / 60 for r in esiti if r["esito"] == "completata"]
    import numpy as np
    med = float(np.median(ok)) if ok else float("nan")
    stima_h = N_CAMPAGNA / a.lavoratori * med / 60 if ok else float("nan")
    R = {"contesto": a.contesto, "n": len(P), "lavoratori": a.lavoratori, "fili": a.fili,
         "statica": applica_statica(None), "ambiente": ambiente(a.fili),
         "minuti": {"min": float(min(ok)) if ok else None, "mediana": med, "max": float(max(ok)) if ok else None},
         "parete_min": parete / 60, "completati": len(ok), "falliti": len(esiti) - len(ok),
         "stima_campagna": {"addestramenti": N_CAMPAGNA, "ore": stima_h,
                            "regola": "270 / lavoratori x mediana dei minuti per addestramento"},
         "istante": datetime.now(timezone.utc).isoformat()}
    f = a.out / ETICHETTA / f"pilota_tempi_{a.lavoratori}.json"
    f.write_text(json.dumps(R, indent=2))
    print(f"\n  {len(ok)} completati, {len(esiti) - len(ok)} falliti; minuti per addestramento min/mediana/max "
          f"{R['minuti']['min']:.1f}/{med:.1f}/{R['minuti']['max']:.1f}; parete {parete/60:.1f} min")
    print(f"  stima per {N_CAMPAGNA} addestramenti a {a.lavoratori} lavoratori: {stima_h:.1f} h  (+ 54 adattamenti, minuti)")
    print(f"  salvato in {f}")
    return 0 if len(ok) == len(esiti) else 1


if __name__ == "__main__":
    raise SystemExit(main())
