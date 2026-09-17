#!/usr/bin/env python3
"""
Audit del riferimento di flusso libero nei tre contesti primari.
=================================================================
Nessun addestramento. Ricostruisce, per Madrid, Londra e Melbourne: origine di
`free_flow_kph`, eventuale periodo di stima, e disponibilita' al momento
dell'inserimento simulato.

PERCHE' E' IL CONTROLLO CHE DECIDE. La campagna principale richiede un riferimento
FISSO e disponibile indipendentemente dalla storia accumulata dal nuovo sensore. Se
`free_flow_kph` e' un attributo esterno del segmento, il bersaglio attuale e'
utilizzabile; se e' stimato dalle osservazioni, non lo e' per un sensore appena
installato, e la specifica della normalizzazione resta aperta.

LE QUATTRO DOMANDE, e cosa le risolve:

  1. VARIA NEL TEMPO? Se il valore cambia fra intervalli del medesimo segmento, non
     e' un attributo statico ma una quantita' ricalcolata, e va capito su cosa.
  2. VARIA FRA GIORNI? Un riferimento costante entro il giorno ma diverso fra
     giorni suggerisce una stima giornaliera, quindi dipendente dalle osservazioni.
  3. E' COPERTO OVUNQUE? Un segmento privo di riferimento non ha bersaglio: la
     quota scoperta misura quanti nodi sarebbero inservibili all'inserimento.
  4. E' PLAUSIBILE COME FLUSSO LIBERO? Un riferimento pari o inferiore alla
     velocita' mediana osservata non e' una velocita' a strada sgombra, ed e' il
     segno di una stima dal regime osservato anziche' di un attributo.

COSA NON PUO' STABILIRE. Che il valore sia disponibile IN PRODUZIONE per un
segmento mai osservato. Questo dipende dal contratto con la sorgente, non dai dati
storici: se `free_flow_kph` compare solo nelle righe che hanno anche una velocita'
misurata, la sua disponibilita' a priori resta da documentare presso il fornitore.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/audit_riferimento.py
    poetry run python evoluzione/audit/audit_riferimento.py --giorni 5
"""
import argparse
import glob as globmod
from pathlib import Path

import numpy as np
import pandas as pd

T4 = "data_collection/traffic4cast"
CTX = {"MADRID_2022": "Madrid", "LONDON_2022": "Londra", "MELBOURNE_2022": "Melbourne"}


def file_velocita(citta, n):
    """I file giornalieri di `speed_classes`, in parquet o in csv."""
    # i file giornalieri stanno DENTRO speed_classes/<citta>/ e si chiamano per
    # data: cercare "speed" nel nome del file pesca invece il grafo degli archi,
    # che ha le sole colonne u e v
    for est in ("parquet", "csv", "csv.gz"):
        for schema in (f"{T4}/{citta}/speed_classes/*/speed_classes_*.{est}",
                       f"{T4}/{citta}/speed_classes/**/*.{est}",
                       f"{T4}/{citta}/**/speed_classes_*.{est}"):
            f = sorted(globmod.glob(schema, recursive=True))
            if f:
                return f[:n], schema
    return [], None


def leggi(x):
    """Parquet o csv: il pacchetto ufficiale usa il primo, ma le copie di lavoro
    possono essere state convertite."""
    if str(x).endswith(".parquet"):
        return pd.read_parquet(x)
    return pd.read_csv(x, low_memory=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="audit del riferimento di flusso libero")
    ap.add_argument("--giorni", type=int, default=3,
                    help="file giornalieri da esaminare per contesto")
    a = ap.parse_args()

    for citta, nome in CTX.items():
        print("=" * 76)
        print(f"{nome}")
        print("=" * 76)
        f, schema = file_velocita(citta, a.giorni)
        if not f:
            print(f"  file di velocita' non trovati sotto {T4}/{citta}/")
            print("  cercare a mano: find data_collection/traffic4cast/"
                  f"{citta} -name '*.parquet' | head")
            print()
            continue
        print(f"  {len(f)} file esaminati, schema {schema}")

        D = []
        for x in f:
            d = leggi(x)
            d.columns = [c.lower() for c in d.columns]
            if "free_flow_kph" not in d.columns:
                print(f"  {Path(x).name}: colonne {list(d.columns)}")
                print("  `free_flow_kph` assente: e' stato aperto il file "
                      "sbagliato, verificare lo schema di ricerca")
                break
            D.append(d.assign(_file=Path(x).name))
        if not D:
            print()
            continue
        d = pd.concat(D, ignore_index=True)
        seg = ["u", "v"] if {"u", "v"} <= set(d.columns) else [d.columns[0]]
        print(f"  {len(d):,} righe, {d.groupby(seg).ngroups:,} segmenti distinti")

        # -- 1. varia nel tempo, entro segmento? ----------------------------
        g = d.groupby(seg).free_flow_kph
        nun = g.nunique()
        print(f"\n  [1] valori distinti per segmento: mediana {nun.median():.0f}, "
              f"massimo {nun.max()}")
        print(f"      segmenti con UN solo valore: {100*(nun == 1).mean():.1f}%")
        if (nun == 1).mean() > 0.99:
            print("      -> COSTANTE nel tempo: si comporta come attributo statico")
        else:
            print("      -> VARIA: non e' un attributo statico, va capito su cosa "
                  "sia ricalcolato")

        # -- 2. varia fra giorni? -------------------------------------------
        if d._file.nunique() > 1:
            per_file = d.groupby(seg + ["_file"]).free_flow_kph.first().unstack()
            uguali = per_file.nunique(axis=1, dropna=True)
            print(f"\n  [2] segmenti con lo stesso valore in tutti i giorni: "
                  f"{100*(uguali <= 1).mean():.1f}%")

        # -- 3. copertura ----------------------------------------------------
        manc = d.free_flow_kph.isna().mean()
        nulli = (d.free_flow_kph <= 0).mean()
        print(f"\n  [3] mancanti {100*manc:.2f}%, non positivi {100*nulli:.2f}%")
        segm = d.groupby(seg).free_flow_kph.apply(lambda s: s.notna().any())
        print(f"      segmenti con almeno un riferimento: {100*segm.mean():.1f}%")

        # -- 4. plausibilita' -------------------------------------------------
        if "median_speed_kph" in d.columns:
            v = pd.to_numeric(d.median_speed_kph, errors="coerce")
            r = pd.to_numeric(d.free_flow_kph, errors="coerce")
            m = np.isfinite(v) & np.isfinite(r) & (r > 0)
            rapp = (v[m] / r[m])
            print(f"\n  [4] rapporto velocita' su riferimento: mediana "
                  f"{rapp.median():.3f}, quota sopra 1: {100*(rapp > 1).mean():.2f}%")
            print(f"      quartili [{rapp.quantile(.25):.3f}; {rapp.quantile(.75):.3f}]")
            if (rapp > 1).mean() > 0.10:
                print("      -> oltre un decimo delle osservazioni supera il "
                      "riferimento: non e' un massimo osservato")
            print(f"      riferimento: mediana {r[m].median():.1f} km/h, "
                  f"intervallo [{r[m].min():.0f}; {r[m].max():.0f}]")
        print()

    print("=" * 76)
    print("COSA QUESTO AUDIT NON PUO' STABILIRE")
    print("=" * 76)
    print("  Che il valore sia disponibile IN PRODUZIONE per un segmento mai")
    print("  osservato. Se `free_flow_kph` compare solo nelle righe che hanno anche")
    print("  una velocita' misurata, la sua disponibilita' a priori dipende dal")
    print("  contratto con la sorgente e va documentata presso il fornitore, non")
    print("  dedotta dai dati storici.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
