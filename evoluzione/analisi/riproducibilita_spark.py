#!/usr/bin/env python3
"""
Riproducibilita' fra architetture: di quanto il ricalcolo su QUESTA macchina differisce
dagli aggregati salvati (calcolati sul Mac dell'autore), cella per cella di E2.
=========================================================================================
Sola lettura. Per ciascuna delle 108 celle di E2 (`predizioni_e2/F0p_*.npz`, probabilita'
in float32): ricalcola `A_per_nodo` con `aggregati_per_nodo` e misura lo scarto relativo
per elemento rispetto a quello salvato; ricalcola la wCE di cella dagli aggregati salvati
e da quelli ricalcolati; verifica la coerenza interna (wCE dalle celle contro wCE dagli
aggregati, stessa macchina). Scrive `results/evoluzione/riproducibilita_spark.json`
(macchina, numpy, torch, tutte le celle, massimi) con impronta: e' la fonte della frase
di riproducibilita' del paper.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/riproducibilita_spark.py
"""
import argparse
import glob
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.pesi import carica as carica_pesi  # noqa: E402
from evoluzione.esperimenti.ricostruisci_predizioni import (  # noqa: E402
    aggregati_per_nodo, wce_da_predizioni)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    import torch
    celle, dt = [], None
    for f in sorted(glob.glob(str(a.out / "predizioni_e2" / "F0p_*_p*_s*.npz"))):
        n = Path(f).stem.split("_")
        c, p, s = n[1], int(n[2][1:]), int(n[3][1:])
        z = np.load(f, allow_pickle=True)
        dt = str(z["prob"].dtype)
        pesi = np.asarray(carica_pesi(a.out / "pesi_griglia", c, p).vettore(), dtype="float64")
        A, Bm, _ = aggregati_per_nodo(z["prob"], z["y"], z["m"], pesi)
        As = z["A_per_nodo"]
        rel = np.abs(A - As) / np.maximum(np.abs(As), 1e-300)
        den = Bm.sum(0)
        ws = float(np.nanmean(np.where(den > 0, As.sum(0) / np.maximum(den, 1e-12), np.nan)))
        wr = float(np.nanmean(np.where(den > 0, A.sum(0) / np.maximum(den, 1e-12), np.nan)))
        w1, _ = wce_da_predizioni(z["prob"], z["y"], z["m"], pesi)
        celle.append({"contesto": c, "partizione": p, "seme": s, "file": Path(f).name,
                      "scarto_rel_max_elemento": float(rel.max()),
                      "quota_elementi_oltre_1e-12": float(np.mean(rel > 1e-12)),
                      "wce_da_aggregati_salvati": ws, "wce_da_aggregati_ricalcolati": wr,
                      "scarto_rel_wce": abs(wr - ws) / abs(ws),
                      "coerenza_interna_abs": abs(float(w1) - wr)})
    if not celle:
        raise SystemExit("nessuna cella di E2")
    doc = {"istante": datetime.now(timezone.utc).isoformat(),
           "macchina": {"nodo": platform.node(), "piattaforma": platform.platform(), "arch": platform.machine(),
                        "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__},
           "riferimento": "aggregati salvati: Mac dell'autore (Apple M3 Max, macOS, numpy 2.5.1)",
           "dtype_probabilita": dt, "celle": len(celle),
           "massimi": {"scarto_rel_max_elemento": max(x["scarto_rel_max_elemento"] for x in celle),
                       "scarto_rel_max_wce_cella": max(x["scarto_rel_wce"] for x in celle),
                       "coerenza_interna_max": max(x["coerenza_interna_abs"] for x in celle),
                       "celle_con_elemento_oltre_1e-12": sum(x["scarto_rel_max_elemento"] > 1e-12 for x in celle),
                       "celle_con_wce_oltre_1e-9": sum(x["scarto_rel_wce"] > 1e-9 for x in celle)},
           "per_cella": celle}
    fj = a.out / "riproducibilita_spark.json"
    fj.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    imp = hashlib.sha256(fj.read_bytes()).hexdigest()[:16]
    m = doc["massimi"]
    print(f"  {doc['macchina']['nodo']} {doc['macchina']['arch']} numpy {np.__version__}; {len(celle)} celle, probabilita' {dt}")
    print(f"  scarto relativo massimo per elemento {m['scarto_rel_max_elemento']:.2e} "
          f"({m['celle_con_elemento_oltre_1e-12']} celle oltre 1e-12); sulla wCE di cella {m['scarto_rel_max_wce_cella']:.2e} "
          f"({m['celle_con_wce_oltre_1e-9']} celle oltre 1e-9); coerenza interna {m['coerenza_interna_max']:.1e}")
    print(f"  salvato in {fj} (impronta {imp})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
