"""
Validazione incrociata: r RICOSTRUITO (spire GO-MO) vs r MISURATO (sonde t4c)
============================================================================
Stessa citta' (Madrid), stesso distretto (8), stesso periodo (giu-dic 2021).
Aggancia ogni sensore GO-MO al segmento t4c piu' vicino, allinea i quarti d'ora,
e confronta il fattore di congestione ricostruito da flusso/occupazione contro
quello misurato da sonde GPS. Chiude l'assunzione di ricostruzione con i dati.

Robustezza: cerca automaticamente lo scostamento temporale globale migliore
(fuso orario / convenzione degli slot) prima di correlare.

Uso (da data_collection/):
  poetry run python t4c_crossval.py \
      --gomo-targets go-mo/gomo/targets_2021_urb_d8.npz \
      --gomo-sensors go-mo/gomo/traffic_sensors.csv \
      --t4c-nodes traffic4cast/MADRID_2022/road_graph_nodes_osm.parquet \
      --t4c-edges traffic4cast/MADRID_2022/road_graph_edges_district.parquet \
      --speed-dir traffic4cast/MADRID_2022/speed_classes/madrid \
      --out crossval_results.csv
Serve: pandas, pyarrow, numpy, scipy
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import rankdata

ap = argparse.ArgumentParser(description="Validazione incrociata ricostruito vs misurato")
ap.add_argument("--gomo-targets", type=Path, required=True)
ap.add_argument("--gomo-sensors", type=Path, required=True)
ap.add_argument("--t4c-nodes", type=Path, required=True)
ap.add_argument("--t4c-edges", type=Path, required=True)
ap.add_argument("--speed-dir", type=Path, required=True)
ap.add_argument("--exclude-empty", action="store_true",
                help="esclude le celle in cui r_emp e' stato imposto a 1.0 dalla regola occ<OCC_EMPTY")
ap.add_argument("--max-dist", type=float, default=120.0, help="distanza max sensore-segmento (m)")
ap.add_argument("--min-overlap", type=int, default=200, help="min quarti d'ora in comune per coppia")
ap.add_argument("--out", type=Path, default=Path("crossval_results.csv"))
args = ap.parse_args()
GREEN, RED = 0.8, 0.4
def cls_of(r): return np.where(~np.isfinite(r), 0, np.where(r >= GREEN, 1, np.where(r >= RED, 2, 3)))

# ------------------------------------------------ GO-MO (ricostruito) ---------
z = np.load(args.gomo_targets, allow_pickle=True)
g_ts = pd.to_datetime(z["timestamps"]); g_sid = z["sensor_ids"].astype(str); g_r = z["r_emp"].astype("float32")
if args.exclude_empty:
    _n0 = int(np.isfinite(g_r).sum())
    g_r = np.where(g_r == 1.0, np.nan, g_r)
    _n1 = int(np.isfinite(g_r).sum())
    print(f"[exclude-empty] celle con r=1.0 rimosse: {_n0-_n1:,} su {_n0:,} ({100*(_n0-_n1)/_n0:.1f}%)")
gs = pd.read_csv(args.gomo_sensors, dtype={"id": str})
latc = next(c for c in gs.columns if c.lower() in ("latitude", "lat"))
lonc = next(c for c in gs.columns if c.lower() in ("longitude", "lon", "lng"))
gs = gs.set_index("id")
g_lat = pd.to_numeric(gs[latc].reindex(g_sid), errors="coerce").to_numpy()
g_lon = pd.to_numeric(gs[lonc].reindex(g_sid), errors="coerce").to_numpy()
ok = np.isfinite(g_lat) & np.isfinite(g_lon)
print(f"GO-MO: {len(g_sid)} sensori 2021 ({ok.sum()} con coordinate)")

# ------------------------------------------------ t4c: coordinate segmenti ----
nd = pd.read_parquet(args.t4c_nodes); coord = {int(r.node_id): (r.latitude, r.longitude) for r in nd.itertuples()}
edg = pd.read_parquet(args.t4c_edges).astype("int64")
edg = edg[edg["u"].isin(coord) & edg["v"].isin(coord)].drop_duplicates(["u", "v"]).reset_index(drop=True)
edg["sid"] = edg["u"].astype(str) + "_" + edg["v"].astype(str)
mlat = edg.apply(lambda r: (coord[r.u][0] + coord[r.v][0]) / 2, axis=1).to_numpy()
mlon = edg.apply(lambda r: (coord[r.u][1] + coord[r.v][1]) / 2, axis=1).to_numpy()
print(f"t4c: {len(edg):,} segmenti geolocalizzati")

# ------------------------------------------------ aggancio sensore->segmento --
lat0 = np.nanmean(g_lat[ok]); mX = lambda la, lo: np.c_[(lo - np.nanmean(g_lon[ok])) * np.cos(np.radians(lat0)) * 111320.0,
                                                        (la - lat0) * 110540.0]
tree = cKDTree(mX(mlat, mlon))
dist, idx = tree.query(mX(g_lat, g_lon), k=1)
match = ok & (dist <= args.max_dist)
pairs = [(g_sid[i], edg["sid"].iloc[idx[i]], edg["u"].iloc[idx[i]], edg["v"].iloc[idx[i]], dist[i])
         for i in range(len(g_sid)) if match[i]]
print(f"coppie sensore-segmento entro {args.max_dist:.0f} m: {len(pairs)} "
      f"(distanza mediana {np.median([p[4] for p in pairs]):.0f} m)")
seg_needed = pd.DataFrame({"u": [p[2] for p in pairs], "v": [p[3] for p in pairs]}).drop_duplicates()

# ------------------------------------------------ t4c: r misurato -------------
parts = []
for f in sorted(args.speed_dir.glob("*.parquet")):
    df = pd.read_parquet(f, columns=["u", "v", "day", "t", "median_speed_kph", "free_flow_kph"]).merge(
        seg_needed, on=["u", "v"], how="inner")
    parts.append(df)
sc = pd.concat(parts, ignore_index=True)
sc["sid"] = sc["u"].astype(str) + "_" + sc["v"].astype(str)
sc["ts"] = pd.to_datetime(sc["day"]) + pd.to_timedelta(sc["t"] * 15, unit="min")
ff = sc.groupby("sid")["free_flow_kph"].median()
sc["r"] = np.clip(sc["median_speed_kph"] / sc["sid"].map(ff), 0, 1.5)
t4c_r = {sid: grp.set_index("ts")["r"] for sid, grp in sc.groupby("sid")}
common = pd.DatetimeIndex(sorted(sc["ts"].unique()))
print(f"t4c: {len(sc):,} righe misurate | {len(common):,} quarti d'ora distinti (giu-dic 2021)")

# matrici allineate su 'common'
gpos = {s: i for i, s in enumerate(g_sid)}
gdf = pd.DataFrame(g_r, index=g_ts, columns=g_sid)                  # ricostruito (2021 intero)
M = np.full((len(common), len(pairs)), np.nan, "float32")           # misurato
for j, (s, seg, u, v, d) in enumerate(pairs):
    M[:, j] = t4c_r[seg].reindex(common).to_numpy()

# ------------------------------------------------ ricerca dello scostamento ---
def col_corr(A, B):
    out = np.full(A.shape[1], np.nan)
    for j in range(A.shape[1]):
        m = np.isfinite(A[:, j]) & np.isfinite(B[:, j])
        if m.sum() >= args.min_overlap:
            a, b = A[m, j], B[m, j]
            if a.std() > 1e-6 and b.std() > 1e-6:
                out[j] = np.corrcoef(a, b)[0, 1]
    return out

sensors_of_pairs = [p[0] for p in pairs]
best = (-2, 0, None)
for shift in range(-8, 9):                                          # +-2 ore
    G = gdf.reindex(common + pd.Timedelta(shift * 15, "min"))[sensors_of_pairs].to_numpy("float32")
    med = np.nanmedian(col_corr(G, M))
    print(f"  scostamento {shift:+3d} ({shift*15:+5d} min): mediana {med:+.4f}")
    if med > best[0]: best = (med, shift, G)
med_corr, shift, G = best
print(f"\nscostamento temporale ottimo: {shift} quarti d'ora ({shift*15:+d} min) "
      f"-> {'nessun fuso' if shift == 0 else 'probabile differenza di fuso/convenzione'}")

# ------------------------------------------------ metriche finali -------------
def col_corr_rank(A, B):
    out = np.full(A.shape[1], np.nan)
    for j in range(A.shape[1]):
        m = np.isfinite(A[:, j]) & np.isfinite(B[:, j])
        if m.sum() >= args.min_overlap:
            a, b = rankdata(A[m, j]), rankdata(B[m, j])
            if a.std() > 1e-6 and b.std() > 1e-6:
                out[j] = np.corrcoef(a, b)[0, 1]
    return out

print("\n=== correlazione di rango: sonde contro ciascun ingresso grezzo ===")
_shift_td = pd.Timedelta(shift * 15, "min")
_occ_raw = z["occupancy"].astype("float32")
_empty = np.isfinite(_occ_raw) & (_occ_raw < 5.0)
print(f"  [maschera] celle vuote: {_empty.sum():,} ({100*_empty.mean():.1f}%) | "
      f"applicata: {args.exclude_empty}")
for _nome, _key in (("r ricostruito", "r_emp"), ("occupazione", "occupancy"), ("flusso", "flow")):
    _v = z[_key].astype("float32")
    if args.exclude_empty:
        _v = np.where(_empty, np.nan, _v)
    _df = pd.DataFrame(_v, index=g_ts, columns=g_sid)
    _best, _bsh = 0.0, 0
    for _sh in range(-8, 9):
        _Ai = _df.reindex(common + pd.Timedelta(_sh * 15, "min"))[sensors_of_pairs].to_numpy("float32")
        _mi = np.nanmedian(col_corr_rank(_Ai, M))
        if np.isfinite(_mi) and abs(_mi) > abs(_best): _best, _bsh = _mi, _sh
    _A = _df.reindex(common + pd.Timedelta(_bsh * 15, "min"))[sensors_of_pairs].to_numpy("float32")
    _p = col_corr(_A, M); _s = col_corr_rank(_A, M)
    print(f"  {_nome:16s} scost. ottimo {_bsh:+2d} ({_bsh*15:+4d} min) | "
          f"Pearson {np.nanmedian(_p):+.4f} | Spearman {np.nanmedian(_s):+.4f} | "
          f"coppie {np.isfinite(_s).sum()}")

corrs = col_corr(G, M)
gc = cls_of(G); mc = cls_of(M); both = (gc > 0) & (mc > 0)
agree = (gc[both] == mc[both]).mean()
# aggregato binario congestione (giallo+rosso vs verde)
gb = np.where(gc[both] == 1, 0, 1); mb = np.where(mc[both] == 1, 0, 1)
tp = ((gb == 1) & (mb == 1)).sum(); fn = ((gb == 0) & (mb == 1)).sum()
recall_cong = tp / max(tp + fn, 1)
print(f"\n=== VALIDAZIONE INCROCIATA (ricostruito vs misurato) ===")
print(f"coppie valide: {np.isfinite(corrs).sum()} | correlazione r: mediana {np.nanmedian(corrs):.3f}, "
      f"media {np.nanmean(corrs):.3f}")
print(f"concordanza di classe (3 classi): {agree:.1%}")
print(f"recall della congestione ricostruita (giallo+rosso): {recall_cong:.1%} "
      f"(quanta congestione misurata le spire 'vedono')")
dg = gc[both]; dm = mc[both]
print("\ndistribuzione classi sui punti allineati:")
print(f"  ricostruito (spire) verde/giallo/rosso = "
      f"{(dg==1).mean():.1%} / {(dg==2).mean():.1%} / {(dg==3).mean():.1%}")
print(f"  misurato   (sonde)  verde/giallo/rosso = "
      f"{(dm==1).mean():.1%} / {(dm==2).mean():.1%} / {(dm==3).mean():.1%}")

# --- correlazione del PROFILO settimanale medio (cattura il pattern tipico?) ---
slotkey = (common.dayofweek * 96 + common.hour * 4 + common.minute // 15).to_numpy()
prof = []
for j in range(len(pairs)):
    a = pd.Series(G[:, j]).groupby(slotkey).mean(); b = pd.Series(M[:, j]).groupby(slotkey).mean()
    m = a.notna() & b.notna()
    if m.sum() >= 100 and a[m].std() > 1e-6 and b[m].std() > 1e-6:
        prof.append(np.corrcoef(a[m], b[m])[0, 1])
prof = np.array(prof)
print(f"\ncorrelazione del profilo settimanale medio (672 momenti-tipo): "
      f"mediana {np.nanmedian(prof):.3f}, media {np.nanmean(prof):.3f}  (su {len(prof)} coppie)")
print("  -> alta = il proxy coglie il pattern tipico anche se non l'istante; "
      "bassa = non coglie nemmeno la stagionalita'")

pd.DataFrame({"gomo_sensor": [p[0] for p in pairs], "t4c_segment": [p[1] for p in pairs],
              "dist_m": [p[4] for p in pairs], "corr": corrs}).to_csv(args.out, index=False)
print(f"\nsalvato -> {args.out}")
