#!/usr/bin/env python3
"""
F0: lo stesso E di F, con l'embedding MEDIO e nessun adattamento.
==================================================================
**Separa due spiegazioni** che F–P confonde:

    F0   backbone E congelato, nuovo nodo = media degli embedding iniziali,
         NESSUN aggiornamento: non usa le ventiquattro ore per ottimizzare
    F    lo STESSO E congelato, embedding adattato sulle ventiquattro ore

F0 e' **esattamente il punto di partenza di F**. Backbone, statiche, teste,
normalizzazione e ingressi dinamici restano identici; cambia solo l'embedding
del nuovo nodo.

**Nessun addestramento**: sola inferenza sulle celle gia' usate per F.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_f0.py
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.componente.adattamento import carica_E, copia_da_E  # noqa
from evoluzione.componente.predittore import ORIZZONTI  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _canali, _carica, _lotto, _normalizzazione, _partizioni)
from evoluzione.esperimenti.esegui_inserimento import CALENDARIO  # noqa
from evoluzione.esperimenti.fasi import percorso_E  # noqa: E402
from evoluzione.esperimenti.inserimento import statica_cella, statiche  # noqa: E402
from evoluzione.esperimenti.ricostruisci_predizioni import (  # noqa: E402
    aggregati_per_nodo, wce_da_predizioni)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

D_STAT = 5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--dir-pred", type=Path,
                    default=Path("results/evoluzione/predizioni_f0"))
    a = ap.parse_args()
    a.dir_pred.mkdir(parents=True, exist_ok=True)
    _, dich, semi_t = configurazione(inserimento=True)
    from evoluzione.analisi.pesi import carica as carica_pesi
    print("=" * 80)
    print("F0 — embedding MEDIO, nessun adattamento")
    print("=" * 80)
    righe = []
    for c in ("Madrid", "Londra", "Melbourne"):
        D = _carica(c, a.out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        t0, t1 = CALENDARIO[c]
        fine = D["r"].shape[0] - max(ORIZZONTI)
        per = GR.origini_dopo(ok, t1, fine)
        for p in (0, 1, 2):
            nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
                SEME_PARTIZIONE[p])})
            NORM, nr, nv = _normalizzazione(D, nodi, ist)
            x = _canali(D, nr, nv)
            stat = statiche(D)
            pesi = np.asarray(carica_pesi(a.out / "pesi_griglia", c, p)
                              .vettore(), dtype="float64")
            stat0 = stat
            for i_s, s in enumerate(semi_t):
                stat = statica_cella(stat0, D, nodi, nodi["prova"], t0, int(dich[i_s]))   # E14
                S = torch.as_tensor(stat[nodi["prova"]])
                fE = percorso_E(a.out / "E_inserimento_griglia", c, p, int(s))
                dE, nodi_in, imp_E = carica_E(fE, D_STAT)
                m, forn = copia_da_E(dE, nodi_in, nodi["prova"], D_STAT)
                # **`AdaptedNodeEmbedding` INIZIALIZZA GIA' alla media degli
                # embedding iniziali** (identita.py, righe 247-248): F0 e'
                # quindi lo stato di partenza di F, non una scelta aggiuntiva.
                # Lo si verifica invece di assumerlo.
                with torch.no_grad():
                    medio = forn.iniziali.detach().mean(0, keepdim=True)
                    if not torch.allclose(forn.nuovi.detach(),
                                          medio.expand_as(forn.nuovi)):
                        raise RuntimeError(
                            "l'inizializzazione non e' la media degli "
                            "embedding iniziali: F0 non sarebbe il punto di "
                            "partenza di F")
                m.eval()
                prima = {k: z.clone() for k, z in m.state_dict().items()}
                PB = np.empty((len(per), len(nodi["prova"]), len(ORIZZONTI), 3),
                              dtype="float32")
                YY = np.zeros(PB.shape[:3], dtype="int8")
                MM = np.zeros(PB.shape[:3], dtype=bool)
                t_in = time.time()
                with torch.inference_mode():
                    for i in range(0, len(per), 256):
                        bl = np.asarray(per[i:i + 256], dtype="int64")
                        X, Y, Mk = _lotto(x, D["classe"], bl, nodi["prova"])
                        out = m(X, node_ids=[int(z) for z in nodi["prova"]],
                                static_inputs=S)
                        PB[i:i + len(bl)] = torch.softmax(out, -1).numpy()
                        YY[i:i + len(bl)] = Y.numpy()
                        MM[i:i + len(bl)] = Mk.numpy()
                dt = time.time() - t_in
                assert all(torch.equal(prima[k], z)
                           for k, z in m.state_dict().items()), "stato mosso"
                w, ph = wce_da_predizioni(PB, YY, MM, pesi)
                Ah, Bh, Nh = aggregati_per_nodo(PB, YY, MM, pesi)
                np.savez_compressed(
                    a.dir_pred / f"F0_{c}_p{p}_s{int(dich[i_s])}.npz",
                    prob=PB, y=YY, m=MM, A_per_nodo=Ah, B_per_nodo=Bh,
                    celle_per_nodo=Nh,
                    nodi=np.asarray(nodi["prova"], dtype="int32"),
                    origini=np.asarray(per, dtype="int32"),
                    orizzonti=np.asarray(ORIZZONTI, dtype="int16"),
                    contesto=c, partizione=p, seme=int(dich[i_s]),
                    braccio="F0", t0=t0, t1=t1, impronta_ck=imp_E)
                righe.append({"contesto": c, "partizione": p,
                              "seme": int(dich[i_s]), "wce": w,
                              "per_orizzonte": ph.tolist(),
                              "punto_E": fE.name, "secondi": dt})
                print(f"  {c:11s} p{p} s{int(dich[i_s])}  wCE {w:.6f}  "
                      f"{dt:5.1f}s", flush=True)
    (a.dir_pred / "controllo_f0.json").write_text(json.dumps(
        {"esecuzioni": righe,
         "definizione": ("F0 = stesso E di F, embedding del nuovo nodo posto "
                         "alla MEDIA degli embedding iniziali, nessun "
                         "aggiornamento. Stesse celle di F."),
         "nota": "nessun parametro si muove: verificato a ogni esecuzione"},
        indent=2))
    print(f"\n  {len(righe)} esecuzioni, nessun parametro mosso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
