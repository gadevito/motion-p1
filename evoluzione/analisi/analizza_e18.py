#!/usr/bin/env python3
"""
E18 — analisi di verifica dalla seconda revisione esterna (protocol/E18.md). SOLA ANALISI.
==========================================================================================
Nessun addestramento. Ingressi: artefatti gia' congelati (probabilita' per cella di E16, aggregati
di E4/E5/E6/E15, json congelati, mappe sensore -> posizione). Quattro parti, eseguite nell'ordine
C -> A -> B -> D; ciascuna scrive la propria voce in `results/evoluzione/e18_risultati.json`
(`--parte tutte` le rifa' tutte, come nella fase E18 di `analysis/main.py`).

    --parte C   correzione 27 (E16): righe F'(1 sett.) di F15/F16 ricalcolate sulle origini con eta' >
                1 settimana per ENTRAMBI i bracci (F'(1 sett.) e C), grezze e con le quattro calibrazioni
                (parametri gia' stimati sulla validazione, in e16_risultati.json: cambia solo la finestra);
                riga aggiuntiva "C, origini > 1 sett." per calibrazione. CONTROLLO bloccante: la wCE grezza
                per orizzonte di F'(1 sett.) e C sulla finestra, ricalcolata dalle probabilita', coincide con
                l'aggregato congelato della campagna (predizioni_e4 citta', predizioni_e6 PEMS08, fascia
                eta' > 1 settimana) entro 1e-6 relativo; nodi e origini identici. Se fallisce, si ferma.
    --parte A   (dopo il pilota) ROC empirica, AUC, pAUC(0-10 %), richiamo a FA fissi; vedi `parte_A`.
    --parte B   bootstrap che conserva il sensore fisico; vedi `parte_B`.
    --parte D   provenienza della politica gated(1 sett., 0); vedi `parte_D`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_e18.py --parte C
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e16 import (  # noqa: E402
    CALIBRAZIONI, _AB, _applica, _boot_vec, _log_p, _metriche, _wce_ab)
from evoluzione.esperimenti.esegui_e4 import FASCE_ETA  # noqa: E402

SEME_BOOT = 20261028
TOLLERANZA_C = 1e-6
DELTA_NI = 0.005
GRUPPI = ("Madrid", "Londra", "Melbourne", "PEMS08")
ETA_SETT = FASCE_ETA[1]                       # 672 passi: una settimana


def imp(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def _ic(v):
    q = np.nanpercentile(v, [2.5, 97.5]); return [float(q[0]), float(q[1])]


def segno(ic):
    return "-" if ic[1] < 0 else ("+" if ic[0] > 0 else "0")


def categoria(ic):
    if ic[1] < 0:
        return "superiorita'"
    if ic[1] < DELTA_NI:
        return "non inferiorita'"
    if ic[0] > 0:
        return "inferiorita'"
    return "inconclusivo"


def _carica_json(out: Path):
    f = out / "e18_risultati.json"
    return json.loads(f.read_text()) if f.exists() else {}


def _salva_json(out: Path, R: dict):
    f = out / "e18_risultati.json"
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(R, indent=1, ensure_ascii=False))
    tmp.replace(f)


def _wce_oriz(A, B):
    num, den = A.sum(0), B.sum(0)
    return np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)


# ------------------------------------------------------------------- parte C --
def parte_C(out: Path) -> dict:
    """Correzione 27: F'(1 sett.) e C di E16 sulle origini con eta' > 1 settimana.

    Oltre alla wCE con ricampionamento (F15), le metriche di F16 sulla stessa finestra: ECE per classe, log-loss
    non pesata, Brier multiclasse, wCE, per cella e in media per gruppo (`medie_settimana`, come `medie_test` di E16).
    """
    E16 = json.loads((out / "e16_risultati.json").read_text())
    file_p = sorted((out / "predizioni_e16").glob("prova_*_p*_s*.npz"))
    if not file_p:
        raise RuntimeError("predizioni_e16/prova_* assenti")
    celle_gr, controllo, ingressi, fuori = {}, {}, {}, []
    print(f"  {len(file_p)} celle di prova di E16; finestra: eta' > {ETA_SETT} passi (una settimana); bracci C e F'(1 sett.)")
    for fp in file_p:
        z = np.load(fp, allow_pickle=True)
        c, p, s, gr = str(z["contesto"]), int(z["partizione"]), int(z["seme"]), str(z["gruppo"])
        sel = z["eta"] > ETA_SETT
        if not sel.any():
            raise RuntimeError(f"{fp.name}: nessuna origine con eta' > 1 settimana")
        Y, M, w = z["y"][sel], z["m"][sel].astype(bool), z["pesi"].astype("float64")
        par = E16["per_cella"][f"{gr}/{c}/p{p}/s{s}"]["parametri"]
        cella = {"K": int(len(z["nodi"])), "A": {}, "B": {}, "wce": {}, "metriche": {}, "contesto": c}

        def _met(P_):
            return {k_: v_ for k_, v_ in _metriche(P_, Y, M, w).items() if k_ != "affidabilita"}
        for nome in ("C", "Fp_672"):
            P = z[f"prob_{nome}"][sel].astype("float64"); lp = _log_p(P)
            cella["A"][f"{nome}/grezzo"], cella["B"][f"{nome}/grezzo"] = _AB(P, Y, M, w)
            cella["metriche"][f"{nome}/grezzo"] = _met(P)
            for cal in CALIBRAZIONI:
                tipo = cal.split("_")[0]
                theta = np.asarray(par[f"{nome}/{cal}"]["theta"], dtype="float64")
                Pc = _applica(lp, theta, tipo)
                cella["A"][f"{nome}/{cal}"], cella["B"][f"{nome}/{cal}"] = _AB(Pc, Y, M, w)
                cella["metriche"][f"{nome}/{cal}"] = _met(Pc)
        # CONTROLLO: wCE grezza per orizzonte sulla finestra == aggregato congelato (fascia eta' > 1 sett.)
        f_c = (out / "predizioni_e4" / f"prova_{c}_p{p}_s{s}.npz") if gr != "PEMS08" else \
              (out / "predizioni_e6" / f"prova_{c}_p{p}_s{s}.npz")
        if not f_c.exists():
            raise RuntimeError(f"controllo C: manca l'aggregato congelato {f_c}")
        zc = np.load(f_c, allow_pickle=True)
        sel_c = zc["eta"] > ETA_SETT
        if not (np.array_equal(zc["nodi"].astype("int64"), z["nodi"].astype("int64"))
                and np.array_equal(zc["origini"][sel_c].astype("int64"), z["origini"][sel].astype("int64"))):
            raise RuntimeError(f"controllo C, {fp.name}: nodi od origini (eta' > 1 sett.) diversi da {f_c.name}")
        sc = {}
        for nome in ("C", "Fp_672"):
            mio = _wce_oriz(cella["A"][f"{nome}/grezzo"], cella["B"][f"{nome}/grezzo"])
            loro = _wce_oriz(zc[f"A_{nome}"][2], zc[f"B_{nome}"][2])
            rel = float(np.nanmax(np.abs(mio - loro) / np.maximum(np.abs(loro), 1e-12)))
            sc[nome] = rel
            if rel > TOLLERANZA_C:
                fuori.append(f"{fp.name} {nome}: {rel:.2e} (rispetto a {f_c.name}, fascia eta' > 1 sett.)")
        controllo[f"{gr}/{c}/p{p}/s{s}"] = {"file_congelato": f_c.name, "scarto_relativo_max": sc,
                                           "origini_finestra": int(sel.sum()), "origini_totali": int(len(sel))}
        ingressi[fp.name] = imp(fp)
        celle_gr.setdefault(gr, {})[(gr, p, s)] = cella
    print(f"  controllo: {len(controllo)} celle, scarto relativo massimo "
          f"{max(max(v['scarto_relativo_max'].values()) for v in controllo.values()):.2e} (soglia {TOLLERANZA_C:g})")
    if fuori:
        # BLOCCANTE, dopo aver esaminato tutte le celle: l'elenco completo serve a chi deve decidere
        raise RuntimeError(f"controllo C: {len(fuori)} celle oltre {TOLLERANZA_C:g} — E18-C si ferma:\n    " + "\n    ".join(fuori))
    R = {"definizione": "finestra: origini con eta' > 1 settimana per F'(1 sett.) E per C; parametri di calibrazione "
                        "di e16_risultati.json (stimati sulla validazione della stessa cella), invariati; metriche di F16 "
                        "(ECE per classe a 10 intervalli, log-loss non pesata, Brier multiclasse, wCE) per cella sulla stessa "
                        "finestra e in media sulle celle, come `medie_test` di E16",
         "finestra_passi": int(ETA_SETT), "tolleranza_controllo": TOLLERANZA_C, "repliche": None, "seme_bootstrap": SEME_BOOT,
         "controllo": controllo, "gruppi": {}, "riferimento_intero_periodo": {},
         "per_cella_settimana": {f"{k[0]}/{v['contesto']}/p{k[1]}/s{k[2]}": v["metriche"] for cc in celle_gr.values()
                                 for k, v in cc.items()},
         "impronte_ingressi": {
             "e16_risultati.json": imp(out / "e16_risultati.json"), "predizioni_e16": ingressi}}
    from evoluzione.esperimenti.esegui_e16 import B_BOOT
    R["repliche"] = B_BOOT
    rng = np.random.default_rng(SEME_BOOT)
    chiavi = [f"{n}/{v}" for n in ("C", "Fp_672") for v in ("grezzo",) + CALIBRAZIONI]
    for gr in GRUPPI:
        celle = celle_gr.get(gr)
        if not celle:
            continue

        def f(z, idx, _ch=chiavi):
            return np.array([_wce_ab(z["A"][k], z["B"][k], idx) for k in _ch])
        m0, rep = _boot_vec(celle, f, rng)
        pos = {k: i for i, k in enumerate(chiavi)}
        G = {"celle": len(celle), "wce_settimana": {k: {"media": float(m0[i]), "ic_con_nodi": _ic(rep[:, i])} for i, k in enumerate(chiavi)},
             "differenze_settimana": {}}
        for var in ("grezzo",) + CALIBRAZIONI:
            d = rep[:, pos[f"Fp_672/{var}"]] - rep[:, pos[f"C/{var}"]]; ic = _ic(d)
            G["differenze_settimana"][f"Fp_672-C/{var}"] = {"media": float(m0[pos[f"Fp_672/{var}"]] - m0[pos[f"C/{var}"]]),
                                                            "ic_con_nodi": ic, "segno": segno(ic), "categoria": categoria(ic)}
        # medie sulle celle delle metriche di F16 sulla finestra (ECE per classe, log-loss, Brier, wCE)
        G["medie_settimana"] = {}
        for k in chiavi:
            mm = [v["metriche"][k] for v in celle.values()]
            G["medie_settimana"][k] = {"logloss": float(np.mean([m["logloss"] for m in mm])), "brier": float(np.mean([m["brier"] for m in mm])),
                                       "wce": float(np.mean([m["wce"] for m in mm])),
                                       "ece": {str(kk): float(np.mean([m["ece"][str(kk)] for m in mm])) for kk in range(3)}}
        R["gruppi"][gr] = G
        # il riferimento: i valori di E16 sull'intero periodo (F15: Fp_672-C; F16: wCE di Fp_672 e C; medie_test)
        g16 = E16["gruppi"][gr]
        R["riferimento_intero_periodo"][gr] = {
            "differenze": {k: g16["differenze"][k] for k in g16["differenze"] if k.startswith("Fp_672-C/")},
            "wce": {k: g16["wce"][k] for k in chiavi if k in g16["wce"]},
            "medie_test": {k: g16["medie_test"][k] for k in chiavi if k in g16.get("medie_test", {})}}
        print(f"  {gr:10s} {len(celle)} celle: F'(1 sett.) - C grezzo su eta' > 1 sett. "
              f"{G['differenze_settimana']['Fp_672-C/grezzo']['media']:+.4f} {G['differenze_settimana']['Fp_672-C/grezzo']['ic_con_nodi']} "
              f"(intero periodo, E16: {g16['differenze']['Fp_672-C/grezzo']['media']:+.4f})")
    R["istante"] = datetime.now(timezone.utc).isoformat()
    return R


# ------------------------------------------------------------------- parte A --
CONG = 2                                   # classe congestionata (indice), come esegui_e8.CONG
LIVELLI_FA = (0.005, 0.01, 0.02, 0.05, 0.10)
PAUC_MAX = 0.10
GRUPPI_A = GRUPPI + ("PEMS04",)                 # PEMS04 da predizioni_e18_pems04/ (A.6): C, F0', F'(1 sett.)
DIR_PEMS04 = "predizioni_e18_pems04"
BRACCI_INTERO = ("C", "A", "F0", "F0p")
BRACCI_SETT = ("C", "Fp_672")
CONFRONTI_A = (("F0-C", "F0", "C", "intero"), ("F0p-F0", "F0p", "F0", "intero"), ("F0p-C", "F0p", "C", "intero"),
               ("A-C", "A", "C", "intero"), ("Fp_672-C", "Fp_672", "C", "sett"))
METRICHE = ("auc", "pauc") + tuple(f"richiamo_fa_{fa}" for fa in LIVELLI_FA)


def _prepara_roc(score, lab, sens):
    """Ordina una volta per cella e braccio: punteggi decrescenti; `idx` = ultimo indice di ogni
    punteggio DISTINTO (la ROC empirica su tutti i punteggi distinti)."""
    o = np.argsort(-score, kind="stable")
    sc = score[o]
    idx = np.flatnonzero(np.diff(sc) != 0)
    idx = np.append(idx, len(sc) - 1)
    return lab[o].astype("int64"), sens[o].astype("int64"), idx


def _metriche_roc(pos, sens, idx, w):
    """AUC trapezoidale completa, pAUC su FPR in [0, PAUC_MAX] (area / PAUC_MAX), richiamo ai livelli
    di FA per interpolazione lineare sulla ROC empirica, con pesi di molteplicita' `w` sui sensori."""
    wp = w[sens]
    cp = np.cumsum(wp * pos)[idx]; cn = np.cumsum(wp * (1 - pos))[idx]
    P, N = cp[-1], cn[-1]
    if P <= 0 or N <= 0:
        return np.full(len(METRICHE), np.nan)
    tpr = np.concatenate([[0.0], cp / P]); fpr = np.concatenate([[0.0], cn / N])
    auc = float(np.sum((fpr[1:] - fpr[:-1]) * (tpr[1:] + tpr[:-1]) / 2.0))
    # pAUC: integrale fino a PAUC_MAX, con il segmento che attraversa il limite interpolato
    j = int(np.searchsorted(fpr, PAUC_MAX, side="right"))        # fpr[:j] <= PAUC_MAX
    area = float(np.sum((fpr[1:j] - fpr[:j - 1]) * (tpr[1:j] + tpr[:j - 1]) / 2.0)) if j > 1 else 0.0
    if j < len(fpr) and fpr[j] > fpr[j - 1]:
        t_lim = tpr[j - 1] + (tpr[j] - tpr[j - 1]) * (PAUC_MAX - fpr[j - 1]) / (fpr[j] - fpr[j - 1])
        area += (PAUC_MAX - fpr[j - 1]) * (tpr[j - 1] + t_lim) / 2.0
    pauc = area / PAUC_MAX
    # richiamo a FA fisso: per ogni FPR distinta il richiamo massimo raggiunto (ultimo punto), poi interpolazione
    ult = np.append(np.flatnonzero(np.diff(fpr) > 0), len(fpr) - 1)
    ric = np.interp(np.asarray(LIVELLI_FA), fpr[ult], tpr[ult])
    return np.concatenate([[auc, pauc], ric])


def _cella_A(args):
    """Una cella: metriche puntuali e per replica (pesi di molteplicita' sui sensori) per ogni coppia
    braccio-finestra, piu' il richiamo sotto argmax; verifica contro sklearn sulla prima cella."""
    fp, nd_file, verifica = args
    import time
    t_in = time.time()
    z = np.load(fp, allow_pickle=True)
    nd = np.load(nd_file)                                           # (B, K) posizioni estratte
    B, K = nd.shape
    pesi_rep = np.stack([np.bincount(r, minlength=K) for r in nd]).astype("float64")   # (B, K) molteplicita'
    uno = np.ones(K)
    m = z["m"].astype(bool); y = z["y"].astype("int64"); eta = z["eta"]
    modelli = json.loads(str(z["modelli"]))
    sens_all = np.broadcast_to(np.arange(K)[None, :, None], m.shape)
    R = {"cella": f"{z['gruppo']}/{z['contesto']}/p{int(z['partizione'])}/s{int(z['seme'])}", "K": int(K),
         "punto": {}, "rep": {}, "argmax_punto": {}, "argmax_rep": {}, "verifica_sklearn": None}
    for fin, bracci, sel in (("intero", BRACCI_INTERO, np.ones(len(eta), dtype=bool)),
                             ("sett", BRACCI_SETT, eta > ETA_SETT)):
        msel = m & sel[:, None, None]
        lab = (y[msel] == CONG).astype("int64"); sens = sens_all[msel]
        for nome in bracci:
            if nome not in modelli:
                continue
            P = z[f"prob_{nome}"]
            score = P[..., CONG][msel].astype("float64")
            pos, se, idx = _prepara_roc(score, lab, sens)
            R["punto"][f"{nome}/{fin}"] = _metriche_roc(pos, se, idx, uno)
            R["rep"][f"{nome}/{fin}"] = np.stack([_metriche_roc(pos, se, idx, pesi_rep[b]) for b in range(B)])
            if verifica and fin == "intero" and nome == "C":
                from sklearn.metrics import roc_curve
                fpr_s, tpr_s, _ = roc_curve(lab, score, drop_intermediate=False)
                auc_s = float(np.sum((fpr_s[1:] - fpr_s[:-1]) * (tpr_s[1:] + tpr_s[:-1]) / 2.0))
                ult = np.append(np.flatnonzero(np.diff(fpr_s) > 0), len(fpr_s) - 1)
                ric_s = np.interp(np.asarray(LIVELLI_FA), fpr_s[ult], tpr_s[ult])
                mio = R["punto"]["C/intero"]
                R["verifica_sklearn"] = {"cella": R["cella"], "scarto_auc": float(abs(mio[0] - auc_s)),
                                         "scarto_richiami_max": float(np.max(np.abs(mio[2:] - ric_s))),
                                         "punti": int(len(score)), "soglie_distinte": int(len(idx))}
            # richiamo sotto argmax: TP e FN per sensore (intero periodo), pesati nelle repliche
            if fin == "intero":
                pred_c = (P.argmax(-1) == CONG)
                tp_k = ((pred_c & (y == CONG)) & msel).sum((0, 2)).astype("float64")
                fn_k = ((~pred_c & (y == CONG)) & msel).sum((0, 2)).astype("float64")
                R["argmax_punto"][nome] = float(tp_k.sum() / max(tp_k.sum() + fn_k.sum(), 1e-12))
                tp = pesi_rep @ tp_k; fn = pesi_rep @ fn_k
                R["argmax_rep"][nome] = tp / np.maximum(tp + fn, 1e-12)
    R["secondi"] = time.time() - t_in
    return R


def parte_A(out: Path, pilota=None, repliche=None, lavoratori=1) -> dict:
    """ROC empirica, AUC, pAUC(0-10 %), richiamo a FA fissi; bootstrap congiunto con pesi di molteplicita'."""
    import multiprocessing as mp
    import tempfile
    import time
    B = int(repliche or 4000)
    gruppi = (pilota,) if pilota else GRUPPI_A
    file_p = sorted((out / "predizioni_e16").glob("prova_*_p*_s*.npz")) + sorted((out / DIR_PEMS04).glob("prova_*_p*_s*.npz"))
    per_gruppo = {}
    for fp in file_p:
        with np.load(fp, allow_pickle=True) as z:
            per_gruppo.setdefault(str(z["gruppo"]), []).append((fp, int(z["partizione"]), int(z["seme"]), int(len(z["nodi"]))))
    R = {"definizione": "punteggio = p(congestionata) per (origine, sensore, orizzonte) sui bersagli validi; ROC empirica su tutti i "
                        "punteggi distinti per cella, orizzonti e sensori riuniti; AUC trapezoidale; pAUC su FPR in [0, 0.10] "
                        "(area / 0.10); richiamo a FA 0.5/1/2/5/10 % per interpolazione lineare; unita' = cella, media sulle celle",
         "finestre": {"intero": "tutte le origini dopo t1 (C, A, F0, F0')", "sett": "origini con eta' > 1 settimana (F'(1 sett.) e C)"},
         "repliche": B, "seme_bootstrap": SEME_BOOT, "pilota": pilota, "gruppi": {}, "tempi": {}, "verifica_sklearn": {},
         "impronte_ingressi": {f"{fp.parent.name}/{fp.name}": imp(fp) for g in gruppi for fp, _, _, _ in per_gruppo.get(g, [])},
         "pems04": {"cartella": DIR_PEMS04, "bracci": "C, F0', F'(1 sett.) (nessun E ne' A per PEMS04: A1, A2, A4 non definibili)",
                    "ricostruzione": "esegui_e16.py --fase predizioni --contesto pems04 --dir-pred predizioni_e18_pems04 --statica congelata (sole celle di prova)"}}
    for gr in gruppi:
        celle = per_gruppo.get(gr)
        if not celle:
            print(f"  {gr}: nessuna cella in predizioni_e16"); continue
        K = celle[0][3]
        if any(k != K for _, _, _, k in celle):
            raise RuntimeError(f"{gr}: numero di sensori diverso fra celle")
        parts = sorted({p for _, p, _, _ in celle}); semi = sorted({s for _, _, s, _ in celle})
        rng = np.random.default_rng(SEME_BOOT + GRUPPI_A.index(gr))
        ps = rng.choice(parts, (B, len(parts)), True); ss = rng.choice(semi, (B, len(semi)), True)
        nd = rng.integers(0, K, (B, K))
        t0 = time.time()
        with tempfile.TemporaryDirectory() as td:
            nd_file = Path(td) / f"nd_{gr}.npy"; np.save(nd_file, nd)
            lavori = [(fp, str(nd_file), i == 0) for i, (fp, _, _, _) in enumerate(celle)]
            print(f"  {gr}: {len(celle)} celle, {K} sensori, {B} repliche, {lavoratori} lavoratori", flush=True)
            if lavoratori > 1:
                with mp.get_context("spawn").Pool(lavoratori) as pool:
                    ris = list(pool.imap(_cella_A, lavori))
            else:
                ris = [_cella_A(x) for x in lavori]
        per_cella = {(p, s): r for (fp, p, s, _), r in zip(celle, ris)}
        sec = [r["secondi"] for r in ris]
        R["tempi"][gr] = {"parete_s": time.time() - t0, "macchina_s": float(sum(sec)), "per_cella_s": {"min": min(sec), "mediana": float(np.median(sec)), "max": max(sec)}}
        for r in ris:
            if r["verifica_sklearn"]:
                R["verifica_sklearn"][gr] = r["verifica_sklearn"]
        print(f"    parete {R['tempi'][gr]['parete_s']/60:.1f} min, macchina {R['tempi'][gr]['macchina_s']/3600:.2f} h, "
              f"per cella {np.median(sec):.0f} s; verifica sklearn: {R['verifica_sklearn'].get(gr)}", flush=True)
        # media sulle celle: puntuale su tutte, per replica sulle celle estratte (partizioni x semi)
        chiavi = sorted(ris[0]["rep"])
        G = {"celle": len(celle), "sensori": K, "metriche": {}, "argmax": {}, "confronti": {}, "recupero_argmax": {}}
        punto = {k: np.mean([r["punto"][k] for r in ris], axis=0) for k in chiavi}
        rep = {}
        for k in chiavi:
            M = np.empty((B, len(METRICHE)))
            for b in range(B):
                M[b] = np.mean([per_cella[(p, s)]["rep"][k][b] for p in ps[b] for s in ss[b]], axis=0)
            rep[k] = M
        for k in chiavi:
            G["metriche"][k] = {met: {"media": float(punto[k][i]), "ic_con_nodi": _ic(rep[k][:, i])} for i, met in enumerate(METRICHE)}
        am_punto = {n: float(np.mean([r["argmax_punto"][n] for r in ris])) for n in ris[0]["argmax_punto"]}
        am_rep = {n: np.array([np.mean([per_cella[(p, s)]["argmax_rep"][n][b] for p in ps[b] for s in ss[b]]) for b in range(B)])
                  for n in ris[0]["argmax_punto"]}
        G["argmax"] = {n: {"richiamo": am_punto[n], "ic_con_nodi": _ic(am_rep[n])} for n in am_punto}
        for nome, n1, n2, fin in CONFRONTI_A:
            k1, k2 = f"{n1}/{fin}", f"{n2}/{fin}"
            if k1 not in punto or k2 not in punto:
                continue
            d = {}
            for i, met in enumerate(METRICHE):
                v = rep[k1][:, i] - rep[k2][:, i]; ic = _ic(v)
                d[met] = {"media": float(punto[k1][i] - punto[k2][i]), "ic_con_nodi": ic, "segno": segno(ic)}
            G["confronti"][nome] = {"finestra": fin, **d}
        # A4: recall persa da F0 sotto argmax contro C e quota recuperata a FA 5 %: 1 - perdita_FA5 / perdita_argmax
        if "F0" in am_punto and "C" in am_punto:
            i5 = METRICHE.index("richiamo_fa_0.05")
            pa0 = am_punto["C"] - am_punto["F0"]; pf0 = punto["C/intero"][i5] - punto["F0/intero"][i5]
            pa = am_rep["C"] - am_rep["F0"]; pf = rep["C/intero"][:, i5] - rep["F0/intero"][:, i5]
            G["recupero_argmax"] = {"perdita_argmax_punti": {"media": float(100 * pa0), "ic_con_nodi": _ic(100 * pa)},
                                    "perdita_fa5_punti": {"media": float(100 * pf0), "ic_con_nodi": _ic(100 * pf)},
                                    "quota_recuperata": {"media": float(1 - pf0 / pa0) if pa0 != 0 else None, "ic_con_nodi": _ic(1 - pf / pa),
                                                         "repliche_perdita_argmax_non_positiva": int(np.sum(pa <= 0))},
                                    "definizione": "1 - (richiamo_C - richiamo_F0 a FA 5 %) / (richiamo_C - richiamo_F0 sotto argmax)"}
        R["gruppi"][gr] = G
        c_ = G["confronti"]
        print("    " + " | ".join(f"AUC {n} {c_[n]['auc']['media']:+.4f} {c_[n]['auc']['ic_con_nodi']}" for n in ("F0-C", "F0p-F0", "Fp_672-C") if n in c_)
              + (f" | recupero a FA 5 %: {G['recupero_argmax']['quota_recuperata']['media']:.3f}" if G["recupero_argmax"] else ""), flush=True)
    R["istante"] = datetime.now(timezone.utc).isoformat()
    return R


# ------------------------------------------------------------------- parte B --
def _wce_pesata(A, Bm, w):
    """wCE con pesi di molteplicita' `w` sui sensori: A, B (K, H)."""
    num = w @ A; den = w @ Bm
    return float(np.nanmean(np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)))


def _ab_fascia(z, nome, fascia):
    A, Bm = z[f"A_{nome}"], z[f"B_{nome}"]
    if A.ndim == 3:
        A = A[:3].sum(0) if fascia is None else A[fascia]
        Bm = Bm[:3].sum(0) if fascia is None else Bm[fascia]
    return np.asarray(A, dtype="float64"), np.asarray(Bm, dtype="float64")


def _ids_cella(D_cache, out: Path, contesto: str, nodi):
    """ID fisici dei sensori di una cella: D["sid"][nodi], con D caricato una volta per contesto."""
    if contesto not in D_cache:
        from evoluzione.esperimenti.addestramento import _carica
        D_cache[contesto] = _carica(contesto, out / "maschere")
    sid = D_cache[contesto]["sid"]
    return np.asarray(sid[np.asarray(nodi, dtype="int64")]).astype(str)


def _boot_sensore(celle, ids, f_vec, rng, B):
    """Il bootstrap congiunto del paper con il passo sui sensori che conserva l'ID FISICO (E18, parte B):
    partizioni e semi con reimmissione come oggi; K_d identificatori estratti con reimmissione fra i
    distinti delle partizioni; ogni partizione pesa i propri sensori con la molteplicita' del loro ID
    (0 se non estratto); stessi pesi per bracci, partizioni e semi della replica. Restituisce anche lo
    schema ATTUALE (posizioni) ricalcolato con le stesse estrazioni di partizioni e semi.

    `celle`: {(p, s): z}; `ids`: {p: array di ID (K)}; `f_vec(z, w) -> vettore`."""
    kk = sorted(celle); parts = sorted({k[0] for k in kk}); semi = sorted({k[1] for k in kk})
    K = len(ids[parts[0]])
    distinti = np.array(sorted(set(np.concatenate([ids[p] for p in parts]).tolist())))
    pos_id = {p: np.searchsorted(distinti, ids[p]) for p in parts}
    uno = np.ones(K)
    m0 = np.mean([f_vec(celle[k], uno) for k in kk], axis=0)
    rep_s = np.empty((B, len(m0))); rep_p = np.empty((B, len(m0)))
    for b in range(B):
        ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
        est = rng.integers(0, len(distinti), len(distinti))
        molt = np.bincount(est, minlength=len(distinti)).astype("float64")
        nd = rng.integers(0, K, K); w_pos = np.bincount(nd, minlength=K).astype("float64")
        rep_s[b] = np.mean([f_vec(celle[(p, s)], molt[pos_id[p]]) for p in ps for s in ss], axis=0)
        rep_p[b] = np.mean([f_vec(celle[(p, s)], w_pos) for p in ps for s in ss], axis=0)
    return m0, rep_s, rep_p, {"sensori_distinti": int(len(distinti)), "occorrenze": int(K * len(parts)), "K": int(K)}


def _carica_celle(out: Path, cartella: str, prefisso: str, filtro=None):
    celle = {}
    for f in sorted((out / cartella).glob(f"{prefisso}_*_p*_s*.npz")):
        with np.load(f, allow_pickle=True) as z:
            d = {q: z[q] for q in z.files}
        if filtro and not filtro(d):
            continue
        celle[(str(d["contesto"]), int(d["partizione"]), int(d["seme"]))] = d
    return celle


def parte_B(out: Path, repliche=None) -> dict:
    """Bootstrap che conserva il sensore fisico, applicato alle differenze di Tabella III (a)-(e) per
    contesto ed episodio, a quelle di Tabella E9 (E15), e a quelle di E17 (gated(tau,N) - F0', gated(1 sett., 0)
    - F0' e - gated(tau,N), R-orig(1 sett.) - F'(1 sett.) con margini minimi, F'(1 sett.) - A)."""
    from evoluzione.esperimenti.esegui_e4 import _politica, _wce
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    from evoluzione.esperimenti.addestramento import _partizioni
    B = int(repliche or 4000)
    rng = np.random.default_rng(SEME_BOOT + 100)
    SC4 = json.loads((out / "e4_scelta_gated.json").read_text())["scelta"]
    SC6 = json.loads((out / "e6_scelta_gated.json").read_text())["scelta"]["PEMS08"]
    SC6a = json.loads((out / "e6a_scelta_gated.json").read_text())["scelta"]["PEMS04"]
    E5 = json.loads((out / "e5_risultati.json").read_text()); E6 = json.loads((out / "e6_risultati.json").read_text())
    E6a = json.loads((out / "e6a_risultati.json").read_text()); E15 = json.loads((out / "e15_risultati.json").read_text())
    E17 = json.loads((out / "e17_risultati.json").read_text()); E3b = json.loads((out / "e3bis_risultati.json").read_text())
    D_cache = {}
    R = {"definizione": "passo sui sensori: K_d identificatori fisici estratti con reimmissione fra i distinti delle partizioni "
                        "del contesto; ogni partizione pesa i propri sensori di prova con la molteplicita' del loro ID; pesi "
                        "condivisi fra bracci, partizioni e semi della replica; partizioni e semi ricampionati come oggi",
         "repliche": B, "seme_bootstrap": SEME_BOOT + 100, "delta_non_inferiorita": DELTA_NI, "contesti": {}, "cambi_categoria": [],
         "verifica_mappa": None, "impronte_ingressi": {}}

    def registra(nome_ctx, celle, ids, voci, attuali):
        """`voci`: {nome: (f_vec_scalare)}; `attuali`: {nome: intervallo congelato o None}."""
        nomi = list(voci)

        def f_vec(z, w):
            return np.array([voci[n](z, w) for n in nomi])
        m0, rep_s, rep_p, info = _boot_sensore(celle, ids, f_vec, rng, B)
        C = {"celle": len(celle), **info, "differenze": {}}
        for i, n in enumerate(nomi):
            ic_s = _ic(rep_s[:, i]); ic_p = _ic(rep_p[:, i]); att = attuali.get(n)
            d = {"media": float(m0[i]), "ic_per_sensore": ic_s, "categoria_per_sensore": categoria(ic_s),
                 "ic_posizioni_ricalcolato": ic_p, "categoria_posizioni_ricalcolato": categoria(ic_p)}
            if att is not None:
                d["ic_attuale"] = [float(att["ic_con_nodi"][0]), float(att["ic_con_nodi"][1])]
                d["media_attuale"] = float(att["media"]); d["fonte_attuale"] = att.get("fonte")
                d["categoria_attuale"] = categoria(d["ic_attuale"])
                if d["categoria_attuale"] != d["categoria_per_sensore"]:
                    R["cambi_categoria"].append({"contesto": nome_ctx, "differenza": n, "da": d["categoria_attuale"],
                                                 "a": d["categoria_per_sensore"], "ic_attuale": d["ic_attuale"], "ic_per_sensore": ic_s})
            C["differenze"][n] = d
        R["contesti"][nome_ctx] = C
        cambi = [c for c in R["cambi_categoria"] if c["contesto"] == nome_ctx]
        print(f"  {nome_ctx:16s} {len(celle)} celle, {info['sensori_distinti']} sensori distinti su {info['occorrenze']} occorrenze; "
              f"{len(nomi)} differenze, cambi di categoria: {len(cambi)}", flush=True)

    def dif(n1, n2, fascia, tau=None, N=None):
        def f(z, w):
            def AB(n):
                if n == "gated":
                    return _politica(z, tau, N)
                if n == "gated0":
                    return _politica(z, 672, 0)
                return _ab_fascia(z, n, fascia)
            A1, B1 = AB(n1); A2, B2 = AB(n2)
            return _wce_pesata(A1, B1, w) - _wce_pesata(A2, B2, w)
        return f

    def att(j, **k):
        return None if j is None else {**j, **k}

    # --- Tabella III (a)-(e) ed E17, citta' ep. 1-3 (predizioni_e5), PEMS08 (predizioni_e6), PEMS04 (predizioni_e6a)
    for c in ("Madrid", "Londra", "Melbourne"):
        tau, N = SC4[c]["tau"], SC4[c]["N"]
        for k in (1, 2, 3):
            celle = _carica_celle(out, "predizioni_e5", f"ep{k}", lambda d, c=c: str(d["contesto"]) == c)
            celle = {(p, s): z for (c_, p, s), z in celle.items()}
            if len(celle) != 18:
                raise RuntimeError(f"{c} ep{k}: {len(celle)} celle, attese 18")
            ids = {p: _ids_cella(D_cache, out, c, z["nodi"]) for (p, s), z in celle.items()}
            if R["verifica_mappa"] is None:
                D = D_cache[c]; p0 = sorted(ids)[0]
                nodi, _ = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[p0])})
                z0 = celle[(p0, sorted(s for (p, s) in celle if p == p0)[0])]
                R["verifica_mappa"] = {"contesto": c, "partizione": p0, "nodi_uguali_a_partizioni": bool(np.array_equal(nodi["prova"].astype("int64"), z0["nodi"].astype("int64"))),
                                       "sid_distinti_nel_contesto": int(len(set(np.asarray(D["sid"]).astype(str).tolist()))), "K": int(len(D["sid"]))}
            g = E17["politica"][f"{c}/ep{k}"]["confronti"]
            voci = {"(a) F0p-C": dif("F0p", "C", None), "(b) gated-F0p": dif("gated", "F0p", None, tau, N),
                    "(c) Fp_672-C >1sett": dif("Fp_672", "C", 2), "(d) Fp_96-C": dif("Fp_96", "C", None),
                    "(e) Fp_672-A >1sett": dif("Fp_672", "A", 2), "E17 gated(1sett,0)-F0p": dif("gated0", "F0p", None),
                    "E17 gated(1sett,0)-gated": dif("gated0", "gated", None, tau, N)}
            attuali = {f"({a_}) {n}": att(E5["affermazioni"].get(f"{c}/ep{k}/{a_}"), fonte="e5_risultati.json")
                       for a_, n in (("a", "F0p-C"), ("b", "gated-F0p"), ("c", "Fp_672-C >1sett"), ("d", "Fp_96-C"), ("e", "Fp_672-A >1sett"))}
            attuali["E17 gated(1sett,0)-F0p"] = att(g.get("gated672_0-F0p"), fonte="e17_risultati.json")
            attuali["E17 gated(1sett,0)-gated"] = att(g.get("gated672_0-gated_sel"), fonte="e17_risultati.json")
            registra(f"{c}/ep{k}", celle, ids, voci, attuali)
            R["impronte_ingressi"][f"predizioni_e5/ep{k}_{c}"] = f"{len(celle)} celle"
    for nome_ctx, cart, SC, EJ, con_A, con_R in (("PEMS08", "predizioni_e6", SC6, E6, True, True), ("PEMS04", "predizioni_e6a", SC6a, E6a, False, False)):
        celle = _carica_celle(out, cart, "prova")
        celle = {(int(str(c_).rsplit("_p", 1)[1]), s): z for (c_, p, s), z in celle.items()}
        ids = {p: _ids_cella(D_cache, out, f"{nome_ctx}_p{p}", z["nodi"]) for (p, s), z in celle.items()}
        tau, N = SC["tau"], SC["N"]; g = E17["politica"][nome_ctx]["confronti"]
        voci = {"(a) F0p-C": dif("F0p", "C", None), "(b) gated-F0p": dif("gated", "F0p", None, tau, N),
                "(c) Fp_672-C >1sett": dif("Fp_672", "C", 2), "(d) Fp_96-C": dif("Fp_96", "C", None),
                "E17 gated(1sett,0)-F0p": dif("gated0", "F0p", None), "E17 gated(1sett,0)-gated": dif("gated0", "gated", None, tau, N)}
        attuali = {f"({a_}) {n}": att(EJ["affermazioni"].get(a_), fonte=f"{'e6' if con_A else 'e6a'}_risultati.json")
                   for a_, n in (("a", "F0p-C"), ("b", "gated-F0p"), ("c", "Fp_672-C >1sett"), ("d", "Fp_96-C"))}
        if con_A:
            voci["(e) Fp_672-A >1sett"] = dif("Fp_672", "A", 2); attuali["(e) Fp_672-A >1sett"] = att(EJ["affermazioni"].get("e"), fonte="e6_risultati.json")
        if con_R:
            voci["E17 Rorig_672-Fp_672 >1sett"] = dif("Rorig_672", "Fp_672", 2)
            attuali["E17 Rorig_672-Fp_672 >1sett"] = att(EJ["altri"].get("Rorig_672-Fp_672_eta>1sett"), fonte="e6_risultati.json (altri)")
        attuali["E17 gated(1sett,0)-F0p"] = att(g.get("gated672_0-F0p"), fonte="e17_risultati.json")
        attuali["E17 gated(1sett,0)-gated"] = att(g.get("gated672_0-gated_sel"), fonte="e17_risultati.json")
        registra(nome_ctx, celle, ids, voci, attuali)
    # --- Tabella E9: la campagna causale (predizioni_e15), citta' ep. 1
    for c in ("Madrid", "Londra", "Melbourne"):
        celle = _carica_celle(out, "predizioni_e15", "prova", lambda d, c=c: str(d["contesto"]) == c)
        celle = {(p, s): z for (c_, p, s), z in celle.items()}
        ids = {p: _ids_cella(D_cache, out, c, z["nodi"]) for (p, s), z in celle.items()}
        k_sel = int(E15["citta"][c]["k_secondaria"])
        voci = {"F0-C": dif("F0", "C", None), "F0p-C": dif("F0p", "C", None), "Fp_672-C >1sett": dif("Fp_672", "C", 2),
                "Fp_672-A >1sett": dif("Fp_672", "A", 2), "A-C": dif("A", "C", None), "A-C_A": dif("A", "C_A", None),
                "C_A-C": dif("C_A", "C", None), f"Fpk_672-C >1sett": dif(f"Fp_672_k{k_sel}", "C", 2),
                f"Fpk_672-A >1sett": dif(f"Fp_672_k{k_sel}", "A", 2)}
        d15 = E15["citta"][c]["dichiarazioni"]
        attuali = {n: att(d15.get(n.split(" ")[0]), fonte="e15_risultati.json") for n in voci}
        registra(f"E15 {c}", celle, ids, voci, attuali)
    # --- E3-bis: R-orig(1 sett.) - F'(1 sett.) sulle origini comuni (predizioni_fase3_672 + predizioni_e4 fascia 2)
    for c in ("Madrid", "Londra", "Melbourne"):
        celle = {}
        for f in sorted((out / "predizioni_fase3_672").glob(f"R-orig_{c}_p*_s*.npz")):
            with np.load(f, allow_pickle=True) as zr:
                p, s = int(zr["partizione"]) if "partizione" in zr.files else int(f.stem.split("_p")[1].split("_s")[0]), int(f.stem.rsplit("_s", 1)[1])
                z4 = np.load(out / "predizioni_e4" / f"prova_{c}_p{p}_s{s}.npz", allow_pickle=True)
                if not np.array_equal(zr["nodi"].astype("int64"), z4["nodi"].astype("int64")):
                    raise RuntimeError(f"E3-bis {c} p{p} s{s}: nodi diversi fra R-orig e E4")
                celle[(p, s)] = {"A_Rorig": np.asarray(zr["A_per_nodo"], dtype="float64"), "B_Rorig": np.asarray(zr["B_per_nodo"], dtype="float64"),
                                 "A_Fp": np.asarray(z4["A_Fp_672"][2], dtype="float64"), "B_Fp": np.asarray(z4["B_Fp_672"][2], dtype="float64"),
                                 "nodi": zr["nodi"]}
        if not celle:
            print(f"  E3-bis {c}: predizioni_fase3_672 assenti, salto"); continue
        ids = {p: _ids_cella(D_cache, out, c, z["nodi"]) for (p, s), z in celle.items()}
        voci = {"Rorig_672-Fp_672 >1sett": lambda z, w: _wce_pesata(z["A_Rorig"], z["B_Rorig"], w) - _wce_pesata(z["A_Fp"], z["B_Fp"], w)}
        attuali = {"Rorig_672-Fp_672 >1sett": att(E3b["confronti"].get(f"{c}/Rw-Fpw"), fonte="e3bis_risultati.json")}
        registra(f"E3-bis {c}", celle, ids, voci, attuali)
        d = R["contesti"][f"E3-bis {c}"]["differenze"]["Rorig_672-Fp_672 >1sett"]
        d["margine_minimo_per_sensore"] = float(max(abs(d["ic_per_sensore"][0]), abs(d["ic_per_sensore"][1])))
        d["margine_minimo_attuale"] = E17["margine_minimo"].get(c, {}).get("delta_min")
    if "PEMS08" in R["contesti"] and "E17 Rorig_672-Fp_672 >1sett" in R["contesti"]["PEMS08"]["differenze"]:
        d = R["contesti"]["PEMS08"]["differenze"]["E17 Rorig_672-Fp_672 >1sett"]
        d["margine_minimo_per_sensore"] = float(max(abs(d["ic_per_sensore"][0]), abs(d["ic_per_sensore"][1])))
        d["margine_minimo_attuale"] = E17["margine_minimo"].get("PEMS08", {}).get("delta_min")
    R["istante"] = datetime.now(timezone.utc).isoformat()
    print(f"  cambi di categoria in tutto: {len(R['cambi_categoria'])}")
    return R


# ------------------------------------------------------------------- parte D --
def _git(args, cwd):
    import subprocess
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _prima_data(cwd, percorso=None, testo=None):
    """La data (YYYY-MM-DD) e il commit del primo commit che aggiunge `percorso` o che introduce `testo`."""
    if testo is not None:
        o = _git(["log", "--reverse", "--format=%ad %h", "--date=short", "-S", testo, "--"] + ([percorso] if percorso else []), cwd)
    else:
        o = _git(["log", "--reverse", "--diff-filter=A", "--format=%ad %h", "--date=short", "--", percorso], cwd)
    if not o:
        return None
    d, h = o.splitlines()[0].split()
    return {"data": d, "commit": h}


def parte_D(out: Path) -> dict:
    """Provenienza della politica gated(1 sett., 0): per gli undici contesti, i confronti (attuali e per sensore,
    da B) e le date da `git log`: prima osservazione dei risultati del contesto (file CONGELAMENTO_*) e prima
    formulazione scritta della politica (protocollo e manoscritto)."""
    rep = Path(__file__).resolve().parents[2]; paper = rep.parent / "paper1"
    E17 = json.loads((out / "e17_risultati.json").read_text())
    Bp = _carica_json(out).get("B", {}).get("contesti", {})
    FILE_CTX = {"ep1": "CONGELAMENTO_E4.md", "ep2": "CONGELAMENTO_E5.md", "ep3": "CONGELAMENTO_E5.md",
                "PEMS08": "CONGELAMENTO_E6.md", "PEMS04": "CONGELAMENTO_E6.md"}
    # dove il contesto e' stato osservato per la prima volta: il primo commit del file di congelamento che lo riporta
    # (i risultati di E2 per le citta', ep. 1, precedono E4: si prende il piu' antico fra E2 ed E4)
    oss = {}
    for k, f in FILE_CTX.items():
        d = _prima_data(rep, f)
        oss[k] = {**d, "file": f} if d else None
    # citta', ep. 1: i primi risultati sono quelli della fase 3 (E_F_GRIGLIA) e di E2; si prende il piu' antico
    for f in ("CONGELAMENTO_E_F_GRIGLIA.md", "CONGELAMENTO_E2.md"):
        d = _prima_data(rep, f)
        if d and (oss["ep1"] is None or d["data"] < oss["ep1"]["data"]):
            oss["ep1"] = {**d, "file": f}
    # prima formulazione scritta della politica "una settimana di attesa, poi F'(1 sett.) per tutti"
    form = {"protocollo": {}, "manoscritto": {}}
    # SOLO la politica gated(1 sett., 0): «gated» da solo (E4) e «una settimana» (E5) sono la politica gated(tau, N)
    # e le durate di adattamento, non questa formulazione
    for f, testi in (("protocol/E17.md", ("gated(1 sett., 0)", "gated(1wk,0)", "gated(1 sett, 0)")),):
        for t in testi:
            d = _prima_data(rep, f, t)
            if d:
                form["protocollo"][f"{f} «{t}»"] = d
    if paper.exists():
        for t in ("gated(1wk,0)", "gated(1\\,wk,0)", "waiting a week", "after one week, then", "1\\,\\text{wk}, 0"):
            d = _prima_data(paper, None, t)
            if d:
                form["manoscritto"][f"«{t}»"] = d
    prima_form = min((d["data"] for d in list(form["protocollo"].values()) + list(form["manoscritto"].values())), default=None)
    R = {"definizione": "tabella per gli undici contesti: campagna, gated(1 sett., 0) - F0', gated(1 sett., 0) - gated(tau, N), intervalli "
                        "attuali (E17) e per sensore (B), data della prima osservazione dei risultati del contesto (git log dei "
                        "CONGELAMENTO_*), data della prima formulazione scritta della politica (protocollo e manoscritto, git log -S)",
         "prima_formulazione": {"data": prima_form, "dettaglio": form}, "osservazioni": oss, "contesti": {}, "istante": None}
    for k in E17["politica"]:
        c = k.split("/")[0]; ep = k.split("/")[1] if "/" in k else k
        g = E17["politica"][k]["confronti"]
        d = {"campagna": {"ep1": "E4/E2 (campagna principale)", "ep2": "E5", "ep3": "E5", "PEMS08": "E6", "PEMS04": "E6-bis (parte A)"}[ep],
             "gated0-F0p": {"media": g["gated672_0-F0p"]["media"], "ic_attuale": g["gated672_0-F0p"]["ic_con_nodi"], "categoria_attuale": categoria(g["gated672_0-F0p"]["ic_con_nodi"])},
             "gated0-gated": {"media": g["gated672_0-gated_sel"]["media"], "ic_attuale": g["gated672_0-gated_sel"]["ic_con_nodi"], "categoria_attuale": categoria(g["gated672_0-gated_sel"]["ic_con_nodi"])},
             "osservato": oss.get(ep), "osservato_prima_della_formulazione": (oss.get(ep) or {}).get("data") is not None and prima_form is not None
             and oss[ep]["data"] < prima_form}
        bq = Bp.get(k if "/" in k else k, {}).get("differenze", {})
        for n, kb in (("gated0-F0p", "E17 gated(1sett,0)-F0p"), ("gated0-gated", "E17 gated(1sett,0)-gated")):
            if kb in bq:
                d[n]["ic_per_sensore"] = bq[kb]["ic_per_sensore"]; d[n]["categoria_per_sensore"] = bq[kb]["categoria_per_sensore"]
        R["contesti"][k] = d
    n_prima = sum(1 for d in R["contesti"].values() if d["osservato_prima_della_formulazione"])
    n_tot = len(R["contesti"])
    R["esito"] = {"contesti": n_tot, "osservati_prima_della_formulazione": n_prima, "osservati_dopo": n_tot - n_prima,
                  "atteso": "nessun contesto osservato dopo la formulazione -> valutazione post hoc descrittiva",
                  "verdetto": ("tutti gli undici contesti erano gia' stati osservati quando la politica e' stata scritta: valutazione post hoc "
                               "descrittiva, senza conferma prospettica" if n_prima == n_tot else
                               f"{n_tot - n_prima} contesti osservati DOPO la formulazione: per quelli la valutazione e' prospettica")}
    R["istante"] = datetime.now(timezone.utc).isoformat()
    print(f"  prima formulazione scritta: {prima_form}; contesti osservati prima: {n_prima}/{len(R['contesti'])}")
    return R


def forma(out: Path) -> dict:
    """La forma dei file di E16, per la stima dei tempi della parte A: punteggi validi per cella."""
    R = {}
    for fp in sorted((out / "predizioni_e16").glob("prova_*_p*_s*.npz")):
        z = np.load(fp, allow_pickle=True)
        gr = str(z["gruppo"]); m = z["m"].astype(bool); sel = z["eta"] > ETA_SETT
        r = R.setdefault(gr, {"celle": 0, "punti_validi": 0, "punti_validi_settimana": 0, "forma_prob": list(z["prob_C"].shape),
                              "bracci": json.loads(str(z["modelli"])), "origini": 0, "sensori": int(len(z["nodi"]))})
        r["celle"] += 1; r["punti_validi"] += int(m.sum()); r["punti_validi_settimana"] += int(m[sel].sum()); r["origini"] += int(len(z["eta"]))
    for gr, r in R.items():
        print(f"  {gr:10s} {r['celle']} celle, prob {r['forma_prob']} (origini, sensori, orizzonti, classi), bracci {r['bracci']}; "
              f"punteggi validi per cella: {r['punti_validi'] / r['celle']:.0f} (intero), {r['punti_validi_settimana'] / r['celle']:.0f} (> 1 sett.)")
    return R


def main() -> int:
    ap = argparse.ArgumentParser(description="E18 — analisi di verifica (sola analisi)")
    ap.add_argument("--parte", required=True, choices=("C", "A", "B", "D", "tutte", "forma"))
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--pilota", default=None, help="parte A: una sola citta', per la stima dei tempi")
    ap.add_argument("--repliche", type=int, default=None, help="parte A: 4000 (predefinito) o 1000, dichiarato")
    ap.add_argument("--lavoratori", type=int, default=1, help="parte A: celle in parallelo")
    a = ap.parse_args()
    if a.parte == "forma":
        forma(a.out); return 0
    R = _carica_json(a.out)
    parti = ("C", "A", "B", "D") if a.parte == "tutte" else (a.parte,)
    for parte in parti:
        print("=" * 84); print(f"E18 — parte {parte}"); print("=" * 84)
        if parte == "C":
            R["C"] = parte_C(a.out)
        elif parte == "A":
            R["A"] = parte_A(a.out, a.pilota, a.repliche, a.lavoratori)
        elif parte == "B":
            R["B"] = parte_B(a.out, a.repliche)
        else:
            R["D"] = parte_D(a.out)
        R["protocollo"] = {"file": "protocol/E18.md", "impronta": imp(Path("protocol/E18.md"))}
        R["istante"] = datetime.now(timezone.utc).isoformat()
        _salva_json(a.out, R)
        print(f"  -> {a.out / 'e18_risultati.json'} (parte {parte})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
