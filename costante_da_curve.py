#!/usr/bin/env python3
"""
Costante entropia-richiamo dalle CURVE salvate, priore storico incluso.
========================================================================
Nessun addestramento. Legge `replication/**/metrics_*.csv`, che contengono la
curva precisione-richiamo gia' calcolata per ciascun modello e orizzonte.

PERCHE' QUESTA FONTE E NON I DUMP. La costante richiede g(tau), cioe' la densita'
della curva di richiamo alla soglia decisionale. I dump di probabilita' la
consentono, ma non contengono il priore storico ne' il MLP per-nodo: `gomo_classify`
salva le sole modalita' passate a `--modes`, e il priore e' calcolato a parte come
riferimento. I file di metriche contengono invece la curva per OGNI modello
valutato, priore compreso — ed e' la fonte su cui il calcolo originario era stato
condotto.

IL PRIORE E' IL CASO LIMITE. Ha la distribuzione predittiva piu' piatta di tutte:
predice la stessa cosa per ogni momento-tipo. Se la costante fosse una proprieta'
dei soli modelli che ordinano bene, li' differirebbe di molto. Verificarla su di
esso e' quindi il controllo che distingue una proprieta' del compito da una
proprieta' della fascia di testa.

LA FORMULA, derivata al primo ordine:

    Delta_richiamo = 3 tau g(tau) wCE |Delta|

Il fattore tre viene dalla pesatura: con w_k = N/(3 n_k) il prodotto fra peso e
frequenza vale N/3 per ogni classe, sicche' la classe critica contribuisce un
terzo dell'entropia INDIPENDENTEMENTE dalla sua rarita'. tau e' la soglia di
probabilita' che riproduce il richiamo della regola della classe piu' probabile,
e g(tau) = -dG/dtau la densita' della curva in quel punto.

Uso (dalla radice OR3/):

    poetry run python costante_da_curve.py
    poetry run python costante_da_curve.py --orizzonte 30m
"""
import argparse
import glob as globmod

import numpy as np
import pandas as pd

NOME = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
        "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023"}


def curve(ctx, orizzonte):
    """Restituisce {modello: (griglia di soglie, curva di richiamo, richiamo alla
    regola della classe piu' probabile)} per il contesto indicato."""
    f = [x for x in globmod.glob("replication/**/metrics_*.csv", recursive=True)
         if f"metrics_{ctx}_s" in x]
    if not f:
        return {}
    D = pd.concat([pd.read_csv(x) for x in f], ignore_index=True)
    fuori = {}
    for tag in D.tag.unique():
        m, h = str(tag).split("|")
        if h != orizzonte:
            continue
        pr = D[(D.kind == "pr_curve") & (D.tag == tag)].groupby("idx")[["a", "b"]].mean()
        cl = D[(D.kind == "class") & (D.tag == tag) & (D.idx == 2)]
        if not len(pr) or not len(cl):
            continue
        # `idx` e' la soglia in centesimi, `b` il richiamo sulla classe critica
        t = pr.index.to_numpy() / 100.0
        G = pr.b.to_numpy()
        fuori[m] = (t, G, float(cl.b.mean()))
    return fuori


def costante(t, G, ric, wce):
    """(tau, g(tau), variazione di richiamo per un punto percentuale di entropia)."""
    o = np.argsort(t)
    t, G = t[o], G[o]
    # tau: dove la curva di richiamo vale quello osservato alla regola dell'argmax
    tau = float(np.interp(ric, G[::-1], t[::-1]))
    g = float(-np.gradient(G, t)[int(np.argmin(np.abs(t - tau)))])
    return tau, g, 3 * tau * g * wce * 0.01


def entropie(ctx):
    """wCE media per modello, dai file di risultato."""
    fuori = {}
    for pref in ("fix_classify", "classify", "camp_classify", "prec_classify",
                 "lgbristr", "stid"):
        for f in sorted(globmod.glob(f"replication/*/{pref}_{ctx}_s?.csv")):
            d = pd.read_csv(f)
            cm = "model" if "model" in d.columns else "mode"
            for m in d[cm].unique():
                fuori.setdefault(str(m), []).append(d[d[cm] == m].wCE.mean())
    return {k: float(np.mean(v)) for k, v in fuori.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description="costante dalle curve salvate")
    ap.add_argument("--orizzonte", default="15m")
    a = ap.parse_args()

    print("=" * 96)
    print(f"COSTANTE dalle curve salvate — orizzonte {a.orizzonte}")
    print("=" * 96)
    print(f"{'contesto':10s} {'modello':14s} {'tau':>7} {'g(tau)':>8} {'wCE':>8} "
          f"{'per 1% di wCE':>15}")
    tab = {}
    for c, n in NOME.items():
        cur = curve(c, a.orizzonte)
        wce = entropie(c)
        if not cur:
            print(f"{n:10s} curve non trovate")
            continue
        for m in sorted(cur):
            w = wce.get(m)
            if w is None:
                # il priore compare nei CSV come `hist_prior`; il tabellare puo'
                # comparire come `lightgbm` o `lgb_fair` a seconda della campagna
                w = wce.get({"lightgbm": "lgb_fair"}.get(m, m))
            if w is None:
                print(f"{n:10s} {m:14s} entropia non trovata")
                continue
            tau, g, k = costante(*cur[m], w)
            tab.setdefault(n, {})[m] = k
            print(f"{n:10s} {m:14s} {tau:7.3f} {g:8.3f} {w:8.4f} {k:15.4f}")
        print()

    if tab:
        print("=" * 96)
        print("VARIABILITA' FRA MODELLI, entro ciascun contesto")
        print("=" * 96)
        print(f"{'contesto':10s} {'modelli':>8} {'minimo':>9} {'massimo':>9} "
              f"{'rapporto':>9}   con il priore?")
        for n, d in tab.items():
            v = list(d.values())
            print(f"{n:10s} {len(v):8d} {min(v):9.4f} {max(v):9.4f} "
                  f"{max(v)/max(min(v),1e-9):8.2f}x   "
                  f"{'si' if 'hist_prior' in d else 'NO'}")
        tutti = [x for d in tab.values() for x in d.values()]
        print(f"\n  complessivo: {min(tutti):.4f} ÷ {max(tutti):.4f}")
        print("\n  Se la costante resta stabile INCLUDENDO il priore storico, la sua")
        print("  invarianza non e' una proprieta' dei modelli che ordinano bene ma del")
        print("  compito, poiche' il priore ha la distribuzione predittiva piu' piatta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
