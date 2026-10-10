#!/usr/bin/env python3
"""
Figura 2 della sezione 5.1: il costo di trasferimento e il token.
==================================================================
Due righe × quattro colonne (Madrid, Londra, Melbourne, PEMS08).
Sopra: F₀ − C e F₀′ − C in wCE con intervallo al 95 %, A − C come riferimento;
tutto da `e8_risultati.json` (ΔwCE ricalcolata dalle stesse celle e verificata
a 1e-6 contro E2/E4/E6). Sotto: curve richiamo–falsi allarmi di C, F₀, F₀′ sul
perimetro di tutte le origini dopo t₁ (`griglia_*` delle celle `curva_*`,
sommate su celle e nodi), soglie 0,05…0,95.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/figura2_51.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e8 import CONTESTI_E8, DIR_PRED, curva  # noqa: E402

GRUPPI = ("Madrid", "Londra", "Melbourne", "PEMS08")
BRACCI = (("F0-C", "F₀ − C", "#b86b00"), ("F0p-C", "F₀′ − C", "#1f77b4"))
CURVE = (("C", "C", "#444444", "-"), ("F0", "F₀", "#b86b00", ":"), ("F0p", "F₀′", "#1f77b4", "--"))
FA_MAX = 0.12


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--figure", type=Path, default=Path("figure"))
    a = ap.parse_args()
    RS = json.loads((a.out / "e8_risultati.json").read_text())
    somme = {}
    for nome, cost in CONTESTI_E8.items():
        if nome == "pems04":
            continue
        ctx = cost(a.out)
        for (c, p, s) in ctx["unita"]:
            with np.load(a.out / DIR_PRED / f"curva_{c}_p{p}_s{s}.npz", allow_pickle=True) as z:
                gr = str(z["gruppo"])
                for m, *_ in CURVE:
                    somme.setdefault(gr, {}); somme[gr][m] = somme[gr].get(m, 0) + z[f"griglia_{m}"].sum(1)
    fig, axs = plt.subplots(2, 4, figsize=(15, 7.2))
    for j, gr in enumerate(GRUPPI):
        ax = axs[0, j]; cf = RS["gruppi"][gr]["confronti"]
        for i, (k, et, col) in enumerate(BRACCI):
            w = cf[k]["wce"]; lo, hi = w["ic_con_nodi"]
            ax.errorbar([i], [w["media"]], yerr=[[w["media"] - lo], [hi - w["media"]]], fmt="o", color=col, capsize=4, lw=1.5)
            ax.annotate(f"{w['media']:+.3f}", (i, hi), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=8)
        wa = cf["A-C"]["wce"]
        ax.axhline(wa["media"], color="#2ca02c", ls="-.", lw=1.2)
        ax.axhspan(wa["ic_con_nodi"][0], wa["ic_con_nodi"][1], color="#2ca02c", alpha=.12)
        ax.text(1.45, wa["ic_con_nodi"][1], f"A − C {wa['media']:+.3f}", color="#2ca02c", fontsize=8, va="bottom", ha="right")
        ax.axhline(0, color="#999999", lw=.8)
        ax.set_xticks([0, 1]); ax.set_xticklabels([et for _, et, _ in BRACCI]); ax.set_xlim(-0.5, 1.5)
        ax.set_title(gr); ax.grid(axis="y", alpha=.3)
        if j == 0:
            ax.set_ylabel("ΔwCE rispetto a C (negativo = meglio)")
        ax = axs[1, j]
        for m, et, col, ls in CURVE:
            if m in somme.get(gr, {}):
                far, rich = curva(somme[gr][m]); o = np.argsort(far)
                ax.plot(100 * far[o], 100 * rich[o], ls, color=col, lw=1.6, label=et)
        ax.set_xlim(0, 100 * FA_MAX); ax.set_ylim(0, 100); ax.grid(alpha=.3)
        ax.set_xlabel("falsi allarmi (%)")
        for fa in (2, 5, 10):
            ax.axvline(fa, color="#bbbbbb", lw=.6, ls=":")
        if j == 0:
            ax.set_ylabel("richiamo, classe congestionata (%)"); ax.legend(loc="upper left", fontsize=8)
    fig.suptitle("Figura 2 — Il costo di trasferimento in wCE (sopra) e le curve richiamo–falsi allarmi di C, F₀, F₀′ (sotto)", fontsize=10)
    fig.tight_layout()
    a.figure.mkdir(parents=True, exist_ok=True)
    f = a.figure / "figura2_51.png"; fig.savefig(f, dpi=150)
    print(f"  figura in {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
