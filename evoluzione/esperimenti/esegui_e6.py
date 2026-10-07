#!/usr/bin/env python3
"""
E6 — replica esterna, parte B (PEMS08). Esecutore per fasi (protocol/E6.md).
=============================================================================
Sei contesti-partizione `PEMS08_p0…p5` × sei semi (201–206); t0 di prova 3840,
t0 di validazione 3162, pre-registrati. Ogni fase verifica i prerequisiti
della precedente e riparte dai marcatori.

    --fase pilota       un C a seme unico, processo unico: il costo (fatto il 7/10)
    --fase addestra     C, A, E', R-orig(24 h), R-orig(1 sett.): 5 × 36 = 180
    --fase seleziona-F  configurazione di F' (aggiornamenti, passo) sulla giornata
                        di validazione, nodi di validazione, regola di seleziona_F,
                        da E' (su PEMS08 E non esiste); scrive e congela
    --fase valuta       celle (p, s) dell'episodio di validazione (per gated) e di
                        prova: C, [A], F0', F'(24 h), F'(48 h), F'(1 sett.),
                        [R-orig(24 h), R-orig(1 sett.)]; controlli per cella
    --fase scegli       (tau, N) con la regola di E4 sulle celle di validazione;
                        impronta registrata prima del test
    --fase test         confronti pre-registrati con ricampionamento congiunto
                        (partizioni × semi × nodi); e6_risultati.json

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_e6.py --fase addestra --piano
    poetry run python evoluzione/esperimenti/esegui_e6.py --fase addestra --lavoratori 8
    poetry run python evoluzione/esperimenti/esegui_e6.py --fase seleziona-F
    poetry run python evoluzione/esperimenti/esegui_e6.py --fase valuta --episodio validazione --lavoratori 8
    poetry run python evoluzione/esperimenti/esegui_e6.py --fase scegli
    poetry run python evoluzione/esperimenti/esegui_e6.py --fase valuta --episodio prova --lavoratori 8
    poetry run python evoluzione/esperimenti/esegui_e6.py --fase test
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
    D_STAT, FASCE_ETA, N_SOGLIE, TAU, _aggregati, _boot, _nome_e_token,
    _politica, _wce)
from evoluzione.esperimenti.esegui_pems04 import Esec, cfg_pems, marcatore  # noqa: E402

CONTESTI = tuple(f"PEMS08_p{k}" for k in range(6))   # 6 partizioni x 6 semi (E6.md)
SEMI_E6 = (201, 202, 203, 204, 205, 206)
T0_PROVA = 3840          # protocol/E6.md, parte B: pre-registrato (giorno 40)
T0_VALIDAZIONE = 3162    # primo_t0 sul periodo di selezione [3162, 3840)
L24, SETTIMANA = 96, 672
DURATE = (96, 192, 672)                               # 24 h, 48 h, 1 settimana
ETICHETTA = "e6_pems08"                               # C, A, R-orig(24 h)
ETICHETTA_672 = "e6_pems08_672"                       # R-orig(1 sett.)
ETICHETTA_PILOTA = "e6_pilota"
DIR_PRED = "predizioni_e6"
DIR_SEL = "selezione_F_e6"
RHO = 0.15
SEME_BOOT = 20261010
SEME_PILOTA = 201
R_ORIG = "R-orig"


def _scrivi_atomico(f: Path, testo: str):
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".tmp")
    with open(tmp, "w") as h:
        h.write(testo); h.flush(); os.fsync(h.fileno())
    os.replace(tmp, f)


def _impronta(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()[:16]


def _part(c: str) -> int:
    return int(c.rsplit("_p", 1)[1])


def episodio(nome: str, D):
    """(t0, t1, fine, chiave dei nodi) dell'episodio."""
    from evoluzione.componente import griglia as GR
    e = D["r"].shape[0] - GR.MAX_ORIZZ
    if nome == "prova":
        return T0_PROVA, T0_PROVA + L24, e, "prova"
    return T0_VALIDAZIONE, T0_VALIDAZIONE + L24, T0_PROVA, "validazione"


def _dati(c: str, out: Path):
    """D, ok, nodi, ist (fine_periodo = t0 di prova), normalizzazione, canali, statiche."""
    import numpy as np
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import _canali, _carica, _normalizzazione, _partizioni
    from evoluzione.esperimenti.inserimento import statiche
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE_E6
    D = _carica(c, out / "maschere")
    ok = GR.passi_regolari(D["ts"])
    nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE_E6[_part(c)])},
                            T0_PROVA)
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    return D, ok, nodi, ist, _canali(D, nr, nv), statiche(D)


# ------------------------------------------------------------- configurazioni --
def cfg_e6(b: str, c: str, p: int, s: int, out: Path, etichetta: str = ETICHETTA) -> dict:
    """C (anche il pilota): la configurazione di PEMS04 con pesi di PEMS08,
    `fine_periodo` = t0 di prova e cartelle proprie."""
    cfg = cfg_pems(b, c, p, s, out)
    cfg.update({"etichetta": etichetta, "dir_pesi": str(out / "pesi_pems08"),
                "fine_periodo": T0_PROVA,
                "dir_stati_completi": str(out / f"stati_{etichetta}")})
    return cfg


def cfg_lavoro(x: dict, out: Path, nodi, ok) -> dict:
    """La configurazione del braccio di un lavoro: tutto dalla tabella unica
    (`cfg_braccio`), con le sole differenze di E6 dichiarate qui."""
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.inserimento import cfg_braccio
    from evoluzione.esperimenti.semi import seme_torch
    b, c, p, s = x["braccio"], x["contesto"], x["partizione"], x["seme"]
    pb = proprieta_braccio(b)
    if pb.preparatorio:                                   # E'
        cfg = {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
               "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
               "orizzonti": [1, 2, 4, 8], "sorgente": "pems04",
               "etichetta": f"{b}_{ETICHETTA}", "braccio": b,
               **({"rho": RHO} if pb.richiede_rho else {}),
               "training_protocol": "principale", "griglia_temporale": "reale",
               "checkpoint_selection_population": "initial_network",
               "nome_ck": f"ck_{b}_{c}_p{p}_s{seme_torch(s)}.pt"}
    else:
        L = x.get("acquisizione", L24)
        t1 = T0_PROVA + L
        o_acq = GR.origini_acquisizione(ok, T0_PROVA, t1)
        cfg = cfg_braccio(b, c, p, s, out, nodi, o_acq, t1=t1)
        cfg["sorgente"] = "pems04"
        cfg["etichetta"] = ETICHETTA_672 if L == SETTIMANA else ETICHETTA
        cfg["acquisizione_passi"] = L
    cfg.update({"dir_pesi": str(out / "pesi_pems08"), "dir_canonico": str(out / "canonico"),
                "dir_stati_completi": str(out / f"stati_{cfg['etichetta']}"),
                "fine_periodo": T0_PROVA})
    return cfg


def _ck_di(x: dict, out: Path) -> Path:
    from evoluzione.esperimenti.semi import seme_torch
    b, c, p, s = x["braccio"], x["contesto"], x["partizione"], x["seme"]
    if proprieta_braccio(b).preparatorio:
        return out / f"{b}_{ETICHETTA}" / f"ck_{b}_{c}_p{p}_s{seme_torch(s)}.pt"
    et = ETICHETTA_672 if x.get("acquisizione", L24) == SETTIMANA else ETICHETTA
    return out / et / f"ck_{b}_{c}_p{p}_s{s}.pt"


def lavori(out: Path) -> list:
    E_TOK = _nome_e_token()
    lav = []
    for s in SEMI_E6:
        for c in CONTESTI:
            p = _part(c)
            for b, L in (("C", None), ("A", None), (E_TOK, None), (R_ORIG, L24), (R_ORIG, SETTIMANA)):
                x = {"contesto": c, "partizione": p, "seme": int(s), "braccio": b}
                if L is not None:
                    x["acquisizione"] = L
                x["ck"] = str(_ck_di(x, out))
                lav.append(x)
    return lav


# -------------------------------------------------------------------- pilota --
def _pilota(out: Path, fili: int) -> dict:
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.componente.registro import Registro
    from evoluzione.esperimenti.addestramento import addestra_una
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE_E6
    c, p, s, b = CONTESTI[0], 0, SEME_PILOTA, "C"
    cfg = cfg_e6(b, c, p, s, out, ETICHETTA_PILOTA)
    ck = out / ETICHETTA_PILOTA / cfg["nome_ck"]
    if marcatore(ck).exists():
        return json.loads(marcatore(ck).read_text())
    reg = Registro.avvia(f"{ETICHETTA_PILOTA}/{b}", note=f"{c} seme {s} braccio {b} PILOTA",
                         radice=out / "registro")
    x = {"contesto": c, "partizione": p, "seme": s, "braccio": b, "pilota": True}
    reg.configurazione({**cfg, **x})
    t_in = time.time()
    gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE_E6[p]),
           "inizializzazione": np.random.default_rng(s)}
    addestra_una(Esec(c, p, cfg["variante"]), reg, cfg, gen, out)
    reg.completa()
    if not ck.exists():
        raise RuntimeError(f"punto di controllo atteso assente: {ck}")
    r = {**x, "secondi": time.time() - t_in, "fili": fili,
         "istante": datetime.now(timezone.utc).isoformat()}
    _scrivi_atomico(marcatore(ck), json.dumps(r, indent=2))
    return r


# ----------------------------------------------------------------- addestra --
def _addestra(args):
    x, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.componente.registro import Registro
    from evoluzione.esperimenti.addestramento import addestra_una
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE_E6
    out = Path(out)
    c, p, s, b = x["contesto"], x["partizione"], x["seme"], x["braccio"]
    t_in = time.time()
    reg = None
    try:
        D, ok, nodi, ist, _, _ = _dati(c, out)
        cfg = cfg_lavoro(x, out, nodi, ok)
        reg = Registro.avvia(f"{cfg['etichetta']}/{b}",
                             note=f"{c} seme {s} braccio {b}"
                                  + (f" acquisizione {x['acquisizione']}" if "acquisizione" in x else ""),
                             radice=out / "registro")
        reg.configurazione({**cfg, **x})
        gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE_E6[p]),
               "inizializzazione": np.random.default_rng(s)}
        addestra_una(Esec(c, p, cfg.get("variante")), reg, cfg, gen, out)
        ck = Path(x["ck"])
        if not ck.exists():
            raise RuntimeError(f"punto di controllo atteso assente: {ck}")
        reg.completa()
        dt = time.time() - t_in
        _scrivi_atomico(marcatore(ck), json.dumps(
            {**x, "secondi": dt, "fili": fili, "istante": datetime.now(timezone.utc).isoformat()}, indent=2))
        return {**x, "esito": "completata", "secondi": dt}
    except Exception as e:                                   # noqa: BLE001
        if reg is not None:
            reg.evento(f"{type(e).__name__}: {e}"); reg.completa("fallita")
        return {**x, "esito": "fallita", "secondi": time.time() - t_in,
                "errore": f"{type(e).__name__}: {e}"[:300]}


def fase_addestra(out: Path, lavoratori: int, fili: int, piano: bool) -> int:
    lav = lavori(out)
    fatti = [x for x in lav if marcatore(Path(x["ck"])).exists()]
    da_fare = [x for x in lav if x not in fatti]
    print(f"  {len(lav)} addestramenti: {len(CONTESTI)} contesti-partizione x {len(SEMI_E6)} semi x 5 bracci "
          f"(C, A, {_nome_e_token()}, {R_ORIG} 24 h, {R_ORIG} 1 sett.); {len(fatti)} gia' fatti, "
          f"{len(da_fare)} da eseguire")
    print(f"  fine_periodo {T0_PROVA}, pesi pesi_pems08, canonico a 11 canali riusato, "
          f"cartelle {ETICHETTA}/, {ETICHETTA_672}/, {_nome_e_token()}_{ETICHETTA}/")
    if piano:
        for x in da_fare[:6]:
            print(f"     {x['contesto']} s{x['seme']} {x['braccio']:4s}"
                  + (f" acq {x['acquisizione']}" if "acquisizione" in x else "") + f"  -> {x['ck']}")
        return 0
    ctx = mp.get_context("spawn"); t0 = time.time(); esiti = []
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_addestra, [(x, str(out), fili) for x in da_fare]), 1):
            esiti.append(r)
            tr = time.time() - t0
            print(f"  [{i:3d}/{len(da_fare)}] {r['contesto']} s{r['seme']} {r['braccio']:4s}"
                  f"{(' acq ' + str(r['acquisizione'])) if 'acquisizione' in r else '':9s} "
                  f"{r['esito']:10s} {r['secondi']/60:5.1f} min | trascorse {tr/3600:4.1f} h, "
                  f"restano ~{tr/i*(len(da_fare)-i)/3600:4.1f} h"
                  + (f"\n        {r['errore']}" if r["esito"] == "fallita" else ""), flush=True)
    fall = [r for r in esiti if r["esito"] != "completata"]
    _scrivi_atomico(out / "esito_e6_addestra.json", json.dumps(
        {"completate": len(esiti) - len(fall), "fallite": fall, "gia_fatte": len(fatti),
         "ore_calendario": (time.time() - t0) / 3600, "lavoratori": lavoratori,
         "istante": datetime.now(timezone.utc).isoformat()}, indent=2, ensure_ascii=False))
    print(f"\n  {len(esiti) - len(fall)} completati, {len(fall)} falliti, {(time.time() - t0)/3600:.1f} h")
    return 0 if not fall else 1


# -------------------------------------------------------------- seleziona-F --
def fase_seleziona_F(out: Path, piano: bool) -> int:
    """La regola di `seleziona_F` (griglia, giornata di validazione, nodi di
    validazione, media su semi poi partizioni, spareggio) applicata a E' con
    `da_E1(..., "token")`: su PEMS08 E non esiste."""
    import numpy as np
    import torch
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import adatta, carica_E, verifica_vincoli
    from evoluzione.componente.episodio import giornata_valutazione, lotti_episodio
    from evoluzione.esperimenti.addestramento import _perdita
    from evoluzione.esperimenti.esegui_e2 import da_E1
    from evoluzione.esperimenti.seleziona_F import griglia, scegli
    from evoluzione.esperimenti.semi import seme_torch
    E_TOK = _nome_e_token()
    f_cfg = out / DIR_SEL / "configurazione_F.json"
    if f_cfg.exists() and json.loads(f_cfg.read_text()).get("congelata"):
        print(f"  configurazione gia' congelata: {f_cfg}"); return 0
    mancanti = [x["ck"] for x in lavori(out) if x["braccio"] == E_TOK and not marcatore(Path(x["ck"])).exists()]
    if mancanti:
        raise RuntimeError(f"{len(mancanti)} punti E' senza marcatore, per esempio {mancanti[:2]}")
    print(f"  griglia {griglia()}; episodio di validazione t0 = {T0_VALIDAZIONE}, giornata dopo t1; "
          f"nodi di validazione; {len(CONTESTI) * len(SEMI_E6)} gruppi x {len(griglia())} candidati")
    if piano:
        return 0
    (out / DIR_SEL).mkdir(parents=True, exist_ok=True)
    per_gruppo = {}
    for c in CONTESTI:
        p = _part(c)
        D, ok, nodi, ist, x, stat = _dati(c, out)
        t0v, t1v, fine_v, _ = episodio("validazione", D)
        nodi_ep = nodi["validazione"]
        w = torch.as_tensor(carica_pesi(out / "pesi_pems08", c, p).vettore(), dtype=torch.float32)
        o_ad = GR.origini_acquisizione(ok, t0v, t1v)
        fine_g = giornata_valutazione(D["ts"], t1v, fine_v)
        o_va = GR.origini_dopo(ok, t1v, fine_g + 1)
        for s in SEMI_E6:
            f_man = out / DIR_SEL / f"sel_{c}_p{p}_s{s}.json"
            if f_man.exists():
                per_gruppo[(c, p, s)] = json.loads(f_man.read_text()); continue
            fE = Path(_ck_di({"contesto": c, "partizione": p, "seme": s, "braccio": E_TOK}, out))
            dE, nodi_in, imp_E = carica_E(fE, D_STAT)
            lotti = lotti_episodio(x, D["classe"], stat, nodi_ep, o_ad)
            lotti_val = lotti_episodio(x, D["classe"], stat, nodi_ep, o_va)
            punteggi, dett = {}, []
            for b, e in griglia():
                mF, forn = da_E1(dE, nodi_in, nodi_ep, "token")
                reg_ad = []; t_c = time.time()
                n_agg = adatta(mF, forn, lotti, w, e, b, reg_ad)
                mF.eval()
                with torch.inference_mode():
                    L = []
                    for Xv, nv_, Yv, Mv, Sv in lotti_val:
                        o_ = mF(Xv, node_ids=nv_, static_inputs=Sv)
                        lv, _ = _perdita(o_, Yv, Mv, w)
                        L.append(float(lv))
                punteggi[(b, e)] = float(np.mean(L)) if L else float("nan")
                verifica_vincoli(mF, forn, dE, imp_E, dE["state_dict"]["identita.embedding"], fE)
                dett.append({"aggiornamenti_richiesti": b, "passo": e, "aggiornamenti_eseguiti": n_agg,
                             "wCE_validazione": punteggi[(b, e)], "secondi": time.time() - t_c})
                print(f"    {c} s{s} ({b:3d},{e:g})  wCE {punteggi[(b, e)]:.5f}", flush=True)
                del mF, forn
            man = {"contesto": c, "partizione": p, "seme": int(s), "partenza": "E' (token ignoto)",
                   "acquisizione": [int(t0v), int(t1v)], "valutazione": [int(t1v), int(fine_g)],
                   "origini_adattamento": len(o_ad), "origini_valutazione": len(o_va),
                   "impronta_E": imp_E, "punto_di_controllo_E": fE.name,
                   "punteggi": {str(k): v for k, v in punteggi.items()}, "candidati": dett,
                   "regola": "wCE media sugli orizzonti, poi sui semi, poi sulle partizioni; "
                             "a parita': meno aggiornamenti, poi passo minore",
                   "istante": datetime.now(timezone.utc).isoformat()}
            f_man.write_text(json.dumps(man, indent=2, ensure_ascii=False))
            per_gruppo[(c, p, s)] = man
    # aggregazione: media sui semi dentro ogni partizione, poi sulle partizioni
    agg = {}
    for k in griglia():
        per_part = []
        for c in CONTESTI:
            v = [d["punteggi"][str(k)] for (c_, _, _), d in per_gruppo.items() if c_ == c]
            v = [z for z in v if z is not None and np.isfinite(z)]
            if v:
                per_part.append(float(np.mean(v)))
        agg[k] = float(np.mean(per_part))
    k_s = scegli(agg)
    doc = {"scelte": {"PEMS08": {"aggiornamenti": int(k_s[0]), "passo": float(k_s[1]),
                                 "wce_validazione": agg[k_s]}},
           "una_per_dataset": True, "partenza": "E' (token ignoto): su PEMS08 E non esiste",
           "griglia": [list(k) for k in griglia()], "aggregati": {str(k): v for k, v in agg.items()},
           "regola_spareggio": "meno aggiornamenti, poi passo minore",
           "calendario_validazione": [T0_VALIDAZIONE, T0_VALIDAZIONE + L24],
           "gruppi": len(per_gruppo), "congelata": True,
           "istante": datetime.now(timezone.utc).isoformat()}
    testo = json.dumps(doc, indent=2, ensure_ascii=False)
    doc["impronta"] = _impronta(testo)
    _scrivi_atomico(f_cfg, json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"\n  configurazione di F' su PEMS08: aggiornamenti {k_s[0]}, passo {k_s[1]:g} "
          f"(wCE validazione {agg[k_s]:.5f}); impronta {doc['impronta']}; congelata in {f_cfg}")
    return 0


# ------------------------------------------------------------------- valuta --
def _cfgF(out: Path) -> dict:
    d = json.loads((out / DIR_SEL / "configurazione_F.json").read_text())
    if not d.get("congelata"):
        raise RuntimeError("configurazione di F' non congelata")
    return d


def _cella(args):
    c, s, ep_nome, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.analizza_copertura_e4 import celle_valide
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import adatta, carica_E
    from evoluzione.componente.episodio import lotti_episodio
    from evoluzione.esperimenti.esegui_e2 import da_E1, valuta
    from evoluzione.esperimenti.inserimento import _modello_da_ck
    out = Path(out); p = _part(c)
    g = out / DIR_PRED / f"{ep_nome}_{c}_p{p}_s{s}.npz"
    if g.exists():
        return {"c": c, "s": s, "ep": ep_nome, "esito": "presente", "secondi": 0}
    t_in = time.time()
    try:
        E_TOK = _nome_e_token()
        D, ok, nodi, ist, x, stat = _dati(c, out)
        t0, t1, fine, chiave = episodio(ep_nome, D)
        nn = nodi[chiave]
        per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
        if not len(per):
            raise RuntimeError("perimetro vuoto")
        P_ = carica_pesi(out / "pesi_pems08", c, p)
        pesi = np.asarray(P_.vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
        cfgF = _cfgF(out); scF = cfgF["scelte"]["PEMS08"]
        fE = Path(_ck_di({"contesto": c, "partizione": p, "seme": s, "braccio": E_TOK}, out))
        dEp, nodi_in, imp_Ep = carica_E(fE, D_STAT)
        mC, dC = _modello_da_ck(out / ETICHETTA / f"ck_C_{c}_p{p}_s{s}.pt", D, nodi, None)
        # CONTROLLO 7 (E4): i nodi dell'episodio fuori da E', C, pesi, normalizzazione
        nn_set = set(int(z) for z in nn)
        for nome, ni in (("E'", nodi_in), ("C", dC["nodi_iniziali"]),
                         ("pesi.nodi_addestramento", P_.nodi_addestramento),
                         ("normalizzazione", nodi["addestramento"])):
            if set(int(z) for z in ni) & nn_set:
                raise RuntimeError(f"controllo 7, {nome}: nodi dell'episodio presenti")
        if dC.get("fine_periodo") not in (None, T0_PROVA) and int(dC.get("fine_periodo")) != T0_PROVA:
            raise RuntimeError(f"C: fine_periodo {dC.get('fine_periodo')} diverso da {T0_PROVA}")
        eta = per - t0
        idx = [eta <= FASCE_ETA[0], (eta > FASCE_ETA[0]) & (eta <= FASCE_ETA[1]), eta > FASCE_ETA[1]]
        tagli = np.array_split(np.arange(len(per)), 3)
        fasce = idx + [np.isin(np.arange(len(per)), q) for q in tagli]
        o_acq = GR.origini_acquisizione(ok, t0, t1)
        cv, cop = celle_valide(D, nn, o_acq, t0, t1)
        ris, impronte = {}, {"Ep": imp_Ep}

        def salva(nome, m):
            PB, YY, MM, w, ph, dt = valuta(m, x, D["classe"], nn, per, S, pesi)
            A, Bm = _aggregati(PB, YY, MM, pesi, fasce)
            ris[f"A_{nome}"] = A; ris[f"B_{nome}"] = Bm; ris[f"wce_{nome}"] = w
            return w

        salva("C", mC)
        m0, _ = da_E1(dEp, nodi_in, nn, "token"); salva("F0p", m0)
        n_agg = {}
        for L in DURATE:
            o_L = GR.origini_acquisizione(ok, t0, t0 + L)
            if not o_L:
                raise RuntimeError(f"L={L}: nessuna origine d'adattamento")
            m, forn = da_E1(dEp, nodi_in, nn, "token")
            n_agg[f"Fp_{L}"] = adatta(m, forn, lotti_episodio(x, D["classe"], stat, nn, o_L), w_t,
                                      scF["passo"], scF["aggiornamenti"])
            salva(f"Fp_{L}", m)
        if ep_nome == "prova":
            mA, dA = _modello_da_ck(out / ETICHETTA / f"ck_A_{c}_p{p}_s{s}.pt", D, nodi, None)
            if not nn_set <= set(int(z) for z in dA["nodi_iniziali"]):
                raise RuntimeError("A: il veterano deve avere i nodi nuovi")
            salva("A", mA)
            for L, et in ((L24, ETICHETTA), (SETTIMANA, ETICHETTA_672)):
                mR, dR = _modello_da_ck(out / et / f"ck_{R_ORIG}_{c}_p{p}_s{s}.pt", D, nodi, None)
                # R-orig(1 sett.) conosce la settimana: lo si valuta comunque su `per`
                # (dopo t1 = t0 + 24 h); il confronto pre-registrato con F'(1 sett.)
                # e' sulla fascia eta' > 1 settimana, dove entrambi hanno gli stessi dati
                salva(f"Rorig_{L}", mR)
        g.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            g, nodi=np.asarray(nn, dtype="int32"), origini=per.astype("int32"), eta=eta.astype("int32"),
            celle_valide=cv.astype("int32"), copertura=cop.astype("float32"),
            fasce=np.asarray([int(m.sum()) for m in fasce]), durate=np.asarray(DURATE),
            t0=t0, t1=t1, fine=fine, episodio=ep_nome, contesto=c, partizione=p, seme=s,
            impronta_Ep=imp_Ep, impronta_configurazione_F=cfgF["impronta"],
            aggiornamenti=json.dumps(n_agg), configurazione_F=json.dumps(scF), controllo_7="ok", **ris)
        return {"c": c, "s": s, "ep": ep_nome, "esito": "ok", "secondi": time.time() - t_in,
                "wce": {k: round(float(ris[f"wce_{k}"]), 5) for k in ("C", "F0p", "Fp_96", "Fp_672")
                        if f"wce_{k}" in ris}}
    except Exception as e:                                   # noqa: BLE001
        return {"c": c, "s": s, "ep": ep_nome, "esito": "fallita",
                "errore": f"{type(e).__name__}: {e}"[:300], "secondi": time.time() - t_in}


def fase_valuta(out: Path, lavoratori: int, fili: int, piano: bool, ep_nome: str) -> int:
    _cfgF(out)
    if ep_nome == "prova" and not (out / "e6_scelta_gated.json").exists():
        raise RuntimeError("la prova si valuta dopo --fase scegli: (tau, N) va registrato prima del test")
    celle = [(c, s, ep_nome, str(out), fili) for c in CONTESTI for s in SEMI_E6]
    fatte = sum((out / DIR_PRED / f"{ep_nome}_{c}_p{_part(c)}_s{s}.npz").exists() for c, s, *_ in celle)
    print(f"  episodio {ep_nome}: {len(celle)} celle, {fatte} gia' fatte; modelli C, F0', F'(24 h/48 h/1 sett.)"
          + (", A, R-orig(24 h), R-orig(1 sett.)" if ep_nome == "prova" else ""))
    if piano:
        return 0
    ctx = mp.get_context("spawn"); t0 = time.time(); fall = 0
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_cella, celle), 1):
            if r["esito"] == "fallita":
                fall += 1; print(f"  [{i:3d}/{len(celle)}] {r['c']} s{r['s']} FALLITA {r['errore']}", flush=True)
            elif r["esito"] == "ok":
                print(f"  [{i:3d}/{len(celle)}] {r['c']} s{r['s']} "
                      + " ".join(f"{q} {v}" for q, v in r["wce"].items()) + f"  {r['secondi']:4.0f}s", flush=True)
    print(f"\n  {len(celle) - fall} celle, {fall} fallite, {(time.time() - t0)/60:.1f} min")
    return 0 if not fall else 1


def _carica_celle(out: Path, ep_nome: str) -> dict:
    import numpy as np
    celle = {}
    for f in sorted((out / DIR_PRED).glob(f"{ep_nome}_*_p*_s*.npz")):
        with np.load(f, allow_pickle=True) as z:
            d = {k: z[k] for k in z.files}
        celle[("PEMS08", int(d["partizione"]), int(d["seme"]))] = d
    return celle


# ------------------------------------------------------------------- scegli --
def fase_scegli(out: Path) -> int:
    """(tau, N) con la REGOLA DI E4 sulle celle di validazione: minimo della wCE
    integrata; spareggio N maggiore, poi tau = mai, poi tau minore."""
    import numpy as np
    celle = _carica_celle(out, "validazione")
    if len(celle) != len(CONTESTI) * len(SEMI_E6):
        raise RuntimeError(f"{len(celle)} celle di validazione, attese {len(CONTESTI) * len(SEMI_E6)}")
    tab = {(tau, N): float(np.mean([_wce(*_politica(z, tau, N)) for z in celle.values()]))
           for tau in TAU for N in N_SOGLIE}

    def chiave(item):
        (tau, N), v = item
        return (round(v, 9), -N, 0 if tau is None else 1, tau if tau is not None else 0)
    (tau_s, N_s), v_s = min(tab.items(), key=chiave)
    cv = np.concatenate([z["celle_valide"] for z in celle.values()])
    doc = {"scelta": {"PEMS08": {"tau": tau_s, "N": N_s, "wce_validazione": v_s, "celle": len(celle)}},
           "griglia_validazione": {f"tau={'mai' if t is None else t}/N={N}": v for (t, N), v in tab.items()},
           "celle_valide_validazione": {"min": int(cv.min()), "mediana": float(np.median(cv)), "max": int(cv.max())},
           "regola": ("minimo della wCE integrata su tutte le origini dopo t1 dell'episodio di validazione, "
                      "nodi di validazione; spareggio: N maggiore, poi tau = mai, poi tau minore"),
           "variante_dichiarata": "gated(tau, N = 0) con lo stesso tau, riportata accanto",
           "griglie": {"tau": ["96", "192", "672", "mai"], "N": list(N_SOGLIE)},
           "istante": datetime.now(timezone.utc).isoformat()}
    testo = json.dumps(doc, indent=2, ensure_ascii=False)
    doc["impronta"] = _impronta(testo)
    f = out / "e6_scelta_gated.json"
    if f.exists():
        prec = json.loads(f.read_text())
        if prec.get("impronta") != doc["impronta"]:
            raise RuntimeError("e6_scelta_gated.json esiste con impronta diversa: non si sovrascrive")
    _scrivi_atomico(f, json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"  PEMS08: tau = {'mai' if tau_s is None else str(tau_s) + ' passi'}, N = {N_s} "
          f"(wCE validazione {v_s:.5f}); celle valide per nodo min/mediana/max "
          f"{doc['celle_valide_validazione']['min']}/{doc['celle_valide_validazione']['mediana']:.0f}/"
          f"{doc['celle_valide_validazione']['max']}; impronta {doc['impronta']}")
    return 0


# --------------------------------------------------------------------- test --
def fase_test(out: Path) -> dict:
    import numpy as np
    SC = json.loads((out / "e6_scelta_gated.json").read_text())
    tau, N = SC["scelta"]["PEMS08"]["tau"], SC["scelta"]["PEMS08"]["N"]
    cfgF = _cfgF(out)
    celle = _carica_celle(out, "prova")
    if len(celle) != len(CONTESTI) * len(SEMI_E6):
        raise RuntimeError(f"{len(celle)} celle di prova, attese {len(CONTESTI) * len(SEMI_E6)}")
    for z in celle.values():
        if str(z["impronta_configurazione_F"]) != cfgF["impronta"]:
            raise RuntimeError("cella con configurazione di F' diversa da quella congelata")
    rng = np.random.default_rng(SEME_BOOT)
    AFF = {"a": ("F0p", "C", None), "b": ("gated", "F0p", None), "c": ("Fp_672", "C", 2),
           "d": ("Fp_96", "C", None), "e": ("Fp_672", "A", 2)}
    ALTRI = {"gated-C": ("gated", "C", None), "gated0-F0p": ("gated0", "F0p", None),
             "gated0-C": ("gated0", "C", None), "A-C": ("A", "C", None),
             "Rorig_672-Fp_672_eta>1sett": ("Rorig_672", "Fp_672", 2),
             "Rorig_96-C": ("Rorig_96", "C", None), "Rorig_672-Rorig_96_eta>1sett": ("Rorig_672", "Rorig_96", 2),
             "Fp_672-C_intero": ("Fp_672", "C", None), "Fp_192-C": ("Fp_192", "C", None)}

    def diff(n1, n2, fascia):
        def AB(z, n, idx):
            if n == "gated":
                A, Bm = _politica(z, tau, N)
            elif n == "gated0":
                A, Bm = _politica(z, tau, 0)
            else:
                A, Bm = z[f"A_{n}"], z[f"B_{n}"]
                A = A.sum(0) if fascia is None else A[fascia]
                Bm = Bm.sum(0) if fascia is None else Bm[fascia]
            return (A, Bm) if idx is None else (A[idx], Bm[idx])
        return lambda z, idx: _wce(*AB(z, n1, idx)) - _wce(*AB(z, n2, idx))

    def segno(r):
        lo, hi = r["ic_con_nodi"]
        return "-" if hi < 0 else ("+" if lo > 0 else "0")
    R = {"impronta_scelta_gated": SC["impronta"], "impronta_configurazione_F": cfgF["impronta"],
         "scelta_gated": SC["scelta"]["PEMS08"], "configurazione_F": cfgF["scelte"]["PEMS08"],
         "celle": len(celle), "affermazioni": {}, "altri": {}, "nodi_sotto_N": {}}
    print(f"\nPEMS08: gated(tau={tau}, N={N}), {len(celle)} celle ({len(CONTESTI)} partizioni x {len(SEMI_E6)} semi)")
    for a_, (n1, n2, fascia) in AFF.items():
        r = _boot(celle, diff(n1, n2, fascia), rng)
        R["affermazioni"][a_] = {**r, "confronto": f"{n1}-{n2}", "fascia": fascia, "segno": segno(r)}
        print(f"  ({a_}) {n1:7s}-{n2:4s}{' eta>1sett' if fascia == 2 else '          '} "
              f"{r['media']:+.5f} [{r['ic_con_nodi'][0]:+.5f}, {r['ic_con_nodi'][1]:+.5f}]  segno {segno(r)}")
    for nome, (n1, n2, fascia) in ALTRI.items():
        r = _boot(celle, diff(n1, n2, fascia), rng)
        R["altri"][nome] = {**r, "segno": segno(r)}
        print(f"  {nome:28s} {r['media']:+.5f} [{r['ic_con_nodi'][0]:+.5f}, {r['ic_con_nodi'][1]:+.5f}]  segno {segno(r)}")
    sotto = [int((z["celle_valide"] < N).sum()) for z in celle.values()]
    cv = np.concatenate([z["celle_valide"] for z in celle.values()])
    R["nodi_sotto_N"] = {"N": N, "media_per_cella": float(np.mean(sotto)), "massimo": int(max(sotto)),
                         "nodi": int(len(next(iter(celle.values()))["celle_valide"])),
                         "celle_valide_min_mediana_max": [int(cv.min()), float(np.median(cv)), int(cv.max())]}
    print(f"  nodi sotto N={N}: media {np.mean(sotto):.1f} per cella, massimo {max(sotto)}; "
          f"celle valide per nodo min/mediana/max {cv.min()}/{np.median(cv):.0f}/{cv.max()}")
    from evoluzione.esperimenti.esegui_e4 import B_BOOT
    R["repliche"] = B_BOOT; R["seme_bootstrap"] = SEME_BOOT
    R["istante"] = datetime.now(timezone.utc).isoformat()
    (out / "e6_risultati.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print(f"  salvato in {out / 'e6_risultati.json'}")
    return R


# --------------------------------------------------------------------- main --
def main() -> int:
    ap = argparse.ArgumentParser(description="E6 parte B (PEMS08)")
    ap.add_argument("--fase", choices=("pilota", "addestra", "seleziona-F", "valuta", "scegli", "test"),
                    required=True)
    ap.add_argument("--episodio", choices=("validazione", "prova"), default=None)
    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    print("=" * 84); print(f"E6 — PEMS08, fase {a.fase}"); print("=" * 84)
    for f in ("pesi_pems08/pesi_PEMS08_p5_p5.json", "maschere/maschere_PEMS08_p5.npz", "canonico"):
        if not (a.out / f).exists():
            raise SystemExit(f"prerequisito assente: {a.out / f}")
    if a.fase == "pilota":
        cfg = cfg_e6("C", CONTESTI[0], 0, SEME_PILOTA, a.out, ETICHETTA_PILOTA)
        print(f"  un addestramento: C su {CONTESTI[0]} p0 seme {SEME_PILOTA}, fine_periodo {T0_PROVA}, "
              f"pesi {cfg['dir_pesi']}, epoche {cfg['epoche']}, fili {a.fili}; cartella {a.out / ETICHETTA_PILOTA}")
        print("  il punto di controllo NON si guarda: serve solo il tempo")
        if a.piano:
            return 0
        r = _pilota(a.out, a.fili)
        print(f"\n  COSTO PILOTA: {r['secondi']:.0f} s = {r['secondi'] / 60:.1f} min (processo unico, {r['fili']} fili)")
        (a.out / "e6_pilota.json").write_text(json.dumps(r, indent=2))
        return 0
    if a.fase == "addestra":
        return fase_addestra(a.out, a.lavoratori, a.fili, a.piano)
    if a.fase == "seleziona-F":
        return fase_seleziona_F(a.out, a.piano)
    if a.fase == "valuta":
        if a.episodio is None:
            raise SystemExit("--fase valuta richiede --episodio validazione|prova")
        return fase_valuta(a.out, a.lavoratori, a.fili, a.piano, a.episodio)
    if a.fase == "scegli":
        return fase_scegli(a.out)
    fase_test(a.out); return 0


if __name__ == "__main__":
    raise SystemExit(main())
