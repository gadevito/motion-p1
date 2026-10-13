#!/usr/bin/env python3
"""
CONGELAMENTO_E14B.md — E14, stadio B: tutte le fasi con la statica in variante, contro i congelati.
======================================================================================================
Ogni numero viene da file. Congelati: `results/evoluzione/*.json` della campagna (statica non
causale) e `protocol/e14b/congelata/e14b_livelli_congelata.json`. Varianti: i fasci di
`protocol/e14b/<variante>/` (json rigenerati nella copia `~/OR3_<variante>` sulla Spark con
`esegui_e14b.sh`, manifesto con commit e impronte). Si includono le varianti il cui fascio esiste.

Criteri (stadio A, invariati): una dichiarazione e' «insensibile» alla variante se |Δ| < 0,002 wCE
e il segno dell'intervallo e' lo stesso (−, + o a cavallo dello zero); «sensibile» altrimenti.
«Cambia il verdetto» = cambia il segno dell'intervallo (per le citta', anche la lettura «stesso
segno in 3/3 episodi»).

Scrive `CONGELAMENTO_E14B.md` e `results/evoluzione/congelamento_e14b.json`.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e14b.py
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("results/evoluzione")
PROT = Path("protocol/e14b")
VARIANTI = ("c", "a", "b")
SOGLIA_DELTA = 0.002
CITTA = ("Madrid", "Londra", "Melbourne")
EPISODI = (1, 2, 3)
AFF = {"a": "F₀′ − C > 0", "b": "gated − F₀′ < 0", "c": "F′(1 sett.) − C < 0, origini comuni",
       "d": "F′(24 h) − C", "e": "F′(1 sett.) − A, origini comuni"}
E8_CONF = ("A-C", "F0-C", "F0p-C", "Fp_96-C", "Fp_672-C_eta>1sett", "gated-F0p", "Rorig_672-Fp_672_eta>1sett")


class IngressoMancante(Exception):
    pass


def leggi(f: Path):
    if not f.exists():
        raise IngressoMancante(str(f))
    return json.loads(f.read_text())


def impronta(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def segno_ic(r):
    if r is None:
        return "n.d."
    lo, hi = r["ic_con_nodi"] if "ic_con_nodi" in r else r["ic"]
    return "-" if hi < 0 else ("+" if lo > 0 else "0")


def f5(x):
    return "n.d." if x is None else f"{x:+.4f}"


def ic_s(r):
    if r is None:
        return "n.d."
    lo, hi = r["ic_con_nodi"] if "ic_con_nodi" in r else r["ic"]
    return f"{r['media']:+.4f} [{lo:+.4f}, {hi:+.4f}]"


def confronto(rc, rv):
    """Δ = media variante − media congelata; insensibile per il criterio dello stadio A."""
    if rc is None or rv is None:
        return {"delta": None, "segno_congelato": segno_ic(rc), "segno_variante": segno_ic(rv),
                "insensibile": None, "cambia_verdetto": None}
    d = rv["media"] - rc["media"]
    sc, sv = segno_ic(rc), segno_ic(rv)
    return {"delta": d, "segno_congelato": sc, "segno_variante": sv,
            "insensibile": bool(abs(d) < SOGLIA_DELTA and sc == sv), "cambia_verdetto": sc != sv}


def carica_insieme(radice: Path, livelli: Path):
    J = {}
    for n in ("e5_risultati", "e6_risultati", "e6a_risultati", "e6bis_risultati", "e4_risultati",
              "e4_scelta_gated", "e5_k_secondaria", "e6_scelta_gated", "e6a_scelta_gated", "e8_soglie",
              "e8_risultati", "e8bis_risultati", "analisi_e3", "veterani_e3", "e3bis_risultati", "e7_stadio1",
              "riselezione_rmon_test"):
        J[n] = leggi(radice / f"{n}.json")
    J["livelli"] = leggi(livelli)
    return J


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    C = carica_insieme(a.out, PROT / "congelata" / "e14b_livelli_congelata.json")
    V, MAN = {}, {}
    for v in VARIANTI:
        if (PROT / v / "manifesto.json").exists():
            MAN[v] = leggi(PROT / v / "manifesto.json")
            V[v] = carica_insieme(PROT / v, PROT / v / f"e14b_livelli_{v}.json")
    if not V:
        raise IngressoMancante(f"nessun fascio in {PROT}/<variante>/")
    vv = list(V)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    R = {"varianti": vv, "manifesti": MAN, "soglia_delta": SOGLIA_DELTA, "dichiarazioni": {}, "pems_controllo": {},
         "livelli": {}, "scelte": {}, "e7": {}, "e8": {}, "altre": {}, "sintesi": {}}
    L = []
    L.append("# CONGELAMENTO E14 — stadio B: statica in variante su tutte le fasi (E2–E8-bis)\n")
    L.append(f"Generato da `genera_congelamento_e14b.py` al commit `{commit}`, "
             f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. Protocollo: `protocol/E14.md` "
             f"(stadio B, mandato del revisore 13/10). Nessun riaddestramento: punti di controllo della campagna; "
             f"rifatte le sole fasi di valutazione, le selezioni su validazione e le analisi, con "
             f"`OR3_STATICA=<variante>` (`inserimento.statica_cella`). Varianti nel fascio: "
             + ", ".join(f"**({v})** commit `{MAN[v]['commit']}`, fascio preparato {MAN[v]['preparata']}, "
                         f"{len(MAN[v]['file'])} file" for v in vv) + ".\n")
    L.append("Letture dichiarate. (1) La configurazione di F′ (`selezione_F_*`, fase 2 della campagna, fuori da "
             "E2–E8-bis) resta quella congelata. (2) Le selezioni su validazione — (τ, N) di E4, E6, E6a; k di E5; "
             "soglie di E8 — sono rifatte con la variante. (3) Su PEMS04/08 ogni variante e' l'identita' "
             "(copertura 1 per ogni sensore, stadio 0): quelle fasi sono il controllo a scarto zero della pipeline. "
             "(4) Il controllo di `ricostruisci_predizioni` contro gli aggregati conservati non e' bloccante sotto "
             "una variante (lo scarto e' l'effetto della variante, registrato in `controllo_*.json`).\n")
    L.append(f"Criteri (stadio A): insensibile se |Δ| < {SOGLIA_DELTA} wCE e stesso segno dell'intervallo; "
             "«cambia il verdetto» se cambia il segno dell'intervallo. Δ = variante − congelato (medie); gli intervalli "
             "sono quelli al 95 % con ricampionamento congiunto di ciascun insieme.\n")

    # ---- 1. le cinque dichiarazioni, per contesto ---------------------------------------------------
    L.append("## 1. Le cinque dichiarazioni (a)–(e), per contesto, congelato contro variante\n")
    L.append("Citta': una riga per episodio (E5); PEMS08 (E6) e PEMS04 (E6a, (e) non riportabile). "
             "Valore [intervallo] e segno; Δ e lettura per variante.\n")
    testa = "| contesto | ep | dich. | congelato | " + " | ".join(f"({v}) valore | ({v}) Δ | ({v}) lettura" for v in vv) + " |"
    L.append(testa); L.append("|" + "---|" * (4 + 3 * len(vv)))
    n_sens, n_verd, n_tot = {v: 0 for v in vv}, {v: 0 for v in vv}, {v: 0 for v in vv}
    righe_delta = []

    def riga(ctx, ep, aff, rc, rvs):
        key = f"{ctx}/ep{ep}/{aff}" if ep else f"{ctx}/{aff}"
        R["dichiarazioni"][key] = {"congelato": rc, "varianti": {}}
        celle = []
        for v in vv:
            cf = confronto(rc, rvs[v]); R["dichiarazioni"][key]["varianti"][v] = {"valore": rvs[v], **cf}
            if cf["insensibile"] is not None:
                n_tot[v] += 1; n_sens[v] += int(not cf["insensibile"]); n_verd[v] += int(cf["cambia_verdetto"])
            lett = "n.d." if cf["insensibile"] is None else (
                "insensibile" if cf["insensibile"] else ("**cambia il verdetto** " if cf["cambia_verdetto"] else "sensibile ")
                + f"({cf['segno_congelato']}→{cf['segno_variante']})")
            celle.append(f"{ic_s(rvs[v])} {segno_ic(rvs[v])} | {f5(cf['delta'])} | {lett}")
            righe_delta.append((ctx, ep, aff, v, cf["delta"], rc, rvs[v]))
        L.append(f"| {ctx} | {ep or '—'} | ({aff}) | {ic_s(rc)} {segno_ic(rc)} | " + " | ".join(celle) + " |")

    for c in CITTA:
        for k in EPISODI:
            for aff in AFF:
                riga(c, k, aff, C["e5_risultati"]["affermazioni"].get(f"{c}/ep{k}/{aff}"),
                     {v: V[v]["e5_risultati"]["affermazioni"].get(f"{c}/ep{k}/{aff}") for v in vv})
    for aff in AFF:
        riga("PEMS08", None, aff, C["e6_risultati"]["affermazioni"].get(aff),
             {v: V[v]["e6_risultati"]["affermazioni"].get(aff) for v in vv})
    for aff in "abcd":
        riga("PEMS04", None, aff, C["e6a_risultati"]["affermazioni"].get(aff),
             {v: V[v]["e6a_risultati"]["affermazioni"].get(aff) for v in vv})
    L.append("")
    L.append("### 1b. Lettura «stesso segno in 3/3 episodi» per citta' (regola di E5)\n")
    L.append("| citta' | dich. | congelato | " + " | ".join(f"({v})" for v in vv) + " |")
    L.append("|" + "---|" * (3 + len(vv)))
    n_33 = {v: 0 for v in vv}
    for c in CITTA:
        for aff in AFF:
            sc = C["e5_risultati"]["stesso_segno"][f"{c}/{aff}"]
            celle = []
            for v in vv:
                sv = V[v]["e5_risultati"]["stesso_segno"][f"{c}/{aff}"]
                camb = (sv["segni"] != sc["segni"]) or (sv["concorda"] != sc["concorda"])
                n_33[v] += int(camb)
                celle.append(f"{''.join(sv['segni'])} {'si' if sv['concorda'] else 'no'}" + (" **≠**" if camb else ""))
                R["dichiarazioni"].setdefault("stesso_segno", {})[f"{c}/{aff}/{v}"] = {"congelato": sc, "variante": sv, "cambia": camb}
            L.append(f"| {c} | ({aff}) | {''.join(sc['segni'])} {'si' if sc['concorda'] else 'no'} | " + " | ".join(celle) + " |")
    L.append("")
    L.append("### 1c. Tabella delle Δ (dichiarazione × contesto × variante), con gli intervalli dei due insiemi\n")
    L.append("| dich. | contesto | ep | variante | Δ | intervallo congelato | intervallo variante |")
    L.append("|---|---|---|---|---|---|---|")
    for ctx, ep, aff, v, d, rc, rv in sorted(righe_delta, key=lambda z: (z[2], CITTA.index(z[0]) if z[0] in CITTA else 9, z[1] or 0, z[3])):
        L.append(f"| ({aff}) | {ctx} | {ep or '—'} | ({v}) | {f5(d)} | {ic_s(rc)} | {ic_s(rv)} |")
    L.append("")

    # ---- 2. livelli assoluti e rapporto ---------------------------------------------------------------
    L.append("## 2. Livelli assoluti di C, A, F₀ e rapporto (F₀ − C)/(A − C), per citta' (`e14b_livelli_*.json`)\n")
    L.append("Episodio 1, 36 celle per citta', intervalli con ricampionamento congiunto (4.000 repliche, stesso seme "
             "nei due insiemi). Il rapporto dice quanta parte del divario C→A resta aperta a F₀.\n")
    L.append("| citta' | insieme | wCE C | wCE A | wCE F₀ | A − C | F₀ − C | (F₀ − C)/(A − C) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for c in CITTA:
        for et, J in [("congelato", C)] + [(f"({v})", V[v]) for v in vv]:
            z = J["livelli"]["per_citta"][c]; Lv, D, rr = z["livelli"], z["differenze"], z["rapporto_F0C_su_AC"]
            L.append(f"| {c} | {et} | {Lv['C']['media']:.4f} [{Lv['C']['ic'][0]:.4f}, {Lv['C']['ic'][1]:.4f}] "
                     f"| {Lv['A']['media']:.4f} [{Lv['A']['ic'][0]:.4f}, {Lv['A']['ic'][1]:.4f}] "
                     f"| {Lv['F0']['media']:.4f} [{Lv['F0']['ic'][0]:.4f}, {Lv['F0']['ic'][1]:.4f}] "
                     f"| {ic_s(D['A-C'])} | {ic_s(D['F0-C'])} | {rr['media']:.3f} [{rr['ic'][0]:.3f}, {rr['ic'][1]:.3f}] |")
            R["livelli"][f"{c}/{et}"] = z
    L.append("")
    L.append("| citta' | variante | Δ wCE C | Δ wCE A | Δ wCE F₀ | Δ (A − C) | Δ (F₀ − C) | Δ rapporto |")
    L.append("|---|---|---|---|---|---|---|---|")
    for c in CITTA:
        zc = C["livelli"]["per_citta"][c]
        for v in vv:
            zv = V[v]["livelli"]["per_citta"][c]
            dl = {n: zv["livelli"][n]["media"] - zc["livelli"][n]["media"] for n in ("C", "A", "F0")}
            dd = {n: zv["differenze"][n]["media"] - zc["differenze"][n]["media"] for n in ("A-C", "F0-C")}
            dr = zv["rapporto_F0C_su_AC"]["media"] - zc["rapporto_F0C_su_AC"]["media"]
            R["livelli"][f"{c}/delta_{v}"] = {**dl, **dd, "rapporto": dr}
            L.append(f"| {c} | ({v}) | {dl['C']:+.4f} | {dl['A']:+.4f} | {dl['F0']:+.4f} | {dd['A-C']:+.4f} | {dd['F0-C']:+.4f} | {dr:+.3f} |")
    L.append("")

    # ---- 3. selezioni su validazione ---------------------------------------------------------------------
    L.append("## 3. Le selezioni su validazione: cambiano con la variante?\n")
    L.append("| selezione | contesto | congelato | " + " | ".join(f"({v})" for v in vv) + " |")
    L.append("|" + "---|" * (3 + len(vv)))

    def tn(sc):
        return f"τ={'mai' if sc['tau'] is None else sc['tau']}, N={sc['N']}"
    n_sel = {v: 0 for v in vv}
    for c in CITTA:
        sc = C["e4_scelta_gated"]["scelta"][c]; celle = []
        for v in vv:
            sv = V[v]["e4_scelta_gated"]["scelta"][c]; camb = (sv["tau"], sv["N"]) != (sc["tau"], sc["N"]); n_sel[v] += camb
            celle.append(tn(sv) + (" **≠**" if camb else "")); R["scelte"][f"E4/{c}/{v}"] = {"congelato": sc, "variante": sv, "cambia": camb}
        L.append(f"| E4 (τ, N) | {c} | {tn(sc)} | " + " | ".join(celle) + " |")
    for c in CITTA:
        kc = C["e5_k_secondaria"]["k"][c]; celle = []
        for v in vv:
            kv = V[v]["e5_k_secondaria"]["k"][c]; camb = kv != kc; n_sel[v] += camb
            celle.append(f"k={kv}" + (" **≠**" if camb else "")); R["scelte"][f"E5k/{c}/{v}"] = {"congelato": kc, "variante": kv, "cambia": camb}
        L.append(f"| E5 k secondario | {c} | k={kc} | " + " | ".join(celle) + " |")
    for et, nome, ctx in (("E6 (τ, N)", "e6_scelta_gated", "PEMS08"), ("E6a (τ, N)", "e6a_scelta_gated", "PEMS04")):
        sc = C[nome]["scelta"][ctx]; celle = []
        for v in vv:
            sv = V[v][nome]["scelta"][ctx]; camb = (sv["tau"], sv["N"]) != (sc["tau"], sc["N"]); n_sel[v] += camb
            celle.append(tn(sv) + (" **≠**" if camb else "")); R["scelte"][f"{et}/{v}"] = {"congelato": sc, "variante": sv, "cambia": camb}
        L.append(f"| {et} | {ctx} | {tn(sc)} | " + " | ".join(celle) + " |")
    # soglie di E8
    n_sog = {v: [0, 0] for v in vv}
    for gr, sog in C["e8_soglie"].items():
        if gr.startswith("_"):
            continue
        for m, z in sog.items():
            for v in vv:
                zv = V[v]["e8_soglie"].get(gr, {}).get(m)
                if zv is None:
                    continue
                n_sog[v][1] += 1; n_sog[v][0] += int((zv["prim"], zv["par"]) != (z["prim"], z["par"]))
                R["scelte"][f"E8soglie/{gr}/{m}/{v}"] = {"congelato": [z["prim"], z["par"]], "variante": [zv["prim"], zv["par"]]}
    L.append("| E8 soglie (prim, par) cambiate | tutti | — | " + " | ".join(f"{n_sog[v][0]} su {n_sog[v][1]}" for v in vv) + " |")
    L.append("")

    # ---- 4. E7 -----------------------------------------------------------------------------------------
    L.append("## 4. E7, stadio 1: l'ipotesi e la regola di decisione\n")
    for et, J in [("congelato", C)] + [(f"({v})", V[v]) for v in vv]:
        d = J["e7_stadio1"]["decisione"]; ip = J["e7_stadio1"]["ipotesi"]
        R["e7"][et] = {"decisione": d, "ipotesi_vale": ip.get("vale")}
        L.append(f"- {et}: ipotesi vale = **{ip.get('vale')}**, fallita in almeno un gruppo = {d['ipotesi_fallita_in_almeno_un_gruppo']}, "
                 f"stadio 2a = **{'si esegue' if d['stadio_2a'] else 'non si esegue'}**.")
    camb_e7 = {v: (V[v]["e7_stadio1"]["decisione"]["stadio_2a"] != C["e7_stadio1"]["decisione"]["stadio_2a"]
                   or V[v]["e7_stadio1"]["ipotesi"].get("vale") != C["e7_stadio1"]["ipotesi"].get("vale")) for v in vv}
    L.append("- La decisione di E7 " + "; ".join(f"({v}): {'**cambia**' if camb_e7[v] else 'non cambia'}" for v in vv) + ".\n")

    # ---- 5. E8 / E8-bis -------------------------------------------------------------------------------
    L.append("## 5. E8 (wCE e regola primaria) ed E8-bis (ΔAUC): segni dei confronti per gruppo\n")
    L.append("| gruppo | confronto | wCE congelato | " + " | ".join(f"wCE ({v})" for v in vv)
             + " | ΔAUC congelato | " + " | ".join(f"ΔAUC ({v})" for v in vv) + " |")
    L.append("|" + "---|" * (4 + 2 * len(vv)))
    n_e8 = {v: 0 for v in vv}
    for gr in C["e8_risultati"]["gruppi"]:
        for nome in E8_CONF:
            rc = C["e8_risultati"]["gruppi"][gr]["confronti"].get(nome, {}).get("wce")
            bc = C["e8bis_risultati"]["gruppi"].get(gr, {}).get("confronti", {}).get(nome, {}).get("auc")
            if rc is None and bc is None:
                continue
            cw, cb = [], []
            for v in vv:
                rv = V[v]["e8_risultati"]["gruppi"].get(gr, {}).get("confronti", {}).get(nome, {}).get("wce")
                bv = V[v]["e8bis_risultati"]["gruppi"].get(gr, {}).get("confronti", {}).get(nome, {}).get("auc")
                cf = confronto(rc, rv); cfb = confronto(bc, bv)
                n_e8[v] += int(bool(cf["cambia_verdetto"])) + int(bool(cfb["cambia_verdetto"]))
                R["e8"][f"{gr}/{nome}/{v}"] = {"wce": cf, "auc": cfb}
                cw.append(f"{ic_s(rv)} {segno_ic(rv)}" + (" **≠**" if cf["cambia_verdetto"] else ""))
                cb.append(f"{ic_s(bv)} {segno_ic(bv)}" + (" **≠**" if cfb["cambia_verdetto"] else ""))
            L.append(f"| {gr} | {nome} | {ic_s(rc)} {segno_ic(rc)} | " + " | ".join(cw) + f" | {ic_s(bc)} {segno_ic(bc)} | " + " | ".join(cb) + " |")
    L.append("")

    # ---- 6. altre dichiarazioni (E3, E3-bis, veterani, E4, R-mon-eq) ---------------------------------
    L.append("## 6. Altre dichiarazioni del paper: E3, E3-bis, veterani, E4\n")
    L.append("| fase | confronto | congelato | " + " | ".join(f"({v}) valore | ({v}) Δ | ({v}) lettura" for v in vv) + " |")
    L.append("|" + "---|" * (3 + 3 * len(vv)))
    n_altre = {v: [0, 0] for v in vv}

    def riga_altra(fase, chiave, rc, rvs, et=None):
        celle = []
        for v in vv:
            cf = confronto(rc, rvs[v]); R["altre"][f"{fase}/{chiave}/{v}"] = cf
            if cf["insensibile"] is not None:
                n_altre[v][1] += 1; n_altre[v][0] += int(cf["cambia_verdetto"])
            lett = "n.d." if cf["insensibile"] is None else ("insensibile" if cf["insensibile"] else
                                                            ("**cambia il verdetto**" if cf["cambia_verdetto"] else "sensibile"))
            celle.append(f"{ic_s(rvs[v])} {segno_ic(rvs[v])} | {f5(cf['delta'])} | {lett}")
        L.append(f"| {fase} | {et or chiave} | {ic_s(rc)} {segno_ic(rc)} | " + " | ".join(celle) + " |")

    for c in CITTA:
        for n1, n2 in (("R-orig", "C"), ("R-orig", "R"), ("R-mon", "R-orig")):
            k = f"{c}/{n1}-{n2}"
            riga_altra("E3", k, C["analisi_e3"]["confronti"].get(k), {v: V[v]["analisi_e3"]["confronti"].get(k) for v in vv})
    for c in CITTA:
        for n1, n2 in (("R-orig", "C"), ("R-orig", "E")):
            k = f"{c}/{n1}-{n2}"
            riga_altra("E3 veterani", k, C["veterani_e3"]["confronti"].get(k), {v: V[v]["veterani_e3"]["confronti"].get(k) for v in vv})
    for c in CITTA:
        for k2 in ("Rw-Fpw", "Rw-C", "Fpw-C"):
            k = f"{c}/{k2}"
            riga_altra("E3-bis", k, C["e3bis_risultati"]["confronti"].get(k), {v: V[v]["e3bis_risultati"]["confronti"].get(k) for v in vv})
    for c in CITTA:
        for k2 in ("gated-F0p", "gated-C", "F_96-C", "Fp_96-C", "F0-C", "F0p-C"):
            k = f"{c}/{k2}"
            riga_altra("E4", k, C["e4_risultati"]["confronti"].get(k), {v: V[v]["e4_risultati"]["confronti"].get(k) for v in vv})
    L.append("")
    eq = {et: [J["e3bis_risultati"]["confronti"][f"{c}/Rw-Fpw"]["equivalente_3pc"] for c in CITTA]
          for et, J in [("congelato", C)] + [(f"({v})", V[v]) for v in vv]}
    L.append("E3-bis, equivalenza ±3 % di R-orig(1 sett.) e F′(1 sett.) per citta' (Madrid, Londra, Melbourne): "
             + "; ".join(f"{et} {['si' if z else 'no' for z in q]}" for et, q in eq.items()) + ".\n")
    R["altre"]["e3bis_equivalenza"] = eq

    # ---- 7. PEMS: controllo a scarto zero ---------------------------------------------------------
    L.append("## 7. Controllo: PEMS08 e PEMS04 a scarto zero (variante = identita' per costruzione)\n")
    for v in vv:
        mx = 0.0; n = 0
        for aff, rc in C["e6_risultati"]["affermazioni"].items():
            rv = V[v]["e6_risultati"]["affermazioni"][aff]; mx = max(mx, abs(rv["media"] - rc["media"])); n += 1
        for aff, rc in C["e6a_risultati"]["affermazioni"].items():
            rv = V[v]["e6a_risultati"]["affermazioni"][aff]; mx = max(mx, abs(rv["media"] - rc["media"])); n += 1
        for k, rc in C["e6bis_risultati"]["confronti"].items():
            rv = V[v]["e6bis_risultati"]["confronti"][k]; mx = max(mx, abs(rv["media"] - rc["media"])); n += 1
        for gr in ("PEMS08", "PEMS04"):
            for nome, z in C["e8_risultati"]["gruppi"].get(gr, {}).get("confronti", {}).items():
                zv = V[v]["e8_risultati"]["gruppi"].get(gr, {}).get("confronti", {}).get(nome)
                if zv and "wce" in z and "wce" in zv:
                    mx = max(mx, abs(zv["wce"]["media"] - z["wce"]["media"])); n += 1
        imp = {n_: (impronta(a.out / f"{n_}.json"), impronta(PROT / v / f"{n_}.json"))
               for n_ in ("e6_scelta_gated", "e6a_scelta_gated")}
        R["pems_controllo"][v] = {"confronti": n, "scarto_massimo_medie": mx, "impronte_scelte": imp}
        L.append(f"- ({v}): {n} confronti PEMS (E6, E6-bis, E6a, E8 PEMS08/PEMS04), scarto massimo sulle medie "
                 f"**{mx:.1e}** ({'zero' if mx == 0 else 'NON zero'}); scelte (τ, N) PEMS08/PEMS04: impronte "
                 + ", ".join(f"{k} {'uguali' if q[0] == q[1] else 'DIVERSE'}" for k, q in imp.items()) + ".")
    L.append("")

    # ---- 8. sintesi -------------------------------------------------------------------------------
    L.append("## 8. Sintesi\n")
    for v in vv:
        R["sintesi"][v] = {"dichiarazioni_valutate": n_tot[v], "sensibili": n_sens[v], "verdetti_cambiati": n_verd[v],
                           "stesso_segno_cambiati": n_33[v], "selezioni_cambiate": n_sel[v],
                           "soglie_e8_cambiate": n_sog[v], "e7_cambia": camb_e7[v], "e8_verdetti_cambiati": n_e8[v],
                           "altre_verdetti_cambiati": n_altre[v]}
        L.append(f"- **Variante ({v})**: dichiarazioni (a)–(e) valutate {n_tot[v]}, sensibili {n_sens[v]}, con verdetto cambiato "
                 f"**{n_verd[v]}**; letture 3/3 cambiate {n_33[v]} su {5 * len(CITTA)}; selezioni su validazione cambiate "
                 f"{n_sel[v]} su {len(CITTA) * 2 + 2}; soglie E8 cambiate {n_sog[v][0]} su {n_sog[v][1]}; E7 "
                 f"{'cambia' if camb_e7[v] else 'non cambia'}; E8/E8-bis verdetti cambiati {n_e8[v]}; altre dichiarazioni "
                 f"(E3, veterani, E3-bis, E4) con verdetto cambiato {n_altre[v][0]} su {n_altre[v][1]}.")
    L.append("")
    L.append("## 9. Impronte\n")
    for v in vv:
        L.append(f"- fascio ({v}): manifesto `{impronta(PROT / v / 'manifesto.json')}`, commit `{MAN[v]['commit']}`; "
                 + ", ".join(f"`{k}` {MAN[v]['file'][k]}" for k in ("e5_risultati.json", "e6_risultati.json", "e8_risultati.json",
                                                                    "e4_scelta_gated.json", "e8_soglie.json")))
    L.append("- congelati: " + ", ".join(f"`{n}` {impronta(a.out / f'{n}.json')}" for n in
                                        ("e5_risultati", "e6_risultati", "e6a_risultati", "e4_risultati", "e8_risultati", "e8bis_risultati",
                                         "e4_scelta_gated", "e8_soglie", "e7_stadio1"))
             + f", `e14b_livelli_congelata.json` {impronta(PROT / 'congelata' / 'e14b_livelli_congelata.json')}.")
    R["istante"] = datetime.now(timezone.utc).isoformat(); R["commit"] = commit
    fj = a.out / "congelamento_e14b.json"
    fj.write_text(json.dumps(R, indent=1, ensure_ascii=False))
    L.append(f"- `results/evoluzione/congelamento_e14b.json`: {impronta(fj)}.")
    Path("CONGELAMENTO_E14B.md").write_text("\n".join(L) + "\n")
    print(f"  CONGELAMENTO_E14B.md scritto (impronta {impronta(Path('CONGELAMENTO_E14B.md'))}); json {impronta(fj)}")
    for v in vv:
        print(f"  ({v}): " + json.dumps(R["sintesi"][v]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
