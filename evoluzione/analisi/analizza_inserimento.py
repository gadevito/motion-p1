#!/usr/bin/env python3
"""
Analisi della fase 3: qualita', costo, tempo di disponibilita'.
================================================================
**Le prestazioni vengono dall'intera campagna; i costi SOLTANTO dal campione
isolato.** I tempi delle esecuzioni concorrenti si riportano come costo
operativo della sperimentazione, non per dire che un braccio sia piu' veloce.

CONFRONTI, appaiati per (citta', partizione, seme):

    P - C   il descrittore serve?
    P - F   conviene rispetto all'adattamento dell'embedding?
    P - R   conviene rispetto al riaddestramento completo?
    P - A   quanto resta dal riferimento privilegiato?

L'incertezza viene da un **ricampionamento incrociato** su semi e partizioni:
si ricampionano i semi e le partizioni, non le singole esecuzioni, perche' le
combinazioni della stessa partizione non sono indipendenti.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_inserimento.py
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

BRACCI = ("C", "P", "A", "R", "F")
CITTA = ("Madrid", "Londra", "Melbourne")
CONFRONTI = (("P", "C"), ("P", "F"), ("P", "R"), ("P", "A"), ("F", "R"))
B = 10000


def leggi(dir_c: Path):
    dati, costi = {}, defaultdict(list)
    for f in sorted(dir_c.glob("*.json")):
        if f.name.startswith("esito_"):
            continue
        d = json.loads(f.read_text())
        k = (d["contesto"], d["partizione"], d["seme"], d["braccio"])
        dati[k] = d
        if d.get("modalita_misura") == "isolata":
            costi[d["braccio"]].append(d)
    return dati, costi


def wce(d, chiave="perimetro_primario"):
    v = d["valutazione"].get(chiave)
    return None if v is None else v["perdita"]


def bootstrap(coppie, semi, parts, rng, B=B):
    """Ricampiona SEMI e PARTIZIONI, non le singole esecuzioni."""
    if not coppie:
        return (np.nan, np.nan, np.nan)
    v = []
    for _ in range(B):
        s = rng.choice(semi, len(semi), replace=True)
        p = rng.choice(parts, len(parts), replace=True)
        x = [coppie[(pp, ss)] for ss in s for pp in p if (pp, ss) in coppie]
        if x:
            v.append(float(np.mean(x)))
    a = np.array(v)
    return float(np.mean(a)), float(np.percentile(a, 2.5)), \
        float(np.percentile(a, 97.5))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/inserimento_griglia"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    dati, costi = leggi(a.dir)
    if not dati:
        print(f"nessun manifesto in {a.dir}")
        return 1
    semi = sorted({k[2] for k in dati})
    parts = sorted({k[1] for k in dati})
    print("=" * 84)
    print(f"FASE 3 — {len(dati)} esecuzioni, {len(semi)} semi, "
          f"{len(parts)} partizioni")
    print("=" * 84)

    # ---- qualita' per braccio e citta' ---------------------------------
    print("\nwCE sul perimetro primario, media su semi e partizioni\n")
    print(f"  {'citta':11s} " + "".join(f"{b:>10}" for b in BRACCI))
    med = {}
    for c in CITTA:
        riga = []
        for b in BRACCI:
            v = [wce(dati[k]) for k in dati if k[0] == c and k[3] == b
                 and wce(dati[k]) is not None]
            med[(c, b)] = float(np.mean(v)) if v else np.nan
            riga.append(med[(c, b)])
        print(f"  {c:11s} " + "".join(f"{x:10.5f}" for x in riga))

    # ---- confronti appaiati ---------------------------------------------
    print(f"\n{'=' * 84}\nDIFFERENZE APPAIATE, ricampionamento incrociato\n"
          f"{'=' * 84}")
    print("  negativo = il primo braccio ha perdita MINORE\n")
    rng = np.random.default_rng(20260923)
    fuori = {}
    for c in CITTA:
        print(f"  {c}")
        for b1, b2 in CONFRONTI:
            cop = {}
            for p in parts:
                for s in semi:
                    k1, k2 = (c, p, s, b1), (c, p, s, b2)
                    if k1 in dati and k2 in dati:
                        v1, v2 = wce(dati[k1]), wce(dati[k2])
                        if v1 is not None and v2 is not None:
                            cop[(p, s)] = v1 - v2
            m, lo, hi = bootstrap(cop, semi, parts, rng)
            fuori[f"{c}/{b1}-{b2}"] = {"media": m, "ic95": [lo, hi],
                                       "coppie": len(cop)}
            seg = "" if np.isnan(m) else (
                "  <- intervallo non contiene lo zero"
                if lo * hi > 0 else "")
            print(f"     {b1}-{b2}  {m:+.5f}  IC95 [{lo:+.5f}, {hi:+.5f}]  "
                  f"n={len(cop)}{seg}")

    # ---- fasce temporali --------------------------------------------------
    print(f"\n{'=' * 84}\nPER TEMPO DALL'INSTALLAZIONE\n{'=' * 84}")
    fasce = [x for x in ("prima giornata", "fino a una settimana",
                         "oltre una settimana")]
    print(f"  {'braccio':8s} " + "".join(f"{f[:14]:>16}" for f in fasce))
    for b in BRACCI:
        riga = []
        for f in fasce:
            v = [wce(dati[k], f) for k in dati if k[3] == b
                 and wce(dati[k], f) is not None]
            riga.append(float(np.mean(v)) if v else np.nan)
        print(f"  {b:8s} " + "".join(f"{x:16.5f}" for x in riga))

    # ---- qualita' e costo ---------------------------------------------------
    print(f"\n{'=' * 84}\nQUALITA' E COSTO\n{'=' * 84}")
    print("  **costi dal solo campione isolato**, un processo, macchina libera")
    print(f"\n  {'braccio':8s} {'wCE':>9} {'addestr.':>10} {'inserim.':>11} "
          f"{'attesa dati':>12} {'disponibile':>12}")
    qc = {}
    for b in BRACCI:
        w = [wce(dati[k]) for k in dati if k[3] == b
             and wce(dati[k]) is not None]
        ci = costi.get(b, [])
        med_ = lambda f: (float(np.median([f(x) for x in ci])) if ci
                          else float("nan"))
        qc[b] = {"wCE": float(np.mean(w)) if w else np.nan,
                 "addestramento_s": med_(lambda x: x["costo"]["addestramento_s"]),
                 "inserimento_s": med_(lambda x: x["costo"]["inserimento_s"]),
                 "attesa_dati_s": med_(
                     lambda x: x["tempo_disponibilita"]["attesa_dati_s"]),
                 "disponibilita_s": med_(
                     lambda x: x["tempo_disponibilita"]["disponibilita_s"]),
                 "esecuzioni_isolate": len(ci)}
        q = qc[b]
        print(f"  {b:8s} {q['wCE']:9.5f} {q['addestramento_s']/60:9.1f}m "
              f"{q['inserimento_s']:10.1f}s {q['attesa_dati_s']/3600:11.0f}h "
              f"{q['disponibilita_s']/3600:11.1f}h")
    print("\n  A non e' una strategia disponibile in esercizio: e' il livello")
    print("  raggiungibile avendo il nodo fin dall'inizio.")

    if a.out:
        a.out.write_text(json.dumps(
            {"esecuzioni": len(dati), "semi": semi, "partizioni": parts,
             "wCE": {f"{c}/{b}": v for (c, b), v in med.items()},
             "differenze": fuori, "qualita_costo": qc}, indent=2))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
