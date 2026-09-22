#!/usr/bin/env python3
"""
Fase 1 — punti di controllo E, in parallelo.
=============================================
3 citta' x 3 partizioni x 12 semi = **108 addestramenti** con embedding liberi
sui soli nodi iniziali.

IL PROTOCOLLO si dichiara: `principale` (2.290 aggiornamenti, undici punti,
selezione su V-full) o `storico`. **Le due serie vanno in cartelle diverse**:
`E_inserimento` conserva i 108 punti storici, che non si sovrascrivono.

IL PARALLELISMO, misurato prima di sceglierlo (`misura_parallelismo.py`):

    il numero di fili NON cambia la numerica: impronte identiche con 1, 2, 4, 14
    8 processi x 1 filo: 3,51x, la migliore delle configurazioni misurate

**Un solo ambiente**: tutti i bracci sulla stessa macchina, stesso backend CPU.
Hardware, librerie e fili vanno nel manifesto di ciascuna esecuzione.

LA RIPRESA NON SI FIDA DEL FILE DEI PESI. Il ciclo principale salva il punto
migliore a ogni miglioramento, gia' dal primo punto: un'esecuzione interrotta
lascerebbe un file che SEMBRA completo. **Un'esecuzione e' completata solo se
esiste il suo marcatore `.fatto`**, scritto atomicamente dopo la fine.

**I riepiloghi li scrive soltanto il processo padre**: otto lavoratori che
scrivono `ordine_E.json` si sovrascriverebbero.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_E.py --piano
    poetry run python evoluzione/esperimenti/esegui_E.py --lavoratori 8
"""
import argparse
import json
import multiprocessing as mp
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

BRACCIO = "E"
CARTELLA = {"storico": "E_inserimento", "principale": "E_inserimento_principale"}


class Esec:
    """L'esecuzione: variante None, perche' E non usa descrittori."""

    def __init__(self, c, p):
        self.contesto, self.partizione = c, p
        self.inizializzazione, self.variante = 0, None


def ambiente(fili: int) -> dict:
    """Hardware, librerie, backend e fili: richiesti per il parallelismo."""
    import numpy as np
    import torch
    return {"piattaforma": platform.platform(),
            "processore": platform.processor(),
            "nuclei_logici": os.cpu_count(),
            "python": platform.python_version(),
            "torch": torch.__version__, "numpy": np.__version__,
            "backend": "cpu", "fili_torch": fili,
            "nota": ("numero di fili verificato ininfluente sulla numerica: "
                     "impronte identiche con 1, 2, 4 e 14 fili")}


def marcatore(ck: Path) -> Path:
    return ck.with_name(ck.name + ".fatto")


def scrivi_atomico_testo(f: Path, testo: str):
    tmp = f.with_name(f.name + ".tmp")
    with open(tmp, "w") as h:
        h.write(testo); h.flush(); os.fsync(h.fileno())
    os.replace(tmp, f)


def _lavora(args):
    """UN addestramento. Al livello del modulo: `spawn` deve poterlo importare."""
    x, cfg, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.componente.registro import Registro
    from evoluzione.esperimenti.addestramento import addestra_una
    from evoluzione.esperimenti.fasi import percorso_E
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    out = Path(out)
    ck = percorso_E(out / cfg["etichetta"], x["contesto"], x["partizione"],
                    x["seme_torch"])
    t0 = time.time()
    reg = Registro.avvia(f"{cfg['etichetta']}/{BRACCIO}",
                         note=f"{x['contesto']} p{x['partizione']} "
                              f"seme {x['seme']}",
                         radice=out / "registro")
    reg.configurazione({**cfg, **x})
    reg.evento(f"ambiente: {json.dumps(ambiente(fili))}")
    try:
        gen = {"partizione": np.random.default_rng(
                   SEME_PARTIZIONE[x["partizione"]]),
               # il seme DICHIARATO: `addestra_una` ne deriva quello di torch
               "inizializzazione": np.random.default_rng(x["seme"])}
        ck_ = addestra_una(Esec(x["contesto"], x["partizione"]), reg, cfg,
                           gen, out)
        if Path(ck_) != ck:
            raise RuntimeError(f"punto di controllo inatteso: {ck_} contro {ck}")
        reg.completa()
        dt = time.time() - t0
        # IL MARCATORE, per ultimo e atomico: solo ora l'esecuzione e' completa
        scrivi_atomico_testo(marcatore(ck), json.dumps(
            {**x, "secondi": dt, "ambiente": ambiente(fili),
             "istante": datetime.now(timezone.utc).isoformat()}, indent=2))
        return {**x, "esito": "completata", "secondi": dt}
    except Exception as e:                                  # noqa: BLE001
        reg.evento(f"{type(e).__name__}: {e}")
        reg.completa("fallita")
        return {**x, "esito": "fallita", "secondi": time.time() - t0,
                "errore": f"{type(e).__name__}: {e}"[:300]}


def piano(contesti, semi_dich, semi_torch, partizioni):
    """Contesti intercalati e partizioni ruotate."""
    fuori = []
    for i, (s, st) in enumerate(zip(semi_dich, semi_torch)):
        for j, p in enumerate(partizioni):
            r = (i * len(partizioni) + j) % len(contesti)
            for c in contesti[r:] + contesti[:r]:
                fuori.append({"contesto": c, "partizione": p, "seme": int(s),
                              "seme_torch": int(st), "braccio": BRACCIO})
    return fuori


def main() -> int:
    from evoluzione.esperimenti.fasi import (
        CONTESTI, PARTIZIONI, PrerequisitoMancante, descrivi_braccio,
        percorso_E, verifica_E)
    from evoluzione.esperimenti.semi import configurazione

    ap = argparse.ArgumentParser(description="fase 1: punti di controllo E")
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--protocollo", default="principale",
                    choices=("principale", "storico"))
    ap.add_argument("--lavoratori", type=int, default=1)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()

    _, dich, semi_torch = configurazione(inserimento=True)
    etichetta = CARTELLA[a.protocollo]
    dir_E = a.out / etichetta
    P = [x for x in piano(list(a.contesto), dich, semi_torch, PARTIZIONI)
         if x["contesto"] in a.contesto]
    cfg = {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
           "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
           "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
           "etichetta": etichetta, "braccio": BRACCIO,
           "training_protocol": a.protocollo,
           "checkpoint_selection_population": "initial_network",
           "dir_canonico": str(a.out / "canonico"),
           "dir_stati_completi": str(a.out / f"stati_completi_{etichetta}")}

    print("=" * 84)
    print(f"FASE 1 — PUNTI DI CONTROLLO E  ({len(P)} addestramenti)")
    print("=" * 84)
    d = descrivi_braccio(BRACCIO)
    print(f"  popolazione: {d['popolazione']} | corpus: {d['corpus']}")
    print(f"  protocollo: **{a.protocollo}** -> {dir_E}")
    if a.protocollo == "principale":
        print(f"     2.290 aggiornamenti, undici punti, selezione su V-full, "
              f"nessun arresto anticipato")
    print(f"  parallelismo: {a.lavoratori} lavoratori x {a.fili} filo/i, "
          f"backend CPU")

    try:
        verifica_E(a.out / "canonico", a.out / "maschere", a.out / "pesi",
                   semi_torch, a.contesto)
        print(f"  prerequisiti verificati: canonico, maschere, pesi")
    except PrerequisitoMancante as e:
        print(f"\n{e}")
        return 1

    fatte = [x for x in P if marcatore(percorso_E(dir_E, x["contesto"],
                                                  x["partizione"],
                                                  x["seme_torch"])).exists()]
    da_fare = [x for x in P if x not in fatte]
    print(f"\n  completate (marcatore presente): {len(fatte)} | "
          f"da eseguire: {len(da_fare)}")

    if a.piano:
        print(f"\n  --piano: nessuna esecuzione avviata.")
        for x in da_fare[:6]:
            print(f"     {x['contesto']:11s} p{x['partizione']} "
                  f"seme {x['seme']}->{x['seme_torch']}")
        return 0

    dir_E.mkdir(parents=True, exist_ok=True)
    scrivi_atomico_testo(dir_E / "ordine_E.json", json.dumps(
        {"istante": datetime.now(timezone.utc).isoformat(),
         "protocollo": a.protocollo, "lavoratori": a.lavoratori,
         "fili": a.fili, "ambiente": ambiente(a.fili),
         "avvertenza": "NON modificabile in funzione dei risultati",
         "ordine": P}, indent=2, ensure_ascii=False))

    ctx = mp.get_context("spawn")
    esiti, t0 = [], time.time()
    lavori = [(x, cfg, str(a.out), a.fili) for x in da_fare]
    with ctx.Pool(a.lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_lavora, lavori), 1):
            esiti.append(r)
            trasc = time.time() - t0
            resto = trasc / i * (len(lavori) - i)
            print(f"  [{i:3d}/{len(lavori)}] {r['contesto']:11s} "
                  f"p{r['partizione']} s{r['seme']}  {r['esito']:10s} "
                  f"{r['secondi']/60:5.1f} min  | trascorse "
                  f"{trasc/3600:5.1f} h, ne restano ~{resto/3600:5.1f} h"
                  + (f"\n        {r['errore']}" if r["esito"] == "fallita"
                     else ""), flush=True)

    fallite = [r for r in esiti if r["esito"] == "fallita"]
    scrivi_atomico_testo(dir_E / "esito_E.json", json.dumps(
        {"protocollo": a.protocollo, "completate": len(esiti) - len(fallite),
         "fallite": fallite, "gia_fatte": len(fatte),
         "ore_calendario": (time.time() - t0) / 3600,
         "ore_macchina": sum(r["secondi"] for r in esiti) / 3600,
         "istante": datetime.now(timezone.utc).isoformat()},
        indent=2, ensure_ascii=False))
    print(f"\n{'=' * 84}")
    print(f"  {len(esiti) - len(fallite)} completate, {len(fallite)} fallite, "
          f"{len(fatte)} gia' fatte")
    print(f"  {(time.time() - t0)/3600:.1f} ore di calendario, "
          f"{sum(r['secondi'] for r in esiti)/3600:.1f} ore-macchina")
    return 0 if not fallite else 1


if __name__ == "__main__":
    raise SystemExit(main())
