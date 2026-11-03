#!/usr/bin/env python3
"""
E18-quater, parte B — distribuzione delle classi PER SENSORE nei bersagli del periodo di prova (richiesta del
revisore, 3/11/2026, 12:40). Sola lettura dei bersagli: nessun modello, nessuna predizione.

Per ciascun contesto del Paper 1 e ciascuna partizione dei nodi usata dagli esperimenti (le unita' di E8:
citta' p0-p2, PEMS08 p0-p5, PEMS04 p0-p2), con lo STESSO perimetro delle valutazioni (origini dopo t1 fino
alla fine del periodo, `origini_dopo`; bersagli ai quattro orizzonti; cella (origine, orizzonte) valida se la
classe e' > 0), per ogni sensore la quota di bersagli nella classe congestionata (classe 3) fra i validi.
Per contesto e gruppo di sensori — iniziali (`addestramento`), nuovi (`prova`), validazione — le statistiche
sulle coppie (partizione, sensore): numero, minimo, primo quartile, mediana, terzo quartile, massimo, media,
sensori con zero congestionati, sensori senza bersagli validi; e le frequenze delle tre classi aggregate.

    poetry run python evoluzione/analisi/classi_per_sensore.py            # -> results/evoluzione/e18quater_classi_risultati.json
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

CONGESTIONATA = 3
GRUPPI = (("iniziali", "addestramento"), ("nuovi", "prova"), ("validazione", "validazione"))
ORDINE_CTX = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")


def _sha(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def _stat(v):
    import numpy as np
    v = np.asarray(v, dtype="float64")
    ok = np.isfinite(v)
    q = v[ok]
    if not len(q):
        return {"n": int(len(v)), "senza_bersagli": int((~ok).sum())}
    return {"n": int(len(v)), "senza_bersagli": int((~ok).sum()), "min": float(q.min()),
            "q1": float(np.percentile(q, 25)), "mediana": float(np.median(q)), "q3": float(np.percentile(q, 75)),
            "max": float(q.max()), "media": float(q.mean()), "zero_congestionati": int((q == 0).sum())}


def main() -> int:
    import numpy as np
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.predittore import ORIZZONTI
    from evoluzione.esperimenti.addestramento import CTX, _carica, _partizioni
    from evoluzione.esperimenti.esegui_e8 import CONTESTI_E8
    ap = argparse.ArgumentParser(description="classi per sensore nei bersagli del periodo di prova")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    H = np.asarray(ORIZZONTI, dtype="int64")
    R = {"definizione": "per sensore, quota di bersagli nella classe congestionata (3) fra le celle (origine, orizzonte) valide "
                        "(classe > 0) del periodo di prova: origini dopo t1 fino alla fine del periodo (origini_dopo, come le "
                        "valutazioni), quattro orizzonti; statistiche sulle coppie (partizione, sensore) per gruppo",
         "istante": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "contesti": {}, "impronte_ingressi": {}}
    per_ctx = {}                                                             # gruppo -> {grp: [quote]}, classi
    for nome_ctx, costruisci in CONTESTI_E8.items():
        ctx = costruisci(a.out)
        unita = sorted({(c, p) for c, p, _ in ctx["unita"]})
        for c, p in unita:
            g = ctx["gruppo"](c)
            D = _carica(c, a.out / "maschere"); ok = GR.passi_regolari(D["ts"])
            e = D["r"].shape[0] - GR.MAX_ORIZZ
            t0, t1, fine, chiave = ctx["calendario"](c, "prova")
            fine = e if fine is None else (int(e * .85) if fine == "quota85" else fine)
            nodi, _ = _partizioni(D, {"partizione": np.random.default_rng(ctx["seme_partizione"](p))}, ctx["fine_periodo"])
            per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
            if not len(per):
                raise RuntimeError(f"{c} p{p}: perimetro vuoto")
            Y = D["classe"][(per[:, None] + H[None, :])]                    # (T, H, K)
            valido = Y > 0
            n_val = valido.sum((0, 1)).astype("float64")                     # per sensore
            n_cong = ((Y == CONGESTIONATA) & valido).sum((0, 1)).astype("float64")
            quota = np.where(n_val > 0, n_cong / np.maximum(n_val, 1), np.nan)
            G = per_ctx.setdefault(g, {"quote": {k: [] for k, _ in GRUPPI}, "classi": {k: np.zeros(3, "int64") for k, _ in GRUPPI},
                                       "partizioni": [], "sensori": None, "finestra": None, "origini": []})
            for grp, ch in GRUPPI:
                nn = np.asarray(nodi[ch], dtype="int64")
                G["quote"][grp] += [float(q) for q in quota[nn]]
                for k in (1, 2, 3):
                    G["classi"][grp][k - 1] += int((Y[:, :, nn] == k).sum())
            G["partizioni"].append(f"{c}/p{p}")
            G["sensori"] = int(D["classe"].shape[1]); G["origini"].append(int(len(per)))
            G["finestra"] = {"t0": int(t0), "t1": int(t1), "fine": int(fine), "orizzonti": [int(h) for h in H]}
            tp, eti = CTX[c]
            R["impronte_ingressi"][f"{c}/bersagli"] = _sha(Path(tp))
            R["impronte_ingressi"][f"{c}/maschere"] = _sha(a.out / "maschere" / f"maschere_{eti}.npz")
            print(f"  {g:10s} {c:10s} p{p}: {len(per)} origini, {D['classe'].shape[1]} sensori; quota congestionati "
                  + ", ".join(f"{grp} mediana {np.nanmedian(quota[np.asarray(nodi[ch])]):.3f}" for grp, ch in GRUPPI), flush=True)
    for g in ORDINE_CTX:
        G = per_ctx[g]
        R["contesti"][g] = {"partizioni": G["partizioni"], "sensori_per_partizione": G["sensori"],
                            "origini_per_partizione": G["origini"], "finestra": G["finestra"],
                            "gruppi": {grp: {**_stat(G["quote"][grp]),
                                             "frequenze_classi": [int(x) for x in G["classi"][grp]],
                                             "quota_congestionati_aggregata": float(G["classi"][grp][2] / max(G["classi"][grp].sum(), 1))}
                                       for grp, _ in GRUPPI}}
    fj = a.out / "e18quater_classi_risultati.json"
    fj.write_text(json.dumps(R, indent=1, ensure_ascii=False))
    print(f"  -> {fj} ({_sha(fj)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
