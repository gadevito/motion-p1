#!/usr/bin/env python3
"""
Patch di `genera_congelamento_e3bis.py` — sezione 3 (costi), difetto 17.
=========================================================================
La prima versione scriveva «almeno 6×» dividendo la mediana di R-orig(1 sett.)
sulle tre citta' (2268 s) per il solo F′(1 sett.) misurato in isolamento
(Melbourne, 406 s). Dopo la patch lo script legge R-orig(1 sett.) **per citta'**
dai manifesti isolati di `inserimento_griglia_672`, verifica che la mediana
sulle nove celle coincida con `costi_e3bis.json`, e riporta il rapporto solo
dove numeratore e denominatore sono misurati nella stessa citta'. Ogni
sostituzione e' letterale: se il testo atteso non c'e' (una volta sola), si
ferma senza toccare il file.

Uso (dalla radice OR3/):

    poetry run python patch_e3bis_costi.py
    poetry run python genera_congelamento_e3bis.py
"""
from pathlib import Path

F = Path("genera_congelamento_e3bis.py")
S = F.read_text()

SOSTITUZIONI = [
    # 1. documento(): tabella e rapporto
    ('''    a("| configurazione | calcolo all'inserimento | attesa dati | rimisure che riproducono la concorrente |")
    a("|---|---|---|---|")
    a(f"| R-orig(1 sett.) | **{r['inserimento_s']:.0f} s** | {r['attesa_dati_s']/3600:.0f} h | "
      f"{r['rimisure_che_riproducono_la_concorrente']}/{r['esecuzioni_isolate']} |")
    for c in CITTA:
        g = K4["tabella"]["gated"][c]
        if g["tau"] == 672:
            a(f"| F′(1 sett.) {c} (da costi_e4) | {g['adattamento_s']:.0f} s | {g['attesa_dati_s']/3600:.0f} h | — |")
    a(f"| F′(24 h) (da costi_e4) | {K4['tabella']['Fp']['inserimento_s']:.0f} s | 24 h | — |")
    fp_w = [K4["tabella"]["gated"][c]["adattamento_s"] for c in CITTA if K4["tabella"]["gated"][c]["tau"] == 672]
    if fp_w:
        a("")
        citta_w = [c for c in CITTA if K4["tabella"]["gated"][c]["tau"] == 672]
        a(f"Rapporto di calcolo a parita' di dati: R-orig(1 sett.) / F′(1 sett.) = "
          f"**almeno {r['inserimento_s'] / max(fp_w):.0f}×**: il denominatore e' l'unico F′(1 sett.) "
          f"misurato in isolamento ({', '.join(citta_w)}, {max(fp_w):.0f} s, con la configurazione F "
          f"piu' costosa, 200 aggiornamenti); a Madrid e Londra F ha 50 aggiornamenti e il rapporto "
          f"sarebbe maggiore. Il confronto dei costi del paper e' ora a dati simmetrici: il "
          f"riaddestramento compra pochi millesimi a diverse volte il costo, non nulla a cento.")
''',
     '''    RO = R["R-orig_per_citta"]
    a("| configurazione | calcolo all'inserimento | attesa dati | rimisure che riproducono la concorrente |")
    a("|---|---|---|---|")
    a(f"| R-orig(1 sett.), mediana sulle {r['esecuzioni_isolate']} celle delle tre citta' | "
      f"**{r['inserimento_s']:.0f} s** | {r['attesa_dati_s']/3600:.0f} h | "
      f"{r['rimisure_che_riproducono_la_concorrente']}/{r['esecuzioni_isolate']} |")
    for c in CITTA:
        a(f"| R-orig(1 sett.) {c} (mediana su {RO[c]['n']} semi) | **{RO[c]['inserimento_s']:.0f} s** | "
          f"{r['attesa_dati_s']/3600:.0f} h | {RO[c]['n']}/{RO[c]['n']} |")
    for c in CITTA:
        g = K4["tabella"]["gated"][c]
        if g["tau"] == 672:
            a(f"| F′(1 sett.) {c} (da costi_e4) | {g['adattamento_s']:.0f} s | {g['attesa_dati_s']/3600:.0f} h | — |")
    a(f"| F′(24 h) (da costi_e4) | {K4['tabella']['Fp']['inserimento_s']:.0f} s | 24 h | — |")
    citta_w = [c for c in CITTA if K4["tabella"]["gated"][c]["tau"] == 672]
    citta_no = [c for c in CITTA if c not in citta_w]
    if citta_w:
        a("")
        rapporti = "; ".join(f"{c} **{RO[c]['inserimento_s'] / K4['tabella']['gated'][c]['adattamento_s']:.1f}×**"
                             f" ({RO[c]['inserimento_s']:.0f} s / {K4['tabella']['gated'][c]['adattamento_s']:.0f} s)"
                             for c in citta_w)
        a(f"Rapporto di calcolo a parita' di dati, R-orig(1 sett.) / F′(1 sett.), **nella stessa citta'**: "
          f"{rapporti}. In E4 F′(1 sett.) e' misurato in isolamento solo dove tau = 672 ({', '.join(citta_w)}); "
          f"per {', '.join(citta_no)} il rapporto non si calcola qui (i tempi appaiati nelle tre citta' e su "
          f"PEMS08 sono in `costi_appaiati.json`, misura successiva). Il confronto dei costi del paper e' a "
          f"dati simmetrici: il riaddestramento compra pochi millesimi a diverse volte il costo, non nulla a cento.")
'''),
    # 2. documento(): dichiarazione della correzione
    ('''    a("- Le fasce d'eta' della valutazione restano quelle di E3; con t₁ = t₀ + 672 tutte le origini "
      "valutate cadono nella terza.")
''',
     '''    a("- Le fasce d'eta' della valutazione restano quelle di E3; con t₁ = t₀ + 672 tutte le origini "
      "valutate cadono nella terza.")
    a("- **Correzione del 2026-10-10 (difetto 17 del registro)**: la prima versione della sezione 3 "
      "scriveva «almeno 6×» dividendo la mediana di R-orig(1 sett.) sulle nove celle delle tre citta' "
      "per il solo F′(1 sett.) misurato in isolamento (Melbourne, la configurazione F piu' costosa nella "
      "citta' piu' piccola). Lo script ora riporta R-orig(1 sett.) per citta' dai manifesti isolati e il "
      "rapporto solo nella stessa citta'; il documento e' rigenerato, non modificato a mano.")
'''),
    # 3. main(): R-orig per citta' dai manifesti isolati
    ('''    print("[3/4] costi"); K = leggi(a.out / "costi_e3bis.json"); K4 = leggi(a.out / "costi_e4.json")
''',
     '''    print("[3/4] costi"); K = leggi(a.out / "costi_e3bis.json"); K4 = leggi(a.out / "costi_e4.json")
    RO = {}
    for c in CITTA:
        v = []
        for s in (201, 202, 203):
            m = leggi(d / f"R-orig_{c}_p0_s{s}.json")
            if m.get("modalita_misura") != "isolata" or "rimisura_di" not in m:
                raise IngressoMancante(f"R-orig_{c}_p0_s{s}.json non e' una rimisura isolata")
            v.append(float(m["costo"]["inserimento_s"]))
        v.sort(); RO[c] = {"n": len(v), "inserimento_s": v[len(v) // 2], "valori": v}
    tutte = sorted(x for c in CITTA for x in RO[c]["valori"])
    if len(tutte) != 9 or abs(tutte[4] - K["R-orig"]["inserimento_s"]) > 1e-9:
        raise IngressoMancante(f"mediana sulle {len(tutte)} celle {tutte[len(tutte) // 2]:.1f} s diversa da "
                               f"costi_e3bis.json {K['R-orig']['inserimento_s']:.1f} s")
'''),
    ('''         "esecuzioni": E, "risultati": RS, "costi": K, "costi_e4": K4, "impronte": {f: h(f) for f in FILE}}
''',
     '''         "esecuzioni": E, "risultati": RS, "costi": K, "costi_e4": K4, "R-orig_per_citta": RO,
         "impronte": {f: h(f) for f in FILE}}
'''),
]

for vecchio, nuovo in SOSTITUZIONI:
    n = S.count(vecchio)
    assert n == 1, f"testo atteso trovato {n} volte, non 1:\n{vecchio[:120]}"
    S = S.replace(vecchio, nuovo)
F.write_text(S)
compile(S, str(F), "exec")
print(f"  {F}: {len(SOSTITUZIONI)} sostituzioni applicate, compila")
