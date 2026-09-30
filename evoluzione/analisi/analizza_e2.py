#!/usr/bin/env python3
"""
E2 — i tre confronti PRE-REGISTRATI, con ricampionamento dei nodi.
===================================================================
    1. F0' - C        il costo di trasferimento e' rimosso?
    2. F0' - F0       quanto ne era «embedding medio»?
    3. F' - C         l'adattamento vale, se il punto di partenza e' sano?

> **Successo = (1) soddisfatto in 3 citta' su 3** — intervallo che include lo
> zero o e' negativo — **e (3) negativo con intervallo che esclude lo zero in
> almeno 2.**

Di supporto: F0' - F0mean' (effetto del solo token) e F' - F.

**Lettura ESPLORATIVA dichiarata**, non pre-registrata: la relazione fra la
distanza del token dalla media e la prestazione di F0'.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_e2.py
"""
import argparse
import json
from pathlib import Path

import numpy as np

CITTA = ("Madrid", "Londra", "Melbourne")
B = 4000
CONFRONTI = (("F0p", "C", "1. F0' - C      trasferimento", True),
             ("F0p", "F0", "2. F0' - F0     embedding medio", False),
             ("Fp", "C", "3. F' - C       adattamento", True),
             ("F0p", "F0meanp", "   F0' - F0mean' token", False),
             ("Fp", "F", "   F' - F       supporto", False))


def wce(A, Bm, idx=None):
    a = A if idx is None else A[idx]
    b = Bm if idx is None else Bm[idx]
    num, den = a.sum(0), b.sum(0)
    return float(np.nanmean(np.where(den > 0, num / np.maximum(den, 1e-12),
                                     np.nan)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2", type=Path,
                    default=Path("results/evoluzione/predizioni_e2"))
    ap.add_argument("--f0", type=Path,
                    default=Path("results/evoluzione/predizioni_f0"))
    ap.add_argument("--altri", type=Path,
                    default=Path("results/evoluzione/predizioni_fase3"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    rng = np.random.default_rng(20260930)
    print("=" * 88)
    print("E2 — il costo di trasferimento e' rimosso dall'addestramento "
          "con token ignoto?")
    print("=" * 88)
    fuori, esito1, esito3 = {}, [], []
    for c in CITTA:
        d, manca = {}, []
        for f in sorted(a.e2.glob(f"F0p_{c}_p*_s*.npz")):
            p = int(f.stem.split("_p")[1].split("_")[0])
            s = int(f.stem.split("_s")[1])
            for b_, dirs in (("F0p", a.e2), ("F0meanp", a.e2), ("Fp", a.e2),
                             ("F0", a.f0), ("F", a.altri), ("C", a.altri)):
                g = dirs / f"{b_}_{c}_p{p}_s{s}.npz"
                if g.exists():
                    d[(b_, p, s)] = np.load(g, allow_pickle=True)
                else:
                    manca.append(g.name)
        if manca:
            print(f"\n{c}: mancano {len(manca)} file, per esempio {manca[0]}")
            continue
        parts = sorted({k[1] for k in d}); semi = sorted({k[2] for k in d})
        K = d[("F0p", parts[0], semi[0])]["A_per_nodo"].shape[0]
        print(f"\n{c}  {len(semi)} semi x {len(parts)} partizioni, {K} nodi")
        print(f"  {'confronto':28s} {'media':>10} {'IC95 con nodi':>26}")
        for n1, n2, eti, chiave in CONFRONTI:
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
            fuori[f"{c}/{n1}-{n2}"] = {"media": m0, "ic_con_nodi": q.tolist()}
            zero = q[0] * q[1] <= 0
            print(f"  {eti:28s} {m0:+10.5f} [{q[0]:+.5f}, {q[1]:+.5f}]"
                  + ("   include lo zero" if zero else ""))
            if eti.startswith("1."):
                esito1.append(zero or q[1] < 0)
            if eti.startswith("3."):
                esito3.append(q[1] < 0)

    print("\n" + "=" * 88)
    print("CRITERIO PRE-REGISTRATO")
    print("=" * 88)
    print(f"  (1) F0' - C non positivo in {sum(esito1)}/3 citta'  "
          f"{'soddisfatto' if sum(esito1) == 3 else 'NON soddisfatto'}")
    print(f"  (3) F' - C negativo con intervallo che esclude lo zero in "
          f"{sum(esito3)}/3  {'soddisfatto' if sum(esito3) >= 2 else 'NON soddisfatto'}")
    ok = sum(esito1) == 3 and sum(esito3) >= 2
    print(f"\n  > **{'SUCCESSO' if ok else 'NON SODDISFATTO'}**: "
          + ("il costo di trasferimento e' rimosso dall'addestramento con "
             "token ignoto, e l'adattamento locale resta utile"
             if ok else "si riportano gli effetti circoscritti"))
    if a.out:
        a.out.write_text(json.dumps(fuori, indent=2))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
