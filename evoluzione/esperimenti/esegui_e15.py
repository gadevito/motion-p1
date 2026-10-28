#!/usr/bin/env python3
"""
E15 — Campagna causale end-to-end (protocol/E15.md).
=====================================================
Statica causale a FINESTRA ESPANSIVA (predefinita del codice dopo E15: `inserimento.STATICA_PREDEFINITA`),
tre citta', episodio 1, 3 partizioni, semi 201–206. Cinque fasi, nell'ordine:

    --fase controllo   UNA cella (Madrid, p0, seme 201), braccio C, con `--statica congelata` e gli
                       stessi semi, in una cartella propria: la wCE deve coincidere con quella della
                       campagna congelata (`inserimento_griglia/C_Madrid_p0_s201.json`) a scarto ZERO,
                       e il punto di controllo bit per bit. Prova che e' cambiata solo la statica.
    --fase preflight   `checks/preflight.py` (15 controlli, il 15 sulla finestra espansiva) su tutte
                       le 54 celle (citta' x partizione x seme); verde ovunque, o si ferma.
    --fase addestra    270 addestramenti: E, E' (token, rho 0,15), C, A, C_A per cella, con gli STESSI
                       esecutori della campagna (`esegui_E._lavora`, `esegui_inserimento._lavora`),
                       in cartelle proprie `e15_*`; ripresa dai marcatori; tempo di parete come assert.
    --fase valuta-validazione   per cella, episodio di VALIDAZIONE causale (nodi di validazione, finestra
                       espansiva): F0' e F'(1 sett.; k) per k in (10, 50, 200), passo congelato.
    --fase scegli-k    k per citta' dalla validazione (wCE media su eta' > 1 settimana); scritto in
                       e15_k_secondaria.json con impronta PRIMA di qualsiasi valutazione sul test.
    --fase valuta      per cella, episodio di PROVA: C, A, C_A dai punti (A e C_A con la statica dei nodi
                       di prova su [0, t0): per loro sono iniziali — lettura 1 del revisore); F0 (media di
                       E), F0' (token di E'), F'(1 sett.) con la configurazione congelata; F'(1 sett.; k
                       scelto); aggregati A, B per (fascia d'eta', nodo, orizzonte).
    --fase analizza    le sette differenze (F0-C, F0'-C, F'(1 sett.)-C, F'(1 sett.)-A, A-C, A-C_A,
                       C_A-C) con 4.000 ricampionamenti congiunti; le cinque congelate sulle STESSE
                       celle e con le STESSE estrazioni (predizioni_e5 ep. 1, predizioni_e4 per F0);
                       verdetto (segno dell'intervallo) causale accanto al congelato; le pubblicate a 12
                       semi come riferimento; rapporti (F0-C)/(A-C) e (F0-C)/(A-C_A); k secondario.
                       Scrive e15_risultati.json.

Perimetro: origini comuni dopo t1; per i confronti a una settimana, origini con eta' > 1 settimana.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_e15.py --fase controllo
    poetry run python evoluzione/esperimenti/esegui_e15.py --fase preflight
    poetry run python evoluzione/esperimenti/esegui_e15.py --fase addestra --piano
    poetry run python evoluzione/esperimenti/esegui_e15.py --fase addestra --lavoratori 16
    poetry run python evoluzione/esperimenti/esegui_e15.py --fase valuta-validazione --lavoratori 16
    poetry run python evoluzione/esperimenti/esegui_e15.py --fase scegli-k
    poetry run python evoluzione/esperimenti/esegui_e15.py --fase valuta --lavoratori 16
    poetry run python evoluzione/esperimenti/esegui_e15.py --fase analizza
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

from evoluzione.componente.bracci import proprieta as proprieta_braccio  # noqa: E402
from evoluzione.esperimenti.esegui_e4 import (  # noqa: E402
    B_BOOT, CITTA, D_STAT, FASCE_ETA, _aggregati, _wce)

PARTIZIONI_E15 = (0, 1, 2)
SEMI_E15 = (201, 202, 203, 204, 205, 206)
BRACCI_ADDESTRATI = ("E", "E1", "C", "A", "C_A")        # E' = E1 (token ignoto), rho 0,15
RHO = 0.15
ET = {"E": "e15_E_inserimento_griglia", "E1": "e15_E1_inserimento_griglia",
      "ins": "e15_inserimento_griglia", "controllo": "e15_controllo_congelata"}
DIR_PRED = "predizioni_e15"
L_SETT = 672
K_SECONDARIA = (10, 50, 200)                               # la griglia di `seleziona_F.AGGIORNAMENTI`
# la configurazione di F' congelata per citta' (aggiornamenti, passo): il file deve coincidere
PROTOCOLLO_F = {"Madrid": (50, 0.01), "Londra": (50, 0.01), "Melbourne": (200, 0.001)}
CELLA_CONTROLLO = ("Madrid", 0, 201, "C")
SEME_BOOT = 20261023
DELTA_NI = 0.005                                            # categoria E17, riportata accanto al segno
STATICA_E15 = "espansiva"


# ------------------------------------------------------------------ comuni --
def celle():
    return [(c, p, s) for s in SEMI_E15 for p in PARTIZIONI_E15 for c in CITTA]


def scrivi(f: Path, obj):
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
    os.replace(tmp, f)


def semi_torch_di():
    from evoluzione.esperimenti.semi import configurazione
    _, dich, st = configurazione(inserimento=True)
    d = {int(s): int(t) for s, t in zip(dich, st)}
    if tuple(dich[:6]) != SEMI_E15:
        raise RuntimeError(f"i primi sei semi dichiarati sono {dich[:6]}, attesi {SEMI_E15}")
    return d


def cfg_E(braccio: str, out: Path) -> dict:
    """La configurazione di `esegui_E.main` per il protocollo `griglia` (E) e `griglia_E1` (E'),
    con l'etichetta propria di E15."""
    et = ET[braccio]
    return {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
            "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
            "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
            "etichetta": et, "braccio": braccio,
            **({"rho": RHO} if proprieta_braccio(braccio).richiede_rho else {}),
            "training_protocol": "principale", "griglia_temporale": "reale",
            "dir_pesi": str(out / "pesi_griglia"),
            "checkpoint_selection_population": "initial_network",
            "dir_canonico": str(out / "canonico"),
            "dir_stati_completi": str(out / f"stati_completi_{et}")}


def ck_di(b, c, p, s, out: Path, st: dict) -> Path:
    from evoluzione.esperimenti.fasi import percorso_E
    if proprieta_braccio(b).preparatorio:          # E ed E' (tabella unica), via `esegui_E`
        return percorso_E(out / ET[b], c, p, st[s], braccio=b)
    return out / ET["ins"] / f"ck_{b}_{c}_p{p}_s{s}.pt"


def marcatore_di(b, c, p, s, out: Path, st: dict) -> Path:
    if proprieta_braccio(b).preparatorio:          # E ed E' (tabella unica), via `esegui_E`
        return ck_di(b, c, p, s, out, st).with_name(ck_di(b, c, p, s, out, st).name + ".fatto")
    return out / ET["ins"] / f"{b}_{c}_p{p}_s{s}.json.fatto"


def piano_addestra(out: Path, st: dict):
    """Un braccio per cella, celle intercalate: citta' e bracci ruotati come in fase 1 e 3."""
    P = []
    for i, s in enumerate(SEMI_E15):
        for j, p in enumerate(PARTIZIONI_E15):
            r = (i * len(PARTIZIONI_E15) + j) % len(CITTA)
            k = (i * len(PARTIZIONI_E15) + j) % len(BRACCI_ADDESTRATI)
            for c in CITTA[r:] + CITTA[:r]:
                for b in BRACCI_ADDESTRATI[k:] + BRACCI_ADDESTRATI[:k]:
                    P.append({"contesto": c, "partizione": p, "seme": int(s), "seme_torch": st[s],
                              "braccio": b})
    return P


def _addestra(args):
    """UN addestramento, con gli esecutori della campagna. A livello di modulo per `spawn`."""
    x, out, fili = args
    out = Path(out)
    from evoluzione.esperimenti.inserimento import variante_statica
    b = x["braccio"]
    if proprieta_braccio(b).preparatorio:          # E ed E' (tabella unica), via `esegui_E`
        from evoluzione.esperimenti.esegui_E import _lavora
        r = _lavora((x, cfg_E(b, out), str(out), fili))
    else:
        from evoluzione.esperimenti.esegui_inserimento import _lavora
        r = _lavora(({**x, "etichetta": ET["ins"]}, str(out), fili, "concorrente"))
    return {**r, "statica": variante_statica()}


def fase_addestra(out: Path, lavoratori: int, fili: int, piano: bool) -> int:
    from evoluzione.esperimenti.esegui_E import ambiente
    from evoluzione.esperimenti.fasi import PrerequisitoMancante, verifica_E
    from evoluzione.esperimenti.inserimento import variante_statica
    st = semi_torch_di()
    P = piano_addestra(out, st)
    fatte = [x for x in P if marcatore_di(x["braccio"], x["contesto"], x["partizione"], x["seme"], out, st).exists()]
    da_fare = [x for x in P if x not in fatte]
    print("=" * 84)
    print(f"E15 — ADDESTRAMENTI ({len(P)}: {len(BRACCI_ADDESTRATI)} bracci x {len(CITTA)} citta' x "
          f"{len(PARTIZIONI_E15)} partizioni x {len(SEMI_E15)} semi) — statica «{variante_statica()}»")
    print("=" * 84)
    if variante_statica() != STATICA_E15:
        print(f"  FERMO: la campagna causale richiede la statica «{STATICA_E15}»")
        return 1
    try:
        verifica_E(out / "canonico", out / "maschere", out / "pesi_griglia",
                   [st[s] for s in SEMI_E15], list(CITTA))
        print("  prerequisiti verificati: canonico, maschere, pesi")
    except PrerequisitoMancante as e:
        print(f"\n{e}")
        return 1
    print(f"  completate (marcatore presente): {len(fatte)} | da eseguire: {len(da_fare)}")
    print(f"  parallelismo: {lavoratori} lavoratori x {fili} filo/i | ambiente {json.dumps(ambiente(fili))}")
    if piano:
        for x in da_fare[:10]:
            print(f"     {x['braccio']:3s} {x['contesto']:10s} p{x['partizione']} seme {x['seme']}")
        return 0
    for et in ET.values():
        if et != ET["controllo"]:
            (out / et).mkdir(parents=True, exist_ok=True)
    scrivi(out / ET["ins"] / "ordine_e15.json",
           {"istante": datetime.now(timezone.utc).isoformat(), "statica": variante_statica(),
            "lavoratori": lavoratori, "fili": fili, "ambiente": ambiente(fili),
            "avvertenza": "NON modificabile in funzione dei risultati", "ordine": P})
    ctx = mp.get_context("spawn"); esiti, t0 = [], time.time()
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_addestra, [(x, str(out), fili) for x in da_fare]), 1):
            esiti.append(r)
            trasc = time.time() - t0; resto = trasc / i * (len(da_fare) - i)
            print(f"  [{i:3d}/{len(da_fare)}] {r['braccio']:3s} {r['contesto']:10s} p{r['partizione']} "
                  f"s{r['seme']}  {r['esito']:10s} {r['secondi']/60:5.1f} min | trascorse {trasc/3600:5.1f} h, "
                  f"ne restano ~{resto/3600:5.1f} h" + (f"\n        {r['errore']}" if r["esito"] == "fallita" else ""),
                  flush=True)
            lo, hi = proprieta_braccio(r["braccio"]).parete_attesa_min
            if r["esito"] == "completata" and not (lo <= r["secondi"] / 60 <= hi):
                print(f"\n  **FERMO IL LANCIO**: {r['secondi']/60:.1f} min fuori da [{lo:g}, {hi:g}] per {r['braccio']}",
                      flush=True)
                esiti.append({**r, "esito": "fuori_intervallo"}); pool.terminate(); break
    fallite = [r for r in esiti if r["esito"] in ("fallita", "fuori_intervallo")]
    scrivi(out / ET["ins"] / "esito_e15.json",
           {"completate": len(esiti) - len(fallite), "fallite": fallite, "gia_fatte": len(fatte),
            "ore_calendario": (time.time() - t0) / 3600, "ore_macchina": sum(r["secondi"] for r in esiti) / 3600,
            "statica": variante_statica(), "ambiente": ambiente(fili), "lavoratori": lavoratori, "fili": fili,
            "istante": datetime.now(timezone.utc).isoformat()})
    print(f"\n  {len(esiti) - len(fallite)} completate, {len(fallite)} fallite, {len(fatte)} gia' fatte; "
          f"{(time.time() - t0)/3600:.1f} h di calendario, {sum(r['secondi'] for r in esiti)/3600:.1f} ore-macchina")
    return 0 if not fallite else 1


# --------------------------------------------------------------- controllo --
def fase_controllo(out: Path, fili: int) -> int:
    """Una cella con la statica CONGELATA e gli stessi semi: wCE a scarto zero e punto bit per bit."""
    import numpy as np
    import torch
    from evoluzione.esperimenti.esegui_inserimento import _lavora
    from evoluzione.esperimenti.inserimento import variante_statica
    c, p, s, b = CELLA_CONTROLLO
    print("=" * 84)
    print(f"E15 — CONTROLLO A SCARTO ZERO: {b} {c} p{p} seme {s} con statica «{variante_statica()}»")
    print("=" * 84)
    if variante_statica() != "congelata":
        print("  FERMO: il controllo richiede `--statica congelata` (riproduce la campagna del Paper 1)")
        return 1
    f_rif = out / "inserimento_griglia" / f"{b}_{c}_p{p}_s{s}.json"
    ck_rif = out / "inserimento_griglia" / f"ck_{b}_{c}_p{p}_s{s}.pt"
    if not f_rif.exists() or not ck_rif.exists():
        print(f"  FERMO: manca il riferimento congelato {f_rif} o {ck_rif}")
        return 1
    st = semi_torch_di()
    x = {"contesto": c, "partizione": p, "seme": s, "seme_torch": st[s], "braccio": b, "etichetta": ET["controllo"]}
    f_out = out / ET["controllo"] / f"{b}_{c}_p{p}_s{s}.json"
    if f_out.exists():
        f_out.unlink()
    for f in (f_out.with_name(f_out.name + ".fatto"), out / ET["controllo"] / f"ck_{b}_{c}_p{p}_s{s}.pt"):
        if f.exists():
            f.unlink()
    t0 = time.time()
    r = _lavora((x, str(out), fili, "concorrente"))
    print(f"  esito {r['esito']} in {(time.time() - t0)/60:.1f} min" + (f": {r.get('errore')}" if r["esito"] != "completata" else ""))
    if r["esito"] != "completata":
        return 1
    w_rif = json.loads(f_rif.read_text())["valutazione"]["perimetro_primario"]["perdita"]
    w_ora = json.loads(f_out.read_text())["valutazione"]["perimetro_primario"]["perdita"]
    scarto = abs(w_ora - w_rif)
    d_rif = torch.load(ck_rif, map_location="cpu", weights_only=False)["state_dict"]
    d_ora = torch.load(out / ET["controllo"] / f"ck_{b}_{c}_p{p}_s{s}.pt", map_location="cpu", weights_only=False)["state_dict"]
    chiavi_ok = set(d_rif) == set(d_ora)
    diff = max(float((d_rif[k].double() - d_ora[k].double()).abs().max()) for k in d_rif) if chiavi_ok else float("nan")
    bit = chiavi_ok and all(torch.equal(d_rif[k], d_ora[k]) for k in d_rif)
    import platform
    R = {"cella": {"contesto": c, "partizione": p, "seme": s, "braccio": b}, "statica": variante_statica(),
         "wce_congelata": w_rif, "wce_riprodotta": w_ora, "scarto_assoluto": scarto,
         "scarto_relativo": scarto / abs(w_rif), "punto_identico_al_bit": bool(bit),
         "scarto_massimo_parametri": diff, "macchina": platform.platform(), "fili": fili,
         "riferimento": str(f_rif), "riprodotto": str(f_out), "secondi": time.time() - t0,
         "istante": datetime.now(timezone.utc).isoformat(),
         "verdetto": "scarto zero" if scarto == 0 and bit else
                     ("scarto nullo in wCE, punto non identico al bit" if scarto == 0 else "SCARTO NON NULLO")}
    scrivi(out / ET["controllo"] / "controllo_e15.json", R)
    print(f"  wCE congelata {w_rif:.12f} | riprodotta {w_ora:.12f} | scarto {scarto:.3e} (rel {R['scarto_relativo']:.3e})")
    print(f"  punto di controllo identico al bit: {bit} (scarto massimo sui parametri {diff:.3e})")
    print(f"  verdetto: **{R['verdetto']}** -> {out / ET['controllo'] / 'controllo_e15.json'}")
    return 0 if R["verdetto"] == "scarto zero" else 1


# --------------------------------------------------------------- preflight --
def fase_preflight(out: Path) -> int:
    from evoluzione.esperimenti.inserimento import variante_statica
    print("=" * 84)
    print(f"E15 — PREFLIGHT su {len(celle())} celle, statica «{variante_statica()}»")
    print("=" * 84)
    if variante_statica() != STATICA_E15:
        print(f"  FERMO: serve la statica «{STATICA_E15}»"); return 1
    esiti, rossi = {}, []
    for c, p, s in celle():
        cmd = [sys.executable, str(RADICE / "checks" / "preflight.py"), "--contesto", c, "--partizione", str(p),
               "--seme", str(s), "--bracci", "C", "P", "--out", str(out)]
        pr = subprocess.run(cmd, capture_output=True, text=True, cwd=str(RADICE),
                            env={**os.environ, "OR3_STATICA": variante_statica()})
        j = json.loads((out / "preflight.json").read_text()) if (out / "preflight.json").exists() else None
        ok = pr.returncode == 0 and j is not None and all(e["ok"] for e in j["esiti"])
        riga15 = [ln.strip() for ln in pr.stdout.splitlines() if ln.strip().startswith("[15]")]
        esiti[f"{c}/p{p}/s{s}"] = {"ok": ok, "codice": pr.returncode, "controlli": j["esiti"] if j else None,
                                   "riga_15": riga15[0] if riga15 else None}
        n_ok = sum(1 for e in (j["esiti"] if j else []) if e["ok"])
        print(f"  {c:10s} p{p} s{s}: {'verde' if ok else 'ROSSO'} ({n_ok}/{len(j['esiti']) if j else '?'})", flush=True)
        if not ok:
            rossi.append(f"{c}/p{p}/s{s}")
            print(pr.stdout[-1500:]); print(pr.stderr[-1500:])
    scrivi(out / "e15_preflight.json", {"statica": variante_statica(), "celle": esiti, "rosse": rossi,
                                         "istante": datetime.now(timezone.utc).isoformat()})
    print(f"\n  {len(esiti) - len(rossi)}/{len(esiti)} celle verdi -> {out / 'e15_preflight.json'}")
    return 0 if not rossi else 1


# ------------------------------------------------------------------ valuta --
def _valuta_origini(m, x, classe, nn, per, stat, pesi):
    """Come `esegui_e2.valuta`, ma con la statica PER ORIGINE quando e' espansiva."""
    import numpy as np
    import torch
    from evoluzione.componente.predittore import ORIZZONTI
    from evoluzione.esperimenti.addestramento import _lotto
    from evoluzione.esperimenti.inserimento import statica_alle_origini
    from evoluzione.esperimenti.ricostruisci_predizioni import wce_da_predizioni
    PB = np.empty((len(per), len(nn), len(ORIZZONTI), 3), dtype="float32")
    YY = np.zeros(PB.shape[:3], dtype="int8"); MM = np.zeros(PB.shape[:3], dtype=bool)
    m.eval()
    prima = {k: z.clone() for k, z in m.state_dict().items()}
    S_f = torch.as_tensor(np.asarray(stat)[nn].astype("float32"))
    with torch.inference_mode():
        for i in range(0, len(per), 256):
            bl = np.asarray(per[i:i + 256], dtype="int64")
            X, Y, Mk = _lotto(x, classe, bl, nn)
            S_o = statica_alle_origini(stat, nn, bl)
            out = m(X, node_ids=[int(z) for z in nn], static_inputs=(S_f if S_o is None else torch.as_tensor(S_o)))
            PB[i:i + len(bl)] = torch.softmax(out, -1).numpy()
            YY[i:i + len(bl)] = Y.numpy(); MM[i:i + len(bl)] = Mk.numpy()
    if any(not torch.equal(prima[k], z) for k, z in m.state_dict().items()):
        raise RuntimeError("lo stato del modello si e' mosso in inferenza")
    w, ph = wce_da_predizioni(PB, YY, MM, pesi)
    return PB, YY, MM, w



def _contesto_cella(c, p, s, out, fili):
    """Dati, nodi, pesi, configurazione di F e punti E/E' della cella: comune ai due episodi."""
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import carica_E
    from evoluzione.esperimenti.addestramento import _canali, _carica, _normalizzazione, _partizioni
    from evoluzione.esperimenti.inserimento import variante_statica
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    if variante_statica() != STATICA_E15:
        raise RuntimeError(f"statica «{variante_statica()}»: la campagna causale richiede «{STATICA_E15}»")
    st = semi_torch_di()
    D = _carica(c, out / "maschere")
    ok = GR.passi_regolari(D["ts"])
    nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])})
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    P_ = carica_pesi(out / "pesi_griglia", c, p)
    pesi = np.asarray(P_.vettore(), dtype="float64")
    cfgF = json.loads((out / "selezione_F_griglia" / "configurazione_F.json").read_text())["scelte"][c]
    if (int(cfgF["aggiornamenti"]), float(cfgF["passo"])) != PROTOCOLLO_F[c]:
        raise RuntimeError(f"configurazione di F per {c}: {cfgF} diversa dal protocollo {PROTOCOLLO_F[c]}")
    dEp, nodi_in2, imp_Ep = carica_E(ck_di("E1", c, p, s, out, st), D_STAT)
    if "identita.ignoto" not in dEp["state_dict"]:
        raise RuntimeError("il punto E' non ha il token ignoto")
    return dict(st=st, D=D, ok=ok, nodi=nodi, x=x, P_=P_, pesi=pesi, w_t=torch.as_tensor(pesi, dtype=torch.float32),
                cfgF=cfgF, dEp=dEp, nodi_in2=nodi_in2, imp_Ep=imp_Ep)


def _episodio(K, c, p, s, out, nome, t0, t1, fine, nn, k_sec, con_bracci):
    """Un episodio (prova o validazione): aggregati A, B per (fascia d'eta', nodo, orizzonte) di ciascun
    modello. La statica: espansiva per chi vede il sensore come nuovo (C, F0, F0', F'); per A e C_A i nodi
    sono iniziali, copertura su [0, t0) (lettura 1 del revisore, 27/10)."""
    import numpy as np
    from evoluzione.analisi.analizza_copertura_e4 import celle_valide
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import adatta, carica_E, copia_da_E
    from evoluzione.componente.episodio import lotti_episodio
    from evoluzione.esperimenti.esegui_e2 import da_E1
    from evoluzione.esperimenti.inserimento import (
        StaticaEspansiva, _modello_da_ck, nodi_davvero_nuovi, statica_cella, statiche)
    D, ok, nodi, x, P_, pesi, w_t, cfgF = (K[k] for k in ("D", "ok", "nodi", "x", "P_", "pesi", "w_t", "cfgF"))
    dEp, nodi_in2, st = K["dEp"], K["nodi_in2"], K["st"]
    per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
    if not len(per):
        raise RuntimeError(f"{nome}: perimetro vuoto")
    stat = statica_cella(statiche(D), D, nodi, nn, t0, s)                              # sensori nuovi
    stat_vet = statica_cella(statiche(D), D, nodi, nodi_davvero_nuovi("A", nn), t0, s)  # A, C_A: iniziali
    if not isinstance(stat, StaticaEspansiva) or not isinstance(stat_vet, StaticaEspansiva):
        raise RuntimeError("la statica della cella non e' espansiva")
    if np.array_equal(np.asarray(stat)[nn, 0], np.asarray(stat_vet)[nn, 0]):
        raise RuntimeError("statica dei nuovi uguale a quella degli iniziali: la finestra non e' applicata")
    nn_set = set(int(z) for z in nn)
    for nome_, ni in (("E'", nodi_in2), ("pesi.nodi_addestramento", P_.nodi_addestramento),
                      ("normalizzazione", nodi["addestramento"])):
        if set(int(z) for z in ni) & nn_set:
            raise RuntimeError(f"{nome}, controllo nodi, {nome_}: nodi dell'episodio presenti")
    eta = per - t0
    fasce = [eta <= FASCE_ETA[0], (eta > FASCE_ETA[0]) & (eta <= FASCE_ETA[1]), eta > FASCE_ETA[1]]
    if int(fasce[2].sum()) == 0:
        raise RuntimeError(f"{nome}: nessuna origine con eta' > 1 settimana")
    o_acq = GR.origini_acquisizione(ok, t0, t1)
    cv, cop = celle_valide(D, nn, o_acq, t0, t1)
    ris, n_agg, impr = {}, {}, {}

    def salva(nome_m, m, statica):
        PB, YY, MM, w = _valuta_origini(m, x, D["classe"], nn, per, statica, pesi)
        A, Bm = _aggregati(PB, YY, MM, pesi, fasce)
        ris[f"A_{nome_m}"] = A; ris[f"B_{nome_m}"] = Bm; ris[f"wce_{nome_m}"] = w
    if con_bracci:
        dE, nodi_in, imp_E = carica_E(ck_di("E", c, p, s, out, st), D_STAT)
        if set(int(z) for z in nodi_in) & nn_set:
            raise RuntimeError(f"{nome}, controllo nodi, E: nodi dell'episodio presenti")
        mC, dC = _modello_da_ck(ck_di("C", c, p, s, out, st), D, nodi, None)
        if set(int(z) for z in dC["nodi_iniziali"]) & nn_set:
            raise RuntimeError(f"{nome}, controllo nodi, C: nodi dell'episodio presenti")
        salva("C", mC, stat)
        for b in ("A", "C_A"):
            m_, d_ = _modello_da_ck(ck_di(b, c, p, s, out, st), D, nodi, None)
            if not nn_set <= set(int(z) for z in d_["nodi_iniziali"]):
                raise RuntimeError(f"{nome}, controllo nodi, {b}: deve contenere i nodi nuovi")
            if d_.get("training_protocol") != "principale":
                raise RuntimeError(f"{b}: protocollo {d_.get('training_protocol')}")
            salva(b, m_, stat_vet)
        for b in BRACCI_ADDESTRATI:
            impr[b] = hashlib.sha256(ck_di(b, c, p, s, out, st).read_bytes()).hexdigest()[:16]
        m0, _ = copia_da_E(dE, nodi_in, nn, D_STAT); salva("F0", m0, stat)
        impr["impronta_E"] = imp_E
    m0p, _ = da_E1(dEp, nodi_in2, nn, "token"); salva("F0p", m0p, stat)
    o_L = GR.origini_acquisizione(ok, t0, t0 + L_SETT)
    if not o_L:
        raise RuntimeError(f"{nome}: nessuna origine d'adattamento a una settimana")
    lotti = lotti_episodio(x, D["classe"], stat, nn, o_L)
    adatt = ([("Fp_672", int(cfgF["aggiornamenti"]))] if con_bracci else []) + [(f"Fp_672_k{k}", int(k)) for k in k_sec]
    for nome_m, k in adatt:
        m, forn = da_E1(dEp, nodi_in2, nn, "token")
        n_agg[nome_m] = adatta(m, forn, lotti, w_t, float(cfgF["passo"]), int(k))
        salva(nome_m, m, stat)
    if con_bracci and f"Fp_672_k{int(cfgF['aggiornamenti'])}" in ris:
        kc = f"Fp_672_k{int(cfgF['aggiornamenti'])}"
        if not (np.array_equal(ris["A_Fp_672"], ris[f"A_{kc}"]) and np.array_equal(ris["B_Fp_672"], ris[f"B_{kc}"])):
            raise RuntimeError(f"F'(1 sett.) e {kc}: aggregati diversi (adattamento non deterministico)")
    return dict(nodi=np.asarray(nn, dtype="int32"), origini=per.astype("int32"), eta=eta.astype("int32"),
                celle_valide=cv.astype("int32"), copertura=cop.astype("float32"),
                fasce=np.asarray([int(f.sum()) for f in fasce]), t0=t0, t1=t1, fine=fine,
                aggiornamenti=json.dumps(n_agg), impronte_ck=json.dumps(impr), **ris)


def _comuni(K, c, p, s):
    from evoluzione.esperimenti.inserimento import variante_statica
    return dict(contesto=c, partizione=p, seme=s, statica=variante_statica(), configurazione_F=json.dumps(K["cfgF"]),
                impronta_Ep=K["imp_Ep"], impronta_pesi=K["P_"].impronta)


def _cella_val(args):
    """Episodio di VALIDAZIONE causale: nodi di validazione, F0' e F'(1 sett.; k) per k nella griglia."""
    c, p, s, out, fili = args
    import numpy as np
    out = Path(out)
    g = out / DIR_PRED / f"val_{c}_p{p}_s{s}.npz"
    if g.exists():
        return {"c": c, "p": p, "s": s, "esito": "presente", "secondi": 0}
    t_in = time.time()
    try:
        from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
        from evoluzione.esperimenti.seleziona_F import CALENDARIO_VAL_GRIGLIA
        K = _contesto_cella(c, p, s, out, fili)
        t0v, t1v = CALENDARIO_VAL_GRIGLIA[c]
        R = _episodio(K, c, p, s, out, "validazione", t0v, t1v, CALENDARIO[c][0], K["nodi"]["validazione"], K_SECONDARIA, False)
        g.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(g, episodio="validazione", k_griglia=np.asarray(K_SECONDARIA), **_comuni(K, c, p, s), **R)
        return {"c": c, "p": p, "s": s, "esito": "ok", "secondi": time.time() - t_in,
                "wce": {q: round(float(R[f"wce_{q}"]), 5) for q in ["F0p"] + [f"Fp_672_k{k}" for k in K_SECONDARIA]}}
    except Exception as e:                                   # noqa: BLE001
        return {"c": c, "p": p, "s": s, "esito": "fallita", "errore": f"{type(e).__name__}: {e}"[:300],
                "secondi": time.time() - t_in}


def _cella_prova(args):
    """Episodio di PROVA: C, A, C_A, F0, F0', F'(1 sett.) e F'(1 sett.; k scelto) sui nodi di prova."""
    c, p, s, out, fili = args
    import numpy as np
    out = Path(out)
    g = out / DIR_PRED / f"prova_{c}_p{p}_s{s}.npz"
    if g.exists():
        return {"c": c, "p": p, "s": s, "esito": "presente", "secondi": 0}
    t_in = time.time()
    try:
        from evoluzione.componente.predittore import ORIZZONTI
        from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
        KS = json.loads((out / "e15_k_secondaria.json").read_text())
        k_sel = int(KS["k"][c])
        K = _contesto_cella(c, p, s, out, fili)
        t0, t1 = CALENDARIO[c]
        fine_tot = K["D"]["r"].shape[0] - max(ORIZZONTI)
        R = _episodio(K, c, p, s, out, "prova", t0, t1, fine_tot, K["nodi"]["prova"], (k_sel,), True)
        # CONTROLLO perimetro: le STESSE chiavi e le STESSE origini delle celle congelate (E5 ep. 1, E4)
        controllo = {}
        for nome_f, f_r in (("e5", out / "predizioni_e5" / f"ep1_{c}_p{p}_s{s}.npz"),
                            ("e4", out / "predizioni_e4" / f"prova_{c}_p{p}_s{s}.npz")):
            if not f_r.exists():
                raise RuntimeError(f"controllo perimetro: manca {f_r}")
            with np.load(f_r, allow_pickle=True) as zr:
                if not (np.array_equal(zr["nodi"].astype("int64"), R["nodi"].astype("int64"))
                        and np.array_equal(zr["origini"].astype("int64"), R["origini"].astype("int64"))):
                    raise RuntimeError(f"controllo perimetro, {nome_f}: nodi od origini diversi dalla cella congelata")
                controllo[nome_f] = "stessi nodi e stesse origini"
        g.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(g, episodio="prova", k_secondaria=k_sel, impronta_k_secondaria=KS["impronta"],
                            controllo_perimetro=json.dumps(controllo), **_comuni(K, c, p, s), **R)
        return {"c": c, "p": p, "s": s, "esito": "ok", "secondi": time.time() - t_in,
                "wce": {q: round(float(R[f"wce_{q}"]), 5) for q in ("C", "A", "C_A", "F0", "F0p", "Fp_672")}}
    except Exception as e:                                   # noqa: BLE001
        return {"c": c, "p": p, "s": s, "esito": "fallita", "errore": f"{type(e).__name__}: {e}"[:300],
                "secondi": time.time() - t_in}


def _esegui_celle(f, out: Path, lavoratori: int, fili: int, titolo: str) -> int:
    ctx = mp.get_context("spawn"); t0 = time.time(); fall = 0
    print(f"  {titolo}")
    with ctx.Pool(lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(f, [(c, p, s, str(out), fili) for c, p, s in celle()]), 1):
            if r["esito"] == "fallita":
                fall += 1
                print(f"  [{i:3d}/{len(celle())}] {r['c']:10s} p{r['p']} s{r['s']} FALLITA {r['errore']}", flush=True)
            else:
                print(f"  [{i:3d}/{len(celle())}] {r['c']:10s} p{r['p']} s{r['s']} {r['esito']:8s} {r['secondi']/60:5.1f} min  "
                      + (" ".join(f"{k} {v:.4f}" for k, v in r["wce"].items()) if "wce" in r else ""), flush=True)
    print(f"\n  {len(celle()) - fall} celle, {fall} fallite, {(time.time() - t0)/60:.1f} min")
    return 0 if fall == 0 else 1


def _addestramenti_mancanti(out: Path):
    st = semi_torch_di()
    return [(b, c, p, s) for c, p, s in celle() for b in BRACCI_ADDESTRATI
            if not marcatore_di(b, c, p, s, out, st).exists()]


def fase_valuta_validazione(out: Path, lavoratori: int, fili: int) -> int:
    from evoluzione.esperimenti.inserimento import variante_statica
    print("=" * 84)
    print(f"E15 — VALIDAZIONE causale per cella ({len(celle())} celle), statica «{variante_statica()}»")
    print("=" * 84)
    m = [z for z in _addestramenti_mancanti(out) if z[0] == "E1"]
    if m:
        print(f"  FERMO: {len(m)} punti E' senza marcatore, es. {m[:5]}"); return 1
    return _esegui_celle(_cella_val, out, lavoratori, fili,
                         f"F0' e F'(1 sett.; k) per k in {K_SECONDARIA} sui nodi di validazione, finestra espansiva")


def fase_scegli_k(out: Path) -> int:
    """k per citta' dalla VALIDAZIONE causale (wCE media su eta' > 1 settimana); scritto con impronta PRIMA del test."""
    import numpy as np
    va = _carica(out, "val")
    if len(va) != len(celle()):
        print(f"  FERMO: {len(va)} celle di validazione, attese {len(celle())}"); return 1
    f = out / "e15_k_secondaria.json"
    if f.exists():
        print(f"  FERMO: {f} esiste gia' (impronta {json.loads(f.read_text())['impronta']}): non si riscrive"); return 1
    K = {"regola": "k in (10, 50, 200), passo congelato per citta'; wCE media sulle origini con eta' > 1 settimana "
                   "dell'episodio di validazione causale (nodi di validazione, finestra espansiva); a pari merito il k minore",
         "griglia": list(K_SECONDARIA), "k": {}, "wce_validazione": {}, "k_congelato": {}, "passo": {},
         "celle_per_citta": {}, "istante": datetime.now(timezone.utc).isoformat()}
    for c in CITTA:
        cv = {k: z for k, z in va.items() if k[0] == c}
        medie = {str(k): float(np.mean([_wce(*_ab(z, f"Fp_672_k{k}", 2, None)) for z in cv.values()])) for k in K_SECONDARIA}
        K["k"][c] = int(min(K_SECONDARIA, key=lambda k: (medie[str(k)], k)))
        K["wce_validazione"][c] = medie; K["k_congelato"][c] = PROTOCOLLO_F[c][0]; K["passo"][c] = PROTOCOLLO_F[c][1]
        K["celle_per_citta"][c] = len(cv)
        print(f"  {c:10s} " + ", ".join(f"k={k}: {medie[str(k)]:.5f}" for k in K_SECONDARIA) + f"  -> k = {K['k'][c]} (congelato {PROTOCOLLO_F[c][0]})")
    K["impronta"] = hashlib.sha256(json.dumps({q: K[q] for q in ("k", "wce_validazione", "griglia")}, sort_keys=True).encode()).hexdigest()[:16]
    scrivi(f, K)
    print(f"  scritto {f}, impronta {K['impronta']} — prima di qualsiasi valutazione sul test")
    return 0


def fase_valuta(out: Path, lavoratori: int, fili: int, piano: bool) -> int:
    from evoluzione.esperimenti.inserimento import variante_statica
    print("=" * 84)
    print(f"E15 — VALUTAZIONE sulla PROVA per cella ({len(celle())} celle), statica «{variante_statica()}»")
    print("=" * 84)
    m = _addestramenti_mancanti(out)
    if m:
        print(f"  FERMO: {len(m)} addestramenti senza marcatore, es. {m[:5]}"); return 1
    if not (out / "e15_k_secondaria.json").exists():
        print("  FERMO: manca e15_k_secondaria.json (fasi valuta-validazione e scegli-k prima del test)"); return 1
    KS = json.loads((out / "e15_k_secondaria.json").read_text())
    print(f"  k secondario per citta' {KS['k']} (impronta {KS['impronta']})")
    if piano:
        print("  bracci: C, A, C_A, F0, F0', F'(1 sett.), F'(1 sett.; k scelto)"); return 0
    return _esegui_celle(_cella_prova, out, lavoratori, fili, "C, A (statica da iniziali), C_A (idem), F0, F0', F'(1 sett.), F'(1 sett.; k)")



# ----------------------------------------------------------------- analisi --
def _carica(out: Path, prefisso: str):
    import numpy as np
    celle_ = {}
    for f in sorted((out / DIR_PRED).glob(f"{prefisso}_*_p*_s*.npz")):
        with np.load(f, allow_pickle=True) as z:
            d = {q: z[q] for q in z.files}
        celle_[(str(d["contesto"]), int(d["partizione"]), int(d["seme"]))] = d
    return celle_


def _ab(z, nome, fascia, idx, origine=None):
    """(A, B) per nodo e orizzonte: fascia None = somma delle tre fasce d'eta'; `origine` "c"/"f"
    sceglie, nelle celle unite, gli aggregati causali o congelati."""
    kA, kB = (f"A_{nome}", f"B_{nome}") if origine is None else ((origine, f"A_{nome}"), (origine, f"B_{nome}"))
    A, Bm = z[kA], z[kB]
    A = A[:3].sum(0) if fascia is None else A[fascia]
    Bm = Bm[:3].sum(0) if fascia is None else Bm[fascia]
    return (A, Bm) if idx is None else (A[idx], Bm[idx])


def _boot_vec(celle_, f_vec, rng, K):
    """Le estrazioni di `_boot` (E4): partizioni, semi, posizioni dei nodi; `f_vec` -> vettore per cella."""
    import numpy as np
    kk = sorted(celle_); parts = sorted({k[1] for k in kk}); semi = sorted({k[2] for k in kk})
    m0 = np.mean([f_vec(celle_[k], None) for k in kk], axis=0)
    rep = np.empty((B_BOOT, len(m0)))
    for b in range(B_BOOT):
        ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
        nd = rng.integers(0, K, K)
        rep[b] = np.mean([f_vec(celle_[(kk[0][0], p, s)], nd) for p in ps for s in ss], axis=0)
    return m0, rep


def _ic(v):
    import numpy as np
    q = np.nanpercentile(v, [2.5, 97.5]); return [float(q[0]), float(q[1])]


def segno(ic):
    return "-" if ic[1] < 0 else ("+" if ic[0] > 0 else "0")


def categoria(ic):
    """Le categorie di E17 (superiorita', non inferiorita', inconclusivo) piu' la simmetrica
    «inferiorita'» (limite inferiore > 0): un intervallo tutto sopra zero non e' inconclusivo."""
    if ic[1] < 0:
        return "superiorita'"
    if ic[1] < DELTA_NI:
        return "non inferiorita'"
    if ic[0] > 0:
        return "inferiorita'"
    return "inconclusivo"


# le statistiche per cella, in un solo vettore: stesse estrazioni per causale e congelata
STAT = [("C", None, "c"), ("A", None, "c"), ("C_A", None, "c"), ("F0", None, "c"), ("F0p", None, "c"),
        ("Fp_672", 2, "c"), ("C", 2, "c"), ("A", 2, "c"), ("C_A", 2, "c"), ("F0", 2, "c"), ("F0p", 2, "c"),
        ("Fpk", 2, "c"),
        ("C", None, "f"), ("A", None, "f"), ("F0", None, "f"), ("F0p", None, "f"),
        ("Fp_672", 2, "f"), ("C", 2, "f"), ("A", 2, "f")]
IDX = {(n, f, o): i for i, (n, f, o) in enumerate(STAT)}
DICHIARAZIONI = [  # (nome, minuendo, sottraendo, fascia, perimetro in prosa)
    ("F0-C", "F0", "C", None, "tutte le origini dopo t1"),
    ("F0p-C", "F0p", "C", None, "tutte le origini dopo t1"),
    ("Fp_672-C", "Fp_672", "C", 2, "origini con eta' > 1 settimana"),
    ("Fp_672-A", "Fp_672", "A", 2, "origini con eta' > 1 settimana"),
    ("A-C", "A", "C", None, "tutte le origini dopo t1"),
    ("A-C_A", "A", "C_A", None, "tutte le origini dopo t1"),
    ("C_A-C", "C_A", "C", None, "tutte le origini dopo t1")]
CONGELATE = ("F0-C", "F0p-C", "Fp_672-C", "Fp_672-A", "A-C")
SECONDARIE_F2 = [("F0-C", "F0", "C"), ("F0p-C", "F0p", "C"), ("A-C", "A", "C"), ("A-C_A", "A", "C_A"), ("C_A-C", "C_A", "C")]


def _pubblicate(out: Path):
    """Le differenze PUBBLICATE (12 semi, 36 celle per citta'), come riferimento: F0-C, F0p-C, A-C e il
    rapporto (F0-C)/(A-C) da `protocol/e14b/congelata/e14b_livelli_congelata.json` (insieme congelato);
    F'(1 sett.)-C e F'(1 sett.)-A da `e3bis_risultati.json` (origini con eta' > 1 settimana), se le chiavi
    esistono. Ogni valore porta la sua fonte; se manca, resta assente e il congelamento lo dice."""
    R = {"fonti": {}, "citta": {c: {} for c in CITTA}}
    f14 = RADICE / "protocol" / "e14b" / "congelata" / "e14b_livelli_congelata.json"
    if f14.exists():
        J = json.loads(f14.read_text())
        R["fonti"]["e14b_livelli_congelata.json"] = {"impronta": hashlib.sha256(f14.read_bytes()).hexdigest()[:16],
                                                     "repliche": J.get("repliche"), "seme": J.get("seme")}
        for c in CITTA:
            z = J["per_citta"][c]
            for n in ("F0-C", "F0p-C", "A-C"):
                if n in z["differenze"]:
                    d = z["differenze"][n]
                    R["citta"][c][n] = {"media": float(d["media"]), "ic_con_nodi": [float(d["ic"][0]), float(d["ic"][1])],
                                        "celle": z["celle"], "fonte": "protocol/e14b/congelata/e14b_livelli_congelata.json"}
            r = z.get("rapporto_F0C_su_AC")
            if r:
                R["citta"][c]["(F0-C)/(A-C)"] = {"media": float(r["media"]), "ic_con_nodi": [float(r["ic"][0]), float(r["ic"][1])],
                                                 "celle": z["celle"], "fonte": "protocol/e14b/congelata/e14b_livelli_congelata.json"}
    f3 = out / "e3bis_risultati.json"
    if f3.exists():
        J = json.loads(f3.read_text())
        R["fonti"]["e3bis_risultati.json"] = {"impronta": hashlib.sha256(f3.read_bytes()).hexdigest()[:16]}
        conf = J.get("confronti", {})
        for c in CITTA:
            for nome, cand in (("Fp_672-C", ("Fpw-C", "Fp_672-C", "Fpw-C_rif")), ("Fp_672-A", ("Fpw-A", "Fp_672-A", "Fpw-A_rif"))):
                for k in cand:
                    z = conf.get(f"{c}/{k}")
                    if isinstance(z, dict) and "media" in z:
                        R["citta"][c][nome] = {"media": float(z["media"]), "ic_con_nodi": [float(v) for v in z.get("ic_con_nodi", z.get("ic", [float('nan')] * 2))],
                                               "celle": z.get("celle"), "fonte": f"e3bis_risultati.json confronti[{c}/{k}]"}
                        break
    return R


def fase_analizza(out: Path) -> int:
    import numpy as np
    pr, va = _carica(out, "prova"), _carica(out, "val")
    if len(pr) != len(celle()) or len(va) != len(celle()):
        print(f"  FERMO: {len(pr)} celle di prova e {len(va)} di validazione, attese {len(celle())}"); return 1
    rng = np.random.default_rng(SEME_BOOT)
    KS = json.loads((out / "e15_k_secondaria.json").read_text())
    PUB = _pubblicate(out)
    R = {"protocollo": "protocol/E15.md", "statica": STATICA_E15, "repliche": B_BOOT, "seme_bootstrap": SEME_BOOT,
         "k_secondaria_file": {"impronta": KS["impronta"], "istante": KS["istante"], "regola": KS["regola"]},
         "pubblicate_fonti": PUB["fonti"],
         "semi": list(SEMI_E15), "partizioni": list(PARTIZIONI_E15), "delta_non_inferiorita": DELTA_NI,
         "perimetro": {"principale": "origini comuni dopo t1 (fasce d'eta' 1-3)", "settimana": "origini con eta' > 1 settimana (fascia 3)",
                       "congelate": "predizioni_e5/ep1_* (C, A, F0', F'(1 sett.)) e predizioni_e4/prova_* (F0): stesse celle, stessi nodi, stesse origini, stesse estrazioni"},
         "k_secondaria": {}, "citta": {}, "costi": {}}
    for c in CITTA:
        cc = {k: z for k, z in pr.items() if k[0] == c}
        cv = {k: z for k, z in va.items() if k[0] == c}
        if len(cc) != 18 or len(cv) != 18:
            raise RuntimeError(f"{c}: {len(cc)} celle di prova, {len(cv)} di validazione, attese 18")
        # k secondario: dal file scritto PRIMA del test (ricalcolato qui come controllo)
        medie = {k: float(np.mean([_wce(*_ab(z, f"Fp_672_k{k}", 2, None)) for z in cv.values()])) for k in K_SECONDARIA}
        k_sel = int(KS["k"][c])
        if k_sel != min(K_SECONDARIA, key=lambda k: (medie[k], k)):
            raise RuntimeError(f"{c}: k nel file ({k_sel}) diverso da quello ricalcolato dalla validazione")
        for z in cc.values():
            if int(z["k_secondaria"]) != k_sel or str(z["impronta_k_secondaria"]) != KS["impronta"]:
                raise RuntimeError(f"{c}: una cella di prova usa un k o un'impronta diversi dal file")
        R["k_secondaria"][c] = {"k": k_sel, "wce_validazione": {str(k): medie[k] for k in K_SECONDARIA},
                                "k_congelato": PROTOCOLLO_F[c][0], "passo": PROTOCOLLO_F[c][1]}
        # le celle congelate, sulle stesse chiavi
        cong = {}
        for (c_, p, s) in cc:
            z5 = np.load(out / "predizioni_e5" / f"ep1_{c}_p{p}_s{s}.npz", allow_pickle=True)
            z4 = np.load(out / "predizioni_e4" / f"prova_{c}_p{p}_s{s}.npz", allow_pickle=True)
            d = {f"A_{n}": z5[f"A_{n}"] for n in ("C", "A", "F0p", "Fp_672")}
            d.update({f"B_{n}": z5[f"B_{n}"] for n in ("C", "A", "F0p", "Fp_672")})
            d["A_F0"], d["B_F0"] = z4["A_F0"], z4["B_F0"]
            if not np.array_equal(z5["nodi"].astype("int64"), cc[(c_, p, s)]["nodi"].astype("int64")):
                raise RuntimeError("celle congelate: nodi diversi")
            cong[(c_, p, s)] = d
        unite = {k: {**{("c", q): v for q, v in cc[k].items()}, **{("f", q): v for q, v in cong[k].items()}} for k in cc}

        def f_vec(z, idx):
            v = []
            for n, f, o in STAT:
                nome = f"Fp_672_k{k_sel}" if n == "Fpk" else n
                v.append(_wce(*_ab(z, nome, f, idx, origine=o)))
            return np.array(v)
        K = int(next(iter(cc.values()))["celle_valide"].shape[0])
        m0, rep = _boot_vec(unite, f_vec, rng, K)
        Rc = {"celle": len(cc), "nodi": K, "k_secondaria": int(k_sel),
              "livelli": {}, "dichiarazioni": {}, "congelate": {}, "pubblicate": PUB["citta"].get(c, {}),
              "secondarie_settimana": {}, "rapporti": {}}
        for n, f, o in STAT:
            Rc["livelli"][f"{'causale' if o == 'c' else 'congelata'}/{n}{'' if f is None else '/settimana'}"] = {
                "media": float(m0[IDX[(n, f, o)]]), "ic_con_nodi": _ic(rep[:, IDX[(n, f, o)]])}

        def diff(i, j):
            d0 = float(m0[i] - m0[j]); ic = _ic(rep[:, i] - rep[:, j])
            return {"media": d0, "ic_con_nodi": ic, "segno": segno(ic), "categoria": categoria(ic)}
        for nome, a_, b_, f, prosa in DICHIARAZIONI:
            Rc["dichiarazioni"][nome] = {**diff(IDX[(a_, f, "c")], IDX[(b_, f, "c")]), "perimetro": prosa}
        for nome, a_, b_, f, prosa in DICHIARAZIONI:
            if nome in CONGELATE:
                Rc["congelate"][nome] = {**diff(IDX[(a_, f, "f")], IDX[(b_, f, "f")]), "perimetro": prosa}
                Rc["dichiarazioni"][nome]["segno_congelato"] = Rc["congelate"][nome]["segno"]
                Rc["dichiarazioni"][nome]["confermata"] = Rc["dichiarazioni"][nome]["segno"] == Rc["congelate"][nome]["segno"]
                Rc["dichiarazioni"][nome]["categoria_coincide"] = (Rc["dichiarazioni"][nome]["categoria"]
                                                                   == Rc["congelate"][nome]["categoria"])
                pb = Rc["pubblicate"].get(nome)
                if pb is not None:
                    pb["scarto_da_congelata_54"] = float(pb["media"] - Rc["congelate"][nome]["media"])
        Rc["dichiarazioni"]["Fpk_672-C"] = {**diff(IDX[("Fpk", 2, "c")], IDX[("C", 2, "c")]), "perimetro": "origini con eta' > 1 settimana",
                                            "nota": f"secondaria: F'(1 sett.; k = {k_sel}) riselezionato sulla validazione causale"}
        Rc["dichiarazioni"]["Fpk_672-A"] = {**diff(IDX[("Fpk", 2, "c")], IDX[("A", 2, "c")]), "perimetro": "origini con eta' > 1 settimana",
                                            "nota": f"secondaria: k = {k_sel}"}
        for nome, a_, b_ in SECONDARIE_F2:
            Rc["secondarie_settimana"][nome] = diff(IDX[(a_, 2, "c")], IDX[(b_, 2, "c")])

        def rapporto(num, den, nome):
            n0 = m0[num[0]] - m0[num[1]]; d0 = m0[den[0]] - m0[den[1]]
            rn = rep[:, num[0]] - rep[:, num[1]]; rd = rep[:, den[0]] - rep[:, den[1]]
            Rc["rapporti"][nome] = {"media": float(n0 / d0) if d0 != 0 else None, "ic_con_nodi": _ic(rn / rd),
                                    "numeratore": float(n0), "denominatore": float(d0),
                                    "repliche_den_senza_divario": int(np.sum(rd >= 0))}      # A - C >= 0: nessun divario
        rapporto((IDX[("F0", None, "c")], IDX[("C", None, "c")]), (IDX[("A", None, "c")], IDX[("C", None, "c")]), "(F0-C)/(A-C)")
        rapporto((IDX[("F0", None, "c")], IDX[("C", None, "c")]), (IDX[("A", None, "c")], IDX[("C_A", None, "c")]), "(F0-C)/(A-C_A)")
        rapporto((IDX[("F0", None, "f")], IDX[("C", None, "f")]), (IDX[("A", None, "f")], IDX[("C", None, "f")]), "congelata (F0-C)/(A-C)")
        rapporto((IDX[("C_A", None, "c")], IDX[("C", None, "c")]), (IDX[("A", None, "c")], IDX[("C", None, "c")]), "(C_A-C)/(A-C)")
        # ADDENDUM del revisore (28/10, sola analisi): recupero causale e riduzione del costo da parte del token
        Rc["addendum"] = {"data": "2026-10-28", "recupero": {}, "riduzione_token": {}}

        def quoziente(num, den):
            """(media del rapporto puntuale, IC del rapporto nella stessa replica, repliche con denominatore <= 0)."""
            n0 = m0[num[0]] - m0[num[1]]; d0 = m0[den[0]] - m0[den[1]]
            rn = rep[:, num[0]] - rep[:, num[1]]; rd = rep[:, den[0]] - rep[:, den[1]]
            return {"media": float(n0 / d0) if d0 != 0 else None, "ic_con_nodi": _ic(rn / rd),
                    "numeratore": float(n0), "denominatore": float(d0), "repliche_den_non_positivo": int(np.sum(rd <= 0))}
        C2, A2, CA2, F2 = IDX[("C", 2, "c")], IDX[("A", 2, "c")], IDX[("C_A", 2, "c")], IDX[("Fp_672", 2, "c")]
        fC2, fA2, fF2 = IDX[("C", 2, "f")], IDX[("A", 2, "f")], IDX[("Fp_672", 2, "f")]
        Rc["addendum"]["recupero"] = {
            "definizione": "(L_C - L_F'(1 sett.)) / (L_C - L_A) sulle origini con eta' > 1 settimana (E17); "
                           "variante con A - C_A al denominatore: (L_C - L_F'(1 sett.)) / (L_C_A - L_A)",
            "causale (L_C-L_A)": quoziente((C2, F2), (C2, A2)),
            "causale (L_C_A-L_A)": quoziente((C2, F2), (CA2, A2)),
            "congelata 54 celle (L_C-L_A)": quoziente((fC2, fF2), (fC2, fA2))}
        C0, F00, F0p0 = IDX[("C", None, "c")], IDX[("F0", None, "c")], IDX[("F0p", None, "c")]
        fC0, fF00, fF0p0 = IDX[("C", None, "f")], IDX[("F0", None, "f")], IDX[("F0p", None, "f")]

        def riduzione(c, f0, f0p):
            q = quoziente((f0p, c), (f0, c))
            rn = rep[:, f0p] - rep[:, c]; rd = rep[:, f0] - rep[:, c]
            return {"media": None if q["media"] is None else float(1 - q["media"]), "ic_con_nodi": _ic(1 - rn / rd),
                    "F0p-C": q["numeratore"], "F0-C": q["denominatore"], "repliche_den_non_positivo": q["repliche_den_non_positivo"]}
        Rc["addendum"]["riduzione_token"] = {
            "definizione": "1 - (F0' - C) / (F0 - C), tutte le origini dopo t1: la quota del costo di F0 rispetto a C "
                           "che il token toglie",
            "causale": riduzione(C0, F00, F0p0), "congelata 54 celle": riduzione(fC0, fF00, fF0p0)}
        R["citta"][c] = Rc
        print(f"\n{c}: {len(cc)} celle, {Rc['nodi']} nodi; k secondario {k_sel}")
        for nome, d in Rc["dichiarazioni"].items():
            print(f"  {nome:10s} {d['media']:+.5f} [{d['ic_con_nodi'][0]:+.5f}, {d['ic_con_nodi'][1]:+.5f}] segno {d['segno']}"
                  + (f" | congelata {Rc['congelate'][nome]['media']:+.5f} segno {d['segno_congelato']} -> "
                     f"{'confermata' if d['confermata'] else 'CAMBIA'}" if nome in CONGELATE else ""))
        for nome, d in Rc["rapporti"].items():
            print(f"  {nome:22s} {d['media'] if d['media'] is None else round(d['media'], 3)} [{d['ic_con_nodi'][0]:.3f}, {d['ic_con_nodi'][1]:.3f}]")
    conf = {c: all(R["citta"][c]["dichiarazioni"][n]["confermata"] for n in CONGELATE) for c in CITTA}
    R["esito"] = {"confermate_per_citta": conf, "tutte_confermate": all(conf.values()),
                  "regola": "se le cinque dichiarazioni sono confermate in ogni citta', la campagna causale e' il risultato principale "
                            "e la congelata va nel supplemento; altrimenti il testo segue il verdetto causale e lo dice",
                  "cambiano": [f"{c}/{n}" for c in CITTA for n in CONGELATE if not R["citta"][c]["dichiarazioni"][n]["confermata"]]}
    # costi e macchina, dai marcatori e dagli esiti
    st = semi_torch_di()
    sec = {}
    for b in BRACCI_ADDESTRATI:
        v = []
        for c, p, s in celle():
            f = marcatore_di(b, c, p, s, out, st)
            try:
                v.append(float(json.loads(f.read_text())["secondi"]))
            except Exception:                                     # noqa: BLE001
                pass
        sec[b] = {"n": len(v), "minuti_mediana": float(np.median(v)) / 60 if v else None, "ore_macchina": sum(v) / 3600}
    R["costi"] = {"addestramenti": sec, "adattamenti": len(celle()),
                  "esito_e15": json.loads((out / ET["ins"] / "esito_e15.json").read_text()) if (out / ET["ins"] / "esito_e15.json").exists() else None,
                  "pilota": {f.name: json.loads(f.read_text()) for f in sorted((out / "E_pilota_e15").glob("pilota_tempi_*.json"))}
                  if (out / "E_pilota_e15").exists() else {}}
    R["controllo_scarto_zero"] = (json.loads((out / ET["controllo"] / "controllo_e15.json").read_text())
                                  if (out / ET["controllo"] / "controllo_e15.json").exists() else None)
    R["preflight"] = (json.loads((out / "e15_preflight.json").read_text()) if (out / "e15_preflight.json").exists() else None)
    if R["preflight"] is not None:
        R["preflight"] = {"celle": len(R["preflight"]["celle"]), "rosse": R["preflight"]["rosse"], "statica": R["preflight"]["statica"]}
    R["impronte_celle"] = {f"{k[0]}/p{k[1]}/s{k[2]}": json.loads(str(z["impronte_ck"])) for k, z in sorted(pr.items())}
    R["impronte_celle_validazione_Ep"] = {f"{k[0]}/p{k[1]}/s{k[2]}": str(z["impronta_Ep"]) for k, z in sorted(va.items())}
    R["istante"] = datetime.now(timezone.utc).isoformat()
    scrivi(out / "e15_risultati.json", R)
    print(f"\n  esito: {'tutte e cinque confermate in ogni citta' if R['esito']['tutte_confermate'] else 'cambiano: ' + ', '.join(R['esito']['cambiano'])}")
    print(f"  -> {out / 'e15_risultati.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="E15 — campagna causale end-to-end")
    ap.add_argument("--fase", required=True,
                    choices=("controllo", "preflight", "addestra", "valuta-validazione", "scegli-k", "valuta", "analizza"))
    ap.add_argument("--lavoratori", type=int, default=1)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    from evoluzione.esperimenti.inserimento import applica_statica, argomento_statica
    argomento_statica(ap)
    a = ap.parse_args()
    applica_statica(a.statica)
    if a.fase == "controllo":
        return fase_controllo(a.out, a.fili)
    if a.fase == "preflight":
        return fase_preflight(a.out)
    if a.fase == "addestra":
        return fase_addestra(a.out, a.lavoratori, a.fili, a.piano)
    if a.fase == "valuta-validazione":
        return fase_valuta_validazione(a.out, a.lavoratori, a.fili)
    if a.fase == "scegli-k":
        return fase_scegli_k(a.out)
    if a.fase == "valuta":
        return fase_valuta(a.out, a.lavoratori, a.fili, a.piano)
    return fase_analizza(a.out)


if __name__ == "__main__":
    raise SystemExit(main())
