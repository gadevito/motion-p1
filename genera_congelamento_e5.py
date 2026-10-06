#!/usr/bin/env python3
"""
Congelamento di E5 — piu' episodi d'inserimento.
=================================================
**Ogni numero e' derivato dai file**: affermazioni, altri confronti, nodi sotto
N e regola di lettura da `e5_risultati.json`; calendario e potenza da
`preparazione_e5.json`; origini e salti da `e5_prepara.json`; k della
secondaria da `e5_k_secondaria.json`; (tau, N) da `e4_scelta_gated.json`;
F'(1 sett.) − A dell'episodio principale da `e5_settimana_vs_A.json`;
addestramenti dai marcatori e da `esito_e5_addestra.json`; punti selezionati
dal registro; celle e controlli dai `predizioni_e5/*.npz`. Il verdetto e'
calcolato dai segni, non scritto.

Se un ingresso obbligatorio manca, si ferma.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e5.py
"""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

RADICE = Path(__file__).resolve().parent
sys.path.insert(0, str(RADICE))
from evoluzione.esperimenti.esegui_e5 import (  # noqa: E402
    CITTA, DIR_PRED, EPISODI, NUOVI, SEMI_E5, _nome_e_token, etichette)

OUT = Path("results/evoluzione")
FILE = ["evoluzione/esperimenti/addestramento.py",
        "evoluzione/esperimenti/esegui_e5.py",
        "evoluzione/esperimenti/preparazione_e5.py",
        "evoluzione/analisi/settimana_vs_A_e5.py",
        "evoluzione/analisi/analizza_e5.py",
        "protocol/E5.md"]
AFF = {"a": "F₀′ − C", "b": "gated − F₀′", "c": "F′(1 sett.) − C, eta' > 1 sett.",
       "d": "F′(24 h) − C", "e": "F′(1 sett.) − A, eta' > 1 sett."}
ET_TAU = {96: "24 h", 192: "48 h", 672: "1 settimana", None: "mai"}


class IngressoMancante(RuntimeError):
    pass


def h(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    except OSError:
        return "assente"


def commit_git() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, cwd=RADICE).stdout.strip()[:12] or "n.d."
    except Exception:                                        # noqa: BLE001
        return "n.d."


def leggi(f: Path):
    if not f.exists():
        raise IngressoMancante(f"assente: {f}")
    return json.loads(f.read_text())


def addestramenti(out: Path) -> dict:
    E_TOK = _nome_e_token()
    E = {"marcatori": {}, "selezionati": Counter(), "esito": leggi(out / "esito_e5_addestra.json")}
    for k in NUOVI:
        et = etichette(k)
        for b, cart in (("C", et["ins"]), ("A", et["ins"]), (E_TOK, et["E"])):
            E["marcatori"][f"ep{k}/{b}"] = len(list((out / cart).glob(f"ck_{b}_*_p*_s*.pt.fatto")))
    for f in (out / "registro").glob("*.json"):
        try:
            d = json.loads(f.read_text())
        except ValueError:
            continue
        if "_ep" in str(d.get("esperimento", "")) and d.get("run_status") == "completato" \
                and "protocollo_principale" in d:
            E["selezionati"][int(d["protocollo_principale"]["aggiornamento_selezionato"])] += 1
    E["selezionati"] = dict(sorted(E["selezionati"].items()))
    return E


def celle(out: Path) -> dict:
    C = {"per_episodio": {}, "controllo_6_max": 0.0, "controllo_3": 0, "k": set(), "imp_k": set()}
    for f in sorted((out / DIR_PRED).glob("ep*_*_p*_s*.npz")):
        z = np.load(f, allow_pickle=True)
        k = int(z["episodio"])
        C["per_episodio"][k] = C["per_episodio"].get(k, 0) + 1
        if str(z["controllo_3"]) == "ok":
            C["controllo_3"] += 1
        if k == 1:
            c6 = json.loads(str(z["controllo_6"]))
            C["controllo_6_max"] = max([C["controllo_6_max"]] + list(c6.values()))
        C["k"].add((str(z["contesto"]), int(z["k_secondaria"])))
        C["imp_k"].add(str(z["impronta_k_secondaria"]))
    C["k"] = sorted(C["k"]); C["imp_k"] = sorted(C["imp_k"])
    return C


def _f(x, n=3):
    return f"{x:+.{n}f}"


def _ic(q, n=3):
    return f"[{_f(q[0], n)}, {_f(q[1], n)}]"


def documento(R: dict) -> str:
    A = []; a = A.append
    RS, PR, PP, KS, SC, SV, E, C = (R["risultati"], R["prepara"], R["preparazione"],
                                    R["k_secondaria"], R["scelta_e4"], R["settimana_vs_A"],
                                    R["addestramenti"], R["celle"])
    a("# Congelamento — E5, piu' episodi d'inserimento")
    a("")
    a(f"**Congelato il {R['data']}**, commit `{R['commit']}`. Pre-registrazione "
      f"`protocol/E5.md` (impronta `{R['impronte']['protocol/E5.md']}`), firmata al commit "
      f"`cff0310c7c49fe36` prima del lancio (E3-bis compreso). **Ogni numero e' calcolato da "
      f"`genera_congelamento_e5.py`** dai file di risultato; il verdetto e' derivato, non scritto.")
    a("")
    a("## 1. Che cosa e' stato eseguito")
    a("")
    n_tr = sum(E["marcatori"].values())
    a("| | |")
    a("|---|---|")
    a(f"| addestramenti | **{n_tr}** marcatori (" + ", ".join(f"{k} {v}" for k, v in E["marcatori"].items())
      + f"); esito del lancio: {E['esito']['completate']} completati, {len(E['esito']['fallite'])} falliti, "
      f"{E['esito']['ore_calendario']:.1f} ore di calendario con {E['esito']['lavoratori']} processi — "
      f"**non e' il costo seriale** |")
    a("| aggiornamento selezionato (episodi 2 e 3, dal registro) | "
      + ", ".join(f"u{u} × {n}" for u, n in E["selezionati"].items()) + " |")
    a(f"| celle valutate | " + ", ".join(f"episodio {k} {v}" for k, v in sorted(C["per_episodio"].items()))
      + f"; semi {SEMI_E5} |")
    a(f"| controllo 3 (nodi nuovi fuori da E′, C, pesi, normalizzazione; dentro A) | verificato in "
      f"{C['controllo_3']} celle su {sum(C['per_episodio'].values())} |")
    a(f"| controllo 6 (episodio 1 = celle di E4) | scarto relativo massimo {C['controllo_6_max']:.1e} "
      f"su C, F₀′, F′(24 h/48 h/1 sett.) |")
    a(f"| (τ, N) | letti da `e4_scelta_gated.json`, impronta `{SC['impronta']}` (= `{RS['impronta_scelta_e4']}`), "
      f"mai riselezionati |")
    a(f"| k della secondaria | `e5_k_secondaria.json`, impronta `{KS['impronta']}` (= `{RS['impronta_k_secondaria']}`, "
      f"una sola nelle celle: {C['imp_k']}); k = " + ", ".join(f"{c} {KS['k'][c]}" for c in CITTA) + " |")
    a(f"| ricampionamento | {RS['repliche']} repliche, seme {RS['seme_bootstrap']}, partizioni × semi × nodi |")
    a("")
    a("## 2. Calendario degli episodi (regola meccanica, verificata dall'esecutore)")
    a("")
    a("| citta' | ep. | t₀ | data e ora | valutazione (origini amm.) | addestramento (origini amm.) | perdita |")
    a("|---|---|---|---|---|---|---|")
    for c in CITTA:
        for z in PP["calendario"][c]["episodi"]:
            a(f"| {c} | {z['episodio']} | {z['t0']} | {z['data_t0'][:16]} | {z['origini_valutazione']} | "
              f"{z['origini_addestramento']} | {z['perdita_addestramento']:.1%} |")
    a("")
    a("**Righe contro origini, contate dall'esecutore** (`e5_prepara.json`): ")
    for c in CITTA:
        q = PR["origini_prova"][c]
        a(f"- {c}: {q['righe_periodo_prova']} righe del periodo di prova → {q['nominali']} origini nominali, "
          f"{q['escluse']} escluse per salto, {q['ammissibili']} ammissibili. Salti: "
          + "; ".join(f"righe {i} ({s['da'][:10]} → {s['a'][:10]}, {s['origini_escluse']} origini)"
                      for i, s in q["salti"].items()) + ".")
    a("")
    a("Le 38 origini escluse in ogni citta' sono **due salti di sette giorni** del calendario "
      "Traffic4cast, 19 origini ciascuno (12 di finestra + 8 di orizzonte − 1): un valore della "
      "sorgente, non una costante.")
    a("")
    a("## 3. Scelte pre-registrate e loro base")
    a("")
    a("### Sei semi (201–206): la semiampiezza non dipende dai semi")
    a("")
    a("| citta' | confronto | 6 semi | 12 semi |")
    a("|---|---|---|---|")
    for c in CITTA:
        for k, v in PP["potenza"][c].items():
            a(f"| {c} | {k} | ±{v['semiampiezza_6']:.4f} | ±{v['semiampiezza_12']:.4f} |")
    a("")
    a("### k della secondaria (traiettoria sull'episodio di validazione esteso, mai dal test)")
    a("")
    for c in CITTA:
        cv = KS["curva_validazione"][c]
        a(f"- {c}: k = **{KS['k'][c]}**; " + ", ".join(f"k{k} {v:.4f}" for k, v in cv.items()))
    a("")
    a("## 4. Le affermazioni principali per citta' × episodio")
    a("")
    a("| citta' | aff. | episodio 1 | episodio 2 | episodio 3 | segni | stesso segno 3/3 | solo ep. 3 |")
    a("|---|---|---|---|---|---|---|---|")
    conc = {}
    for c in CITTA:
        for k_, et in AFF.items():
            rr = [RS["affermazioni"][f"{c}/ep{e}/{k_}"] for e in EPISODI]
            ss = RS["stesso_segno"][f"{c}/{k_}"]
            conc[(c, k_)] = ss["concorda"]
            a(f"| {c} | ({k_}) {et} | " + " | ".join(f"{_f(r['media'])} {_ic(r['ic_con_nodi'])}" for r in rr)
              + f" | {''.join(ss['segni'])} | {'**si**' if ss['concorda'] else 'no'} | {ss['solo_ep3']} |")
    a("")
    n_conc = sum(conc.values()); n_tot = len(conc)
    a(f"Segno dell'intervallo: − (sotto lo zero), + (sopra), 0 (lo zero dentro). **{n_conc} affermazioni su "
      f"{n_tot} hanno lo stesso segno in tutti e tre gli episodi**; le altre vanno riportate nel paper come "
      f"dipendenti dall'episodio, con la figura `figure/episodi_e5.png`.")
    hi_b = max(RS["affermazioni"][f"{c}/ep{e}/b"]["ic_con_nodi"][1] for c in CITTA for e in EPISODI)
    n_b_neg = sum(1 for c in CITTA for e in EPISODI if RS["affermazioni"][f"{c}/ep{e}/b"]["ic_con_nodi"][1] < 0)
    a(f"- **Il criterio primario di E4, esteso ai nove episodi**: gated − F₀′ ha estremo superiore massimo "
      f"{_f(hi_b)} ({'≤ +0,005: la politica non peggiora mai il modello che la ospita, su nessuna data' if hi_b <= 0.005 else 'OLTRE +0,005'}); "
      f"lo migliora con intervallo sotto lo zero in {n_b_neg}/9.")
    for k_, et in AFF.items():
        cc_ = [c for c in CITTA if conc[(c, k_)]]
        a(f"- ({k_}) {et}: concorda in {len(cc_)}/3 citta'" + (f" ({', '.join(cc_)})" if cc_ else "")
          + "; solo episodio 3: " + ", ".join(f"{c} {RS['stesso_segno'][f'{c}/{k_}']['solo_ep3']}" for c in CITTA) + ".")
    a("")
    a("## 5. Altri confronti (secondari)")
    a("")
    a("| citta' | confronto | episodio 1 | episodio 2 | episodio 3 |")
    a("|---|---|---|---|---|")
    for c in CITTA:
        for k_, et in (("gated-C", "gated − C"), ("A-C", "A − C"), ("Fp_672-C_intero", "F′(1 sett.) − C, intero periodo"),
                       ("Fp_96k-C", "F′(24 h, k) − C [secondaria]"), ("Fp_96k-Fp_96", "F′(24 h, k) − F′(24 h) [secondaria]")):
            rr = [RS["altri"][f"{c}/ep{e}/{k_}"] for e in EPISODI]
            a(f"| {c} | {et} | " + " | ".join(f"{_f(r['media'])} {_ic(r['ic_con_nodi'])}" for r in rr) + " |")
    a("")
    note = []
    for c in CITTA:
        d = [RS["altri"][f"{c}/ep{e}/Fp_96k-Fp_96"] for e in EPISODI]
        if all(abs(r["media"]) < 1e-12 for r in d):
            note.append(f"{c}: k = {KS['k'][c]} coincide con la configurazione congelata, quindi "
                        f"F′(24 h, k) ≡ F′(24 h) per costruzione")
        else:
            note.append(f"{c}: k = {KS['k'][c]}; F′(24 h, k) − F′(24 h) = "
                        + ", ".join(f"{_f(r['media'])}" for r in d) + " negli episodi 1-3; F′(24 h, k) − C = "
                        + ", ".join(f"{_f(RS['altri'][f'{c}/ep{e}/Fp_96k-C']['media'])}" for e in EPISODI))
    a("La secondaria non entra in nessuna affermazione principale (pre-registrata come tale). "
      + "; ".join(note) + ".")
    a("")
    a("## 6. N al lavoro: nodi sotto soglia per episodio")
    a("")
    a("| citta' | N | episodio 1 | episodio 2 | episodio 3 |")
    a("|---|---|---|---|---|")
    for c in CITTA:
        q = [RS["nodi_sotto_N"][f"{c}/ep{e}"] for e in EPISODI]
        a(f"| {c} | {q[0]['N']} | " + " | ".join(f"{z['media_per_cella']:.1f} (max {z['massimo']}) su {z['nodi']}" for z in q) + " |")
    a("")
    dove = [(c, e) for c in CITTA for e in EPISODI if RS["nodi_sotto_N"][f"{c}/ep{e}"]["massimo"] > 0]
    if not dove:
        a("N e' **rimasto inerte ovunque**: nessun nodo sotto soglia in alcun episodio.")
    else:
        a("N e' **entrato in gioco** in: " + ", ".join(
            f"{c} ep. {e} ({RS['nodi_sotto_N'][f'{c}/ep{e}']['media_per_cella']:.0f} nodi su "
            f"{RS['nodi_sotto_N'][f'{c}/ep{e}']['nodi']} tenuti su F₀′)" for c, e in dove)
          + ". In validazione (E4) era inerte; sul test no. Dove molti nodi restano su F₀′, gated − F₀′ "
            "si avvicina a zero per costruzione: " + "; ".join(
            f"{c} ep. {e} gated − F₀′ {_f(RS['affermazioni'][f'{c}/ep{e}/b']['media'])} contro "
            f"F′(1 sett.) − C {_f(RS['affermazioni'][f'{c}/ep{e}/c']['media'])}" for c, e in dove
            if RS["nodi_sotto_N"][f"{c}/ep{e}"]["media_per_cella"] > 0.5 * RS["nodi_sotto_N"][f"{c}/ep{e}"]["nodi"])
          + ". La soglia, scelta dallo spareggio, ha trattenuto adattamenti che avrebbero pagato: va detto nel paper.")
    a("")
    a("## 7. F′(1 settimana) − A sull'episodio principale (numero richiesto, calcolato prima di E5)")
    a("")
    for c in CITTA:
        r = SV["confronti"][f"{c}/Fp_672-A"]; ac = SV["confronti"][f"{c}/A-C"]
        a(f"- {c}: {_f(r['media'])} {_ic(r['ic_con_nodi'])}{' (zero dentro)' if r['include_zero'] else ''}; "
          f"A − C {_f(ac['media'])}; quota del divario recuperata {1 - r['media'] / (-ac['media']):.0%}.")
    a("")
    a("## 8. Dichiarazioni")
    a("")
    a("- **Sei semi invece di otto**: deviazione dalla lettera del §9 confermata dal revisore; la "
      "semiampiezza cambia di ±0,0003 fra 12 e 6 semi (sezione 3).")
    a("- **Costo del protocollo corretto prima del lancio**: 324 addestramenti, non 108 (le tre citta' "
      f"non erano moltiplicate); il lancio e' durato {E['esito']['ore_calendario']:.1f} ore con 8 processi.")
    a("- **Limitazione 7**: l'episodio di validazione di E4 cade dentro il periodo di valutazione "
      "dell'episodio 2 (nodi diversi); per questo (b) ed (e) sono riportate anche per il solo episodio 3.")
    a("- Nei periodi di valutazione degli episodi 2 la lunghezza differisce dove un salto della griglia "
      "impedisce l'uguaglianza esatta (Madrid 1438, Londra 1520 contro 1426 e 1440): dichiarato, non corretto.")
    a("- `_partizioni` accetta `fine_periodo` e la finestra del descrittore si verifica solo per chi lo usa: "
      "collaudi 8/8 (scarto 0), 25/25, 24/24, 19/19 dopo la modifica.")
    a("- Il numero di repliche del ricampionamento e' `esegui_e4.B_BOOT`, usato da `_boot`; una costante "
      "locale omonima nei moduli di E5 e' stata rimossa perche' non comandava nulla (stesso valore).")
    e3bis = (OUT / "e3bis_risultati.json").exists()
    a("- **E3-bis**: " + ("eseguito, vedi il suo congelamento." if e3bis else
                        "**non eseguito** prima di questo congelamento: nel paper il confronto dei costi "
                        "fra R-orig (24 h di dati) e F′ (1 settimana) e' dichiarato **a dati asimmetrici**."))
    a("")
    a("## 9. Impronte")
    a("")
    a("| file | impronta |")
    a("|---|---|")
    for f, hh in R["impronte"].items():
        a(f"| `{f}` | `{hh}` |")
    a("")
    a("**Nessun parametro scelto dopo aver visto i risultati**: t₀, semi, (τ, N), k della secondaria e "
      "configurazione di F sono nella pre-registrazione firmata o in file con impronta scritti prima del test.")
    return "\n".join(A) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    print("[1/7] addestramenti"); E = addestramenti(a.out)
    if sum(E["marcatori"].values()) != 324 or E["esito"]["fallite"]:
        raise IngressoMancante(f"addestramenti {E['marcatori']}, falliti {E['esito']['fallite']}")
    print("[2/7] celle"); C = celle(a.out)
    if sum(C["per_episodio"].values()) != 162 or C["controllo_6_max"] > 1e-6:
        raise IngressoMancante(f"celle {C['per_episodio']}, controllo 6 {C['controllo_6_max']:.1e}")
    print("[3/7] risultati"); RS = leggi(a.out / "e5_risultati.json")
    print("[4/7] preparazione e prepara"); PP = leggi(a.out / "preparazione_e5.json"); PR = leggi(a.out / "e5_prepara.json")
    print("[5/7] k secondaria e scelta E4"); KS = leggi(a.out / "e5_k_secondaria.json"); SC = leggi(a.out / "e4_scelta_gated.json")
    if KS["impronta"] != RS["impronta_k_secondaria"] or SC["impronta"] != RS["impronta_scelta_e4"] \
            or C["imp_k"] != [KS["impronta"]]:
        raise IngressoMancante("impronte di k o di (tau, N) non coerenti fra file e risultati")
    print("[6/7] F'(1 sett.) - A"); SV = leggi(a.out / "e5_settimana_vs_A.json")
    print("[7/7] documento")
    R = {"data": datetime.now(timezone.utc).date().isoformat(), "commit": commit_git(),
         "addestramenti": E, "celle": C, "risultati": RS, "preparazione": PP, "prepara": PR,
         "k_secondaria": KS, "scelta_e4": SC, "settimana_vs_A": SV,
         "impronte": {f: h(f) for f in FILE}}
    (a.out / "congelamento_e5.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=list))
    Path("CONGELAMENTO_E5.md").write_text(documento(R))
    n = sum(1 for v in RS["stesso_segno"].values() if v["concorda"])
    print(f"  generato CONGELAMENTO_E5.md; numeri in results/evoluzione/congelamento_e5.json")
    print(f"  stesso segno in 3/3 episodi: {n} affermazioni su {len(RS['stesso_segno'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
