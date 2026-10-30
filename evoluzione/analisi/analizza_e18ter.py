#!/usr/bin/env python3
"""
E18-ter — livelli assoluti alle soglie operative (terza revisione esterna, 30/10/2026). Sola analisi.
======================================================================================================
Richiesta del revisore (30/10, 09:00 e 09:30, punto 2.3): tabella dei valori assoluti — richiamo, tasso di falsi
allarmi, precisione della classe congestionata — alla soglia F1-ottima (`prim`) e alla soglia appaiata sul tasso di
falsi allarmi di C in validazione (`par`), per contesto, per i bracci dei confronti centrali: C, A, F0, F0', F'(1 sett.),
gated(tau, N), R-orig(1 sett.). Dagli artefatti congelati di E8:

    e8_soglie.json              soglie per contesto e braccio (impronta verificata contro ogni cella)
    predizioni_e8/prova_*.npz   matrici di confusione (fascia d'eta', sensore, orizzonte, vero, predetto) per regola e braccio
    e8_risultati.json           livelli aggregati di E8 (finestra intera): CONTROLLO BLOCCANTE, scarto <= 1e-12

Finestre: intera (tutte le origini dopo t1) per C, A, F0, F0', gated(tau, N); origini con eta' > 1 settimana (fascia 2)
per F'(1 sett.) e R-orig(1 sett.) e per la C con cui si confrontano (correzione 27: la finestra intera non e' causale
per F'(1 sett.)). I livelli sulla finestra > 1 settimana non sono in alcun congelamento: calcolati qui dalle stesse
matrici, con nota datata nel congelamento.

Per ogni livello: «aggregato» = metrica della confusione sommata sulle celle (come `livelli` di E8); «media sulle
celle» con intervallo al 95 % dal ricampionamento congiunto di E8 (partizioni, semi, posizioni dei sensori con pesi di
molteplicita'; 4 000 repliche; seme di E8 del contesto; stessi indici per tutti i bracci di un contesto).

    poetry run python evoluzione/analisi/analizza_e18ter.py --parte livelli [--repliche 4000]
    poetry run python evoluzione/analisi/analizza_e18ter.py --parte wce16

Parte `wce16` (richiesta del revisore, 30/10, 09:45): la colonna wCE della tabella delle metriche di calibrazione
(F17) ricalcolata con la definizione del manoscritto — per orizzonte Σ w_y·(−log p_y) / Σ w_y su origini e sensori
validi, poi media sui quattro orizzonti — dalle stesse probabilita' di E16 (`predizioni_e16/prova_*`, parametri di
calibrazione di `e16_risultati.json`), finestra intera per tutti i bracci e finestra > 1 settimana per F'(1 sett.) e
C (come E18 parte C). Verifiche bloccanti: (i) la media sulle celle coincide con `e16_risultati.json` → `wce` (media
del ricampionamento, stessa definizione per cella) entro 1e-9 — per le due celle sostituite il 28/10 (E18 parte C) il
confronto usa gli originali della Spark in `predizioni_e16_spark_sostituite/`, su cui E16 fu calcolato; il valore
riportato e' quello delle probabilita' attuali e lo scarto fra i due e' registrato — quindi le differenze di F16
restano invariate; (ii) per
C, F0, F0', A grezzi, i livelli per cella coincidono con gli aggregati congelati della campagna (`predizioni_e4`,
`predizioni_fase3`, `predizioni_e6`: gli stessi che il controllo di E8 riproduce) entro 1e-6 (rumore fra macchine,
voce 22); (iii) sulla finestra > 1 settimana, C e F'(1 sett.) coincidono con E18 parte C `wce_settimana` entro 1e-9.

Scrive results/evoluzione/e18ter_risultati.json (chiavi `livelli`, `wce16`).
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e4 import B_BOOT  # noqa: E402
from evoluzione.esperimenti.esegui_e8 import CONG, CONTESTI_E8, DIR_PRED, _gated_conf, metriche  # noqa: E402
from evoluzione.esperimenti.esegui_e16 import CALIBRAZIONI, _AB, _applica, _log_p, _wce_ab  # noqa: E402
from evoluzione.esperimenti.esegui_e4 import FASCE_ETA  # noqa: E402

TOLLERANZA = 1e-12
REGOLE = ("prim", "par")
METRICHE = ("richiamo", "falsi_allarmi", "precisione", "f1_congestionata")
BRACCI_INTERO = ("C", "A", "F0", "F0p", "gated")
BRACCI_SETT = ("C", "Fp_672", "Rorig_672")
FASCIA_SETT = 2


def imp(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def _metriche_vett(M):
    """M (..., 3, 3) [vero, predetto] -> dizionario di array (...) delle metriche della classe congestionata."""
    M = np.asarray(M, dtype="float64")
    tp = M[..., CONG, CONG]; fn = M[..., CONG, :].sum(-1) - tp; fp = M[..., :, CONG].sum(-1) - tp
    tn = M.sum((-1, -2)) - tp - fn - fp
    rich = tp / np.maximum(tp + fn, 1e-12); prec = tp / np.maximum(tp + fp, 1e-12); far = fp / np.maximum(fp + tn, 1e-12)
    f1c = 2 * tp / np.maximum(2 * tp + fn + fp, 1e-12)
    return {"richiamo": rich, "falsi_allarmi": far, "precisione": prec, "f1_congestionata": f1c}


def _conf_cella(z, braccio, regola, fascia, tau, N):
    """Confusione (K, 3, 3) della cella: braccio, regola, finestra (fascia None = somma delle fasce), sommata sugli orizzonti."""
    C = _gated_conf(z, regola, tau, N) if braccio == "gated" else z[f"conf_{regola}_{braccio}"]
    C = C.sum(0) if fascia is None else C[fascia]                     # (K, H, 3, 3)
    return C.sum(1).astype("float64")                                 # (K, 3, 3)


def parte_livelli(out: Path, repliche: int) -> dict:
    SG = json.loads((out / "e8_soglie.json").read_text())
    E8 = json.loads((out / "e8_risultati.json").read_text())
    R = {"definizione": "richiamo, tasso di falsi allarmi, precisione e F1 della classe congestionata alle soglie di E8 "
                        "(prim = F1-ottima in validazione; par = tasso di falsi allarmi appaiato a quello di C in validazione), "
                        "per braccio e contesto; finestra intera per C, A, F0, F0', gated(tau, N); origini con eta' > 1 settimana "
                        "per F'(1 sett.), R-orig(1 sett.) e la C di riferimento; aggregato (confusioni sommate sulle celle, come "
                        "i livelli di E8) e media sulle celle con intervallo al 95 % (ricampionamento congiunto di E8)",
         "regole": {"prim": SG["_regole"]["regola_primaria"], "par": SG["_regole"]["regola_parita"]},
         "finestre": {"intero": "tutte le origini dopo t1 (fasce sommate)", "sett": f"origini con eta' > 1 settimana (fascia {FASCIA_SETT})"},
         "bracci": {"intero": list(BRACCI_INTERO), "sett": list(BRACCI_SETT)}, "repliche": repliche, "tolleranza_controllo": TOLLERANZA,
         "impronta_soglie": SG["_impronta"], "gruppi": {}, "controllo": {},
         "impronte_ingressi": {"e8_soglie.json": imp(out / "e8_soglie.json"), "e8_risultati.json": imp(out / "e8_risultati.json")}}
    for nome, costruttore in CONTESTI_E8.items():
        ctx = costruttore(out)
        celle = {}
        for (c, p, s) in ctx["unita"]:
            g = out / DIR_PRED / f"prova_{c}_p{p}_s{s}.npz"
            if not g.exists():
                raise RuntimeError(f"manca {g}")
            with np.load(g, allow_pickle=True) as z:
                d = {k: z[k] for k in z.files}
            if str(d["impronta_soglie"]) != SG["_impronta"]:
                raise RuntimeError(f"{g.name}: impronta delle soglie diversa da e8_soglie.json")
            R["impronte_ingressi"][f"{DIR_PRED}/{g.name}"] = imp(g)
            celle[(ctx["gruppo"](c), p, s)] = d
        for gr in sorted({k[0] for k in celle}):
            cc = {k: z for k, z in celle.items() if k[0] == gr}
            kk = sorted(cc); parts = sorted({k[1] for k in kk}); semi = sorted({k[2] for k in kk})
            sc = ctx["gated"](gr); tau, N = sc["tau"], sc["N"]
            modelli = json.loads(str(next(iter(cc.values()))["modelli"]))
            K = int(next(iter(cc.values()))["celle_valide"].shape[0])
            rng = np.random.default_rng(ctx["seme_boot"])
            print(f"\n{gr}: {len(cc)} celle, K = {K}; gated(tau={tau}, N={N}); bracci {modelli}")
            G = {"celle": len(cc), "sensori": K, "gated": {"tau": tau, "N": N}, "seme_bootstrap": ctx["seme_boot"],
                 "soglie": {b: {r: SG[gr][b][r] for r in REGOLE} for b in modelli if b in SG[gr]}, "livelli": {}}
            combo = [(fin, r, b) for fin, bb in (("intero", BRACCI_INTERO), ("sett", BRACCI_SETT)) for r in REGOLE for b in bb
                     if (b in modelli) or (b == "gated" and "F0p" in modelli)]
            # confusioni per cella (ncelle, K, 3, 3) per ogni combinazione, nell'ordine kk
            CONF = {}
            for fin, r, b in combo:
                fascia = None if fin == "intero" else FASCIA_SETT
                CONF[(fin, r, b)] = np.stack([_conf_cella(cc[k], b, r, fascia, tau, N) for k in kk])
            # aggregati e controllo contro e8_risultati.json (finestra intera)
            ctrl = {"confronti": 0, "scarto_max": 0.0, "fuori": []}
            for (fin, r, b), Cn in CONF.items():
                agg = {m: float(v) for m, v in _metriche_vett(Cn.sum((0, 1))).items()}
                G["livelli"][f"{fin}/{r}/{b}"] = {"aggregato": agg}
                if fin == "intero":
                    rif = E8["gruppi"][gr]["livelli"].get(f"{r}/{b}")
                    if rif is None:
                        raise RuntimeError(f"{gr}: livello {r}/{b} assente in e8_risultati.json")
                    for m in METRICHE:
                        sc_ = abs(agg[m] - rif[m]); ctrl["confronti"] += 1; ctrl["scarto_max"] = max(ctrl["scarto_max"], sc_)
                        if sc_ > TOLLERANZA:
                            ctrl["fuori"].append(f"{gr} {r}/{b} {m}: {agg[m]!r} vs {rif[m]!r}")
            if ctrl["fuori"]:
                raise RuntimeError(f"controllo contro e8_risultati.json fallito ({len(ctrl['fuori'])}):\n    " + "\n    ".join(ctrl["fuori"]))
            print(f"  controllo contro e8_risultati.json: {ctrl['confronti']} valori, scarto massimo {ctrl['scarto_max']:.1e}")
            R["controllo"][gr] = {"confronti": ctrl["confronti"], "scarto_max": ctrl["scarto_max"]}
            # media sulle celle e ricampionamento congiunto (stessi indici per tutte le combinazioni)
            idx_cella = {k: i for i, k in enumerate(kk)}
            m0 = {key: {m: float(v.mean()) for m, v in _metriche_vett(Cn.sum(1)).items()} for key, Cn in CONF.items()}
            rep = {key: {m: np.empty(repliche) for m in METRICHE} for key in CONF}
            for bi in range(repliche):
                ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
                nd = rng.integers(0, K, K); w = np.bincount(nd, minlength=K).astype("float64")
                sel = [idx_cella[(gr, p, s)] for p in ps for s in ss]
                for key, Cn in CONF.items():
                    M = np.einsum("k,ckij->cij", w, Cn[sel])             # (ncelle ricampionate, 3, 3)
                    for m, v in _metriche_vett(M).items():
                        rep[key][m][bi] = v.mean()
            for key in CONF:
                fin, r, b = key
                G["livelli"][f"{fin}/{r}/{b}"]["media_celle"] = {
                    m: {"media": m0[key][m], "ic_con_nodi": [float(q) for q in np.percentile(rep[key][m], [2.5, 97.5])]} for m in METRICHE}
            for fin, r, b in combo:
                v = G["livelli"][f"{fin}/{r}/{b}"]
                print(f"  [{fin:6s} {r:4s}] {b:10s} richiamo {v['media_celle']['richiamo']['media']:.3f} "
                      f"[{v['media_celle']['richiamo']['ic_con_nodi'][0]:.3f}, {v['media_celle']['richiamo']['ic_con_nodi'][1]:.3f}]  "
                      f"FA {v['media_celle']['falsi_allarmi']['media']:.4f}  prec {v['media_celle']['precisione']['media']:.3f}  "
                      f"(aggregato {v['aggregato']['richiamo']:.3f} / {v['aggregato']['falsi_allarmi']:.4f} / {v['aggregato']['precisione']:.3f})", flush=True)
            R["gruppi"][gr] = G
    R["istante"] = datetime.now(timezone.utc).isoformat()
    return R


# ------------------------------------------------------------------- wce16 --
TOLL_W16, TOLL_CAMP = 1e-9, 1e-6
ETA_SETT = FASCE_ETA[1]


def _congelato_campagna(out: Path, gr: str, c: str, p: int, s: int, nome: str):
    """A, B (K, H) dell'aggregato congelato della campagna sulla finestra intera, per il braccio grezzo `nome`."""
    if gr == "PEMS08":
        f = out / "predizioni_e6" / f"prova_{c}_p{p}_s{s}.npz"
        if nome == "F0":
            f = out / "predizioni_e6bis" / f"prova_{c}_p{p}_s{s}.npz"
        z = np.load(f, allow_pickle=True); return f, z[f"A_{nome}"].sum(0), z[f"B_{nome}"].sum(0)
    if nome == "A":
        f = out / "predizioni_fase3" / f"A_{c}_p{p}_s{s}.npz"
        z = np.load(f, allow_pickle=True); return f, z["A_per_nodo"], z["B_per_nodo"]
    f = out / "predizioni_e4" / f"prova_{c}_p{p}_s{s}.npz"
    z = np.load(f, allow_pickle=True); return f, z[f"A_{nome}"].sum(0), z[f"B_{nome}"].sum(0)


def parte_wce16(out: Path) -> dict:
    E16 = json.loads((out / "e16_risultati.json").read_text())
    E18 = json.loads((out / "e18_risultati.json").read_text())
    file_p = sorted((out / "predizioni_e16").glob("prova_*_p*_s*.npz"))
    if not file_p:
        raise RuntimeError("predizioni_e16/prova_* assenti")
    R = {"definizione": "wCE con la definizione del manoscritto: per orizzonte Σ w_y·(−log p_y) / Σ w_y sulle coppie (origine, "
                        "sensore) valide, poi media sui quattro orizzonti; per cella, poi media sulle celle; dalle probabilita' di E16 "
                        "(grezze e calibrate con i parametri di e16_risultati.json); finestra intera per tutti i bracci, finestra "
                        "> 1 settimana per F'(1 sett.) e C",
         "tolleranze": {"e16": TOLL_W16, "campagna": TOLL_CAMP, "e18_C": TOLL_W16}, "finestra_passi": int(ETA_SETT),
         "gruppi": {}, "per_cella": {}, "controlli": {}, "impronte_ingressi": {"e16_risultati.json": imp(out / "e16_risultati.json"),
                                                                                "e18_risultati.json": imp(out / "e18_risultati.json")}}
    per_gr = {}
    fuori = []
    for fp in file_p:
        z = np.load(fp, allow_pickle=True)
        c, p, s, gr = str(z["contesto"]), int(z["partizione"]), int(z["seme"]), str(z["gruppo"])
        chiave = f"{gr}/{c}/p{p}/s{s}"
        par = E16["per_cella"][chiave]["parametri"]
        Y, M, w = z["y"], z["m"].astype(bool), z["pesi"].astype("float64")
        sel = z["eta"] > ETA_SETT
        cella = {"intero": {}, "sett": {}, "controllo_campagna": {}}
        for nome in json.loads(str(z["modelli"])):
            P = z[f"prob_{nome}"].astype("float64"); lp = _log_p(P)
            varianti = {"grezzo": P}
            for cal in CALIBRAZIONI:
                if f"{nome}/{cal}" in par:
                    varianti[cal] = _applica(lp, np.asarray(par[f"{nome}/{cal}"]["theta"], dtype="float64"), cal.split("_")[0])
            for var, Pv in varianti.items():
                A, B = _AB(Pv, Y, M, w)
                cella["intero"][f"{nome}/{var}"] = _wce_ab(A, B)
                if nome in ("C", "Fp_672"):
                    As, Bs = _AB(Pv[sel], Y[sel], M[sel], w)
                    cella["sett"][f"{nome}/{var}"] = _wce_ab(As, Bs)
            if nome in ("C", "F0", "F0p", "A"):
                try:
                    f_c, Ac, Bc = _congelato_campagna(out, gr, c, p, s, nome)
                except FileNotFoundError as e:
                    raise RuntimeError(f"aggregato congelato assente per {chiave} {nome}: {e}")
                w_c = _wce_ab(np.asarray(Ac, dtype="float64"), np.asarray(Bc, dtype="float64"))
                rel = abs(cella["intero"][f"{nome}/grezzo"] - w_c) / max(abs(w_c), 1e-12)
                cella["controllo_campagna"][nome] = {"file": f_c.name, "congelato": w_c, "scarto_relativo": rel}
                if rel > TOLL_CAMP:
                    fuori.append(f"{chiave} {nome}: {rel:.2e} (contro {f_c.name})")
        # celle sostituite il 28/10 (E18 parte C: ricostruite sul Mac, originali della Spark in predizioni_e16_spark_sostituite/):
        # e16_risultati.json fu calcolato sugli originali, quindi il confronto con E16 usa l'originale; il valore riportato
        # e' quello delle probabilita' attuali e lo scarto fra i due e' registrato (rumore fra macchine, voce 22)
        f_orig = out / "predizioni_e16_spark_sostituite" / fp.name
        if f_orig.exists():
            zo = np.load(f_orig, allow_pickle=True)
            cella["intero_originale_spark"] = {}
            for nome in json.loads(str(zo["modelli"])):
                P = zo[f"prob_{nome}"].astype("float64"); lp = _log_p(P)
                cella["intero_originale_spark"][f"{nome}/grezzo"] = _wce_ab(*_AB(P, Y, M, w))
                for cal in CALIBRAZIONI:
                    if f"{nome}/{cal}" in par:
                        Pv = _applica(lp, np.asarray(par[f"{nome}/{cal}"]["theta"], dtype="float64"), cal.split("_")[0])
                        cella["intero_originale_spark"][f"{nome}/{cal}"] = _wce_ab(*_AB(Pv, Y, M, w))
            cella["scarto_sostituzione_max"] = max(abs(cella["intero"][k] - cella["intero_originale_spark"][k]) for k in cella["intero"])
            R["impronte_ingressi"][f"predizioni_e16_spark_sostituite/{fp.name}"] = imp(f_orig)
        R["per_cella"][chiave] = cella
        R["impronte_ingressi"][f"predizioni_e16/{fp.name}"] = imp(fp)
        per_gr.setdefault(gr, []).append(cella)
    if fuori:
        raise RuntimeError(f"controllo contro gli aggregati congelati della campagna: {len(fuori)} celle oltre {TOLL_CAMP:g}:\n    " + "\n    ".join(fuori))
    for gr, celle in per_gr.items():
        G = {"celle": len(celle), "wce_intero": {}, "wce_sett": {}}
        for fin, dest in (("intero", "wce_intero"), ("sett", "wce_sett")):
            chiavi = sorted(set().union(*(set(cl[fin]) for cl in celle)))
            for k in chiavi:
                vals = [cl[fin][k] for cl in celle if k in cl[fin]]
                G[dest][k] = {"media": float(np.mean(vals)), "celle": len(vals)}
        # controlli: (i) e16_risultati → wce[k].media; (iii) E18 parte C → wce_settimana[k].media
        g16 = E16["gruppi"][gr]["wce"]; g18 = E18["C"]["gruppi"].get(gr, {}).get("wce_settimana", {})
        # media di confronto con E16: con gli originali della Spark per le celle sostituite
        med16 = {k: float(np.mean([cl.get("intero_originale_spark", cl["intero"])[k] for cl in celle if k in cl["intero"]])) for k in G["wce_intero"]}
        sc16 = max((abs(med16[k] - g16[k]["media"]) for k in med16 if k in g16), default=0.0)
        n16 = sum(1 for k in med16 if k in g16)
        sost = [cl for cl in celle if "intero_originale_spark" in cl]
        G["celle_sostituite"] = {"n": len(sost), "scarto_max_per_cella": max((cl["scarto_sostituzione_max"] for cl in sost), default=0.0),
                                 "scarto_max_media_gruppo": max((abs(G["wce_intero"][k]["media"] - med16[k]) for k in med16), default=0.0)}
        sc18 = max((abs(G["wce_sett"][k]["media"] - g18[k]["media"]) for k in G["wce_sett"] if k in g18), default=0.0)
        n18 = sum(1 for k in G["wce_sett"] if k in g18)
        sc_c = max(cl["controllo_campagna"][n]["scarto_relativo"] for cl in celle for n in cl["controllo_campagna"])
        n_c = sum(len(cl["controllo_campagna"]) for cl in celle)
        R["controlli"][gr] = {"e16_wce": {"confronti": n16, "scarto_max": sc16, "celle_sostituite": len(sost)},
                              "e18_C_wce_settimana": {"confronti": n18, "scarto_max": sc18},
                              "campagna": {"confronti": n_c, "scarto_relativo_max": sc_c}}
        if sc16 > TOLL_W16 or sc18 > TOLL_W16:
            raise RuntimeError(f"{gr}: scarto contro e16_risultati {sc16:.2e} o contro E18 parte C {sc18:.2e} oltre {TOLL_W16:g}")
        R["gruppi"][gr] = G
        print(f"  {gr:10s} {len(celle)} celle ({len(sost)} sostituite, scarto max sulla media {G['celle_sostituite']['scarto_max_media_gruppo']:.1e}): "
              f"e16 wce {n16} valori, scarto max {sc16:.1e}; E18-C {n18} valori, scarto max {sc18:.1e}; "
              f"campagna {n_c} celle×bracci, scarto relativo max {sc_c:.1e}; C grezzo {G['wce_intero']['C/grezzo']['media']:.4f}, "
              f"F'(1 sett.) grezzo > 1 sett. {G['wce_sett'].get('Fp_672/grezzo', {}).get('media', float('nan')):.4f}", flush=True)
    R["istante"] = datetime.now(timezone.utc).isoformat()
    return R


def main() -> int:
    ap = argparse.ArgumentParser(description="E18-ter — livelli assoluti alle soglie operative (sola analisi)")
    ap.add_argument("--parte", required=True, choices=("livelli", "wce16", "tutte"))
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--repliche", type=int, default=B_BOOT)
    a = ap.parse_args()
    f = a.out / "e18ter_risultati.json"
    R = json.loads(f.read_text()) if f.exists() else {}
    for parte in (("livelli", "wce16") if a.parte == "tutte" else (a.parte,)):
        print("=" * 84); print(f"E18-ter — parte {parte}"); print("=" * 84)
        if parte == "livelli":
            R["livelli"] = parte_livelli(a.out, a.repliche)
        else:
            R["wce16"] = parte_wce16(a.out)
    R["istante"] = datetime.now(timezone.utc).isoformat()
    tmp = f.with_name(f.name + ".tmp"); tmp.write_text(json.dumps(R, indent=1, ensure_ascii=False)); tmp.replace(f)
    print(f"  -> {f} (impronta {imp(f)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
