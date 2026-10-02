#!/usr/bin/env python3
"""
Analisi aggiunta il 2/10, non pre-registrata — la selezione a peso uguale.
===========================================================================
R-mon seleziona sulla media PESATA PER CELLE fra rete iniziale e nodi nuovi
(ultime 6 ore): i nodi nuovi pesano lo 0,3 % e la scelta coincide con quella
di R-orig in 107 celle su 108. Il revisore chiede la riselezione a PESO UGUALE
(0,5 rete iniziale + 0,5 nodi nuovi).

**Il ciclo salva soltanto il punto migliore, non gli undici.** Quindi dai file
si puo' dire soltanto, per ciascuna delle 108 esecuzioni, QUALE punto la regola
a peso uguale avrebbe scelto e se e' diverso da quello salvato: lo si legge
dalle curve nel manifesto (V-full e V-nuovi-6h a ogni punto). Valutarlo sul
test richiederebbe di riaddestrare quelle celle salvando tutti i punti.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/riselezione_rmon.py --out results/evoluzione/riselezione_rmon.json
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radice", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    righe = []
    for f in sorted((a.radice / "registro").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if d.get("esperimento") != "inserimento_griglia/R-mon" or \
                d.get("run_status") != "completato":
            continue
        cfg = d.get("resolved_configuration") or {}
        art = d.get("protocollo_principale") or {}
        curve = art.get("curve") or []
        if not curve or "V-nuovi-6h" not in curve[0]:
            continue
        u = [r["aggiornamento"] for r in curve]
        vf = np.array([r["V-full"] for r in curve])
        vn = np.array([r["V-nuovi-6h"] for r in curve])
        vs = np.array([r["V-selezione"] for r in curve])
        # a parita', il PRECEDENTE: argmin restituisce il primo minimo
        u_salvato = u[int(np.argmin(vs))]
        u_uguale = u[int(np.argmin(0.5 * vf + 0.5 * vn))]
        u_solo_nuovi = u[int(np.argmin(vn))]
        righe.append({"istante": d.get("timestamp_avvio", ""),
                      "contesto": cfg.get("contesto"), "partizione": cfg.get("partizione"),
                      "seme": cfg.get("seme"), "u_salvato": u_salvato,
                      "u_peso_uguale": u_uguale, "u_solo_nuovi": u_solo_nuovi,
                      "diverso": u_uguale != u_salvato,
                      "V_full_salvato": float(vf[u.index(u_salvato)]),
                      "V_full_peso_uguale": float(vf[u.index(u_uguale)]),
                      "V_nuovi_salvato": float(vn[u.index(u_salvato)]),
                      "V_nuovi_peso_uguale": float(vn[u.index(u_uguale)])})
    if not righe:
        print("  nessun manifesto R-mon con la curva a due componenti")
        return 1
    # UNA RIGA PER CELLA: le rimisure isolate hanno un manifesto proprio con
    # la stessa numerica; si tiene l'ultimo
    ultimo = {}
    for r in righe:
        k = (r["contesto"], r["partizione"], r["seme"])
        if k not in ultimo or r["istante"] > ultimo[k]["istante"]:
            ultimo[k] = r
    righe = sorted(ultimo.values(), key=lambda r: (r["contesto"], r["partizione"], r["seme"]))
    n = len(righe); div = [r for r in righe if r["diverso"]]
    print("=" * 84)
    print("R-mon — riselezione a PESO UGUALE, dalle curve (solo conteggio)")
    print("=" * 84)
    print(f"  esecuzioni: {n}; la regola a peso uguale sceglie un punto DIVERSO "
          f"in {len(div)} ({len(div) / n:.0%})")
    for c in ("Madrid", "Londra", "Melbourne"):
        rc = [r for r in righe if r["contesto"] == c]
        dc = [r for r in rc if r["diverso"]]
        print(f"     {c:11s} {len(dc):3d} su {len(rc)}")
    print(f"  punti scelti (salvato -> peso uguale), i piu' frequenti: "
          + ", ".join(f"u{k[0]}->u{k[1]} x{v}" for k, v in Counter(
              (r["u_salvato"], r["u_peso_uguale"]) for r in div).most_common(6)))
    if div:
        d_full = np.array([r["V_full_peso_uguale"] - r["V_full_salvato"] for r in div])
        d_nuo = np.array([r["V_nuovi_peso_uguale"] - r["V_nuovi_salvato"] for r in div])
        print(f"  nelle celle diverse, il punto a peso uguale costa sulla rete "
              f"iniziale (V-full) in media {d_full.mean():+.5f} e guadagna sui "
              f"nodi nuovi (V-nuovi-6h) {d_nuo.mean():+.5f}")
    print("\n  **solo conteggio**: il ciclo salva il solo punto migliore; per "
          "valutare sul test il punto a peso uguale vanno riaddestrate le celle "
          "diverse salvando tutti i punti (deterministico, ~40 min l'una).")
    if a.out:
        a.out.write_text(json.dumps({"esecuzioni": n, "diverse": len(div),
                                     "righe": righe}, indent=2))
        print(f"  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
