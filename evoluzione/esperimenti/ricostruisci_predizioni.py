#!/usr/bin/env python3
"""
Ricostruzione delle predizioni della fase 3, senza nuovi addestramenti.
=======================================================================
Le predizioni per cella **non erano state salvate**: e' una lacuna rispetto al
protocollo, registrata come tale. Si ricostruiscono dai punti di controllo.

> **Non e' verificabile l'identita' con le predizioni originarie.** Il controllo
> possibile e' un altro: le metriche RICALCOLATE dalle predizioni ricostruite
> devono riprodurre gli aggregati conservati, per **ciascuna esecuzione e
> ciascun orizzonte**, non solo sulle medie cittadine.

TOLLERANZA, dichiarata PRIMA di eseguire: **1e-6 relativo** sulla wCE di ogni
esecuzione e di ogni orizzonte. Uno scarto maggiore ferma il confronto; la
tolleranza non si alza dopo averlo visto.

Si scrive in una cartella DISTINTA: gli aggregati congelati non si toccano.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/ricostruisci_predizioni.py --braccio P
    poetry run python evoluzione/esperimenti/ricostruisci_predizioni.py --braccio C
"""
import argparse
import hashlib
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
from evoluzione.esperimenti.inserimento import _modello_da_ck, statica_cella, statiche  # noqa
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

TOLLERANZA = 1e-6
DIR_C = Path("results/evoluzione/inserimento_griglia")


def impronta(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def aggregati_per_nodo(prob, y, m, pesi):
    """A_h e B_h **per ciascun nodo**, che il protocollo prevedeva e che la
    fase 3 non aveva conservato: senza, il ricampionamento dei nodi non e'
    possibile."""
    T, K, H = m.shape
    A = np.zeros((K, H)); B = np.zeros((K, H)); N = np.zeros((K, H), dtype="int64")
    for h in range(H):
        mm = m[..., h]
        if not mm.any():
            continue
        pr = np.clip(prob[..., h, :], 1e-12, 1.0)
        yy = y[..., h]
        ce = -np.log(np.take_along_axis(pr, yy[..., None].astype("int64"),
                                        -1)[..., 0])
        w = pesi[yy]
        A[:, h] = (ce * w * mm).sum(0)
        B[:, h] = (w * mm).sum(0)
        N[:, h] = mm.sum(0)
    return A, B, N


def wce_da_predizioni(prob, y, m, pesi):
    """La stessa formula del valutatore: A_h / B_h per orizzonte, poi media."""
    A = np.zeros(len(ORIZZONTI)); B = np.zeros(len(ORIZZONTI))
    for h in range(len(ORIZZONTI)):
        mm = m[..., h]
        if not mm.any():
            continue
        p = np.clip(prob[..., h, :][mm], 1e-12, 1.0)
        yy = y[..., h][mm]
        w = pesi[yy]
        A[h] = float((w * -np.log(p[np.arange(len(yy)), yy])).sum())
        B[h] = float(w.sum())
    per_h = np.where(B > 0, A / np.maximum(B, 1e-12), np.nan)
    return float(np.nanmean(per_h)), per_h


def main() -> int:
    ap = argparse.ArgumentParser()
    # i bracci che hanno un punto di controllo o un adattamento in
    # `inserimento_griglia`: i cinque della fase 3 piu' quelli di E3
    ap.add_argument("--braccio", default="P",
                    choices=("C", "P", "A", "R", "F", "R-orig", "R-mon"))
    ap.add_argument("--pems04", action="store_true",
                    help="verifica esterna. **Nessun aggregato storico da "
                         "riprodurre**: la campagna PEMS04 non ne salva")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--dir-pred", type=Path, default=None,
                    help="predefinito: predizioni_fase3 (o predizioni_fase3_<passi>)")
    ap.add_argument("--acquisizione-passi", type=int, default=96,
                    help="E3-bis: la campagna con acquisizione (t0, t0 + L]; i "
                         "punti stanno in inserimento_griglia_<L>")
    a = ap.parse_args()
    # la cartella dei punti e dei manifesti segue l'acquisizione dichiarata
    dir_c = (DIR_C if a.acquisizione_passi == 96
             else DIR_C.with_name(f"{DIR_C.name}_{a.acquisizione_passi}"))
    if a.dir_pred is None:
        a.dir_pred = (Path("results/evoluzione/predizioni_fase3") if a.acquisizione_passi == 96
                      else Path(f"results/evoluzione/predizioni_fase3_{a.acquisizione_passi}"))
    a.dir_pred.mkdir(parents=True, exist_ok=True)
    _, dich, _ = configurazione(inserimento=True)
    from evoluzione.analisi.pesi import carica as carica_pesi
    print("=" * 84)
    print(f"RICOSTRUZIONE DELLE PREDIZIONI — braccio {a.braccio}, "
          f"tolleranza {TOLLERANZA:g} relativa")
    if a.acquisizione_passi != 96:
        print(f"  acquisizione (t0, t0 + {a.acquisizione_passi}] (E3-bis): punti in {dir_c}, "
              f"predizioni in {a.dir_pred}")
    print("=" * 84)
    guai, righe = [], []
    contesti = (("PEMS04_p0", "PEMS04_p1", "PEMS04_p2") if a.pems04
                else ("Madrid", "Londra", "Melbourne"))
    for i_c, c in enumerate(contesti):
        D = _carica(c, a.out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        fine = D["r"].shape[0] - max(ORIZZONTI)
        if a.pems04:
            t0 = GR.primo_t0(D["ts"], ok, int(fine * .85), fine, False)
            t1 = t0 + GR.L_DESCRITTORE
        else:
            t0, t1 = CALENDARIO[c][0], CALENDARIO[c][0] + a.acquisizione_passi
        per = GR.origini_dopo(ok, t1, fine)
        for p in ([i_c] if a.pems04 else (0, 1, 2)):
            nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
                SEME_PARTIZIONE[p])})
            NORM, nr, nv = _normalizzazione(D, nodi, ist)
            x = _canali(D, nr, nv)
            stat0 = statiche(D)
            pesi = np.asarray(carica_pesi(
                a.out / ("pesi_pems04" if a.pems04 else "pesi_griglia"),
                c, p).vettore(), dtype="float64")
            for s in dich:
                stat = statica_cella(stat0, D, nodi, nodi["prova"], t0, int(s))        # E14
                if a.pems04:
                    d_man = None          # nessun aggregato da riprodurre
                else:
                    man = dir_c / f"{a.braccio}_{c}_p{p}_s{int(s)}.json"
                    if not man.exists():
                        guai.append(f"manifesto {man.name}: assente"); continue
                    d_man = json.loads(man.read_text())
                desc = None
                if a.braccio == "F":
                    # F non e' un punto di controllo: si RIADATTA dal punto E,
                    # in modo deterministico, con la configurazione congelata
                    from evoluzione.componente.registro import Registro
                    from evoluzione.esperimenti.inserimento import adatta_F
                    st_ = int(configurazione(inserimento=True)[2][
                        list(dich).index(s)])
                    o_acq = GR.origini_acquisizione(ok, t0, t1)
                    rg = Registro.avvia("ricostruzione/F", note=f"{c} p{p} {s}",
                                        radice=a.out / "registro_ricostruzione")
                    m, _ = adatta_F(c, p, st_, a.out, D, nodi, ist, o_acq, rg)
                    rg.completa()
                    ck = Path(f"(riadattato da ck_E_{c}_p{p}_s{st_}.pt)")
                    imp_ck = f"E:{st_}"
                else:
                    ck = (Path("results/evoluzione/pems04")
                          / f"ck_{a.braccio}_{c}_s{int(s)}.pt" if a.pems04
                          else dir_c / f"ck_{a.braccio}_{c}_p{p}_s{int(s)}.pt")
                    if not ck.exists():
                        guai.append(f"{ck.name}: assente"); continue
                    m, dck = _modello_da_ck(ck, D, nodi, None)
                    if (dck["contesto"], dck["partizione"],
                            dck["braccio"]) != (c, p, a.braccio):
                        guai.append(f"{ck.name}: provenienza incoerente")
                        continue
                    imp_ck = impronta(ck)
                    if dck["d_descrittore"]:
                        GR.verifica_finestra_descrittore(ok, int(t1))
                        desc = _descrittori(D, nodi["prova"], int(t1),
                                            "BASE-CORRECTED", NORM)
                prima = {k: t.clone() for k, t in m.state_dict().items()}
                S = torch.as_tensor(stat[nodi["prova"]])
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
                                descriptor=desc, static_inputs=S)
                        PB[i:i + len(bl)] = torch.softmax(out, -1).numpy()
                        YY[i:i + len(bl)] = Y.numpy()
                        MM[i:i + len(bl)] = Mk.numpy()
                dt = time.time() - t_in
                if any(not torch.equal(prima[k], v)
                       for k, v in m.state_dict().items()):
                    guai.append(f"{ck.name}: lo stato e' cambiato in inferenza")
                w_new, per_h = wce_da_predizioni(PB, YY, MM, pesi)
                if d_man is None:
                    w_old, rel, rel_h = float("nan"), 0.0, 0.0
                    righe.append({"contesto": c, "partizione": p,
                                  "seme": int(s), "braccio": a.braccio,
                                  "impronta_ck": imp_ck,
                                  "wce_ricalcolata": w_new,
                                  "wce_conservata": None,
                                  "scarto_relativo": 0.0,
                                  "scarto_relativo_max_orizzonte": 0.0,
                                  "origini": len(per),
                                  "nodi": len(nodi["prova"]),
                                  "secondi_inferenza": dt})
                    Ah, Bh, Nh = aggregati_per_nodo(PB, YY, MM, pesi)
                    np.savez_compressed(
                        a.dir_pred / f"{a.braccio}_{c}_p{p}_s{int(s)}.npz",
                        prob=PB, y=YY, m=MM, A_per_nodo=Ah, B_per_nodo=Bh,
                        celle_per_nodo=Nh,
                        nodi=np.asarray(nodi["prova"], dtype="int32"),
                        origini=np.asarray(per, dtype="int32"),
                        orizzonti=np.asarray(ORIZZONTI, dtype="int16"),
                        contesto=c, partizione=p, seme=int(s),
                        braccio=a.braccio, t0=t0, t1=t1, impronta_ck=imp_ck)
                    print(f"  {c} s{int(s)}  wCE {w_new:.6f}  {dt:5.1f}s",
                          flush=True)
                    continue
                w_old = d_man["valutazione"]["perimetro_primario"]["perdita"]
                oh_old = d_man["valutazione"]["perimetro_primario"][
                    "per_orizzonte"]
                rel = abs(w_new - w_old) / abs(w_old)
                rel_h = max(abs(x_ - y_) / abs(y_) for x_, y_ in
                            zip(per_h, oh_old) if np.isfinite(x_))
                Ah, Bh, Nh = aggregati_per_nodo(PB, YY, MM, pesi)
                righe.append({"contesto": c, "partizione": p, "seme": int(s),
                              "braccio": a.braccio, "impronta_ck": imp_ck,
                              "wce_ricalcolata": w_new, "wce_conservata": w_old,
                              "scarto_relativo": rel,
                              "scarto_relativo_max_orizzonte": rel_h,
                              "origini": len(per), "nodi": len(nodi["prova"]),
                              "secondi_inferenza": dt})
                if rel > TOLLERANZA or rel_h > TOLLERANZA:
                    guai.append(f"{ck.name}: scarto {rel:.2e} (orizzonti "
                                f"{rel_h:.2e}) oltre la tolleranza")
                np.savez_compressed(
                    a.dir_pred / f"{a.braccio}_{c}_p{p}_s{int(s)}.npz",
                    prob=PB, y=YY, m=MM,
                    nodi=np.asarray(nodi["prova"], dtype="int32"),
                    origini=np.asarray(per, dtype="int32"),
                    orizzonti=np.asarray(ORIZZONTI, dtype="int16"),
                    A_per_nodo=Ah, B_per_nodo=Bh, celle_per_nodo=Nh,
                    contesto=c, partizione=p, seme=int(s), braccio=a.braccio,
                    t0=t0, t1=t1, impronta_ck=imp_ck)
                print(f"  {c:11s} p{p} s{int(s)}  wCE {w_new:.6f} contro "
                      f"{w_old:.6f}  scarto {rel:.1e}  {dt:5.1f}s", flush=True)
    (a.dir_pred / f"controllo_{a.braccio}.json").write_text(json.dumps(
        {"tolleranza": TOLLERANZA, "esecuzioni": righe, "anomalie": guai,
         "deviazione_protocollo": (
             "gli intervalli della fase 3 sono stati ottenuti ricampionando "
             "partizioni e inizializzazioni sulle metriche aggregate per "
             "esecuzione: NON includono il ricampionamento dei nodi previsto "
             "dal protocollo. Questi artefatti per nodo e orizzonte lo rendono "
             "possibile nella rianalisi."),
         "nota": ("le predizioni originarie non erano state salvate: si "
                  "confrontano le metriche ricalcolate con gli aggregati "
                  "conservati, non le predizioni")}, indent=2))
    print(f"\n{'=' * 84}")
    print(f"  {len(righe)} esecuzioni ricostruite, {len(guai)} anomalie")
    if righe:
        r = [x["scarto_relativo"] for x in righe]
        rh = [x["scarto_relativo_max_orizzonte"] for x in righe]
        print(f"  scarto relativo: massimo {max(r):.2e} sulla wCE, "
              f"{max(rh):.2e} sugli orizzonti")
    for g in guai[:8]:
        print(f"     {g}")
    return 0 if not guai else 1


if __name__ == "__main__":
    raise SystemExit(main())
