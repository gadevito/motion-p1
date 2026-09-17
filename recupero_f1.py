#!/usr/bin/env python3
"""
Recupero di F1-macro dalla taratura delle soglie, per entrambi i modelli.
=========================================================================
Nessun addestramento: legge i dump di validazione e di prova.

PERCHE' QUESTA FONTE E NON LE CURVE. La curva precisione-richiamo salvata nei
file di metriche riporta precisione, richiamo e tasso di allarme sulla SOLA
classe critica: la F1-macro coinvolge tutte e tre le classi e non e' quindi
ricostruibile da essa. I dump di `probsval/` contengono invece le distribuzioni
predette su validazione e su prova, sicche' la soglia si tara sulla prima e si
applica alla seconda — che e' l'unica taratura dispiegabile.

TRE CONVENZIONI CHE CAMBIANO IL RISULTATO.

  * La soglia va tarata sulla VALIDAZIONE e applicata alla PROVA. Tararla sulla
    prova da' un oracolo non dispiegabile, che lo script riporta accanto per
    misurare quanto la taratura onesta costi.
  * Il riferimento tabellare e' `lgb_fair` sulla popolazione RISTRETTA, non
    `lightgbm` sulla piena: la correzione di §6.2.1 vale anche qui.
  * Cinque semi, non tre: i dump di validazione coprono l'intera campagna
    estesa, a differenza della riesecuzione dedicata alla curva.

Uso (dalla radice OR3/):

    poetry run python recupero_f1.py
    poetry run python recupero_f1.py --griglia 200
"""
import argparse
import glob as globmod
import itertools

import numpy as np

H = ("15m", "30m", "60m", "120m")
NOME = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
        "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023"}
GO = "data_collection/go-mo/gomo"
T4 = "data_collection/traffic4cast"
TARGETS = {
    "t4cmad": f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4clon": f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4cmel": f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
    "d8_2024": f"{GO}/targets_2024_urb_d8.npz",
    "d15_2024": f"{GO}/targets_2024_urb_d15.npz",
    "d8_2023": f"{GO}/targets_2023_urb_d8.npz",
}
# nn/gb sono i dump di VALIDAZIONE, nn_test/gb_test quelli di PROVA
MODELLI = {"rete": ("nn", "nn_test", "gwn_none"),
           "tabellare": ("gb", "gb_test", "lgb_fair")}


def blocchi(percorso, tag):
    if not globmod.glob(percorso):
        return None
    z = np.load(percorso, allow_pickle=True)
    out = []
    for h in H:
        k = [x[3:] for x in z.files
             if x.startswith("tag") and str(z[x]) == f"{tag}|{h}"]
        if not k:
            return None
        i = k[0]
        out.append((z[f"p{i}"].astype("float32"), z[f"y{i}"].astype(int)))
    return out


def f1_macro(P, Y, soglie=None):
    """F1 media sulle tre classi. Con `soglie` la decisione e' presa dividendo
    ciascuna probabilita' per la soglia della classe e prendendo il massimo,
    che generalizza la regola della classe piu' probabile (soglie tutte pari)."""
    pred = (P / soglie).argmax(1) if soglie is not None else P.argmax(1)
    f = []
    for k in range(3):
        vp = float(((pred == k) & (Y == k)).sum())
        fp = float(((pred == k) & (Y != k)).sum())
        fn = float(((pred != k) & (Y == k)).sum())
        f.append(2 * vp / max(2 * vp + fp + fn, 1e-9))
    return float(np.mean(f))


def tara(bv, griglia, campione=400_000):
    """Con milioni di celle la ricerca su griglia fine e' proibitiva: ogni
    valutazione scorre l'intero insieme, e la ricerca coordinata ne richiede
    sei volte la griglia. Si tara quindi su un CAMPIONE casuale della
    validazione — la soglia ottima e' stabile ben prima di quattrocentomila
    celle — e si applica poi all'insieme di prova per intero."""
    """Soglie per classe che massimizzano la F1-macro sulla VALIDAZIONE.

    Ricerca coordinata: si ottimizza una classe alla volta a soglie fisse per le
    altre, ripetendo due volte. Una ricerca esaustiva su tre classi sarebbe
    cubica nella griglia e non aggiunge nulla, poiche' la superficie e' regolare.
    """
    P = np.concatenate([x[0] for x in bv])
    Y = np.concatenate([x[1] for x in bv])
    if len(Y) > campione:
        r = np.random.default_rng(0).choice(len(Y), campione, replace=False)
        P, Y = P[r], Y[r]
    s = np.ones(3)
    val = np.linspace(0.2, 3.0, griglia)
    for _ in range(2):
        for k in range(3):
            best, bs = -1, s[k]
            for v in val:
                t = s.copy()
                t[k] = v
                m = f1_macro(P, Y, t)
                if m > best:
                    best, bs = m, v
            s[k] = bs
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description="recupero di F1-macro dalla taratura")
    ap.add_argument("--dir", default="replication/probsval")
    ap.add_argument("--griglia", type=int, default=60)
    ap.add_argument("--semi", type=int, default=5)
    a = ap.parse_args()

    print("F1-macro: regola della classe piu' probabile, soglie tarate su")
    print("validazione (dispiegabile) e su prova (oracolo, non dispiegabile)\n")
    print(f"{'contesto':10s} {'modello':11s} {'argmax':>8} {'tarata':>8} "
          f"{'recupero':>10} {'oracolo':>9} {'semi':>5}")
    rec = {}
    for c, n in NOME.items():
        for eti, (pv, pt, tag) in MODELLI.items():
            A, T, O = [], [], []
            for s in range(a.semi):
                bv = blocchi(f"{a.dir}/{pv}_{c}_s{s}.npz", tag)
                bt = blocchi(f"{a.dir}/{pt}_{c}_s{s}.npz", tag)
                if not (bv and bt):
                    break
                Pt = np.concatenate([x[0] for x in bt])
                Yt = np.concatenate([x[1] for x in bt])
                A.append(f1_macro(Pt, Yt))
                T.append(f1_macro(Pt, Yt, tara(bv, a.griglia)))
                O.append(f1_macro(Pt, Yt, tara(bt, a.griglia)))
            if len(A) < 3:
                print(f"{n:10s} {eti:11s} dump incompleti ({len(A)}/{a.semi})")
                continue
            am, tm, om = np.mean(A), np.mean(T), np.mean(O)
            r = 100 * (tm - am) / am
            rec.setdefault(c, {})[eti] = r
            print(f"{n:10s} {eti:11s} {am:8.4f} {tm:8.4f} {r:+9.2f}% "
                  f"{100*(om-am)/am:+8.2f}% {len(A):5d}")
        print()

    if rec:
        print("RAPPORTO fra i due recuperi")
        print(f"{'contesto':10s} {'rete':>9} {'tabellare':>10} {'rapporto':>9}")
        rr = []
        for c, d in rec.items():
            if len(d) < 2:
                continue
            q = d["rete"] / d["tabellare"] if abs(d["tabellare"]) > 1e-9 else float("nan")
            rr.append(q)
            print(f"{NOME[c]:10s} {d['rete']:+8.2f}% {d['tabellare']:+9.2f}% "
                  f"{q:8.1f}x")
        if rr:
            rr = np.array([x for x in rr if np.isfinite(x)])
            print(f"\n  intervallo del rapporto: {rr.min():.1f}x ÷ {rr.max():.1f}x")
        print("\n  Il rapporto e' informativo solo dove ENTRAMBI i recuperi sono")
        print("  positivi: se il riferimento peggiora con la taratura, il quoziente")
        print("  cambia segno e non misura piu' un rapporto fra guadagni.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
