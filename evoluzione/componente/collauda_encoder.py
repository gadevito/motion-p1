#!/usr/bin/env python3
"""
Collaudo dell'encoder e del modello completo — audit B e D.
============================================================
Nessun addestramento.

    1. audit B — inventario dei parametri dell'INTERO modello: aggiungere
       sensori non deve aumentare i parametri appresi;
    2. audit D — stato completo invariato prima e dopo inserimento e inferenza,
       buffer compresi;
    3. equivarianza alla permutazione dei nodi;
    4. indipendenza dal lotto nell'encoder;
    5. trattamento dei non stimabili e assenza di valori non finiti.

Le verifiche 3, 4 e 5 si eseguono anche in assenza di torch, sul riferimento in
numpy. Le verifiche 1 e 2 richiedono torch e vengono dichiarate saltate se non
disponibile: NON si contano come superate.

Uso (dalla radice OR3/):

    poetry run python evoluzione/componente/collauda_encoder.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.encoder import (  # noqa: E402
    NASCOSTE, NEUTRO, USCITA, EncoderRiferimento, n_parametri,
    prepara_ingresso)
from evoluzione.componente.estrattore import SCHEMI  # noqa: E402

ESITI = []
SALTATE = []


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def salta(n, titolo, perche):
    SALTATE.append(n)
    print(f"  [{n}] SALTATA  {titolo}")
    print(f"        {perche}")


def main() -> int:
    print("dimensioni d'ingresso e parametri, per variante")
    print(f"  {'variante':16s} {'ingresso':>9} {'W1':>8} {'b1':>5} {'W2':>7} "
          f"{'b2':>4} {'totale':>8}")
    D = {}
    for s, d in SCHEMI.items():
        di = len(d["statistiche"]) + len(d["disponibilita"])
        D[s] = di
        p = n_parametri(di)
        print(f"  {s:16s} {di:9d} {p['W1']:8d} {p['b1']:5d} {p['W2']:7d} "
              f"{p['b2']:4d} {p['totale']:8d}")
    print(f"\n  struttura nascosta {NASCOSTE} e uscita {USCITA} uguali fra le "
          f"varianti; cambia la sola dimensione d'ingresso.")

    # ------------------------------------------------------------- [1] -----
    print("\n[1] audit B — parametri specifici per sensore")
    try:
        import torch
        import torch.nn as nn
        from evoluzione.componente.encoder import (costruisci_torch,
                                                   inventario_per_nodo)

        class Modello(nn.Module):
            """Modello minimo con encoder condiviso e ramo statico separato."""

            def __init__(self, d_desc, d_stat, d_din, uscita=3):
                super().__init__()
                self.enc = costruisci_torch(d_desc)
                self.stat = nn.Linear(d_stat, 8)
                self.testa = nn.Linear(USCITA + 8 + d_din, uscita)

            def forward(self, desc, stat, din):
                z = self.enc(desc)
                a = torch.relu(self.stat(stat))
                return self.testa(torch.cat([z, a, din], -1))

        m = Modello(D["EXTENDED"], 5, 4)
        tot = sum(p.numel() for p in m.parameters())
        inv10 = inventario_per_nodo(m, 10)
        inv50 = inventario_per_nodo(m, 50)
        verifica(1, "nessun parametro indicizzato sul nodo",
                 not inv10 and not inv50,
                 f"{tot:,} parametri totali; inventario vuoto per 10 e 50 nodi")
        # il conteggio non cambia col numero di sensori elaborati
        for n in (10, 50, 500):
            x = (torch.randn(n, D["EXTENDED"]), torch.randn(n, 5), torch.randn(n, 4))
            m(*x)
        verifica("1b", "aggiungere sensori non aumenta i parametri appresi",
                 sum(p.numel() for p in m.parameters()) == tot,
                 f"{tot:,} prima e dopo inferenza su 10, 50 e 500 sensori")
        verifica("1c", "l'encoder ha i parametri attesi",
                 sum(p.numel() for p in m.enc.parameters())
                 == n_parametri(D["EXTENDED"])["totale"])

        # ---------------------------------------------------------- [2] ----
        print("\n[2] audit D — stato invariato da inserimento e inferenza")
        import hashlib

        def impronta(mod):
            h = hashlib.sha256()
            for k, v in sorted(mod.state_dict().items()):
                h.update(k.encode())
                h.update(v.detach().cpu().numpy().tobytes())
            return h.hexdigest()

        m.eval()
        pre = impronta(m)
        with torch.no_grad():
            for n in (10, 37, 200):      # espansioni successive simulate
                m(torch.randn(n, D["EXTENDED"]), torch.randn(n, 5),
                  torch.randn(n, 4))
        verifica(2, "pesi, buffer e statistiche invariati dopo l'inferenza",
                 impronta(m) == pre, f"impronta {pre[:16]}")
        buffer = list(m.buffers())
        verifica("2b", "nessun buffer con statistiche mobili",
                 len(buffer) == 0,
                 "nessun dropout ne' normalizzazione: nulla da aggiornare in "
                 "inferenza")
    except ImportError:
        salta(1, "audit B — inventario dei parametri", "torch non disponibile")
        salta(2, "audit D — stato invariato", "torch non disponibile")

    # ------------------------------------------------------------- [3] -----
    print("\n[3] equivarianza alla permutazione dei nodi")
    E = EncoderRiferimento(D["EXTENDED"], seme=1)
    rng = np.random.default_rng(0)
    U = rng.normal(0, 1, (40, D["EXTENDED"]))
    perm = rng.permutation(40)
    verifica(3, "permutando gli ingressi le uscite seguono la permutazione",
             np.allclose(E(U)[perm], E(U[perm]), atol=1e-12),
             "l'encoder agisce sul singolo sensore: la permutazione commuta")
    print("        NOTA: questo verifica il solo encoder. L'equivarianza del")
    print("        MODELLO con grafo richiede di permutare coerentemente anche")
    print("        l'adiacenza, e va verificata sul modello completo.")

    # ------------------------------------------------------------- [4] -----
    print("\n[4] indipendenza dal lotto")
    uno = np.vstack([E(U[i:i + 1]) for i in range(len(U))])
    verifica(4, "uno alla volta contro l'intero lotto",
             np.allclose(uno, E(U), atol=1e-12))
    misti = np.vstack([E(U[[i] + list(rng.choice(40, 7))])[0:1]
                       for i in range(len(U))])
    verifica("4b", "il vettore non dipende dagli altri sensori del lotto",
             np.allclose(misti, E(U), atol=1e-12),
             "ogni sensore confrontato con lotti casuali diversi")

    # ------------------------------------------------------------- [5] -----
    print("\n[5] non stimabili e valori non finiti")
    nomi = SCHEMI["EXTENDED"]["statistiche"]
    s = rng.normal(0, 1, len(nomi))
    q = rng.random(len(SCHEMI["EXTENDED"]["disponibilita"]))
    s[3] = np.nan
    u, sost = prepara_ingresso(s, q, non_stimabili=[nomi[3]], nomi=nomi)
    verifica(5, "il non stimabile e' sostituito con il valore neutro",
             u[3] == NEUTRO and nomi[3] in sost and np.isfinite(u).all())
    s2 = s.copy(); s2[7] = np.inf
    u2, sost2 = prepara_ingresso(s2, q, non_stimabili=[nomi[3]], nomi=nomi)
    verifica("5b", "un non finito NON dichiarato viene sostituito e segnalato",
             np.isfinite(u2).all()
             and any("NON DICHIARATO" in x for x in sost2),
             f"segnalati: {[x for x in sost2 if 'NON' in x]}")
    try:
        prepara_ingresso(s, np.array([np.nan] * len(q)), nomi=nomi)
        rifiuta = False
    except ValueError:
        rifiuta = True
    verifica("5c", "una disponibilita' non finita e' rifiutata", rifiuta,
             "e' un difetto, non un dato mancante")

    zero = np.zeros(D["EXTENDED"])
    id_pre = E.identita_predefinita
    verifica("5d", "storia interamente indisponibile: identita' predefinita "
             "CONDIVISA",
             np.allclose(E(zero[None, :])[0], id_pre, atol=1e-12)
             and np.linalg.norm(id_pre) > 0,
             f"norma {np.linalg.norm(id_pre):.4f}: non nulla, ma identica per "
             f"ogni sensore in quello stato")

    print("\n" + "=" * 70)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate"
          + (f", {len(SALTATE)} saltate" if SALTATE else ""))
    if SALTATE:
        print(f"  saltate: {SALTATE} — NON contano come superate")
    print("=" * 70)
    return 0 if all(ESITI) and not SALTATE else 1


if __name__ == "__main__":
    raise SystemExit(main())
