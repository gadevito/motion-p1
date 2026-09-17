#!/usr/bin/env python3
"""
Costruzione del rapporto di congestione, con validita' PRIMA del troncamento.
==============================================================================
Sostituisce l'ordine difettoso di `t4c22_adapter.py`:

    r = np.clip(speed / ff[None, :], 0, 1.5)      # troncamento
    cls = ...; v = np.isfinite(r)                  # validita', troppo tardi

CHE COSA ANDAVA STORTO, nei tre casi distinti.

  * riferimento NULLO: la divisione produce infinito, il troncamento lo porta a
    1,5 e il controllo di finitezza lo trova valido. La cella riceve la classe
    libera.
  * riferimento NEGATIVO: il rapporto risulta negativo e il TRONCAMENTO lo porta
    a zero. La cella riceve la classe critica.
  * riferimento POSITIVO INFINITO: una velocita' finita divisa per infinito
    produce gia' zero, PRIMA del troncamento. La cella riceve comunque la classe
    critica, ma per una ragione diversa dalla precedente.
  * velocita' INFINITA con riferimento valido: il rapporto e' infinito e il
    troncamento lo rende finito.

Il primo e il quarto producono la classe libera, il secondo e il terzo quella
critica. L'errore puo' essere amplificato dalla pesatura della classe critica,
secondo i pesi specifici del contesto.

LA VELOCITA' ZERO NON VA ESCLUSA. Puo' rappresentare traffico fermo, secondo la
semantica della sorgente: e' un valore legittimo che produce rapporto zero e classe
critica, ed e' corretto cosi'.

L'ORDINE CORRETTO. Si validano gli operandi, si divide solo dove sono validi, si
verifica che il rapporto sia finito, e solo allora si tronca. La maschera resta
esplicita e accompagna il risultato: una cella non valida non e' una cella con
rapporto zero.
"""
from __future__ import annotations

import numpy as np

# soglie di classe: r < 0,4 critica; 0,4 <= r < 0,8 intermedia; r >= 0,8 libera
SOGLIA_CRITICA, SOGLIA_LIBERA = 0.40, 0.80
TRONCAMENTO = (0.0, 1.5)
# IL TIPO IN CUI SI VALUTANO LE SOGLIE FA PARTE DELLA DEFINIZIONE DEL BERSAGLIO.
# Il rapporto coincide fra precisione singola e doppia, ma il confronto con 0,4 e
# 0,8 cade da parti opposte in alcune celle prossime alle soglie: sui tre contesti
# primari sono 2.331, 3.946 e 108, ossia 0,248, 0,415 e 0,0175 per mille. Si
# conserva la precisione SINGOLA della pipeline originaria, perche' e' cio' che
# definisce le classi degli esperimenti gia' svolti.
TIPO_SOGLIE = "float32"
CLASSE_NON_VALIDA = 0


def costruisci_rapporto(speed, ff, troncamento=TRONCAMENTO):
    """(r, valid) — il rapporto e la maschera di validita'.

    `speed` ha forma (T, S), `ff` forma (S,). Le celle non valide valgono `nan`
    in `r` e `False` in `valid`: NON zero, che sarebbe indistinguibile da un
    rapporto legittimamente nullo.
    """
    speed = np.asarray(speed, dtype="float64")
    ff = np.asarray(ff, dtype="float64")
    # il riferimento e' valido se finito e POSITIVO: uno zero rende il rapporto
    # infinito, un negativo lo rende negativo e il troncamento lo porterebbe a
    # zero, cioe' alla classe critica
    ff_ok = np.isfinite(ff) & (ff > 0)
    # la velocita' zero e' ammessa: rappresenta traffico fermo
    sp_ok = np.isfinite(speed) & (speed >= 0)
    ingresso_ok = sp_ok & ff_ok[None, :]

    grezzo = np.full(speed.shape, np.nan, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        np.divide(speed, ff[None, :], out=grezzo, where=ingresso_ok)
    # il rapporto puo' non essere finito anche con operandi validi, per
    # traboccamento: si verifica DOPO la divisione e PRIMA del troncamento
    valid = ingresso_ok & np.isfinite(grezzo)

    r = np.full(speed.shape, np.nan, dtype="float64")
    r[valid] = np.clip(grezzo[valid], *troncamento)
    return r.astype(TIPO_SOGLIE), valid


def assegna_classi(r, valid):
    """Classi solo dove `valid`; altrove la classe convenzionale di non validita'."""
    cls = np.full(r.shape, CLASSE_NON_VALIDA, dtype="int64")
    cls[valid & (r < SOGLIA_CRITICA)] = 3
    cls[valid & (r >= SOGLIA_CRITICA) & (r < SOGLIA_LIBERA)] = 2
    cls[valid & (r >= SOGLIA_LIBERA)] = 1
    return cls


def costruisci(speed, ff, troncamento=TRONCAMENTO):
    """Rapporto, maschera e classi in un passaggio."""
    r, valid = costruisci_rapporto(speed, ff, troncamento)
    return r, valid, assegna_classi(r, valid)


# ---------------------------------------------------------------------------
def costruisci_vecchio(speed, ff, troncamento=TRONCAMENTO):
    """L'implementazione ORIGINARIA, riprodotta per il confronto di non
    regressione. Non va usata in produzione: e' qui perche' il confronto deve
    essere fra due funzioni, non fra una funzione e un ricordo del codice."""
    speed = np.asarray(speed, dtype="float64")
    ff = np.asarray(ff, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        r = np.clip(speed / ff[None, :], *troncamento).astype(TIPO_SOGLIE)
    valid = np.isfinite(r)
    cls = np.full(r.shape, CLASSE_NON_VALIDA, dtype="int64")
    cls[valid & (r < SOGLIA_CRITICA)] = 3
    cls[valid & (r >= SOGLIA_CRITICA) & (r < SOGLIA_LIBERA)] = 2
    cls[valid & (r >= SOGLIA_LIBERA)] = 1
    return r, valid, cls
