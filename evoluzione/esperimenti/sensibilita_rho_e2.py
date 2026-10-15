#!/usr/bin/env python3
"""
Sensibilita' a rho dell'identity dropout (protocol/E2.md, «riportata come
figura»).
======================================================================
rho = 0,15 e' stato fissato prima del lancio. Qui si chiede quanto l'esito
dipenda da quella scelta: **una citta', quattro semi, rho in {0,05; 0,30}**,
con rho = 0,15 preso dalla campagna gia' eseguita.

    addestramento   E1 con rho 0,05 e 0,30, Madrid p0, semi 201-204:
                    8 traiettorie, lo stesso lavoratore di `esegui_E.py`,
                    cartella propria per ciascun rho
    valutazione     F0' (token, nessun aggiornamento) e F' (adattato) sulle
                    stesse celle di E2, con le stesse funzioni di
                    `esegui_e2.py`; C dalla fase 3
    esito           F0' - C e F' - C per rho, media sui semi, intervallo a
                    ricampionamento di semi e nodi; veterani e norma del
                    token per rho

**E' una figura, non un criterio.** Nessuna soglia, nessun verdetto: il
congelamento di E2 la registra come eseguita e ne riporta i numeri.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/sensibilita_rho_e2.py --piano
    poetry run python evoluzione/esperimenti/sensibilita_rho_e2.py --lavoratori 8
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

CONTESTO, PARTIZIONE = "Madrid", 0
SEMI_DICH = (201, 202, 203, 204)
RHO_NUOVI = (0.05, 0.30)
RHO_CAMPAGNA = 0.15
CARTELLA = {0.05: "E1_rho005_inserimento_griglia",
            0.30: "E1_rho030_inserimento_griglia",
            0.15: "E1_inserimento_griglia"}
DIR_PRED = "predizioni_sensibilita_rho"
B_BOOT, SEME_BOOT = 4000, 20260930


def cfg_rho(rho: float, out: Path) -> dict:
    """La configurazione di `esegui_E.py --braccio E1 --protocollo
    griglia_E1`, con rho ed etichetta propri. Tutto il resto identico."""
    return {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
            "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
            "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
            "etichetta": CARTELLA[rho], "braccio": "E1", "rho": float(rho),
            "training_protocol": "principale", "griglia_temporale": "reale",
            "dir_pesi": str(out / "pesi_griglia"),
            "checkpoint_selection_population": "initial_network",
            "dir_canonico": str(out / "canonico"),
            "dir_stati_completi": str(out / f"stati_completi_{CARTELLA[rho]}")}


def piano_addestramenti(out: Path):
    from evoluzione.esperimenti.esegui_E import marcatore
    from evoluzione.esperimenti.fasi import percorso_E
    from evoluzione.esperimenti.semi import seme_torch
    tutti, da_fare = [], []
    for rho in RHO_NUOVI:
        for s in SEMI_DICH:
            x = {"contesto": CONTESTO, "partizione": PARTIZIONE, "seme": s,
                 "seme_torch": seme_torch(s), "braccio": "E1", "rho": rho}
            ck = percorso_E(out / CARTELLA[rho], CONTESTO, PARTIZIONE,
                            x["seme_torch"], braccio="E1")
            tutti.append(x)
            if not marcatore(ck).exists():
                da_fare.append(x)
    return tutti, da_fare


def _addestra(args):
    """Il lavoratore di `esegui_E`, con la configurazione di questo rho."""
    x, out, fili = args
    from evoluzione.esperimenti.esegui_E import _lavora
    cfg = cfg_rho(x["rho"], Path(out))
    return _lavora(({k: v for k, v in x.items() if k != "rho"}, cfg, out, fili))


def valuta_rho(out: Path, rho: float, dir_pred: Path) -> list:
    """F0', F' e veterani per ciascun seme, dai punti E1 di questo rho.

    Stesse funzioni di `esegui_e2.py`: `da_E1`, `valuta`, `adatta`. Per
    rho = 0,15 si leggono le predizioni gia' salvate dalla campagna E2.
    """
    import numpy as np
    import torch
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import adatta, carica_E, copia_da_E
    from evoluzione.componente.episodio import lotti_episodio
    from evoluzione.componente.predittore import ORIZZONTI
    from evoluzione.esperimenti.addestramento import (
        _canali, _carica, _normalizzazione, _partizioni)
    from evoluzione.esperimenti.esegui_e2 import D_STAT, da_E1, valuta
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    from evoluzione.esperimenti.fasi import percorso_E
    from evoluzione.esperimenti.inserimento import statiche
    from evoluzione.esperimenti.ricostruisci_predizioni import aggregati_per_nodo
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, seme_torch

    cfgF = json.loads((out / "selezione_F_griglia" /
                       "configurazione_F.json").read_text())["scelte"][CONTESTO]
    D = _carica(CONTESTO, out / "maschere")
    ok = GR.passi_regolari(D["ts"])
    t0, t1 = CALENDARIO[CONTESTO]
    fine = D["r"].shape[0] - max(ORIZZONTI)
    per = GR.origini_dopo(ok, t1, fine)
    o_acq = GR.origini_acquisizione(ok, t0, t1)
    nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
        SEME_PARTIZIONE[PARTIZIONE])})
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    from evoluzione.esperimenti.inserimento import statica_cella
    stat = statica_cella(statiche(D), D, nodi, nodi["prova"], t0, 0)
    pesi = np.asarray(carica_pesi(out / "pesi_griglia", CONTESTO, PARTIZIONE)
                      .vettore(), dtype="float64")
    S_nuovi = torch.as_tensor(stat[nodi["prova"]])
    S_vet = torch.as_tensor(stat[nodi["addestramento"]])
    w_pesi = torch.as_tensor(pesi, dtype=torch.float32)
    righe = []
    for s in SEMI_DICH:
        st = seme_torch(s)
        f1 = percorso_E(out / CARTELLA[rho], CONTESTO, PARTIZIONE, st,
                        braccio="E1")
        dE1, nodi_in, imp1 = carica_E(f1, D_STAT)
        sd = dE1["state_dict"]
        tok = sd["identita.ignoto"].reshape(-1).double()
        emb = sd["identita.embedding"].double()
        r = {"rho": rho, "seme": s, "impronta_ck": imp1,
             "rapporto_norma_token": float(tok.norm() / emb.norm(dim=1).median()),
             "distanza_dalla_media": float((tok - emb.mean(0)).norm())}
        for braccio, partenza, adattare in (("F0p", "token", False),
                                            ("Fp", "token", True)):
            # rho = 0,15: le predizioni della campagna E2, gia' salvate
            nome = (f"{braccio}_{CONTESTO}_p{PARTIZIONE}_s{s}"
                    + ("" if rho == RHO_CAMPAGNA else f"_rho{rho:.2f}") + ".npz")
            g = (out / "predizioni_e2" if rho == RHO_CAMPAGNA else dir_pred) / nome
            if g.exists():
                z = np.load(g, allow_pickle=True)
                A, Bm = z["A_per_nodo"], z["B_per_nodo"]
                nodi_z = z["nodi"].tolist()
            else:
                m, forn = da_E1(dE1, nodi_in, nodi["prova"], partenza)
                if adattare:
                    lotti = lotti_episodio(x, D["classe"], stat, nodi["prova"],
                                           o_acq)
                    adatta(m, forn, lotti, w_pesi, cfgF["passo"],
                           cfgF["aggiornamenti"])
                PB, YY, MM, w, ph, dt = valuta(m, x, D["classe"],
                                               nodi["prova"], per, S_nuovi, pesi)
                A, Bm, Nh = aggregati_per_nodo(PB, YY, MM, pesi)
                np.savez_compressed(
                    g, prob=PB, y=YY, m=MM, A_per_nodo=A, B_per_nodo=Bm,
                    celle_per_nodo=Nh,
                    nodi=np.asarray(nodi["prova"], dtype="int32"),
                    origini=np.asarray(per, dtype="int32"),
                    orizzonti=np.asarray(ORIZZONTI, dtype="int16"),
                    contesto=CONTESTO, partizione=PARTIZIONE, seme=s,
                    braccio=braccio, rho=rho, t0=t0, t1=t1, impronta_ck=imp1)
                nodi_z = [int(k) for k in nodi["prova"]]
            r[braccio] = {"A": A, "B": Bm, "nodi": nodi_z}
        # veterani: E1 di questo rho contro E, sui nodi iniziali
        fE = percorso_E(out / "E_inserimento_griglia", CONTESTO, PARTIZIONE, st)
        dE, _, _ = carica_E(fE, D_STAT)
        coppia = {}
        for nome, dd in (("E", dE), ("E1", dE1)):
            mm, _ = copia_da_E(dd, nodi_in, [], D_STAT)
            with torch.no_grad():
                mm.identita.iniziali.copy_(dd["state_dict"]["identita.embedding"])
            _, _, _, w_, _, _ = valuta(mm, x, D["classe"], nodi["addestramento"],
                                       per, S_vet, pesi)
            coppia[nome] = w_
        r["veterani_rel"] = (coppia["E1"] - coppia["E"]) / abs(coppia["E"])
        # C della fase 3, stessa cella: appaiamento verificato qui
        zc = np.load(out / "predizioni_fase3" /
                     f"C_{CONTESTO}_p{PARTIZIONE}_s{s}.npz", allow_pickle=True)
        if zc["nodi"].tolist() != r["F0p"]["nodi"] or \
                zc["origini"].tolist() != np.asarray(per).tolist():
            raise RuntimeError(f"seme {s}: C non appaiato con F0' (nodi o "
                               f"origini diversi)")
        r["C"] = {"A": zc["A_per_nodo"], "B": zc["B_per_nodo"]}
        print(f"  rho {rho:.2f} s{s}: token {r['rapporto_norma_token']:.2f}x, "
              f"veterani {r['veterani_rel']:+.2%}", flush=True)
        righe.append(r)
    return righe


def confronti(righe, rng):
    """F0' - C e F' - C: media sui semi, IC a ricampionamento di semi e nodi."""
    import numpy as np
    from evoluzione.analisi.analizza_e2 import wce
    K = righe[0]["C"]["A"].shape[0]
    fuori = {}
    for n1 in ("F0p", "Fp"):
        diff = [wce(r[n1]["A"], r[n1]["B"]) - wce(r["C"]["A"], r["C"]["B"])
                for r in righe]
        v = []
        for _ in range(B_BOOT):
            ss = rng.integers(0, len(righe), len(righe))
            nd = rng.integers(0, K, K)
            v.append(np.mean([wce(righe[i][n1]["A"], righe[i][n1]["B"], nd)
                              - wce(righe[i]["C"]["A"], righe[i]["C"]["B"], nd)
                              for i in ss]))
        q = np.percentile(v, [2.5, 97.5])
        fuori[f"{n1}-C"] = {"media": float(np.mean(diff)),
                            "per_seme": [float(d) for d in diff],
                            "ic_semi_nodi": q.tolist()}
    return fuori


def figura(ris: dict, f: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rhos = sorted(float(k) for k in ris)
    fig, ax = plt.subplots(figsize=(6, 4))
    for n1, eti, off in (("F0p-C", "F₀′ − C", -0.004), ("Fp-C", "F′ − C", 0.004)):
        m = [ris[f"{r:.2f}"][n1]["media"] for r in rhos]
        lo = [ris[f"{r:.2f}"][n1]["ic_semi_nodi"][0] for r in rhos]
        hi = [ris[f"{r:.2f}"][n1]["ic_semi_nodi"][1] for r in rhos]
        xs = [r + off for r in rhos]
        ax.errorbar(xs, m, yerr=[[a - b for a, b in zip(m, lo)],
                                 [b - a for a, b in zip(m, hi)]],
                    fmt="o-", capsize=3, label=eti)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("ρ (identity dropout)")
    ax.set_ylabel("Δ wCE rispetto a C (negativo = meglio)")
    ax.set_xticks(rhos)
    ax.set_title(f"Sensibilità a ρ — {CONTESTO} p{PARTIZIONE}, "
                 f"{len(SEMI_DICH)} semi; IC 95 % su semi × nodi")
    ax.legend()
    fig.tight_layout()
    f.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(f, dpi=150)


def main() -> int:
    ap = argparse.ArgumentParser(description="sensibilita' a rho, E2")
    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    from evoluzione.esperimenti.inserimento import applica_statica, argomento_statica
    argomento_statica(ap)
    a = ap.parse_args()
    applica_statica(a.statica)
    tutti, da_fare = piano_addestramenti(a.out)
    print("=" * 84)
    print("SENSIBILITA' A RHO — E2, figura")
    print("=" * 84)
    print(f"  {CONTESTO} p{PARTIZIONE}, semi {SEMI_DICH}; rho nuovi {RHO_NUOVI},"
          f" rho della campagna {RHO_CAMPAGNA}")
    print(f"  addestramenti E1: {len(tutti)} previsti, {len(da_fare)} da fare "
          f"(marcatori .fatto); cartelle {[CARTELLA[r] for r in RHO_NUOVI]}")
    print(f"  parallelismo: {a.lavoratori} processi x {a.fili} filo")
    if a.piano:
        print("\n  --piano: nessuna esecuzione avviata.")
        for x in da_fare:
            print(f"     rho {x['rho']:.2f} seme {x['seme']}->{x['seme_torch']}")
        return 0

    t0 = time.time()
    if da_fare:
        ctx = mp.get_context("spawn")
        with ctx.Pool(min(a.lavoratori, len(da_fare))) as pool:
            for i, r in enumerate(pool.imap_unordered(
                    _addestra, [(x, str(a.out), a.fili) for x in da_fare]), 1):
                print(f"  [{i}/{len(da_fare)}] seme {r['seme']} "
                      f"{r['esito']:10s} {r['secondi']/60:5.1f} min"
                      + (f"\n      {r['errore']}" if r["esito"] == "fallita"
                         else ""), flush=True)
                if r["esito"] == "fallita":
                    return 1
    ore_add = (time.time() - t0) / 3600

    print("\n[valutazione] F0' e F' per rho, sulle celle di E2")
    import numpy as np
    dir_pred = a.out / DIR_PRED
    dir_pred.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEME_BOOT)
    ris, dett = {}, {}
    for rho in sorted(RHO_NUOVI + (RHO_CAMPAGNA,)):
        righe = valuta_rho(a.out, rho, dir_pred)
        ris[f"{rho:.2f}"] = confronti(righe, rng)
        dett[f"{rho:.2f}"] = [{k: v for k, v in r.items()
                               if k not in ("F0p", "Fp", "C")} for r in righe]
        c = ris[f"{rho:.2f}"]
        print(f"  rho {rho:.2f}: F0' - C {c['F0p-C']['media']:+.4f} "
              f"[{c['F0p-C']['ic_semi_nodi'][0]:+.4f}, "
              f"{c['F0p-C']['ic_semi_nodi'][1]:+.4f}] | F' - C "
              f"{c['Fp-C']['media']:+.4f} [{c['Fp-C']['ic_semi_nodi'][0]:+.4f}, "
              f"{c['Fp-C']['ic_semi_nodi'][1]:+.4f}]")
    f_fig = RADICE / "figure" / "sensibilita_rho_e2.png"
    figura(ris, f_fig)
    riep = {"contesto": CONTESTO, "partizione": PARTIZIONE,
            "semi": list(SEMI_DICH), "rho": sorted(RHO_NUOVI + (RHO_CAMPAGNA,)),
            "rho_campagna": RHO_CAMPAGNA, "confronti": ris,
            "per_seme": dett, "repliche": B_BOOT, "seme_bootstrap": SEME_BOOT,
            "nota": ("figura, non criterio: intervallo su semi (4) e nodi, "
                     "una sola partizione; non confrontabile con gli "
                     "intervalli a tre livelli della campagna"),
            "figura": str(f_fig.relative_to(RADICE)),
            "ore_calendario_addestramento": ore_add,
            "istante": datetime.now(timezone.utc).isoformat()}
    f = a.out / "sensibilita_rho_e2.json"
    f.write_text(json.dumps(riep, indent=2, ensure_ascii=False))
    print(f"\n  riepilogo in {f}; figura in {f_fig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
