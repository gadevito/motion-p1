#!/usr/bin/env python3
"""
E18-quater — C_A ri-valutato sui sensori nuovi con la coverage espandente (richiesta del revisore, 3/11/2026).
=============================================================================================================
In E15 (`esegui_e15._episodio`) A e C_A ricevono, in valutazione, la coverage dei sensori nuovi calcolata su
[0, t0) come per gli iniziali (`nodi_davvero_nuovi`: corpus privilegiato), mentre C, F0, F0', F' ricevono la
finestra espansiva da t0. La differenza C_A - C mescola quindi due cose: la storia anteriore a t0 dei sensori
nuovi nell'ADDESTRAMENTO (i dati) e la coverage di VALUTAZIONE ([0, t0) contro espansiva). Qui, a modelli
congelati e senza riaddestrare, si ri-valuta il solo C_A con la STESSA statica che vede C (la finestra
espansiva di E15, `OR3_STATICA` assente; `_contesto_cella` rifiuta ogni altra variante):

    C_A_esp - C_A     effetto della coverage (stesso modello, due coverage)
    C_A_esp - C       effetto dei dati a pari coverage
    A - C_A_esp       valore dell'identita' a pari coverage

Celle, nodi di prova, origini, pesi, fasce d'eta', ricampionamento (partizioni x semi x posizioni dei nodi,
4.000 repliche, stesso seme di E15) sono quelli di E15; le celle di E15 (`predizioni_e15/prova_*.npz`) sono
l'ingresso e il riferimento. Controlli bloccanti: stessi nodi e stesse origini della cella E15; la
ri-valutazione di C_A con la statica di E15 riproduce bit per bit gli aggregati salvati da E15 (stessa
pipeline); le medie di A - C, A - C_A, C_A - C ricalcolate qui coincidono con `e15_risultati.json`.

    poetry run python evoluzione/esperimenti/esegui_e18quater.py --fase valuta --lavoratori 16
    poetry run python evoluzione/esperimenti/esegui_e18quater.py --fase analizza
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

from evoluzione.esperimenti.esegui_e15 import (  # noqa: E402
    B_BOOT, CITTA, DELTA_NI, DIR_PRED, FASCE_ETA, SEME_BOOT, STATICA_E15, _ab, _aggregati, _boot_vec, _carica, _ic,
    _valuta_origini, _wce, categoria, celle, ck_di, segno, semi_torch_di, _contesto_cella)

DIR_Q = "predizioni_e18quater"
BRACCIO = "C_A"


def _sha(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def _cella(args):
    c, p, s, out, fili = args
    import numpy as np
    out = Path(out)
    g = out / DIR_Q / f"prova_{c}_p{p}_s{s}.npz"
    if g.exists():
        return {"c": c, "p": p, "s": s, "esito": "presente", "secondi": 0}
    t_in = time.time()
    try:
        from evoluzione.componente import griglia as GR
        from evoluzione.componente.predittore import ORIZZONTI
        from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
        from evoluzione.esperimenti.inserimento import (
            StaticaEspansiva, _modello_da_ck, nodi_davvero_nuovi, statica_cella, statiche, variante_statica)
        K = _contesto_cella(c, p, s, out, fili)
        D, ok, nodi, x, pesi, st = (K[k] for k in ("D", "ok", "nodi", "x", "pesi", "st"))
        t0, t1 = CALENDARIO[c]
        fine = D["r"].shape[0] - max(ORIZZONTI)
        nn = nodi["prova"]
        per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
        f15 = out / DIR_PRED / f"prova_{c}_p{p}_s{s}.npz"
        with np.load(f15, allow_pickle=True) as z:
            z15 = {q: z[q] for q in ("nodi", "origini", "A_C_A", "B_C_A", "t0", "t1", "statica")}
        if not (np.array_equal(z15["nodi"].astype("int64"), np.asarray(nn, dtype="int64"))
                and np.array_equal(z15["origini"].astype("int64"), per)):
            raise RuntimeError("nodi od origini diversi dalla cella E15")
        if int(z15["t0"]) != t0 or int(z15["t1"]) != t1 or str(z15["statica"]) != STATICA_E15:
            raise RuntimeError("t0, t1 o statica della cella E15 diversi da quelli attesi")
        stat_ini = statica_cella(statiche(D), D, nodi, nodi_davvero_nuovi(BRACCIO, nn), t0, s)   # E15: [0, t0)
        stat_nuovi = statica_cella(statiche(D), D, nodi, nn, t0, s)                             # come C
        if variante_statica() == "espansiva" and not isinstance(stat_nuovi, StaticaEspansiva):
            raise RuntimeError("la statica dei nuovi non e' espansiva")
        if np.array_equal(np.asarray(stat_nuovi)[nn, 0], np.asarray(stat_ini)[nn, 0]):
            raise RuntimeError("statica dei nuovi uguale a quella degli iniziali: la finestra non e' applicata")
        ck = ck_di(BRACCIO, c, p, s, out, st)
        m_, d_ = _modello_da_ck(ck, D, nodi, None)
        nn_set = set(int(z) for z in nn)
        if not nn_set <= set(int(z) for z in d_["nodi_iniziali"]):
            raise RuntimeError(f"{BRACCIO}: deve contenere i nodi nuovi")
        if d_.get("training_protocol") != "principale":
            raise RuntimeError(f"{BRACCIO}: protocollo {d_.get('training_protocol')}")
        eta = per - t0
        fasce = [eta <= FASCE_ETA[0], (eta > FASCE_ETA[0]) & (eta <= FASCE_ETA[1]), eta > FASCE_ETA[1]]
        # controllo: con la statica di E15 gli aggregati sono quelli salvati da E15, bit per bit
        PB, YY, MM, w0 = _valuta_origini(m_, x, D["classe"], nn, per, stat_ini, pesi)
        A0, B0 = _aggregati(PB, YY, MM, pesi, fasce)
        if not (np.array_equal(A0, z15["A_C_A"]) and np.array_equal(B0, z15["B_C_A"])):
            raise RuntimeError("controllo: la ri-valutazione di C_A con la statica di E15 non riproduce gli aggregati di E15")
        # la valutazione nuova: stesso modello, coverage dei nuovi come per C
        PB, YY, MM, w1 = _valuta_origini(m_, x, D["classe"], nn, per, stat_nuovi, pesi)
        A1, B1 = _aggregati(PB, YY, MM, pesi, fasce)
        g.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            g, contesto=c, partizione=p, seme=s, statica=variante_statica(), braccio=BRACCIO,
            nodi=np.asarray(nn, dtype="int32"), origini=per.astype("int32"), eta=eta.astype("int32"),
            fasce=np.asarray([int(f.sum()) for f in fasce]), t0=t0, t1=t1, fine=fine,
            impronta_ck=_sha(ck), impronta_cella_e15=_sha(f15), impronta_pesi=K["P_"].impronta,
            controllo="aggregati di C_A con la statica di E15 identici a quelli salvati da E15",
            A_C_A_esp=A1, B_C_A_esp=B1, wce_C_A_esp=w1, wce_C_A_controllo=w0)
        return {"c": c, "p": p, "s": s, "esito": "ok", "secondi": time.time() - t_in,
                "wce": {"C_A": round(float(w0), 5), "C_A_esp": round(float(w1), 5)}}
    except Exception as e:                                   # noqa: BLE001
        return {"c": c, "p": p, "s": s, "esito": "fallita", "errore": f"{type(e).__name__}: {e}"[:300],
                "secondi": time.time() - t_in}


def fase_valuta(out: Path, lavoratori: int, fili: int) -> int:
    from evoluzione.esperimenti.inserimento import variante_statica
    print("=" * 84)
    print(f"E18-quater — C_A ri-valutato con la coverage dei nuovi come C ({len(celle())} celle), statica «{variante_statica()}»")
    print("=" * 84)
    mancanti = [k for k in celle() if not (out / DIR_PRED / f"prova_{k[0]}_p{k[1]}_s{k[2]}.npz").exists()]
    if mancanti:
        print(f"  FERMO: {len(mancanti)} celle di E15 mancanti, es. {mancanti[:3]}"); return 1
    ctx = mp.get_context("spawn"); t_in = time.time(); fall = 0
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_cella, [(c, p, s, str(out), fili) for c, p, s in celle()]), 1):
            if r["esito"] == "fallita":
                fall += 1
                print(f"  [{i:3d}/{len(celle())}] {r['c']:10s} p{r['p']} s{r['s']} FALLITA {r['errore']}", flush=True)
            else:
                print(f"  [{i:3d}/{len(celle())}] {r['c']:10s} p{r['p']} s{r['s']} {r['esito']:8s} {r['secondi']/60:5.1f} min  "
                      + (" ".join(f"{k} {v:.4f}" for k, v in r["wce"].items()) if "wce" in r else ""), flush=True)
    print(f"\n  {len(celle()) - fall} celle, {fall} fallite, {(time.time() - t_in)/60:.1f} min")
    return 0 if fall == 0 else 1


STAT_Q = [("C", None), ("A", None), ("C_A", None), ("C_A_esp", None), ("C", 2), ("A", 2), ("C_A", 2), ("C_A_esp", 2)]
IDX_Q = {k: i for i, k in enumerate(STAT_Q)}
DIFFERENZE = [  # (nome, minuendo, sottraendo, lettura)
    ("C_A_esp-C_A", "C_A_esp", "C_A", "effetto della coverage di valutazione (stesso modello)"),
    ("C_A_esp-C", "C_A_esp", "C", "effetto dei dati anteriori a t0 nell'addestramento, a pari coverage"),
    ("A-C_A_esp", "A", "C_A_esp", "valore dell'identita' a pari coverage"),
    ("A-C", "A", "C", "riferimento E15 (stessa media; intervallo con estrazioni proprie)"),
    ("A-C_A", "A", "C_A", "riferimento E15"),
    ("C_A-C", "C_A", "C", "riferimento E15")]
RIFERIMENTI_E15 = ("A-C", "A-C_A", "C_A-C")


def fase_analizza(out: Path) -> int:
    import numpy as np
    pr, q = _carica(out, "prova"), {}
    for f in sorted((out / DIR_Q).glob("prova_*_p*_s*.npz")):
        with np.load(f, allow_pickle=True) as z:
            d = {k: z[k] for k in z.files}
        q[(str(d["contesto"]), int(d["partizione"]), int(d["seme"]))] = d
    if len(pr) != len(celle()) or len(q) != len(celle()):
        print(f"  FERMO: {len(pr)} celle E15 e {len(q)} celle E18-quater, attese {len(celle())}"); return 1
    f15 = out / "e15_risultati.json"
    R15 = json.loads(f15.read_text())
    statiche_q = sorted({str(z["statica"]) for z in q.values()})
    if len(statiche_q) != 1:
        print(f"  FERMO: statiche diverse fra le celle: {statiche_q}"); return 1
    rng = np.random.default_rng(SEME_BOOT)
    R = {"protocollo": "protocol/E18quater.md", "braccio": BRACCIO, "statica_valutazione_nuovi": statiche_q[0],
         "statica_e15": STATICA_E15, "repliche": B_BOOT, "seme_bootstrap": SEME_BOOT, "delta_non_inferiorita": DELTA_NI,
         "istante": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "impronte": {"e15_risultati.json": _sha(f15),
                      "celle_e15": {f"{k[0]}/p{k[1]}/s{k[2]}": str(q[k]["impronta_cella_e15"]) for k in sorted(q)},
                      "ck_C_A": {f"{k[0]}/p{k[1]}/s{k[2]}": str(q[k]["impronta_ck"]) for k in sorted(q)}},
         "controlli": {"aggregati_C_A_riprodotti": "ogni cella: ri-valutazione con la statica di E15 identica bit per bit agli aggregati di E15",
                       "medie_riferimento_vs_e15": {}},
         "perimetro": {"principale": "origini comuni dopo t1 (fasce d'eta' 1-3)", "settimana": "origini con eta' > 1 settimana (fascia 3)"},
         "citta": {}}
    for c in CITTA:
        cc = {k: z for k, z in pr.items() if k[0] == c}
        if len(cc) != 18:
            raise RuntimeError(f"{c}: {len(cc)} celle E15, attese 18")
        unite = {}
        for k, z in cc.items():
            zq = q[k]
            if not np.array_equal(zq["nodi"].astype("int64"), z["nodi"].astype("int64")):
                raise RuntimeError(f"{k}: nodi diversi fra E15 e E18-quater")
            if not np.array_equal(zq["origini"].astype("int64"), z["origini"].astype("int64")):
                raise RuntimeError(f"{k}: origini diverse fra E15 e E18-quater")
            unite[k] = {**{f"{a}_{n}": z[f"{a}_{n}"] for a in ("A", "B") for n in ("C", "A", "C_A")},
                        "A_C_A_esp": zq["A_C_A_esp"], "B_C_A_esp": zq["B_C_A_esp"], "celle_valide": z["celle_valide"]}

        def f_vec(z, idx):
            return np.array([_wce(*_ab(z, n, f, idx)) for n, f in STAT_Q])
        K = int(next(iter(cc.values()))["celle_valide"].shape[0])
        m0, rep = _boot_vec(unite, f_vec, rng, K)
        Rc = {"celle": len(cc), "nodi": K, "livelli": {}, "differenze": {}, "settimana": {}}
        for n, f in STAT_Q:
            Rc["livelli"][f"{n}{'' if f is None else '/settimana'}"] = {"media": float(m0[IDX_Q[(n, f)]]),
                                                                       "ic_con_nodi": _ic(rep[:, IDX_Q[(n, f)]])}

        def diff(i, j):
            d0 = float(m0[i] - m0[j]); ic = _ic(rep[:, i] - rep[:, j])
            return {"media": d0, "ic_con_nodi": ic, "segno": segno(ic), "categoria": categoria(ic)}
        for nome, a_, b_, lettura in DIFFERENZE:
            Rc["differenze"][nome] = {**diff(IDX_Q[(a_, None)], IDX_Q[(b_, None)]), "lettura": lettura}
            Rc["settimana"][nome] = diff(IDX_Q[(a_, 2)], IDX_Q[(b_, 2)])
        # controllo: le medie dei riferimenti coincidono con E15 (stesse celle, stessi aggregati)
        for nome in RIFERIMENTI_E15:
            m15 = R15["citta"][c]["dichiarazioni"][nome]["media"]
            sc = abs(Rc["differenze"][nome]["media"] - m15)
            if sc > 1e-12:
                raise RuntimeError(f"{c}: media di {nome} = {Rc['differenze'][nome]['media']:.12f} diversa da E15 {m15:.12f}")
            Rc["differenze"][nome]["e15"] = {"media": m15, "ic_con_nodi": R15["citta"][c]["dichiarazioni"][nome]["ic_con_nodi"]}
            R["controlli"]["medie_riferimento_vs_e15"][f"{c}/{nome}"] = f"scarto {sc:.1e}"
        i_c, i_ca, i_e = IDX_Q[("C", None)], IDX_Q[("C_A", None)], IDX_Q[("C_A_esp", None)]
        Rc["quota_coverage"] = {
            "definizione": "(C_A - C_A_esp) / (C_A - C): quota del divario C_A - C dovuta alla coverage di valutazione; "
                           "il resto, (C_A_esp - C) / (C_A - C), ai dati anteriori a t0 nell'addestramento",
            "media": float((m0[i_ca] - m0[i_e]) / (m0[i_ca] - m0[i_c])),
            "ic_con_nodi": _ic((rep[:, i_ca] - rep[:, i_e]) / (rep[:, i_ca] - rep[:, i_c])),
            "repliche_den_senza_divario": int(np.sum(rep[:, i_ca] - rep[:, i_c] >= 0))}
        R["citta"][c] = Rc
    fj = out / "e18quater_risultati.json"
    fj.write_text(json.dumps(R, indent=2, ensure_ascii=False))
    # il resoconto derivato
    L = ["# E18-quater — C_A con la coverage di valutazione dei sensori nuovi uguale a quella di C", "",
         f"Derivato da `evoluzione/esperimenti/esegui_e18quater.py --fase analizza` da `results/evoluzione/e18quater_risultati.json` "
         f"(impronta `{_sha(fj)}`) il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}; ingresso "
         f"`e15_risultati.json` (impronta `{R['impronte']['e15_risultati.json']}`). Modelli congelati di E15; statica dei nuovi "
         f"in valutazione: «{statiche_q[0]}» (E15 dava a C_A la coverage su [0, t0)). Medie sulle 18 celle per citta'; intervalli al 95 % "
         f"da {B_BOOT} ricampionamenti congiunti (partizioni, semi, posizioni dei nodi), seme {SEME_BOOT}. wCE, tutte le origini dopo t1.", "",
         "| citta' | differenza | media | IC 95 % | segno | categoria | E15 (media; IC) |", "|---|---|---:|---|:-:|---|---|"]
    for c in CITTA:
        for nome, _, _, _ in DIFFERENZE:
            d = R["citta"][c]["differenze"][nome]
            e = d.get("e15")
            L.append(f"| {c} | {nome} | {d['media']:+.4f} | [{d['ic_con_nodi'][0]:+.4f}, {d['ic_con_nodi'][1]:+.4f}] | {d['segno']} | "
                     f"{d['categoria']} | " + (f"{e['media']:+.4f}; [{e['ic_con_nodi'][0]:+.4f}, {e['ic_con_nodi'][1]:+.4f}]" if e else "—") + " |")
    L += ["", "Quota del divario C_A − C dovuta alla coverage di valutazione, (C_A − C_A_esp)/(C_A − C); il complemento a 1 e' la "
          "quota dei dati anteriori a t0 nell'addestramento:", "", "| citta' | quota coverage | IC 95 % |", "|---|---:|---|"]
    for c in CITTA:
        r = R["citta"][c]["quota_coverage"]
        L.append(f"| {c} | {r['media']:.3f} | [{r['ic_con_nodi'][0]:.3f}, {r['ic_con_nodi'][1]:.3f}] |")
    L += ["", "Livelli (wCE, tutte le origini dopo t1):", "", "| citta' | C | A | C_A | C_A_esp |", "|---|---:|---:|---:|---:|"]
    for c in CITTA:
        lv = R["citta"][c]["livelli"]
        L.append(f"| {c} | " + " | ".join(f"{lv[n]['media']:.4f}" for n in ("C", "A", "C_A", "C_A_esp")) + " |")
    L += ["", "Controlli: in ogni cella la ri-valutazione di C_A con la statica di E15 riproduce bit per bit gli aggregati salvati da E15; "
          "le medie di A − C, A − C_A, C_A − C coincidono con `e15_risultati.json` (scarto ≤ 1e-12); gli intervalli dei riferimenti "
          "qui hanno estrazioni proprie (stesso seme, vettore di statistiche diverso) e differiscono da quelli di E15 solo per questo.", ""]
    fm = RADICE / "protocol" / "e18quater" / "RISULTATI.md"
    fm.parent.mkdir(parents=True, exist_ok=True); fm.write_text("\n".join(L))
    print("\n".join(L)); print(f"  -> {fj} ({_sha(fj)}), {fm.relative_to(RADICE)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="E18-quater — C_A con la coverage dei nuovi come C")
    ap.add_argument("--fase", required=True, choices=("valuta", "analizza"))
    ap.add_argument("--lavoratori", type=int, default=1)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    if a.fase == "valuta":
        return fase_valuta(a.out, a.lavoratori, a.fili)
    return fase_analizza(a.out)


if __name__ == "__main__":
    raise SystemExit(main())
