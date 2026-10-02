#!/usr/bin/env python3
"""
E3, controllo 2 — il riaddestramento peggiora la rete esistente?
==================================================================
Sui NODI INIZIALI, periodo di prova, celle appaiate (seme, partizione, nodo):

    R-orig − C     il riaddestramento leale contro il modello in esercizio
    R-orig − E     contro il modello con identita' sui soli iniziali
    R − C          il riaddestramento ingenuo
    R-mon − R-orig

Intervallo al 95% con ricampionamento congiunto di partizioni, semi e nodi.
**Se R-orig − C o R-orig − E e' positivo con intervallo che esclude lo zero,
e' un costo della politica e va in tabella** (protocol/E3.md).

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_veterani_e3.py --out results/evoluzione/veterani_e3.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.analizza_e2 import wce  # noqa: E402

CITTA = ("Madrid", "Londra", "Melbourne")
B = 4000
SEME_BOOTSTRAP = 20261002
CONFRONTI = (("R-orig", "C"), ("R-orig", "E"), ("R", "C"), ("R-mon", "R-orig"))
BRACCI = ("C", "E", "R", "R-orig", "R-mon")


def calcola(dir_pred: Path, stampa=print) -> dict:
    rng = np.random.default_rng(SEME_BOOTSTRAP)
    fuori, celle, mancanti, costo = {}, {}, {}, {}
    for c in CITTA:
        d, manca = {}, []
        for f in sorted(Path(dir_pred).glob(f"R-orig_{c}_p*_s*.npz")):
            p = int(f.stem.split("_p")[1].split("_")[0])
            s = int(f.stem.split("_s")[1])
            for b_ in BRACCI:
                g = Path(dir_pred) / f"{b_}_{c}_p{p}_s{s}.npz"
                if g.exists():
                    d[(b_, p, s)] = np.load(g, allow_pickle=True)
                else:
                    manca.append(g.name)
        if manca or not d:
            mancanti[c] = manca or ["nessun file R-orig"]
            stampa(f"\n{c}: mancano {len(mancanti[c])} file, per esempio "
                   f"{mancanti[c][0]}")
            continue
        parts = sorted({k[1] for k in d}); semi = sorted({k[2] for k in d})
        # i nodi iniziali dipendono dalla PARTIZIONE: K per partizione
        for (b_, p, s), z in d.items():
            rif = d[("R-orig", p, s)]
            if z["nodi"].tolist() != rif["nodi"].tolist():
                raise RuntimeError(f"{c} p{p} s{s}: {b_} non appaiato")
        K = {p: d[("R-orig", p, semi[0])]["A_per_nodo"].shape[0] for p in parts}
        celle[c] = {"semi": len(semi), "partizioni": len(parts),
                    "nodi_per_partizione": K}
        stampa(f"\n{c}  {len(semi)} semi x {len(parts)} partizioni, nodi "
               f"iniziali {K}")
        stampa(f"  {'confronto':18s} {'media':>10} {'IC95 con nodi':>26}")
        for n1, n2 in CONFRONTI:
            m0 = float(np.mean([
                wce(d[(n1, p, s)]["A_per_nodo"], d[(n1, p, s)]["B_per_nodo"])
                - wce(d[(n2, p, s)]["A_per_nodo"], d[(n2, p, s)]["B_per_nodo"])
                for p in parts for s in semi]))
            v = []
            for _ in range(B):
                ps = rng.choice(parts, len(parts), True)
                ss = rng.choice(semi, len(semi), True)
                nd = {p: rng.integers(0, K[p], K[p]) for p in parts}
                v.append(np.mean([
                    wce(d[(n1, p, s)]["A_per_nodo"],
                        d[(n1, p, s)]["B_per_nodo"], nd[p])
                    - wce(d[(n2, p, s)]["A_per_nodo"],
                          d[(n2, p, s)]["B_per_nodo"], nd[p])
                    for p in ps for s in ss]))
            q = np.percentile(v, [2.5, 97.5])
            zero = bool(q[0] * q[1] <= 0)
            k = f"{c}/{n1}-{n2}"
            fuori[k] = {"media": m0, "ic_con_nodi": q.tolist(), "include_zero": zero}
            stampa(f"  {n1 + ' - ' + n2:18s} {m0:+10.5f} [{q[0]:+.5f}, {q[1]:+.5f}]"
                   + ("   include lo zero" if zero else ""))
            if n1 == "R-orig" and n2 in ("C", "E"):
                costo[k] = bool(q[0] > 0)
    return {"confronti": fuori, "celle": celle, "mancanti": mancanti,
            "costo_della_politica": costo, "repliche": B,
            "seme_bootstrap": SEME_BOOTSTRAP}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", type=Path,
                    default=Path("results/evoluzione/predizioni_veterani_e3"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    print("=" * 84)
    print("E3 — VETERANI: la rete esistente prima e dopo il riaddestramento")
    print("=" * 84)
    r = calcola(a.pred)
    print("\n" + "=" * 84)
    peggio = [k for k, v in r["costo_della_politica"].items() if v]
    print("  costo della politica (R-orig peggiora la rete esistente con "
          "intervallo che esclude lo zero): "
          + (", ".join(peggio) if peggio else "NESSUNO"))
    if a.out:
        a.out.write_text(json.dumps(r, indent=2, ensure_ascii=False))
        print(f"  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
