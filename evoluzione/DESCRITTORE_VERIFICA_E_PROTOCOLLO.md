# Descrittore in addestramento: verifica, e protocollo del confronto

**Primo deliverable.** Nessun addestramento eseguito.

---

## A. Che descrittore vedeva P durante l'addestramento

**Non era ricalcolato sulle ventiquattro ore precedenti ciascuna origine, né
fisso su un episodio di inserimento simulato.** Era **un'unica istantanea
riferita alla fine del periodo di addestramento**, applicata a tutte le origini.

`evoluzione/esperimenti/addestramento.py`:

| riga | |
|---|---|
| 602 | `t_desc_tr = int(ist["addestramento"][-1])` — **l'ultima origine del periodo** |
| 609 | `dtr = _descrittori(D, nodi_add, t_desc_tr, E.variante, NORM)` — calcolato **una volta** |
| 343, 352, 657 | `descriptor=dtr` — lo **stesso** tensore a ogni aggiornamento |
| 601, 610, 668 | per la validazione, `t_desc_va = ist["validazione"][0]`, ugualmente unico |

La finestra è `(t − 96, t]` in righe (`estrattore.py` riga 194), e la
diagnostica ha verificato che per questi istanti copre **ventiquattro ore
reali**.

### I timestamp che contribuivano

Per Madrid, `t_desc_tr` = 7318: il descrittore di addestramento riassume le
ventiquattro ore che precedono **la fine del periodo di addestramento**, cioè le
righe 7223–7318.

> **Conseguenza da registrare: per quasi tutte le origini di addestramento quel
> descrittore riassume osservazioni SUCCESSIVE all'origine.** Non è una
> contaminazione della valutazione — i bersagli di prova restano intatti — ma
> significa che in addestramento il descrittore non ha la relazione temporale
> che ha in esercizio.

### Differenza rispetto all'impiego

| | addestramento | fase 3, valutazione |
|---|---|---|
| quando | una volta, fine del periodo | una volta, a $t_1$ |
| rispetto all'origine | quasi sempre **successivo** | sempre **precedente** |
| durante l'uso | invariato | invariato per ~1.470 origini, fino a settimane |

**L'impiego con descrittore congelato differisce dalla modalità di
addestramento**, e differisce in una direzione che l'addestramento non ha mai
mostrato al modello: un descrittore sempre più vecchio dell'origine.

---

## B. Protocollo del confronto, prima di eseguire

### Perimetro

**Tutti i punti di controllo di P della fase 3**, 108, senza selezione in base
ai risultati. Nessun nuovo addestramento.

| variante | pesi | descrittore |
|---|---|---|
| **P-frozen** | congelati | prime 24 ore da $t_0$, poi invariato |
| **P-refresh** | congelati | ultime 24 ore disponibili, **ricalcolato a ogni origine** |

La finestra di P-refresh è $(t - 24\text{h},\, t] \cap (t_0,\, t]$, sulla
griglia reale: nessuna riga anteriore a $t_0 + 1$, nessuna osservazione
successiva a $t$, nessun giorno compresso.

### Che cosa resta identico

Nodi, istanti, bersagli, ingressi dinamici, calendario, statiche,
normalizzazione, pesi delle classi, regole decisionali. **Non si aggiornano
pesi, buffer o parametri di normalizzazione**: soltanto il descrittore.

### Controlli bloccanti, prima dei risultati

1. **P-frozen riproduce le predizioni della fase 3** entro $10^{-6}$ relativo.
2. Alla fine delle prime ventiquattro ore i due descrittori **coincidono**.
3. Nessuna osservazione successiva a $t$ o anteriore a $t_0 + 1$ entra nel
   descrittore.
4. Le finestre non attraversano salti della griglia; dove la finestra reale è
   incompleta, la copertura si riporta e non si comprime.
5. Lo stato completo del modello è **invariato** dopo l'inferenza.
6. Le chiavi delle predizioni coincidono fra le due varianti **e con C**.

### Risultati da riportare, per città

- differenza appaiata **P-refresh − P-frozen** e **P-refresh − C**, con
  ricampionamento incrociato su semi e partizioni;
- perdite assolute, wCE e **average precision**;
- andamento delle differenze nel tempo dall'inserimento, sulle **fasce già
  definite** nella fase 3; ogni suddivisione ulteriore è dichiarata
  esplorativa;
- **copertura delle finestre** e disponibilità delle bande;
- **costo di aggiornamento del descrittore**, per origine e cumulato.

### Natura

**Analisi post-hoc**, motivata dalla perdita di vantaggio nel tempo. Non
sostituisce il risultato della fase 3 e non dimostra in anticipo che la causa
sia l'invecchiamento del descrittore. Se P-refresh migliora, resta
un'**ipotesi da confermare su dati non usati per formularla**. Se non migliora,
si registra anche questo.

**F, R, architettura e iperparametri non si toccano.**
