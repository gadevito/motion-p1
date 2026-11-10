# Candidate items (P0 §8, phase 2)

Extracted from the frozen inventory (`inventory.json` sha256 `187f7cde9b1858b67494d44aaa4a41cc2172a31b5bfd9cbc5fddd2573c45dfd6`) at `main` aa9f478b3fa8, `paper4` ef31396c28cf. `candidates.json` sha256 `08f3bba5c3911924d0830a48d4627c9c4001bd77fed360c94e5460ce0c8a5817`. Verbatim text; no type, phase or status: those are decided in phases 3 and 5. A candidate is not a problem.

## Counts

- `main`, deviation: 5
- `main`, git commit: 50
- `main`, record note: 40
- `main`, register row: 35
- `main`, report flag: 79
- `main`, tag diff: 569
- `paper4`, deviation: 3
- `paper4`, git commit: 25
- `paper4`, record note: 24
- `paper4`, register row: 26
- `paper4`, report flag: 1

## `main` — deviation

**C-main-DEV-001** · `protocol/E4.md` · line 30 (text pattern)

```
| citta' | Madrid, Londra, Melbourne. **PEMS04 rinviato a E6**: sulla verifica esterna non esiste E′ (ne' F), e crearli e' il disegno di E6, parte A. Deviazione dal §8, dichiarata qui. |
```

**C-main-DEV-002** · `protocol/E4.md` · line 52 (text pattern)

```
   durata, su griglia regolare: 5, 29, 77, 173, 653. Deviazione dal §8,
```

**C-main-DEV-003** · `protocol/E5.md` · line 142 (text pattern)

```
quello, indipendentemente dai semi. **Questa e' una deviazione dalla lettera
```

**C-main-DEV-004** · `protocol/E5.md` · line 150 (text pattern)

```
revisore il 4/10**: deviazione dalla lettera del §9 coerente con il suo scopo
```

**C-main-DEV-005** · `protocol/E8.md` · line 85 (text pattern)

```
**Deviazione del 9/10, dopo il pilota di tempo e prima di scegliere qualunque
```


## `main` — git commit

**C-main-GIT-001** · commit 207f23f435b1, 2026-11-10T16:38:36+01:00 · register: 33, 34

```
registro: voce 34, la voce 33 è ritirata (la seconda macchina del 12/10 era Spark, commit 01af3f7); processo: rettifica datata in I3
```

**C-main-GIT-002** · commit 00a790db5761, 2026-11-10T16:25:57+01:00 · register: 22, 33

```
processo: incidente I3 (voce 22, falso positivo del controllo di appaiamento), verifica preliminare; registro voce 33, causa della 22 corretta (stessa architettura)
```

**C-main-GIT-003** · commit f60c00a3a6ed, 2026-11-10T16:19:17+01:00 · register: 23

```
processo: incidente I2 (Paper 4, voce 23, pesi di classe nel confronto dei placement), verifica preliminare; orario della revisione corretto dalla sequenza dei commit
```

**C-main-GIT-004** · commit ca99ef25c2f1, 2026-11-10T15:49:23+01:00 · register: 29

```
processo: incidente I1 (voce 29, AUC su 19 soglie), verifica preliminare della ricostruzione dalle tracce; lacune dichiarate
```

**C-main-GIT-005** · commit 0a4a33a786e2, 2026-11-10T12:28:49+01:00 · register: 32

```
registro: voce 32, codice di terzi MoGERNN rimosso dal tracciamento e LICENSE CC BY 4.0
```

**C-main-GIT-006** · commit 4013add4099b, 2026-11-03T20:37:20+01:00 · register: 30, 31

```
paper1: verifica dei numeri sul manoscritto diviso in sezioni; dilatazioni nella forma del testo; figura della rete con la tabella degli embedding B; registro inglese, voci 30 e 31

- tabelle_paper1.verifica legge main.tex con i file di sezione richiamati da \input espansi (sections/,
  supplement/); gli \input di figures/ restano non espansi, come prima (tabelle generate, non testo
  trascritto). Senza questo la verifica non vedeva i numeri del manoscritto diviso il 1/11.
- voce «dilatazioni»: il testo stampa «1, 2, 4 and 8» (scelta di Gabriele, 3/11).
- figura_rete.py, versione inglese: «B: K×8» e «mean of B», come la figura decisa da Gabriele (3/11).
- register_of_corrections.en.md: voci 30 (riscrittura della storia) e 31 (soglia di congestione).
Provato prima del commit con il giro completo 20261103T154653Z (manoscritto 59e772c): TUTTO COINCIDE,
48 fasi; la figura rigenerata dal giro coincide con quella del manoscritto.

Paper1
```

**C-main-GIT-007** · commit b4ab62a8c3b0, 2026-11-03T12:38:32+01:00 · register: 31

```
E18-quater, forma standard: parte B (classi per sensore nei bersagli di prova), generatore del congelamento, fase E18QUATER in main.py, tabelle del supplemento (sezione E dopo E10; accanto a C5), protocollo aggiornato; registro voce 31 (soglia di congestione nel manoscritto)
```

**C-main-GIT-008** · commit 94d8807537f6, 2026-11-01T09:53:38+01:00 · register: unregistered

```
main.py: opzione --solo-testo, verifica di testo senza rigenerazione

Con --solo-testo main.py non esegue alcuna fase e non rigenera alcun numero. Si appoggia a un giro
completo concluso con TUTTO COINCIDE sugli stessi ingressi: una cartella di lavoro conservata
(rapporto.json) o un CONFRONTO registrato (protocol/spark/CONFRONTO_<tag>.md, commit OR3 dal tag);
predefinito il piu' recente valido, scelta esplicita con --rif e --rif-commit. Verifica:
- ingressi: impronte di results/evoluzione uguali a quelle registrate da quel giro; impronte citate
  nei congelamenti;
- trascrizioni: ogni valore stampato nel testo (verifica di tabelle_paper1) contro il congelato e
  contro il rigenerato di quel giro;
- tabelle e figure del manoscritto: riusate da quel giro, confrontate con la versione del manoscritto
  di quel giro (identiche, o solo testo con gli stessi numeri; PDF identici al byte);
- rimandi: \ref e \Sref con la loro etichetta, nessuna etichetta duplicata, \cite con \bibitem.
Scrive CONFRONTO.md con l'esito e «verifica di testo su giro completo <giro>, OR3 <hash>»; uscita 0
solo se tutto coincide. Il giro completo resta il riferimento: la verifica di testo non lo sostituisce
al tag (il giro completo del tag m lo fa la Spark).

Paper1
```

**C-main-GIT-009** · commit 8b177d20dc11, 2026-10-31T21:00:56+01:00 · register: 30

```
E18 parte D: limite storico 923c02e (era 964e4f5 prima della riscrittura della storia, voce 30)
```

**C-main-GIT-010** · commit f0431247e5ef, 2026-10-31T11:42:55+01:00 · register: 30

```
Riscrittura della storia prima della pubblicazione: tabella hash prima -> pubblicato, voce 30 del registro
```

**C-main-GIT-011** · commit 217624d6f28c, 2026-10-30T13:51:10+01:00 · register: unregistered

```
main.py, fase E18TER: esegue tutte le parti, come il congelamento; riga scritta il 30/10 dall'esecutore, corretta dal giro

Il giro del 30/10 su df9ad70 eseguiva analizza_e18ter.py --parte livelli: la parte wce16 (colonna wCE di F17 con la
definizione del manoscritto) mancava dalla rigenerazione, che risultava DIVERSO per la sola voce /wce16 (1.293
numeri con scarto 0) e riscriveva F17 con la wCE di E16. Ora --parte tutte.

Paper1
```

**C-main-GIT-012** · commit 8177eb217eff, 2026-10-29T10:49:16+01:00 · register: 29

```
paper1: voce 29 nella traduzione inglese del registro; riassunto E18 con le impronte dopo e18-bis

Paper1
```

**C-main-GIT-013** · commit e03a5926810e, 2026-10-29T10:45:31+01:00 · register: 29

```
CONGELAMENTO_E18 rigenerato (parte C completa, voce 29), riga 29 del registro; rimosso voce28.py
```

**C-main-GIT-014** · commit 784a4fb6e1e4, 2026-10-29T10:38:07+01:00 · register: 29

```
E18-bis: parte C con ECE, log-loss e Brier sulla finestra > 1 settimana; voce 29 (non 28) per la ROC empirica, nota datata nel generatore
```

**C-main-GIT-015** · commit 7d5aa3fa7547, 2026-10-29T10:36:04+01:00 · register: 28

```
paper1: voce 28 nella traduzione inglese del registro; impronte nuove di protocol/E6.md, protocol/E14.md e CONGELAMENTO_E14B.md nei riassunti (dai file); tabella G21 in caratteri compatti

Paper1
```

**C-main-GIT-016** · commit 1a3381f57999, 2026-10-29T10:30:15+01:00 · register: 28

```
congelamento_e14b.json rigenerato con la voce 28
```

**C-main-GIT-017** · commit 2d4bb450213b, 2026-10-29T10:29:31+01:00 · register: unregistered

```
Merge branch 'esecutore/voce28'

# Conflicts:
#	protocol/REGISTRO_CORREZIONI.md
```

**C-main-GIT-018** · commit 30e15b872607, 2026-10-29T10:17:03+01:00 · register: 27

```
paper1: E18 nel supplemento (sezione G da congelamento_e18.json: ROC empirica, bootstrap per sensore, margini, provenienza della politica), righe F'(1 sett.) delle tabelle di E16 dalla parte C (correzione 27), 24 verifiche nuove dei numeri stampati; voce 27 del registro chiusa; riassunto E18

Paper1
```

**C-main-GIT-019** · commit db06fa303df5, 2026-10-29T10:14:34+01:00 · register: 28

```
Voce 28: nomi di ruolo nelle note sulle correzioni (E6, E14, generatore E14-B, correzione 23), CONGELAMENTO_E14B rigenerato con nota datata; distance.csv di PEMS04 non usato (ADDENDUM §7); ripartizione di results/ per il deposito
```

**C-main-GIT-020** · commit 754a20acfae0, 2026-10-29T09:58:51+01:00 · register: unregistered

```
E18: congelamento (C correzione 27 con controllo, A ROC/pAUC/richiami a FA fissi, B bootstrap per sensore, D provenienza della politica)
```

**C-main-GIT-021** · commit dc8ea6d2b201, 2026-10-28T22:18:58+01:00 · register: 1, 27

```
paper1: README inglese come README.md (italiano in README.it.md); registro italiano consolidato protocol/REGISTRO_CORREZIONI.md (voci 1–27, originale), register_of_corrections.en.md come sua traduzione

Paper1
```

**C-main-GIT-022** · commit c1f4751e8c99, 2026-10-28T22:10:39+01:00 · register: unregistered

```
paper1: livello inglese del repository (README.en, glossario, riassunti E3–E18, registro delle correzioni 1–27)

Quattro file nuovi, nessun file esistente modificato. Gli originali italiani restano il documento di riferimento.

Paper1
```

**C-main-GIT-023** · commit d7b9f509ce6f, 2026-10-28T21:32:53+01:00 · register: unregistered

```
E18: parte C (correzione 27, E16 su origini > 1 settimana) con controllo bloccante; rapporto di forma per la stima di A
```

**C-main-GIT-024** · commit a3384ed455f2, 2026-10-28T21:18:02+01:00 · register: unregistered

```
E18: protocollo di analisi dalla seconda revisione (A ROC/pAUC, B bootstrap per sensore, C correzione 27 E16, D provenienza politica); firmato
```

**C-main-GIT-025** · commit cc286a819da1, 2026-10-15T08:59:04+02:00 · register: unregistered

```
Statica causale predefinita (correzione del difetto 21, dopo E14): OR3_STATICA assente = causale (variante a); --statica=congelata su 18 esecutori riproduce la campagna; statica dell'addestramento da statica_addestramento; adatta_F, valuta_prova, seleziona_F, E6/E6a seleziona-F, refresh, costi_e4, rho da statica_cella; collauda_protocolli fissa congelata; preflight 15 (E14 n. 8): identita' al bit con m_r perturbata dopo t0+24h, blocca su congelata. Collaudi 8/8 19/19 37/37 25/25 24/24 11/11, preflight 15/15 (14/15 su congelata), pilota E14 nc scarto 0, main.py --solo E2 congelata: tutto coincide
```

**C-main-GIT-026** · commit 6f672454afe7, 2026-10-15T08:14:26+02:00 · register: unregistered

```
Merge branch 'esecutore/difetto-23'
```

**C-main-GIT-027** · commit 1ce57696561d, 2026-10-15T08:06:02+02:00 · register: unregistered

```
Difetto 26: il controllo PEMS confronta (tau, N) e riporta la delta wCE di validazione a parte; CONGELAMENTO_E14B.md rigenerato con correzione datata
```

**C-main-GIT-028** · commit f90ceafe78b0, 2026-10-13T21:13:16+02:00 · register: unregistered

```
Difetto 23: frequenze_classi.py legge gli artefatti usati (pesi_griglia, pesi_pems04, pesi_pems08 p0-p5) con impronta per file; correzione datata in protocol/E6.md con la tabella rigenerata. Nessun effetto sui risultati
```

**C-main-GIT-029** · commit ab039e1ef35f, 2026-10-13T07:42:58+02:00 · register: unregistered

```
paper1: main.py — tolleranza combinata; indice delle impronte deterministico

- confronto numerico |d| <= atol + rtol*|congelato| (atol 1e-10, rtol 1e-9,
  come numpy.isclose) al posto del solo relativo: un criterio solo relativo
  bocciava statistiche dell'ordine di 1e-3 per scarti di 1e-11 (Spark)
- documenti: righe con gli stessi testi e numeri entro la stessa tolleranza
  non fanno fallire (sono riportate come informative)
- impronte citate senza nome di file: vince il file d'origine (SHA dei byte
  o campo impronta di primo livello), poi l'ordine alfabetico; prima vinceva
  il primo file trovato da rglob, che dipende dal filesystem (Mac e Spark
  davano e6_risultati.json/e8_risultati.json contro e6_scelta_gated.json/
  e8_soglie.json)
- CONFRONTO.md riporta le impronte del codice di analysis/

Nessun giro: il tag f aspetta E14 stadio A ed esecutore/e14, difetto-23.

Paper1
```

**C-main-GIT-030** · commit 3a20a945b1c1, 2026-10-12T22:09:05+02:00 · register: unregistered

```
paper1: CONFRONTO.md di riferimento per il tag e; \label nelle tabelle del supplementare

Giro completo di analysis/main.py sul merge 9f8ca34 (difetto 22) con il
cambio di analysis/tabelle_suppl.py qui committato (\label tab:suppC3/C8/C9;
era finito per errore nel commit di E14 poi spostato su esecutore/e14);
manoscritto 2c6e4e0 (pulito): TUTTO COINCIDE, risultati reali invariati.
Nuovo: 8 voci della §III "Network" (125 voci del manoscritto);
verifica_appaiamento.py cambiato dopo il congelamento di E2 (difetto 22,
01af3f7); riproducibilita_spark.json ed e14_stadio0.json fra gli ingressi.
Figure e tabelle del manoscritto rigenerate identiche byte per byte.

Paper1
```

**C-main-GIT-031** · commit 01af3f7ac40e, 2026-10-12T20:05:54+02:00 · register: 22

```
Esecutore: voce 22 — tolleranza del controllo di appaiamento 1e-12 -> 1e-7 (float32 fra architetture: Spark 4,9e-9 per elemento, 3,8e-11 sulla wCE di cella, 1,2e-14 coerenza interna; riproducibilita_spark.json 0f628bcbb05a6cf6)
```

**C-main-GIT-032** · commit c58df00f376b, 2026-10-12T08:21:10+02:00 · register: unregistered

```
paper1: impronta canonica dei file di scelta

I file di scelta (e4_scelta_gated, e6_scelta_gated, e6a_scelta_gated,
e8_soglie) includono l'istante di generazione e un'impronta calcolata anche
su quell'istante: rigenerati, cambiavano a ogni giro e CONFRONTO.md non era
identico fra due giri. main.py confronta ora l'impronta canonica (json a
chiavi ordinate, senza istante e senza il campo impronta); una differenza fa
fallire; il controllo resta. Verificato sui quattro file: congelato =
rigenerato. Registrato in NOTE come scelta, non difetto.

Paper1
```

**C-main-GIT-033** · commit 02be9e174265, 2026-10-11T22:15:43+02:00 · register: unregistered

```
paper1: manoscritto nel repo

OR3/paper1 (prima deliverables/paper1, che ora e' un collegamento simbolico
qui): main.tex, supplementary.tex, NOTE_PER_GLI_AUTORI.md,
letter_MoGERNN_authors.txt, IEEEtran.cls, figure prodotte da
analysis/main.py --paper paper1 e tabella C1; esclusi PDF compilati, PDF di
riferimento e template (paper1/.gitignore).

Il manoscritto contiene gia' il punto 1 del revisore (11/10): tutti i tempi
dalla sessione unica (costi_tabella_sessione.json), abstract 13-39 s /
127-401 s / 377-2,229 s, rapporti 3.0x-16.1x, "about 1 s per sensor per week",
token a costo zero in addestramento, riaddestramento uguale a 24 h e a 1 sett.,
nota di Tab. II (sessione unica; tempi di E3-bis ed E6 superati). NOTE:
difetto 17 chiuso, difetto 20 (prosa di E5), tempi superati. main.pdf: 9 pagine.

Paper1
```

**C-main-GIT-034** · commit 25af2ef00a9c, 2026-10-11T22:03:39+02:00 · register: 20

```
Merge esecutore/e5-prosa: voce 20, prosa di E5 stabile nel tempo
```

**C-main-GIT-035** · commit 03bcece3ecf2, 2026-10-11T22:03:39+02:00 · register: 20

```
Esecutore: voce 20 — CONGELAMENTO_E5 rigenerato per la riga di prosa su E3-bis (stessi numeri 52cdd962ff9888f6; impronta 069509f0570bbc0a)
```

**C-main-GIT-036** · commit e824dbee4dc2, 2026-10-10T18:15:50+02:00 · register: unregistered

```
Merge esecutore/e3-riviste: difetto 19, conteggio delle riviste dal solo lancio di E3
```

**C-main-GIT-037** · commit db9f8f3b1c24, 2026-10-10T18:15:50+02:00 · register: unregistered

```
Esecutore: difetto 19 — riviste di E3 dal solo lancio (108 manifesti per braccio, per impronta); rimisure con etichetta propria nel registro; CONGELAMENTO_E3 rigenerato (impronta 110ec4be3f3f9151)
```

**C-main-GIT-038** · commit d8ef81299651, 2026-10-10T18:09:49+02:00 · register: unregistered

```
paper1: analysis/main.py, prima versione

Rigenera ogni numero del Paper 1 dalle predizioni per cella con il codice
statistico del repository e lo confronta con i congelamenti:
- sandbox con clone APFS di results/evoluzione (altrove collegamenti
  simbolici e controllo d'integrita'); nulla viene scritto in results/
- 34 fasi: architettura dai checkpoint, scelte su validazione (confrontate e
  ripristinate), test con ricampionamento, E3/E3-bis/E7, generatori E2-E8
- confronto numero per numero con i json congelati e dei CONGELAMENTO_E*.md
  (date e impronte mascherate; differenze di sola prosa separate)
- tabelle del manoscritto (analysis/tabelle_paper1.py) e tabella C1
- impronte dei file citate nei congelamenti (analysis/impronte.py)
- rapporto deterministico analysis/rigenerazione/CONFRONTO.md (tracciato),
  per il diff fra macchine
- figure: gli script esistenti, con --lingua en verso paper1/figures/
  (stile in evoluzione/analisi/stile_paper.py; in 'it' come prima)

Prima rigenerazione completa: tutti i numeri coincidono salvo il difetto 19
(riviste di E3, 108 -> 117 esecuzioni). CONFRONTO.md di riferimento al
prossimo giro, dopo la correzione del difetto 19 e la rimisura dei tempi.

Paper1
```

**C-main-GIT-039** · commit 416be4e23c1e, 2026-10-10T16:19:45+02:00 · register: unregistered

```
Merge esecutore/tempi-e6: tempi appaiati, E3-bis difetto 17, architettura dai checkpoint, metadati audit MoGERNN, ricognizione Paper 4
```

**C-main-GIT-040** · commit 05b1be7ccc2b, 2026-10-10T16:01:25+02:00 · register: unregistered

```
Esecutore: E3-bis §3 corretta (difetto 17) — R-orig(1 sett.) per citta' dai manifesti isolati, rapporto solo nella stessa citta'; patch letterale e congelamento rigenerato
```

**C-main-GIT-041** · commit d90f9e09aab6, 2026-10-09T16:36:13+02:00 · register: unregistered

```
E8: deviazione dichiarata (A non valutabile in validazione, eredita le soglie di C)
```

**C-main-GIT-042** · commit 6629f40fd549, 2026-10-08T07:25:20+02:00 · register: unregistered

```
da_E1: sorgente del predittore dal punto di controllo (undici canali su PEMS); difetto emerso in E6 seleziona-F
```

**C-main-GIT-043** · commit c25495cdb6b8, 2026-09-22T13:27:20+02:00 · register: unregistered

```
congelamento: fase E principale e selezione di F

108 punti E col protocollo principale, 0 falliti; 68 selezionati al
tetto di 2.290 aggiornamenti.

Selezione di F sui nuovi E: Madrid e Londra (50, 0.01), Melbourne
(200, 0.001). La scelta cambia in tutte e tre le citta' rispetto alla
selezione storica (200, 0.01): il trasferimento automatico sarebbe
stato scorretto. Margini sulla seconda configurazione: 0,0004 / 0,0029
/ 0,0021 wCE.

Audit MoGERNN: benchmark in isolamento, rettifica delle misure prese
durante la fase E.
```

**C-main-GIT-044** · commit 904c6d1a7761, 2026-09-19T10:08:23+02:00 · register: unregistered

```
fase 3 sospesa: rettifica del budget di addestramento

Un'«epoca» e' UN aggiornamento dell'ottimizzatore, non una passata sul
corpus: le campagne hanno usato al massimo 35 aggiornamenti su 32
istanti ciascuno, con validazione dopo ognuno. La denominazione del
protocollo non corrispondeva all'implementazione.

Scarto quantificato: 229 aggiornamenti per passata nominale, 35
eseguiti, 14,4% delle origini coperte.

Secondo fatto emerso: la validazione usa sempre i PRIMI 32 istanti del
periodo, mai altri. Il punto di controllo e' selezionato sul 2% del
periodo di validazione, in tutte le campagne.

Budget dei bracci addestrati da zero: 32 x K_iniziali = 20.160 finestre
per aggiornamento, uguale per C, P, A, R. Non 24.480 per R.

Campagne precedenti non cancellate: i risultati restano validi come
confronti SOTTO quel budget.
```

**C-main-GIT-045** · commit 5fdb881fd5af, 2026-09-18T08:32:27+02:00 · register: unregistered

```
chiusura del raccordo: conclusione definitiva

Nel protocollo induttivo a ventiquattro ore, con inizializzazione
controllata dei moduli comuni e dodici inizializzazioni nuove,
BASE-CORRECTED risulta non inferiore a LEGACY entro l'1% di wCE a
Londra e Melbourne. A Madrid l'esito resta non conclusivo. Il criterio
congiunto sulle tre citta' non e' soddisfatto.

L'audit finale non ha rilevato difetti nei percorsi implementativi
VERIFICATI: non esclude in assoluto qualsiasi errore. Sensibilita'
all'ottimizzazione ed effetto della rappresentazione possono interagire
e non sono necessariamente spiegazioni alternative.

Si adotta BASE-CORRECTED come base ingegneristica, motivandola con la
gestione esplicita e verificabile della disponibilita'. LEGACY resta il
riferimento documentato.
```

**C-main-GIT-046** · commit 0b7fc84dca4b, 2026-09-18T08:20:14+02:00 · register: unregistered

```
congelamento della conferma: criterio congiunto non soddisfatto

Non inferiorita' sostenuta a Londra e Melbourne, non conclusiva a Madrid.
Il criterio congiunto sulle tre citta' non e' soddisfatto. A Madrid la
stima puntuale e' interna al margine, il limite superiore lo supera, e
l'esito e' stabile alla precisione Monte Carlo: 0 ripetizioni su 10
sotto il margine.

Non e' dimostrata inferiorita' rilevante. Alcune conclusioni ottenute
con tre inizializzazioni non si mantengono sulle dodici nuove.

Le metriche secondarie non mostrano un miglioramento uniforme della
discriminazione della classe critica.

Chiude il raccordo, non il progetto: BASE-CORRECTED resta studiabile
come soluzione ingegneristica esplicita e verificabile, ma non e'
universalmente priva di costo predittivo entro l'1%.
```

**C-main-GIT-047** · commit 0ce3f293d1f2, 2026-09-17T22:44:55+02:00 · register: unregistered

```
protocollo di conferma: dodici inizializzazioni nuove

Addendum 2. Semi 101..112, verificati assenti dai manifesti di tutte le
campagne in qualunque ruolo. Perimetro, appaiamento, iperparametri e
metriche invariati: 3 x 3 x 12 x 2 = 216 addestramenti.

Conferma solo se tutte e tre le citta' hanno U95 < +1%. Criterio di
intersezione, nessuna correzione per molteplicita' sul verdetto
congiunto. L'analisi combinata sui quindici semi non puo' salvare una
conferma fallita sui dodici nuovi.

Un registro degli stati per campagna: quello unico veniva sovrascritto.
```

**C-main-GIT-048** · commit 83a9a8bacfac, 2026-09-17T21:13:52+02:00 · register: unregistered

```
congelamento dei risultati del raccordo

Nessuna citta' dimostra la non inferiorita' con entrambe le procedure.
L'evidenza di deterioramento a Londra non e' robusta alla specificazione
incrociata. Stime puntuali sfavorevoli a BASE-CORRECTED, incertezza
insufficiente per conclusioni robuste rispetto al margine.

Criterio di deterioramento registrato come specificazione non
preregistrata. Storia delle tre campagne, con i difetti delle due
invalidate e la dichiarazione di quali risultati erano stati esaminati.
```

**C-main-GIT-049** · commit 4525efa1f5f7, 2026-09-17T19:22:57+02:00 · register: unregistered

```
pesi come artefatto condiviso; ricampionamento corretto

La prima campagna e' archiviata come NON CONFORME: l'addestramento usava
l'entropia non pesata mentre il protocollo fissa w_k = N/(3 n_k), e i pesi
di valutazione non erano tracciati. Ricalcolare le metriche non
correggerebbe l'obiettivo dell'apprendimento: si riaddestra.

Artefatto dei pesi: nove vettori, uno per citta' e partizione, dai soli
nodi e periodo di addestramento. Consumato da addestramento e analisi,
non ricalcolato. Popolazione di conteggio dichiarata, conteggio per
orizzonte esplicito, classe assente che interrompe.

Ricampionamento: ogni occorrenza di partizione estrae le proprie
inizializzazioni. Correzione verificata: riduce la dispersione da 0,338
a 0,266, non la aumenta.

Tre prove mirate: 15/15. Integrazione: 19/19.
```

**C-main-GIT-050** · commit 9cde540ec14a, 2026-09-17T18:05:11+02:00 · register: unregistered

```
estrattore 1.3: copertura_coppie nel blocco di disponibilita' condiviso

Era calcolata solo dentro il ramo EXTENDED e restava a zero su
BASE-CORRECTED: le due varianti non condividevano davvero le informazioni
di disponibilita', che e' il requisito perche' il confronto isoli le
statistiche comportamentali.

Aggiunte due verifiche: che la componente sia calcolata, e che tutte e
quattordici coincidano fra le due varianti, confrontate una per una.

Schema invariato alla 1.2; disegno del raccordo invariato alla 4.
```


## `main` — record note

**C-main-REC-001** · `CONGELAMENTO_APPAIAMENTO.md` · line 105

```
tocca la sola BASE-CORRECTED, e il controllo non si è mosso.
```

**C-main-REC-002** · `CONGELAMENTO_APPAIAMENTO.md` · line 128

```
| città | LEGACY | BASE-CORRECTED | differenza |
```

**C-main-REC-003** · `CONGELAMENTO_APPAIAMENTO.md` · line 134

```
## 8. Una correzione da registrare
```

**C-main-REC-004** · `CONGELAMENTO_APPAIAMENTO.md` · line 162

```
| `BASE-CORRECTED_seme2029167940_c9_h32_b4_s5_d26` | `53f694125b859a667bc8c7b05b14a36b39b7997dadece0025eacd1b969c4feab` |
```

**C-main-REC-005** · `CONGELAMENTO_APPAIAMENTO.md` · line 163

```
| `BASE-CORRECTED_seme2029167940_c9_h32_b4_s5_d26_allineato` | `46abcf2919808209bec44037bc588b0aef72ddbc71d08fcd08d837afb916d301` |
```

**C-main-REC-006** · `CONGELAMENTO_APPAIAMENTO.md` · line 165

```
| `BASE-CORRECTED_seme1918988776_c9_h32_b4_s5_d26` | `4ac80675e6eeb97761d758b010239983087a3a5dc5ff37f2a2c53137c0b7dff4` |
```

**C-main-REC-007** · `CONGELAMENTO_APPAIAMENTO.md` · line 166

```
| `BASE-CORRECTED_seme1918988776_c9_h32_b4_s5_d26_allineato` | `517100256a86c3d02cca1c553f3e6cd30e3955dfc6df6f921ecfb984b181213f` |
```

**C-main-REC-008** · `CONGELAMENTO_APPAIAMENTO.md` · line 168

```
| `BASE-CORRECTED_seme2007055255_c9_h32_b4_s5_d26` | `8eb24b2ffa14fd1dc2c6e3f2215a757cccd3fb60b8936ddca39fce249b006b4f` |
```

**C-main-REC-009** · `CONGELAMENTO_APPAIAMENTO.md` · line 169

```
| `BASE-CORRECTED_seme2007055255_c9_h32_b4_s5_d26_allineato` | `d81808054d6c174e0dbfe7b5c4d3bcde5c842886278aa6278ca09a663ae6f9ab` |
```

**C-main-REC-010** · `CONGELAMENTO_APPAIAMENTO.md` · line 191

```
misurano la correzione. Serve una conferma su inizializzazioni nuove.
```

**C-main-REC-011** · `CONGELAMENTO_CONFERMA.md` · line 8

```
> BASE-CORRECTED rispetto a LEGACY è sostenuta a Londra e Melbourne, ma
```

**C-main-REC-012** · `CONGELAMENTO_CONFERMA.md` · line 104

```
| città | LEGACY | BASE-CORRECTED | differenza |
```

**C-main-REC-013** · `CONGELAMENTO_CONFERMA.md` · line 121

```
| BASE-CORRECTED — completata | 108 |
```

**C-main-REC-014** · `CONGELAMENTO_CONFERMA.md` · line 162

```
**Si adotta BASE-CORRECTED come base ingegneristica**, motivandola con la
```

**C-main-REC-015** · `CONGELAMENTO_CONFERMA.md` · line 177

```
> **BASE-CORRECTED può essere studiata come soluzione ingegneristica
```

**C-main-REC-016** · `CONGELAMENTO_E14.md` · line 118

```
- Preflight n. 8 (perturbazione di `m_r` dopo t₀ → `static_inputs` invariato): da aggiungere con la correzione del codice, qualunque sia l'esito (pre-registro, controlli, punto 2).
```

**C-main-REC-017** · `CONGELAMENTO_E14B.md` · line 5

```
Rigenerato il 2026-10-29 (registro, voce 28): nelle note sulle correzioni chi aveva trovato un difetto e' indicato con il ruolo («durante la stesura del manoscritto»), non con il nome di uno strumento di lavoro; nessun numero cambia.
```

**C-main-REC-018** · `CONGELAMENTO_E14B.md` · line 342

```
Correzione 2026-10-15 (registro, voce 26, trovata durante la stesura del manoscritto): la prima versione di questa sezione confrontava l'intero record della scelta, compresa la wCE di validazione (che fra Mac e Spark differisce di ~1e-9), e marcava «DIVERSA» scelte con (τ, N) identici; ora si confrontano (τ, N) e la Δ della wCE si riporta a parte.
```

**C-main-REC-019** · `CONGELAMENTO_E15.md` · line 3

```
Generato da `genera_congelamento_e15.py` al commit `1b5a4bb`, 2026-10-28 16:03 UTC. Protocollo `protocol/E15.md` (impronta `31d731567da30bb4`), firmato prima di ogni numero; `e15_risultati.json` impronta `82df1d02792e330e`. Statica «espansiva»: iniziali con copertura media su [0, t₀); nuovo sensore con finestra espansiva da t₀ all'origine corrente, minimo 24 h. Tre citta', episodio 1, partizioni [0, 1, 2], semi [201, 202, 203, 204, 205, 206]: 54 celle; 4000 ricampionamenti congiunti (partizioni × semi × sensori, schema di E4), seme 20261023, le STESSE estrazioni per le differenze causali e per quelle congelate. Letture del protocollo del 27/10 (in `protocol/E15.md`): per A e C_A i sensori di prova sono iniziali a tutti gli effetti, copertura su [0, t₀) in addestramento, selezione e valutazione; la finestra minima di 24 h e l'espansione valgono per C, F₀, F₀′, F′ e per la selezione di k sui nodi di validazione. **Rigenerato il 28/10/2026** con l'addendum di sola analisi del revisore (sezione 7-bis) e, nello stesso giorno, con i registri dei tempi come ingresso congelato in `protocol/e15/tempi/` (sezione 7-ter) e con il pilota letto da `protocol/e15/tempi/pilota_tempi_16.json` (terza rigenerazione): nuove impronte, numeri precedenti invariati.
```

**C-main-REC-020** · `CONGELAMENTO_E15.md` · line 119

```
## 7-bis. Addendum del 28/10/2026 (revisore, sola analisi; correzione datata)
```

**C-main-REC-021** · `CONGELAMENTO_E16.md` · line 5

```
**Deviazione dichiarata**: A non ha embedding per i sensori di validazione (E8 la esclude dalla validazione): senza calibrazione post-hoc; le differenze «A − C» dopo calibrazione usano A grezza e C calibrata.
```

**C-main-REC-022** · `CONGELAMENTO_E18.md` · line 5

```
Rigenerato il 2026-10-29 (seconda versione; la prima, del 28/10, aveva impronta `b284661178a15d9c`): (i) la sostituzione delle affermazioni a 19 soglie e' la **voce 29** del registro delle correzioni, non la 28 scritta nel protocollo §1 r. 61 (la 28 era gia' stata assegnata ai nomi di ruolo nelle note sulle correzioni): deviazione dichiarata in §6; (ii) la parte C e' completata con le metriche di F16 (ECE per classe, log-loss, Brier) sulla stessa finestra, come il protocollo §3 richiede («righe F′(1wk) di F16 ricalcolate»): la prima versione riportava la sola wCE. Nessun numero gia' congelato cambia.
```

**C-main-REC-023** · `CONGELAMENTO_E18.md` · line 7

```
## 1. Parte C — E16: finestra di F′(1 sett.) (correzione 27)
```

**C-main-REC-024** · `CONGELAMENTO_E18.md` · line 338

```
## 6. Deviazioni (con data e motivo)
```

**C-main-REC-025** · `CONGELAMENTO_E18.md` · line 341

```
- 28/10/2026, A.6: PEMS04 ha solo C, F₀′ e F′(1 sett.) (nessun E ne' A): A1, A2, A4 not defined (no E, no A); A3 and F₀′ − C only — come da A.6, non e' una deviazione. La validazione di PEMS04 non viene ricostruita (non serve ad A).
```

**C-main-REC-026** · `CONGELAMENTO_E18.md` · line 343

```
- 29/10/2026, numerazione: il protocollo §1 r. 61 assegnava alla sostituzione delle affermazioni a 19 soglie (ROC empirica) la voce 28 del registro delle correzioni; la voce 28 era gia' stata assegnata il 29/10 ai nomi di ruolo nelle note sulle correzioni, quindi la sostituzione e' la voce 29. Il protocollo non si modifica (firmato); §2c e il registro portano 29.
```

**C-main-REC-027** · `CONGELAMENTO_E18QUATER.md` · line 3

```
Generato da `genera_congelamento_e18quater.py` al commit `b4ab62a`, 2026-11-03 11:39 UTC. Protocollo `protocol/E18quater.md` (nota datata del 3/11/2026; impronta `56046a7784a5169e`); `e18quater_risultati.json` impronta `316f1f9a3b0fa29e`; `e18quater_classi_risultati.json` impronta `020fea6939297a96`. Nessun addestramento: parte A a modelli congelati di E15, parte B sola lettura dei bersagli.
```

**C-main-REC-028** · `CONGELAMENTO_E18TER.md` · line 161

```
## 4. Deviazioni e note datate
```

**C-main-REC-029** · `CONGELAMENTO_E3.md` · line 102

```
- **Correzione del 2026-10-10 (difetto 19 del registro)**: il conteggio delle riviste prendeva dal registro ogni esecuzione completata di R, R-orig e R-mon, comprese le 9 rimisure isolate di R-orig e R-mon fatte per la tabella dei costi (117 invece di 108). Ora il lancio di E3 e' definito dai 108 manifesti per braccio di `inserimento_griglia/`, elencati per impronta in `analisi_e3.json` (`riviste/<braccio>/lancio`), e di ogni cella conta la sola esecuzione che ha prodotto la wCE registrata; le rimisure future hanno etichetta propria nel registro (`…/rimisura`). Documento rigenerato, non modificato a mano.
```

**C-main-REC-030** · `CONGELAMENTO_E3bis.md` · line 47

```
- **Correzione del 2026-10-10 (difetto 17 del registro)**: la prima versione della sezione 3 scriveva «almeno 6×» dividendo la mediana di R-orig(1 sett.) sulle nove celle delle tre citta' per il solo F′(1 sett.) misurato in isolamento (Melbourne, la configurazione F piu' costosa nella citta' piu' piccola). Lo script ora riporta R-orig(1 sett.) per citta' dai manifesti isolati e il rapporto solo nella stessa citta'; il documento e' rigenerato, non modificato a mano.
```

**C-main-REC-031** · `CONGELAMENTO_E4.md` · line 121

```
- **Deviazione dal §8 del protocollo, dichiarata prima del lancio in E4.md**: curva a {6 h, 12 h, 24 h, 48 h, 1 settimana} invece di {1 h, 4 h, …}: sotto le 5 ore la regola delle origini non ne contiene alcuna.
```

**C-main-REC-032** · `CONGELAMENTO_E4.md` · line 122

```
- **Stima di costo del protocollo sbagliata, non deviazione**: «< 10 ore-processo» contava gli adattamenti; le 13 valutazioni per cella sull'intero periodo piu' le 12 intermedie della traiettoria hanno portato il lancio a 11.3 ore con 8 processi. Nessun parametro e' cambiato.
```

**C-main-REC-033** · `CONGELAMENTO_E5.md` · line 129

```
- **Sei semi invece di otto**: deviazione dalla lettera del §9 confermata dal revisore; la semiampiezza cambia di ±0,0003 fra 12 e 6 semi (sezione 3).
```

**C-main-REC-034** · `CONGELAMENTO_E5.md` · line 136

```
- **Correzione del 2026-10-11 (voce 20 del registro, documentazione)**: la frase precedente su E3-bis dipendeva da quali esperimenti esistevano al momento della generazione; `analysis/main.py` l'ha trovata diversa rigenerando (numeri identici, impronta dei numeri `52cdd962ff9888f6` da entrambe le parti). Resa stabile nel tempo; documento rigenerato, non modificato a mano.
```

**C-main-REC-035** · `CONGELAMENTO_E8.md` · line 3

```
**Congelato il 2026-10-10**, commit `853c8474b7ce`. Protocollo `protocol/E8.md` (impronta `611d3541a6086e19`), firmato al commit `1185d9ecceb39bdf` prima di ricostruire; deviazione del 9/10 dichiarata nel file (A eredita le soglie di C). **Nessun criterio**: è descrittivo. **Ogni numero e' calcolato da `genera_congelamento_e8.py`** da `e8_risultati.json` e `e8_soglie.json`. Va in appendice C; la frase derivata (§4) nel testo della sezione 5.1.
```

**C-main-REC-036** · `CONGELAMENTO_E8.md` · line 274

```
- Protocollo E8: A previsto in validazione, non valutabile (ha i nodi di prova): eredita le soglie di C — deviazione del 9/10.
```

**C-main-REC-037** · `CONGELAMENTO_E_F_PIPELINE_PRECEDENTE.md` · line 3

```
> **Risultati della pipeline precedente alla correzione della griglia temporale.** Le origini erano costruite per indice di riga: circa il 2,6% attraversava un salto della serie, con orizzonti che non corrispondevano al tempo reale. **Questi punti E e questa selezione di F non sono gli artefatti preparatori definitivi**: si rigenerano con la regola approvata. Le configurazioni scelte qui **non si trasferiscono** alla selezione corretta.
```

**C-main-REC-038** · `CONGELAMENTO_RACCORDO.md` · line 1

```
# Congelamento dei risultati del raccordo LEGACY ↔ BASE-CORRECTED
```

**C-main-REC-039** · `CONGELAMENTO_RACCORDO.md` · line 11

```
> BASE-CORRECTED, ma l'incertezza non consente conclusioni robuste rispetto
```

**C-main-REC-040** · `CONGELAMENTO_RACCORDO.md` · line 153

```
maschere: BASE-CORRECTED cambia insieme imputazione, dimensionalità e
```


## `main` — register row

**C-main-REG-001** · `protocol/REGISTRO_CORREZIONI.md` · line 23, item 1

```
| 1 | un lotto per epoca presentato come un'epoca | 35 aggiornamenti = 15 % di un passaggio; con un budget adeguato l'ordine dei modelli è cambiato | `evoluzione/RETTIFICA_BUDGET.md` |
```

**C-main-REG-002** · `protocol/REGISTRO_CORREZIONI.md` · line 24, item 2

```
| 2 | selezione del checkpoint su 32 istanti fissi di validazione (2 %) | selezione sull'intero insieme di validazione | `evoluzione/RETTIFICA_BUDGET.md` |
```

**C-main-REG-003** · `protocol/REGISTRO_CORREZIONI.md` · line 25, item 3

```
| 3 | un clamp che assegnava una classe ai bersagli mancanti | riguardava il 40 % dei bersagli di Londra; mascherati | `CONGELAMENTO_RACCORDO.md` |
```

**C-main-REG-004** · `protocol/REGISTRO_CORREZIONI.md` · line 26, item 4

```
| 4 | ramo statico e teste disallineati fra varianti (640 estrazioni in più) | artefatto canonico per impronta | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-005** · `protocol/REGISTRO_CORREZIONI.md` · line 27, item 5

```
| 5 | finestre costruite per indice attraverso i salti di calendario | orizzonte senza il significato dichiarato; 2,6 % delle origini escluse come non ammissibili | `CONGELAMENTO_E_F_PIPELINE_PRECEDENTE.md` |
```

**C-main-REG-006** · `protocol/REGISTRO_CORREZIONI.md` · line 28, item 6

```
| 6 | riga t₀ inclusa nell'adattamento | 77 origini invece di 78 | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-007** · `protocol/REGISTRO_CORREZIONI.md` · line 29, item 7

```
| 7 | descrittore addestrato su un'istantanea non causale di fine periodo | variante causale pre-registrata, non eseguita (paper, Limitations) | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-008** · `protocol/REGISTRO_CORREZIONI.md` · line 30, item 8

```
| 8 | popolazione di nodi 900/900/594 contro i 828/774/587 documentati | dichiarata | `evoluzione/RETTIFICA_POPOLAZIONE.md` |
```

**C-main-REG-009** · `protocol/REGISTRO_CORREZIONI.md` · line 31, item 9

```
| 9 | bracci dichiarati in sei punti; quattro dimenticati aggiungendo un braccio | tabella unica delle proprietà dei bracci, collaudo con 36 controlli | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-010** · `protocol/REGISTRO_CORREZIONI.md` · line 32, item 10

```
| 10 | R-orig e R-mon instradati nel ramo di adattamento | 216 esecuzioni, trovate dal tempo di calcolo, in quarantena con indice | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-011** · `protocol/REGISTRO_CORREZIONI.md` · line 33, item 11

```
| 11 | un riepilogo di fase sovrascritto da un lancio successivo | uscite scritte per lancio | `CONGELAMENTO_E3.md` |
```

**C-main-REG-012** · `protocol/REGISTRO_CORREZIONI.md` · line 34, item 12

```
| 12 | script di fattibilità che arrotondava le partizioni a 27 sensori invece di 26 | corretto prima del lancio | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-013** · `protocol/REGISTRO_CORREZIONI.md` · line 35, item 13

```
| 13 | un predittore a nove canali costruito qualunque fosse la sorgente | falliva su PEMS; città invariate | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-014** · `protocol/REGISTRO_CORREZIONI.md` · line 36, item 14

```
| 14 | un criterio post hoc non discriminante proposto in revisione dell'esperimento di copertura | corretto prima dell'uso | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-015** · `protocol/REGISTRO_CORREZIONI.md` · line 37, item 15

```
| 15 | un ramo di lettura del generatore delle metriche operative che scriveva «non distinguibile» per «sopra a qualche livello, mai sotto» | corretto prima del commit | `CONGELAMENTO_E8.md` |
```

**C-main-REG-016** · `protocol/REGISTRO_CORREZIONI.md` · line 38, item 16

```
| 16 | `np.trapz` assente nell'ambiente | trapezi espliciti | `CONGELAMENTO_E8.md` |
```

**C-main-REG-017** · `protocol/REGISTRO_CORREZIONI.md` · line 39, item 17a

```
| 17a | generatore di E3-bis: «almeno 6×» divideva la mediana di R-orig(1 sett.) sulle nove celle delle tre città per il solo F′(1 sett.) misurato in isolamento (Melbourne) | tempi per contesto dalla sessione unica (`costi_tabella_sessione.json`); rapporto solo nella stessa città; congelamento di E3-bis rigenerato (impronta `174d8e2d1808516c`) | `CONGELAMENTO_E3bis.md` |
```

**C-main-REG-018** · `protocol/REGISTRO_CORREZIONI.md` · line 40, item 17b

```
| 17b | in una bozza del manoscritto i tempi 36,8 s e 35,7 s erano attribuiti a F′(1 sett.) a Madrid e Londra; sono i tempi di gated(48 h) di E4 | manoscritto corretto con i tempi appaiati per città | `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-019** · `protocol/REGISTRO_CORREZIONI.md` · line 41, item 18

```
| 18 | una citazione in una bozza del manoscritto non corrispondeva al riferimento a cui rimandava | citazione tolta; il riferimento citato con il suo titolo | `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-020** · `protocol/REGISTRO_CORREZIONI.md` · line 42, item 19

```
| 19 | il conteggio delle riviste di E3 prendeva dal registro ogni esecuzione completata di R, R-orig e R-mon, comprese le 9 rimisure isolate fatte per la tabella dei costi (117 invece di 108) | lancio definito dai 108 manifesti per braccio, elencati per impronta in `analisi_e3.json`; ogni cella conta solo l'esecuzione che ha prodotto la wCE registrata; rimisure etichettate a parte; congelamento rigenerato, non modificato a mano; numeri del paper invariati | `CONGELAMENTO_E3.md` |
```

**C-main-REG-021** · `protocol/REGISTRO_CORREZIONI.md` · line 43, item 20

```
| 20 | una frase del congelamento di E5 su E3-bis dipendeva da quali esperimenti esistevano al momento della generazione; trovata diversa rigenerando (numeri identici) | frase resa stabile nel tempo; congelamento rigenerato, non modificato a mano | `CONGELAMENTO_E5.md` |
```

**C-main-REG-022** · `protocol/REGISTRO_CORREZIONI.md` · line 44, item 21

```
| 21 | ramo statico alimentato con la copertura del sensore sull'intera serie, test compreso | effetto misurato da E14: confinato ai bracci senza un'identità appresa per il sensore, wCE dei bracci spostata di ≤ 0,007; l'unica lettura a tre episodi che cambia lo fa a favore del paper; le cinque dichiarazioni ristabilite da capo a fondo con ingressi causali da E15; codice causale per default dopo lo studio (`--statica=congelata` riproduce la campagna congelata) | `protocol/E14.md`, `CONGELAMENTO_E14.md`, `CONGELAMENTO_E14B.md`, `CONGELAMENTO_E15.md` |
```

**C-main-REG-023** · `protocol/REGISTRO_CORREZIONI.md` · line 45, item 22

```
| 22 | il controllo di identità dei dati nella verifica dell'appaiamento di E2 confrontava aggregati float32 ricalcolati con rtol 10⁻¹²; fallito fra architetture diverse (scarto massimo sull'elemento 4,9 × 10⁻⁹) | tolleranza portata a 10⁻⁷; trovato rigenerando su una seconda macchina | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-024** · `protocol/REGISTRO_CORREZIONI.md` · line 46, item 23

```
| 23 | la tabella descrittiva congelata delle frequenze di classe (E6, `frequenze_classi.json`) era calcolata da un insieme precedente di file dei pesi di classe (campagna per indice) e da 3 delle 6 partizioni di PEMS08, non dai file caricati dagli esperimenti | tabella ricostruita dai file effettivamente caricati, con impronte; nessun effetto sui risultati; cambiano tre limiti descrittivi (città: classe congestionata fino a 15,9 % invece di 15,7 %; Madrid 9,0–9,5 %; Londra 15,4–15,9 %) | `protocol/E6.md` (correzione datata) |
```

**C-main-REG-025** · `protocol/REGISTRO_CORREZIONI.md` · line 47, item 24

```
| 24 | `adatta_F` costruiva un proprio vettore statico invece di prendere quello della cella; con le varianti di E14 F era adattato con lo scalare congelato e valutato con quello della variante; nessun effetto sui numeri congelati (lì i due coincidevano) | rilevato dal controllo 3 di E4 durante lo stadio B (scarti 10⁻⁴–10⁻³); corretto (commit `8f9afbf`), F riadattato, E4 rieseguito | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-026** · `protocol/REGISTRO_CORREZIONI.md` · line 48, item 25

```
| 25 | l'orchestratore dello stadio B (`esegui_e14b.sh`) eseguiva la fase «origini» di E6 prima di E6a, di cui legge le predizioni; nessun effetto sui numeri; `main.py` non coinvolto | trovato rigenerando da zero; fase spostata dopo E6a | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
```

**C-main-REG-027** · `protocol/REGISTRO_CORREZIONI.md` · line 49, item 26

```
| 26 | il generatore di E14-B confrontava l'intero record della scelta (τ, N) di PEMS, compresa la wCE di validazione che differisce di ~10⁻⁹ fra macchine, e marcava come «diverse» scelte (τ, N) identiche | solo documentazione, nessun effetto sui numeri; il generatore confronta (τ, N) e riporta a parte la differenza di wCE; congelamento rigenerato con correzione datata (commit `109aca5`, impronta `864b21c7796aefb2`) | `CONGELAMENTO_E14B.md` |
```

**C-main-REG-028** · `protocol/REGISTRO_CORREZIONI.md` · line 50, item 27

```
| 27 | in `esegui_e16.py` ogni braccio era valutato su tutte le origini dopo t₁; per F′(1 sett.) questo include la prima settimana, in cui l'embedding adattato usa dati fino a t₀ + 1 settimana, quindi le righe F′(1 sett.) delle tabelle di E16 sono su una finestra non causale per quel braccio; il controllo bloccante confrontava con l'aggregato congelato somma delle tre fasce e non poteva rilevarlo; la quota di calibrazione s di F₀ − C non è toccata | corretto da E18, parte C: righe F′(1 sett.) delle tabelle di E16 ricalcolate sulle origini più vecchie di una settimana per entrambi i bracci, parametri di calibrazione invariati; controllo bloccante sugli aggregati congelati superato (scarto relativo massimo 8,66 × 10⁻⁷, soglia 10⁻⁶) | `protocol/E18.md` §3, `CONGELAMENTO_E18.md` §1 |
```

**C-main-REG-029** · `protocol/REGISTRO_CORREZIONI.md` · line 51, item 28

```
| 28 | nelle note sulle correzioni (`protocol/E6.md` r. 265, `protocol/E14.md` r. 15, `genera_congelamento_e14b.py` r. 357, `evoluzione/analisi/correzione_difetto_23.py` r. 76) chi aveva trovato il difetto era indicato con il nome di uno strumento di lavoro anziche' con il ruolo | solo documentazione, nessun numero cambia: «trovato durante la stesura del manoscritto» nei quattro punti; `CONGELAMENTO_E14B.md` rigenerato dallo script con nota datata (2026-10-29). Impronte prima → dopo: `protocol/E6.md` `2644259cc48fae08` → `90818c7597925712`; `protocol/E14.md` `b669b5d8a269f1bd` → `b30984ca153d3e5d`; `CONGELAMENTO_E14B.md` `864b21c7796aefb2` → `58e774413c805d58`. Regola permanente dal 2026-10-29: nessun riferimento a strumenti di lavoro in file, commenti, messaggi di commit e note; dove serve, «revisione interna» o «stesura del manoscritto» | `protocol/REGISTRO_CORREZIONI.md`; `CONGELAMENTO_E14B.md` |
```

**C-main-REG-030** · `protocol/REGISTRO_CORREZIONI.md` · line 52, item 29

```
| 29 | l'AUC di E8-bis era calcolata su 19 soglie fisse (seconda revisione esterna, punto 3); le affermazioni che ne dipendevano sono ri-valutate sulla ROC empirica su tutti i punteggi distinti (E18 parte A, `CONGELAMENTO_E18.md` §2c). Il protocollo E18 §1 r. 61 chiamava questa voce «28»: il numero 28 era gia' assegnato (nomi di ruolo), quindi e' la 29; il protocollo firmato non si modifica, la deviazione e' dichiarata in `CONGELAMENTO_E18.md` §6 | E18 parte A (nessun addestramento); `CONGELAMENTO_E18.md` rigenerato il 2026-10-29 con nota datata, e con la parte C completata dalle stesse probabilita' con ECE per classe, log-loss e Brier sulla finestra > 1 settimana (protocollo §3; la prima versione riportava la sola wCE). Impronte prima → dopo: `CONGELAMENTO_E18.md` `b284661178a15d9c` → `54f5530ab845588c`; `e18_risultati.json` `4f705ba30cd5946c`; `congelamento_e18.json` `f054365ac1387dfd`. Rigenerato di nuovo il 2026-10-29: i tempi della parte A nel documento vengono dal registro `protocol/e18/tempi_parte_A.json` (prima esecuzione, 28/10), come per E15, perche' il giro di rigenerazione coincideva su tutti i numeri ma non sui tempi stampati; impronta `CONGELAMENTO_E18.md` `54f5530ab845588c` → `046fbffc7afcc5ff`. Rigenerato il 2026-10-29 (parte D): ricerca storica limitata ai commit fino alla firma del protocollo (OR3 `964e4f5`, manoscritto `ae12921`), stesso esito; impronta `CONGELAMENTO_E18.md` `046fbffc7afcc5ff` → `2e56a7202de95383`, `e18_risultati.json` `ddc86f7c534d44a2`, `congelamento_e18.json` `5f3138ca8f77ac9a` | `CONGELAMENTO_E18.md`; `results/evoluzione/e18_risultati.json`; `analysis/tabelle_suppl.py` (F17) |
```

**C-main-REG-031** · `protocol/REGISTRO_CORREZIONI.md` · line 53, item 30

```
| 30 | la storia del repository conteneva una copia antica del manoscritto (`paper1/`, cinque commit) e, nelle versioni passate di alcuni file e in due messaggi di commit, il nome di uno strumento di lavoro al posto del ruolo | solo storia, nessun numero cambia: riscrittura su un clone a parte prima della pubblicazione (2026-10-31): `paper1/` tolta da tutta la storia, nomi di ruolo nelle versioni passate, tag riscritti con gli stessi nomi; tabella hash prima → pubblicato in `protocol/RISCRITTURA_STORIA.md` (i file che citano hash non sono modificati: la tabella e' la chiave di lettura) | `protocol/RISCRITTURA_STORIA.md` |
```

**C-main-REG-032** · `protocol/REGISTRO_CORREZIONI.md` · line 54, item 31

```
| 31 | la descrizione della soglia di congestione nel manoscritto non corrisponde al codice: su Traffic4cast il riferimento di flusso libero e' per segmento (`free_flow_kph` dell'anagrafica, `evoluzione/esperimenti/costruisci_maschere.py` r. 26 e 146) e le classi sono 0,8/0,4 sul rapporto velocita'/riferimento (`data_collection/traffic4cast/t4c22_adapter.py` r. 11); su PEMS04 e PEMS08 il riferimento e' uno per partizione, il 95° percentile delle velocita' aggregate dei soli nodi iniziali nel periodo di addestramento, e le classi sono 0,8/0,5 (`evoluzione/esperimenti/estrai_pems04.py` r. 63-64, 119, 122) | errore di testo, nessun effetto sui risultati (3/11/2026): correzione del testo del manoscritto a cura della stesura; convenzioni dichiarate in `protocol/E18quater.md` (parte B) e nella didascalia della tabella delle classi per sensore (E18-quater) | `protocol/E18quater.md`, `CONGELAMENTO_E18QUATER.md` |
```

**C-main-REG-033** · `protocol/REGISTRO_CORREZIONI.md` · line 55, item 32

```
| 32 | il repository pubblico tracciava per intero il codice di MoGERNN (`evoluzione/MoGERNN-main/`, 38 file, compreso un modello pre-addestrato), codice di terzi il cui repository upstream non dichiara alcuna licenza; nessun numero del paper dipende da quel codice (solo i tre file di audit in `results/evoluzione/audit_mogernn/`) | rimosso dal tracciamento su `main` e `paper4` (commit 06e48d6 / ef7f6d6, 2026-11-10), con regola in `.gitignore` e `evoluzione/MoGERNN-main/ORIGINE.md` (URL upstream, commit e80f6ca, SHA-256 dei file di riferimento, identici alla copia usata); la copia resta locale per gli audit. Aggiunto `LICENSE` CC BY 4.0 (commit 3a07da8 / 1715e8f), la stessa del record Zenodo. La storia e i tag precedenti conservano i file; nessuna riscrittura. Nessun effetto sui numeri | `evoluzione/MoGERNN-main/ORIGINE.md`; `LICENSE`; revisione interna del 2026-11-10 |
```

**C-main-REG-034** · `protocol/REGISTRO_CORREZIONI.md` · line 56, item 33

```
| 33 | la voce 22 e il messaggio del commit 01af3f7 attribuiscono lo scarto di 4,9 × 10⁻⁹ a «architetture diverse»; la seconda macchina del 12/10 era un altro MacBook M3, stessa architettura: lo scarto viene da non-determinismo numerico fra ambienti (riduzioni, BLAS, thread, versioni), non dall'architettura. La correzione (tolleranza 10⁻⁷, poi tolleranza combinata in `main.py`, ab039e1) resta valida | causa corretta qui; la voce 22 non si modifica. Nessun effetto sui numeri. Trovato ricostruendo la sequenza dell'incidente dalle tracce | `protocol/processo/incidenti/I3.md`; commit 01af3f7, 9f8ca34, ab039e1; dichiarazione del responsabile sulla seconda macchina, 2026-11-10 |
```

**C-main-REG-035** · `protocol/REGISTRO_CORREZIONI.md` · line 57, item 34

```
| 34 | la voce 33 è errata e va ritirata: afferma, su una dichiarazione a memoria del responsabile, che la seconda macchina del 12/10 fosse un MacBook M3 della stessa architettura; il messaggio del commit della correzione (01af3f7) attribuisce lo scarto di 4,9 × 10⁻⁹ a Spark (aarch64), con `riproducibilita_spark.json` 0f628bcbb05a6cf6, e il 13/10 E14 stadio A gira sulla Spark (7c8eb28). La diagnosi originaria della voce 22 («fra architetture diverse») è sostenuta dalle tracce | la voce 33 resta nel registro come ritirata; la 22 non cambia. Nessun effetto sui numeri. Trovato dalla verifica documentaria dei revisori interni sulle schede degli incidenti (2026-11-10): una voce di registro scritta da una testimonianza senza controllare l'artefatto citato dal commit | revisori interni, 2026-11-10 | `protocol/processo/incidenti/I3.md`, rettifica; commit 01af3f7, 7c8eb28; `results/evoluzione/riproducibilita_spark.json` |
```


## `main` — report flag

**C-main-RPT-001** · `analysis/rigenerazione/CONFRONTO.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-002** · `analysis/rigenerazione/CONFRONTO.md` · line 16

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-003** · `analysis/rigenerazione/CONFRONTO.md` · line 127

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-004** · `analysis/rigenerazione/CONFRONTO.md` · line 196

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-005** · `analysis/rigenerazione/CONFRONTO.md` · line 285

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-006** · `analysis/rigenerazione/CONFRONTO.md` · line 293

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```

**C-main-RPT-007** · `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-008** · `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` · line 15

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-009** · `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` · line 138

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-010** · `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` · line 197

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-011** · `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` · line 286

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-012** · `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` · line 290

```
- `CONGELAMENTO_E3bis.md`: `-| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |`
```

**C-main-RPT-013** · `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` · line 291

```
- `CONGELAMENTO_E3bis.md`: `+| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 2.1e-11, Londra 2.2e-11, Melbourne 3.6e-11 |`
```

**C-main-RPT-014** · `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` · line 295

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```

**C-main-RPT-015** · `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-016** · `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` · line 15

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-017** · `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` · line 138

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-018** · `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` · line 197

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-019** · `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` · line 286

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-020** · `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` · line 290

```
- `CONGELAMENTO_E3bis.md`: `-| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |`
```

**C-main-RPT-021** · `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` · line 291

```
- `CONGELAMENTO_E3bis.md`: `+| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 2.1e-11, Londra 2.2e-11, Melbourne 3.6e-11 |`
```

**C-main-RPT-022** · `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` · line 295

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```

**C-main-RPT-023** · `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-024** · `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` · line 16

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-025** · `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` · line 159

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-026** · `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` · line 221

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-027** · `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` · line 310

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-028** · `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` · line 314

```
- `CONGELAMENTO_E3bis.md`: `-| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |`
```

**C-main-RPT-029** · `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` · line 315

```
- `CONGELAMENTO_E3bis.md`: `+| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 2.1e-11, Londra 2.2e-11, Melbourne 3.6e-11 |`
```

**C-main-RPT-030** · `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` · line 319

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```

**C-main-RPT-031** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-032** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · line 5

```
- esito: **DIFFERENZE O ERRORI**
```

**C-main-RPT-033** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · line 16

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-034** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · line 127

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-035** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · line 192

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-036** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · line 282

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-037** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · line 286

```
- `CONGELAMENTO_E3bis.md`: `-| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |`
```

**C-main-RPT-038** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · line 287

```
- `CONGELAMENTO_E3bis.md`: `+| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 2.1e-11, Londra 2.2e-11, Melbourne 3.6e-11 |`
```

**C-main-RPT-039** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · line 291

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```

**C-main-RPT-040** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-041** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` · line 16

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-042** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` · line 127

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-043** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` · line 192

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-044** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` · line 281

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-045** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` · line 285

```
- `CONGELAMENTO_E3bis.md`: `-| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |`
```

**C-main-RPT-046** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` · line 286

```
- `CONGELAMENTO_E3bis.md`: `+| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 2.1e-11, Londra 2.2e-11, Melbourne 3.6e-11 |`
```

**C-main-RPT-047** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` · line 290

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```

**C-main-RPT-048** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-049** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` · line 16

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-050** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` · line 127

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-051** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` · line 192

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-052** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` · line 281

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-053** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` · line 285

```
- `CONGELAMENTO_E3bis.md`: `-| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |`
```

**C-main-RPT-054** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` · line 286

```
- `CONGELAMENTO_E3bis.md`: `+| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 2.1e-11, Londra 2.2e-11, Melbourne 3.6e-11 |`
```

**C-main-RPT-055** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` · line 290

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```

**C-main-RPT-056** · `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-057** · `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` · line 16

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-058** · `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` · line 127

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-059** · `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` · line 192

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-060** · `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` · line 281

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-061** · `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` · line 285

```
- `CONGELAMENTO_E3bis.md`: `-| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |`
```

**C-main-RPT-062** · `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` · line 286

```
- `CONGELAMENTO_E3bis.md`: `+| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 2.1e-11, Londra 2.2e-11, Melbourne 3.6e-11 |`
```

**C-main-RPT-063** · `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` · line 290

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```

**C-main-RPT-064** · `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-065** · `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` · line 16

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-066** · `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` · line 127

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-067** · `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` · line 192

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-068** · `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` · line 281

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-069** · `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` · line 285

```
- `CONGELAMENTO_E3bis.md`: `-| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |`
```

**C-main-RPT-070** · `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` · line 286

```
- `CONGELAMENTO_E3bis.md`: `+| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 2.1e-11, Londra 2.2e-11, Melbourne 3.6e-11 |`
```

**C-main-RPT-071** · `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` · line 290

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```

**C-main-RPT-072** · `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` · line 3

```
Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.
```

**C-main-RPT-073** · `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` · line 16

```
| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
```

**C-main-RPT-074** · `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` · line 127

```
| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
```

**C-main-RPT-075** · `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` · line 196

```
Impronte canoniche dei file di scelta (istante di generazione e campo impronta mascherati; una differenza fa fallire):
```

**C-main-RPT-076** · `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` · line 285

```
## 5. Documenti: differenze di sola prosa (stessi numeri)
```

**C-main-RPT-077** · `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` · line 289

```
- `CONGELAMENTO_E3bis.md`: `-| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |`
```

**C-main-RPT-078** · `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` · line 290

```
- `CONGELAMENTO_E3bis.md`: `+| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 2.1e-11, Londra 2.2e-11, Melbourne 3.6e-11 |`
```

**C-main-RPT-079** · `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` · line 294

```
Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.
```


## `main` — tag diff

**C-main-TAG-001** · `CONGELAMENTO_E3bis.md` · paper1-freeze-20261010..paper1-freeze-20261010b

```
CONGELAMENTO_E3bis.md: numstat 7	3	CONGELAMENTO_E3bis.md
```

**C-main-TAG-002** · `evoluzione/analisi/architettura_ck.py` · paper1-freeze-20261010..paper1-freeze-20261010b

```
evoluzione/analisi/architettura_ck.py: numstat 111	0	evoluzione/analisi/architettura_ck.py
```

**C-main-TAG-003** · `evoluzione/audit/METADATI_AUDIT.md` · paper1-freeze-20261010..paper1-freeze-20261010b

```
evoluzione/audit/METADATI_AUDIT.md: numstat 21	0	evoluzione/audit/METADATI_AUDIT.md
```

**C-main-TAG-004** · `evoluzione/audit/metadati_audit.py` · paper1-freeze-20261010..paper1-freeze-20261010b

```
evoluzione/audit/metadati_audit.py: numstat 83	0	evoluzione/audit/metadati_audit.py
```

**C-main-TAG-005** · `evoluzione/esperimenti/costi_appaiati.py` · paper1-freeze-20261010..paper1-freeze-20261010b

```
evoluzione/esperimenti/costi_appaiati.py: numstat 159	0	evoluzione/esperimenti/costi_appaiati.py
```

**C-main-TAG-006** · `evoluzione/esperimenti/ricognizione_paper4.sh` · paper1-freeze-20261010..paper1-freeze-20261010b

```
evoluzione/esperimenti/ricognizione_paper4.sh: numstat 48	0	evoluzione/esperimenti/ricognizione_paper4.sh
```

**C-main-TAG-007** · `evoluzione/esperimenti/ricognizione_paper4_log.sh` · paper1-freeze-20261010..paper1-freeze-20261010b

```
evoluzione/esperimenti/ricognizione_paper4_log.sh: numstat 44	0	evoluzione/esperimenti/ricognizione_paper4_log.sh
```

**C-main-TAG-008** · `evoluzione/esperimenti/costi_appaiati.py` · paper1-freeze-20261010b..paper1-freeze-20261010c

```
evoluzione/esperimenti/costi_appaiati.py: numstat 43	4	evoluzione/esperimenti/costi_appaiati.py
```

**C-main-TAG-009** · `CONGELAMENTO_E3.md` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
CONGELAMENTO_E3.md: numstat 7	7	CONGELAMENTO_E3.md
```

**C-main-TAG-010** · `analysis/impronte.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
analysis/impronte.py: numstat 133	0	analysis/impronte.py
```

**C-main-TAG-011** · `analysis/main.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
analysis/main.py: numstat 586	0	analysis/main.py
```

**C-main-TAG-012** · `analysis/tabelle_paper1.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
analysis/tabelle_paper1.py: numstat 192	0	analysis/tabelle_paper1.py
```

**C-main-TAG-013** · `evoluzione/analisi/analizza_e3.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
evoluzione/analisi/analizza_e3.py: numstat 48	6	evoluzione/analisi/analizza_e3.py
```

**C-main-TAG-014** · `evoluzione/analisi/analizza_e4.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
evoluzione/analisi/analizza_e4.py: numstat 56	0	evoluzione/analisi/analizza_e4.py
```

**C-main-TAG-015** · `evoluzione/analisi/analizza_e5.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
evoluzione/analisi/analizza_e5.py: numstat 42	0	evoluzione/analisi/analizza_e5.py
```

**C-main-TAG-016** · `evoluzione/analisi/figura2_51.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
evoluzione/analisi/figura2_51.py: numstat 40	17	evoluzione/analisi/figura2_51.py
```

**C-main-TAG-017** · `evoluzione/analisi/figura_e8bis.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
evoluzione/analisi/figura_e8bis.py: numstat 28	11	evoluzione/analisi/figura_e8bis.py
```

**C-main-TAG-018** · `evoluzione/analisi/stile_paper.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
evoluzione/analisi/stile_paper.py: numstat 27	0	evoluzione/analisi/stile_paper.py
```

**C-main-TAG-019** · `evoluzione/esperimenti/esegui_inserimento.py` · paper1-freeze-20261010c..paper1-freeze-20261010d

```
evoluzione/esperimenti/esegui_inserimento.py: numstat 3	1	evoluzione/esperimenti/esegui_inserimento.py
```

**C-main-TAG-020** · `CONGELAMENTO_E6.md` · paper1-freeze-20261010d..paper1-freeze-20261010e

```
CONGELAMENTO_E6.md: numstat 4	4	CONGELAMENTO_E6.md
```

**C-main-TAG-021** · `evoluzione/esperimenti/esegui_e6.py` · paper1-freeze-20261010d..paper1-freeze-20261010e

```
evoluzione/esperimenti/esegui_e6.py: numstat 34	1	evoluzione/esperimenti/esegui_e6.py
```

**C-main-TAG-022** · `analysis/impronte.py` · paper1-freeze-20261010e..paper1-freeze-20261011

```
analysis/impronte.py: numstat 56	0	analysis/impronte.py
```

**C-main-TAG-023** · `analysis/main.py` · paper1-freeze-20261010e..paper1-freeze-20261011

```
analysis/main.py: numstat 35	4	analysis/main.py
```

**C-main-TAG-024** · `analysis/tabelle_paper1.py` · paper1-freeze-20261010e..paper1-freeze-20261011

```
analysis/tabelle_paper1.py: numstat 4	2	analysis/tabelle_paper1.py
```

**C-main-TAG-025** · `evoluzione/esperimenti/costi_appaiati.py` · paper1-freeze-20261010e..paper1-freeze-20261011

```
evoluzione/esperimenti/costi_appaiati.py: numstat 85	1	evoluzione/esperimenti/costi_appaiati.py
```

**C-main-TAG-026** · `evoluzione/esperimenti/costi_sessione.py` · paper1-freeze-20261010e..paper1-freeze-20261011

```
evoluzione/esperimenti/costi_sessione.py: numstat 267	0	evoluzione/esperimenti/costi_sessione.py
```

**C-main-TAG-027** · `CONGELAMENTO_E5.md` · paper1-freeze-20261011..paper1-freeze-20261011b

```
CONGELAMENTO_E5.md: numstat 5	4	CONGELAMENTO_E5.md
```

**C-main-TAG-028** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261011..paper1-freeze-20261011b

```
analysis/rigenerazione/CONFRONTO.md: numstat 582	0	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-029** · `analysis/impronte.py` · paper1-freeze-20261011b..paper1-freeze-20261011c

```
analysis/impronte.py: numstat 2	3	analysis/impronte.py
```

**C-main-TAG-030** · `analysis/main.py` · paper1-freeze-20261011b..paper1-freeze-20261011c

```
analysis/main.py: numstat 5	3	analysis/main.py
```

**C-main-TAG-031** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261011b..paper1-freeze-20261011c

```
analysis/rigenerazione/CONFRONTO.md: numstat 43	39	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-032** · `analysis/tabelle_paper1.py` · paper1-freeze-20261011b..paper1-freeze-20261011c

```
analysis/tabelle_paper1.py: numstat 21	11	analysis/tabelle_paper1.py
```

**C-main-TAG-033** · `analysis/main.py` · paper1-freeze-20261011c..paper1-freeze-20261012d

```
analysis/main.py: numstat 64	6	analysis/main.py
```

**C-main-TAG-034** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261011c..paper1-freeze-20261012d

```
analysis/rigenerazione/CONFRONTO.md: numstat 12	5	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-035** · `analysis/main.py` · paper1-freeze-20261012d..paper1-freeze-20261012e

```
analysis/main.py: numstat 6	0	analysis/main.py
```

**C-main-TAG-036** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261012d..paper1-freeze-20261012e

```
analysis/rigenerazione/CONFRONTO.md: numstat 15	3	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-037** · `analysis/tabelle_paper1.py` · paper1-freeze-20261012d..paper1-freeze-20261012e

```
analysis/tabelle_paper1.py: numstat 12	0	analysis/tabelle_paper1.py
```

**C-main-TAG-038** · `analysis/tabelle_suppl.py` · paper1-freeze-20261012d..paper1-freeze-20261012e

```
analysis/tabelle_suppl.py: numstat 133	0	analysis/tabelle_suppl.py
```

**C-main-TAG-039** · `evoluzione/analisi/riproducibilita_spark.py` · paper1-freeze-20261012d..paper1-freeze-20261012e

```
evoluzione/analisi/riproducibilita_spark.py: numstat 86	0	evoluzione/analisi/riproducibilita_spark.py
```

**C-main-TAG-040** · `evoluzione/analisi/verifica_appaiamento.py` · paper1-freeze-20261012d..paper1-freeze-20261012e

```
evoluzione/analisi/verifica_appaiamento.py: numstat 9	1	evoluzione/analisi/verifica_appaiamento.py
```

**C-main-TAG-041** · `CONGELAMENTO_E14.md` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
CONGELAMENTO_E14.md: numstat 131	0	CONGELAMENTO_E14.md
```

**C-main-TAG-042** · `CONGELAMENTO_E14B.md` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
CONGELAMENTO_E14B.md: numstat 354	0	CONGELAMENTO_E14B.md
```

**C-main-TAG-043** · `analysis/impronte.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
analysis/impronte.py: numstat 25	12	analysis/impronte.py
```

**C-main-TAG-044** · `analysis/main.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
analysis/main.py: numstat 33	5	analysis/main.py
```

**C-main-TAG-045** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
analysis/rigenerazione/CONFRONTO.md: numstat 84	41	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-046** · `analysis/tabelle_suppl.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
analysis/tabelle_suppl.py: numstat 166	0	analysis/tabelle_suppl.py
```

**C-main-TAG-047** · `evoluzione/analisi/correzione_difetto_23.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/analisi/correzione_difetto_23.py: numstat 95	0	evoluzione/analisi/correzione_difetto_23.py
```

**C-main-TAG-048** · `evoluzione/analisi/e14_stadio0.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/analisi/e14_stadio0.py: numstat 163	0	evoluzione/analisi/e14_stadio0.py
```

**C-main-TAG-049** · `evoluzione/analisi/e14b_fascio.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/analisi/e14b_fascio.py: numstat 85	0	evoluzione/analisi/e14b_fascio.py
```

**C-main-TAG-050** · `evoluzione/analisi/e14b_livelli.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/analisi/e14b_livelli.py: numstat 130	0	evoluzione/analisi/e14b_livelli.py
```

**C-main-TAG-051** · `evoluzione/analisi/frequenze_classi.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/analisi/frequenze_classi.py: numstat 41	17	evoluzione/analisi/frequenze_classi.py
```

**C-main-TAG-052** · `evoluzione/esperimenti/addestramento.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/addestramento.py: numstat 2	3	evoluzione/esperimenti/addestramento.py
```

**C-main-TAG-053** · `evoluzione/esperimenti/collauda_protocolli.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/collauda_protocolli.py: numstat 5	0	evoluzione/esperimenti/collauda_protocolli.py
```

**C-main-TAG-054** · `evoluzione/esperimenti/costi_e4.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/costi_e4.py: numstat 5	1	evoluzione/esperimenti/costi_e4.py
```

**C-main-TAG-055** · `evoluzione/esperimenti/e14b_prepara_copia.sh` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/e14b_prepara_copia.sh: numstat 67	0	evoluzione/esperimenti/e14b_prepara_copia.sh
```

**C-main-TAG-056** · `evoluzione/esperimenti/esegui_E.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_E.py: numstat 3	0	evoluzione/esperimenti/esegui_E.py
```

**C-main-TAG-057** · `evoluzione/esperimenti/esegui_e14.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_e14.py: numstat 296	0	evoluzione/esperimenti/esegui_e14.py
```

**C-main-TAG-058** · `evoluzione/esperimenti/esegui_e14b.sh` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_e14b.sh: numstat 125	0	evoluzione/esperimenti/esegui_e14b.sh
```

**C-main-TAG-059** · `evoluzione/esperimenti/esegui_e2.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_e2.py: numstat 8	3	evoluzione/esperimenti/esegui_e2.py
```

**C-main-TAG-060** · `evoluzione/esperimenti/esegui_e4.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_e4.py: numstat 5	2	evoluzione/esperimenti/esegui_e4.py
```

**C-main-TAG-061** · `evoluzione/esperimenti/esegui_e5.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_e5.py: numstat 7	4	evoluzione/esperimenti/esegui_e5.py
```

**C-main-TAG-062** · `evoluzione/esperimenti/esegui_e6.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_e6.py: numstat 9	0	evoluzione/esperimenti/esegui_e6.py
```

**C-main-TAG-063** · `evoluzione/esperimenti/esegui_e6a.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_e6a.py: numstat 7	0	evoluzione/esperimenti/esegui_e6a.py
```

**C-main-TAG-064** · `evoluzione/esperimenti/esegui_e8.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_e8.py: numstat 6	2	evoluzione/esperimenti/esegui_e8.py
```

**C-main-TAG-065** · `evoluzione/esperimenti/esegui_f0.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_f0.py: numstat 7	2	evoluzione/esperimenti/esegui_f0.py
```

**C-main-TAG-066** · `evoluzione/esperimenti/esegui_inserimento.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_inserimento.py: numstat 3	0	evoluzione/esperimenti/esegui_inserimento.py
```

**C-main-TAG-067** · `evoluzione/esperimenti/esegui_refresh.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/esegui_refresh.py: numstat 5	1	evoluzione/esperimenti/esegui_refresh.py
```

**C-main-TAG-068** · `evoluzione/esperimenti/inserimento.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/inserimento.py: numstat 92	4	evoluzione/esperimenti/inserimento.py
```

**C-main-TAG-069** · `evoluzione/esperimenti/ricostruisci_predizioni.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/ricostruisci_predizioni.py: numstat 13	4	evoluzione/esperimenti/ricostruisci_predizioni.py
```

**C-main-TAG-070** · `evoluzione/esperimenti/riselezione_rmon_test.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/riselezione_rmon_test.py: numstat 5	2	evoluzione/esperimenti/riselezione_rmon_test.py
```

**C-main-TAG-071** · `evoluzione/esperimenti/seleziona_F.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/seleziona_F.py: numstat 5	3	evoluzione/esperimenti/seleziona_F.py
```

**C-main-TAG-072** · `evoluzione/esperimenti/sensibilita_rho_e2.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/sensibilita_rho_e2.py: numstat 5	1	evoluzione/esperimenti/sensibilita_rho_e2.py
```

**C-main-TAG-073** · `evoluzione/esperimenti/veterani_e3.py` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
evoluzione/esperimenti/veterani_e3.py: numstat 5	2	evoluzione/esperimenti/veterani_e3.py
```

**C-main-TAG-074** · `protocol/E14.md` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/E14.md: numstat 91	0	protocol/E14.md
```

**C-main-TAG-075** · `protocol/E6.md` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/E6.md: numstat 17	0	protocol/E6.md
```

**C-main-TAG-076** · `protocol/e14_stadio0.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14_stadio0.json: numstat 2218	0	protocol/e14_stadio0.json
```

**C-main-TAG-077** · `protocol/e14b/a/analisi_e3.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/analisi_e3.json: numstat 1864	0	protocol/e14b/a/analisi_e3.json
```

**C-main-TAG-078** · `protocol/e14b/a/congelamento_e2.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/congelamento_e2.json: numstat 777	0	protocol/e14b/a/congelamento_e2.json
```

**C-main-TAG-079** · `protocol/e14b/a/congelamento_e3.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/congelamento_e3.json: numstat 3244	0	protocol/e14b/a/congelamento_e3.json
```

**C-main-TAG-080** · `protocol/e14b/a/congelamento_e3bis.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/congelamento_e3bis.json: numstat 676	0	protocol/e14b/a/congelamento_e3bis.json
```

**C-main-TAG-081** · `protocol/e14b/a/congelamento_e4.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/congelamento_e4.json: numstat 8069	0	protocol/e14b/a/congelamento_e4.json
```

**C-main-TAG-082** · `protocol/e14b/a/congelamento_e5.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/congelamento_e5.json: numstat 2073	0	protocol/e14b/a/congelamento_e5.json
```

**C-main-TAG-083** · `protocol/e14b/a/congelamento_e7.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/congelamento_e7.json: numstat 2165	0	protocol/e14b/a/congelamento_e7.json
```

**C-main-TAG-084** · `protocol/e14b/a/copertura_e4.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/copertura_e4.json: numstat 5832	0	protocol/e14b/a/copertura_e4.json
```

**C-main-TAG-085** · `protocol/e14b/a/curve_e8bis_punti.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/curve_e8bis_punti.json: numstat 1596	0	protocol/e14b/a/curve_e8bis_punti.json
```

**C-main-TAG-086** · `protocol/e14b/a/e14b_livelli_a.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e14b_livelli_a.json: numstat 358	0	protocol/e14b/a/e14b_livelli_a.json
```

**C-main-TAG-087** · `protocol/e14b/a/e3bis_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e3bis_risultati.json: numstat 207	0	protocol/e14b/a/e3bis_risultati.json
```

**C-main-TAG-088** · `protocol/e14b/a/e4_griglia_test.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e4_griglia_test.json: numstat 80	0	protocol/e14b/a/e4_griglia_test.json
```

**C-main-TAG-089** · `protocol/e14b/a/e4_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e4_risultati.json: numstat 1539	0	protocol/e14b/a/e4_risultati.json
```

**C-main-TAG-090** · `protocol/e14b/a/e4_scelta_gated.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e4_scelta_gated.json: numstat 95	0	protocol/e14b/a/e4_scelta_gated.json
```

**C-main-TAG-091** · `protocol/e14b/a/e5_k_secondaria.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e5_k_secondaria.json: numstat 36	0	protocol/e14b/a/e5_k_secondaria.json
```

**C-main-TAG-092** · `protocol/e14b/a/e5_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e5_risultati.json: numstat 1075	0	protocol/e14b/a/e5_risultati.json
```

**C-main-TAG-093** · `protocol/e14b/a/e5_settimana_vs_A.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e5_settimana_vs_A.json: numstat 149	0	protocol/e14b/a/e5_settimana_vs_A.json
```

**C-main-TAG-094** · `protocol/e14b/a/e6_origini_comuni.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e6_origini_comuni.json: numstat 19	0	protocol/e14b/a/e6_origini_comuni.json
```

**C-main-TAG-095** · `protocol/e14b/a/e6_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e6_risultati.json: numstat 170	0	protocol/e14b/a/e6_risultati.json
```

**C-main-TAG-096** · `protocol/e14b/a/e6_scelta_gated.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e6_scelta_gated.json: numstat 51	0	protocol/e14b/a/e6_scelta_gated.json
```

**C-main-TAG-097** · `protocol/e14b/a/e6a_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e6a_risultati.json: numstat 124	0	protocol/e14b/a/e6a_risultati.json
```

**C-main-TAG-098** · `protocol/e14b/a/e6a_scelta_gated.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e6a_scelta_gated.json: numstat 50	0	protocol/e14b/a/e6a_scelta_gated.json
```

**C-main-TAG-099** · `protocol/e14b/a/e6bis_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e6bis_risultati.json: numstat 63	0	protocol/e14b/a/e6bis_risultati.json
```

**C-main-TAG-100** · `protocol/e14b/a/e7_posthoc.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e7_posthoc.json: numstat 368	0	protocol/e14b/a/e7_posthoc.json
```

**C-main-TAG-101** · `protocol/e14b/a/e7_stadio1.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e7_stadio1.json: numstat 1788	0	protocol/e14b/a/e7_stadio1.json
```

**C-main-TAG-102** · `protocol/e14b/a/e8_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e8_risultati.json: numstat 4923	0	protocol/e14b/a/e8_risultati.json
```

**C-main-TAG-103** · `protocol/e14b/a/e8_soglie.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e8_soglie.json: numstat 353	0	protocol/e14b/a/e8_soglie.json
```

**C-main-TAG-104** · `protocol/e14b/a/e8bis_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/e8bis_risultati.json: numstat 2416	0	protocol/e14b/a/e8bis_risultati.json
```

**C-main-TAG-105** · `protocol/e14b/a/manifesto.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/manifesto.json: numstat 48	0	protocol/e14b/a/manifesto.json
```

**C-main-TAG-106** · `protocol/e14b/a/predizioni_e2/controllo_e2.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_e2/controllo_e2.json: numstat 5736	0	protocol/e14b/a/predizioni_e2/controllo_e2.json
```

**C-main-TAG-107** · `protocol/e14b/a/predizioni_f0/controllo_f0.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_f0/controllo_f0.json: numstat 1518	0	protocol/e14b/a/predizioni_f0/controllo_f0.json
```

**C-main-TAG-108** · `protocol/e14b/a/predizioni_fase3/controllo_A.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_fase3/controllo_A.json: numstat 1522	0	protocol/e14b/a/predizioni_fase3/controllo_A.json
```

**C-main-TAG-109** · `protocol/e14b/a/predizioni_fase3/controllo_C.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_fase3/controllo_C.json: numstat 1522	0	protocol/e14b/a/predizioni_fase3/controllo_C.json
```

**C-main-TAG-110** · `protocol/e14b/a/predizioni_fase3/controllo_F.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_fase3/controllo_F.json: numstat 1522	0	protocol/e14b/a/predizioni_fase3/controllo_F.json
```

**C-main-TAG-111** · `protocol/e14b/a/predizioni_fase3/controllo_P.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_fase3/controllo_P.json: numstat 1522	0	protocol/e14b/a/predizioni_fase3/controllo_P.json
```

**C-main-TAG-112** · `protocol/e14b/a/predizioni_fase3/controllo_R-mon.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_fase3/controllo_R-mon.json: numstat 1522	0	protocol/e14b/a/predizioni_fase3/controllo_R-mon.json
```

**C-main-TAG-113** · `protocol/e14b/a/predizioni_fase3/controllo_R-orig.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_fase3/controllo_R-orig.json: numstat 1522	0	protocol/e14b/a/predizioni_fase3/controllo_R-orig.json
```

**C-main-TAG-114** · `protocol/e14b/a/predizioni_fase3/controllo_R.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_fase3/controllo_R.json: numstat 1522	0	protocol/e14b/a/predizioni_fase3/controllo_R.json
```

**C-main-TAG-115** · `protocol/e14b/a/predizioni_fase3_672/controllo_R-orig.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/predizioni_fase3_672/controllo_R-orig.json: numstat 1522	0	protocol/e14b/a/predizioni_fase3_672/controllo_R-orig.json
```

**C-main-TAG-116** · `protocol/e14b/a/riselezione_rmon_test.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/riselezione_rmon_test.json: numstat 79	0	protocol/e14b/a/riselezione_rmon_test.json
```

**C-main-TAG-117** · `protocol/e14b/a/veterani_e3.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/a/veterani_e3.json: numstat 140	0	protocol/e14b/a/veterani_e3.json
```

**C-main-TAG-118** · `protocol/e14b/c/analisi_e3.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/analisi_e3.json: numstat 1864	0	protocol/e14b/c/analisi_e3.json
```

**C-main-TAG-119** · `protocol/e14b/c/congelamento_e2.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/congelamento_e2.json: numstat 777	0	protocol/e14b/c/congelamento_e2.json
```

**C-main-TAG-120** · `protocol/e14b/c/congelamento_e3.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/congelamento_e3.json: numstat 3244	0	protocol/e14b/c/congelamento_e3.json
```

**C-main-TAG-121** · `protocol/e14b/c/congelamento_e3bis.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/congelamento_e3bis.json: numstat 676	0	protocol/e14b/c/congelamento_e3bis.json
```

**C-main-TAG-122** · `protocol/e14b/c/congelamento_e4.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/congelamento_e4.json: numstat 8069	0	protocol/e14b/c/congelamento_e4.json
```

**C-main-TAG-123** · `protocol/e14b/c/congelamento_e5.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/congelamento_e5.json: numstat 2073	0	protocol/e14b/c/congelamento_e5.json
```

**C-main-TAG-124** · `protocol/e14b/c/congelamento_e7.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/congelamento_e7.json: numstat 2159	0	protocol/e14b/c/congelamento_e7.json
```

**C-main-TAG-125** · `protocol/e14b/c/copertura_e4.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/copertura_e4.json: numstat 5832	0	protocol/e14b/c/copertura_e4.json
```

**C-main-TAG-126** · `protocol/e14b/c/curve_e8bis_punti.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/curve_e8bis_punti.json: numstat 1596	0	protocol/e14b/c/curve_e8bis_punti.json
```

**C-main-TAG-127** · `protocol/e14b/c/e14b_livelli_c.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e14b_livelli_c.json: numstat 358	0	protocol/e14b/c/e14b_livelli_c.json
```

**C-main-TAG-128** · `protocol/e14b/c/e3bis_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e3bis_risultati.json: numstat 207	0	protocol/e14b/c/e3bis_risultati.json
```

**C-main-TAG-129** · `protocol/e14b/c/e4_griglia_test.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e4_griglia_test.json: numstat 80	0	protocol/e14b/c/e4_griglia_test.json
```

**C-main-TAG-130** · `protocol/e14b/c/e4_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e4_risultati.json: numstat 1539	0	protocol/e14b/c/e4_risultati.json
```

**C-main-TAG-131** · `protocol/e14b/c/e4_scelta_gated.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e4_scelta_gated.json: numstat 95	0	protocol/e14b/c/e4_scelta_gated.json
```

**C-main-TAG-132** · `protocol/e14b/c/e5_k_secondaria.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e5_k_secondaria.json: numstat 36	0	protocol/e14b/c/e5_k_secondaria.json
```

**C-main-TAG-133** · `protocol/e14b/c/e5_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e5_risultati.json: numstat 1075	0	protocol/e14b/c/e5_risultati.json
```

**C-main-TAG-134** · `protocol/e14b/c/e5_settimana_vs_A.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e5_settimana_vs_A.json: numstat 149	0	protocol/e14b/c/e5_settimana_vs_A.json
```

**C-main-TAG-135** · `protocol/e14b/c/e6_origini_comuni.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e6_origini_comuni.json: numstat 19	0	protocol/e14b/c/e6_origini_comuni.json
```

**C-main-TAG-136** · `protocol/e14b/c/e6_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e6_risultati.json: numstat 170	0	protocol/e14b/c/e6_risultati.json
```

**C-main-TAG-137** · `protocol/e14b/c/e6_scelta_gated.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e6_scelta_gated.json: numstat 51	0	protocol/e14b/c/e6_scelta_gated.json
```

**C-main-TAG-138** · `protocol/e14b/c/e6a_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e6a_risultati.json: numstat 124	0	protocol/e14b/c/e6a_risultati.json
```

**C-main-TAG-139** · `protocol/e14b/c/e6a_scelta_gated.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e6a_scelta_gated.json: numstat 50	0	protocol/e14b/c/e6a_scelta_gated.json
```

**C-main-TAG-140** · `protocol/e14b/c/e6bis_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e6bis_risultati.json: numstat 63	0	protocol/e14b/c/e6bis_risultati.json
```

**C-main-TAG-141** · `protocol/e14b/c/e7_posthoc.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e7_posthoc.json: numstat 365	0	protocol/e14b/c/e7_posthoc.json
```

**C-main-TAG-142** · `protocol/e14b/c/e7_stadio1.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e7_stadio1.json: numstat 1785	0	protocol/e14b/c/e7_stadio1.json
```

**C-main-TAG-143** · `protocol/e14b/c/e8_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e8_risultati.json: numstat 4923	0	protocol/e14b/c/e8_risultati.json
```

**C-main-TAG-144** · `protocol/e14b/c/e8_soglie.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e8_soglie.json: numstat 353	0	protocol/e14b/c/e8_soglie.json
```

**C-main-TAG-145** · `protocol/e14b/c/e8bis_risultati.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/e8bis_risultati.json: numstat 2416	0	protocol/e14b/c/e8bis_risultati.json
```

**C-main-TAG-146** · `protocol/e14b/c/manifesto.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/manifesto.json: numstat 48	0	protocol/e14b/c/manifesto.json
```

**C-main-TAG-147** · `protocol/e14b/c/predizioni_e2/controllo_e2.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_e2/controllo_e2.json: numstat 5736	0	protocol/e14b/c/predizioni_e2/controllo_e2.json
```

**C-main-TAG-148** · `protocol/e14b/c/predizioni_f0/controllo_f0.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_f0/controllo_f0.json: numstat 1518	0	protocol/e14b/c/predizioni_f0/controllo_f0.json
```

**C-main-TAG-149** · `protocol/e14b/c/predizioni_fase3/controllo_A.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_fase3/controllo_A.json: numstat 1522	0	protocol/e14b/c/predizioni_fase3/controllo_A.json
```

**C-main-TAG-150** · `protocol/e14b/c/predizioni_fase3/controllo_C.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_fase3/controllo_C.json: numstat 1522	0	protocol/e14b/c/predizioni_fase3/controllo_C.json
```

**C-main-TAG-151** · `protocol/e14b/c/predizioni_fase3/controllo_F.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_fase3/controllo_F.json: numstat 1522	0	protocol/e14b/c/predizioni_fase3/controllo_F.json
```

**C-main-TAG-152** · `protocol/e14b/c/predizioni_fase3/controllo_P.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_fase3/controllo_P.json: numstat 1522	0	protocol/e14b/c/predizioni_fase3/controllo_P.json
```

**C-main-TAG-153** · `protocol/e14b/c/predizioni_fase3/controllo_R-mon.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_fase3/controllo_R-mon.json: numstat 1522	0	protocol/e14b/c/predizioni_fase3/controllo_R-mon.json
```

**C-main-TAG-154** · `protocol/e14b/c/predizioni_fase3/controllo_R-orig.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_fase3/controllo_R-orig.json: numstat 1522	0	protocol/e14b/c/predizioni_fase3/controllo_R-orig.json
```

**C-main-TAG-155** · `protocol/e14b/c/predizioni_fase3/controllo_R.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_fase3/controllo_R.json: numstat 1522	0	protocol/e14b/c/predizioni_fase3/controllo_R.json
```

**C-main-TAG-156** · `protocol/e14b/c/predizioni_fase3_672/controllo_R-orig.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/predizioni_fase3_672/controllo_R-orig.json: numstat 1522	0	protocol/e14b/c/predizioni_fase3_672/controllo_R-orig.json
```

**C-main-TAG-157** · `protocol/e14b/c/riselezione_rmon_test.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/riselezione_rmon_test.json: numstat 79	0	protocol/e14b/c/riselezione_rmon_test.json
```

**C-main-TAG-158** · `protocol/e14b/c/veterani_e3.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/c/veterani_e3.json: numstat 140	0	protocol/e14b/c/veterani_e3.json
```

**C-main-TAG-159** · `protocol/e14b/congelata/e14b_livelli_congelata.json` · paper1-freeze-20261012e..paper1-freeze-20261015f

```
protocol/e14b/congelata/e14b_livelli_congelata.json: numstat 358	0	protocol/e14b/congelata/e14b_livelli_congelata.json
```

**C-main-TAG-160** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261015f..paper1-freeze-20261015g

```
analysis/rigenerazione/CONFRONTO.md: numstat 1	1	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-161** · `analysis/main.py` · paper1-freeze-20261015g..paper1-freeze-20261015h

```
analysis/main.py: numstat 3	1	analysis/main.py
```

**C-main-TAG-162** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261015g..paper1-freeze-20261015h

```
analysis/rigenerazione/CONFRONTO.md: numstat 7	3	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-163** · `evoluzione/analisi/figura_rete.py` · paper1-freeze-20261015g..paper1-freeze-20261015h

```
evoluzione/analisi/figura_rete.py: numstat 239	0	evoluzione/analisi/figura_rete.py
```

**C-main-TAG-164** · `CONGELAMENTO_E15.md` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
CONGELAMENTO_E15.md: numstat 420	0	CONGELAMENTO_E15.md
```

**C-main-TAG-165** · `CONGELAMENTO_E16.md` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
CONGELAMENTO_E16.md: numstat 224	0	CONGELAMENTO_E16.md
```

**C-main-TAG-166** · `CONGELAMENTO_E17.md` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
CONGELAMENTO_E17.md: numstat 88	0	CONGELAMENTO_E17.md
```

**C-main-TAG-167** · `analysis/main.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
analysis/main.py: numstat 17	1	analysis/main.py
```

**C-main-TAG-168** · `analysis/tabelle_paper1.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
analysis/tabelle_paper1.py: numstat 31	20	analysis/tabelle_paper1.py
```

**C-main-TAG-169** · `analysis/tabelle_suppl.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
analysis/tabelle_suppl.py: numstat 195	10	analysis/tabelle_suppl.py
```

**C-main-TAG-170** · `evoluzione/analisi/analizza_e17.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/analisi/analizza_e17.py: numstat 187	0	evoluzione/analisi/analizza_e17.py
```

**C-main-TAG-171** · `evoluzione/analisi/analizza_e4.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/analisi/analizza_e4.py: numstat 18	13	evoluzione/analisi/analizza_e4.py
```

**C-main-TAG-172** · `evoluzione/analisi/figura2_51.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/analisi/figura2_51.py: numstat 6	0	evoluzione/analisi/figura2_51.py
```

**C-main-TAG-173** · `evoluzione/analisi/figura_cronologia.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/analisi/figura_cronologia.py: numstat 121	0	evoluzione/analisi/figura_cronologia.py
```

**C-main-TAG-174** · `evoluzione/analisi/scheda_fatti.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/analisi/scheda_fatti.py: numstat 306	0	evoluzione/analisi/scheda_fatti.py
```

**C-main-TAG-175** · `evoluzione/componente/bracci.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/componente/bracci.py: numstat 6	0	evoluzione/componente/bracci.py
```

**C-main-TAG-176** · `evoluzione/componente/episodio.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/componente/episodio.py: numstat 6	2	evoluzione/componente/episodio.py
```

**C-main-TAG-177** · `evoluzione/componente/valutazione.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/componente/valutazione.py: numstat 7	2	evoluzione/componente/valutazione.py
```

**C-main-TAG-178** · `evoluzione/esperimenti/addestramento.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/esperimenti/addestramento.py: numstat 3	1	evoluzione/esperimenti/addestramento.py
```

**C-main-TAG-179** · `evoluzione/esperimenti/collauda_bracci.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/esperimenti/collauda_bracci.py: numstat 13	0	evoluzione/esperimenti/collauda_bracci.py
```

**C-main-TAG-180** · `evoluzione/esperimenti/collauda_statica_espansiva.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/esperimenti/collauda_statica_espansiva.py: numstat 181	0	evoluzione/esperimenti/collauda_statica_espansiva.py
```

**C-main-TAG-181** · `evoluzione/esperimenti/esegui_e15.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/esperimenti/esegui_e15.py: numstat 894	0	evoluzione/esperimenti/esegui_e15.py
```

**C-main-TAG-182** · `evoluzione/esperimenti/esegui_e16.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/esperimenti/esegui_e16.py: numstat 369	0	evoluzione/esperimenti/esegui_e16.py
```

**C-main-TAG-183** · `evoluzione/esperimenti/inserimento.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/esperimenti/inserimento.py: numstat 91	10	evoluzione/esperimenti/inserimento.py
```

**C-main-TAG-184** · `evoluzione/esperimenti/pilota_tempi_e15.py` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
evoluzione/esperimenti/pilota_tempi_e15.py: numstat 90	0	evoluzione/esperimenti/pilota_tempi_e15.py
```

**C-main-TAG-185** · `protocol/E15.md` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/E15.md: numstat 31	0	protocol/E15.md
```

**C-main-TAG-186** · `protocol/E16.md` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/E16.md: numstat 11	0	protocol/E16.md
```

**C-main-TAG-187** · `protocol/E17.md` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/E17.md: numstat 13	0	protocol/E17.md
```

**C-main-TAG-188** · `protocol/e15/e15_risultati.json` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/e15_risultati.json: numstat 2189	0	protocol/e15/e15_risultati.json
```

**C-main-TAG-189** · `protocol/e15/tempi/A/A_Londra_p0_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p0_s201.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p0_s201.json.fatto
```

**C-main-TAG-190** · `protocol/e15/tempi/A/A_Londra_p0_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p0_s202.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p0_s202.json.fatto
```

**C-main-TAG-191** · `protocol/e15/tempi/A/A_Londra_p0_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p0_s203.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p0_s203.json.fatto
```

**C-main-TAG-192** · `protocol/e15/tempi/A/A_Londra_p0_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p0_s204.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p0_s204.json.fatto
```

**C-main-TAG-193** · `protocol/e15/tempi/A/A_Londra_p0_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p0_s205.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p0_s205.json.fatto
```

**C-main-TAG-194** · `protocol/e15/tempi/A/A_Londra_p0_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p0_s206.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p0_s206.json.fatto
```

**C-main-TAG-195** · `protocol/e15/tempi/A/A_Londra_p1_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p1_s201.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p1_s201.json.fatto
```

**C-main-TAG-196** · `protocol/e15/tempi/A/A_Londra_p1_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p1_s202.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p1_s202.json.fatto
```

**C-main-TAG-197** · `protocol/e15/tempi/A/A_Londra_p1_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p1_s203.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p1_s203.json.fatto
```

**C-main-TAG-198** · `protocol/e15/tempi/A/A_Londra_p1_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p1_s204.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p1_s204.json.fatto
```

**C-main-TAG-199** · `protocol/e15/tempi/A/A_Londra_p1_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p1_s205.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p1_s205.json.fatto
```

**C-main-TAG-200** · `protocol/e15/tempi/A/A_Londra_p1_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p1_s206.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p1_s206.json.fatto
```

**C-main-TAG-201** · `protocol/e15/tempi/A/A_Londra_p2_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p2_s201.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p2_s201.json.fatto
```

**C-main-TAG-202** · `protocol/e15/tempi/A/A_Londra_p2_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p2_s202.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p2_s202.json.fatto
```

**C-main-TAG-203** · `protocol/e15/tempi/A/A_Londra_p2_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p2_s203.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p2_s203.json.fatto
```

**C-main-TAG-204** · `protocol/e15/tempi/A/A_Londra_p2_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p2_s204.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p2_s204.json.fatto
```

**C-main-TAG-205** · `protocol/e15/tempi/A/A_Londra_p2_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p2_s205.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p2_s205.json.fatto
```

**C-main-TAG-206** · `protocol/e15/tempi/A/A_Londra_p2_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Londra_p2_s206.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Londra_p2_s206.json.fatto
```

**C-main-TAG-207** · `protocol/e15/tempi/A/A_Madrid_p0_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p0_s201.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p0_s201.json.fatto
```

**C-main-TAG-208** · `protocol/e15/tempi/A/A_Madrid_p0_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p0_s202.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p0_s202.json.fatto
```

**C-main-TAG-209** · `protocol/e15/tempi/A/A_Madrid_p0_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p0_s203.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p0_s203.json.fatto
```

**C-main-TAG-210** · `protocol/e15/tempi/A/A_Madrid_p0_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p0_s204.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p0_s204.json.fatto
```

**C-main-TAG-211** · `protocol/e15/tempi/A/A_Madrid_p0_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p0_s205.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p0_s205.json.fatto
```

**C-main-TAG-212** · `protocol/e15/tempi/A/A_Madrid_p0_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p0_s206.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p0_s206.json.fatto
```

**C-main-TAG-213** · `protocol/e15/tempi/A/A_Madrid_p1_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p1_s201.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p1_s201.json.fatto
```

**C-main-TAG-214** · `protocol/e15/tempi/A/A_Madrid_p1_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p1_s202.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p1_s202.json.fatto
```

**C-main-TAG-215** · `protocol/e15/tempi/A/A_Madrid_p1_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p1_s203.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p1_s203.json.fatto
```

**C-main-TAG-216** · `protocol/e15/tempi/A/A_Madrid_p1_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p1_s204.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p1_s204.json.fatto
```

**C-main-TAG-217** · `protocol/e15/tempi/A/A_Madrid_p1_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p1_s205.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p1_s205.json.fatto
```

**C-main-TAG-218** · `protocol/e15/tempi/A/A_Madrid_p1_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p1_s206.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p1_s206.json.fatto
```

**C-main-TAG-219** · `protocol/e15/tempi/A/A_Madrid_p2_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p2_s201.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p2_s201.json.fatto
```

**C-main-TAG-220** · `protocol/e15/tempi/A/A_Madrid_p2_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p2_s202.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p2_s202.json.fatto
```

**C-main-TAG-221** · `protocol/e15/tempi/A/A_Madrid_p2_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p2_s203.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p2_s203.json.fatto
```

**C-main-TAG-222** · `protocol/e15/tempi/A/A_Madrid_p2_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p2_s204.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p2_s204.json.fatto
```

**C-main-TAG-223** · `protocol/e15/tempi/A/A_Madrid_p2_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p2_s205.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p2_s205.json.fatto
```

**C-main-TAG-224** · `protocol/e15/tempi/A/A_Madrid_p2_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Madrid_p2_s206.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Madrid_p2_s206.json.fatto
```

**C-main-TAG-225** · `protocol/e15/tempi/A/A_Melbourne_p0_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p0_s201.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p0_s201.json.fatto
```

**C-main-TAG-226** · `protocol/e15/tempi/A/A_Melbourne_p0_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p0_s202.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p0_s202.json.fatto
```

**C-main-TAG-227** · `protocol/e15/tempi/A/A_Melbourne_p0_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p0_s203.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p0_s203.json.fatto
```

**C-main-TAG-228** · `protocol/e15/tempi/A/A_Melbourne_p0_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p0_s204.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p0_s204.json.fatto
```

**C-main-TAG-229** · `protocol/e15/tempi/A/A_Melbourne_p0_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p0_s205.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p0_s205.json.fatto
```

**C-main-TAG-230** · `protocol/e15/tempi/A/A_Melbourne_p0_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p0_s206.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p0_s206.json.fatto
```

**C-main-TAG-231** · `protocol/e15/tempi/A/A_Melbourne_p1_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p1_s201.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p1_s201.json.fatto
```

**C-main-TAG-232** · `protocol/e15/tempi/A/A_Melbourne_p1_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p1_s202.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p1_s202.json.fatto
```

**C-main-TAG-233** · `protocol/e15/tempi/A/A_Melbourne_p1_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p1_s203.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p1_s203.json.fatto
```

**C-main-TAG-234** · `protocol/e15/tempi/A/A_Melbourne_p1_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p1_s204.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p1_s204.json.fatto
```

**C-main-TAG-235** · `protocol/e15/tempi/A/A_Melbourne_p1_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p1_s205.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p1_s205.json.fatto
```

**C-main-TAG-236** · `protocol/e15/tempi/A/A_Melbourne_p1_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p1_s206.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p1_s206.json.fatto
```

**C-main-TAG-237** · `protocol/e15/tempi/A/A_Melbourne_p2_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p2_s201.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p2_s201.json.fatto
```

**C-main-TAG-238** · `protocol/e15/tempi/A/A_Melbourne_p2_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p2_s202.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p2_s202.json.fatto
```

**C-main-TAG-239** · `protocol/e15/tempi/A/A_Melbourne_p2_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p2_s203.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p2_s203.json.fatto
```

**C-main-TAG-240** · `protocol/e15/tempi/A/A_Melbourne_p2_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p2_s204.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p2_s204.json.fatto
```

**C-main-TAG-241** · `protocol/e15/tempi/A/A_Melbourne_p2_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p2_s205.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p2_s205.json.fatto
```

**C-main-TAG-242** · `protocol/e15/tempi/A/A_Melbourne_p2_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/A/A_Melbourne_p2_s206.json.fatto: numstat 1	0	protocol/e15/tempi/A/A_Melbourne_p2_s206.json.fatto
```

**C-main-TAG-243** · `protocol/e15/tempi/C/C_Londra_p0_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p0_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p0_s201.json.fatto
```

**C-main-TAG-244** · `protocol/e15/tempi/C/C_Londra_p0_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p0_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p0_s202.json.fatto
```

**C-main-TAG-245** · `protocol/e15/tempi/C/C_Londra_p0_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p0_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p0_s203.json.fatto
```

**C-main-TAG-246** · `protocol/e15/tempi/C/C_Londra_p0_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p0_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p0_s204.json.fatto
```

**C-main-TAG-247** · `protocol/e15/tempi/C/C_Londra_p0_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p0_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p0_s205.json.fatto
```

**C-main-TAG-248** · `protocol/e15/tempi/C/C_Londra_p0_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p0_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p0_s206.json.fatto
```

**C-main-TAG-249** · `protocol/e15/tempi/C/C_Londra_p1_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p1_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p1_s201.json.fatto
```

**C-main-TAG-250** · `protocol/e15/tempi/C/C_Londra_p1_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p1_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p1_s202.json.fatto
```

**C-main-TAG-251** · `protocol/e15/tempi/C/C_Londra_p1_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p1_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p1_s203.json.fatto
```

**C-main-TAG-252** · `protocol/e15/tempi/C/C_Londra_p1_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p1_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p1_s204.json.fatto
```

**C-main-TAG-253** · `protocol/e15/tempi/C/C_Londra_p1_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p1_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p1_s205.json.fatto
```

**C-main-TAG-254** · `protocol/e15/tempi/C/C_Londra_p1_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p1_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p1_s206.json.fatto
```

**C-main-TAG-255** · `protocol/e15/tempi/C/C_Londra_p2_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p2_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p2_s201.json.fatto
```

**C-main-TAG-256** · `protocol/e15/tempi/C/C_Londra_p2_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p2_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p2_s202.json.fatto
```

**C-main-TAG-257** · `protocol/e15/tempi/C/C_Londra_p2_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p2_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p2_s203.json.fatto
```

**C-main-TAG-258** · `protocol/e15/tempi/C/C_Londra_p2_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p2_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p2_s204.json.fatto
```

**C-main-TAG-259** · `protocol/e15/tempi/C/C_Londra_p2_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p2_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p2_s205.json.fatto
```

**C-main-TAG-260** · `protocol/e15/tempi/C/C_Londra_p2_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Londra_p2_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Londra_p2_s206.json.fatto
```

**C-main-TAG-261** · `protocol/e15/tempi/C/C_Madrid_p0_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p0_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p0_s201.json.fatto
```

**C-main-TAG-262** · `protocol/e15/tempi/C/C_Madrid_p0_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p0_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p0_s202.json.fatto
```

**C-main-TAG-263** · `protocol/e15/tempi/C/C_Madrid_p0_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p0_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p0_s203.json.fatto
```

**C-main-TAG-264** · `protocol/e15/tempi/C/C_Madrid_p0_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p0_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p0_s204.json.fatto
```

**C-main-TAG-265** · `protocol/e15/tempi/C/C_Madrid_p0_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p0_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p0_s205.json.fatto
```

**C-main-TAG-266** · `protocol/e15/tempi/C/C_Madrid_p0_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p0_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p0_s206.json.fatto
```

**C-main-TAG-267** · `protocol/e15/tempi/C/C_Madrid_p1_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p1_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p1_s201.json.fatto
```

**C-main-TAG-268** · `protocol/e15/tempi/C/C_Madrid_p1_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p1_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p1_s202.json.fatto
```

**C-main-TAG-269** · `protocol/e15/tempi/C/C_Madrid_p1_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p1_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p1_s203.json.fatto
```

**C-main-TAG-270** · `protocol/e15/tempi/C/C_Madrid_p1_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p1_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p1_s204.json.fatto
```

**C-main-TAG-271** · `protocol/e15/tempi/C/C_Madrid_p1_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p1_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p1_s205.json.fatto
```

**C-main-TAG-272** · `protocol/e15/tempi/C/C_Madrid_p1_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p1_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p1_s206.json.fatto
```

**C-main-TAG-273** · `protocol/e15/tempi/C/C_Madrid_p2_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p2_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p2_s201.json.fatto
```

**C-main-TAG-274** · `protocol/e15/tempi/C/C_Madrid_p2_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p2_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p2_s202.json.fatto
```

**C-main-TAG-275** · `protocol/e15/tempi/C/C_Madrid_p2_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p2_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p2_s203.json.fatto
```

**C-main-TAG-276** · `protocol/e15/tempi/C/C_Madrid_p2_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p2_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p2_s204.json.fatto
```

**C-main-TAG-277** · `protocol/e15/tempi/C/C_Madrid_p2_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p2_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p2_s205.json.fatto
```

**C-main-TAG-278** · `protocol/e15/tempi/C/C_Madrid_p2_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Madrid_p2_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Madrid_p2_s206.json.fatto
```

**C-main-TAG-279** · `protocol/e15/tempi/C/C_Melbourne_p0_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p0_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p0_s201.json.fatto
```

**C-main-TAG-280** · `protocol/e15/tempi/C/C_Melbourne_p0_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p0_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p0_s202.json.fatto
```

**C-main-TAG-281** · `protocol/e15/tempi/C/C_Melbourne_p0_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p0_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p0_s203.json.fatto
```

**C-main-TAG-282** · `protocol/e15/tempi/C/C_Melbourne_p0_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p0_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p0_s204.json.fatto
```

**C-main-TAG-283** · `protocol/e15/tempi/C/C_Melbourne_p0_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p0_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p0_s205.json.fatto
```

**C-main-TAG-284** · `protocol/e15/tempi/C/C_Melbourne_p0_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p0_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p0_s206.json.fatto
```

**C-main-TAG-285** · `protocol/e15/tempi/C/C_Melbourne_p1_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p1_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p1_s201.json.fatto
```

**C-main-TAG-286** · `protocol/e15/tempi/C/C_Melbourne_p1_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p1_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p1_s202.json.fatto
```

**C-main-TAG-287** · `protocol/e15/tempi/C/C_Melbourne_p1_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p1_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p1_s203.json.fatto
```

**C-main-TAG-288** · `protocol/e15/tempi/C/C_Melbourne_p1_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p1_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p1_s204.json.fatto
```

**C-main-TAG-289** · `protocol/e15/tempi/C/C_Melbourne_p1_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p1_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p1_s205.json.fatto
```

**C-main-TAG-290** · `protocol/e15/tempi/C/C_Melbourne_p1_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p1_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p1_s206.json.fatto
```

**C-main-TAG-291** · `protocol/e15/tempi/C/C_Melbourne_p2_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p2_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p2_s201.json.fatto
```

**C-main-TAG-292** · `protocol/e15/tempi/C/C_Melbourne_p2_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p2_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p2_s202.json.fatto
```

**C-main-TAG-293** · `protocol/e15/tempi/C/C_Melbourne_p2_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p2_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p2_s203.json.fatto
```

**C-main-TAG-294** · `protocol/e15/tempi/C/C_Melbourne_p2_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p2_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p2_s204.json.fatto
```

**C-main-TAG-295** · `protocol/e15/tempi/C/C_Melbourne_p2_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p2_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p2_s205.json.fatto
```

**C-main-TAG-296** · `protocol/e15/tempi/C/C_Melbourne_p2_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C/C_Melbourne_p2_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C/C_Melbourne_p2_s206.json.fatto
```

**C-main-TAG-297** · `protocol/e15/tempi/C_A/C_A_Londra_p0_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p0_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p0_s201.json.fatto
```

**C-main-TAG-298** · `protocol/e15/tempi/C_A/C_A_Londra_p0_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p0_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p0_s202.json.fatto
```

**C-main-TAG-299** · `protocol/e15/tempi/C_A/C_A_Londra_p0_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p0_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p0_s203.json.fatto
```

**C-main-TAG-300** · `protocol/e15/tempi/C_A/C_A_Londra_p0_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p0_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p0_s204.json.fatto
```

**C-main-TAG-301** · `protocol/e15/tempi/C_A/C_A_Londra_p0_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p0_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p0_s205.json.fatto
```

**C-main-TAG-302** · `protocol/e15/tempi/C_A/C_A_Londra_p0_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p0_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p0_s206.json.fatto
```

**C-main-TAG-303** · `protocol/e15/tempi/C_A/C_A_Londra_p1_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p1_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p1_s201.json.fatto
```

**C-main-TAG-304** · `protocol/e15/tempi/C_A/C_A_Londra_p1_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p1_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p1_s202.json.fatto
```

**C-main-TAG-305** · `protocol/e15/tempi/C_A/C_A_Londra_p1_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p1_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p1_s203.json.fatto
```

**C-main-TAG-306** · `protocol/e15/tempi/C_A/C_A_Londra_p1_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p1_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p1_s204.json.fatto
```

**C-main-TAG-307** · `protocol/e15/tempi/C_A/C_A_Londra_p1_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p1_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p1_s205.json.fatto
```

**C-main-TAG-308** · `protocol/e15/tempi/C_A/C_A_Londra_p1_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p1_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p1_s206.json.fatto
```

**C-main-TAG-309** · `protocol/e15/tempi/C_A/C_A_Londra_p2_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p2_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p2_s201.json.fatto
```

**C-main-TAG-310** · `protocol/e15/tempi/C_A/C_A_Londra_p2_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p2_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p2_s202.json.fatto
```

**C-main-TAG-311** · `protocol/e15/tempi/C_A/C_A_Londra_p2_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p2_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p2_s203.json.fatto
```

**C-main-TAG-312** · `protocol/e15/tempi/C_A/C_A_Londra_p2_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p2_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p2_s204.json.fatto
```

**C-main-TAG-313** · `protocol/e15/tempi/C_A/C_A_Londra_p2_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p2_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p2_s205.json.fatto
```

**C-main-TAG-314** · `protocol/e15/tempi/C_A/C_A_Londra_p2_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Londra_p2_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Londra_p2_s206.json.fatto
```

**C-main-TAG-315** · `protocol/e15/tempi/C_A/C_A_Madrid_p0_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p0_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p0_s201.json.fatto
```

**C-main-TAG-316** · `protocol/e15/tempi/C_A/C_A_Madrid_p0_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p0_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p0_s202.json.fatto
```

**C-main-TAG-317** · `protocol/e15/tempi/C_A/C_A_Madrid_p0_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p0_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p0_s203.json.fatto
```

**C-main-TAG-318** · `protocol/e15/tempi/C_A/C_A_Madrid_p0_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p0_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p0_s204.json.fatto
```

**C-main-TAG-319** · `protocol/e15/tempi/C_A/C_A_Madrid_p0_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p0_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p0_s205.json.fatto
```

**C-main-TAG-320** · `protocol/e15/tempi/C_A/C_A_Madrid_p0_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p0_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p0_s206.json.fatto
```

**C-main-TAG-321** · `protocol/e15/tempi/C_A/C_A_Madrid_p1_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p1_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p1_s201.json.fatto
```

**C-main-TAG-322** · `protocol/e15/tempi/C_A/C_A_Madrid_p1_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p1_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p1_s202.json.fatto
```

**C-main-TAG-323** · `protocol/e15/tempi/C_A/C_A_Madrid_p1_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p1_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p1_s203.json.fatto
```

**C-main-TAG-324** · `protocol/e15/tempi/C_A/C_A_Madrid_p1_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p1_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p1_s204.json.fatto
```

**C-main-TAG-325** · `protocol/e15/tempi/C_A/C_A_Madrid_p1_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p1_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p1_s205.json.fatto
```

**C-main-TAG-326** · `protocol/e15/tempi/C_A/C_A_Madrid_p1_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p1_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p1_s206.json.fatto
```

**C-main-TAG-327** · `protocol/e15/tempi/C_A/C_A_Madrid_p2_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p2_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p2_s201.json.fatto
```

**C-main-TAG-328** · `protocol/e15/tempi/C_A/C_A_Madrid_p2_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p2_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p2_s202.json.fatto
```

**C-main-TAG-329** · `protocol/e15/tempi/C_A/C_A_Madrid_p2_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p2_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p2_s203.json.fatto
```

**C-main-TAG-330** · `protocol/e15/tempi/C_A/C_A_Madrid_p2_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p2_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p2_s204.json.fatto
```

**C-main-TAG-331** · `protocol/e15/tempi/C_A/C_A_Madrid_p2_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p2_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p2_s205.json.fatto
```

**C-main-TAG-332** · `protocol/e15/tempi/C_A/C_A_Madrid_p2_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Madrid_p2_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Madrid_p2_s206.json.fatto
```

**C-main-TAG-333** · `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p0_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p0_s201.json.fatto
```

**C-main-TAG-334** · `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p0_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p0_s202.json.fatto
```

**C-main-TAG-335** · `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p0_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p0_s203.json.fatto
```

**C-main-TAG-336** · `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p0_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p0_s204.json.fatto
```

**C-main-TAG-337** · `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p0_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p0_s205.json.fatto
```

**C-main-TAG-338** · `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p0_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p0_s206.json.fatto
```

**C-main-TAG-339** · `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p1_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p1_s201.json.fatto
```

**C-main-TAG-340** · `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p1_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p1_s202.json.fatto
```

**C-main-TAG-341** · `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p1_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p1_s203.json.fatto
```

**C-main-TAG-342** · `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p1_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p1_s204.json.fatto
```

**C-main-TAG-343** · `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p1_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p1_s205.json.fatto
```

**C-main-TAG-344** · `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p1_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p1_s206.json.fatto
```

**C-main-TAG-345** · `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s201.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p2_s201.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p2_s201.json.fatto
```

**C-main-TAG-346** · `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s202.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p2_s202.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p2_s202.json.fatto
```

**C-main-TAG-347** · `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s203.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p2_s203.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p2_s203.json.fatto
```

**C-main-TAG-348** · `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s204.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p2_s204.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p2_s204.json.fatto
```

**C-main-TAG-349** · `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s205.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p2_s205.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p2_s205.json.fatto
```

**C-main-TAG-350** · `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s206.json.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/C_A/C_A_Melbourne_p2_s206.json.fatto: numstat 1	0	protocol/e15/tempi/C_A/C_A_Melbourne_p2_s206.json.fatto
```

**C-main-TAG-351** · `protocol/e15/tempi/E/ck_E_Londra_p0_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p0_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p0_s1150248972.pt.fatto
```

**C-main-TAG-352** · `protocol/e15/tempi/E/ck_E_Londra_p0_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p0_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p0_s1157715887.pt.fatto
```

**C-main-TAG-353** · `protocol/e15/tempi/E/ck_E_Londra_p0_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p0_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p0_s1592395901.pt.fatto
```

**C-main-TAG-354** · `protocol/e15/tempi/E/ck_E_Londra_p0_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p0_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p0_s399595374.pt.fatto
```

**C-main-TAG-355** · `protocol/e15/tempi/E/ck_E_Londra_p0_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p0_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p0_s643310434.pt.fatto
```

**C-main-TAG-356** · `protocol/e15/tempi/E/ck_E_Londra_p0_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p0_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p0_s682647013.pt.fatto
```

**C-main-TAG-357** · `protocol/e15/tempi/E/ck_E_Londra_p1_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p1_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p1_s1150248972.pt.fatto
```

**C-main-TAG-358** · `protocol/e15/tempi/E/ck_E_Londra_p1_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p1_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p1_s1157715887.pt.fatto
```

**C-main-TAG-359** · `protocol/e15/tempi/E/ck_E_Londra_p1_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p1_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p1_s1592395901.pt.fatto
```

**C-main-TAG-360** · `protocol/e15/tempi/E/ck_E_Londra_p1_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p1_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p1_s399595374.pt.fatto
```

**C-main-TAG-361** · `protocol/e15/tempi/E/ck_E_Londra_p1_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p1_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p1_s643310434.pt.fatto
```

**C-main-TAG-362** · `protocol/e15/tempi/E/ck_E_Londra_p1_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p1_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p1_s682647013.pt.fatto
```

**C-main-TAG-363** · `protocol/e15/tempi/E/ck_E_Londra_p2_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p2_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p2_s1150248972.pt.fatto
```

**C-main-TAG-364** · `protocol/e15/tempi/E/ck_E_Londra_p2_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p2_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p2_s1157715887.pt.fatto
```

**C-main-TAG-365** · `protocol/e15/tempi/E/ck_E_Londra_p2_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p2_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p2_s1592395901.pt.fatto
```

**C-main-TAG-366** · `protocol/e15/tempi/E/ck_E_Londra_p2_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p2_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p2_s399595374.pt.fatto
```

**C-main-TAG-367** · `protocol/e15/tempi/E/ck_E_Londra_p2_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p2_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p2_s643310434.pt.fatto
```

**C-main-TAG-368** · `protocol/e15/tempi/E/ck_E_Londra_p2_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Londra_p2_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Londra_p2_s682647013.pt.fatto
```

**C-main-TAG-369** · `protocol/e15/tempi/E/ck_E_Madrid_p0_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p0_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p0_s1150248972.pt.fatto
```

**C-main-TAG-370** · `protocol/e15/tempi/E/ck_E_Madrid_p0_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p0_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p0_s1157715887.pt.fatto
```

**C-main-TAG-371** · `protocol/e15/tempi/E/ck_E_Madrid_p0_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p0_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p0_s1592395901.pt.fatto
```

**C-main-TAG-372** · `protocol/e15/tempi/E/ck_E_Madrid_p0_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p0_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p0_s399595374.pt.fatto
```

**C-main-TAG-373** · `protocol/e15/tempi/E/ck_E_Madrid_p0_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p0_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p0_s643310434.pt.fatto
```

**C-main-TAG-374** · `protocol/e15/tempi/E/ck_E_Madrid_p0_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p0_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p0_s682647013.pt.fatto
```

**C-main-TAG-375** · `protocol/e15/tempi/E/ck_E_Madrid_p1_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p1_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p1_s1150248972.pt.fatto
```

**C-main-TAG-376** · `protocol/e15/tempi/E/ck_E_Madrid_p1_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p1_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p1_s1157715887.pt.fatto
```

**C-main-TAG-377** · `protocol/e15/tempi/E/ck_E_Madrid_p1_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p1_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p1_s1592395901.pt.fatto
```

**C-main-TAG-378** · `protocol/e15/tempi/E/ck_E_Madrid_p1_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p1_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p1_s399595374.pt.fatto
```

**C-main-TAG-379** · `protocol/e15/tempi/E/ck_E_Madrid_p1_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p1_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p1_s643310434.pt.fatto
```

**C-main-TAG-380** · `protocol/e15/tempi/E/ck_E_Madrid_p1_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p1_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p1_s682647013.pt.fatto
```

**C-main-TAG-381** · `protocol/e15/tempi/E/ck_E_Madrid_p2_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p2_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p2_s1150248972.pt.fatto
```

**C-main-TAG-382** · `protocol/e15/tempi/E/ck_E_Madrid_p2_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p2_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p2_s1157715887.pt.fatto
```

**C-main-TAG-383** · `protocol/e15/tempi/E/ck_E_Madrid_p2_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p2_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p2_s1592395901.pt.fatto
```

**C-main-TAG-384** · `protocol/e15/tempi/E/ck_E_Madrid_p2_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p2_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p2_s399595374.pt.fatto
```

**C-main-TAG-385** · `protocol/e15/tempi/E/ck_E_Madrid_p2_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p2_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p2_s643310434.pt.fatto
```

**C-main-TAG-386** · `protocol/e15/tempi/E/ck_E_Madrid_p2_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Madrid_p2_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Madrid_p2_s682647013.pt.fatto
```

**C-main-TAG-387** · `protocol/e15/tempi/E/ck_E_Melbourne_p0_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p0_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p0_s1150248972.pt.fatto
```

**C-main-TAG-388** · `protocol/e15/tempi/E/ck_E_Melbourne_p0_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p0_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p0_s1157715887.pt.fatto
```

**C-main-TAG-389** · `protocol/e15/tempi/E/ck_E_Melbourne_p0_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p0_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p0_s1592395901.pt.fatto
```

**C-main-TAG-390** · `protocol/e15/tempi/E/ck_E_Melbourne_p0_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p0_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p0_s399595374.pt.fatto
```

**C-main-TAG-391** · `protocol/e15/tempi/E/ck_E_Melbourne_p0_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p0_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p0_s643310434.pt.fatto
```

**C-main-TAG-392** · `protocol/e15/tempi/E/ck_E_Melbourne_p0_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p0_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p0_s682647013.pt.fatto
```

**C-main-TAG-393** · `protocol/e15/tempi/E/ck_E_Melbourne_p1_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p1_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p1_s1150248972.pt.fatto
```

**C-main-TAG-394** · `protocol/e15/tempi/E/ck_E_Melbourne_p1_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p1_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p1_s1157715887.pt.fatto
```

**C-main-TAG-395** · `protocol/e15/tempi/E/ck_E_Melbourne_p1_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p1_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p1_s1592395901.pt.fatto
```

**C-main-TAG-396** · `protocol/e15/tempi/E/ck_E_Melbourne_p1_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p1_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p1_s399595374.pt.fatto
```

**C-main-TAG-397** · `protocol/e15/tempi/E/ck_E_Melbourne_p1_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p1_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p1_s643310434.pt.fatto
```

**C-main-TAG-398** · `protocol/e15/tempi/E/ck_E_Melbourne_p1_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p1_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p1_s682647013.pt.fatto
```

**C-main-TAG-399** · `protocol/e15/tempi/E/ck_E_Melbourne_p2_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p2_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p2_s1150248972.pt.fatto
```

**C-main-TAG-400** · `protocol/e15/tempi/E/ck_E_Melbourne_p2_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p2_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p2_s1157715887.pt.fatto
```

**C-main-TAG-401** · `protocol/e15/tempi/E/ck_E_Melbourne_p2_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p2_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p2_s1592395901.pt.fatto
```

**C-main-TAG-402** · `protocol/e15/tempi/E/ck_E_Melbourne_p2_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p2_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p2_s399595374.pt.fatto
```

**C-main-TAG-403** · `protocol/e15/tempi/E/ck_E_Melbourne_p2_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p2_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p2_s643310434.pt.fatto
```

**C-main-TAG-404** · `protocol/e15/tempi/E/ck_E_Melbourne_p2_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E/ck_E_Melbourne_p2_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E/ck_E_Melbourne_p2_s682647013.pt.fatto
```

**C-main-TAG-405** · `protocol/e15/tempi/E1/ck_E1_Londra_p0_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p0_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p0_s1150248972.pt.fatto
```

**C-main-TAG-406** · `protocol/e15/tempi/E1/ck_E1_Londra_p0_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p0_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p0_s1157715887.pt.fatto
```

**C-main-TAG-407** · `protocol/e15/tempi/E1/ck_E1_Londra_p0_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p0_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p0_s1592395901.pt.fatto
```

**C-main-TAG-408** · `protocol/e15/tempi/E1/ck_E1_Londra_p0_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p0_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p0_s399595374.pt.fatto
```

**C-main-TAG-409** · `protocol/e15/tempi/E1/ck_E1_Londra_p0_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p0_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p0_s643310434.pt.fatto
```

**C-main-TAG-410** · `protocol/e15/tempi/E1/ck_E1_Londra_p0_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p0_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p0_s682647013.pt.fatto
```

**C-main-TAG-411** · `protocol/e15/tempi/E1/ck_E1_Londra_p1_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p1_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p1_s1150248972.pt.fatto
```

**C-main-TAG-412** · `protocol/e15/tempi/E1/ck_E1_Londra_p1_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p1_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p1_s1157715887.pt.fatto
```

**C-main-TAG-413** · `protocol/e15/tempi/E1/ck_E1_Londra_p1_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p1_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p1_s1592395901.pt.fatto
```

**C-main-TAG-414** · `protocol/e15/tempi/E1/ck_E1_Londra_p1_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p1_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p1_s399595374.pt.fatto
```

**C-main-TAG-415** · `protocol/e15/tempi/E1/ck_E1_Londra_p1_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p1_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p1_s643310434.pt.fatto
```

**C-main-TAG-416** · `protocol/e15/tempi/E1/ck_E1_Londra_p1_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p1_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p1_s682647013.pt.fatto
```

**C-main-TAG-417** · `protocol/e15/tempi/E1/ck_E1_Londra_p2_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p2_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p2_s1150248972.pt.fatto
```

**C-main-TAG-418** · `protocol/e15/tempi/E1/ck_E1_Londra_p2_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p2_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p2_s1157715887.pt.fatto
```

**C-main-TAG-419** · `protocol/e15/tempi/E1/ck_E1_Londra_p2_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p2_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p2_s1592395901.pt.fatto
```

**C-main-TAG-420** · `protocol/e15/tempi/E1/ck_E1_Londra_p2_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p2_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p2_s399595374.pt.fatto
```

**C-main-TAG-421** · `protocol/e15/tempi/E1/ck_E1_Londra_p2_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p2_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p2_s643310434.pt.fatto
```

**C-main-TAG-422** · `protocol/e15/tempi/E1/ck_E1_Londra_p2_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Londra_p2_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Londra_p2_s682647013.pt.fatto
```

**C-main-TAG-423** · `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1150248972.pt.fatto
```

**C-main-TAG-424** · `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1157715887.pt.fatto
```

**C-main-TAG-425** · `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1592395901.pt.fatto
```

**C-main-TAG-426** · `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p0_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p0_s399595374.pt.fatto
```

**C-main-TAG-427** · `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p0_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p0_s643310434.pt.fatto
```

**C-main-TAG-428** · `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p0_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p0_s682647013.pt.fatto
```

**C-main-TAG-429** · `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1150248972.pt.fatto
```

**C-main-TAG-430** · `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1157715887.pt.fatto
```

**C-main-TAG-431** · `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1592395901.pt.fatto
```

**C-main-TAG-432** · `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p1_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p1_s399595374.pt.fatto
```

**C-main-TAG-433** · `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p1_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p1_s643310434.pt.fatto
```

**C-main-TAG-434** · `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p1_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p1_s682647013.pt.fatto
```

**C-main-TAG-435** · `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1150248972.pt.fatto
```

**C-main-TAG-436** · `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1157715887.pt.fatto
```

**C-main-TAG-437** · `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1592395901.pt.fatto
```

**C-main-TAG-438** · `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p2_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p2_s399595374.pt.fatto
```

**C-main-TAG-439** · `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p2_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p2_s643310434.pt.fatto
```

**C-main-TAG-440** · `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Madrid_p2_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Madrid_p2_s682647013.pt.fatto
```

**C-main-TAG-441** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1150248972.pt.fatto
```

**C-main-TAG-442** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1157715887.pt.fatto
```

**C-main-TAG-443** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1592395901.pt.fatto
```

**C-main-TAG-444** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s399595374.pt.fatto
```

**C-main-TAG-445** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s643310434.pt.fatto
```

**C-main-TAG-446** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s682647013.pt.fatto
```

**C-main-TAG-447** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1150248972.pt.fatto
```

**C-main-TAG-448** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1157715887.pt.fatto
```

**C-main-TAG-449** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1592395901.pt.fatto
```

**C-main-TAG-450** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s399595374.pt.fatto
```

**C-main-TAG-451** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s643310434.pt.fatto
```

**C-main-TAG-452** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s682647013.pt.fatto
```

**C-main-TAG-453** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1150248972.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1150248972.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1150248972.pt.fatto
```

**C-main-TAG-454** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1157715887.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1157715887.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1157715887.pt.fatto
```

**C-main-TAG-455** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1592395901.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1592395901.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1592395901.pt.fatto
```

**C-main-TAG-456** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s399595374.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s399595374.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s399595374.pt.fatto
```

**C-main-TAG-457** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s643310434.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s643310434.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s643310434.pt.fatto
```

**C-main-TAG-458** · `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s682647013.pt.fatto` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s682647013.pt.fatto: numstat 20	0	protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s682647013.pt.fatto
```

**C-main-TAG-459** · `protocol/e15/tempi/esito_e15.json` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/esito_e15.json: numstat 22	0	protocol/e15/tempi/esito_e15.json
```

**C-main-TAG-460** · `protocol/e15/tempi/pilota_tempi_16.json` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e15/tempi/pilota_tempi_16.json: numstat 32	0	protocol/e15/tempi/pilota_tempi_16.json
```

**C-main-TAG-461** · `protocol/e16/e16_risultati.json` · paper1-freeze-20261015h..paper1-freeze-20261028i

```
protocol/e16/e16_risultati.json: numstat 411264	0	protocol/e16/e16_risultati.json
```

**C-main-TAG-462** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261028i..paper1-freeze-20261028j

```
analysis/rigenerazione/CONFRONTO.md: numstat 83	55	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-463** · `evoluzione/analisi/figura2_51.py` · paper1-freeze-20261028i..paper1-freeze-20261028j

```
evoluzione/analisi/figura2_51.py: numstat 1	1	evoluzione/analisi/figura2_51.py
```

**C-main-TAG-464** · `CONGELAMENTO_E14B.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
CONGELAMENTO_E14B.md: numstat 4	2	CONGELAMENTO_E14B.md
```

**C-main-TAG-465** · `CONGELAMENTO_E18.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
CONGELAMENTO_E18.md: numstat 352	0	CONGELAMENTO_E18.md
```

**C-main-TAG-466** · `analysis/main.py` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
analysis/main.py: numstat 64	7	analysis/main.py
```

**C-main-TAG-467** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
analysis/rigenerazione/CONFRONTO.md: numstat 45	17	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-468** · `analysis/tabelle_paper1.py` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
analysis/tabelle_paper1.py: numstat 57	5	analysis/tabelle_paper1.py
```

**C-main-TAG-469** · `analysis/tabelle_suppl.py` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
analysis/tabelle_suppl.py: numstat 214	4	analysis/tabelle_suppl.py
```

**C-main-TAG-470** · `evoluzione/ADDENDUM_PEMS04.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
evoluzione/ADDENDUM_PEMS04.md: numstat 4	0	evoluzione/ADDENDUM_PEMS04.md
```

**C-main-TAG-471** · `evoluzione/analisi/analizza_e18.py` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
evoluzione/analisi/analizza_e18.py: numstat 738	0	evoluzione/analisi/analizza_e18.py
```

**C-main-TAG-472** · `evoluzione/audit/manifesto_zenodo.py` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
evoluzione/audit/manifesto_zenodo.py: numstat 99	0	evoluzione/audit/manifesto_zenodo.py
```

**C-main-TAG-473** · `evoluzione/audit/ripartizione_results.py` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
evoluzione/audit/ripartizione_results.py: numstat 115	0	evoluzione/audit/ripartizione_results.py
```

**C-main-TAG-474** · `evoluzione/audit/verifica_ingressi_e18.py` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
evoluzione/audit/verifica_ingressi_e18.py: numstat 87	0	evoluzione/audit/verifica_ingressi_e18.py
```

**C-main-TAG-475** · `evoluzione/esperimenti/esegui_e16.py` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
evoluzione/esperimenti/esegui_e16.py: numstat 9	7	evoluzione/esperimenti/esegui_e16.py
```

**C-main-TAG-476** · `protocol/E18.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
protocol/E18.md: numstat 147	0	protocol/E18.md
```

**C-main-TAG-477** · `protocol/REGISTRO_CORREZIONI.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
protocol/REGISTRO_CORREZIONI.md: numstat 52	0	protocol/REGISTRO_CORREZIONI.md
```

**C-main-TAG-478** · `protocol/SUMMARIES.en.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
protocol/SUMMARIES.en.md: numstat 155	0	protocol/SUMMARIES.en.md
```

**C-main-TAG-479** · `protocol/e18/COPIA_INGRESSI_MAC.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
protocol/e18/COPIA_INGRESSI_MAC.md: numstat 342	0	protocol/e18/COPIA_INGRESSI_MAC.md
```

**C-main-TAG-480** · `protocol/e18/tempi_parte_A.json` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
protocol/e18/tempi_parte_A.json: numstat 55	0	protocol/e18/tempi_parte_A.json
```

**C-main-TAG-481** · `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
protocol/spark/CONFRONTO_paper1-freeze-20261028i.md: numstat 679	0	protocol/spark/CONFRONTO_paper1-freeze-20261028i.md
```

**C-main-TAG-482** · `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
protocol/spark/CONFRONTO_paper1-freeze-20261028j.md: numstat 679	0	protocol/spark/CONFRONTO_paper1-freeze-20261028j.md
```

**C-main-TAG-483** · `protocol/zenodo/RIPARTIZIONE_RESULTS.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
protocol/zenodo/RIPARTIZIONE_RESULTS.md: numstat 301	0	protocol/zenodo/RIPARTIZIONE_RESULTS.md
```

**C-main-TAG-484** · `protocol/zenodo/RIPARTIZIONE_RESULTS_spark.md` · paper1-freeze-20261028j..paper1-freeze-20261030k

```
protocol/zenodo/RIPARTIZIONE_RESULTS_spark.md: numstat 301	0	protocol/zenodo/RIPARTIZIONE_RESULTS_spark.md
```

**C-main-TAG-485** · `CONGELAMENTO_E18TER.md` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
CONGELAMENTO_E18TER.md: numstat 170	0	CONGELAMENTO_E18TER.md
```

**C-main-TAG-486** · `analysis/main.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
analysis/main.py: numstat 11	1	analysis/main.py
```

**C-main-TAG-487** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
analysis/rigenerazione/CONFRONTO.md: numstat 32	53	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-488** · `analysis/tabelle_paper1.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
analysis/tabelle_paper1.py: numstat 75	35	analysis/tabelle_paper1.py
```

**C-main-TAG-489** · `analysis/tabelle_suppl.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
analysis/tabelle_suppl.py: numstat 132	43	analysis/tabelle_suppl.py
```

**C-main-TAG-490** · `evoluzione/analisi/analizza_e18ter.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/analisi/analizza_e18ter.py: numstat 312	0	evoluzione/analisi/analizza_e18ter.py
```

**C-main-TAG-491** · `evoluzione/audit/archivi_zenodo.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/archivi_zenodo.py: numstat 114	0	evoluzione/audit/archivi_zenodo.py
```

**C-main-TAG-492** · `evoluzione/audit/massimi_e14b.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/massimi_e14b.py: numstat 84	0	evoluzione/audit/massimi_e14b.py
```

**C-main-TAG-493** · `evoluzione/audit/patch/README.md` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/README.md: numstat 4	0	evoluzione/audit/patch/README.md
```

**C-main-TAG-494** · `evoluzione/audit/patch/patch_attributo_distanza.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_attributo_distanza.py: numstat 225	0	evoluzione/audit/patch/patch_attributo_distanza.py
```

**C-main-TAG-495** · `evoluzione/audit/patch/patch_e14b_adatta_F.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e14b_adatta_F.py: numstat 61	0	evoluzione/audit/patch/patch_e14b_adatta_F.py
```

**C-main-TAG-496** · `evoluzione/audit/patch/patch_e14b_ricostruzione.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e14b_ricostruzione.py: numstat 57	0	evoluzione/audit/patch/patch_e14b_ricostruzione.py
```

**C-main-TAG-497** · `evoluzione/audit/patch/patch_e15.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e15.py: numstat 386	0	evoluzione/audit/patch/patch_e15.py
```

**C-main-TAG-498** · `evoluzione/audit/patch/patch_e15_main.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e15_main.py: numstat 42	0	evoluzione/audit/patch/patch_e15_main.py
```

**C-main-TAG-499** · `evoluzione/audit/patch/patch_e18_e16.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e18_e16.py: numstat 80	0	evoluzione/audit/patch/patch_e18_e16.py
```

**C-main-TAG-500** · `evoluzione/audit/patch/patch_e18_main.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e18_main.py: numstat 38	0	evoluzione/audit/patch/patch_e18_main.py
```

**C-main-TAG-501** · `evoluzione/audit/patch/patch_e18ter_main.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e18ter_main.py: numstat 115	0	evoluzione/audit/patch/patch_e18ter_main.py
```

**C-main-TAG-502** · `evoluzione/audit/patch/patch_e18ter_tabellaV.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e18ter_tabellaV.py: numstat 87	0	evoluzione/audit/patch/patch_e18ter_tabellaV.py
```

**C-main-TAG-503** · `evoluzione/audit/patch/patch_e18ter_tabelle.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e18ter_tabelle.py: numstat 202	0	evoluzione/audit/patch/patch_e18ter_tabelle.py
```

**C-main-TAG-504** · `evoluzione/audit/patch/patch_e3_riviste.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e3_riviste.py: numstat 156	0	evoluzione/audit/patch/patch_e3_riviste.py
```

**C-main-TAG-505** · `evoluzione/audit/patch/patch_e3bis_costi.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e3bis_costi.py: numstat 116	0	evoluzione/audit/patch/patch_e3bis_costi.py
```

**C-main-TAG-506** · `evoluzione/audit/patch/patch_e5_prosa.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e5_prosa.py: numstat 38	0	evoluzione/audit/patch/patch_e5_prosa.py
```

**C-main-TAG-507** · `evoluzione/audit/patch/patch_e6_origini.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_e6_origini.py: numstat 116	0	evoluzione/audit/patch/patch_e6_origini.py
```

**C-main-TAG-508** · `evoluzione/audit/patch/patch_g18_21.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_g18_21.py: numstat 57	0	evoluzione/audit/patch/patch_g18_21.py
```

**C-main-TAG-509** · `evoluzione/audit/patch/patch_g23.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_g23.py: numstat 47	0	evoluzione/audit/patch/patch_g23.py
```

**C-main-TAG-510** · `evoluzione/audit/patch/patch_l_didascalie.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_l_didascalie.py: numstat 63	0	evoluzione/audit/patch/patch_l_didascalie.py
```

**C-main-TAG-511** · `evoluzione/audit/patch/patch_metrics.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_metrics.py: numstat 49	0	evoluzione/audit/patch/patch_metrics.py
```

**C-main-TAG-512** · `evoluzione/audit/patch/patch_priore_calibrato.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_priore_calibrato.py: numstat 135	0	evoluzione/audit/patch/patch_priore_calibrato.py
```

**C-main-TAG-513** · `evoluzione/audit/patch/patch_statica_causale.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_statica_causale.py: numstat 266	0	evoluzione/audit/patch/patch_statica_causale.py
```

**C-main-TAG-514** · `evoluzione/audit/patch/patch_statica_variante.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_statica_variante.py: numstat 275	0	evoluzione/audit/patch/patch_statica_variante.py
```

**C-main-TAG-515** · `evoluzione/audit/patch/patch_stats_friedman.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_stats_friedman.py: numstat 182	0	evoluzione/audit/patch/patch_stats_friedman.py
```

**C-main-TAG-516** · `evoluzione/audit/patch/patch_tempi_main.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_tempi_main.py: numstat 42	0	evoluzione/audit/patch/patch_tempi_main.py
```

**C-main-TAG-517** · `evoluzione/audit/patch/patch_tolleranza_appaiamento.py` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
evoluzione/audit/patch/patch_tolleranza_appaiamento.py: numstat 54	0	evoluzione/audit/patch/patch_tolleranza_appaiamento.py
```

**C-main-TAG-518** · `protocol/E18ter.md` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
protocol/E18ter.md: numstat 41	0	protocol/E18ter.md
```

**C-main-TAG-519** · `protocol/e14b/MASSIMI_DELTA.md` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
protocol/e14b/MASSIMI_DELTA.md: numstat 18	0	protocol/e14b/MASSIMI_DELTA.md
```

**C-main-TAG-520** · `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
protocol/spark/CONFRONTO_paper1-freeze-20261030k.md: numstat 709	0	protocol/spark/CONFRONTO_paper1-freeze-20261030k.md
```

**C-main-TAG-521** · `protocol/zenodo/ARCHIVI.md` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
protocol/zenodo/ARCHIVI.md: numstat 14	0	protocol/zenodo/ARCHIVI.md
```

**C-main-TAG-522** · `protocol/zenodo/MANIFEST.txt` · paper1-freeze-20261030k..paper1-freeze-20261030l

```
protocol/zenodo/MANIFEST.txt: numstat 12683	0	protocol/zenodo/MANIFEST.txt
```

**C-main-TAG-523** · `evoluzione/audit/archivi_zenodo.py` · paper1-freeze-20261030l..paper1-freeze-20261030l-pub

```
evoluzione/audit/archivi_zenodo.py: numstat 15	5	evoluzione/audit/archivi_zenodo.py
```

**C-main-TAG-524** · `protocol/REGISTRO_CORREZIONI.md` · paper1-freeze-20261030l..paper1-freeze-20261030l-pub

```
protocol/REGISTRO_CORREZIONI.md: numstat 2	1	protocol/REGISTRO_CORREZIONI.md
```

**C-main-TAG-525** · `protocol/RISCRITTURA_STORIA.md` · paper1-freeze-20261030l..paper1-freeze-20261030l-pub

```
protocol/RISCRITTURA_STORIA.md: numstat 159	0	protocol/RISCRITTURA_STORIA.md
```

**C-main-TAG-526** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` · paper1-freeze-20261030l..paper1-freeze-20261030l-pub

```
protocol/spark/CONFRONTO_paper1-freeze-20261030l.md: numstat 688	0	protocol/spark/CONFRONTO_paper1-freeze-20261030l.md
```

**C-main-TAG-527** · `protocol/zenodo/ARCHIVI.md` · paper1-freeze-20261030l..paper1-freeze-20261030l-pub

```
protocol/zenodo/ARCHIVI.md: numstat 5	3	protocol/zenodo/ARCHIVI.md
```

**C-main-TAG-528** · `protocol/zenodo/MANIFEST.txt` · paper1-freeze-20261030l..paper1-freeze-20261030l-pub

```
protocol/zenodo/MANIFEST.txt: numstat 6	4	protocol/zenodo/MANIFEST.txt
```

**C-main-TAG-529** · `evoluzione/analisi/analizza_e18.py` · paper1-freeze-20261030l-pub..paper1-freeze-20261030l-pub2

```
evoluzione/analisi/analizza_e18.py: numstat 2	1	evoluzione/analisi/analizza_e18.py
```

**C-main-TAG-530** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` · paper1-freeze-20261030l-pub2..paper1-freeze-20261030l-pub3

```
protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md: numstat 691	0	protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md
```

**C-main-TAG-531** · `analysis/main.py` · paper1-freeze-20261030l-pub3..paper1-freeze-20261101m

```
analysis/main.py: numstat 211	1	analysis/main.py
```

**C-main-TAG-532** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261030l-pub3..paper1-freeze-20261101m

```
analysis/rigenerazione/CONFRONTO.md: numstat 46	579	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-533** · `analysis/tabelle_suppl.py` · paper1-freeze-20261030l-pub3..paper1-freeze-20261101m

```
analysis/tabelle_suppl.py: numstat 2	2	analysis/tabelle_suppl.py
```

**C-main-TAG-534** · `evoluzione/audit/massimi_e14b.py` · paper1-freeze-20261030l-pub3..paper1-freeze-20261101m

```
evoluzione/audit/massimi_e14b.py: numstat 12	2	evoluzione/audit/massimi_e14b.py
```

**C-main-TAG-535** · `evoluzione/audit/patch/patch_e14_massimi.py` · paper1-freeze-20261030l-pub3..paper1-freeze-20261101m

```
evoluzione/audit/patch/patch_e14_massimi.py: numstat 62	0	evoluzione/audit/patch/patch_e14_massimi.py
```

**C-main-TAG-536** · `evoluzione/audit/patch/patch_limite_d.py` · paper1-freeze-20261030l-pub3..paper1-freeze-20261101m

```
evoluzione/audit/patch/patch_limite_d.py: numstat 49	0	evoluzione/audit/patch/patch_limite_d.py
```

**C-main-TAG-537** · `protocol/e14b/MASSIMI_DELTA.md` · paper1-freeze-20261030l-pub3..paper1-freeze-20261101m

```
protocol/e14b/MASSIMI_DELTA.md: numstat 13	13	protocol/e14b/MASSIMI_DELTA.md
```

**C-main-TAG-538** · `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` · paper1-freeze-20261030l-pub3..paper1-freeze-20261101m

```
protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md: numstat 688	0	protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md
```

**C-main-TAG-539** · `analysis/main.py` · paper1-freeze-20261101m..paper1-freeze-20261101m2

```
analysis/main.py: numstat 2	2	analysis/main.py
```

**C-main-TAG-540** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261101m..paper1-freeze-20261101m2

```
analysis/rigenerazione/CONFRONTO.md: numstat 2	2	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-541** · `evoluzione/audit/patch/patch_main_solo_testo.py` · paper1-freeze-20261101m..paper1-freeze-20261101m2

```
evoluzione/audit/patch/patch_main_solo_testo.py: numstat 48	0	evoluzione/audit/patch/patch_main_solo_testo.py
```

**C-main-TAG-542** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261101m2..paper1-freeze-20261101n

```
analysis/rigenerazione/CONFRONTO.md: numstat 2	2	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-543** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261101n..paper1-freeze-20261101o

```
analysis/rigenerazione/CONFRONTO.md: numstat 2	2	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-544** · `evoluzione/audit/massimi_e14b.py` · paper1-freeze-20261101n..paper1-freeze-20261101o

```
evoluzione/audit/massimi_e14b.py: numstat 24	7	evoluzione/audit/massimi_e14b.py
```

**C-main-TAG-545** · `evoluzione/audit/patch/patch_e14_massimi_2.py` · paper1-freeze-20261101n..paper1-freeze-20261101o

```
evoluzione/audit/patch/patch_e14_massimi_2.py: numstat 74	0	evoluzione/audit/patch/patch_e14_massimi_2.py
```

**C-main-TAG-546** · `protocol/e14b/MASSIMI_DELTA.md` · paper1-freeze-20261101n..paper1-freeze-20261101o

```
protocol/e14b/MASSIMI_DELTA.md: numstat 9	7	protocol/e14b/MASSIMI_DELTA.md
```

**C-main-TAG-547** · `CONGELAMENTO_E18QUATER.md` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
CONGELAMENTO_E18QUATER.md: numstat 73	0	CONGELAMENTO_E18QUATER.md
```

**C-main-TAG-548** · `analysis/main.py` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
analysis/main.py: numstat 11	1	analysis/main.py
```

**C-main-TAG-549** · `analysis/rigenerazione/CONFRONTO.md` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
analysis/rigenerazione/CONFRONTO.md: numstat 593	47	analysis/rigenerazione/CONFRONTO.md
```

**C-main-TAG-550** · `analysis/tabelle_paper1.py` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
analysis/tabelle_paper1.py: numstat 15	2	analysis/tabelle_paper1.py
```

**C-main-TAG-551** · `analysis/tabelle_suppl.py` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
analysis/tabelle_suppl.py: numstat 71	0	analysis/tabelle_suppl.py
```

**C-main-TAG-552** · `evoluzione/analisi/classi_per_sensore.py` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
evoluzione/analisi/classi_per_sensore.py: numstat 111	0	evoluzione/analisi/classi_per_sensore.py
```

**C-main-TAG-553** · `evoluzione/analisi/figura_rete.py` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
evoluzione/analisi/figura_rete.py: numstat 2	2	evoluzione/analisi/figura_rete.py
```

**C-main-TAG-554** · `evoluzione/audit/patch/patch_e18quater_cat.py` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
evoluzione/audit/patch/patch_e18quater_cat.py: numstat 49	0	evoluzione/audit/patch/patch_e18quater_cat.py
```

**C-main-TAG-555** · `evoluzione/audit/patch/patch_e18quater_main.py` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
evoluzione/audit/patch/patch_e18quater_main.py: numstat 142	0	evoluzione/audit/patch/patch_e18quater_main.py
```

**C-main-TAG-556** · `evoluzione/audit/patch/patch_registro_31.py` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
evoluzione/audit/patch/patch_registro_31.py: numstat 42	0	evoluzione/audit/patch/patch_registro_31.py
```

**C-main-TAG-557** · `evoluzione/esperimenti/esegui_e18quater.py` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
evoluzione/esperimenti/esegui_e18quater.py: numstat 262	0	evoluzione/esperimenti/esegui_e18quater.py
```

**C-main-TAG-558** · `protocol/E18quater.md` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
protocol/E18quater.md: numstat 28	0	protocol/E18quater.md
```

**C-main-TAG-559** · `protocol/REGISTRO_CORREZIONI.md` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
protocol/REGISTRO_CORREZIONI.md: numstat 2	1	protocol/REGISTRO_CORREZIONI.md
```

**C-main-TAG-560** · `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
protocol/spark/CONFRONTO_paper1-freeze-20261101n.md: numstat 688	0	protocol/spark/CONFRONTO_paper1-freeze-20261101n.md
```

**C-main-TAG-561** · `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
protocol/spark/CONFRONTO_paper1-freeze-20261101o.md: numstat 688	0	protocol/spark/CONFRONTO_paper1-freeze-20261101o.md
```

**C-main-TAG-562** · `protocol/spark/NOTA_20261101n.md` · paper1-freeze-20261101o..paper1-freeze-20261103p

```
protocol/spark/NOTA_20261101n.md: numstat 6	0	protocol/spark/NOTA_20261101n.md
```

**C-main-TAG-563** · `evoluzione/audit/manifesto_zenodo.py` · paper1-freeze-20261103p..paper1-freeze-20261103q

```
evoluzione/audit/manifesto_zenodo.py: numstat 2	0	evoluzione/audit/manifesto_zenodo.py
```

**C-main-TAG-564** · `evoluzione/audit/patch/patch_manifesto_nota.py` · paper1-freeze-20261103p..paper1-freeze-20261103q

```
evoluzione/audit/patch/patch_manifesto_nota.py: numstat 44	0	evoluzione/audit/patch/patch_manifesto_nota.py
```

**C-main-TAG-565** · `evoluzione/audit/patch/patch_zenodo_regola.py` · paper1-freeze-20261103p..paper1-freeze-20261103q

```
evoluzione/audit/patch/patch_zenodo_regola.py: numstat 43	0	evoluzione/audit/patch/patch_zenodo_regola.py
```

**C-main-TAG-566** · `evoluzione/audit/ripartizione_results.py` · paper1-freeze-20261103p..paper1-freeze-20261103q

```
evoluzione/audit/ripartizione_results.py: numstat 4	1	evoluzione/audit/ripartizione_results.py
```

**C-main-TAG-567** · `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` · paper1-freeze-20261103p..paper1-freeze-20261103q

```
protocol/spark/CONFRONTO_paper1-freeze-20261103p.md: numstat 701	0	protocol/spark/CONFRONTO_paper1-freeze-20261103p.md
```

**C-main-TAG-568** · `protocol/zenodo/RIPARTIZIONE_RESULTS.md` · paper1-freeze-20261103p..paper1-freeze-20261103q

```
protocol/zenodo/RIPARTIZIONE_RESULTS.md: numstat 21	15	protocol/zenodo/RIPARTIZIONE_RESULTS.md
```

**C-main-TAG-569** · `protocol/zenodo/RIPARTIZIONE_RESULTS_spark.md` · paper1-freeze-20261103p..paper1-freeze-20261103q

```
protocol/zenodo/RIPARTIZIONE_RESULTS_spark.md: numstat 11	5	protocol/zenodo/RIPARTIZIONE_RESULTS_spark.md
```


## `paper4` — deviation

**C-paper4-DEV-001** · `protocol/paper4/E9.md` · line 258 (text pattern)

```
Deviations, item 1.
```

**C-paper4-DEV-002** · `protocol/paper4/E9.md` · line 288 (heading)

```
1. *2026-11-07, cost measurement.* The first two isolated measurements ran the arms in the order G0, G1,
```

**C-paper4-DEV-003** · `protocol/paper4/P4A.md` · line 228 (heading)

```
1. *2026-11-08, after the signature, before the run.* The signed `p4a.py` (ff3204dee7064a27) writes every
```


## `paper4` — git commit

**C-paper4-GIT-001** · commit ef31396c28cf, 2026-11-10T16:19:14+01:00 · register: 23, 26

```
paper4: register item 26, time of the internal review in item 23 and E10predbis.md corrected from the commit sequence (14:38, not 15:15)
```

**C-paper4-GIT-002** · commit a9710f1701d1, 2026-11-10T12:31:19+01:00 · register: 25

```
paper4: register item 25, third-party MoGERNN code removed from tracking and LICENSE CC BY 4.0
```

**C-paper4-GIT-003** · commit fe81f4596617, 2026-11-10T11:37:55+01:00 · register: unregistered

```
paper4: main.py step 3d fails unless S2 of the supplementary material gives protocol/paper4/<record>.md (<commit>) for each of the 13 frozen records, the commit in this repository, the file signed at that commit and the frozen-record commit equal to EXPERIMENTS; S1 Source items without a path and commit are listed; step 3c strips the break points of inline code, which hid every file name (the supplement count was 0, it is 55); protocol/paper4/fase2/genera_limiti_fonti.py regenerates LIMITI_FONTI.json from git objects at a commit, keeping its structure and section_vi_support mapping (reproduces the committed file at 2849887 byte for byte)
```

**C-paper4-GIT-004** · commit d2f6220ba912, 2026-11-10T09:44:52+01:00 · register: unregistered

```
paper4: main.py step 3 covers the two LaTeX projects of the manuscript (paper at the root, supplementary material in supplementary/): every generated .tex from the current Markdown, every LaTeX reference resolved inside its own project, fixed-text references between the projects listed (3b); every file named in section VI listed in protocol/paper4/fase2/LIMITI_FONTI.json (3c); text-only check PASS on manuscript ffe0b36
```

**C-paper4-GIT-005** · commit 17ad609cd0e9, 2026-11-10T09:14:05+01:00 · register: 24

```
paper4: LIMITI_FONTI.json, provenance of the 14 files supporting section VI (commit, blob, sha256, supported block; P4A signed b633f53 vs archived e53d3cb); register item 24
```

**C-paper4-GIT-006** · commit b05df6edf9dd, 2026-11-09T15:18:25+01:00 · register: 23

```
paper4: main.py checks and regenerates the records of E10-pred-bis and E12-sexies-bis (regeneration identical); register item 23 (class weights of each design in E10-pred, corrected by E10-pred-bis); text-only check PASS on the manuscript after the internal review of 2026-11-09 (15:15, 15:30)
```

**C-paper4-GIT-007** · commit 9421197566bf, 2026-11-09T14:39:10+01:00 · register: 22

```
paper4: main.py checks and regenerates the records of E12-quater, E12-quinquies, E10-pred and E12-sexies and the figure of E12-sexies (new paper4/analysis/figure_e12sexies.py, drawn from e12sexies_risultati.json); regeneration of the four records and the figure identical; register item 22 (asymmetric fallback of E12-ter, measured by E12-quater); text-only check PASS on the rewritten manuscript
```

**C-paper4-GIT-008** · commit ad5f64b35927, 2026-11-08T21:38:08+01:00 · register: unregistered

```
paper4: E10-pred, E12-quater, E12-quinquies drafts approved with one correction each (input masks under uniform placement declared and their realised share recorded, cells with an observed segment reported; full fallback chain with a control per link and the case D' better than D; N_min per slot and readable bins declared in advance)
```

**C-paper4-GIT-009** · commit c11e3c5cb91b, 2026-11-08T20:59:41+01:00 · register: 21

```
paper4: model states not saved, stated in §VI Reproducibility and in Data and Code Availability (sentence of the internal review); Zenodo DOI 10.5281/zenodo.24059573 with three archives from the executor's partition; README no longer claims checkpoints; register item 21 (declared design choice, no effect on the numbers); provenance of 7.5 h and archive sizes declared; text-only check PASS; manuscript/ untouched
```

**C-paper4-GIT-010** · commit a9fd300048df, 2026-11-08T20:22:46+01:00 · register: 1, 13

```
paper4: draft restructured after the internal review of the full draft (Part B before Part A; setting and protocol stated once; E12, E12-bis and E12-ter in one section with one table; limits collected; Melbourne stated once in the discussion; installation vs masked-node kriging; earlier report named only in the introduction and discussion; abstract under 200 words; RQs in standard form; contributions reordered; third open direction); authors, grant, bibliography, biographies and data availability as in Paper 1; supplement with register items 1-3, 8-13 and the frozen records; one LaTeX file per section and an Overleaf package; main.py sources updated, text check PASS
```

**C-paper4-GIT-011** · commit ae392326b112, 2026-11-08T20:05:26+01:00 · register: unregistered

```
paper4: full draft typeset into one PDF (paper4/manuscript/build.py: Markdown sections to IEEEtran main.tex, Tectonic; register of corrections as supplement); working title, abstract and lead of Part B; README of Paper 4 with the map of the experiments and the regeneration; protocol status of 4A updated
```

**C-paper4-GIT-012** · commit 130e2e4f57ad, 2026-11-08T19:55:44+01:00 · register: 18, 20

```
paper4: causes of items 18-20 from the executor's measurements (CAUSE_4A.md, 03fd226); dated note appended to CONGELAMENTO_4A.md (now f8f093436de33d99; generated text before the note still 7304d9639f91ec81, no computed control changes); Part A section without cause markers; main.py checks the generated text and masks the note; SUMMARIES.en.md lists the Italian records of Part A
```

**C-paper4-GIT-013** · commit c3e8ab6eff17, 2026-11-08T15:38:12+01:00 · register: 18, 20

```
paper4: Part A section draft (three corrections declared, statements descriptive; Table 69 with 30 sections and 29 in the rank correlation); register items 18-20 with the diagnosis so far, causes open for the executor; main.py regenerates and checks P4A (seventh frozen record)
```

**C-paper4-GIT-014** · commit e53d3cb235c0, 2026-11-08T15:01:42+01:00 · register: unregistered

```
paper4: P4A input check after the run outside the frozen p4a.py (verifica_p4a.py); deviation 1 dated (no per-figure CSVs; check added)
```

**C-paper4-GIT-015** · commit f99b765ddabc, 2026-11-08T14:55:42+01:00 · register: 14, 17

```
paper4: P4A on the review's decisions (threshold between sensors primary, in time secondary; descriptive reading rules; Austin volume-occupancy recomputed; arterial values per pair primary); register items 14-17; P4A code (step 0, Tables 64-69 recomputed, corrections 1-3, weighted bootstrap, guard, frozen-record generator, self-tests); fingerprinted copy of t4c_crossval.py; manifest of the Part A inputs
```

**C-paper4-GIT-016** · commit 824f6caf3ab7, 2026-11-08T14:43:47+01:00 · register: unregistered

```
paper4: P4A pre-registration draft (three datasets with fingerprints, regeneration of Tables 64-69, three corrections, untraced deliverable numbers, choices to confirm); perimeter of the negative result in limits and discussion; English summaries of the Phase 1 records
```

**C-paper4-GIT-017** · commit 61367a0008e7, 2026-11-08T14:24:02+01:00 · register: 9, 13

```
paper4: E12-ter section; introduction, research questions and contributions; discussion, limits, conclusion; Part A outline and status; paper order; thesis rewritten (protocol §1.1, dated note), §1.2-§1.3 status, §2.6 choices of the analyses without training, §3 points closed; register of corrections items 9-13; paper4/analysis/main.py (fingerprints, regeneration of the six frozen records, numbers in the text)
```

**C-paper4-GIT-018** · commit 0be7e7aeaabf, 2026-11-07T15:37:39+01:00 · register: unregistered

```
paper4: E9 isolated cost of G1-rand(deg) (135.9 s) and G1 in the same conditions; launched by the executor; deviation on the earlier measurements
```

**C-paper4-GIT-019** · commit 646332df6dda, 2026-11-06T21:42:09+01:00 · register: unregistered

```
paper4: E9 and E11 section, two precision fixes
```

**C-paper4-GIT-020** · commit 4fd7fe173feb, 2026-11-06T21:38:31+01:00 · register: 8

```
paper4: register of corrections, item 8 (E11 generator, red-recall indexing)
```

**C-paper4-GIT-021** · commit b2863c98c07d, 2026-11-06T19:02:25+01:00 · register: unregistered

```
paper4: E11 generator, red-recall indexing corrected (node and class selected in two steps), recall in the self-test, end-to-end self-test on a synthetic copy
```

**C-paper4-GIT-022** · commit a8621901cbb6, 2026-11-06T16:56:20+01:00 · register: unregistered

```
paper4: E11 diagnostic D4 (dropout 0.3 on block outputs, no static attribute) with the adoption rule fixed before launch
```

**C-paper4-GIT-023** · commit 41cea36cf78f, 2026-11-06T15:54:49+01:00 · register: unregistered

```
paper4: Tables 34-35 regenerable only after fixing the pairing (RC 4); first-run reading of the deliverable's control noted for the appendix of defects
```

**C-paper4-GIT-024** · commit e9ca476b0d8c, 2026-11-06T15:54:30+01:00 · register: 7

```
paper4: register of corrections, item 7 (weights, topology and connectivity of the deliverable's negative control)
```

**C-paper4-GIT-025** · commit b937aa2f1d0e, 2026-11-06T11:46:22+01:00 · register: 1, 3

```
paper4: single protocol with Part A and Part B (sections 1-2, review decisions of 6/11 and brief 9b); E11 pre-registration draft; register of corrections items 1-3
```


## `paper4` — record note

**C-paper4-REC-001** · `paper4/congelamenti/CONGELAMENTO_4A.md` · line 11

```
## Correction 1 — M30 threshold out of sample (mean over 5 splits [interval])
```

**C-paper4-REC-002** · `paper4/congelamenti/CONGELAMENTO_4A.md` · line 49

```
## Table 69 and correction 3 — Austin, lanes
```

**C-paper4-REC-003** · `paper4/congelamenti/CONGELAMENTO_4A.md` · line 59

```
Correction 3: rank correlation between lanes and section area under the curve over 29 sections (by lanes: {'2': 21, '3': 6, '4': 2}): -0.441 [-0.714; -0.072].
```

**C-paper4-REC-004** · `paper4/congelamenti/CONGELAMENTO_4A.md` · line 146

```
## Controls, deviations and defects
```

**C-paper4-REC-005** · `paper4/congelamenti/CONGELAMENTO_4A.md` · line 149

```
2. The thresholds of correction 1 were chosen on half A and saved with fingerprint before any metric of half B.
```

**C-paper4-REC-006** · `paper4/congelamenti/CONGELAMENTO_4A.md` · line 150

```
3. The arterial values of Table 68 and the Austin volume–occupancy correlations are recomputed (register of corrections, items 14–16); the deliverable's brackets of Austin are interquartile ranges (item 17).
```

**C-paper4-REC-007** · `paper4/congelamenti/CONGELAMENTO_4A.md` · line 153

```
## Dated note (2026-11-08), appended after freezing
```

**C-paper4-REC-008** · `paper4/congelamenti/CONGELAMENTO_4A.md` · line 157

```
1. **T67, green class (register of corrections, item 18).** The deliverable's green class was 0.8 ≤ r_tr < 1.5. The 442,965 cells it misses are exactly those whose measured factor is clipped at 1.5 (`carica_m30`); with that class the conserved module gives 2,989,877 cells and +0.0326, as printed. The conserved code has 1.6 (`validazione_colocalizzata.py`, line 117) in its only commit (dc8b6bb, 2026-09-17): the version that printed the table is not conserved. The overall +0.255 is not reproduced by that class nor by six other cell sets (from +0.249 to +0.480): generator not found.
```

**C-paper4-REC-009** · `paper4/congelamenti/CONGELAMENTO_4A.md` · line 159

```
3. **Austin sections (item 20).** The 40 sections are `intname|direction` after excluding the three intersections without direction. The only definition that gives the brief's 31 is "sections with a defined area under the curve, whatever the number of lanes": the 29 of correction 3 plus 2 with one lane. The section that leaves correction 3 (30 → 29) is `LAMARZENNIA|SB`: 2 lanes, 43,081 aggregated cells, 11 of them with a congested lane, so its area under the curve is undefined. The deliverable's lane–AUC correlation (−0.541, p = 0.002, over 31 sections) is not reproduced: −0.269 (p = 0.144) over those 31, −0.441 (p = 0.017) over the 29 of correction 3. Its section excluded for a prevalence difference of −45.1 points does not exist under the conserved code, where every difference is ≥ 0 by construction (maximum +52.0, `BurnetRutland|SB`). No conserved script computes either value: generator not found. The prevalence differences of 3 and 4 lanes (+18.62 and +9.88 against +18.35 and +9.93 printed) are not traced.
```

**C-paper4-REC-010** · `paper4/congelamenti/CONGELAMENTO_E10pred.md` · line 35

```
## Controls, deviations and defects
```

**C-paper4-REC-011** · `paper4/congelamenti/CONGELAMENTO_E10predbis.md` · line 31

```
## Controls, deviations and defects
```

**C-paper4-REC-012** · `paper4/congelamenti/CONGELAMENTO_E10predbis.md` · line 34

```
2. Register of corrections, item 23: E10-pred scored each design with its own class weights.
```

**C-paper4-REC-013** · `paper4/congelamenti/CONGELAMENTO_E11.md` · line 73

```
## Deviations and defects
```

**C-paper4-REC-014** · `paper4/congelamenti/CONGELAMENTO_E11.md` · line 76

```
2. Control of the warning `p4b.py:367: Mean of empty slice` (dated note, 2026-11-06), printed once per run (240 of 240). It comes from the historical-average table (node × weekly slot), built on observed nodes only (D1); the empty rows lie on the node axis. Checked by this generator on the 60 rebuilt setups (configuration × seed; the four arms of a seed share them): empty rows 45–67 per setup, equal to the hidden nodes in every setup: True; observed nodes without training data: 0; setups with a non-finite value in the historical average: 0. The empty mean is replaced by the global mean and hidden rows are set to zero before any input is built. Per-cell files with a non-finite probability on target nodes: 0 runs of 240 (720 files checked). No NaN enters the means or the resample, which use per-node sums over valid cells only (item 1).
```

**C-paper4-REC-015** · `paper4/congelamenti/CONGELAMENTO_E11.md` · line 81

```
7. Defect of this generator, found at its first run on 2026-11-06 and corrected before any output was written: the red-recall step indexed `p[:, nodes, :, 2]` in one step, which numpy reorders to (nodes, origins, horizons) and which stopped with an IndexError. Node selection and class selection are now separate (`red_recall`), covered by the self-test with origins != nodes.
```

**C-paper4-REC-016** · `paper4/congelamenti/CONGELAMENTO_E12.md` · line 151

```
## Controls, deviations and defects
```

**C-paper4-REC-017** · `paper4/congelamenti/CONGELAMENTO_E12bis.md` · line 62

```
## Controls, deviations and defects
```

**C-paper4-REC-018** · `paper4/congelamenti/CONGELAMENTO_E12quater.md` · line 109

```
## Controls, deviations and defects
```

**C-paper4-REC-019** · `paper4/congelamenti/CONGELAMENTO_E12quinquies.md` · line 71

```
## Controls, deviations and defects
```

**C-paper4-REC-020** · `paper4/congelamenti/CONGELAMENTO_E12sexies.md` · line 497

```
## Controls, deviations and defects
```

**C-paper4-REC-021** · `paper4/congelamenti/CONGELAMENTO_E12sexiesbis.md` · line 222

```
## Controls, deviations and defects
```

**C-paper4-REC-022** · `paper4/congelamenti/CONGELAMENTO_E12ter.md` · line 79

```
## Controls, deviations and defects
```

**C-paper4-REC-023** · `paper4/congelamenti/CONGELAMENTO_E9.md` · line 85

```
## Controls, deviations and defects
```

**C-paper4-REC-024** · `paper4/congelamenti/CONGELAMENTO_E9.md` · line 89

```
3. Cost measurement (E9.md, Deviations 1): the two first isolated measurements of G1-rand(deg) were taken during Spotlight indexing and are not used; the cost table uses the measurement with Spotlight idle.
```


## `paper4` — register row

**C-paper4-REG-001** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 17, item 1

```
| 1 | Windows built by index across calendar jumps: the Traffic4cast series are one-week blocks separated by 7-day jumps (Madrid 15, London 16, Melbourne 15), and `models/gomo_sparse.py:119` builds origins as `arange` over raw indices | admissible-origin rule (15-min cadence from the first input step to the last target), with a causality test, as in Paper 1 (register of corrections item 5). Effect: to be measured as the share of excluded origins per city | reading the timestamps of the target files while drafting the perimeter, 2026-11-06 | `protocol/paper4/PROTOCOLLO.md` §2.3 |
```

**C-paper4-REG-002** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 18, item 2

```
| 2 | Free-flow reference on the loop contexts computed as the 85th percentile of speed over the whole year, test period included (`OR3/data_collection/go-mo/2_gomo_targets.py:42`) | 85th percentile on the training period only, if GO-MO contexts are used in forecasting; the city contexts use the provider's `free_flow_kph`, which is causal | reading the target builders, 2026-11-06 | `protocol/paper4/PROTOCOLLO.md` §2.1 |
```

**C-paper4-REG-003** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 19, item 3

```
| 3 | Population: `gomo_sparse.py` aligns 828 / 774 / 587 nodes (Madrid, London, Melbourne), not the 900 / 900 / 594 of the target files | declared; the same difference as Paper 1, register of corrections item 8 | `aligned graph` lines in `OLD/log/sparse_5semi.log`, `sparse_fixed.log`, `gomo_corretto.log`, 2026-11-06 | `protocol/paper4/PROTOCOLLO.md` §2.3 |
```

**C-paper4-REG-004** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 20, item 4

```
| 4 | Tables 34-35 (negative control of the geometry) could be regenerated only after fixing the pairing in the conserved script: `analisi/geometria_criteri.py` paired the true and randomised graphs by looking for `knn` in the graph *name* (r. 202-203), whereas `knn` is the `modo` column and the names are `comp_q<xy>` / `neg_rand_q<xy>` (`make_geo_sweep.py` r. 52, 76); the result CSVs are also named `geo_<city>_<graph>_s<s>.csv` while the script looked for `geo_<graph>_s<s>.csv` (r. 142, 206-207). No pair was ever found with the preserved script; the tables were nevertheless computed from the preserved CSVs, since the re-run reproduces them exactly | pairing by `comp_q<xy>` ↔ `neg_rand_q<xy>` of the same city and city-prefixed CSV names (`evoluzione/audit/patch/patch_p4_criterio4.py`, 2026-11-06); criterion 4 re-run on the preserved CSVs (`OLD/replication/geo/`, 5 seeds), row-by-row comparison with Tables 34-35 in `protocol/paper4/fase1/GEOMETRIA_CRITERIO4_rigenerato.md`: Tables 34-35 and the Melbourne run (text, p. 96) reproduced exactly, including the per-seed values. Register only: no Paper 4 number depends on it | search for the generator of Tables 34-35 (D7), 2026-11-06 | `protocol/paper4/fase1/GEOMETRIA_CRITERIO4_rigenerato.md` |
```

**C-paper4-REG-005** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 21, item 5

```
| 5 | Table 66 (ratio between the rank correlation of the raw inputs and that of the reconstructed factor) has no generator: `data_collection/t4c_crossval.py` prints the per-input correlations to the screen (r. 137-160) and saves only the pairs (r. 194); no script computes the ratio. The `--exclude-empty` and `--max-dist 30` outputs (README §7.11, r. 727-729) were not preserved | the three README commands re-run with preserved outputs, fingerprints of CSVs and inputs, comparison with Tables 64-65 in `protocol/paper4/fase1/CROSSVAL_rigenerato.md` (Tables 64-65 and the 30 m sensitivity reproduced exactly; base CSV byte-identical to the preserved one); Table 66 not regenerated (no generator), to be recomputed from the preserved screen outputs if needed | search for the generator of Tables 64-66 (D8), 2026-11-06 | `protocol/paper4/fase1/CROSSVAL_rigenerato.md` |
```

**C-paper4-REG-006** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 22, item 6

```
| 6 | `t4cmad_rand_k1.pkl`, `t4cmad_rand_k2.pkl` (written in the same second, 22/8/2026) and `t4cmad_identity_graph.pkl` (21/8/2026) have no generator in the repository, in the untracked files or in the two histories; the only traces of use are `OLD/log/randk.log` (ten runs of `models/gomo_sparse.py` whose CSVs `replication/randk{1,2}_t4cmad_s{0-4}.csv` were not preserved) and `OLD/log/identita.log` (`replication/identita/ident_t4cmad_s0-4.csv`, preserved) | graphs characterised from the files (nodes, edges, degree distribution, weights, overlap with the road graph, fingerprints) in `protocol/paper4/fase1/GRAFI_SENZA_GENERATORE.md`; no result of the deliverable is traced to them | search for the generator (D9), 2026-11-06 | `protocol/paper4/fase1/GRAFI_SENZA_GENERATORE.md` |
```

**C-paper4-REG-007** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 23, item 7

```
| 7 | Negative control of the deliverable's geometry: the randomised edges carried their new geographic distance as weight (`make_geo_sweep.py:49`, `weight = D[a, b] + 1`) with a kernel σ of their own (`models/gomo_sparse.py:149`); on the three preserved pairs the mean kernel was 0.23–0.36 for the randomised graphs against 0.20–0.48 for the kNN graphs, with randomised medians 0.04–0.26, and the three randomised graphs were not connected. Weights, topology and connectivity differed together: the control did not isolate the geometry | E11: both randomised graphs receive the multiset of G1's weights permuted over their edges, and connectivity is preserved (`protocol/paper4/E11.md`, Design, preflight 5 and 5-bis). Register only: no Paper 4 number depends on the deliverable's control | weight check on `geo_sweep/*_neg_rand_*.pkl` against the kNN pairs, 2026-11-06 | `protocol/paper4/E11.md` |
```

**C-paper4-REG-008** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 24, item 8

```
| 8 | Defect of the E11 frozen-record generator: the red-recall step indexed `p[:, nodes, :, 2]` in one step, which numpy reorders to (nodes, origins, horizons); the first run stopped with an IndexError (14 against 997) before writing any output | node and class selected in two steps (`red_recall` in `paper4/code/genera_congelamento_e11.py`, commit b2863c9); recall added to the self-test with origins ≠ nodes, and an end-to-end self-test on a synthetic copy of the campaign. No number was produced by the defective version | first run of the generator by the executor, 2026-11-06 | `paper4/congelamenti/CONGELAMENTO_E11.md`, deviations item 7 |
```

**C-paper4-REG-009** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 25, item 9

```
| 9 | First E11 node-set rule: on three Melbourne pairs (configuration × seed) the realised shares of observed, validation-hidden and test-hidden nodes fell outside ±15 points of the targets; the preflight reported 22 of 23 checks passed | cells assigned by deficit on the target shares 40/20/40, on the smallest grid G ≥ 6 with at least 20 occupied cells; geometry covariates registered with the node sets; preflight 4-bis passed on all 12 configurations × 5 seeds. Found and corrected before any training | E11 preflight, 2026-11-06 (commit e363bf7; correction 21db33d) | `protocol/paper4/E11.md`, Design and preflight 4-bis |
```

**C-paper4-REG-010** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 26, item 10

```
| 10 | The first E11 frozen record reported red recall at the 5% false-alarm threshold chosen on validation without the false-alarm rate realised on test, so a recall could be read as discrimination where the threshold was not met | the generator reports the realised rate next to every recall (commit 5cda9c3); record regenerated with every number identical to the previous one (`--compare-with`; 4e04ba7, 459b43ee3e649a31). The same rule holds in E9, E12, E12-bis and E12-ter | drafting of the E11 section, 2026-11-06 | `paper4/congelamenti/CONGELAMENTO_E11.md` |
```

**C-paper4-REG-011** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 27, item 11

```
| 11 | The first two isolated cost measurements of G1-rand(deg) in E9 ran during Spotlight indexing (load average 36–62) and gave 303.8 s and 393.9 s against 159–179 s for G1 | arm re-measured alone with Spotlight idle (135.9 s), and G1 in the same conditions (168.5 s); the signature line reports these; the earlier figures stay in the manifest, unused | the executor, cost measurement, 2026-11-07 | `protocol/paper4/E9.md`, Deviations 1 |
```

**C-paper4-REG-012** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 28, item 12

```
| 12 | The first synthetic self-test of E12-bis populated only the 0–250 m bin, so its condition "beats the prior more strongly within 250 m than in the outer bins" was met vacuously | synthetic world widened (clusters across 20 km) and at least one outer bin required (`selftest` in `paper4/code/e12bis.py`); found and corrected before the preflight and the signature | drafting of the E12-bis code, 2026-11-08 | `paper4/code/e12bis.py` (27adfe03f24647e8) |
```

**C-paper4-REG-013** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 29, item 13

```
| 13 | The frozen E12 code (`e12.py`, 3ec453d15372b217) had no input check after the run and no end-to-end self-test of its frozen-record generator, which E9 and E11 had | both added outside the frozen file, in `paper4/code/verifica_e12.py` (e4b753bc52fdf7f5, commit ac545db), before the campaign; E12-bis and E12-ter carry them inside their own code | drafting of the E12 commands for the executor, 2026-11-08 | `paper4/code/verifica_e12.py` |
```

**C-paper4-REG-014** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 30, item 14

```
| 14 | The area under the curve on the Madrid arterials, 0.542 (Table 68, p. 132; text p. 131; Gini 0.084), and with it the 58% / 42% split of the arterial gap (p. 132), has no source: it is hard-coded at line 195 of `analisi/validazione_colocalizzata.py`, and no script, log or output in `OR3/` or `OLD/` contains it | recomputed in Part A from the 399 base pairs of `t4c_crossval.py`: median over pairs of the per-pair area under the curve (primary) and value on the pooled cells (secondary), with intervals; the split recomputed from them. Defect of the deliverable; no effect on the numbers of the paper, which are all regenerated | search of `OR3/` and `OLD/` while drafting P4A, 2026-11-08 | `protocol/paper4/P4A.md`, Design, step 0 |
```

**C-paper4-REG-015** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 31, item 15

```
| 15 | The rank correlation on the Madrid arterials is +0.001 in Table 68 (p. 132, hard-coded at line 195 of the same script) and +0.071 in the text of p. 131 and in the script's docstring: two values for the same quantity, neither computed | recomputed in Part A in the same two ways as item 14; both deliverable values reported next to the recomputed ones. Defect of the deliverable; no effect on the numbers of the paper | reading of Table 68 against the text, 2026-11-08 | `protocol/paper4/P4A.md`, Design, step 0 |
```

**C-paper4-REG-016** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 32, item 16

```
| 16 | The Austin volume–occupancy rank correlations at lane and at section level, +0.7241 and +0.2999 (text p. 133), have no generator: no line of `analisi/validazione_colocalizzata.py` computes them | recomputed in Part A from the Austin data with a declared definition (sections with at least 3 lanes, after the script's filters). Defect of the deliverable; no effect on the numbers of the paper | reading of the script against the text, 2026-11-08 | `protocol/paper4/P4A.md`, Design, step 0 |
```

**C-paper4-REG-017** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 33, item 17

```
| 17 | The within-lane area under the curve in Austin, "0,990, con intervallo [0,959; 0,999]" (text p. 131), presents as an interval the interquartile range across lanes printed by the script; the brackets of Table 69 are also interquartile ranges | reported in Part A as interquartile ranges, with the bootstrap interval over sections next to them (correction 2). Defect of the deliverable; no effect on the numbers of the paper | reading of `sez_austin` against the text, 2026-11-08 | `protocol/paper4/P4A.md`, Correction 2 |
```

**C-paper4-REG-018** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 34, item 18

```
| 18 | Table 67, measured class green: the deliverable counts 2,989,877 cells and a rank correlation of +0.033; the regenerated table counts 3,432,842 and +0.012, and its three classes sum to the 4,199,040 non-imputed cells while the deliverable's do not. The overall rank correlation is +0.255 printed against +0.249 regenerated. The other rows of Table 67 are identical | cause (executor, 2026-11-08): the deliverable's green class was 0.8 ≤ r_tr < 1.5. The 442,965 cells it misses are exactly those whose measured factor is clipped at 1.5 (`carica_m30`); with that class the conserved module gives 2,989,877 cells and +0.0326. The conserved code has 1.6 (`validazione_colocalizzata.py`, line 117) in its only commit (dc8b6bb, 2026-09-17), so the version that printed the table is not conserved. The overall +0.255 is reproduced neither by that class nor by six other cell sets (+0.249 to +0.480): generator not found. Defect of the deliverable; no effect on the numbers of the paper | comparison in `CONGELAMENTO_4A.md`; causes in `CAUSE_4A.md` (03fd226), 2026-11-08 | `paper4/congelamenti/CONGELAMENTO_4A.md`, comparison and dated note; `protocol/paper4/fase2/CAUSE_4A.md` |
```

**C-paper4-REG-019** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 35, item 19

```
| 19 | Table 68, neighbour bands: rank correlation, area under the curve and Gini differ from the deliverable by 0.001–0.009; median distances identical (14 / 31 / 31 / 96 m). Regenerated sensors per band: 191 / 181 / 156 / 165 | cause (executor, 2026-11-08): the deliverable's table does not print sensors per band; the filter of `p4a.py` is the conserved one (`sez_accoppiamento`, lines 176–178), so the counts are those of that filter. Not caused by the coordinate file (`traffic_sensors.csv` and `traffic_sensors_lug2026.csv` give the same rows). No variant of the cell filter reproduces the differences: without the imputation filter on the loop and with a positive loop speed the values are identical to ours; the nearest neighbour and the exclusion of the clipped cells of item 18 move further away. Not found; version not conserved. Defect of the deliverable; no effect on the numbers of the paper | comparison in `CONGELAMENTO_4A.md`; causes in `CAUSE_4A.md` (03fd226), 2026-11-08 | `paper4/congelamenti/CONGELAMENTO_4A.md`, comparison and dated note; `protocol/paper4/fase2/CAUSE_4A.md` |
```

**C-paper4-REG-020** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 36, item 20

```
| 20 | Austin sections: the brief counts 31; after the script's filters there are 40 (10 with one lane, 30 with at least 2: 22 / 6 / 2, as in Table 69); correction 3 uses 29. The deliverable states a lane–AUC rank correlation of −0.541 (p = 0.002) over 31 sections and excludes one section for a prevalence difference of −45.1 points. The prevalence differences of 3 and 4 lanes are +18.62 and +9.88 points, against +18.35 and +9.93 printed | cause (executor, 2026-11-08): the 40 sections are `intname|direction` after excluding the three intersections without direction. The only definition that gives 31 is "sections with a defined area under the curve (more than 20 congested and more than 20 non-congested cells), whatever the number of lanes": the 29 plus 2 with one lane. The section that leaves correction 3 is `LAMARZENNIA|SB`: 2 lanes, 43,081 aggregated cells, 11 with a congested lane, so its area under the curve is undefined. The −0.541 is not reproduced (−0.269, p = 0.144, over those 31; −0.441, p = 0.017, over the 29), and no conserved script computes it. The section at −45.1 points does not exist under the conserved code: every prevalence difference is ≥ 0 by construction (maximum +52.0, `BurnetRutland|SB`). Generator not found for either; the two prevalence differences are not traced. Defect of the deliverable; no effect on the numbers of the paper | comparison in `CONGELAMENTO_4A.md` and preflight count; causes in `CAUSE_4A.md` (03fd226), 2026-11-08 | `paper4/congelamenti/CONGELAMENTO_4A.md`, comparison and dated note; `protocol/paper4/fase2/CAUSE_4A.md`; `protocol/paper4/P4A.md`, Correction 3 |
```

**C-paper4-REG-021** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 37, item 21

```
| 21 | Model states are not saved: the frozen training code (`paper4/code/p4b.py`, `train`) keeps the states at the checkpoints in memory for validation-based selection and writes only per-cell predictions; no file of model weights exists in `paper4/runs/` | declared design choice: every number regenerates from the per-cell predictions; re-evaluating the models on other data requires retraining (180 + 240 trainings, about 7.5 h on the Mac M3, from the isolated costs of `E9.md`, at most 6.6 h, and `E11.md`, about 0.9 h). No effect on the numbers of the paper; stated in §VI (Reproducibility) and in Data and Code Availability | internal review of the Zenodo partition, 2026-11-08 | `paper4/code/p4b.py` (`train`); `protocol/paper4/zenodo/RIPARTIZIONE_RUNS.md` (c9222f224441b6b2); `protocol/paper4/E9.md`, `protocol/paper4/E11.md` (costs) |
```

**C-paper4-REG-022** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 38, item 22

```
| 22 | Asymmetric fallback in E12-ter: when a row of the table with the neighbour had fewer than 20 pairs, it fell back to the E12-bis row, which has no calendar, while the calendar-only table kept the calendar; 6–66% of the lookups fell back overall, at most 9.8% within 250 m, so the losses of E12-ter beyond 250 m mixed the neighbour's class with the loss of the calendar | measured by E12-quater (pre-registered, fallback to the calendar-only row, so that the two tables differ only where the neighbour is used): D′ − D is −0.03 to +0.40 points within 250 m in Madrid and London and up to +20.8 beyond (London, 10%, 500–1,000 m); D′ stays negative at 250–500 m in Madrid and London (−4.7 to −12.3). The frozen record of E12-ter is unchanged; the paper reports D′ in §III-C and Table II | the analysis of the E12-ter fallbacks in the draft and the internal review of 2026-11-08 (21:45); measured 2026-11-09 | `protocol/paper4/E12quater.md`; `paper4/congelamenti/CONGELAMENTO_E12quater.md` (21fc58f, 971f0bdb951b17f1) |
```

**C-paper4-REG-023** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 39, item 23

```
| 23 | E10-pred scored each placement with the class weights of its own configuration (`paper4/code/e10pred.py`, `cell_for`, line 337: `node_sums(p, y, keep, rec["class_weights"])`), computed from that design's observed segments; on the segments hidden under both placements, Δ therefore mixed the change of predictions with a change of the scoring function (Melbourne, seed 0: (0.455, 1.544, 6.552) uniform against (0.474, 1.450, 4.969) blocks). V(G1) within one design is not affected | E10-pred-bis (pre-registered) rescores both placements from the saved predictions with one weight vector per city, from the training period of all its segments; with the design weights its code reproduces the frozen record of E10-pred to the bit. With common weights Δ G0 is +0.15 / −0.16 / +5.10 in Madrid, London and Melbourne (E10-pred: +0.01 / −0.29 / +2.78) and Δ G1 +0.07 / −0.31 / +3.79 (+1.05 in Melbourne); in Melbourne the reading of Δ G0 becomes "uniform placement forecasts the common segments better", +5.10 [+3.10; +6.37]. The frozen record of E10-pred is unchanged; the paper reports E10-pred-bis in §III-D and Table V | internal review of 2026-11-09 (15:15, item 1) | `protocol/paper4/E10predbis.md`; `paper4/congelamenti/CONGELAMENTO_E10predbis.md` (e9ce6c2, 30ef7b7182aadede) |
```

**C-paper4-REG-024** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 40, item 24

```
| 24 | §VI (Limits) recalled protocols and controls without a provenance list of the files it relies on, so the correspondence between the limits stated in the paper and the versioned documents could not be checked from the manuscript alone | `protocol/paper4/fase2/LIMITI_FONTI.json`: 14 files with last-change commit, blob, SHA-256 and the block of §VI each one supports; for P4A the signed text (`b633f53`) and the archived version with the dated deviation (`e53d3cb`) are distinguished; `REGISTRO_CORREZIONI.md` is recorded as an audit-only snapshot. At the tag, the files are checked for presence and identity against the archive. No number of the paper is affected | internal review of §VI, 2026-11-10 | `protocol/paper4/fase2/LIMITI_FONTI.json` |
```

**C-paper4-REG-025** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 41, item 25

```
| 25 | The public repository tracked the whole MoGERNN code (`evoluzione/MoGERNN-main/`, 38 files including a pre-trained model), third-party code whose upstream repository declares no licence. No number of Paper 4 depends on it (`paper4/` and `protocol/paper4/` never reference it; the Zenodo code archive is limited to those paths) | Removed from tracking on `paper4` and `main` (commits ef7f6d6 / 06e48d6, 2026-11-10) with a `.gitignore` rule and `evoluzione/MoGERNN-main/ORIGINE.md` (upstream URL, commit e80f6ca, SHA-256 of reference files, identical to the local copy); `LICENSE` CC BY 4.0 added (1715e8f / 3a07da8), the licence of the Zenodo records. Both commits follow the tag `paper4-freeze-20261110a` and touch neither `paper4/` nor `protocol/paper4/`. History and earlier tags keep the files; no rewrite. No number affected | internal review, 2026-11-10 | `evoluzione/MoGERNN-main/ORIGINE.md`; `LICENSE`; register of Paper 1, item 32 |
```

**C-paper4-REG-026** · `protocol/paper4/REGISTRO_CORREZIONI.md` · line 42, item 26

```
| 26 | Item 23 and `protocol/paper4/E10predbis.md` (r. 8) date the internal review that found the scoring defect at "2026-11-09, 15:15"; the correction was drafted at 14:58 (commit 89a0cb7) and signed at 15:01 (b489ff9), before that time. The review message is of 2026-11-09 14:38; 15:15 is the time at which the observation was forwarded for assessment, not the time of the review. Found by reconstructing the sequence from commit timestamps | the signed protocol is not modified; the time is corrected here. No number affected | reconstruction of the incident sequence, 2026-11-10 | `protocol/processo/incidenti/I2.md` (branch `main`); commits 89a0cb7, b489ff9, e9ce6c2 |
```


## `paper4` — report flag

**C-paper4-RPT-001** · `paper4/analysis/reports/20261110T084415Z.md` · line 167

```
- projects: FAIL
```

