#!/usr/bin/env python3
"""
CONGELAMENTO_E16.md — calibrazione (protocol/E16.md).
=====================================================
Ogni numero viene da `results/evoluzione/e16_risultati.json` (`esegui_e16.py --fase analizza`) e dai
file che esso cita. Scrive `CONGELAMENTO_E16.md` e `results/evoluzione/congelamento_e16.json`.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e16.py
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

OUT = Path("results/evoluzione")
CITTA = ("Madrid", "Londra", "Melbourne")
NOMI = {"grezzo": "grezzo", "T_nll": "T (log-loss)", "T_wce": "T (wCE)", "V_nll": "vettore (log-loss)", "V_wce": "vettore (wCE)"}
BR = {"C": "C", "A": "A", "F0": "F₀", "F0p": "F₀′", "Fp_672": "F′(1 sett.)"}


def imp(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def ic(r, d=4):
    return f"{r['media']:+.{d}f} [{r['ic_con_nodi'][0]:+.{d}f}, {r['ic_con_nodi'][1]:+.{d}f}]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    fj = a.out / "e16_risultati.json"; R = json.loads(fj.read_text())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    gruppi = list(R["gruppi"])
    L = ["# CONGELAMENTO E16 — calibrazione", "",
         f"Generato da `genera_congelamento_e16.py` al commit `{commit}`, {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
         f"Protocollo `protocol/E16.md` (impronta `{imp(Path('protocol/E16.md'))}`), firmato prima di ogni numero. "
         f"`e16_risultati.json` impronta `{imp(fj)}`. Probabilita' per cella ricostruite dai punti di controllo della campagna "
         f"(`esegui_e16.py --fase predizioni`, `--statica congelata`, stesso `_modelli` di E8, controllo bloccante sugli aggregati "
         f"congelati ≤ 1e-6) su validazione e prova: citta' episodio 1 (36 celle) e PEMS08 (36 celle). Calibrazione post-hoc stimata "
         f"SOLO sulla validazione della stessa cella, una per braccio e cella: temperature scaling e vector scaling (W diagonale + b), "
         f"obiettivi log-loss non pesata e wCE (posteriore ripesato), riportati separatamente. {R['repliche']} ricampionamenti "
         f"congiunti (schema di E4), seme {R['seme_bootstrap']}; {R['bin']} intervalli di affidabilita'.", "",
         f"**Deviazione dichiarata**: {R['nota_A']}; le differenze «A − C» dopo calibrazione usano A grezza e C calibrata.", ""]

    # 1. quota di calibrazione
    L += ["## 1. Quota di calibrazione s = 1 − (F₀ᶜᵃˡ − Cᶜᵃˡ)/(F₀ − C)", "",
          "Criterio (E16): «calibration first, discrimination second» resta solo se il limite inferiore di s supera 0,5 in tutte "
          "e tre le citta'; PEMS08 si riporta («calibration alone» esce in ogni caso).", "",
          "| gruppo | " + " | ".join(NOMI[c] for c in R["calibrazioni"]) + " |", "|---|" + "---|" * len(R["calibrazioni"])]
    crit = {cal: all(R["gruppi"][c]["quota_calibrazione"][cal]["limite_inferiore_sopra_0.5"] for c in CITTA if c in R["gruppi"]) for cal in R["calibrazioni"]}
    for g in gruppi:
        Q = R["gruppi"][g]["quota_calibrazione"]
        L.append(f"| {g} | " + " | ".join(f"{Q[c]['media']:.3f} [{Q[c]['ic_con_nodi'][0]:.3f}, {Q[c]['ic_con_nodi'][1]:.3f}]" for c in R["calibrazioni"]) + " |")
    L += ["", "Limite inferiore > 0,5 in tutte e tre le citta': " + ", ".join(f"{NOMI[c]} **{'si' if v else 'no'}**" for c, v in crit.items()) + ".", ""]

    # 2. wCE e differenze prima/dopo
    L += ["## 2. wCE sul test e differenze fra bracci, prima e dopo la calibrazione", ""]
    for g in gruppi:
        G = R["gruppi"][g]
        L += [f"### {g} ({G['celle']} celle)", "",
              "| braccio | " + " | ".join(NOMI[c] for c in ("grezzo",) + tuple(R["calibrazioni"])) + " |", "|---|" + "---|" * 5]
        for b in ("C", "A", "F0", "F0p", "Fp_672"):
            if f"{b}/grezzo" not in G["wce"]:
                continue
            L.append(f"| {BR[b]} | " + " | ".join(f"{G['wce'][f'{b}/{c}']['media']:.4f}" if f"{b}/{c}" in G["wce"] else "—" for c in ("grezzo",) + tuple(R["calibrazioni"])) + " |")
        L += ["", "| differenza | " + " | ".join(NOMI[c] for c in ("grezzo",) + tuple(R["calibrazioni"])) + " |", "|---|" + "---|" * 5]
        for d in ("F0-C", "F0p-C", "Fp_672-C", "A-C", "F0p-F0"):
            riga = []
            for c in ("grezzo",) + tuple(R["calibrazioni"]):
                z = G["differenze"].get(f"{d}/{c}")
                riga.append(f"{ic(z)} {z['segno']}" if z else "—")
            n1, n2 = d.split("-")
            L.append(f"| {BR[n1]} − {BR[n2]} | " + " | ".join(riga) + " |")
        L.append("")

    # 3. metriche di calibrazione
    L += ["## 3. ECE per classe, log-loss non pesata, Brier (medie sulle celle del test)", ""]
    for g in gruppi:
        G = R["gruppi"][g]
        L += [f"### {g}", "", "| braccio / calibrazione | ECE verde | ECE gialla | ECE rossa | log-loss | Brier | wCE |", "|---|---|---|---|---|---|---|"]
        for k in sorted(G["medie_test"], key=lambda z: (list(BR).index(z.split("/")[0]), list(NOMI).index(z.split("/")[1]))):
            m = G["medie_test"][k]; b, c = k.split("/")
            L.append(f"| {BR[b]} / {NOMI[c]} | {m['ece']['0']:.4f} | {m['ece']['1']:.4f} | {m['ece']['2']:.4f} | {m['logloss']:.4f} | {m['brier']:.4f} | {m['wce']:.4f} |")
        L.append("")

    # 4. temperature
    L += ["## 4. Temperature stimate sulla validazione (mediana e intervallo min–max sulle celle)", "",
          "| gruppo | braccio | T (log-loss) | T (wCE) |", "|---|---|---|---|"]
    for g in gruppi:
        for b in ("C", "F0", "F0p", "Fp_672"):
            Ts = {cal: [v["parametri"][f"{b}/{cal}"]["T"] for k, v in R["per_cella"].items() if v["gruppo"] == g and f"{b}/{cal}" in v["parametri"]]
                  for cal in ("T_nll", "T_wce")}
            if Ts["T_nll"]:
                L.append(f"| {g} | {BR[b]} | " + " | ".join(f"{np.median(Ts[c]):.3f} [{min(Ts[c]):.3f}, {max(Ts[c]):.3f}]" for c in ("T_nll", "T_wce")) + " |")
    L.append("")
    L += ["## 5. Impronte", "",
          f"- `results/evoluzione/e16_risultati.json` `{imp(fj)}`; `protocol/E16.md` `{imp(Path('protocol/E16.md'))}`; "
          f"`evoluzione/esperimenti/esegui_e16.py` `{imp(Path('evoluzione/esperimenti/esegui_e16.py'))}`."]
    J = {"commit": commit, "istante": datetime.now(timezone.utc).isoformat(), "criterio_s": crit,
         "gruppi": R["gruppi"], "impronte": {"e16_risultati.json": imp(fj), "protocol/E16.md": imp(Path("protocol/E16.md"))}}
    (a.out / "congelamento_e16.json").write_text(json.dumps(J, indent=1, ensure_ascii=False))
    L.append(f"- `results/evoluzione/congelamento_e16.json` `{imp(a.out / 'congelamento_e16.json')}`.")
    Path("CONGELAMENTO_E16.md").write_text("\n".join(L) + "\n")
    print(f"  CONGELAMENTO_E16.md (impronta {imp(Path('CONGELAMENTO_E16.md'))}); json {imp(a.out / 'congelamento_e16.json')}")
    print("  criterio s (limite inferiore > 0,5 in tutte le citta'): " + json.dumps(crit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
