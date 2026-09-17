#!/usr/bin/env python3
"""
Caratterizzazione del dataset radar di Austin (§3.4).
=====================================================
Produce tutti i numeri riportati nella sezione: record e duplicati,
intersezioni e corsie, periodo ricostruito dai campi separati, quota di
marche temporali corrotte, celle valide dopo il filtro, corsie con almeno
200 celle, quantizzazione dell'occupazione e distribuzione delle classi
secondo la convenzione di §4.2.

Due avvertenze sui dati, entrambe verificate e dichiarate nel documento:

  * il campo `curdatetime` e' corrotto sul 18,3% dei record (marca al 1970,
    da un riferimento in millisecondi letto come secondi). I campi separati
    `year/month/day/hour/minute` sono coerenti fra loro e con `timebin`, e
    sono quelli usati qui;
  * l'occupazione e' pubblicata come percentuale INTERA (mediana 4, primo
    quartile 2): ai valori bassi il denominatore del rapporto volume su
    occupazione e' fortemente quantizzato.

Il filtro trattiene volume e occupazione positivi e occupazione entro 100.
NON si filtra sulla velocita', che e' la variabile di riferimento: filtrare
sul riferimento sposterebbe la sua distribuzione. Verificato che escludere
le velocita' oltre 80 o 60 miglia orarie non altera la correlazione entro
corsia oltre la quarta cifra decimale.

Uso (dalla cartella austin/radar/, dopo `scarica.py`):

    poetry run python caratterizza_radar.py --input radar_completo.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SOGLIA_VERDE, SOGLIA_ROSSO = 0.80, 0.40   # convenzione di §4.2
MIGLIA_KM = 1.60934


def carica(percorso: Path) -> pd.DataFrame:
    d = pd.DataFrame(json.load(open(percorso)))
    for c in ("volume", "occupancy", "speed", "year", "month", "day", "hour", "minute"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description="caratterizzazione del dataset radar di Austin")
    ap.add_argument("--input", type=Path, default=Path("radar_completo.json"))
    ap.add_argument("--min-celle", type=int, default=200,
                    help="soglia di celle valide per contare una corsia")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"ERRORE: {args.input} non trovato. Esegui prima scarica.py.")
        return 1

    d = carica(args.input)
    print("=" * 84)
    print("STRUTTURA")
    print("=" * 84)
    print(f"record                 {len(d):,}")
    print(f"identificativi distinti {d.row_id.nunique():,}  (duplicati: {len(d) - d.row_id.nunique():,})")
    print(f"intersezioni            {d.intname.nunique()}")
    print(f"rilevatori              {d.detid.nunique()}")
    print(f"corsie (int x det)      {d.groupby(['intname', 'detname']).ngroups}")
    dirs = d.direction.value_counts()
    print(f"direzioni               {dict(dirs.head(6))}")
    senza_dir = sorted(d.loc[d.direction == 'None', 'intname'].unique())
    print(f"intersezioni senza direzione: {senza_dir}")
    print("  (vanno escluse dalle analisi per sezione: l'aggregazione")
    print("   mescolerebbe versi di marcia opposti)")

    print()
    print("=" * 84)
    print("COPERTURA TEMPORALE (dai campi separati, non da curdatetime)")
    print("=" * 84)
    t = pd.to_datetime(dict(year=d.year, month=d.month, day=d.day), errors="coerce")
    print(f"periodo                 {t.min().date()} -> {t.max().date()}")
    print(f"giorni distinti         {t.dt.date.nunique():,}")
    span = (t.max() - t.min()).days + 1
    print(f"giorni di calendario    {span:,}  (copertura {100 * t.dt.date.nunique() / span:.0f}%)")
    print(f"date non ricostruibili  {int(t.isna().sum())}")
    print(f"record per anno         {dict(d.year.value_counts().sort_index())}")
    tc = pd.to_datetime(d.curdatetime, errors="coerce", format="ISO8601")
    ok = tc.notna() & d.year.notna()
    disc = int((tc[ok].dt.year.values != d.year[ok].values).sum())
    print(f"curdatetime incoerente  {disc:,} record ({100 * disc / max(ok.sum(), 1):.1f}%)"
          f"  -> marca al 1970, campo scartato")

    print()
    print("=" * 84)
    print("QUALITA' E FILTRO")
    print("=" * 84)
    for c, lim in (("volume", None), ("occupancy", 100), ("speed", 80)):
        fuori = int((d[c] > lim).sum()) if lim else 0
        riga = (f"  {c:10s} validi {100 * d[c].notna().mean():5.1f}%   "
                f"zeri {100 * (d[c] == 0).mean():5.1f}%")
        if lim:
            riga += f"   oltre {lim}: {100 * fuori / len(d):5.2f}%"
        print(riga)
    filtro = (d.volume > 0) & (d.occupancy > 0) & (d.occupancy <= 100)
    x = d[filtro].copy()
    print(f"  celle valide dopo il filtro: {len(x):,} ({100 * len(x) / len(d):.1f}%)")
    print("  (nessun filtro sulla velocita': e' la variabile di riferimento)")

    x["corsia"] = x.intname + "|" + x.detname
    dim = x.groupby("corsia").size()
    print(f"  corsie con almeno {args.min_celle} celle: {int((dim >= args.min_celle).sum())} "
          f"su {len(dim)}")
    print(f"  celle per corsia: mediana {dim.median():,.0f}, "
          f"quartili [{dim.quantile(.25):,.0f}; {dim.quantile(.75):,.0f}]")

    print()
    print("=" * 84)
    print("DISTRIBUZIONE DELLE GRANDEZZE (celle valide)")
    print("=" * 84)
    for c in ("volume", "occupancy", "speed"):
        q = x[c].quantile([.05, .25, .5, .75, .95])
        print(f"  {c:10s} " + "  ".join(f"p{int(k * 100)}={v:.1f}" for k, v in q.items()))
    interi = np.allclose(x.occupancy.dropna() % 1, 0)
    print(f"  occupazione pubblicata come intero percentuale: {interi}"
          f"  (mediana {x.occupancy.median():.0f}, primo quartile {x.occupancy.quantile(.25):.0f})")
    print("  -> ai valori bassi il denominatore del rapporto volume/occupazione")
    print("     e' fortemente quantizzato: risoluzione limitata per costruzione")

    print()
    print("=" * 84)
    print(f"CLASSI DI CONGESTIONE (soglie {SOGLIA_VERDE}/{SOGLIA_ROSSO} sul percentile 85 per corsia)")
    print("=" * 84)
    ff = x.groupby("corsia").speed.transform(lambda s: s.quantile(.85))
    r = np.clip(x.speed / ff, 0, 1.5)
    cl = pd.cut(r, [-.01, SOGLIA_ROSSO, SOGLIA_VERDE, 1.6],
                labels=["rosso", "giallo", "verde"])
    fr = 100 * cl.value_counts(normalize=True)
    for k in ("verde", "giallo", "rosso"):
        print(f"  {k:8s} {fr[k]:5.2f}%")
    print("  (per confronto: contesti primari ~45/45/10, contesti a spire ~87/10/3)")
    print()
    print(f"velocita' media {x.speed.mean():.1f} miglia/h "
          f"= {x.speed.mean() * MIGLIA_KM:.1f} km/h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
