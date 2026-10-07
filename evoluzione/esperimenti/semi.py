#!/usr/bin/env python3
"""
I semi della campagna, in un modulo che non importa nulla.
==========================================================
Vivono qui perche' orchestratore, preparazione degli stati e audit ne hanno
bisogno, e farli importare l'uno dall'altro chiuderebbe un ciclo.

I SEMI DICHIARATI NON SONO QUELLI PASSATI A `torch.manual_seed`. L'orchestratore
semina un generatore numpy con `SEME_INIZIALIZZAZIONE[s]` e ne ESTRAE il seme di
torch, sicche' 7, 18 e 29 diventano 2.029.167.940, 1.918.988.776 e 2.007.055.255.

**Derivarli, e non copiarli**, impedisce che una modifica dell'orchestratore li
disallinei in silenzio — che e' esattamente cio' che stava per accadere.
"""
import numpy as np

PARTIZIONI = (0, 1, 2)
INIZIALIZZAZIONI = (0, 1, 2)
SEME_PARTIZIONE = {p: 1000 + 37 * p for p in PARTIZIONI}
# E6 parte B (PEMS08): sei partizioni da sei semi, STESSA formula; dizionario a
# parte perche' le campagne delle citta' e di PEMS04 restano a tre partizioni.
PARTIZIONI_E6 = (0, 1, 2, 3, 4, 5)
SEME_PARTIZIONE_E6 = {p: 1000 + 37 * p for p in PARTIZIONI_E6}
SEME_INIZIALIZZAZIONE = {s: 7 + 11 * s for s in INIZIALIZZAZIONI}

SEMI_DICHIARATI = tuple(SEME_INIZIALIZZAZIONE[s]
                        for s in sorted(INIZIALIZZAZIONI))

# ---------------------------------------------------------------- CONFERMA --
# Addendum 2: DODICI inizializzazioni nuove, 101..112, mai usate per valutazioni
# predittive. La sequenza consecutiva e' ammissibile: non serve cercare numeri
# apparentemente piu' casuali.
#
# NOTA: il valore 101 e' gia' stato usato come seme di PARTIZIONE nelle prove
# tecniche, che non producevano valutazioni predittive della campagna. Qui e' un
# seme di INIZIALIZZAZIONE, e i due ruoli non si toccano.
INIZIALIZZAZIONI_CONFERMA = tuple(range(12))
SEME_INIZIALIZZAZIONE_CONFERMA = {s: 101 + s for s in INIZIALIZZAZIONI_CONFERMA}
SEMI_DICHIARATI_CONFERMA = tuple(
    SEME_INIZIALIZZAZIONE_CONFERMA[s] for s in INIZIALIZZAZIONI_CONFERMA)


def seme_torch(seme_dichiarato: int) -> int:
    """Il seme che l'orchestratore passa a `torch.manual_seed`."""
    return int(np.random.default_rng(seme_dichiarato).integers(0, 2 ** 31 - 1))


# --------------------------------------------------------- INSERIMENTO -----
# Esperimento principale: DODICI inizializzazioni nuove, 201..212. Non si usano
# ne' i tre semi di sviluppo (7, 18, 29) ne' i dodici della conferma (101..112):
# quelli hanno gia' prodotto valutazioni predittive.
INIZIALIZZAZIONI_INSERIMENTO = tuple(range(12))
SEME_INIZIALIZZAZIONE_INSERIMENTO = {s: 201 + s
                                     for s in INIZIALIZZAZIONI_INSERIMENTO}
SEMI_DICHIARATI_INSERIMENTO = tuple(
    SEME_INIZIALIZZAZIONE_INSERIMENTO[s] for s in INIZIALIZZAZIONI_INSERIMENTO)

# ------------------------------------------------- PROVA DI ADEGUATEZZA -----
# Tre inizializzazioni per la prova del budget, su UNA partizione (seme 1000).
# 301, 302, 303: mai usati per selezioni predittive.
INIZIALIZZAZIONI_ADEGUATEZZA = (0, 1, 2)
SEME_INIZIALIZZAZIONE_ADEGUATEZZA = {s: 301 + s
                                     for s in INIZIALIZZAZIONI_ADEGUATEZZA}
SEMI_DICHIARATI_ADEGUATEZZA = tuple(
    SEME_INIZIALIZZAZIONE_ADEGUATEZZA[s] for s in INIZIALIZZAZIONI_ADEGUATEZZA)

SEMI_TORCH = tuple(seme_torch(s) for s in SEMI_DICHIARATI)
SEMI_TORCH_CONFERMA = tuple(seme_torch(s) for s in SEMI_DICHIARATI_CONFERMA)
SEMI_TORCH_INSERIMENTO = tuple(seme_torch(s)
                               for s in SEMI_DICHIARATI_INSERIMENTO)
SEMI_TORCH_ADEGUATEZZA = tuple(seme_torch(s)
                               for s in SEMI_DICHIARATI_ADEGUATEZZA)


def configurazione(conferma: bool = False, inserimento: bool = False,
                   adeguatezza: bool = False):
    """(inizializzazioni, semi dichiarati, semi di torch) per la campagna."""
    if sum((conferma, inserimento, adeguatezza)) > 1:
        raise ValueError("le campagne si escludono a vicenda")
    if adeguatezza:
        return (INIZIALIZZAZIONI_ADEGUATEZZA, SEMI_DICHIARATI_ADEGUATEZZA,
                SEMI_TORCH_ADEGUATEZZA)
    if inserimento:
        return (INIZIALIZZAZIONI_INSERIMENTO, SEMI_DICHIARATI_INSERIMENTO,
                SEMI_TORCH_INSERIMENTO)
    if conferma:
        return (INIZIALIZZAZIONI_CONFERMA, SEMI_DICHIARATI_CONFERMA,
                SEMI_TORCH_CONFERMA)
    return INIZIALIZZAZIONI, SEMI_DICHIARATI, SEMI_TORCH
