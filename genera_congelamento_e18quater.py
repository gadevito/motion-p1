#!/usr/bin/env python3
"""
CONGELAMENTO_E18QUATER.md e results/evoluzione/congelamento_e18quater.json da results/evoluzione/e18quater_risultati.json
(parte A: C_A con la coverage di valutazione dei nuovi uguale a quella di C) e results/evoluzione/e18quater_classi_risultati.json
(parte B: classi per sensore nei bersagli di prova). Ogni numero viene dai due json; nessun valore scritto a mano.
Dalla radice OR3/:  python3 genera_congelamento_e18quater.py
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("results/evoluzione")
CITTA = ("Madrid", "Londra", "Melbourne")
CTX = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")
DIFF_IT = {"C_A_esp-C_A": "C_A^esp − C_A (effetto della coverage)", "C_A_esp-C": "C_A^esp − C (effetto dei dati, pari coverage)",
           "A-C_A_esp": "A − C_A^esp", "A-C": "A − C (riferimento E15)", "A-C_A": "A − C_A (riferimento E15)", "C_A-C": "C_A − C (riferimento E15)"}
GRP_IT = {"iniziali": "iniziali", "nuovi": "nuovi", "validazione": "validazione"}


def imp(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def ic(v, dec=4):
    return f"{v['media']:+.{dec}f} [{v['ic_con_nodi'][0]:+.{dec}f}, {v['ic_con_nodi'][1]:+.{dec}f}]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    fa, fb = a.out / "e18quater_risultati.json", a.out / "e18quater_classi_risultati.json"
    A, B = json.loads(fa.read_text()), json.loads(fb.read_text())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    prot = Path("protocol/E18quater.md")
    L = ["# CONGELAMENTO E18-QUATER — coverage di valutazione di C_A e classi per sensore", "",
         f"Generato da `genera_congelamento_e18quater.py` al commit `{commit}`, {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
         f"Protocollo `protocol/E18quater.md` (nota datata del 3/11/2026; impronta `{imp(prot)}`); `e18quater_risultati.json` impronta "
         f"`{imp(fa)}`; `e18quater_classi_risultati.json` impronta `{imp(fb)}`. Nessun addestramento: parte A a modelli congelati di E15, parte B "
         "sola lettura dei bersagli.", "",
         "## 1. Parte A — C_A ri-valutato con la coverage dei sensori nuovi uguale a quella di C", "",
         f"Braccio `{A['braccio']}`; statica dei nuovi in valutazione «{A['statica_valutazione_nuovi']}» (E15: coverage su [0, t0) per A e C_A); "
         f"{A['repliche']} ricampionamenti congiunti (partizioni × semi × posizioni dei nodi), seme {A['seme_bootstrap']}, δ = {A['delta_non_inferiorita']}. "
         f"Perimetro: {A['perimetro']['principale']}; settimana = {A['perimetro']['settimana']}.", "",
         f"**Controlli bloccanti**: {A['controlli']['aggregati_C_A_riprodotti']}; medie dei riferimenti contro `e15_risultati.json` "
         f"(impronta `{A['impronte']['e15_risultati.json']}`): "
         + "; ".join(f"{k} {v}" for k, v in A["controlli"]["medie_riferimento_vs_e15"].items()) + ": superati.", "",
         "| citta' | differenza | media [IC 95 %] | segno | categoria | > 1 sett.: media [IC] | E15: media [IC] |", "|---|---|---|---|---|---|---|"]
    for c in CITTA:
        Rc = A["citta"][c]
        for k, et in DIFF_IT.items():
            d, s = Rc["differenze"][k], Rc["settimana"][k]
            e = d.get("e15")
            L.append(f"| {c} | {et} | {ic(d)} | {d['segno']} | {d['categoria']} | {ic(s)} | " + (ic(e) if e else "—") + " |")
    L += ["", "| citta' | celle | nodi | C | A | C_A | C_A^esp | quota del divario C_A − C dovuta alla coverage [IC] | repliche con C_A − C ≥ 0 |",
          "|---|---:|---:|---:|---:|---:|---:|---|---:|"]
    for c in CITTA:
        Rc = A["citta"][c]; lv = Rc["livelli"]; q = Rc["quota_coverage"]
        L.append(f"| {c} | {Rc['celle']} | {Rc['nodi']} | " + " | ".join(f"{lv[n]['media']:.4f}" for n in ("C", "A", "C_A", "C_A_esp"))
                 + f" | {q['media']:.3f} [{q['ic_con_nodi'][0]:.3f}, {q['ic_con_nodi'][1]:.3f}] | {q['repliche_den_senza_divario']} |")
    L += ["", f"Quota: {A['citta'][CITTA[0]]['quota_coverage']['definizione']}.", "",
          "## 2. Parte B — classi per sensore nei bersagli del periodo di prova", "",
          f"{B['definizione']}. Gruppi: iniziali = nodi di addestramento, nuovi = nodi di prova, validazione = nodi di validazione "
          "della partizione.", "",
          "| contesto | partizioni | sensori/part. | origini/part. | gruppo | coppie (part., sensore) | min | q1 | mediana | q3 | max | media | "
          "zero congestionati | senza bersagli | quota aggregata | frequenze (1, 2, 3) |", "|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for g in CTX:
        G = B["contesti"][g]
        for i, (grp, et) in enumerate(GRP_IT.items()):
            s = G["gruppi"][grp]
            L.append(f"| {g if i == 0 else ''} | {len(G['partizioni']) if i == 0 else ''} | {G['sensori_per_partizione'] if i == 0 else ''} | "
                     f"{'–'.join(str(x) for x in sorted(set(G['origini_per_partizione']))) if i == 0 else ''} | {et} | {s['n']} | "
                     + (f"{s['min']:.3f} | {s['q1']:.3f} | {s['mediana']:.3f} | {s['q3']:.3f} | {s['max']:.3f} | {s['media']:.3f} | {s['zero_congestionati']}"
                        if "min" in s else "— | — | — | — | — | — | —")
                     + f" | {s['senza_bersagli']} | {s['quota_congestionati_aggregata']:.3f} | {', '.join(f'{x:,}' for x in s['frequenze_classi'])} |")
    L += ["", "Finestre (passi di 15 min): " + "; ".join(f"{g}: t0 {B['contesti'][g]['finestra']['t0']}, t1 {B['contesti'][g]['finestra']['t1']}, "
                                                        f"fine {B['contesti'][g]['finestra']['fine']}" for g in CTX) + ".", "",
          "## 3. Note datate", "",
          "- 3/11/2026, parte A: ri-valutazione a modelli congelati; le medie e gli intervalli dei riferimenti A − C, A − C_A, C_A − C "
          "coincidono con E15 (stesse celle, stessi aggregati, stesse estrazioni del ricampionamento).",
          "- 3/11/2026, parte B: perimetro identico alle valutazioni (unita' di E8, `origini_dopo`); nessun numero del Paper 1 dipende "
          "da questa tabella, che descrive i bersagli.", ""]
    ingr = dict(A["impronte"]["celle_e15"]); ingr.update({f"ck_C_A/{k}": v for k, v in A["impronte"]["ck_C_A"].items()})
    ingr["e15_risultati.json"] = A["impronte"]["e15_risultati.json"]; ingr.update(B["impronte_ingressi"])
    fjo = a.out / "congelamento_e18quater.json"
    J = {"commit": commit, "istante": datetime.now(timezone.utc).isoformat(), "risultati": {"parte_A": A, "parte_B": B},
         "impronte": {"e18quater_risultati.json": imp(fa), "e18quater_classi_risultati.json": imp(fb), "protocol/E18quater.md": imp(prot),
                      "evoluzione/esperimenti/esegui_e18quater.py": imp(Path("evoluzione/esperimenti/esegui_e18quater.py")),
                      "evoluzione/analisi/classi_per_sensore.py": imp(Path("evoluzione/analisi/classi_per_sensore.py")),
                      "ingressi": {"file": len(ingr), "impronta_insieme": hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(ingr.items())).encode()).hexdigest()[:16]}}}
    fjo.write_text(json.dumps(J, indent=1, ensure_ascii=False))
    L += ["## 4. Impronte", "",
          f"- `results/evoluzione/e18quater_risultati.json` `{imp(fa)}`; `results/evoluzione/e18quater_classi_risultati.json` `{imp(fb)}`; "
          f"`protocol/E18quater.md` `{imp(prot)}`; `results/evoluzione/congelamento_e18quater.json` `{imp(fjo)}`.",
          f"- Ingressi: {len(ingr)} file (celle `predizioni_e15/prova_*.npz`, punti di controllo di C_A, `e15_risultati.json`, bersagli e "
          f"maschere dei contesti), insieme `{J['impronte']['ingressi']['impronta_insieme']}`.",
          f"- `evoluzione/esperimenti/esegui_e18quater.py` `{J['impronte']['evoluzione/esperimenti/esegui_e18quater.py']}`; "
          f"`evoluzione/analisi/classi_per_sensore.py` `{J['impronte']['evoluzione/analisi/classi_per_sensore.py']}`."]
    Path("CONGELAMENTO_E18QUATER.md").write_text("\n".join(L) + "\n")
    print(f"  CONGELAMENTO_E18QUATER.md (impronta {imp(Path('CONGELAMENTO_E18QUATER.md'))}); json {imp(fjo)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
