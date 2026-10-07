#!/usr/bin/env python3
"""
E3-bis — R-orig con una settimana di dati contro F'(1 settimana), C e A.
=========================================================================
Pre-registrato in protocol/E5.md (sezione E3-bis). Tutto sulle **origini
comuni** (eta' > 1 settimana): sono esattamente le origini dopo t1 = t0 + 672
su cui R-orig(1 sett.) e' stato valutato e ricostruito (`predizioni_fase3_672`).

Sorgenti (nessun modello si esegue):
  R-orig(1 sett.)   predizioni_fase3_672/R-orig_*.npz  (A_per_nodo, B_per_nodo)
  R-orig(24 h)      predizioni_fase3/R-orig_*.npz, aggregato sulle origini > t0+672
  A, C              predizioni_fase3/{A,C}_*.npz, idem
  F'(1 sett.), F0'  aggregati di E4 (predizioni_e4/prova_*.npz, terza fascia)

Verifiche: le origini di R-orig(1 sett.) coincidono con la terza fascia di E4
(stesso insieme); C aggregato dalle predizioni di E3 coincide con il C di E4
entro 1e-9. Ricampionamento congiunto (partizioni x semi x nodi), 4000
repliche, seme 20261009. Equivalenza con margine ±3 % di wC (come in E3).

Scrive results/evoluzione/e3bis_risultati.json.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_e3bis.py
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e4 import (  # noqa: E402
    B_BOOT, CITTA, FASCE_ETA, _aggregati, _boot, _carica_celle, _wce)

SEME = 20261009
TOLLERANZA = 1e-9
MARGINE = 0.03


def _aggrega(f: Path, pesi, t0: int):
    """A, B (K,H) sulle origini > t0 + 672, dalle predizioni complete."""
    with np.load(f, allow_pickle=True) as z:
        per = z["origini"].astype("int64")
        m = per - t0 > FASCE_ETA[1]
        A, Bm = _aggregati(z["prob"], z["y"], z["m"], pesi, [m])
        return A[0], Bm[0], per[m], z["nodi"].astype("int64")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    from evoluzione.analisi.pesi import carica as carica_pesi
    print("=" * 84)
    print("E3-bis — R-orig(1 settimana) contro F'(1 settimana), C e A, origini comuni")
    print("=" * 84)
    ctrl = json.loads((a.out / "predizioni_fase3_672" / "controllo_R-orig.json").read_text())
    if ctrl["anomalie"] or len(ctrl["esecuzioni"]) != 108:
        raise RuntimeError(f"ricostruzione di R-orig(1 sett.): {len(ctrl['esecuzioni'])} esecuzioni, "
                           f"anomalie {ctrl['anomalie'][:3]}")
    celle = _carica_celle(a.out, "prova")
    rng = np.random.default_rng(SEME)
    R = {"confronti": {}, "verifica_C": {}, "origini_comuni": {}, "margine": {}, "ricostruzione": {
        "esecuzioni": len(ctrl["esecuzioni"]), "anomalie": len(ctrl["anomalie"]),
        "scarto_max": max(e["scarto_relativo"] for e in ctrl["esecuzioni"])}}
    for c in CITTA:
        kk = sorted(k for k in celle if k[0] == c)
        if len(kk) != 36:
            raise RuntimeError(f"{c}: {len(kk)} celle, attese 36")
        cc, sc_max = {}, 0.0
        for k in kk:
            _, p, s = k
            z = celle[k]
            pesi = np.asarray(carica_pesi(a.out / "pesi_griglia", c, p).vettore(), dtype="float64")
            t0 = int(z["t0"])
            # R-orig(1 sett.): le sue origini sono gia' tutte > t0 + 672
            with np.load(a.out / "predizioni_fase3_672" / f"R-orig_{c}_p{p}_s{s}.npz", allow_pickle=True) as zr:
                per_r = zr["origini"].astype("int64")
                A_r, B_r = zr["A_per_nodo"], zr["B_per_nodo"]
                nodi_r = zr["nodi"].astype("int64")
            per_e4 = z["origini"].astype("int64")[z["eta"].astype("int64") > FASCE_ETA[1]]
            if not (np.array_equal(per_r, per_e4) and np.array_equal(nodi_r, z["nodi"].astype("int64"))):
                raise RuntimeError(f"{c} p{p} s{s}: origini o nodi di R-orig(1 sett.) diversi dalla "
                                   f"terza fascia di E4 ({len(per_r)} contro {len(per_e4)})")
            A_r24, B_r24, _, _ = _aggrega(a.out / "predizioni_fase3" / f"R-orig_{c}_p{p}_s{s}.npz", pesi, t0)
            A_A, B_A, _, _ = _aggrega(a.out / "predizioni_fase3" / f"A_{c}_p{p}_s{s}.npz", pesi, t0)
            A_C, B_C, _, _ = _aggrega(a.out / "predizioni_fase3" / f"C_{c}_p{p}_s{s}.npz", pesi, t0)
            rel = abs(_wce(A_C, B_C) - _wce(z["A_C"][2], z["B_C"][2])) / abs(_wce(z["A_C"][2], z["B_C"][2]))
            sc_max = max(sc_max, rel)
            if rel > TOLLERANZA:
                raise RuntimeError(f"{c} p{p} s{s}: C ricalcolato diverso da E4 ({rel:.1e})")
            cc[k] = {"celle_valide": z["celle_valide"],
                     "A_Rw": A_r[None], "B_Rw": B_r[None], "A_R24": A_r24[None], "B_R24": B_r24[None],
                     "A_A": A_A[None], "B_A": B_A[None], "A_C": A_C[None], "B_C": B_C[None],
                     "A_Fpw": z["A_Fp_672"][2][None], "B_Fpw": z["B_Fp_672"][2][None],
                     "A_F0p": z["A_F0p"][2][None], "B_F0p": z["B_F0p"][2][None]}
        R["verifica_C"][c] = sc_max
        R["origini_comuni"][c] = int(len(per_r))
        wC = float(np.mean([_wce(cc[k]["A_C"].sum(0), cc[k]["B_C"].sum(0)) for k in kk]))
        R["margine"][c] = MARGINE * wC

        def diff(n1, n2):
            def f(z, idx):
                def AB(n):
                    A, Bm = z[f"A_{n}"].sum(0), z[f"B_{n}"].sum(0)
                    return (A, Bm) if idx is None else (A[idx], Bm[idx])
                return _wce(*AB(n1)) - _wce(*AB(n2))
            return f

        print(f"\n{c}: {len(kk)} celle, {len(per_r)} origini comuni, verifica C {sc_max:.1e}, "
              f"margine ±{MARGINE * wC:.4f}")
        for n1, n2, et in (("Rw", "Fpw", "R-orig(1 sett.) - F'(1 sett.)"), ("Rw", "C", "R-orig(1 sett.) - C"),
                           ("Rw", "A", "R-orig(1 sett.) - A"), ("Rw", "R24", "R-orig(1 sett.) - R-orig(24 h)"),
                           ("Fpw", "C", "F'(1 sett.) - C"), ("A", "C", "A - C")):
            r = _boot(cc, diff(n1, n2), rng)
            r["equivalente_3pc"] = bool(-MARGINE * wC <= r["ic_con_nodi"][0] and r["ic_con_nodi"][1] <= MARGINE * wC)
            R["confronti"][f"{c}/{n1}-{n2}"] = {**r, "etichetta": et}
            print(f"  {et:32s} {r['media']:+.5f} [{r['ic_con_nodi'][0]:+.5f}, {r['ic_con_nodi'][1]:+.5f}]"
                  + ("   include lo zero" if r["include_zero"] else "")
                  + ("   equivalente ±3%" if r["equivalente_3pc"] else ""))
    R["repliche"] = B_BOOT; R["seme_bootstrap"] = SEME; R["istante"] = datetime.now(timezone.utc).isoformat()
    f = a.out / "e3bis_risultati.json"
    f.write_text(json.dumps(R, indent=2, ensure_ascii=False))
    n_eq = sum(R["confronti"][f"{c}/Rw-Fpw"]["equivalente_3pc"] for c in CITTA)
    n_zero = sum(R["confronti"][f"{c}/Rw-Fpw"]["include_zero"] for c in CITTA)
    print("\n" + "=" * 84)
    print(f"R-orig(1 sett.) - F'(1 sett.): include lo zero in {n_zero}/3, equivalente entro ±3 % in {n_eq}/3")
    print(f"  salvato in {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
