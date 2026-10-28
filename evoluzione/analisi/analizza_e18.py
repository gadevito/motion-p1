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
def parte_A(out: Path, pilota=None, repliche=None) -> dict:
    raise NotImplementedError("parte A: dopo la stima dei tempi (pilota su una citta')")


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
            R["A"] = parte_A(a.out, a.pilota, a.repliche)
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
