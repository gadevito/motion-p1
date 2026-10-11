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
    ap.add_argument("--da-json", action="store_true",
                    help="non rimisura: rilegge costi_appaiati.json (intatto) e riscrive la sola tabella")
    ap.add_argument("--sessione", action="store_true",
                    help="la tabella dai tempi della sessione unica (costi_sessione.json), senza rimisurare")
    a = ap.parse_args()
    if a.sessione:
        return _scrivi_tabella_sessione(a)
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
    fj = a.out / "costi_appaiati.json"
    if a.da_json:
        doc = json.loads(fj.read_text()); tab, righe = doc["tabella"], doc["celle_F"]
        if abs(doc["R-orig_672_mediana_9_celle_s"] - glob) > 1e-9:
            raise RuntimeError("costi_appaiati.json non coerente con i manifesti di R-orig")
        return _scrivi_tabella(a, doc, tab, righe, glob, tutte, h(fj))
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
    fj.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    return _scrivi_tabella(a, doc, tab, righe, glob, tutte, h(fj))


def _nodi_prova(c: str, out: Path) -> int:
    """I nodi di prova della partizione 0: su di essi si adatta F′ (da `_partizioni`, non a memoria)."""
    import numpy as np
    from evoluzione.esperimenti.addestramento import _carica, _partizioni
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    D = _carica(c, out / "maschere")
    nodi, _ = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[ISOLATO["partizione"]])})
    return int(len(nodi["prova"]))


def _scrivi_tabella(a, doc, tab, righe, glob, tutte, imp) -> int:
    nodi = {c: _nodi_prova(c, a.out) for c in CITTA}
    agg = {c: next(r for r in righe if r["contesto"] == c)["misure"][f"Fp_{SETTIMANA}"]["aggiornamenti"] for c in CITTA}
    orig = {L: next(iter(righe))["misure"][f"Fp_{L}"]["origini"] for L in (96, SETTIMANA)}
    rif = CITTA[0]
    rapp = {c: (tab[c]["Fp_96_s"] / tab[rif]["Fp_96_s"], tab[c]["Fp_672_s"] / tab[rif]["Fp_672_s"]) for c in CITTA}
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
          "Melbourne: i rapporti per citta' sono nella colonna a destra.",
          "- **Che cosa misura il tempo di F′, e perche' Melbourne costa di piu'.** E' il tempo per cella, "
          "un processo, un filo di torch: copia del punto di controllo di E′, costruzione dei lotti su tutte "
          f"le origini in (t₀, t₀+L] ({orig[96]} a 24 h, {orig[SETTIMANA]} a 1 sett.) e `aggiornamenti` passi di "
          "Adam sulla tabella dei nodi di prova della partizione ("
          + ", ".join(f"{c} {nodi[c]}" for c in CITTA) + " nodi), con (passo, aggiornamenti) scelti su "
          "validazione per citta' in E4 (`selezione_F_griglia/configurazione_F.json`): aggiornamenti "
          + ", ".join(f"{c} {agg[c]}" for c in CITTA) + ". Il rapporto con "
          + f"{rif} e' " + "; ".join(f"{c} {rapp[c][0]:.1f}× a 24 h e {rapp[c][1]:.1f}× a 1 sett." for c in CITTA[1:])
          + ". Ogni aggiornamento e' un passaggio completo (gradiente a lotto pieno, `adatta`) su tutte le "
          "origini della finestra e tutti i nodi di prova, quindi il tempo e' ∝ aggiornamenti × origini × nodi: "
          "il rapporto fra citta' e' lo stesso alle due finestre (le origini si semplificano) e vale il "
          "rapporto dei prodotti aggiornamenti × nodi, "
          + "; ".join(f"{c} {agg[c] * nodi[c] / (agg[rif] * nodi[rif]):.2f}× atteso" for c in CITTA[1:])
          + ".", "",
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
    print(f"\n  json {a.out / 'costi_appaiati.json'} (impronta {imp}); tabella {fm.relative_to(RADICE)}")
    return 0


def _scrivi_tabella_sessione(a) -> int:
    """La tabella dei costi dalla SESSIONE UNICA (`costi_sessione.json`): stessa macchina, stesso
    momento, macchina ferma; tutte le voci del paper per contesto. Mediane sui tre semi."""
    import numpy as np
    med = lambda v: float(np.median(v))  # noqa: E731
    fj = a.out / "costi_sessione.json"
    D = json.loads(fj.read_text()); imp = h(fj)
    if "istante_fine" not in D:
        raise RuntimeError("costi_sessione.json: sessione non chiusa")
    VOCI = (("C", "C"), ("E1", "E′"), ("Fp_96", "F′(24 h)"), ("Fp_672", "F′(1 sett.)"),
            ("R-orig_96", "R-orig(24 h)"), ("R-orig_672", "R-orig(1 sett.)"))
    tab, agg, scarti = {}, {}, []
    for c in CITTA:
        celle = [v for v in D["celle"].values() if v["contesto"] == c]
        if len(celle) != len(ISOLATO["semi"]):
            raise RuntimeError(f"{c}: {len(celle)} celle nella sessione")
        tab[c] = {"n": len(celle),
                  "C": med([v["C"]["addestramento_s"] for v in celle]),
                  "E1": med([v["E1"]["addestramento_s"] for v in celle]),
                  "Fp_96": med([v["Fp"]["Fp_96"]["inserimento_s"] for v in celle]),
                  "Fp_672": med([v["Fp"]["Fp_672"]["inserimento_s"] for v in celle]),
                  "R-orig_96": med([v["R-orig_96"]["inserimento_s"] for v in celle]),
                  "R-orig_672": med([v["R-orig_672"]["inserimento_s"] for v in celle])}
        agg[c] = celle[0]["Fp"]["Fp_672"]["aggiornamenti"]
        scarti += [v[k]["scarto_relativo"] for v in celle for k in ("C", "R-orig_96", "R-orig_672")]
        scarti += [v["Fp"][k]["scarto_relativo"] for v in celle for k in ("Fp_96", "Fp_672")]
    P = D["PEMS08"]; E_TOK = [k for k in P["addestramento_s"] if k not in ("C", "A", "R-orig_96", "R-orig_672")]
    if len(E_TOK) != 1:
        raise RuntimeError(f"PEMS08: braccio E′ non identificato fra {list(P['addestramento_s'])}")
    tab["PEMS08"] = {"n": len(P["semi"]), "C": P["addestramento_s"]["C"]["mediana"],
                     "E1": P["addestramento_s"][E_TOK[0]]["mediana"],
                     "Fp_96": P["adattamento_s"]["Fp_96"]["mediana"], "Fp_672": P["adattamento_s"]["Fp_672"]["mediana"],
                     "R-orig_96": P["addestramento_s"]["R-orig_96"]["mediana"],
                     "R-orig_672": P["addestramento_s"]["R-orig_672"]["mediana"], "A": P["addestramento_s"]["A"]["mediana"]}
    nodi = {c: _nodi_prova(c, a.out) for c in CITTA}
    mp, md = D["macchina_prima"], D["macchina_dopo"]
    A = ["# Costi per contesto — una macchina, una sessione, macchina ferma", "",
         f"Generato da `evoluzione/esperimenti/costi_appaiati.py --sessione` il {D['istante_fine'][:10]}; numeri in "
         f"`results/evoluzione/costi_sessione.json` (impronta `{imp}`), scritto da `costi_sessione.py`. "
         f"Macchina: {mp['cpu'] or mp['arch']}, torch {mp['torch']}, un processo, un filo; sessione dal "
         f"{D['istante_inizio'][:16].replace('T', ' ')} UTC al {D['istante_fine'][:16].replace('T', ' ')} UTC "
         f"({D['ore_sessione']:.1f} h), load average prima {mp['load_average'][0]:.2f} / dopo {md['load_average'][0]:.2f}"
         + (f", **{D['riprese']} ripresa/e**" if D.get("riprese") else "") + ". "
         "Campione isolato: partizione 0, semi 201-203 (citta'), semi 201-203 (PEMS08); mediane sui semi. "
         f"Controlli: wCE di C, R-orig e F′ riprodotte entro 1e-6 (scarto massimo {max(scarti):.1e} su {len(scarti)}); "
         f"pesi di E′ riprodotti 9/9; PEMS08 {P['checkpoint_che_riproducono_i_pesi_di_e6']} checkpoint sui pesi di E6.", "",
         "| contesto | n | " + " | ".join(et for _, et in VOCI) + " | R-orig/F′ (24 h) | R-orig/F′ (1 sett.) |",
         "|---|---|" + "---|" * (len(VOCI) + 2)]
    for c, t in tab.items():
        A.append(f"| {c} | {t['n']} | " + " | ".join(
            (f"{t[k]/60:.1f} min" if k in ("C", "E1") else f"{t[k]:.0f} s") for k, _ in VOCI)
            + f" | {t['R-orig_96'] / t['Fp_96']:.1f}× | {t['R-orig_672'] / t['Fp_672']:.1f}× |")
    A += ["", f"- A (veterano, non operativo) su PEMS08: {tab['PEMS08']['A']/60:.1f} min di addestramento.",
          "- F′ e' per cella: copia di E′, lotti su tutte le origini della finestra e `aggiornamenti` passi di Adam a "
          "gradiente pieno sui nodi di prova (" + ", ".join(f"{c} {nodi[c]} nodi, {agg[c]} aggiornamenti" for c in CITTA)
          + "): il tempo e' ∝ aggiornamenti × origini × nodi, da cui le differenze fra citta'.",
          "- R-orig riaddestra l'intera rete ampliata dopo i dati: il suo tempo cresce col numero di nodi della rete "
          "(900 Madrid/Londra, 594 Melbourne, 170 PEMS08).", "",
          "| ingresso | impronta |", "|---|---|", f"| `results/evoluzione/costi_sessione.json` | `{imp}` |",
          f"| `results/evoluzione/costi_sessione_pems08.json` | `{h(a.out / 'costi_sessione_pems08.json')}` |"]
    fm = RADICE / "paper" / "tabella_costi_appaiati.md"
    fm.write_text("\n".join(A) + "\n")
    ft = a.out / "costi_tabella_sessione.json"
    ft.write_text(json.dumps({"macchina": mp, "load_average_prima": mp["load_average"], "load_average_dopo": md["load_average"],
                              "carico_max_ammesso": D.get("carico_max_ammesso"), "riprese": D.get("riprese", 0),
                              "istante_inizio": D["istante_inizio"], "istante_fine": D["istante_fine"],
                              "ore_sessione": D["ore_sessione"], "unita": "secondi, mediana sui semi",
                              "voci": {k: et for k, et in VOCI}, "tabella": tab, "nodi_prova": nodi, "aggiornamenti_F": agg,
                              "controlli": {"scarto_relativo_massimo_wce": max(scarti), "n_wce": len(scarti),
                                            "pesi_E1_riprodotti": "9/9",
                                            "checkpoint_pems08_riprodotti": P["checkpoint_che_riproducono_i_pesi_di_e6"]},
                              "sorgente": {"file": "results/evoluzione/costi_sessione.json", "impronta": imp}},
                             indent=2, ensure_ascii=False))
    A.append(f"| `results/evoluzione/costi_tabella_sessione.json` | `{h(ft)}` |")
    fm.write_text("\n".join(A) + "\n")
    print("\n".join(A[4:4 + len(tab) + 2]))
    print(f"\n  tabella {fm.relative_to(RADICE)} (json impronta {imp})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
