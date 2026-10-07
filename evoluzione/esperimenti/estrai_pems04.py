#!/usr/bin/env python3
"""
Estrattore PEMS04 -> gli artefatti che `_carica` gia' consuma.
===============================================================
Produce, per CIASCUNA partizione, i due file che il caricatore si aspetta:

    maschere_PEMS04_p<k>.npz   sensor_ids, timestamps, speed_grezza,
                               conteggio_grezzo, occupazione_grezza,
                               maschera_r, maschera_conteggio,
                               maschera_occupazione, riferimento_risolto,
                               sorgente
    bersagli_PEMS04_p<k>.npz   sensor_ids, congestion_emp

**Tre file, uno per partizione**, perche' il riferimento e' stimato sui SOLI
nodi iniziali di quella partizione e il caricatore lo applica a tutti i nodi.
Un unico file costringerebbe a un riferimento comune alle tre partizioni,
contro la specifica.

SCELTE, tutte dichiarate nell'addendum:

    aggregazione   5 -> 15 minuti: flusso SOMMA, occupazione e velocita' MEDIA
    calendario     1 gennaio - 28 febbraio 2018, ora locale California assunta
    riferimento    percentile 95 delle velocita' AGGREGATE dei soli nodi
                   iniziali, nel solo periodo di addestramento, per partizione
    classi         rapporto >= 0,8 -> 1, 0,5-0,8 -> 2, < 0,5 -> 3
    flusso         **CONTINUO**, aggregato e standardizzato dal protocollo.
                   I terzili sono una proposta SCARTATA prima del test.
    maschere       derivate dai CONTROLLI DI VALIDITA' dei valori distribuiti,
                   non imposte a uno. Se tutti passano, si registrano come
                   sempre vere, e significano «valore numericamente
                   disponibile nel rilascio preprocessato», non «misura grezza
                   osservata dal sensore».

**Lo schema di PEMS04 ha TRE grandezze dinamiche** — velocita' relativa, flusso
continuo, occupazione — e **tre maschere**: undici ingressi con il calendario,
contro i nove di Traffic4cast. Punti di controllo e artefatti canonici vivono
quindi in cartelle proprie e non sono confrontabili.

**PEMS08 (E6, parte B)**: stesso estrattore, stesse scelte, parametrizzato su
nome, inizio del calendario e **fine del periodo** (t0 di prova pre-registrato):
con `--fine-periodo t0` il periodo di addestramento e' [11, int(t0·0,70/0,85)),
le quote del principale su [0, t0) come `_partizioni(fine=t0)`, ed e' su quello
che si stima il riferimento. Il campo `sorgente` resta "pems04": e' il nome
dello SCHEMA (tre grandezze, undici ingressi) che `_carica` consuma, non del
dataset.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/estrai_pems04.py \\
        --file data_collection/pems04/pems04.npz
    poetry run python evoluzione/esperimenti/estrai_pems04.py \\
        --file data_collection/pems08/pems08.npz --nome PEMS08 \\
        --inizio 2016-07-01 --fine-periodo 3840 --dati data_collection/pems08
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

AGG = 3
PERC = 95
SOGLIE = (0.8, 0.5)
INIZIO = "2018-01-01"
SEMI_PARTIZIONE = {0: 1000, 1: 1037, 2: 1074}      # 1000 + 37 p (semi.SEME_PARTIZIONE)
ORIZZ_MAX = 8


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, required=True)
    ap.add_argument("--out", type=Path,
                    default=Path("results/evoluzione/maschere"))
    ap.add_argument("--dati", type=Path, default=Path("data_collection/pems04"))
    ap.add_argument("--nome", default="PEMS04", help="PEMS04 o PEMS08")
    ap.add_argument("--inizio", default=INIZIO)
    ap.add_argument("--fine-periodo", type=int, default=None,
                    help="t0 di prova pre-registrato: addestramento = "
                         "[11, int(t0*.70/.85)) (E6 parte B)")
    ap.add_argument("--partizioni", type=int, default=3,
                    help="numero di partizioni (E6 parte B: 6); seme 1000 + 37 p")
    a = ap.parse_args()
    semi_part = {p: 1000 + 37 * p for p in range(a.partizioni)}
    assert all(semi_part[p] == SEMI_PARTIZIONE[p] for p in SEMI_PARTIZIONE if p in semi_part)
    nome, pref = a.nome, a.nome.lower()
    X = np.load(a.file)["data"]
    T, N, _ = X.shape
    Tq = (T // AGG) * AGG
    fl = X[:Tq, :, 0].reshape(-1, AGG, N).sum(1)
    ve = X[:Tq, :, 2].reshape(-1, AGG, N).mean(1)
    Tg = fl.shape[0]
    ts = pd.date_range(a.inizio, periods=Tg, freq="15min")
    sid = np.array([f"{pref}_{i:04d}" for i in range(N)])
    oc = X[:Tq, :, 1].reshape(-1, AGG, N).mean(1)
    e = Tg - ORIZZ_MAX
    # fine del periodo di ADDESTRAMENTO: 70 % della serie (campagna PEMS04) o
    # le quote del principale su [0, t0) (E6 parte B), come _partizioni(fine=t0)
    a_va = int(e * .70) if a.fine_periodo is None else int(a.fine_periodo * .70 / .85)
    # LE MASCHERE dai controlli di validita' dei valori DISTRIBUITI
    m_ve = np.isfinite(ve) & (ve > 0)
    m_fl = np.isfinite(fl) & (fl >= 0)
    m_oc = np.isfinite(oc) & (oc >= 0) & (oc <= 1)
    print(f"  maschere dai controlli: velocita' {m_ve.mean():.4%} vere, "
          f"flusso {m_fl.mean():.4%}, occupazione {m_oc.mean():.4%}")
    a.out.mkdir(parents=True, exist_ok=True)
    a.dati.mkdir(parents=True, exist_ok=True)
    rapporto = {}
    print("=" * 76)
    print(f"ESTRAZIONE {nome} — {Tg} istanti a 15 minuti, {N} nodi")
    print(f"  calendario {ts[0]} -> {ts[-1]}; addestramento [11, {a_va})"
          + (f" da --fine-periodo {a.fine_periodo}" if a.fine_periodo is not None else ""))
    print("=" * 76)
    for p, seme in semi_part.items():
        perm = np.random.default_rng(seme).permutation(N)
        iniziali = perm[:int(N * .70)]
        # IL RIFERIMENTO: soli nodi iniziali, solo addestramento, dopo
        # l'aggregazione, CONGELATO prima di validazione e prova
        rif_val = float(np.percentile(ve[11:a_va][:, iniziali], PERC))
        rif = np.full(N, rif_val)
        rap = ve / rif_val
        cl = np.where(rap >= SOGLIE[0], 1, np.where(rap >= SOGLIE[1], 2, 3))
        np.savez_compressed(
            a.out / f"maschere_{nome}_p{p}.npz", sensor_ids=sid,
            timestamps=ts.values, speed_grezza=ve.astype("float32"),
            conteggio_grezzo=fl.astype("float32"),
            occupazione_grezza=oc.astype("float32"),
            maschera_r=m_ve, maschera_conteggio=m_fl,
            maschera_occupazione=m_oc, riferimento_risolto=rif,
            sorgente="pems04")
        np.savez_compressed(a.dati / f"bersagli_{nome}_p{p}.npz",
                            sensor_ids=sid, congestion_emp=cl.astype("int64"),
                            timestamps=ts.values)
        d = {int(k): float(np.mean(cl == k)) for k in (1, 2, 3)}
        d_tr = {int(k): float(np.mean(cl[11:a_va] == k)) for k in (1, 2, 3)}
        d_pr = ({int(k): float(np.mean(cl[a.fine_periodo:e] == k)) for k in (1, 2, 3)}
                if a.fine_periodo is not None else None)
        rapporto[f"p{p}"] = {"riferimento_mph": rif_val,
                             "nodi_iniziali": len(iniziali), "classi": d,
                             "classi_addestramento": d_tr, "classi_prova": d_pr,
                             "maschere_sempre_vere": {
                                 "velocita": bool(m_ve.all()),
                                 "flusso": bool(m_fl.all()),
                                 "occupazione": bool(m_oc.all())}}
        print(f"  p{p}  riferimento {rif_val:6.2f} mph su {len(iniziali)} nodi "
              f"iniziali | classi {d[1]:.1%} / {d[2]:.1%} / {d[3]:.1%}")
    Path(f"results/evoluzione/estrazione_{pref}.json").write_text(
        json.dumps({"scelte": {"aggregazione": "flusso somma, resto media",
                               "percentile": PERC, "soglie": SOGLIE,
                               "inizio": a.inizio, "nome": nome,
                               "fine_periodo": a.fine_periodo,
                               "addestramento": [11, a_va]},
                    "partizioni": rapporto,
                    "terzili": "proposta SCARTATA prima del test: si usa il "
                               "flusso continuo",
                    "limite": ("il rilascio e' gia' imputato: le maschere "
                               "derivano dai controlli di validita' sui valori "
                               "DISTRIBUITI e significano disponibilita' "
                               "numerica nel rilascio, non misura grezza "
                               "osservata")},
                   indent=2))
    print(f"\n  le maschere derivano dai controlli di validita': dove tutti")
    print(f"  passano significano DISPONIBILITA' NUMERICA NEL RILASCIO, non")
    print(f"  misura grezza osservata dal sensore")
    print(f"\n  registrare in CTX: {nome}_p<k> -> "
          f"(bersagli_{nome}_p<k>.npz, '{nome}_p<k>')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
