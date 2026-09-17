"""
Ispezione dei dati Traffic4cast 2022 (Madrid) scaricati da HERE.
Stampa l'alberatura e lo schema (colonne, tipi, prime righe) dei file parquet
di speed_classes e road_graph, cosi' l'adattatore verra' scritto sui nomi reali.

Uso (da dove hai scompattato lo zip, o passando la radice):
    poetry run python inspect_t4c22.py --root /percorso/di/MADRID_2022
Serve: pandas, pyarrow   ->   poetry add pyarrow
"""
from pathlib import Path
import argparse
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--root", type=Path, default=Path("."))
ap.add_argument("--rows", type=int, default=3)
args = ap.parse_args()

def tree(root, maxdepth=3):
    root = Path(root)
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root); depth = len(rel.parts)
        if depth > maxdepth: continue
        if p.is_dir():
            print("  " * (depth - 1) + f"[{rel.parts[-1]}]/")
        elif p.suffix in (".parquet", ".csv") or depth <= 2:
            sz = p.stat().st_size / 1e6
            print("  " * (depth - 1) + f"{rel.parts[-1]}  ({sz:.1f} MB)")

def show(label, files):
    print(f"\n===== {label} =====")
    if not files:
        print("  (nessun file trovato con questo pattern)"); return
    f = files[0]
    print(f"file di esempio: {f}")
    try:
        df = pd.read_parquet(f)
    except Exception as e:
        print(f"  impossibile leggere il parquet: {e}"); return
    print(f"righe: {len(df):,}  colonne: {list(df.columns)}")
    print("\ntipi:"); print(df.dtypes.to_string())
    print(f"\nprime {args.rows} righe:"); print(df.head(args.rows).to_string())
    for c in df.columns:
        if df[c].nunique() < 100:
            vals = sorted(df[c].dropna().unique().tolist())[:20]
            print(f"  valori distinti di '{c}' (<=20): {vals}")
    # colonne chiave tipiche
    for key in ("u", "v", "gkey", "t", "day", "median_speed_kph", "free_flow_kph",
                "volume", "volume_class", "speed_kph", "length_meters", "lanes",
                "highway", "oneway", "x", "y", "lon", "lat", "node_id", "counter_info"):
        if key in df.columns:
            s = df[key]
            extra = f"min={s.min()} max={s.max()}" if pd.api.types.is_numeric_dtype(s) else f"nunique={s.nunique()}"
            print(f"  [{key}] {extra}")

print("ALBERATURA (max 3 livelli):"); tree(args.root)
show("SPEED_CLASSES (velocita' per segmento, per giorno)",
     sorted(Path(args.root).rglob("*speed_classes*.parquet")) or sorted(Path(args.root).rglob("speed_classes/**/*.parquet")))
show("ROAD_GRAPH — ARCHI (segmenti stradali)",
     sorted(Path(args.root).rglob("*edges*.parquet")))
show("ROAD_GRAPH — NODI (incroci)",
     sorted(Path(args.root).rglob("*nodes*.parquet")))
