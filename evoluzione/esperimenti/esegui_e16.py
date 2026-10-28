#!/usr/bin/env python3
"""
E16 — calibrazione (protocol/E16.md). Due fasi.
================================================
    --fase predizioni   ricostruisce dai punti di controllo le PROBABILITA' per cella di C, F0, F0',
                        F'(1 sett.) [e A sul test] sull'episodio di validazione e di prova, citta' ep. 1
                        (36 celle) e PEMS08 (36 celle), con lo stesso `_modelli` di E8 e il controllo
                        BLOCCANTE: la wCE ricalcolata riproduce l'aggregato congelato (scarto <= 1e-6).
                        Statica della campagna (`--statica congelata`, obbligatoria: e' il Paper 1).
                        Scrive `predizioni_e16/<episodio>_<c>_p<p>_s<s>.npz` (prob float32).
    --fase analizza     per gruppo (citta', PEMS08) e braccio: diagrammi di affidabilita' per classe
                        (10 intervalli) ed ECE per classe; log-loss non pesata; Brier multiclasse; wCE.
                        Calibrazione post-hoc stimata SOLO sulla validazione della stessa cella, una per
                        braccio e cella: temperature scaling (T) e vector scaling (W diagonale + b), con
                        due obiettivi separati, log-loss naturale e wCE (posteriore ripesato); metriche e
                        differenze fra bracci prima e dopo (ricampionamento congiunto di E4); quota
                        s = 1 - (F0_cal - C_cal)/(F0 - C) per citta' con intervallo. A: nessun embedding
                        per i sensori di validazione (E8 la esclude dalla validazione): entra senza
                        calibrazione, dichiarato. Scrive `e16_risultati.json`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_e16.py --fase predizioni --statica congelata --lavoratori 16
    poetry run python evoluzione/esperimenti/esegui_e16.py --fase analizza
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

DIR_PRED = "predizioni_e16"
TOLLERANZA = 1e-6
MODELLI = {"prova": ("C", "A", "F0", "F0p", "Fp_672"), "validazione": ("C", "F0", "F0p", "Fp_672")}
CONTESTI = ("citta", "pems08")
N_BIN = 10
B_BOOT, SEME_BOOT = 4000, 20261023
CALIBRAZIONI = ("T_nll", "T_wce", "V_nll", "V_wce")


# ------------------------------------------------------------------ predizioni --
def _cella(args):
    nome_ctx, c, p, s, ep_nome, out, fili, dir_pred = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import _canali, _carica, _normalizzazione, _partizioni
    from evoluzione.esperimenti.esegui_e2 import valuta
    from evoluzione.esperimenti.esegui_e8 import CONTESTI_E8, FASCE_ETA, _modelli, _wce_per_oriz
    from evoluzione.esperimenti.inserimento import statica_cella, statiche, variante_statica
    out = Path(out)
    g = out / dir_pred / f"{ep_nome}_{c}_p{p}_s{s}.npz"
    if g.exists():
        return {"c": c, "p": p, "s": s, "ep": ep_nome, "esito": "presente", "secondi": 0}
    t_in = time.time()
    try:
        if variante_statica() != "congelata":
            raise RuntimeError("E16 ricostruisce la campagna del Paper 1: serve --statica congelata")
        ctx = CONTESTI_E8[nome_ctx](out)
        ctx = {**ctx, "modelli": {k: tuple(m for m in MODELLI[k] if m in ctx["modelli"][k]) for k in MODELLI}}
        D = _carica(c, out / "maschere"); ok = GR.passi_regolari(D["ts"])
        e = D["r"].shape[0] - GR.MAX_ORIZZ
        t0, t1, fine, chiave = ctx["calendario"](c, ep_nome)
        fine = e if fine is None else fine
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(ctx["seme_partizione"](p))}, ctx["fine_periodo"])
        nn = nodi[chiave]
        per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
        NORM, nr, nv = _normalizzazione(D, nodi, ist); x = _canali(D, nr, nv)
        stat = statica_cella(statiche(D), D, nodi, nn, t0, s)
        pesi = np.asarray(carica_pesi(out / ctx["dir_pesi"], c, p).vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32); S = torch.as_tensor(stat[nn])
        eta = per - t0
        fasce = [eta <= FASCE_ETA[0], (eta > FASCE_ETA[0]) & (eta <= FASCE_ETA[1]), eta > FASCE_ETA[1]]
        M, imp = _modelli(ctx, c, p, s, out, D, nodi, nn, ok, x, stat, w_t, t0, ep_nome)
        ris, controllo = {}, {}
        YY0 = MM0 = None
        for nome, m in M.items():
            PB, YY, MM, w, ph, dt = valuta(m, x, D["classe"], nn, per, S, pesi)
            if YY0 is None:
                YY0, MM0 = YY.astype("int8"), MM.astype(bool)
            # controllo BLOCCANTE contro l'aggregato congelato (come E8, controllo 1)
            cong = ctx["congelato"](c, p, s, ep_nome, nome)
            if cong is not None:
                f_c, kA, kB, somma = cong
                if not f_c.exists():
                    raise RuntimeError(f"controllo: manca l'aggregato congelato {f_c}")
                zc = np.load(f_c, allow_pickle=True)
                pr = np.clip(PB, 1e-12, 1.0)
                ce = -np.log(np.take_along_axis(pr, YY[..., None].astype("int64"), -1)[..., 0])
                wgt = pesi[YY.astype("int64")] * MM
                if somma == "fascia2":
                    sel = fasce[2]; A_mio, B_mio = (ce * wgt)[sel].sum(0), wgt[sel].sum(0); per_c = per[sel]
                else:
                    A_mio, B_mio, per_c = (ce * wgt).sum(0), wgt.sum(0), per
                if not (np.array_equal(zc["nodi"].astype("int64"), np.asarray(nn, dtype="int64"))
                        and np.array_equal(zc["origini"].astype("int64"), per_c)):
                    raise RuntimeError(f"controllo, {nome}: nodi od origini diversi da {f_c.name}")
                Ac, Bc = zc[kA], zc[kB]
                if somma is True:
                    Ac, Bc = Ac[:3].sum(0), Bc[:3].sum(0)
                rel = float(np.nanmax(np.abs(_wce_per_oriz(A_mio, B_mio) - _wce_per_oriz(Ac, Bc)) / np.maximum(np.abs(_wce_per_oriz(Ac, Bc)), 1e-12)))
                controllo[nome] = {"scarto_relativo_max": rel, "file": f_c.name}
                if rel > TOLLERANZA:
                    raise RuntimeError(f"controllo, {nome}: scarto relativo {rel:.2e} oltre {TOLLERANZA:g} ({f_c.name})")
            ris[f"prob_{nome}"] = PB.astype("float32")
            del PB
        g.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            g, nodi=np.asarray(nn, dtype="int32"), origini=per.astype("int32"), eta=eta.astype("int32"),
            y=YY0, m=MM0, pesi=pesi.astype("float64"), fasce=np.asarray([int(f.sum()) for f in fasce]),
            contesto=c, partizione=p, seme=s, episodio=ep_nome, gruppo=ctx["gruppo"](c), t0=t0, t1=t1, fine=fine,
            modelli=json.dumps(list(M)), impronte_ck=json.dumps(imp), controllo=json.dumps(controllo),
            statica=variante_statica(), macchina=__import__("platform").platform(), **ris)
        return {"c": c, "p": p, "s": s, "ep": ep_nome, "esito": "ok", "secondi": time.time() - t_in,
                "controlli": len(controllo), "scarto_max": max([v["scarto_relativo_max"] for v in controllo.values()] or [0.0])}
    except Exception as ex:                                  # noqa: BLE001
        return {"c": c, "p": p, "s": s, "ep": ep_nome, "esito": "fallita", "errore": f"{type(ex).__name__}: {ex}"[:300],
                "secondi": time.time() - t_in}


def fase_predizioni(out: Path, contesti, lavoratori, fili, piano, pilota, solo=None, dir_pred=DIR_PRED) -> int:
    from evoluzione.esperimenti.esegui_e8 import CONTESTI_E8
    celle = []
    for nome in contesti:
        ctx = CONTESTI_E8[nome](out)
        unita = ctx["unita"][:1] if pilota else ctx["unita"]
        for ep in ("validazione", "prova"):
            celle += [(nome, c, p, s, ep, str(out), fili, dir_pred) for (c, p, s) in unita]
    if solo:
        # `--solo episodio:contesto:partizione:seme ...`: le sole celle indicate (p.es. rifatte sulla
        # macchina degli aggregati congelati quando il controllo fra macchine supera la tolleranza)
        chiavi = {tuple(z.split(":")) for z in solo}
        celle = [x for x in celle if (x[4], x[1], str(x[2]), str(x[3])) in chiavi]
        print(f"  --solo: {len(celle)} celle su richiesta {sorted(chiavi)}")
    fatte = sum((out / dir_pred / f"{ep}_{c}_p{p}_s{s}.npz").exists() for _, c, p, s, ep, _, _, _ in celle)
    print(f"  {len(celle)} celle (contesti {contesti}, validazione + prova), {fatte} gia' fatte; modelli {MODELLI}; "
          f"controllo bloccante sugli aggregati congelati (<= {TOLLERANZA:g}); probabilita' float32")
    if piano:
        return 0
    ctx = mp.get_context("spawn"); t0 = time.time(); fall = 0; sc = 0.0
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_cella, celle), 1):
            if r["esito"] == "fallita":
                fall += 1
                print(f"  [{i:3d}/{len(celle)}] {r['ep']:11s} {r['c']:10s} p{r['p']} s{r['s']} FALLITA {r['errore']}", flush=True)
            elif r["esito"] == "ok":
                sc = max(sc, r["scarto_max"])
                print(f"  [{i:3d}/{len(celle)}] {r['ep']:11s} {r['c']:10s} p{r['p']} s{r['s']} ok  {r['controlli']} controlli, "
                      f"scarto max {r['scarto_max']:.1e}  {r['secondi']:4.0f}s", flush=True)
    print(f"\n  {len(celle) - fall} celle, {fall} fallite, scarto massimo {sc:.1e}, {(time.time() - t0)/60:.1f} min")
    return 0 if not fall else 1


# -------------------------------------------------------------------- analisi --
def _log_p(PB):
    import numpy as np
    return np.log(np.clip(PB, 1e-12, 1.0))


def _softmax(Z):
    import numpy as np
    Z = Z - Z.max(-1, keepdims=True); E = np.exp(Z)
    return E / E.sum(-1, keepdims=True)


def _nll(P, Y, M, w=None):
    """Media (pesata se w) di -log p_y sulle celle valide."""
    import numpy as np
    pr = np.clip(np.take_along_axis(P, Y[..., None].astype("int64"), -1)[..., 0], 1e-12, 1.0)
    ce = -np.log(pr)
    if w is None:
        return float(ce[M].mean())
    wg = w[Y.astype("int64")] * M
    return float((ce * wg).sum() / wg.sum())


def _calibra(logp, Y, M, w, tipo, obiettivo):
    """Parametri di calibrazione sulla validazione: T (scalare) o V (W diag 3 + b 3), minimizzando
    log-loss non pesata (`nll`) o wCE (`wce`, posteriore ripesato dai pesi di classe)."""
    import numpy as np
    from scipy.optimize import minimize
    lp = logp[M]; y = Y[M].astype("int64")
    pesi = None if obiettivo == "nll" else w
    wg = None if pesi is None else pesi[y]

    one = np.eye(3)[y]
    pw = (np.ones(len(y)) if wg is None else wg); pw = pw / pw.sum()

    def perdita(theta):
        # valore e gradiente analitico: Z = lp * a + b (a = exp(theta[:3]) oppure a = exp(-theta[0]) scalare, b = 0)
        if tipo == "T":
            a = np.exp(-theta[0]); Z = lp * a
        else:
            a = np.exp(theta[:3]); Z = lp * a + theta[3:]
        Z = Z - Z.max(-1, keepdims=True)
        ls = Z - np.log(np.exp(Z).sum(-1, keepdims=True))
        q = np.exp(ls)
        ce = -ls[np.arange(len(y)), y]
        dZ = (q - one) * pw[:, None]                            # dL/dZ, sommato sui campioni con i pesi
        if tipo == "T":
            g = np.array([-(dZ * lp * a).sum()])                # dZ/dtheta = -Z
        else:
            g = np.concatenate([(dZ * lp).sum(0) * a, dZ.sum(0)])
        return float((ce * pw).sum()), g
    x0 = np.zeros(1 if tipo == "T" else 6)
    r = minimize(perdita, x0, jac=True, method="L-BFGS-B")
    return r.x, float(r.fun)


def _applica(logp, theta, tipo):
    import numpy as np
    Z = logp * np.exp(-theta[0]) if tipo == "T" else logp * np.exp(theta[:3]) + theta[3:]
    return _softmax(Z)


def _metriche(P, Y, M, w):
    """ECE per classe (10 intervalli, affidabilita'), log-loss non pesata, Brier multiclasse, wCE."""
    import numpy as np
    Yf = Y[M].astype("int64"); Pf = P[M]
    one = np.eye(3)[Yf]
    out = {"logloss": _nll(P, Y, M), "wce": _nll(P, Y, M, w), "brier": float(((Pf - one) ** 2).sum(-1).mean()),
           "ece": {}, "affidabilita": {}}
    bordi = np.linspace(0, 1, N_BIN + 1)
    for k in range(3):
        pk = Pf[:, k]; yk = (Yf == k).astype("float64")
        idx = np.clip(np.digitize(pk, bordi[1:-1]), 0, N_BIN - 1)
        n = np.bincount(idx, minlength=N_BIN).astype("float64")
        conf = np.bincount(idx, weights=pk, minlength=N_BIN) / np.maximum(n, 1)
        acc = np.bincount(idx, weights=yk, minlength=N_BIN) / np.maximum(n, 1)
        out["ece"][str(k)] = float((n / n.sum() * np.abs(acc - conf)).sum())
        out["affidabilita"][str(k)] = {"n": n.astype(int).tolist(), "confidenza": conf.tolist(), "frequenza": acc.tolist()}
    return out


def _AB(P, Y, M, w):
    import numpy as np
    pr = np.clip(np.take_along_axis(P, Y[..., None].astype("int64"), -1)[..., 0], 1e-12, 1.0)
    ce = -np.log(pr); wg = w[Y.astype("int64")] * M
    return (ce * wg).sum(0), wg.sum(0)                       # (K,H)


def _wce_ab(A, B, idx=None):
    import numpy as np
    if idx is not None:
        A, B = A[idx], B[idx]
    num, den = A.sum(0), B.sum(0)
    return float(np.nanmean(np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)))


def _boot_vec(celle, f_vec, rng):
    import numpy as np
    kk = sorted(celle); parts = sorted({k[1] for k in kk}); semi = sorted({k[2] for k in kk})
    K = celle[kk[0]]["K"]
    m0 = np.mean([f_vec(celle[k], None) for k in kk], axis=0); rep = np.empty((B_BOOT, len(m0)))
    for b in range(B_BOOT):
        ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True); nd = rng.integers(0, K, K)
        rep[b] = np.mean([f_vec(celle[(kk[0][0], p, s)], nd) for p in ps for s in ss], axis=0)
    return m0, rep


def fase_analizza(out: Path) -> int:
    import numpy as np
    rng = np.random.default_rng(SEME_BOOT)
    file_v = sorted((out / DIR_PRED).glob("validazione_*_p*_s*.npz"))
    R = {"modelli": MODELLI, "calibrazioni": CALIBRAZIONI, "bin": N_BIN, "repliche": B_BOOT, "seme_bootstrap": SEME_BOOT,
         "nota_A": "A non ha embedding per i sensori di validazione (E8 la esclude dalla validazione): senza calibrazione post-hoc",
         "per_cella": {}, "gruppi": {}}
    celle_gr = {}
    print(f"  {len(file_v)} celle di validazione; per ciascuna: parametri di T e V (obiettivi nll e wce) per braccio, poi il test")
    for fv in file_v:
        zv = np.load(fv, allow_pickle=True)
        c, p, s = str(zv["contesto"]), int(zv["partizione"]), int(zv["seme"]); gr = str(zv["gruppo"])
        fp = out / DIR_PRED / f"prova_{c}_p{p}_s{s}.npz"
        if not fp.exists():
            raise RuntimeError(f"manca {fp}")
        zp = np.load(fp, allow_pickle=True)
        w = zp["pesi"].astype("float64"); Yp, Mp = zp["y"], zp["m"].astype(bool); Yv, Mv = zv["y"], zv["m"].astype(bool)
        cella = {"K": int(len(zp["nodi"])), "A": {}, "B": {}}
        voce = {"gruppo": gr, "parametri": {}, "test": {}, "validazione": {}}
        for nome in json.loads(str(zp["modelli"])):
            Pp = zp[f"prob_{nome}"].astype("float64"); lpp = _log_p(Pp)
            voce["test"][f"{nome}/grezzo"] = _metriche(Pp, Yp, Mp, w)
            cella["A"][f"{nome}/grezzo"], cella["B"][f"{nome}/grezzo"] = _AB(Pp, Yp, Mp, w)
            if f"prob_{nome}" in zv.files:
                Pv = zv[f"prob_{nome}"].astype("float64"); lpv = _log_p(Pv)
                voce["validazione"][f"{nome}/grezzo"] = {k_: v_ for k_, v_ in _metriche(Pv, Yv, Mv, w).items() if k_ != "affidabilita"}
                for cal in CALIBRAZIONI:
                    tipo, ob = cal.split("_")
                    theta, fun = _calibra(lpv, Yv, Mv, w, tipo, ob)
                    voce["parametri"][f"{nome}/{cal}"] = {"theta": theta.tolist(), "perdita_validazione": fun,
                                                          **({"T": float(np.exp(theta[0]))} if tipo == "T" else {})}
                    Pc = _applica(lpp, theta, tipo)
                    voce["test"][f"{nome}/{cal}"] = _metriche(Pc, Yp, Mp, w)
                    cella["A"][f"{nome}/{cal}"], cella["B"][f"{nome}/{cal}"] = _AB(Pc, Yp, Mp, w)
        R["per_cella"][f"{gr}/{c}/p{p}/s{s}"] = voce
        celle_gr.setdefault(gr, {})[(gr, p, s)] = cella
        print(f"    {gr:10s} {c:10s} p{p} s{s}: " + " ".join(
            f"{n}:T_nll={voce['parametri'][f'{n}/T_nll']['T']:.2f}" for n in ("C", "F0", "F0p", "Fp_672") if f"{n}/T_nll" in voce["parametri"]), flush=True)
    # ---- per gruppo: livelli e differenze con ricampionamento; quota s ----
    for gr, celle in celle_gr.items():
        chiavi = sorted(next(iter(celle.values()))["A"])
        def f(z, idx, _ch=chiavi):
            return np.array([_wce_ab(z["A"][k], z["B"][k], idx) for k in _ch])
        m0, rep = _boot_vec(celle, f, rng)
        ic = lambda v: [float(q) for q in np.nanpercentile(v, [2.5, 97.5])]
        G = {"celle": len(celle), "wce": {k: {"media": float(m0[i]), "ic_con_nodi": ic(rep[:, i])} for i, k in enumerate(chiavi)},
             "differenze": {}, "quota_calibrazione": {}, "medie_test": {}}
        pos = {k: i for i, k in enumerate(chiavi)}
        for var in ("grezzo",) + CALIBRAZIONI:
            for n1, n2 in (("F0", "C"), ("F0p", "C"), ("Fp_672", "C"), ("A", "C"), ("F0p", "F0")):
                k1, k2 = f"{n1}/{var}", f"{n2}/{var}"
                if n1 == "A" and var != "grezzo":
                    k1 = "A/grezzo"                            # A resta grezza, dichiarato
                if k1 in pos and k2 in pos:
                    d0 = m0[pos[k1]] - m0[pos[k2]]; dr = rep[:, pos[k1]] - rep[:, pos[k2]]
                    G["differenze"][f"{n1}-{n2}/{var}"] = {"media": float(d0), "ic_con_nodi": ic(dr),
                                                           "segno": "-" if ic(dr)[1] < 0 else ("+" if ic(dr)[0] > 0 else "0")}
        for cal in CALIBRAZIONI:
            if f"F0/{cal}" in pos:
                num = (rep[:, pos[f"F0/{cal}"]] - rep[:, pos[f"C/{cal}"]]); den = (rep[:, pos["F0/grezzo"]] - rep[:, pos["C/grezzo"]])
                s0 = 1 - (m0[pos[f"F0/{cal}"]] - m0[pos[f"C/{cal}"]]) / (m0[pos["F0/grezzo"]] - m0[pos["C/grezzo"]])
                G["quota_calibrazione"][cal] = {"media": float(s0), "ic_con_nodi": ic(1 - num / den),
                                                "definizione": "s = 1 - (F0_cal - C_cal)/(F0 - C)", "limite_inferiore_sopra_0.5": bool(ic(1 - num / den)[0] > 0.5)}
        # medie sul test delle metriche per cella (ECE per classe, log-loss, Brier)
        voci = [v for k, v in R["per_cella"].items() if v["gruppo"] == gr]
        for k in chiavi:
            mm = [v["test"][k] for v in voci if k in v["test"]]
            G["medie_test"][k] = {"logloss": float(np.mean([m["logloss"] for m in mm])), "brier": float(np.mean([m["brier"] for m in mm])),
                                  "wce": float(np.mean([m["wce"] for m in mm])),
                                  "ece": {str(kk): float(np.mean([m["ece"][str(kk)] for m in mm])) for kk in range(3)}}
        R["gruppi"][gr] = G
        print(f"\n  {gr}: " + "; ".join(f"s({cal}) = {q['media']:.3f} [{q['ic_con_nodi'][0]:.3f}, {q['ic_con_nodi'][1]:.3f}]"
                                       for cal, q in G["quota_calibrazione"].items()))
    R["istante"] = datetime.now(timezone.utc).isoformat()
    f = out / "e16_risultati.json"
    f.write_text(json.dumps(R, indent=1, ensure_ascii=False))
    print(f"  salvato in {f} (impronta {hashlib.sha256(f.read_bytes()).hexdigest()[:16]})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fase", choices=("predizioni", "analizza"), required=True)
    # E18 (A.6): `pems04` ammesso ma NON predefinito, con `--dir-pred` propria: E16 resta com'e'
    ap.add_argument("--contesto", nargs="*", choices=CONTESTI + ("pems04",), default=list(CONTESTI))
    ap.add_argument("--dir-pred", default=DIR_PRED, help="cartella d'uscita della fase predizioni (E18: predizioni_e18_pems04)")
    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--pilota", action="store_true")
    ap.add_argument("--solo", nargs="*", default=None, help="episodio:contesto:partizione:seme ...")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    from evoluzione.esperimenti.inserimento import applica_statica, argomento_statica
    argomento_statica(ap)
    a = ap.parse_args()
    applica_statica(a.statica)
    print("=" * 84); print(f"E16 — fase {a.fase}"); print("=" * 84)
    if a.fase == "predizioni":
        return fase_predizioni(a.out, a.contesto, a.lavoratori, a.fili, a.piano, a.pilota, a.solo, a.dir_pred)
    return fase_analizza(a.out)


if __name__ == "__main__":
    raise SystemExit(main())
