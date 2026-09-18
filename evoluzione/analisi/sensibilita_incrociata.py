#!/usr/bin/env python3
"""
Sensibilita' del ricampionamento alla struttura INCROCIATA.
============================================================
Nessun addestramento: opera sulle predizioni gia' salvate.

IL DISEGNO E' INCROCIATO — partizione × inizializzazione — mentre la procedura
originaria estrae le inizializzazioni SEPARATAMENTE dentro ciascuna partizione.
La matrice mostra che la differenza fra varianti e' fortemente associata
all'inizializzazione e si mantiene attraverso le partizioni: su Melbourne `s0` da'
circa +4,3 e `s2` circa −0,93 su tutte e tre. L'estrazione separata **puo' non
preservare quella dipendenza fra celle della stessa colonna**.

LE DUE PROCEDURE, riportate AFFIANCATE.

    originaria   tre partizioni con reinserimento; per CIASCUNA occorrenza tre
                 inizializzazioni con reinserimento, estratte indipendentemente
    incrociata   tre partizioni con reinserimento; UNA SOLA lista di
                 inizializzazioni per replica, usata per TUTTE le partizioni
                 estratte

In entrambe: appaiamento fra varianti mantenuto, molteplicita' dei nodi
preservate, medesimo ricampionamento dei dati.

**L'ANALISI ORIGINARIA NON SI SOSTITUISCE.** Le due si affiancano, e i
cambiamenti di verdetto si dichiarano.

**CON TRE INIZIALIZZAZIONI ANCHE LA PROCEDURA ALTERNATIVA RESTA POCO INFORMATA**
sulla variabilita' dell'addestramento: la sensibilita' dice se il verdetto dipenda
dalla struttura assunta, non quale delle due sia giusta.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/sensibilita_incrociata.py
    poetry run python evoluzione/analisi/sensibilita_incrociata.py --repliche 2000
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.analizza_raccordo import (  # noqa: E402
    CONTESTI, LIVELLO_EQ, LIVELLO_NI, MARGINE, aggregati, carica, controlla,
    coppie_presenti, esito_eq, esito_ni, partizioni_presenti, perdita,
    pesi_classe)


def _stima(dati, occorrenze, c):
    """Media sulle inizializzazioni entro occorrenza, poi sulle occorrenze."""
    d = []
    for p, sel_s in occorrenze:
        e = []
        for s in sel_s:
            if (p, s) not in dati:
                continue
            _, Sa, Wa, Sb, Wb = dati[(p, s)]
            la, lb = perdita(Sa, Wa, c), perdita(Sb, Wb, c)
            if np.isfinite(la) and np.isfinite(lb) and la > 0:
                e.append(100.0 * (lb - la) / la)
        if e:
            d.append(float(np.mean(e)))
    return float(np.mean(d)) if d else np.nan


def intervalli(dati, repliche, procedura, seme=0):
    """`procedura` in {"originaria", "incrociata"}."""
    rng = np.random.default_rng(seme)
    parti = sorted({p for p, _ in dati})
    per_part = {p: sorted(s for q, s in dati if q == p) for p in parti}
    K = len(next(iter(dati.values()))[0])
    uno = np.ones(K)
    punto = _stima(dati, [(p, per_part[p]) for p in parti], uno)

    rep = []
    for _ in range(repliche):
        idx_p = rng.integers(len(parti), size=len(parti))
        if procedura == "incrociata":
            # UNA SOLA lista di inizializzazioni, condivisa fra le partizioni:
            # conserva la dipendenza fra celle della stessa colonna
            base = sorted({s for _, s in dati})
            comune = [base[j] for j in rng.integers(len(base), size=len(base))]
            occ = [(parti[i], comune) for i in idx_p]
        elif procedura == "originaria":
            occ = []
            for i in idx_p:
                p = parti[i]
                q = per_part[p]
                occ.append((p, [q[j] for j in rng.integers(len(q), size=len(q))]))
        else:
            raise ValueError(f"procedura ignota: {procedura}")
        c = np.bincount(rng.integers(K, size=K), minlength=K).astype("float64")
        x = _stima(dati, occ, c)
        if np.isfinite(x):
            rep.append(x)
    if len(rep) < 50:
        return None
    rep = np.array(rep)

    def ric(q):
        return punto + np.percentile(rep, q) - rep.mean()

    return {"stima": punto, "repliche": len(rep),
            "ni_sup": ric(100 * LIVELLO_NI),
            "eq_inf": ric(100 * (1 - LIVELLO_EQ) / 2),
            "eq_sup": ric(100 * (1 - (1 - LIVELLO_EQ) / 2)),
            "procedura": procedura}


def main() -> int:
    ap = argparse.ArgumentParser(description="sensibilita' incrociata")
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/raccordo"))
    ap.add_argument("--pesi", type=Path,
                    default=Path("results/evoluzione/pesi"))
    ap.add_argument("--repliche", type=int, default=1000)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    print("=" * 86)
    print("SENSIBILITA' DEL RICAMPIONAMENTO ALLA STRUTTURA INCROCIATA")
    print("=" * 86)
    print("  originaria: inizializzazioni estratte dentro CIASCUNA occorrenza")
    print("  incrociata: UNA lista di inizializzazioni per replica, condivisa")
    print("              fra tutte le partizioni estratte")
    print(f"\n  margine ±{MARGINE}% | {a.repliche} repliche")
    print("\n  L'analisi originaria NON e' sostituita: le due si affiancano.")

    fuori = {}
    for c in CONTESTI:
        PZ = {p: pesi_classe(c, p, a.pesi)
              for p in partizioni_presenti(a.dir, c)}
        dati = {}
        for p, s in coppie_presenti(a.dir, c):
            D = carica(a.dir, c, p, s)
            if D is None:
                continue
            controlla(D, c, p, s)                   # BLOCCANTE, come sempre
            w = PZ[p].vettore()
            na, Sa, Wa = aggregati(D["LEGACY"], w)
            nb, Sb, Wb = aggregati(D["BASE-CORRECTED"], w)
            dati[(p, s)] = (na, Sa, Wa, Sb, Wb)
        if not dati:
            print(f"\n{c}: nessuna coppia")
            continue
        print(f"\n{'=' * 86}\n{c}   ({len(dati)} coppie)\n{'=' * 86}")
        print(f"  {'procedura':13s} {'stima':>9} {'lim. NI':>9} "
              f"{'equivalenza':>20}  {'non inferiorita':<26} equivalenza")
        R = {}
        for proc in ("originaria", "incrociata"):
            r = intervalli(dati, a.repliche, proc)
            if r is None:
                print(f"  {proc:13s} ricampionamento non riuscito")
                continue
            R[proc] = {**r, "ni": esito_ni(r), "eq": esito_eq(r)}
            print(f"  {proc:13s} {r['stima']:+8.3f}% {r['ni_sup']:+8.3f}% "
                  f"[{r['eq_inf']:+7.3f};{r['eq_sup']:+7.3f}]  "
                  f"{R[proc]['ni']:<26} {R[proc]['eq']}")
        if len(R) == 2:
            o, i = R["originaria"], R["incrociata"]
            amp_o = o["eq_sup"] - o["eq_inf"]
            amp_i = i["eq_sup"] - i["eq_inf"]
            cambia = o["ni"] != i["ni"] or o["eq"] != i["eq"]
            print(f"\n  ampiezza dell'intervallo  originaria {amp_o:6.3f}  "
                  f"incrociata {amp_i:6.3f}  rapporto {amp_i/max(amp_o,1e-9):5.2f}x")
            print(f"  IL VERDETTO {'CAMBIA' if cambia else 'non cambia'} "
                  f"fra le due procedure")
            if cambia:
                print(f"     originaria: {o['ni']} / {o['eq']}")
                print(f"     incrociata: {i['ni']} / {i['eq']}")
        fuori[c] = R

    print(f"\n{'=' * 86}\nRIEPILOGO\n{'=' * 86}")
    print(f"  {'citta':11s} {'verdetto originaria':<28} verdetto incrociata")
    cambiati = 0
    for c, R in fuori.items():
        if len(R) < 2:
            continue
        o, i = R["originaria"], R["incrociata"]
        cambiati += o["ni"] != i["ni"]
        print(f"  {c:11s} {o['ni']:<28} {i['ni']}"
              + ("   <- CAMBIA" if o["ni"] != i["ni"] else ""))
    print(f"\n  verdetti che cambiano: {cambiati}/{len(fuori)}")
    print("\n  Con TRE inizializzazioni anche la procedura incrociata resta poco")
    print("  informata sulla variabilita' dell'addestramento: la sensibilita'")
    print("  dice se il verdetto dipenda dalla struttura assunta, NON quale")
    print("  delle due procedure sia corretta.")

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(
            {"margine": MARGINE, "repliche": a.repliche,
             "nota": ("l'analisi originaria non e' sostituita; le due procedure "
                      "si affiancano"),
             "risultati": fuori}, indent=2, ensure_ascii=False))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
