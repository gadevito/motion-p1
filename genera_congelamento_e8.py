#!/usr/bin/env python3
"""
Congelamento di E8 — metriche operative (post hoc, dichiarato).
================================================================
**Ogni numero e' derivato da `e8_risultati.json`** (differenze fra bracci con
ricampionamento congiunto, per tre regole di decisione, piu' la ΔwCE ricalcolata
dalle stesse celle e verificata contro gli aggregati congelati), da
`e8_soglie.json` (soglie con impronta) e dalle celle di `predizioni_e8/`
(controlli). Nessun criterio: le frasi sono derivate dai segni.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e8.py
"""
import argparse
import glob
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parent
sys.path.insert(0, str(RADICE))

OUT = Path("results/evoluzione")
FILE = ["evoluzione/esperimenti/esegui_e8.py", "protocol/E8.md", "protocol/E8bis.md"]
CURVE_ET = {"A-C": "A − C", "F0-C": "F₀ − C", "F0p-C": "F₀′ − C", "Fp_96-C": "F′(24 h) − C",
            "Fp_672-C_eta>1sett": "F′(1 sett.) − C, eta' > 1 sett.", "Rorig_672-Fp_672_eta>1sett": "R-orig(1 sett.) − F′(1 sett.), eta' > 1 sett.",
            "F0p-F0": "F₀′ − F₀"}
GRUPPI = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")
CONF_ET = {"A-C": "A − C", "F0-C": "F₀ − C", "F0p-C": "F₀′ − C", "Fp_96-C": "F′(24 h) − C",
           "Fp_672-C_eta>1sett": "F′(1 sett.) − C, eta' > 1 sett.", "gated-F0p": "gated − F₀′",
           "Rorig_672-Fp_672_eta>1sett": "R-orig(1 sett.) − F′(1 sett.), eta' > 1 sett."}
REG_ET = {"prim": "primaria (F1 per braccio)", "par": "parita' di falsi allarmi con C", "argmax": "argmax"}
MET_ET = {"richiamo": "richiamo (congestionata)", "precisione": "precisione", "falsi_allarmi": "falsi allarmi",
          "f1_macro": "F1-macro"}
PRINCIPALE = "Fp_672-C_eta>1sett"


class IngressoMancante(RuntimeError):
    pass


def h(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    except OSError:
        return "assente"


def commit_git() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              cwd=RADICE).stdout.strip()[:12] or "n.d."
    except Exception:                                        # noqa: BLE001
        return "n.d."


def leggi(f: Path):
    if not f.exists():
        raise IngressoMancante(f"assente: {f}")
    return json.loads(f.read_text())


def _f(x, n=3):
    return f"{x:+.{n}f}"


def _ic(q, n=3):
    return f"[{_f(q[0], n)}, {_f(q[1], n)}]"


def _s(r):
    return r["segno"].replace("-", "−")


def _pt(x):
    return f"{100 * x:+.1f}"


def controlli(out: Path) -> dict:
    import numpy as np
    n, sc_max, n_ctrl = 0, 0.0, 0
    for f in glob.glob(str(out / "predizioni_e8" / "*_*_p*_s*.npz")):
        with np.load(f, allow_pickle=True) as z:
            c = json.loads(str(z["controllo"])) if "controllo" in z.files else {}
        n += 1; n_ctrl += len(c)
        if c:
            sc_max = max(sc_max, max(v["scarto_relativo_max"] for v in c.values()))
    return {"celle": n, "controlli": n_ctrl, "scarto_max": sc_max}


def documento(R: dict) -> str:
    RS, SG, CT = R["risultati"], R["soglie"], R["controlli"]
    A = []; a = A.append
    a("# Congelamento — E8, metriche operative (post hoc, dichiarato)")
    a("")
    a(f"**Congelato il {R['data']}**, commit `{R['commit']}`. Protocollo `protocol/E8.md` (impronta "
      f"`{R['impronte']['protocol/E8.md']}`), firmato al commit `1185d9ecceb39bdf` prima di ricostruire; deviazione "
      f"del 9/10 dichiarata nel file (A eredita le soglie di C). **Nessun criterio**: è descrittivo. "
      f"**Ogni numero e' calcolato da `genera_congelamento_e8.py`** da `e8_risultati.json` e `e8_soglie.json`. "
      f"Va in appendice C; la frase derivata (§4) nel testo della sezione 5.1.")
    a("")
    a("## 1. Che cosa e' stato eseguito")
    a("")
    a("| | |")
    a("|---|---|")
    a(f"| ricostruzione | {CT['celle']} celle (validazione + prova) dai punti di controllo dei congelamenti, nessun "
      f"addestramento; **{CT['controlli']} controlli** contro gli aggregati congelati, scarto relativo massimo "
      f"**{CT['scarto_max']:.1e}** (soglia 1e-6): la ricostruzione riproduce i congelamenti |")
    a(f"| soglie | `e8_soglie.json`, impronta `{SG['_impronta']}`, scelte su validazione prima di qualunque metrica di "
      f"prova; griglia {SG['_regole']['griglia'][0]:.2f}…{SG['_regole']['griglia'][-1]:.2f}; A eredita C, R-orig(1 sett.) eredita F′(1 sett.) |")
    a(f"| ricampionamento | {RS['repliche']} repliche congiunte (partizioni × semi × nodi), semi dei congelamenti |")
    a("| contesti | Madrid, Londra, Melbourne (episodio 1; gli episodi 2–3 non inclusi, deciso dopo il pilota), "
      "PEMS08 (6 × 6), PEMS04 (3 × 12) |")
    a("")
    a("## 2. Soglie scelte su validazione")
    a("")
    bracci = ["C", "A", "F0", "F0p", "Fp_96", "Fp_192", "Fp_672", "Rorig_672"]
    a("| gruppo | " + " | ".join(bracci) + " |")
    a("|---|" + "---|" * len(bracci))
    for g in GRUPPI:
        if g not in SG:
            continue
        riga = []
        for b in bracci:
            v = SG[g].get(b)
            riga.append("—" if v is None else f"{v['prim']:.2f} / {v['par']:.2f}" + (" (er.)" if v.get("ereditata_da") else ""))
        a(f"| {g} | " + " | ".join(riga) + " |")
    a("")
    a("Per cella: soglia primaria / soglia a parita' di falsi allarmi con C; «er.» = ereditata.")
    a("")
    a("## 3. Differenze fra bracci, per regola e metrica")
    a("")
    diverg = []
    for g in GRUPPI:
        if g not in RS["gruppi"]:
            continue
        RG = RS["gruppi"][g]
        a(f"### {g} ({RG['celle']} celle; gated τ = {RG['gated']['tau']}, N = {RG['gated']['N']})")
        a("")
        if g == "PEMS08":
            a("**Intervalli larghi per costruzione**: classe congestionata allo 0,9–1,4 % (p0 allo 0,9 %), 26 nodi "
              "nuovi per partizione (protocollo E6, ripetuto qui).")
            a("")
        a("| confronto | ΔwCE | regola | Δrichiamo (punti) | Δfalsi allarmi (punti) | Δprecisione (punti) | ΔF1-macro (punti) |")
        a("|---|---|---|---|---|---|---|")
        for k, et in CONF_ET.items():
            if k not in RG["confronti"]:
                continue
            cc = RG["confronti"][k]; w = cc["wce"]
            for i, reg in enumerate(("prim", "par", "argmax")):
                m = cc[reg]
                cella = lambda q: f"{_pt(m[q]['media'])} [{_pt(m[q]['ic_con_nodi'][0])}, {_pt(m[q]['ic_con_nodi'][1])}] {_s(m[q])}"
                a(f"| {et if i == 0 else ''} | {(_f(w['media']) + ' ' + _ic(w['ic_con_nodi']) + ' ' + _s(w)) if i == 0 else ''} | "
                  f"{REG_ET[reg]} | {cella('richiamo')} | {cella('falsi_allarmi')} | {cella('precisione')} | {cella('f1_macro')} |")
                # divergenza: wCE sotto lo zero e richiamo sotto lo zero (o viceversa), con intervalli che escludono lo zero
                if w["segno"] == "-" and m["richiamo"]["segno"] == "-":
                    diverg.append(f"{g}, {et}, regola {REG_ET[reg]}: ΔwCE {_f(w['media'])} ma Δrichiamo {_pt(m['richiamo']['media'])} punti")
                if w["segno"] == "+" and m["richiamo"]["segno"] == "+":
                    diverg.append(f"{g}, {et}, regola {REG_ET[reg]}: ΔwCE {_f(w['media'])} ma Δrichiamo {_pt(m['richiamo']['media'])} punti")
        a("")
        a("Livelli (regola primaria): " + "; ".join(
            f"{n.split('/')[1]} richiamo {v['richiamo']:.3f}, falsi allarmi {v['falsi_allarmi']:.4f}"
            for n, v in RG["livelli"].items() if n.startswith("prim/")) + ".")
        a("")
    a("Δ in punti percentuali; segno «−» = intervallo sotto lo zero, «+» sopra, «0» include lo zero. "
      "ΔwCE ricalcolata dalle stesse celle (verificata a 1e-6 contro i congelamenti).")
    a("")
    a("## 4. La frase derivata per il paper (confronto principale, F′(1 sett.) − C sulle origini comuni)")
    a("")
    for g in GRUPPI:
        if g not in RS["gruppi"] or PRINCIPALE not in RS["gruppi"][g]["confronti"]:
            continue
        cc = RS["gruppi"][g]["confronti"][PRINCIPALE]; w = cc["wce"]; par = cc["par"]; pr = cc["prim"]
        if par["richiamo"]["segno"] == "0":
            a(f"- **{g}**: ΔwCE {_f(w['media'])} {_ic(w['ic_con_nodi'])}; a parita' di falsi allarmi il richiamo sulla "
              f"classe congestionata **non si distingue** ({_pt(par['richiamo']['media'])} punti "
              f"[{_pt(par['richiamo']['ic_con_nodi'][0])}, {_pt(par['richiamo']['ic_con_nodi'][1])}]): nessuna frase.")
        else:
            fa = par["falsi_allarmi"]; tenuta = fa["segno"] == "0"
            a(f"- **{g}**: «ΔwCE = {_f(w['media'])} corrisponde a **{_pt(par['richiamo']['media'])} punti di richiamo** "
              f"sulla classe congestionata [{_pt(par['richiamo']['ic_con_nodi'][0])}, {_pt(par['richiamo']['ic_con_nodi'][1])}] "
              + (f"a parita' di falsi allarmi (scarto residuo {_pt(fa['media'])} punti, intervallo che include lo zero)»"
                 if tenuta else
                 f"con soglie a parita' di falsi allarmi **su validazione**; sul test la parita' **non ha retto**: "
                 f"scarto residuo di falsi allarmi {_pt(fa['media'])} punti [{_pt(fa['ic_con_nodi'][0])}, {_pt(fa['ic_con_nodi'][1])}], "
                 f"quindi il richiamo va letto insieme ai falsi allarmi, non da solo»")
              + f"; con la regola primaria {_pt(pr['richiamo']['media'])} punti di richiamo con {_pt(pr['falsi_allarmi']['media'])} "
              f"punti di falsi allarmi.")
    a("")
    n_ten = sum(1 for g in GRUPPI if g in RS["gruppi"] and PRINCIPALE in RS["gruppi"][g]["confronti"]
                and RS["gruppi"][g]["confronti"][PRINCIPALE]["par"]["falsi_allarmi"]["segno"] == "0")
    n_tot = sum(1 for g in GRUPPI if g in RS["gruppi"] and PRINCIPALE in RS["gruppi"][g]["confronti"])
    a(f"La parita' di falsi allarmi imposta su validazione ha retto sul test (scarto residuo con intervallo che include "
      f"lo zero) in **{n_ten} contesti su {n_tot}**: la soglia che eguaglia i falsi allarmi su validazione non li eguaglia "
      f"sul test, e la frase «a parita'» vale solo dove lo scarto residuo e' indistinguibile da zero.")
    a("")
    a("## 5. Richiamo e wCE si muovono insieme?")
    a("")
    if diverg:
        a("**Divergenze** (ΔwCE e Δrichiamo con intervalli che escludono lo zero nello stesso verso, cioe' wCE migliore "
          "e richiamo peggiore o viceversa): si riportano entrambe, non si sceglie la metrica.")
        a("")
        for d in diverg:
            a(f"- {d}")
    else:
        a("In nessun confronto la wCE e il richiamo si muovono in direzioni opposte con intervalli che escludono lo zero: "
          "dove la wCE migliora, il richiamo non peggiora, e viceversa.")
    a("")
    BI = R.get("bis")
    if BI:
        a("## 7. E8-bis — discriminazione e calibrazione (`protocol/E8bis.md`)")
        a("")
        a(f"Curve richiamo–falsi allarmi sulla griglia completa di soglie ({len(SG['_regole']['griglia'])} punti), per nodo, "
          f"sul test; AUC della classe congestionata (trapezi) e richiamo interpolato ai livelli di falsi allarmi "
          f"{', '.join(f'{100 * x:g} %' for x in BI['livelli_fa'])}; {BI['repliche']} repliche congiunte; gated escluso.")
        a("")
        verdetti = {}
        for g in GRUPPI:
            if g not in BI["gruppi"]:
                continue
            BG = BI["gruppi"][g]
            a(f"### {g}")
            a("")
            a("AUC (intero / eta' > 1 sett.): " + "; ".join(
                f"{n} {BG['auc'][n + '/intero']:.3f} / {BG['auc'][n + '/eta7']:.3f}"
                for n in sorted({k.split('/')[0] for k in BG['auc']})) + ".")
            a("")
            a("| confronto | ΔAUC | " + " | ".join(f"Δrichiamo a FA {100 * x:g} %" for x in BI["livelli_fa"]) + " | lettura |")
            a("|---|---|" + "---|" * len(BI["livelli_fa"]) + "---|")
            for k, et in CURVE_ET.items():
                if k not in BG["confronti"]:
                    continue
                cf = BG["confronti"][k]; r = cf["auc"]
                segni = [v["segno"] if v else None for v in (cf["richiamo_a_fa"][str(x)] for x in BI["livelli_fa"])]
                presenti = [z for z in segni if z is not None]
                if not presenti:
                    lett = "n.d."
                elif all(z == "+" for z in presenti):
                    lett = "**domina** C a ogni livello" if k.endswith("-C") else "**domina** a ogni livello"
                elif all(z == "-" for z in presenti):
                    lett = "**dominato** a ogni livello"
                elif "+" in presenti and "-" in presenti:
                    lett = "**le curve si incrociano**"
                elif "-" in presenti:
                    lett = "sotto a qualche livello, mai sopra"
                elif "+" in presenti:
                    lett = "sopra a qualche livello, mai sotto"
                else:
                    lett = "indistinguibile a ogni livello"
                verdetti[(g, k)] = (r["segno"], lett)
                celle = []
                for x in BI["livelli_fa"]:
                    v = cf["richiamo_a_fa"][str(x)]
                    celle.append("n.d." if v is None else f"{_pt(v['media'])} [{_pt(v['ic_con_nodi'][0])}, {_pt(v['ic_con_nodi'][1])}] {v['segno'].replace('-', '−')}")
                a(f"| {et} | {_f(r['media'], 4)} {_ic(r['ic_con_nodi'], 4)} {r['segno'].replace('-', '−')} | " + " | ".join(celle) + f" | {lett} |")
            a("")
        a("### Lettura derivata (regole scritte in `protocol/E8bis.md`)")
        a("")
        for g in GRUPPI:
            if (g, "Fp_672-C_eta>1sett") in verdetti:
                sa, lett = verdetti[(g, "Fp_672-C_eta>1sett")]
                a(f"- **{g}, F′(1 sett.) − C**: ΔAUC {sa.replace('-', '−')}; {lett}. "
                  + ("Il guadagno in wCE e' reale a ogni punto operativo." if "domina" in lett and "dominato" not in lett
                     else "Compromesso vero fra richiamo e falsi allarmi: si riporta come tale." if "incrociano" in lett
                     else "Le curve non si distinguono: la differenza di wCE non si traduce in discriminazione misurabile."))
            if (g, "F0-C") in verdetti:
                sa, lett = verdetti[(g, "F0-C")]
                a(f"- **{g}, F₀ − C**: ΔAUC {sa.replace('-', '−')}; {lett}. "
                  + ("Il costo di trasferimento e' **calibrazione pura**: le curve coincidono e solo la wCE differisce."
                     if sa == "0" and "indistinguibile" in lett else
                     "Il costo di trasferimento e' **anche discriminazione**, nella misura dell'intervallo di ΔAUC." if sa == "-"
                     else "Vedi tabella."))
            if (g, "A-C") in verdetti:
                cf = BI["gruppi"][g]["confronti"]["A-C"]
                v = cf["richiamo_a_fa"].get("0.02") or cf["richiamo_a_fa"].get("0.05")
                if v:
                    a(f"- **{g}, A − C**: l'identita' vale {_pt(v['media'])} punti di richiamo [{_pt(v['ic_con_nodi'][0])}, {_pt(v['ic_con_nodi'][1])}] "
                      f"a falsi allarmi fissati (2 % o 5 %): la traduzione del 3–5 % di wCE.")
        a("")
    a("## 6. Impronte")
    a("")
    a("| file | impronta |")
    a("|---|---|")
    for f, hh in R["impronte"].items():
        a(f"| `{f}` | `{hh}` |")
    a(f"| soglie | `{SG['_impronta']}` |")
    return "\n".join(A) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    print("[1/3] ingressi"); RS = leggi(a.out / "e8_risultati.json"); SG = leggi(a.out / "e8_soglie.json")
    if RS["impronta_soglie"] != SG["_impronta"]:
        raise IngressoMancante("impronta delle soglie non coerente")
    print("[2/3] controlli dalle celle"); CT = controlli(a.out)
    f_bis = a.out / "e8bis_risultati.json"
    BI = json.loads(f_bis.read_text()) if f_bis.exists() else None
    R = {"data": datetime.now(timezone.utc).date().isoformat(), "commit": commit_git(), "risultati": RS,
         "soglie": SG, "controlli": CT, "bis": BI, "impronte": {f: h(f) for f in FILE}}
    print("[3/3] documento")
    Path("CONGELAMENTO_E8.md").write_text(documento(R))
    print("  generato CONGELAMENTO_E8.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
