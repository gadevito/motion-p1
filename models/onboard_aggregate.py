"""
Aggregazione della curva di onboarding (identita' da storia recente)
====================================================================
Legge i CSV prodotti da gomo_onboard.py (colonne: history, split, wCE, ...) per
piu' semi e calcola, a ciascuna lunghezza di storia, la frazione di divario verso
il veterano colmata dal nodo mai visto:

  divario colmato(H) = (wCE_heldout(0h) - wCE_heldout(H)) / (wCE_heldout(0h) - wCE_seen)

media +- deviazione standard sui semi. Nota: puo' superare 100% se il sottoinsieme
tenuto fuori e' intrinsecamente piu' facile di quello visto (partizione casuale).

Uso (da models/):
  poetry run python onboard_aggregate.py --glob "onboard_mad_s?.csv" --label Madrid
  poetry run python onboard_aggregate.py --glob "onboard_lon_s?.csv" --label Londra
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--glob", required=True)
ap.add_argument("--label", default="")
args = ap.parse_args()

ORDER = ["0h", "1h", "4h", "24h", "1wk"]
per_seed = {}   # history -> lista di divari colmati (uno per seme)
seen_list, h0_list = [], []
nfiles = 0
for f in sorted(Path(".").glob(args.glob)):
    df = pd.read_csv(f)
    seen = df[df.split == "seen"]["wCE"].mean()           # ~costante fra le storie
    ho = df[df.split == "held-out"].set_index("history")["wCE"]
    if "0h" not in ho.index: continue
    h0 = ho["0h"]; denom = h0 - seen
    if abs(denom) < 1e-6: continue
    nfiles += 1; seen_list.append(seen); h0_list.append(h0)
    for h in ORDER:
        if h in ho.index:
            per_seed.setdefault(h, []).append((h0 - ho[h]) / denom)

if nfiles == 0:
    raise SystemExit("nessun file corrispondente")
sd = lambda a: float(np.std(a, ddof=1)) if len(a) > 1 else 0.0
print(f"\n=== {args.label} — curva di onboarding ({nfiles} semi) ===")
print(f"veterano (nodi visti): wCE = {np.mean(seen_list):.4f} ± {sd(seen_list):.4f}")
print(f"nodo nuovo a 0h:       wCE = {np.mean(h0_list):.4f} ± {sd(h0_list):.4f}\n")
print(f"{'storia':>8} | {'divario colmato':>22} | n")
for h in ORDER:
    if h in per_seed:
        v = np.array(per_seed[h]) * 100
        print(f"{h:>8} | {v.mean():>10.0f}% ± {sd(v)/1:>5.0f}%      | {len(v)}")
print("\nCriterio pre-registrato: >=70% a 24h. Nota: valori >100% = sottoinsieme "
      "tenuto fuori piu' facile del visto (partizione casuale), non superiorita' reale.")
