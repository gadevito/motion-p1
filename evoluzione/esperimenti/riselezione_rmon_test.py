#!/usr/bin/env python3
"""
Analisi aggiunta il 2/10 — R-mon con selezione a PESO UGUALE, sul test.
=========================================================================
Dalle curve (`analisi/riselezione_rmon.py`) si sa in quali celle la regola
0,5 rete iniziale + 0,5 nodi nuovi avrebbe scelto un punto diverso da quello
salvato. Per quelle celle, e solo per quelle:

    --addestra   riaddestra R-mon (deterministico: stesso seme, stesse
                 estrazioni) salvando TUTTI gli undici punti, in una cartella
                 propria; verifica che il punto migliore coincida a bit con
                 quello della campagna
    --valuta     ricostruisce il modello dal punto a peso uguale e salva le
                 predizioni per cella sui nodi nuovi (`Rmoneq_*.npz`); nelle
                 celle in cui il punto coincide, Rmoneq = R-mon per costruzione
    --analizza   R-mon-eq - R-orig, - R-mon, - C con ricampionamento congiunto

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/riselezione_rmon_test.py --addestra --lavoratori 8
    poetry run python evoluzione/esperimenti/riselezione_rmon_test.py --valuta
    poetry run python evoluzione/esperimenti/riselezione_rmon_test.py --analizza
"""
import argparse
import json
import multiprocessing as mp
import shutil
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

ETICHETTA = "rmon_punti"
BRACCIO = "R-mon"
NOME = "Rmoneq"
CITTA = ("Madrid", "Londra", "Melbourne")


def celle_diverse(out: Path):
    d = json.loads((out / "riselezione_rmon.json").read_text())
    return [(r["contesto"], int(r["partizione"]), int(r["seme"]),
             int(r["u_peso_uguale"]), int(r["u_salvato"]))
            for r in d["righe"] if r["diverso"]], d["righe"]


def _addestra(args):
    c, p, s, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.registro import Registro
    from evoluzione.esperimenti.addestramento import (_carica, _partizioni,
                                                      addestra_una)
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO, Esec
    from evoluzione.esperimenti.inserimento import cfg_braccio
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    out = Path(out)
    t_in = time.time()
    try:
        ck_fin = out / ETICHETTA / f"ck_{BRACCIO}_{c}_p{p}_s{s}.pt"
        if (ck_fin.with_name(ck_fin.name + ".fatto")).exists():
            return {"c": c, "p": p, "s": s, "esito": "gia' fatta", "secondi": 0}
        t0, t1 = CALENDARIO[c]
        D = _carica(c, out / "maschere")
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[p])})
        ok = GR.passi_regolari(D["ts"])
        o_acq = GR.origini_acquisizione(ok, t0, t1)
        cfg = cfg_braccio(BRACCIO, c, p, s, out, nodi, o_acq, t1=t1)
        cfg.update({"etichetta": ETICHETTA, "salva_tutti_i_punti": True,
                    "dir_stati_completi": str(out / f"stati_completi_{ETICHETTA}")})
        reg = Registro.avvia(f"{ETICHETTA}/{BRACCIO}",
                             note=f"{c} p{p} seme {s}: tutti i punti",
                             radice=out / "registro")
        reg.configurazione({**cfg, "contesto": c, "partizione": p, "seme": s})
        addestra_una(Esec(c, p, cfg["variante"]), reg, cfg, {
            "partizione": np.random.default_rng(SEME_PARTIZIONE[p]),
            "inizializzazione": np.random.default_rng(s)}, out)
        reg.completa()
        # DETERMINISMO: il punto migliore deve coincidere con la campagna
        a = torch.load(ck_fin, map_location="cpu", weights_only=False)
        b = torch.load(out / "inserimento_griglia" / ck_fin.name,
                       map_location="cpu", weights_only=False)
        sc = max(float((a["state_dict"][k].float() - b["state_dict"][k].float())
                       .abs().max()) for k in a["state_dict"])
        if sc != 0.0 or a["aggiornamento"] != b["aggiornamento"]:
            raise RuntimeError(f"il riaddestramento NON riproduce la campagna: "
                               f"scarto {sc:.2e}, u{a['aggiornamento']} contro "
                               f"u{b['aggiornamento']}")
        (ck_fin.with_name(ck_fin.name + ".fatto")).write_text(
            json.dumps({"scarto": sc, "aggiornamento": a["aggiornamento"]}))
        return {"c": c, "p": p, "s": s, "esito": "completata",
                "secondi": time.time() - t_in, "scarto": sc}
    except Exception as e:                                   # noqa: BLE001
        return {"c": c, "p": p, "s": s, "esito": "fallita",
                "errore": f"{type(e).__name__}: {e}"[:300],
                "secondi": time.time() - t_in}


def valuta(out: Path, diverse, righe):
    import numpy as np
    import torch
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.predittore import ORIZZONTI
    from evoluzione.esperimenti.addestramento import (
        _canali, _carica, _normalizzazione, _partizioni)
    from evoluzione.esperimenti.esegui_e2 import valuta as valuta_e2
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    from evoluzione.esperimenti.inserimento import _modello_da_ck, statiche
    from evoluzione.esperimenti.ricostruisci_predizioni import aggregati_per_nodo
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    dir_pred = out / "predizioni_fase3"
    div = {(c, p, s): (u_eq, u_sal) for c, p, s, u_eq, u_sal in diverse}
    n_copie = n_val = 0
    for r in righe:
        c, p, s = r["contesto"], int(r["partizione"]), int(r["seme"])
        g = dir_pred / f"{NOME}_{c}_p{p}_s{s}.npz"
        if (c, p, s) not in div:
            # stesso punto: le predizioni di R-mon valgono per costruzione
            shutil.copyfile(dir_pred / f"R-mon_{c}_p{p}_s{s}.npz", g)
            n_copie += 1
    per_c = {}
    for (c, p, s), (u_eq, u_sal) in sorted(div.items()):
        if c not in per_c:
            D = _carica(c, out / "maschere")
            ok = GR.passi_regolari(D["ts"])
            t0, t1 = CALENDARIO[c]
            fine = D["r"].shape[0] - max(ORIZZONTI)
            per_c[c] = (D, ok, t0, t1, GR.origini_dopo(ok, t1, fine))
        D, ok, t0, t1, per = per_c[c]
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[p])})
        NORM, nr, nv = _normalizzazione(D, nodi, ist)
        x = _canali(D, nr, nv)
        stat = statiche(D)
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                          dtype="float64")
        ck = out / ETICHETTA / f"ck_{BRACCIO}_{c}_p{p}_s{s}_u{u_eq}.pt"
        m, d = _modello_da_ck(ck, D, nodi, None)
        S = torch.as_tensor(stat[nodi["prova"]])
        PB, YY, MM, w, ph, dt = valuta_e2(m, x, D["classe"], nodi["prova"], per,
                                          S, pesi)
        A, Bm, N = aggregati_per_nodo(PB, YY, MM, pesi)
        np.savez_compressed(
            dir_pred / f"{NOME}_{c}_p{p}_s{s}.npz", prob=PB, y=YY, m=MM,
            A_per_nodo=A, B_per_nodo=Bm, celle_per_nodo=N,
            nodi=np.asarray(nodi["prova"], dtype="int32"),
            origini=np.asarray(per, dtype="int32"),
            orizzonti=np.asarray(ORIZZONTI, dtype="int16"),
            contesto=c, partizione=p, seme=s, braccio=NOME, t0=t0, t1=t1,
            aggiornamento=u_eq, aggiornamento_salvato=u_sal)
        n_val += 1
        print(f"  {c:11s} p{p} s{s}  u{u_sal} -> u{u_eq}  wCE {w:.6f}  {dt:4.1f}s",
              flush=True)
    print(f"\n  {n_copie} celle copiate da R-mon (stesso punto), {n_val} valutate")


def analizza(out: Path):
    import numpy as np
    from evoluzione.analisi.analizza_e2 import wce
    rng = np.random.default_rng(20261003)
    dir_pred = out / "predizioni_fase3"
    fuori = {}
    for c in CITTA:
        d = {}
        for f in sorted(dir_pred.glob(f"{NOME}_{c}_p*_s*.npz")):
            p = int(f.stem.split("_p")[1].split("_")[0]); s = int(f.stem.split("_s")[1])
            for b in (NOME, "R-mon", "R-orig", "C"):
                d[(b, p, s)] = np.load(dir_pred / f"{b}_{c}_p{p}_s{s}.npz",
                                       allow_pickle=True)
        parts = sorted({k[1] for k in d}); semi = sorted({k[2] for k in d})
        K = d[(NOME, parts[0], semi[0])]["A_per_nodo"].shape[0]
        print(f"\n{c}  {len(semi)} semi x {len(parts)} partizioni, {K} nodi")
        for n2 in ("R-mon", "R-orig", "C"):
            m0 = float(np.mean([wce(d[(NOME, p, s)]["A_per_nodo"], d[(NOME, p, s)]["B_per_nodo"])
                                - wce(d[(n2, p, s)]["A_per_nodo"], d[(n2, p, s)]["B_per_nodo"])
                                for p in parts for s in semi]))
            v = []
            for _ in range(4000):
                ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
                nd = rng.integers(0, K, K)
                v.append(np.mean([wce(d[(NOME, p, s)]["A_per_nodo"], d[(NOME, p, s)]["B_per_nodo"], nd)
                                  - wce(d[(n2, p, s)]["A_per_nodo"], d[(n2, p, s)]["B_per_nodo"], nd)
                                  for p in ps for s in ss]))
            q = np.percentile(v, [2.5, 97.5])
            fuori[f"{c}/{NOME}-{n2}"] = {"media": m0, "ic_con_nodi": q.tolist(),
                                         "include_zero": bool(q[0] * q[1] <= 0)}
            print(f"  R-mon-eq - {n2:7s} {m0:+.5f} [{q[0]:+.5f}, {q[1]:+.5f}]"
                  + ("   include lo zero" if q[0] * q[1] <= 0 else ""))
    (out / "riselezione_rmon_test.json").write_text(json.dumps(
        {"confronti": fuori, "nota": "analisi aggiunta il 2/10, non pre-registrata; "
         "secondaria", "repliche": 4000, "seme_bootstrap": 20261003}, indent=2))
    print(f"\n  salvato in {out / 'riselezione_rmon_test.json'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--addestra", action="store_true")
    ap.add_argument("--valuta", action="store_true")
    ap.add_argument("--analizza", action="store_true")
    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    diverse, righe = celle_diverse(a.out)
    print("=" * 84)
    print(f"R-mon a PESO UGUALE — {len(diverse)} celle con punto diverso su {len(righe)}")
    print("=" * 84)
    if a.addestra:
        from evoluzione.componente.bracci import proprieta
        lo, hi = proprieta(BRACCIO).parete_attesa_min
        ctx = mp.get_context("spawn")
        t0 = time.time()
        with ctx.Pool(a.lavoratori) as pool:
            for i, r in enumerate(pool.imap_unordered(
                    _addestra, [(c, p, s, str(a.out), a.fili) for c, p, s, _, _ in diverse]), 1):
                print(f"  [{i:2d}/{len(diverse)}] {r['c']:11s} p{r['p']} s{r['s']} "
                      f"{r['esito']:10s} {r['secondi']/60:5.1f} min"
                      + (f"  scarto {r['scarto']:.0e}" if "scarto" in r else "")
                      + (f"\n      {r['errore']}" if r["esito"] == "fallita" else ""),
                      flush=True)
                if r["esito"] == "fallita":
                    pool.terminate(); return 1
                if r["esito"] == "completata" and not (lo <= r["secondi"] / 60 <= hi):
                    print(f"  **FERMO**: fuori dall'intervallo [{lo:g}, {hi:g}] min")
                    pool.terminate(); return 1
        print(f"\n  {(time.time() - t0) / 3600:.1f} ore di calendario")
    if a.valuta:
        valuta(a.out, diverse, righe)
    if a.analizza:
        analizza(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
