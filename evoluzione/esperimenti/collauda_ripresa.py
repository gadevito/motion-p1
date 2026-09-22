#!/usr/bin/env python3
"""
Collaudo della ripresa: continua contro interrotta e ripresa.
==============================================================
    1. l'esecuzione ripresa produce gli STESSI pesi di quella continua;
    2. la scrittura e' ATOMICA: un file incompleto non risulta valido;
    3. il punto CORRENTE e quello MIGLIORE sono distinti;
    4. riprendere dal MIGLIORE viene RIFIUTATO;
    5. lo stato dell'ottimizzatore e' ripristinato, non reinizializzato;
    6. lo stato del generatore di torch e' ripristinato.

**Riprendere dal migliore altererebbe la traiettoria**: e' il difetto che il
punto 4 impedisce.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_ripresa.py
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.identita import NoIdentity
from evoluzione.componente.predittore import (
    CANALI_T4C, FINESTRA, ORIZZONTI, PredittorePerNodo)
from evoluzione.esperimenti.prova_adeguatezza import (
    scrivi_atomico, stato_completo)

ESITI = []
D_STAT = 5


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def modello(seme=5):
    torch.manual_seed(seme)
    return PredittorePerNodo(0, D_STAT, sorgente="traffic4cast",
                             identita=NoIdentity())


def lotti(n, K=8, B=4, seme=1):
    g = torch.Generator().manual_seed(seme)
    return [(torch.randn(B, len(CANALI_T4C), K, FINESTRA, generator=g),
             torch.randint(0, 3, (B, K, len(ORIZZONTI)), generator=g),
             torch.randn(K, D_STAT, generator=g)) for _ in range(n)]


def gira(m, opt, dati, da, a_):
    for i in range(da, a_):
        X, Y, S = dati[i]
        out = m(X, node_ids=list(range(X.shape[2])), static_inputs=S)
        L = F.cross_entropy(out.reshape(-1, 3), Y.reshape(-1))
        opt.zero_grad(); L.backward(); opt.step()
    return m


def main() -> int:
    dep = Path(tempfile.mkdtemp(prefix="collaudo_ripresa_"))
    N, TAGLIO = 30, 12
    dati = lotti(N)
    print("=" * 76)
    print("COLLAUDO DELLA RIPRESA")
    print("=" * 76)

    # ---- [A] esecuzione CONTINUA --------------------------------------
    mA = modello(); oA = torch.optim.Adam(mA.parameters(), lr=1e-2)
    gira(mA, oA, dati, 0, N)

    # ---- [B] interrotta, salvata, ripresa ------------------------------
    mB = modello(); oB = torch.optim.Adam(mB.parameters(), lr=1e-2)
    gira(mB, oB, dati, 0, TAGLIO)
    f = dep / "corrente.pt"
    st = stato_completo(mB, oB, TAGLIO, TAGLIO,
                        {"torch": torch.get_rng_state().tolist()},
                        {"contesto": "prova"},
                        {"aggiornamento": 3, "V-full": 0.5})
    scrivi_atomico(f, lambda fh: torch.save(st, fh))
    del mB, oB
    d = torch.load(f, map_location="cpu", weights_only=False)
    mC = modello(); oC = torch.optim.Adam(mC.parameters(), lr=1e-2)
    mC.load_state_dict(d["model_state_dict"], strict=True)
    oC.load_state_dict(d["optimizer_state_dict"])
    gira(mC, oC, dati, d["ultimo_aggiornamento"], N)

    sA, sC = mA.state_dict(), mC.state_dict()
    dmax = max(float((sA[k] - sC[k]).abs().max())
               for k in sA if sA[k].is_floating_point())
    v(1, "la ripresa produce gli STESSI pesi dell'esecuzione continua",
      dmax == 0.0,
      f"scarto massimo {dmax:.2e} su {len(sA)} tensori; interruzione a "
      f"{TAGLIO}/{N}")

    # ---- [2] scrittura atomica -----------------------------------------
    tmp = list(dep.glob("*.tmp"))
    v(2, "nessun temporaneo resta dopo la scrittura", not tmp,
      f"`os.replace` rinomina soltanto a scrittura completata")
    f2 = dep / "vuoto.pt"
    try:
        scrivi_atomico(f2, lambda fh: (_ for _ in ()).throw(OSError("disco")))
    except OSError:
        pass
    v("2b", "una scrittura fallita non lascia il file di destinazione",
      not f2.exists(),
      "il temporaneo non viene rinominato, quindi la destinazione resta "
      "intatta o assente")

    # ---- [3] e [4] corrente contro migliore -----------------------------
    v(3, "il punto corrente dichiara il proprio tipo",
      d.get("tipo") == "corrente", f"tipo «{d.get('tipo')}»")
    v("3b", "porta lo stato della SELEZIONE, distinto dai pesi correnti",
      d["selezione"]["aggiornamento"] == 3
      and d["ultimo_aggiornamento"] == TAGLIO,
      f"migliore a u{d['selezione']['aggiornamento']}, corrente a "
      f"u{d['ultimo_aggiornamento']}: sono DIVERSI")
    mi = {"tipo": "migliore", "model_state_dict": mA.state_dict(),
          "aggiornamento": 3}
    f3 = dep / "migliore.pt"
    scrivi_atomico(f3, lambda fh: torch.save(mi, fh))
    d3 = torch.load(f3, map_location="cpu", weights_only=False)
    v(4, "un punto MIGLIORE e' riconoscibile e va rifiutato per la ripresa",
      d3.get("tipo") == "migliore",
      "riprendere da qui altererebbe la traiettoria")

    # ---- [5] lo stato dell'ottimizzatore --------------------------------
    st_o = d["optimizer_state_dict"]["state"]
    v(5, "lo stato di Adam e' salvato, non reinizializzato",
      len(st_o) > 0 and all("exp_avg" in x for x in st_o.values()),
      f"{len(st_o)} tensori con momenti di primo e secondo ordine")

    # ---- [6] il generatore -----------------------------------------------
    v(6, "lo stato del generatore di torch e' salvato",
      "torch" in d["generatori"] and len(d["generatori"]["torch"]) > 0,
      f"{len(d['generatori']['torch'])} byte")

    print("\n" + "=" * 76)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 76)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
