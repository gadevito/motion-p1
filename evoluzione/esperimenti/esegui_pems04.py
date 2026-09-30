#!/usr/bin/env python3
"""
Verifica esterna su PEMS04: 72 addestramenti, soli C e P.
==========================================================
    3 contesti x 12 inizializzazioni x 2 modelli = 72

**Ogni contesto E' una partizione**: `PEMS04_p<k>` gira con `partizione=k`, e
`_coerenza_pems04` lo impone. Non ci sono E, F, A ne' R: la politica di
aggiornamento e' gia' congelata e la validazione seleziona soltanto i punti di
controllo di C e P.

**P si valuta due volte dallo stesso punto di controllo**, congelato e
aggiornato: e' `esegui_refresh.py` a farlo, dopo.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_pems04.py --piano
    poetry run python evoluzione/esperimenti/esegui_pems04.py --lavoratori 8
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

ETICHETTA = "pems04"
CONTESTI = ("PEMS04_p0", "PEMS04_p1", "PEMS04_p2")
BRACCI = ("C", "P")


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


def cfg_pems(b: str, c: str, p: int, s: int, out: Path) -> dict:
    from evoluzione.componente.bracci import proprieta as proprieta_braccio
    return {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
            "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
            "orizzonti": [1, 2, 4, 8], "sorgente": "pems04",
            "etichetta": ETICHETTA, "braccio": b,
            "training_protocol": "principale", "griglia_temporale": "reale",
            "checkpoint_selection_population": "initial_network",
            "dir_pesi": str(out / "pesi_pems04"),
            "dir_canonico": str(out / "canonico"),
            "dir_stati_completi": str(out / f"stati_{ETICHETTA}"),
            "popolazione": "iniziale", "campionamento": "uniforme_istanti",
            "valutazione_interna": False,
            "nome_ck": f"ck_{b}_{c}_s{s}.pt",
            # lo schema del descrittore lo dice la tabella unica dei bracci
            "variante": proprieta_braccio(b).variante}


def _lavora(args):
    x, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.componente.registro import Registro
    from evoluzione.esperimenti.addestramento import addestra_una
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    out = Path(out)
    c, p, s, b = x["contesto"], x["partizione"], x["seme"], x["braccio"]
    cfg = cfg_pems(b, c, p, s, out)
    ck = out / ETICHETTA / cfg["nome_ck"]
    t0 = time.time()
    reg = Registro.avvia(f"{ETICHETTA}/{b}", note=f"{c} seme {s} braccio {b}",
                         radice=out / "registro")
    reg.configurazione({**cfg, **x})
    try:
        gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE[p]),
               "inizializzazione": np.random.default_rng(s)}
        addestra_una(Esec(c, p, cfg["variante"]), reg, cfg, gen, out)
        reg.completa()
        scrivi_atomico(marcatore(ck), json.dumps(
            {**x, "secondi": time.time() - t0,
             "istante": datetime.now(timezone.utc).isoformat()}))
        return {**x, "esito": "completata", "secondi": time.time() - t0}
    except Exception as e:                                   # noqa: BLE001
        reg.evento(f"{type(e).__name__}: {e}")
        reg.completa("fallita")
        return {**x, "esito": "fallita", "secondi": time.time() - t0,
                "errore": f"{type(e).__name__}: {e}"[:300]}


def main() -> int:
    from evoluzione.esperimenti.semi import configurazione
    ap = argparse.ArgumentParser(description="verifica esterna su PEMS04")
    ap.add_argument("--lavoratori", type=int, default=1)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    _, dich, _ = configurazione(inserimento=True)
    P = [{"contesto": c, "partizione": i, "seme": int(s), "braccio": b}
         for i, c in enumerate(CONTESTI) for s in dich for b in BRACCI]
    dir_c = a.out / ETICHETTA
    print("=" * 80)
    print(f"VERIFICA ESTERNA SU PEMS04 — {len(P)} addestramenti")
    print("=" * 80)
    print(f"  {len(CONTESTI)} contesti x {len(dich)} inizializzazioni x "
          f"{len(BRACCI)} modelli")
    print(f"  **ogni contesto e' una partizione**; nessun E, F, A o R")
    fatte = [x for x in P if marcatore(
        dir_c / cfg_pems(x["braccio"], x["contesto"], x["partizione"],
                         x["seme"], a.out)["nome_ck"]).exists()]
    da_fare = [x for x in P if x not in fatte]
    print(f"\n  completate: {len(fatte)} | da eseguire: {len(da_fare)}")
    if a.piano:
        for x in da_fare[:4]:
            print(f"     {x['contesto']} p{x['partizione']} s{x['seme']} "
                  f"{x['braccio']}")
        return 0
    dir_c.mkdir(parents=True, exist_ok=True)
    ctx = mp.get_context("spawn")
    esiti, t_in = [], time.time()
    with ctx.Pool(a.lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(
                _lavora, [(x, str(a.out), a.fili) for x in da_fare]), 1):
            esiti.append(r)
            tr = time.time() - t_in
            print(f"  [{i:3d}/{len(da_fare)}] {r['contesto']} s{r['seme']} "
                  f"{r['braccio']}  {r['esito']:10s} {r['secondi']/60:5.1f} min "
                  f"| {tr/3600:4.1f} h, restano ~"
                  f"{tr/i*(len(da_fare)-i)/3600:4.1f} h"
                  + (f"\n        {r['errore']}"
                     if r["esito"] == "fallita" else ""), flush=True)
    falliti = [r for r in esiti if r["esito"] == "fallita"]
    scrivi_atomico(dir_c / "esito_pems04.json", json.dumps(
        {"completate": len(esiti) - len(falliti), "fallite": falliti,
         "ore_calendario": (time.time() - t_in) / 3600,
         "lavoratori": a.lavoratori, "fili": a.fili}, indent=2))
    print(f"\n  {len(esiti) - len(falliti)} completate, {len(falliti)} fallite")
    return 0 if not falliti else 1


if __name__ == "__main__":
    raise SystemExit(main())
