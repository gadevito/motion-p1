#!/usr/bin/env python3
"""
E4 — figure e griglia (tau, N) sul test, dai risultati della fase test.
=======================================================================
Legge `e4_risultati.json`, `e4_scelta_gated.json` e le celle di prova in
`predizioni_e4/`; non ricalcola nessun confronto. Produce:

    figure/curva_e4.png        Delta wCE rispetto a C per durata d'adattamento,
                               sulle origini comuni (eta' > 1 settimana)
    figure/traiettoria_e4.png  wCE sul periodo di prova lungo l'adattamento a
                               24 h, e perdita d'adattamento per aggiornamento
    figure/griglia_e4.png      wCE della politica per (tau, N): validazione
                               (usata per la scelta) e test (NON usata, figura)
    results/evoluzione/e4_griglia_test.json

La griglia sul test e' **dichiarata non usata per la scelta**: la scelta e'
quella registrata in e4_scelta_gated.json, con la sua impronta e il suo istante.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_e4.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e4 import (  # noqa: E402
    CITTA, DURATE, N_SOGLIE, TAU, _carica_celle, _politica, _wce)

ETICHETTA_L = {24: "6 h", 48: "12 h", 96: "24 h", 192: "48 h", 672: "1 sett."}
ETICHETTA_TAU = {96: "24 h", 192: "48 h", 672: "1 sett.", None: "mai"}


def griglia_test(out: Path) -> dict:
    """La wCE integrata della politica per (tau, N) sulle celle di PROVA:
    stessa regola della validazione, riportata come figura."""
    celle = _carica_celle(out, "prova")
    g = {}
    for c in CITTA:
        kk = [k for k in celle if k[0] == c]
        if len(kk) != 36:
            raise RuntimeError(f"{c}: {len(kk)} celle di prova, attese 36")
        g[c] = {f"tau={'mai' if t is None else t}/N={N}":
                float(np.mean([_wce(*_politica(celle[k], t, N)) for k in kk]))
                for t in TAU for N in N_SOGLIE}
    return g


def fig_curva(R, f: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, c in zip(axs, CITTA):
        for nome, et, col in (("F", "F (da E)", "C0"), ("Fp", "F' (da E')", "C1")):
            m = [R["curva"][f"{c}/{nome}_{L}-C"]["media"] for L in DURATE]
            lo = [R["curva"][f"{c}/{nome}_{L}-C"]["ic_con_nodi"][0] for L in DURATE]
            hi = [R["curva"][f"{c}/{nome}_{L}-C"]["ic_con_nodi"][1] for L in DURATE]
            ax.errorbar(DURATE, m, yerr=[np.subtract(m, lo), np.subtract(hi, m)],
                        marker="o", capsize=3, label=et, color=col)
        for nome, et, col in (("F0", "F0 (media)", "C0"), ("F0p", "F0' (token)", "C1")):
            r = R["curva"][f"{c}/{nome}-C"]
            ax.axhline(r["media"], ls=":", color=col, label=et)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xscale("log"); ax.set_xticks(DURATE)
        ax.set_xticklabels([ETICHETTA_L[L] for L in DURATE])
        ax.set_title(f"{c} — {R['curva'][f'{c}/origini_comuni']} origini comuni")
        ax.set_xlabel("durata d'adattamento")
    axs[0].set_ylabel("Δ wCE rispetto a C (età > 1 settimana)")
    axs[0].legend(fontsize=8)
    fig.tight_layout(); f.parent.mkdir(parents=True, exist_ok=True); fig.savefig(f, dpi=150)


def fig_traiettoria(R, f: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 3, figsize=(12, 6.5))
    for j, c in enumerate(CITTA):
        for nome, et, col in (("F", "F (da E)", "C0"), ("Fp", "F' (da E')", "C1")):
            t = R["traiettoria"][f"{c}/{nome}"]
            k = sorted(int(z) for z in t)
            axs[0, j].plot(k, [t[str(z)] for z in k], marker="o", color=col, label=et)
            p = R["traiettoria"][f"{c}/{nome}/perdita"]
            axs[1, j].plot(range(1, len(p) + 1), p, color=col, label=et)
        axs[0, j].set_title(c); axs[0, j].set_xlabel("aggiornamenti")
        axs[1, j].set_xlabel("aggiornamenti")
    axs[0, 0].set_ylabel("wCE sul periodo di prova"); axs[1, 0].set_ylabel("perdita d'adattamento (24 h)")
    axs[0, 0].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(f, dpi=150)


def fig_griglia(G_val, G_test, scelta, f: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 3, figsize=(12, 6.5))
    for i, (G, tit) in enumerate(((G_val, "validazione (usata per la scelta)"),
                                  (G_test, "test (NON usata per la scelta)"))):
        for j, c in enumerate(CITTA):
            M = np.array([[G[c][f"tau={'mai' if t is None else t}/N={N}"] for N in N_SOGLIE]
                          for t in TAU])
            ax = axs[i, j]
            im = ax.imshow(M, cmap="viridis_r", aspect="auto")
            for a_, t in enumerate(TAU):
                for b_, N in enumerate(N_SOGLIE):
                    ax.text(b_, a_, f"{M[a_, b_]:.4f}", ha="center", va="center", fontsize=7,
                            color="w" if M[a_, b_] > M.mean() else "k")
            s = scelta[c]
            ax.add_patch(plt.Rectangle((N_SOGLIE.index(s["N"]) - .5, TAU.index(s["tau"]) - .5),
                                       1, 1, fill=False, ec="red", lw=2))
            ax.set_xticks(range(len(N_SOGLIE))); ax.set_xticklabels([str(N) for N in N_SOGLIE])
            ax.set_yticks(range(len(TAU))); ax.set_yticklabels([ETICHETTA_TAU[t] for t in TAU])
            ax.set_title(f"{c} — {tit}", fontsize=9)
            ax.set_xlabel("N (celle valide minime)")
            if j == 0:
                ax.set_ylabel("τ")
            fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout(); fig.savefig(f, dpi=150)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--figure", type=Path, default=Path("figure"))
    a = ap.parse_args()
    R = json.loads((a.out / "e4_risultati.json").read_text())
    SC = json.loads((a.out / "e4_scelta_gated.json").read_text())
    if R.get("impronta_scelta") != SC.get("impronta"):
        raise RuntimeError("i risultati del test non si riferiscono alla scelta registrata")
    print("=" * 84); print("E4 — figure e griglia (tau, N) sul test"); print("=" * 84)
    G = griglia_test(a.out)
    for c in CITTA:
        s = SC["scelta"][c]
        k = f"tau={'mai' if s['tau'] is None else s['tau']}/N={s['N']}"
        migliore = min(G[c].items(), key=lambda kv: kv[1])
        print(f"  {c:11s} scelta {k:16s} wCE test {G[c][k]:.5f}; minimo sul test "
              f"{migliore[0]:16s} {migliore[1]:.5f}"
              + ("   (coincidono)" if migliore[0] == k else ""))
    doc = {"griglia_test": G, "scelta": SC["scelta"], "impronta_scelta": SC["impronta"],
           "nota": "griglia sul test riportata come figura, NON usata per la scelta"}
    (a.out / "e4_griglia_test.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    fig_curva(R, a.figure / "curva_e4.png")
    fig_traiettoria(R, a.figure / "traiettoria_e4.png")
    fig_griglia(SC["griglia_validazione"], G, SC["scelta"], a.figure / "griglia_e4.png")
    print(f"  salvati: {a.out / 'e4_griglia_test.json'}, {a.figure}/curva_e4.png, "
          f"traiettoria_e4.png, griglia_e4.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
