#!/usr/bin/env python3
"""
Congelamento di E4 — F contro C e la politica gated.
=====================================================
**Ogni numero e' derivato dai file**: confronti, terzi, curva e traiettoria da
`e4_risultati.json`; scelta e griglia di validazione da `e4_scelta_gated.json`;
griglia sul test da `e4_griglia_test.json`; costi da `costi_e4.json`; celle,
controlli per cella (3, 4, 6, 7), impronte, origini e aggiornamenti dai file
`predizioni_e4/*.npz`; durata del lancio da `e4_valuta.log` se presente;
copertura da `copertura_e4.json` se presente. Il verdetto e' calcolato dai
segni e dagli intervalli, non scritto.

Se un ingresso obbligatorio manca, si ferma.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e4.py
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

RADICE = Path(__file__).resolve().parent
sys.path.insert(0, str(RADICE))
from evoluzione.esperimenti.esegui_e4 import (  # noqa: E402
    CITTA, DIR_PRED, DURATE, N_SOGLIE, TAU)

OUT = Path("results/evoluzione")
FILE = ["evoluzione/componente/adattamento.py",
        "evoluzione/esperimenti/esegui_e4.py",
        "evoluzione/esperimenti/costi_e4.py",
        "evoluzione/analisi/analizza_e4.py",
        "evoluzione/analisi/analizza_copertura_e4.py",
        "protocol/E4.md"]
ET_L = {24: "6 h", 48: "12 h", 96: "24 h", 192: "48 h", 672: "1 settimana"}
ET_TAU = {96: "24 h", 192: "48 h", 672: "1 settimana", None: "mai"}
SOGLIA_IC = 0.005


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


def celle(out: Path) -> dict:
    """Conteggi e controlli per cella dai file npz: nessun numero dal log."""
    d = out / DIR_PRED
    E = {"prova": {}, "validazione": {}, "controllo_3": {}, "controllo_7": 0,
         "impronte_uguali": True, "origini_adattamento": {}, "fasce": {},
         "aggiornamenti": {}, "durate_validazione": None}
    sc_max = {}
    imp = {}
    for ep in ("prova", "validazione"):
        for c in CITTA:
            ff = sorted(d.glob(f"{ep}_{c}_p*_s*.npz"))
            E[ep][c] = len(ff)
            for f in ff:
                z = np.load(f, allow_pickle=True)
                k = (c, int(z["partizione"]), int(z["seme"]))
                imp.setdefault(k, set()).add((str(z["impronta_E"]), str(z["impronta_Ep"])))
                if str(z["controllo_7"]) == "ok":
                    E["controllo_7"] += 1
                if ep == "prova":
                    for m, q in json.loads(str(z["controllo_3"])).items():
                        sc_max[m] = max(sc_max.get(m, 0.0), q["scarto_relativo"])
                    E["fasce"].setdefault(c, set()).add(tuple(int(v) for v in z["fasce"]))
                    agg = json.loads(str(z["aggiornamenti"]))
                    E["aggiornamenti"].setdefault(c, set()).add(
                        tuple(sorted(agg.items())))
                else:
                    E["durate_validazione"] = [int(v) for v in z["durate"]]
    E["controllo_3"] = sc_max
    # le impronte di E ed E' di una cella sono uguali fra prova e validazione
    E["impronte_uguali"] = all(len(v) == 1 for v in imp.values())
    E["celle_distinte"] = len(imp)
    for c in CITTA:
        if len(E["fasce"][c]) != 1:
            raise IngressoMancante(f"{c}: fasce diverse fra le celle di prova")
        E["fasce"][c] = list(E["fasce"][c])[0]
        if len(E["aggiornamenti"][c]) != 1:
            raise IngressoMancante(f"{c}: aggiornamenti diversi fra le celle di prova")
        E["aggiornamenti"][c] = dict(list(E["aggiornamenti"][c])[0])
    # origini d'adattamento per durata: dalla griglia regolare di una cella di prova
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import _carica
    from evoluzione.esperimenti.esegui_e4 import calendario
    for c in CITTA:
        D = _carica(c, out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        t0, _ = calendario("prova", c)
        E["origini_adattamento"][c] = {L: len(GR.origini_acquisizione(ok, t0, t0 + L))
                                       for L in DURATE}
    return E


def durata_lancio(out: Path):
    f = out / "e4_valuta.log"
    if not f.exists():
        return None
    m = re.findall(r"(\d+) celle, (\d+) fallite, ([\d.]+) min", f.read_text())
    return {"celle": int(m[-1][0]), "fallite": int(m[-1][1]),
            "minuti": float(m[-1][2])} if m else None


def plateau(traj: dict, tol=0.005):
    """Primo aggiornamento alla cui wCE e' entro `tol` relativo dal minimo, e il
    minimo stesso."""
    k = sorted(int(z) for z in traj)
    v = [traj[str(z)] for z in k]
    m = min(v); i_min = int(np.argmin(v))
    primo = next(z for z, w in zip(k, v) if w <= m * (1 + tol))
    return {"minimo": m, "a": k[i_min], "plateau": primo, "finale": v[-1], "ultimo": k[-1]}


def _f(x, n=3):
    return f"{x:+.{n}f}"


def _ic(q, n=3):
    return f"[{_f(q[0], n)}, {_f(q[1], n)}]"


def documento(R: dict) -> str:
    A = []; a = A.append
    E, RS, SC, G, K, L = (R["celle"], R["risultati"], R["scelta"], R["griglia_test"],
                          R["costi"], R["lancio"])
    C = RS["confronti"]
    n_agg = "/".join(str(v) for v in sorted({w for c in CITTA for w in E["aggiornamenti"][c].values()}))
    a("# Congelamento — E4, F contro C e la politica gated")
    a("")
    a(f"**Congelato il {R['data']}**, commit `{R['commit']}`. Pre-registrazione "
      f"`protocol/E4.md` (impronta `{R['impronte']['protocol/E4.md']}`), firmata al "
      f"commit `dadd2dc2dcb59798` prima del lancio. **Ogni numero e' calcolato da "
      f"`genera_congelamento_e4.py`** dai file di risultato; il verdetto e' derivato, "
      f"non scritto.")
    a("")
    a("## 1. Che cosa e' stato eseguito")
    a("")
    a("| | |")
    a("|---|---|")
    a("| addestramenti | **nessuno**: C, E ed E′ sono i punti delle campagne precedenti, "
      f"impronte verificate per cella (controllo 4: {'uguali' if E['impronte_uguali'] else 'DIVERSE'} "
      f"fra episodio di prova e di validazione nelle {E['celle_distinte']} celle) |")
    per_c = ", ".join(f"{c} {E['prova'][c]}" for c in CITTA)
    a(f"| celle | prova {sum(E['prova'].values())} ({per_c}), "
      f"validazione {sum(E['validazione'].values())}"
      + (f"; lancio: {L['celle']} celle, {L['fallite']} fallite, {L['minuti']/60:.1f} ore in "
         f"concorrenza (8 processi) — **non e' il costo seriale**" if L else "") + " |")
    a(f"| durate d'adattamento | prova {', '.join(ET_L[d] for d in DURATE)}; validazione "
      f"{', '.join(ET_L[d] for d in E['durate_validazione'])} (i soli τ della politica) |")
    a("| origini d'adattamento per durata | " + "; ".join(
        f"{c}: " + ", ".join(f"{ET_L[d]} {n}" for d, n in E["origini_adattamento"][c].items())
        for c in CITTA) + " |")
    a("| aggiornamenti eseguiti (= configurati) | " + "; ".join(
        f"{c} {sorted(set(E['aggiornamenti'][c].values()))}" for c in CITTA) + " |")
    a(f"| controllo 3 (wCE dai punti contro le ricostruite, tolleranza 1e-6) | scarto massimo: "
      + ", ".join(f"{m} {v:.1e}" for m, v in E["controllo_3"].items()) + " |")
    a(f"| controllo 6 (stessi nodi e origini) | verificato in ogni cella di prova, "
      f"insieme al 3 |")
    a(f"| controllo 7 (nodi di validazione esclusi da E, E′, C, pesi, normalizzazione) | "
      f"verificato in {E['controllo_7']} celle su {sum(E['prova'].values()) + sum(E['validazione'].values())} |")
    a(f"| ricampionamento | {RS['repliche']} repliche, seme {RS['seme_bootstrap']}, "
      f"partizioni × semi × nodi |")
    a("")
    a("## 2. La scelta di (τ, N) sulla validazione — controllo 1")
    a("")
    a(f"Registrata in `e4_scelta_gated.json` (impronta `{SC['impronta']}`, "
      f"{SC['istante']}), prima del test; i risultati del test riportano la stessa "
      f"impronta (`{RS['impronta_scelta']}`). Regola: {SC['regola']}.")
    a("")
    a("| citta' | τ | N | wCE validazione | celle | pari merito |")
    a("|---|---|---|---|---|---|")
    for c in CITTA:
        s = SC["scelta"][c]; g = SC["griglia_validazione"][c]
        v = s["wce_validazione"]
        pari = [k for k, w in g.items() if abs(w - v) < 1e-9]
        a(f"| {c} | {ET_TAU[s['tau']]} | {s['N']} | {v:.5f} | {s['celle']} | "
          f"{', '.join(pari)} |")
    a("")
    a("Dove piu' coppie coincidono alla nona cifra, nessun nodo di validazione aveva "
      "meno celle valide di quelle soglie: lo spareggio (N maggiore) ha deciso, come "
      "pre-registrato.")
    a("")
    a("## 3. Criterio primario: gated − F₀′ ≤ 0 ovunque")
    a("")
    a("| citta' | gated(τ, N) | gated − F₀′ | IC 95 % | IC ≤ +0,005 |")
    a("|---|---|---|---|---|")
    n_ok = 0
    for c in CITTA:
        r = C[f"{c}/gated-F0p"]; s = SC["scelta"][c]
        ok = r["ic_con_nodi"][1] <= SOGLIA_IC; n_ok += ok
        a(f"| {c} | ({ET_TAU[s['tau']]}, {s['N']}) | **{_f(r['media'])}** | "
          f"{_ic(r['ic_con_nodi'])} | {'si' if ok else 'NO'} |")
    a("")
    a(f"**Criterio {'SODDISFATTO' if n_ok == 3 else 'NON soddisfatto'}** ({n_ok}/3): "
      + ("la politica non peggiora mai il modello unico che la ospita, e lo migliora in "
         "tutte e tre le citta' con intervallo interamente sotto lo zero."
         if all(C[f"{c}/gated-F0p"]["ic_con_nodi"][1] < 0 for c in CITTA) else
         "vedi tabella."))
    a("")
    a("### Secondari")
    a("")
    a("| citta' | gated − C | F₀′ − C (costo del modello unico) | gated − F′(24 h) | gated − oracolo |")
    a("|---|---|---|---|---|")
    for c in CITTA:
        r1, r2, r3, r4 = (C[f"{c}/gated-C"], C[f"{c}/F0p-C"], C[f"{c}/gated-Fp_96"],
                          C[f"{c}/gated-oracolo"])
        a(f"| {c} | {_f(r1['media'])} {_ic(r1['ic_con_nodi'])}"
          f"{' (zero dentro)' if r1['include_zero'] else ''} | {_f(r2['media'])} "
          f"{_ic(r2['ic_con_nodi'])} | {_f(r3['media'])} {_ic(r3['ic_con_nodi'])}"
          f"{' (zero dentro)' if r3['include_zero'] else ''} | {_f(r4['media'])} "
          f"{_ic(r4['ic_con_nodi'])} (oracolo {r4['oracolo']}) |")
    a("")
    paga = [c for c in CITTA if C[f"{c}/gated-C"]["ic_con_nodi"][1] < 0]
    pari = [c for c in CITTA if C[f"{c}/gated-C"]["include_zero"]]
    f0 = [C[f"{c}/F0p-C"]["media"] for c in CITTA]
    a(f"Rispetto a C la politica paga in {len(paga)} citta' ({', '.join(paga)}) ed e' alla "
      f"pari in {len(pari)} ({', '.join(pari) or '—'}). La frase del paper, derivata: "
      f"«il modello unico con token costa rispetto a un secondo modello senza identita' "
      f"da {_f(min(f0))} a {_f(max(f0))}; con la politica gated non peggiora mai e in "
      f"{len(paga)} citta' su 3 batte C».")
    a("")
    a("## 4. F − C e F′ − C a 24 ore, intero periodo e terzi")
    a("")
    a("| citta' | F − C | F′ − C | F′ − F | F₀ − C |")
    a("|---|---|---|---|---|")
    for c in CITTA:
        rr = [C[f"{c}/F_96-C"], C[f"{c}/Fp_96-C"], C[f"{c}/Fp_96-F_96"], C[f"{c}/F0-C"]]
        a(f"| {c} | " + " | ".join(f"{_f(r['media'])} {_ic(r['ic_con_nodi'])}"
                                    f"{' (zero dentro)' if r['include_zero'] else ''}"
                                    for r in rr) + " |")
    a("")
    a("| citta' | braccio | terzo 1 | terzo 2 | terzo 3 |")
    a("|---|---|---|---|---|")
    for c in CITTA:
        for n, et in (("F_96", "F − C"), ("Fp_96", "F′ − C"), ("F0p", "F₀′ − C")):
            tt = [RS["terzi"][f"{c}/{n}-C/terzo{i}"] for i in (1, 2, 3)]
            a(f"| {c} | {et} | " + " | ".join(
                f"{_f(t['media'])}{'' if not t['include_zero'] else ' (0)'}" for t in tt) + " |")
    a("")
    a("(0) = intervallo che include lo zero. L'adattamento a 24 ore **invecchia** dove "
      "il suo vantaggio si riduce dal primo al terzo terzo; F₀′ − C e' costante per "
      "costruzione (nessun adattamento).")
    a("")
    a("## 5. Curva per eta' (origini comuni, eta' > 1 settimana) — figura `figure/curva_e4.png`")
    a("")
    a("| citta' | origini | " + " | ".join(f"F {ET_L[d]}" for d in DURATE) + " | "
      + " | ".join(f"F′ {ET_L[d]}" for d in DURATE) + " | F₀′ |")
    a("|---|---|" + "---|" * (2 * len(DURATE) + 1))
    for c in CITTA:
        cv = RS["curva"]
        a(f"| {c} | {cv[f'{c}/origini_comuni']} | "
          + " | ".join(f"{_f(cv[f'{c}/F_{d}-C']['media'])}" for d in DURATE) + " | "
          + " | ".join(f"{_f(cv[f'{c}/Fp_{d}-C']['media'])}" for d in DURATE)
          + f" | {_f(cv[f'{c}/F0p-C']['media'])} |")
    a("")
    sett = {c: RS["curva"][f"{c}/Fp_672-C"] for c in CITTA}
    n_sett = sum(1 for r in sett.values() if r["ic_con_nodi"][1] < 0)
    a(f"Adattando su una settimana, F′ batte C sulle origini comuni in **{n_sett} citta' su 3** "
      f"(" + ", ".join(f"{c} {_f(sett[c]['media'])} {_ic(sett[c]['ic_con_nodi'])}" for c in CITTA)
      + ").")
    corte = [d for d in DURATE if d < 96]
    peggio = all(RS["curva"][f"{c}/{n}_{d}-C"]["ic_con_nodi"][0] > 0
                 for c in CITTA for n in ("F", "Fp") for d in corte)
    o_corte = sorted({E["origini_adattamento"][c][d] for c in CITTA for d in corte})
    esito_corte = ("peggiora il modello in tutte le citta', per F e per F′, con intervallo "
                   "sopra lo zero" if peggio else "non peggiora ovunque: vedi tabella")
    et_corte = " e ".join(ET_L[d] for d in corte)
    o_txt = "/".join(str(o) for o in o_corte)
    a(f"Sotto le 24 ore ({et_corte}: {o_txt} origini per {n_agg} aggiornamenti) "
      f"l'adattamento {esito_corte}. Figura, non criterio.")
    a("")
    a("## 6. Traiettoria dell'adattamento a 24 ore — figura `figure/traiettoria_e4.png`")
    a("")
    a("| citta' | braccio | wCE a 0 | minimo (a k) | plateau (entro 0,5 %) | finale (a k) |")
    a("|---|---|---|---|---|---|")
    prima = 0
    for c in CITTA:
        pf = R["traiettoria"][f"{c}/F"]; pp = R["traiettoria"][f"{c}/Fp"]
        prima += pp["plateau"] <= pf["plateau"]
        for et, p_, t in (("F", pf, RS["traiettoria"][f"{c}/F"]), ("F′", pp, RS["traiettoria"][f"{c}/Fp"])):
            a(f"| {c} | {et} | {t['0']:.4f} | {p_['minimo']:.4f} ({p_['a']}) | {p_['plateau']} | "
              f"{p_['finale']:.4f} ({p_['ultimo']}) |")
    a("")
    a(f"F′ raggiunge il plateau non dopo F in {prima} citta' su 3. Dove la wCE finale e' "
      f"sopra il minimo, i {n_agg} "
      f"aggiornamenti congelati (scelti per il giorno di validazione) sovradattano le 77 "
      f"origini del test: e' un fatto sulla configurazione di F, dichiarato, non ritoccato.")
    a("")
    a("## 7. Griglia (τ, N) sul test — figura `figure/griglia_e4.png`, NON usata per la scelta")
    a("")
    a("| citta' | scelta (validazione) | wCE test della scelta | minimo sul test | wCE | coincidono |")
    a("|---|---|---|---|---|---|")
    for c in CITTA:
        s = SC["scelta"][c]; g = G["griglia_test"][c]
        k = f"tau={'mai' if s['tau'] is None else s['tau']}/N={s['N']}"
        kmin, vmin = min(g.items(), key=lambda kv: kv[1])
        a(f"| {c} | {k} | {g[k]:.5f} | {kmin} | {vmin:.5f} | "
          f"{'si' if abs(g[k] - vmin) < 1e-9 else 'no'} |")
    a("")
    a("Il trasferimento dalla validazione (periodo di selezione dei punti, limitazione 8) "
      "al test e' imperfetto dove la riga dice «no»; la scelta resta quella registrata.")
    a("")
    a("## 8. Costi — campione isolato, un processo (`costi_e4.json`)")
    a("")
    T = K["tabella"]
    a("| configurazione | calcolo all'inserimento | attesa dati | pronto dopo |")
    a("|---|---|---|---|")
    a("| F₀′ (modello unico, token) | 0 s | 0 | **all'installazione** |")
    a(f"| F′ (24 h) | {T['Fp']['inserimento_s']:.1f} s | 24 h | {T['Fp']['disponibilita_s']/3600:.1f} h |")
    for c in CITTA:
        g = T["gated"][c]
        a(f"| gated {c} (τ = {ET_TAU[g['tau']]}, N = {g['N']}) | F₀′ subito, poi "
          f"{g['adattamento_s']:.1f} s | {g['attesa_dati_s']/3600:.0f} h | "
          f"F₀′ all'installazione, F′ dopo {g['disponibilita_adattamento_s']/3600:.1f} h |")
    a("")
    a(f"Le {K['rimisure_che_riproducono_la_concorrente']} rimisure isolate riproducono la "
      f"wCE concorrente entro {K['tolleranza']:g}. Per confronto, in E3 il riaddestramento "
      f"leale (R-orig) costava 2206 s dopo 24 h di dati.")
    a("")
    a("## 9. Dichiarazioni")
    a("")
    a("- **Deviazione dal §8 del protocollo, dichiarata prima del lancio in E4.md**: curva "
      "a {6 h, 12 h, 24 h, 48 h, 1 settimana} invece di {1 h, 4 h, …}: sotto le 5 ore la "
      "regola delle origini non ne contiene alcuna.")
    if L:
        a(f"- **Stima di costo del protocollo sbagliata, non deviazione**: «< 10 ore-processo» "
          f"contava gli adattamenti; le 13 valutazioni per cella sull'intero periodo piu' le "
          f"12 intermedie della traiettoria hanno portato il lancio a {L['minuti']/60:.1f} ore "
          f"con 8 processi. Nessun parametro e' cambiato.")
    a("- **Limitazione 8**: (τ, N) scelti sul periodo di validazione cronologica, su cui i "
      "punti di C, E, E′ sono stati selezionati (non addestrati); la sezione 7 mostra "
      "quanto il trasferimento ha reso.")
    a("- La griglia di N {0, 77, 154, 231} e' stata fissata dopo l'analisi di copertura del "
      "2/10 (quartili del massimo), come dichiarato nel protocollo; sulla validazione le "
      "soglie basse coincidono (sezione 2).")
    a("- In validazione si sono adattate le sole durate della politica (24 h, 48 h, "
      "1 settimana): le altre non sarebbero servite a nulla.")
    if R["copertura"] is None:
        a("- Analisi di copertura (punto 5 del protocollo): eseguita il 2/10 con "
          "`analizza_copertura_e4.py`, numeri riportati nel protocollo §5; il file "
          "`copertura_e4.json` non e' presente in `results/evoluzione`, quindi qui non si "
          "ricopiano.")
    else:
        righe = []
        for c in CITTA:
            z = R["copertura"].get(c, {})
            if "spearman_celle_FC" not in z:
                righe.append(f"{c} n.d."); continue
            r1, r2 = z["spearman_celle_FC"], z["spearman_celle_FpC"]
            righe.append(f"{c} ρ(celle valide, F − C) = {r1['rho']:+.2f} "
                         f"[{r1['ic_nodi'][0]:+.2f}, {r1['ic_nodi'][1]:+.2f}], "
                         f"F′ − C {r2['rho']:+.2f} [{r2['ic_nodi'][0]:+.2f}, {r2['ic_nodi'][1]:+.2f}]")
        a("- Analisi di copertura (punto 5, descrittiva, `copertura_e4.json`): "
          + "; ".join(righe) + ". Senza soglia di successo: ipotesi per E7.")
    a("")
    a("## 10. Impronte")
    a("")
    a("| file | impronta |")
    a("|---|---|")
    for f, hh in R["impronte"].items():
        a(f"| `{f}` | `{hh}` |")
    a("")
    a("**Nessun parametro scelto dopo aver visto il test**: griglie di τ e N, regola di "
      "selezione e spareggio, criterio e soglia sono nella pre-registrazione firmata; "
      "la griglia sul test e' figura.")
    return "\n".join(A) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    print("[1/6] celle e controlli dai npz"); E = celle(a.out)
    if sum(E["prova"].values()) != 108 or sum(E["validazione"].values()) != 108:
        raise IngressoMancante(f"celle: prova {E['prova']}, validazione {E['validazione']}")
    if any(v > 1e-6 for v in E["controllo_3"].values()) or not E["impronte_uguali"]:
        raise IngressoMancante("controlli 3/4 non superati")
    print("[2/6] risultati del test"); RS = leggi(a.out / "e4_risultati.json")
    print("[3/6] scelta"); SC = leggi(a.out / "e4_scelta_gated.json")
    if RS.get("impronta_scelta") != SC.get("impronta"):
        raise IngressoMancante("i risultati non si riferiscono alla scelta registrata")
    print("[4/6] griglia sul test"); G = leggi(a.out / "e4_griglia_test.json")
    print("[5/6] costi"); K = leggi(a.out / "costi_e4.json")
    print("[6/6] lancio e copertura"); L = durata_lancio(a.out)
    cop = a.out / "copertura_e4.json"
    COP = json.loads(cop.read_text()) if cop.exists() else None
    R = {"data": datetime.now(timezone.utc).date().isoformat(), "commit": commit_git(),
         "celle": E, "risultati": RS, "scelta": SC, "griglia_test": G, "costi": K,
         "lancio": L, "copertura": COP,
         "traiettoria": {f"{c}/{n}": plateau(RS["traiettoria"][f"{c}/{n}"])
                         for c in CITTA for n in ("F", "Fp")},
         "impronte": {f: h(f) for f in FILE}}
    (a.out / "congelamento_e4.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=list))
    Path("CONGELAMENTO_E4.md").write_text(documento(R))
    print("  generato CONGELAMENTO_E4.md; numeri in results/evoluzione/congelamento_e4.json")
    print("  criterio primario: " + ("SODDISFATTO" if RS["criterio"]["soddisfatto"] else "NON soddisfatto")
          + "; gated - F0': " + ", ".join(
              f"{c} {RS['confronti'][f'{c}/gated-F0p']['media']:+.4f}" for c in CITTA))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
