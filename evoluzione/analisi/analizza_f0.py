#!/usr/bin/env python3
"""
Da dove viene il vantaggio di F: adattamento locale o modello iniziale?
=======================================================================
    F  - F0   il contributo dell'ADATTAMENTO sulle ventiquattro ore
    F0 - C    il contributo del modello E con identita' PREDEFINITA
    F  - C    la somma dei due, gia' nota dalla fase 3

F0 e' lo stato di partenza di F: stesso backbone congelato, embedding del nuovo
nodo alla media degli iniziali, nessun aggiornamento. **Stesse celle.**

Incertezza: ricampionamento incrociato di partizioni, inizializzazioni e NODI,
con gli stessi ricampioni per tutti i bracci.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_f0.py
"""
import argparse
import json
from pathlib import Path

import numpy as np

CITTA = ("Madrid", "Londra", "Melbourne")
B = 4000


def wce(A, Bm, idx=None):
    a = A if idx is None else A[idx]
    b = Bm if idx is None else Bm[idx]
    num, den = a.sum(0), b.sum(0)
    return float(np.nanmean(np.where(den > 0, num / np.maximum(den, 1e-12),
                                     np.nan)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--f0", type=Path,
                    default=Path("results/evoluzione/predizioni_f0"))
    ap.add_argument("--altri", type=Path,
                    default=Path("results/evoluzione/predizioni_fase3"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    rng = np.random.default_rng(20260925)
    print("=" * 84)
    print("F0 — il vantaggio di F viene dall'adattamento o dal modello E?")
    print("=" * 84)
    fuori = {}
    for c in CITTA:
        ff = sorted(a.f0.glob(f"F0_{c}_p*_s*.npz"))
        if not ff:
            print(f"\n{c}: nessun file F0"); continue
        chiavi = [(int(f.stem.split("_p")[1].split("_")[0]),
                   int(f.stem.split("_s")[1])) for f in ff]
        d = {}
        manca = []
        for (p, s), f in zip(chiavi, ff):
            d[("F0", p, s)] = np.load(f, allow_pickle=True)
            for b_ in ("F", "C"):
                g = a.altri / f"{b_}_{c}_p{p}_s{s}.npz"
                if not g.exists():
                    manca.append(g.name); continue
                d[(b_, p, s)] = np.load(g, allow_pickle=True)
        if manca:
            print(f"\n{c}: mancano {len(manca)} file, per esempio {manca[0]}")
            continue
        parts = sorted({k[1] for k in d}); semi = sorted({k[2] for k in d})
        K = d[("F0", parts[0], semi[0])]["A_per_nodo"].shape[0]
        print(f"\n{c}  {len(semi)} semi x {len(parts)} partizioni, {K} nodi")
        print(f"  {'confronto':16s} {'media':>10} {'IC95 con nodi':>26}")
        for n1, n2, eti in (("F", "F0", "F − F0  adattamento"),
                            ("F0", "C", "F0 − C  modello E"),
                            ("F", "C", "F − C   somma")):
            m0 = float(np.mean([
                wce(d[(n1, p, s)]["A_per_nodo"], d[(n1, p, s)]["B_per_nodo"])
                - wce(d[(n2, p, s)]["A_per_nodo"], d[(n2, p, s)]["B_per_nodo"])
                for p in parts for s in semi]))
            v = []
            for _ in range(B):
                ps = rng.choice(parts, len(parts), True)
                ss = rng.choice(semi, len(semi), True)
                nd = rng.integers(0, K, K)
                v.append(np.mean([
                    wce(d[(n1, p, s)]["A_per_nodo"],
                        d[(n1, p, s)]["B_per_nodo"], nd)
                    - wce(d[(n2, p, s)]["A_per_nodo"],
                          d[(n2, p, s)]["B_per_nodo"], nd)
                    for p in ps for s in ss]))
            q = np.percentile(v, [2.5, 97.5])
            fuori[f"{c}/{eti.split()[0]}-{eti.split()[2]}"] = {
                "media": m0, "ic_con_nodi": q.tolist()}
            print(f"  {eti:16s} {m0:+10.5f} [{q[0]:+.5f}, {q[1]:+.5f}]"
                  + ("" if q[0] * q[1] > 0 else "   <- include lo zero"))
    print(f"\n{'=' * 84}")
    print("  F − F0 negativo: l'adattamento sulle ventiquattro ore contribuisce")
    print("  F0 − C positivo: il modello E con identita' predefinita NON basta")
    if a.out:
        a.out.write_text(json.dumps(fuori, indent=2))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
