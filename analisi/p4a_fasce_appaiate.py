#!/usr/bin/env python3
"""
Paper 4, Parte A, punto 5 della revisione interna (8/11/2026): sensori M30 presenti in piu' fasce di distanza
e confronto appaiato sugli stessi sensori. Sola lettura; importa `analisi/validazione_colocalizzata.py` del
deliverable (f1f6340779b612d5) senza modifiche e ne replica il filtro di `sez_accoppiamento` (r. 170-183): per ogni
sensore i e fascia [lo, hi), vicino j piu' prossimo a 33 m fra quelli nella fascia; celle con r_pr_i finito,
r_tr_j finito, sp_j > 0, oc_i >= 5; la coppia vale se ha > 50 celle. Nessun numero del paper cambia.

Scrive: sensori per fascia, intersezioni fra fasce (coppie e tutte e quattro), e per i sensori comuni a ogni coppia
di fasce la correlazione di rango, l'AUC (rosso = r_tr_j < 0,4) e il Gini di ciascuna fascia, calcolati sulle
sole celle di quei sensori, accanto ai valori sull'insieme completo.

    python3 analisi/p4a_fasce_appaiate.py --gomo ../OR3/data_collection/go-mo/gomo
"""
import argparse
import hashlib
import importlib.util
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

RADICE = Path(__file__).resolve().parents[1]
FASCE = [(0, 20), (19, 72), (20, 60), (60, 200)]


def _sha(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gomo", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=RADICE / "protocol" / "paper4" / "fase2" / "FASCE_APPAIATE.md")
    a = ap.parse_args()
    p = RADICE / "analisi" / "validazione_colocalizzata.py"
    spec = importlib.util.spec_from_file_location("vc", p); vc = importlib.util.module_from_spec(spec); spec.loader.exec_module(vc)
    vc.GOMO = a.gomo
    d = vc.carica_m30()
    s = pd.read_csv(a.gomo / "traffic_sensors.csv", dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
    s["id"] = s["id"].astype(str)
    XY = s.set_index("id").reindex(d["sub"])[["utm_x", "utm_y"]].to_numpy()
    D = np.sqrt(((XY[:, None, :] - XY[None, :, :]) ** 2).sum(-1)); np.fill_diagonal(D, np.inf)
    S = len(d["sub"])
    coppie = {}            # fascia -> {i: (A_i, B_i, dist)}
    for lo, hi in FASCE:
        cp = {}
        for i in range(S):
            c = np.where((D[i] >= lo) & (D[i] < hi))[0]
            if not len(c):
                continue
            j = c[np.argmin(np.abs(D[i][c] - 33.0))]
            m = (np.isfinite(d["r_pr"][:, i]) & np.isfinite(d["r_tr"][:, j]) & (d["sp"][:, j] > 0) & (d["oc"][:, i] >= vc.OCC_VUOTA))
            if m.sum() > 50:
                cp[i] = (d["r_pr"][m, i], d["r_tr"][m, j], D[i, j])
        coppie[(lo, hi)] = cp

    def metriche(cp, ins):
        A = np.concatenate([cp[i][0] for i in ins]); B = np.concatenate([cp[i][1] for i in ins])
        y = (B < vc.SOGLIA_ROSSO).astype(int)
        auc = roc_auc_score(y, -A) if 50 < y.sum() < len(y) - 50 else np.nan
        return len(ins), float(np.median([cp[i][2] for i in ins])), int(len(A)), spearmanr(A, B).statistic, auc, 2 * auc - 1

    et = lambda f: f"{f[0]}-{f[1]} m"
    L = ["# Parte A, punto 5 — sensori M30 presenti in piu' fasce di distanza e confronto appaiato", "",
         f"Generato da `analisi/p4a_fasce_appaiate.py` il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} con il modulo "
         f"congelato `analisi/validazione_colocalizzata.py` (`{_sha(p)}`), dati `{a.gomo}`; filtro di `sez_accoppiamento` "
         "(r. 170-183) replicato. Sola lettura; nessun numero del paper cambia.", "",
         f"Sensori allineati: {S}. Un sensore «e' in una fascia» se ha un vicino in quella fascia e la coppia supera le 50 celle.", "",
         "## Sensori per fascia e intersezioni", "", "| fascia | sensori | dist. mediana | celle | ρ | AUC | Gini |", "|---|---:|---:|---:|---:|---:|---:|"]
    for f in FASCE:
        n, dm, nc, rho, auc, g = metriche(coppie[f], list(coppie[f]))
        L.append(f"| {et(f)} | {n} | {dm:.0f} m | {nc:,} | {rho:+.4f} | {auc:.4f} | {g:.4f} |")
    L += ["", "| fasce | sensori comuni | solo nella prima | solo nella seconda |", "|---|---:|---:|---:|"]
    for f1, f2 in combinations(FASCE, 2):
        s1, s2 = set(coppie[f1]), set(coppie[f2])
        L.append(f"| {et(f1)} ∩ {et(f2)} | {len(s1 & s2)} | {len(s1 - s2)} | {len(s2 - s1)} |")
    tutti = set.intersection(*(set(coppie[f]) for f in FASCE))
    estremi = set(coppie[(0, 20)]) & set(coppie[(60, 200)])
    unione = set.union(*(set(coppie[f]) for f in FASCE))
    L += ["", f"Sensori in **tutte e quattro** le fasce: {len(tutti)}; in **0-20 e 60-200 m** (la domanda del revisore): {len(estremi)}; "
          f"in almeno una fascia: {len(unione)} su {S}.", "",
          "## Confronto appaiato: stesse metriche sui soli sensori comuni a ogni coppia di fasce", "",
          "Per ogni coppia di fasce, le metriche di ciascuna fascia ricalcolate sulle celle dei soli sensori comuni, cosi' che la "
          "differenza fra le due fasce non dipenda dalla composizione dei sensori.", "",
          "| fasce | sensori comuni | fascia | dist. mediana | celle | ρ | AUC | Gini | ΔGini (seconda − prima) |", "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for f1, f2 in combinations(FASCE, 2):
        com = sorted(set(coppie[f1]) & set(coppie[f2]))
        if len(com) < 20:
            L.append(f"| {et(f1)} ∩ {et(f2)} | {len(com)} | — | | | | | | meno di 20 sensori comuni |"); continue
        m1, m2 = metriche(coppie[f1], com), metriche(coppie[f2], com)
        for k, (f, m) in enumerate(((f1, m1), (f2, m2))):
            L.append(f"| {et(f1)} ∩ {et(f2)} | {len(com)} | {et(f)} | {m[1]:.0f} m | {m[2]:,} | {m[3]:+.4f} | {m[4]:.4f} | {m[5]:.4f} | "
                     + (f"{m2[5] - m1[5]:+.4f}" if k == 1 else ""))
    if len(tutti) >= 20:
        L += ["", f"### Sui {len(tutti)} sensori presenti in tutte e quattro le fasce", "",
              "| fascia | dist. mediana | celle | ρ | AUC | Gini |", "|---|---:|---:|---:|---:|---:|"]
        for f in FASCE:
            m = metriche(coppie[f], sorted(tutti))
            L.append(f"| {et(f)} | {m[1]:.0f} m | {m[2]:,} | {m[3]:+.4f} | {m[4]:.4f} | {m[5]:.4f} |")
    L.append("")
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text("\n".join(L))
    print("\n".join(L)); print(f"  -> {a.out} ({_sha(a.out)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
