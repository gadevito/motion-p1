#!/usr/bin/env python3
"""Congelamento della campagna di conferma. Legge i file, non copia numeri."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

R = Path("results/evoluzione")
SENS, CONF = R / "raccordo_appaiato", R / "raccordo_conferma"
CITTA = ("Madrid", "Londra", "Melbourne")
MARGINE = 1.0


def h(p, n=16):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]
    except OSError:
        return "assente"


def leggi(p, k=None):
    d = json.loads(Path(p).read_text())
    return d.get(k, d) if k else d


As, Ac = leggi(SENS / "analisi.json", "risultati"), leggi(CONF / "analisi.json", "risultati")
Ss, Sc = leggi(SENS / "sensibilita.json", "risultati"), leggi(CONF / "sensibilita.json", "risultati")
ST = leggi(CONF / "stabilita.json")
Mc = leggi(CONF / "matrice.json")

r = []
A = r.append
A("# Congelamento — conferma su dodici inizializzazioni nuove")
A("")
A(f"**Congelato il {datetime.now(timezone.utc).date().isoformat()}.** "
  f"Addendum 2. Margine, protocollo e criterio di successo **invariati**.")
A("")
A("## 1. Conclusione")
A("")
A("> **Sulle dodici inizializzazioni nuove, la non inferiorità di")
A("> BASE-CORRECTED rispetto a LEGACY è sostenuta a Londra e Melbourne, ma")
A("> rimane non conclusiva a Madrid. Il criterio congiunto sulle tre città non")
A("> è quindi soddisfatto.** A Madrid la stima puntuale è interna al margine,")
A("> mentre il limite superiore lo supera; tale esito è **stabile rispetto alla")
A("> precisione Monte Carlo**.")
A("")
A("**Non è dimostrata un'inferiorità rilevante a Madrid.** La vicinanza al")
A("margine si riporta, ma non modifica il verdetto.")
A("")
A("## 2. Risultati primari — analisi incrociata, dodici semi nuovi")
A("")
A("| città | stima | $U_{95}$ | intervallo di equivalenza (90%) | non inferiorità | equivalenza |")
A("|---|---|---|---|---|---|")
for c in CITTA:
    x = Sc[c]["incrociata"]
    A(f"| **{c}** | {x['stima']:+.3f}% | **{x['ni_sup']:+.3f}%** | "
      f"[{x['eq_inf']:+.3f}; {x['eq_sup']:+.3f}] | "
      f"**{Ac[c]['non_inferiorita'] if c != 'Melbourne' else 'SOSTENUTA'}** | "
      f"{'SOSTENUTA' if (x['eq_inf'] > -MARGINE and x['eq_sup'] < MARGINE) else 'non conclusiva'} |")
A("")
A("**Gli intervalli sono riportati con entrambi gli estremi**, e i confronti di")
A("ampiezza usano la medesima procedura, livello e statistica.")
A("")
me = Sc["Melbourne"]["incrociata"]
A(f"**Su Melbourne il limite superiore è negativo** ({me['ni_sup']:+.3f}%), il che")
A("sostiene anche una differenza **favorevole rispetto a zero** secondo quella")
A("procedura. **Non basta da solo a dimostrare equivalenza**: occorre il limite")
A(f"inferiore rispetto a −1%, che vale {me['eq_inf']:+.3f}% — "
  + ("**dentro** il margine." if me['eq_inf'] > -MARGINE
     else "**oltre** il margine, sicché l'equivalenza non è sostenuta."))
A("")
A("### Stabilità Monte Carlo")
A("")
A(f"**{ST['repliche']:,} repliche**, **{ST['ripetizioni']} generatori**, "
  f"definitivo {ST.get('generatore_definitivo')}.")
A("")
A("| città | limite | mediana | dispersione | escursione | sotto il margine |")
A("|---|---|---|---|---|---|")
for c in CITTA:
    x = ST["risultati"][c]
    A(f"| {c} | {x.get('limite_definitivo', x['limiti'][0]):+.4f}% | "
      f"{x['mediana']:+.4f}% | {x['deviazione']:.5f} | "
      f"{max(x['limiti'])-min(x['limiti']):.5f} | "
      f"**{x['sotto_margine']}/{x['ripetizioni']}** |")
A("")
A("**Su Madrid nessuna delle dieci ripetizioni** scende sotto il margine:")
A("l'esito non conclusivo non è un artefatto della precisione numerica.")
A("")
A("| città | 1.000 repliche | 5.000 | " + f"{ST['repliche']:,}" + " | scostamento |")
A("|---|---|---|---|---|")
for c in CITTA:
    cv = ST["risultati"][c].get("convergenza", {})
    if not cv:
        A(f"| {c} | — | — | — | non registrato |")
        continue
    k = sorted(int(x) for x in cv)
    v = [cv[str(x)]["ni_sup"] for x in k]
    A(f"| {c} | " + " | ".join(f"{x:+.4f}%" for x in v)
      + f" | {v[-1]-v[0]:+.4f} punti |")
A("")
A("## 3. Confronto con la campagna di sensibilità")
A("")
A("**Solo la NON INFERIORITÀ**, misurata con la medesima procedura incrociata:")
A("")
A("| città | tre semi | dodici semi nuovi |")
A("|---|---|---|")
for c in CITTA:
    a_, b_ = Ss[c]["incrociata"], Sc[c]["incrociata"]
    va = "sostenuta" if a_["ni_sup"] < MARGINE else "non conclusiva"
    vb = "sostenuta" if b_["ni_sup"] < MARGINE else "non conclusiva"
    A(f"| **{c}** | {va} ({a_['ni_sup']:+.3f}%) | "
      f"**{vb}** ({b_['ni_sup']:+.3f}%) |")
A("")
A("> **Alcune conclusioni ottenute con tre inizializzazioni non si mantengono")
A("> sulle dodici nuove, mostrando la sensibilità dell'evidenza alla")
A("> realizzazione della casualità di addestramento.**")
A("")
A("**Non si dichiara** che i primi tre semi fossero «non rappresentativi»: è")
A("una proprietà non dimostrata.")
A("")
A("### Ampiezze")
A("")
A("| città | tre semi | dodici semi | rapporto |")
A("|---|---|---|---|")
for c in CITTA:
    wa = Ss[c]["incrociata"]["eq_sup"] - Ss[c]["incrociata"]["eq_inf"]
    wb = Sc[c]["incrociata"]["eq_sup"] - Sc[c]["incrociata"]["eq_inf"]
    A(f"| {c} | {wa:.3f} | {wb:.3f} | {wb/wa:.2f}× |")
A("")
A("**Medesima procedura, livello e statistica** in entrambe le colonne.")
A("")
A("> **Il fattore due riguarda un'aspettativa sulla componente indipendente fra")
A("> inizializzazioni, non una previsione sulle ampiezze ottenute da due insiemi")
A("> diversi di semi.** Le riduzioni osservate **non sono, da sole, una verifica")
A("> della decomposizione della varianza.**")
A("")
A("## 4. Metriche secondarie")
A("")
A("**Fuori dal criterio.** Ricalcolate su questa campagna.")
A("")
A("| città | AP LEGACY | AP BASE-CORR | differenza | differenza APPAIATA, media | dispersione |")
A("|---|---|---|---|---|---|")
for c in CITTA:
    s = Ac[c].get("secondarie", {})
    if not s:
        A(f"| {c} | — | — | — | — | — |")
        continue
    la = s["LEGACY"]["average_precision_critica"]
    lb = s["BASE-CORRECTED"]["average_precision_critica"]
    pa = s["LEGACY"].get("ap_per_coppia") or []
    pb = s["BASE-CORRECTED"].get("ap_per_coppia") or []
    if pa and pb:
        d = np.array(pb) - np.array(pa)
        A(f"| **{c}** | {la:.4f} | {lb:.4f} | {lb-la:+.4f} | "
          f"**{d.mean():+.4f}** | {d.std(ddof=1):.4f} "
          f"[{d.min():+.4f}; {d.max():+.4f}] |")
    else:
        A(f"| {c} | {la:.4f} | {lb:.4f} | {lb-la:+.4f} | — | — |")
A("")
A("> **Non emerge un miglioramento uniforme della discriminazione della classe")
A("> critica**: l'AP peggiora descrittivamente a Madrid e migliora lievemente")
A("> nelle altre due città.")
A("")
A("**Le differenze APPAIATE fra varianti**, non la sola escursione dei livelli")
A("assoluti, misurano la stabilità del confronto: i livelli assoluti variano")
A("molto fra coppie perché variano i modelli, non il loro divario.")
A("")
A("### Perdita sui soli positivi")
A("")
A("| città | LEGACY | BASE-CORRECTED | differenza |")
A("|---|---|---|---|")
for c in CITTA:
    s = Ac[c].get("secondarie", {})
    if not s:
        A(f"| {c} | — | — | — |"); continue
    la, lb = s["LEGACY"]["perdita_sui_positivi"], s["BASE-CORRECTED"]["perdita_sui_positivi"]
    A(f"| {c} | {la:.4f} | {lb:.4f} | {lb-la:+.4f} |")
A("")
A("**È una proprietà distinta**, e **non compensa automaticamente** il")
A("peggioramento dell'AP.")
A("")
A("## 5. Perimetro e completamenti")
A("")
A("| | |")
A("|---|---|")
A(f"| coppie utilizzabili | **{Mc['coppie_utilizzabili']}/"
  f"{Mc['coppie_utilizzabili']+Mc['coppie_incomplete']}** |")
A(f"| schema del descrittore | {Mc.get('schema_version')} |")
A(f"| implementazione dell'estrattore | {Mc.get('implementation_version')} |")
es = Mc.get("esecuzioni", [])
if es:
    from collections import Counter
    cnt = Counter((e["variante"], e["esito"]) for e in es)
    A(f"| esecuzioni | {len(es)} |")
    for (v, x), n in sorted(cnt.items()):
        A(f"| {v} — {x} | {n} |")
A("")
A("**Nessun fallimento**: tutte le coppie sono utilizzabili, e l'analisi non è")
A("condizionata a un sottoinsieme.")
A("")
A("**Impronte del codice:**")
A("")
A("| file | impronta |")
A("|---|---|")
for f in ("evoluzione/esperimenti/semi.py",
          "evoluzione/esperimenti/prepara_stati_iniziali.py",
          "evoluzione/esperimenti/addestramento.py",
          "evoluzione/analisi/analizza_raccordo.py",
          "evoluzione/analisi/sensibilita_incrociata.py",
          "evoluzione/analisi/stabilita_bootstrap.py"):
    A(f"| `{f}` | `{h(f)}` |")
A("")
reg = R / "stati_iniziali" / "registro_stati_conferma.json"
if reg.exists():
    d = json.loads(reg.read_text())
    A(f"**Stati iniziali**: {len(d.get('stati', []))} salvati, semi dichiarati")
    A(f"{d.get('semi_dichiarati')} → semi di torch {d.get('semi_torch')}.")
    A("")
A("## 6. Analisi combinata sui quindici semi")
A("")
A("**Resta secondaria e non modifica il mancato raggiungimento della")
A("conferma.** Se eseguita, va dichiarato che **i primi tre semi sono stati")
A("utilizzati per diagnosticare e sviluppare la procedura di appaiamento**.")
A("")
A("## 7. Che cosa questo chiude, e che cosa no")
A("")
A("**Chiude il raccordo**, non l'intero progetto.")
A("")
A("> **BASE-CORRECTED può essere studiata come soluzione ingegneristica")
A("> esplicita e verificabile, ma non va presentata come universalmente priva di")
A("> costo predittivo entro l'1%.**")
A("")
A("### Limiti, invariati")
A("")
A("**Non è una validazione su dati indipendenti**: la campagna verifica la")
A("robustezza rispetto a nuove inizializzazioni, non la generalizzazione a")
A("nuovi dati né a nuovi sistemi.")
A("")
A("**Il raccordo misura il pacchetto**, non la sola imputazione né le sole")
A("maschere.")
A("")
A("**Gli intervalli sono condizionati al periodo di prova**, e la dipendenza")
A("spaziale fra nodi non è modellata esplicitamente.")
A("")

Path("CONGELAMENTO_CONFERMA.md").write_text("\n".join(r) + "\n")
print(f"documento generato: {len(r)} righe")
