#!/usr/bin/env python3
"""
E5 — Piu' episodi d'inserimento (protocol/E5.md).
==================================================
Cinque fasi, nell'ordine; ciascuna verifica i prerequisiti della precedente.

    --fase prepara       ricalcola i nove t0 (regola meccanica) e si ferma se
                         differiscono da preparazione_e5.json; conta per
                         citta' le origini nominali/escluse/ammissibili del
                         periodo di prova e STAMPA le origini escluse col salto
                         a cui corrispondono; pesi di classe per episodio
                         (pesi_griglia_ep2, pesi_griglia_ep3)
    --fase k-secondaria  k per citta' dalla traiettoria di F'(24 h) calcolata
                         SULL'EPISODIO DI VALIDAZIONE ESTESO di E4 (mai dal
                         test); scrive e5_k_secondaria.json con impronta
    --fase addestra      C, A, E' per gli episodi 2 e 3: 3 x 18 x 2 = 108
                         addestramenti, budget 2.290, parallelo, ripresa dai
                         marcatori, tempo di parete come assert
    --fase valuta        per cella ed episodio: C, A, F0', F'(24 h), F'(48 h),
                         F'(1 sett.), F'(24 h, k) su tutte le origini dopo t1;
                         aggregati per fascia d'eta' e per terzo; controlli
    --fase test          le affermazioni (a)-(e) per citta' x episodio con
                         ricampionamento congiunto; nodi sotto N; stesso segno
                         in 3/3; e5_risultati.json

Episodio 1 = la campagna principale: C, A, E' e gli aggregati di E4 si
riusano (semi 201-206); A viene dalle predizioni ricostruite di E3.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_e5.py --fase prepara --piano
    poetry run python evoluzione/esperimenti/esegui_e5.py --fase prepara
    poetry run python evoluzione/esperimenti/esegui_e5.py --fase k-secondaria --lavoratori 8
    poetry run python evoluzione/esperimenti/esegui_e5.py --fase addestra --piano
    poetry run python evoluzione/esperimenti/esegui_e5.py --fase addestra --lavoratori 8
    poetry run python evoluzione/esperimenti/esegui_e5.py --fase valuta --lavoratori 8
    poetry run python evoluzione/esperimenti/esegui_e5.py --fase test
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

from evoluzione.componente.bracci import proprieta as proprieta_braccio  # noqa: E402
from evoluzione.esperimenti.esegui_e4 import (  # noqa: E402
    CITTA, D_STAT, FASCE_ETA, PUNTI_TRAIETTORIA, _aggregati, _boot,
    _nome_e_token, _politica, _wce, calendario)

EPISODI = (1, 2, 3)
NUOVI = (2, 3)                                   # gli episodi da addestrare
SEMI_E5 = (201, 202, 203, 204, 205, 206)         # i sei con identificativo piu' basso
DURATE = (96, 192, 672)                          # 24 h, 48 h (tau di Madrid e Londra), 1 sett.
MODELLI_BASE = ("C", "A", "F0p") + tuple(f"Fp_{L}" for L in DURATE) + ("Fp_96k",)
DIR_PRED = "predizioni_e5"
RHO = 0.15
B_BOOT, SEME_BOOT = 4000, 20261007
L24 = 96


def _impronta_testo(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()[:16]


def _scrivi_atomico(f: Path, testo: str):
    tmp = f.with_name(f.name + ".tmp")
    with open(tmp, "w") as h:
        h.write(testo); h.flush(); os.fsync(h.fileno())
    os.replace(tmp, f)


# ------------------------------------------------------------- calendario --
def episodi_registrati(out: Path) -> dict:
    """{citta: {k: {t0, t1, fine}}} da preparazione_e5.json."""
    f = out / "preparazione_e5.json"
    if not f.exists():
        raise RuntimeError(f"manca {f}: eseguire preparazione_e5.py --calendario")
    R = json.loads(f.read_text())["calendario"]
    fuori = {}
    for c in CITTA:
        fuori[c] = {}
        for z in R[c]["episodi"]:
            if not z.get("fattibile", True):
                continue
            fuori[c][int(z["episodio"])] = {"t0": int(z["t0"]), "t1": int(z["t1"]),
                                             "fine": int(z["fine_valutazione"])}
        if set(fuori[c]) != set(EPISODI):
            raise RuntimeError(f"{c}: episodi registrati {sorted(fuori[c])}, attesi {EPISODI}")
    return fuori


def etichette(k: int) -> dict:
    """Le cartelle di un episodio: l'1 e' la campagna principale."""
    E_TOK = _nome_e_token()
    if k == 1:
        return {"ins": "inserimento_griglia", "E": f"{E_TOK}_inserimento_griglia",
                "pesi": "pesi_griglia"}
    return {"ins": f"inserimento_griglia_ep{k}", "E": f"{E_TOK}_inserimento_griglia_ep{k}",
            "pesi": f"pesi_griglia_ep{k}"}


def _fine_periodo(k: int, ep: dict):
    """`fine_periodo` per `_partizioni`: None per l'episodio 1."""
    return None if k == 1 else ep[k]["t0"]


# ---------------------------------------------------------------- prepara --
def _salti_delle_escluse(ok, amm, t1: int, fine: int):
    """Le origini del periodo (t1, fine) non ammissibili, ciascuna con la
    posizione del salto che la esclude e la sua durata."""
    import numpy as np
    from evoluzione.componente import griglia as GR
    T = len(ok) + 1
    nominali = [t for t in range(t1 + 1, fine) if t + GR.MAX_ORIZZ < fine]
    escluse = [t for t in nominali if not amm[t]]
    righe = []
    for t in escluse:
        a, b = t - GR.FINESTRA + 1, t + GR.MAX_ORIZZ
        salti = [int(i) for i in range(max(a, 0), min(b, T - 1)) if not ok[i]]
        righe.append({"origine": int(t), "salti_fra_righe": salti})
    return len(nominali), escluse, righe


def fase_prepara(out: Path, piano: bool):
    import numpy as np
    from evoluzione.analisi.pesi import calcola as calcola_pesi, carica as carica_pesi, salva as salva_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.predittore import ORIZZONTI
    from evoluzione.esperimenti.addestramento import _carica, _partizioni
    from evoluzione.esperimenti.preparazione_e5 import calendario as ricalcola
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    ep = episodi_registrati(out)
    # CONTROLLO 1: i t0 ricalcolati coincidono con quelli registrati
    R = ricalcola(out)
    for c in CITTA:
        for z in R[c]["episodi"]:
            k = int(z["episodio"])
            if (int(z["t0"]), int(z["t1"]), int(z["fine_valutazione"])) != \
                    (ep[c][k]["t0"], ep[c][k]["t1"], ep[c][k]["fine"]):
                raise RuntimeError(f"{c} ep{k}: t0 ricalcolato {z['t0']} diverso dal "
                                   f"registrato {ep[c][k]['t0']}")
    print("\n  controllo 1: i nove t0 ricalcolati coincidono con preparazione_e5.json")
    rapporto = {"origini_prova": {}, "pesi": {}}
    for c in CITTA:
        D = _carica(c, out / "maschere")
        ts = D["ts"]
        ok = GR.passi_regolari(ts)
        amm = GR.maschera_origini(ok)
        T = D["r"].shape[0]
        # righe contro origini: il conto di protocol/E5.md, rifatto
        e = T - GR.MAX_ORIZZ
        righe_prova = e - int(e * .85)
        t1, fine = ep[c][1]["t1"], ep[c][1]["fine"]
        n_nom, escluse, dett = _salti_delle_escluse(ok, amm, t1, fine)
        n_amm = len(GR.origini_dopo(ok, t1, fine))
        if n_nom - len(escluse) != n_amm:
            raise RuntimeError(f"{c}: conteggio incoerente {n_nom} - {len(escluse)} != {n_amm}")
        print(f"\n{c}: periodo di prova {righe_prova} righe; origini nominali {n_nom}, "
              f"escluse per salto {len(escluse)}, ammissibili {n_amm}")
        # i salti distinti che escludono origini, con durata e numero di origini colpite
        per_salto = {}
        for r in dett:
            for i in r["salti_fra_righe"]:
                per_salto.setdefault(i, []).append(r["origine"])
        for i in sorted(per_salto):
            durata = (ts[i + 1] - ts[i])
            print(f"    salto fra le righe {i} e {i + 1} ({ts[i]} -> {ts[i + 1]}, "
                  f"{durata}): esclude {len(per_salto[i])} origini "
                  f"[{min(per_salto[i])}..{max(per_salto[i])}]")
        rapporto["origini_prova"][c] = {
            "righe_periodo_prova": int(righe_prova), "nominali": n_nom,
            "escluse": len(escluse), "ammissibili": n_amm,
            "salti": {str(i): {"da": str(ts[i]), "a": str(ts[i + 1]),
                               "origini_escluse": len(v)} for i, v in per_salto.items()}}
        # pesi per episodio (2, 3), piu' la verifica che l'episodio 1 sia quello di sempre
        for p in (0, 1, 2):
            # UN GENERATORE NUOVO PER OGNI CHIAMATA: `_partizioni` lo consuma,
            # e riusarlo darebbe una permutazione diversa dei nodi
            def gen():
                return {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])}
            nodi, ist = _partizioni(D, gen())
            P1 = carica_pesi(out / "pesi_griglia", c, p)
            if P1.periodo_addestramento != [int(GR.filtra(ist["addestramento"], amm)[0]),
                                            int(GR.filtra(ist["addestramento"], amm)[-1])]:
                raise RuntimeError(f"{c} p{p}: il periodo dei pesi del principale non e' "
                                   f"quello di _partizioni senza `fine`")
            for k in NUOVI:
                nodi_k, ist_k = _partizioni(D, gen(), _fine_periodo(k, ep[c]))
                if not np.array_equal(nodi_k["prova"], nodi["prova"]):
                    raise RuntimeError("i nodi cambiano con `fine`: non devono")
                orig = GR.filtra(ist_k["addestramento"], amm)
                P = calcola_pesi(c, p, D["classe"], nodi_k["addestramento"], orig,
                                 ORIZZONTI, versione_codice=f"griglia_reale_ep{k}")
                d_p = out / etichette(k)["pesi"]
                f_p = d_p / f"pesi_{c}_p{p}.json"
                if f_p.exists():
                    Pv = carica_pesi(d_p, c, p)
                    if Pv.impronta != P.impronta:
                        raise RuntimeError(f"{f_p} esiste con impronta diversa: non si sovrascrive")
                elif not piano:
                    salva_pesi(P, d_p)
                rapporto["pesi"][f"{c}/p{p}/ep{k}"] = {
                    "origini_addestramento": int(len(orig)), "pesi": P.pesi,
                    "periodo": P.periodo_addestramento, "impronta": P.impronta,
                    "pesi_ep1": P1.pesi}
                print(f"    p{p} ep{k}: addestramento [{ist_k['addestramento'][0]}, "
                      f"{ist_k['addestramento'][-1]}] ({len(orig)} origini amm.), selezione "
                      f"[{ist_k['validazione'][0]}, {ist_k['validazione'][-1]}], pesi "
                      f"{np.round(P.pesi, 4).tolist()} (ep1 {np.round(P1.pesi, 4).tolist()})"
                      + ("" if piano else "  salvati"))
    if not piano:
        (out / "e5_prepara.json").write_text(json.dumps(
            {**rapporto, "istante": datetime.now(timezone.utc).isoformat()}, indent=2,
            ensure_ascii=False))
        print(f"\n  salvato in {out / 'e5_prepara.json'}")


# ----------------------------------------------------------- k secondaria --
def _k_cella(args):
    """F'(24 h) sull'episodio di validazione esteso di E4, con il gancio:
    wCE integrata ai punti della traiettoria."""
    c, p, s, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import adatta, carica_E
    from evoluzione.componente.episodio import lotti_episodio
    from evoluzione.esperimenti.addestramento import _canali, _carica, _normalizzazione, _partizioni
    from evoluzione.esperimenti.esegui_e2 import da_E1, valuta
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    from evoluzione.esperimenti.fasi import percorso_E
    from evoluzione.esperimenti.inserimento import statiche
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, seme_torch
    out = Path(out)
    t_in = time.time()
    try:
        E_TOK = _nome_e_token()
        t0, t1 = calendario("validazione", c)
        D = _carica(c, out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        fine = CALENDARIO[c][0]
        per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])})
        nn = nodi["validazione"]
        NORM, nr, nv = _normalizzazione(D, nodi, ist)
        x = _canali(D, nr, nv)
        stat = statiche(D)
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
        cfgF = json.loads((out / "selezione_F_griglia" / "configurazione_F.json")
                          .read_text())["scelte"][c]
        dEp, nodi_in, imp = carica_E(
            percorso_E(out / f"{E_TOK}_inserimento_griglia", c, p, seme_torch(s), braccio=E_TOK), D_STAT)
        if set(int(z) for z in nodi_in) & set(int(z) for z in nn):
            raise RuntimeError("nodi di validazione nella mappa di E'")
        m, forn = da_E1(dEp, nodi_in, nn, "token")
        _, _, _, w0, _, _ = valuta(m, x, D["classe"], nn, per, S, pesi)
        traj = {"0": float(w0)}

        def gancio(k, perdita, _m=m):
            if k in PUNTI_TRAIETTORIA:
                with torch.inference_mode():
                    _, _, _, w_, _, _ = valuta(_m, x, D["classe"], nn, per, S, pesi)
                traj[str(k)] = float(w_)
        lotti = lotti_episodio(x, D["classe"], stat, nn, GR.origini_acquisizione(ok, t0, t1))
        n = adatta(m, forn, lotti, w_t, cfgF["passo"], cfgF["aggiornamenti"], gancio=gancio)
        traj[str(n)] = traj.get(str(n), float(valuta(m, x, D["classe"], nn, per, S, pesi)[3]))
        return {"c": c, "p": p, "s": s, "esito": "ok", "traiettoria": traj,
                "origini": int(len(per)), "nodi": int(len(nn)), "impronta_Ep": imp,
                "secondi": time.time() - t_in}
    except Exception as e:                                   # noqa: BLE001
        return {"c": c, "p": p, "s": s, "esito": "fallita",
                "errore": f"{type(e).__name__}: {e}"[:300], "secondi": time.time() - t_in}


def fase_k_secondaria(out: Path, lavoratori: int, fili: int, piano: bool):
    import numpy as np
    from evoluzione.esperimenti.semi import configurazione
    _, dich, _ = configurazione(inserimento=True)
    f = out / "e5_k_secondaria.json"
    celle = [(c, p, int(s), str(out), fili) for c in CITTA for p in (0, 1, 2) for s in dich]
    print(f"  {len(celle)} celle (episodio di validazione esteso di E4, nodi di validazione, "
          f"12 semi); punti {PUNTI_TRAIETTORIA} troncati alla configurazione")
    if piano:
        return
    ctx = mp.get_context("spawn"); t0 = time.time(); ris = []
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_k_cella, celle), 1):
            ris.append(r)
            if r["esito"] == "fallita":
                print(f"  [{i:3d}/{len(celle)}] {r['c']:10s} p{r['p']} s{r['s']} FALLITA {r['errore']}", flush=True)
            else:
                print(f"  [{i:3d}/{len(celle)}] {r['c']:10s} p{r['p']} s{r['s']} "
                      + " ".join(f"k{k} {v:.4f}" for k, v in sorted(r["traiettoria"].items(), key=lambda kv: int(kv[0])))
                      + f"  {r['secondi']:4.0f}s", flush=True)
    fall = [r for r in ris if r["esito"] == "fallita"]
    if fall:
        raise RuntimeError(f"{len(fall)} celle fallite: k non si sceglie su un campione parziale")
    scelta, curve = {}, {}
    for c in CITTA:
        rc = [r for r in ris if r["c"] == c]
        punti = sorted({int(k) for r in rc for k in r["traiettoria"]})
        media = {str(k): float(np.mean([r["traiettoria"][str(k)] for r in rc])) for k in punti
                 if all(str(k) in r["traiettoria"] for r in rc)}
        k_min = min((k for k in media if int(k) > 0), key=lambda k: (media[k], int(k)))
        scelta[c] = int(k_min); curve[c] = media
        print(f"  {c:11s} k = {k_min} (wCE validazione {media[k_min]:.5f}; "
              + ", ".join(f"k{k} {v:.4f}" for k, v in media.items()) + ")")
    doc = {"k": scelta, "curva_validazione": curve, "celle": len(ris),
           "regola": ("argmin della wCE integrata media sulle celle, lungo la traiettoria di "
                      "F'(24 h) sull'episodio di validazione esteso di E4; a parita' il k minore"),
           "istante": datetime.now(timezone.utc).isoformat()}
    doc["impronta"] = _impronta_testo(json.dumps(doc, indent=2, ensure_ascii=False))
    if f.exists():
        prec = json.loads(f.read_text())
        if prec.get("k") != scelta:
            raise RuntimeError(f"{f} esiste con k DIVERSI: non si sovrascrive")
        print(f"  k gia' registrati in {f}, identici"); return
    f.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"  k registrati in {f} (impronta {doc['impronta']}), prima di qualunque test")


# --------------------------------------------------------------- addestra --
class Esec:
    def __init__(self, c, p, variante=None):
        self.contesto, self.partizione = c, p
        self.inizializzazione, self.variante = 0, variante


def _cfg_episodio(b: str, c: str, p: int, s: int, k: int, out: Path, nodi, o_acq, t1, ep):
    """La configurazione di C e A viene da `cfg_braccio` (fase 3), quella di E'
    da quella di `esegui_E`; qui si cambiano SOLO cartelle, pesi e `fine_periodo`."""
    from evoluzione.esperimenti.inserimento import cfg_braccio
    from evoluzione.esperimenti.semi import seme_torch
    et = etichette(k)
    pb = proprieta_braccio(b)
    if pb.preparatorio:                       # E'
        cfg = {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
               "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
               "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
               "etichetta": et["E"], "braccio": b,
               **({"rho": RHO} if pb.richiede_rho else {}),
               "training_protocol": "principale", "griglia_temporale": "reale",
               "checkpoint_selection_population": "initial_network",
               "nome_ck": f"ck_{b}_{c}_p{p}_s{seme_torch(s)}.pt"}
    else:
        cfg = cfg_braccio(b, c, p, s, out, nodi, o_acq, t1=t1)
        cfg["etichetta"] = et["ins"]
    cfg.update({"dir_pesi": str(out / et["pesi"]), "dir_canonico": str(out / "canonico"),
                "dir_stati_completi": str(out / f"stati_completi_{cfg['etichetta']}"),
                "fine_periodo": ep[k]["t0"], "episodio": k})
    return cfg


def _addestra(args):
    x, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.registro import Registro
    from evoluzione.esperimenti.addestramento import _carica, _partizioni, addestra_una
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    out = Path(out)
    c, p, s, k, b = x["contesto"], x["partizione"], x["seme"], x["episodio"], x["braccio"]
    ep = episodi_registrati(out)[c]
    t_in = time.time()
    reg = Registro.avvia(f"{etichette(k)[ 'E' if proprieta_braccio(b).preparatorio else 'ins']}/{b}",
                         note=f"{c} p{p} seme {s} braccio {b} episodio {k}", radice=out / "registro")
    try:
        D = _carica(c, out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        t0, t1 = ep[k]["t0"], ep[k]["t1"]
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])},
                                _fine_periodo(k, ep))
        o_acq = GR.origini_acquisizione(ok, t0, t1)
        cfg = _cfg_episodio(b, c, p, s, k, out, nodi, o_acq, t1, ep)
        reg.configurazione({**cfg, **x})
        gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE[p]),
               "inizializzazione": np.random.default_rng(s)}
        addestra_una(Esec(c, p, cfg.get("variante")), reg, cfg, gen, out)
        ck = out / cfg["etichetta"] / cfg["nome_ck"]
        if not ck.exists():
            raise RuntimeError(f"punto di controllo atteso assente: {ck}")
        reg.completa()
        dt = time.time() - t_in
        _scrivi_atomico(ck.with_name(ck.name + ".fatto"), json.dumps(
            {**x, "secondi": dt, "istante": datetime.now(timezone.utc).isoformat()}, indent=2))
        return {**x, "esito": "completata", "secondi": dt}
    except Exception as e:                                   # noqa: BLE001
        reg.evento(f"{type(e).__name__}: {e}"); reg.completa("fallita")
        return {**x, "esito": "fallita", "secondi": time.time() - t_in,
                "errore": f"{type(e).__name__}: {e}"[:300]}


def _lavori_addestramento(out: Path):
    from evoluzione.esperimenti.semi import seme_torch
    E_TOK = _nome_e_token()
    ep = episodi_registrati(out)
    lav = []
    for k in NUOVI:
        for s in SEMI_E5:
            for p in (0, 1, 2):
                for c in CITTA:
                    for b in ("C", "A", E_TOK):
                        et = etichette(k)
                        nome = (f"ck_{b}_{c}_p{p}_s{seme_torch(s)}.pt" if proprieta_braccio(b).preparatorio
                                else f"ck_{b}_{c}_p{p}_s{s}.pt")
                        ck = out / (et["E"] if proprieta_braccio(b).preparatorio else et["ins"]) / nome
                        lav.append({"contesto": c, "partizione": p, "seme": int(s), "episodio": k,
                                    "braccio": b, "ck": str(ck), "t0": ep[c][k]["t0"]})
    return lav


def fase_addestra(out: Path, lavoratori: int, fili: int, piano: bool):
    lav = _lavori_addestramento(out)
    for k in NUOVI:
        for c in CITTA:
            if not (out / etichette(k)["pesi"] / f"pesi_{c}_p0.json").exists():
                raise RuntimeError(f"pesi dell'episodio {k} assenti per {c}: eseguire --fase prepara")
    fatti = [x for x in lav if Path(x["ck"] + ".fatto").exists()]
    da_fare = [x for x in lav if x not in fatti]
    print(f"  {len(lav)} addestramenti (episodi {NUOVI}, semi {SEMI_E5}, bracci C, A, "
          f"{_nome_e_token()}), {len(fatti)} gia' fatti, {len(da_fare)} da eseguire; budget 2.290, "
          f"canonico riusato, pesi per episodio, fine_periodo = t0 dell'episodio")
    if piano:
        for x in da_fare[:6]:
            print(f"     ep{x['episodio']} {x['contesto']:11s} p{x['partizione']} s{x['seme']} {x['braccio']}  t0 {x['t0']}")
        return 0
    ctx = mp.get_context("spawn"); t0 = time.time(); esiti = []
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_addestra, [(x, str(out), fili) for x in da_fare]), 1):
            esiti.append(r)
            trasc = time.time() - t0
            print(f"  [{i:3d}/{len(da_fare)}] ep{r['episodio']} {r['contesto']:11s} p{r['partizione']} "
                  f"s{r['seme']} {r['braccio']:3s} {r['esito']:10s} {r['secondi']/60:5.1f} min | "
                  f"trascorse {trasc/3600:4.1f} h, restano ~{trasc/i*(len(da_fare)-i)/3600:4.1f} h"
                  + (f"\n        {r['errore']}" if r["esito"] == "fallita" else ""), flush=True)
            lo, hi = proprieta_braccio(r["braccio"]).parete_attesa_min
            if r["esito"] == "completata" and not (lo <= r["secondi"] / 60 <= hi):
                print(f"\n  **FERMO IL LANCIO**: {r['secondi']/60:.1f} min fuori da [{lo:g}, {hi:g}]", flush=True)
                esiti.append({**r, "esito": "fuori_intervallo"}); pool.terminate(); break
    fall = [r for r in esiti if r["esito"] != "completata"]
    _scrivi_atomico(out / "esito_e5_addestra.json", json.dumps(
        {"completate": len(esiti) - len(fall), "fallite": fall, "gia_fatte": len(fatti),
         "ore_calendario": (time.time() - t0) / 3600, "lavoratori": lavoratori,
         "istante": datetime.now(timezone.utc).isoformat()}, indent=2, ensure_ascii=False))
    print(f"\n  {len(esiti) - len(fall)} completati, {len(fall)} falliti, {(time.time() - t0)/3600:.1f} h")
    return 0 if not fall else 1


# ----------------------------------------------------------------- valuta --
def _cella(args):
    c, p, s, k, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.analizza_copertura_e4 import celle_valide
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import adatta, carica_E
    from evoluzione.componente.episodio import lotti_episodio
    from evoluzione.esperimenti.addestramento import _canali, _carica, _normalizzazione, _partizioni
    from evoluzione.esperimenti.esegui_e2 import da_E1, valuta
    from evoluzione.esperimenti.fasi import percorso_E
    from evoluzione.esperimenti.inserimento import _modello_da_ck, statiche
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, seme_torch
    out = Path(out)
    g = out / DIR_PRED / f"ep{k}_{c}_p{p}_s{s}.npz"
    if g.exists():
        return {"c": c, "p": p, "s": s, "k": k, "esito": "presente", "secondi": 0}
    t_in = time.time()
    try:
        E_TOK = _nome_e_token()
        ep = episodi_registrati(out)[c]
        K_SEC = json.loads((out / "e5_k_secondaria.json").read_text())
        k_sec = int(K_SEC["k"][c])
        et = etichette(k)
        t0, t1, fine = ep[k]["t0"], ep[k]["t1"], ep[k]["fine"]
        D = _carica(c, out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])},
                                _fine_periodo(k, ep))
        nn = nodi["prova"]
        NORM, nr, nv = _normalizzazione(D, nodi, ist)
        x = _canali(D, nr, nv)
        stat = statiche(D)
        P_ = carica_pesi(out / et["pesi"], c, p)
        pesi = np.asarray(P_.vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
        cfgF = json.loads((out / "selezione_F_griglia" / "configurazione_F.json")
                          .read_text())["scelte"][c]
        st = seme_torch(s)
        dEp, nodi_in, imp_Ep = carica_E(percorso_E(out / et["E"], c, p, st, braccio=E_TOK), D_STAT)
        mC, dC = _modello_da_ck(out / et["ins"] / f"ck_C_{c}_p{p}_s{s}.pt", D, nodi, None)
        mA, dA = _modello_da_ck(out / et["ins"] / f"ck_A_{c}_p{p}_s{s}.pt", D, nodi, None)
        # CONTROLLO 3: nodi nuovi fuori da E', C, pesi, normalizzazione; dentro A
        nn_set = set(int(z) for z in nn)
        for nome, ni in (("E'", nodi_in), ("C", dC["nodi_iniziali"]),
                         ("pesi.nodi_addestramento", P_.nodi_addestramento),
                         ("normalizzazione", nodi["addestramento"])):
            if set(int(z) for z in ni) & nn_set:
                raise RuntimeError(f"controllo 3, {nome}: nodi nuovi presenti")
        if not nn_set <= set(int(z) for z in dA["nodi_iniziali"]):
            raise RuntimeError("controllo 3, A: il veterano deve avere i nodi nuovi")
        # CONTROLLO 4: budget e configurazione di F
        if k != 1:
            for nome, d_ in (("C", dC), ("A", dA)):
                if d_.get("training_protocol") != "principale":
                    raise RuntimeError(f"controllo 4, {nome}: protocollo {d_.get('training_protocol')}")
        eta = per - t0
        idx = [eta <= FASCE_ETA[0], (eta > FASCE_ETA[0]) & (eta <= FASCE_ETA[1]), eta > FASCE_ETA[1]]
        tagli = np.array_split(np.arange(len(per)), 3)
        fasce = idx + [np.isin(np.arange(len(per)), q) for q in tagli]
        o_acq = GR.origini_acquisizione(ok, t0, t1)
        cv, cop = celle_valide(D, nn, o_acq, t0, t1)
        ris, prov = {}, {}

        def salva(nome, m):
            PB, YY, MM, w, ph, dt = valuta(m, x, D["classe"], nn, per, S, pesi)
            A, Bm = _aggregati(PB, YY, MM, pesi, fasce)
            ris[f"A_{nome}"] = A; ris[f"B_{nome}"] = Bm; ris[f"wce_{nome}"] = w
            prov[nome] = "calcolato"
            return w

        salva("C", mC); salva("A", mA)
        m0, _ = da_E1(dEp, nodi_in, nn, "token"); salva("F0p", m0)
        n_agg = {}
        for nome, L, n_upd in ([(f"Fp_{L}", L, cfgF["aggiornamenti"]) for L in DURATE]
                               + [("Fp_96k", 96, k_sec)]):
            o_L = GR.origini_acquisizione(ok, t0, t0 + L)
            if not o_L:
                raise RuntimeError(f"{nome}: nessuna origine d'adattamento")
            m, forn = da_E1(dEp, nodi_in, nn, "token")
            n_agg[nome] = adatta(m, forn, lotti_episodio(x, D["classe"], stat, nn, o_L), w_t,
                                 cfgF["passo"], n_upd)
            salva(nome, m)
        # CONTROLLO 6 (episodio 1): coincide con le celle di E4
        controllo_6 = {}
        if k == 1:
            z4 = np.load(out / "predizioni_e4" / f"prova_{c}_p{p}_s{s}.npz", allow_pickle=True)
            if not (np.array_equal(z4["nodi"].astype("int64"), np.asarray(nn, dtype="int64"))
                    and np.array_equal(z4["origini"].astype("int64"), per)):
                raise RuntimeError("controllo 6: nodi od origini diversi da E4")
            for nome in ("C", "F0p") + tuple(f"Fp_{L}" for L in DURATE):
                rel = abs(float(ris[f"wce_{nome}"]) - float(z4[f"wce_{nome}"])) / abs(float(z4[f"wce_{nome}"]))
                controllo_6[nome] = rel
                if rel > 1e-6:
                    raise RuntimeError(f"controllo 6, {nome}: scarto {rel:.1e} da E4")
            if str(z4["impronta_Ep"]) != imp_Ep:
                raise RuntimeError("controllo 6: impronta di E' diversa da E4")
        g.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            g, nodi=np.asarray(nn, dtype="int32"), origini=per.astype("int32"),
            eta=eta.astype("int32"), celle_valide=cv.astype("int32"), copertura=cop.astype("float32"),
            fasce=np.asarray([int(m_.sum()) for m_ in fasce]), t0=t0, t1=t1, fine=fine,
            episodio=k, contesto=c, partizione=p, seme=s, impronta_Ep=imp_Ep,
            impronta_pesi=P_.impronta, impronta_k_secondaria=K_SEC["impronta"], k_secondaria=k_sec,
            aggiornamenti=json.dumps(n_agg), configurazione_F=json.dumps(cfgF),
            controllo_6=json.dumps(controllo_6), controllo_3="ok", **ris)
        return {"c": c, "p": p, "s": s, "k": k, "esito": "ok", "secondi": time.time() - t_in,
                "wce": {q: round(float(ris[f"wce_{q}"]), 5) for q in ("C", "A", "F0p", "Fp_96", "Fp_672")}}
    except Exception as e:                                   # noqa: BLE001
        return {"c": c, "p": p, "s": s, "k": k, "esito": "fallita",
                "errore": f"{type(e).__name__}: {e}"[:300], "secondi": time.time() - t_in}


def fase_valuta(out: Path, lavoratori: int, fili: int, piano: bool, episodi):
    if not (out / "e5_k_secondaria.json").exists():
        raise RuntimeError("e5_k_secondaria.json assente: eseguire --fase k-secondaria prima")
    celle = [(c, p, s, k, str(out), fili) for k in episodi for c in CITTA for p in (0, 1, 2) for s in SEMI_E5]
    fatte = sum((out / DIR_PRED / f"ep{k}_{c}_p{p}_s{s}.npz").exists() for c, p, s, k, _, _ in celle)
    print(f"  {len(celle)} celle (episodi {tuple(episodi)}, semi {SEMI_E5}), {fatte} gia' fatte; modelli "
          f"{MODELLI_BASE}; k secondario da e5_k_secondaria.json; controlli 3, 4, 6 per cella")
    if piano:
        return 0
    ctx = mp.get_context("spawn"); t0 = time.time(); fall = 0
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_cella, celle), 1):
            if r["esito"] == "fallita":
                fall += 1
                print(f"  [{i:3d}/{len(celle)}] ep{r['k']} {r['c']:10s} p{r['p']} s{r['s']} FALLITA {r['errore']}", flush=True)
            elif r["esito"] == "ok":
                print(f"  [{i:3d}/{len(celle)}] ep{r['k']} {r['c']:10s} p{r['p']} s{r['s']} "
                      + " ".join(f"{q} {v}" for q, v in r["wce"].items()) + f"  {r['secondi']:4.0f}s", flush=True)
    print(f"\n  {len(celle) - fall} celle, {fall} fallite, {(time.time() - t0)/60:.1f} min")
    return 0 if not fall else 1


# ------------------------------------------------------------------- test --
def _carica_celle_e5(out: Path):
    import numpy as np
    celle = {}
    for f in sorted((out / DIR_PRED).glob("ep*_*_p*_s*.npz")):
        with np.load(f, allow_pickle=True) as z:
            d = {q: z[q] for q in z.files}
        celle[(int(d["episodio"]), str(d["contesto"]), int(d["partizione"]), int(d["seme"]))] = d
    return celle


def fase_test(out: Path):
    import numpy as np
    SC = json.loads((out / "e4_scelta_gated.json").read_text())
    K_SEC = json.loads((out / "e5_k_secondaria.json").read_text())
    celle = _carica_celle_e5(out)
    rng = np.random.default_rng(SEME_BOOT)
    AFF = {"a": ("F0p", "C", None), "b": ("gated", "F0p", None), "c": ("Fp_672", "C", 2),
           "d": ("Fp_96", "C", None), "e": ("Fp_672", "A", 2)}
    ALTRI = {"gated-C": ("gated", "C", None), "Fp_96k-C": ("Fp_96k", "C", None),
             "Fp_96k-Fp_96": ("Fp_96k", "Fp_96", None), "A-C": ("A", "C", None),
             "Fp_672-C_intero": ("Fp_672", "C", None)}
    R = {"impronta_scelta_e4": SC["impronta"], "impronta_k_secondaria": K_SEC["impronta"],
         "k_secondaria": K_SEC["k"], "affermazioni": {}, "altri": {}, "nodi_sotto_N": {},
         "stesso_segno": {}, "celle": {}}

    def diff(n1, n2, fascia, tau, N):
        def f(z, idx):
            def AB(n):
                if n == "gated":
                    A, Bm = _politica(z, tau, N)
                else:
                    A, Bm = z[f"A_{n}"], z[f"B_{n}"]
                    A = A.sum(0) if fascia is None else A[fascia]
                    Bm = Bm.sum(0) if fascia is None else Bm[fascia]
                return (A, Bm) if idx is None else (A[idx], Bm[idx])
            return _wce(*AB(n1)) - _wce(*AB(n2))
        return f

    def segno(r):
        lo, hi = r["ic_con_nodi"]
        return "-" if hi < 0 else ("+" if lo > 0 else "0")

    for c in CITTA:
        tau, N = SC["scelta"][c]["tau"], SC["scelta"][c]["N"]
        for k in EPISODI:
            cc = {(c, p, s): z for (k_, c_, p, s), z in celle.items() if k_ == k and c_ == c}
            if len(cc) != 18:
                raise RuntimeError(f"{c} ep{k}: {len(cc)} celle, attese 18")
            for z in cc.values():
                if str(z["impronta_k_secondaria"]) != K_SEC["impronta"]:
                    raise RuntimeError(f"{c} ep{k}: impronta di k diversa da quella registrata")
            R["celle"][f"{c}/ep{k}"] = len(cc)
            print(f"\n{c} episodio {k}: gated(tau={tau}, N={N}), {len(cc)} celle")
            for a_, (n1, n2, fascia) in AFF.items():
                r = _boot(cc, diff(n1, n2, fascia, tau, N), rng)
                R["affermazioni"][f"{c}/ep{k}/{a_}"] = {**r, "confronto": f"{n1}-{n2}",
                                                        "fascia": fascia, "segno": segno(r)}
                print(f"  ({a_}) {n1:7s}-{n2:4s}{' eta>1sett' if fascia == 2 else '          '} "
                      f"{r['media']:+.5f} [{r['ic_con_nodi'][0]:+.5f}, {r['ic_con_nodi'][1]:+.5f}]  segno {segno(r)}")
            for nome, (n1, n2, fascia) in ALTRI.items():
                R["altri"][f"{c}/ep{k}/{nome}"] = _boot(cc, diff(n1, n2, fascia, tau, N), rng)
            sotto = [int((z["celle_valide"] < N).sum()) for z in cc.values()]
            R["nodi_sotto_N"][f"{c}/ep{k}"] = {"N": N, "media_per_cella": float(np.mean(sotto)),
                                               "massimo": int(max(sotto)), "nodi": int(len(next(iter(cc.values()))["celle_valide"]))}
            print(f"  nodi sotto N={N}: media {np.mean(sotto):.1f} per cella, massimo {max(sotto)}")
        for a_ in AFF:
            segni = [R["affermazioni"][f"{c}/ep{k}/{a_}"]["segno"] for k in EPISODI]
            R["stesso_segno"][f"{c}/{a_}"] = {"segni": segni, "concorda": len(set(segni)) == 1,
                                              "solo_ep3": R["affermazioni"][f"{c}/ep3/{a_}"]["segno"]}
    R["repliche"] = B_BOOT; R["seme_bootstrap"] = SEME_BOOT
    R["istante"] = datetime.now(timezone.utc).isoformat()
    (out / "e5_risultati.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print("\n" + "=" * 84)
    print("STESSO SEGNO IN 3/3 EPISODI (regola di lettura):")
    for c in CITTA:
        print(f"  {c:11s} " + "  ".join(f"({a_}) {''.join(R['stesso_segno'][f'{c}/{a_}']['segni'])} "
                                        f"{'si' if R['stesso_segno'][f'{c}/{a_}']['concorda'] else 'NO'}" for a_ in AFF))
    print(f"  salvato in {out / 'e5_risultati.json'}")
    return R


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fase", choices=("prepara", "k-secondaria", "addestra", "valuta", "test"), required=True)
    ap.add_argument("--episodio", nargs="*", type=int, default=list(EPISODI))
    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    print("=" * 84); print(f"E5 — fase {a.fase}"); print("=" * 84)
    if a.fase == "prepara":
        fase_prepara(a.out, a.piano); return 0
    if a.fase == "k-secondaria":
        fase_k_secondaria(a.out, a.lavoratori, a.fili, a.piano); return 0
    if a.fase == "addestra":
        return fase_addestra(a.out, a.lavoratori, a.fili, a.piano)
    if a.fase == "valuta":
        return fase_valuta(a.out, a.lavoratori, a.fili, a.piano, a.episodio)
    fase_test(a.out); return 0


if __name__ == "__main__":
    raise SystemExit(main())
