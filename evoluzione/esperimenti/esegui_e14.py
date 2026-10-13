#!/usr/bin/env python3
"""
E14 — stadio A: sensibilita' delle dichiarazioni primarie alla statica non causale.
=====================================================================================
Pre-registrazione: `protocol/E14.md` (12/10 19:00, emendamento 20:20). Nessun riaddestramento.

Celle: episodio 1 delle tre citta' (3 partizioni x 12 semi) e PEMS08 (6 partizioni x 6 semi),
cioe' le stesse unita' di E8. Bracci: C, A, F₀, F₀′, F′(1 sett.) (adattamento rifatto con la
statica della variante, stesso budget e seme), R-orig(1 sett.), dai checkpoint congelati e con
la macchina di E8 (`_modelli`, `valuta`). Per ogni cella si salva A/B per nodo e per fascia d'eta'
(`AF_`, `BF_`), come in E8.

Varianti del vettore statico (una scalare per nodo; le altre quattro componenti costanti):
    nc   non causale: `inserimento.statiche` — SOLO per il controllo 1 (10 celle): deve riprodurre
         gli aggregati di `predizioni_e8/prova_*` a scarto zero (stessa pipeline)
    a    nodi nuovi: media di m_r su (t0, t0 + 24 h]; iniziali: media su [0, t0)
    b    nodi nuovi: media delle coperture causali degli iniziali su [0, t0); iniziali: idem (a)
    c    nodi nuovi: coperture non causali permutate fra i nodi nuovi della cella
         (seme della permutazione = seme della cella); iniziali: non causale
Solo i nodi di prova entrano nella valutazione e nell'adattamento di F′: la statica degli
iniziali non e' consumata nello stadio A (serve solo in addestramento, che non si rifa').

Riferimento «non causale» dello stadio A: gli aggregati per cella di `predizioni_e8/prova_*`
(verificati in E8 contro E2/E4/E6 entro 1e-6). Test: per ciascun confronto pre-registrato
(F₀−C, F₀′−C, F′(1 sett.)−C, F′(1 sett.)−A, R-orig(1 sett.)−F′(1 sett.), A−C) e per la wCE
assoluta di C e di A: media e intervallo (ricampionamento congiunto partizioni x semi x nodi,
`esegui_e4.B_BOOT` repliche, semi di E8) con la statica non causale e con ciascuna variante;
Δ fra i due; verdetto «insensibile» se |Δ| < 0,002 wCE e il segno dell'intervallo e' conservato.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_e14.py --fase celle --piano
    poetry run python evoluzione/esperimenti/esegui_e14.py --fase celle --lavoratori 16
    poetry run python evoluzione/esperimenti/esegui_e14.py --fase test
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
from evoluzione.esperimenti.esegui_e4 import B_BOOT, FASCE_ETA, _boot, _wce  # noqa: E402
from evoluzione.esperimenti.esegui_e8 import CONTESTI_E8, _modelli  # noqa: E402

DIR_PRED = "predizioni_e14"
DIR_E8 = "predizioni_e8"
VARIANTI = ("a", "b", "c")
MODELLI = ("C", "A", "F0", "F0p", "Fp_672", "Rorig_672")
CONTESTI = ("citta", "pems08")
L24, SETTIMANA = 96, 672
N_CONTROLLO = 10
# controllo 1: sulla STESSA macchina di E8 (Mac) lo scarto atteso e' zero; su un'altra
# architettura il forward in float32 diverge (voce 22): la soglia di arresto e' quella di E8,
# e lo scarto osservato si registra per cella e si riporta nel congelamento
TOLLERANZA_CONTROLLO = 1e-6
SOGLIA_DELTA = 0.002
CONF = {"F0-C": ("F0", "C", None), "F0p-C": ("F0p", "C", None),
        "Fp_672-C_eta>1sett": ("Fp_672", "C", 2), "Fp_672-A_eta>1sett": ("Fp_672", "A", 2),
        "Rorig_672-Fp_672_eta>1sett": ("Rorig_672", "Fp_672", 2), "A-C": ("A", "C", None)}
ASSOLUTE = {"wCE_C": ("C", None), "wCE_A": ("A", None)}


def statica_variante(D, nodi, nn, t0, variante, seme):
    """Il vettore statico (K, 5) della variante; la prima colonna e' la copertura."""
    import numpy as np
    from evoluzione.esperimenti.inserimento import statiche
    stat = statiche(D).copy()
    if variante == "nc":
        return stat, {"variante": "nc"}
    m = D["m_r"].astype("float64")
    cov_nc = stat[:, 0].astype("float64")
    cov_c_ini = m[:t0].mean(0)
    stat[:, 0] = cov_c_ini.astype("float32")                     # iniziali (e tutti): causale [0, t0)
    ini = nodi["addestramento"]
    if variante == "a":
        stat[nn, 0] = m[t0 + 1:t0 + L24 + 1, :].mean(0)[nn].astype("float32")
    elif variante == "b":
        stat[nn, 0] = np.float32(cov_c_ini[ini].mean())
    elif variante == "c":
        stat[:, 0] = cov_nc.astype("float32")                     # iniziali: non causale
        rng = np.random.default_rng(int(seme))
        stat[nn, 0] = cov_nc[nn][rng.permutation(len(nn))].astype("float32")
    else:
        raise ValueError(variante)
    return stat, {"variante": variante, "copertura_nuovi_media": float(stat[nn, 0].mean()),
                  "copertura_nuovi_nc_media": float(cov_nc[nn].mean())}


def _cella(args):
    nome_ctx, c, p, s, variante, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.analizza_copertura_e4 import celle_valide
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import _canali, _carica, _normalizzazione, _partizioni
    from evoluzione.esperimenti.esegui_e2 import valuta
    out = Path(out)
    g = out / DIR_PRED / variante / f"prova_{c}_p{p}_s{s}.npz"
    if g.exists():
        return {"c": c, "p": p, "s": s, "variante": variante, "esito": "presente", "secondi": 0}
    t_in = time.time()
    try:
        ctx = CONTESTI_E8[nome_ctx](out)
        ctx["modelli"] = {"prova": MODELLI}
        D = _carica(c, out / "maschere"); ok = GR.passi_regolari(D["ts"])
        e = D["r"].shape[0] - GR.MAX_ORIZZ
        t0, t1, fine, chiave = ctx["calendario"](c, "prova")
        fine = e if fine is None else fine
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(ctx["seme_partizione"](p))}, ctx["fine_periodo"])
        nn = nodi[chiave]
        per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
        NORM, nr, nv = _normalizzazione(D, nodi, ist); x = _canali(D, nr, nv)
        stat, info = statica_variante(D, nodi, nn, t0, variante, s)
        pesi = np.asarray(carica_pesi(out / ctx["dir_pesi"], c, p).vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32); S = torch.as_tensor(stat[nn])
        eta = per - t0
        fasce = [eta <= FASCE_ETA[0], (eta > FASCE_ETA[0]) & (eta <= FASCE_ETA[1]), eta > FASCE_ETA[1]]
        cv, _ = celle_valide(D, nn, GR.origini_acquisizione(ok, t0, t1), t0, t1)
        M, imp = _modelli(ctx, c, p, s, out, D, nodi, nn, ok, x, stat, w_t, t0, "prova")
        ris, controllo = {}, {}
        z8 = np.load(out / DIR_E8 / f"prova_{c}_p{p}_s{s}.npz", allow_pickle=True)
        if not (np.array_equal(z8["nodi"].astype("int64"), np.asarray(nn, dtype="int64"))
                and np.array_equal(z8["origini"].astype("int64"), per)):
            raise RuntimeError("nodi od origini diversi da predizioni_e8")
        for nome, m in M.items():
            PB, YY, MM, w, ph, dt = valuta(m, x, D["classe"], nn, per, S, pesi)
            pr = np.clip(PB, 1e-12, 1.0)
            ce = -np.log(np.take_along_axis(pr, YY[..., None].astype("int64"), -1)[..., 0])
            wgt = pesi[YY.astype("int64")] * MM
            ris[f"A_{nome}"] = (ce * wgt).sum(0).astype("float64"); ris[f"B_{nome}"] = wgt.sum(0).astype("float64")
            ris[f"AF_{nome}"] = np.stack([(ce * wgt)[fm].sum(0) for fm in fasce]).astype("float64")
            ris[f"BF_{nome}"] = np.stack([wgt[fm].sum(0) for fm in fasce]).astype("float64")
            # scarto dalla stessa cella di E8 (statica non causale): per il controllo 1 deve essere zero
            mio = _wce(ris[f"AF_{nome}"].sum(0), ris[f"BF_{nome}"].sum(0))
            loro = _wce(z8[f"AF_{nome}"].sum(0), z8[f"BF_{nome}"].sum(0))
            controllo[nome] = {"wce": float(mio), "wce_e8": float(loro),
                               "scarto_relativo": float(abs(mio - loro) / max(abs(loro), 1e-12))}
            if variante == "nc" and controllo[nome]["scarto_relativo"] > TOLLERANZA_CONTROLLO:
                raise RuntimeError(f"controllo 1, {nome}: wCE {mio:.9f} contro E8 {loro:.9f} "
                                   f"(scarto {controllo[nome]['scarto_relativo']:.1e} oltre {TOLLERANZA_CONTROLLO:g})")
            del PB, YY, MM
        g.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            g, nodi=np.asarray(nn, dtype="int32"), origini=per.astype("int32"), eta=eta.astype("int32"),
            celle_valide=cv.astype("int32"), fasce=np.asarray([int(f.sum()) for f in fasce]),
            contesto=c, partizione=p, seme=s, episodio="prova", gruppo=ctx["gruppo"](c), t0=t0, t1=t1, fine=fine,
            variante=variante, statica_nuovi=stat[nn, 0].astype("float32"), info=json.dumps(info),
            modelli=json.dumps(list(M)), impronte_ck=json.dumps(imp), controllo=json.dumps(controllo), **ris)
        return {"c": c, "p": p, "s": s, "variante": variante, "esito": "ok", "secondi": time.time() - t_in,
                "scarto_max_da_e8": max(v["scarto_relativo"] for v in controllo.values())}
    except Exception as ex:                                  # noqa: BLE001
        return {"c": c, "p": p, "s": s, "variante": variante, "esito": "fallita",
                "errore": f"{type(ex).__name__}: {ex}"[:300], "secondi": time.time() - t_in}


def _lavori(out: Path, varianti):
    lav = []
    for nome in CONTESTI:
        ctx = CONTESTI_E8[nome](out)
        unita = list(ctx["unita"])
        for v in varianti:
            if v == "nc":
                # controllo 1, 10 celle pre-registrate: partizione 0, semi 201-203 nelle tre citta' (9) e
                # la prima cella di PEMS08 (1)
                celle = ([u for u in unita if u[1] == 0 and u[2] in (201, 202, 203)] if nome == "citta"
                         else [u for u in unita if u[1] == 0][:1])
            else:
                celle = unita
            lav += [(nome, c, p, s, v, str(out), 1) for (c, p, s) in celle]
    return lav


def fase_celle(out: Path, lavoratori: int, fili: int, piano: bool, varianti, pilota: bool = False) -> int:
    lav = [(n, c, p, s, v, o, fili) for (n, c, p, s, v, o, _) in _lavori(out, varianti)]
    fatte = [x for x in lav if (out / DIR_PRED / x[4] / f"prova_{x[1]}_p{x[2]}_s{x[3]}.npz").exists()]
    da_fare = [x for x in lav if x not in fatte]
    if pilota:
        da_fare = da_fare[:1]; lavoratori = 1
        print("  PILOTA: una sola cella-variante, un processo")
    print(f"  varianti {list(varianti)}: {len(lav)} cella-varianti ({len(fatte)} presenti, {len(da_fare)} da fare); "
          f"{lavoratori} processi x {fili} filo; modelli {MODELLI}")
    for v in varianti:
        print(f"    {v}: {sum(1 for x in lav if x[4] == v)} celle")
    if piano:
        return 0
    ctx = mp.get_context("spawn"); esiti = []; t_in = time.time()
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_cella, da_fare), 1):
            esiti.append(r); tr = time.time() - t_in
            print(f"  [{i:3d}/{len(da_fare)}] {r['variante']:2s} {r['c']:10s} p{r['p']} s{r['s']} {r['esito']:8s} "
                  f"{r['secondi']:6.0f} s  scarto da E8 {r.get('scarto_max_da_e8', float('nan')):.1e} | "
                  f"{tr/3600:4.1f} h, restano ~{tr/i*(len(da_fare)-i)/3600:4.1f} h"
                  + (f"\n        {r['errore']}" if r["esito"] == "fallita" else ""), flush=True)
    fallite = [r for r in esiti if r["esito"] == "fallita"]
    (out / f"esito_e14_celle.json").write_text(json.dumps(
        {"varianti": list(varianti), "completate": len(esiti) - len(fallite), "fallite": fallite,
         "presenti_prima": len(fatte), "lavoratori": lavoratori, "ore_calendario": (time.time() - t_in) / 3600,
         "istante": datetime.now(timezone.utc).isoformat()}, indent=2))
    print(f"\n  {len(esiti) - len(fallite)} completate, {len(fallite)} fallite, {(time.time() - t_in) / 3600:.2f} h")
    return 0 if not fallite else 1


def _carica(out: Path, cartella: Path, unita, gruppo):
    import numpy as np
    cc = {}
    for (c, p, s) in unita:
        with np.load(cartella / f"prova_{c}_p{p}_s{s}.npz", allow_pickle=True) as z:
            cc[(gruppo(c), p, s)] = {k: z[k] for k in z.files}
    return cc


def _wce_di(z, n, fascia, idx):
    A, Bm = z[f"AF_{n}"], z[f"BF_{n}"]
    A = A.sum(0) if fascia is None else A[fascia]; Bm = Bm.sum(0) if fascia is None else Bm[fascia]
    return (A, Bm) if idx is None else (A[idx], Bm[idx])


def _segno(r):
    lo, hi = r["ic_con_nodi"]
    return "-" if hi < 0 else ("+" if lo > 0 else "0")


def fase_test(out: Path) -> dict:
    import numpy as np
    R = {"repliche": B_BOOT, "soglia_delta": SOGLIA_DELTA, "varianti": list(VARIANTI), "gruppi": {}}
    for nome in CONTESTI:
        ctx = CONTESTI_E8[nome](out)
        for gr in sorted({ctx["gruppo"](c) for (c, _, _) in ctx["unita"]}):
            unita = [u for u in ctx["unita"] if ctx["gruppo"](u[0]) == gr]
            cc_nc = _carica(out, out / DIR_E8, unita, ctx["gruppo"])
            RG = {"celle": len(unita), "confronti": {}, "assolute": {}, "controllo_1": {}}
            # controllo 1: celle «nc» dello stadio A contro E8
            for (c, p, s) in unita:
                f = out / DIR_PRED / "nc" / f"prova_{c}_p{p}_s{s}.npz"
                if f.exists():
                    with np.load(f, allow_pickle=True) as z:
                        RG["controllo_1"][f"{c}_p{p}_s{s}"] = max(v["scarto_relativo"] for v in json.loads(str(z["controllo"])).values())
            print(f"\n{gr}: {len(unita)} celle; controllo 1 su {len(RG['controllo_1'])} celle, scarto massimo "
                  f"{max(RG['controllo_1'].values()) if RG['controllo_1'] else float('nan'):.1e}")
            celle_v = {v: _carica(out, out / DIR_PRED / v, unita, ctx["gruppo"]) for v in VARIANTI}
            for nome_c, (n1, n2, fascia) in CONF.items():
                f = lambda z, idx, _a=n1, _b=n2, _f=fascia: _wce(*_wce_di(z, _a, _f, idx)) - _wce(*_wce_di(z, _b, _f, idx))  # noqa: E731
                r_nc = _boot(cc_nc, f, np.random.default_rng(ctx["seme_boot"])); r_nc["segno"] = _segno(r_nc)
                riga = {"nc": r_nc}
                for v in VARIANTI:
                    r = _boot(celle_v[v], f, np.random.default_rng(ctx["seme_boot"])); r["segno"] = _segno(r)
                    r["delta_da_nc"] = r["media"] - r_nc["media"]
                    r["insensibile"] = bool(abs(r["delta_da_nc"]) < SOGLIA_DELTA and r["segno"] == r_nc["segno"])
                    riga[v] = r
                RG["confronti"][nome_c] = riga
                print(f"  {nome_c:28s} nc {r_nc['media']:+.4f} [{r_nc['ic_con_nodi'][0]:+.4f}, {r_nc['ic_con_nodi'][1]:+.4f}] {r_nc['segno']} | "
                      + " | ".join(f"{v} {riga[v]['media']:+.4f} Δ{riga[v]['delta_da_nc']:+.4f} {riga[v]['segno']} "
                                   f"{'ins' if riga[v]['insensibile'] else 'SENS'}" for v in VARIANTI), flush=True)
            for nome_a, (n1, fascia) in ASSOLUTE.items():
                f = lambda z, idx, _a=n1, _f=fascia: _wce(*_wce_di(z, _a, _f, idx))  # noqa: E731
                r_nc = _boot(cc_nc, f, np.random.default_rng(ctx["seme_boot"]))
                riga = {"nc": r_nc}
                for v in VARIANTI:
                    r = _boot(celle_v[v], f, np.random.default_rng(ctx["seme_boot"])); r["delta_da_nc"] = r["media"] - r_nc["media"]
                    riga[v] = r
                RG["assolute"][nome_a] = riga
                print(f"  {nome_a:28s} nc {r_nc['media']:.4f} | " + " | ".join(f"{v} {riga[v]['media']:.4f} Δ{riga[v]['delta_da_nc']:+.4f}" for v in VARIANTI))
            RG["tutte_insensibili"] = {v: all(RG["confronti"][k][v]["insensibile"] for k in CONF) for v in VARIANTI}
            R["gruppi"][gr] = RG
    R["verdetto"] = {v: all(RG["tutte_insensibili"][v] for RG in R["gruppi"].values()) for v in VARIANTI}
    R["istante"] = datetime.now(timezone.utc).isoformat()
    (out / "e14_risultati.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print("\n  tutte e sei insensibili in tutti i contesti: " + ", ".join(f"({v}) {'si' if R['verdetto'][v] else 'NO'}" for v in VARIANTI))
    print(f"  salvato in {out / 'e14_risultati.json'}")
    return R


def main() -> int:
    ap = argparse.ArgumentParser(description="E14 stadio A")
    ap.add_argument("--fase", choices=("celle", "test"), required=True)
    ap.add_argument("--varianti", nargs="*", default=["nc", *VARIANTI], help="nc = controllo 1 (10 celle)")
    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--pilota", action="store_true", help="una sola cella-variante, un processo")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    print("=" * 84); print(f"E14 — stadio A, fase {a.fase}"); print("=" * 84)
    if a.fase == "celle":
        return fase_celle(a.out, a.lavoratori, a.fili, a.piano, tuple(a.varianti), a.pilota)
    fase_test(a.out); return 0


if __name__ == "__main__":
    raise SystemExit(main())
