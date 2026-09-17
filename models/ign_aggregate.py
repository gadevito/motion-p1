"""
Aggregazione dell'ablazione sulle statiche (IGN)
===============================================
Legge i CSV prodotti da gomo_ign.py con nomi  ign_{citta}_s{seme}_{set}.csv
(e  ign_{citta}_s{seme}_transd.csv  come riferimento) e calcola, per ogni set
di feature statiche:

  divario colmato = (wCE_senza_identita - wCE_con_statiche) / (wCE_senza_identita - wCE_veterano)

dove 'senza identita' = transduttivo sui nodi mai visti (ripiego)
     'veterano'       = transduttivo sui nodi visti
Media e deviazione standard sui semi. Riporta anche il richiamo della classe rossa.

Uso (da models/):
  poetry run python ign_aggregate.py --glob "ign_mad_s*.csv" --label Madrid
  poetry run python ign_aggregate.py --glob "ign_lon_s*.csv" --label Londra
"""
from pathlib import Path
import argparse, re
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser(description="Aggregazione ablazione statiche")
ap.add_argument("--glob", required=True)
ap.add_argument("--label", default="")
ap.add_argument("--out", type=Path, default=None)
args = ap.parse_args()

rows = []
for f in sorted(Path(".").glob(args.glob)):
    m = re.match(r"ign_(\w+?)_s(\d+)_(.+)\.csv$", f.name)
    if not m:
        print(f"  (salto {f.name}: nome non riconosciuto)"); continue
    city, seed, fset = m.group(1), int(m.group(2)), m.group(3)
    df = pd.read_csv(f)
    for split in ("seen", "held-out"):
        sub = df[df["split"] == split]
        if len(sub) == 0: continue
        rows.append({"city": city, "seed": seed, "set": fset, "model": sub["model"].iloc[0],
                     "split": split, "wCE": sub["wCE"].mean(), "red": sub["red_recall"].mean()})
if not rows:
    raise SystemExit("nessun file corrispondente al pattern")
d = pd.DataFrame(rows)

# riferimenti dal transduttivo, per seme
ref = d[d["set"] == "transd"].pivot_table(index="seed", columns="split", values=["wCE", "red"])
if ref.empty:
    raise SystemExit("mancano i file *_transd.csv (riferimento)")
vet = ref[("wCE", "seen")]          # veterano
noid = ref[("wCE", "held-out")]     # nodo nuovo senza identita'
noid_red = ref[("red", "held-out")]

print(f"\n=== {args.label} — ablazione delle caratteristiche statiche ===")
print(f"veterano (nodi visti):        wCE = {vet.mean():.4f} ± {vet.std():.4f}")
print(f"nodo nuovo, nessuna identita: wCE = {noid.mean():.4f} ± {noid.std():.4f}"
      f"   (richiamo rosso {noid_red.mean():.3f})")
print(f"divario da colmare:           {(noid - vet).mean():.4f}\n")

out = []
for fset in [s for s in d["set"].unique() if s != "transd"]:
    sub = d[(d["set"] == fset) & (d["split"] == "held-out")].set_index("seed")
    seeds = sorted(set(sub.index) & set(vet.index))
    if not seeds: continue
    closed = np.array([(noid[s] - sub.loc[s, "wCE"]) / (noid[s] - vet[s]) for s in seeds])
    wce = np.array([sub.loc[s, "wCE"] for s in seeds]); red = np.array([sub.loc[s, "red"] for s in seeds])
    sd = lambda a: a.std(ddof=1) if len(a) > 1 else 0.0    # stima non distorta, coerente con i riferimenti
    out.append({"set": fset.replace("-", ", "), "n_semi": len(seeds),
                "wCE": f"{wce.mean():.4f} ± {sd(wce):.4f}",
                "divario colmato": f"{closed.mean():+.1%} ± {sd(closed):.1%}",
                "richiamo rosso": f"{red.mean():.3f}"})
res = pd.DataFrame(out)
# ordina per numero di feature (approssimato dal numero di virgole)
res["_n"] = res["set"].str.count(",")
res = res.sort_values("_n").drop(columns="_n")
print(res.to_string(index=False))
print("\nDivario colmato: positivo = le statiche recuperano identita'; "
      "negativo = fanno peggio del non avere identita' affatto.")
if args.out: res.to_csv(args.out, index=False); print(f"\nsalvato -> {args.out}")
