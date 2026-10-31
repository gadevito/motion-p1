#!/usr/bin/env python3
"""
CONGELAMENTO_E18.md — analisi di verifica dalla seconda revisione esterna (protocol/E18.md).
=============================================================================================
Ogni numero viene da `results/evoluzione/e18_risultati.json` (parti A, B, C, D di `analizza_e18.py`) e
dai file congelati che esso cita (valori a 19 soglie di `e8bis_risultati.json` come termine sostituito).
Scrive `CONGELAMENTO_E18.md` e `results/evoluzione/congelamento_e18.json`.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e18.py
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("results/evoluzione")
CITTA = ("Madrid", "Londra", "Melbourne")
GRUPPI_A = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")
CAL = ("grezzo", "T_nll", "T_wce", "V_nll", "V_wce")
CAL_IT = {"grezzo": "grezzo", "T_nll": "T (log-loss)", "T_wce": "T (wCE)", "V_nll": "V (log-loss)", "V_wce": "V (wCE)"}
SEGNO = {"-": "sotto zero", "+": "sopra zero", "0": "include lo zero"}
LIVELLI = ("0.005", "0.01", "0.02", "0.05", "0.1")


def imp(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def ic(r, k="ic_con_nodi", dec=4):
    return f"{r['media']:+.{dec}f} [{r[k][0]:+.{dec}f}, {r[k][1]:+.{dec}f}]"


def ic2(media, iv, dec=4):
    return f"{media:+.{dec}f} [{iv[0]:+.{dec}f}, {iv[1]:+.{dec}f}]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    fj = a.out / "e18_risultati.json"
    R = json.loads(fj.read_text())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    parti = [p for p in ("C", "A", "B", "D") if p in R]
    L = ["# CONGELAMENTO E18 — analisi di verifica dalla seconda revisione esterna", "",
         f"Generato da `genera_congelamento_e18.py` al commit `{commit}`, {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
         f"Protocollo `protocol/E18.md` (impronta `{imp(Path('protocol/E18.md'))}`; firma 28/10/2026, commit 964e4f5), letto per intero "
         f"prima del codice; `e18_risultati.json` impronta `{imp(fj)}`. Nessun addestramento: sola analisi da artefatti congelati. "
         f"Parti presenti: {', '.join(parti)}. Ordine di esecuzione: C → A → B → D.", "",
         "Rigenerato il 2026-10-29 (seconda versione; la prima, del 28/10, aveva impronta `b284661178a15d9c`): (i) la sostituzione "
         "delle affermazioni a 19 soglie e' la **voce 29** del registro delle correzioni, non la 28 scritta nel protocollo §1 r. 61 "
         "(la 28 era gia' stata assegnata ai nomi di ruolo nelle note sulle correzioni): deviazione dichiarata in §6; (ii) la parte C "
         "e' completata con le metriche di F16 (ECE per classe, log-loss, Brier) sulla stessa finestra, come il protocollo §3 richiede "
         "(«righe F′(1wk) di F16 ricalcolate»): la prima versione riportava la sola wCE. Nessun numero gia' congelato cambia.", ""]

    # ------------------------------------------------------------------ C --
    if "C" in R:
        C = R["C"]
        n_ctrl = len(C["controllo"]); sc_max = max(max(v["scarto_relativo_max"].values()) for v in C["controllo"].values())
        L += ["## 1. Parte C — E16: finestra di F′(1 sett.) (correzione 27)", "",
              f"{C['definizione']}. Finestra: origini con eta' > {C['finestra_passi']} passi. {C['repliche']} ricampionamenti "
              f"congiunti (schema di E16), seme {C['seme_bootstrap']}.", "",
              f"**Controllo bloccante**: per ciascuna delle {n_ctrl} celle di prova, la wCE grezza per orizzonte di F′(1 sett.) e di C "
              f"sulla finestra, ricalcolata dalle probabilita' di E16, contro l'aggregato congelato della campagna (fascia eta' > 1 "
              f"settimana di `predizioni_e4` per le citta', di `predizioni_e6` per PEMS08), nodi e origini identici: scarto relativo "
              f"massimo **{sc_max:.2e}** (soglia {C['tolleranza_controllo']:g}): superato.", "",
              "| contesto | calibrazione | wCE F′(1 sett.), > 1 sett. | wCE C, > 1 sett. | F′(1 sett.) − C, > 1 sett. [IC 95 %] | categoria | F′(1 sett.) − C, intero periodo (E16, non causale per la prima settimana) |",
              "|---|---|---|---|---|---|---|"]
        for gr in GRUPPI_A[:4]:
            if gr not in C["gruppi"]:
                continue
            G = C["gruppi"][gr]; rif = C["riferimento_intero_periodo"][gr]
            for i, var in enumerate(CAL):
                d = G["differenze_settimana"][f"Fp_672-C/{var}"]; wf = G["wce_settimana"][f"Fp_672/{var}"]; wc = G["wce_settimana"][f"C/{var}"]
                r16 = rif["differenze"].get(f"Fp_672-C/{var}")
                L.append(f"| {gr if i == 0 else ''} | {CAL_IT[var]} | {wf['media']:.4f} | {wc['media']:.4f} | {ic(d)} | {d['categoria']} | "
                         f"{ic(r16) if r16 else '—'} |")
        L += ["", "**Metriche di F16 sulla finestra > 1 settimana** (medie sulle celle, come `medie_test` di E16; ECE per classe a "
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
        L += ["", "Le righe F′(1 sett.) di F15 (differenze) e di F16 (metriche per braccio) vanno sostituite con questi valori; in F16 si "
              "aggiunge la riga «C, origini > 1 settimana» per ogni calibrazione (colonna «wCE C, > 1 sett.»). I parametri di temperature "
              "e vector scaling sono quelli di E16 (stimati sulla validazione): cambia solo la finestra di valutazione.", ""]

    # ------------------------------------------------------------------ A --
    if "A" in R:
        A = R["A"]
        f_t = Path("protocol/e18/tempi_parte_A.json")
        if not f_t.exists():
            raise SystemExit("FERMO: manca protocol/e18/tempi_parte_A.json (registro dei tempi della parte A)")
        RT = json.loads(f_t.read_text()); T = RT["tempi"]
        e8 = a.out / "e8bis_risultati.json"
        E8 = json.loads(e8.read_text())["gruppi"] if e8.exists() else {}
        L += ["## 2. Parte A — ROC empirica, AUC, pAUC(0–10 %), richiamo a falsi allarmi fissi", "",
              f"{A['definizione']}. Finestre: {A['finestre']['intero']}; {A['finestre']['sett']}. Intervalli: {A['repliche']} "
              f"ricampionamenti congiunti (partizioni × semi × posizioni dei sensori) con pesi di molteplicita' sui sensori, "
              f"ordinamento una volta per cella e braccio; stessi indici per i due bracci di una differenza; seme {A['seme_bootstrap']} + indice del gruppo.", "",
              f"PEMS04 (A.6): ricostruzione tipo E16 in `{A['pems04']['cartella']}/` (36 celle di prova, 3 controlli per cella); "
              f"bracci C, F₀′, F′(1 sett.): A1, A2, A4 not defined (no E, no A); A3 and F₀′ − C only.", "",
              "| gruppo | celle | sensori | parete (min) | ore-macchina | s per cella (mediana) | verifica sklearn: scarto AUC / richiami | punteggi | soglie distinte |",
              "|---|---|---|---|---|---|---|---|---|"]
        for gr in GRUPPI_A:
            if gr not in T:
                continue
            v = A["verifica_sklearn"].get(gr, {}); G = A["gruppi"][gr]
            L.append(f"| {gr} | {G['celle']} | {G['sensori']} | {T[gr]['parete_s']/60:.1f} | {T[gr]['macchina_s']/3600:.2f} | "
                     f"{T[gr]['per_cella_s']['mediana']:.0f} | {v.get('scarto_auc', float('nan')):.1e} / {v.get('scarto_richiami_max', float('nan')):.1e} | "
                     f"{v.get('punti', '—')} | {v.get('soglie_distinte', '—')} |")
        tot_m = sum(T[g]["macchina_s"] for g in T) / 3600
        L += ["", f"Totale: {tot_m:.1f} ore-macchina; sotto le 6 h per citta' del protocollo, quindi 4.000 repliche ovunque. "
              f"Tempi dal registro `protocol/e18/tempi_parte_A.json` (prima esecuzione, {RT['data']}, impronta `{imp(f_t)}`), "
              f"come per E15: i tempi dell'esecuzione corrente sono in `e18_risultati.json` → `A/tempi` e non entrano in questo documento.", "",
              "### 2a. AUC e pAUC per braccio (media sulle celle [IC 95 %])", "",
              "| gruppo | braccio / finestra | AUC | pAUC (0–10 %) | AUC a 19 soglie (E8-bis, sostituita) |", "|---|---|---|---|---|"]
        for gr in GRUPPI_A:
            if gr not in A["gruppi"]:
                continue
            G = A["gruppi"][gr]
            for k in sorted(G["metriche"]):
                n, fin = k.split("/"); m = G["metriche"][k]
                e8k = f"{n}/{'eta7' if fin == 'sett' else 'intero'}"
                v19 = E8.get(gr, {}).get("auc", {}).get(e8k)
                L.append(f"| {gr} | {n} / {'> 1 sett.' if fin == 'sett' else 'intero'} | {ic2(m['auc']['media'], m['auc']['ic_con_nodi'])} | "
                         f"{ic2(m['pauc']['media'], m['pauc']['ic_con_nodi'])} | {('%.4f' % v19) if isinstance(v19, (int, float)) else '—'} |")
        L += ["", "### 2b. Confronti (differenze, stessi indici): ΔAUC, ΔpAUC e Δrichiamo ai livelli di falsi allarmi", "",
              "| gruppo | confronto | finestra | ΔAUC [IC] | ΔpAUC [IC] | " + " | ".join(f"Δrichiamo FA {float(l)*100:g} %" for l in LIVELLI) + " |",
              "|---|---|---|---|---|" + "---|" * len(LIVELLI)]
        for gr in GRUPPI_A:
            if gr not in A["gruppi"]:
                continue
            for nome, d in A["gruppi"][gr]["confronti"].items():
                L.append(f"| {gr} | {nome} | {'> 1 sett.' if d['finestra'] == 'sett' else 'intero'} | {ic2(d['auc']['media'], d['auc']['ic_con_nodi'])} {d['auc']['segno']} | "
                         f"{ic2(d['pauc']['media'], d['pauc']['ic_con_nodi'])} {d['pauc']['segno']} | "
                         + " | ".join(f"{100*d[f'richiamo_fa_{l}']['media']:+.1f} [{100*d[f'richiamo_fa_{l}']['ic_con_nodi'][0]:+.1f}, {100*d[f'richiamo_fa_{l}']['ic_con_nodi'][1]:+.1f}] {d[f'richiamo_fa_{l}']['segno']}" for l in LIVELLI) + " |")
        # affermazioni A1-A5
        L += ["", "### 2c. Affermazioni ri-valutate (sostituiscono quelle a 19 soglie; voce 29 del registro — il protocollo §1 r. 61 "
              "scriveva 28, vedi §6)", ""]

        def seg(gr, nome, met="auc"):
            return A["gruppi"].get(gr, {}).get("confronti", {}).get(nome, {}).get(met, {}).get("segno")
        a1 = {c: seg(c, "F0-C") for c in CITTA}; a1p = seg("PEMS08", "F0-C")
        L.append(f"- **A1** ΔAUC(F₀ − C) < 0 nelle tre citta': " + ", ".join(f"{c} {SEGNO.get(a1[c], '—')}" for c in CITTA)
                 + f" → **{'confermata' if all(a1[c] == '-' for c in CITTA) else 'NON confermata'}**; PEMS08: {SEGNO.get(a1p, '—')}.")
        a2 = {g: seg(g, "F0p-F0") for g in GRUPPI_A[:4]}
        L.append(f"- **A2** ΔAUC(F₀′ − F₀) > 0 nelle tre citta' e su PEMS08: " + ", ".join(f"{g} {SEGNO.get(a2[g], '—')}" for g in GRUPPI_A[:4])
                 + f" → citta' **{'confermata' if all(a2[c] == '+' for c in CITTA) else 'NON confermata'}**, PEMS08 **{'confermata' if a2.get('PEMS08') == '+' else 'NON confermata'}**.")
        a3 = {}
        for g in GRUPPI_A:
            d = A["gruppi"].get(g, {}).get("confronti", {}).get("Fp_672-C")
            if d:
                a3[g] = [d[f"richiamo_fa_{l}"]["segno"] for l in LIVELLI]
        L.append("- **A3** F′(1 sett.) sopra C in richiamo ai cinque livelli di FA (origini > 1 settimana), segni per livello 0,5/1/2/5/10 %: "
                 + "; ".join(f"{g} {''.join(s)}" for g, s in a3.items())
                 + f" → sopra zero a tutti e cinque i livelli in {sum(all(x == '+' for x in s) for s in a3.values())}/{len(a3)} contesti; per livello: "
                 + ", ".join(f"{float(l)*100:g} %: {sum(s[i] == '+' for s in a3.values())}/{len(a3)}" for i, l in enumerate(LIVELLI)) + ".")
        L += ["- **A4** richiamo perso da F₀ sotto argmax e quota recuperata a FA 5 %:", "",
              "| gruppo | richiamo argmax C | richiamo argmax F₀ | perdita sotto argmax (punti) [IC] | perdita a FA 5 % (punti) [IC] | quota recuperata [IC] | testo attuale |",
              "|---|---|---|---|---|---|---|"]
        testo = {"Madrid": "92 %", "Londra": "81 %", "Melbourne": "80 %"}
        for g in GRUPPI_A:
            G = A["gruppi"].get(g, {})
            if not G.get("recupero_argmax"):
                continue
            r = G["recupero_argmax"]; am = G["argmax"]
            q = r["quota_recuperata"]
            L.append(f"| {g} | {100*am['C']['richiamo']:.1f} | {100*am['F0']['richiamo']:.1f} | {ic2(r['perdita_argmax_punti']['media'], r['perdita_argmax_punti']['ic_con_nodi'], 1)} | "
                     f"{ic2(r['perdita_fa5_punti']['media'], r['perdita_fa5_punti']['ic_con_nodi'], 1)} | "
                     f"{('%.3f' % q['media']) if q['media'] is not None else '—'} [{q['ic_con_nodi'][0]:.3f}, {q['ic_con_nodi'][1]:.3f}]"
                     f"{' (repliche con perdita argmax ≤ 0: %d)' % q['repliche_perdita_argmax_non_positiva'] if q['repliche_perdita_argmax_non_positiva'] else ''} | {testo.get(g, '—')} |")
        L += ["", "Le soglie scelte su validazione (−7,9 / −0,8 / −0,7 punti) restano dalla campagna originaria (E8) e il testo le separa da queste.",
              "- **A5** ΔpAUC(0–10 %): colonna «ΔpAUC» della tabella 2b, descrittiva.", ""]

    # ------------------------------------------------------------------ B --
    if "B" in R:
        Bq = R["B"]
        L += ["## 3. Parte B — bootstrap che conserva il sensore fisico", "",
              f"{Bq['definizione']}. {Bq['repliche']} repliche, seme {Bq['seme_bootstrap']}. Categorie: superiorita' (limite superiore < 0), "
              f"non inferiorita' (limite superiore < δ = {Bq['delta_non_inferiorita']}), inferiorita' (limite inferiore > 0), inconclusivo. "
              f"Gli intervalli attuali restano quelli pre-registrati e primari; quelli per sensore sono una sensibilita'.", ""]
        vm = Bq.get("verifica_mappa")
        if vm:
            L.append(f"Mappa posizione → ID fisico (`D[\"sid\"][nodi]`): verificata su {vm['contesto']} p{vm['partizione']} contro "
                     f"`_partizioni(SEME_PARTIZIONE[p])`: nodi uguali = {vm['nodi_uguali_a_partizioni']}; {vm['sid_distinti_nel_contesto']} ID distinti su {vm['K']} sensori del contesto.")
        L += ["", "| contesto | sensori distinti / occorrenze | differenza | media | IC attuale (congelato) | categoria | IC attuale ricalcolato (stesse estrazioni) | IC per sensore | categoria per sensore | esito |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for ctx, Cq in Bq["contesti"].items():
            for i, (n, d) in enumerate(Cq["differenze"].items()):
                att = f"{d['media_attuale']:+.4f} [{d['ic_attuale'][0]:+.4f}, {d['ic_attuale'][1]:+.4f}]" if "ic_attuale" in d else "—"
                cat_a = d.get("categoria_attuale", "—")
                esito = ("**cambia**" if "ic_attuale" in d and cat_a != d["categoria_per_sensore"] else "invariata") if "ic_attuale" in d else "—"
                L.append(f"| {ctx if i == 0 else ''} | {(str(Cq['sensori_distinti']) + ' / ' + str(Cq['occorrenze'])) if i == 0 else ''} | {n} | {d['media']:+.4f} | {att} | {cat_a} | "
                         f"[{d['ic_posizioni_ricalcolato'][0]:+.4f}, {d['ic_posizioni_ricalcolato'][1]:+.4f}] | [{d['ic_per_sensore'][0]:+.4f}, {d['ic_per_sensore'][1]:+.4f}] | "
                         f"{d['categoria_per_sensore']} | {esito} |")
        L += ["", f"**Cambi di categoria** (attuale → per sensore): {len(Bq['cambi_categoria'])}."]
        for cmb in Bq["cambi_categoria"]:
            L.append(f"- {cmb['contesto']}, {cmb['differenza']}: {cmb['da']} → {cmb['a']} (attuale [{cmb['ic_attuale'][0]:+.4f}, {cmb['ic_attuale'][1]:+.4f}], "
                     f"per sensore [{cmb['ic_per_sensore'][0]:+.4f}, {cmb['ic_per_sensore'][1]:+.4f}]).")
        # i tre casi nominati dal protocollo
        L += ["", "Casi nominati dal protocollo (se cambiano, la frase passa a «inconclusive under sensor-level resampling»):"]
        for ctx, n, et in (("Madrid/ep3", "(b) gated-F0p", "non inferiorita' di gated(τ,N) − F₀′, Madrid ep. 3"),
                           ("Melbourne/ep2", "(b) gated-F0p", "non inferiorita' di gated(τ,N) − F₀′, Melbourne ep. 2"),
                           ("PEMS08", "E17 gated(1sett,0)-F0p", "superiorita' di gated(1 sett., 0) − F₀′, PEMS08")):
            d = Bq["contesti"].get(ctx, {}).get("differenze", {}).get(n)
            if d:
                L.append(f"- {et}: attuale {d.get('categoria_attuale', '—')} → per sensore {d['categoria_per_sensore']} "
                         f"([{d['ic_per_sensore'][0]:+.4f}, {d['ic_per_sensore'][1]:+.4f}]).")
        L += ["", "Margini minimi di equivalenza (R-orig(1 sett.) ≡ F′(1 sett.)), max(|lo|, |hi|) dell'intervallo al 95 %:", "",
              "| contesto | attuale (E17) | per sensore |", "|---|---|---|"]
        for ctx, n in (("E3-bis Madrid", "Rorig_672-Fp_672 >1sett"), ("E3-bis Londra", "Rorig_672-Fp_672 >1sett"),
                       ("E3-bis Melbourne", "Rorig_672-Fp_672 >1sett"), ("PEMS08", "E17 Rorig_672-Fp_672 >1sett")):
            d = Bq["contesti"].get(ctx, {}).get("differenze", {}).get(n)
            if d and "margine_minimo_per_sensore" in d:
                ma = d.get("margine_minimo_attuale")
                L.append(f"| {ctx} | {('%.4f' % ma) if isinstance(ma, (int, float)) else '—'} | {d['margine_minimo_per_sensore']:.4f} |")
        L.append("")

    # ------------------------------------------------------------------ D --
    if "D" in R:
        Dq = R["D"]; pf = Dq["prima_formulazione"]
        lim = Dq.get("limite_storia", {})
        L += ["## 4. Parte D — provenienza della politica gated(1 sett., 0) (documentaria)", "",
              f"{Dq['definizione']}.", "",
              "Nota del 29/10/2026 (richiesta del revisore): la ricerca storica (`git log -S` delle stringhe della politica, "
              "`git log --diff-filter=A` dei file CONGELAMENTO_*) e' limitata ai commit raggiungibili dalla firma del protocollo E18 "
              "(28/10/2026): " + "; ".join(f"{k} `{v['commit']}` ({v['data']})" for k, v in lim.items() if isinstance(v, dict))
              + ". Motivo: la ricostruzione e' storica e non deve dipendere dalle modifiche successive al protocollo e al manoscritto. "
              "Esito invariato rispetto alla versione del 28/10.", "",
              f"Prima formulazione scritta della politica: **{pf['data']}** — "
              + "; ".join(f"{k}: {v['data']} ({v['commit']})" for k, v in list(pf["dettaglio"]["protocollo"].items()) + list(pf["dettaglio"]["manoscritto"].items())) + ".", "",
              "| contesto | campagna | gated(1 sett., 0) − F₀′ [IC attuale] | categoria | IC per sensore | categoria | gated(1 sett., 0) − gated(τ,N) [IC attuale] | categoria | prima osservazione dei risultati (file, commit) | osservato prima della formulazione |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for k, d in Dq["contesti"].items():
            g0, gg = d["gated0-F0p"], d["gated0-gated"]; o = d.get("osservato") or {}
            L.append(f"| {k} | {d['campagna']} | {ic2(g0['media'], g0['ic_attuale'])} | {g0['categoria_attuale']} | "
                     f"{('[%+.4f, %+.4f]' % tuple(g0['ic_per_sensore'])) if 'ic_per_sensore' in g0 else '—'} | {g0.get('categoria_per_sensore', '—')} | "
                     f"{ic2(gg['media'], gg['ic_attuale'])} | {gg['categoria_attuale']} | {o.get('data', '—')} ({o.get('file', '—')}, {o.get('commit', '—')}) | "
                     f"{'sì' if d['osservato_prima_della_formulazione'] else 'no'} |")
        L += ["", f"Esito: {Dq['esito']['osservati_prima_della_formulazione']} contesti su {Dq['esito']['contesti']} osservati prima della prima "
              f"formulazione scritta ({pf['data']}); atteso: {Dq['esito']['atteso']}. **{Dq['esito'].get('verdetto', '')}**. Il paper riporta la "
              f"politica come valutazione post hoc descrittiva sugli undici contesti, senza «not used to formulate it» e senza conferma prospettica.", ""]

    # ------------------------------------------------------------- 5, 6, 7 --
    L += ["## 5. TOST (punto 6) — nessun calcolo", "",
          "I margini minimi usano gli estremi dell'intervallo al 95 % (`analizza_e17.py` r. 72 e 167): equivalgono a un TOST a α = 0,025 "
          "per lato, piu' conservativo del convenzionale (α = 0,05, 90 %). Si dichiara cosi' nel testo; non si cambia percentile. "
          "δ = 0,005 e' stato fissato in E17 quando i limiti superiori ≈ 0,003 e 0,004 erano noti: le due non inferiorita' sono analisi "
          "secondaria post hoc e non entrano nella sintesi confirmatory (superiorita' in 8 contesti su 11).", "",
          "## 6. Deviazioni (con data e motivo)", "",
          "- 28/10/2026, parte C: due celle di `predizioni_e16` (prova Madrid p1 s203, Melbourne p2 s212) avevano, sulla finestra > 1 "
          "settimana, scarto relativo 1,36e-6 e 1,56e-6 rispetto all'aggregato congelato (soglia 1e-6): rumore fra macchine (voce 22; le "
          "probabilita' erano state ricostruite sulla Spark, gli aggregati sul Mac). Rimedio gia' usato in E16: le due celle sono state "
          "ricostruite sul Mac con `esegui_e16.py --solo` (controllo interno di E16 a 1,1e-14 e 9,6e-16) e copiate sulla Spark; gli "
          "originali sono in `predizioni_e16_spark_sostituite/`. Tolleranza invariata.",
          "- 28/10/2026, A.6: PEMS04 ha solo C, F₀′ e F′(1 sett.) (nessun E ne' A): A1, A2, A4 not defined (no E, no A); A3 and F₀′ − C only "
          "— come da A.6, non e' una deviazione. La validazione di PEMS04 non viene ricostruita (non serve ad A).",
          "- 29/10/2026, parte B: per i contesti di PEMS04 i confronti con A ed R-orig non esistono (nessun A, nessun R-orig in E6-bis parte A); "
          "per le citta' R-orig(1 sett.) − F′(1 sett.) usa `predizioni_fase3_672` (R-orig per nodo sulle origini comuni) e la fascia > 1 "
          "settimana di `predizioni_e4`, come E3-bis.",
          "- 29/10/2026, numerazione: il protocollo §1 r. 61 assegnava alla sostituzione delle affermazioni a 19 soglie (ROC empirica) "
          "la voce 28 del registro delle correzioni; la voce 28 era gia' stata assegnata il 29/10 ai nomi di ruolo nelle note sulle "
          "correzioni, quindi la sostituzione e' la voce 29. Il protocollo non si modifica (firmato); §2c e il registro portano 29.",
          "- 29/10/2026, parte C: la prima versione del congelamento (28/10, `b284661178a15d9c`) riportava per la finestra > 1 settimana "
          "la sola wCE; il protocollo §3 richiede le righe F′(1wk) di F16 intere (ECE per classe, log-loss, Brier, wCE). Completate "
          "qui dalle stesse probabilita' e con gli stessi parametri di calibrazione (`analizza_e18.py --parte C` rieseguito; le parti "
          "A, B, D non sono state rieseguite e i loro numeri sono invariati).",
          "- 29/10/2026, tempi: il giro `--solo E18` sulla Spark coincideva su tutti i numeri ma non sul documento, che stampava i "
          "tempi misurati della parte A (diversi a ogni esecuzione). Come per E15, i tempi della prima esecuzione (28/10) sono "
          "copiati nel registro `protocol/e18/tempi_parte_A.json` e il documento li legge da li'; `main.py` tratta `A/tempi` del "
          "json come metadati.",
          "- 29/10/2026, parte D: ricerca storica limitata ai commit fino alla firma del protocollo (OR3 `964e4f5`, = `923c02e` "
          "dopo la riscrittura della storia del 31/10/2026, voce 30; manoscritto "
          "`ae12921` = `manoscritto-20261028j`), su richiesta del revisore; il protocollo §4 non fissava un limite. Stesso esito "
          "(prima formulazione 2026-10-22, 11 contesti su 11 osservati prima); `analizza_e18.py --parte D` rieseguito, parti A, B, C "
          "invariate.", ""]
    ingr = {}
    for p in parti:
        ii = R[p].get("impronte_ingressi", {})
        if isinstance(ii, dict):
            ingr[p] = {"file": len(ii), "impronta_insieme": hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(ii.items())).encode()).hexdigest()[:16]}
    J = {"commit": commit, "istante": datetime.now(timezone.utc).isoformat(), "risultati": R,
         "impronte": {"e18_risultati.json": imp(fj), "protocol/E18.md": imp(Path("protocol/E18.md")), "ingressi_per_parte": ingr}}
    (a.out / "congelamento_e18.json").write_text(json.dumps(J, indent=1, ensure_ascii=False))
    L += ["## 7. Impronte", "",
          f"- `results/evoluzione/e18_risultati.json` `{imp(fj)}`; `protocol/E18.md` `{imp(Path('protocol/E18.md'))}`; "
          f"`results/evoluzione/congelamento_e18.json` `{imp(a.out / 'congelamento_e18.json')}`.",
          "- Ingressi per parte (impronte dei file elencate in `e18_risultati.json` → `impronte_ingressi`): "
          + "; ".join(f"{p}: {v['file']} file, insieme `{v['impronta_insieme']}`" for p, v in ingr.items()) + ".",
          f"- `evoluzione/analisi/analizza_e18.py` `{imp(Path('evoluzione/analisi/analizza_e18.py'))}`."]
    Path("CONGELAMENTO_E18.md").write_text("\n".join(L) + "\n")
    print(f"  CONGELAMENTO_E18.md (impronta {imp(Path('CONGELAMENTO_E18.md'))}); json {imp(a.out / 'congelamento_e18.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
