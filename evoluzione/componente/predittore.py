#!/usr/bin/env python3
"""
Predittore per-nodo: componente temporale di Graph WaveNet, senza scambio spaziale.
===================================================================================
«Per-nodo» significa previsione SENZA scambio fra sensori, non un modello
addestrato separatamente per ciascuno: i pesi sono condivisi da tutti.

    finestra dinamica + calendario
              |
      encoder temporale condiviso      convoluzioni causali dilatate, a cancelli
              |
      fusione con identita' osservabile e ramo statico
              |
      quattro teste per orizzonte, tre logit ciascuna

IPERPARAMETRI, ripresi dalla configurazione EFFETTIVA di `gomo_classify.py` e non
dal nome del modello:

    finestra dinamica     12 passi, tre ore
    canali d'ingresso     8, con `no_ha = True`: niente profilo storico settimanale
    nucleo temporale      2, dilatazioni 1, 2, 4, 8
    canali nascosti       32
    blocchi               4
    normalizzazione       BatchNorm2d sul residuo, statistiche mobili

CAMPO RICETTIVO. Con una convoluzione di nucleo 2 per ciascuna dilatazione — le due
convoluzioni del cancello sono PARALLELE, non seriali —

    R = 1 + (2-1)(1 + 2 + 4 + 8) = 16 posizioni

su una finestra di 12. L'imbottitura e' CAUSALE a sinistra, sicche' nessuna
posizione vede il futuro; **anche l'ultima posizione puo' dipendere da quattro
posizioni di imbottitura**, non solo le prime. La storia realmente osservata e' di
dodici passi.

LA MEDIA STORICA PER NODO E' ESCLUSA. Un sensore appena installato con ventiquattro
ore di osservazioni non ha un profilo settimanale consolidato, e fornirglielo dal
periodo anteriore all'installazione violerebbe il protocollo. L'esclusione vale
anche per la futura variante con grafo: la reintroduzione sara' un'ablazione
separata.

LA BATCHNORM RESTA, con lo stato congelato in esercizio. In addestramento aggiorna
le statistiche sui soli dati ammessi; in validazione, prova e inserimento si usa
`model.eval()`. **Durante l'addestramento introduce un accoppiamento fra sensori
attraverso le statistiche del lotto**, pur non scambiando messaggi: va dichiarato.

NESSUN PARAMETRO SPECIFICO PER SENSORE. Aggiungere sensori non cambia il conteggio.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from evoluzione.componente.encoder import NASCOSTE, USCITA, costruisci_torch

# I CANALI DIPENDONO DALLA SORGENTE ed entrano nel tensore in quest'ordine.
#
# SU TRAFFIC4CAST SONO NOVE: due dinamici, le loro due maschere, cinque di
# calendario. L'occupazione e' ASSENTE dalla sorgente — non mancante — sicche'
# conservarla per uniformita' con GO-MO darebbe al modello due ingressi costanti,
# il valore e la sua maschera.
#
# LE MASCHERE SI COSTRUISCONO PRIMA DEL RIEMPIMENTO. Valgono 1 dove
# l'osservazione e' valida e disponibile all'istante della previsione, 0 dove
# manca, e' invalida o e' anteriore all'installazione. NON si standardizzano, e
# riguardano ESCLUSIVAMENTE la finestra passata: mai la disponibilita' del
# bersaglio futuro.
#
# Lo zero usato per l'assenza non deve contribuire alle statistiche come una
# classe osservata: e' la ragione per cui la maschera della classe di volume si
# ricostruisce dalla validita' della sorgente.
CANALI_T4C = ["r_riempito", "volume_class_riempito",
              "maschera_r", "maschera_volume_class",
              "ora_sin", "ora_cos", "giorno_sin", "giorno_cos", "festivo"]
CANALI_GOMO = ["r_riempito", "conteggio_norm", "occupazione_norm",
               "maschera_r", "maschera_conteggio", "maschera_occupazione",
               "ora_sin", "ora_cos", "giorno_sin", "giorno_cos", "festivo"]
# SU PEMS04 SONO UNDICI, come su GO-MO: velocita' relativa, flusso CONTINUO e
# occupazione, le loro tre maschere, cinque di calendario. La lista e' dichiarata
# a parte perche' la SORGENTE e' diversa — provenienza, risoluzione e riferimento
# di velocita' non coincidono — anche se la struttura e' la stessa.
CANALI_PEMS04 = ["r_riempito", "conteggio_norm", "occupazione_norm",
                 "maschera_r", "maschera_conteggio", "maschera_occupazione",
                 "ora_sin", "ora_cos", "giorno_sin", "giorno_cos", "festivo"]
CANALI_INGRESSO = CANALI_T4C          # il raccordo gira su Traffic4cast
FINESTRA = 12
NUCLEO = 2
DILATAZIONI = (1, 2, 4, 8)
NASCOSTI = 32
ORIZZONTI = (1, 2, 4, 8)          # passi: 15, 30, 60, 120 minuti
N_CLASSI = 3


def campo_ricettivo(nucleo=NUCLEO, dilatazioni=DILATAZIONI) -> int:
    """Posizioni da cui l'ultima uscita puo' dipendere.

    Vale per convoluzioni a cancello con i due rami PARALLELI: se fossero seriali
    ciascun blocco contribuirebbe il doppio.
    """
    return 1 + (nucleo - 1) * sum(dilatazioni)


class GTCN(nn.Module):
    """Convoluzione temporale causale dilatata, a cancelli.

    `f` e `g` sono paralleli: il ramo di trasformazione e quello di controllo
    vedono lo stesso ingresso imbottito.
    """

    def __init__(self, c, k, d):
        super().__init__()
        self.pad = (k - 1) * d
        self.f = nn.Conv2d(c, c, (1, k), dilation=(1, d))
        self.g = nn.Conv2d(c, c, (1, k), dilation=(1, d))

    def forward(self, x):
        # imbottitura a SINISTRA soltanto: nessuna posizione vede il futuro
        x = F.pad(x, (self.pad, 0))
        return torch.tanh(self.f(x)) * torch.sigmoid(self.g(x))


class Blocco(nn.Module):
    """Convoluzione temporale, derivazione per lo scarto, residuo normalizzato.

    Senza ramo di scambio spaziale: e' la differenza rispetto al backbone con
    grafo, e l'unica.
    """

    def __init__(self, c, d):
        super().__init__()
        self.tcn = GTCN(c, NUCLEO, d)
        self.skip = nn.Conv2d(c, c, (1, 1))
        self.bn = nn.BatchNorm2d(c, track_running_stats=True)

    def forward(self, x):
        res = x
        x = self.tcn(x)
        s = self.skip(x)
        # NOTA sul backbone storico: dopo l'ultimo blocco si usa il solo `skip`,
        # sicche' l'uscita normalizzata dell'ULTIMO blocco viene scartata e i
        # suoi due parametri non ricevono gradiente. Sono 64 su 26.244. Le sue
        # statistiche correnti si aggiornano comunque, perche' il passaggio in
        # avanti avviene: buffer vivi, pesi morti. Si conserva com'e', perche'
        # il collegamento con `gwn_none` e' la ragione della scelta.
        return self.bn(x + res), s


class PredittorePerNodo(nn.Module):
    def __init__(self, d_descrittore: int, d_statiche: int,
                 sorgente: str = "traffic4cast",
                 c_in: int | None = None, nascosti: int = NASCOSTI,
                 dilatazioni=DILATAZIONI, n_orizzonti: int = len(ORIZZONTI),
                 n_classi: int = N_CLASSI, d_statiche_uscita: int = 8,
                 identita=None):
        """`identita` e' un FornitoreIdentita; assente, si costruisce
        l'encoder osservabile — **lo stesso fornitore esplicito**, non una forma
        diversa.

        **L'ORDINE DI COSTRUZIONE E' QUELLO STORICO**: `start`, `blocchi`,
        identita', `stat`, `e1`, `e2`. Il fornitore ha dimensioni diverse fra i
        bracci, sicche' `stat`, `e1` ed `e2` ricevono estrazioni diverse: **e'
        l'ARTEFATTO CANONICO a uniformarli**, ed e' il meccanismo unico e
        verificabile prescritto dal protocollo.

        Costruire l'identita' per ultima preverrebbe il disallineamento
        all'origine, ma renderebbe i quarantacinque stati iniziali gia' salvati
        non piu' riproducibili da questo codice: sono registrazioni di cio' che
        e' stato eseguito, e la loro riproducibilita' e' verificata da
        `collauda_appaiamento.py`."""
        super().__init__()
        CANALI = {"traffic4cast": CANALI_T4C, "gomo": CANALI_GOMO,
                  "pems04": CANALI_PEMS04}
        if sorgente not in CANALI:
            raise ValueError(f"sorgente ignota: {sorgente}")
        self.sorgente = sorgente
        self.canali = CANALI[sorgente]
        c_in = len(self.canali) if c_in is None else c_in
        self.d_descrittore, self.d_statiche = d_descrittore, d_statiche
        self.n_orizzonti, self.n_classi = n_orizzonti, n_classi
        self.start = nn.Conv2d(c_in, nascosti, (1, 1))
        self.blocchi = nn.ModuleList([Blocco(nascosti, d) for d in dilatazioni])
        # L'IDENTITA', separata dal backbone. **UNA SOLA FORMA CANONICA**: il
        # fornitore c'e' sempre, e il valore predefinito costruisce lo stesso
        # fornitore esplicito e lo stesso albero dei moduli.
        #
        # La compatibilita' storica vive nel CARICATORE degli artefatti
        # (`migra_chiavi.py`), non qui: due forme per lo stesso modello sono
        # l'ambiguita' che poi produce difetti.
        from evoluzione.componente.identita import ObservableIdentityEncoder
        self.identita = (identita if identita is not None
                         else ObservableIdentityEncoder(d_descrittore, NASCOSTE))

        # l'anagrafica: ramo SEPARATO, comune alle strategie
        self.stat = nn.Linear(d_statiche, d_statiche_uscita)
        d_fuso = nascosti + USCITA + d_statiche_uscita
        self.e1 = nn.Conv2d(d_fuso, nascosti, (1, 1))
        self.e2 = nn.Conv2d(nascosti, n_orizzonti * n_classi, (1, 1))

    def forward(self, dynamic_inputs, *, node_ids, descriptor=None,
                static_inputs=None):
        """`dynamic_inputs` (B, C_IN, K, T); il resto SOLO per nome.

        **`node_ids` e' obbligatorio per tutti i fornitori**, come metadato di
        allineamento: non diventa per questo un'informazione appresa.

            ObservableIdentityEncoder   richiede `descriptor`, ne verifica
                                        dimensione e corrispondenza con i nodi
            LearnedNodeEmbedding        usa `node_ids`; RIFIUTA un descrittore
            AdaptedNodeEmbedding        usa `node_ids`; verifica l'appartenenza
            NoIdentity                  non usa gli identificativi come
                                        caratteristiche; RIFIUTA un descrittore

        Restituisce (B, K, orizzonti, classi).
        """
        x = dynamic_inputs
        statiche = static_inputs
        if statiche is None:
            raise ValueError("`static_inputs` e' obbligatorio")
        B, _, K, _ = x.shape
        h = self.start(x)
        skip = 0
        for b in self.blocchi:
            h, s = b(h)
            skip = skip + s[..., -1:]          # l'ultima posizione temporale
        skip = F.relu(skip)                    # (B, nascosti, K, 1)

        z = self.identita(B, K, node_ids=node_ids,
                          descriptor=descriptor)       # (B, 8, K, 1)
        a = F.relu(self.stat(statiche))
        if a.dim() == 2:
            a = a.unsqueeze(0).expand(B, -1, -1)
        a = a.permute(0, 2, 1).unsqueeze(-1)                  # (B, 8, K, 1)

        fuso = torch.cat([skip, z, a], dim=1)
        out = self.e2(F.relu(self.e1(fuso)))                  # (B, H*C, K, 1)
        return (out.squeeze(-1)
                .view(B, self.n_orizzonti, self.n_classi, K)
                .permute(0, 3, 1, 2))                         # (B, K, H, C)

    # -- descrizione, da registrare ----------------------------------------
    def descrizione(self) -> dict:
        per_nodo = [{"nome": n, "forma": list(p.shape)}
                    for n, p in self.named_parameters()
                    if p.dim() and p.shape[0] not in (self.d_descrittore,
                                                      self.d_statiche)]
        return {
            "canali_ingresso": self.canali,
            "n_canali_ingresso": len(self.canali),
            "sorgente": self.sorgente,
            "profilo_storico_settimanale": False,
            "finestra": FINESTRA,
            "nucleo": NUCLEO,
            "dilatazioni": list(DILATAZIONI),
            "campo_ricettivo": campo_ricettivo(),
            "imbottitura": "causale a sinistra",
            "storia_osservata": FINESTRA,
            "nascosti": NASCOSTI,
            "blocchi": len(self.blocchi),
            "normalizzazione": "BatchNorm2d, track_running_stats=True",
            "d_descrittore": self.d_descrittore,
            "d_statiche": self.d_statiche,
            "orizzonti": list(ORIZZONTI),
            "classi": self.n_classi,
            "parametri_totali": sum(p.numel() for p in self.parameters()),
            "parametri_identita": sum(p.numel()
                                      for p in self.identita.parameters()),
            "identita": (self.identita.descrizione()
                         if self.identita is not None
                         else {"tipo": "ObservableIdentityEncoder",
                               "moduli_autorizzati": [],
                               "parametri_per_nodo": 0}),
            "buffer": [n for n, _ in self.named_buffers()],
            "parametri_senza_gradiente": [
                f"blocchi.{len(self.blocchi)-1}.bn.weight",
                f"blocchi.{len(self.blocchi)-1}.bn.bias"],
            "nota_ultimo_blocco": (
                "l'uscita normalizzata dell'ultimo blocco e' scartata dal "
                "backbone storico: i suoi due parametri non si addestrano, "
                "mentre le sue statistiche correnti si aggiornano"),
        }
