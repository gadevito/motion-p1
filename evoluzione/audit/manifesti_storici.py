#!/usr/bin/env python3
"""
Manifesti retrospettivi per i risultati storici.
=================================================
Nessuna esecuzione. Scrive un manifesto per ciascun risultato del deliverable che
la campagna JSS potrebbe riusare o modificare.

PERCHE' SEPARATI DAI MANIFESTI DI ESECUZIONE. Un manifesto scritto durante
l'esecuzione attesta cio' che e' accaduto; uno scritto oggi attesta cio' che si e'
potuto ricostruire. Confonderli darebbe ai risultati storici una tracciabilita' che
non hanno.

I CAMPI NON ACCERTATI RESTANO MANCANTI. Non si compilano assumendo che il codice
corrente coincida con quello che ha prodotto il risultato: la configurazione e'
cambiata almeno tre volte fra il 18 e il 26 agosto, e il repository non esisteva.

TRE FAMIGLIE DA NON CONFONDERE, che lo script tiene separate:

  1. sedici statistiche con compressione PCA  — esperimento superato;
  2. sedici statistiche con proiezione appresa — la Tabella 54;
  3. quarantacinque statistiche con encoder a due strati — non attribuito.

Nessun risultato si trasferisce da una famiglia all'altra.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/manifesti_storici.py
    poetry run python evoluzione/audit/manifesti_storici.py --elenca
"""
import argparse
import glob as globmod
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.registro import Registro, impronta_file  # noqa: E402

# ---------------------------------------------------------------------------
# Ciascuna voce elenca cio' che e' stato ACCERTATO e cio' che resta MANCANTE.
# Lo stato segue la tabella fissata dal revisore senior.
# ---------------------------------------------------------------------------
STORICI = [
    dict(
        etichetta="Tabella 54 — recupero del residuo di identita'",
        famiglia="2. sedici statistiche, proiezione appresa",
        noti={
            "descrittore": {
                "n_caratteristiche": 16,
                "file": "descrittori/{contesto}_raw.npy",
                "contenuto": ("dispersione per fascia oraria, quantili, "
                              "autocorrelazione a ritardo unitario, frequenza per "
                              "classe, ora del picco, asimmetria fra salita e "
                              "discesa del profilo giornaliero"),
                "stato": "dimensione verificata sul file oggi disponibile",
            },
            "trasformazione": {
                "tipo": "proiezione lineare appresa congiuntamente al modello",
                "dimensioni": [2, 8],
                "stato": "ricostruita dal registro delle sessioni, non da checkpoint",
            },
            "celle": {
                "A": "a6A — completa, con vettori appresi per nodo",
                "C": "a6C — priva di vettori appresi",
                "P2": "a6P2 — descrittore a 2 dimensioni",
                "P8": "a6P8 — descrittore a 8 dimensioni",
                "architettura": "la medesima in tutte e quattro, tag gwn_none",
                "stato": "tag verificato nei dump; ingressi attivi NON verificati",
            },
            "valutazione": {
                "fonte": "dump di probabilita', entropia ricalcolata cella per cella",
                "orizzonti": ["15m", "30m", "60m", "120m"],
                "semi": 5,
                "pesi": "N/(3 n_k) sul periodo di addestramento",
            },
            "aggregazione": {
                "formula": "R_P = (1/S) somma_s [ (L_C,s - L_P,s) / (L_C,s - L_A,s) ]",
                "descrizione": "media dei rapporti appaiati per seme",
                "nota_denominazione": (
                    "nel codice A e' la cella COMPLETA e C quella priva di "
                    "embedding: il «divario A-C» della tabella corrisponde a "
                    "L_C - L_A. Nel paper si usera' «vantaggio dell'embedding» "
                    "con la formula accanto, senza lettere."),
                "stato": "verificata nel codice del registro delle sessioni",
            },
            "intervalli": {
                "procedura": ("300 repliche; ciascuna estrae UN seme a caso e i "
                              "nodi con reinserimento; intervallo ricentrato "
                              "sulla stima campionaria"),
                "stato": "RICOSTRUITA, non validata",
                "riserva": (
                    "la procedura estrae un singolo seme per replica mentre la "
                    "stima e' una media su cinque: puo' rappresentare la "
                    "variabilita' di una esecuzione, non la distribuzione "
                    "campionaria della media. Ricentrare non risolve la "
                    "differenza. Il ricampionamento dei nodi non rappresenta la "
                    "dipendenza spaziale ne' include quella temporale."),
            },
            "collaudo": {"a6A": 0.9047, "cellA": 0.9047, "esito": "coerenti"},
            "criterio": {
                "enunciato": "recupero sopra il 70% in almeno quattro contesti su sei",
                "esito_P2": "tre contesti (Melbourne 76,5, Londra 75,6, Madrid 75,2)",
                "esito_P8": "cinque contesti",
                "stato": ("descritto come preregistrato; per chiamarlo tale serve "
                          "un documento datato anteriore alle esecuzioni. Se era "
                          "un protocollo interno non depositato, va descritto "
                          "come tale."),
            },
        },
        mancanti=[
            "code_commit — il repository non esisteva all'epoca",
            "working_tree_status",
            "collegamento certo fra il file di descrittore e le esecuzioni che "
            "hanno prodotto i dump: la forma (K,16) attesta il file oggi "
            "disponibile, non quello caricato allora",
            "quali ingressi fossero attivi: il tag gwn_none non lo prova",
            "assenza di parametri specifici per nodo nelle celle C, P2 e P8",
            "se la trasformazione fosse lineare o a due strati, in assenza di "
            "checkpoint da ispezionare",
            "environment_versions",
            "dataset_manifest_hash e node_split_hash",
        ],
    ),
    dict(
        etichetta="Descrittore PCA — esperimento superato",
        famiglia="1. sedici statistiche, compressione PCA",
        noti={
            "file": "descrittori/{contesto}_d2.npy e _d8.npy",
            "data_creazione": "18/08, anteriore al descrittore grezzo attuale",
            "relazione_con_raw": ("le componenti principali di _raw: correlazione "
                                  "canonica minima 1,0000 su tutti e sei i "
                                  "contesti, entro la precisione numerica e nelle "
                                  "condizioni del calcolo"),
            "esito": ("recupero 59,4% contro 80,5% della proiezione appresa, su "
                      "Madrid a due epoche"),
            "stato": ("confronto ESPLORATIVO: non e' accertato che condivida "
                      "contesto, popolazione, dimensione, semi, ingressi, "
                      "riferimento del recupero e periodo di stima della PCA"),
        },
        mancanti=[
            "condizioni del confronto con la proiezione appresa",
            "periodo usato per stimare la PCA",
            "centratura e trasformazione applicate prima della decomposizione",
            "se l'esito 59,4/80,5 provenga da esecuzioni complete o parziali "
            "(il registro dice «a due epoche»)",
        ],
    ),
    dict(
        etichetta="Descrittore a 45 statistiche — non attribuito",
        famiglia="3. quarantacinque statistiche, encoder a due strati",
        noti={
            "file": "descrittori/{contesto}_ext.npy",
            "data_creazione": "21/08",
            "configurazione": "--desc-proj 8 --desc-hidden 32, campagna a6X8",
            "parametri_della_mappa": "45x32 + 32x8 = 1.696",
            "stato": ("nessun risultato del deliverable e' stato attribuito a "
                      "questa famiglia"),
        },
        mancanti=[
            "se abbia prodotto un risultato riportato nel deliverable",
            "esito dell'esecuzione, se avvenuta",
            "lettura preregistrata dichiarata prima della campagna",
        ],
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="manifesti retrospettivi")
    ap.add_argument("--radice", type=Path,
                    default=Path("results/evoluzione/registro"))
    ap.add_argument("--elenca", action="store_true",
                    help="mostra cosa verrebbe scritto, senza scrivere")
    a = ap.parse_args()

    print("=" * 76)
    print("MANIFESTI RETROSPETTIVI")
    print("=" * 76)
    for v in STORICI:
        print(f"\n{v['etichetta']}")
        print(f"  famiglia: {v['famiglia']}")
        print(f"  campi accertati: {len(v['noti'])} gruppi")
        print(f"  campi MANCANTI: {len(v['mancanti'])}")
        for m in v["mancanti"]:
            print(f"     - {m}")
        if a.elenca:
            continue
        # impronte dei file di descrittore oggi presenti, come evidenza parziale
        noti = dict(v["noti"])
        mod = v["noti"].get("descrittore", {}).get("file") or v["noti"].get("file")
        if mod and "{contesto}" in str(mod):
            impronte = {}
            for c in ("t4cmad", "t4clon", "t4cmel", "d8_2024", "d15_2024", "d8_2023"):
                p = str(mod).replace("{contesto}", c)
                for q in ([p] if "_" in p else []) + globmod.glob(p):
                    h = impronta_file(q)
                    if h:
                        impronte[q] = h
            if impronte:
                noti["impronte_file_oggi_presenti"] = impronte
                noti["_nota_impronte"] = (
                    "attestano il contenuto dei file OGGI, non che siano quelli "
                    "caricati dalle esecuzioni originarie")
        p = Registro.retrospettivo(v["etichetta"], noti, v["mancanti"], a.radice)
        print(f"  -> {p}")

    if not a.elenca:
        print(f"\n  scritti in {a.radice}")
        print("\n  Questi manifesti NON conferiscono ai risultati storici la")
        print("  tracciabilita' delle esecuzioni nuove: attestano cio' che si e'")
        print("  potuto ricostruire, e dichiarano il resto come mancante.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
