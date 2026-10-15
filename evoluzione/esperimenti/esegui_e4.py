#!/usr/bin/env python3
"""
E4 — F contro C e la politica gated (protocol/E4.md).
======================================================
Nessun addestramento. Tre fasi, da eseguire nell'ordine:

    --fase valuta    per ogni cella (citta', partizione, seme) e per i DUE
                     episodi (prova, validazione): adatta F e F' per ogni durata
                     L, valuta C, F0, F0', F(L), F'(L) su tutte le origini dopo
                     t1 e salva gli AGGREGATI per (fascia d'eta', nodo,
                     orizzonte) e per (terzo, nodo, orizzonte); traiettoria di
                     F e F' a 24 h sull'episodio di prova
    --fase scegli    (tau, N) per citta' sull'EPISODIO DI VALIDAZIONE, metrica
                     integrata su tutte le origini dopo t1; scrive
                     results/evoluzione/e4_scelta_gated.json con impronta e
                     istante PRIMA di toccare il test
    --fase test      una sola valutazione sul test con la coppia scelta;
                     confronti con ricampionamento congiunto; curva; terzi;
                     figure; results/evoluzione/e4_risultati.json

Le fasce d'eta' sono (t1, t0+192], (t0+192, t0+672], (t0+672, fine]: con
tau in {24 h, 48 h, 1 settimana, mai} la politica si compone per fascia, senza
nuovi adattamenti. La curva per eta' usa la terza fascia, comune a tutte le
durate.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_e4.py --fase valuta --piano
    poetry run python evoluzione/esperimenti/esegui_e4.py --fase valuta --lavoratori 8
    poetry run python evoluzione/esperimenti/esegui_e4.py --fase scegli
    poetry run python evoluzione/esperimenti/esegui_e4.py --fase test
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

CITTA = ("Madrid", "Londra", "Melbourne")
DIR_PRED = "predizioni_e4"
DURATE = (24, 48, 96, 192, 672)             # 6 h, 12 h, 24 h, 48 h, 1 settimana
TAU = (96, 192, 672, None)                  # 24 h, 48 h, 1 settimana, mai
N_SOGLIE = (0, 77, 154, 231)
FASCE_ETA = (192, 672)                      # confini: (t1,192], (192,672], (672,fine]
PUNTI_TRAIETTORIA = (5, 10, 25, 50, 100, 200)
MODELLI = ("C", "F0", "F0p") + tuple(f"F_{L}" for L in DURATE) + \
    tuple(f"Fp_{L}" for L in DURATE)
D_STAT = 5
B_BOOT, SEME_BOOT = 4000, 20261004


def _nome_e_token():
    """Il braccio E' (token ignoto) secondo la TABELLA, non una stringa."""
    from evoluzione.componente.bracci import bracci_con
    v = bracci_con(fornitore="embedding_token")
    if len(v) != 1:
        raise RuntimeError(f"atteso un solo braccio con token ignoto: {v}")
    return v[0]


def calendario(episodio: str, c: str):
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    from evoluzione.esperimenti.seleziona_F import CALENDARIO_VAL_GRIGLIA
    return (CALENDARIO if episodio == "prova" else CALENDARIO_VAL_GRIGLIA)[c]


def _aggregati(PB, YY, MM, pesi, idx_fasce):
    """A e B per (fascia, nodo, orizzonte) e totali. `idx_fasce` e' un elenco
    di maschere booleane sulle origini."""
    import numpy as np
    T, K, H = MM.shape
    pr = np.clip(PB, 1e-12, 1.0)
    ce = -np.log(np.take_along_axis(pr, YY[..., None].astype("int64"), -1)[..., 0])
    w = pesi[YY.astype("int64")] * MM                       # (T,K,H)
    a = ce * w
    A = np.stack([a[m].sum(0) for m in idx_fasce])          # (F,K,H)
    Bm = np.stack([w[m].sum(0) for m in idx_fasce])
    return A.astype("float64"), Bm.astype("float64")


def _cella(args):
    c, p, s, episodio, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.analizza_copertura_e4 import celle_valide
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import adatta, carica_E, copia_da_E
    from evoluzione.componente.episodio import lotti_episodio
    from evoluzione.componente.predittore import ORIZZONTI
    from evoluzione.esperimenti.addestramento import (
        _canali, _carica, _normalizzazione, _partizioni)
    from evoluzione.esperimenti.esegui_e2 import da_E1, valuta
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    from evoluzione.esperimenti.fasi import percorso_E
    from evoluzione.esperimenti.inserimento import _modello_da_ck, statica_cella, statiche
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, seme_torch
    out = Path(out)
    g = out / DIR_PRED / f"{episodio}_{c}_p{p}_s{s}.npz"
    if g.exists():
        return {"c": c, "p": p, "s": s, "ep": episodio, "esito": "presente", "secondi": 0}
    t_in = time.time()
    try:
        E_TOK = _nome_e_token()
        t0, t1 = calendario(episodio, c)
        D = _carica(c, out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        fine_tot = D["r"].shape[0] - max(ORIZZONTI)
        fine = fine_tot if episodio == "prova" else CALENDARIO[c][0]
        per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
        if not len(per):
            raise RuntimeError("perimetro vuoto")
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[p])})
        nn = nodi["prova"] if episodio == "prova" else nodi["validazione"]
        NORM, nr, nv = _normalizzazione(D, nodi, ist)
        x = _canali(D, nr, nv)
        stat = statica_cella(statiche(D), D, nodi, nn, t0, s)                      # E14
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
        cfgF = json.loads((out / "selezione_F_griglia" / "configurazione_F.json")
                          .read_text())["scelte"][c]
        st = seme_torch(s)
        dE, nodi_in, imp_E = carica_E(percorso_E(out / "E_inserimento_griglia", c, p, st), D_STAT)
        dEp, nodi_in2, imp_Ep = carica_E(
            percorso_E(out / f"{E_TOK}_inserimento_griglia", c, p, st, braccio=E_TOK), D_STAT)
        # C
        mC, dC = _modello_da_ck(out / "inserimento_griglia" / f"ck_C_{c}_p{p}_s{s}.pt",
                                D, nodi, None)
        # CONTROLLO 7: i nodi dell'episodio non compaiono nella mappa nodo-riga
        # di E, E' e C, nei nodi di stima dei pesi, nel perimetro della
        # normalizzazione (nodi di addestramento): verificato, non assunto
        P_ = carica_pesi(out / "pesi_griglia", c, p)
        nn_set = set(int(z) for z in nn)
        for nome, ni in (("E", nodi_in), ("E'", nodi_in2), ("C", dC["nodi_iniziali"]),
                         ("pesi.nodi_addestramento", P_.nodi_addestramento),
                         ("normalizzazione", nodi["addestramento"])):
            inter = set(int(z) for z in ni) & nn_set
            if inter:
                raise RuntimeError(f"controllo 7, {nome}: nodi dell'episodio presenti: "
                                   f"{sorted(inter)[:5]}")
        # CONTROLLO 4: le impronte di E ed E' sono quelle delle campagne
        # (predizioni_f0 e predizioni_e2 le registrano cella per cella)
        rif = {"E": out / "predizioni_f0" / f"F0_{c}_p{p}_s{s}.npz",
               "E'": out / "predizioni_e2" / f"F0p_{c}_p{p}_s{s}.npz"}
        for nome, (f_rif, imp) in {"E": (rif["E"], imp_E), "E'": (rif["E'"], imp_Ep)}.items():
            if not f_rif.exists():
                raise RuntimeError(f"controllo 4: manca {f_rif}")
            imp_reg = str(np.load(f_rif, allow_pickle=True)["impronta_ck"])
            if imp_reg != imp:
                raise RuntimeError(f"controllo 4, {nome}: impronta {imp} diversa da "
                                   f"quella registrata {imp_reg}")
        # fasce d'eta' e terzi, sulle origini
        eta = per - t0
        idx_eta = [eta <= FASCE_ETA[0],
                   (eta > FASCE_ETA[0]) & (eta <= FASCE_ETA[1]),
                   eta > FASCE_ETA[1]]
        tagli = np.array_split(np.arange(len(per)), 3)
        idx_terzi = [np.isin(np.arange(len(per)), q) for q in tagli]
        fasce = idx_eta + idx_terzi
        cv, cop = celle_valide(D, nn, GR.origini_acquisizione(ok, t0, t1), t0, t1)
        ris = {}

        def salva(nome, m):
            PB, YY, MM, w, ph, dt = valuta(m, x, D["classe"], nn, per, S, pesi)
            A, Bm = _aggregati(PB, YY, MM, pesi, fasce)
            ris[f"A_{nome}"] = A; ris[f"B_{nome}"] = Bm
            ris[f"wce_{nome}"] = w
            return w

        salva("C", mC)
        # F0 e F0'
        m0, _ = copia_da_E(dE, nodi_in, nn, D_STAT); salva("F0", m0)
        m0p, _ = da_E1(dEp, nodi_in2, nn, "token"); salva("F0p", m0p)
        # F(L) e F'(L): adattamento su (t0, t0+L], iperparametri congelati
        # sul test tutte le durate della curva; in validazione solo i tau della
        # politica (le altre non servirebbero a nulla)
        durate = DURATE if episodio == "prova" else tuple(t for t in TAU if t is not None)
        n_agg = {}
        for L in durate:
            o_L = GR.origini_acquisizione(ok, t0, t0 + L)
            if not o_L:
                raise RuntimeError(f"L={L}: nessuna origine d'adattamento")
            lotti = lotti_episodio(x, D["classe"], stat, nn, o_L)
            # (etichetta, costruttore della copia, etichetta del punto di partenza)
            for nome, costruisci, nome0 in (
                    ("F", lambda: copia_da_E(dE, nodi_in, nn, D_STAT), "F0"),
                    ("Fp", lambda: da_E1(dEp, nodi_in2, nn, "token"), "F0p")):
                m, forn = costruisci()
                traj = None
                if episodio == "prova" and L == 96:
                    traj = {"perdita": [], "aggiornamento": [], "wce_test": {}}

                    def gancio(k, perdita, _m=m, _t=traj):
                        _t["perdita"].append(perdita); _t["aggiornamento"].append(k)
                        if k in PUNTI_TRAIETTORIA:
                            with torch.inference_mode():
                                _, _, _, w_, _, _ = valuta(_m, x, D["classe"], nn, per, S, pesi)
                            _t["wce_test"][str(k)] = w_
                n = adatta(m, forn, lotti, w_t, cfgF["passo"], cfgF["aggiornamenti"],
                           gancio=(gancio if traj is not None else None))
                n_agg[f"{nome}_{L}"] = n
                salva(f"{nome}_{L}", m)
                if traj is not None:
                    traj["wce_test"]["0"] = float(ris[f"wce_{nome0}"])
                    ris[f"traiettoria_{nome}"] = json.dumps(traj)
        # CONTROLLI 3 e 6 (solo sull'episodio di prova, dove esistono i
        # resoconti): wCE di C, F0, F0', F(24 h), F'(24 h) ricalcolate dai punti
        # contro quelle ricostruite; stessi nodi e stesse origini. Scarto
        # relativo massimo 1e-6, altrimenti ci si ferma.
        controllo_3 = {}
        if episodio == "prova":
            for mio, loro, cart in (("C", "C", "predizioni_fase3"), ("F0", "F0", "predizioni_f0"),
                                    ("F0p", "F0p", "predizioni_e2"), ("F_96", "F", "predizioni_fase3"),
                                    ("Fp_96", "Fp", "predizioni_e2")):
                f_r = out / cart / f"{loro}_{c}_p{p}_s{s}.npz"
                if not f_r.exists():
                    raise RuntimeError(f"controllo 3: manca {f_r}")
                zr = np.load(f_r, allow_pickle=True)
                if not (np.array_equal(zr["nodi"].astype("int64"), np.asarray(nn, dtype="int64"))
                        and np.array_equal(zr["origini"].astype("int64"), per)):
                    raise RuntimeError(f"controllo 6, {loro}: nodi od origini diversi")
                w_loro = _wce(zr["A_per_nodo"], zr["B_per_nodo"])
                rel = abs(float(ris[f"wce_{mio}"]) - w_loro) / abs(w_loro)
                controllo_3[mio] = {"wce": float(ris[f"wce_{mio}"]), "riferimento": w_loro,
                                    "scarto_relativo": rel}
                if rel > 1e-6:
                    raise RuntimeError(f"controllo 3, {mio} contro {cart}/{loro}: scarto "
                                       f"relativo {rel:.2e} oltre 1e-6")
        g.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            g, nodi=np.asarray(nn, dtype="int32"), origini=per.astype("int32"),
            eta=eta.astype("int32"), celle_valide=cv.astype("int32"),
            copertura=cop.astype("float32"), fasce=np.asarray([int(m.sum()) for m in fasce]), durate=np.asarray(durate),
            t0=t0, t1=t1, fine=fine, episodio=episodio, contesto=c, partizione=p, seme=s,
            impronta_E=imp_E, impronta_Ep=imp_Ep, aggiornamenti=json.dumps(n_agg),
            configurazione_F=json.dumps(cfgF), controllo_3=json.dumps(controllo_3),
            controllo_7="ok", **ris)
        return {"c": c, "p": p, "s": s, "ep": episodio, "esito": "ok",
                "secondi": time.time() - t_in,
                "wce": {k: round(float(ris[f"wce_{k}"]), 5) for k in ("C", "F0", "F0p", "F_96", "Fp_96")}}
    except Exception as e:                                   # noqa: BLE001
        return {"c": c, "p": p, "s": s, "ep": episodio, "esito": "fallita",
                "errore": f"{type(e).__name__}: {e}"[:300], "secondi": time.time() - t_in}


# ------------------------------------------------------------------ analisi --
def _wce(A, B):
    """A, B (K,H) -> wCE: media sugli orizzonti di sum_k A / sum_k B."""
    import numpy as np
    num, den = A.sum(0), B.sum(0)
    return float(np.nanmean(np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)))


def _politica(z, tau, N):
    """A, B (K,H) della politica gated(tau, N) composti per fascia d'eta'."""
    import numpy as np
    cv = z["celle_valide"]
    A0, B0 = z["A_F0p"][:3], z["B_F0p"][:3]                 # (3,K,H) fasce d'eta'
    if tau is None:
        A, Bm = A0.sum(0), B0.sum(0)
    else:
        Ap, Bp = z[f"A_Fp_{tau}"][:3], z[f"B_Fp_{tau}"][:3]
        # fascia 0: eta' <= 192; 1: (192,672]; 2: > 672. tau=96 -> F' ovunque;
        # tau=192 -> F0' su 0, F' su 1,2; tau=672 -> F0' su 0,1, F' su 2
        da = {96: 0, 192: 1, 672: 2}[tau]
        A = sum(A0[i] for i in range(da)) + sum(Ap[i] for i in range(da, 3))
        Bm = sum(B0[i] for i in range(da)) + sum(Bp[i] for i in range(da, 3))
        A = np.asarray(A, dtype="float64"); Bm = np.asarray(Bm, dtype="float64")
    sotto = cv < N                                           # resta su F0'
    A = np.where(sotto[:, None], A0.sum(0), A); Bm = np.where(sotto[:, None], B0.sum(0), Bm)
    return A, Bm


def _carica_celle(out: Path, episodio: str):
    import numpy as np
    celle = {}
    for f in sorted((out / DIR_PRED).glob(f"{episodio}_*_p*_s*.npz")):
        with np.load(f, allow_pickle=True) as z:
            # in memoria: un NpzFile decomprime a OGNI accesso, e il
            # ricampionamento ne fa migliaia
            d = {k: z[k] for k in z.files}
        d["files"] = list(d)
        celle[(str(d["contesto"]), int(d["partizione"]), int(d["seme"]))] = d
    return celle


def fase_scegli(out: Path):
    import numpy as np
    celle = _carica_celle(out, "validazione")
    if not celle:
        raise RuntimeError("nessuna cella di validazione: eseguire --fase valuta")
    scelta, griglia = {}, {}
    for c in CITTA:
        kk = [k for k in celle if k[0] == c]
        if len(kk) != 36:
            raise RuntimeError(f"{c}: {len(kk)} celle di validazione, attese 36")
        tab = {}
        for tau in TAU:
            for N in N_SOGLIE:
                tab[(tau, N)] = float(np.mean([_wce(*_politica(celle[k], tau, N)) for k in kk]))
        # SPAREGGIO: la politica piu' semplice — N maggiore, poi tau = mai, poi tau minore
        def chiave(item):
            (tau, N), v = item
            return (round(v, 9), -N, 0 if tau is None else 1, tau if tau is not None else 0)
        (tau_s, N_s), v_s = min(tab.items(), key=chiave)
        scelta[c] = {"tau": tau_s, "N": N_s, "wce_validazione": v_s,
                     "celle": len(kk)}
        griglia[c] = {f"tau={'mai' if t is None else t}/N={N}": v for (t, N), v in tab.items()}
        print(f"  {c:11s} tau = {'mai' if tau_s is None else str(tau_s) + ' passi'}, "
              f"N = {N_s}  (wCE validazione {v_s:.5f})")
    doc = {"scelta": scelta, "griglia_validazione": griglia,
           "regola": ("minimo della wCE integrata su tutte le origini dopo t1 "
                      "dell'episodio di validazione, nodi della partizione di "
                      "validazione; spareggio: N maggiore, poi tau = mai, poi tau minore"),
           "griglie": {"tau": ["96", "192", "672", "mai"], "N": list(N_SOGLIE)},
           "istante": datetime.now(timezone.utc).isoformat()}
    testo = json.dumps(doc, indent=2, ensure_ascii=False)
    doc["impronta"] = hashlib.sha256(testo.encode()).hexdigest()[:16]
    f = out / "e4_scelta_gated.json"
    if f.exists():
        prec = json.loads(f.read_text())
        if prec.get("scelta") != scelta:
            raise RuntimeError(f"{f} esiste con una scelta DIVERSA: non si sovrascrive")
        print(f"  scelta gia' registrata in {f}, identica")
        return doc
    f.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"  scelta registrata in {f} (impronta {doc['impronta']}), prima del test")
    return doc


def _boot(celle_c, f_pair, rng):
    """Differenza media e IC con ricampionamento di partizioni, semi e nodi.
    `f_pair(z, idx) -> (d)` restituisce la differenza per la cella sui nodi idx."""
    import numpy as np
    kk = sorted(celle_c)
    parts = sorted({k[1] for k in kk}); semi = sorted({k[2] for k in kk})
    K = celle_c[kk[0]]["celle_valide"].shape[0]
    m0 = float(np.mean([f_pair(celle_c[k], None) for k in kk]))
    v = []
    for _ in range(B_BOOT):
        ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
        nd = rng.integers(0, K, K)
        v.append(np.mean([f_pair(celle_c[(kk[0][0], p, s)], nd) for p in ps for s in ss]))
    q = np.percentile(v, [2.5, 97.5])
    return {"media": m0, "ic_con_nodi": q.tolist(), "include_zero": bool(q[0] * q[1] <= 0)}


def fase_test(out: Path):
    import numpy as np
    f_sc = out / "e4_scelta_gated.json"
    if not f_sc.exists():
        raise RuntimeError("scelta di (tau, N) assente: eseguire --fase scegli prima")
    SC = json.loads(f_sc.read_text())
    celle = _carica_celle(out, "prova")
    rng = np.random.default_rng(SEME_BOOT)
    R = {"scelta": SC["scelta"], "impronta_scelta": SC.get("impronta"), "confronti": {},
         "terzi": {}, "curva": {}, "traiettoria": {}, "celle": {}}

    def diff(n1, n2, fascia=None, tau=None, N=None):
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

    for c in CITTA:
        cc = {k: z for k, z in celle.items() if k[0] == c}
        if len(cc) != 36:
            raise RuntimeError(f"{c}: {len(cc)} celle di prova, attese 36")
        tau, N = SC["scelta"][c]["tau"], SC["scelta"][c]["N"]
        K = next(iter(cc.values()))["celle_valide"].shape[0]
        R["celle"][c] = {"n": len(cc), "nodi": int(K), "tau": tau, "N": N}
        print(f"\n{c}: gated(tau={'mai' if tau is None else tau}, N={N}), {len(cc)} celle, {K} nodi")
        coppie = [("F_96", "C"), ("Fp_96", "C"), ("F0", "C"), ("F0p", "C"),
                  ("gated", "F0p"), ("gated", "C"), ("gated", "Fp_96"), ("Fp_96", "F_96")]
        for n1, n2 in coppie:
            r = _boot(cc, diff(n1, n2, tau=tau, N=N), rng)
            R["confronti"][f"{c}/{n1}-{n2}"] = r
            print(f"  {n1:7s} - {n2:7s} {r['media']:+.5f} [{r['ic_con_nodi'][0]:+.5f}, "
                  f"{r['ic_con_nodi'][1]:+.5f}]" + ("   include lo zero" if r["include_zero"] else ""))
        # gated - min(C, F') : l'oracolo per citta' e' il migliore in media
        mC = np.mean([_wce(z["A_C"].sum(0), z["B_C"].sum(0)) for z in cc.values()])
        mF = np.mean([_wce(z["A_Fp_96"].sum(0), z["B_Fp_96"].sum(0)) for z in cc.values()])
        oracolo = "C" if mC <= mF else "Fp_96"
        R["confronti"][f"{c}/gated-oracolo"] = {**R["confronti"][f"{c}/gated-{oracolo}"],
                                                "oracolo": oracolo}
        # terzi consecutivi del periodo (persistenza): F - C, F' - C, F0 - C, F0' - C
        for n1 in ("F_96", "Fp_96", "F0", "F0p"):
            for i in range(3):
                R["terzi"][f"{c}/{n1}-C/terzo{i + 1}"] = _boot(cc, diff(n1, "C", fascia=3 + i), rng)
        # curva per eta': fascia 2 (> 672), comune a tutte le durate; il
        # conteggio delle origini si riporta (controllo 2) e deve coincidere
        # fra le celle della citta'
        n_com = {int(z["fasce"][2]) for z in cc.values()}
        if len(n_com) != 1:
            raise RuntimeError(f"{c}: origini comuni diverse fra le celle: {sorted(n_com)}")
        R["curva"][f"{c}/origini_comuni"] = n_com.pop()
        for L in DURATE:
            for n1 in (f"F_{L}", f"Fp_{L}"):
                R["curva"][f"{c}/{n1}-C"] = _boot(cc, diff(n1, "C", fascia=2), rng)
        for n1 in ("F0", "F0p"):
            R["curva"][f"{c}/{n1}-C"] = _boot(cc, diff(n1, "C", fascia=2), rng)
        # traiettoria: media sulle celle della wCE al passo k
        for nome in ("F", "Fp"):
            tr = [json.loads(str(z[f"traiettoria_{nome}"])) for z in cc.values()
                  if f"traiettoria_{nome}" in z["files"]]
            if tr:
                punti = sorted({int(k) for t in tr for k in t["wce_test"]})
                R["traiettoria"][f"{c}/{nome}"] = {
                    str(k): float(np.mean([t["wce_test"][str(k)] for t in tr if str(k) in t["wce_test"]]))
                    for k in punti}
                R["traiettoria"][f"{c}/{nome}/perdita"] = np.mean(
                    [t["perdita"] for t in tr], axis=0).tolist()
    # criterio primario: gated - F0' <= 0 ovunque, IC senza positivi oltre 0,005
    ok = all(R["confronti"][f"{c}/gated-F0p"]["ic_con_nodi"][1] <= 0.005 for c in CITTA)
    R["criterio"] = {"primario_gated_meno_F0p": {c: R["confronti"][f"{c}/gated-F0p"] for c in CITTA},
                     "soddisfatto": bool(ok)}
    R["repliche"] = B_BOOT; R["seme_bootstrap"] = SEME_BOOT
    R["istante"] = datetime.now(timezone.utc).isoformat()
    (out / "e4_risultati.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print("\n" + "=" * 84)
    print(f"CRITERIO PRIMARIO gated - F0' <= 0 ovunque (IC senza positivi oltre 0,005): "
          f"{'SODDISFATTO' if ok else 'NON soddisfatto'}")
    print(f"  salvato in {out / 'e4_risultati.json'}")
    return R


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fase", choices=("valuta", "scegli", "test"), required=True)
    ap.add_argument("--episodio", nargs="*", default=["prova", "validazione"])
    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    from evoluzione.esperimenti.inserimento import applica_statica, argomento_statica
    argomento_statica(ap)
    a = ap.parse_args()
    applica_statica(a.statica)
    print("=" * 84); print(f"E4 — fase {a.fase}"); print("=" * 84)
    if a.fase == "valuta":
        from evoluzione.esperimenti.semi import configurazione
        _, dich, _ = configurazione(inserimento=True)
        celle = [(c, p, int(s), ep, str(a.out), a.fili)
                 for ep in a.episodio for c in CITTA for p in (0, 1, 2) for s in dich]
        fatte = sum((a.out / DIR_PRED / f"{ep}_{c}_p{p}_s{s}.npz").exists()
                    for c, p, s, ep, _, _ in celle)
        print(f"  {len(celle)} celle ({', '.join(a.episodio)}), {fatte} gia' fatte")
        print(f"  prova: durate {DURATE}, modelli {len(MODELLI)}, traiettoria a L=96; "
              f"validazione: durate {tuple(t for t in TAU if t is not None)}")
        print(f"  E' = braccio «{_nome_e_token()}»; F con (passo, aggiornamenti) congelati "
              f"da selezione_F_griglia/configurazione_F.json; controlli 3, 4, 6, 7 per cella")
        print(f"  episodi: prova = CALENDARIO di esegui_inserimento, validazione = "
              f"CALENDARIO_VAL_GRIGLIA di seleziona_F, nodi della partizione di validazione")
        if a.piano:
            return 0
        ctx = mp.get_context("spawn"); t0 = time.time(); fall = 0
        with ctx.Pool(a.lavoratori) as pool:
            for i, r in enumerate(pool.imap_unordered(_cella, celle), 1):
                if r["esito"] == "fallita":
                    fall += 1
                    print(f"  [{i:3d}/{len(celle)}] {r['ep']:11s} {r['c']:10s} p{r['p']} s{r['s']} "
                          f"FALLITA {r['errore']}", flush=True)
                elif r["esito"] == "ok":
                    print(f"  [{i:3d}/{len(celle)}] {r['ep']:11s} {r['c']:10s} p{r['p']} s{r['s']} "
                          + " ".join(f"{k} {v}" for k, v in r["wce"].items())
                          + f"  {r['secondi']:4.0f}s", flush=True)
        print(f"\n  {len(celle) - fall} celle, {fall} fallite, {(time.time() - t0) / 60:.1f} min")
        return 0 if not fall else 1
    if a.fase == "scegli":
        fase_scegli(a.out); return 0
    fase_test(a.out); return 0


if __name__ == "__main__":
    raise SystemExit(main())
