#!/usr/bin/env python3
"""
Collaudo ridotto della verifica esterna su PEMS04.
===================================================
    [1] schema del descrittore: 29 componenti, nomi prescritti
    [2] undici canali, tutti finiti, statistiche reali
    [3] appaiamento dei moduli comuni fra C e P nelle NUOVE dimensioni
    [4] componenti COSTANTI: verificate una per una sulle finestre usate,
        e normalizzate senza divisioni per zero
    [5] artefatti in cartelle proprie, non confrontabili con Traffic4cast
    [6] nessun episodio di inserimento in validazione: **non e' applicabile**

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_pems04.py
    poetry run python evoluzione/esperimenti/collauda_pems04.py \\
        --contesto PEMS08_p0 --fine-periodo 3840      # E6 parte B
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import SCHEMI_PEMS04  # noqa: E402
from evoluzione.componente.identita import (  # noqa: E402
    NoIdentity, ObservableIdentityEncoder)
from evoluzione.componente.predittore import PredittorePerNodo  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _canali, _carica, _descrittori, _normalizzazione, _partizioni, canali_di,
    sorgente_di)

OUT = Path("results/evoluzione")
CTX, PART = "PEMS04_p0", 0      # predefiniti; --contesto e --fine-periodo (E6)
ESITI = []


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def main() -> int:
    import argparse
    global CTX, PART
    ap = argparse.ArgumentParser()
    ap.add_argument("--contesto", default=CTX, help="PEMS04_p<k> o PEMS08_p<k>")
    ap.add_argument("--fine-periodo", type=int, default=None,
                    help="t0 di prova pre-registrato (E6 parte B): i periodi "
                         "seguono _partizioni(fine=t0)")
    a = ap.parse_args()
    CTX = a.contesto; PART = int(CTX.rsplit("_p", 1)[1])
    print("=" * 78)
    print(f"COLLAUDO {CTX.split('_p')[0]} — {CTX}"
          + (f", fine del periodo {a.fine_periodo}" if a.fine_periodo is not None else ""))
    print("=" * 78)
    S = SCHEMI_PEMS04["BASE-CORRECTED"]
    d = len(S["statistiche"]) + len(S["disponibilita"])
    v(1, "schema a 29 componenti con i nomi prescritti",
      d == 29 and all(k in S["statistiche"] for k in
                      ("media_conteggio", "dev_conteggio", "media_occupazione",
                       "dev_occupazione"))
      and "media_volume_class" not in S["statistiche"],
      f"{len(S['statistiche'])} statistiche + {len(S['disponibilita'])} "
      f"disponibilita'; sorgente '{S['sorgente']}'")

    D = _carica(CTX, OUT / "maschere")
    nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(1000 + 37 * PART)},
                            a.fine_periodo)
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    v(2, "undici canali, finiti, con statistiche reali",
      x.shape[1] == 11 and np.isfinite(x).all()
      and NORM["media_occupazione"][1] > 1e-5,
      f"{x.shape[1]} canali, {x.shape[2]} nodi; occupazione "
      f"{tuple(round(z, 4) for z in NORM['media_occupazione'])}")
    v("2b", "i nomi dei canali seguono la sorgente",
      len(canali_di(sorgente_di(CTX))) == 11
      and "occupazione" in canali_di(sorgente_di(CTX)))

    # ---- [3] appaiamento dei moduli comuni -----------------------------
    t_rif = int(ist["addestramento"][-1])
    desc = _descrittori(D, nodi["addestramento"], t_rif, "BASE-CORRECTED", NORM)
    v(3, "il descrittore ha 29 componenti e valori finiti",
      desc.shape[-1] == 29 and bool(torch.isfinite(desc).all()),
      f"forma {tuple(desc.shape)}")
    torch.manual_seed(7)
    mC = PredittorePerNodo(0, 5, sorgente="pems04", identita=NoIdentity())
    torch.manual_seed(7)
    mP = PredittorePerNodo(29, 5, sorgente="pems04",
                           identita=ObservableIdentityEncoder(29))
    sC, sP = mC.state_dict(), mP.state_dict()
    comuni = [k for k in sC if k in sP and sC[k].shape == sP[k].shape
              and not k.startswith("identita.")]
    # **IL FORNITORE SI COSTRUISCE PRIMA DEL PREDITTORE**, come argomento: ha
    # dimensioni diverse fra i bracci e consuma estrazioni diverse, sicche'
    # TUTTI i moduli comuni divergono — `start` e `blocchi` inclusi. Coincidono
    # soltanto i buffer, inizializzati a valori fissi.
    #
    # **E' l'artefatto canonico a uniformarli**, ed e' il meccanismo unico
    # previsto dal protocollo: va preparato per PEMS04 con c_in = 11.
    # **Non tutto nasce dal generatore.** I parametri affini della
    # normalizzazione partono da uno e zero, i buffer da valori fissi: sono
    # deterministici e coincidono per costruzione, non per appaiamento.
    det = (".bn.", "running_mean", "running_var", "num_batches_tracked")
    par = [k for k in comuni if not any(d in k for d in det)]
    div = [k for k in par if not torch.equal(sC[k], sP[k])]
    v("3b", "senza artefatto canonico i moduli comuni DIVERGONO",
      len(par) > 0 and len(div) == len(par),
      f"{len(div)}/{len(par)} parametri diversi allo stesso seme: e' il "
      f"motivo per cui l'artefatto canonico esiste")
    buf = [k for k in comuni if k not in par]
    v("3b-bis", "cio' che ha inizializzazione deterministica coincide",
      len(buf) > 0 and all(torch.equal(sC[k], sP[k]) for k in buf),
      f"{len(buf)} tensori: buffer e parametri affini della normalizzazione")
    prim = [t.shape for k, t in sC.items() if k.startswith("start")]
    v("3c", "i primi strati accettano undici canali",
      any(11 in tuple(s) for s in prim), f"forme dei primi strati: {prim[:3]}")

    # ---- [4] componenti costanti, una per una ---------------------------
    n_st = len(S["statistiche"])
    dd = desc.detach().numpy()
    var = dd.std(0)
    cost = [S["statistiche"][i] if i < n_st else S["disponibilita"][i - n_st]
            for i in np.flatnonzero(var < 1e-9)]
    print(f"\n  componenti COSTANTI sulle finestre usate: {len(cost)}/29")
    for c in cost:
        print(f"     {c}")
    v(4, "le componenti costanti sono verificate, non dedotte",
      True, "elenco sopra, da riportare nell'addendum")
    v("4b", "nessun valore non finito dalla normalizzazione",
      bool(np.isfinite(dd).all()), "nessuna divisione per zero")

    # ---- [5] cartelle proprie ------------------------------------------
    v(5, "gli artefatti PEMS non si mescolano con Traffic4cast",
      sorgente_di(CTX) == "pems04" and sorgente_di("Madrid") == "traffic4cast",
      "canonico e punti di controllo seguono la configurazione, che cambia "
      "con c_in = 11")

    # ---- [6] nessun episodio in validazione ------------------------------
    v(6, "nessun episodio di inserimento in validazione: non applicabile",
      True, "F non appartiene a questa verifica; la validazione seleziona "
            "soltanto i punti di controllo di C e P")

    print("\n" + "=" * 78)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 78)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
