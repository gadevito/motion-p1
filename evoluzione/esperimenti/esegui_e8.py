#!/usr/bin/env python3
"""
E8 — metriche operative (protocol/E8.md). Post hoc, dichiarato, nessun addestramento.
======================================================================================
Ricostruisce dai punti di controllo le classi predette dei bracci del paper,
per cella, e salva **matrici di confusione per fascia d'eta', nodo e
orizzonte** (3 × K × H × 3 × 3) sotto tre regole di decisione, piu' A/B per
nodo per il CONTROLLO BLOCCANTE: la wCE ricalcolata deve riprodurre
l'aggregato congelato (E4/E5/E6/E6-bis/E6a, fase 3, E3-bis) con scarto
relativo <= 1e-6 per cella e per orizzonte.

    --fase validazione   celle dell'episodio di validazione: per ogni modello la
                         matrice di confusione sommata (nodi, orizzonti) per
                         ciascuna soglia della griglia, piu' quella dell'argmax
    --fase soglie        e8_soglie.json con impronta: per contesto e braccio la
                         soglia primaria (F1 della classe congestionata) e quella
                         a parita' di falsi allarmi con C
    --fase prova         celle dell'episodio di prova con le tre regole
    --fase test          differenze fra bracci con il ricampionamento congiunto

    --contesto citta | pems08 | pems04   (predefinito: tutti)
    --pilota                              una cella per contesto, per il tempo

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_e8.py --fase validazione --pilota
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))
from evoluzione.esperimenti.esegui_e4 import (  # noqa: E402
    B_BOOT, D_STAT, FASCE_ETA, _boot, _nome_e_token, _wce)

DIR_PRED = "predizioni_e8"
TOLLERANZA = 1e-6
SOGLIE = [round(0.05 * k, 2) for k in range(1, 20)]          # 0,05 … 0,95
REGOLE = ("prim", "par", "argmax")
CONG = 2                                                     # classe congestionata (indice)
L24, SETTIMANA = 96, 672

# --------------------------------------------------------------- contesti --
# Ogni contesto dichiara: unita' (contesto, partizione, seme), calendario dei
# due episodi, cartelle dei punti di controllo, dove sta l'aggregato congelato
# per il controllo, semi del ricampionamento (quelli dei congelamenti).
CITTA = ("Madrid", "Londra", "Melbourne")


def contesto_citta(out: Path):
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    from evoluzione.esperimenti.seleziona_F import CALENDARIO_VAL_GRIGLIA
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione
    _, dich, _ = configurazione(inserimento=True)
    SC = json.loads((out / "e4_scelta_gated.json").read_text())["scelta"]
    cfgF = json.loads((out / "selezione_F_griglia" / "configurazione_F.json").read_text())["scelte"]
    E_TOK = _nome_e_token()
    unita = [(c, p, int(s)) for c in CITTA for p in (0, 1, 2) for s in dich]
    return {
        "nome": "citta", "unita": unita, "gruppo": lambda c: c,
        "seme_partizione": lambda p: SEME_PARTIZIONE[p], "fine_periodo": None,
        "calendario": lambda c, ep: ((CALENDARIO[c][0], CALENDARIO[c][1], None, "prova") if ep == "prova"
                                     else (CALENDARIO_VAL_GRIGLIA[c][0], CALENDARIO_VAL_GRIGLIA[c][1],
                                           CALENDARIO[c][0], "validazione")),
        "dir_pesi": "pesi_griglia", "cfgF": lambda c: cfgF[c], "gated": lambda c: SC[c],
        "ck": {"C": lambda c, p, s, st: out / "inserimento_griglia" / f"ck_C_{c}_p{p}_s{s}.pt",
               "A": lambda c, p, s, st: out / "inserimento_griglia" / f"ck_A_{c}_p{p}_s{s}.pt",
               "E": lambda c, p, s, st: out / "E_inserimento_griglia" / f"ck_E_{c}_p{p}_s{st}.pt",
               "E1": lambda c, p, s, st: out / f"{E_TOK}_inserimento_griglia" / f"ck_{E_TOK}_{c}_p{p}_s{st}.pt",
               "Rorig_672": lambda c, p, s, st: out / "inserimento_griglia_672" / f"ck_R-orig_{c}_p{p}_s{s}.pt"},
        "modelli": {"prova": ("C", "A", "F0", "F0p", "Fp_96", "Fp_192", "Fp_672", "Rorig_672"),
                    "validazione": ("C", "F0", "F0p", "Fp_96", "Fp_192", "Fp_672")},
        # aggregati congelati: (file, chiave A, chiave B, somma delle fasce?)
        "congelato": lambda c, p, s, ep, m: (
            (out / "predizioni_e4" / f"{ep}_{c}_p{p}_s{s}.npz", f"A_{m}", f"B_{m}", True)
            if m in ("C", "F0", "F0p", "Fp_96", "Fp_192", "Fp_672") else
            (out / "predizioni_fase3" / f"A_{c}_p{p}_s{s}.npz", "A_per_nodo", "B_per_nodo", False)
            if m == "A" and ep == "prova" else
            # E3-bis valuta R-orig(1 sett.) sulle SOLE origini comuni (dopo t0 + 672): il
            # controllo si fa sulla fascia eta' > 1 settimana, che e' quel perimetro
            (out / "predizioni_fase3_672" / f"R-orig_{c}_p{p}_s{s}.npz", "A_per_nodo", "B_per_nodo", "fascia2")
            if m == "Rorig_672" and ep == "prova" else None),
        "seme_boot": 20261004}


def contesto_pems08(out: Path):
    from evoluzione.esperimenti.esegui_e6 import (
        CONTESTI, ETICHETTA, ETICHETTA_672, ETICHETTA_E, SEMI_E6, T0_PROVA, T0_VALIDAZIONE, DIR_SEL)
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE_E6
    SC = json.loads((out / "e6_scelta_gated.json").read_text())["scelta"]["PEMS08"]
    cfgF = json.loads((out / DIR_SEL / "configurazione_F.json").read_text())["scelte"]["PEMS08"]
    E_TOK = _nome_e_token()
    unita = [(c, int(c.rsplit("_p", 1)[1]), int(s)) for c in CONTESTI for s in SEMI_E6]
    return {
        "nome": "pems08", "unita": unita, "gruppo": lambda c: "PEMS08",
        "seme_partizione": lambda p: SEME_PARTIZIONE_E6[p], "fine_periodo": T0_PROVA,
        "calendario": lambda c, ep: ((T0_PROVA, T0_PROVA + L24, None, "prova") if ep == "prova"
                                     else (T0_VALIDAZIONE, T0_VALIDAZIONE + L24, T0_PROVA, "validazione")),
        "dir_pesi": "pesi_pems08", "cfgF": lambda c: cfgF, "gated": lambda c: SC,
        "ck": {"C": lambda c, p, s, st: out / ETICHETTA / f"ck_C_{c}_p{p}_s{s}.pt",
               "A": lambda c, p, s, st: out / ETICHETTA / f"ck_A_{c}_p{p}_s{s}.pt",
               "E": lambda c, p, s, st: out / ETICHETTA_E / f"ck_E_{c}_p{p}_s{st}.pt",
               "E1": lambda c, p, s, st: out / f"{E_TOK}_{ETICHETTA}" / f"ck_{E_TOK}_{c}_p{p}_s{st}.pt",
               "Rorig_672": lambda c, p, s, st: out / ETICHETTA_672 / f"ck_R-orig_{c}_p{p}_s{s}.pt"},
        "modelli": {"prova": ("C", "A", "F0", "F0p", "Fp_96", "Fp_672", "Rorig_672"),
                    "validazione": ("C", "F0", "F0p", "Fp_96", "Fp_672")},
        "congelato": lambda c, p, s, ep, m: (
            (out / "predizioni_e6" / f"{ep}_{c}_p{p}_s{s}.npz", f"A_{m}", f"B_{m}", True)
            if m in ("C", "F0p", "Fp_96", "Fp_672") or (ep == "prova" and m in ("A", "Rorig_672")) else
            (out / "predizioni_e6bis" / f"prova_{c}_p{p}_s{s}.npz", "A_F0", "B_F0", True)
            if m == "F0" and ep == "prova" else None),
        "seme_boot": 20261010}


def contesto_pems04(out: Path):
    from evoluzione.esperimenti.esegui_e6a import (
        CONTESTI, DIR_C, DIR_PESI, DIR_SEL, ETICHETTA_E, T0_PROVA, T0_VALIDAZIONE, semi_campagna)
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    SC = json.loads((out / "e6a_scelta_gated.json").read_text())["scelta"]["PEMS04"]
    cfgF = json.loads((out / DIR_SEL / "configurazione_F.json").read_text())["scelte"]["PEMS04"]
    E_TOK = _nome_e_token()
    unita = [(c, int(c.rsplit("_p", 1)[1]), int(s)) for c in CONTESTI for s in semi_campagna()]
    return {
        "nome": "pems04", "unita": unita, "gruppo": lambda c: "PEMS04",
        "seme_partizione": lambda p: SEME_PARTIZIONE[p], "fine_periodo": None,
        "calendario": lambda c, ep: ((T0_PROVA, T0_PROVA + L24, None, "prova") if ep == "prova"
                                     else (T0_VALIDAZIONE, T0_VALIDAZIONE + L24, "quota85", "validazione")),
        "dir_pesi": DIR_PESI, "cfgF": lambda c: cfgF, "gated": lambda c: SC,
        "ck": {"C": lambda c, p, s, st: out / DIR_C / f"ck_C_{c}_s{s}.pt",
               "E1": lambda c, p, s, st: out / ETICHETTA_E / f"ck_{E_TOK}_{c}_p{p}_s{st}.pt"},
        "modelli": {"prova": ("C", "F0p", "Fp_96", "Fp_192", "Fp_672"),
                    "validazione": ("C", "F0p", "Fp_96", "Fp_192", "Fp_672")},
        "congelato": lambda c, p, s, ep, m: (out / "predizioni_e6a" / f"{ep}_{c}_p{p}_s{s}.npz", f"A_{m}", f"B_{m}", True),
        "seme_boot": 20261011}


CONTESTI_E8 = {"citta": contesto_citta, "pems08": contesto_pems08, "pems04": contesto_pems04}


def _scrivi_atomico(f: Path, testo: str):
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".tmp")
    with open(tmp, "w") as h:
        h.write(testo); h.flush(); os.fsync(h.fileno())
    os.replace(tmp, f)


def _impronta(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()[:16]


# ---------------------------------------------------------------- metriche --
def _wce_per_oriz(A, B):
    import numpy as np
    num, den = A.sum(0), B.sum(0)
    return np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)


def confusione(pred, YY, MM, fasce, K, H):
    """(F, K, H, 3, 3): [fascia, nodo, orizzonte, vero, predetto], sulle celle valide."""
    import numpy as np
    C = np.zeros((len(fasce), K, H, 3, 3), dtype="int32")
    for i, fm in enumerate(fasce):
        y = YY[fm]; q = pred[fm]; m = MM[fm]
        for v in range(3):
            for w in range(3):
                C[i, :, :, v, w] = ((y == v) & (q == w) & m).sum(0)
    return C


def predizione(PB, regola, t):
    """Classi predette: argmax, oppure congestionata se p >= t altrimenti argmax fra le altre due."""
    import numpy as np
    if regola == "argmax":
        return PB.argmax(-1).astype("int8")
    alt = PB[..., :CONG].argmax(-1).astype("int8")
    return np.where(PB[..., CONG] >= t, CONG, alt).astype("int8")


def metriche(C3):
    """Dalla matrice (3, 3) [vero, predetto]: richiamo e precisione della congestionata,
    tasso di falsi allarmi, F1-macro."""
    import numpy as np
    C3 = np.asarray(C3, dtype="float64")
    tp = C3[CONG, CONG]; fn = C3[CONG].sum() - tp; fp = C3[:, CONG].sum() - tp; tn = C3.sum() - tp - fn - fp
    rich = tp / max(tp + fn, 1e-12); prec = tp / max(tp + fp, 1e-12); far = fp / max(fp + tn, 1e-12)
    f1 = []
    for k in range(3):
        tpk = C3[k, k]; fnk = C3[k].sum() - tpk; fpk = C3[:, k].sum() - tpk
        f1.append(2 * tpk / max(2 * tpk + fnk + fpk, 1e-12))
    return {"richiamo": float(rich), "precisione": float(prec), "falsi_allarmi": float(far),
            "f1_macro": float(np.mean(f1)), "f1_congestionata": float(f1[CONG])}


# ------------------------------------------------------------------- cella --
def _modelli(ctx, c, p, s, out, D, nodi, nn, ok, x, stat, w_t, t0, ep_nome):
    """Costruisce i modelli richiesti; registra le impronte dei punti di controllo."""
    import torch
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import adatta, carica_E, copia_da_E
    from evoluzione.componente.episodio import lotti_episodio
    from evoluzione.esperimenti.addestramento import sorgente_di
    from evoluzione.esperimenti.esegui_e2 import da_E1
    from evoluzione.esperimenti.inserimento import _modello_da_ck
    from evoluzione.esperimenti.semi import seme_torch
    st = seme_torch(s); cfgF = ctx["cfgF"](c); imp = {}
    richiesti = ctx["modelli"][ep_nome]
    M = {}
    for nome in ("C", "A", "Rorig_672"):
        if nome in richiesti:
            f = ctx["ck"][nome](c, p, s, st)
            m, d = _modello_da_ck(f, D, nodi, None); M[nome] = m
            imp[nome] = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    dE = dEp = None
    if "F0" in richiesti:
        fE = ctx["ck"]["E"](c, p, s, st); dE, nodi_in, imp["E"] = carica_E(fE, D_STAT)
        M["F0"], _ = copia_da_E(dE, nodi_in, nn, D_STAT, sorgente=sorgente_di(dE.get("contesto", "")))
    if any(n.startswith("F0p") or n.startswith("Fp_") for n in richiesti):
        fEp = ctx["ck"]["E1"](c, p, s, st); dEp, nodi_in2, imp["E1"] = carica_E(fEp, D_STAT)
        M["F0p"], _ = da_E1(dEp, nodi_in2, nn, "token")
        for nome in richiesti:
            if nome.startswith("Fp_"):
                L = int(nome.split("_")[1])
                o_L = GR.origini_acquisizione(ok, t0, t0 + L)
                m, forn = da_E1(dEp, nodi_in2, nn, "token")
                adatta(m, forn, lotti_episodio(x, D["classe"], stat, nn, o_L), w_t, cfgF["passo"], cfgF["aggiornamenti"])
                M[nome] = m
    return M, imp


def _cella(args):
    nome_ctx, c, p, s, ep_nome, out, fili, soglie = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.analizza_copertura_e4 import celle_valide
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import _canali, _carica, _normalizzazione, _partizioni
    from evoluzione.esperimenti.esegui_e2 import valuta
    from evoluzione.esperimenti.inserimento import statiche
    out = Path(out)
    g = out / DIR_PRED / f"{ep_nome}_{c}_p{p}_s{s}.npz"
    if g.exists():
        return {"c": c, "p": p, "s": s, "ep": ep_nome, "esito": "presente", "secondi": 0}
    t_in = time.time()
    try:
        ctx = CONTESTI_E8[nome_ctx](out)
        ep_cal = "prova" if ep_nome == "curva" else ep_nome      # E8-bis: le curve sono sul test
        D = _carica(c, out / "maschere"); ok = GR.passi_regolari(D["ts"])
        e = D["r"].shape[0] - GR.MAX_ORIZZ
        t0, t1, fine, chiave = ctx["calendario"](c, ep_cal)
        fine = e if fine is None else (int(e * .85) if fine == "quota85" else fine)
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(ctx["seme_partizione"](p))}, ctx["fine_periodo"])
        nn = nodi[chiave]; K = len(nn)
        per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
        NORM, nr, nv = _normalizzazione(D, nodi, ist); x = _canali(D, nr, nv); stat = statiche(D)
        pesi = np.asarray(carica_pesi(out / ctx["dir_pesi"], c, p).vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32); S = torch.as_tensor(stat[nn])
        eta = per - t0
        fasce = [eta <= FASCE_ETA[0], (eta > FASCE_ETA[0]) & (eta <= FASCE_ETA[1]), eta > FASCE_ETA[1]]
        cv, _ = celle_valide(D, nn, GR.origini_acquisizione(ok, t0, t1), t0, t1)
        M, imp = _modelli(ctx, c, p, s, out, D, nodi, nn, ok, x, stat, w_t, t0, ep_cal)
        H = None; ris = {}; controllo = {}
        for nome, m in M.items():
            PB, YY, MM, w, ph, dt = valuta(m, x, D["classe"], nn, per, S, pesi)
            H = MM.shape[2]
            # A/B per nodo e CONTROLLO contro l'aggregato congelato
            pr = np.clip(PB, 1e-12, 1.0)
            ce = -np.log(np.take_along_axis(pr, YY[..., None].astype("int64"), -1)[..., 0])
            wgt = pesi[YY.astype("int64")] * MM
            A = (ce * wgt).sum(0); B = wgt.sum(0)
            ris[f"A_{nome}"] = A.astype("float64"); ris[f"B_{nome}"] = B.astype("float64")
            if ep_nome in ("prova", "curva"):
                ris[f"AF_{nome}"] = np.stack([(ce * wgt)[fm].sum(0) for fm in fasce]).astype("float64")
                ris[f"BF_{nome}"] = np.stack([wgt[fm].sum(0) for fm in fasce]).astype("float64")
            cong = ctx["congelato"](c, p, s, ep_cal, nome)
            if cong is not None:
                f_c, kA, kB, somma = cong
                if not f_c.exists():
                    raise RuntimeError(f"controllo 1: manca l'aggregato congelato {f_c}")
                zc = np.load(f_c, allow_pickle=True)
                if somma == "fascia2":
                    # perimetro congelato = origini con eta' > 1 settimana
                    sel = fasce[2]; per_c = per[sel]
                    A_mio, B_mio = (ce * wgt)[sel].sum(0), wgt[sel].sum(0)
                else:
                    per_c, A_mio, B_mio = per, A, B
                if not (np.array_equal(zc["nodi"].astype("int64"), np.asarray(nn, dtype="int64"))
                        and np.array_equal(zc["origini"].astype("int64"), per_c)):
                    raise RuntimeError(f"controllo 2, {nome}: nodi od origini diversi da {f_c.name}")
                Ac, Bc = zc[kA], zc[kB]
                if somma is True:
                    Ac, Bc = Ac[:3].sum(0), Bc[:3].sum(0)
                mio, loro = _wce_per_oriz(A_mio, B_mio), _wce_per_oriz(Ac, Bc)
                rel = float(np.nanmax(np.abs(mio - loro) / np.maximum(np.abs(loro), 1e-12)))
                controllo[nome] = {"scarto_relativo_max": rel, "file": f_c.name}
                if rel > TOLLERANZA:
                    raise RuntimeError(f"controllo 1, {nome}: scarto relativo {rel:.2e} oltre {TOLLERANZA:g} ({f_c.name})")
            if ep_nome == "validazione":
                # confusione sommata (nodi, orizzonti, origini) per ogni soglia, piu' argmax
                grid = np.zeros((len(SOGLIE), 3, 3), dtype="int64")
                tutte = [np.ones(len(per), dtype=bool)]
                for i, t in enumerate(SOGLIE):
                    grid[i] = confusione(predizione(PB, "prim", t), YY, MM, tutte, K, H)[0].sum((0, 1))
                ris[f"griglia_{nome}"] = grid
                ris[f"argmax_{nome}"] = confusione(predizione(PB, "argmax", None), YY, MM, tutte, K, H)[0].sum((0, 1))
            elif ep_nome == "curva":
                # E8-bis: confusione PER NODO a ogni soglia, tutte le origini e eta' > 1 sett.
                due = [np.ones(len(per), dtype=bool), fasce[2]]
                G = np.zeros((len(SOGLIE), 2, K, 3, 3), dtype="int64")
                for i, t in enumerate(SOGLIE):
                    G[i] = confusione(predizione(PB, "prim", t), YY, MM, due, K, H).sum(2)
                ris[f"griglia_{nome}"] = G[:, 0]; ris[f"griglia7_{nome}"] = G[:, 1]
            else:
                sg = soglie[ctx["gruppo"](c)][nome]
                for regola in REGOLE:
                    t = None if regola == "argmax" else sg[regola]
                    ris[f"conf_{regola}_{nome}"] = confusione(predizione(PB, regola, t), YY, MM, fasce, K, H)
            del PB, YY, MM
        g.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            g, nodi=np.asarray(nn, dtype="int32"), origini=per.astype("int32"), eta=eta.astype("int32"),
            celle_valide=cv.astype("int32"), fasce=np.asarray([int(f.sum()) for f in fasce]),
            contesto=c, partizione=p, seme=s, episodio=ep_nome, gruppo=ctx["gruppo"](c), t0=t0, t1=t1, fine=fine,
            modelli=json.dumps(list(M)), impronte_ck=json.dumps(imp), controllo=json.dumps(controllo),
            soglie=json.dumps(soglie.get(ctx["gruppo"](c)) if soglie else None),
            impronta_soglie=(soglie or {}).get("_impronta", ""), **ris)
        return {"c": c, "p": p, "s": s, "ep": ep_nome, "esito": "ok", "secondi": time.time() - t_in,
                "controlli": len(controllo), "scarto_max": max([v["scarto_relativo_max"] for v in controllo.values()] or [0.0])}
    except Exception as ex:                                  # noqa: BLE001
        return {"c": c, "p": p, "s": s, "ep": ep_nome, "esito": "fallita", "errore": f"{type(ex).__name__}: {ex}"[:300],
                "secondi": time.time() - t_in}


def _celle(out: Path, contesti, ep_nome, pilota: bool, fili: int, soglie):
    celle = []
    for nome in contesti:
        ctx = CONTESTI_E8[nome](out)
        uu = ctx["unita"][:1] if pilota else ctx["unita"]
        if pilota and nome == "citta":
            uu = [u for u in ctx["unita"] if u[0] == "Londra"][:1] or uu
        celle += [(nome, c, p, s, ep_nome, str(out), fili, soglie) for (c, p, s) in uu]
    return celle


def fase_celle(out: Path, contesti, ep_nome, lavoratori, fili, piano, pilota) -> int:
    soglie = None
    if ep_nome == "prova":
        f = out / "e8_soglie.json"
        if not f.exists():
            raise RuntimeError("la prova richiede e8_soglie.json (--fase soglie)")
        soglie = json.loads(f.read_text())
    celle = _celle(out, contesti, ep_nome, pilota, fili, soglie)
    fatte = sum((out / DIR_PRED / f"{ep_nome}_{c}_p{p}_s{s}.npz").exists() for _, c, p, s, *_ in celle)
    print(f"  episodio {ep_nome}: {len(celle)} celle ({', '.join(contesti)}){' — PILOTA' if pilota else ''}, "
          f"{fatte} gia' fatte; controllo 1 a {TOLLERANZA:g} su ogni aggregato congelato")
    if piano:
        return 0
    ctx = mp.get_context("spawn"); t0 = time.time(); fall = 0
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_cella, celle), 1):
            if r["esito"] == "fallita":
                fall += 1; print(f"  [{i:3d}/{len(celle)}] {r['c']} p{r['p']} s{r['s']} FALLITA {r['errore']}", flush=True)
            elif r["esito"] == "ok":
                print(f"  [{i:3d}/{len(celle)}] {r['c']:10s} p{r['p']} s{r['s']} ok  controlli {r['controlli']} "
                      f"(scarto max {r['scarto_max']:.1e})  {r['secondi']:5.0f}s", flush=True)
    print(f"\n  {len(celle) - fall} celle, {fall} fallite, {(time.time() - t0)/60:.1f} min")
    return 0 if not fall else 1


# ------------------------------------------------------------------ soglie --
def fase_soglie(out: Path, contesti) -> int:
    import numpy as np
    f_out = out / "e8_soglie.json"
    if f_out.exists():
        print(f"  {f_out} esiste: non si sovrascrive (le soglie si scelgono una volta)"); return 0
    S = {}
    for nome in contesti:
        ctx = CONTESTI_E8[nome](out)
        grid, argm = {}, {}
        for (c, p, s) in ctx["unita"]:
            g = out / DIR_PRED / f"validazione_{c}_p{p}_s{s}.npz"
            if not g.exists():
                raise RuntimeError(f"cella di validazione assente: {g}")
            z = np.load(g, allow_pickle=True); gr = ctx["gruppo"](c)
            for m in json.loads(str(z["modelli"])):
                grid.setdefault(gr, {}).setdefault(m, np.zeros((len(SOGLIE), 3, 3), dtype="int64"))
                grid[gr][m] += z[f"griglia_{m}"]
        for gr, GM in grid.items():
            if "C" not in GM:
                raise RuntimeError(f"{gr}: manca C in validazione")
            # primaria: F1 della congestionata, a parita' la soglia piu' alta
            sog = {}
            for m, G in GM.items():
                f1 = [metriche(G[i])["f1_congestionata"] for i in range(len(SOGLIE))]
                i_best = max(range(len(SOGLIE)), key=lambda i: (round(f1[i], 12), SOGLIE[i]))
                sog[m] = {"prim": SOGLIE[i_best], "f1_val": f1[i_best],
                          "far_val_prim": metriche(G[i_best])["falsi_allarmi"]}
            far_C = sog["C"]["far_val_prim"]
            for m, G in GM.items():
                far = [metriche(G[i])["falsi_allarmi"] for i in range(len(SOGLIE))]
                i_par = min(range(len(SOGLIE)), key=lambda i: (round(abs(far[i] - far_C), 12), -SOGLIE[i]))
                sog[m]["par"] = SOGLIE[i_par]; sog[m]["far_val_par"] = far[i_par]
                sog[m]["richiamo_val_par"] = metriche(G[i_par])["richiamo"]
            # R-orig(1 sett.) eredita le soglie di F'(1 sett.); A quelle di C (protocollo,
            # deviazione del 9/10: A non ha i nodi di validazione in tabella)
            if "Fp_672" in sog and "Rorig_672" not in sog:
                sog["Rorig_672"] = {**sog["Fp_672"], "ereditata_da": "Fp_672"}
            if "A" not in sog:
                sog["A"] = {**sog["C"], "ereditata_da": "C"}
            S[gr] = sog
            print(f"  {gr:10s} " + "  ".join(f"{m}: prim {v['prim']:.2f} par {v['par']:.2f}" for m, v in sog.items()))
    doc = {"griglia": SOGLIE, "regola_primaria": "massimo F1 della classe congestionata su validazione, "
                                                "matrici sommate sulle celle; a parita' la soglia piu' alta",
           "regola_parita": "tasso di falsi allarmi uguale a quello di C alla sua soglia primaria; a parita' la piu' alta",
           "soglie": S, "istante": datetime.now(timezone.utc).isoformat()}
    doc["_impronta"] = _impronta(json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True))
    doc_piatto = {**S, "_impronta": doc["_impronta"], "_regole": {k: doc[k] for k in ("griglia", "regola_primaria", "regola_parita")},
                  "_istante": doc["istante"]}
    _scrivi_atomico(f_out, json.dumps(doc_piatto, indent=2, ensure_ascii=False))
    print(f"  salvato in {f_out}; impronta {doc['_impronta']}")
    return 0


# -------------------------------------------------------------------- test --
def _gated_conf(z, regola, tau, N):
    """Confusione (F, K, H, 3, 3) della politica gated composta per fascia e nodo."""
    import numpy as np
    C0 = z[f"conf_{regola}_F0p"]
    if tau is None:
        C = C0.copy()
    else:
        Ct = z[f"conf_{regola}_Fp_{tau}"]; da = {96: 0, 192: 1, 672: 2}[tau]
        C = C0.copy(); C[da:] = Ct[da:]
    sotto = z["celle_valide"] < N
    C[:, sotto] = C0[:, sotto]
    return C


def fase_test(out: Path, contesti) -> dict:
    import numpy as np
    SG = json.loads((out / "e8_soglie.json").read_text())
    CONF = {"A-C": ("A", "C", None), "F0-C": ("F0", "C", None), "F0p-C": ("F0p", "C", None),
            "Fp_96-C": ("Fp_96", "C", None), "Fp_672-C_eta>1sett": ("Fp_672", "C", 2),
            "gated-F0p": ("gated", "F0p", None), "Rorig_672-Fp_672_eta>1sett": ("Rorig_672", "Fp_672", 2)}
    MET = ("richiamo", "precisione", "falsi_allarmi", "f1_macro")
    R = {"impronta_soglie": SG["_impronta"], "repliche": B_BOOT, "gruppi": {}}
    for nome in contesti:
        ctx = CONTESTI_E8[nome](out)
        celle = {}
        for (c, p, s) in ctx["unita"]:
            g = out / DIR_PRED / f"prova_{c}_p{p}_s{s}.npz"
            with np.load(g, allow_pickle=True) as z:
                d = {k: z[k] for k in z.files}
            if str(d["impronta_soglie"]) != SG["_impronta"]:
                raise RuntimeError(f"{g.name}: impronta delle soglie diversa da e8_soglie.json")
            celle[(ctx["gruppo"](c), p, s)] = d
        for gr in sorted({k[0] for k in celle}):
            cc = {k: z for k, z in celle.items() if k[0] == gr}
            sc = ctx["gated"](gr if nome != "citta" else gr)
            tau, N = sc["tau"], sc["N"]
            modelli = json.loads(str(next(iter(cc.values()))["modelli"]))
            rng = np.random.default_rng(ctx["seme_boot"])
            print(f"\n{gr}: {len(cc)} celle; gated(tau={tau}, N={N})")
            RG = {"celle": len(cc), "gated": {"tau": tau, "N": N}, "livelli": {}, "confronti": {}}

            def conf_di(z, n, regola, fascia, idx):
                C = _gated_conf(z, regola, tau, N) if n == "gated" else z[f"conf_{regola}_{n}"]
                C = C.sum(0) if fascia is None else C[fascia]            # (K,H,3,3)
                if idx is not None:
                    C = C[idx]
                return C.sum((0, 1))                                      # (3,3)
            def wce_di(z, n, fascia, idx):
                if n == "gated":
                    A0, B0 = z["AF_F0p"], z["BF_F0p"]
                    if tau is None:
                        A, Bm = A0.copy(), B0.copy()
                    else:
                        da = {96: 0, 192: 1, 672: 2}[tau]
                        A, Bm = A0.copy(), B0.copy(); A[da:] = z[f"AF_Fp_{tau}"][da:]; Bm[da:] = z[f"BF_Fp_{tau}"][da:]
                    sotto = z["celle_valide"] < N
                    A[:, sotto] = A0[:, sotto]; Bm[:, sotto] = B0[:, sotto]
                else:
                    A, Bm = z[f"AF_{n}"], z[f"BF_{n}"]
                A = A.sum(0) if fascia is None else A[fascia]; Bm = Bm.sum(0) if fascia is None else Bm[fascia]
                return (A, Bm) if idx is None else (A[idx], Bm[idx])
            for nome_c, (n1, n2, fascia) in CONF.items():
                if (n1 not in modelli and n1 != "gated") or n2 not in modelli:
                    continue
                r = _boot(cc, lambda z, idx, _a=n1, _b=n2, _f=fascia: _wce(*wce_di(z, _a, _f, idx)) - _wce(*wce_di(z, _b, _f, idx)), rng)
                lo, hi = r["ic_con_nodi"]; r["segno"] = "-" if hi < 0 else ("+" if lo > 0 else "0")
                RG["confronti"].setdefault(nome_c, {})["wce"] = r
                print(f"  [wce   ] {nome_c:28s} {r['media']:+.4f} [{lo:+.4f}, {hi:+.4f}]  segno {r['segno']}", flush=True)
            for regola in REGOLE:
                for n in list(modelli) + ["gated"]:
                    if n == "gated" and "F0p" not in modelli:
                        continue
                    tot = sum(conf_di(z, n, regola, None, None) for z in cc.values())
                    RG["livelli"][f"{regola}/{n}"] = metriche(tot)
                for nome_c, (n1, n2, fascia) in CONF.items():
                    if (n1 not in modelli and n1 != "gated") or n2 not in modelli:
                        continue
                    RG["confronti"].setdefault(nome_c, {})[regola] = {}
                    for met in MET:
                        def f_pair(z, idx, _n1=n1, _n2=n2, _f=fascia, _m=met, _r=regola):
                            return metriche(conf_di(z, _n1, _r, _f, idx))[_m] - metriche(conf_di(z, _n2, _r, _f, idx))[_m]
                        r = _boot(cc, f_pair, rng)
                        lo, hi = r["ic_con_nodi"]
                        r["segno"] = "-" if hi < 0 else ("+" if lo > 0 else "0")
                        RG["confronti"][nome_c][regola][met] = r
                    rr = RG["confronti"][nome_c][regola]
                    print(f"  [{regola:6s}] {nome_c:28s} richiamo {rr['richiamo']['media']:+.3f} "
                          f"[{rr['richiamo']['ic_con_nodi'][0]:+.3f}, {rr['richiamo']['ic_con_nodi'][1]:+.3f}]  "
                          f"falsi all. {rr['falsi_allarmi']['media']:+.4f}  F1-macro {rr['f1_macro']['media']:+.3f}", flush=True)
            R["gruppi"][gr] = RG
    R["istante"] = datetime.now(timezone.utc).isoformat()
    (out / "e8_risultati.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print(f"\n  salvato in {out / 'e8_risultati.json'}")
    return R


# ------------------------------------------------------------------ E8-bis --
LIVELLI_FA = (0.005, 0.01, 0.02, 0.05, 0.10)


def curva(G):
    """G (19, 3, 3) sommata sui nodi -> (far, richiamo) a ogni soglia, vettoriale."""
    import numpy as np
    G = np.asarray(G, dtype="float64")
    tp = G[:, CONG, CONG]; fn = G[:, CONG, :].sum(1) - tp; fp = G[:, :, CONG].sum(1) - tp
    tn = G.sum((1, 2)) - tp - fn - fp
    rich = tp / np.maximum(tp + fn, 1e-12); far = fp / np.maximum(fp + tn, 1e-12)
    return far, rich


def auc_e_richiami(G):
    """Area sotto la curva richiamo-falsi allarmi (trapezi, con gli estremi (0,0) e (1,1))
    e il richiamo interpolato ai livelli LIVELLI_FA (nan se il livello non e' raggiunto)."""
    import numpy as np
    far, rich = curva(G)
    o = np.argsort(far, kind="stable"); x = np.concatenate([[0.0], far[o], [1.0]]); y = np.concatenate([[0.0], rich[o], [1.0]])
    a = float(np.sum((x[1:] - x[:-1]) * (y[1:] + y[:-1]) / 2.0))
    xs, ys = far[o], rich[o]
    r = np.array([np.interp(fa, xs, ys) if xs.min() <= fa <= xs.max() else np.nan for fa in LIVELLI_FA])
    return a, r


def _boot_curve(cc, modelli, rng):
    """Ricampionamento congiunto (partizioni x semi x nodi) di AUC e richiami a FA fissati,
    per modello e per perimetro (intero, eta' > 1 sett.), in UN passaggio per replica."""
    import numpy as np
    kk = sorted(cc); parts = sorted({k[1] for k in kk}); semi = sorted({k[2] for k in kk})
    K = cc[kk[0]]["celle_valide"].shape[0]
    chiavi = [(n, sett) for n in modelli for sett in ("intero", "eta7")]
    def somma(sel_cells, nd):
        out = {}
        for n, sett in chiavi:
            key = f"griglia7_{n}" if sett == "eta7" else f"griglia_{n}"
            tot = None
            for k in sel_cells:
                G = cc[k][key] if nd is None else cc[k][key][:, nd]
                tot = G.sum(1) if tot is None else tot + G.sum(1)
            out[(n, sett)] = tot
        return out
    def stime(S):
        return {q: auc_e_richiami(G) for q, G in S.items()}
    punto = stime(somma(kk, None))
    rep = {q: ([], []) for q in chiavi}
    for _ in range(B_BOOT):
        ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
        nd = rng.integers(0, K, K)
        sel = [(kk[0][0], p, s) for p in ps for s in ss]
        for q, (a, r) in stime(somma(sel, nd)).items():
            rep[q][0].append(a); rep[q][1].append(r)
    return punto, {q: (np.asarray(v[0]), np.asarray(v[1])) for q, v in rep.items()}


def _ic_segno(v):
    import numpy as np
    v = np.asarray(v, dtype="float64"); v = v[np.isfinite(v)]
    if len(v) == 0:
        return None
    q = np.percentile(v, [2.5, 97.5])
    return {"ic_con_nodi": q.tolist(), "segno": "-" if q[1] < 0 else ("+" if q[0] > 0 else "0"), "repliche_valide": int(len(v))}


def fase_test_curve(out: Path, contesti) -> dict:
    import numpy as np
    CONF = {"A-C": ("A", "C", "intero"), "F0-C": ("F0", "C", "intero"), "F0p-C": ("F0p", "C", "intero"),
            "Fp_96-C": ("Fp_96", "C", "intero"), "Fp_672-C_eta>1sett": ("Fp_672", "C", "eta7"),
            "Rorig_672-Fp_672_eta>1sett": ("Rorig_672", "Fp_672", "eta7"), "F0p-F0": ("F0p", "F0", "intero")}
    R = {"repliche": B_BOOT, "livelli_fa": list(LIVELLI_FA), "gruppi": {}}
    for nome in contesti:
        ctx = CONTESTI_E8[nome](out)
        celle = {}
        for (c, p, s) in ctx["unita"]:
            g = out / DIR_PRED / f"curva_{c}_p{p}_s{s}.npz"
            with np.load(g, allow_pickle=True) as z:
                d = {k: z[k] for k in z.files}
            celle[(ctx["gruppo"](c), p, s)] = d
        for gr in sorted({k[0] for k in celle}):
            cc = {k: z for k, z in celle.items() if k[0] == gr}
            modelli = json.loads(str(next(iter(cc.values()))["modelli"]))
            rng = np.random.default_rng(ctx["seme_boot"] + 7)
            print(f"\n{gr}: {len(cc)} celle (curve, {B_BOOT} repliche)", flush=True)
            punto, rep = _boot_curve(cc, modelli, rng)
            RG = {"celle": len(cc), "auc": {f"{n}/{sett}": punto[(n, sett)][0] for (n, sett) in punto},
                  "richiamo_a_fa": {f"{n}/{sett}": {str(fa): (None if not np.isfinite(v) else float(v))
                                                    for fa, v in zip(LIVELLI_FA, punto[(n, sett)][1])} for (n, sett) in punto},
                  "confronti": {}}
            for nome_c, (n1, n2, sett) in CONF.items():
                if n1 not in modelli or n2 not in modelli:
                    continue
                d_auc = rep[(n1, sett)][0] - rep[(n2, sett)][0]
                r = {"media": punto[(n1, sett)][0] - punto[(n2, sett)][0], **_ic_segno(d_auc)}
                rf = {}
                for j, fa in enumerate(LIVELLI_FA):
                    m1, m2 = punto[(n1, sett)][1][j], punto[(n2, sett)][1][j]
                    if not (np.isfinite(m1) and np.isfinite(m2)):
                        rf[str(fa)] = None; continue
                    ic = _ic_segno(rep[(n1, sett)][1][:, j] - rep[(n2, sett)][1][:, j])
                    rf[str(fa)] = None if ic is None else {"media": float(m1 - m2), **ic}
                RG["confronti"][nome_c] = {"auc": r, "richiamo_a_fa": rf}
                def _fmt(v):
                    return "n.d." if v is None else "%+.1f%s" % (100 * v["media"], v["segno"])
                print(f"  {nome_c:28s} ΔAUC {r['media']:+.4f} [{r['ic_con_nodi'][0]:+.4f}, {r['ic_con_nodi'][1]:+.4f}] {r['segno']}"
                      f"  Δrichiamo a FA: " + " ".join(f"{fa}:{_fmt(v)}" for fa, v in rf.items()), flush=True)
            R["gruppi"][gr] = RG
    R["istante"] = datetime.now(timezone.utc).isoformat()
    (out / "e8bis_risultati.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print(f"\n  salvato in {out / 'e8bis_risultati.json'}")
    return R


def main() -> int:
    ap = argparse.ArgumentParser(description="E8 metriche operative")
    ap.add_argument("--fase", choices=("validazione", "soglie", "prova", "test", "curve", "test-curve"), required=True)
    ap.add_argument("--contesto", nargs="*", choices=list(CONTESTI_E8), default=list(CONTESTI_E8))
    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--pilota", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    print("=" * 84); print(f"E8 — metriche operative, fase {a.fase} ({', '.join(a.contesto)})"); print("=" * 84)
    if a.fase in ("validazione", "prova", "curve"):
        return fase_celle(a.out, a.contesto, "curva" if a.fase == "curve" else a.fase,
                          a.lavoratori, a.fili, a.piano, a.pilota)
    if a.fase == "test-curve":
        fase_test_curve(a.out, a.contesto); return 0
    if a.fase == "soglie":
        return fase_soglie(a.out, a.contesto)
    fase_test(a.out, a.contesto); return 0


if __name__ == "__main__":
    raise SystemExit(main())
