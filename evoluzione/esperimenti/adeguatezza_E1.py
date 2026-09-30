#!/usr/bin/env python3
"""
Prova di adeguatezza ridotta per E1 (controllo 4 di protocol/E2.md).
=====================================================================
**Una traiettoria a 4.580 aggiornamenti** per E ed E1, stessa citta', stessa
partizione, stesso seme, attraverso `addestra_una` — lo stesso percorso della
campagna, non una copia. La domanda: **l'ordine fra E ed E1 sulla V-full della
rete iniziale a 2.290 e' lo stesso che a 4.580?** Se no, il budget non e'
adeguato per E1 e lo si dichiara.

    citta'       Madrid
    partizione   0 (seme 1000)
    seme         201, il primo della campagna d'inserimento
    punti        gli undici della campagna, poi ogni 229 fino a 4.580

**Il seme e' uno di quelli della campagna, di proposito**: i primi undici
punti della curva devono coincidere esattamente con quelli registrati nei
manifesti di `E_inserimento_griglia` ed `E1_inserimento_griglia`. Se non
coincidono, questa prova non sta misurando la campagna.

Scrive in `results/evoluzione/adeguatezza_E1/` e il riepilogo in
`results/evoluzione/adeguatezza_E1.json`, che il congelamento di E2 legge.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/adeguatezza_E1.py --piano
    poetry run python evoluzione/esperimenti/adeguatezza_E1.py --lavoratori 2
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

from evoluzione.componente.bracci import proprieta as proprieta_braccio  # noqa
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    AGGIORNAMENTI_PRINCIPALE, PUNTI_PRINCIPALE)

ETICHETTA = "adeguatezza_E1"
CONTESTO, PARTIZIONE, SEME = "Madrid", 0, 201
TETTO = 4580
PUNTI = tuple(PUNTI_PRINCIPALE) + tuple(
    range(AGGIORNAMENTI_PRINCIPALE + 229, TETTO + 1, 229))
BRACCI = ("E", "E1")
RHO = 0.15
CARTELLA_CAMPAGNA = {"E": "E_inserimento_griglia", "E1": "E1_inserimento_griglia"}


class Esec:
    def __init__(self, c, p):
        self.contesto, self.partizione = c, p
        self.inizializzazione, self.variante = 0, None


def cfg_di(braccio: str, out: Path) -> dict:
    """La configurazione di `esegui_E.py --protocollo griglia`, con il tetto
    esteso. Tutto il resto identico: canonico, pesi della griglia, selezione
    sulla rete iniziale."""
    return {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
            "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
            "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
            "etichetta": ETICHETTA, "braccio": braccio,
            **({"rho": RHO} if proprieta_braccio(braccio).richiede_rho else {}),
            "training_protocol": "principale", "griglia_temporale": "reale",
            "max_optimizer_updates": TETTO, "punti": list(PUNTI),
            "dir_pesi": str(out / "pesi_griglia"),
            "checkpoint_selection_population": "initial_network",
            "dir_canonico": str(out / "canonico"),
            "dir_stati_completi": str(out / f"stati_completi_{ETICHETTA}")}


def _lavora(args):
    braccio, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.componente.registro import Registro
    from evoluzione.esperimenti.addestramento import addestra_una
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    out = Path(out)
    cfg = cfg_di(braccio, out)
    reg = Registro.avvia(f"{ETICHETTA}/{braccio}",
                         note=f"{CONTESTO} p{PARTIZIONE} seme {SEME} tetto {TETTO}",
                         radice=out / "registro")
    reg.configurazione({**cfg, "contesto": CONTESTO, "partizione": PARTIZIONE,
                        "seme": SEME})
    t0 = time.time()
    try:
        gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE[PARTIZIONE]),
               "inizializzazione": np.random.default_rng(SEME)}
        ck = addestra_una(Esec(CONTESTO, PARTIZIONE), reg, cfg, gen, out)
        reg.completa()
        man = json.loads(Path(reg._p).read_text())
        return {"braccio": braccio, "esito": "completata",
                "secondi": time.time() - t0, "ck": str(ck),
                "manifesto": str(reg._p),
                "curve": man["protocollo_principale"]["curve"],
                "aggiornamento_selezionato":
                    man["protocollo_principale"]["aggiornamento_selezionato"]}
    except Exception as e:                                  # noqa: BLE001
        reg.evento(f"{type(e).__name__}: {e}")
        reg.completa("fallita")
        return {"braccio": braccio, "esito": "fallita",
                "secondi": time.time() - t0,
                "errore": f"{type(e).__name__}: {e}"[:400]}


def curva_campagna(out: Path, braccio: str) -> list | None:
    """La curva dei primi undici punti registrata nella CAMPAGNA, per lo
    stesso braccio, citta', partizione e seme."""
    exp = f"{CARTELLA_CAMPAGNA[braccio]}/{braccio}"
    for f in sorted((out / "registro").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        cfg = d.get("resolved_configuration") or {}
        if (d.get("esperimento") == exp and d.get("run_status") == "completato"
                and cfg.get("contesto") == CONTESTO
                and int(cfg.get("partizione", -1)) == PARTIZIONE
                and int(cfg.get("seme", -1)) == SEME):
            return d.get("protocollo_principale", {}).get("curve")
    return None


def selezione(curve, tetto: int) -> dict:
    """Il minimo di V-full fra i punti <= tetto; a parita', il precedente —
    la regola della campagna, simulata a posteriori."""
    mig, u_mig = float("inf"), None
    for r in curve:
        if r["aggiornamento"] <= tetto and r["V-full"] < mig:
            mig, u_mig = r["V-full"], r["aggiornamento"]
    return {"aggiornamento": u_mig, "V-full": mig}


def main() -> int:
    ap = argparse.ArgumentParser(description="adeguatezza ridotta per E1")
    ap.add_argument("--lavoratori", type=int, default=2)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    print("=" * 84)
    print(f"ADEGUATEZZA RIDOTTA PER E1 — tetto {TETTO}, {len(BRACCI)} "
          f"traiettorie")
    print("=" * 84)
    print(f"  {CONTESTO} p{PARTIZIONE} seme {SEME}; bracci {BRACCI}; "
          f"rho = {RHO} per E1")
    print(f"  punti: {list(PUNTI)}")
    print(f"  cartella: {a.out / ETICHETTA}; pesi: {a.out / 'pesi_griglia'}")
    print(f"  parallelismo: {a.lavoratori} processi x {a.fili} filo")
    rif = {b: curva_campagna(a.out, b) for b in BRACCI}
    for b in BRACCI:
        print(f"  curva della campagna per {b}: "
              + (f"{len(rif[b])} punti" if rif[b] else "**NON trovata**"))
    if a.piano:
        print("\n  --piano: nessuna esecuzione avviata.")
        return 0
    if any(rif[b] is None for b in BRACCI):
        print("\n  senza la curva della campagna il confronto non e' "
              "possibile: mi fermo.")
        return 1

    ctx = mp.get_context("spawn")
    t0 = time.time()
    with ctx.Pool(a.lavoratori) as pool:
        esiti = list(pool.imap_unordered(
            _lavora, [(b, str(a.out), a.fili) for b in BRACCI]))
    esiti = {r["braccio"]: r for r in esiti}
    for b in BRACCI:
        r = esiti[b]
        print(f"  {b:3s} {r['esito']:10s} {r['secondi']/60:6.1f} min"
              + (f"\n      {r['errore']}" if r["esito"] == "fallita" else ""))
    if any(r["esito"] != "completata" for r in esiti.values()):
        return 1

    # ---- [1] i primi undici punti coincidono con la campagna --------------
    print("\n[1] i primi undici punti riproducono la campagna")
    coincide = {}
    for b in BRACCI:
        qui = {r["aggiornamento"]: r["V-full"] for r in esiti[b]["curve"]}
        la = {r["aggiornamento"]: r["V-full"] for r in rif[b]}
        sc = max(abs(qui[u] - la[u]) for u in la)
        coincide[b] = {"scarto_massimo": sc, "punti": len(la)}
        print(f"  {b:3s} scarto massimo {sc:.2e} su {len(la)} punti "
              f"{'PASSA' if sc == 0.0 else 'FALLISCE'}")

    # ---- [2] ordine a 2.290 e a 4.580 --------------------------------------
    print("\n[2] selezione e ordine")
    sel = {b: {str(t): selezione(esiti[b]["curve"], t)
               for t in (AGGIORNAMENTI_PRINCIPALE, TETTO)} for b in BRACCI}
    ordine = {}
    for t in (AGGIORNAMENTI_PRINCIPALE, TETTO):
        vE, v1 = sel["E"][str(t)]["V-full"], sel["E1"][str(t)]["V-full"]
        ordine[str(t)] = "E < E1" if vE < v1 else "E1 < E"
        print(f"  tetto {t}: E u{sel['E'][str(t)]['aggiornamento']} "
              f"V-full {vE:.5f} | E1 u{sel['E1'][str(t)]['aggiornamento']} "
              f"V-full {v1:.5f}  -> {ordine[str(t)]}")
    invariato = ordine[str(AGGIORNAMENTI_PRINCIPALE)] == ordine[str(TETTO)]
    # migliora oltre 2.290? di quanto, in relativo
    oltre = {b: (sel[b][str(AGGIORNAMENTI_PRINCIPALE)]["V-full"]
                 - sel[b][str(TETTO)]["V-full"])
             / sel[b][str(AGGIORNAMENTI_PRINCIPALE)]["V-full"] for b in BRACCI}
    for b in BRACCI:
        print(f"  {b:3s} miglioramento relativo di V-full oltre 2.290: "
              f"{oltre[b]:+.3%}")
    print(f"\n  **ordine {'INVARIATO' if invariato else 'CAMBIATO'}** fra "
          f"2.290 e 4.580"
          + ("" if invariato else ": il budget NON e' adeguato per E1, da "
             "dichiarare"))

    riep = {"contesto": CONTESTO, "partizione": PARTIZIONE, "seme": SEME,
            "rho": RHO, "tetto": TETTO, "punti": list(PUNTI),
            "bracci": list(BRACCI),
            "curve": {b: esiti[b]["curve"] for b in BRACCI},
            "riproduce_campagna": coincide,
            "selezione": sel, "ordine": ordine, "ordine_invariato": invariato,
            "miglioramento_relativo_oltre_2290": oltre,
            "secondi": {b: esiti[b]["secondi"] for b in BRACCI},
            "nota_tempi": "in concorrenza: non entrano nella tabella dei costi",
            "manifesti": {b: esiti[b]["manifesto"] for b in BRACCI},
            "ore_calendario": (time.time() - t0) / 3600,
            "istante": datetime.now(timezone.utc).isoformat()}
    f = a.out / "adeguatezza_E1.json"
    f.write_text(json.dumps(riep, indent=2, ensure_ascii=False))
    print(f"\n  riepilogo in {f}")
    return 0 if all(c["scarto_massimo"] == 0.0 for c in coincide.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
