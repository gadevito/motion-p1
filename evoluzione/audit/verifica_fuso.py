#!/usr/bin/env python3
"""
Verifica del fuso effettivo delle marche temporali.
====================================================
Nessun addestramento. Prerequisito alla costruzione delle fasce orarie: se le
marche sono in UTC e la citta' non vi coincide, `ora // 3` assegna le
osservazioni a fasce sbagliate, e la fascia notturna di Melbourne cadrebbe nel
pomeriggio.

COME SI STABILISCE SENZA DOCUMENTAZIONE. Il traffico urbano ha un profilo
giornaliero con un minimo notturno attorno alle tre o quattro del mattino LOCALI
e due massimi nelle ore di punta. Si calcola il profilo medio per ora della marca
e si osserva dove cade il minimo: se cade fra le due e le cinque, le marche sono
gia' locali; altrimenti lo scarto dice di quanto sono sfasate.

LA MISURA E' IL FLUSSO O L'OCCUPAZIONE, non il fattore di congestione: `r` e'
alto di notte — strada libera — e basso nelle ore di punta, sicche' il suo minimo
cade nelle punte e non nella notte. Il flusso ha invece il minimo dove il
traffico e' minimo, che e' quel che serve.

Lo scarto atteso, se le marche fossero in UTC:

    Madrid       UTC+1 d'inverno, UTC+2 d'estate
    Londra       UTC+0 d'inverno, UTC+1 d'estate
    Melbourne    UTC+10 d'inverno australe, UTC+11 d'estate

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/verifica_fuso.py
"""
import argparse
import glob as globmod

import numpy as np
import pandas as pd

T4 = "data_collection/traffic4cast"
CTX = {"Madrid": (f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz", "Europe/Madrid"),
       "Londra": (f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz", "Europe/London"),
       "Melbourne": (f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
                     "Australia/Melbourne")}


def main() -> int:
    ap = argparse.ArgumentParser(description="fuso delle marche temporali")
    ap.add_argument("--canale", default="flow", choices=["flow", "occupancy", "r_emp"])
    a = ap.parse_args()

    for nome, (p, fuso) in CTX.items():
        if not globmod.glob(p):
            print(f"{nome}: bersagli non trovati")
            continue
        z = np.load(p, allow_pickle=True)
        print("=" * 74)
        print(nome)
        print("=" * 74)
        if "timestamps" not in z.files:
            print("  campo `timestamps` assente: il fuso non e' verificabile qui")
            print("  le fasce andrebbero costruite dall'indice di slot, "
                  "dichiarando l'assunzione\n")
            continue
        ts = pd.to_datetime(z["timestamps"])
        print(f"  {len(ts):,} marche | da {ts.min()} a {ts.max()}")
        print(f"  fuso dichiarato nell'oggetto: {ts.tz if ts.tz else 'assente (naive)'}")

        canale = a.canale if a.canale in z.files else "r_emp"
        X = np.asarray(z[canale], dtype="float64")
        n = min(len(ts), X.shape[0])
        ore = ts.hour.to_numpy()[:n]
        prof = np.array([np.nanmean(X[:n][ore == h]) if (ore == h).any() else np.nan
                         for h in range(24)])
        vmin, vmax = int(np.nanargmin(prof)), int(np.nanargmax(prof))
        print(f"\n  profilo di `{canale}` per ora della marca:")
        sc = np.nanmax(prof) - np.nanmin(prof)
        for h in range(24):
            q = int(round(28 * (prof[h] - np.nanmin(prof)) / sc)) if sc else 0
            seg = "min" if h == vmin else "MAX" if h == vmax else "   "
            print(f"    {h:02d}  {'█'*q:<28} {prof[h]:8.2f}  {seg}")

        # il minimo notturno atteso e' fra le due e le cinque LOCALI
        atteso = range(2, 6)
        if vmin in atteso:
            print(f"\n  -> il minimo cade alle {vmin:02d}: le marche sono gia' LOCALI")
        else:
            sfas = [(vmin - x) % 24 for x in atteso]
            print(f"\n  -> il minimo cade alle {vmin:02d}, fuori dalla notte locale "
                  f"attesa (02–05)")
            print(f"     sfasamento compatibile: {sorted(set(sfas))} ore")
            print(f"     per {fuso} andrebbe applicata la conversione prima di "
                  "costruire le fasce")
        print()

    print("=" * 74)
    print("  Il canale usato e' il flusso, non il fattore di congestione: `r` e'")
    print("  alto di notte, sicche' il suo minimo cade nelle ore di punta e non")
    print("  direbbe nulla sul fuso. Con `--canale r_emp` si osserva il profilo")
    print("  inverso, e il MASSIMO diventa l'indicatore della notte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
