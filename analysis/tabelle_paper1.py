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
import re
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
                   ("A-C_A", ("-0.038", "-0.033", "-0.037"))):   # C_A - C non piu' stampato (resta la quota)
        for (c, _), st in zip(CITTA, val):
            R.append(("II, §V", f"{k}, {c} (causale)", "E15", "congelamento_e15.json", E15(c, k), st, _f3))
    # rapporto costo di trasferimento / valore dell'identita': nel testo come intervallo «1.5 to 2.1» (terza lettura)
    RAP = [["risultati", "citta", c, "rapporti", "(F0-C)/(A-C_A)", "media"] for c, _ in CITTA]
    R.append(("§V-A", "(F0 - C)/(A - C_A), minimo sulle citta' (causale)", "E15", "congelamento_e15.json",
              ("max18", RAP), "1.5", lambda v: f"{-v:.1f}"))
    R.append(("§V-A", "(F0 - C)/(A - C_A), massimo sulle citta' (causale)", "E15", "congelamento_e15.json",
              ("min", RAP), "2.1", lambda v: f"{-v:.1f}"))
    for k, val in (("F0-C", "+0.156"), ("F0p-C", "-0.039")):
        R.append(("II", f"{k}, PEMS08", "E8", "e8_risultati.json",
                  ["gruppi", "PEMS08", "confronti", k, "wce", "media"], val, _f3))
    for (c, _), st in zip(CITTA, ("-0.011", "+0.032", "-0.020")):     # sei semi, episodio 1 (tabella C3)
        R.append(("III-B", f"F'(24 h) - C, {c} (sei semi, episodio 1)", "E5", "e5_risultati.json",
                  ["affermazioni", f"{c}/ep1/d", "media"], st, _f3))
    # (i valori della curva di Fig. 4 per F'(1 wk) - C non sono piu' stampati nel testo: revisione di leggibilita')
    for k, st in (("d", "-0.074"), ("e", "+0.040")):
        R.append(("III-B", f"({k}) PEMS08", "E6", "e6_risultati.json", ["affermazioni", k, "media"], st, _f3))
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
              "1, 2, 4 and 8", lambda v: ", ".join(map(str, v[:-1])) + " and " + str(v[-1])))
    # ---- Tabella III (segni per episodio) e nota ------------------------------
    # Tabella V (segni per episodio e «within delta»): generata da scrivi_tabella_replica, che legge i segni dai json
    # e si ferma se non coincidono con il campo `segno`; nel testo non c'e' piu' trascrizione da verificare
    # i valori di PEMS04/PEMS08 della vecchia nota alla Tab. III sono righe della tabella C1 del supplemento
    # (scrivi_tabella_C1), generate dai json: non c'e' trascrizione da verificare
    # ---- E18 (seconda revisione esterna): ROC empirica, bootstrap per sensore ---------------------------
    GA = lambda g, k, m: ["risultati", "A", "gruppi", g, "confronti", k, m, "media"]
    pt = lambda v: f"{100 * v:+.1f}"
    for k, g, st in (("F0-C", "PEMS08", "+0.008"), ("F0p-F0", "PEMS08", "-0.004")):
        R.append(("§V-A", f"dAUC {k}, {g} (E18)", "E18", "congelamento_e18.json", GA(g, k, "auc"), st, _f3))
    # nelle citta' i Delta AUC sono nel testo come intervallo «da ... a ...»: minimo e massimo sulle tre citta'
    CIT3 = ("Madrid", "Londra", "Melbourne")
    for k, lo, hi in (("F0-C", "-0.051", "-0.018"), ("F0p-F0", "+0.013", "+0.045"), ("A-C", "+0.017", "+0.036")):
        V = [GA(g, k, "auc") for g in CIT3]
        R.append(("§V-A", f"dAUC {k}, minimo sulle citta' (E18)", "E18", "congelamento_e18.json", ("min", V), lo, _f3))
        R.append(("§V-A", f"dAUC {k}, massimo sulle citta' (E18)", "E18", "congelamento_e18.json", ("max18", V), hi, _f3))
    V = [GA(g, "F0-C", "richiamo_fa_0.05") for g in CIT3]       # perdita di richiamo a FA 5 %, «1.3 to 4.5 points»
    R.append(("§V-A", "richiamo a FA 5 % F0-C, perdita minima sulle citta' (E18)", "E18", "congelamento_e18.json",
              ("max18", V), "1.3", lambda v: f"{-100 * v:.1f}"))
    R.append(("§V-A", "richiamo a FA 5 % F0-C, perdita massima sulle citta' (E18)", "E18", "congelamento_e18.json",
              ("min", V), "4.5", lambda v: f"{-100 * v:.1f}"))
    R.append(("§V-A", "richiamo a FA 5 % F0-C, PEMS08 (E18)", "E18", "congelamento_e18.json",
              GA("PEMS08", "F0-C", "richiamo_fa_0.05"), "+5.3", pt))
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


def testo_del_manoscritto(tex: Path) -> str:
    """Il testo di `tex` con i file di sezione richiamati da \\input espansi, ricorsivamente (dal 2026-11-03 il
    manoscritto e' diviso in sections/ e supplement/). Gli \\input di figures/ restano non espansi, come prima:
    sono tabelle generate, non testo trascritto."""
    def espandi(m):
        nome = m.group(1)
        if nome.startswith("figures/"):
            return m.group(0)
        return testo_del_manoscritto(tex.parent / (nome if nome.endswith(".tex") else nome + ".tex"))
    return re.sub(r"\\input\{([^}]+)\}", espandi, tex.read_text())


def verifica(ris: Path, ris_congelati: Path, tex: Path | None, esperimenti) -> list:
    """Per ogni cella: valore rigenerato (da `ris`), congelato (da `ris_congelati`),
    scarto, e confronto con il valore stampato (stesso arrotondamento del testo)."""
    t = None
    if tex is not None:
        t = _norm(testo_del_manoscritto(tex))
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
                         + f" & $({', '.join(R['stesso_segno'][f'{c}/{k}']['segni'])})$ \\\\")
        for g in ("PEMS04", "PEMS08"):
            r = P[g].get(k)
            righe.append(f" & {g} & " + (cella(r) + f" & -- & -- & ${r['segno']}$" if r else
                                          r"n.r. & -- & -- & --") + " \\\\")
        righe.append(r"\addlinespace")
    testa = (r"{\footnotesize\setlength{\tabcolsep}{3pt}" "\n" r"\begin{longtable}{@{}l l c c c c@{}}" "\n"
             r"\caption{Statements (a)--(e) of the replication (main paper, Table~V), per city and installation "
             r"episode: mean $\Delta$wCE over runs and 95\% interval from 4{,}000 joint resamples; last column: "
             r"sign per episode. Six seeds (201--206), pre-registered campaign; for the cities, the episode-1 values "
             r"of the main text come from the causal campaign on the same runs (Section~E). PEMS04 and PEMS08: one "
             r"installation date, pre-registered campaign; n.r.: not reportable ($A$ not trained on PEMS04).}\label{tab:suppC1}\\" "\n"
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
    # le due scale di lettura, in celle separate (presentazione cambiata il 2026-10-30, analisi invariata): segno
    # dell'intervallo rispetto a zero (fav./unf./inc.) e margine (within delta = 0.005: yes se il limite superiore e'
    # sotto delta, la regola della «non inferiorita'» di E17)
    def scala(ic):
        lo, hi = ic
        return ("fav." if hi < 0 else ("unf." if lo > 0 else "inc.")), ("yes" if hi < 0.005 else "no")
    en = {"Madrid": "Madrid", "Londra": "London", "Melbourne": "Melbourne", "PEMS08": "PEMS08", "PEMS04": "PEMS04"}
    nome = lambda c: (f"{en[c.split('/ep')[0]]} {c.split('/ep')[1]}" if "/ep" in c else en[c])
    righe = []
    for c, X in D.items():
        g = B[c]["differenze"]["(b) gated-F0p"]
        a, b = X["gated0-F0p"], X["gated0-gated"]
        sg, dg = scala(g["ic_attuale"]); sa, da = scala(a["ic_attuale"]); sa2, da2 = scala(a["ic_per_sensore"]); sb, db = scala(b["ic_attuale"])
        righe.append(f"{nome(c)} & ${g['media_attuale']:+.3f}$ & {sg} & {dg} & "
                     f"${a['media']:+.3f}$ & {sa}/{sa2} & {da}/{da2} & "
                     f"${b['media']:+.3f}$ & {sb} & {db} \\\\".replace("$+0.000$", "$0.000$")
                     .replace("$-0.000$", "$0.000$"))
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("% generato da OR3/analysis/main.py (tabelle_paper1.scrivi_tabella_politiche): non modificare a mano\n"
                 + "\n".join(righe) + "\n\\bottomrule\n")       # \bottomrule qui: dopo \input darebbe Misplaced \noalign


def scrivi_tabella_replica(ris: Path, f: Path) -> None:
    """Tabella V del testo (`tab:replication`): le cinque dichiarazioni pre-registrate su ogni contesto, con le due
    scale di lettura dagli stessi intervalli congelati — riga dei segni (−/+/0: intervallo sotto / sopra zero / lo
    include; verificati contro il campo `segno` dei json, si ferma se differiscono; per episodio, separati da virgole
    come la colonna «Signs» di C1) e riga «within delta» (y: limite superiore sotto 0.005). Citta': E5, episodi 1–3; PEMS08: E6; PEMS04: E6-bis parte A ((e) non riportabile).
    Presentazione cambiata il 2026-10-30, analisi invariata."""
    e5 = json.loads((ris / "e5_risultati.json").read_text())["affermazioni"]
    e6 = json.loads((ris / "e6_risultati.json").read_text())["affermazioni"]
    e6a = json.loads((ris / "e6a_risultati.json").read_text())["affermazioni"]
    ETIC = (("a", r"(a) $\Fzp-\C$"), ("b", r"(b) gated$-\Fzp$"), ("c", r"(c) $\Fp{\wk}-\C$"),
            ("d", r"(d) $\Fp{24\,h}-\C$"), ("e", r"(e) $\Fp{\wk}-\A$"))

    def scale(r, dove):
        lo, hi = r["ic_con_nodi"]
        s = "-" if hi < 0 else ("+" if lo > 0 else "0")
        if r.get("segno") is not None and r["segno"] != s:
            raise RuntimeError(f"Tabella V, {dove}: segno dall'intervallo {s!r} diverso dal campo congelato {r['segno']!r}")
        return s, ("y" if hi < 0.005 else "n")
    righe = []
    for k, et in ETIC:
        segni, delta = [], []
        for c, _ in CITTA:
            ss = [scale(e5[f"{c}/ep{n}/{k}"], f"{c}/ep{n}/{k}") for n in (1, 2, 3)]
            segni.append("$(" + ", ".join(s for s, _ in ss) + ")$"); delta.append("(" + ", ".join(d for _, d in ss) + ")")
        for src, nome in ((e6a, "PEMS04"), (e6, "PEMS08")):
            if k in src:
                s, d = scale(src[k], f"{nome}/{k}"); segni.append(f"${s}$" if s != "0" else "0"); delta.append(d)
            else:
                segni.append("n.r."); delta.append("n.r.")
        righe.append(et + " & " + " & ".join(segni) + " \\\\")
        righe.append("\\quad within $\\delta$ & " + " & ".join(delta) + " \\\\")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("% generato da OR3/analysis/main.py (tabelle_paper1.scrivi_tabella_replica): non modificare a mano\n"
                 + "\n".join(righe) + "\n\\bottomrule\n")
