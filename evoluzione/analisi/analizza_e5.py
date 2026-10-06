#!/usr/bin/env python3
"""
E5 — figura a punti episodio × citta' per le affermazioni (a)–(e).
===================================================================
Legge `e5_risultati.json`; non ricalcola nulla. Produce:

    figure/episodi_e5.png     cinque pannelli, uno per affermazione: per
                              citta' tre punti (episodi 1, 2, 3) con
                              intervallo; lo zero come riferimento
    figure/secondaria_e5.png  gated − C, F'(24 h, k) − C e F'(24 h, k) − F'(24 h)

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_e5.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e5 import CITTA, EPISODI  # noqa: E402

TITOLI = {"a": "(a) F₀′ − C", "b": "(b) gated − F₀′", "c": "(c) F′(1 sett.) − C, età > 1 sett.",
          "d": "(d) F′(24 h) − C", "e": "(e) F′(1 sett.) − A, età > 1 sett."}
ALTRI = {"gated-C": "gated − C", "Fp_96k-C": "F′(24 h, k) − C", "Fp_96k-Fp_96": "F′(24 h, k) − F′(24 h)"}


def _punti(ax, righe, titolo):
    """righe: {citta: [(media, lo, hi, segno) per episodio]}."""
    x0 = 0
    xt, xl = [], []
    for c in CITTA:
        for i, (m, lo, hi, sg) in enumerate(righe[c]):
            x = x0 + i
            ax.errorbar(x, m, yerr=[[m - lo], [hi - m]], fmt="o", capsize=3,
                        color={"-": "C2", "+": "C3", "0": "C7"}[sg])
            xt.append(x); xl.append(str(i + 1))
        x0 += len(righe[c]) + 1
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(xt); ax.set_xticklabels(xl, fontsize=8)
    for j, c in enumerate(CITTA):
        ax.text(j * 4 + 1, 1.02, c, transform=ax.get_xaxis_transform(), ha="center", fontsize=9)
    ax.set_title(titolo, fontsize=9, pad=16)
    ax.set_xlabel("episodio", fontsize=8)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--figure", type=Path, default=Path("figure"))
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    R = json.loads((a.out / "e5_risultati.json").read_text())
    a.figure.mkdir(parents=True, exist_ok=True)
    print("=" * 84); print("E5 — figura a punti episodio × citta'"); print("=" * 84)
    fig, axs = plt.subplots(1, 5, figsize=(17, 3.8))
    for ax, k in zip(axs, "abcde"):
        righe = {c: [(r["media"], r["ic_con_nodi"][0], r["ic_con_nodi"][1], r["segno"])
                     for r in (R["affermazioni"][f"{c}/ep{e}/{k}"] for e in EPISODI)] for c in CITTA}
        _punti(ax, righe, TITOLI[k])
        print(f"  ({k}) " + "  ".join(f"{c} {''.join(R['stesso_segno'][f'{c}/{k}']['segni'])}"
                                     f"{' concorda' if R['stesso_segno'][f'{c}/{k}']['concorda'] else ' NO'}"
                                     for c in CITTA))
    axs[0].set_ylabel("Δ wCE (verde: < 0, rosso: > 0, grigio: zero dentro)", fontsize=8)
    fig.tight_layout(); fig.savefig(a.figure / "episodi_e5.png", dpi=150)
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.8))
    for ax, (k, tit) in zip(axs, ALTRI.items()):
        righe = {}
        for c in CITTA:
            rr = []
            for e in EPISODI:
                r = R["altri"][f"{c}/ep{e}/{k}"]
                lo, hi = r["ic_con_nodi"]
                rr.append((r["media"], lo, hi, "-" if hi < 0 else ("+" if lo > 0 else "0")))
            righe[c] = rr
        _punti(ax, righe, tit + ("  (secondaria, k = " + ", ".join(
            f"{c[:3]} {R['k_secondaria'][c]}" for c in CITTA) + ")" if "k" in k else ""))
    fig.tight_layout(); fig.savefig(a.figure / "secondaria_e5.png", dpi=150)
    print(f"  salvate {a.figure}/episodi_e5.png e secondaria_e5.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
