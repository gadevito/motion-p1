#!/usr/bin/env python3
"""
Profilo di MoGERNN, PRIMA di ottimizzare.
==========================================
Dove vanno i 18,6 secondi per aggiornamento con 765 nodi? Senza questa
risposta si rischia di ottimizzare una voce trascurabile.

Commit esaminato: 86b153fb4bf9358e32079930ccaea1cbcffa66f8. **Il codice
originale non viene modificato**: si avvolgono le funzioni per misurarle.

MISURA

    [A] forward per componente, con CONTEGGIO delle chiamate:
        random walk dell'encoder/decoder (MoGERNN.py 218-219)
        random walk dell'esperto di diffusione (agg.py 131-132)
        ciascuno dei cinque esperti
        convoluzioni di diffusione delle celle ricorrenti (DiffConv)
    [B] operazioni di torch, forward E backward, col profiler
    [C] memoria di picco del processo

**Il conteggio delle chiamate con un solo esperto attivo** mostra dal percorso
d'esecuzione se gli esperti non scelti vengono calcolati: e' la prova che il
revisore chiede oltre al rapporto dei tempi.

Uso:

    poetry run python evoluzione/audit/profila_mogernn.py --repo /percorso/MoGERNN-main
"""
import argparse
import resource
import sys
import time
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import torch

TEMPI = defaultdict(float)
CHIAMATE = defaultdict(int)


def avvolgi(nome, f):
    def g(*a, **k):
        t0 = time.perf_counter()
        r = f(*a, **k)
        TEMPI[nome] += time.perf_counter() - t0
        CHIAMATE[nome] += 1
        return r
    return g


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--nodi", type=int, default=765)
    ap.add_argument("--lotto", type=int, default=64)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo.resolve()))
    import model.MoGERNN as M
    import layers.agg as G
    import layers.DCRNNCell as R

    # le due random walk si distinguono per il modulo che le importa
    M.calculate_random_walk_matrix = avvolgi(
        "rw encoder/decoder", M.calculate_random_walk_matrix)
    G.calculate_random_walk_matrix = avvolgi(
        "rw esperto diffusione", G.calculate_random_walk_matrix)
    for nome in ("MeanAggregator", "WMeanAggregator", "MaxPoolingAggregator",
                 "MinPoolingAggregator", "DiffusionAggregator"):
        C = getattr(G, nome)
        C.forward = avvolgi(f"esperto {nome}", C.forward)
    R.DiffConv.forward = avvolgi("DiffConv (celle ricorrenti)",
                                 R.DiffConv.forward)

    def cfg(k):
        return SimpleNamespace(
            input_len=12, pred_len=12, look_back=0, d_model=64, e_layers=2,
            k_hop=1, enc_in=1, num_experts=5, num_used_experts=k,
            mean_expert=True, weight_expert=True, max_expert=True,
            min_expert=True, diffusion_expert=True)

    N, B = a.nodi, a.lotto
    g = torch.Generator().manual_seed(0)
    A = (torch.rand(N, N, generator=g) < 0.05).float() * torch.rand(N, N,
                                                                    generator=g)
    A.fill_diagonal_(1.0)
    X = torch.randn(B, 12, N, 1, generator=g)
    X[:, :, : N // 4] = 0.0                       # un quarto dei nodi ignoti
    Y = torch.randn(B, 12, N, 1, generator=g)

    print("=" * 78)
    print(f"PROFILO MoGERNN — {N} nodi, lotto {B}, un aggiornamento")
    print("=" * 78)

    # ---- [A] forward per componente, con un solo esperto attivo --------
    m = M.Model(cfg(1)).float()
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    m.train()
    out = m(A, X, None, None, Y, None, 1)            # riscaldamento
    torch.nn.functional.mse_loss(out, Y).backward()
    TEMPI.clear(); CHIAMATE.clear()
    t0 = time.perf_counter()
    opt.zero_grad()
    out = m(A, X, None, None, Y, None, 1)
    t_fw = time.perf_counter() - t0
    t1 = time.perf_counter()
    torch.nn.functional.mse_loss(out, Y).backward(); opt.step()
    t_bw = time.perf_counter() - t1
    print(f"\n[A] forward {t_fw:.2f} s | backward + passo {t_bw:.2f} s | "
          f"totale {t_fw + t_bw:.2f} s")
    print(f"    **un solo esperto attivo** (num_used_experts = 1)\n")
    print(f"    {'componente':34s} {'chiamate':>9} {'secondi':>9} "
          f"{'% forward':>10}")
    for k in sorted(TEMPI, key=TEMPI.get, reverse=True):
        print(f"    {k:34s} {CHIAMATE[k]:9d} {TEMPI[k]:9.3f} "
              f"{100 * TEMPI[k] / t_fw:9.1f}%")
    esperti = [k for k in CHIAMATE if k.startswith("esperto")]
    print(f"\n    esperti CHIAMATI con un solo esperto attivo: {len(esperti)}/5")
    print(f"    -> {'tutti calcolati: il gating sparso NON evita il calcolo' if len(esperti) == 5 else 'solo quelli scelti'}")

    # ---- [B] operazioni di torch, forward e backward --------------------
    from torch.profiler import ProfilerActivity, profile
    with profile(activities=[ProfilerActivity.CPU]) as prof:
        opt.zero_grad()
        out = m(A, X, None, None, Y, None, 1)
        torch.nn.functional.mse_loss(out, Y).backward(); opt.step()
    print(f"\n[B] operazioni piu' costose, forward E backward "
          f"(tempo proprio)\n")
    print(prof.key_averages().table(sort_by="self_cpu_time_total",
                                    row_limit=12, max_name_column_width=34))

    # ---- [C] memoria ------------------------------------------------------
    picco = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    picco_gb = picco / 1e9 if sys.platform == "darwin" else picco / 1e6
    print(f"[C] memoria di picco del processo: {picco_gb:.1f} GB")
    print(f"    con 8 processi in parallelo: ~{8 * picco_gb:.0f} GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
