#!/usr/bin/env python3
"""
E3 — riaddestramento leale: i confronti PRE-REGISTRATI, con ricampionamento
dei nodi, e il conteggio delle riviste.
=============================================================================
    principale   R-orig - C      negativo = il riaddestramento leale paga;
                                 positivo = anche leale non paga a questo budget
    secondari    R-orig - R      il danno del campionamento per nodo
                 R-mon - R-orig  il valore della sorveglianza dei nodi nuovi
    descrittivo  R-mon - C

Celle (seme, partizione, nodo) appaiate; intervallo al 95% con ricampionamento
congiunto di partizioni, semi e nodi (stessa procedura di `analizza_e2`).

Il **conteggio delle riviste** per origine, iniziali contro nuovi, viene dai
manifesti del registro (`campionamento_uniforme_nodo` per R,
`campionamento_uniforme_origine` per R-orig e R-mon): per R-orig il rapporto
atteso e' 1, e si verifica.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_e3.py
    poetry run python evoluzione/analisi/analizza_e3.py --out results/evoluzione/analisi_e3.json
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
CONFRONTI = (("R-orig", "C", "1. R-orig - C     principale"),
             ("R-orig", "R", "   R-orig - R     campionamento"),
             ("R-mon", "R-orig", "   R-mon - R-orig sorveglianza"),
             ("R-mon", "C", "   R-mon - C      descrittivo"))
BRACCI = ("C", "R", "R-orig", "R-mon")


def calcola(dir_pred: Path, stampa=print) -> dict:
    rng = np.random.default_rng(SEME_BOOTSTRAP)
    fuori, celle, mancanti, principale = {}, {}, {}, {}
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
        K = d[("R-orig", parts[0], semi[0])]["A_per_nodo"].shape[0]
        # appaiamento: stessi nodi e origini in ogni cella
        for (b_, p, s), z in d.items():
            rif = d[("R-orig", p, s)]
            if (z["nodi"].tolist() != rif["nodi"].tolist()
                    or z["origini"].tolist() != rif["origini"].tolist()):
                raise RuntimeError(f"{c} p{p} s{s}: {b_} non appaiato con R-orig")
        celle[c] = {"semi": len(semi), "partizioni": len(parts), "nodi": int(K)}
        stampa(f"\n{c}  {len(semi)} semi x {len(parts)} partizioni, {K} nodi")
        stampa(f"  {'confronto':30s} {'media':>10} {'IC95 con nodi':>26}")
        for n1, n2, eti in CONFRONTI:
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
            zero = bool(q[0] * q[1] <= 0)
            fuori[f"{c}/{n1}-{n2}"] = {"media": m0, "ic_con_nodi": q.tolist(),
                                       "include_zero": zero, "etichetta": eti.strip()}
            stampa(f"  {eti:30s} {m0:+10.5f} [{q[0]:+.5f}, {q[1]:+.5f}]"
                   + ("   include lo zero" if zero else ""))
            if eti.startswith("1."):
                principale[c] = ("paga" if q[1] < 0 else
                                 "non paga" if q[0] > 0 else "non conclusivo")
    return {"confronti": fuori, "celle": celle, "mancanti": mancanti,
            "principale": principale, "repliche": B,
            "seme_bootstrap": SEME_BOOTSTRAP}


def riviste(radice: Path) -> dict:
    """Riviste per origine, iniziali contro nuovi, per R, R-orig, R-mon: dai
    manifesti completati del registro. Mediana sulle esecuzioni."""
    per_b = {b: [] for b in ("R", "R-orig", "R-mon")}
    for f in sorted((radice / "registro").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        exp = d.get("esperimento", "")
        if not exp.startswith("inserimento_griglia/") or \
                d.get("run_status") != "completato":
            continue
        b = exp.split("/", 1)[1]
        if b not in per_b:
            continue
        art = (d.get("campionamento_uniforme_nodo")
               or d.get("campionamento_uniforme_origine"))
        if not art:
            continue
        rea = art["realizzata"]
        rip = rea["ripetizioni_per_origine"]
        est = rea["estrazioni_per_nodo"]
        per_b[b].append({
            "rip_iniziali": rip["iniziali"]["media"],
            "rip_nuovi": rip["nuovi"]["media"],
            "rapporto_rip": rip["nuovi"]["media"] / max(rip["iniziali"]["media"], 1e-12),
            "estr_iniziali": est["iniziali"]["media"],
            "estr_nuovi": est["nuovi"]["media"],
            "quota_nuovi": rea["quota_realizzata_nuovi"]})
    fuori = {}
    for b, v in per_b.items():
        if not v:
            fuori[b] = {"esecuzioni": 0}
            continue
        fuori[b] = {"esecuzioni": len(v)}
        for k in ("rip_iniziali", "rip_nuovi", "rapporto_rip", "estr_iniziali",
                  "estr_nuovi", "quota_nuovi"):
            a = np.array([z[k] for z in v])
            fuori[b][k] = {"mediana": float(np.median(a)),
                           "minimo": float(a.min()), "massimo": float(a.max())}
    return fuori


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", type=Path,
                    default=Path("results/evoluzione/predizioni_fase3"))
    ap.add_argument("--radice", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    print("=" * 88)
    print("E3 — il riaddestramento LEALE batte C?")
    print("=" * 88)
    r = calcola(a.pred)
    print("\n" + "=" * 88)
    print("CRITERIO PRE-REGISTRATO: R-orig - C con intervallo che esclude lo zero")
    print("=" * 88)
    for c in CITTA:
        print(f"  {c:11s} {r['principale'].get(c, 'mancante')}")
    print("\n" + "=" * 88)
    print("CONTEGGIO DELLE RIVISTE PER ORIGINE (mediana sulle esecuzioni)")
    print("=" * 88)
    rv = riviste(a.radice)
    print(f"  {'braccio':8s} {'esec.':>5} {'iniziali':>10} {'nuovi':>10} "
          f"{'rapporto':>9} {'quota nuovi':>12}")
    for b, z in rv.items():
        if z["esecuzioni"]:
            print(f"  {b:8s} {z['esecuzioni']:5d} "
                  f"{z['rip_iniziali']['mediana']:10.2f} "
                  f"{z['rip_nuovi']['mediana']:10.2f} "
                  f"{z['rapporto_rip']['mediana']:9.3f} "
                  f"{z['quota_nuovi']['mediana']:12.4%}")
        else:
            print(f"  {b:8s}     0  (nessun manifesto)")
    r["riviste"] = rv
    if a.out:
        a.out.write_text(json.dumps(r, indent=2, ensure_ascii=False))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
