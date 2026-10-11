#!/usr/bin/env python3
"""
Tutti i tempi del paper in UNA sessione, su UNA macchina ferma.
=================================================================
Campione isolato (partizione 0, semi 201-203), un processo, un filo di torch, nell'ordine:

    per ogni citta' e seme:   E′ (addestramento iniziale del modello unico col token)
                              C  (addestramento del modello senza identita')
                              R-orig(24 h), R-orig(1 sett.)   riaddestramento leale
                              F′(24 h), F′(1 sett.)           adattamento
    PEMS08:                   fase `costi` di E6 (C, A, E′, R-orig 24 h/1 sett., F′ 24 h/1 sett.)

Nulla di E3, E3-bis, E4, E6 viene toccato: ogni uscita va in cartelle `*_sessione`
(`E1_costi_sessione`, `inserimento_griglia_sessione`, `inserimento_griglia_672_sessione`,
`e6_sessione_*`). Controlli: ogni wCE di C, R-orig e F′ riproduce quella registrata entro 1e-6
relativo; ogni E′ e ogni checkpoint di PEMS08 riproduce l'impronta dei pesi gia' congelati.
Load average e macchina registrati prima e dopo. Scrive `results/evoluzione/costi_sessione.json`
dopo OGNI misura (ripresa con `--riprendi` se la sessione si interrompe: una ripresa e' dichiarata
nel json, non nascosta).

Uso (dalla radice OR3/, macchina ferma, nessun altro processo pesante):

    poetry run python evoluzione/esperimenti/costi_sessione.py --piano
    poetry run python evoluzione/esperimenti/costi_sessione.py
    poetry run python evoluzione/esperimenti/costi_appaiati.py --sessione     # la tabella
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

from evoluzione.esperimenti.esegui_e4 import CITTA  # noqa: E402
from evoluzione.esperimenti.esegui_inserimento import ISOLATO  # noqa: E402

SEMI = ISOLATO["semi"]
P0 = ISOLATO["partizione"]
TOLLERANZA = 1e-6
ET_E1 = "E1_costi_sessione"
ET_INS = {96: "inserimento_griglia_sessione", 672: "inserimento_griglia_672_sessione"}
ORIG_INS = {96: "inserimento_griglia", 672: "inserimento_griglia_672"}
PREFISSO_PEMS = "e6_sessione_"


def _h16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _impronta_ck(p: Path) -> str:
    from evoluzione.componente.adattamento import carica_E
    return carica_E(p, 5)[2]


def macchina() -> dict:
    import torch
    cpu = ""
    try:
        cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
    except Exception:                                        # noqa: BLE001
        pass
    return {"piattaforma": platform.platform(), "arch": platform.machine(), "cpu": cpu,
            "python": platform.python_version(), "torch": torch.__version__, "fili_torch": 1,
            "load_average": list(os.getloadavg())}


def cfg_E1(out: Path, c: str, s: int) -> dict:
    """La configurazione EFFETTIVA dell'addestramento originale di E′, dal registro
    (`resolved_configuration`), non ricostruita a memoria."""
    for f in sorted((out / "registro").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if d.get("esperimento") == "E1_inserimento_griglia/E1" and d.get("run_status") == "completato" \
                and d.get("note") == f"{c} p{P0} seme {s}":
            cfg = dict(d["resolved_configuration"])
            for k in ("contesto", "partizione", "seme", "seme_torch", "braccio"):
                cfg.pop(k, None)
            cfg["braccio"] = "E1"
            return cfg
    raise RuntimeError(f"registro: nessun addestramento completato di E1 per {c} p{P0} seme {s}")


def misura_E1(c: str, s: int, out: Path, fili: int) -> dict:
    from evoluzione.esperimenti import esegui_E
    from evoluzione.esperimenti.fasi import PARTIZIONI, percorso_E
    from evoluzione.esperimenti.semi import configurazione
    _, dich, semi_torch = configurazione(inserimento=True)
    x = [x for x in esegui_E.piano([c], dich, semi_torch, PARTIZIONI, braccio="E1")
         if x["partizione"] == P0 and x["seme"] == s]
    if len(x) != 1:
        raise RuntimeError(f"E1 {c} p{P0} s{s}: {len(x)} voci nel piano")
    x = x[0]
    cfg = cfg_E1(out, c, s)
    cfg["etichetta"] = ET_E1
    cfg["dir_stati_completi"] = str(out / f"stati_completi_{ET_E1}")
    r = esegui_E._lavora((x, cfg, str(out), fili))
    if r["esito"] != "completata":
        raise RuntimeError(f"E1 {c} s{s}: {r.get('errore')}")
    nuovo = percorso_E(out / ET_E1, c, P0, x["seme_torch"], braccio="E1")
    orig = percorso_E(out / "E1_inserimento_griglia", c, P0, x["seme_torch"], braccio="E1")
    i_n, i_o = _impronta_ck(nuovo), _impronta_ck(orig)
    if i_n != i_o:
        raise RuntimeError(f"E1 {c} s{s}: impronta dei pesi {i_n} diversa dall'originale {i_o}")
    return {"addestramento_s": r["secondi"], "impronta_pesi": i_n, "riproduce_originale": True}


def misura_inserimento(c: str, s: int, braccio: str, L: int, out: Path, fili: int) -> dict:
    from evoluzione.esperimenti import esegui_inserimento as EI
    from evoluzione.esperimenti.fasi import PARTIZIONI
    from evoluzione.esperimenti.semi import configurazione
    _, dich, semi_torch = configurazione(inserimento=True)
    x = [x for x in EI.piano([c], dich, semi_torch, PARTIZIONI, bracci=[braccio])
         if x["partizione"] == P0 and x["seme"] == s]
    if len(x) != 1:
        raise RuntimeError(f"{braccio} {c} p{P0} s{s}: {len(x)} voci nel piano")
    x = dict(x[0])
    x["etichetta"] = ET_INS[L]
    if L != 96:
        x["calendario"] = (EI.CALENDARIO[c][0], EI.CALENDARIO[c][0] + L)
        x["attesa_dati_s"] = L * 900
    r = EI._lavora((x, str(out), fili, "isolata"))
    if r["esito"] != "completata":
        raise RuntimeError(f"{braccio} {c} s{s} L{L}: {r.get('errore')}")
    nome = f"{braccio}_{c}_p{P0}_s{s}.json"
    nuovo = json.loads((out / ET_INS[L] / nome).read_text())
    orig = json.loads((out / ORIG_INS[L] / nome).read_text())
    w_n = nuovo["valutazione"]["perimetro_primario"]["perdita"]
    w_o = orig["valutazione"]["perimetro_primario"]["perdita"]
    rel = abs(w_n - w_o) / max(abs(w_o), 1e-12)
    if rel > TOLLERANZA:
        raise RuntimeError(f"{braccio} {c} s{s} L{L}: wCE {w_n:.6f} contro registrata {w_o:.6f} (scarto {rel:.1e})")
    return {"addestramento_s": nuovo["costo"]["addestramento_s"], "inserimento_s": nuovo["costo"]["inserimento_s"],
            "secondi_parete": r["secondi"], "wce": w_n, "wce_registrata": w_o, "scarto_relativo": rel}


def misura_Fp(c: str, s: int, out: Path, fili: int) -> dict:
    from evoluzione.esperimenti.costi_e4 import _misura
    r = _misura(c, P0, s, out, 672, fili)
    return {k: {"inserimento_s": v["inserimento_s"], "aggiornamenti": v["aggiornamenti"], "origini": v["origini"],
                "scarto_relativo": v["scarto_relativo"]} for k, v in r["misure"].items()}


def misura_pems08(out: Path) -> dict:
    """La fase `costi` di E6 con prefisso proprio; `e6_costi.json` originale preservato."""
    from evoluzione.esperimenti import esegui_e6 as E6
    E6.PREFISSO_COSTI = PREFISSO_PEMS
    f_orig = out / "e6_costi.json"
    f_bk = out / "e6_costi.prima_della_sessione.json"
    if f_orig.exists() and not f_bk.exists():
        shutil.copy2(f_orig, f_bk)
    try:
        if E6.fase_costi(out, False) != 0:
            raise RuntimeError("fase costi di E6 fallita")
        nuovo = json.loads(f_orig.read_text())
    finally:
        if f_bk.exists():
            shutil.copy2(f_bk, f_orig)
    (out / "costi_sessione_pems08.json").write_text(json.dumps(nuovo, indent=2, ensure_ascii=False))
    # controllo: ogni checkpoint della sessione riproduce i pesi del campione isolato di E6
    rip, tot = 0, 0
    E_TOK = E6._nome_e_token()
    for s in E6.SEMI_COSTI:
        for b, L in (("C", None), ("A", None), (E_TOK, None), (E6.R_ORIG, E6.L24), (E6.R_ORIG, E6.SETTIMANA)):
            x = {"contesto": E6.CONTESTI[0], "partizione": 0, "seme": int(s), "braccio": b, "isolato": True}
            if L is not None:
                x["acquisizione"] = L
            E6.PREFISSO_COSTI = PREFISSO_PEMS; ck_n = E6._ck_di(x, out)
            E6.PREFISSO_COSTI = "e6_costi_"; ck_o = E6._ck_di(x, out)
            tot += 1
            if ck_o.exists() and _impronta_ck(ck_n) == _impronta_ck(ck_o):
                rip += 1
    E6.PREFISSO_COSTI = PREFISSO_PEMS
    nuovo["checkpoint_che_riproducono_i_pesi_di_e6"] = f"{rip}/{tot}"
    if rip != tot:
        raise RuntimeError(f"PEMS08: solo {rip}/{tot} checkpoint riproducono i pesi del campione di E6")
    return nuovo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--riprendi", action="store_true")
    ap.add_argument("--carico-max", type=float, default=4.0, help="load average (1 min) oltre il quale non si parte")
    a = ap.parse_args()
    fj = a.out / "costi_sessione.json"
    celle = [(c, s) for c in CITTA for s in SEMI]
    print("=" * 84)
    print("COSTI — UNA SESSIONE, UNA MACCHINA FERMA, UN PROCESSO")
    print("=" * 84)
    m = macchina()
    print(f"  {m['cpu'] or m['arch']} | torch {m['torch']} | load average ora {m['load_average']}")
    print(f"  {len(celle)} celle citta' × (E′, C, R-orig 24 h, R-orig 1 sett., F′ 24 h, F′ 1 sett.) + PEMS08 (15 addestramenti + 6 adattamenti)")
    # stima dai file esistenti, solo per il piano
    try:
        K3 = json.loads((a.out / "costi_e3.json").read_text())
        K3b = json.loads((a.out / "costi_e3bis.json").read_text())
        K6 = json.loads((a.out / "e6_costi.json").read_text())
        fatti = sorted((a.out / "E1_inserimento_griglia").glob("*.fatto"))
        e1 = [json.loads(f.read_text())["secondi"] for f in fatti]
        e1_med = sorted(e1)[len(e1) // 2] if e1 else 0.0
        ore = (len(celle) * (e1_med + K3["C"]["addestramento_s"] + K3["R-orig"]["inserimento_s"]
                             + K3b["R-orig"]["inserimento_s"] + 600)
               + 3 * sum(v["mediana"] for v in K6["addestramento_s"].values()) + 900) / 3600
        print(f"  stima dai file (C {K3['C']['addestramento_s']/60:.0f} min, E′ {e1_med/60:.0f} min concorrente, "
              f"R-orig {K3['R-orig']['inserimento_s']/60:.0f} / {K3b['R-orig']['inserimento_s']/60:.0f} min, "
              f"PEMS08 {sum(v['mediana'] for v in K6['addestramento_s'].values())/60:.0f} min per seme): **~{ore:.0f} h**")
    except (OSError, KeyError, ValueError) as e:
        print(f"  stima non disponibile ({type(e).__name__})")
    if a.piano:
        return 0
    if m["load_average"][0] > a.carico_max:
        print(f"\n  load average {m['load_average'][0]:.2f} > {a.carico_max}: la macchina non e' ferma. Fermo qui.")
        return 1
    doc = {"istante_inizio": datetime.now(timezone.utc).isoformat(), "macchina_prima": m,
           "modalita": "isolata, un processo, un filo di torch, una sessione", "carico_max_ammesso": a.carico_max, "celle": {}, "riprese": 0}
    if a.riprendi and fj.exists():
        doc = json.loads(fj.read_text()); doc["riprese"] = doc.get("riprese", 0) + 1
        doc.setdefault("carichi_alla_ripresa", []).append(m["load_average"])
        print(f"  ripresa n. {doc['riprese']} (dichiarata nel json)")
    import torch
    torch.set_num_threads(a.fili)

    def salva():
        fj.write_text(json.dumps(doc, indent=2, ensure_ascii=False))

    t_in = time.time()
    for c, s in celle:
        k = f"{c}_p{P0}_s{s}"
        cella = doc["celle"].setdefault(k, {"contesto": c, "seme": s})
        for nome, fn in (("E1", lambda: misura_E1(c, s, a.out, a.fili)),
                         ("C", lambda: misura_inserimento(c, s, "C", 96, a.out, a.fili)),
                         ("R-orig_96", lambda: misura_inserimento(c, s, "R-orig", 96, a.out, a.fili)),
                         ("R-orig_672", lambda: misura_inserimento(c, s, "R-orig", 672, a.out, a.fili)),
                         ("Fp", lambda: misura_Fp(c, s, a.out, a.fili))):
            if nome in cella:
                continue
            t_ = time.time()
            cella[nome] = fn()
            cella[nome]["load_average_dopo"] = list(os.getloadavg())
            salva()
            print(f"  {c:10s} s{s} {nome:10s} {time.time() - t_:8.1f} s   [{(time.time() - t_in) / 3600:5.2f} h]", flush=True)
    if "PEMS08" not in doc:
        doc["PEMS08"] = misura_pems08(a.out); salva()
        print(f"  PEMS08 fatto   [{(time.time() - t_in) / 3600:5.2f} h]")
    doc["macchina_dopo"] = macchina()
    doc["istante_fine"] = datetime.now(timezone.utc).isoformat()
    doc["ore_sessione"] = (time.time() - t_in) / 3600
    salva()
    print(f"\n  sessione chiusa in {doc['ore_sessione']:.2f} h; load average dopo {doc['macchina_dopo']['load_average']}")
    print(f"  salvato in {fj} (impronta {_h16(fj)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
