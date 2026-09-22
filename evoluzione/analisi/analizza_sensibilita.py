#!/usr/bin/env python3
"""
Sensibilita' al budget: 2.290 contro 4.580 aggiornamenti.
==========================================================
**La domanda, delimitata**: raddoppiare il budget modifica sostanzialmente le
differenze fra C, P ed E osservate sulla validazione?

**Non serve a cercare un plateau.** Il tetto principale resta 2.290; questa
analisi quantifica il limite di quella scelta.

Si riportano:

    1. la RIPRODUZIONE: le nuove traiettorie coincidono coi piloti originari
       fino a 2.290?
    2. il GUADAGNO per famiglia, da 2.290 a 4.580
    3. le DIFFERENZE fra famiglie ai due budget, e quanto cambiano
    4. l'ORDINE fra famiglie: e' lo stesso?

**Se le differenze cambiano molto**, le conclusioni vanno circoscritte al
budget usato, e il confronto non si presenta come indipendente dal tempo di
addestramento.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_sensibilita.py
"""
import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np

CONTESTI = ("Madrid", "Londra", "Melbourne")
MODELLI = ("C", "P", "E")
PRINCIPALE, ESTESO = 2290, 4580


def vfull(t, u):
    r = next((x for x in t["curve"] if x["aggiornamento"] == u), None)
    return None if r is None else r["V-full"]


def main() -> int:
    ap = argparse.ArgumentParser(description="sensibilita' al budget")
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/adeguatezza"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    T = {(t["contesto"], t["modello"], t["seme"]): t
         for t in (json.loads(p.read_text())
                   for p in sorted(a.dir.glob("traj_*.json")))}
    O = {(t["contesto"], t["modello"], t["seme"]): t
         for t in (json.loads(p.read_text())
                   for p in sorted((a.dir / "originali").glob("traj_*.json")))}

    print("=" * 84)
    print(f"SENSIBILITA' AL BUDGET — {PRINCIPALE} contro {ESTESO} aggiornamenti")
    print("=" * 84)

    # ---- [1] riproduzione ------------------------------------------------
    print("\n[1] RIPRODUZIONE dei piloti originari, fino a 2.290\n")
    sc = []
    for k, t in T.items():
        o = O.get(k)
        if o is None:
            continue
        com = {r["aggiornamento"]: r["V-full"] for r in o["curve"]}
        s = [abs(r["V-full"] - com[r["aggiornamento"]]) for r in t["curve"]
             if r["aggiornamento"] in com]
        sc.append(max(s) if s else float("nan"))
    sc = np.array(sc)
    print(f"  traiettorie confrontate: {len(sc)}")
    print(f"  scarto massimo su tutte: {np.nanmax(sc):.2e}")
    print(f"  identiche a scarto zero: {int((sc == 0).sum())}/{len(sc)}")
    riprodotte = bool(np.nanmax(sc) <= 1e-6)
    print(f"  > {'RIPRODUZIONE ESATTA' if np.nanmax(sc) == 0 else 'riproduzione entro 1e-6' if riprodotte else 'DIVERGENZE: da indagare'}")

    # ---- [2] guadagno per famiglia ----------------------------------------
    print(f"\n[2] GUADAGNO da {PRINCIPALE} a {ESTESO}, mediato sui semi\n")
    print(f"  {'citta':11s} {'mod':4s} {'a 2290':>9} {'a 4580':>9} "
          f"{'guadagno':>10}")
    M = {}
    for c in CONTESTI:
        for mo in MODELLI:
            ks = [k for k in T if k[0] == c and k[1] == mo]
            v2 = np.mean([vfull(T[k], PRINCIPALE) for k in ks])
            v4 = np.mean([vfull(T[k], ESTESO) for k in ks])
            M[(c, mo)] = (v2, v4)
            print(f"  {c:11s} {mo:4s} {v2:9.5f} {v4:9.5f} "
                  f"{(v2-v4)/v2:+9.2%}")
    g = np.array([(v2 - v4) / v2 for v2, v4 in M.values()])
    print(f"\n  guadagno: mediana {np.median(g):+.2%}, massimo {g.max():+.2%}")

    # ---- [3] differenze fra famiglie --------------------------------------
    print(f"\n[3] DIFFERENZE fra famiglie ai due budget\n")
    print(f"  {'citta':11s} {'coppia':7s} {'a 2290':>10} {'a 4580':>10} "
          f"{'variazione':>11} {'relativa':>10}")
    var = []
    for c in CONTESTI:
        for x, y in combinations(MODELLI, 2):
            d2 = M[(c, x)][0] - M[(c, y)][0]
            d4 = M[(c, x)][1] - M[(c, y)][1]
            rel = (d4 - d2) / abs(d2) if abs(d2) > 1e-9 else float("nan")
            var.append(rel)
            print(f"  {c:11s} {x}-{y:5s} {d2:+10.5f} {d4:+10.5f} "
                  f"{d4-d2:+11.5f} {rel:+9.1%}")
    var = np.array([v for v in var if np.isfinite(v)])
    print(f"\n  variazione relativa delle differenze:")
    print(f"     mediana {np.median(np.abs(var)):.1%} | "
          f"massimo {np.abs(var).max():.1%}")

    # ---- [4] l'ordine ------------------------------------------------------
    print(f"\n[4] ORDINE fra famiglie\n")
    stesso = 0
    for c in CONTESTI:
        o2 = sorted(MODELLI, key=lambda mo: M[(c, mo)][0])
        o4 = sorted(MODELLI, key=lambda mo: M[(c, mo)][1])
        stesso += o2 == o4
        print(f"  {c:11s} a 2290: {' < '.join(o2)}   a 4580: "
              f"{' < '.join(o4)}   {'STESSO' if o2 == o4 else 'CAMBIA'}")
    print(f"\n  ordine invariato in {stesso}/{len(CONTESTI)} citta'")

    # ---- [5] il MIGLIORE selezionato, non il finale -----------------------
    print(f"\n[5] MIGLIORE su V-full, non il valore FINALE\n")
    print("  [2]-[4] riportano i valori ALL'AGGIORNAMENTO FINALE. Il minimo")
    print("  sull'insieme ESTESO non puo' peggiorare: i punti precedenti")
    print("  restano disponibili.\n")
    print(f"  {'citta':11s} {'mod':4s} {'min<=2290':>10} {'min<=4580':>10} "
          f"{'guadagno':>10}")
    Mb = {}
    for c in CONTESTI:
        for mo in MODELLI:
            ks = [k for k in T if k[0] == c and k[1] == mo]
            b2 = np.mean([min(r["V-full"] for r in T[k]["curve"]
                              if r["aggiornamento"] <= PRINCIPALE) for k in ks])
            b4 = np.mean([min(r["V-full"] for r in T[k]["curve"]
                              if r["aggiornamento"] <= ESTESO) for k in ks])
            Mb[(c, mo)] = (b2, b4)
            print(f"  {c:11s} {mo:4s} {b2:10.5f} {b4:10.5f} "
                  f"{(b2-b4)/b2:+9.2%}")
    peg = [k for k, (b2, b4) in Mb.items() if b4 > b2 + 1e-12]
    print(f"\n  peggioramenti sul MIGLIORE: {len(peg)} "
          f"({'nessuno, come deve' if not peg else peg})")

    # ---- [6] l'ordine PER SEME, non solo sulle medie -----------------------
    print(f"\n[6] ORDINE per SEME, al budget principale\n")
    per_seme = 0
    tot = 0
    for c in CONTESTI:
        semi = sorted({k[2] for k in T if k[0] == c})
        for s in semi:
            v = {mo: vfull(T[(c, mo, s)], PRINCIPALE) for mo in MODELLI
                 if (c, mo, s) in T}
            o = sorted(v, key=v.get)
            tot += 1
            ok = o == ["E", "P", "C"]
            per_seme += ok
            print(f"  {c:11s} seme {s}: {' < '.join(o)}  "
                  f"{'' if ok else '<- DIVERSO dalla media'}")
    print(f"\n  ordine E < P < C in {per_seme}/{tot} combinazioni seme-citta'")
    if per_seme < tot:
        print(f"  > l'ordinamento riguarda le MEDIE, non ogni inizializzazione")

    print(f"\n{'=' * 84}")
    print("  La lettura non e' «2.290 e' adeguato»: e' QUANTO le differenze")
    print("  dipendano dal budget. Se cambiano molto, le conclusioni si")
    print("  circoscrivono al budget usato.")

    if a.out:
        a.out.write_text(json.dumps(
            {"riproduzione_scarto_massimo": float(np.nanmax(sc)),
             "guadagno_mediano": float(np.median(g)),
             "variazione_differenze_mediana": float(np.median(np.abs(var))),
             "variazione_differenze_massima": float(np.abs(var).max()),
             "ordine_invariato": stesso,
             "per_combinazione": {f"{c}/{m}": list(v)
                                  for (c, m), v in M.items()}},
            indent=2, ensure_ascii=False))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
