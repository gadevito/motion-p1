#!/usr/bin/env python3
"""
Collaudo del token ignoto e dell'identity dropout (E2).
========================================================
Uso (dalla radice OR3/):

    poetry run python evoluzione/componente/collauda_token_ignoto.py
"""
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.identita import LearnedNodeEmbedding  # noqa: E402

E = []


def v(n, titolo, cond, dett=""):
    E.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def main() -> int:
    print("=" * 76)
    print("TOKEN IGNOTO E IDENTITY DROPOUT")
    print("=" * 76)
    ids = list(range(40))
    g = torch.Generator().manual_seed(0)
    f = LearnedNodeEmbedding(ids, generatore=g, token_ignoto=True, rho=0.15)

    f.eval()
    a = f(2, 40, node_ids=ids); b = f(2, 40, node_ids=ids)
    v(1, "in VALUTAZIONE il fornitore e' deterministico", torch.equal(a, b),
      "il dropout non deve agire fuori dall'addestramento")

    f.train()
    torch.manual_seed(1); c1 = f(2, 40, node_ids=ids)
    torch.manual_seed(2); c2 = f(2, 40, node_ids=ids)
    v(2, "in ADDESTRAMENTO il dropout sostituisce righe diverse",
      not torch.equal(c1, c2))

    torch.manual_seed(7)
    quote = []
    for _ in range(200):
        z = f(1, 40, node_ids=ids)[0, :, :, 0].T          # (40, 8)
        quote.append(float((z == f.ignoto[0]).all(1).float().mean()))
    q = sum(quote) / len(quote)
    v(3, "la quota sostituita approssima rho", abs(q - 0.15) < 0.02,
      f"{q:.4f} contro 0,15 atteso, su 200 lotti")

    f.eval()
    m = torch.zeros(40, dtype=torch.bool); m[3] = True
    z = f(1, 40, node_ids=ids, ignoti=m)[0, :, :, 0].T
    v(4, "la maschera esplicita agisce sui soli nodi indicati",
      bool(torch.allclose(z[3], f.ignoto[0]))
      and not bool(torch.allclose(z[4], f.ignoto[0])))

    f2 = LearnedNodeEmbedding(ids, generatore=g)
    try:
        f2(1, 40, node_ids=ids, ignoti=m)
        ko = False
    except ValueError:
        ko = True
    v(5, "senza token, nodi ignoti vengono RIFIUTATI", ko)

    try:
        LearnedNodeEmbedding(ids, generatore=g, rho=0.15)
        ko2 = False
    except ValueError:
        ko2 = True
    v(6, "rho senza token ignoto viene RIFIUTATO", ko2)

    v(7, "il token e' un modulo per nodo, quindi non e' comune",
      "ignoto" in f.moduli_per_nodo(), str(f.moduli_per_nodo()))

    f.train()
    z = f(1, 40, node_ids=ids)
    z.sum().backward()
    v(8, "il token riceve gradiente: viene appreso",
      f.ignoto.grad is not None and float(f.ignoto.grad.abs().sum()) > 0,
      f"somma dei gradienti {float(f.ignoto.grad.abs().sum()):.4f}")

    print("\n" + "=" * 76)
    print(f"  {sum(E)}/{len(E)} verifiche superate")
    return 0 if all(E) else 1


if __name__ == "__main__":
    raise SystemExit(main())
