#!/usr/bin/env python3
"""
Descrittori osservabili di nodo per l'esperimento sull'identita' (§8.6.1).
==========================================================================
Genera i file `.npy` (K x d) che `gomo_classify.py --node-desc` consuma al
posto dell'embedding di identita'.

REGOLA FONDAMENTALE: tutte le statistiche sono calcolate SUL SOLO PERIODO DI
ADDESTRAMENTO (primo 70%), come ogni altra statistica derivata dai dati (§3.5).
Calcolarle sull'intero periodo farebbe filtrare informazione del test nel
modello e invaliderebbe l'esperimento.

L'aggancio sensore-grafo replica quello dei modelli (cKDTree a 20 m), cosi' che
la popolazione del descrittore coincida con quella modellata: 828 / 774 / 587
sui contesti primari, nessuna perdita sui contesti a spire.

DUE FAMIGLIE DI DESCRITTORE.

  base (16 statistiche) - media, dispersione, cinque quantili, autocorrelazione
    a ritardo uno, frazione di salite e discese, dispersione delle differenze,
    frequenza per classe, ora del minimo del profilo, dispersione del profilo
    orario.

  esteso (45 statistiche) - le sedici precedenti piu' venti per fascia oraria
    (cinque fasce x media, dispersione, decimo e novantesimo percentile), sei
    per feriale/festivo, e tre fra asimmetria, curtosi e persistenza a un'ora.

AVVERTENZA DA DICHIARARE. La famiglia estesa e' stata scelta DOPO aver visto
l'esito a sedici statistiche, sugli stessi insiemi di test. Il rischio e'
modesto ma la selezione va dichiarata, come per le configurazioni aggiunte
dell'esperimento sul meteo.

Uso (dalla radice OR3/):

    poetry run python analisi/genera_descrittori.py --out-dir descrittori
    poetry run python analisi/genera_descrittori.py --famiglia esteso
"""
from pathlib import Path
import argparse
import pickle

import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

BASE = Path("data_collection")
GOMO = BASE / "go-mo" / "gomo"
T4C = BASE / "traffic4cast"

CONTESTI = {
    "d8_2024":  (GOMO / "targets_2024_urb_d8.npz",  GOMO / "routes-graph.pkl",
                 GOMO / "traffic_sensors.csv"),
    "d15_2024": (GOMO / "targets_2024_urb_d15.npz", GOMO / "routes-graph.pkl",
                 GOMO / "traffic_sensors.csv"),
    "d8_2023":  (GOMO / "targets_2023_urb_d8.npz",  GOMO / "routes-graph.pkl",
                 GOMO / "traffic_sensors.csv"),
    "t4cmad":   (T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
                 T4C / "MADRID_2022/gomo_fmt/t4cmad_routes-graph.pkl",
                 T4C / "MADRID_2022/gomo_fmt/t4cmad_sensors.csv"),
    "t4clon":   (T4C / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
                 T4C / "LONDON_2022/gomo_fmt/t4cmad_routes-graph.pkl",
                 T4C / "LONDON_2022/gomo_fmt/t4cmad_sensors.csv"),
    "t4cmel":   (T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
                 T4C / "MELBOURNE_2022/gomo_fmt/t4cmel_routes-graph.pkl",
                 T4C / "MELBOURNE_2022/gomo_fmt/t4cmel_sensors.csv"),
}
FASCE = [(0, 6), (6, 10), (10, 16), (16, 20), (20, 24)]
ORIZZONTE_MAX = 8
QUOTA_ADDESTRAMENTO = 0.7


def statistiche(v, cc, ore, gio, esteso: bool):
    ok = np.isfinite(v)
    f = [np.nanmean(v), np.nanstd(v)]
    f += list(np.nanquantile(v[ok], [0.05, 0.25, 0.5, 0.75, 0.95])) if ok.sum() else [0.] * 5
    d = np.diff(v[ok]) if ok.sum() > 1 else np.array([0.])
    f += [np.corrcoef(v[ok][:-1], v[ok][1:])[0, 1] if ok.sum() > 2 else 0.,
          float(np.mean(d < 0)), float(np.mean(d > 0)), float(np.std(d))]
    vv = cc > 0
    f += [float(np.mean(cc[vv] == k)) if vv.sum() else 0. for k in (1, 2, 3)]
    prof = np.array([np.nanmean(v[ore == h]) if (ore == h).any() else np.nan
                     for h in range(24)])
    f += [float(np.nanargmin(prof)) if np.isfinite(prof).any() else 0.,
          float(np.nanstd(prof))]                       # -> 16 statistiche
    if not esteso:
        return f
    for a, b in FASCE:
        m = (ore >= a) & (ore < b) & ok
        f += ([np.nanmean(v[m]), np.nanstd(v[m])]
              + list(np.nanquantile(v[m], [0.10, 0.90]))) if m.sum() > 3 else [0.] * 4
    for m in ((gio < 5) & ok, (gio >= 5) & ok):
        f += ([np.nanmean(v[m]), np.nanstd(v[m]),
               float(np.mean(cc[m] == 3)) if m.sum() else 0.]) if m.sum() > 3 else [0.] * 3
    if ok.sum() > 3:
        x = v[ok]
        mu, sd = x.mean(), x.std() + 1e-9
        f += [float(((x - mu) ** 3).mean() / sd ** 3),
              float(((x - mu) ** 4).mean() / sd ** 4),
              np.corrcoef(x[:-4], x[4:])[0, 1] if ok.sum() > 5 else 0.]
    else:
        f += [0., 0., 0.]
    return f                                            # -> 45 statistiche


def main() -> int:
    ap = argparse.ArgumentParser(description="descrittori osservabili di nodo")
    ap.add_argument("--out-dir", type=Path, default=Path("descrittori"))
    ap.add_argument("--famiglia", choices=["base", "esteso", "entrambe"],
                    default="entrambe")
    ap.add_argument("--contesti", nargs="*", default=list(CONTESTI))
    a = ap.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)

    famiglie = (["base", "esteso"] if a.famiglia == "entrambe" else [a.famiglia])
    for c in a.contesti:
        tp, gp, sp = CONTESTI[c]
        if not tp.exists():
            print(f"{c:10s} target non trovato: {tp}")
            continue
        z = np.load(tp, allow_pickle=True)
        sids = z["sensor_ids"].astype(str)
        r = z["r_emp"].astype("float32")
        C = z["congestion_emp"]
        ts = pd.to_datetime(z["timestamps"])

        rg = pickle.load(open(gp, "rb"))
        sens = pd.read_csv(sp, dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
        nodi = list(rg.nodes)
        if "utm_x" in rg.nodes[nodi[0]]:
            nxy = np.array([[rg.nodes[n]["utm_x"], rg.nodes[n]["utm_y"]] for n in nodi])
            d_, i_ = cKDTree(sens[["utm_x", "utm_y"]].to_numpy()).query(nxy, k=1)
            rg = nx.relabel_nodes(
                rg, {nodi[k]: sens["id"].to_numpy()[i_[k]]
                     for k in range(len(nodi)) if d_[k] <= 20}, copy=True)
        tenuti = [s for s in sids if s in rg.nodes]
        pos = {s: i for i, s in enumerate(sids)}
        ki = np.array([pos[s] for s in tenuti])
        r, C = r[:, ki], C[:, ki]

        T, K = r.shape
        tr = slice(0, int((T - ORIZZONTE_MAX) * QUOTA_ADDESTRAMENTO))
        R, CC = r[tr], C[tr]
        ore = ts.hour.to_numpy()[tr]
        gio = ts.dayofweek.to_numpy()[tr]

        for fam in famiglie:
            F = np.array([np.nan_to_num(np.array(
                statistiche(R[:, k], CC[:, k], ore, gio, fam == "esteso"), dtype="float64"))
                for k in range(K)])
            F = (F - F.mean(0)) / (F.std(0) + 1e-9)
            nulle = int((np.abs(F).sum(1) < 1e-6).sum())
            costanti = int((F.std(0) < 1e-6).sum())
            suffisso = "d16" if fam == "base" else "ext"
            fuori = a.out_dir / f"{c}_{suffisso}.npy"
            np.save(fuori, F.astype("float32"))
            print(f"{c:10s} {fam:7s} K={K:4d} -> {F.shape[1]:2d} statistiche  "
                  f"righe nulle {nulle:3d}  colonne costanti {costanti:2d}  "
                  f"NaN {int(np.isnan(F).sum()):3d}  -> {fuori}")

    print("\nControlli attesi: zero righe nulle, zero colonne costanti, zero NaN.")
    print("Una colonna costante significa che una statistica e' vuota per tutti i nodi")
    print("del contesto — con fasce orarie strette puo' accadere e va saputo.")
    print("\nLe statistiche sono calcolate sul SOLO periodo di addestramento (primo 70%).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
