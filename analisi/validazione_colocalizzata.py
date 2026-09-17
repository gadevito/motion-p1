#!/usr/bin/env python3
"""
Validazione co-localizzata della ricostruzione (§8.6.4, Tabelle 65-67).
=======================================================================
Nessun addestramento: elaborazione sui dati gia' costruiti.

LA DOMANDA. La ricostruzione della velocita' da flusso e occupazione (§3.2.3) e'
usata in tre dei sei contesti. La sua validita' richiede un confronto con una
misura INDIPENDENTE di velocita'. Il confronto con le sonde (§8.6.3) non e'
co-localizzato: accoppia una spira a una sonda distante in mediana trentatre
metri, e quindi mescola l'errore della ricostruzione con quello
dell'accoppiamento.

I TRE PERIMETRI, in ordine di rigore decrescente:

  anello M30   stesso dispositivo misura flusso, occupazione E velocita'.
               Nessun errore di accoppiamento. Regime a scorrimento libero.
  Austin       stesso dispositivo, su arterie SEMAFORIZZATE e per corsia.
               E' la condizione che i primi due non danno congiuntamente.
  arterie d8   riferimento da sonde a trentatre metri. Non co-localizzato.

IL RISULTATO CENTRALE E' UNA DISSOCIAZIONE, non un'insufficienza. La
ricostruzione sbaglia il LIVELLO ovunque — anche dove il riferimento e'
co-localizzato e il regime e' a scorrimento libero — e ovunque DISCRIMINA la
classe critica. Le due grandezze sono indipendenti, ed e' la stessa dissociazione
fra affidabilita' e risoluzione misurata sul classificatore neurale.

DUE CORREZIONI CHE QUESTA VALIDAZIONE IMPONE A §8.6.3:

  1. Il regime in cui la ricostruzione funziona e' l'OPPOSTO di quello che
     sembrava. La correlazione CRESCE con l'occupazione, da -0,112 sotto il 10%
     a +0,463 sopra il 40%. L'accuratezza apparente a traffico scarso era un
     artefatto della regola di strada vuota, che impone il valore unitario e
     quindi «indovina» per costruzione.
  2. Il valore di circa 0,04 misurato sulle arterie NON misura la ricostruzione:
     misura in larga parte l'incertezza dell'accoppiamento. Sull'anello, a
     distanza comparabile, la correlazione vale +0,076 contro il +0,071 delle
     arterie.

SCALA DI GINI PER LA RIPARTIZIONE. Le differenze di area sotto la curva NON sono
additive: da 0,5 a 0,984 c'e' tutto il campo di discriminazione, da 0,726 a
0,542 una porzione molto diversa. La scala di Gini (2*AUC - 1) e' additiva e
consente di ripartire il divario. Sommare differenze di AUC e' un errore che un
revisore segna.

Uso (dalla radice OR3/):

    poetry run python analisi/validazione_colocalizzata.py
    poetry run python analisi/validazione_colocalizzata.py --sezioni anello austin
"""
from pathlib import Path
import argparse

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

GOMO = Path("data_collection/go-mo/gomo")
T4C = Path("data_collection/traffic4cast/MADRID_2022/gomo_fmt")
AUSTIN = Path("austin/radar/radar_completo.json")
OCC_VUOTA = 5.0
PCTL = 85
MIGLIA_KM = 1.60934
SOGLIA_ROSSO = 0.40


def gini(auc):
    return 2 * auc - 1


# ------------------------------------------------------------------ anello --
def carica_m30():
    z = np.load(GOMO / "targets_2024_m30.npz", allow_pickle=True)
    m = np.load(GOMO / "tensors_2024_m30.npz", allow_pickle=True)
    ids = [str(x) for x in m["sensor_ids"]]
    pos = {str(s): i for i, s in enumerate(z["sensor_ids"])}
    ti = np.array([i for i, s in enumerate(ids) if s in pos])
    gi = np.array([pos[ids[i]] for i in ti])
    sp = m["speed"].astype("float32")[:, ti]
    fl = m["flow"].astype("float32")[:, ti]
    oc = m["occupancy"].astype("float32")[:, ti]
    ff = z["ff_emp"].astype("float32")[gi]
    sub = [ids[i] for i in ti]
    with np.errstate(invalid="ignore", divide="ignore"):
        p = fl / oc
    p[~(np.isfinite(oc) & (oc >= OCC_VUOTA) & (oc > 0))] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        r_pr = np.clip(p / np.nanpercentile(p, PCTL, axis=0)[None, :], 0, 1.5)
        r_tr = np.clip(sp / ff[None, :], 0, 1.5)
    imputate = np.isfinite(oc) & (oc < OCC_VUOTA)
    return dict(r_pr=r_pr, r_tr=r_tr, oc=oc, sp=sp, ff=ff, sub=sub, imputate=imputate)


def sez_anello(d):
    print("=" * 92)
    print("ANELLO M30 - riferimento co-localizzato, regime a scorrimento libero")
    print("=" * 92)
    v = np.isfinite(d["r_pr"]) & np.isfinite(d["r_tr"]) & (d["sp"] > 0)
    tot = np.isfinite(d["r_tr"]) & (d["sp"] > 0)
    print(f"sensori allineati {len(d['sub'])} | celle valide {int(tot.sum()):,}")
    print(f"quota imputata dalla regola di strada vuota: "
          f"{100 * d['imputate'][tot].mean():.2f}%   (arterie urbane: 77-78%)")
    print(f"celle non imputate: {int(v.sum()):,}")
    a, b = d["r_pr"][v], d["r_tr"][v]
    print(f"\ncorrelazione di rango sulle celle non imputate: {spearmanr(a, b).statistic:+.4f}")

    print(f"\n{'fascia di occupazione':24s} {'celle':>11} {'corr. di rango':>16}")
    for lo, hi in ((5, 10), (10, 20), (20, 40), (40, 100)):
        m = v & (d["oc"] >= lo) & (d["oc"] < hi)
        if m.sum() < 100:
            continue
        print(f"  {lo:3d}-{hi:3d}%{'':14s} {int(m.sum()):11,} "
              f"{spearmanr(d['r_pr'][m], d['r_tr'][m]).statistic:+16.3f}")
    print(f"\n{'classe misurata':24s} {'celle':>11} {'corr. di rango':>16}")
    for lo, hi, nome in ((0.8, 1.6, "verde"), (0.4, 0.8, "giallo"), (0.0, 0.4, "rosso")):
        m = v & (d["r_tr"] >= lo) & (d["r_tr"] < hi)
        if m.sum() < 100:
            continue
        print(f"  {nome:22s} {int(m.sum()):11,} "
              f"{spearmanr(d['r_pr'][m], d['r_tr'][m]).statistic:+16.3f}")
    print("\n  Il segno si INVERTE al crescere dell'occupazione: a occupazione bassa il")
    print("  rapporto fra flusso e occupazione e' dominato dall'instabilita' del denominatore.")

    y = (b < SOGLIA_ROSSO).astype(int)
    auc = roc_auc_score(y, -a)
    print(f"\narea sotto la curva, rosso contro resto: {auc:.4f}  (Gini {gini(auc):.4f})")
    print(f"area sotto la curva, giallo+rosso:      "
          f"{roc_auc_score((b < 0.8).astype(int), -a):.4f}")
    print(f"\n{'soglia':10s} {'precisione':>11} {'richiamo':>9} {'F1':>7}")
    for s in (0.20, 0.30, 0.40, 0.50):
        pr_ = a < s
        tp = (pr_ & (y == 1)).sum()
        fp = (pr_ & (y == 0)).sum()
        fn = ((~pr_) & (y == 1)).sum()
        p_ = tp / max(tp + fp, 1)
        r_ = tp / max(tp + fn, 1)
        print(f"  r < {s:.2f} {p_:11.4f} {r_:9.4f} "
              f"{2 * p_ * r_ / max(p_ + r_, 1e-9):7.4f}")
    print(f"\nprecisione di un predittore casuale: {y.mean():.4f}")
    print("\n  Correlazione bassa e discriminazione alta CONVIVONO: sono due grandezze")
    print("  indipendenti, non una contraddizione.")
    print("\n  LIMITE DA DICHIARARE: la soglia va scelta su dati tenuti da parte. Con 4,2")
    print("  milioni di celle il sovraadattamento e' trascurabile, ma la convenzione")
    print("  adottata altrove nel documento richiede la taratura fuori campione.\n")


def sez_accoppiamento(d, args):
    print("=" * 92)
    print("SCOMPOSIZIONE DELL'ERRORE DI ACCOPPIAMENTO")
    print("=" * 92)
    print("Sull'anello si sostituisce il riferimento del sensore stesso con quello di un")
    print("altro sensore a distanza crescente, tenendo fermi REGIME e TECNOLOGIA.\n")
    s = pd.read_csv(GOMO / "traffic_sensors.csv", dtype={"id": "string"}) \
        .dropna(subset=["utm_x", "utm_y"])
    s["id"] = s["id"].astype(str)
    XY = s.set_index("id").reindex(d["sub"])[["utm_x", "utm_y"]].to_numpy()
    D = np.sqrt(((XY[:, None, :] - XY[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(D, np.inf)
    print(f"{'riferimento':28s} {'dist. mediana':>14} {'corr.':>9} {'AUC':>8} {'Gini':>8}")
    v = np.isfinite(d["r_pr"]) & np.isfinite(d["r_tr"]) & (d["sp"] > 0)
    a = d["r_pr"][v]
    b = d["r_tr"][v]
    auc0 = roc_auc_score((b < SOGLIA_ROSSO).astype(int), -a)
    print(f"{'stesso sensore':28s} {0:12.0f} m {spearmanr(a, b).statistic:+9.3f} "
          f"{auc0:8.4f} {gini(auc0):8.4f}")
    fasce = [(0, 20), (19, 72), (20, 60), (60, 200)]
    for lo, hi in fasce:
        A, B, dd = [], [], []
        for i in range(len(d["sub"])):
            c = np.where((D[i] >= lo) & (D[i] < hi))[0]
            if not len(c):
                continue
            j = c[np.argmin(np.abs(D[i][c] - 33.0))]     # il piu' vicino a 33 m
            m = (np.isfinite(d["r_pr"][:, i]) & np.isfinite(d["r_tr"][:, j])
                 & (d["sp"][:, j] > 0) & (d["oc"][:, i] >= OCC_VUOTA))
            if m.sum() > 50:
                A.append(d["r_pr"][m, i])
                B.append(d["r_tr"][m, j])
                dd.append(D[i, j])
        if len(A) < 20:
            print(f"{'vicino a ' + str(lo) + '-' + str(hi) + ' m':28s} pochi sensori")
            continue
        A = np.concatenate(A)
        B = np.concatenate(B)
        y = (B < SOGLIA_ROSSO).astype(int)
        auc = roc_auc_score(y, -A) if 50 < y.sum() < len(y) - 50 else np.nan
        eti = f"vicino a {lo}-{hi} m"
        if (lo, hi) == (19, 72):
            eti += " *"
        print(f"{eti:28s} {np.median(dd):12.0f} m {spearmanr(A, B).statistic:+9.3f} "
              f"{auc:8.4f} {gini(auc):8.4f}")
    print(f"{'arterie, sonde (§8.6.3)':28s} {33:12.0f} m {0.001:+9.3f} "
          f"{0.542:8.4f} {gini(0.542):8.4f}")
    print("\n  * fascia costruita A POSTERIORI per appaiare la distanza mediana a quella")
    print("    delle coppie urbane. Va dichiarato.")
    print("\n  La ripartizione va fatta sulla scala di GINI, che e' additiva. Le differenze")
    print("  di area sotto la curva NON lo sono: da 0,5 a 0,984 c'e' tutto il campo di")
    print("  discriminazione, da 0,726 a 0,542 una porzione molto diversa.")
    print("\n  LIMITE: la separazione fra regime e differenza fra tecnologie non e'")
    print("  misurabile, perche' l'anello e' coperto per il 2024 e le sonde per il periodo")
    print("  giugno-dicembre 2021, senza sovrapposizione. Il residuo e' attribuito")
    print("  CONGIUNTAMENTE a regime e tecnologia.\n")


# ------------------------------------------------------------------ Austin --
def carica_austin():
    import json
    d = pd.DataFrame(json.load(open(AUSTIN)))
    for c in ("volume", "occupancy", "speed", "year", "month", "day", "hour", "minute"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[(d.volume > 0) & (d.occupancy > 0) & (d.occupancy <= 100)
          & (d.speed > 0) & d.year.between(2017, 2021) & (d.direction != "None")].copy()
    d["speed"] *= MIGLIA_KM
    d["ist"] = (d.year.astype(int).astype(str)
                + d.month.astype(int).astype(str).str.zfill(2)
                + d.day.astype(int).astype(str).str.zfill(2)
                + d.hour.astype(int).astype(str).str.zfill(2)
                + d.minute.astype(int).astype(str).str.zfill(2))
    d["corsia"] = d.intname + "|" + d.detname
    d["sez"] = d.intname + "|" + d.direction
    d["p"] = d.volume / d.occupancy
    d["r_pr"] = np.clip(d.p / d.groupby("corsia").p.transform(lambda s: s.quantile(.85)), 0, 1.5)
    d["r_tr"] = np.clip(d.speed / d.groupby("corsia").speed.transform(lambda s: s.quantile(.85)), 0, 1.5)
    d["rosso"] = d.r_tr < SOGLIA_ROSSO
    return d.sort_values(["corsia", "ist"])


def sez_austin(x):
    print("=" * 92)
    print("AUSTIN - riferimento co-localizzato su arterie SEMAFORIZZATE, per corsia")
    print("=" * 92)
    print("Escluse le tre intersezioni prive del campo direzione: l'aggregazione vi")
    print("mescolerebbe versi di marcia opposti.\n")
    per = [spearmanr(q.r_pr, q.r_tr).statistic
           for _, q in x.groupby("corsia") if len(q) >= 200]
    per = [v for v in per if np.isfinite(v)]
    print(f"celle {len(x):,} | corsie {x.corsia.nunique()} | "
          f"corsie con almeno 200 celle {len(per)}")
    print(f"correlazione di rango aggregata: {spearmanr(x.r_pr, x.r_tr).statistic:+.4f}")
    print(f"correlazione di rango ENTRO CORSIA: mediana {np.median(per):+.4f} "
          f"[{np.percentile(per, 25):+.3f}; {np.percentile(per, 75):+.3f}]")
    au = [roc_auc_score(q.rosso, -q.r_pr) for _, q in x.groupby("corsia")
          if q.rosso.sum() > 20 and (~q.rosso).sum() > 20]
    print(f"area sotto la curva ENTRO CORSIA: mediana {np.median(au):.4f} "
          f"[{np.percentile(au, 25):.3f}; {np.percentile(au, 75):.3f}]  ({len(au)} corsie)")
    print("\n  Confronto diretto: sulle arterie di Madrid, con riferimento NON")
    print("  co-localizzato, gli stessi valori sono +0,071 e 0,542. Il regime semaforizzato")
    print("  non basta quindi a spiegare il fallimento su Madrid.\n")

    print("-" * 92)
    print("AGGREGAZIONE FRA CORSIE")
    print("-" * 92)
    cps = x.groupby("sez").corsia.nunique()
    x["una_rossa"] = x.rosso
    agg = x.groupby(["sez", "ist"], as_index=False).agg(
        volume=("volume", "sum"), occupancy=("occupancy", "mean"),
        speed=("speed", "mean"), una_rossa=("una_rossa", "max"))
    agg = agg[(agg.volume > 0) & (agg.occupancy > 0) & (agg.speed > 0)].copy()
    agg["p"] = agg.volume / agg.occupancy
    agg["r_pr"] = np.clip(agg.p / agg.groupby("sez").p.transform(lambda s: s.quantile(.85)), 0, 1.5)
    agg["r_tr"] = np.clip(agg.speed / agg.groupby("sez").speed.transform(lambda s: s.quantile(.85)), 0, 1.5)
    agg["rosso_sez"] = agg.r_tr < SOGLIA_ROSSO
    print(f"{'corsie':7s} {'sezioni':>8} {'celle':>11} {'AUC vs >=1 corsia rossa':>28} "
          f"{'diff. prevalenza':>17}")
    for k in sorted(cps.unique()):
        if k == 1:
            continue                       # caso degenere: nessuna aggregazione
        sel = cps[cps == k].index
        q = agg[agg.sez.isin(sel)]
        if len(q) < 1000:
            continue
        au = [roc_auc_score(g.una_rossa, -g.r_pr) for _, g in q.groupby("sez")
              if g.una_rossa.sum() > 20 and (~g.una_rossa).sum() > 20]
        f = (f"{np.median(au):.3f} [{np.percentile(au, 25):.3f}; "
             f"{np.percentile(au, 75):.3f}] n={len(au)}" if au else "n.d.")
        d_ = 100 * (q.una_rossa.mean() - q.rosso_sez.mean())
        print(f"{k:7d} {len(sel):8d} {len(q):11,} {f:>28} {d_:+16.2f}pp")
    print("\n  Il livello a UNA corsia e' escluso: non vi e' aggregazione, ed e' il caso")
    print("  degenere. La differenza di prevalenza e' riportata al posto del rapporto")
    print("  perche' additiva e stabile con denominatori piccoli.")
    print("\n  DUE COMPONENTI CON DESTINATARI DIVERSI. La prima e' la definizione del")
    print("  bersaglio: mediare la velocita' fra corsie nasconde di per se' gli episodi")
    print("  localizzati, e vale per QUALUNQUE dispositivo, compresi quelli che la")
    print("  velocita' la misurano direttamente. La seconda e' la perdita attribuibile")
    print("  alla ricostruzione, ed e' quella misurata dall'area sotto la curva.")
    print("\n  I dati NON fondano una soglia: la numerosita' va da due a ventidue sezioni")
    print("  per livello e gli intervalli si sovrappongono.\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="validazione co-localizzata")
    ap.add_argument("--sezioni", nargs="*",
                    default=["anello", "accoppiamento", "austin"])
    a = ap.parse_args()

    if {"anello", "accoppiamento"} & set(a.sezioni):
        if not (GOMO / "tensors_2024_m30.npz").exists():
            print("tensori M30 non trovati: eseguire prima 1_gomo_stage1_loader.py")
        else:
            d = carica_m30()
            if "anello" in a.sezioni:
                sez_anello(d)
            if "accoppiamento" in a.sezioni:
                sez_accoppiamento(d, a)
    if "austin" in a.sezioni:
        if not AUSTIN.exists():
            print(f"{AUSTIN} non trovato: eseguire prima austin/radar/scarica.py")
        else:
            sez_austin(carica_austin())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
