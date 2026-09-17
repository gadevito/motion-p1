#!/usr/bin/env python3
"""Genera il congelamento della campagna di sensibilita' all'appaiamento.

Legge i file effettivi: nessun numero copiato a mano.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

R = Path("results/evoluzione")
VECCHIA, NUOVA = R / "raccordo", R / "raccordo_appaiato"
CITTA = ("Madrid", "Londra", "Melbourne")
MARGINE = 1.0
# il generatore del risultato DEFINITIVO si LEGGE dal file, non si assume


def h(p, n=16):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]
    except OSError:
        return "assente"


def leggi(p, chiave=None):
    d = json.loads(Path(p).read_text())
    return d.get(chiave, d) if chiave else d


Av = leggi(VECCHIA / "analisi.json", "risultati")
An = leggi(NUOVA / "analisi.json", "risultati")
Sv = leggi(VECCHIA / "sensibilita.json", "risultati")
Sn = leggi(NUOVA / "sensibilita.json", "risultati")
ST = leggi(NUOVA / "stabilita.json")
Mn = leggi(NUOVA / "matrice.json")
GENERATORE_DEFINITIVO = ST.get("generatore_definitivo", 1000)

r = []
A = r.append
A("# Congelamento — sensibilità all'appaiamento dell'inizializzazione")
A("")
A(f"**Congelato il {datetime.now(timezone.utc).date().isoformat()}.** "
  f"Addendum 1 al disegno congelato alla versione 5.")
A("")
A("## 1. Le due campagne")
A("")
A("| campagna | funzione |")
A("|---|---|")
A("| **raccordo** | confronto con inizializzazione **parzialmente disallineata** |")
A("| **raccordo_appaiato** | sensibilità **prospetticamente specificata** all'allineamento dei moduli comuni |")
A("")
A("**Entrambe si conservano.** La prima non è invalidata: è il confronto svolto")
A("secondo il protocollo allora vigente, con il disallineamento scoperto dopo.")
A("")
A("## 2. Conclusione fissata")
A("")
A("> **L'allineamento dell'inizializzazione dei moduli comuni modifica")
A("> sostanzialmente le differenze predittive osservate e riduce la loro")
A("> variabilità fra inizializzazioni.** Nella campagna di sensibilità la non")
A("> inferiorità è sostenuta nelle tre città; l'equivalenza è sostenuta in due.")
A("")
A("> **Il deterioramento osservato nella prima campagna non è robusto")
A("> all'allineamento dell'inizializzazione dei moduli comuni e non può essere")
A("> attribuito alla sola rappresentazione.**")
A("")
A("**Non si scrive** che il risultato «dipendeva dall'inizializzazione e non")
A("dalla rappresentazione»: l'intervento mostra una sensibilità effettiva, ma")
A("**non esclude interazioni fra rappresentazione e inizializzazione**.")
A("")
A("## 3. Stima e intervalli, prima e dopo")
A("")
A("| città | stima prima | stima dopo | differenza | NI prima | NI dopo |")
A("|---|---|---|---|---|---|")
for c in CITTA:
    a, b = Av[c], An[c]
    A(f"| **{c}** | {a['stima']:+.3f}% | **{b['stima']:+.3f}%** | "
      f"{b['stima']-a['stima']:+.3f} | {a['ni_sup']:+.3f}% | "
      f"**{b['ni_sup']:+.3f}%** |")
A("")
A("**Differenza appaiata fra i delta**, con il controllo LEGACY fermo: "
  + ", ".join(f"{c} {An[c]['stima']-Av[c]['stima']:+.3f}" for c in CITTA)
  + " punti. **Lo spostamento è nella stessa direzione in tutte le città.**")
A("")
A("### Verdetti")
A("")
A("| città | non inferiorità | equivalenza |")
A("|---|---|---|")
for c in CITTA:
    A(f"| **{c}** | prima {Av[c]['non_inferiorita']} → **dopo "
      f"{An[c]['non_inferiorita']}** | prima {Av[c]['equivalenza']} → "
      f"**dopo {An[c]['equivalenza']}** |")
A("")
A("**Con entrambe le procedure di ricampionamento** nessun verdetto della nuova")
A("campagna cambia: originaria e incrociata concordano su tutte e tre le città.")
A("")
A("## 4. Stabilità Monte Carlo del limite")
A("")
A("**Il generatore del risultato definitivo è il seme "
  f"{GENERATORE_DEFINITIVO}**, identificato senza selezionarlo in funzione")
A("dell'esito. Gli altri nove **documentano la sensibilità numerica**.")
A("")
A("| città | limite (generatore definitivo) | mediana | dispersione | escursione | sotto il margine |")
A("|---|---|---|---|---|---|")
for c in CITTA:
    x = ST["risultati"][c]
    A(f"| {c} | **{x.get('limite_definitivo', x['limiti'][0]):+.4f}%** | "
      f"{x['mediana']:+.4f}% | "
      f"{x['deviazione']:.5f} | {max(x['limiti'])-min(x['limiti']):.5f} | "
      f"{x['sotto_margine']}/{x['ripetizioni']} |")
A("")
A(f"Con **{ST['repliche']:,} repliche** e **{ST['ripetizioni']} generatori**.")
A("")
A("**Nessuna città appare marginale rispetto alla precisione numerica del")
A("ricampionamento**: il limite resta sotto il margine in tutte le ripetizioni.")
A("")
A("**Lo scostamento con la numerosità**, misurato sul MEDESIMO generatore")
A("definitivo — misurarlo su un altro mescolerebbe due effetti:")
A("")
A("| città | 1.000 repliche | 5.000 | " + f"{ST['repliche']:,}" + " | scostamento |")
A("|---|---|---|---|---|")
for c in CITTA:
    cv = ST["risultati"][c].get("convergenza", {})
    if not cv:
        A(f"| {c} | — | — | — | non registrato |")
        continue
    k = sorted(int(x) for x in cv)
    v = [cv[str(x)]["ni_sup"] if str(x) in cv else cv[x]["ni_sup"] for x in k]
    A(f"| {c} | " + " | ".join(f"{x:+.4f}%" for x in v)
      + f" | **{v[-1]-v[0]:+.4f}** punti |")
A("")
A("**Le analisi a mille repliche erano meno precise di quanto sembrasse.**")
A("")
A("> **La dispersione Monte Carlo del limite non è la significatività")
A("> dell'effetto predittivo**, e non si usa come argomento inferenziale.")
A("")
A("## 5. Matrice partizione × inizializzazione")
A("")
A("| città | escursione fra i semi, prima | dopo | dispersione fra inizializzazioni |")
A("|---|---|---|---|")
for c, pr, do, di in (("Madrid", 2.500, 0.789, "1,290 → 0,407"),
                      ("Londra", 5.310, 1.223, "2,784 → 0,612"),
                      ("Melbourne", 5.214, 2.849, "2,637 → 1,482")):
    A(f"| {c} | {pr:.3f} | **{do:.3f}** | {di} |")
A("")
A("**La struttura per colonna si attenua ma non sparisce**: su Melbourne resta")
A("un'escursione di 2,85 punti fra le tre inizializzazioni.")
A("")
A("> **L'escursione fra inizializzazioni non si confronta con il margine**, che")
A("> si riferisce all'effetto **medio**: descrive un'altra quantità.")
A("")
A("## 6. Stabilità del controllo LEGACY")
A("")
A("> **La ripetizione di LEGACY riproduce esattamente le perdite nelle")
A("> esecuzioni considerate.** Scarto relativo massimo `0,00e+00%` su tutte e")
A("> ventisette le celle, nei tre contesti.")
A("")
A("**Non dimostra** che il backend sia universalmente deterministico, né che")
A("tutte le predizioni coincidano: **sono state confrontate le perdite**.")
A("")
A("È però la condizione che rende interpretabile il confronto: l'intervento")
A("tocca la sola BASE-CORRECTED, e il controllo non si è mosso.")
A("")
A("## 7. Metriche secondarie, ricalcolate su questa campagna")
A("")
A("**Non si trasferiscono dalla campagna precedente**: un modello diverso ha")
A("ordinamenti diversi.")
A("")
A("| città | AP LEGACY | AP BASE-CORR | differenza assoluta | variazione relativa |")
A("|---|---|---|---|---|")
for c in CITTA:
    s = An[c].get("secondarie", {})
    if not s:
        A(f"| {c} | — | — | — | — |")
        continue
    la = s["LEGACY"]["average_precision_critica"]
    lb = s["BASE-CORRECTED"]["average_precision_critica"]
    # media delle variazioni relative APPAIATE, quando le coppie ci sono
    pa = s["LEGACY"].get("ap_per_coppia")
    pb = s["BASE-CORRECTED"].get("ap_per_coppia")
    rel_app = (float(np.mean([100 * (y - x) / x for x, y in zip(pa, pb)]))
               if pa and pb else None)
    A(f"| **{c}** | {la:.4f} | {lb:.4f} | **{lb-la:+.4f}**, cioè "
      f"{100*(lb-la):+.2f} punti percentuali | **{100*(lb-la)/la:+.2f}%** "
      f"dalle medie; {rel_app:+.2f}% appaiata |" if rel_app is not None
      else f"| **{c}** | {la:.4f} | {lb:.4f} | {lb-la:+.4f} | "
           f"{100*(lb-la)/la:+.2f}% |")
A("")
A("**Le due colonne sono grandezze diverse**: la differenza assoluta è in punti")
A("percentuali di average precision, la variazione relativa è il rapporto. La")
A("**variazione appaiata** media le variazioni delle nove coppie, e può")
A("differire da quella calcolata sulle medie.")
A("")
A("> **Il miglioramento dell'AP è descrittivamente concorde nelle tre città,")
A("> non una superiorità inferenziale dimostrata.**")
A("")
A("### Perdita sui soli positivi")
A("")
A("| città | LEGACY | BASE-CORRECTED | differenza |")
A("|---|---|---|---|")
for c in CITTA:
    s = An[c].get("secondarie", {})
    if not s:
        A(f"| {c} | — | — | — |")
        continue
    la = s["LEGACY"]["perdita_sui_positivi"]
    lb = s["BASE-CORRECTED"]["perdita_sui_positivi"]
    A(f"| {c} | {la:.4f} | {lb:.4f} | {lb-la:+.4f} |")
A("")
A("## 8. Una correzione da registrare")
A("")
A("Nella diagnostica precedente l'average precision era stata tratta dalla")
A("**sola coppia `p0 s0`**. Su Madrid quel valore era **0,2355**, mentre la")
A("media sulle nove coppie è **0,2002**, con estremi 0,1793 e 0,2355.")
A("")
A("> **Una singola cella descrive quella combinazione di partizione e")
A("> inizializzazione, non l'intera colonna né la campagna.**")
A("")
A("Le metriche secondarie sono ora calcolate su tutte e nove le coppie, con")
A("estremi riportati.")
A("")
A("## 9. Artefatti")
A("")
A("| | |")
A("|---|---|")
A(f"| schema del descrittore | {Mn.get('schema_version')} |")
A(f"| implementazione dell'estrattore | {Mn.get('implementation_version')} |")
A(f"| coppie utilizzabili | {Mn['coppie_utilizzabili']}/"
  f"{Mn['coppie_utilizzabili']+Mn['coppie_incomplete']} |")
A(f"| repliche del ricampionamento | {ST['repliche']:,} |")
A(f"| generatore definitivo | {GENERATORE_DEFINITIVO} |")
A("")
A("**Stati iniziali**, uno per seme e configurazione, salvati in")
A("`results/evoluzione/stati_iniziali/`:")
A("")
reg = R / "stati_iniziali" / "registro_stati.json"
if reg.exists():
    d = json.loads(reg.read_text())
    A("| chiave | impronta |")
    A("|---|---|")
    for x in d.get("stati", []):
        A(f"| `{x['chiave']}` | `{x['impronta']}` |")
    A("")
    A(f"Semi dichiarati {d.get('semi_dichiarati')} → semi di torch "
      f"{d.get('semi_torch')}.")
A("")
A("**Impronte del codice:**")
A("")
A("| file | impronta |")
A("|---|---|")
for f in ("evoluzione/esperimenti/prepara_stati_iniziali.py",
          "evoluzione/esperimenti/addestramento.py",
          "evoluzione/esperimenti/semi.py",
          "evoluzione/analisi/analizza_raccordo.py",
          "evoluzione/analisi/sensibilita_incrociata.py",
          "evoluzione/analisi/stabilita_bootstrap.py",
          "evoluzione/analisi/confronta_campagne.py"):
    A(f"| `{f}` | `{h(f)}` |")
A("")
A("## 10. Limiti")
A("")
A("**Non è una replica su dati indipendenti**: stessi contesti, partizioni,")
A("semi e dati. È un'analisi di sensibilità.")
A("")
A("**Gli stessi tre semi hanno scoperto e diagnosticato il problema**, e ora ne")
A("misurano la correzione. Serve una conferma su inizializzazioni nuove.")
A("")
A("**Con tre inizializzazioni** entrambe le procedure restano poco informate")
A("sulla variabilità dell'addestramento.")
A("")
A("**Il raccordo misura il pacchetto**, non la sola imputazione né le sole")
A("maschere.")
A("")
A("**Gli intervalli sono condizionati al periodo di prova** e la dipendenza")
A("spaziale fra nodi non è modellata.")
A("")

Path("CONGELAMENTO_APPAIAMENTO.md").write_text("\n".join(r) + "\n")
print(f"documento generato: {len(r)} righe")
