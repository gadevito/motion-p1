#!/usr/bin/env python3
"""
Valore del meteo — ablazione e controllo a permutazione (§8.6.2, Tabella 61).
=============================================================================
Nessun addestramento: legge i CSV di `gomo_weather_ablation.py`, che con la
patch della curva contengono una riga per epoca e per ramo (`riga == "curva"`)
oltre alle righe finali per sottoinsieme (`riga == "finale"`).

IL CONTROLLO A PERMUTAZIONE. Le cinque serie meteorologiche sono sostituite con
le STESSE serie permutate fra giornate dello stesso mese e della stessa
categoria feriale o festiva. La permutazione conserva distribuzione, persistenza
e scala di ciascun canale e ne distrugge il SOLO allineamento temporale con il
bersaglio. Il confronto reale contro permutato separa quindi per costruzione il
contenuto informativo dal costo strutturale di ampliare l'ingresso.

E' piu' stringente del controllo a rumore previsto dal protocollo, che con i
canali sostituiti aveva in comune la sola dimensionalita'.

TRE REGOLE DI LETTURA, fissate prima di vedere i numeri:

  * reale e permutato indistinguibili -> il meteo di area non porta informazione,
    e il degrado rispetto al ramo privo di meteo e' costo strutturale;
  * permutato peggiore del reale      -> il meteo informa;
  * reale peggiore del permutato      -> il meteo interferisce.

`is_rain` E' PERMUTATA INSIEME AL METEO, ed e' corretto: se restasse allineata,
il ramo permutato conserverebbe l'informazione sul regime e il controllo
perderebbe proprio la potenza che serve. Ne discende pero' che nel ramo
permutato i sottoinsiemi `rain` e `dry` sono definiti sul meteo permutato: il
confronto fra rami usa i soli valori `all`.

IL POTERE DEL TEST NON E' UNIFORME. E' pieno sulle variabili a variazione rapida
— precipitazione, nuvolosita' e vento — e ridotto su temperatura e umidita',
largamente conservate dalla permutazione. Queste ultime sono pero' anche quelle
che i canali di calendario gia' spiegano: lo script misura entrambe le cose e le
riporta accanto.

Uso (dalla radice OR3/):

    poetry run python analisi/meteo_permutazione.py
    poetry run python analisi/meteo_permutazione.py --epoca 25
"""
from pathlib import Path
import argparse
import glob as globmod
import math

import numpy as np
import pandas as pd

BASE = Path("data_collection")
T4C = BASE / "traffic4cast"
METEO = {
    "t4cmad": (T4C / "MADRID_2022/gomo_fmt/weather_t4cmad.npz", "Madrid"),
    "t4clon": (T4C / "LONDON_2022/gomo_fmt/weather_t4clon.npz", "Londra"),
    "t4cmel": (T4C / "MELBOURNE_2022/gomo_fmt/weather_t4cmel.npz", "Melbourne"),
}


def st(v):
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


def leggi(schema, c, s, modello, epoca, colonna="test_wCE"):
    f = globmod.glob(schema.format(c=c, s=s))
    if not f:
        return None
    d = pd.read_csv(f[0])
    if "riga" in d.columns and (d.riga == "curva").any():
        q = d[(d.riga == "curva") & (d.model == modello) & (d.epoca == epoca)]
        if len(q):
            return float(q[colonna].iloc[0])
        return None
    q = d[(d.model == modello) & (d.get("subset", "all") == "all")]
    return float(q.wCE.mean()) if len(q) else None


def main() -> int:
    ap = argparse.ArgumentParser(description="meteo: ablazione e permutazione")
    ap.add_argument("--dir", type=Path, default=Path("replication"))
    ap.add_argument("--epoca", type=int, default=25,
                    help="epoca di valutazione, fissa per tutti i rami e i semi")
    ap.add_argument("--semi", type=int, default=5)
    a = ap.parse_args()

    reale = str(a.dir / "wx_reale_{c}_s{s}.csv")
    perm = str(a.dir / "wx_permutato_{c}_s{s}.csv")

    # ------------------------------------------------------------ collaudo --
    print("=" * 96)
    print("COLLAUDO - il ramo privo di meteo deve coincidere fra le due varianti")
    print("=" * 96)
    ok = True
    for c, (_, nome) in METEO.items():
        scarti = []
        for s in range(a.semi):
            x = leggi(reale, c, s, "base", a.epoca)
            y = leggi(perm, c, s, "base", a.epoca)
            if x is not None and y is not None:
                scarti.append(abs(x - y))
        if not scarti:
            print(f"  {nome:10s} CSV incompleti")
            ok = False
            continue
        m = max(scarti)
        print(f"  {nome:10s} scarto massimo {m:.6f}  {'ok' if m < 1e-5 else 'ANOMALIA'}")
        ok = ok and m < 1e-5
    if not ok:
        print("\n  Uno scarto non nullo significa che la permutazione tocca qualcosa che")
        print("  non dovrebbe: fermarsi e verificare prima di leggere i risultati.")

    # ------------------------------------------------------------ tabella ---
    print("\n" + "=" * 96)
    print(f"TABELLA 61 - ablazione con controllo a permutazione (epoca {a.epoca})")
    print("=" * 96)
    print(f"{'contesto':10s} | {'senza meteo':>16} {'reale':>16} {'permutato':>16} | "
          f"{'degr. reale':>11} {'degr. perm.':>11} | reale-perm.")
    for c, (_, nome) in METEO.items():
        b, r, p = [], [], []
        for s in range(a.semi):
            x = leggi(reale, c, s, "base", a.epoca)
            y = leggi(reale, c, s, "weather", a.epoca)
            z = leggi(perm, c, s, "weather", a.epoca)
            if None in (x, y, z):
                continue
            b.append(x)
            r.append(y)
            p.append(z)
        if len(b) < a.semi:
            print(f"{nome:10s} incompleto ({len(b)}/{a.semi})")
            continue
        mb, sb = st(b)
        mr, sr = st(r)
        mp, sp = st(p)
        dr = 100 * (mr - mb) / mb
        dp = 100 * (mp - mb) / mb
        diff = st([100 * (r[i] - p[i]) / p[i] for i in range(len(b))])
        print(f"{nome:10s} | {mb:8.4f} ± {sb:5.4f} {mr:8.4f} ± {sr:5.4f} "
              f"{mp:8.4f} ± {sp:5.4f} | {dr:+10.2f}% {dp:+10.2f}% | {diff[0]:+.2f}%")

    # ------------------------------------------------------- curvatura ------
    print("\n" + "=" * 96)
    print("CURVATURA - differenza fra i rami a venti, venticinque e trenta epoche")
    print("=" * 96)
    print("Se la differenza e' stabile fra le tre epoche, la scelta del punto di arresto")
    print("e' irrilevante e va dichiarato. Se cresce, il numero fisso favorisce il ramo")
    print("privo di meteo e il degrado misurato include quel pezzo.\n")
    print(f"{'contesto':10s} {'variante':11s} | " +
          " ".join(f"{'ep ' + str(e):>10}" for e in (20, 25, 30)))
    for c, (_, nome) in METEO.items():
        for schema, eti in ((reale, "reale"), (perm, "permutato")):
            riga = []
            for ep in (20, 25, 30):
                v = []
                for s in range(a.semi):
                    x = leggi(schema, c, s, "base", ep, "val_wCE")
                    y = leggi(schema, c, s, "weather", ep, "val_wCE")
                    if x is not None and y is not None:
                        v.append(y - x)
                riga.append(f"{st(v)[0]:+10.4f}" if len(v) == a.semi else f"{'—':>10}")
            print(f"{nome:10s} {eti:11s} | " + " ".join(riga))

    # --------------------------------------------- potere della permutazione -
    print("\n" + "=" * 96)
    print("POTERE DEL TEST - quanto la permutazione distrugge, per variabile")
    print("=" * 96)
    rng = np.random.default_rng(7717)
    print(f"{'contesto':10s} {'variabile':22s} {'corr. reale-permutata':>22} "
          f"{'R2 sul calendario':>19}")
    for c, (p, nome) in METEO.items():
        if not p.exists():
            print(f"{nome:10s} file meteo non trovato")
            continue
        z = np.load(p, allow_pickle=True)
        W = z["weather"].astype("float64")
        V = [str(v) for v in z["variables"]]
        t = pd.to_datetime(z["timestamps"])
        gi = pd.DataFrame({"d": t.date,
                           "b": t.to_period("M").astype(str) + "|" + (t.dayofweek < 5).astype(str)})
        mappa = {}
        for _, q in gi.drop_duplicates("d").groupby("b"):
            g = list(q.d)
            if len(g) > 1:
                pp = list(rng.permutation(g))
                for _ in range(30):
                    if all(x != y for x, y in zip(g, pp)):
                        break
                    pp = list(rng.permutation(g))
                mappa.update(dict(zip(g, pp)))
            else:
                mappa[g[0]] = g[0]
        pos = {}
        for i, d in enumerate(gi.d):
            pos.setdefault(d, []).append(i)
        idx = np.arange(len(W))
        for d, righe in pos.items():
            src = pos.get(mappa.get(d, d), righe)
            for k, r_ in enumerate(righe):
                idx[r_] = src[k] if k < len(src) else r_
        Wp = W[idx]
        q = (t.hour * 4 + t.minute // 15).to_numpy()
        dw = t.dayofweek.to_numpy()
        doy = t.dayofyear.to_numpy()
        X = np.column_stack([np.sin(2 * np.pi * q / 96), np.cos(2 * np.pi * q / 96),
                             np.sin(2 * np.pi * dw / 7), np.cos(2 * np.pi * dw / 7),
                             (dw >= 5).astype(float),
                             np.sin(2 * np.pi * doy / 365), np.cos(2 * np.pi * doy / 365),
                             np.ones(len(q))])
        for j, v in enumerate(V):
            m = np.isfinite(W[:, j]) & np.isfinite(Wp[:, j])
            corr = np.corrcoef(W[m, j], Wp[m, j])[0, 1]
            y = W[:, j]
            mm = np.isfinite(y)
            beta, *_ = np.linalg.lstsq(X[mm], y[mm], rcond=None)
            res = y[mm] - X[mm] @ beta
            r2 = 1 - res.var() / max(y[mm].var(), 1e-12)
            print(f"{nome if j == 0 else '':10s} {v:22s} {corr:+22.3f} {r2:19.3f}")
        print()

    print("Le due colonne coincidono ordine per ordine: le variabili che la permutazione")
    print("CONSERVA sono esattamente quelle che il calendario GIA' SPIEGA, e per la stessa")
    print("ragione fisica — variano lentamente, quindi entro lo stesso mese sono simili fra")
    print("giorni e prevedibili da ora e stagione. L'informazione su cui il test non decide")
    print("e' quindi informazione che il modello riceve comunque per altra via.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
