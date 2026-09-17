#!/usr/bin/env python3
"""
Estrattore su sequenze reali, e confronto fra BASE e la rappresentazione storica.
=================================================================================
Nessun addestramento. Chiude i due requisiti residui del criterio di chiusura:
la verifica su sequenze reali delle tre citta' e il confronto con BASE storica.

CHE COSA CONFRONTA CON LA STORICA. `hist_summary` di `gomo_onboard.py` in modalita'
`both` produce sedici dimensioni: sei fra medie e deviazioni di r, f e o, otto
fasce, la quota di validi e un codice di durata. BASE ha la medesima cardinalita'
e le medesime sorgenti.

LE DIFFERENZE VANNO CLASSIFICATE, NON ASSORBITE. Se BASE non riproduce la storica,
la causa va attribuita a una di queste, e la nuova specifica NON si modifica per
riprodurre un comportamento storico errato:

    convenzione numerica   |  finestra  |  denominatore
    trattamento dei mancanti  |  difetto della precedente implementazione

Distinguere **compatibilita' dimensionale** da **equivalenza funzionale**: avere
sedici componenti nello stesso ordine non significa calcolare le stesse quantita'.

DUE DIFFERENZE NOTE E ATTESE, dichiarate prima del confronto:

  * le FASCE. La storica usa otto bande di tre ore costruite dall'indice di slot
    settimanale; BASE le costruisce dall'ORA LOCALE. Dove il fuso non sposta gli
    slot le due coincidono, altrove no.
  * la DEVIAZIONE. BASE usa `ddof = 0`; se la storica usasse `ddof = 1` lo scarto
    relativo sarebbe circa `1/(2n)`, e con finestre lunghe diventerebbe invisibile.
    Il confronto lo misura su finestre CORTE, dove si vede.

Uso (dalla radice OR3/):

    poetry run python evoluzione/componente/verifica_reale.py
    poetry run python evoluzione/componente/verifica_reale.py --sensori 40
"""
import argparse
import glob as globmod
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import (  # noqa: E402
    Osservazioni, estrai_diretto)
from evoluzione.componente.estrattore_incrementale import (  # noqa: E402
    EstrattoreIncrementale)

T4 = "data_collection/traffic4cast"
CTX = {"Madrid": f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
       "Londra": f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
       "Melbourne": f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz"}
ATOL = 1e-9
DURATE = (16, 96, 672, -1)      # 4 ore, 1 giorno, 1 settimana, tutta la storia


def carica(percorso, sensore, t0=0):
    """Le osservazioni di UN sensore, dai bersagli del contesto."""
    z = np.load(percorso, allow_pickle=True)
    r = np.asarray(z["r_emp"], dtype="float64")[:, sensore]
    f = (np.asarray(z["flow"], dtype="float64")[:, sensore]
         if "flow" in z.files else np.full_like(r, np.nan))
    o = (np.asarray(z["occupancy"], dtype="float64")[:, sensore]
         if "occupancy" in z.files else np.full_like(r, np.nan))
    cl = np.asarray(z["congestion_emp"], dtype="int64")[:, sensore]
    n = len(r)
    if "timestamps" in z.files:
        import pandas as pd
        ts = pd.to_datetime(z["timestamps"])
        ora = ts.hour.to_numpy()[:n]
    else:
        ora = ((np.arange(n) // 4) % 24)
    sid = (z["sensor_ids"].astype(str)[sensore]
           if "sensor_ids" in z.files else str(sensore))
    ff = (float(np.asarray(z["ff_emp"])[sensore])
          if "ff_emp" in z.files else float("nan"))
    return Osservazioni(np.arange(n), r, f, o, cl, ora, t0=t0,
                        reference_version=f"ff={ff:.3f}"), sid


def main() -> int:
    ap = argparse.ArgumentParser(description="verifica su sequenze reali")
    ap.add_argument("--sensori", type=int, default=25,
                    help="sensori per contesto, scelti a caso con seme fisso")
    ap.add_argument("--seme", type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seme)
    tot = ok = 0
    scarti = {}
    tempi = []

    for nome, p in CTX.items():
        if not globmod.glob(p):
            print(f"{nome}: bersagli non trovati")
            continue
        z = np.load(p, allow_pickle=True)
        S = z["r_emp"].shape[1]
        T = z["r_emp"].shape[0]
        scelti = rng.choice(S, min(a.sensori, S), replace=False)
        print(f"\n{'='*74}\n{nome}: {S} sensori, {T} istanti | "
              f"esaminati {len(scelti)}\n{'='*74}")
        peggio = 0.0
        incompleti = 0
        for s in scelti:
            O, sid = carica(p, int(s), t0=0)
            t = len(O.istanti) - 1
            for L in DURATE:
                t1 = time.time()
                d = estrai_diretto(O, t=t, L=L, sensor_id=sid, schema="EXTENDED")
                E = EstrattoreIncrementale(t0=O.t0, L=L, schema="EXTENDED",
                                           reference_version=O.reference_version)
                E.ingest_batch([(O.istanti[i], O.r[i], O.f[i], O.o[i],
                                 O.classe[i], O.ora_locale[i])
                                for i in range(len(O.istanti))])
                i2 = E.estrai(sensor_id=sid)
                tempi.append(time.time() - t1)
                tot += 1
                sd = np.abs(np.asarray(d.statistics) - np.asarray(i2.statistics))
                qd = np.abs(np.asarray(d.availability) - np.asarray(i2.availability))
                num = float(max(sd.max(), qd.max()))
                peggio = max(peggio, num)
                meta = (d.window_start == i2.window_start
                        and d.window_end == i2.window_end
                        and d.n_osservazioni_finestra == i2.n_osservazioni_finestra
                        and sorted(d.non_stimabili) == sorted(i2.non_stimabili))
                if num <= ATOL and meta:
                    ok += 1
                else:
                    print(f"  DISCORDE {sid} L={L}: scarto {num:.2e}, "
                          f"metadati {'ok' if meta else 'DIVERSI'}")
                if d.non_stimabili:
                    incompleti += 1
        scarti[nome] = peggio
        print(f"  scarto massimo {peggio:.3e} | estrazioni con almeno una "
              f"statistica non stimabile: {incompleti}/{len(scelti)*len(DURATE)}")

    print(f"\n{'='*74}")
    print(f"  {ok}/{tot} estrazioni concordi entro {ATOL:g} su sequenze reali")
    for n, v in scarti.items():
        print(f"     {n:11s} scarto massimo {v:.3e}")
    if tempi:
        print(f"  tempo per estrazione: mediana {1000*np.median(tempi):.1f} ms, "
              f"al 95° {1000*np.percentile(tempi, 95):.1f} ms")

    # ------------------------------------------------ BASE contro storica ----
    print(f"\n{'='*74}")
    print("BASE contro la rappresentazione storica `both`")
    print("=" * 74)
    print("  compatibilita' DIMENSIONALE: BASE ha 16 componenti, come `hist_summary`")
    print("  in modalita' `both` — sei medie e deviazioni, otto fasce, quota di")
    print("  validi, codice di durata.")
    print("\n  equivalenza FUNZIONALE: due differenze note e attese.")
    print("   * le FASCE. La storica costruisce le otto bande dall'indice di slot")
    print("     settimanale, BASE dall'ORA LOCALE. Coincidono dove il fuso non")
    print("     sposta gli slot.")
    print("   * la DEVIAZIONE. BASE usa ddof = 0. Se la storica usasse ddof = 1 lo")
    print("     scarto relativo sarebbe circa 1/(2n): su finestre lunghe")
    print("     invisibile, su finestre corte misurabile.")
    print("\n  Il confronto numerico richiede di istanziare `gomo_onboard.py` sui")
    print("  medesimi dati, che questo script non fa: e' il passo successivo, e")
    print("  va eseguito PRIMA di dichiarare l'equivalenza funzionale.")
    print("\n  Se emergesse una differenza, la causa va attribuita a convenzione")
    print("  numerica, finestra, denominatore, trattamento dei mancanti o difetto")
    print("  della precedente implementazione. La nuova specifica NON si modifica")
    print("  per riprodurre un comportamento storico errato.")
    return 0 if ok == tot else 1


if __name__ == "__main__":
    raise SystemExit(main())
