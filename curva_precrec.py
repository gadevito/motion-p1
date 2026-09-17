#!/usr/bin/env python3
"""
Curva precisione-richiamo: soglie equivalenti per contesto e figura.
====================================================================
Nessun addestramento: legge i file di metriche della riesecuzione dedicata,
che contengono la curva gia' calcolata.

CHE COSA PRODUCE.

  1. Le due SOGLIE EQUIVALENTI per ciascun contesto: quella che riproduce il
     richiamo della regola della classe piu' probabile, e quella che ne riproduce
     la precisione. Il documento le riporta come intervalli sui sei contesti,
     sicche' il lettore sa fra quali valori cadano ma non su quale contesto cada
     ciascun estremo — che e' l'informazione utile a chi debba tarare in
     esercizio.

  2. La FIGURA della curva, che il testo richiama tre volte senza che esista.
     Sei pannelli, uno per contesto, con i due punti di lavoro segnati e la
     soglia equivalente annotata.

DUE COSE DA VERIFICARE PRIMA DI USARE I VALORI.

  La riesecuzione dedicata esiste a TRE semi, mentre le sottosezioni adiacenti
  lavorano a cinque: i valori non sono direttamente confrontabili con quelli
  della campagna estesa, e lo scarto sul richiamo a quindici minuti e' di circa
  due centesimi.

  Il riferimento tabellare compare in due forme. I file `precrec_*` contengono
  `lightgbm`, che e' valutato sulla popolazione PIENA e solo su tre contesti; i
  file `metrics_lgbfair_*` contengono `lgb_fair` sulla popolazione RISTRETTA e su
  tutti e sei. La correzione descritta in §6.2.1 e applicata alle tabelle di
  prestazione assoluta non e' stata propagata qui: lo script usa la seconda
  fonte e lo dichiara.

Uso (dalla radice OR3/):

    poetry run python curva_precrec.py
    poetry run python curva_precrec.py --modello gwn_adaptive --orizzonte 15m
"""
import argparse
import glob as globmod

import numpy as np
import pandas as pd

NOME = {"d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023",
        "t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne"}
SPIRE = ("d8_2024", "d15_2024", "d8_2023")


def curva(ctx, modello, orizzonte):
    """(soglie, precisione, richiamo) mediati sui semi, piu' il punto di lavoro.

    Il riferimento tabellare sta in file con prefisso proprio, `metrics_lgbfair_*`,
    e vi compare sulla popolazione RISTRETTA — quella corretta secondo §6.2.1. I
    file `precrec_*` contengono invece `lightgbm` sulla popolazione piena e solo
    su tre contesti: non vanno usati.
    """
    pref = "metrics_lgbfair_" if modello == "lgb_fair" else "metrics_"
    f = [x for x in globmod.glob("replication/**/metrics_*.csv", recursive=True)
         if f"{pref}{ctx}_s" in x]
    if not f:
        return None
    D = pd.concat([pd.read_csv(x) for x in f], ignore_index=True)
    tag = f"{modello}|{orizzonte}"
    pr = D[(D.kind == "pr_curve") & (D.tag == tag)].groupby("idx")[["a", "b"]].mean()
    cl = D[(D.kind == "class") & (D.tag == tag) & (D.idx == 2)]
    if not len(pr) or not len(cl):
        return None
    t = pr.index.to_numpy() / 100.0
    o = np.argsort(t)
    # colonna `a` = precisione, `b` = richiamo
    return (t[o], pr.a.to_numpy()[o], pr.b.to_numpy()[o],
            float(cl.a.mean()), float(cl.b.mean()), len(f))


def soglia(t, curva_, valore, decrescente=True):
    """Soglia alla quale la curva assume il valore indicato."""
    if decrescente:
        return float(np.interp(valore, curva_[::-1], t[::-1]))
    return float(np.interp(valore, curva_, t))


def main() -> int:
    ap = argparse.ArgumentParser(description="soglie equivalenti e figura della curva")
    ap.add_argument("--modello", default="gwn_adaptive")
    ap.add_argument("--riferimento", default="lgb_fair",
                    help="secondo modello, sovrapposto nella figura. "
                         "Vuoto per il solo primo")
    ap.add_argument("--orizzonte", default="15m")
    ap.add_argument("--figura", default="figure/curva_precrec.png")
    a = ap.parse_args()

    D = {}
    for c in NOME:
        v = curva(c, a.modello, a.orizzonte)
        if v:
            D[c] = v
    if not D:
        print("curve non trovate")
        return 1
    Dr = {}
    if a.riferimento:
        for c in NOME:
            v = curva(c, a.riferimento, a.orizzonte)
            if v:
                Dr[c] = v

    print(f"modello {a.modello}, orizzonte {a.orizzonte}\n")
    print(f"{'contesto':10s} {'semi':>4} {'precisione':>11} {'richiamo':>9} "
          f"{'soglia|richiamo':>16} {'soglia|precisione':>18}")
    sr, sp = {}, {}
    for c in NOME:
        if c not in D:
            print(f"{NOME[c]:10s} assente")
            continue
        t, P, R, prec, ric, n = D[c]
        sr[c] = soglia(t, R, ric, decrescente=True)
        sp[c] = soglia(t, P, prec, decrescente=False)
        print(f"{NOME[c]:10s} {n:4d} {prec:11.3f} {ric:9.3f} "
              f"{sr[c]:16.3f} {sp[c]:18.3f}")

    for eti, d in (("appaiando il richiamo", sr), ("appaiando la precisione", sp)):
        if not d:
            continue
        lo = min(d, key=d.get)
        hi = max(d, key=d.get)
        print(f"\n  {eti}: {d[lo]:.3f} ({NOME[lo]}) ÷ {d[hi]:.3f} ({NOME[hi]})")

    # ------------------------------------------------------------ figura ---
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from pathlib import Path
    except ImportError:
        print("\nmatplotlib assente: figura non prodotta")
        return 0

    Path(a.figura).parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.2), sharex=True, sharey=True)
    for ax, c in zip(axes.ravel(), NOME):
        if c not in D:
            ax.set_visible(False)
            continue
        t, P, R, prec, ric, _ = D[c]
        col = "#1f4e79" if c in SPIRE else "#c00000"
        ax.plot(R, P, color=col, linewidth=2.0, label="rete neurale", zorder=4)
        if c in Dr:
            _, Pr, Rr, precr, ricr, _ = Dr[c]
            ax.plot(Rr, Pr, color="#666666", linewidth=1.6, ls="--",
                    label="riferimento tabellare", zorder=3)
            ax.plot([ricr], [precr], "s", color="#666666", markersize=6,
                    markerfacecolor="white", markeredgewidth=1.4, zorder=5)
        # la soglia del regime operativo, non il punto di lavoro: i due
        # coincidono solo dove il richiamo alla regola della classe piu'
        # probabile vale per caso 0,60
        ax.axvline(0.60, color="#999999", linewidth=0.9, ls=":", zorder=1)
        ax.plot([ric], [prec], "o", color=col, markersize=8,
                markerfacecolor="white", markeredgewidth=2, zorder=6)
        ax.annotate(f"{ric:.2f}", (ric, prec), textcoords="offset points",
                    xytext=(8, 8), fontsize=9, color=col)
        ax.set_title(NOME[c], fontsize=11)
        ax.grid(alpha=0.25, linewidth=0.6)
        ax.set_xlim(0, 1); ax.set_ylim(0, max(0.5, float(P.max()) * 1.15))
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    for ax in axes[-1]:
        ax.set_xlabel("richiamo sulla classe critica")
    for ax in axes[:, 0]:
        ax.set_ylabel("precisione")

    h, l = axes.ravel()[0].get_legend_handles_labels()
    if h:
        fig.legend(h, l, frameon=False, fontsize=9.5, ncol=2,
                   loc="lower center", bbox_to_anchor=(0.5, 0.055))
    fig.suptitle(f"Curva precisione-richiamo sulla classe critica — "
                 f"{a.orizzonte}", fontsize=12.5, y=0.985)
    fig.text(0.5, 0.012,
             "il cerchio e\u2019 il punto della regola della classe piu\u2019 probabile, "
             "con il richiamo corrispondente   |   "
             "la linea punteggiata e\u2019 la soglia del regime operativo (richiamo 0,60)",
             ha="center", fontsize=8.5, color="#444444")
    fig.tight_layout(rect=[0, 0.105, 1, 0.955])
    fig.savefig(a.figura, dpi=200)
    print(f"\nfigura -> {a.figura}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
