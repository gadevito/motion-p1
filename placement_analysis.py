"""
Analisi di posizionamento: cosa rende un sensore nuovo rapidamente operativo?
Unita' = nodo tenuto fuori; esito = quota di divario colmato a 24h (per nodo, per seme).
Predittori dal grafo e dall'anagrafica: distanza mediana dai vicini, grado,
copertura del nodo (quota celle valide), flusso libero, classe stradale.

Uso (dalla radice OR3/), per citta':
  poetry run python placement_analysis.py --pernode "models/onboard_mel_s*_pernode.csv" \
      --targets data_collection/traffic4cast/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz \
      --graph   data_collection/traffic4cast/MELBOURNE_2022/gomo_fmt/t4cmel_routes-graph.pkl \
      --label Melbourne
"""
import argparse, glob, pickle
import numpy as np, pandas as pd, networkx as nx

ap = argparse.ArgumentParser()
ap.add_argument("--pernode", required=True, help="glob dei *_pernode.csv (3 semi)")
ap.add_argument("--targets", required=True)
ap.add_argument("--graph", required=True)
ap.add_argument("--label", default="")
args = ap.parse_args()

z = np.load(args.targets, allow_pickle=True)
sids = z["sensor_ids"].astype(str); C = z["congestion_emp"]
cov = (C > 0).mean(0)                                   # copertura per nodo
G = pickle.load(open(args.graph, "rb"))
ndist, ndeg = {}, {}
for n in G.nodes:
    ws = [G[n][u]["weight"] for u in G[n]]
    ndist[str(n)] = float(np.median(ws)) if ws else np.nan
    ndeg[str(n)] = G.degree(n)
covmap = {s: float(cov[i]) for i, s in enumerate(sids)}

frames = []
for f in sorted(glob.glob(args.pernode)):
    d = pd.read_csv(f, dtype={"sensor_id": str}); d["seed"] = f
    frames.append(d)
d = pd.concat(frames, ignore_index=True)
if d["sensor_id"].eq("").all():
    raise SystemExit("sensor_id vuoto nei per-node: rilanciare onboard dopo la patch (serve l'array ids)")

# esito: divario colmato a 24h = (wCE0 - wCE24)/(wCE0 - wCE_veterano_medio)
w0 = d[d.history == "0h"].set_index(["seed", "sensor_id"])["wCE"]
w24 = d[d.history == "24h"].set_index(["seed", "sensor_id"])["wCE"]
# riferimento veterano: dal file aggregato non per-nodo; qui usiamo il wCE mediano dei nodi a 1wk come proxy conservativo
w1w = d[d.history == "1wk"].set_index(["seed", "sensor_id"])["wCE"]
out = pd.DataFrame({"w0": w0, "w24": w24}).dropna().reset_index()
out["recover"] = (out.w0 - out.w24)                      # riduzione assoluta di wCE in 24h
out["dist_vicini_m"] = out.sensor_id.map(ndist)
out["grado"] = out.sensor_id.map(ndeg)
out["copertura"] = out.sensor_id.map(covmap)

print(f"=== {args.label} — posizionamento: predittori del recupero a 24h ===")
print(f"nodi x semi: {len(out)}  (nodi distinti: {out.sensor_id.nunique()})")
rng = np.random.default_rng(0)
for var in ("dist_vicini_m", "grado", "copertura"):
    v = out[[var, "recover"]].dropna()
    r = np.corrcoef(v[var], v.recover)[0, 1]
    bs = [np.corrcoef(*v.sample(len(v), replace=True, random_state=int(rng.integers(1e9))).T.values)[0, 1]
          for _ in range(2000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    print(f"  corr(recupero, {var:>14s}) = {r:+.3f}   IC95% bootstrap [{lo:+.3f}, {hi:+.3f}]")
print("Lettura: correlazione negativa con dist_vicini_m = i nodi con vicini lontani recuperano meno")
print("(coerente con l'ipotesi geometria); positiva con copertura = conta la qualita' della storia.")
out.to_csv(f"placement_{args.label or 'ctx'}.csv", index=False)
print(f"dettaglio per nodo -> placement_{args.label or 'ctx'}.csv")
