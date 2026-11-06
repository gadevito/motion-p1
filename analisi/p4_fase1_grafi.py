#!/usr/bin/env python3
"""
Paper 4, fase 1, punto 3 (richiesta del revisore, 6/11/2026): caratterizzazione dal file dei tre grafi senza
generatore in `data_collection/traffic4cast/MADRID_2022/gomo_fmt/` — `t4cmad_rand_k1.pkl`, `t4cmad_rand_k2.pkl`,
`t4cmad_identity_graph.pkl` — e, per confronto, del grafo stradale `t4cmad_routes-graph.pkl` (da `t4c22_adapter.py`).
Per ciascuno: impronta, byte, data di modifica, tipo, nodi, archi, orientato/multi, attributi di nodi e archi,
distribuzione dei gradi (min, quartili, mediana, media, max, istogramma), pesi (min, mediana, media, max),
componenti connesse, cappi, archi doppi, sovrapposizione di nodi e archi con il grafo stradale.
Scrive `protocol/paper4/fase1/GRAFI_SENZA_GENERATORE.md`. Sola lettura.

    poetry run python analisi/p4_fase1_grafi.py --dir ../OR3/data_collection/traffic4cast/MADRID_2022/gomo_fmt
"""
import argparse
import hashlib
import pickle
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
FILE = ("t4cmad_rand_k1.pkl", "t4cmad_rand_k2.pkl", "t4cmad_identity_graph.pkl", "t4cmad_routes-graph.pkl")


def _sha(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def q(v, p):
    import numpy as np
    return float(np.percentile(np.asarray(v, dtype="float64"), p)) if len(v) else float("nan")


def descrivi(G):
    import networkx as nx
    import numpy as np
    d = {"tipo": type(G).__name__, "orientato": G.is_directed(), "multi": G.is_multigraph(),
         "nodi": G.number_of_nodes(), "archi": G.number_of_edges()}
    gradi = [g for _, g in G.degree()]
    d["grado"] = {"min": min(gradi), "q1": q(gradi, 25), "mediana": q(gradi, 50), "q3": q(gradi, 75), "max": max(gradi),
                  "media": float(np.mean(gradi))} if gradi else {}
    d["istogramma_gradi"] = sorted(Counter(gradi).items())
    attr_n = Counter(k for _, z in G.nodes(data=True) for k in z); attr_e = Counter(k for *_, z in G.edges(data=True) for k in z)
    d["attributi_nodi"], d["attributi_archi"] = dict(attr_n), dict(attr_e)
    pesi = [z["weight"] for *_, z in G.edges(data=True) if "weight" in z and isinstance(z["weight"], (int, float))]
    d["pesi"] = {"n": len(pesi), "min": min(pesi), "mediana": q(pesi, 50), "media": float(np.mean(pesi)), "max": max(pesi)} if pesi else {"n": 0}
    d["cappi"] = int(nx.number_of_selfloops(G))
    U = G.to_undirected() if G.is_directed() else G
    comp = sorted((len(c) for c in nx.connected_components(U)), reverse=True)
    d["componenti"] = {"n": len(comp), "gigante": comp[0] if comp else 0, "prime": comp[:5]}
    d["tipo_nodo"] = Counter(type(n).__name__ for n in G.nodes()).most_common(3)
    d["esempio_nodi"] = [repr(n) for n in list(G.nodes())[:3]]
    d["esempio_arco"] = repr(next(iter(G.edges(data=True)), None))[:200]
    d["gradi_fissi"] = (len(set(gradi)) == 1)
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=RADICE / "protocol" / "paper4" / "fase1" / "GRAFI_SENZA_GENERATORE.md")
    a = ap.parse_args()
    G, D = {}, {}
    for f in FILE:
        p = a.dir / f
        if not p.exists():
            print(f"FERMO: manca {p}"); return 1
        with open(p, "rb") as h:
            G[f] = pickle.load(h)
        D[f] = descrivi(G[f])
        D[f]["file"] = {"sha256": _sha(p), "byte": p.stat().st_size,
                        "modificato": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
    rif = G["t4cmad_routes-graph.pkl"]
    N0, E0 = set(rif.nodes()), {frozenset(e) for e in rif.edges()}
    L = ["# Paper 4, fase 1 — grafi senza generatore: caratterizzazione dal file", "",
         f"Generato da `analisi/p4_fase1_grafi.py` il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} (non modificare a mano) "
         f"da `{a.dir}`. I tre grafi `t4cmad_rand_k1.pkl`, `t4cmad_rand_k2.pkl` (scritti nello stesso secondo, 22/8/2026) e "
         "`t4cmad_identity_graph.pkl` (21/8/2026) non hanno generatore nel repository ne' nelle storie (D9); le sole tracce d'uso "
         "sono `OLD/log/randk.log` (dieci esecuzioni di `models/gomo_sparse.py`, CSV di uscita non conservati) e `OLD/log/identita.log` "
         "(`replication/identita/ident_t4cmad_s0-4.csv`, conservati). Il grafo stradale `t4cmad_routes-graph.pkl` "
         "(`data_collection/traffic4cast/t4c22_adapter.py` r. 144) e' il riferimento per la sovrapposizione.", "",
         "| file | sha256 | byte | modificato | tipo | nodi | archi | cappi | comp. (gigante) | gradi min/q1/med/q3/max (media) | pesi n, min/med/media/max |",
         "|---|---|---:|---|---|---:|---:|---:|---|---|---|"]
    for f in FILE:
        d = D[f]; g = d["grado"]; w = d["pesi"]
        L.append(f"| `{f}` | `{d['file']['sha256']}` | {d['file']['byte']:,} | {d['file']['modificato']} | {d['tipo']}"
                 f"{' orientato' if d['orientato'] else ''}{' multi' if d['multi'] else ''} | {d['nodi']} | {d['archi']} | {d['cappi']} | "
                 f"{d['componenti']['n']} ({d['componenti']['gigante']}) | "
                 + (f"{g['min']}/{g['q1']:.0f}/{g['mediana']:.0f}/{g['q3']:.0f}/{g['max']} ({g['media']:.2f})" if g else "—") + " | "
                 + (f"{w['n']}, {w['min']:.1f}/{w['mediana']:.1f}/{w['media']:.1f}/{w['max']:.1f}" if w["n"] else "nessun peso") + " |")
    L += ["", "## Dettaglio per grafo", ""]
    for f in FILE:
        d, g = D[f], G[f]
        Nf, Ef = set(g.nodes()), {frozenset(e) for e in g.edges()}
        L += [f"### `{f}`", "",
              f"- attributi dei nodi: {d['attributi_nodi'] or 'nessuno'}; attributi degli archi: {d['attributi_archi'] or 'nessuno'}",
              f"- tipo dei nodi: {d['tipo_nodo']}; esempi: {', '.join(d['esempio_nodi'])}; esempio di arco: `{d['esempio_arco']}`",
              f"- istogramma dei gradi (grado: nodi): " + ", ".join(f"{k}: {v}" for k, v in d["istogramma_gradi"]) + (" — **grado costante**" if d["gradi_fissi"] else ""),
              f"- componenti connesse: {d['componenti']['n']}, le piu' grandi {d['componenti']['prime']}",
              f"- nodi in comune con il grafo stradale: {len(Nf & N0)} su {len(Nf)}; archi (non orientati) in comune: {len(Ef & E0)} su {len(Ef)}", ""]
    r1, r2 = G["t4cmad_rand_k1.pkl"], G["t4cmad_rand_k2.pkl"]
    E1, E2 = {frozenset(e) for e in r1.edges()}, {frozenset(e) for e in r2.edges()}
    L += ["## Relazioni fra i grafi", "",
          f"- `rand_k1` e `rand_k2`: stessi nodi: {set(r1.nodes()) == set(r2.nodes())}; archi in comune {len(E1 & E2)} "
          f"(k1 ha {len(E1)}, k2 {len(E2)}); rapporto archi k2/k1 = {len(E2) / max(len(E1), 1):.2f}",
          f"- lettura: se `k` fosse il numero di vicini per nodo, un grafo a k vicini non orientato avrebbe grado medio fra k e 2k "
          f"(k1: {D['t4cmad_rand_k1.pkl']['grado']['media']:.2f}; k2: {D['t4cmad_rand_k2.pkl']['grado']['media']:.2f}); "
          "con coppie casuali a pari numero di archi il grado medio sarebbe 2·archi/nodi: "
          f"k1 {2 * len(E1) / max(r1.number_of_nodes(), 1):.2f}, k2 {2 * len(E2) / max(r2.number_of_nodes(), 1):.2f}.",
          f"- `identity_graph`: {D['t4cmad_identity_graph.pkl']['archi']} archi su {D['t4cmad_identity_graph.pkl']['nodi']} nodi, "
          f"cappi {D['t4cmad_identity_graph.pkl']['cappi']}" + (" — **nessun arco: grafo identita' (nessuna propagazione fra nodi)**" if D['t4cmad_identity_graph.pkl']['archi'] == 0 else (" — **solo cappi**" if D['t4cmad_identity_graph.pkl']['archi'] == D['t4cmad_identity_graph.pkl']['cappi'] else "")) + ".", "",
          f"Script: `analisi/p4_fase1_grafi.py` `{_sha(Path(__file__))}`.", ""]
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text("\n".join(L))
    print("\n".join(L[:12])); print(f"  -> {a.out} ({_sha(a.out)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
