#!/usr/bin/env python3
"""
E6 — replica esterna, parte B (PEMS08). Esecutore per fasi.
=============================================================
Pre-registrazione in `protocol/E6.md`. Questa versione contiene la sola fase
**pilota** (costo di un addestramento di C su PEMS08, a seme unico, che non si
guarda): serve a scrivere il costo nel protocollo PRIMA della firma. Le fasi
della campagna si aggiungono dopo la firma, come per E5.

Il pilota usa ESATTAMENTE la configurazione della campagna (`cfg_pems` di
`esegui_pems04`, con pesi `pesi_pems08`, `fine_periodo` = t0 di prova
pre-registrato e cartelle proprie): quel che si misura e' quel che si lancera'.
**Processo unico, macchina scarica**: il tempo entra nella tabella dei costi.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_e6.py --fase pilota --piano
    poetry run python evoluzione/esperimenti/esegui_e6.py --fase pilota
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))
from evoluzione.esperimenti.esegui_pems04 import (  # noqa: E402
    Esec, cfg_pems, marcatore, scrivi_atomico)

CONTESTI = tuple(f"PEMS08_p{k}" for k in range(6))   # 6 partizioni x 6 semi (E6.md)
SEMI_E6 = (201, 202, 203, 204, 205, 206)
T0_PROVA = 3840          # protocol/E6.md, parte B: pre-registrato
T0_VALIDAZIONE = 3162
ETICHETTA = "e6_pems08"
ETICHETTA_PILOTA = "e6_pilota"
SEME_PILOTA = 201        # il primo seme dichiarato; il punto non entra nella campagna


def cfg_e6(b: str, c: str, p: int, s: int, out: Path, etichetta: str = ETICHETTA) -> dict:
    """La configurazione di PEMS04 con tre differenze dichiarate: pesi di
    PEMS08, `fine_periodo` = t0 di prova, cartelle proprie."""
    cfg = cfg_pems(b, c, p, s, out)
    cfg.update({"etichetta": etichetta, "dir_pesi": str(out / "pesi_pems08"),
                "fine_periodo": T0_PROVA,
                "dir_stati_completi": str(out / f"stati_{etichetta}")})
    return cfg


def _pilota(out: Path, fili: int) -> dict:
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.componente.registro import Registro
    from evoluzione.esperimenti.addestramento import addestra_una
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    c, p, s, b = CONTESTI[0], 0, SEME_PILOTA, "C"
    cfg = cfg_e6(b, c, p, s, out, ETICHETTA_PILOTA)
    ck = out / ETICHETTA_PILOTA / cfg["nome_ck"]
    if marcatore(ck).exists():
        return json.loads(marcatore(ck).read_text())
    reg = Registro.avvia(f"{ETICHETTA_PILOTA}/{b}", note=f"{c} seme {s} braccio {b} PILOTA",
                         radice=out / "registro")
    x = {"contesto": c, "partizione": p, "seme": s, "braccio": b, "pilota": True}
    reg.configurazione({**cfg, **x})
    t_in = time.time()
    gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE[p]),
           "inizializzazione": np.random.default_rng(s)}
    addestra_una(Esec(c, p, cfg["variante"]), reg, cfg, gen, out)
    reg.completa()
    if not ck.exists():
        raise RuntimeError(f"punto di controllo atteso assente: {ck}")
    r = {**x, "secondi": time.time() - t_in, "fili": fili,
         "istante": datetime.now(timezone.utc).isoformat()}
    scrivi_atomico(marcatore(ck), json.dumps(r, indent=2))
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description="E6 parte B (PEMS08)")
    ap.add_argument("--fase", choices=("pilota",), required=True)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    print("=" * 80); print(f"E6 — PEMS08, fase {a.fase}"); print("=" * 80)
    for f in ("pesi_pems08/pesi_PEMS08_p0_p0.json", "maschere/maschere_PEMS08_p0.npz",
              "canonico"):
        if not (a.out / f).exists():
            raise SystemExit(f"prerequisito assente: {a.out / f}")
    if a.fase == "pilota":
        cfg = cfg_e6("C", CONTESTI[0], 0, SEME_PILOTA, a.out, ETICHETTA_PILOTA)
        print(f"  un addestramento: C su {CONTESTI[0]} p0 seme {SEME_PILOTA}, "
              f"fine_periodo {T0_PROVA}, pesi {cfg['dir_pesi']}, epoche {cfg['epoche']}, "
              f"fili {a.fili}; cartella {a.out / ETICHETTA_PILOTA}")
        print("  il punto di controllo NON si guarda: serve solo il tempo")
        if a.piano:
            return 0
        r = _pilota(a.out, a.fili)
        print(f"\n  COSTO PILOTA: {r['secondi']:.0f} s = {r['secondi'] / 60:.1f} min "
              f"(processo unico, {r['fili']} fili)")
        (a.out / "e6_pilota.json").write_text(json.dumps(r, indent=2))
        print(f"  salvato in {a.out / 'e6_pilota.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
