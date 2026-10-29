#!/usr/bin/env python3
"""
E18-bis, passo 1 (codice): sostituzioni letterali in `evoluzione/analisi/analizza_e18.py` e in
`genera_congelamento_e18.py`. Si ferma se un testo atteso non compare esattamente una volta.

1. Parte C: oltre alla wCE (bootstrap), le metriche di F16 sulla stessa finestra (origini con eta' > 1 settimana),
   dalle stesse probabilita' e con gli stessi parametri di calibrazione: ECE per classe (10 intervalli), log-loss
   non pesata, Brier multiclasse, wCE; per cella (`per_cella_settimana`) e in media per gruppo (`medie_settimana`,
   stessa struttura di `medie_test` di E16). Nessun altro numero cambia.
2. Generatore: «voce 28» → «voce 29» (il protocollo §1 r. 61 diceva 28; la 28 e' dei nomi di ruolo), nota datata
   in testa, tabella delle metriche di F16 in §1, due righe in §6 (deviazioni con data e motivo).

Dalla radice OR3/ (ramo esecutore/e18-bis):  python3 e18bis_codice.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
AN = R / "evoluzione" / "analisi" / "analizza_e18.py"
GEN = R / "genera_congelamento_e18.py"

SOST = {AN: [
    ('''    CALIBRAZIONI, _AB, _applica, _boot_vec, _log_p, _wce_ab)''',
     '''    CALIBRAZIONI, _AB, _applica, _boot_vec, _log_p, _metriche, _wce_ab)'''),
    ('''    """Correzione 27: F'(1 sett.) e C di E16 sulle origini con eta' > 1 settimana."""''',
     '''    """Correzione 27: F'(1 sett.) e C di E16 sulle origini con eta' > 1 settimana.

    Oltre alla wCE con ricampionamento (F15), le metriche di F16 sulla stessa finestra: ECE per classe, log-loss
    non pesata, Brier multiclasse, wCE, per cella e in media per gruppo (`medie_settimana`, come `medie_test` di E16).
    """'''),
    ('''        cella = {"K": int(len(z["nodi"])), "A": {}, "B": {}, "wce": {}}
        for nome in ("C", "Fp_672"):
            P = z[f"prob_{nome}"][sel].astype("float64"); lp = _log_p(P)
            cella["A"][f"{nome}/grezzo"], cella["B"][f"{nome}/grezzo"] = _AB(P, Y, M, w)
            for cal in CALIBRAZIONI:
                tipo = cal.split("_")[0]
                theta = np.asarray(par[f"{nome}/{cal}"]["theta"], dtype="float64")
                Pc = _applica(lp, theta, tipo)
                cella["A"][f"{nome}/{cal}"], cella["B"][f"{nome}/{cal}"] = _AB(Pc, Y, M, w)''',
     '''        cella = {"K": int(len(z["nodi"])), "A": {}, "B": {}, "wce": {}, "metriche": {}, "contesto": c}

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
                cella["metriche"][f"{nome}/{cal}"] = _met(Pc)'''),
    ('''    R = {"definizione": "finestra: origini con eta' > 1 settimana per F'(1 sett.) E per C; parametri di calibrazione "
                        "di e16_risultati.json (stimati sulla validazione della stessa cella), invariati",''',
     '''    R = {"definizione": "finestra: origini con eta' > 1 settimana per F'(1 sett.) E per C; parametri di calibrazione "
                        "di e16_risultati.json (stimati sulla validazione della stessa cella), invariati; metriche di F16 "
                        "(ECE per classe a 10 intervalli, log-loss non pesata, Brier multiclasse, wCE) per cella sulla stessa "
                        "finestra e in media sulle celle, come `medie_test` di E16",'''),
    ('''         "controllo": controllo, "gruppi": {}, "riferimento_intero_periodo": {}, "impronte_ingressi": {''',
     '''         "controllo": controllo, "gruppi": {}, "riferimento_intero_periodo": {},
         "per_cella_settimana": {f"{k[0]}/{v['contesto']}/p{k[1]}/s{k[2]}": v["metriche"] for cc in celle_gr.values()
                                 for k, v in cc.items()},
         "impronte_ingressi": {'''),
    ('''        R["gruppi"][gr] = G
        # il riferimento: i valori di E16 sull'intero periodo (F15: Fp_672-C; F16: wCE di Fp_672 e C)
        g16 = E16["gruppi"][gr]
        R["riferimento_intero_periodo"][gr] = {
            "differenze": {k: g16["differenze"][k] for k in g16["differenze"] if k.startswith("Fp_672-C/")},
            "wce": {k: g16["wce"][k] for k in chiavi if k in g16["wce"]}}''',
     '''        # medie sulle celle delle metriche di F16 sulla finestra (ECE per classe, log-loss, Brier, wCE)
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
            "medie_test": {k: g16["medie_test"][k] for k in chiavi if k in g16.get("medie_test", {})}}'''),
], GEN: [
    ('''         f"Parti presenti: {', '.join(parti)}. Ordine di esecuzione: C → A → B → D.", ""]''',
     '''         f"Parti presenti: {', '.join(parti)}. Ordine di esecuzione: C → A → B → D.", "",
         "Rigenerato il 2026-10-29 (seconda versione; la prima, del 28/10, aveva impronta `b284661178a15d9c`): (i) la sostituzione "
         "delle affermazioni a 19 soglie e' la **voce 29** del registro delle correzioni, non la 28 scritta nel protocollo §1 r. 61 "
         "(la 28 era gia' stata assegnata ai nomi di ruolo nelle note sulle correzioni): deviazione dichiarata in §6; (ii) la parte C "
         "e' completata con le metriche di F16 (ECE per classe, log-loss, Brier) sulla stessa finestra, come il protocollo §3 richiede "
         "(«righe F′(1wk) di F16 ricalcolate»): la prima versione riportava la sola wCE. Nessun numero gia' congelato cambia.", ""]'''),
    ('''        L += ["", "Le righe F′(1 sett.) di F15 (differenze) e di F16 (metriche per braccio) vanno sostituite con questi valori; in F16 si "''',
     '''        L += ["", "**Metriche di F16 sulla finestra > 1 settimana** (medie sulle celle, come `medie_test` di E16; ECE per classe a "
              "10 intervalli, log-loss non pesata, Brier multiclasse, wCE; stesse probabilita', stessi parametri di calibrazione). "
              "Aggiunte il 2026-10-29 (vedi §6).", "",
              "| contesto | braccio | calibrazione | ECE cl. 0 | ECE cl. 1 | ECE cl. 2 | log-loss | Brier | wCE | log-loss / Brier intero periodo (E16) |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for gr in GRUPPI_A[:4]:
            if gr not in C["gruppi"] or "medie_settimana" not in C["gruppi"][gr]:
                continue
            MS = C["gruppi"][gr]["medie_settimana"]; MT = C["riferimento_intero_periodo"][gr].get("medie_test", {})
            primo = True
            for br, et in (("Fp_672", "F′(1 sett.)"), ("C", "C")):
                for var in CAL:
                    m = MS[f"{br}/{var}"]; r16 = MT.get(f"{br}/{var}")
                    L.append(f"| {gr if primo else ''} | {et} | {CAL_IT[var]} | {m['ece']['0']:.4f} | {m['ece']['1']:.4f} | {m['ece']['2']:.4f} | "
                             f"{m['logloss']:.4f} | {m['brier']:.4f} | {m['wce']:.4f} | "
                             + (f"{r16['logloss']:.4f} / {r16['brier']:.4f}" if r16 else "—") + " |")
                    primo = False
        L += ["", "Le righe F′(1 sett.) di F15 (differenze) e di F16 (metriche per braccio) vanno sostituite con questi valori; in F16 si "'''),
    ('''        L += ["", "### 2c. Affermazioni ri-valutate (sostituiscono quelle a 19 soglie; voce 28 del registro)", ""]''',
     '''        L += ["", "### 2c. Affermazioni ri-valutate (sostituiscono quelle a 19 soglie; voce 29 del registro — il protocollo §1 r. 61 "
              "scriveva 28, vedi §6)", ""]'''),
    ('''          "settimana di `predizioni_e4`, come E3-bis.", ""]''',
     '''          "settimana di `predizioni_e4`, come E3-bis.",
          "- 29/10/2026, numerazione: il protocollo §1 r. 61 assegnava alla sostituzione delle affermazioni a 19 soglie (ROC empirica) "
          "la voce 28 del registro delle correzioni; la voce 28 era gia' stata assegnata il 29/10 ai nomi di ruolo nelle note sulle "
          "correzioni, quindi la sostituzione e' la voce 29. Il protocollo non si modifica (firmato); §2c e il registro portano 29.",
          "- 29/10/2026, parte C: la prima versione del congelamento (28/10, `b284661178a15d9c`) riportava per la finestra > 1 settimana "
          "la sola wCE; il protocollo §3 richiede le righe F′(1wk) di F16 intere (ECE per classe, log-loss, Brier, wCE). Completate "
          "qui dalle stesse probabilita' e con gli stessi parametri di calibrazione (`analizza_e18.py --parte C` rieseguito; le parti "
          "A, B, D non sono state rieseguite e i loro numeri sono invariati).", ""]'''),
]}


def main() -> int:
    for f, coppie in SOST.items():
        t = f.read_text()
        for vecchio, _ in coppie:
            n = t.count(vecchio)
            if n != 1:
                print(f"FERMO: in {f.relative_to(R)} il testo atteso compare {n} volte:\n{vecchio[:160]}"); return 1
    for f, coppie in SOST.items():
        t = f.read_text()
        for vecchio, nuovo in coppie:
            t = t.replace(vecchio, nuovo)
        f.write_text(t); print(f"  {f.relative_to(R)}: {len(coppie)} sostituzioni")
    import py_compile
    for f in SOST:
        py_compile.compile(str(f), doraise=True)
    print("  compilazione: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
