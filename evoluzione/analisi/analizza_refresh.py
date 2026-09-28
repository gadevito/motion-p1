#!/usr/bin/env python3
"""
Confronto P-refresh contro P-frozen e C, con DUE perimetri di incertezza.
=========================================================================
    originario  ricampionamento di partizioni e inizializzazioni sulle
                metriche aggregate per esecuzione — la procedura della fase 3
    con nodi    ricampionamento anche dei NODI dentro ciascuna partizione,
                previsto dal protocollo e ora possibile

**La seconda non e' una conferma della prima**: corregge il perimetro
dell'incertezza. L'analisi congelata non si sovrascrive.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_refresh.py
"""
import argparse
import json
from pathlib import Path

import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

CITTA = ("Madrid", "Londra", "Melbourne")
FASCE = ((0, 96, "prima giornata"), (96, 672, "fino a una settimana"),
         (672, 10 ** 9, "oltre una settimana"))
B = 4000


def carica(f: Path):
    z = np.load(f, allow_pickle=True)
    return {"A": z["A_per_nodo"], "B": z["B_per_nodo"],
            "prob": z["prob"], "y": z["y"], "m": z["m"],
            "origini": z["origini"], "t1": int(z["t1"]),
            "completa": z["finestra_completa"] if "finestra_completa" in z
            else None}


def wce(A, B_, idx=None):
    a = A if idx is None else A[idx]
    b = B_ if idx is None else B_[idx]
    num, den = a.sum(0), b.sum(0)
    return float(np.nanmean(np.where(den > 0, num / np.maximum(den, 1e-12),
                                     np.nan)))


def wce_fascia(d, a_, b_, pesi):
    """wCE sulla fascia: **pesata**, come la metrica del protocollo."""
    sel = (d["origini"] - d["t1"] >= a_) & (d["origini"] - d["t1"] < b_)
    if not sel.any():
        return np.nan
    p, y, m = d["prob"][sel], d["y"][sel], d["m"][sel]
    out = []
    for h in range(m.shape[-1]):
        mm = m[..., h]
        if not mm.any():
            out.append(np.nan); continue
        pr = np.clip(p[..., h, :][mm], 1e-12, 1)
        yy = y[..., h][mm].astype("int64")
        w = pesi[yy]
        ce = -np.log(pr[np.arange(len(yy)), yy])
        out.append(float((w * ce).sum() / w.sum()))
    return float(np.nanmean(out))


def ap_macro(p, y, m):
    """Average precision macro, dalle probabilita' salvate."""
    from sklearn.metrics import average_precision_score
    mm = m.any(-1)
    v = []
    for h in range(m.shape[-1]):
        s = m[..., h]
        if s.sum() < 10:
            continue
        yy = y[..., h][s].astype(int)
        pp = p[..., h, :][s]
        try:
            v.append(average_precision_score(
                np.eye(3)[yy], pp, average="macro"))
        except Exception:                                    # noqa: BLE001
            pass
    return float(np.mean(v)) if v else np.nan


def main() -> int:
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--froz", type=Path,
                     default=Path("results/evoluzione/predizioni_fase3"))
    ap_.add_argument("--refr", type=Path,
                     default=Path("results/evoluzione/predizioni_refresh"))
    ap_.add_argument("--out", type=Path, default=None)
    a = ap_.parse_args()
    rng = np.random.default_rng(20260924)
    print("=" * 84)
    print("P-REFRESH contro P-FROZEN e C")
    print("=" * 84)
    fuori = {}
    for c in CITTA:
        ff = sorted(a.froz.glob(f"P_{c}_p*_s*.npz"))
        if not ff:
            continue
        chiavi = [(int(f.stem.split("_p")[1].split("_")[0]),
                   int(f.stem.split("_s")[1])) for f in ff]
        dati = {}
        for (p, s), f in zip(chiavi, ff):
            dati[("P", p, s)] = carica(f)
            dati[("C", p, s)] = carica(a.froz / f"C_{c}_p{p}_s{s}.npz")
            dati[("R", p, s)] = carica(a.refr / f"Prefresh_{c}_p{p}_s{s}.npz")
        parts = sorted({k[1] for k in dati}); semi = sorted({k[2] for k in dati})
        from evoluzione.analisi.pesi import carica as carica_pesi
        pesi = {p: np.asarray(carica_pesi(
            Path("results/evoluzione/pesi_griglia"), c, p).vettore(),
            dtype="float64") for p in parts}
        print(f"\n{c}  {len(chiavi)} esecuzioni, copertura finestre "
              f"{dati[('R', parts[0], semi[0])]['completa'].mean():.1%}")
        print(f"  {'confronto':22s} {'media':>10} "
              f"{'IC95 originario':>26} {'IC95 con nodi':>26}")
        for n1, n2, eti in (("R", "P", "P-refresh − P-frozen"),
                            ("R", "C", "P-refresh − C"),
                            ("P", "C", "P-frozen − C")):
            d_es = {(p, s): wce(dati[(n1, p, s)]["A"], dati[(n1, p, s)]["B"])
                    - wce(dati[(n2, p, s)]["A"], dati[(n2, p, s)]["B"])
                    for p in parts for s in semi}
            m0 = float(np.mean(list(d_es.values())))
            v1 = []
            for _ in range(B):
                ps = rng.choice(parts, len(parts), True)
                ss = rng.choice(semi, len(semi), True)
                v1.append(np.mean([d_es[(p, s)] for p in ps for s in ss]))
            K = dati[(n1, parts[0], semi[0])]["A"].shape[0]
            v2 = []
            for _ in range(B):
                ps = rng.choice(parts, len(parts), True)
                ss = rng.choice(semi, len(semi), True)
                nd = rng.integers(0, K, K)
                v2.append(np.mean([
                    wce(dati[(n1, p, s)]["A"], dati[(n1, p, s)]["B"], nd)
                    - wce(dati[(n2, p, s)]["A"], dati[(n2, p, s)]["B"], nd)
                    for p in ps for s in ss]))
            q1 = np.percentile(v1, [2.5, 97.5]); q2 = np.percentile(v2, [2.5, 97.5])
            fuori[f"{c}/{eti}"] = {"media": m0, "ic_originario": q1.tolist(),
                                   "ic_con_nodi": q2.tolist()}
            print(f"  {eti:22s} {m0:+10.5f} "
                  f"[{q1[0]:+.5f}, {q1[1]:+.5f}] "
                  f"[{q2[0]:+.5f}, {q2[1]:+.5f}]"
                  + ("" if q1[0] * q1[1] > 0 and q2[0] * q2[1] > 0
                     else "   <- una delle due include lo zero"))
        print(f"\n  {'metrica':24s} {'P-frozen':>10} {'P-refresh':>11} {'C':>10}")
        ap_v = []
        for n in ("P", "R", "C"):
            v = [ap_macro(dati[(n, p, s)]["prob"], dati[(n, p, s)]["y"],
                          dati[(n, p, s)]["m"])
                 for p in parts[:1] for s in semi[:3]]
            ap_v.append(float(np.nanmean(v)))
        print(f"  {'average precision':24s} {ap_v[0]:10.5f} {ap_v[1]:11.5f} "
              f"{ap_v[2]:10.5f}   (p0, tre semi)")
        fuori[f"{c}/average_precision"] = {"P_frozen": ap_v[0],
                                           "P_refresh": ap_v[1], "C": ap_v[2]}
        print(f"\n  {'fascia':24s} {'P-frozen':>10} {'P-refresh':>11} {'C':>10}")
        for a_, b_, nome in FASCE:
            r = []
            for n in ("P", "R", "C"):
                v = [wce_fascia(dati[(n, p, s)], a_, b_, pesi[p])
                     for p in parts for s in semi]
                r.append(float(np.nanmean(v)))
            print(f"  {nome:24s} {r[0]:10.5f} {r[1]:11.5f} {r[2]:10.5f}")
    if a.out:
        a.out.write_text(json.dumps(fuori, indent=2))
        print(f"\n  salvato in {a.out}")
    print("\n  Gli intervalli «con nodi» non confermano i precedenti: ne")
    print("  correggono il perimetro. L'analisi congelata resta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
