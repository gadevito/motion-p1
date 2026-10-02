#!/usr/bin/env python3
"""
E4, aggiunta del 2/10 — la finestra di adattamento contiene abbastanza?
=========================================================================
Analisi DESCRITTIVA, senza addestramento. Per ogni nodo nuovo:

    celle valide     bersagli assegnati nella finestra di acquisizione
                     (t0, t1], sulle 77 origini e i 4 orizzonti: cio' che
                     l'adattamento di F ha davvero potuto usare
    copertura        quota di righe con misura valida nella finestra
    F  - C           differenza di wCE per nodo (media sui 12 semi)
    F' - C           idem dal token ignoto (E2)

Correlazione di Spearman fra celle valide e F - C (e F' - C) sui nodi, con
intervallo a ricampionamento dei nodi; e una tabella per quartili di celle
valide, con la media di F - C in ciascun quartile. **Se la correlazione c'e'**,
la politica gated di E4 prende una soglia N di osservazioni valide, scelta su
validazione; se non c'e', la copertura e' esclusa come spiegazione di Londra
dentro la citta' (E7 resta per la spiegazione fra citta').

Su PEMS04 **F non esiste** (la campagna esterna ha C, P e P-refresh): si
riporta P-refresh - C, che usa la stessa finestra, dichiarandolo come
surrogato.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_copertura_e4.py --out results/evoluzione/copertura_e4.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

CITTA = ("Madrid", "Londra", "Melbourne")
B = 2000
SEME_BOOTSTRAP = 20261002


def wce_per_nodo(z):
    A, Bm = z["A_per_nodo"], z["B_per_nodo"]
    r = np.where(Bm > 0, A / np.maximum(Bm, 1e-12), np.nan)
    return np.nanmean(r, axis=1)                        # (K,)


def celle_valide(D, nodi, o_acq, t0, t1):
    """Per nodo: bersagli assegnati sulle origini d'acquisizione x orizzonti,
    e quota di righe con misura valida in (t0, t1]."""
    from evoluzione.componente.predittore import ORIZZONTI
    nodi = np.asarray(nodi, dtype="int64")
    v = np.zeros(len(nodi), dtype="int64")
    for t in o_acq:
        for o in ORIZZONTI:
            v += (D["classe"][t + o][nodi] > 0).astype("int64")
    righe = np.arange(t0 + 1, t1 + 1)
    cop = D["m_r"][np.ix_(righe, nodi)].mean(0)
    return v, cop


def spearman_boot(x, y, rng):
    from scipy.stats import spearmanr
    r0 = float(spearmanr(x, y).statistic)
    K = len(x)
    v = []
    for _ in range(B):
        i = rng.integers(0, K, K)
        if len(np.unique(x[i])) < 3:
            continue
        v.append(spearmanr(x[i], y[i]).statistic)
    q = np.percentile(v, [2.5, 97.5])
    return r0, q.tolist()


def quartili(x, y, rng):
    """Media di y per quartile di x, con IC a ricampionamento dei nodi."""
    qs = np.percentile(x, [25, 50, 75])
    bins = np.digitize(x, qs)
    fuori = []
    for b in range(4):
        m = bins == b
        if not m.any():
            fuori.append(None); continue
        yy = y[m]
        v = [np.mean(yy[rng.integers(0, len(yy), len(yy))]) for _ in range(B)]
        fuori.append({"n_nodi": int(m.sum()),
                      "celle_valide_min": int(x[m].min()),
                      "celle_valide_max": int(x[m].max()),
                      "media": float(yy.mean()),
                      "ic_nodi": np.percentile(v, [2.5, 97.5]).tolist()})
    return fuori


def citta_principale(c, radice, rng, stampa):
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import _carica, _partizioni
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione
    _, dich, _ = configurazione(inserimento=True)
    D = _carica(c, radice / "maschere")
    ok = GR.passi_regolari(D["ts"])
    t0, t1 = CALENDARIO[c]
    o_acq = GR.origini_acquisizione(ok, t0, t1)
    X, COP, dFC, dFpC, PART = [], [], [], [], []
    manca = []
    for p in (0, 1, 2):
        nodi, _ = _partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[p])})
        nn = nodi["prova"]
        v, cop = celle_valide(D, nn, o_acq, t0, t1)
        d1, d2 = [], []
        for s in dich:
            fC = radice / "predizioni_fase3" / f"C_{c}_p{p}_s{int(s)}.npz"
            fF = radice / "predizioni_fase3" / f"F_{c}_p{p}_s{int(s)}.npz"
            fFp = radice / "predizioni_e2" / f"Fp_{c}_p{p}_s{int(s)}.npz"
            if not (fC.exists() and fF.exists() and fFp.exists()):
                manca.append(f"{c} p{p} s{s}"); continue
            zC, zF, zFp = (np.load(f, allow_pickle=True) for f in (fC, fF, fFp))
            if zC["nodi"].tolist() != [int(k) for k in nn]:
                raise RuntimeError(f"{c} p{p} s{s}: nodi non appaiati")
            wC = wce_per_nodo(zC)
            d1.append(wce_per_nodo(zF) - wC)
            d2.append(wce_per_nodo(zFp) - wC)
        if not d1:
            continue
        X.append(v); COP.append(cop)
        dFC.append(np.mean(d1, 0)); dFpC.append(np.mean(d2, 0))
        PART.append(np.full(len(nn), p))
    if not X:
        return {"mancanti": manca}
    x = np.concatenate(X); cop = np.concatenate(COP)
    y1 = np.concatenate(dFC); y2 = np.concatenate(dFpC)
    r1, q1 = spearman_boot(x, y1, rng)
    r2, q2 = spearman_boot(x, y2, rng)
    rc, qc = spearman_boot(cop, y1, rng)
    out = {"nodi": int(len(x)), "origini_acquisizione": len(o_acq),
           "celle_valide": {"min": int(x.min()), "mediana": float(np.median(x)),
                            "max": int(x.max()),
                            "massimo_possibile": len(o_acq) * 4},
           "copertura_mediana": float(np.median(cop)),
           "spearman_celle_FC": {"rho": r1, "ic_nodi": q1},
           "spearman_celle_FpC": {"rho": r2, "ic_nodi": q2},
           "spearman_copertura_FC": {"rho": rc, "ic_nodi": qc},
           "quartili_FC": quartili(x, y1, rng),
           "quartili_FpC": quartili(x, y2, rng),
           "per_nodo": {"celle_valide": x.tolist(), "copertura": cop.tolist(),
                        "F-C": y1.tolist(), "Fp-C": y2.tolist(),
                        "partizione": np.concatenate(PART).tolist()},
           "mancanti": manca}
    stampa(f"\n{c}: {len(x)} nodi nuovi, celle valide {out['celle_valide']['min']}–"
           f"{out['celle_valide']['max']} su {len(o_acq) * 4} (mediana "
           f"{out['celle_valide']['mediana']:.0f}), copertura mediana "
           f"{out['copertura_mediana']:.1%}")
    stampa(f"  Spearman(celle valide, F - C)  = {r1:+.3f} [{q1[0]:+.3f}, {q1[1]:+.3f}]")
    stampa(f"  Spearman(celle valide, F' - C) = {r2:+.3f} [{q2[0]:+.3f}, {q2[1]:+.3f}]")
    stampa(f"  Spearman(copertura,    F - C)  = {rc:+.3f} [{qc[0]:+.3f}, {qc[1]:+.3f}]")
    stampa(f"  {'quartile':10s} {'celle':>10s} {'n':>5s} {'F - C':>22s} {'F'' - C':>22s}")
    for i, (a_, b_) in enumerate(zip(out["quartili_FC"], out["quartili_FpC"])):
        if a_ is None:
            continue
        stampa(f"  Q{i + 1:<9d} {a_['celle_valide_min']:4d}–{a_['celle_valide_max']:<4d} "
               f"{a_['n_nodi']:5d} {a_['media']:+8.4f} [{a_['ic_nodi'][0]:+.4f}, "
               f"{a_['ic_nodi'][1]:+.4f}] {b_['media']:+8.4f} [{b_['ic_nodi'][0]:+.4f}, "
               f"{b_['ic_nodi'][1]:+.4f}]")
    return out


def pems04(radice, rng, stampa):
    """Surrogato: P-refresh - C e P - C per nodo, stessa finestra."""
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.predittore import ORIZZONTI
    from evoluzione.esperimenti.addestramento import _carica, _partizioni
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione
    _, dich, _ = configurazione(inserimento=True)
    X, Y1, Y2, manca = [], [], [], []
    for p, c in enumerate(("PEMS04_p0", "PEMS04_p1", "PEMS04_p2")):
        try:
            D = _carica(c, radice / "maschere")
        except Exception as e:                               # noqa: BLE001
            manca.append(f"{c}: {type(e).__name__}"); continue
        ok = GR.passi_regolari(D["ts"])
        fine = D["r"].shape[0] - max(ORIZZONTI)
        t0 = GR.primo_t0(D["ts"], ok, int(fine * .85), fine, False)
        t1 = t0 + GR.L_DESCRITTORE
        o_acq = GR.origini_acquisizione(ok, t0, t1)
        nodi, _ = _partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[p])})
        nn = nodi["prova"]
        v, _ = celle_valide(D, nn, o_acq, t0, t1)
        d1, d2 = [], []
        for s in dich:
            fC = radice / "predizioni_fase3" / f"C_{c}_p{p}_s{int(s)}.npz"
            fP = radice / "predizioni_fase3" / f"P_{c}_p{p}_s{int(s)}.npz"
            fR = radice / "predizioni_refresh" / f"Prefresh_{c}_p{p}_s{int(s)}.npz"
            if not (fC.exists() and fP.exists() and fR.exists()):
                manca.append(f"{c} s{s}"); continue
            zC, zP, zR = (np.load(f, allow_pickle=True) for f in (fC, fP, fR))
            wC = wce_per_nodo(zC)
            d1.append(wce_per_nodo(zR) - wC); d2.append(wce_per_nodo(zP) - wC)
        if d1:
            X.append(v); Y1.append(np.mean(d1, 0)); Y2.append(np.mean(d2, 0))
    if not X:
        stampa(f"\nPEMS04: file mancanti ({manca[:3]}…): analisi omessa")
        return {"mancanti": manca}
    x = np.concatenate(X); y1 = np.concatenate(Y1); y2 = np.concatenate(Y2)
    r1, q1 = spearman_boot(x, y1, rng); r2, q2 = spearman_boot(x, y2, rng)
    stampa(f"\nPEMS04 (surrogato: P-refresh - C e P - C): {len(x)} nodi nuovi, "
           f"celle valide mediana {np.median(x):.0f}")
    stampa(f"  Spearman(celle valide, P-refresh - C) = {r1:+.3f} [{q1[0]:+.3f}, {q1[1]:+.3f}]")
    stampa(f"  Spearman(celle valide, P - C)         = {r2:+.3f} [{q2[0]:+.3f}, {q2[1]:+.3f}]")
    return {"nodi": int(len(x)), "surrogato": "P-refresh - C, P - C",
            "spearman_celle_PrefreshC": {"rho": r1, "ic_nodi": q1},
            "spearman_celle_PC": {"rho": r2, "ic_nodi": q2},
            "quartili_PrefreshC": quartili(x, y1, rng), "mancanti": manca}


def figura(ris, f):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, c in zip(axs, CITTA):
        z = ris.get(c, {})
        if "per_nodo" not in z:
            ax.set_title(f"{c}: dati mancanti"); continue
        pn = z["per_nodo"]
        ax.scatter(pn["celle_valide"], pn["F-C"], s=9, alpha=.5, label="F − C")
        ax.scatter(pn["celle_valide"], pn["Fp-C"], s=9, alpha=.5, marker="x",
                   label="F′ − C")
        ax.axhline(0, color="k", lw=.8)
        ax.set_title(f"{c}  ρ={z['spearman_celle_FC']['rho']:+.2f} / "
                     f"{z['spearman_celle_FpC']['rho']:+.2f}")
        ax.set_xlabel("celle valide nelle 24 h")
    axs[0].set_ylabel("Δ wCE per nodo (media sui semi)")
    axs[0].legend()
    fig.tight_layout(); f.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(f, dpi=150)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radice", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    rng = np.random.default_rng(SEME_BOOTSTRAP)
    print("=" * 88)
    print("E4 — celle valide nella finestra di adattamento contro F - C, per nodo")
    print("=" * 88)
    ris = {c: citta_principale(c, a.radice, rng, print) for c in CITTA}
    ris["PEMS04"] = pems04(a.radice, rng, print)
    f_fig = Path("figure/copertura_e4.png")
    figura(ris, f_fig)
    ris["figura"] = str(f_fig); ris["repliche"] = B; ris["seme_bootstrap"] = SEME_BOOTSTRAP
    if a.out:
        a.out.write_text(json.dumps(ris, indent=2, ensure_ascii=False))
        print(f"\n  salvato in {a.out}; figura in {f_fig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
