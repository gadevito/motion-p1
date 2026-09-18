#!/usr/bin/env python3
"""
Stabilita' Monte Carlo del limite di non inferiorita'.
======================================================
Nessun addestramento.

**IL LIMITE DI MELBOURNE DISTA 0,02 PUNTI DAL MARGINE**: +0,977% contro +1,000%.
Prima di cristallizzare il verdetto occorre sapere quanto quel limite dipenda
dalle repliche estratte.

CHE COSA SI MISURA. Lo stesso limite, ricalcolato con **generatori diversi** e
numerosita' crescenti. La dispersione fra ripetizioni e' la precisione Monte
Carlo: se il limite oscilla attorno all'1%, il verdetto e' **numericamente
marginale** e va dichiarato tale.

**LE RIPETIZIONI SERVONO A MISURARE LA STABILITA', NON A SCEGLIERE.** Si riporta
la dispersione e il numero di ripetizioni che cadono da ciascun lato del margine,
non il valore piu' favorevole.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/stabilita_bootstrap.py
    poetry run python evoluzione/analisi/stabilita_bootstrap.py --repliche 20000
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.analizza_raccordo import (  # noqa: E402
    CONTESTI, MARGINE, aggregati, carica, controlla, coppie_presenti,
    partizioni_presenti, pesi_classe)
from evoluzione.analisi.sensibilita_incrociata import intervalli  # noqa: E402


def prepara(dir_camp: Path, dir_pesi: Path, contesto):
    dati = {}
    W = {p: pesi_classe(contesto, p, dir_pesi).vettore()
         for p in partizioni_presenti(dir_camp, contesto)}
    for p, s in coppie_presenti(dir_camp, contesto):
        D = carica(dir_camp, contesto, p, s)
        if D is None:
            continue
        controlla(D, contesto, p, s)
        na, Sa, Wa = aggregati(D["LEGACY"], W[p])
        _, Sb, Wb = aggregati(D["BASE-CORRECTED"], W[p])
        dati[(p, s)] = (na, Sa, Wa, Sb, Wb)
    return dati


def main() -> int:
    ap = argparse.ArgumentParser(description="stabilita' del ricampionamento")
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/raccordo_appaiato"))
    ap.add_argument("--pesi", type=Path,
                    default=Path("results/evoluzione/pesi"))
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--repliche", type=int, default=20000)
    ap.add_argument("--ripetizioni", type=int, default=10)
    ap.add_argument("--definitivo", type=int, default=1000,
                    help="il generatore del risultato riportato, identificato "
                         "senza selezionarlo in funzione dell'esito")
    ap.add_argument("--procedura", default="incrociata",
                    choices=("incrociata", "originaria"))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    print("=" * 86)
    print("STABILITA' MONTE CARLO DEL LIMITE DI NON INFERIORITA'")
    print("=" * 86)
    print(f"  campagna {a.dir}")
    print(f"  procedura {a.procedura} | {a.repliche:,} repliche x "
          f"{a.ripetizioni} generatori diversi | margine +{MARGINE}%")
    print("\n  Le ripetizioni misurano la STABILITA', non scelgono il risultato:")
    print("  si riportano dispersione e conteggi, non il valore favorevole.")

    fuori = {}
    for c in a.contesto:
        dati = prepara(a.dir, a.pesi, c)
        if not dati:
            print(f"\n{c}: nessuna coppia")
            continue
        print(f"\n{'=' * 86}\n{c}\n{'=' * 86}")

        # LA CONVERGENZA SI MISURA SUL GENERATORE DEFINITIVO, lo stesso che
        # produce il risultato riportato: misurarla su un altro mescolerebbe
        # lo scostamento dovuto alla numerosita' con quello fra generatori.
        print(f"  convergenza con la numerosita' (generatore definitivo "
              f"{a.definitivo})")
        print(f"     {'repliche':>10} {'stima':>9} {'lim. NI':>10} "
              f"{'eq_inf':>9} {'eq_sup':>9}")
        conv = {}
        for n in (1000, 5000, a.repliche):
            r = intervalli(dati, n, a.procedura, seme=a.definitivo)
            if r:
                conv[n] = {k: r[k] for k in ("stima", "ni_sup", "eq_inf",
                                             "eq_sup")}
                print(f"     {n:10,} {r['stima']:+8.4f}% {r['ni_sup']:+9.4f}% "
                      f"{r['eq_inf']:+8.4f}% {r['eq_sup']:+8.4f}%")
        if 1000 in conv and a.repliche in conv:
            d = conv[a.repliche]["ni_sup"] - conv[1000]["ni_sup"]
            print(f"     scostamento del limite da 1.000 a {a.repliche:,} "
                  f"repliche: {d:+.4f} punti")

        # la dispersione fra GENERATORI diversi, a numerosita' piena
        print(f"\n  dispersione fra {a.ripetizioni} generatori, "
              f"{a.repliche:,} repliche ciascuno")
        lim, stime = [], []
        for k in range(a.ripetizioni):
            # il definitivo e' il primo: la serie lo comprende, sicche' il
            # valore riportato e' uno di quelli di cui si misura la dispersione
            r = intervalli(dati, a.repliche, a.procedura,
                           seme=a.definitivo + k)
            if r:
                lim.append(r["ni_sup"])
                stime.append(r["stima"])
        if not lim:
            continue
        lim = np.array(lim)
        sotto = int((lim < MARGINE).sum())
        print(f"     limite di non inferiorita': "
              f"minimo {lim.min():+.4f}%  mediana {np.median(lim):+.4f}%  "
              f"massimo {lim.max():+.4f}%")
        print(f"     deviazione fra ripetizioni {lim.std(ddof=1):.5f} | "
              f"escursione {lim.max()-lim.min():.5f}")
        print(f"     stima puntuale: {stime[0]:+.4f}% "
              f"(invariata: non dipende dal ricampionamento)")
        print(f"     ripetizioni sotto il margine: {sotto}/{len(lim)}")
        dist = float(MARGINE - np.median(lim))
        marginale = sotto not in (0, len(lim)) or abs(dist) < 3 * lim.std(ddof=1)
        print(f"     distanza dal margine {dist:+.4f} punti, pari a "
              f"{abs(dist)/max(lim.std(ddof=1),1e-12):.1f} deviazioni")
        if sotto == len(lim) and not marginale:
            print(f"     VERDETTO STABILE: non inferiorita' sostenuta in tutte "
                  f"le ripetizioni, e a distanza dal margine")
        elif sotto == len(lim):
            print(f"     VERDETTO NUMERICAMENTE MARGINALE: sostenuto in tutte "
                  f"le ripetizioni, ma il limite dista meno di tre deviazioni "
                  f"dal margine")
        elif sotto == 0:
            print(f"     VERDETTO STABILE: non sostenuto in alcuna ripetizione")
        else:
            print(f"     VERDETTO NUMERICAMENTE MARGINALE: il limite attraversa "
                  f"il margine fra le ripetizioni")
        fuori[c] = {"limiti": lim.tolist(), "stima": stime[0],
                    "convergenza": conv, "generatore_definitivo": a.definitivo,
                    "limite_definitivo": float(lim[0]),
                    "mediana": float(np.median(lim)),
                    "deviazione": float(lim.std(ddof=1)),
                    "sotto_margine": sotto, "ripetizioni": len(lim),
                    "marginale": bool(marginale)}

    print(f"\n{'=' * 86}")
    print("  L'escursione fra le tre INIZIALIZZAZIONI e' un'altra quantita' e")
    print("  non si confronta con il margine, che si riferisce all'effetto")
    print("  MEDIO. Qui si misura la sola precisione del ricampionamento.")
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(
            {"campagna": str(a.dir), "procedura": a.procedura,
             "repliche": a.repliche, "ripetizioni": a.ripetizioni,
             "margine": MARGINE, "generatore_definitivo": a.definitivo,
             "nota": ("la convergenza e il limite riportato vengono dal MEDESIMO "
                      "generatore: misurarli su generatori diversi "
                      "mescolerebbe lo scostamento per numerosita' con quello "
                      "fra generatori"),
             "risultati": fuori},
            indent=2, ensure_ascii=False))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
