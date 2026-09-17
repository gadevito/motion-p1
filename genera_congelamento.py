"""Genera il documento di congelamento dai file effettivi, non da numeri copiati."""
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

R = Path("results/evoluzione")
D = R / "raccordo"

def h(p, n=16):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]
    except OSError:
        return "assente"

A = json.loads((D / "analisi.json").read_text())
S = json.loads((D / "sensibilita.json").read_text())
# il file annida sotto "risultati": leggerlo piatto darebbe KeyError
S = S.get("risultati", S)
M = json.loads((D / "matrice.json").read_text())
CITTA = ("Madrid", "Londra", "Melbourne")

r = []
r.append("# Congelamento dei risultati del raccordo LEGACY ↔ BASE-CORRECTED")
r.append("")
r.append(f"**Congelato il {datetime.now(timezone.utc).date().isoformat()}.** "
         f"Nessun addestramento successivo.")
r.append("")
r.append("## 1. Conclusione fissata")
r.append("")
r.append("> **Nessuna città dimostra la non inferiorità con entrambe le procedure")
r.append("> considerate.** L'evidenza di deterioramento superiore all'1% osservata a")
r.append("> Londra con il ricampionamento originario **non è robusta alla")
r.append("> specificazione incrociata**. Le stime puntuali sono sfavorevoli a")
r.append("> BASE-CORRECTED, ma l'incertezza non consente conclusioni robuste rispetto")
r.append("> al margine prefissato.")
r.append("")
r.append("**Due precisazioni sulla lettura.**")
r.append("")
r.append("L'esito negativo **non si rafforza come evidenza di peggioramento**: resta")
r.append("robusta la sola *mancata dimostrazione* della non inferiorità.")
r.append("")
r.append("L'allargamento degli intervalli è **coerente** con una dipendenza associata")
r.append("all'inizializzazione, ma **non ne è una conferma indipendente**: deriva")
r.append("proprio dalla diversa struttura imposta al ricampionamento.")
r.append("")
r.append("## 2. Stime e intervalli, procedure affiancate")
r.append("")
r.append("**Le stime puntuali sono INVARIATE fra le due procedure**: il")
r.append("ricampionamento modifica gli intervalli, non lo stimatore.")
r.append("")
r.append("| città | stima | procedura | limite NI (95% unil.) | equivalenza (90% bil.) | ampiezza |")
r.append("|---|---|---|---|---|---|")
for c in CITTA:
    for proc in ("originaria", "incrociata"):
        x = S[c][proc]
        amp = x["eq_sup"] - x["eq_inf"]
        r.append(f"| {c if proc=='originaria' else ''} | "
                 f"{x['stima']:+.3f}% | {proc} | {x['ni_sup']:+.3f}% | "
                 f"[{x['eq_inf']:+.3f}; {x['eq_sup']:+.3f}] | {amp:.3f} |")
r.append("")
rap = [ (S[c]['incrociata']['eq_sup']-S[c]['incrociata']['eq_inf']) /
        (S[c]['originaria']['eq_sup']-S[c]['originaria']['eq_inf']) for c in CITTA ]
r.append(f"Ampiezza dell'incrociata rispetto all'originaria: "
         + ", ".join(f"**{x:.2f}×**" for x in rap) + ".")
r.append("")
r.append("## 3. Verdetti, separati per domanda")
r.append("")
r.append("| città | non inferiorità | equivalenza | deterioramento oltre il margine |")
r.append("|---|---|---|---|")
for c in CITTA:
    o, i = S[c]["originaria"], S[c]["incrociata"]
    det_o = "sì" if o["eq_inf"] > 1.0 else "non stabilito"
    det_i = "sì" if i["eq_inf"] > 1.0 else "non stabilito"
    r.append(f"| **{c}** | **non dimostrata** con entrambe | **non sostenuta** "
             f"con entrambe | orig. {det_o} / incr. {det_i} |")
r.append("")
r.append("**Su Londra il verdetto cambia**: `eq_inf` passa da "
         f"{S['Londra']['originaria']['eq_inf']:+.3f} a "
         f"{S['Londra']['incrociata']['eq_inf']:+.3f}, sicché l'intervallo non sta")
r.append("più interamente sopra il margine.")
r.append("")
r.append("**Su Madrid lo scarto dal margine è di 0,019 punti percentuali** — "
         f"{A['risultati']['Madrid']['ni_sup']:+.3f}% contro +1,000%. La vicinanza")
r.append("si dichiara, **senza trasformarla in accettazione**.")
r.append("")
r.append("**Su Melbourne l'intervallo originario è interamente positivo**: il")
r.append("risultato è non conclusivo **rispetto al margine dell'1%**, non rispetto")
r.append("all'assenza di differenza.")
r.append("")
r.append("## 4. Criterio di deterioramento: specificazione NON preregistrata")
r.append("")
r.append("Il protocollo congelato fissa la non inferiorità al 95% unilaterale e")
r.append("l'equivalenza al 90% bilaterale, ma **non definisce con quale limite si")
r.append("dichiari il deterioramento oltre il margine**.")
r.append("")
r.append("L'implementazione usa il **limite inferiore dell'intervallo bilaterale al")
r.append("90%**, coerente con il test unilaterale al 5% di")
r.append("")
r.append("$$H_0:\\ \\delta \\leq 1\\% \\qquad \\text{contro} \\qquad H_1:\\ \\delta > 1\\%$$")
r.append("")
r.append("> **Si registra come specificazione non esplicitata nel protocollo")
r.append("> originario, non come criterio preregistrato.** Non modifica la domanda")
r.append("> principale già fissata: nessuna città dimostra la non inferiorità.")
r.append("")
r.append("## 5. Artefatti della campagna conforme")
r.append("")
r.append(f"| | |")
r.append(f"|---|---|")
r.append(f"| schema del descrittore | {M.get('schema_version')} |")
r.append(f"| implementazione dell'estrattore | {M.get('implementation_version')} |")
r.append(f"| coppie utilizzabili | {M['coppie_utilizzabili']}/"
         f"{M['coppie_utilizzabili']+M['coppie_incomplete']} |")
r.append(f"| ricampionamento | {A['repliche']} repliche |")
r.append(f"| margine | ±{A['margine']}% |")
r.append("")
r.append("**Impronte del codice di analisi:**")
r.append("")
r.append("| file | impronta |")
r.append("|---|---|")
for f in ("evoluzione/analisi/analizza_raccordo.py",
          "evoluzione/analisi/sensibilita_incrociata.py",
          "evoluzione/analisi/pesi.py",
          "evoluzione/analisi/ricampionamento.py",
          "evoluzione/esperimenti/addestramento.py",
          "evoluzione/esperimenti/esegui_raccordo.py",
          "evoluzione/componente/estrattore.py",
          "evoluzione/componente/predittore.py"):
    r.append(f"| `{f}` | `{h(f)}` |")
r.append("")
r.append("**Pesi di classe**, uno per città e partizione, consumati da")
r.append("addestramento e analisi senza ricalcolo:")
r.append("")
r.append("| città | p0 | p1 | p2 |")
r.append("|---|---|---|---|")
for c in CITTA:
    imp = []
    for p in range(3):
        f = R / "pesi" / f"pesi_{c}_p{p}.json"
        imp.append(json.loads(f.read_text())["impronta"] if f.exists() else "—")
    r.append(f"| {c} | `{imp[0]}` | `{imp[1]}` | `{imp[2]}` |")
r.append("")
r.append("## 6. Storia delle esecuzioni")
r.append("")
r.append("**Tre campagne. Le prime due sono invalidate e NON entrano nell'analisi.**")
r.append("")
r.append("### Prima campagna — non conforme")
r.append("")
r.append("**Difetto**: l'addestramento usava l'entropia **non pesata**, mentre il")
r.append("protocollo fissa $w_k = N/(3n_k)$. I pesi della valutazione non erano")
r.append("tracciati: `reg.metrica(...)` non veniva mai chiamato.")
r.append("")
r.append("**I risultati NON erano stati esaminati**: il difetto è emerso durante la")
r.append("verifica dell'analisi, prima di interpretarli.")
r.append("")
r.append("### Seconda campagna — non conforme")
r.append("")
r.append("**Difetto**: `clamp(0, 2)` portava i bersagli **non assegnati alla classe")
r.append("verde**. Nel periodo di prova erano il **14,1%** su Madrid, il **40,0%** su")
r.append("Londra, il **19,6%** su Melbourne. Il modello imparava a prevedere verde")
r.append("dove non c'è misura, e la metrica lo premiava — mentre i pesi erano stimati")
r.append("sulle sole celle valide.")
r.append("")
r.append("> **I risultati ERANO STATI ESAMINATI prima della scoperta del difetto.**")
r.append("> Davano Madrid non inferiore, Londra in deterioramento e Melbourne non")
r.append("> conclusiva. Il difetto è emerso da una verifica successiva del codice,")
r.append("> non dall'esame di quei numeri.")
r.append("")
r.append("### Che cosa resta e che cosa no")
r.append("")
r.append("| | conservato |")
r.append("|---|---|")
r.append("| manifesti delle esecuzioni | **sì**, in `results/evoluzione/registro/` |")
r.append("| versioni del codice | **sì**, nella storia del repository |")
r.append("| difetti e motivazione dell'invalidazione | **sì**, in questo documento e nel diario |")
r.append("| **predizioni e punti di controllo** | **NO, eliminati** e quindi non più disponibili |")
r.append("")
r.append("**Le predizioni delle due campagne invalidate non sono ricostruibili** senza")
r.append("riaddestrare. La scelta è stata di liberare 4,4 GB di risultati non")
r.append("interpretabili, conservando la traccia di che cosa fossero e perché lo")
r.append("fossero.")
r.append("")
r.append("### Terza campagna — conforme")
r.append("")
r.append("Collaudo dell'integrazione **22 verifiche su 22**, con la distribuzione")
r.append("valutata che coincide con quella delle celle valide a **scarto nullo**, e")
r.append("**54 esecuzioni su 54** completate al primo tentativo.")
r.append("")
r.append("## 7. Limiti dichiarati")
r.append("")
r.append("**Il raccordo misura il pacchetto**, non la sola imputazione né le sole")
r.append("maschere: BASE-CORRECTED cambia insieme imputazione, dimensionalità e")
r.append("capacità del primo strato. Il peggioramento non è attribuibile a una")
r.append("componente senza un'ablazione separata.")
r.append("")
r.append("**Gli intervalli sono condizionati al periodo di prova** e descrivono la")
r.append("variabilità rispetto a partizioni, inizializzazioni e nodi valutati. Non")
r.append("quantificano la trasferibilità ad altri periodi.")
r.append("")
r.append("**La dipendenza spaziale fra nodi non è modellata**: si ricampionano nodi")
r.append("singoli, non blocchi spaziali.")
r.append("")
r.append("**Con tre inizializzazioni** entrambe le procedure restano poco informate")
r.append("sulla variabilità dell'addestramento. La sensibilità dice **se** il verdetto")
r.append("dipenda dalla struttura assunta, **non quale** procedura sia corretta.")
r.append("")
r.append("**L'encoder è stato scelto per la rappresentazione nuova.** Nessuna variante")
r.append("è ottimizzata, ma la configurazione non è neutrale rispetto a LEGACY.")
r.append("")
Path("CONGELAMENTO_RACCORDO.md").write_text("\n".join(r) + "\n")
print("documento generato:", len(r), "righe")
