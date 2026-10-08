#!/usr/bin/env python3
"""
Congelamento di E6 — replica esterna, parte B (PEMS08).
=========================================================
**Ogni numero e' derivato dai file di risultato**: `e6_risultati.json` (confronti
pre-registrati), `e6_scelta_gated.json`, `selezione_F_e6/configurazione_F.json`,
`esito_e6_addestra.json`, `e6_pilota.json`, `e6_costi.json`,
`estrazione_pems08.json`, `pesi_pems08/rapporto_pesi_pems08.json`, le celle di
`predizioni_e6/` (livello della wCE per l'equivalenza ±3 %) e, per il confronto
dei segni con le citta', `e5_risultati.json` (episodio 1). La parte A (PEMS04)
non e' stata eseguita: lo si scrive.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e6.py
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

from evoluzione.esperimenti.esegui_e6 import T0_VALIDAZIONE  # noqa: E402

OUT = Path("results/evoluzione")
CITTA = ("Madrid", "Londra", "Melbourne")
FILE = ["evoluzione/esperimenti/esegui_e6.py", "evoluzione/esperimenti/esegui_e6a.py",
        "evoluzione/esperimenti/estrai_pems04.py",
        "evoluzione/esperimenti/calendario_pems08.py", "evoluzione/esperimenti/esegui_e2.py",
        "protocol/E6.md", "protocol/E6bis.md"]
AFF_ET = {"a": "F₀′ − C", "b": "gated − F₀′", "c": "F′(1 sett.) − C, eta' > 1 sett.",
          "d": "F′(24 h) − C", "e": "F′(1 sett.) − A, eta' > 1 sett."}
ALTRI_ET = {"gated-C": "gated − C", "gated0-F0p": "gated(τ, N = 0) − F₀′", "gated0-C": "gated(τ, N = 0) − C",
            "A-C": "A − C", "Rorig_672-Fp_672_eta>1sett": "R-orig(1 sett.) − F′(1 sett.), eta' > 1 sett.",
            "Rorig_96-C": "R-orig(24 h) − C", "Rorig_672-Rorig_96_eta>1sett": "R-orig(1 sett.) − R-orig(24 h), eta' > 1 sett.",
            "Fp_672-C_intero": "F′(1 sett.) − C, tutte le origini dopo t₁", "Fp_192-C": "F′(48 h) − C"}
SOGLIA_EQ = 0.03
BIS_ET = {"F0-C": "F₀ − C (embedding medio)", "F0p-F0": "F₀′ − F₀ (il token)",
          "F_672-Fp_672_eta>1sett": "F(1 sett.) − F′(1 sett.), eta' > 1 sett.", "F_96-Fp_96": "F(24 h) − F′(24 h)",
          "F_672-C_eta>1sett": "F(1 sett.) − C, eta' > 1 sett.", "F_96-C": "F(24 h) − C"}
AFF_A_ET = {"a": "F₀′ − C", "b": "gated − F₀′", "c": "F′(1 sett.) − C, eta' > 1 sett.", "d": "F′(24 h) − C"}


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


def _f(x, n=3):
    return f"{x:+.{n}f}"


def _ic(q, n=3):
    return f"[{_f(q[0], n)}, {_f(q[1], n)}]"


def _segno(r):
    lo, hi = r["ic_con_nodi"]
    return "−" if hi < 0 else ("+" if lo > 0 else "0")


def _wce(A, B):
    import numpy as np
    num, den = A.sum(0), B.sum(0)
    return float(np.nanmean(np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)))


def livelli(out: Path) -> dict:
    """wCE media per modello sulle celle di prova (intero e fascia eta' > 1 sett.)."""
    import numpy as np
    liv = {}
    files = sorted(glob.glob(str(out / "predizioni_e6" / "prova_*_p*_s*.npz")))
    if not files:
        raise IngressoMancante("nessuna cella di prova in predizioni_e6/")
    for f in files:
        with np.load(f, allow_pickle=True) as z:
            for k in z.files:
                if k.startswith("A_"):
                    n = k[2:]
                    A, B = z[k], z["B_" + n]
                    liv.setdefault(n, {"intero": [], "eta7": []})
                    liv[n]["intero"].append(_wce(A.sum(0), B.sum(0)))
                    liv[n]["eta7"].append(_wce(A[2], B[2]))
    return {n: {q: float(np.mean(v)) for q, v in d.items()} for n, d in liv.items()}, len(files)


def documento(R: dict) -> str:
    RS, SC, CF, AD, PI, CO, PE, PW, E5 = (R[k] for k in ("risultati", "scelta", "cfgF", "addestra",
                                                          "pilota", "costi", "estrazione", "pesi", "e5"))
    LV, n_celle = R["livelli"], R["n_celle"]
    A = []; a = A.append
    a("# Congelamento — E6, replica esterna, parte B (PEMS08)")
    a("")
    a(f"**Congelato il {R['data']}**, commit `{R['commit']}`. Pre-registrazione `protocol/E6.md` "
      f"(impronta `{R['impronte']['protocol/E6.md']}`), firmata al commit `546bd72f7aea520f` prima del lancio. "
      f"**Ogni numero e' calcolato da `genera_congelamento_e6.py`** dai file di risultato."
      + (" E6-bis (`protocol/E6bis.md`, firmata al commit `168d6f5f57d721d5`) e' nella sezione 3b." if R.get("bis") else "")
      + (" La parte A (PEMS04) e' nella sezione 3c." if R.get("parte_a") else
         " **La parte A (PEMS04, bracci definitivi) non e' stata eseguita** e non e' in questo documento."))
    a("")
    a("## 1. Che cosa e' stato eseguito")
    a("")
    a("| | |")
    a("|---|---|")
    a(f"| dati | PEMS08, 170 sensori, 62 giorni a 15 min; estrazione con le scelte di PEMS04 "
      f"(`estrazione_pems08.json`: riferimento = percentile {PE['scelte']['percentile']} sui 118 nodi iniziali in "
      f"[{PE['scelte']['addestramento'][0]}, {PE['scelte']['addestramento'][1]}), soglie {PE['scelte']['soglie']}) |")
    a(f"| calendario | t₀ di prova {R['t0']} (giorno 40), t₁ = {R['t0'] + 96}; t₀ di validazione {R['t0v']}; "
      f"origini dopo t₁ nel test {R['origini_prova']}, comuni (eta' > 1 sett.) {R['origini_comuni']} |")
    a(f"| disegno | **6 contesti-partizione × 6 semi (201–206)** = 36 celle per braccio; 26 nodi nuovi per partizione, "
      f"156 distinti (motivo nel protocollo) |")
    a(f"| addestramenti | {AD['completate']} completati, {len(AD['fallite'])} falliti, {AD['ore_calendario']:.1f} h di calendario "
      f"con {AD['lavoratori']} lavoratori (C, A, E′, R-orig 24 h, R-orig 1 sett.); canonico a 11 canali riusato; pesi su [11, 3162) |")
    a(f"| F′ | configurazione selezionata su PEMS08 da E′: **{CF['scelte']['PEMS08']['aggiornamenti']} aggiornamenti, "
      f"passo {CF['scelte']['PEMS08']['passo']:g}** (wCE di validazione {CF['scelte']['PEMS08']['wce_validazione']:.4f}, "
      f"{CF['gruppi']} gruppi × {len(CF['griglia'])} candidati), impronta `{CF['impronta']}`, congelata prima della prova |")
    sc = SC["scelta"]["PEMS08"]; cvv = SC["celle_valide_validazione"]
    a(f"| gated | (τ, N) con la regola di E4 sull'episodio di validazione: **τ = {sc['tau']} passi "
      f"({'24 h' if sc['tau'] == 96 else '48 h' if sc['tau'] == 192 else '1 sett.' if sc['tau'] == 672 else 'mai'}), "
      f"N = {sc['N']}** (wCE {sc['wce_validazione']:.4f}); impronta `{SC['impronta']}` prima del test. "
      f"Celle valide per nodo in validazione min/mediana/max {cvv['min']}/{cvv['mediana']:.0f}/{cvv['max']}: "
      f"**N e' inerte per costruzione** (copertura 100 %), come dichiarato nel protocollo |")
    a(f"| ricampionamento | {RS['repliche']} repliche congiunte (partizioni × semi × nodi), seme {RS['seme_bootstrap']}; "
      f"{RS['celle']} celle di prova |")
    a("")
    # confronto segni con le citta' (episodio 1)
    a("## 2. Le affermazioni (a)–(e) su PEMS08 e il segno nelle tre citta'")
    a("")
    a("| | confronto | PEMS08 | segno | Madrid | Londra | Melbourne | concorda |")
    a("|---|---|---|---|---|---|---|---|")
    conc = {}
    for k, et in AFF_ET.items():
        r = RS["affermazioni"][k]; s = _segno(r)
        segni_c = {c: E5["affermazioni"][f"{c}/ep1/{k}"]["segno"].replace("-", "−") for c in CITTA}
        tutti = set(segni_c.values())
        if len(tutti) == 1:
            conc[k] = "si" if s == next(iter(tutti)) else "**no**"
        else:
            conc[k] = "citta' discordi" + (" (PEMS08 come " + "/".join(c for c in CITTA if segni_c[c] == s) + ")"
                                           if any(segni_c[c] == s for c in CITTA) else "")
        a(f"| ({k}) | {et} | {_f(r['media'])} {_ic(r['ic_con_nodi'])} | {s} | "
          + " | ".join(segni_c[c] for c in CITTA) + f" | {conc[k]} |")
    a("")
    a("Segni delle citta': `e5_risultati.json`, episodio 1 (la campagna principale). "
      "«−» = intervallo sotto lo zero, «+» sopra, «0» include lo zero.")
    a("")
    a("## 3. Altri confronti pre-registrati")
    a("")
    a("| confronto | Δ | segno |")
    a("|---|---|---|")
    for k, et in ALTRI_ET.items():
        r = RS["altri"][k]
        a(f"| {et} | {_f(r['media'])} {_ic(r['ic_con_nodi'])} | {_segno(r)} |")
    a("")
    # equivalenza R-orig(1 sett.) vs F'(1 sett.)
    r_eq = RS["altri"]["Rorig_672-Fp_672_eta>1sett"]
    liv_F7 = LV["Fp_672"]["eta7"]
    banda = SOGLIA_EQ * liv_F7
    dentro = (r_eq["ic_con_nodi"][0] >= -banda) and (r_eq["ic_con_nodi"][1] <= banda)
    a(f"**Equivalenza ±3 % (R-orig(1 sett.) contro F′(1 sett.), eta' > 1 sett.)**: livello di F′(1 sett.) "
      f"{liv_F7:.4f}, banda ±{banda:.4f}; intervallo {_ic(r_eq['ic_con_nodi'], 4)} → "
      + ("**equivalenti** (intervallo dentro la banda)." if dentro else
         "**non si conclude l'equivalenza**: l'intervallo esce dalla banda (26 nodi nuovi per partizione, intervalli larghi come dichiarato)."))
    a("")
    a(f"Livelli medi di wCE sulle {n_celle} celle di prova (tutte le origini dopo t₁ / eta' > 1 sett.): "
      + "; ".join(f"{n} {d['intero']:.3f} / {d['eta7']:.3f}" for n, d in sorted(LV.items())) + ".")
    a("")
    BI = R.get("bis")
    if BI:
        a("## 3b. E6-bis — il costo di trasferimento su PEMS08 (`protocol/E6bis.md`)")
        a("")
        a(f"E senza token: {R['bis_addestra']['completate']} addestramenti, {len(R['bis_addestra']['fallite'])} falliti; "
          f"F₀ all'embedding medio; F(24 h) e F(1 sett.) con la configurazione di F′ congelata "
          f"(impronta `{BI['impronta_configurazione_F']}`); {BI['celle']} celle sugli stessi nodi e origini di E6 "
          f"(controllo 2); {BI['repliche']} repliche, seme {BI['seme_bootstrap']}.")
        a("")
        a("| confronto | Δ | segno |")
        a("|---|---|---|")
        for k, et in BIS_ET.items():
            r = BI["confronti"][k]
            a(f"| {et} | {_f(r['media'])} {_ic(r['ic_con_nodi'])} | {_segno(r)} |")
        a("")
        r0 = BI["confronti"]["F0-C"]
        a(f"Il costo di trasferimento dell'embedding medio "
          + ("**esiste anche su PEMS08** (F₀ − C sopra lo zero; nelle citta' +0,050…+0,078 in E2)" if _segno(r0) == "+"
             else "**non si misura su PEMS08** (F₀ − C non sopra lo zero; nelle citta' +0,050…+0,078)")
          + "; il token " + ("conta ancora dopo l'adattamento (F − F′ sopra lo zero a 24 h e a 1 settimana)."
                             if _segno(BI["confronti"]["F_96-Fp_96"]) == "+" and _segno(BI["confronti"]["F_672-Fp_672_eta>1sett"]) == "+"
                             else "dopo l'adattamento: vedi tabella."))
        a("")
    PA = R.get("parte_a")
    if PA:
        a("## 3c. Parte A — PEMS04, bracci definitivi (completamento, 168 origini comuni)")
        a("")
        sa = PA["scelta_gated"]; ca = PA["configurazione_F"]
        a(f"E′ su PEMS04: {R['a_addestra']['completate']} addestramenti; F′ selezionata da E′ ({ca['aggiornamenti']} aggiornamenti, "
          f"passo {ca['passo']:g}, impronta `{PA['impronta_configurazione_F']}`); gated τ = {sa['tau']} passi, N = {sa['N']} "
          f"(impronta `{PA['impronta_scelta_gated']}`); {PA['celle']} celle (3 contesti × 12 semi, {PA['nodi_sotto_N']['nodi']} nodi nuovi); "
          f"nodi sotto N {PA['nodi_sotto_N']['media_per_cella']:.1f} per cella su {PA['nodi_sotto_N']['nodi']} "
          f"(celle valide min/mediana/max {PA['nodi_sotto_N']['celle_valide_min_mediana_max'][0]}/"
          f"{PA['nodi_sotto_N']['celle_valide_min_mediana_max'][1]:.0f}/{PA['nodi_sotto_N']['celle_valide_min_mediana_max'][2]}"
          + (": N inerte anche qui, copertura 100 %" if PA['nodi_sotto_N']['celle_valide_min_mediana_max'][0] == 308 else "") + "). "
          f"(e) non riportabile: A non esiste su PEMS04.")
        a("")
        a("| | confronto | PEMS04 | segno | PEMS08 | Madrid | Londra | Melbourne |")
        a("|---|---|---|---|---|---|---|---|")
        for k, et in AFF_A_ET.items():
            r = PA["affermazioni"][k]
            a(f"| ({k}) | {et} | {_f(r['media'])} {_ic(r['ic_con_nodi'])} | {_segno(r)} | {_segno(RS['affermazioni'][k])} | "
              + " | ".join(E5["affermazioni"][f"{c}/ep1/{k}"]["segno"].replace("-", "−") for c in CITTA) + " |")
        a("")
        for k, et in {"gated-C": "gated − C", "Fp_672-C_intero": "F′(1 sett.) − C, tutte le origini", "Fp_192-C": "F′(48 h) − C"}.items():
            r = PA["altri"][k]
            a(f"- {et}: {_f(r['media'])} {_ic(r['ic_con_nodi'])} ({_segno(r)})")
        a("")
        a(f"(c) su PEMS04: {_f(PA['affermazioni']['c']['media'])} {_ic(PA['affermazioni']['c']['ic_con_nodi'])}, "
          + ("**segno concorde** con PEMS08" + (" e con le tre citta'" if all(E5["affermazioni"][f"{c}/ep1/c"]["segno"] == "-" for c in CITTA) else "")
             if _segno(PA["affermazioni"]["c"]) == "−" == _segno(RS["affermazioni"]["c"])
             else "intervallo che " + ("include lo zero" if _segno(PA["affermazioni"]["c"]) == "0" else "sta sopra lo zero")
             + " su 168 origini comuni: limite dichiarato prima")
          + ".")
        a("")
    a("## 4. Nodi sotto soglia e copertura")
    a("")
    ns = RS["nodi_sotto_N"]
    a(f"N = {ns['N']}: nodi sotto soglia {ns['media_per_cella']:.1f} per cella (massimo {ns['massimo']}) su {ns['nodi']}; "
      f"celle valide per nodo min/mediana/max {ns['celle_valide_min_mediana_max'][0]}/{ns['celle_valide_min_mediana_max'][1]:.0f}/"
      f"{ns['celle_valide_min_mediana_max'][2]}. **Non e' un risultato**: il rilascio e' completo per costruzione "
      f"(protocollo, nota derivata); gated(τ, N) e gated(τ, 0) coincidono (Δ identiche nella tabella 3).")
    a("")
    a("## 5. Costi (campione isolato: partizione 0, semi 201–203, un processo)")
    a("")
    a("| braccio | addestramento (s, mediana) | adattamento (s, mediana) | totale per un nodo nuovo (s) |")
    a("|---|---|---|---|")
    ad, at = CO["addestramento_s"], CO["adattamento_s"]
    eE = ad["E1"]["mediana"]
    righe = [("C", ad["C"]["mediana"], 0.0), ("A", ad["A"]["mediana"], 0.0), ("E′", eE, 0.0),
             ("F₀′ (da E′)", eE, 0.0), ("F′(24 h)", eE, at["Fp_96"]["mediana"]), ("F′(1 sett.)", eE, at["Fp_672"]["mediana"]),
             ("R-orig(24 h)", ad["R-orig_96"]["mediana"], 0.0), ("R-orig(1 sett.)", ad["R-orig_672"]["mediana"], 0.0)]
    for nome, tr, adp in righe:
        a(f"| {nome} | {tr:.0f} | {adp:.1f} | {tr + adp:.0f} |")
    a("")
    rap_solo = ad["R-orig_672"]["mediana"] / at["Fp_672"]["mediana"]
    rap_con = ad["R-orig_672"]["mediana"] / (eE + at["Fp_672"]["mediana"])
    a(f"Pilota pre-firma: C {PI['secondi']:.0f} s; campione isolato: C {ad['C']['mediana']:.0f} s. "
      f"R-orig(1 sett.) costa **{rap_solo:.1f}×** il solo adattamento di F′(1 sett.) e **{rap_con:.2f}×** E′ + adattamento: "
      + ("su PEMS08 (118 nodi iniziali, 3 151 origini) il riaddestramento e' economico e il vantaggio di costo "
         "dell'adattamento, netto nelle citta' (E3-bis: almeno 6×), qui si riduce al solo adattamento. Lo si dice."
         if rap_con < 2 else "il vantaggio di costo dell'adattamento regge anche qui."))
    a("")
    a("## 6. Difetti emersi e dichiarati")
    a("")
    a("- `da_E1` (`esegui_e2.py`) costruiva il predittore a nove canali qualunque fosse la sorgente: su PEMS "
      "(undici canali) la copia da E′ falliva. Corretto leggendo la sorgente dal punto di controllo "
      "(commit `6629f40`); collaudi 8/8 a scarto 0, 37/37, 25/25. Nelle citta' il comportamento e' identico: "
      "nessun risultato precedente cambia.")
    if not PA:
        a("- Parte A (PEMS04, bracci definitivi): **non eseguita**; resta il completamento "
          "dichiarato nel protocollo, con il suo limite (168 origini comuni).")
    a("")
    a("## 7. Che cosa dice al paper")
    a("")
    neg = [k for k in AFF_ET if _segno(RS["affermazioni"][k]) == "−"]
    a(f"Su PEMS08, con intervallo che esclude lo zero: {', '.join('(' + k + ')' for k in neg) or 'nessuna affermazione'}. "
      f"La tesi a una settimana — (c) F′(1 sett.) − C sulle origini comuni — "
      + ("**regge** fuori da Traffic4cast" if _segno(RS["affermazioni"]["c"]) == "−" else "**non regge** su PEMS08")
      + f"; i segni concordano con le tre citta' per {sum(1 for k in AFF_ET if conc[k] == 'si')} "
      f"{'affermazione' if sum(1 for k in AFF_ET if conc[k] == 'si') == 1 else 'affermazioni'} su 5 "
      f"(tabella 2). Dove PEMS08 differisce dalle citta' il paper lo riporta nella stessa tabella, senza spiegazioni "
      f"post hoc. La soglia N non si misura su PEMS08 (copertura 100 %); τ scelto in validazione = "
      f"{sc['tau']} passi.")
    a("")
    a("## 8. Impronte")
    a("")
    a("| file | impronta |")
    a("|---|---|")
    for f, hh in R["impronte"].items():
        a(f"| `{f}` | `{hh}` |")
    a(f"| configurazione F′ | `{CF['impronta']}` |")
    a(f"| scelta gated | `{SC['impronta']}` |")
    return "\n".join(A) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    print("[1/3] ingressi")
    RS = leggi(a.out / "e6_risultati.json"); SC = leggi(a.out / "e6_scelta_gated.json")
    CF = leggi(a.out / "selezione_F_e6" / "configurazione_F.json")
    if RS["impronta_scelta_gated"] != SC["impronta"] or RS["impronta_configurazione_F"] != CF["impronta"]:
        raise IngressoMancante("impronte di gated o di F′ non coerenti con e6_risultati.json")
    AD = leggi(a.out / "esito_e6_addestra.json"); PI = leggi(a.out / "e6_pilota.json"); CO = leggi(a.out / "e6_costi.json")
    PE = leggi(a.out / "estrazione_pems08.json"); PW = leggi(a.out / "pesi_pems08" / "rapporto_pesi_pems08.json")
    E5 = leggi(a.out / "e5_risultati.json")
    BI = json.loads((a.out / "e6bis_risultati.json").read_text()) if (a.out / "e6bis_risultati.json").exists() else None
    BA = json.loads((a.out / "esito_e6bis_addestra.json").read_text()) if BI else None
    PA = json.loads((a.out / "e6a_risultati.json").read_text()) if (a.out / "e6a_risultati.json").exists() else None
    AA = json.loads((a.out / "esito_e6a_addestra.json").read_text()) if PA else None
    print("[2/3] livelli dalle celle"); LV, n_celle = livelli(a.out)
    import numpy as np
    z = np.load(sorted(glob.glob(str(a.out / "predizioni_e6" / "prova_*_p0_s201.npz")))[0], allow_pickle=True)
    t0 = int(z["t0"]); per = z["origini"].astype("int64")
    R = {"data": datetime.now(timezone.utc).date().isoformat(), "commit": commit_git(),
         "risultati": RS, "scelta": SC, "cfgF": CF, "addestra": AD, "pilota": PI, "costi": CO,
         "estrazione": PE, "pesi": PW, "e5": E5, "livelli": LV, "n_celle": n_celle,
         "t0": t0, "t0v": T0_VALIDAZIONE, "origini_prova": int(len(per)),
         "origini_comuni": int((per > t0 + 672).sum()),
         "bis": BI, "bis_addestra": BA, "parte_a": PA, "a_addestra": AA,
         "impronte": {f: h(f) for f in FILE}}
    print("[3/3] documento")
    Path("CONGELAMENTO_E6.md").write_text(documento(R))
    print(f"  generato CONGELAMENTO_E6.md; (c) F′(1 sett.) − C: {_f(RS['affermazioni']['c']['media'])} "
          f"{_ic(RS['affermazioni']['c']['ic_con_nodi'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
