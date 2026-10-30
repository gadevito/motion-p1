#!/usr/bin/env python3
"""
CONGELAMENTO_E18TER.md e results/evoluzione/congelamento_e18ter.json da results/evoluzione/e18ter_risultati.json.
Ogni numero viene dal json; nessun valore scritto a mano. Dalla radice OR3/:  python3 genera_congelamento_e18ter.py
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("results/evoluzione")
GRUPPI = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")
BR_IT = {"C": "C", "A": "A", "F0": "F₀", "F0p": "F₀′", "Fp_672": "F′(1 sett.)", "Rorig_672": "R-orig(1 sett.)", "gated": "gated(τ,N)"}
REG_IT = {"prim": "F1-ottima", "par": "FA appaiati a C"}
FIN_IT = {"intero": "intera", "sett": "> 1 sett."}


def imp(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def ic(v, dec=3, scala=1.0):
    return f"{v['media'] * scala:.{dec}f} [{v['ic_con_nodi'][0] * scala:.{dec}f}, {v['ic_con_nodi'][1] * scala:.{dec}f}]"


CAL_IT = {"grezzo": "grezzo", "T_nll": "T (log-loss)", "T_wce": "T (wCE)", "V_nll": "V (log-loss)", "V_wce": "V (wCE)"}
BR16 = ("C", "A", "F0", "F0p", "Fp_672")


def _sezione_wce16(R):
    W = R.get("wce16")
    if not W:
        return []
    L = ["## 1-bis. Colonna wCE di F17 con la definizione del manoscritto (richiesta del 30/10, 09:45)", "",
         f"{W['definizione']}. Finestra > 1 settimana: origini con eta' > {W['finestra_passi']} passi.", "",
         "**Controlli bloccanti**: (i) media sulle celle contro `e16_risultati.json` → `wce` (stessa definizione per cella: "
         "le differenze di F16 restano invariate); (ii) livelli grezzi di C, F₀, F₀′, A per cella contro gli aggregati congelati "
         "della campagna (`predizioni_e4`, `predizioni_fase3`, `predizioni_e6`, `predizioni_e6bis`: quelli che il controllo di E8 "
         "riproduce), scarto relativo; (iii) finestra > 1 settimana contro E18 parte C `wce_settimana`. "
         + "; ".join(f"{g}: e16 {c['e16_wce']['confronti']} valori, scarto max {c['e16_wce']['scarto_max']:.1e}"
                     + (f" (con gli originali della Spark per {c['e16_wce']['celle_sostituite']} cella/e sostituita/e il 28/10; scarto della "
                        f"sostituzione sulla media del gruppo {W['gruppi'][g]['celle_sostituite']['scarto_max_media_gruppo']:.1e})"
                        if c['e16_wce'].get('celle_sostituite') else "") + "; campagna "
                     f"{c['campagna']['confronti']} celle×bracci, scarto relativo max {c['campagna']['scarto_relativo_max']:.1e}; "
                     f"E18-C {c['e18_C_wce_settimana']['confronti']} valori, scarto max {c['e18_C_wce_settimana']['scarto_max']:.1e}"
                     for g, c in W["controlli"].items())
         + f" (soglie {W['tolleranze']['e16']:g} assolute, {W['tolleranze']['campagna']:g} relativa): superati.", "",
         "| contesto | braccio | finestra | " + " | ".join(CAL_IT[c] for c in CAL_IT) + " |", "|---|---|---|---|---|---|---|---|"]
    for g, G in W["gruppi"].items():
        primo = True
        for b in BR16:
            if f"{b}/grezzo" not in G["wce_intero"]:
                continue
            L.append(f"| {g if primo else ''} | {BR_IT[b]} | intera | " + " | ".join(
                f"{G['wce_intero'][f'{b}/{c}']['media']:.4f}" if f"{b}/{c}" in G["wce_intero"] else "—" for c in CAL_IT) + " |"); primo = False
        for b in ("Fp_672", "C"):
            if f"{b}/grezzo" in G["wce_sett"]:
                L.append(f"|  | {BR_IT[b]} | > 1 sett. | " + " | ".join(
                    f"{G['wce_sett'][f'{b}/{c}']['media']:.4f}" if f"{b}/{c}" in G["wce_sett"] else "—" for c in CAL_IT) + " |")
    L += ["", "Nota del 30/10/2026: la colonna «wCE» di F17 (`medie_test` di E16, `_nll` pesata congiuntamente anche sugli orizzonti) "
          "e' sostituita da questi valori nel generatore di F17; i valori precedenti restano in `e16_risultati.json`. Nessuna differenza "
          "fra bracci cambia.", ""]
    return L


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    fj = a.out / "e18ter_risultati.json"
    R = json.loads(fj.read_text())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    prot = Path("protocol/E18ter.md")
    L = ["# CONGELAMENTO E18-TER — terza revisione esterna: livelli assoluti alle soglie operative", "",
         f"Generato da `genera_congelamento_e18ter.py` al commit `{commit}`, {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
         f"Protocollo `protocol/E18ter.md` (trascrizione datata della richiesta del revisore del 30/10/2026; impronta `{imp(prot)}`); "
         f"`e18ter_risultati.json` impronta `{imp(fj)}`. Nessun addestramento: sola analisi da artefatti congelati di E8.", ""]
    Lv = R["livelli"]
    L += ["## 1. Livelli assoluti alle soglie operative (punto 2.3)", "",
          f"{Lv['definizione']}.", "",
          f"Regole di decisione (E8, `e8_soglie.json`, impronta `{Lv['impronta_soglie']}`): prim = {Lv['regole']['prim']}; "
          f"par = {Lv['regole']['par']}. Classe predetta: congestionata se p(congestionata) ≥ soglia, altrimenti argmax fra le altre due. "
          f"Finestre: intera = {Lv['finestre']['intero']}; > 1 sett. = {Lv['finestre']['sett']}. Bracci sulla finestra intera: "
          f"{', '.join(BR_IT[b] for b in Lv['bracci']['intero'])}; sulla finestra > 1 settimana: {', '.join(BR_IT[b] for b in Lv['bracci']['sett'])}. "
          f"Intervalli: {Lv['repliche']} ricampionamenti congiunti (partizioni × semi × posizioni dei sensori, pesi di molteplicita'), "
          f"percentili 2,5/97,5, stessi indici per tutti i bracci di un contesto; seme di E8 del contesto.", "",
          "**Controllo bloccante** (aggregati sulla finestra intera contro `e8_risultati.json` → `livelli`): "
          + "; ".join(f"{g}: {c['confronti']} valori, scarto massimo {c['scarto_max']:.1e}" for g, c in Lv["controllo"].items())
          + f" (soglia {Lv['tolleranza_controllo']:g}): superato.", ""]
    for g in GRUPPI:
        G = Lv["gruppi"].get(g)
        if G is None:
            continue
        L += [f"### 1.{GRUPPI.index(g) + 1}. {g} — {G['celle']} celle, {G['sensori']} sensori per cella; gated(τ = {G['gated']['tau']}, N = {G['gated']['N']})", "",
              "| braccio | finestra | regola | soglia | richiamo, media sulle celle [IC 95 %] | falsi allarmi [IC] | precisione [IC] | F1 cong. [IC] | aggregato: richiamo / FA / precisione |",
              "|---|---|---|---|---|---|---|---|---|"]
        for fin in ("intero", "sett"):
            for r in ("prim", "par"):
                for b in Lv["bracci"][fin]:
                    v = G["livelli"].get(f"{fin}/{r}/{b}")
                    if v is None:
                        continue
                    sog = None if b == "gated" else G["soglie"].get(b, {}).get(r)
                    sog_t = "composta (F₀′, F′)" if b == "gated" else (f"{sog:.2f}" if isinstance(sog, (int, float)) else "—")
                    mc, ag = v["media_celle"], v["aggregato"]
                    L.append(f"| {BR_IT[b]} | {FIN_IT[fin]} | {REG_IT[r]} | {sog_t} | {ic(mc['richiamo'])} | {ic(mc['falsi_allarmi'], 4)} | "
                             f"{ic(mc['precisione'])} | {ic(mc['f1_congestionata'])} | {ag['richiamo']:.3f} / {ag['falsi_allarmi']:.4f} / {ag['precisione']:.3f} |")
        L.append("")
    L += ["Lettura: i livelli sulla finestra intera di C, A, F₀, F₀′ e gated(τ,N) riproducono esattamente i `livelli` di E8 (controllo); "
          "quelli di F′(1 sett.), R-orig(1 sett.) e della C di riferimento sono sulla finestra > 1 settimana, come i confronti "
          "«> 1 sett.» di E8 e di E18 parte C, e non erano in alcun congelamento (vedi §4). Le differenze fra bracci restano quelle "
          "congelate in E8/E17/E18: questa tabella ne da' i livelli, non ne cambia i confronti.", "",
          *_sezione_wce16(R),
          "## 2. Presentazione delle categorie (punto 2 e punto a)", "",
          "Cambio di presentazione, non di analisi (30/10/2026): nei generatori delle tabelle con categorie, le due scale sono "
          "riportate in colonne separate dagli stessi intervalli — segno rispetto a zero (favourable / unfavourable / inconclusive) e "
          "margine (entro δ = 0,005: si'/no). La didascalia della tabella delle metriche di calibrazione riporta l'ECE massimo osservato, "
          "calcolato dal generatore, al posto di «below 0.04». Nessun numero cambia.", "",
          "## 3. Formula della wCE e unita' della ROC (punto 3 e punto b)", "",
          "Dal codice (`esegui_e4.py` `_aggregati` r. 73–85 e `_wce` r. 256–260; `componente/valutazione.py` r. 90–112, 155–172; "
          "`esegui_e16.py` `_nll` r. 173–181, `_AB`/`_wce_ab` r. 242–254; `analizza_e18.py` `_cella_A` r. 239–246, `_metriche_roc` r. 198–218): "
          "per ogni orizzonte h, wCE_h = Σ w_y·(−log p_y) / Σ w_y sulle coppie (origine, sensore) valide — una sola somma pesata congiunta, "
          "non una media di medie per sensore; p tagliata a 1e-12; pesi w_y = N_train/(3·n_y,train) per contesto × partizione, stimati sui "
          "soli nodi e periodo di addestramento; wCE = media semplice sui quattro orizzonti (un orizzonte senza bersagli validi non "
          "contribuisce); differenza fra bracci per run (contesto, partizione, seme) e media sui run; intervallo dal ricampionamento "
          "congiunto di partizioni, semi e posizioni dei sensori (i sensori rientrano nelle somme, 4 000 repliche, percentili 2,5/97,5). "
          "Precisazione per F16: la colonna «wCE» dei livelli per braccio (`_metriche` → `_nll`) e' pesata congiuntamente anche sugli "
          "orizzonti e coincide con la wCE della campagna solo se i Σw per orizzonte sono uguali. ROC di E18: unita' = run; in ogni run "
          "i punteggi p(congestionata) di tutte le terne valide (origine, sensore, orizzonte) nella finestra sono riuniti in una sola ROC "
          "empirica; il ricampionamento pesa i sensori per molteplicita'; AUC, pAUC e richiami mediati sui run. Confermato.", "",
          "## 4. Deviazioni e note datate", "",
          "- 30/10/2026, finestra: i livelli di F′(1 sett.), R-orig(1 sett.) e della C di riferimento sulla finestra > 1 settimana non "
          "sono in alcun congelamento (E8 somma le tre fasce d'eta'); calcolati qui dalle matrici di confusione per fascia salvate in "
          "`predizioni_e8/` (stesse soglie, stessa politica, stesso ricampionamento). Dichiarato nel protocollo §1.",
          "- 30/10/2026, intervalli: i `livelli` di E8 sono aggregati senza intervallo; qui si aggiunge la media sulle celle con "
          "intervallo nello schema di E8 (sequenza del generatore casuale propria di questa analisi, seme di E8).", ""]
    ingr = dict(Lv["impronte_ingressi"]); ingr.update(R.get("wce16", {}).get("impronte_ingressi", {}))
    J = {"commit": commit, "istante": datetime.now(timezone.utc).isoformat(), "risultati": R,
         "impronte": {"e18ter_risultati.json": imp(fj), "protocol/E18ter.md": imp(prot),
                      "ingressi": {"file": len(ingr), "impronta_insieme": hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(ingr.items())).encode()).hexdigest()[:16]}}}
    (a.out / "congelamento_e18ter.json").write_text(json.dumps(J, indent=1, ensure_ascii=False))
    L += ["## 5. Impronte", "",
          f"- `results/evoluzione/e18ter_risultati.json` `{imp(fj)}`; `protocol/E18ter.md` `{imp(prot)}`; "
          f"`results/evoluzione/congelamento_e18ter.json` `{imp(a.out / 'congelamento_e18ter.json')}`.",
          f"- Ingressi: {len(ingr)} file (`e8_soglie.json`, `e8_risultati.json`, `predizioni_e8/prova_*.npz`; `e16_risultati.json`, "
          f"`e18_risultati.json`, `predizioni_e16/prova_*.npz`), insieme "
          f"`{J['impronte']['ingressi']['impronta_insieme']}`.",
          f"- `evoluzione/analisi/analizza_e18ter.py` `{imp(Path('evoluzione/analisi/analizza_e18ter.py'))}`."]
    Path("CONGELAMENTO_E18TER.md").write_text("\n".join(L) + "\n")
    print(f"  CONGELAMENTO_E18TER.md (impronta {imp(Path('CONGELAMENTO_E18TER.md'))}); json {imp(a.out / 'congelamento_e18ter.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
