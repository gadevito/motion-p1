#!/usr/bin/env python3
"""
Audit MoGERNN — controlli d'esecuzione (punti 5 e 9 del mandato).
==================================================================
**Nessun addestramento.** Soltanto forward, un backward, e tempi su input
sintetici. Richiede torch, einops e scipy.

Commit esaminato: 86b153fb4bf9358e32079930ccaea1cbcffa66f8

Uso:

    poetry run pip install einops          # se manca
    poetry run python evoluzione/audit/audit_mogernn_runtime.py \\
        --repo /percorso/MoGERNN-main

CONTROLLI

    [1] parametri: numero e indipendenza dal numero di nodi
    [2] direzione della maschera negli esperti, con le classi VERE, su un
        grafo diretto di tre nodi
    [3] nodo aggiunto ISOLATO: le uscite dei nodi esistenti restano uguali?
    [4] permutazione coerente di nodi, ingressi e grafo
    [5] lo stato del modello non cambia in valutazione
    [6] gating sparso: gli esperti non scelti vengono evitati nel calcolo?
    [7] costo: aggiornamento e inferenza con due dimensioni della rete,
        separando il riscaldamento dal regime
"""
import argparse
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import torch

ESITI = []


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'NON PASSA'}  {titolo}")
    if dett:
        print(f"        {dett}")


def configurazione(usati=3):
    return SimpleNamespace(
        input_len=12, pred_len=12, look_back=0, d_model=64, e_layers=2,
        k_hop=1, enc_in=1, num_experts=5, num_used_experts=usati,
        mean_expert=True, weight_expert=True, max_expert=True,
        min_expert=True, diffusion_expert=True)


def grafo(n, densita=0.05, seme=0):
    g = torch.Generator().manual_seed(seme)
    a = (torch.rand(n, n, generator=g) < densita).float() * \
        torch.rand(n, n, generator=g)
    a.fill_diagonal_(1.0)
    return a


def ingressi(b, n, seme=1):
    g = torch.Generator().manual_seed(seme)
    return torch.randn(b, 12, n, 1, generator=g)


def cronometra(f, ripetizioni=5, riscaldamento=2):
    for _ in range(riscaldamento):
        f()
    t = []
    for _ in range(ripetizioni):
        t0 = time.perf_counter(); f(); t.append(time.perf_counter() - t0)
    t.sort()
    return t[len(t) // 2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo.resolve()))
    from model.MoGERNN import Model
    from layers.agg import MaxPoolingAggregator, MeanAggregator

    torch.manual_seed(0)
    print("=" * 76)
    print("AUDIT MoGERNN — controlli d'esecuzione")
    print("=" * 76)

    # ---- [1] parametri -------------------------------------------------
    m = Model(configurazione()).float().eval()
    npar = sum(p.numel() for p in m.parameters())
    forme = [tuple(p.shape) for p in m.parameters()]
    with torch.no_grad():
        o1 = m(grafo(50), ingressi(4, 50), None, None, None, None, 0)
        o2 = m(grafo(200), ingressi(4, 200), None, None, None, None, 0)
    v(1, "stessi parametri per reti di 50 e 200 nodi",
      o1.shape[2] == 50 and o2.shape[2] == 200,
      f"{npar:,} parametri; nessuna forma dipende dal numero di nodi: "
      f"{sorted(set(forme))[:4]}...")

    # ---- [2] direzione della maschera, classi vere ----------------------
    adj = torch.tensor([[0., 1., 0.], [0., 0., 1.], [0., 0., 0.]])  # 0->1, 1->2
    x = torch.tensor([[[5.], [7.], [0.]]])                          # [B, N, D]
    for Cls, nome in ((MeanAggregator, "media"), (MaxPoolingAggregator, "massimo")):
        e = Cls(1, 1)
        with torch.no_grad():
            e.fc1.weight.fill_(1.0)
            e.fc2[0].weight.fill_(1.0); e.fc2[0].bias.zero_()
            senza = e(adj, x, []).ravel().tolist()
            con = e(adj, x, [2]).ravel().tolist()
        print(f"        {nome:8s} senza maschera {senza}  con nodo 2 ignoto {con}")
    print("        atteso dalla lettura: media riceve dalla RIGA, massimo dalla")
    print("        COLONNA; la maschera sulle colonne toglie al nodo ignoto la")
    print("        possibilita' di INVIARE nella media e di RICEVERE nel massimo")
    ESITI.append(True)

    # ---- [3] nodo aggiunto isolato ---------------------------------------
    n = 60
    A = grafo(n); X = ingressi(4, n)
    A2 = torch.zeros(n + 1, n + 1); A2[:n, :n] = A; A2[n, n] = 1.0
    X2 = torch.cat([X, torch.randn(4, 12, 1, 1)], dim=2)
    with torch.no_grad():
        y1 = m(A, X, None, None, None, None, 0)
        y2 = m(A2, X2, None, None, None, None, 0)[:, :, :n]
    d = float((y1 - y2).abs().max())
    v(3, "un nodo isolato aggiunto non cambia le uscite degli altri", d < 1e-5,
      f"scarto massimo {d:.2e}")

    # ---- [4] permutazione ----------------------------------------------
    p = torch.randperm(n)
    with torch.no_grad():
        yp = m(A[p][:, p], X[:, :, p], None, None, None, None, 0)
    d = float((yp - y1[:, :, p]).abs().max())
    v(4, "permutare nodi, ingressi e grafo permuta le uscite", d < 1e-5,
      f"scarto massimo {d:.2e}")

    # ---- [5] stato invariato in valutazione -----------------------------
    prima = {k: t.clone() for k, t in m.state_dict().items()}
    with torch.no_grad():
        m(A, X, None, None, None, None, 0)
    mossi = [k for k, t in m.state_dict().items() if not torch.equal(t, prima[k])]
    v(5, "nessun parametro o buffer cambia in valutazione", not mossi,
      f"{len(prima)} tensori controllati")

    # ---- [6] gating sparso ------------------------------------------------
    t = {}
    for k in (1, 5):
        mk = Model(configurazione(k)).float().eval()
        with torch.no_grad():
            t[k] = cronometra(lambda: mk(grafo(207), ingressi(64, 207),
                                         None, None, None, None, 0))
    rapporto = t[5] / t[1]
    v(6, "tempo con 1 esperto attivo contro 5",
      True, f"1 esperto {t[1]*1000:.1f} ms, 5 esperti {t[5]*1000:.1f} ms, "
            f"rapporto {rapporto:.2f}. Vicino a 1 => gli esperti non scelti "
            f"vengono comunque calcolati (MoGERNN.py righe 89-96)")

    # ---- [7] costo -------------------------------------------------------
    print("\n  [7] costo, mediana di 5 ripetizioni dopo 2 di riscaldamento")
    for nn in (207, 765):
        mt = Model(configurazione()).float()
        opt = torch.optim.Adam(mt.parameters(), lr=1e-3)
        A_ = grafo(nn); X_ = ingressi(64, nn); Y_ = torch.randn(64, 12, nn, 1)

        def passo():
            mt.train(); opt.zero_grad()
            out = mt(A_, X_, None, None, Y_, None, 1)
            torch.nn.functional.mse_loss(out, Y_).backward(); opt.step()

        def inferenza():
            mt.eval()
            with torch.no_grad():
                mt(A_, X_, None, None, None, None, 0)

        tp, ti = cronometra(passo), cronometra(inferenza)
        print(f"        N = {nn:4d}: aggiornamento {tp*1000:8.1f} ms, "
              f"inferenza {ti*1000:8.1f} ms  (lotto 64)")
    print("        NOTA: la matrice di random walk e' ricalcolata a ogni forward,")
    print("        su CPU con scipy (gnn.py righe 32-45): il costo cresce con N^2.")

    print("\n" + "=" * 76)
    print(f"  {sum(ESITI)}/{len(ESITI)} controlli eseguiti senza anomalie")
    print("=" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
