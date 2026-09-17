#!/usr/bin/env python3
"""
Censimento dei CSV per FIRMA DI CONTENUTO.
==========================================
NON SPOSTA NULLA di suo. Con `--genera-script` scrive uno script di
spostamento da rileggere prima di eseguire.

PERCHE' PER FIRMA E NON PER FILE. Con centinaia di CSV un elenco file per file
e' illeggibile. Lo script raggruppa i file che hanno lo STESSO CONTENUTO
strutturale — stesso insieme di modelli, stesse colonne, stesse metriche — e ne
stampa una riga sola con conteggio, intervallo di date ed esempio. Centinaia di
file collassano in poche decine di righe.

IL VOCABOLARIO E' RICAVATO DAL CODICE, non indovinato:

  gwn_none / gwn_fixed / gwn_adaptive / gwn_both
        Graph WaveNet, le modalita' di `--modes` (gomo_classify, gomo_sparse).
        `none` e' il controllo temporale, `fixed` il grafo dato, `adaptive`
        l'adiacenza appresa.
  stid  MLP per-nodo in stile STID, classe autonoma dentro gomo_classify.
  idw / idw_dist / knn / nbr_idw / nbr_prior
        i CINQUE riferimenti di interpolazione spaziale (gomo_sparse, riga 283).
        Non sono addestrati: si calcolano DENTRO la stessa invocazione dei
        modelli neurali e ne condividono maschera, suddivisione e metrica.
        Sono attivi SOLO nel regime severo, quindi la loro presenza identifica
        un file di R3 anche quando il nome non lo dice.
  hist_prior / persistence / hist_avg
        priore storico di classe e i due riferimenti continui (gomo_baselines).
  lgb_fair       LightGBM a parita' di informazione.
  agcrn / dcrnn  riferimenti ricorrenti (gomo_rnn_baselines).
  staeformer / t4c_gnn
        STAEformer compatto e GCN in stile Traffic4cast (gomo_sota_baselines).
        Il secondo esiste al SOLO orizzonte di quindici minuti.
  base / weather / placebo
        i tre rami di gomo_weather_ablation. Il ramo `base` compare in OGNI
        file ed e' il collaudo: a parita' di seme deve coincidere fra varianti.
  transductive / ign   identita' da attributi statici (gomo_ign).
  temporal / graph
        harness di REGRESSIONE (gomo_stgnn): riportano MAE e RMSE, non entropia
        pesata, e NON appartengono alla suite principale.

Uso (dalla radice OR3/):

    poetry run python censimento_csv.py
    poetry run python censimento_csv.py --firma 3
    poetry run python censimento_csv.py --genera-script riordino.sh
"""
from pathlib import Path
import argparse
import datetime as dt
import re
import shlex
from collections import defaultdict

import pandas as pd

IGNORA = {".git", "__pycache__", ".venv", "node_modules", "__MACOSX", "_archivio"}

# CARTELLE INTOCCABILI. Contengono dati SORGENTE e artefatti costruiti dalla
# pipeline: anagrafiche dei sensori, serie annuali, scarichi grezzi di Austin,
# varianti di soglia, descrittori. Non sono risultati di campagne e spostarli
# romperebbe ogni percorso del README. Lo script li classifica come `sorgente`
# e NON li include mai nello script di spostamento.
SORGENTE = {"data_collection", "austin", "descrittori", "geo_sweep",
            "prereg", "papers", "kit_archivio"}

# Anagrafiche di cui esistono piu' revisioni. La revisione conta: dal 6/7/2026
# `traffic_sensors.csv` su Hugging Face ha perso `max_capacity` e `has_data`, e
# gli esperimenti che le richiedono devono usare quella dei run originali
# (revision 7b8dbd3476). Le copie datate vanno quindi TENUTE TUTTE.
ANAGRAFICHE = ("traffic_sensors", "_sensors.csv", "sensors_hist")

VOCABOLARIO = {
    frozenset({"gwn_none", "gwn_adaptive"}): ("suite", "R2: grafo contro nessun grafo, denso"),
    frozenset({"gwn_none", "gwn_fixed", "gwn_adaptive"}): ("sparse", "R3: tre bracci, misura dichiarata"),
    frozenset({"gwn_none", "gwn_fixed"}): ("sparse", "R3: grafo dato contro nessun grafo"),
    frozenset({"gwn_none", "gwn_adaptive", "gwn_both"}): ("sparse", "R3 con il braccio combinato"),
    frozenset({"gwn_none"}): ("spaiato", "un solo braccio: non usabile per un confronto"),
    frozenset({"gwn_adaptive"}): ("spaiato", "un solo braccio: non usabile per un confronto"),
    frozenset({"gwn_fixed"}): ("spaiato", "un solo braccio: non usabile per un confronto"),
    # ATTENZIONE: gomo_classify scrive `gwn_{mode}` per OGNI modalita' (riga 405),
    # quindi la modalita' `stid` produce `gwn_stid` e non `stid`. Il nome della
    # colonna non e' quello della modalita'.
    frozenset({"gwn_stid"}): ("validita", "MLP per-nodo in stile STID (§8.7.3)"),
    frozenset({"stid"}): ("validita", "MLP per-nodo in stile STID (§8.7.3)"),
    frozenset({"gwn_none", "gwn_stid"}): ("validita", "MLP per-nodo con il controllo temporale"),
    frozenset({"lightgbm"}): ("suite", "LightGBM, ramo interno di gomo_classify"),
    frozenset({"gwn_none", "gwn_adaptive", "hist_prior", "lightgbm"}):
        ("suite", "campagna fondativa: GWN, priore storico e LightGBM insieme"),
    frozenset({"lgb_fair"}): ("suite", "riferimento tabellare"),
    frozenset({"agcrn", "dcrnn"}): ("suite", "riferimenti ricorrenti"),
    frozenset({"agcrn"}): ("suite", "solo AGCRN"),
    frozenset({"dcrnn"}): ("suite", "solo DCRNN"),
    frozenset({"staeformer", "t4c_gnn"}): ("suite", "STAEformer + GCN stile Traffic4cast"),
    frozenset({"staeformer"}): ("validita", "solo STAEformer: probabile scala piena"),
    frozenset({"t4c_gnn"}): ("suite", "solo GCN: unico orizzonte 15 min"),
    frozenset({"base", "weather"}): ("meteo", "ablazione del meteo, due rami"),
    frozenset({"base", "placebo"}): ("meteo", "controllo a rumore"),
    frozenset({"base", "weather", "placebo"}): ("meteo", "ablazione con controllo"),
    frozenset({"transductive", "ign"}): ("identita", "identita' da attributi statici"),
    frozenset({"temporal", "graph"}): ("regressione", "REGRESSIONE, non la suite principale"),
    frozenset({"hist_prior"}): ("riferimenti", "priore storico di classe"),
    frozenset({"persistence", "hist_avg"}): ("riferimenti", "riferimenti continui"),
}
SPAZIALI = {"idw", "idw_dist", "knn", "nbr_idw", "nbr_prior"}
CONSUMA_GRAFO = {"gwn_fixed", "dcrnn", "t4c_gnn"}
SPIRE = ("d8_2024", "d15_2024", "d8_2023", "urb_d")
# nomi inequivocabili: hanno la precedenza sul vocabolario dei modelli, perche'
# un aggregato contiene per costruzione un solo braccio per riga e verrebbe
# altrimenti classificato come spaiato
PER_NOME_PRIORITARIO = [
    (r"^(ALL_results|MODEL_leaderboard|FINDINGS_check)", "aggregati",
     "tabella aggregata degli orchestratori: filtrare `experiment`"),
    # uscite PREDEFINITE di gomo_classify.py, gomo_sparse.py e affini: prodotte
    # da invocazioni senza `--out`, quindi prive di contesto e seme nel nome.
    # Sono esecuzioni estemporanee sul contesto predefinito (d8/2024) e non
    # appartengono ad alcuna campagna: non alimentano alcuna tabella. Deve stare
    # fra le PRIORITARIE perche' i modelli che contengono sono gli stessi della
    # suite, e il vocabolario le rivendicherebbe.
    (r"^(classify|sparse|gwn|stgnn|rnn_baseline|sota_baseline|lgb_fair)_results\.csv$",
     "estemporanei", "uscita predefinita: invocazione senza --out, nessuna campagna"),
    # uscita di onboard_subset_check.py: verifica che il sottoinsieme tenuto
    # fuori non sia intrinsecamente piu' facile (§8.4). Non ha colonna `model`
    # perche' il priore storico non e' un modello.
    (r"^subset_diff", "diagnostiche", "difficolta' del sottoinsieme escluso (R4)"),
    (r"^covariate_", "geo", "covariate della campagna geometrica"),
    (r"^crossval", "validazione", "validazione incrociata contro le sonde"),
    (r"^placement_", "diagnostiche", "posizionamento dei sensori (R4)"),
    (r"^imputazione_", "diagnostiche", "regola di strada vuota"),
    (r"^copertura", "diagnostiche", "copertura realizzata dalle maschere"),
    (r"^tabella_verifiche", "diagnostiche", "verifiche preregistrate"),
    (r"^onboard", "onboard", "R4: inserimento di un sensore nuovo"),
    # la griglia a due fattori e le ablazioni producono righe IDENTICHE per
    # struttura a quelle della suite (stesso modello, stesse colonne): senza
    # questa precedenza finirebbero in `suite` e la decomposizione dell'identita'
    # verrebbe confusa con il confronto R2
    (r"^cell[A-D](-\w+)?_", "identita",
     "griglia 2x2 sull'identita': A emb+HA, B solo emb, C solo HA, D nessuna"),
    (r"^emb_abl", "identita", "ablazione sulla capacita' del codice di identita'"),
    (r"^a6[A-Z0-9]+_", "identita", "descrittore osservabile di nodo"),
    (r"^ident_", "identita", "adiacenza identita': collaudo della saturazione"),
    (r"^ign_\w+_s\d+_", "identita", "identita' da attributi statici"),
    # desc{2,8}: --emb 0 --node-desc descrittori/<ctx>_d<N>.npy, 60 invocazioni.
    # d8 e' il CONTROLLO chiesto dal revisore: se d2 recupera quanto d8,
    # l'informazione dell'identita' sta davvero in due dimensioni.
    (r"^desc\d+_", "identita", "descrittore osservabile: proiezione a 2 e a 8 dimensioni"),
    # --- calibrazione: gomo_classify --modes none con --dump-probs-val --------
    (r"^val_classify_", "calibrazione",
     "ramo neurale della campagna di calibrazione (Tabella 24)"),
    # --- controlli geometrici e randomizzati ---------------------------------
    # sparse_geoF_{short,long,probe}: gomo_sparse --modes fixed su grafi
    # geometrici costruiti a mano (geo_graph_short.pkl / geo_graph_long.pkl).
    # Il braccio `none` e' condiviso fra le due valutazioni.
    (r"^sparse_geoF_probe", "geo", "sonda a un seme sul grafo geometrico corto"),
    (r"^sparse_geoF_", "geo", "grafo geometrico a raggio corto/lungo, braccio fixed"),
    # densrand: adiacenza RANDOMIZZATA nel compito DENSO, non nel regime severo
    (r"^densrand_", "geo", "controllo randomizzato sul compito denso"),
    # --- metriche di soglia --------------------------------------------------
    (r"^precrec_", "diagnostiche",
     "curve precisione-richiamo, --modes adaptive con --dump-metrics"),
    # --- varianti di soglia e di riferimento (§8.7.2) -------------------------
    (r"^(classify|sparse)_(d8_p85tr|t4cmad_g0\d+)_", "validita",
     "verifica sulle scelte di costruzione: soglie di classe e riferimento p85"),
]
# Ricostruito dai transcript delle sessioni: ogni voce corrisponde a un comando
# eseguito davvero, non a una congettura sul nome del file.
PER_NOME = [
    # --- griglia a due fattori sull'identita' (revisione esterna, agosto) -----
    # cell{A,B,C,D}_<ctx>_s<n>: gomo_classify --modes none --emb {8,0} [--no-ha]
    #   A emb+HA | B solo emb | C solo HA | D nessuna identita'
    # cellD-{fixed,adaptive}: isola E1/E2, la terza fonte di identita'
    (r"^cell[A-D](-\w+)?_", "identita"),
    (r"^emb_abl", "identita"),        # ablazione --emb in {2,4,8,16,32,64}, seme 0
    (r"^a6[A-Z0-9]+_|^ident_", "identita"),
    (r"^ign_\w+_s\d+_", "identita"),  # gomo_ign --statics <insieme progressivo>
    # --- campagne principali, tre generazioni successive ----------------------
    # `classify_<ctx>_s<n>` e `sparse_<ctx>_s<n>` senza prefisso sono la PRIMA
    # generazione (luglio). Vanno DOPO le voci con prefisso, altrimenti
    # `fix_classify_...` verrebbe intercettato da `classify` in mezzo al nome:
    # le espressioni sono ancorate a inizio nome, quindi l'ordine basta.
    # campagna del grafo dato sul compito denso, rifatta dopo la patch (§8.5).
    # Contiene gwn_none e gwn_fixed: la stessa firma di `densefix`, che sostituisce.
    # LightGBM sulla POPOLAZIONE PIENA, prodotto da run_replication.py con il solo
    # --targets. E' la campagna che le Tabelle 17-19 usavano prima della correzione
    # di §6.2.1, sostituita da `lgbristr_` sulla popolazione ristretta.
    (r"^lgb_", "storici"),
    (r"^fixdensefix_", "suite"),
    (r"^densefix_", "suite"),
    (r"^fix_classify_", "suite"),     # DOPO la patch dell'attributo: valida
    (r"^camp_classify_", "suite"),    # campagna a cinque semi di agosto
    (r"^prec_classify_", "suite"),    # campagna della precisione
    (r"^fix_sparse_", "sparse"),      # DOPO la patch: valida
    (r"^camp_sparse_", "sparse"),
    (r"^sparse_fixed_", "sparse"),
    (r"^classify_", "suite"),         # prima generazione, luglio
    (r"^sparse_", "sparse"),          # prima generazione, luglio
    (r"^stid_", "validita"),          # MLP per-nodo, §8.7.3
    # --- resto ---------------------------------------------------------------
    (r"^val_(nn|gb)_", "calibrazione"),
    (r"^onboard", "onboard"),
    (r"^geo_|^covariate_", "geo"),
    (r"^wx_|^wgate|^wnoise|^wnotime", "meteo"),
    (r"^(winabl|stae_full|lgbreg|alpha[NG])", "validita"),
    (r"^(lgbonly_|metrics_)", "diagnostiche"),   # --backend lgb, dump di metriche
    (r"^crossval", "validazione"),
    (r"^(placement_|imputazione_|copertura|tabella_)", "diagnostiche"),
]

# Famiglie RIFATTE da una campagna successiva. Il criterio e' il PREFISSO e non
# la data, cosi' non dipende dai timestamp, che uno spostamento puo' alterare.
# La sostituzione vale SOLO dove la correzione ha avuto effetto, cioe' sui
# contesti a velocita' ricostruita: sulle tre citta' `weight` e' gia' la distanza
# e la campagna precedente resta l'unica copia valida. Verificato: `camp_sparse`
# sulle citta' era stata segregata pur essendo l'unica fonte di R3 per Madrid,
# Londra e Melbourne.
CONTESTI_TOCCATI = ("d8_2024", "d15_2024", "d8_2023", "urb_d")

SOSTITUITE = {
    "camp_classify_": ("fix_classify_", "rifatta dopo la patch dell'attributo di distanza"),
    "camp_sparse_":   ("fix_sparse_",   "rifatta dopo la patch dell'attributo di distanza"),
    "sparse_fixed_":  ("fix_sparse_",   "confronto fra file di date diverse: artefatto noto"),
    "densefix_":      ("fixdensefix_", "rifatta dopo la patch dell'attributo di distanza"),
    "lgb_":           ("lgbristr_",    "popolazione piena, sostituita da quella ristretta (§6.2.1)"),
}


def prefisso(nome: str) -> str:
    """Nome della campagna, tolti contesto, seme ed estensione.

    Due file con la STESSA firma di contenuto ma prefisso diverso appartengono a
    campagne diverse — `camp_classify` e `fix_classify` producono righe identiche
    per struttura, ma la seconda e' posteriore alla patch e la prima no. Il
    raggruppamento deve quindi tenerli distinti, altrimenti una campagna valida
    eredita l'etichetta di una superata.
    """
    n = re.sub(r"\.csv$", "", nome)
    n = re.sub(r"_s\d+$", "", n)
    n = re.sub(r"_(d8_20\d\d|d15_20\d\d|t4c(mad|lon|mel)|mad|lon|mel)$", "", n)
    n = re.sub(r"_D\d+$", "", n)
    return n or nome


def firma(p: Path):
    try:
        d = pd.read_csv(p, nrows=8000)
    except Exception as e:
        return None, str(e)[:60]
    col = tuple(c for c in ("model", "mode", "split", "history", "subset", "riga",
                            "experiment", "horizon", "seed", "epoca") if c in d.columns)
    mod = set()
    for c in ("model", "mode"):
        if c in d.columns:
            mod |= {str(x) for x in d[c].dropna().unique()}
    met = tuple(c for c in ("wCE", "macroF1", "red_recall", "red_prec", "MAE_r",
                            "RMSE_r", "acc", "val_wCE", "test_wCE") if c in d.columns)
    return (frozenset(mod), col, met), None


def sostituita(nome: str, presenti: set):
    """Vero se esiste una campagna piu' recente che rifa' la stessa cosa."""
    for vecchio, (nuovo, motivo) in SOSTITUITE.items():
        if not (nome.startswith(vecchio) and nuovo in presenti):
            continue
        if vecchio in ("camp_sparse_", "sparse_fixed_", "densefix_"):
            if not any(x in nome for x in CONTESTI_TOCCATI):
                return None      # citta': la campagna precedente resta valida
        return motivo
    return None


def decodifica(mod, met, nome):
    for s, c, d in PER_NOME_PRIORITARIO:
        if re.search(s, nome):
            return c, d
    spaz = mod & SPAZIALI
    nucleo = frozenset(mod - SPAZIALI)
    if nucleo in VOCABOLARIO:
        cart, desc = VOCABOLARIO[nucleo]
        if spaz:
            desc += f" + {len(spaz)}/5 riferimenti spaziali"
        return cart, desc
    for s, c in PER_NOME:
        if re.search(s, nome):
            return c, "riconosciuto dal nome"
    if spaz and not nucleo:
        return "sparse", f"soli riferimenti spaziali ({len(spaz)}/5)"
    if not mod:
        return "senza_modelli", "nessuna colonna model/mode"
    if "MAE_r" in met:
        return "regressione", "metriche regressive: harness di regressione"
    return "da_classificare", "combinazione di modelli non riconosciuta"


def main() -> int:
    ap = argparse.ArgumentParser(description="censimento dei CSV per firma")
    ap.add_argument("--radice", type=Path, default=Path("."))
    ap.add_argument("--data-patch", default="2026-08-22")
    ap.add_argument("--firma", type=int, default=None, help="elenca i file di una firma")
    ap.add_argument("--genera-script", type=Path, default=None)
    a = ap.parse_args()

    radice = a.radice.resolve()
    soglia = dt.datetime.strptime(a.data_patch, "%Y-%m-%d").timestamp()
    file = [p for p in radice.rglob("*.csv") if not any(x in p.parts for x in IGNORA)]
    if not file:
        print(f"nessun CSV sotto {radice}")
        return 1

    prefissi = set(SOSTITUITE) | {v[0] for v in SOSTITUITE.values()}
    presenti = {n for n in prefissi if any(p.name.startswith(n) for p in file)}

    gruppi = defaultdict(list)
    rotti = []
    sorgenti = []
    for p in sorted(file):
        if set(p.relative_to(radice).parts[:-1]) & SORGENTE:
            sorgenti.append(p)
            continue
        f, err = firma(p)
        if f is None:
            rotti.append((p, err))
        else:
            gruppi[(prefisso(p.name),) + f].append(p)

    print(f"radice: {radice}")
    print(f"CSV: {len(file)}  |  di cui sorgente (intoccabili): {len(sorgenti)}"
          f"  |  firme distinte fra i risultati: {len(gruppi)}\n")
    if sorgenti:
        ana = [p for p in sorgenti if any(k in p.name for k in ANAGRAFICHE)]
        print(f"SORGENTE — {len(sorgenti)} file sotto {'/, '.join(sorted(SORGENTE))}/")
        print("   dati sorgente e artefatti della pipeline: NON vengono spostati.")
        if ana:
            print(f"   fra questi {len(ana)} anagrafiche di sensori. Le revisioni")
            print("   datate vanno tenute TUTTE: dal 6/7/2026 l'anagrafica GO-MO ha")
            print("   perso `max_capacity` e `has_data`, e gli esperimenti che le")
            print("   richiedono devono usare quella dei run originali.")
        print()
    print(f"{'#':>3} {'file':>5} {'periodo':>13} {'destinazione':14s} contenuto")
    print("-" * 102)

    dest = {}
    for i, ((pre, mod, col, met), f) in enumerate(
            sorted(gruppi.items(), key=lambda x: -len(x[1]))):
        t = [x.stat().st_mtime for x in f]
        per = (f"{dt.datetime.fromtimestamp(min(t)):%d/%m}–"
               f"{dt.datetime.fromtimestamp(max(t)):%d/%m}")
        cart, desc = decodifica(mod, met, f[0].name)
        sos = sostituita(f[0].name, presenti)
        if sos:
            cart, desc = "storici", desc + f"   [{sos}]"
        elif (mod & CONSUMA_GRAFO) and any(s in x.name for x in f for s in SPIRE) \
                and max(t) < soglia:
            cart, desc = "superati", desc + "   ANTERIORE ALLA PATCH"
        dest[i] = (cart, f)
        print(f"{i:3d} {len(f):5d} {per:>13} {cart:14s} {desc}")
        print(f"{'':24s} {'':14s} campagna: {pre}")
        print(f"{'':24s} {'':14s} modelli: {','.join(sorted(mod))[:66] or '—'}")
        print(f"{'':24s} {'':14s} esempio: {f[0].relative_to(radice)}")
    print("-" * 102)

    ri = defaultdict(int)
    for c, f in dest.values():
        ri[c] += len(f)
    print("\nriepilogo per destinazione:")
    for c in sorted(ri, key=lambda x: -ri[x]):
        print(f"   replication/{c:16s} {ri[c]:5d} file")

    for eti, nota in (
            ("storici", "rifatti da una campagna piu' recente: SEGREGARE, non cancellare"),
            ("superati", "anteriori alla patch: SEGREGARE, non cancellare"),
            ("spaiato", "un solo braccio: inutilizzabili per quel confronto (§7.3)"),
            ("da_classificare", "combinazione non riconosciuta: guardare uno per uno"),
            ("senza_modelli", "nessuna colonna model/mode")):
        gr = [f for c, f in dest.values() if c == eti]
        if not gr:
            continue
        print(f"\n{eti.upper()} — {sum(len(g) for g in gr)} file  ({nota})")
        for g in gr:
            for p in g[:6]:
                print(f"   {p.relative_to(radice)}")
            if len(g) > 6:
                print(f"   ... e altri {len(g) - 6} della stessa firma")

    if rotti:
        print(f"\nILLEGGIBILI — {len(rotti)}")
        for p, e in rotti[:10]:
            print(f"   {p.relative_to(radice)}: {e}")

    if a.firma is not None and a.firma in dest:
        c, f = dest[a.firma]
        print(f"\nFIRMA {a.firma} -> replication/{c} — {len(f)} file")
        for p in sorted(f):
            print(f"   {dt.datetime.fromtimestamp(p.stat().st_mtime):%d/%m %H:%M}  "
                  f"{p.relative_to(radice)}")

    if a.genera_script:
        righe = ["#!/bin/bash",
                 "# GENERATO DA censimento_csv.py — RILEGGERE PRIMA DI ESEGUIRE.",
                 "# Sposta i CSV in sottocartelle di replication/. Non cancella nulla.",
                 "set -e", ""]
        righe += [f"mkdir -p replication/{c}" for c in sorted(ri)]
        righe.append("")
        for c, f in dest.values():
            for p in f:
                r = p.relative_to(radice)
                if r.parent == Path(f"replication/{c}"):
                    continue
                righe.append(f"mv -n {shlex.quote(str(r))} replication/{c}/ "
                             f"2>/dev/null || true")
        righe += ["", 'echo "fatto. Aggiornare gli schemi di percorso degli script."']
        a.genera_script.write_text("\n".join(righe) + "\n")
        a.genera_script.chmod(0o755)
        print(f"\nscritto {a.genera_script} — rileggerlo prima di eseguirlo.")

    print("\nNON vengono spostati: i CSV sotto " + "/, ".join(sorted(SORGENTE)) + "/,")
    print("ne' le cartelle dei dump (probs/, probsval/, probs_wx/).")
    print("Dopo lo spostamento gli script di analisi vanno invocati con il percorso")
    print("nuovo: tutti accettano lo schema come argomento (--sparse, --dir, --probs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
