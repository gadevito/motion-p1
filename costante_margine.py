#!/usr/bin/env python3
"""
Costante che lega entropia pesata e richiamo, e riferimento indipendente dai modelli.
=====================================================================================
Nessun addestramento: legge i dump di probabilita' e i bersagli.

Serve a motivare il margine di equivalenza con una derivazione verificabile anziche'
con un valore osservato a posteriori.

LA DERIVAZIONE, al primo ordine.

  L'entropia pesata e'  wCE = (1/N) Σ w[y_i] (-log p_i(y_i)),  con Σ w[y_i] = N.
  Con i pesi adottati, w_k = N/(3 n_k), il prodotto fra peso e frequenza vale N/3
  per OGNI classe: la classe critica contribuisce quindi un terzo dell'entropia
  totale INDIPENDENTEMENTE dalla sua rarita'. E' l'argomento strutturale.

  Si consideri una perturbazione moltiplicativa della probabilita' predetta sulla
  classe critica, p3 -> p3(1+e). Allora -log p3 diminuisce di e, e il contributo
  della classe critica all'entropia varia di -(1/3)e. In termini relativi:

      Delta = DeltawCE / wCE = -e / (3 wCE)      =>      e = -3 wCE Delta

  Una cella entra nella classe critica quando p3 supera la soglia tau equivalente
  alla regola della classe piu' probabile. Sotto la perturbazione attraversano la
  soglia le celle con p3 in [tau(1-e), tau], che sono una frazione g(tau) tau e
  delle celle critiche vere. Quindi:

      Delta_richiamo  =  3 tau g(tau) wCE |Delta|

  dove g(tau) = -dG/dtau e' la DENSITA' DELLA CURVA DI RICHIAMO alla soglia, cioe'
  la densita' della distribuzione predittiva sulla classe critica in quel punto.

CHE COSA E' MODEL-DIPENDENTE, E PERCHE' CONTA.

  g(tau) e' una proprieta' della distribuzione PREDITTIVA, non dei dati: dice
  quante celle il modello colloca presso il confine decisionale. Misurarla su un
  modello e usarla per fissare il margine con cui quel modello viene giudicato e'
  circolare — e lo e' qualunque modello si scelga, non solo il priore storico.

  Lo script calcola quindi la costante SU TUTTI i modelli della fascia di testa,
  cosi' che la sua variabilita' sia visibile: se varia poco e' una proprieta' del
  compito e riportarla da un modello solo e' difendibile purche' dichiarato; se
  varia molto il margine va motivato sull'estremo superiore, che e' la scelta
  conservativa.

IL RIFERIMENTO INDIPENDENTE DAI MODELLI.

  La densita' empirica del fattore di congestione alla soglia di classe si calcola
  dai soli bersagli. NON e' la stessa grandezza — dice quante celle hanno il
  BERSAGLIO presso la soglia, non quante il modello ne colloca presso il confine —
  e le due coincidono soltanto per un predittore monotono e calibrato. E' pero'
  l'unico termine di paragone che non dipende da alcun modello, e misura quanto il
  compito sia intrinsecamente di frontiera.

Uso (dalla radice OR3/):

    poetry run python costante_margine.py
    poetry run python costante_margine.py --finestra 0.02
"""
import argparse
import glob as globmod

import numpy as np
import pandas as pd

H = ("15m", "30m", "60m", "120m")
T4 = "data_collection/traffic4cast"
GO = "data_collection/go-mo/gomo"
TARGETS = {
    "t4cmad": f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4clon": f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4cmel": f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
    "d8_2024": f"{GO}/targets_2024_urb_d8.npz",
    "d15_2024": f"{GO}/targets_2024_urb_d15.npz",
    "d8_2023": f"{GO}/targets_2023_urb_d8.npz",
}
NOME = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
        "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023"}
# modelli della fascia di testa, con gli schemi che li contengono
# TUTTI i modelli con dump disponibili, non i soli della fascia di testa.
# Restringere ai migliori e poi concludere che la costante e' stabile fra loro
# sarebbe circolare: si dimostrerebbe una proprieta' dei modelli che ordinano
# bene, non del compito. Il priore storico e' il caso di prova, perche' ha la
# distribuzione predittiva piu' piatta di tutti.
MODELLI = {
    "gwn_adaptive": ["fix_classify", "classify", "camp_classify"],
    "gwn_none":     ["fix_classify", "classify", "camp_classify"],
    "staeformer":   ["fixgraph_sota", "prec_sota", "sota"],
    "agcrn":        ["fixgraph_rnn", "prec_rnn", "rnn"],
    "dcrnn":        ["fixgraph_rnn", "prec_rnn", "rnn"],
    "t4c_gnn":      ["fixgraph_sota", "prec_sota", "sota"],
    "gwn_stid":     ["prec_classify", "fix_classify", "stid"],
    "lgb_fair":     ["lgbristr"],
    "hist_prior":   ["fix_classify", "classify", "camp_classify"],
}
SOGLIA_ROSSO = 0.40      # r sotto questa soglia e' classe critica (§3.2.3)


def blocchi(percorso, tag, orizzonti=None):
    """Con `orizzonti` ristretto a ('15m',) include anche il GCN in stile
    Traffic4cast, che esiste al solo orizzonte di quindici minuti — ed e' del
    resto l'orizzonte su cui la costante era definita in origine."""
    if not globmod.glob(percorso):
        return None
    z = np.load(percorso, allow_pickle=True)
    out = []
    for h in (orizzonti or H):
        k = [x[3:] for x in z.files
             if x.startswith("tag") and str(z[x]) == f"{tag}|{h}"]
        if not k:
            return None
        i = k[0]
        out.append((z[f"p{i}"].astype("float32"), z[f"y{i}"].astype(int)))
    return out


def pesi(c):
    if not globmod.glob(TARGETS[c]):
        return None
    z = np.load(TARGETS[c], allow_pickle=True)
    C = z["congestion_emp"]
    T = C.shape[0]
    fr = np.array([(C[: int((T - 8) * 0.7)] == k).sum() for k in (1, 2, 3)], float)
    return fr.sum() / (np.maximum(fr, 1) * 3)


def costante(b, w):
    """Restituisce (tau, g(tau), wCE, variazione di richiamo per 1% di entropia).

    tau e' la soglia di probabilita' che riproduce il richiamo della regola della
    classe piu' probabile; g(tau) la densita' della curva di richiamo in quel punto,
    stimata per differenze finite su una griglia.
    """
    P = np.concatenate([x[0] for x in b])
    Y = np.concatenate([x[1] for x in b])
    crit = (Y == 2)
    if crit.sum() < 100:
        return None
    p3 = P[crit, 2]
    # richiamo alla regola della classe piu' probabile
    ric = float((P[crit].argmax(1) == 2).mean())
    # curva G(t) = frazione di celle critiche con p3 >= t, su griglia fine
    t = np.linspace(0.01, 0.99, 197)
    G = np.array([(p3 >= x).mean() for x in t])
    # tau: dove la curva vale il richiamo osservato
    tau = float(np.interp(ric, G[::-1], t[::-1]))
    g = float(-np.gradient(G, t)[int(np.argmin(np.abs(t - tau)))])
    # entropia pesata sugli stessi blocchi
    v = []
    for Pk, Yk in b:
        pt = np.clip(Pk[np.arange(len(Yk)), Yk], 1e-7, 1)
        v.append(float(np.sum(w[Yk] * -np.log(pt)) / np.sum(w[Yk])))
    wce = float(np.mean(v))
    return tau, g, wce, 3 * tau * g * wce * 0.01


def densita_empirica(c, finestra):
    """Densita' del fattore di congestione alla soglia di classe, dai soli bersagli.

    Riferimento indipendente dai modelli: misura quante celle hanno il BERSAGLIO
    presso la soglia, cioe' quanto il compito sia intrinsecamente di frontiera.
    """
    if not globmod.glob(TARGETS[c]):
        return None
    z = np.load(TARGETS[c], allow_pickle=True)
    if "r_emp" not in z.files:
        return None
    r = z["r_emp"]
    C = z["congestion_emp"]
    T = C.shape[0]
    te = slice(int((T - 8) * 0.85), None)       # periodo di test approssimato
    v = r[te][np.isfinite(r[te]) & (C[te] > 0)]
    if not len(v):
        return None
    dentro = float(np.mean(np.abs(v - SOGLIA_ROSSO) <= finestra))
    dens = dentro / (2 * finestra)              # densita' per unita' di r
    return dens, dentro, float((v < SOGLIA_ROSSO).mean())


def main() -> int:
    ap = argparse.ArgumentParser(description="costante entropia-richiamo e riferimento empirico")
    ap.add_argument("--probs", default="replication/probs")
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--finestra", type=float, default=0.02,
                    help="semiampiezza della finestra attorno alla soglia di classe")
    a = ap.parse_args()

    print("=" * 100)
    print("COSTANTE: variazione di richiamo per UN PUNTO PERCENTUALE di entropia pesata")
    print("=" * 100)
    print(f"{'contesto':10s} " + "".join(f"{m[:11]:>12}" for m in MODELLI) +
          f"{'intervallo':>16}")
    tab = {}
    for c, n in NOME.items():
        riga, val = [], []
        for m, schemi in MODELLI.items():
            r = None
            for p in schemi:
                oz = ("15m",) if (m == "t4c_gnn" or globals().get("SOLO15")) else None
                B = [blocchi(f"{a.probs}/{p}_{c}_s{s}.npz", m, oz)
                     for s in range(a.semi)]
                B = [x for x in B if x]
                if len(B) >= 3:
                    w = pesi(c)
                    if w is None:
                        break
                    r = [costante(x, w) for x in B]
                    r = [x for x in r if x]
                    break
            if not r:
                riga.append(f"{'—':>12}")
                continue
            k = float(np.mean([x[3] for x in r]))
            val.append(k)
            riga.append(f"{k:12.4f}")
        if val:
            tab[n] = val
            riga.append(f"  {min(val):.4f}–{max(val):.4f}")
        print(f"{n:10s} " + "".join(riga))

    if tab:
        tutti = [x for v in tab.values() for x in v]
        print(f"\n  su tutti i contesti e modelli: {min(tutti):.4f} ÷ {max(tutti):.4f}")
        print(f"  rapporto fra estremi: {max(tutti)/max(min(tutti),1e-9):.1f}x")
        disp = [max(v) / max(min(v), 1e-9) for v in tab.values()]
        print(f"  variabilita' ENTRO contesto, fra modelli: "
              f"{min(disp):.2f}x ÷ {max(disp):.2f}x")
        print("\n  Se la variabilita' entro contesto e' contenuta, la costante e' una")
        print("  proprieta' del compito e riportarla da un modello solo e' difendibile,")
        print("  purche' dichiarato. Se e' ampia, il margine va motivato sull'estremo")
        print("  superiore e la costante riportata come intervallo.")

    print("\n" + "=" * 100)
    print("RIFERIMENTO INDIPENDENTE DAI MODELLI: densita' empirica alla soglia di classe")
    print("=" * 100)
    print(f"{'contesto':10s} {'densita':>10} {'quota entro ±'+format(a.finestra,'.2f'):>18} "
          f"{'quota critica':>14}")
    for c, n in NOME.items():
        d = densita_empirica(c, a.finestra)
        if d is None:
            print(f"{n:10s} bersagli senza r_emp")
            continue
        print(f"{n:10s} {d[0]:10.3f} {100*d[1]:17.2f}% {100*d[2]:13.2f}%")
    print("\n  NON e' la stessa grandezza della costante: dice quante celle hanno il")
    print("  BERSAGLIO presso la soglia, non quante il modello ne colloca presso il")
    print("  confine decisionale. Le due coincidono solo per un predittore monotono e")
    print("  calibrato. E' pero' l'unico termine di paragone che non dipende da alcun")
    print("  modello, e misura quanto il compito sia intrinsecamente di frontiera.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
