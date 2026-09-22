#!/usr/bin/env python3
"""
Analisi della prova di adeguatezza.
====================================
Che cosa si riporta, come prescritto:

    le quattro curve: training, V-prefix, V-full, V-rest
    i due criteri di selezione, sui MEDESIMI quindici candidati
    entrambi i punti scelti, riportati su TUTTE le popolazioni

**Il vantaggio su V-full del punto scelto su V-full e' in parte atteso per
costruzione**: non si presenta come prova indipendente di migliore
generalizzazione.

**Se la curva migliora fino al tetto, la conclusione e' «plateau non osservato
entro il budget esplorato»**, non «addestramento adeguato».

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_adeguatezza.py
"""
import argparse
import json
from pathlib import Path

import numpy as np

CONTESTI = ("Madrid", "Londra", "Melbourne")
MODELLI = ("C", "P", "E")


def seleziona(curve, chiave: str):
    """Il MINIMO fra i quindici candidati; a parita', il PRECEDENTE."""
    v = [(r["aggiornamento"], r[chiave]) for r in curve]
    m = min(z for _, z in v)
    for u, z in v:                      # in ordine crescente: il primo vince
        if z - m <= 1e-12:
            return u
    return None


def riga(curve, u):
    return next(r for r in curve if r["aggiornamento"] == u)


def main() -> int:
    ap = argparse.ArgumentParser(description="analisi dell'adeguatezza")
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/adeguatezza"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    T = [json.loads(p.read_text()) for p in sorted(a.dir.glob("traj_*.json"))]
    if not T:
        print(f"nessuna traiettoria in {a.dir}")
        return 1

    print("=" * 88)
    print(f"ANALISI DELL'ADEGUATEZZA — {len(T)} traiettorie")
    print("=" * 88)
    PUNTI = T[0]["punti"]
    print(f"  punti: {PUNTI}")
    print(f"  esposizioni nominali: "
          + ", ".join(f"{t['contesto']} {t['esposizioni_nominali']:.1f}"
                      for t in T[:3]))

    # ---- le curve, mediate sui semi ------------------------------------
    print(f"\n{'=' * 88}\nV-full, mediata sui tre semi\n{'=' * 88}")
    print(f"  {'citta':11s} {'mod':4s} " +
          "".join(f"{u:>8}" for u in PUNTI))
    med = {}
    for c in CONTESTI:
        for mo in MODELLI:
            s = [t for t in T if t["contesto"] == c and t["modello"] == mo]
            if not s:
                continue
            v = [float(np.mean([riga(t["curve"], u)["V-full"] for t in s]))
                 for u in PUNTI]
            med[(c, mo)] = v
            print(f"  {c:11s} {mo:4s} " + "".join(f"{z:8.4f}" for z in v))

    # ---- il plateau -----------------------------------------------------
    print(f"\n{'=' * 88}\nPLATEAU\n{'=' * 88}")
    print(f"  {'citta':11s} {'mod':4s} {'a 35':>9} {'al tetto':>10} "
          f"{'guadagno':>10} {'1500->2290':>12}  esito")
    plateau = {}
    for (c, mo), v in med.items():
        i35 = PUNTI.index(35)
        g = (v[i35] - v[-1]) / v[i35]
        ultimo = (v[-2] - v[-1]) / v[-2]
        pl = ultimo <= 0.0
        plateau[(c, mo)] = pl
        print(f"  {c:11s} {mo:4s} {v[i35]:9.4f} {v[-1]:10.4f} "
              f"{g:+9.2%} {ultimo:+12.3%}  "
              f"{'plateau' if pl else 'ancora in discesa'}")
    n_pl = sum(plateau.values())
    print(f"\n  {n_pl}/{len(plateau)} combinazioni hanno raggiunto il plateau")
    if n_pl < len(plateau):
        print(f"  > **PLATEAU NON OSSERVATO entro il budget esplorato**,")
        print(f"  > non «addestramento adeguato».")

    # ---- i due criteri, sui medesimi candidati ---------------------------
    print(f"\n{'=' * 88}\nI DUE CRITERI DI SELEZIONE\n{'=' * 88}")
    print(f"  minimo fra i {len(PUNTI)} candidati; a parita', il precedente")
    print(f"\n  {'citta':11s} {'mod':4s} {'seme':>5} {'u(prefix)':>10} "
          f"{'u(full)':>9} | {'prefix@p':>9} {'full@p':>9} {'rest@p':>9} "
          f"| {'prefix@f':>9} {'full@f':>9} {'rest@f':>9}")
    diff, delta_full = 0, []
    for t in T:
        up = seleziona(t["curve"], "V-prefix")
        uf = seleziona(t["curve"], "V-full")
        rp, rf = riga(t["curve"], up), riga(t["curve"], uf)
        diff += up != uf
        delta_full.append(rp["V-full"] - rf["V-full"])
        print(f"  {t['contesto']:11s} {t['modello']:4s} {t['seme']:5d} "
              f"{up:10d} {uf:9d} | {rp['V-prefix']:9.4f} {rp['V-full']:9.4f} "
              f"{rp['V-rest']:9.4f} | {rf['V-prefix']:9.4f} "
              f"{rf['V-full']:9.4f} {rf['V-rest']:9.4f}")
    d = np.array(delta_full)
    print(f"\n  i due criteri scelgono punti DIVERSI in {diff}/{len(T)} "
          f"traiettorie")
    print(f"  perdita su V-full del punto scelto su V-prefix, in eccesso:")
    print(f"     mediana {np.median(d):+.5f} | minimo {d.min():+.5f} | "
          f"massimo {d.max():+.5f}")
    print(f"\n  > **Il vantaggio su V-full del punto scelto su V-full e' in")
    print(f"  > parte ATTESO PER COSTRUZIONE**: non e' prova indipendente di")
    print(f"  > migliore generalizzazione.")

    # ---- il budget storico -----------------------------------------------
    print(f"\n{'=' * 88}\nIL BUDGET STORICO, 35 AGGIORNAMENTI\n{'=' * 88}")
    n35 = sum(1 for t in T if seleziona(t["curve"], "V-full") <= 35)
    print(f"  traiettorie in cui il minimo su V-full cade entro 35: "
          f"{n35}/{len(T)}")
    i35 = PUNTI.index(35)
    ecc = [np.mean([med[k][i35] - med[k][-1] for k in med])]
    print(f"  eccesso medio di perdita a 35 rispetto al tetto: "
          f"{ecc[0]:+.4f}")

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(
            {"punti": PUNTI, "traiettorie": len(T),
             "V_full_mediana": {f"{c}/{m}": v for (c, m), v in med.items()},
             "plateau": {f"{c}/{m}": bool(p) for (c, m), p in plateau.items()},
             "criteri_diversi": diff,
             "eccesso_su_V_full": d.tolist()},
            indent=2, ensure_ascii=False))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
