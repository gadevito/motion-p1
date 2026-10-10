#!/usr/bin/env python3
"""
Costi appaiati per contesto: F′(1 sett.) contro R-orig(1 sett.), stessa macchina.
==================================================================================
Il 2268 s di R-orig(1 sett.) in `costi_e3bis.json` e' la **mediana sulle nove
celle delle tre citta'** (partizione 0, semi 201-203), non il tempo di una
citta'; e in `costi_e4.json` F′(1 sett.) e' misurato in isolamento solo dove
tau = 672 (Melbourne). Qui la tabella si rifa' appaiata:

    F′(24 h), F′(1 sett.)   rimisurate ORA in isolamento (un processo, macchina
                            scarica) in tutte e tre le citta', con `_misura` di
                            `costi_e4.py`: ogni wCE deve riprodurre la fase
                            `valuta` di E4 entro 1e-6 relativo;
    R-orig(1 sett.)         dai manifesti isolati di E3-bis
                            (`inserimento_griglia_672/R-orig_*_p0_s20x.json`),
                            mediana per citta'; la mediana sulle nove celle
                            deve coincidere con `costi_e3bis.json`;
    PEMS08                  da `e6_costi.json` (R-orig_672, Fp_672), gia' isolati.

Scrive `results/evoluzione/costi_appaiati.json` e `paper/tabella_costi_appaiati.md`
(tabella con le impronte degli ingressi e del json). Nessun numero e' trascritto.

Uso (dalla radice OR3/, macchina scarica):

    poetry run python evoluzione/esperimenti/costi_appaiati.py --piano
    poetry run python evoluzione/esperimenti/costi_appaiati.py
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

from evoluzione.esperimenti.costi_e4 import _misura  # noqa: E402
from evoluzione.esperimenti.esegui_e4 import CITTA  # noqa: E402
from evoluzione.esperimenti.esegui_inserimento import ISOLATO  # noqa: E402

SETTIMANA = 672
DIR_RORIG = "inserimento_griglia_672"


def h(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _manifesti_rorig(out: Path):
    """I manifesti isolati di R-orig(1 sett.), per citta'."""
    per = {}
    for c in CITTA:
        for s in ISOLATO["semi"]:
            f = out / DIR_RORIG / f"R-orig_{c}_p{ISOLATO['partizione']}_s{s}.json"
            d = json.loads(f.read_text())
            if d.get("modalita_misura") != "isolata" or "rimisura_di" not in d:
                raise RuntimeError(f"{f.name}: non e' una rimisura isolata")
            if d["tempo_disponibilita"]["attesa_dati_s"] != SETTIMANA * 900:
                raise RuntimeError(f"{f.name}: attesa dati {d['tempo_disponibilita']['attesa_dati_s']} s")
            per.setdefault(c, []).append({"file": str(f.relative_to(out)), "seme": s,
                                          "inserimento_s": d["costo"]["inserimento_s"]})
    return per


def main() -> int:
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    a = ap.parse_args()
    med = lambda v: float(np.median(v))  # noqa: E731
    ingressi = {k: a.out / k for k in ("costi_e3bis.json", "costi_e4.json", "e6_costi.json")}
    K3 = json.loads(ingressi["costi_e3bis.json"].read_text())
    K4 = json.loads(ingressi["costi_e4.json"].read_text())
    K6 = json.loads(ingressi["e6_costi.json"].read_text())
    RO = _manifesti_rorig(a.out)
    tutte = [m["inserimento_s"] for c in CITTA for m in RO[c]]
    glob = med(tutte)
    if abs(glob - K3["R-orig"]["inserimento_s"]) > 1e-9:
        raise RuntimeError(f"mediana sulle 9 celle {glob:.1f} s diversa da costi_e3bis.json "
                           f"{K3['R-orig']['inserimento_s']:.1f} s")
    celle = [(c, ISOLATO["partizione"], s) for c in CITTA for s in ISOLATO["semi"]]
    print("=" * 84)
    print("COSTI APPAIATI — F'(1 sett.) contro R-orig(1 sett.), per contesto")
    print("=" * 84)
    print(f"  R-orig(1 sett.) in costi_e3bis.json = {glob:.0f} s = mediana sulle {len(tutte)} celle "
          f"delle tre citta' (nessuna citta' in particolare)")
    print("  per citta' (mediana su 3 semi): " + ", ".join(f"{c} {med([m['inserimento_s'] for m in RO[c]]):.0f} s" for c in CITTA))
    print(f"  da rimisurare ora in isolamento: F'(24 h) e F'(1 sett.) in {len(celle)} celle "
          f"(partizione {ISOLATO['partizione']}, semi {ISOLATO['semi']}, {a.fili} filo di torch); "
          f"ogni wCE deve riprodurre la fase valuta di E4 entro 1e-6")
    print(f"  PEMS08 da e6_costi.json: R-orig_672 {K6['addestramento_s']['R-orig_672']['mediana']:.0f} s, "
          f"Fp_672 {K6['adattamento_s']['Fp_672']['mediana']:.1f} s")
    if a.piano:
        return 0
    righe = [_misura(c, p, s, a.out, SETTIMANA, a.fili) for c, p, s in celle]
    tab = {}
    for c in CITTA:
        rc = [r for r in righe if r["contesto"] == c]
        tab[c] = {"n": len(rc),
                  "Fp_96_s": med([r["misure"]["Fp_96"]["inserimento_s"] for r in rc]),
                  "Fp_672_s": med([r["misure"][f"Fp_{SETTIMANA}"]["inserimento_s"] for r in rc]),
                  "aggiornamenti_F": rc[0]["misure"][f"Fp_{SETTIMANA}"]["aggiornamenti"],
                  "R-orig_672_s": med([m["inserimento_s"] for m in RO[c]]),
                  "rimisure_che_riproducono_la_concorrente": sum(len(r["misure"]) for r in rc)}
    tab["PEMS08"] = {"n": len(K6["semi"]), "Fp_96_s": K6["adattamento_s"]["Fp_96"]["mediana"],
                     "Fp_672_s": K6["adattamento_s"]["Fp_672"]["mediana"], "aggiornamenti_F": None,
                     "R-orig_672_s": K6["addestramento_s"]["R-orig_672"]["mediana"],
                     "rimisure_che_riproducono_la_concorrente": None}
    for t in tab.values():
        t["rapporto_Rorig_su_Fp_672"] = t["R-orig_672_s"] / t["Fp_672_s"]
    mel = K4["tabella"]["gated"]["Melbourne"]
    doc = {"tabella": tab, "celle_F": righe, "manifesti_R-orig": RO,
           "R-orig_672_mediana_9_celle_s": glob, "R-orig_672_costi_e3bis_s": K3["R-orig"]["inserimento_s"],
           "Fp_672_Melbourne_costi_e4_s": mel["adattamento_s"] if mel["tau"] == SETTIMANA else None,
           "impronte_ingressi": {k: h(f) for k, f in ingressi.items()},
           "impronte_manifesti_R-orig": {m["file"]: h(a.out / m["file"]) for c in CITTA for m in RO[c]},
           "istante": datetime.now(timezone.utc).isoformat()}
    fj = a.out / "costi_appaiati.json"
    fj.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    imp = h(fj)
    A = ["# Costi appaiati per contesto — F′(1 sett.) contro R-orig(1 sett.), stessa macchina", "",
         f"Generato da `evoluzione/esperimenti/costi_appaiati.py` il {doc['istante'][:10]}; "
         f"numeri in `results/evoluzione/costi_appaiati.json` (impronta `{imp}`). "
         "Campione isolato, un processo: partizione 0, semi 201-203 (citta'); PEMS08 da E6 §5. "
         "F′ rimisurato qui in tutte le citta' (ogni wCE riproduce la fase valuta di E4 entro 1e-6); "
         "R-orig(1 sett.) dai manifesti isolati di E3-bis. Mediane sui semi.", "",
         "| contesto | n | F′(24 h) | F′(1 sett.) | aggiornamenti di F | R-orig(1 sett.) | R-orig / F′(1 sett.) |",
         "|---|---|---|---|---|---|---|"]
    for c, t in tab.items():
        A.append(f"| {c} | {t['n']} | {t['Fp_96_s']:.1f} s | **{t['Fp_672_s']:.0f} s** | "
                 f"{t['aggiornamenti_F'] if t['aggiornamenti_F'] is not None else 'cfg E6'} | "
                 f"**{t['R-orig_672_s']:.0f} s** | {t['rapporto_Rorig_su_Fp_672']:.1f}× |")
    per_citta = ", ".join(f"{c} {tab[c]['R-orig_672_s']:.0f} s" for c in CITTA)
    A += ["", f"- Il **{glob:.0f} s** di R-orig(1 sett.) in `costi_e3bis.json` e' la mediana sulle "
          f"{len(tutte)} celle delle tre citta' ({per_citta}): "
          "non appartiene a una citta'.",
          f"- F′(1 sett.) a Melbourne in `costi_e4.json`: {doc['Fp_672_Melbourne_costi_e4_s']:.0f} s "
          f"(rimisura di oggi: {tab['Melbourne']['Fp_672_s']:.0f} s).",
          "- Il «almeno 6×» di E3-bis §3 divideva la mediana sulle tre citta' per il solo F′(1 sett.) di "
          "Melbourne: i rapporti per citta' sono nella colonna a destra.", "",
          "| ingresso | impronta |", "|---|---|"]
    A += [f"| `{k}` | `{v}` |" for k, v in doc["impronte_ingressi"].items()]
    A += [f"| `{k}` | `{v}` |" for k, v in doc["impronte_manifesti_R-orig"].items()]
    fm = RADICE / "paper" / "tabella_costi_appaiati.md"
    fm.parent.mkdir(exist_ok=True)
    fm.write_text("\n".join(A) + "\n")
    print("\n  " + f"{'contesto':10s} {'n':>2} {'F(24h)':>8} {'F(1 sett.)':>11} {'R-orig(1 sett.)':>16} {'rapporto':>9}")
    for c, t in tab.items():
        print(f"  {c:10s} {t['n']:2d} {t['Fp_96_s']:7.1f}s {t['Fp_672_s']:10.0f}s {t['R-orig_672_s']:15.0f}s "
              f"{t['rapporto_Rorig_su_Fp_672']:8.1f}x")
    print(f"\n  salvato in {fj} (impronta {imp}) e {fm.relative_to(RADICE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
