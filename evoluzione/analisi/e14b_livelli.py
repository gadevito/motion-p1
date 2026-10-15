#!/usr/bin/env python3
"""
E14 stadio B — livelli assoluti di wCE per citta' (C, A, F0, F0', F'(24 h)) e rapporto (F0 − C)/(A − C).
=======================================================================================================
Sola lettura delle predizioni per cella della campagna principale (episodio 1, tre citta',
partizioni 0–2, dodici semi): `predizioni_fase3/{C,A}_*.npz`, `predizioni_f0/F0_*.npz`,
`predizioni_e2/{F0p,Fp}_*.npz`. Si esegue nell'albero congelato (`--etichetta congelata`,
`OR3_STATICA` assente) e in ogni copia dello stadio B (`--etichetta c|a|b`): stesso codice,
stesso seme di ricampionamento, cosi' il confronto fra i due e' fra numeri derivati allo
stesso modo.

Per citta': media sulle 36 celle della wCE di ogni braccio; differenze F0 − C, F0' − C, A − C,
F'(24 h) − C; rapporto (F0 − C)/(A − C) («quanto del divario C→A resta aperto a F0»); intervalli
al 95 % con ricampionamento congiunto di partizioni, semi e nodi (4.000 repliche, seme fisso).
Il rapporto si ricampiona come rapporto delle medie nella stessa replica.

Scrive `<out>/e14b_livelli_<etichetta>.json` con impronta.

Uso (dalla radice OR3/ o della copia):

    poetry run python evoluzione/analisi/e14b_livelli.py --etichetta congelata
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e4 import CITTA, _wce  # noqa: E402
from evoluzione.esperimenti.inserimento import variante_statica  # noqa: E402

B_BOOT, SEME = 4000, 20261013
SORGENTI = {"C": ("predizioni_fase3", "C"), "A": ("predizioni_fase3", "A"), "F0": ("predizioni_f0", "F0"),
            "F0p": ("predizioni_e2", "F0p"), "Fp_96": ("predizioni_e2", "Fp")}
DIFFERENZE = (("F0", "C"), ("F0p", "C"), ("A", "C"), ("Fp_96", "C"), ("F0p", "F0"))


def _carica(out: Path, c: str):
    celle = {}
    for f in sorted((out / "predizioni_fase3").glob(f"C_{c}_p*_s*.npz")):
        p = int(f.stem.split("_p")[1].split("_")[0]); s = int(f.stem.split("_s")[1])
        z = {}
        rif = None
        for nome, (cart, pref) in SORGENTI.items():
            g = out / cart / f"{pref}_{c}_p{p}_s{s}.npz"
            if not g.exists():
                raise FileNotFoundError(g)
            with np.load(g, allow_pickle=True) as q:
                z[f"A_{nome}"] = q["A_per_nodo"].astype("float64"); z[f"B_{nome}"] = q["B_per_nodo"].astype("float64")
                nodi, orig = q["nodi"].astype("int64"), q["origini"].astype("int64")
            if rif is None:
                rif = (nodi, orig)
            elif not (np.array_equal(rif[0], nodi) and np.array_equal(rif[1], orig)):
                raise RuntimeError(f"{g.name}: nodi od origini non appaiati con C")
        celle[(c, p, s)] = z
    return celle


def _livelli(celle, rng):
    kk = sorted(celle); parts = sorted({k[1] for k in kk}); semi = sorted({k[2] for k in kk})
    K = celle[kk[0]]["A_C"].shape[0]

    def w(z, n, idx):
        A, Bm = z[f"A_{n}"], z[f"B_{n}"]
        return _wce(A, Bm) if idx is None else _wce(A[idx], Bm[idx])

    def stima(idx, ps, ss):
        m = {n: float(np.mean([w(celle[(kk[0][0], p, s)], n, idx) for p in ps for s in ss])) for n in SORGENTI}
        d = {f"{a}-{b}": m[a] - m[b] for a, b in DIFFERENZE}
        r = (m["F0"] - m["C"]) / (m["A"] - m["C"]) if m["A"] != m["C"] else float("nan")
        return m, d, r

    m0, d0, r0 = stima(None, parts, semi)
    M, D, Rr = {n: [] for n in m0}, {n: [] for n in d0}, []
    for _ in range(B_BOOT):
        ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
        nd = rng.integers(0, K, K)
        m, d, r = stima(nd, ps, ss)
        for n in m:
            M[n].append(m[n])
        for n in d:
            D[n].append(d[n])
        Rr.append(r)

    def ic(v):
        q = np.nanpercentile(v, [2.5, 97.5]); return [float(q[0]), float(q[1])]
    return {"celle": len(kk), "partizioni": parts, "semi": semi, "nodi": int(K),
            "livelli": {n: {"media": m0[n], "ic": ic(M[n])} for n in m0},
            "differenze": {n: {"media": d0[n], "ic": ic(D[n]), "include_zero": bool(np.prod(ic(D[n])) <= 0)} for n in d0},
            "rapporto_F0C_su_AC": {"media": r0, "ic": ic(Rr)}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--etichetta", required=True, help="congelata | a | b | c")
    a = ap.parse_args()
    v = variante_statica()
    if (a.etichetta == "congelata") != (v == "congelata"):
        raise SystemExit(f"etichetta {a.etichetta!r} ma OR3_STATICA da' {v!r}")
    rng = np.random.default_rng(SEME)
    R = {}
    print("=" * 96)
    print(f"E14 stadio B — livelli assoluti per citta' (statica: {v})")
    print("=" * 96)
    for c in CITTA:
        celle = _carica(a.out, c)
        R[c] = _livelli(celle, rng)
        L, Dd, rr = R[c]["livelli"], R[c]["differenze"], R[c]["rapporto_F0C_su_AC"]
        print(f"\n{c}: {R[c]['celle']} celle, {R[c]['nodi']} nodi")
        print("  " + "  ".join(f"{n} {L[n]['media']:.5f} [{L[n]['ic'][0]:.5f}, {L[n]['ic'][1]:.5f}]" for n in L))
        print("  " + "  ".join(f"{n} {Dd[n]['media']:+.5f} [{Dd[n]['ic'][0]:+.5f}, {Dd[n]['ic'][1]:+.5f}]" for n in Dd))
        print(f"  (F0 - C)/(A - C) = {rr['media']:.3f} [{rr['ic'][0]:.3f}, {rr['ic'][1]:.3f}]")
    doc = {"statica": v, "etichetta": a.etichetta, "repliche": B_BOOT, "seme": SEME, "sorgenti": SORGENTI,
           "istante": datetime.now(timezone.utc).isoformat(), "per_citta": R}
    f = a.out / f"e14b_livelli_{a.etichetta}.json"
    f.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"\n  salvato in {f} (impronta {hashlib.sha256(f.read_bytes()).hexdigest()[:16]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
