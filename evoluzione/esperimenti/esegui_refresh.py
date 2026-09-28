#!/usr/bin/env python3
"""
P-refresh: stessi pesi, descrittore aggiornato a ogni origine.
===============================================================
**Nessun addestramento.** Si riusano i 108 punti di controllo di P della fase 3,
senza selezione in base ai risultati.

    P-frozen   descrittore delle prime 24 ore da t0, poi invariato
    P-refresh  descrittore delle ultime 24 ore disponibili, a ogni origine

La finestra di P-refresh e' (t - 24h, t] intersecata con (t0, t], sulla griglia
REALE.

REGOLA DICHIARATA PRIMA DI ESEGUIRE. Dove la finestra di ventiquattro ore
**attraversa un salto**, non esiste una finestra reale completa: comprimere i
giorni assenti e' escluso. In quelle origini **P-refresh usa il descrittore
congelato**, e il loro numero si riporta. Il confronto primario resta sulle
stesse chiavi; la copertura si riporta e, come lettura dichiarata, si riporta
anche il confronto sulle sole origini con finestra completa.

**Non si aggiornano pesi, buffer o parametri di normalizzazione.**

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_refresh.py
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
from evoluzione.componente.predittore import ORIZZONTI  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _canali, _carica, _descrittori, _lotto, _normalizzazione, _partizioni)
from evoluzione.esperimenti.esegui_inserimento import CALENDARIO  # noqa: E402
from evoluzione.esperimenti.inserimento import _modello_da_ck, statiche  # noqa
from evoluzione.esperimenti.ricostruisci_predizioni import (  # noqa: E402
    aggregati_per_nodo, impronta, wce_da_predizioni)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

DIR_C = Path("results/evoluzione/inserimento_griglia")
L = GR.L_DESCRITTORE
# LA VERIFICA ESTERNA: tre contesti, una partizione ciascuno, punti di
# controllo in cartella propria. Il calendario del test non richiede la ricerca
# del primo t0 ammissibile: **la griglia di PEMS04 e' regolare**, quindi il
# primo istante utile del periodo di prova soddisfa gia' la regola. Lo si
# verifica comunque, invece di assumerlo.
PEMS = {"contesti": ("PEMS04_p0", "PEMS04_p1", "PEMS04_p2"),
        "dir_ck": Path("results/evoluzione/pems04"),
        "dir_pesi": "pesi_pems04"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pems04", action="store_true",
                    help="la verifica esterna: tre contesti, punti in pems04")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--dir-pred", type=Path,
                    default=Path("results/evoluzione/predizioni_refresh"))
    a = ap.parse_args()
    a.dir_pred.mkdir(parents=True, exist_ok=True)
    _, dich, _ = configurazione(inserimento=True)
    from evoluzione.analisi.pesi import carica as carica_pesi
    print("=" * 84)
    print("P-REFRESH — stessi pesi, descrittore aggiornato a ogni origine")
    print("=" * 84)
    righe, guai = [], []
    contesti = PEMS["contesti"] if a.pems04 else ("Madrid", "Londra",
                                                  "Melbourne")
    for i_c, c in enumerate(contesti):
        D = _carica(c, a.out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        if a.pems04:
            # il periodo di prova comincia al 85% delle origini: il primo t0
            # con ventiquattro ore complete e' il primo istante utile, e la
            # regola approvata deve confermarlo
            e_ = D["r"].shape[0] - GR.MAX_ORIZZ
            t0 = GR.primo_t0(D["ts"], ok, int(e_ * .85), e_,
                             giornata_dopo=False)
            if t0 is None:
                raise RuntimeError(f"{c}: nessun t0 ammissibile nella prova")
            t1 = t0 + L
            print(f"\n{c}: t0 = {t0} ({D['ts'][t0]}), t1 = {t1}")
        else:
            t0, t1 = CALENDARIO[c]
        fine = D["r"].shape[0] - max(ORIZZONTI)
        per = GR.origini_dopo(ok, t1, fine)
        # LA COPERTURA, decisa dalla griglia e non dai risultati
        completa = np.array([GR.contigue(ok, t - L + 1, t) for t in per])
        # nessuna finestra puo' precedere t0: t >= t1 + 1 e t1 = t0 + 96
        assert min(t - L + 1 for t in per) > t0
        print(f"\n{c}: {len(per)} origini, finestra completa in "
              f"{int(completa.sum())} ({completa.mean():.1%})")
        for p in ([i_c] if a.pems04 else (0, 1, 2)):
            nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
                SEME_PARTIZIONE[p])})
            NORM, nr, nv = _normalizzazione(D, nodi, ist)
            x = _canali(D, nr, nv)
            stat = statiche(D)
            pesi = np.asarray(carica_pesi(
                a.out / (PEMS["dir_pesi"] if a.pems04 else "pesi_griglia"),
                c, p)
                              .vettore(), dtype="float64")
            S = torch.as_tensor(stat[nodi["prova"]])
            # i descrittori, UNO PER ORIGINE, calcolati una volta per partizione
            t_d = time.time()
            desc_frozen = _descrittori(D, nodi["prova"], int(t1),
                                       "BASE-CORRECTED", NORM)
            desc = {}
            for i, t in enumerate(per):
                desc[t] = (_descrittori(D, nodi["prova"], int(t),
                                        "BASE-CORRECTED", NORM)
                           if completa[i] else desc_frozen)
            costo_desc = time.time() - t_d
            for s in dich:
                ck = (PEMS["dir_ck"] / f"ck_P_{c}_s{int(s)}.pt" if a.pems04
                      else DIR_C / f"ck_P_{c}_p{p}_s{int(s)}.pt")
                if not ck.exists():
                    guai.append(f"{ck.name}: assente"); continue
                m, dck = _modello_da_ck(ck, D, nodi, None)
                prima = {k: z.clone() for k, z in m.state_dict().items()}
                PB = np.empty((len(per), len(nodi["prova"]), len(ORIZZONTI), 3),
                              dtype="float32")
                YY = np.zeros(PB.shape[:3], dtype="int8")
                MM = np.zeros(PB.shape[:3], dtype=bool)
                t_in = time.time()
                with torch.inference_mode():
                    for i, t in enumerate(per):
                        X, Y, Mk = _lotto(x, D["classe"], [int(t)],
                                          nodi["prova"])
                        out = m(X, node_ids=[int(z) for z in nodi["prova"]],
                                descriptor=desc[t], static_inputs=S)
                        PB[i] = torch.softmax(out, -1).numpy()[0]
                        YY[i] = Y.numpy()[0]; MM[i] = Mk.numpy()[0]
                dt = time.time() - t_in
                if any(not torch.equal(prima[k], z)
                       for k, z in m.state_dict().items()):
                    guai.append(f"{ck.name}: stato cambiato in inferenza")
                w, ph = wce_da_predizioni(PB, YY, MM, pesi)
                w_sub, _ = wce_da_predizioni(PB[completa], YY[completa],
                                             MM[completa], pesi)
                Ah, Bh, Nh = aggregati_per_nodo(PB, YY, MM, pesi)
                np.savez_compressed(
                    a.dir_pred / f"Prefresh_{c}_p{p}_s{int(s)}.npz",
                    prob=PB, y=YY, m=MM, A_per_nodo=Ah, B_per_nodo=Bh,
                    celle_per_nodo=Nh, finestra_completa=completa,
                    nodi=np.asarray(nodi["prova"], dtype="int32"),
                    origini=np.asarray(per, dtype="int32"),
                    orizzonti=np.asarray(ORIZZONTI, dtype="int16"),
                    contesto=c, partizione=p, seme=int(s), braccio="P-refresh",
                    t0=t0, t1=t1, impronta_ck=impronta(ck))
                righe.append({"contesto": c, "partizione": p, "seme": int(s),
                              "wce": w, "wce_finestre_complete": w_sub,
                              "per_orizzonte": ph.tolist(),
                              "origini": len(per),
                              "origini_finestra_completa": int(completa.sum()),
                              "secondi_inferenza": dt,
                              "secondi_descrittori_partizione": costo_desc})
                print(f"  {c:11s} p{p} s{int(s)}  wCE {w:.6f}  "
                      f"(complete {w_sub:.6f})  {dt:5.1f}s", flush=True)
    (a.dir_pred / "controllo_refresh.json").write_text(json.dumps(
        {"esecuzioni": righe, "anomalie": guai,
         "regola_finestre_incomplete": (
             "dove la finestra di 24 ore attraversa un salto, P-refresh usa il "
             "descrittore congelato: comprimere i giorni assenti e' escluso. "
             "Dichiarata PRIMA dell'esecuzione."),
         "costo": "il costo dei descrittori e' per partizione, non per "
                  "esecuzione: dipende da origini e nodi, non dai pesi"},
        indent=2))
    print(f"\n{'=' * 84}\n  {len(righe)} esecuzioni, {len(guai)} anomalie")
    return 0 if not guai else 1


if __name__ == "__main__":
    raise SystemExit(main())
