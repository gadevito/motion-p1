#!/usr/bin/env python3
"""
Decadimento per orizzonte: valori per contesto e figura a due pannelli.
=======================================================================
Nessun addestramento: legge i file di risultato della campagna indicata.

CHE COSA PRODUCE.

  1. Entropia pesata e richiamo sulla classe critica, per contesto e orizzonte,
     con la CAMPAGNA DI PROVENIENZA dichiarata riga per riga. Serve a stabilire
     se il confronto fra i due decadimenti sia omogeneo: il capoverso conclusivo
     di §8.1.1 cita valori di richiamo che potrebbero provenire da una campagna
     diversa da quella su cui la sottosezione lavora.

  2. La verifica che l'ordinamento fra contesti sia stabile a TUTTI gli
     orizzonti misurati e non ai soli estremi. Le curve non incrociarsi e' una
     proprieta' piu' forte di quella che la tabella mostra, ed e' affermabile
     solo dopo averla controllata su ciascuna coppia e ciascun orizzonte.

  3. La figura a due pannelli: a sinistra l'entropia in valore ASSOLUTO, a
     destra il degrado RELATIVO rispetto ai quindici minuti. Il solo pannello
     relativo, che e' quello attuale, fa partire tutte le curve da zero e occulta
     il livello di partenza, che e' la grandezza su cui i contesti differiscono
     di piu'.

     I tre contesti a velocita' ricostruita sono resi con tratto continuo e i
     tre primari con tratto spezzato, e ciascuno con marcatore e colore propri:
     nella figura attuale i tratteggi si sovrappongono nella regione fra il tre e
     il sette per cento e non sono distinguibili.

Uso (dalla radice OR3/):

    poetry run python decadimento_orizzonte.py
    poetry run python decadimento_orizzonte.py --modello gwn_none --campagne classify
"""
import argparse
import glob as globmod
import itertools

import numpy as np
import pandas as pd

ORIZZONTI = ["15m", "30m", "60m", "120m"]
MINUTI = {"15m": 15, "30m": 30, "60m": 60, "120m": 120}
NOME = {"d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023",
        "t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne"}
SPIRE = ["d8_2024", "d15_2024", "d8_2023"]

STILE = {
    "d8_2024":  dict(color="#1f4e79", marker="o", ls="-"),
    "d15_2024": dict(color="#2e8b57", marker="s", ls="-"),
    "d8_2023":  dict(color="#8b4513", marker="^", ls="-"),
    "t4cmad":   dict(color="#c00000", marker="D", ls="--"),
    "t4clon":   dict(color="#7030a0", marker="v", ls="--"),
    "t4cmel":   dict(color="#d68910", marker="P", ls="--"),
}


def serie(c, modello, campagne, semi):
    """(dizionario orizzonte -> (entropia, richiamo), campagna usata)."""
    for p in campagne:
        f = sorted(globmod.glob(f"replication/*/{p}_{c}_s?.csv"))
        if len(f) < 3:
            continue
        d = pd.concat([pd.read_csv(x) for x in f[:semi]], ignore_index=True)
        cm = "model" if "model" in d.columns else "mode"
        q = d[d[cm] == modello]
        if not len(q) or "horizon" not in q.columns:
            continue
        if "red_recall" not in q.columns:
            continue
        fuori = {}
        for h in ORIZZONTI:
            r = q[q.horizon == h]
            if len(r):
                fuori[h] = (float(r.wCE.mean()), float(r.red_recall.mean()))
        if len(fuori) == len(ORIZZONTI):
            return fuori, p
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser(description="decadimento per orizzonte")
    ap.add_argument("--modello", default="gwn_adaptive")
    ap.add_argument("--campagne", nargs="+",
                    default=["fix_classify", "classify", "camp_classify",
                             "prec_classify"])
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--figura", default="figure/decadimento_orizzonte.png")
    a = ap.parse_args()

    D, fonte = {}, {}
    for c in NOME:
        s, p = serie(c, a.modello, a.campagne, a.semi)
        if s:
            D[c], fonte[c] = s, p

    if not D:
        print("nessuna campagna con richiamo per orizzonte")
        return 1

    # ------------------------------------------------------------ valori ---
    print(f"modello: {a.modello}\n")
    print(f"{'contesto':10s} {'campagna':14s} " +
          "".join(f"{h:>9}" for h in ORIZZONTI) + f"{'degrado':>10}")
    print("ENTROPIA PESATA")
    for c in NOME:
        if c not in D:
            print(f"{NOME[c]:10s} assente")
            continue
        v = [D[c][h][0] for h in ORIZZONTI]
        print(f"{NOME[c]:10s} {fonte[c]:14s} " + "".join(f"{x:9.4f}" for x in v) +
              f"{100*(v[-1]-v[0])/v[0]:+9.1f}%")
    print("\nRICHIAMO SULLA CLASSE CRITICA")
    for c in NOME:
        if c not in D:
            continue
        v = [D[c][h][1] for h in ORIZZONTI]
        print(f"{NOME[c]:10s} {fonte[c]:14s} " + "".join(f"{x:9.3f}" for x in v) +
              f"{100*(v[-1]-v[0])/v[0]:+9.1f}%")

    if len(set(fonte.values())) > 1:
        print("\n  ATTENZIONE: i contesti provengono da campagne diverse; il")
        print("  confronto fra i due decadimenti non e' omogeneo e va dichiarato.")

    # --------------------------------------------- stabilita' ordinamento ---
    print("\nSTABILITA' DELL'ORDINAMENTO FRA CONTESTI")
    ctx = [c for c in NOME if c in D]
    for eti, i in (("entropia", 0), ("richiamo", 1)):
        incroci = []
        for x, y in itertools.combinations(ctx, 2):
            segni = {np.sign(D[x][h][i] - D[y][h][i]) for h in ORIZZONTI}
            if len(segni) > 1:
                incroci.append(f"{NOME[x]}/{NOME[y]}")
        print(f"  {eti:10s} coppie {len(list(itertools.combinations(ctx,2))):2d}  "
              f"incroci: {', '.join(incroci) if incroci else 'NESSUNO'}")
    print("  (nessun incrocio = l'ordinamento e' stabile a tutti e quattro gli")
    print("   orizzonti, e non ai soli estremi che la tabella riporta)")

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
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4))
    x = [MINUTI[h] for h in ORIZZONTI]

    for c in ctx:
        st = STILE[c]
        v = [D[c][h][0] for h in ORIZZONTI]
        ax1.plot(x, v, label=NOME[c], linewidth=1.8, markersize=6,
                 markerfacecolor="white", markeredgewidth=1.4, **st)
        rel = [100 * (y - v[0]) / v[0] for y in v]
        ax2.plot(x, rel, label=NOME[c], linewidth=1.8, markersize=6,
                 markerfacecolor="white", markeredgewidth=1.4, **st)

    for ax, tit, ylab in (
            (ax1, "Livello assoluto", "entropia incrociata pesata"),
            (ax2, "Degrado relativo ai quindici minuti", "variazione (%)")):
        ax.set_xscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{m} min" for m in x])
        ax.minorticks_off()
        ax.set_xlabel("orizzonte di previsione")
        ax.set_ylabel(ylab)
        ax.set_title(tit, fontsize=11)
        ax.grid(alpha=0.25, linewidth=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    ax2.axhline(0, color="black", linewidth=0.8, alpha=0.4)

    # legenda UNICA sotto i due pannelli: collocata dentro il primo si
    # sovrappone alle curve, che nella zona alta a sinistra sono dense
    h, l = ax1.get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=9.5, ncol=6,
               loc="lower center", bbox_to_anchor=(0.5, 0.055))
    fig.suptitle(f"Decadimento per orizzonte — {a.modello}", fontsize=12.5, y=0.985)
    fig.text(0.5, 0.012,
             "tratto continuo: contesti a velocita\u2019 ricostruita   |   "
             "tratto spezzato: contesti a velocita\u2019 misurata",
             ha="center", fontsize=8.5, color="#444444")
    fig.tight_layout(rect=[0, 0.11, 1, 0.95])
    fig.savefig(a.figura, dpi=200)
    print(f"\nfigura -> {a.figura}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
