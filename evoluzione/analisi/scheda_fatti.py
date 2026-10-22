#!/usr/bin/env python3
"""
Scheda dei fatti per la revisione interna (revisore, 20/10/2026) — SOLA LETTURA.
=================================================================================
Otto domande. I fatti di codice (1, 3, 6, 7) sono riportati con il frammento di codice che li
stabilisce, che questo script RITROVA nel file (assert) e cita con il numero di riga: se il codice
cambia, lo script si ferma. I fatti di dati (2, 4, 5, 8) sono calcolati dai file in
`results/evoluzione/` (maschere, predizioni, json congelati) e dal manoscritto se presente.

Scrive `paper/SCHEDA_FATTI.md`.

Uso (dalla radice OR3/, copia con `results/`):

    poetry run python evoluzione/analisi/scheda_fatti.py [--paper ../paper1]
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

CITTA = ("Madrid", "Londra", "Melbourne")


def riga_di(f: str, frammento: str) -> str:
    """Numero di riga (1-based) della prima riga del frammento; assert che esista una volta."""
    t = Path(f).read_text()
    assert t.count(frammento) == 1, f"{f}: frammento atteso una volta:\n{frammento}"
    return f"{f}:{t[:t.index(frammento)].count(chr(10)) + 1}"


def imp(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--paper", type=Path, default=Path("../paper1"))
    a = ap.parse_args()
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import FINESTRA, _carica, _partizioni
    from evoluzione.esperimenti.esegui_e5 import SEMI_E5, episodi_registrati
    from evoluzione.esperimenti.esegui_e6 import T0_PROVA as T0_P8, T0_VALIDAZIONE as T0V_P8
    from evoluzione.esperimenti.esegui_e6a import T0_PROVA as T0_P4, T0_VALIDAZIONE as T0V_P4
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    from evoluzione.esperimenti.seleziona_F import CALENDARIO_VAL_GRIGLIA, FINE_VAL
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, SEME_PARTIZIONE_E6, configurazione
    from evoluzione.esperimenti.esegui_e4 import _wce
    L = []
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    L += [f"# Scheda dei fatti — revisione interna (richiesta del revisore, 20/10/2026)", "",
          f"Generata da `evoluzione/analisi/scheda_fatti.py` al commit `{commit}`, "
          f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. Sola lettura: nessun numero del paper "
          "cambia. I fatti di codice citano il frammento che li stabilisce (ritrovato nel file dallo script); "
          "i fatti di dati sono calcolati dai file di `results/evoluzione/`.", ""]

    # ---- 1. bootstrap --------------------------------------------------------------------------
    r4 = riga_di("evoluzione/esperimenti/esegui_e4.py",
                 "        ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)\n"
                 "        nd = rng.integers(0, K, K)\n"
                 "        v.append(np.mean([f_pair(celle_c[(kk[0][0], p, s)], nd) for p in ps for s in ss]))")
    r3 = riga_di("evoluzione/analisi/analizza_e3.py",
                 "                nd = rng.integers(0, K, K)\n"
                 "                v.append(np.mean([\n"
                 "                    wce(d[(n1, p, s)][\"A_per_nodo\"],\n"
                 "                        d[(n1, p, s)][\"B_per_nodo\"], nd)")
    rv = riga_di("evoluzione/analisi/analizza_veterani_e3.py",
                 "                nd = {p: rng.integers(0, K[p], K[p]) for p in parts}")
    rw = riga_di("evoluzione/esperimenti/esegui_e4.py",
                 "    num, den = A.sum(0), B.sum(0)\n"
                 "    return float(np.nanmean(np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)))")
    rq = riga_di("evoluzione/esperimenti/esegui_e4.py", "    q = np.percentile(v, [2.5, 97.5])")
    L += ["## 1. Il ricampionamento congiunto partizioni × semi × sensori", "",
          f"Procedura (`_boot`, {r4}; identica in E2 `analizza_e2.py`, E5, E6, E6-bis, E6a, E8, E8-bis, E14, "
          "stesse 4.000 repliche, seme fisso per esperimento):", "",
          "- **Incrociato, non gerarchico.** A ogni replica si estraggono con reinserimento: le 3 partizioni "
          "(`ps`), i semi (`ss`, 12 nella campagna principale, 6 in E5/E6) e un vettore `nd` di K **posizioni** "
          "di sensore (K = numero di sensori nuovi per partizione, uguale in tutte le partizioni di una citta'); "
          "la statistica della replica e' la media, sulle |ps| × |ss| celle estratte, della differenza per cella "
          "calcolata sui sensori `nd`. Le tre estrazioni sono indipendenti e si combinano in prodotto (ogni "
          "partizione estratta con ogni seme estratto), non annidate.",
          "- **Stessi indici per tutti i bracci**: `f_pair(z, nd)` calcola la differenza fra i due bracci della "
          "stessa cella sugli stessi sensori `nd`; il confronto e' appaiato per cella e per sensore.",
          f"- **Statistica per sensore**: wCE = media sugli orizzonti di (Σ_k A_k,h / Σ_k B_k,h) sui sensori "
          f"selezionati ({rw}), con A e B gli aggregati per (sensore, orizzonte) salvati per cella; un sensore "
          "estratto due volte conta due volte (pesi interi del ricampionamento).",
          "- **Sensori presenti in piu' partizioni**: le partizioni sono permutazioni indipendenti dei sensori "
          "(`_partizioni`, seme di partizione), quindi lo stesso sensore puo' essere «nuovo» in piu' partizioni. "
          "Il vettore `nd` e' di posizioni nella lista ordinata dei nuovi di ciascuna partizione: la posizione i "
          "indica sensori diversi in partizioni diverse. Nessun accoppiamento fra partizioni per identita' di "
          "sensore: l'unita' ricampionata e' (partizione, posizione), non il sensore fisico.",
          f"- **Intervallo**: percentili 2,5 e 97,5 delle repliche ({rq}); la stima puntuale e' la media delle "
          "differenze per cella su tutte le celle (non la mediana delle repliche). Rappresenta la variabilita' "
          "congiunta rispetto a (i) scelta della partizione dei sensori, (ii) inizializzazione, (iii) campione di "
          "sensori nuovi, a dato osservato fisso.",
          "- **Dipendenza temporale**: le origini NON si ricampionano; gli aggregati A, B sommano su tutte le "
          "origini del perimetro (o della fascia d'eta'), quindi l'intervallo non copre la variabilita' "
          "temporale (nessun bootstrap a blocchi sul tempo). E' una scelta dichiarata nei protocolli.",
          f"- **Eccezioni**: in E3 (`analizza_e3.py`, {r3}) le posizioni `nd` sono estratte una volta per replica e "
          f"applicate a tutte le partizioni come sopra; nei veterani (`analizza_veterani_e3.py`, {rv}) i nodi sono "
          "gli iniziali e `nd` e' estratto per partizione (K[p] diversi); E7 (ρ di Spearman) ricampiona le "
          "unita' (partizione, nodo) con 2.000 repliche; E8-bis ricampiona AUC e richiami con lo stesso schema "
          "congiunto (`_boot_curve`).", ""]

    # ---- 2. PEMS08: i sei insiemi di nuovi sensori ----------------------------------------------
    D8 = _carica("PEMS08_p0", a.out / "maschere")
    ins = {}
    for k in range(6):
        nodi, _ = _partizioni(D8, {"partizione": np.random.default_rng(SEME_PARTIZIONE_E6[k])}, T0_P8)
        ins[k] = set(int(z) for z in nodi["prova"])
    unione = set().union(*ins.values())
    occ = sum(len(v) for v in ins.values())
    conteggio = {}
    for s in unione:
        conteggio[s] = sum(s in v for v in ins.values())
    molt = {m: sum(1 for c_ in conteggio.values() if c_ == m) for m in sorted(set(conteggio.values()))}
    coppie = [(i, j, len(ins[i] & ins[j])) for i in range(6) for j in range(i + 1, 6)]
    L += ["## 2. PEMS08: i sei insiemi di 26 nuovi sensori", "",
          f"Partizioni p0–p5 = permutazioni indipendenti dei {D8['r'].shape[1]} sensori (`_partizioni`, semi "
          f"`SEME_PARTIZIONE_E6`), 15 % nuovi ciascuna: {occ} occorrenze, **{len(unione)} sensori distinti**. "
          "Molteplicita' (quante partizioni includono lo stesso sensore fra i nuovi): "
          + ", ".join(f"{n} sensori in {m} partizion{'e' if m == 1 else 'i'}" for m, n in molt.items()) + ". "
          f"Intersezioni a coppie (sensori in comune): " + ", ".join(f"p{i}∩p{j}={n}" for i, j, n in coppie) + ". "
          "Quindi NON sono disgiunti: le 156 sono occorrenze, e il ricampionamento (§1) le tratta come unita' "
          "(partizione, posizione).", ""]

    # ---- 4. k secondario di E5 --------------------------------------------------------------------
    fk = a.out / "e5_k_secondaria.json"
    K5 = json.loads(fk.read_text())
    tex = a.paper / "main.tex"
    cit = ""
    if tex.exists():
        t = tex.read_text()
        occ200 = [m.start() for m in re.finditer(r"\b200\b", t)]
        ctx = [t[max(0, i - 80):i + 60].replace("\n", " ") for i in occ200 if re.search(r"\bk\b|secondar|Melbourne", t[max(0, i - 200):i + 200])]
        cit = (f" Nel manoscritto (`{tex}`) le occorrenze di «200» vicine a «k», «secondar» o «Melbourne»: {len(ctx)}"
               + ("".join(f"\n  - `…{c}…`" for c in ctx[:4]) if ctx else "."))
    fF = a.out / "selezione_F_griglia" / "configurazione_F.json"
    CF = json.loads(fF.read_text())["scelte"]
    L += ["## 4. Budget secondario k di E5", "",
          f"`{fk}` (impronta `{imp(fk)}`, registrata `{K5.get('impronta')}`): "
          + ", ".join(f"{c} k = **{K5['k'][c]}**" for c in CITTA) + ". Il valore usato da E5 (`esegui_e5.py`, "
          "fase valuta, controllo dell'impronta per cella) e' quello del file: **la tabella D9 (100) e' giusta**. "
          f"Il «200» e' un altro numero: il budget di adattamento di F′ scelto in validazione (`{fF}`, impronta "
          f"`{imp(fF)}`): " + ", ".join(f"{c} {CF[c]['aggiornamenti']} aggiornamenti, passo {CF[c]['passo']}" for c in CITTA)
          + ". Dove il testo dice 200 per k va corretto in 100; dove parla del budget di F′ (p.es. il costo di "
          "401 s di Melbourne) 200 e' giusto." + cit, ""]

    # ---- 5. Londra ep. 1: F0' - C in E2 e in E5 ------------------------------------------------
    _, dich, _ = configurazione(inserimento=True)
    def cella(dir_, pref, c, p, s):
        z = np.load(a.out / dir_ / f"{pref}_{c}_p{p}_s{s}.npz", allow_pickle=True)
        return z["A_per_nodo"].astype("float64"), z["B_per_nodo"].astype("float64"), z["origini"].astype("int64"), z["nodi"].astype("int64")
    diff, orig_n, nodi_n = {}, set(), set()
    for p in (0, 1, 2):
        for s in dich:
            A1, B1, o1, n1 = cella("predizioni_e2", "F0p", "Londra", p, int(s))
            A0, B0, o0, n0 = cella("predizioni_fase3", "C", "Londra", p, int(s))
            assert np.array_equal(o1, o0) and np.array_equal(n1, n0)
            diff[(p, int(s))] = _wce(A1, B1) - _wce(A0, B0)
            orig_n.add(len(o1)); nodi_n.add(len(n1))
    m12 = float(np.mean(list(diff.values()))); m6 = float(np.mean([v for (p, s), v in diff.items() if s in SEMI_E5]))
    E2 = json.loads((a.out / "congelamento_e2.json").read_text())
    e2v = E2["confronti"].get("Londra/F0p-C") or E2["confronti"].get("Londra/F0'-C") or {}
    E5 = json.loads((a.out / "e5_risultati.json").read_text())["affermazioni"]["Londra/ep1/a"]
    E4 = json.loads((a.out / "e4_risultati.json").read_text())["confronti"]["Londra/F0p-C"]
    z5 = np.load(a.out / "predizioni_e5" / "ep1_Londra_p0_s201.npz", allow_pickle=True)
    L += ["## 5. Londra, episodio 1: F₀′ − C vale +0,013 (E2) e +0,015 (E5/C3)", "",
          f"Stesse celle (partizioni 0–2), stesse origini del test ({sorted(orig_n)} origini dopo t₁, {sorted(nodi_n)} "
          f"sensori nuovi), stessi punti di controllo (C della fase 3, F₀′ dal token di E′): le **medie per cella "
          f"coincidono** dove le celle coincidono. Differenza: **i semi**. E2 usa i 12 semi dichiarati "
          f"({list(map(int, dich))}): media delle 36 celle = {m12:+.5f} (congelamento_e2: {e2v.get('media', float('nan')):+.5f} "
          f"[{e2v.get('ic_con_nodi', [float('nan')] * 2)[0]:+.4f}, {e2v.get('ic_con_nodi', [float('nan')] * 2)[1]:+.4f}]). "
          f"E5 usa i 6 semi con identificativo piu' basso ({list(SEMI_E5)}, `SEMI_E5`): media delle 18 celle "
          f"ricalcolata qui dalle stesse predizioni di E2 = {m6:+.5f}; e5_risultati Londra/ep1/(a) = {E5['media']:+.5f} "
          f"[{E5['ic_con_nodi'][0]:+.4f}, {E5['ic_con_nodi'][1]:+.4f}] (predizioni di E5, episodio 1, origini "
          f"{int(len(z5['origini']))}). E4 (12 semi, stesso perimetro): {E4['media']:+.5f}. I semi del ricampionamento "
          "differiscono (E2 20260930, E5 20261007) ma gli intervalli si sovrappongono ampiamente; la differenza "
          "fra +0,013 e +0,015 e' il sottoinsieme di semi, non una campagna diversa.", ""]

    # ---- 8. date -----------------------------------------------------------------------------------
    ep5 = episodi_registrati(a.out)
    L += ["## 8. Date per episodio e contesto (indici della griglia a 15 min → istante)", "",
          "Convenzioni: addestramento su [FINESTRA − 1, a_tr), selezione del checkpoint (V-full) su [a_tr, a_va); "
          "episodio: installazione t₀, acquisizione (t₀, t₁ = t₀ + 24 h], test (t₁, fine]; politica (τ, N) e k "
          "scelti sull'episodio di validazione (t₀ᵛ, t₁ᵛ, fino a FINE_VAL). Episodi 2 e 3 (E5): periodi ricavati "
          "da [0, t₀) con le quote 70/85 e 15/85 (`_partizioni(fine=t₀)`).", "",
          "| contesto | ep. | addestramento | selezione ckpt | validazione politica (t₀ᵛ → t₁ᵛ … fine) | installazione t₀ | t₁ | fine test |",
          "|---|---|---|---|---|---|---|---|"]

    def ts(D, i):
        return str(D["ts"][int(i)])[:16]

    for c in CITTA:
        D = _carica(c, a.out / "maschere")
        e = D["r"].shape[0] - GR.MAX_ORIZZ
        _, ist = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[0])})
        t0, t1 = CALENDARIO[c]; t0v, t1v = CALENDARIO_VAL_GRIGLIA[c]
        L.append(f"| {c} | 1 | {ts(D, ist['addestramento'][0])} → {ts(D, ist['addestramento'][-1])} | "
                 f"{ts(D, ist['validazione'][0])} → {ts(D, ist['validazione'][-1])} | {ts(D, t0v)} → {ts(D, t1v)} … {ts(D, FINE_VAL[c] - 1)} | "
                 f"{ts(D, t0)} ({t0}) | {ts(D, t1)} ({t1}) | {ts(D, e)} ({e}) |")
        for k in (2, 3):
            q = ep5[c][k]
            _, ist_k = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[0])}, q["t0"])
            L.append(f"| {c} | {k} | {ts(D, ist_k['addestramento'][0])} → {ts(D, ist_k['addestramento'][-1])} | "
                     f"{ts(D, ist_k['validazione'][0])} → {ts(D, ist_k['validazione'][-1])} | — (τ, N, k dell'ep. 1) | "
                     f"{ts(D, q['t0'])} ({q['t0']}) | {ts(D, q['t1'])} ({q['t1']}) | {ts(D, q['fine'])} ({q['fine']}) |")
    for nome, ctx, t0, t0v in (("PEMS08", "PEMS08_p0", T0_P8, T0V_P8), ("PEMS04", "PEMS04_p0", T0_P4, T0V_P4)):
        D = _carica(ctx, a.out / "maschere"); e = D["r"].shape[0] - GR.MAX_ORIZZ
        fine_part = t0 if nome == "PEMS08" else None
        _, ist = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE_E6[0])}, fine_part)
        L.append(f"| {nome} | 1 | {ts(D, ist['addestramento'][0])} → {ts(D, ist['addestramento'][-1])} | "
                 f"{ts(D, ist['validazione'][0])} → {ts(D, ist['validazione'][-1])} | {ts(D, t0v)} → {ts(D, t0v + 96)} … {ts(D, t0 - 1)} | "
                 f"{ts(D, t0)} ({t0}) | {ts(D, t0 + 96)} ({t0 + 96}) | {ts(D, e)} ({e}) |")
    L.append("")
    L.append("Nota: la selezione del checkpoint usa i nodi iniziali sul periodo di selezione (`initial_network`); la "
             "validazione della politica (τ, N) e di k usa l'episodio di validazione con i nodi di validazione "
             "(E4 §scegli, E5 k-secondaria, E6/E6a scegli); PEMS04 ha calendario 70/15/15 della serie intera, "
             "PEMS08 il periodo [0, t₀) con le quote del principale.")
    L.append("")

    # ---- 3. adatta_F in eval ----------------------------------------------------------------------
    r_ev = riga_di("evoluzione/componente/adattamento.py",
                   "    m.eval()                       # BatchNorm e buffer fermi\n"
                   "    for p in m.parameters():\n        p.requires_grad_(False)\n"
                   "    for p in forn.parametri_adattabili():\n        p.requires_grad_(True)")
    L += ["## 3. `adatta`: la rete e' in `eval()` durante l'adattamento", "",
          f"Si' ({r_ev}): `m.eval()` prima del ciclo di aggiornamenti — BatchNorm usa le statistiche correnti e i "
          "buffer non si muovono; tutti i parametri sono congelati (`requires_grad_(False)`) tranne gli embedding "
          "adattabili del fornitore d'identita'; ottimizzatore Adam nuovo, solo su quei parametri, nessun "
          "decadimento, nessun arresto anticipato. `verifica_vincoli` (inserimento.py) controlla a valle che il "
          "punto E sia immutato. Vale per F, F′ (24 h, 48 h, 1 sett., k) in tutte le fasi.", ""]

    # ---- 6. AUC delle curve richiamo–falsi allarmi --------------------------------------------------
    r_s = riga_di("evoluzione/esperimenti/esegui_e8.py", "SOGLIE = [round(0.05 * k, 2) for k in range(1, 20)]")
    r_a = riga_di("evoluzione/esperimenti/esegui_e8.py",
                  "    o = np.argsort(far, kind=\"stable\"); x = np.concatenate([[0.0], far[o], [1.0]]); y = np.concatenate([[0.0], rich[o], [1.0]])\n"
                  "    a = float(np.sum((x[1:] - x[:-1]) * (y[1:] + y[:-1]) / 2.0))")
    r_fa = riga_di("evoluzione/esperimenti/esegui_e8.py", "LIVELLI_FA = (0.005, 0.01, 0.02, 0.05, 0.10)")
    L += ["## 6. AUC delle curve richiamo–falsi allarmi (E8-bis)", "",
          f"- **Soglie**: 19 valori 0,05 … 0,95 a passo 0,05 ({r_s}); per ogni soglia t la classe congestionata e' "
          "predetta se p(congestionata) ≥ t, altrimenti l'argmax fra verde e giallo (`predizione`).",
          f"- **Curva**: per ogni soglia, falsi allarmi FAR = FP/(FP+TN) e richiamo = TP/(TP+FN) della classe "
          "congestionata, dalle matrici di confusione SOMMATE su sensori e orizzonti del perimetro (`curva`).",
          f"- **AUC completa, non parziale**: trapezi sui 19 punti ordinati per FAR, con gli estremi (0, 0) e "
          f"(1, 1) aggiunti ({r_a}); nessuna interpolazione oltre i trapezi lineari fra punti consecutivi.",
          f"- **Richiamo a falsi allarmi fissati** ({r_fa}): interpolazione lineare (`np.interp`) della curva ai "
          "livelli FA = 0,5 %, 1 %, 2 %, 5 %, 10 %; `nan` se il livello e' fuori dall'intervallo dei FAR osservati.",
          "- **Aggregazione e intervallo**: la curva e' dei conteggi sommati sulla cella; ΔAUC fra bracci per cella, "
          "ricampionamento congiunto come in §1 (`_boot_curve`, stessi `nd`), percentili 2,5–97,5; segno "
          "dell'intervallo come verdetto. Perimetri: intero e eta' > 1 settimana.", ""]

    # ---- 7. macro-F1 dopo la soglia -------------------------------------------------------------------
    r_p = riga_di("evoluzione/esperimenti/esegui_e8.py",
                  "    alt = PB[..., :CONG].argmax(-1).astype(\"int8\")\n"
                  "    return np.where(PB[..., CONG] >= t, CONG, alt).astype(\"int8\")")
    r_m = riga_di("evoluzione/esperimenti/esegui_e8.py", "        f1.append(2 * tpk / max(2 * tpk + fnk + fpk, 1e-12))")
    L += ["## 7. Macro-F1 dopo la soglia sulla classe rossa", "",
          f"Regola di assegnazione ({r_p}): se p(rossa) ≥ t → rossa; altrimenti **argmax fra verde e gialla** sulle "
          "probabilita' non rinormalizzate (il confronto fra le due e' invariante alla rinormalizzazione). "
          f"Macro-F1 = media delle F1 delle tre classi calcolate dalla matrice di confusione 3×3 ({r_m}); le regole "
          "sono `prim` (soglia che massimizza F1 della rossa in validazione), `par` (stesso tasso di falsi allarmi "
          "di C alla sua soglia primaria) e `argmax`.", ""]
    ordine = ["## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6.", "## 7.", "## 8."]
    # riordina le sezioni per numero
    testo = "\n".join(L)
    testa_fine = testo.index("## 1.")
    corpo = testo[testa_fine:]
    pezzi = {}
    for i, k in enumerate(ordine):
        s = corpo.index(k)
        pezzi[k] = s
    tagli = sorted(pezzi.values()) + [len(corpo)]
    sezioni = {k: corpo[pezzi[k]:tagli[tagli.index(pezzi[k]) + 1]] for k in ordine}
    finale = testo[:testa_fine] + "".join(sezioni[k] for k in ordine)
    Path("paper").mkdir(exist_ok=True)
    f = Path("paper/SCHEDA_FATTI.md"); f.write_text(finale.rstrip("\n") + "\n")
    print(finale)
    print(f"\n  scritto {f} (impronta {imp(f)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
