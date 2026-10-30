#!/usr/bin/env python3
"""
E18-ter, generatori delle tabelle (sostituzioni letterali; si ferma se un testo atteso non compare esattamente una volta).

analysis/tabelle_suppl.py
  - `_scale(ic)`: le due scale di lettura dagli stessi intervalli — segno rispetto a zero (favourable / unfavourable /
    inconclusive) e margine (within delta = 0.005: yes se il limite superiore e' sotto delta, come la «non inferiorita'»
    di E17); nota datata «presentation changed on 2026-10-30, analysis unchanged» nelle didascalie.
  - E9 (`tab:suppE15a`), G21 (`tab:suppG4`), G23 (`tab:suppG6`): la colonna «category» diventa «sign» e «within delta».
  - F17 (`tab:suppE3`): colonna wCE dalla definizione del manoscritto (per orizzonte, poi media sugli orizzonti),
    ricalcolata in E18-ter dalle stesse probabilita' (`congelamento_e18ter.json` → `wce16`); nota datata in didascalia.
analysis/tabelle_paper1.py
  - Tabella IV (`table_policies.tex`): per ogni confronto valore, segno, within delta (tre celle); intestazione nuova
    per il manoscritto nel messaggio a P1.

Dalla radice OR3/:  python3 patch_e18ter_tabelle.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
SUPP = R / "analysis" / "tabelle_suppl.py"
P1 = R / "analysis" / "tabelle_paper1.py"

NOTA = "presentation changed on 2026-10-30, analysis unchanged"

SOST = {SUPP: [
    # helper delle due scale, subito dopo CAT_EN
    ('''CAT_EN = {"superiorita'": "superiority", "non inferiorita'": "non-inferiority", "inconclusivo": "inconclusive",
          "inferiorita'": "inferiority"}''',
     '''CAT_EN = {"superiorita'": "superiority", "non inferiorita'": "non-inferiority", "inconclusivo": "inconclusive",
          "inferiorita'": "inferiority"}
DELTA_CAT = 0.005


def _scale(ic, breve=False):
    """Le due scale di lettura dallo stesso intervallo [lo, hi] (negativo = favorevole alla prima strategia):
    segno rispetto a zero (favourable / unfavourable / inconclusive) e margine (within delta: yes se hi < delta, la
    regola della «non inferiorita'» di E17). Presentazione cambiata il 2026-10-30, analisi invariata."""
    lo, hi = ic
    segno = "favourable" if hi < 0 else ("unfavourable" if lo > 0 else "inconclusive")
    if breve:
        segno = {"favourable": "fav.", "unfavourable": "unf.", "inconclusive": "inc."}[segno]
    return segno, ("yes" if hi < DELTA_CAT else "no")


SCALE_EN = ("sign of the interval against zero (favourable: below; unfavourable: above; inconclusive: includes zero) "
            "and margin (within $\\\\delta=0.005$ wCE: upper bound below $\\\\delta$)")
NOTA = "presentation changed on 2026-10-30, analysis unchanged"'''),
    # E9: E15a
    ('''            righe.append(" & ".join([CTX_EN[c] if i == 0 else "", et, _ic(r, scala=1.0, cifre=3),
                                     CAT_EN.get(r["categoria"], r["categoria"]),''',
     '''            righe.append(" & ".join([CTX_EN[c] if i == 0 else "", et, _ic(r, scala=1.0, cifre=3),
                                     *_scale(r["ic_con_nodi"]),'''),
    ('''        "@{}l l c l c l c@{}",
        "E15: the differences of the causal campaign (six seeds, 18 runs per city, episode 1), with the category of "
        "Section~III of the paper (inferiority: interval above zero), against the pre-registered campaign on the "''',
     '''        "@{}l l c l l c l c@{}",
        "E15: the differences of the causal campaign (six seeds, 18 runs per city, episode 1), with the two reading scales "
        "of the paper — " + SCALE_EN + f"; {NOTA} — against the pre-registered campaign on the "'''),
    ('''        + fonte, "City & Difference & Causal & Category & Frozen, same cells & Verdict & Published (12 seeds)",''',
     '''        + fonte, "City & Difference & Causal & Sign & Within $\\\\delta$ & Frozen, same cells & Verdict & Published (12 seeds)",'''),
    # G21: G4
    ('''            cambia = d["categoria_attuale"] != d["categoria_per_sensore"]
            cat = CAT_EN[d["categoria_per_sensore"]]''',
     '''            cambia = d["categoria_attuale"] != d["categoria_per_sensore"]
            cat = " & ".join((f"\\\\textbf{{{x}}}" if cambia else x) for x in _scale(d["ic_per_sensore"]))'''),
    ('''                         f"$[{d['ic_attuale'][0]:+.4f}, {d['ic_attuale'][1]:+.4f}]$ & {CAT_EN[d['categoria_attuale']]} & "
                         f"$[{d['ic_per_sensore'][0]:+.4f}, {d['ic_per_sensore'][1]:+.4f}]$ & "
                         + (f"\\\\textbf{{{cat}}}" if cambia else cat) + " \\\\\\\\")''',
     '''                         f"$[{d['ic_attuale'][0]:+.4f}, {d['ic_attuale'][1]:+.4f}]$ & {' & '.join(_scale(d['ic_attuale']))} & "
                         f"$[{d['ic_per_sensore'][0]:+.4f}, {d['ic_per_sensore'][1]:+.4f}]$ & " + cat + " \\\\\\\\")'''),
    ('''        "@{}l c l c c l c l@{}",
        "E18, part B: intervals from the current joint resampling (partitions $\\\\times$ seeds $\\\\times$ sensor "''',
     '''        "@{}l c l c c l l c l l@{}",
        "E18, part B: intervals from the current joint resampling (partitions $\\\\times$ seeds $\\\\times$ sensor "'''),
    ('''        "arms, partitions and seeds; 4{,}000 replicates. Categories as in the main paper ($\\\\delta=0.005$ wCE). "
        "Second column: distinct sensors / sensor--partition occurrences. Changes of category in bold. "''',
     '''        "arms, partitions and seeds; 4{,}000 replicates. Two reading scales as in the main paper: " + SCALE_EN + f"; {NOTA}. "
        "Second column: distinct sensors / sensor--partition occurrences. Changes of category in bold. "'''),
    ('''        "Context & sensors & Difference & mean & current interval & category & sensor-level interval & category",''',
     '''        "Context & sensors & Difference & mean & current interval & sign & $\\\\delta$ & sensor-level interval & sign & $\\\\delta$",'''),
    # G23: G6
    ('''        righe.append(f"{_ctx_e18(c)} & {camp} & " + _ic_lista(a["media"], a["ic_attuale"]) + f" & {CAT_EN[a['categoria_attuale']]} & "
                     f"{{\\\\tiny$[{a['ic_per_sensore'][0]:+.4f},{a['ic_per_sensore'][1]:+.4f}]$}} & {CAT_EN[a['categoria_per_sensore']]} & "
                     + _ic_lista(b["media"], b["ic_attuale"]) + f" & {CAT_EN[b['categoria_attuale']]} & {o['data']} \\\\\\\\")''',
     '''        righe.append(f"{_ctx_e18(c)} & {camp} & " + _ic_lista(a["media"], a["ic_attuale"]) + f" & {' & '.join(_scale(a['ic_attuale']))} & "
                     f"{{\\\\tiny$[{a['ic_per_sensore'][0]:+.4f},{a['ic_per_sensore'][1]:+.4f}]$}} & {' & '.join(_scale(a['ic_per_sensore']))} & "
                     + _ic_lista(b["media"], b["ic_attuale"]) + f" & {' & '.join(_scale(b['ic_attuale']))} & {o['data']} \\\\\\\\")'''),
    ('''        "@{}l l c l c l c l c@{}",
        "E18, part D: provenance of the policy gated$(1\\\\,\\\\mathrm{wk},0)$ (token until one week, then $F'(1\\\\,\\\\mathrm{wk})$ "''',
     '''        "@{}l l c l l c l l c l l c@{}",
        "E18, part D: provenance of the policy gated$(1\\\\,\\\\mathrm{wk},0)$ (token until one week, then $F'(1\\\\,\\\\mathrm{wk})$ "'''),
    ('''        "before it: the policy is a post hoc descriptive evaluation on the eleven contexts, without prospective "
        "confirmation." + fonte,
        "Context & campaign & gated$(1\\\\,\\\\mathrm{wk},0)-F_0'$ & category & sensor-level & category & "
        "gated$(1\\\\,\\\\mathrm{wk},0)-$gated$(\\\\tau,N)$ & category & first observed", righe, "tab:suppG6")''',
     '''        "before it: the policy is a post hoc descriptive evaluation on the eleven contexts, without prospective "
        "confirmation. Two reading scales: " + SCALE_EN + f"; {NOTA}." + fonte,
        "Context & campaign & gated$(1\\\\,\\\\mathrm{wk},0)-F_0'$ & sign & $\\\\delta$ & sensor-level & sign & $\\\\delta$ & "
        "gated$(1\\\\,\\\\mathrm{wk},0)-$gated$(\\\\tau,N)$ & sign & $\\\\delta$ & first observed", righe, "tab:suppG6")'''),
    # F17: colonna wCE da wce16 (E18-ter)
    ('''    righe, prima = [], True
    for g in GRUPPI_E16:
        if not prima:
            righe.append("\\\\addlinespace")
        primo = True
        for b, et in BRACCI_E16 + (("C_sett", "$C$$^\\\\dagger$"),):''',
     '''    f_ter = ris / "congelamento_e18ter.json"
    W = json.loads(f_ter.read_text())["risultati"].get("wce16", {}).get("gruppi", {}) if f_ter.exists() else {}
    md_ter = rep / "CONGELAMENTO_E18TER.md"

    def wce_di(g, k, fin, altrimenti):
        """wCE con la definizione del manoscritto (E18-ter, `wce16`): per orizzonte, poi media sugli orizzonti."""
        v = W.get(g, {}).get("wce_intero" if fin == "intero" else "wce_sett", {}).get(k)
        return v["media"] if v else altrimenti
    fonte_ter = (" wCE column: definition of the paper (per horizon $\\\\sum w_y(-\\\\log p_y)/\\\\sum w_y$ over valid origins and "
                 "sensors, then mean over the four horizons), recomputed on 2026-10-30 from the same probabilities (E18-ter; "
                 "record \\\\texttt{CONGELAMENTO\\\\_E18TER.md}, fingerprint \\\\texttt{" + imp(md_ter) + "}); the earlier column "
                 "weighted jointly over horizons; the means over cells equal those behind the differences table."
                 if W and md_ter.exists() else "")
    righe, prima = [], True
    for g in GRUPPI_E16:
        if not prima:
            righe.append("\\\\addlinespace")
        primo = True
        for b, et in BRACCI_E16 + (("C_sett", "$C$$^\\\\dagger$"),):'''),
    ('''                    if m is None:                   # E18 senza le metriche di F16 sulla finestra: solo la wCE
                        w = S[g]["wce_settimana"][k18]["media"]
                        righe.append((CTX_EN[g] if primo else "") + f" & {et_} & {CAL_EN[c]} & -- & -- & -- & -- & -- & {w:.4f} \\\\\\\\")
                    else:
                        e = m["ece"]
                        righe.append((CTX_EN[g] if primo else "") + f" & {et_} & {CAL_EN[c]} & "
                                     + " & ".join(f"{e[k]:.4f}" for k in ("0", "1", "2"))
                                     + f" & {m['logloss']:.4f} & {m['brier']:.4f} & {m['wce']:.4f} \\\\\\\\")''',
     '''                    if m is None:                   # E18 senza le metriche di F16 sulla finestra: solo la wCE
                        w = wce_di(g, k18, "sett", S[g]["wce_settimana"][k18]["media"])
                        righe.append((CTX_EN[g] if primo else "") + f" & {et_} & {CAL_EN[c]} & -- & -- & -- & -- & -- & {w:.4f} \\\\\\\\")
                    else:
                        e = m["ece"]
                        righe.append((CTX_EN[g] if primo else "") + f" & {et_} & {CAL_EN[c]} & "
                                     + " & ".join(f"{e[k]:.4f}" for k in ("0", "1", "2"))
                                     + f" & {m['logloss']:.4f} & {m['brier']:.4f} & {wce_di(g, k18, 'sett', m['wce']):.4f} \\\\\\\\")'''),
    ('''                e = m["ece"]
                righe.append((CTX_EN[g] if primo else "") + f" & {et} & {CAL_EN[c]} & "
                             + " & ".join(f"{e[k]:.4f}" for k in ("0", "1", "2"))
                             + f" & {m['logloss']:.4f} & {m['brier']:.4f} & {m['wce']:.4f} \\\\\\\\")
                primo = False
        prima = False
    ece_v = max(''',
     '''                e = m["ece"]
                righe.append((CTX_EN[g] if primo else "") + f" & {et} & {CAL_EN[c]} & "
                             + " & ".join(f"{e[k]:.4f}" for k in ("0", "1", "2"))
                             + f" & {m['logloss']:.4f} & {m['brier']:.4f} & {wce_di(g, f'{b}/{c}', 'intero', m['wce']):.4f} \\\\\\\\")
                primo = False
        prima = False
    ece_v = max('''),
    ('''           "For $F'(1\\\\,\\\\mathrm{wk})$ only the wCE is recomputed on its causal window (--: not recomputed); the row "
           "$C^\\\\dagger$ is $C$ on the same window.") + fonte + fonte18,''',
     '''           "For $F'(1\\\\,\\\\mathrm{wk})$ only the wCE is recomputed on its causal window (--: not recomputed); the row "
           "$C^\\\\dagger$ is $C$ on the same window.") + fonte + fonte18 + fonte_ter,'''),
], P1: [
    ('''    # segno dell'intervallo (fav./unf./inc.) e, a parte, il margine: «inc.$^\\\\delta$» = inconclusivo con limite superiore entro delta
    cat = {"superiorita'": "fav.", "non inferiorita'": "inc.$^\\\\delta$", "inferiorita'": "unf.", "inconclusivo": "inc."}''',
     '''    # le due scale di lettura, in celle separate (presentazione cambiata il 2026-10-30, analisi invariata): segno
    # dell'intervallo rispetto a zero (fav./unf./inc.) e margine (within delta = 0.005: yes se il limite superiore e'
    # sotto delta, la regola della «non inferiorita'» di E17)
    def scala(ic):
        lo, hi = ic
        return ("fav." if hi < 0 else ("unf." if lo > 0 else "inc.")), ("yes" if hi < 0.005 else "no")'''),
    ('''        righe.append(f"{nome(c)} & ${g['media_attuale']:+.3f}$ {cat[g['categoria_attuale']]} & "
                     f"${a['media']:+.3f}$ {cat[a['categoria_attuale']]}/{cat[a['categoria_per_sensore']]} & "
                     f"${b['media']:+.3f}$ {cat[b['categoria_attuale']]} \\\\\\\\".replace("$+0.000$", "$0.000$")
                     .replace("$-0.000$", "$0.000$"))''',
     '''        sg, dg = scala(g["ic_attuale"]); sa, da = scala(a["ic_attuale"]); sa2, da2 = scala(a["ic_per_sensore"]); sb, db = scala(b["ic_attuale"])
        righe.append(f"{nome(c)} & ${g['media_attuale']:+.3f}$ & {sg} & {dg} & "
                     f"${a['media']:+.3f}$ & {sa}/{sa2} & {da}/{da2} & "
                     f"${b['media']:+.3f}$ & {sb} & {db} \\\\\\\\".replace("$+0.000$", "$0.000$")
                     .replace("$-0.000$", "$0.000$"))'''),
]}


def main() -> int:
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, _ in coppie:
            if t.count(v) != 1:
                print(f"FERMO: in {f.relative_to(R)} il testo atteso compare {t.count(v)} volte:\n{v[:200]}"); return 1
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, n in coppie:
            t = t.replace(v, n)
        f.write_text(t); print(f"  {f.relative_to(R)}: {len(coppie)} sostituzioni")
    import py_compile
    for f in SOST:
        py_compile.compile(str(f), doraise=True)
    print("  compilazione: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
