#!/usr/bin/env python3
"""
Distribuzione delle classi per contesto e per perimetro.
=========================================================
Nessun addestramento: legge i soli bersagli.

PERCHE' SERVE. La frequenza della classe critica compare in dieci punti del
deliverable e assume valori diversi secondo il periodo su cui e' calcolata. Su
Londra la differenza fra addestramento e prova vale due punti e mezzo — 15,37
contro 12,81 per cento — sicche' due sottosezioni consecutive che ne riportino di
diverse sembrano contraddirsi mentre sono entrambe corrette.

Lo script stampa tutti i perimetri affiancati, cosi' che ogni valore riportato
nel documento sia attribuibile a uno di essi. Dove non lo e', non e' una
frequenza di popolazione: due dei valori oggi presenti nel documento si sono
rivelati, alla verifica, un vantaggio percentuale lungo la curva e una quota
oraria di un contesto diverso.

LA CONVENZIONE DA ADOTTARE. Il periodo di ADDESTRAMENTO, che e' quello su cui
§7.1 prescrive di calcolare i pesi della metrica: usare lo stesso perimetro per
la frequenza evita che due grandezze legate fra loro abbiano basi diverse.

Uso (dalla radice OR3/):

    poetry run python distribuzione_classi.py
    poetry run python distribuzione_classi.py --cerca 15.2 2.8
"""
import argparse
import glob as globmod

import numpy as np

GO = "data_collection/go-mo/gomo"
T4 = "data_collection/traffic4cast"
TARGETS = {
    "d8_2024":  f"{GO}/targets_2024_urb_d8.npz",
    "d15_2024": f"{GO}/targets_2024_urb_d15.npz",
    "d8_2023":  f"{GO}/targets_2023_urb_d8.npz",
    "d8_2021":  f"{GO}/targets_2021_urb_d8.npz",
    "d8_p85tr": f"{GO}/targets_2024_urb_d8_p85tr.npz",
    "t4cmad":   f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4clon":   f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4cmel":   f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
}
NOME = {"d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023",
        "d8_2021": "d8/2021", "d8_p85tr": "d8 p85tr",
        "t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne"}


def segmenti(C, tr=0.70, va=0.85):
    """I quattro perimetri. La finestra d'ingresso consuma otto istanti, che
    vanno sottratti prima di suddividere: ometterlo sposta i confini e produce
    frequenze che non corrispondono a quelle degli esperimenti."""
    e = C.shape[0] - 8
    return {"addestramento": C[: int(e * tr)],
            "validazione":   C[int(e * tr): int(e * va)],
            "prova":         C[int(e * va):],
            "intero":        C}


def main() -> int:
    ap = argparse.ArgumentParser(description="distribuzione delle classi per perimetro")
    ap.add_argument("--cerca", type=float, nargs="*", default=[],
                    help="valori da cercare fra tutte le frequenze prodotte")
    a = ap.parse_args()

    PER = ("addestramento", "validazione", "prova", "intero")
    trovati = {}

    print("=" * 88)
    print("QUOTA DELLA CLASSE CRITICA, per perimetro")
    print("=" * 88)
    print(f"{'contesto':10s} " + "".join(f"{p:>15}" for p in PER))
    D = {}
    for c, p in TARGETS.items():
        if not globmod.glob(p):
            print(f"{NOME[c]:10s} bersagli assenti")
            continue
        C = np.load(p, allow_pickle=True)["congestion_emp"]
        D[c] = segmenti(C)
        riga = []
        for k in PER:
            v = D[c][k][D[c][k] > 0]
            if not len(v):
                riga.append(f"{'—':>15}")
                continue
            q = 100 * (v == 3).mean()
            riga.append(f"{q:14.2f}%")
            trovati[(NOME[c], k)] = q
        print(f"{NOME[c]:10s} " + "".join(riga))

    print("\n" + "=" * 88)
    print("DISTRIBUZIONE DELLE TRE CLASSI sul periodo di ADDESTRAMENTO")
    print("=" * 88)
    print(f"{'contesto':10s} {'verde':>9} {'giallo':>9} {'rosso':>9}   arrotondata")
    for c in D:
        v = D[c]["addestramento"]
        v = v[v > 0]
        if not len(v):
            continue
        q = [100 * (v == k).mean() for k in (1, 2, 3)]
        print(f"{NOME[c]:10s} " + "".join(f"{x:8.2f}%" for x in q) +
              f"   {round(q[0])}/{round(q[1])}/{round(q[2])}")

    if a.cerca:
        print("\n" + "=" * 88)
        print("RICERCA DEI VALORI INDICATI")
        print("=" * 88)
        for x in a.cerca:
            vic = sorted(trovati.items(), key=lambda kv: abs(kv[1] - x))[:3]
            esatto = [k for k, v in trovati.items() if abs(v - x) < 0.05]
            if esatto:
                print(f"  {x:6.2f}% -> " +
                      ", ".join(f"{c} ({p})" for c, p in esatto))
            else:
                print(f"  {x:6.2f}% -> NESSUNA corrispondenza. I tre valori piu' "
                      f"vicini distano {abs(vic[0][1]-x):.2f}, "
                      f"{abs(vic[1][1]-x):.2f} e {abs(vic[2][1]-x):.2f} punti:")
                for (cc, pp), vv in vic:
                    print(f"           {vv:6.2f}%  {cc} ({pp})")
        print("\n  Un valore senza corrispondenza NON e' una frequenza di")
        print("  popolazione: va cercato fra le altre grandezze del documento.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
