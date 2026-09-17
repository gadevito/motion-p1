#!/usr/bin/env python3
"""
Effetto della regola di strada vuota sui sei contesti (§3.2.4, Tabelle 5 e 6).
==============================================================================
Ricalcola, senza addestramenti:

  Tabella 5 - celle valide, celle imputate a r = 1,0 dalla regola, frazione,
              e l'indicatore esatto basato sull'occupazione (occ < 5%).
              Lo scarto di ~0,05 punti fra i due criteri corrisponde ai casi
              in cui la velocita' ricostruita coincide esattamente con il
              riferimento di flusso libero.

  Tabella 6 - quota di verde, quota di verde imputato e MASSA METRICA, cioe'
              la frazione di entropia pesata prodotta dalle celle il cui
              bersaglio e' deterministico dato l'ingresso. La massa metrica
              e' la somma dei pesi di classe sulle celle imputate divisa per
              la somma dei pesi su tutte le celle valide: e' esattamente il
              denominatore della wCE ristretto a quel sottoinsieme, quindi
              non richiede alcun modello.

  Inoltre la dispersione dell'imputazione per sensore e per ora del giorno
  (§3.2.4, ultimi tre capoversi): mediana per sensore, sensori sopra il 95%,
  massimo notturno e minimo delle 18:00.

I pesi di classe sono ricalcolati con la convenzione Traffic4cast,
w_k = n / (3 * n_k), sulle frequenze del solo periodo di ADDESTRAMENTO
(primo 70%), come nei modelli.

Uso (dalla radice OR3/):

    poetry run python analisi/imputazione_gomo.py
    poetry run python analisi/imputazione_gomo.py --occ-empty 5.0
"""
from pathlib import Path
import argparse

import numpy as np
import pandas as pd

BASE = Path("data_collection")
GOMO = BASE / "go-mo" / "gomo"
T4C = BASE / "traffic4cast"

SPIRE = {
    "d8/2024":  GOMO / "targets_2024_urb_d8.npz",
    "d15/2024": GOMO / "targets_2024_urb_d15.npz",
    "d8/2023":  GOMO / "targets_2023_urb_d8.npz",
    "d8/2021":  GOMO / "targets_2021_urb_d8.npz",   # perimetro della validazione incrociata
}
CITTA = {
    "Madrid":    T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "Londra":    T4C / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "Melbourne": T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
}
ORIZZONTE_MAX = 8   # passi: 120 minuti, come nella pipeline


def pesi_addestramento(C):
    """w_k = n / (3 n_k) sulle frequenze del solo periodo di addestramento."""
    T = C.shape[0]
    tr = C[: int((T - ORIZZONTE_MAX) * 0.7)]
    fr = np.array([(tr == k).sum() for k in (1, 2, 3)], dtype=float)
    return (fr.sum() / (np.maximum(fr, 1) * 3)).astype("float64")


def maschere(z, occ_empty):
    """Restituisce (valide, imputate_da_r, imputate_da_occ)."""
    C = z["congestion_emp"]
    r = z["r_emp"].astype("float32")
    valide = C > 0
    imp_r = valide & np.isfinite(r) & (r == 1.0)
    if "occupancy" in z.files:
        occ = z["occupancy"].astype("float32")
        imp_o = valide & np.isfinite(occ) & (occ < occ_empty)
    else:
        imp_o = None
    return valide, imp_r, imp_o


def main() -> int:
    ap = argparse.ArgumentParser(description="statistiche della regola di strada vuota")
    ap.add_argument("--occ-empty", type=float, default=5.0,
                    help="soglia di occupazione della regola (default 5.0, come in 4_gomo_urb.py)")
    args = ap.parse_args()

    print("=" * 92)
    print("TABELLA 5 - quota di celle imposte dalla regola di strada vuota (contesti a spire)")
    print("=" * 92)
    print(f"{'contesto':10s} {'celle valide':>14} {'imputate a 1,0':>16} {'frazione':>10} "
          f"{'occ < 5%':>10}")
    for nome, p in SPIRE.items():
        if not p.exists():
            print(f"{nome:10s} target non trovato: {p}")
            continue
        z = np.load(p, allow_pickle=True)
        valide, imp_r, imp_o = maschere(z, args.occ_empty)
        q_o = f"{100 * imp_o.sum() / valide.sum():.2f}%" if imp_o is not None else "n/d"
        print(f"{nome:10s} {int(valide.sum()):14,} {int(imp_r.sum()):16,} "
              f"{100 * imp_r.sum() / valide.sum():9.2f}% {q_o:>10}")

    print()
    print("=" * 92)
    print("CONTROLLO - le celle imputate hanno tutte etichetta verde?")
    print("=" * 92)
    for nome, p in SPIRE.items():
        if not p.exists():
            continue
        z = np.load(p, allow_pickle=True)
        C = z["congestion_emp"]
        _, imp_r, _ = maschere(z, args.occ_empty)
        n = [int((C[imp_r] == k).sum()) for k in (1, 2, 3)]
        stato = "OK" if n[1] == 0 and n[2] == 0 else "ANOMALIA"
        print(f"{nome:10s} verdi {n[0]:12,}  gialle {n[1]:8,}  ROSSE {n[2]:8,}  -> {stato}")

    print()
    print("=" * 92)
    print("TABELLA 6 - verde imputato e massa metrica, sui sei contesti")
    print("=" * 92)
    print(f"{'contesto':10s} {'quota verde':>12} {'verde imputato':>16} "
          f"{'massa metrica':>15}")
    tutti = [(n, p) for n, p in SPIRE.items() if n != "d8/2021"] + list(CITTA.items())
    for nome, p in tutti:
        if not p.exists():
            print(f"{nome:10s} target non trovato")
            continue
        z = np.load(p, allow_pickle=True)
        C = z["congestion_emp"]
        valide, imp_r, _ = maschere(z, args.occ_empty)
        w = pesi_addestramento(C)
        y = C[valide] - 1
        peso_tot = w[y].sum()
        y_imp = C[imp_r] - 1
        peso_imp = w[y_imp].sum()
        verdi = (C == 1) & valide
        print(f"{nome:10s} {100 * verdi.sum() / valide.sum():11.2f}% "
              f"{100 * imp_r.sum() / max(verdi.sum(), 1):15.1f}% "
              f"{100 * peso_imp / peso_tot:14.1f}%")

    print()
    print("=" * 92)
    print("DISPERSIONE DELL'IMPUTAZIONE (contesti a spire)")
    print("=" * 92)
    for nome, p in SPIRE.items():
        if nome == "d8/2021" or not p.exists():
            continue
        z = np.load(p, allow_pickle=True)
        C = z["congestion_emp"]
        valide, imp_r, _ = maschere(z, args.occ_empty)
        per_sensore = imp_r.sum(0) / np.maximum(valide.sum(0), 1)
        ts = pd.to_datetime(z["timestamps"])
        ore = ts.hour.to_numpy()
        per_ora = np.array([
            imp_r[ore == h].sum() / max(valide[ore == h].sum(), 1) for h in range(24)
        ])
        h_max, h_min = int(per_ora.argmax()), int(per_ora.argmin())
        print(f"{nome:10s} mediana per sensore {100 * np.median(per_sensore):5.1f}%  |  "
              f"sensori > 95%: {int((per_sensore > 0.95).sum()):3d}/{C.shape[1]:3d}  |  "
              f"max ore {h_max:02d}:00 {100 * per_ora[h_max]:5.1f}%  "
              f"min ore {h_min:02d}:00 {100 * per_ora[h_min]:5.1f}%  "
              f"(escursione {100 * (per_ora[h_max] - per_ora[h_min]):4.1f} punti)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
