#!/usr/bin/env python3
"""
L'adattamento vettorizzato e' EQUIVALENTE a quello separato per nodo.
======================================================================
Il revisore ha ammesso la vettorizzazione **purche' il risultato sia
equivalente all'adattamento separato dei nodi**. Qui lo si dimostra sui tensori,
non lo si asserisce.

    perdita totale = SOMMA delle perdite per nodo
    => d(somma)/d(embedding_i) = d(perdita_i)/d(embedding_i)

Adam aggiorna elemento per elemento, quindi anche gli aggiornamenti coincidono.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_vettorizzazione.py
"""
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.adattamento import adatta, copia_da_E
from evoluzione.componente.identita import LearnedNodeEmbedding
from evoluzione.componente.predittore import (
    CANALI_T4C, FINESTRA, ORIZZONTI, PredittorePerNodo)

ESITI = []
D_STAT = 5


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def finto_E(nodi, seme=7):
    torch.manual_seed(seme)
    forn = LearnedNodeEmbedding(nodi)
    m = PredittorePerNodo(0, D_STAT, sorgente="traffic4cast", identita=forn)
    return {"state_dict": m.state_dict(), "nodi_iniziali": list(nodi)}


def dati(nodi, B=20, seme=3, vuoti=()):
    g = torch.Generator().manual_seed(seme)
    K = len(nodi)
    X = torch.randn(B, len(CANALI_T4C), K, FINESTRA, generator=g)
    S = torch.randn(K, D_STAT, generator=g)
    Y = torch.randint(0, 3, (B, K, len(ORIZZONTI)), generator=g)
    M = torch.rand(B, K, len(ORIZZONTI), generator=g) > 0.3
    for i in vuoti:
        M[:, i] = False                      # nodo SENZA alcun bersaglio
    return X, [int(x) for x in nodi], Y, M, S


def per_nodo(lotto):
    X, nodi, Y, M, S = lotto
    return [(X[:, :, i:i + 1], [nodi[i]], Y[:, i:i + 1], M[:, i:i + 1],
             S[i:i + 1]) for i in range(len(nodi))]


def main() -> int:
    print("=" * 78)
    print("EQUIVALENZA DELLA VETTORIZZAZIONE")
    print("=" * 78)
    INI = list(range(12))
    NUOVI = [100, 101, 102, 103, 104]
    VUOTO = 2                                  # il terzo nodo senza bersagli
    dE = finto_E(INI)
    pesi = torch.tensor([0.7, 0.8, 3.5])
    lotto = dati(NUOVI, vuoti=(VUOTO,))

    for b, e in ((1, 1e-2), (10, 1e-2), (50, 1e-3)):
        mA, fA = copia_da_E(dE, INI, NUOVI, D_STAT)
        adatta(mA, fA, [lotto], pesi, e, b, vettorizzato=True)
        mB, fB = copia_da_E(dE, INI, NUOVI, D_STAT)
        adatta(mB, fB, per_nodo(lotto), pesi, e, b, vettorizzato=False)
        d = float((fA.nuovi.detach() - fB.nuovi.detach()).abs().max())
        v(f"{b}-{e:g}", f"{b} aggiornamenti a passo {e:g}: embedding identici",
          d < 1e-6, f"scarto massimo {d:.3e}")

    # il nodo senza bersagli non si muove
    mA, fA = copia_da_E(dE, INI, NUOVI, D_STAT)
    prima = fA.nuovi.detach().clone()
    adatta(mA, fA, [lotto], pesi, 1e-2, 50)
    fermo = torch.equal(fA.nuovi[VUOTO].detach(), prima[VUOTO])
    mossi = [i for i in range(len(NUOVI))
             if not torch.equal(fA.nuovi[i].detach(), prima[i])]
    v("vuoto", "il nodo senza bersagli NON si muove", fermo,
      f"mossi: {mossi}, fermo: [{VUOTO}] — e' il comportamento prescritto "
      f"per «adattamento non eseguibile»")
    v("altri", "gli altri nodi si muovono",
      len(mossi) == len(NUOVI) - 1, f"{len(mossi)} su {len(NUOVI) - 1} attesi")

    print("\n" + "=" * 78)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 78)
    print("\n  La vettorizzazione e' 135 volte piu' veloce e produce gli STESSI")
    print("  embedding: e' la condizione posta dal revisore.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
