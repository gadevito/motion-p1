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
    ap_.add_argument("--pems04", action="store_true")
    ap_.add_argument("--out", type=Path, default=None)
    a = ap_.parse_args()
    rng = np.random.default_rng(20260924)
    tutti, semi_tutti = {}, []
    print("=" * 84)
    print("P-REFRESH contro P-FROZEN e C"
          + (" — VERIFICA ESTERNA SU PEMS04" if a.pems04 else ""))
    print("=" * 84)
    fuori = {}
    citta = (("PEMS04_p0", "PEMS04_p1", "PEMS04_p2") if a.pems04 else CITTA)
    # per la STIMA AGGREGATA: i dati di ogni contesto, indicizzati per braccio
    tutti, semi_tutti = {}, []
    for c in citta:
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
        if a.pems04:
            for n in ("P", "C", "R"):
                tutti[(c, n)] = {s: dati[(n, parts[0], s)] for s in semi}
            semi_tutti = semi
        from evoluzione.analisi.pesi import carica as carica_pesi
        d_pesi = Path("results/evoluzione/"
                      + ("pesi_pems04" if a.pems04 else "pesi_griglia"))
        pesi = {p: np.asarray(carica_pesi(d_pesi, c, p).vettore(),
                              dtype="float64") for p in parts}
        for n_ in ("P", "C", "R"):
            tutti[(c, n_)] = {s: dati[(n_, p, s)] for p in parts for s in semi}
        semi_tutti = list(semi)
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
    if a.pems04:
        # ---- STIMA AGGREGATA: l'unita' di analisi e' IL DATASET ----------
        # p0, p1, p2 sono PARTIZIONI dei nodi, non contesti indipendenti: il
        # criterio riguarda i due effetti sul dataset, con uguale peso a
        # partizioni e inizializzazioni. Le partizioni restano analisi di
        # supporto.
        print(f"\n{'=' * 84}\nSTIMA AGGREGATA SU PEMS04 — l'unita' di analisi\n"
              f"{'=' * 84}")
        agg = {}
        for n1, n2, eti in (("R", "C", "Δ_C = refresh − C"),
                            ("R", "P", "Δ_F = refresh − frozen")):
            v1, v2 = [], []
            for _ in range(B):
                cs = rng.choice(len(citta), len(citta), True)
                ss = rng.choice(semi_tutti, len(semi_tutti), True)
                q1, q2 = [], []
                for i in cs:
                    c_ = citta[i]
                    K = tutti[(c_, n1)][semi_tutti[0]]["A"].shape[0]
                    nd = rng.integers(0, K, K)
                    for s_ in ss:
                        d1, d2 = tutti[(c_, n1)][s_], tutti[(c_, n2)][s_]
                        q1.append(wce(d1["A"], d1["B"]) - wce(d2["A"], d2["B"]))
                        q2.append(wce(d1["A"], d1["B"], nd)
                                  - wce(d2["A"], d2["B"], nd))
                v1.append(np.mean(q1)); v2.append(np.mean(q2))
            m0 = float(np.mean(v1))
            q_o = np.percentile(v1, [2.5, 97.5])
            q_n = np.percentile(v2, [2.5, 97.5])
            sup = float(np.percentile(v2, 95))     # UNILATERALE, come fissato
            agg[eti] = {"media": m0, "ic_originario": q_o.tolist(),
                        "ic_con_nodi": q_n.tolist(), "sup_unilaterale_95": sup}
            print(f"  {eti:22s} {m0:+.5f}  IC95 [{q_n[0]:+.5f}, {q_n[1]:+.5f}]"
                  f"  sup unilaterale {sup:+.5f}")
        fuori["PEMS04/aggregato"] = agg
        ok_tot = all(v["sup_unilaterale_95"] < 0 for v in agg.values())
        print(f"\n  > criterio congiunto sul DATASET: "
              f"**{'SODDISFATTO' if ok_tot else 'NON SODDISFATTO'}**")
        if not ok_tot:
            print("  > effetti circoscritti ed esiti non conclusivi")
        print(f"\n{'=' * 84}\nPER PARTIZIONE — analisi di supporto\n"
              f"{'=' * 84}")
        print("  affermazione solo se il limite superiore unilaterale al 95%")
        print("  e' sotto zero per ENTRAMBI i confronti, in ciascun contesto\n")
        ok_tot = True
        for c in citta:
            dC = fuori.get(f"{c}/P-refresh − C", {})
            dF = fuori.get(f"{c}/P-refresh − P-frozen", {})
            sC = dC.get("ic_con_nodi", [0, 1])[1]
            sF = dF.get("ic_con_nodi", [0, 1])[1]
            ok = sC < 0 and sF < 0
            ok_tot &= ok
            print(f"  {c:12s} sup(Δ_C) {sC:+.5f}  sup(Δ_F) {sF:+.5f}  "
                  f"{'soddisfatto' if ok else 'NON soddisfatto'}")
        print(f"\n  > **{'BENEFICIO CONFERMATO' if ok_tot else 'NON CONFERMATO'}** "
              f"nel perimetro dei tre contesti")
        if not ok_tot:
            print("  > si riportano effetti circoscritti ed esiti non "
                  "conclusivi; nessuna maggioranza trasformata in successo")
    print("\n  Gli intervalli «con nodi» non confermano i precedenti: ne")
    print("  correggono il perimetro. L'analisi congelata resta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
