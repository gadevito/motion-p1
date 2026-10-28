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
    CALIBRAZIONI, _AB, _applica, _boot_vec, _log_p, _wce_ab)
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
    """Correzione 27: F'(1 sett.) e C di E16 sulle origini con eta' > 1 settimana."""
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
        cella = {"K": int(len(z["nodi"])), "A": {}, "B": {}, "wce": {}}
        for nome in ("C", "Fp_672"):
            P = z[f"prob_{nome}"][sel].astype("float64"); lp = _log_p(P)
            cella["A"][f"{nome}/grezzo"], cella["B"][f"{nome}/grezzo"] = _AB(P, Y, M, w)
            for cal in CALIBRAZIONI:
                tipo = cal.split("_")[0]
                theta = np.asarray(par[f"{nome}/{cal}"]["theta"], dtype="float64")
                Pc = _applica(lp, theta, tipo)
                cella["A"][f"{nome}/{cal}"], cella["B"][f"{nome}/{cal}"] = _AB(Pc, Y, M, w)
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
                        "di e16_risultati.json (stimati sulla validazione della stessa cella), invariati",
         "finestra_passi": int(ETA_SETT), "tolleranza_controllo": TOLLERANZA_C, "repliche": None, "seme_bootstrap": SEME_BOOT,
         "controllo": controllo, "gruppi": {}, "riferimento_intero_periodo": {}, "impronte_ingressi": {
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
        R["gruppi"][gr] = G
        # il riferimento: i valori di E16 sull'intero periodo (F15: Fp_672-C; F16: wCE di Fp_672 e C)
        g16 = E16["gruppi"][gr]
        R["riferimento_intero_periodo"][gr] = {
            "differenze": {k: g16["differenze"][k] for k in g16["differenze"] if k.startswith("Fp_672-C/")},
            "wce": {k: g16["wce"][k] for k in chiavi if k in g16["wce"]}}
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


def parte_B(out: Path) -> dict:
    raise NotImplementedError("parte B: dopo A")


def parte_D(out: Path) -> dict:
    raise NotImplementedError("parte D: dopo B")


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
            R["B"] = parte_B(a.out)
        else:
            R["D"] = parte_D(a.out)
        R["protocollo"] = {"file": "protocol/E18.md", "impronta": imp(Path("protocol/E18.md"))}
        R["istante"] = datetime.now(timezone.utc).isoformat()
        _salva_json(a.out, R)
        print(f"  -> {a.out / 'e18_risultati.json'} (parte {parte})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
