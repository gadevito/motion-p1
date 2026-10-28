#!/usr/bin/env python3
"""
CONGELAMENTO_E15.md — campagna causale end-to-end (protocol/E15.md).
=====================================================================
Ogni numero viene da `results/evoluzione/e15_risultati.json` (prodotto da `esegui_e15.py --fase analizza`)
e dai file che esso cita (controllo a scarto zero, preflight, esiti e pilota). Scrive `CONGELAMENTO_E15.md`,
`results/evoluzione/congelamento_e15.json` e la copia `protocol/e15/e15_risultati.json`.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e15.py
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("results/evoluzione")
CITTA = ("Madrid", "Londra", "Melbourne")
NOMI = {"F0-C": "F₀ − C", "F0p-C": "F₀′ − C", "Fp_672-C": "F′(1 sett.) − C", "Fp_672-A": "F′(1 sett.) − A",
        "A-C": "A − C", "A-C_A": "A − C_A", "C_A-C": "C_A − C",
        "Fpk_672-C": "F′(1 sett.; k) − C", "Fpk_672-A": "F′(1 sett.; k) − A"}
SEGNO = {"-": "sotto zero", "+": "sopra zero", "0": "include lo zero"}
LIV = {"C": "C", "A": "A", "C_A": "C_A", "F0": "F₀", "F0p": "F₀′", "Fp_672": "F′(1 sett.)", "Fpk": "F′(1 sett.; k)"}


def imp(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def ic(r, dec=4):
    return f"{r['media']:+.{dec}f} [{r['ic_con_nodi'][0]:+.{dec}f}, {r['ic_con_nodi'][1]:+.{dec}f}]"


def rap(r):
    m = "—" if r["media"] is None else f"{r['media']:.3f}"
    return f"{m} [{r['ic_con_nodi'][0]:.3f}, {r['ic_con_nodi'][1]:.3f}]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    fj = a.out / "e15_risultati.json"
    R = json.loads(fj.read_text())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    n_celle = sum(R["citta"][c]["celle"] for c in CITTA)
    L = ["# CONGELAMENTO E15 — campagna causale end-to-end (statica a finestra espansiva)", "",
         f"Generato da `genera_congelamento_e15.py` al commit `{commit}`, {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
         f"Protocollo `protocol/E15.md` (impronta `{imp(Path('protocol/E15.md'))}`), firmato prima di ogni numero; "
         f"`e15_risultati.json` impronta `{imp(fj)}`. Statica «{R['statica']}»: iniziali con copertura media su [0, t₀); "
         f"nuovo sensore con finestra espansiva da t₀ all'origine corrente, minimo 24 h. Tre citta', episodio 1, partizioni "
         f"{R['partizioni']}, semi {R['semi']}: {n_celle} celle; {R['repliche']} ricampionamenti congiunti "
         f"(partizioni × semi × sensori, schema di E4), seme {R['seme_bootstrap']}, le STESSE estrazioni per le "
         f"differenze causali e per quelle congelate. Letture del protocollo del 27/10 (in `protocol/E15.md`): per A e "
         f"C_A i sensori di prova sono iniziali a tutti gli effetti, copertura su [0, t₀) in addestramento, selezione e "
         f"valutazione; la finestra minima di 24 h e l'espansione valgono per C, F₀, F₀′, F′ e per la selezione di k sui "
         f"nodi di validazione. **Rigenerato il 28/10/2026** con l'addendum di sola analisi del revisore (sezione 7-bis) e, "
         f"nello stesso giorno, con i registri dei tempi come ingresso congelato in `protocol/e15/tempi/` (sezione 7-ter) e con "
         f"il pilota letto da `protocol/e15/tempi/pilota_tempi_16.json` (terza rigenerazione): nuove impronte, numeri precedenti "
         f"invariati.", "",
         f"Perimetro: {R['perimetro']['principale']}; per i confronti a una settimana, {R['perimetro']['settimana']}. "
         f"Congelate: {R['perimetro']['congelate']}.", "",
         f"**Verdetto** = segno dell'intervallo al 95 % (sotto zero / include lo zero / sopra zero); una dichiarazione e' "
         f"*confermata* se il segno causale coincide con quello congelato. Accanto, la categoria di E17 (superiorita' = "
         f"limite superiore < 0; non inferiorita' = limite superiore < δ = {R['delta_non_inferiorita']}; inconclusivo) piu' la "
         f"simmetrica inferiorita' (limite inferiore > 0).", ""]

    # 1. controlli
    L += ["## 1. Controlli", ""]
    cz = R.get("controllo_scarto_zero")
    if cz:
        L.append(f"- **Scarto zero** (`--statica congelata`, stessi semi, braccio {cz['cella']['braccio']} {cz['cella']['contesto']} "
                 f"p{cz['cella']['partizione']} seme {cz['cella']['seme']}): wCE congelata {cz['wce_congelata']:.12f}, riprodotta "
                 f"{cz['wce_riprodotta']:.12f}, scarto {cz['scarto_assoluto']:.3e}; punto di controllo identico al bit: "
                 f"{'sì' if cz['punto_identico_al_bit'] else 'no'} (scarto massimo sui parametri {cz['scarto_massimo_parametri']:.3e}); "
                 f"macchina `{cz['macchina']}`. Verdetto: **{cz['verdetto']}**.")
    else:
        L.append("- Scarto zero: **controllo assente** (`controllo_e15.json` non trovato).")
    pf = R.get("preflight")
    if pf:
        L.append(f"- **Preflight** (15 controlli, il 15 sulla finestra espansiva), statica «{pf['statica']}»: "
                 f"{pf['celle'] - len(pf['rosse'])}/{pf['celle']} celle verdi" + (f"; rosse: {pf['rosse']}" if pf["rosse"] else "") + ".")
    else:
        L.append("- Preflight: **assente** (`e15_preflight.json` non trovato).")
    L += ["- **Perimetro**: per ogni cella, nodi e origini coincidono con la cella congelata di E5 (ep. 1) e di E4 (verificato per "
          "cella, `controllo_perimetro`); nodi nuovi assenti da E, E′, C, pesi e normalizzazione, presenti in A e C_A.",
          "- **Configurazione di F′**: quella congelata per citta' — " + "; ".join(
              f"{c} {R['k_secondaria'][c]['k_congelato']}/{R['k_secondaria'][c]['passo']:g}" for c in CITTA)
          + " (aggiornamenti/passo), verificata contro `configurazione_F.json`; F′(1 sett.) e F′(1 sett.; k = k congelato) danno "
            "aggregati identici (adattamento deterministico).", ""]

    # 2. le sette differenze
    L += ["## 2. Le sette differenze, con il verdetto causale accanto a quello congelato", ""]
    for c in CITTA:
        Rc = R["citta"][c]
        L += [f"### {c} — {Rc['celle']} celle, {Rc['nodi']} sensori nuovi", "",
              "| dichiarazione | perimetro | causale [IC 95 %] | verdetto | categoria | congelata, 54 celle [IC 95 %] | verdetto | esito | pubblicata, 12 semi [IC 95 %] |",
              "|---|---|---|---|---|---|---|---|---|"]
        for n in ("F0-C", "F0p-C", "Fp_672-C", "Fp_672-A", "A-C", "A-C_A", "C_A-C"):
            d = Rc["dichiarazioni"][n]
            if n in Rc["congelate"]:
                g = Rc["congelate"][n]
                pb = Rc["pubblicate"].get(n)
                L.append(f"| {NOMI[n]} | {d['perimetro']} | {ic(d)} | {SEGNO[d['segno']]} | {d['categoria']} | {ic(g)} | "
                         f"{SEGNO[g['segno']]} | {'confermata' if d['confermata'] else '**cambia**'} | "
                         f"{(ic(pb) + (' (' + str(pb['celle']) + ' celle)' if pb.get('celle') else '')) if pb else 'non pubblicata a 12 semi'} |")
            else:
                L.append(f"| {NOMI[n]} | {d['perimetro']} | {ic(d)} | {SEGNO[d['segno']]} | {d['categoria']} | — | — | nuova | — |")
        sc = [f"{NOMI[n]} {Rc['pubblicate'][n]['scarto_da_congelata_54']:+.4f}" for n in ("F0-C", "F0p-C", "Fp_672-C", "Fp_672-A", "A-C")
              if n in Rc["pubblicate"] and "scarto_da_congelata_54" in Rc["pubblicate"][n]]
        L += ["", "Pubblicata (12 semi) meno congelata (54 celle, stessi 6 semi): " + ("; ".join(sc) if sc else "nessuna pubblicata trovata")
              + ". Fonti: " + ", ".join(sorted({z['fonte'] for z in Rc['pubblicate'].values()})) + "." if Rc["pubblicate"] else
              "Pubblicate (12 semi): nessuna fonte trovata.", ""]
    es = R["esito"]
    L += ["### Esito", ""]
    if es["tutte_confermate"]:
        L.append("Le cinque dichiarazioni sono **confermate in tutte e tre le citta'**: la campagna causale diventa il risultato "
                 "principale e la congelata va nel supplemento come campagna pre-registrata, con le differenze per nome.")
    else:
        L.append(f"Cambiano: {', '.join(es['cambiano'])}. Il testo segue il verdetto causale e lo dice; le altre dichiarazioni "
                 f"sono confermate ({', '.join(c for c in CITTA if es['confermate_per_citta'][c])}: tutte e cinque).")
    for c in CITTA:
        Rc = R["citta"][c]; ai = Rc["dichiarazioni"]["A-C_A"]; cd = Rc["dichiarazioni"]["C_A-C"]; q = Rc["rapporti"]["(C_A-C)/(A-C)"]
        L.append(f"- {c}: A − C_A {ic(ai)} ({SEGNO[ai['segno']]}: {'l’identita’ vale da sola' if ai['segno'] == '-' else 'l’identita’ da sola non si distingue da zero'}); "
                 f"C_A − C {ic(cd)} ({SEGNO[cd['segno']]}); quota di A − C spiegata dal dato in piu', (C_A − C)/(A − C) = {rap(q)}"
                 + (" — **la maggior parte**: il «valore dell'identita'» va ridimensionato" if q["media"] is not None and q["media"] > 0.5 else "") + ".")
    L.append("")

    # 3. rapporti
    L += ["## 3. Rapporti (F₀ − C)/(A − C) e (F₀ − C)/(A − C_A)", "",
          "Rapporto delle medie nella stessa replica; tutte le origini dopo t₁. La colonna congelata usa le celle congelate "
          "(stesse estrazioni).", "",
          "| citta' | (F₀ − C)/(A − C) causale | (F₀ − C)/(A − C_A) causale | (F₀ − C)/(A − C) congelata, 54 celle | (F₀ − C)/(A − C) pubblicata, 12 semi | repliche senza divario al denominatore (A − C ≥ 0; A − C_A ≥ 0; cong.) |",
          "|---|---|---|---|---|---|"]
    for c in CITTA:
        q = R["citta"][c]["rapporti"]; pb = R["citta"][c]["pubblicate"].get("(F0-C)/(A-C)")
        L.append(f"| {c} | {rap(q['(F0-C)/(A-C)'])} | {rap(q['(F0-C)/(A-C_A)'])} | {rap(q['congelata (F0-C)/(A-C)'])} | "
                 f"{rap(pb) if pb else 'non pubblicata'} | "
                 f"{q['(F0-C)/(A-C)']['repliche_den_senza_divario']} / {q['(F0-C)/(A-C_A)']['repliche_den_senza_divario']} / "
                 f"{q['congelata (F0-C)/(A-C)']['repliche_den_senza_divario']} |")
    L.append("")

    # 4. secondaria k
    L += ["## 4. Secondaria: F′(1 sett.; k) con k riselezionato sull'episodio di validazione causale", "",
          "k scelto per citta' fra " + ", ".join(str(k) for k in sorted(int(k) for k in R["k_secondaria"][CITTA[0]]["wce_validazione"]))
          + " aggiornamenti (passo congelato) con la wCE media sulle origini con eta' > 1 settimana dell'episodio di validazione "
            f"(nodi di validazione, finestra espansiva); a pari merito il k minore. Scelta scritta in `e15_k_secondaria.json` "
            f"(impronta `{R['k_secondaria_file']['impronta']}`, {R['k_secondaria_file']['istante'][:16]} UTC) prima di ogni "
            f"valutazione sul test; ogni cella di prova registra la stessa impronta (verificato).", "",
          "| citta' | wCE validazione per k | k scelto | k congelato | F′(1 sett.; k) − C | verdetto | F′(1 sett.; k) − A | verdetto |",
          "|---|---|---|---|---|---|---|---|"]
    for c in CITTA:
        ks = R["k_secondaria"][c]; Rc = R["citta"][c]
        wv = ", ".join(f"k={k}: {v:.4f}" for k, v in sorted(ks["wce_validazione"].items(), key=lambda z: int(z[0])))
        d1, d2 = Rc["dichiarazioni"]["Fpk_672-C"], Rc["dichiarazioni"]["Fpk_672-A"]
        L.append(f"| {c} | {wv} | {ks['k']} | {ks['k_congelato']} | {ic(d1)} | {SEGNO[d1['segno']]} | {ic(d2)} | {SEGNO[d2['segno']]} |")
    L.append("")

    # 5. settimana
    L += ["## 5. Le stesse differenze sulle origini con eta' > 1 settimana (secondarie)", "",
          "| citta' | " + " | ".join(NOMI[n] for n in ("F0-C", "F0p-C", "A-C", "A-C_A", "C_A-C")) + " |",
          "|---|" + "---|" * 5]
    for c in CITTA:
        S = R["citta"][c]["secondarie_settimana"]
        L.append(f"| {c} | " + " | ".join(f"{ic(S[n])} ({S[n]['segno']})" for n in ("F0-C", "F0p-C", "A-C", "A-C_A", "C_A-C")) + " |")
    L.append("")

    # 6. livelli
    L += ["## 6. Livelli di wCE per braccio (media [IC 95 %])", "",
          "| citta' | origine | " + " | ".join(LIV[k] for k in ("C", "A", "C_A", "F0", "F0p")) + " | C (sett.) | A (sett.) | F′(1 sett.) (sett.) |",
          "|---|---|" + "---|" * 8]
    for c in CITTA:
        lv = R["citta"][c]["livelli"]

        def l_(o, n, f=""):
            k = f"{o}/{n}{f}"
            return f"{lv[k]['media']:.4f} [{lv[k]['ic_con_nodi'][0]:.4f}, {lv[k]['ic_con_nodi'][1]:.4f}]" if k in lv else "—"
        for o in ("causale", "congelata"):
            L.append(f"| {c} | {o} | " + " | ".join(l_(o, n) for n in ("C", "A", "C_A", "F0", "F0p")) + " | "
                     + " | ".join(l_(o, n, "/settimana") for n in ("C", "A", "Fp_672")) + " |")
    L.append("")

    # 7. costi
    co = R["costi"]
    L += ["## 7. Costi e macchina", ""]
    L.append("| braccio | addestramenti | minuti per addestramento (mediana, in concorrenza) | ore-macchina |")
    L.append("|---|---|---|---|")
    for b, z in co["addestramenti"].items():
        L.append(f"| {b} | {z['n']} | {('%.1f' % z['minuti_mediana']) if z['minuti_mediana'] is not None else '—'} | {z['ore_macchina']:.1f} |")
    tot = sum(z["n"] for z in co["addestramenti"].values())
    L.append("")
    if co.get("esito_e15"):
        e = co["esito_e15"]; amb = e.get("ambiente", {})
        L.append(f"Lancio: {tot} addestramenti ({e['completate']} nell'ultima sessione, {e['gia_fatte']} gia' fatte, "
                 f"{len(e['fallite'])} fallite), {e['lavoratori']} lavoratori × {e['fili']} filo/i, {e['ore_calendario']:.1f} h di "
                 f"calendario e {e['ore_macchina']:.1f} ore-macchina nell'ultima sessione; piattaforma `{amb.get('piattaforma')}`, "
                 f"{amb.get('nuclei_logici')} nuclei, torch {amb.get('torch')}, numpy {amb.get('numpy')}. Adattamenti: "
                 f"{co['adattamenti']} celle × 2 sulla prova (F′(1 sett.), F′(1 sett.; k)) + 3 k sulla validazione.")
    for nome, pz in sorted(co.get("pilota", {}).items()):
        L.append(f"Pilota dichiarato (`{co.get('pilota_fonte', nome)}`, ingresso congelato): {pz['n']} addestramenti E su {pz['contesto']} a {pz['lavoratori']} "
                 f"lavoratori, mediana {pz['minuti']['mediana']:.1f} min, stima {pz['stima_campagna']['ore']:.1f} h per "
                 f"{pz['stima_campagna']['addestramenti']} addestramenti, piattaforma `{pz['ambiente']['piattaforma']}`.")
    L.append("")

    # 7-bis. addendum del 28/10
    L += ["## 7-bis. Addendum del 28/10/2026 (revisore, sola analisi; correzione datata)", "",
          "Stesso congelamento rigenerato con due misure in piu', dalle stesse repliche; i numeri delle altre sezioni non "
          "cambiano. **Recupero causale** (E17): (L_C − L_F′(1 sett.))/(L_C − L_A) sulle origini con eta' > 1 settimana, "
          "rapporto delle medie nella stessa replica; anche con A − C_A al denominatore, (L_C − L_F′(1 sett.))/(L_C_A − L_A). "
          "**Riduzione del costo da parte del token**: 1 − (F₀′ − C)/(F₀ − C), tutte le origini dopo t₁.", "",
          "| citta' | recupero causale, (L_C − L_A) | recupero causale, (L_C_A − L_A) | recupero congelato, 54 celle | "
          "riduzione del token, causale | riduzione del token, congelata 54 celle | repliche con denominatore ≤ 0 (rec. c. / rec. c._A / rec. cong. / rid. c. / rid. cong.) |",
          "|---|---|---|---|---|---|---|"]
    for c in CITTA:
        ad = R["citta"][c].get("addendum")
        if not ad:
            L.append(f"| {c} | assente | | | | | |"); continue
        rc, rt = ad["recupero"], ad["riduzione_token"]
        L.append(f"| {c} | {rap(rc['causale (L_C-L_A)'])} | {rap(rc['causale (L_C_A-L_A)'])} | {rap(rc['congelata 54 celle (L_C-L_A)'])} | "
                 f"{rap(rt['causale'])} | {rap(rt['congelata 54 celle'])} | "
                 f"{rc['causale (L_C-L_A)']['repliche_den_non_positivo']} / {rc['causale (L_C_A-L_A)']['repliche_den_non_positivo']} / "
                 f"{rc['congelata 54 celle (L_C-L_A)']['repliche_den_non_positivo']} / {rt['causale']['repliche_den_non_positivo']} / "
                 f"{rt['congelata 54 celle']['repliche_den_non_positivo']} |")
    L.append("")

    # 7-ter. registri dei tempi come ingresso congelato (revisore, 28/10)
    TEMPI = Path("protocol/e15/tempi")
    L += ["## 7-ter. Registri dei tempi (ingresso congelato, `protocol/e15/tempi/`)", "",
          "I marcatori `.fatto` dei 270 addestramenti (secondi, ambiente, istante), l'esito del lancio e il pilota dichiarato, "
          "copiati dai risultati nel repo: la fase E15 di `main.py` li tratta come ingresso, non li rigenera. Per ogni file "
          "l'impronta (sha256, 16 esadecimali); dove il file originale e' ancora nei risultati, l'impronta e' verificata uguale.", ""]
    reg_tempi, n_ver, n_diff = {}, 0, 0
    ORIG = {"E": a.out / "e15_E_inserimento_griglia", "E1": a.out / "e15_E1_inserimento_griglia",
            "C": a.out / "e15_inserimento_griglia", "A": a.out / "e15_inserimento_griglia", "C_A": a.out / "e15_inserimento_griglia"}
    if TEMPI.exists():
        for b in ("E", "E1", "C", "A", "C_A"):
            ff = sorted((TEMPI / b).glob("*.fatto")) if (TEMPI / b).exists() else []
            sec = []
            for f in ff:
                d = json.loads(f.read_text()); i_ = imp(f); sec.append(float(d["secondi"]))
                o = ORIG[b] / f.name
                stato = "—"
                if o.exists():
                    stato = "uguale" if imp(o) == i_ else "**DIVERSA**"; n_ver += 1; n_diff += stato != "uguale"
                reg_tempi[f"{b}/{f.name}"] = {"impronta": i_, "secondi": float(d["secondi"]), "verifica": stato}
            L.append(f"- **{b}**: {len(ff)} marcatori, {sum(sec)/3600:.1f} ore-macchina"
                     + (f", mediana {sorted(sec)[len(sec)//2]/60:.1f} min" if sec else "") + ".")
        for nome in ("esito_e15.json", "pilota_tempi_16.json"):
            f = TEMPI / nome
            if f.exists():
                o = (a.out / "e15_inserimento_griglia" / nome) if nome.startswith("esito") else (a.out / "E_pilota_e15" / nome)
                stato = ("uguale" if imp(o) == imp(f) else "**DIVERSA**") if o.exists() else "—"
                if o.exists():
                    n_ver += 1; n_diff += stato != "uguale"
                reg_tempi[nome] = {"impronta": imp(f), "verifica": stato}
                L.append(f"- `{nome}` `{imp(f)}` (verifica con i risultati: {stato}).")
            else:
                L.append(f"- `{nome}`: **assente** in `protocol/e15/tempi/`.")
        L += ["", f"Verifiche contro i risultati: {n_ver} file confrontati, {n_diff} diversi.", "",
              "| file | secondi | impronta | verifica |", "|---|---|---|---|"]
        for k, z in reg_tempi.items():
            if "secondi" in z:
                L.append(f"| `{k}` | {z['secondi']:.0f} | `{z['impronta']}` | {z['verifica']} |")
    else:
        L.append("**`protocol/e15/tempi/` assente**: i registri dei tempi non sono ancora stati copiati nel repo.")
    L.append("")

    # 8. impronte (la copia in protocol/e15/ si fa a mano, al commit del congelamento: il generatore non scrive nel repo)
    J = {"commit": commit, "istante": datetime.now(timezone.utc).isoformat(), "risultati": R, "registri_tempi": reg_tempi,
         "impronte": {"e15_risultati.json": imp(fj), "protocol/E15.md": imp(Path("protocol/E15.md"))}}
    (a.out / "congelamento_e15.json").write_text(json.dumps(J, indent=1, ensure_ascii=False))
    L += ["## 8. Impronte", "",
          "- Fonti delle pubblicate: " + (", ".join(f"`{k}` `{v['impronta']}`" for k, v in R["pubblicate_fonti"].items()) if R["pubblicate_fonti"] else "nessuna") + ".",
          f"- `results/evoluzione/e15_risultati.json` `{imp(fj)}` (copia committata in `protocol/e15/`); `protocol/E15.md` "
          f"`{imp(Path('protocol/E15.md'))}`; `results/evoluzione/congelamento_e15.json` `{imp(a.out / 'congelamento_e15.json')}`.",
          f"- Punti di controllo per cella (sha256, 16 esadecimali) in `e15_risultati.json` → `impronte_celle` "
          f"({len(R['impronte_celle'])} celle × {len([k for k in next(iter(R['impronte_celle'].values())) if not k.startswith('impronta_')])} "
          f"bracci, piu' l'impronta del punto E)."]
    Path("CONGELAMENTO_E15.md").write_text("\n".join(L) + "\n")
    print(f"  CONGELAMENTO_E15.md (impronta {imp(Path('CONGELAMENTO_E15.md'))}); json {imp(a.out / 'congelamento_e15.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
