#!/usr/bin/env python3
"""
Misura del parallelismo, prima di sceglierlo.
==============================================
**Misura soltanto tempi e numerica, mai prestazioni predittive.** Non tocca i
risultati.

DUE DOMANDE:

    A. il numero di fili di calcolo cambia la NUMERICA?
       Se si', la campagna intera deve usare lo STESSO numero, e va registrato:
       le configurazioni appaiate non devono differire per ambiente.

    B. quale combinazione processi x fili da' piu' aggiornamenti al secondo?
       Su Apple Silicon i nuclei non sono tutti uguali: si misura, non si
       assume.

Si usa il braccio C, il piu' semplice: il costo per aggiornamento e' quasi lo
stesso negli altri, e qui interessa il rapporto fra configurazioni.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/misura_parallelismo.py
"""
import hashlib
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

AGG = 100          # aggiornamenti per lavoratore nella misura B


def _lavora(args):
    """Un lavoratore: carica, costruisce C, esegue `agg` aggiornamenti."""
    fili, agg, seme = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente.identita import NoIdentity
    from evoluzione.componente.predittore import PredittorePerNodo
    from evoluzione.esperimenti.addestramento import (
        _canali, _carica, _lotto, _normalizzazione, _partizioni, _perdita)
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    out = Path("results/evoluzione")
    D = _carica("Madrid", out / "maschere")
    nodi, ist = _partizioni(D, {"partizione":
                                np.random.default_rng(SEME_PARTIZIONE[0])})
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    K = D["r"].shape[1]
    stat = torch.as_tensor(np.stack([D["m_r"].mean(0), np.zeros(K), np.ones(K),
                                     np.zeros(K), np.ones(K)], 1)
                           .astype("float32"))
    w = torch.as_tensor(carica_pesi(out / "pesi", "Madrid", 0).vettore(),
                        dtype=torch.float32)
    torch.manual_seed(seme)
    m = PredittorePerNodo(0, 5, sorgente="traffic4cast", identita=NoIdentity())
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    g = np.random.default_rng(seme)
    na = nodi["addestramento"]
    t0 = time.time()
    for _ in range(agg):
        m.train()
        idx = g.choice(ist["addestramento"], size=32, replace=False)
        X, Y, Mk = _lotto(x, D["classe"], np.sort(idx), na)
        L, _ = _perdita(m(X, node_ids=na, static_inputs=stat[na]), Y, Mk, w)
        opt.zero_grad(); L.backward(); opt.step()
    dt = time.time() - t0
    h = hashlib.sha256()
    for k, v in sorted(m.state_dict().items()):
        h.update(v.detach().cpu().numpy().tobytes())
    return dt, h.hexdigest()[:16]


def main() -> int:
    n = os.cpu_count() or 1
    print("=" * 78)
    print(f"MISURA DEL PARALLELISMO — {n} nuclei logici")
    print("=" * 78)
    ctx = mp.get_context("spawn")

    # ---- A: la numerica dipende dal numero di fili? --------------------
    print("\n[A] il numero di fili cambia i pesi?  (50 aggiornamenti, seme 7)\n")
    impronte = {}
    for f in sorted({1, 2, 4, n}):
        with ctx.Pool(1) as p:
            _, h = p.apply(_lavora, ((f, 50, 7),))
        impronte[f] = h
        print(f"  fili {f:2d}: impronta dei pesi {h}")
    uguali = len(set(impronte.values())) == 1
    print(f"\n  > {'IDENTICI: il numero di fili NON cambia la numerica' if uguali else 'DIVERSI: il numero di fili CAMBIA la numerica'}")
    if not uguali:
        print("  > la campagna intera deve usare UN SOLO numero di fili, "
              "registrato,")
        print("  > e i punti E riaddestrati non saranno bit-identici a quelli")
        print("  > ottenuti con un numero diverso.")

    # ---- B: il rendimento ----------------------------------------------
    print(f"\n[B] rendimento, {AGG} aggiornamenti per lavoratore\n")
    config = [(1, n)]
    for k in (2, 3, 4, 6, 8, 12):
        if k <= n:
            config.append((k, max(1, n // k)))
    print(f"  {'processi':>9} {'fili':>5} {'parete':>9} {'agg/s':>8} "
          f"{'rispetto a 1':>13}")
    base = None
    ris = []
    for k, f in config:
        t0 = time.time()
        with ctx.Pool(k) as p:
            p.map(_lavora, [(f, AGG, 7 + i) for i in range(k)])
        parete = time.time() - t0
        tp = k * AGG / parete
        base = base or tp
        ris.append((k, f, parete, tp))
        print(f"  {k:9d} {f:5d} {parete:8.1f}s {tp:8.2f} {tp/base:12.2f}x")
    k, f, _, tp = max(ris, key=lambda r: r[3])
    print(f"\n  migliore: {k} processi x {f} fili, {tp/base:.2f}x")
    print(f"  la parete include il caricamento dei dati, uguale per tutti")
    print(f"\n  stima per la campagna, 276 ore-macchina: "
          f"~{276 / (tp/base):.0f} ore di calendario")
    print("\n  **Solo tempi**: nessuna prestazione predittiva e' stata")
    print("  osservata, e la numerosita' della campagna non cambia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
