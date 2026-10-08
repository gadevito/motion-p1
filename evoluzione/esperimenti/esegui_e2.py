#!/usr/bin/env python3
"""
E2 — i tre bracci di valutazione dal punto E1, piu' il controllo veterani.
===========================================================================
    F0'        E1 congelato, nodo nuovo = TOKEN IGNOTO, nessun aggiornamento
    F'         E1 congelato, embedding inizializzato al token e ADATTATO
    F0-mean'   E1 congelato, nodo nuovo = MEDIA degli embedding iniziali
               (isola l'effetto del token dal resto)

    veterani   E1 contro E sui NODI INIZIALI: **E1 non deve peggiorare oltre
               l'1% relativo**, altrimenti il token e' un costo della politica

**Nessun addestramento.** Stesse celle di F0 e F.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_e2.py
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
from evoluzione.componente.adattamento import (  # noqa: E402
    adatta, carica_E, copia_da_E)
from evoluzione.componente.episodio import lotti_episodio  # noqa: E402
from evoluzione.componente.predittore import ORIZZONTI  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _canali, _carica, _lotto, _normalizzazione, _partizioni)
from evoluzione.esperimenti.esegui_inserimento import CALENDARIO  # noqa
from evoluzione.esperimenti.fasi import percorso_E  # noqa: E402
from evoluzione.esperimenti.inserimento import statiche  # noqa: E402
from evoluzione.esperimenti.ricostruisci_predizioni import (  # noqa: E402
    aggregati_per_nodo, wce_da_predizioni)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

D_STAT = 5
DIR_E1 = "E1_inserimento_griglia"
DIR_E = "E_inserimento_griglia"


def da_E1(dE, nodi_in, nodi_nuovi, partenza: str):
    """Copia di E1 con il nodo nuovo posto al TOKEN o alla MEDIA.

    `copia_da_E` non trasferisce il token — non e' un modulo comune — quindi
    lo si legge dallo stato e lo si applica esplicitamente.
    """
    # LA SORGENTE VIENE DAL PUNTO DI CONTROLLO (come in `_modello_da_ck`): su
    # PEMS il predittore ha undici canali, e il predefinito a nove non li accoglie
    from evoluzione.esperimenti.addestramento import sorgente_di
    m, forn = copia_da_E(dE, nodi_in, nodi_nuovi, D_STAT,
                         sorgente=sorgente_di(dE.get("contesto", "")))
    sd = dE["state_dict"]
    if "identita.ignoto" not in sd:
        raise RuntimeError("il punto non ha il token ignoto: non e' un E1")
    with torch.no_grad():
        if partenza == "token":
            forn.nuovi.copy_(sd["identita.ignoto"].expand_as(forn.nuovi))
        elif partenza != "media":
            raise ValueError(f"partenza ignota: {partenza}")
    return m, forn


def valuta(m, x, classe, nodi_v, per, S, pesi):
    PB = np.empty((len(per), len(nodi_v), len(ORIZZONTI), 3), dtype="float32")
    YY = np.zeros(PB.shape[:3], dtype="int8")
    MM = np.zeros(PB.shape[:3], dtype=bool)
    m.eval()
    prima = {k: z.clone() for k, z in m.state_dict().items()}
    t0 = time.time()
    with torch.inference_mode():
        for i in range(0, len(per), 256):
            bl = np.asarray(per[i:i + 256], dtype="int64")
            X, Y, Mk = _lotto(x, classe, bl, nodi_v)
            out = m(X, node_ids=[int(z) for z in nodi_v], static_inputs=S)
            PB[i:i + len(bl)] = torch.softmax(out, -1).numpy()
            YY[i:i + len(bl)] = Y.numpy(); MM[i:i + len(bl)] = Mk.numpy()
    if any(not torch.equal(prima[k], z) for k, z in m.state_dict().items()):
        raise RuntimeError("lo stato del modello si e' mosso in inferenza")
    w, ph = wce_da_predizioni(PB, YY, MM, pesi)
    return PB, YY, MM, w, ph, time.time() - t0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--dir-pred", type=Path,
                    default=Path("results/evoluzione/predizioni_e2"))
    a = ap.parse_args()
    a.dir_pred.mkdir(parents=True, exist_ok=True)
    _, dich, semi_t = configurazione(inserimento=True)
    from evoluzione.analisi.pesi import carica as carica_pesi
    cfgF = json.loads((a.out / "selezione_F_griglia" /
                       "configurazione_F.json").read_text())["scelte"]
    print("=" * 84)
    print("E2 — F0', F' e F0-mean' dal punto E1, piu' il controllo veterani")
    print("=" * 84)
    righe, vet = [], []
    for c in ("Madrid", "Londra", "Melbourne"):
        D = _carica(c, a.out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        t0, t1 = CALENDARIO[c]
        fine = D["r"].shape[0] - max(ORIZZONTI)
        per = GR.origini_dopo(ok, t1, fine)
        o_acq = GR.origini_acquisizione(ok, t0, t1)
        sF = cfgF[c]
        for p in (0, 1, 2):
            nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
                SEME_PARTIZIONE[p])})
            NORM, nr, nv = _normalizzazione(D, nodi, ist)
            x = _canali(D, nr, nv)
            stat = statiche(D)
            pesi = np.asarray(carica_pesi(a.out / "pesi_griglia", c, p)
                              .vettore(), dtype="float64")
            S_nuovi = torch.as_tensor(stat[nodi["prova"]])
            S_vet = torch.as_tensor(stat[nodi["addestramento"]])
            w_pesi = torch.as_tensor(pesi, dtype=torch.float32)
            for i_s, st in enumerate(semi_t):
                s = int(dich[i_s])
                f1 = percorso_E(a.out / DIR_E1, c, p, int(st), braccio="E1")
                dE1, nodi_in, imp1 = carica_E(f1, D_STAT)
                for braccio, partenza, adattare in (
                        ("F0p", "token", False),
                        ("F0meanp", "media", False),
                        ("Fp", "token", True)):
                    m, forn = da_E1(dE1, nodi_in, nodi["prova"], partenza)
                    n_agg = 0
                    if adattare:
                        lotti = lotti_episodio(x, D["classe"], stat,
                                               nodi["prova"], o_acq)
                        n_agg = adatta(m, forn, lotti, w_pesi, sF["passo"],
                                       sF["aggiornamenti"])
                    PB, YY, MM, w, ph, dt = valuta(
                        m, x, D["classe"], nodi["prova"], per, S_nuovi, pesi)
                    Ah, Bh, Nh = aggregati_per_nodo(PB, YY, MM, pesi)
                    np.savez_compressed(
                        a.dir_pred / f"{braccio}_{c}_p{p}_s{s}.npz",
                        prob=PB, y=YY, m=MM, A_per_nodo=Ah, B_per_nodo=Bh,
                        celle_per_nodo=Nh,
                        nodi=np.asarray(nodi["prova"], dtype="int32"),
                        origini=np.asarray(per, dtype="int32"),
                        orizzonti=np.asarray(ORIZZONTI, dtype="int16"),
                        contesto=c, partizione=p, seme=s, braccio=braccio,
                        t0=t0, t1=t1, impronta_ck=imp1)
                    righe.append({"contesto": c, "partizione": p, "seme": s,
                                  "braccio": braccio, "wce": w,
                                  "per_orizzonte": ph.tolist(),
                                  "aggiornamenti": n_agg, "secondi": dt})
                    print(f"  {c:11s} p{p} s{s} {braccio:8s} wCE {w:.6f}"
                          + (f"  ({n_agg} aggiornamenti)" if adattare else ""),
                          flush=True)
                # ---- il controllo VETERANI: E1 contro E sui nodi iniziali ---
                fE = percorso_E(a.out / DIR_E, c, p, int(st))
                dE, _, _ = carica_E(fE, D_STAT)
                coppia = {}
                for nome, dd in (("E", dE), ("E1", dE1)):
                    mm, _ = copia_da_E(dd, nodi_in, [], D_STAT)
                    with torch.no_grad():
                        mm.identita.iniziali.copy_(
                            dd["state_dict"]["identita.embedding"])
                    _, _, _, w_, _, _ = valuta(mm, x, D["classe"],
                                               nodi["addestramento"], per,
                                               S_vet, pesi)
                    coppia[nome] = w_
                rel = (coppia["E1"] - coppia["E"]) / abs(coppia["E"])
                vet.append({"contesto": c, "partizione": p, "seme": s,
                            "wce_E": coppia["E"], "wce_E1": coppia["E1"],
                            "scarto_relativo": rel})
                print(f"  {c:11s} p{p} s{s} veterani  E {coppia['E']:.6f}  "
                      f"E1 {coppia['E1']:.6f}  scarto {rel:+.2%}"
                      + ("  **OLTRE L'1%**" if rel > 0.01 else ""), flush=True)
    (a.dir_pred / "controllo_e2.json").write_text(json.dumps(
        {"bracci": righe, "veterani": vet,
         "soglia_veterani": 0.01,
         "definizioni": {
             "F0p": "E1 congelato, nodo nuovo al token ignoto, nessun "
                    "aggiornamento",
             "F0meanp": "E1 congelato, nodo nuovo alla media degli embedding "
                        "iniziali",
             "Fp": "E1 congelato, dal token, adattato con la configurazione "
                   "di F congelata"}}, indent=2))
    oltre = [v_ for v_ in vet if v_["scarto_relativo"] > 0.01]
    print(f"\n  {len(righe)} valutazioni, {len(vet)} confronti sui veterani")
    print(f"  **veterani oltre l'1%: {len(oltre)}**"
          + ("  -> costo della politica, da riportare in tabella" if oltre
             else "  -> il token non danneggia la rete esistente"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
