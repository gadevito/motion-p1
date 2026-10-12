#!/usr/bin/env python3
"""
E14, stadio 0 — quanto differisce l'ingresso statico causale da quello non causale.
=====================================================================================
Sola lettura, nessun modello. La statica consumata da tutti i bracci e' una scalare per
sensore: la copertura `m_r.mean(0)` su TUTTA la serie (`inserimento.statiche`). Qui, per
ogni contesto, episodio e partizione, si calcola per ogni sensore

    Δ = copertura non causale − copertura causale

con la copertura causale definita dal pre-registro (`protocol/E14.md`):
    iniziali (nodi di addestramento):  media di m_r su [0, t₀)
    nuovi (nodi di prova), variante (a): media di m_r su (t₀, t₀ + 24 h]
    nuovi, variante (b):                 media delle coperture causali degli iniziali
(i nodi di validazione, che selezionano e non addestrano, sono riportati a parte come
«selezione» e non entrano nel criterio). Per iniziali e nuovi: mediana, 90° percentile e
massimo di |Δ|; correlazione di rango (Spearman, senza pareggi medi) fra Δ e la frequenza
della classe rossa nel periodo di test (t₁, fine]. Criterio pre-registrato: se il 90°
percentile di |Δ| (iniziali e nuovi insieme) con la variante (a) e' < 0,01 in TUTTI i
contesti ed episodi, lo stadio A usa la sola variante (a); altrimenti entrambe.

Scrive `results/evoluzione/e14_stadio0.json` (con impronta).

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/e14_stadio0.py
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.addestramento import _carica, _partizioni  # noqa: E402
from evoluzione.esperimenti.esegui_e4 import CITTA, calendario  # noqa: E402
from evoluzione.esperimenti.esegui_e5 import episodi_registrati  # noqa: E402
from evoluzione.esperimenti.fasi import PARTIZIONI  # noqa: E402
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, SEME_PARTIZIONE_E6  # noqa: E402

L24 = 96
CLASSE_ROSSA = 2
SOGLIA_P90 = 0.01


def _spearman(x, y):
    x, y = np.asarray(x, "float64"), np.asarray(y, "float64")
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return float("nan")
    rx = np.argsort(np.argsort(x[ok])).astype("float64"); ry = np.argsort(np.argsort(y[ok])).astype("float64")
    rx -= rx.mean(); ry -= ry.mean()
    d = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / d) if d > 0 else float("nan")


def _stat(v):
    v = np.abs(np.asarray(v, "float64"))
    return {"n": int(v.size), "mediana": float(np.median(v)), "p90": float(np.percentile(v, 90)),
            "massimo": float(v.max())} if v.size else {"n": 0}


def _cella(D, nodi, t0, t1, fine):
    m = D["m_r"].astype("float64")
    cov_nc = m.mean(0)
    cov_c_ini = m[:t0].mean(0)                          # [0, t0)
    cov_a = m[t0 + 1:t0 + L24 + 1].mean(0)              # (t0, t0 + 24 h]
    ini, nuo, sel = nodi["addestramento"], nodi["prova"], nodi["validazione"]
    cov_b_nuovi = float(cov_c_ini[ini].mean())          # media delle coperture causali degli iniziali
    d_ini = cov_nc[ini] - cov_c_ini[ini]
    d_sel = cov_nc[sel] - cov_c_ini[sel]
    d_a = cov_nc[nuo] - cov_a[nuo]
    d_b = cov_nc[nuo] - cov_b_nuovi
    cl = D["classe"][t1 + 1:fine + 1]
    rosso = (cl == CLASSE_ROSSA).mean(0)
    return {"nodi": {"iniziali": int(len(ini)), "nuovi": int(len(nuo)), "selezione": int(len(sel))},
            "copertura_non_causale": {"iniziali_media": float(cov_nc[ini].mean()), "nuovi_media": float(cov_nc[nuo].mean())},
            "copertura_causale_iniziali_media": float(cov_c_ini[ini].mean()), "copertura_b_nuovi": cov_b_nuovi,
            "delta_iniziali": _stat(d_ini), "delta_selezione": _stat(d_sel),
            "delta_nuovi_a": _stat(d_a), "delta_nuovi_b": _stat(d_b),
            "p90_abs_delta_tutti_a": float(np.percentile(np.abs(np.concatenate([d_ini, d_a])), 90)),
            "p90_abs_delta_tutti_b": float(np.percentile(np.abs(np.concatenate([d_ini, d_b])), 90)),
            "rho_delta_rosso": {"iniziali": _spearman(d_ini, rosso[ini]), "nuovi_a": _spearman(d_a, rosso[nuo]),
                                "nuovi_b": _spearman(d_b, rosso[nuo])},
            "frequenza_rosso_test": {"iniziali": float(rosso[ini].mean()), "nuovi": float(rosso[nuo].mean())},
            "_grezzi": {"d_ini": d_ini, "d_a": d_a, "d_b": d_b}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    ep5 = episodi_registrati(a.out)
    piani = []                                           # (gruppo, contesto, episodio, partizione, seme_part, t0, t1, fine, fine_partizioni)
    for c in CITTA:
        t0, t1 = calendario("prova", c)
        for p in PARTIZIONI:
            piani.append((c, c, 1, p, SEME_PARTIZIONE[p], t0, t1, None, None))
            for k in (2, 3):
                e = ep5[c][k]
                piani.append((c, c, k, p, SEME_PARTIZIONE[p], e["t0"], e["t1"], e["fine"], e["t0"]))
    for k in range(6):
        piani.append(("PEMS08", f"PEMS08_p{k}", 1, k, SEME_PARTIZIONE_E6[k], 3840, 3840 + L24, None, 3840))
    for k in range(3):
        piani.append(("PEMS04", f"PEMS04_p{k}", 1, k, SEME_PARTIZIONE_E6[k], 4807, 4807 + L24, None, 4807))
    R, cache, pool = {}, {}, {}
    print("=" * 96)
    print("E14 — STADIO 0: Δ copertura = non causale − causale, per sensore")
    print("=" * 96)
    print(f"  {'gruppo':8s} ep p  {'ini n':>5} {'|Δ| p90':>8} {'max':>7} | {'nuovi n':>7} {'(a) p90':>8} {'max':>7} "
          f"{'(b) p90':>8} {'max':>7} | {'p90 tutti(a)':>12} {'ρ(Δ,rosso) ini/a/b':>22}")
    for g, c, k, p, sp, t0, t1, fine, fine_part in piani:
        if c not in cache:
            cache[c] = _carica(c, a.out / "maschere")
        D = cache[c]
        from evoluzione.componente import griglia as GR
        e = D["r"].shape[0] - GR.MAX_ORIZZ
        nodi, _ = _partizioni(D, {"partizione": np.random.default_rng(sp)}, fine_part)
        r = _cella(D, nodi, t0, t1, fine if fine is not None else e)
        gz = r.pop("_grezzi")
        key = f"{g}/ep{k}/p{p}"
        R[key] = {"contesto": c, "episodio": k, "partizione": p, "t0": t0, "t1": t1, "fine": fine if fine is not None else e, **r}
        q = pool.setdefault(f"{g}/ep{k}", {"d_ini": [], "d_a": [], "d_b": []})
        for kk in q:
            q[kk].append(gz[kk])
        print(f"  {g:8s} {k}  {p}  {r['nodi']['iniziali']:5d} {r['delta_iniziali']['p90']:8.4f} {r['delta_iniziali']['massimo']:7.4f} | "
              f"{r['nodi']['nuovi']:7d} {r['delta_nuovi_a']['p90']:8.4f} {r['delta_nuovi_a']['massimo']:7.4f} "
              f"{r['delta_nuovi_b']['p90']:8.4f} {r['delta_nuovi_b']['massimo']:7.4f} | {r['p90_abs_delta_tutti_a']:12.4f} "
              f"{r['rho_delta_rosso']['iniziali']:+.2f} / {r['rho_delta_rosso']['nuovi_a']:+.2f} / {r['rho_delta_rosso']['nuovi_b']:+.2f}")
    # per contesto ed episodio, partizioni riunite (ogni sensore conta una volta per partizione, nel suo ruolo)
    S = {}
    for key, q in pool.items():
        d_ini, d_a, d_b = (np.concatenate(q[kk]) for kk in ("d_ini", "d_a", "d_b"))
        S[key] = {"delta_iniziali": _stat(d_ini), "delta_nuovi_a": _stat(d_a), "delta_nuovi_b": _stat(d_b),
                  "p90_abs_delta_tutti_a": float(np.percentile(np.abs(np.concatenate([d_ini, d_a])), 90)),
                  "p90_abs_delta_tutti_b": float(np.percentile(np.abs(np.concatenate([d_ini, d_b])), 90))}
    sotto = {k: v["p90_abs_delta_tutti_a"] < SOGLIA_P90 for k, v in S.items()}
    verdetto = "stadio A con la sola variante (a)" if all(sotto.values()) else "stadio A con entrambe le varianti (a) e (b)"
    print("\n  per contesto ed episodio (partizioni riunite): p90 |Δ| variante (a), iniziali + nuovi")
    for k, v in S.items():
        print(f"    {k:14s} {v['p90_abs_delta_tutti_a']:.4f}  {'< 0,01' if sotto[k] else '>= 0,01'}   "
              f"(iniziali p90 {v['delta_iniziali']['p90']:.4f}, nuovi (a) p90 {v['delta_nuovi_a']['p90']:.4f}, nuovi (b) p90 {v['delta_nuovi_b']['p90']:.4f})")
    print(f"\n  criterio pre-registrato (p90 |Δ| < {SOGLIA_P90} ovunque, variante (a)): "
          f"{'VERIFICATO' if all(sotto.values()) else 'NON verificato'} → {verdetto}")
    doc = {"istante": datetime.now(timezone.utc).isoformat(), "soglia_p90": SOGLIA_P90, "classe_rossa": CLASSE_ROSSA,
           "definizioni": {"non_causale": "media di m_r su tutta la serie (inserimento.statiche)",
                           "iniziali": "media di m_r su [0, t0)", "nuovi_a": "media di m_r su (t0, t0+96]",
                           "nuovi_b": "media delle coperture causali degli iniziali", "test": "(t1, fine]"},
           "per_cella": R, "per_contesto_episodio": S, "criterio": {"sotto_soglia": sotto, "verdetto": verdetto}}
    fj = a.out / "e14_stadio0.json"
    fj.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"  salvato in {fj} (impronta {hashlib.sha256(fj.read_bytes()).hexdigest()[:16]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
