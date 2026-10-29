"""
Le tabelle del Paper 1: per ogni cella, il valore stampato nel manoscritto e il
punto del file rigenerato da cui deve uscire. `analysis/main.py` le verifica
dopo la rigenerazione (valori arrotondati come nel testo).

Chi cambia una tabella del manoscritto cambia qui la riga corrispondente; un
numero del manoscritto che non ha una riga qui non e' verificato.
Esperimento "ingresso": il file non e' rigenerato da main.py (tempi misurati),
si confronta il valore stampato con il file congelato.
Non sono qui (lo dice il rapporto): dati di disegno (sensori, partizioni, semi,
giorni), R - C del resoconto, R-orig(24 h) e l'addestramento iniziale (in
attesa dei tempi per citta').
"""
import json
from pathlib import Path

CITTA = (("Madrid", "Mad."), ("Londra", "Lon."), ("Melbourne", "Mel."))


def _f3(x):                     # come nel testo: segno esplicito, tre decimali
    return f"{x:+.3f}".replace("+0.000", "0.000")


def _righe():
    R = []
    # ---- Tabella I ---------------------------------------------------------
    for c, et in CITTA:
        R.append(("I", f"origini > 1 sett., {et}", "E4", "e4_risultati.json",
                  ["curva", f"{c}/origini_comuni"], {"Madrid": "869", "Londra": "883", "Melbourne": "854"}[c], str))
    for g, st in (("PEMS04", "168"), ("PEMS08", "1423")):
        R.append(("I", f"origini > 1 sett., {g}", "E6", "e6_origini_comuni.json",
                  [g, "origini_comuni"], st, str))
    # citta', episodio 1: campagna causale (E15), risultato principale per le cinque dichiarazioni
    E15 = lambda c, k: ["risultati", "citta", c, "dichiarazioni", k, "media"]
    for (c, _), st in zip(CITTA, ("-0.040", "-0.034", "-0.045")):
        R.append(("I, II", f"A - C, {c} (causale)", "E15", "congelamento_e15.json", E15(c, "A-C"), st, _f3))
    R.append(("I, II", "A - C, PEMS08", "E8", "e8_risultati.json",
              ["gruppi", "PEMS08", "confronti", "A-C", "wce", "media"], "-0.133", _f3))
    # ---- Tabella II (colonna wCE contro C) -----------------------------------
    for k, val in (("F0-C", ("+0.075", "+0.049", "+0.078")), ("F0p-C", ("+0.008", "+0.014", "0.000")),
                   ("Fp_672-C", ("-0.031", "-0.031", "-0.040")), ("Fp_672-A", ("+0.008", "+0.008", "-0.002")),
                   ("A-C_A", ("-0.038", "-0.033", "-0.037")), ("C_A-C", ("-0.002", "-0.001", "-0.008"))):
        for (c, _), st in zip(CITTA, val):
            R.append(("II, §V", f"{k}, {c} (causale)", "E15", "congelamento_e15.json", E15(c, k), st, _f3))
    for (c, _), st in zip(CITTA, ("1.95", "1.47", "2.13")):
        R.append(("§V-A", f"(F0 - C)/(A - C_A), {c} (causale)", "E15", "congelamento_e15.json",
                  ["risultati", "citta", c, "rapporti", "(F0-C)/(A-C_A)", "media"], st, lambda v: f"{-v:.2f}"))
    for (c, _), st in zip(CITTA, ("0.05", "0.03", "0.19")):
        R.append(("§V-A", f"(C_A - C)/(A - C), {c} (causale)", "E15", "congelamento_e15.json",
                  ["risultati", "citta", c, "rapporti", "(C_A-C)/(A-C)", "media"], st, "{:.2f}".format))
    for k, val in (("F0-C", "+0.156"), ("F0p-C", "-0.039")):
        R.append(("II", f"{k}, PEMS08", "E8", "e8_risultati.json",
                  ["gruppi", "PEMS08", "confronti", k, "wce", "media"], val, _f3))
    for (c, _), st in zip(CITTA, ("-0.011", "+0.034", "-0.019")):
        R.append(("II", f"F'(24 h) - C, {c}", "E2", "congelamento_e2.json",
                  ["confronti", f"{c}/Fp-C", "media"], st, _f3))
    # (i valori della curva di Fig. 4 per F'(1 wk) - C non sono piu' stampati nel testo: revisione di leggibilita')
    for k, st in (("d", "-0.074"), ("e", "+0.040")):
        R.append(("II-B", f"({k}) PEMS08", "E6", "e6_risultati.json", ["affermazioni", k, "media"], st, _f3))
    R.append(("II, III", "F'(1 wk) - C, PEMS08", "E6", "e6_risultati.json",
              ["affermazioni", "c", "media"], "-0.091", _f3))
    R.append(("II", "gated - F0', massimo sui nove episodi", "E5", "e5_risultati.json",
              ("max", [f"{c}/ep{e}/b" for c, _ in CITTA for e in (1, 2, 3)]), "<= +0.004",
              lambda v: "<= +0.004" if v <= 0.004 else _f3(v)))
    # ---- Tabella II (tempi), abstract, §III-§V: sessione unica sul Mac fermo -----
    # costi_tabella_sessione.json: secondi, mediana sui semi; addestramento in minuti
    T = {"Madrid": ("14", "138", "2225", "2229", "16.1", "41.1", "41.2"),
         "Londra": ("15", "139", "2228", "2228", "16.1", "41.0", "41.1"),
         "Melbourne": ("39", "401", "1556", "1557", "3.9", "29.1", "29.2"),
         "PEMS08": ("13", "127", "377", "379", "3.0", "7.1", "7.1")}
    for ctx, st in T.items():
        via = ["tabella", ctx]
        for i, (k, f) in enumerate((("Fp_96", "{:.0f}"), ("Fp_672", "{:.0f}"), ("R-orig_96", "{:.0f}"),
                                    ("R-orig_672", "{:.0f}"))):
            R.append(("II tempi", f"{k}, {ctx}", "ingresso", "costi_tabella_sessione.json", via + [k], st[i],
                      f.format))
        R.append(("II tempi", f"R-orig(1 wk) / F'(1 wk), {ctx}", "ingresso", "costi_tabella_sessione.json",
                  ("rapporto", via + ["R-orig_672"], via + ["Fp_672"]), st[4], "{:.1f}".format))
        for k, j in (("C", 5), ("E1", 6)):
            R.append(("II tempi", f"addestramento {k} (min), {ctx}", "ingresso", "costi_tabella_sessione.json",
                      ("minuti", via + [k]), st[j], "{:.1f}".format))
    # ---- §III: architettura dai checkpoint ------------------------------------
    A, A1 = ["sintesi", "E_inserimento_griglia"], ["sintesi", "E1_inserimento_griglia"]
    for voce, via, st in (("dimensione dell'embedding", A + ["d_emb"], "8"),
                          ("canali Traffic4cast", A + ["c_in"], "9"),
                          ("canali PEMS", ["sintesi", "E1_e6_pems08", "c_in"], "11"),
                          ("canali nascosti", A + ["nascosti"], "32"),
                          ("blocchi", A + ["n_blocchi"], "4"),
                          ("uscite (4 orizzonti x 3 classi)", A + ["uscita"], "12"),
                          ("K Melbourne", A + ["K", 0], "415"),
                          ("K Madrid e Londra", A + ["K", 1], "630"),
                          ("parametri del token", ("diff", A1 + ["parametri", 0], A + ["parametri", 0]), "8"),
                          ("finestra (passi)", ["codice", "finestra_passi"], "12"),
                          ("nucleo", ["codice", "nucleo"], "2"),
                          ("campo ricettivo (passi)", ["codice", "campo_ricettivo"], "16")):
        R.append(("§III", voce, "ARCH", "architettura_ck.json", via, st, str))
    P08, P04 = ["sintesi", "E_e6_pems08"], ["sintesi", "E1_e6_pems04"]
    for voce, via, st in (("K PEMS04", P04 + ["K", 0], "214"), ("K PEMS08", P08 + ["K", 0], "118"),
                          ("parametri Madrid e Londra", A + ["parametri", 1], "28752"),
                          ("parametri Melbourne", A + ["parametri", 0], "27032"),
                          ("parametri PEMS08", P08 + ["parametri", 0], "24720"),
                          ("parametri PEMS04 (E')", P04 + ["parametri", 0], "25496"),
                          ("corpo condiviso, 9 canali", ("corpo", A, 1), "23712"),
                          ("corpo condiviso, 11 canali", ("corpo", P08, 0), "23776")):
        R.append(("§III", voce, "ARCH", "architettura_ck.json", via, st, lambda v: str(int(v))))
    R.append(("§III", "dilatazioni", "ARCH", "architettura_ck.json", ["codice", "dilatazioni"],
              "1, 2, 4, 8", lambda v: ", ".join(map(str, v))))
    # ---- Tabella III (segni per episodio) e nota ------------------------------
    stampati = {"a": ("++0", "+++", "0++"), "b": ("--0", "---", "-0-"), "c": ("---", "---", "---"),
                "d": ("--0", "+00", "-+-"), "e": ("+++", "+++", "0++")}
    for k, ss in stampati.items():
        for (c, et), st in zip(CITTA, ss):
            R.append(("III", f"({k}) {et}", "E5", "e5_risultati.json",
                      ["stesso_segno", f"{c}/{k}", "segni"], st, "".join))
    for k, s04, s08 in (("a", "0", "-"), ("b", "-", "0"), ("c", "-", "-"), ("d", "-", "-"), ("e", None, "0")):
        if s04 is not None:
            R.append(("III", f"({k}) PEMS04", "E6", "e6a_risultati.json", ["affermazioni", k, "segno"], s04, str))
        R.append(("III", f"({k}) PEMS08", "E6", "e6_risultati.json", ["affermazioni", k, "segno"], s08, str))
    # i valori di PEMS04/PEMS08 della vecchia nota alla Tab. III sono righe della tabella C1 del supplemento
    # (scrivi_tabella_C1), generate dai json: non c'e' trascrizione da verificare
    # ---- E18 (seconda revisione esterna): ROC empirica, bootstrap per sensore ---------------------------
    GA = lambda g, k, m: ["risultati", "A", "gruppi", g, "confronti", k, m, "media"]
    pt = lambda v: f"{100 * v:+.1f}"
    for k, g, st in (("F0-C", "Madrid", "-0.051"), ("F0-C", "Londra", "-0.018"), ("F0-C", "Melbourne", "-0.030"),
                     ("F0-C", "PEMS08", "+0.008"), ("F0p-F0", "Madrid", "+0.045"), ("F0p-F0", "Londra", "+0.013"),
                     ("F0p-F0", "Melbourne", "+0.031"), ("F0p-F0", "PEMS08", "-0.004")):
        R.append(("§V-A", f"dAUC {k}, {g} (E18)", "E18", "congelamento_e18.json", GA(g, k, "auc"), st, _f3))
    for k, g, st in (("F0-C", "Madrid", "-3.9"), ("F0-C", "Londra", "-1.3"), ("F0-C", "Melbourne", "-4.5"),
                     ("F0-C", "PEMS08", "+5.3"), ("A-C", "Madrid", "+2.6"), ("A-C", "Londra", "+1.9"),
                     ("A-C", "Melbourne", "+2.5")):
        R.append(("§V-A", f"richiamo a FA 5 % {k}, {g} (E18)", "E18", "congelamento_e18.json",
                  GA(g, k, "richiamo_fa_0.05"), st, pt))
    for g, st in (("Madrid", "92"), ("Londra", "84"), ("Melbourne", "80")):
        R.append(("§V-A", f"quota recuperata a FA 5 %, {g} (E18)", "E18", "congelamento_e18.json",
                  ["risultati", "A", "gruppi", g, "recupero_argmax", "quota_recuperata", "media"], st,
                  lambda v: f"{100 * v:.0f}"))
    R.append(("§V-B", "dAUC F'(1 wk) - C, minimo sui cinque contesti (E18)", "E18", "congelamento_e18.json",
              ("min", [GA(g, "Fp_672-C", "auc") for g in ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")]),
              "+0.007", _f3))
    R.append(("§V-B", "dAUC F'(1 wk) - C, massimo sui cinque contesti (E18)", "E18", "congelamento_e18.json",
              ("max18", [GA(g, "Fp_672-C", "auc") for g in ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")]),
              "+0.032", _f3))
    MB = lambda c, k: ["risultati", "B", "contesti", c, "differenze", k, "margine_minimo_per_sensore"]
    for c, k, st in (("E3-bis Madrid", "Rorig_672-Fp_672 >1sett", "0.006"), ("E3-bis Londra", "Rorig_672-Fp_672 >1sett", "0.005"),
                     ("E3-bis Melbourne", "Rorig_672-Fp_672 >1sett", "0.020"), ("PEMS08", "E17 Rorig_672-Fp_672 >1sett", "0.100")):
        R.append(("§V-B", f"margine minimo per sensore, {c} (E18)", "E18", "congelamento_e18.json", MB(c, k), st,
                  "{:.3f}".format))
    return R


def _leggi(d, via):
    if isinstance(via, tuple) and via[0] == "max":
        return max(d["affermazioni"][k]["media"] for k in via[1])
    if isinstance(via, tuple) and via[0] in ("min", "max18"):
        vals = [_leggi(d, v) for v in via[1]]
        return min(vals) if via[0] == "min" else max(vals)
    if isinstance(via, tuple) and via[0] == "diff":
        return _leggi(d, via[1]) - _leggi(d, via[2])
    if isinstance(via, tuple) and via[0] == "corpo":            # parametri - K x d_emb
        x = _leggi(d, via[1])
        return x["parametri"][via[2]] - x["K"][via[2]] * x["d_emb"]
    if isinstance(via, tuple) and via[0] == "rapporto":
        return _leggi(d, via[1]) / _leggi(d, via[2])
    if isinstance(via, tuple) and via[0] == "minuti":
        return _leggi(d, via[1]) / 60
    for k in via:
        d = d[k]
    return d


def _norm(t: str) -> str:
    for x in ("$", "{", "}", "\\", ",", " ", "\n"):
        t = t.replace(x, "")
    return t


def _nel_tex(stampato: str, tex: str) -> bool:
    return _norm(stampato) in tex


def verifica(ris: Path, ris_congelati: Path, tex: Path | None, esperimenti) -> list:
    """Per ogni cella: valore rigenerato (da `ris`), congelato (da `ris_congelati`),
    scarto, e confronto con il valore stampato (stesso arrotondamento del testo)."""
    t = None
    if tex is not None:
        t = _norm(tex.read_text())
    cache, out = {}, []

    def carica(d, f):
        if (d, f) not in cache:
            cache[(d, f)] = json.loads((d / f).read_text())
        return cache[(d, f)]

    for tab, voce, esp, f, via, stampato, fmt in _righe():
        r = {"tabella": tab, "voce": voce, "file": f, "stampato": stampato}
        try:
            v = _leggi(carica(ris, f), via)
            v0 = _leggi(carica(ris_congelati, f), via)
            r["rigenerato_valore"], r["congelato_valore"] = v, v0
            if isinstance(v, (int, float)) and isinstance(v0, (int, float)) and not isinstance(v, bool):
                d = v - v0
                r["scarto"] = "0" if d == 0 else f"{d:+.2e}"
            else:
                r["scarto"] = "=" if v == v0 else "≠"
            r["rigenerato"] = fmt(v) if callable(fmt) else str(v)
            if esp == "ingresso":
                r["esito"] = "DIVERSO" if r["rigenerato"] != stampato else \
                    "NON TROVATO NEL TEX" if t is not None and not _nel_tex(stampato, t) else "ok (ingresso)"
            elif esp not in esperimenti:
                r["esito"] = f"non rigenerato ({esp} escluso)"
            elif r["rigenerato"] != stampato or r["scarto"] == "≠":
                r["esito"] = "DIVERSO"
            elif t is not None and not stampato.startswith("<=") and not _nel_tex(stampato, t):
                r["esito"] = "NON TROVATO NEL TEX"
            else:
                r["esito"] = "ok"
        except (KeyError, IndexError, FileNotFoundError, TypeError) as e:
            r["rigenerato"] = f"errore: {e!r}"
            r["esito"] = "ERRORE"
        out.append(r)
    return out


def scrivi_tabella_C1(ris: Path, f: Path) -> None:
    """Tabella C1 del materiale supplementare: (a)-(e) per citta' ed episodio, da
    e5_risultati.json (rigenerato), come longtable LaTeX."""
    R = json.loads((ris / "e5_risultati.json").read_text())
    P = {"PEMS04": json.loads((ris / "e6a_risultati.json").read_text())["affermazioni"],
         "PEMS08": json.loads((ris / "e6_risultati.json").read_text())["affermazioni"]}
    en = {"Madrid": "Madrid", "Londra": "London", "Melbourne": "Melbourne"}
    tit = {"a": r"(a) $F_0'-C$", "b": r"(b) gated$-F_0'$", "c": r"(c) $F'(1\,\mathrm{wk})-C$",
           "d": r"(d) $F'(24\,\mathrm{h})-C$", "e": r"(e) $F'(1\,\mathrm{wk})-A$"}
    cella = lambda r: f"${r['media']:+.3f}$ $[{r['ic_con_nodi'][0]:+.3f}, {r['ic_con_nodi'][1]:+.3f}]$"
    righe = []
    for k in "abcde":
        for i, c in enumerate(en):
            rr = [R["affermazioni"][f"{c}/ep{e}/{k}"] for e in (1, 2, 3)]
            righe.append((tit[k] if i == 0 else "") + f" & {en[c]} & " + " & ".join(cella(r) for r in rr)
                         + f" & {''.join(R['stesso_segno'][f'{c}/{k}']['segni'])} \\\\")
        for g in ("PEMS04", "PEMS08"):
            r = P[g].get(k)
            righe.append(f" & {g} & " + (cella(r) + f" & -- & -- & ${r['segno']}$" if r else
                                          r"n.r. & -- & -- & --") + " \\\\")
        righe.append(r"\addlinespace")
    testa = (r"{\footnotesize\setlength{\tabcolsep}{3pt}" "\n" r"\begin{longtable}{@{}l l c c c c@{}}" "\n"
             r"\caption{Statements (a)--(e) of the replication (main paper, Table~V), per city and installation "
             r"episode: mean $\Delta$wCE over cells and 95\% interval from 4{,}000 joint resamples; last column: "
             r"sign per episode. Six seeds (201--206), pre-registered campaign; for the cities, the episode-1 values "
             r"of the main text come from the causal campaign on the same cells (Section~E). PEMS04 and PEMS08: one "
             r"installation date, pre-registered campaign; n.r.: not reportable ($A$ not trained on PEMS04).}\\" "\n"
             r"\toprule" "\n" r"Statement & City & Episode 1 & Episode 2 & Episode 3 & Signs\\" "\n"
             r"\midrule" "\n" r"\endfirsthead" "\n" r"\toprule" "\n"
             r"Statement & City & Episode 1 & Episode 2 & Episode 3 & Signs\\" "\n" r"\midrule" "\n"
             r"\endhead" "\n")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("% generato da OR3/analysis/main.py (tabelle_paper1.scrivi_tabella_C1): non modificare a mano\n"
                 + testa + "\n".join(righe[:-1]) + "\n" + r"\bottomrule" + "\n" + r"\end{longtable}}" + "\n")


def scrivi_tabella_politiche(ris: Path, f: Path) -> None:
    """Tabella delle politiche nel testo (revisione di leggibilita'): per gli undici contesti, gated(tau,N) - F0'
    e gated(1 sett., 0) - F0' con le categorie (attuale e per sensore) e gated(1 sett., 0) - gated(tau,N),
    da congelamento_e18.json (parte B per gated(tau,N) - F0', parte D per il resto)."""
    R = json.loads((ris / "congelamento_e18.json").read_text())["risultati"]
    B, D = R["B"]["contesti"], R["D"]["contesti"]
    cat = {"superiorita'": "sup.", "non inferiorita'": "n.-i.", "inferiorita'": "inf.", "inconclusivo": "inc."}
    en = {"Madrid": "Madrid", "Londra": "London", "Melbourne": "Melbourne", "PEMS08": "PEMS08", "PEMS04": "PEMS04"}
    nome = lambda c: (f"{en[c.split('/ep')[0]]} {c.split('/ep')[1]}" if "/ep" in c else en[c])
    righe = []
    for c, X in D.items():
        g = B[c]["differenze"]["(b) gated-F0p"]
        a, b = X["gated0-F0p"], X["gated0-gated"]
        righe.append(f"{nome(c)} & ${g['media_attuale']:+.3f}$ {cat[g['categoria_attuale']]} & "
                     f"${a['media']:+.3f}$ {cat[a['categoria_attuale']]}/{cat[a['categoria_per_sensore']]} & "
                     f"${b['media']:+.3f}$ {cat[b['categoria_attuale']]} \\\\".replace("$+0.000$", "$0.000$")
                     .replace("$-0.000$", "$0.000$"))
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("% generato da OR3/analysis/main.py (tabelle_paper1.scrivi_tabella_politiche): non modificare a mano\n"
                 + "\n".join(righe) + "\n\\bottomrule\n")       # \bottomrule qui: dopo \input darebbe Misplaced \noalign
