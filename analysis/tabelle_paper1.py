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
    for g, st in (("Madrid", "-0.039"), ("Londra", "-0.035"), ("Melbourne", "-0.038"), ("PEMS08", "-0.133")):
        R.append(("I, II", f"A - C, {g}", "E8", "e8_risultati.json",
                  ["gruppi", g, "confronti", "A-C", "wce", "media"], st, _f3))
    # ---- Tabella II (colonna wCE contro C) -----------------------------------
    for k, val in (("F0-C", ("+0.073", "+0.050", "+0.078", "+0.156")),
                   ("F0p-C", ("+0.008", "+0.013", "+0.001", "-0.039"))):
        for (g, st) in zip(("Madrid", "Londra", "Melbourne", "PEMS08"), val):
            R.append(("II", f"{k}, {g}", "E8", "e8_risultati.json",
                      ["gruppi", g, "confronti", k, "wce", "media"], st, _f3))
    for (c, _), st in zip(CITTA, ("-0.011", "+0.034", "-0.019")):
        R.append(("II", f"F'(24 h) - C, {c}", "E2", "congelamento_e2.json",
                  ["confronti", f"{c}/Fp-C", "media"], st, _f3))
    for (c, _), st in zip(CITTA, ("-0.032", "-0.030", "-0.036")):
        R.append(("II", f"F'(1 wk) - C, {c}", "E4", "e4_risultati.json",
                  ["curva", f"{c}/Fp_672-C", "media"], st, _f3))
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
    nota = {"e6a_risultati.json": {"a": ("+0.003", "-0.007", "+0.013"), "b": ("-0.022", "-0.031", "-0.013"),
                                   "c": ("-0.033", "-0.047", "-0.019"), "d": ("-0.023", "-0.034", "-0.010")},
            "e6_risultati.json": {"a": ("-0.039", "-0.076", "-0.004"), "b": ("-0.034", "-0.071", "+0.009"),
                                  "c": ("-0.091", "-0.131", "-0.042"), "d": ("-0.074", "-0.118", "-0.023"),
                                  "e": ("+0.040", "-0.019", "+0.089")}}
    for f, dd in nota.items():
        rete = "PEMS04" if "e6a" in f else "PEMS08"
        for k, (m, lo, hi) in dd.items():
            R.append(("III nota", f"({k}) {rete} media", "E6", f, ["affermazioni", k, "media"], m, _f3))
            R.append(("III nota", f"({k}) {rete} IC basso", "E6", f, ["affermazioni", k, "ic_con_nodi", 0], lo, _f3))
            R.append(("III nota", f"({k}) {rete} IC alto", "E6", f, ["affermazioni", k, "ic_con_nodi", 1], hi, _f3))
    return R


def _leggi(d, via):
    if isinstance(via, tuple) and via[0] == "max":
        return max(d["affermazioni"][k]["media"] for k in via[1])
    if isinstance(via, tuple) and via[0] == "diff":
        return _leggi(d, via[1]) - _leggi(d, via[2])
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
        righe.append(r"\addlinespace")
    testa = (r"{\footnotesize\setlength{\tabcolsep}{3pt}" "\n" r"\begin{longtable}{@{}l l c c c c@{}}" "\n"
             r"\caption{Statements (a)--(e) of the replication (main paper, Table~III), per city and installation "
             r"episode: mean $\Delta$wCE over cells and 95\% interval from 4{,}000 joint resamples; last column: "
             r"sign per episode.}\\" "\n"
             r"\toprule" "\n" r"Statement & City & Episode 1 & Episode 2 & Episode 3 & Signs\\" "\n"
             r"\midrule" "\n" r"\endfirsthead" "\n" r"\toprule" "\n"
             r"Statement & City & Episode 1 & Episode 2 & Episode 3 & Signs\\" "\n" r"\midrule" "\n"
             r"\endhead" "\n")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("% generato da OR3/analysis/main.py (tabelle_paper1.scrivi_tabella_C1): non modificare a mano\n"
                 + testa + "\n".join(righe[:-1]) + "\n" + r"\bottomrule" + "\n" + r"\end{longtable}}" + "\n")
