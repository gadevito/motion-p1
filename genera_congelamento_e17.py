#!/usr/bin/env python3
"""
CONGELAMENTO_E17.md — politica integrata, categorie, recupero, margine minimo (protocol/E17.md).
================================================================================================
Ogni numero viene da `results/evoluzione/e17_risultati.json` (prodotto da `analizza_e17.py`) e dai
json congelati che esso cita. Scrive `CONGELAMENTO_E17.md` e `results/evoluzione/congelamento_e17.json`.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e17.py
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("results/evoluzione")
CITTA = ("Madrid", "Londra", "Melbourne")


def imp(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def ic(r):
    return f"{r['media']:+.4f} [{r['ic_con_nodi'][0]:+.4f}, {r['ic_con_nodi'][1]:+.4f}]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    fj = a.out / "e17_risultati.json"
    R = json.loads(fj.read_text())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    L = ["# CONGELAMENTO E17 — politica integrata, categorie di verdetto, recupero, margine minimo", "",
         f"Generato da `genera_congelamento_e17.py` al commit `{commit}`, {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
         f"Protocollo `protocol/E17.md` (impronta `{imp(Path('protocol/E17.md'))}`), firmato prima di ogni numero. Sola analisi dalle "
         f"predizioni per cella della campagna congelata (statica non causale, difetto 21 dichiarato) e dai json congelati; "
         f"`e17_risultati.json` impronta `{imp(fj)}`; {R['repliche']} ricampionamenti congiunti (partizioni × semi × sensori, "
         f"schema di E4), seme {R['seme_bootstrap']}.", ""]
    L += [f"**Categorie** (E17): *superiorita'* = limite superiore dell'intervallo < 0; *non inferiorita'* = limite superiore "
          f"< δ = {R['delta_non_inferiorita']} wCE (meta' del piu' piccolo effetto trattato come rilevante); *inconclusivo* altrimenti.", ""]

    # 1. politica
    L += ["## 1. Politica integrata gated(1 sett., 0) come politica completa", "",
          f"{R['politica_definizione']}. wCE integrata su tutte le origini dopo t₁; episodi 2 e 3 non l'hanno formulata, "
          "l'episodio 1 e' il riferimento; PEMS08 e PEMS04 righe aggiuntive.", "",
          "| contesto | celle | (τ, N) selezionata | gated(1 sett., 0) − F₀′ | categoria | gated(1 sett., 0) − gated(τ, N) | gated(1 sett., 0) − C | wCE gated(1 sett., 0) | wCE F₀′ | wCE gated(τ, N) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    n_sup = n_ni = 0
    for k, P in R["politica"].items():
        g = P["confronti"]; lv = P["livelli"]
        cat = g["gated672_0-F0p"]["categoria"]; n_sup += cat == "superiorita'"; n_ni += cat == "non inferiorita'"
        L.append(f"| {k} | {P['celle']} | τ={'mai' if P['tau_sel'] is None else P['tau_sel']}, N={P['N_sel']} | {ic(g['gated672_0-F0p'])} | {cat} | "
                 f"{ic(g['gated672_0-gated_sel'])} | {ic(g['gated672_0-C'])} | {lv['gated672_0']['media']:.4f} | {lv['F0p']['media']:.4f} | {lv['gated_sel']['media']:.4f} |")
    L += ["", f"gated(1 sett., 0) − F₀′: superiorita' in {n_sup}, non inferiorita' in {n_ni}, inconclusivo in "
              f"{len(R['politica']) - n_sup - n_ni} contesti su {len(R['politica'])}.", ""]

    # 2. categorie
    L += ["## 2. Categorie dei verdetti congelati", "",
          "### 2a. gated(τ, N) − F₀′ negli 11 contesti", "",
          "| contesto | valore [IC 95 %] | categoria | fonte |", "|---|---|---|---|"]
    conta = {}
    for k, z in R["categorie"]["gated_sel-F0p"].items():
        conta[z["categoria"]] = conta.get(z["categoria"], 0) + 1
        L.append(f"| {k} | {ic(z)} | {z['categoria']} | `{z['fonte']}` |")
    L += ["", "Totale: " + ", ".join(f"{v} {k}" for k, v in conta.items()) + ".", "",
          "### 2b. R-orig(1 sett.) − F′(1 sett.), origini con eta' > 1 settimana", "",
          "| contesto | valore [IC 95 %] | categoria | fonte |", "|---|---|---|---|"]
    for k, z in R["categorie"]["Rorig_672-Fp_672"].items():
        L.append(f"| {k} | {ic(z)} | {z['categoria']} | `{z['fonte']}` |")
    L.append("")

    # 3. recupero
    L += ["## 3. Recupero del divario C → A da F′(1 sett.)", "",
          "(L_C − L_F′(1 sett.)) / (L_C − L_A) sulle stesse origini (eta' > 1 settimana); intervallo = rapporto delle medie "
          "nella stessa replica.", "",
          "| contesto | L_C | L_F′(1 sett.) | L_A | recupero [IC 95 %] | repliche con denominatore ≤ 0 |", "|---|---|---|---|---|---|"]
    for k, z in R["recupero"].items():
        L.append(f"| {k} | {z['L_C']:.4f} | {z['L_Fp_672']:.4f} | {z['L_A']:.4f} | "
                 f"{z['media']:.3f} [{z['ic_con_nodi'][0]:.3f}, {z['ic_con_nodi'][1]:.3f}] | {z['repliche_den_non_positivo']} |")
    L.append("")

    # 4. margine minimo
    L += ["## 4. Margine minimo di equivalenza (TOST) per R-orig(1 sett.) ≡ F′(1 sett.)", "",
          "Il piu' piccolo δ a cui l'intervallo al 95 % della differenza sta in (−δ, δ): max(|lo|, |hi|). E3-bis usava "
          "±3 % del livello di F′(1 sett.) (colonna «margine ±3 %», dove registrato).", "",
          "| contesto | δ minimo (wCE) | margine ±3 % di E3-bis | fonte |", "|---|---|---|---|"]
    for k, z in R["margine_minimo"].items():
        m3 = z.get("margine_3pc_e3bis")
        L.append(f"| {k} | {z['delta_min']:.4f} | {('%.4f' % m3) if isinstance(m3, (int, float)) else '—'} | `{z['fonte']}` |")
    L.append("")
    L += ["## 5. Impronte", "",
          f"- `results/evoluzione/e17_risultati.json` `{imp(fj)}`; `protocol/E17.md` `{imp(Path('protocol/E17.md'))}`.",
          "- Ingressi: " + ", ".join(f"`{n}` `{imp(a.out / n)}`" for n in ("e5_risultati.json", "e6_risultati.json", "e6a_risultati.json",
                                                                       "e3bis_risultati.json", "e4_scelta_gated.json", "e6_scelta_gated.json",
                                                                       "e6a_scelta_gated.json")) + "."]
    J = {"commit": commit, "istante": datetime.now(timezone.utc).isoformat(), "risultati": R,
         "impronte": {"e17_risultati.json": imp(fj), "protocol/E17.md": imp(Path("protocol/E17.md"))}}
    (a.out / "congelamento_e17.json").write_text(json.dumps(J, indent=1, ensure_ascii=False))
    L.append(f"- `results/evoluzione/congelamento_e17.json` `{imp(a.out / 'congelamento_e17.json')}`.")
    Path("CONGELAMENTO_E17.md").write_text("\n".join(L) + "\n")
    print(f"  CONGELAMENTO_E17.md (impronta {imp(Path('CONGELAMENTO_E17.md'))}); json {imp(a.out / 'congelamento_e17.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
