#!/usr/bin/env python3
"""
Fornitori di identita': il meccanismo separato dal backbone.
=============================================================
Tutti restituiscono un vettore a OTTO dimensioni con la medesima semantica di
interfaccia, sicche' il backbone resta uno solo e le differenze fra strategie
restano visibili nei moduli e nei manifesti, **anziche' nascoste in condizioni
interne**.

    NoIdentity                 C — nessuna identita' specifica
    ObservableIdentityEncoder  P — descrittore calcolato, encoder condiviso
    LearnedNodeEmbedding       E, A, R — tabella appresa, una riga per nodo
    AdaptedNodeEmbedding       F — tabella iniziale CONGELATA, tabella nuova
                                   adattabile, fisicamente separate

IL CONTRATTO DEI PARAMETRI PER NODO, distinto per strategia:

    C, P    nessuno
    E       embedding dei soli nodi INIZIALI
    F       iniziali congelati, nuovi adattabili
    R       embedding della rete ampliata
    A       embedding dei nodi inclusi nel training privilegiato

**K e' il numero effettivo di nodi AMMESSI al training di quel modello**, non il
totale disponibile nel contesto: per E non e' automaticamente 900 × 8, ma dipende
dalla popolazione selezionata e dalla partizione.

**Il controllo «un asse ha dimensione K» e' un'indicazione, non una prova
semantica**: ciascun fornitore dichiara i moduli autorizzati, e l'audit li
confronta con quelli effettivamente presenti.

PER F, LE DUE TABELLE SONO FISICAMENTE SEPARATE, e l'ottimizzatore contiene
soltanto la seconda. E' piu' verificabile che congelare alcune righe di un unico
tensore con una maschera sui gradienti: con un tensore unico, lo stato
dell'ottimizzatore o una regolarizzazione potrebbero modificare righe che si
ritengono congelate.
"""
from __future__ import annotations

import torch
import torch.nn as nn

USCITA = 8


class NodoNonRegistrato(KeyError):
    """Si e' chiesta l'identita' di un nodo che il modello non conosce."""


class ContrattoIdentitaViolato(ValueError):
    """Gli argomenti non rispettano il contratto del fornitore."""


class FornitoreIdentita(nn.Module):
    """Interfaccia comune: da (node_ids, descriptor) a un vettore (B, 8, K, 1).

    **GLI IDENTIFICATIVI SONO PRESENTI PER TUTTI I FORNITORI**, come metadati di
    allineamento: non diventano per questo informazioni apprese. `NoIdentity` e
    `ObservableIdentityEncoder` li usano per verificare numero e ordine dei nodi,
    non come caratteristiche.

    **Nessuna conversione silenziosa** da reale a intero, e **nessun argomento
    informativo ignorato senza controllo**: due argomenti espliciti rendono gli
    errori piu' leggibili, ma i controlli restano necessari.
    """

    uscita = USCITA

    @staticmethod
    def _controlla_nodi(node_ids, K):
        if node_ids is None:
            raise ContrattoIdentitaViolato("`node_ids` e' obbligatorio")
        n = list(node_ids)
        if len(n) != K:
            raise ContrattoIdentitaViolato(
                f"{len(n)} identificativi contro {K} nodi nel tensore dinamico")
        for x in n:
            if isinstance(x, float) or (torch.is_tensor(x)
                                        and x.dtype.is_floating_point):
                raise ContrattoIdentitaViolato(
                    f"identificativo non intero: {x!r}. Nessuna conversione "
                    f"silenziosa da reale a intero.")
        return [int(x) for x in n]

    @staticmethod
    def _rifiuta_descrittore(descriptor, tipo):
        if descriptor is not None:
            raise ContrattoIdentitaViolato(
                f"{tipo} non usa `descriptor`: passarlo e' un errore di "
                f"instradamento, non un argomento ignorato")

    def moduli_per_nodo(self) -> list:
        """I moduli AUTORIZZATI a contenere parametri indicizzati sul nodo.

        L'audit confronta questo elenco con i parametri effettivi: un tensore con
        il primo asse pari a K ma fuori elenco e' un difetto.
        """
        raise NotImplementedError

    def descrizione(self) -> dict:
        raise NotImplementedError


class NoIdentity(FornitoreIdentita):
    """C — nessuna identita' specifica.

    Restituisce un vettore NULLO, non un parametro appreso: il braccio C riceve
    finestra dinamica, calendario e statiche comuni, e nient'altro che lo
    caratterizzi.
    """

    def forward(self, B: int, K: int, *, node_ids, descriptor=None):
        self._controlla_nodi(node_ids, K)      # allineamento, non caratteristica
        self._rifiuta_descrittore(descriptor, "NoIdentity")
        return torch.zeros(B, self.uscita, K, 1)

    def moduli_per_nodo(self):
        return []

    def descrizione(self):
        return {"tipo": "NoIdentity", "parametri_per_nodo": 0,
                "moduli_autorizzati": [],
                "nota": "vettore nullo, non un parametro appreso"}


class ObservableIdentityEncoder(FornitoreIdentita):
    """P — descrittore calcolato, encoder CONDIVISO fra i sensori.

    Nessun parametro indicizzato sul nodo: l'encoder e' lo stesso per tutti, e
    l'identita' viene dalle osservazioni.
    """

    def __init__(self, d_descrittore: int, nascoste: int = 64):
        super().__init__()
        self.d_descrittore = d_descrittore
        self.enc = nn.Sequential(
            nn.Linear(d_descrittore, nascoste),
            nn.ReLU(),
            nn.Linear(nascoste, self.uscita),
        )

    def forward(self, B: int, K: int, *, node_ids, descriptor=None):
        self._controlla_nodi(node_ids, K)      # allineamento, non caratteristica
        if descriptor is None:
            raise ContrattoIdentitaViolato(
                "ObservableIdentityEncoder richiede `descriptor`")
        d = descriptor
        if not torch.is_tensor(d):
            raise ContrattoIdentitaViolato("`descriptor` deve essere un tensore")
        if d.dim() not in (2, 3):
            raise ContrattoIdentitaViolato(
                f"`descriptor` ha {d.dim()} assi, attesi 2 o 3")
        if d.shape[-1] != self.d_descrittore:
            raise ContrattoIdentitaViolato(
                f"descrittore di dimensione {d.shape[-1]}, lo schema ne prevede "
                f"{self.d_descrittore}")
        if d.shape[-2] != K:
            raise ContrattoIdentitaViolato(
                f"{d.shape[-2]} righe di descrittore contro {K} nodi")
        if d.dim() == 2:
            d = d.unsqueeze(0).expand(B, -1, -1)
        return self.enc(d).permute(0, 2, 1).unsqueeze(-1)

    def moduli_per_nodo(self):
        return []

    def descrizione(self):
        return {"tipo": "ObservableIdentityEncoder",
                "d_descrittore": self.d_descrittore,
                "parametri_per_nodo": 0, "moduli_autorizzati": [],
                "parametri": sum(p.numel() for p in self.parameters())}


class LearnedNodeEmbedding(FornitoreIdentita):
    """E, A, R — una riga per nodo AMMESSO al training di quel modello.

    `nodi` e' l'elenco degli identificativi registrati, nell'ordine delle righe.
    **Non esistono righe per i nodi esclusi**: chiedere un nodo non registrato
    solleva, invece di restituire una riga arbitraria.
    """

    def __init__(self, nodi, scala: float = 0.05, generatore=None):
        super().__init__()
        self.registra_ordine = [int(x) for x in nodi]
        self.indice = {n: i for i, n in enumerate(self.registra_ordine)}
        if len(self.indice) != len(self.registra_ordine):
            raise ValueError("identificativi di nodo duplicati")
        w = torch.randn(len(self.registra_ordine), self.uscita,
                        generator=generatore) * scala
        self.embedding = nn.Parameter(w)

    def righe(self, nodi):
        """Le righe dei nodi richiesti. SOLLEVA se uno non e' registrato."""
        fuori = [int(n) for n in nodi if int(n) not in self.indice]
        if fuori:
            raise NodoNonRegistrato(
                f"nodi non registrati in questo modello: {fuori[:8]}"
                f"{'…' if len(fuori) > 8 else ''}. La tabella contiene "
                f"{len(self.registra_ordine)} nodi.")
        return torch.as_tensor([self.indice[int(n)] for n in nodi],
                               dtype=torch.long)

    def forward(self, B: int, K: int, *, node_ids, descriptor=None):
        self._rifiuta_descrittore(descriptor, "LearnedNodeEmbedding")
        idx = self.righe(self._controlla_nodi(node_ids, K))
        z = self.embedding[idx]                       # (K, 8)
        return z.T.unsqueeze(0).unsqueeze(-1).expand(B, -1, -1, -1)

    def moduli_per_nodo(self):
        return ["embedding"]

    def descrizione(self):
        return {"tipo": "LearnedNodeEmbedding",
                "n_nodi_registrati": len(self.registra_ordine),
                "parametri_per_nodo": self.uscita,
                "moduli_autorizzati": ["embedding"],
                "parametri": int(self.embedding.numel()),
                "nota": ("K e' il numero di nodi AMMESSI al training di questo "
                         "modello, non il totale del contesto")}


class AdaptedNodeEmbedding(FornitoreIdentita):
    """F — tabella iniziale CONGELATA, tabella nuova adattabile.

    **Due tensori fisicamente separati.** L'ottimizzatore riceve soltanto
    `nuovi`: congelare righe di un tensore unico con una maschera sui gradienti
    lascerebbe allo stato dell'ottimizzatore o a una regolarizzazione la
    possibilita' di modificarle.

    **L'inizializzazione dei nuovi e' la MEDIA degli embedding iniziali**: regola
    deterministica che non usa dati futuri ne' sceglie un nodo favorevole.
    """

    def __init__(self, iniziale: LearnedNodeEmbedding, nodi_nuovi):
        super().__init__()
        self.registra_ordine = list(iniziale.registra_ordine)
        self.indice = dict(iniziale.indice)
        # la tabella iniziale: copiata e CONGELATA, fuori dall'ottimizzatore
        self.register_buffer("iniziali", iniziale.embedding.detach().clone())
        self.nuovi_ordine = [int(x) for x in nodi_nuovi]
        gia = [n for n in self.nuovi_ordine if n in self.indice]
        if gia:
            raise ValueError(f"nodi gia' registrati fra i nuovi: {gia[:8]}")
        if len(set(self.nuovi_ordine)) != len(self.nuovi_ordine):
            raise ValueError("identificativi duplicati fra i nuovi nodi")
        self.indice_nuovi = {n: i for i, n in enumerate(self.nuovi_ordine)}
        media = self.iniziali.mean(0, keepdim=True)
        self.nuovi = nn.Parameter(media.repeat(len(self.nuovi_ordine), 1).clone())

    def parametri_adattabili(self):
        """I SOLI parametri che l'ottimizzatore deve ricevere."""
        return [self.nuovi]

    def forward(self, B: int, K: int, *, node_ids, descriptor=None):
        self._rifiuta_descrittore(descriptor, "AdaptedNodeEmbedding")
        z = []
        for n in self._controlla_nodi(node_ids, K):
            if n in self.indice:
                z.append(self.iniziali[self.indice[n]])
            elif n in self.indice_nuovi:
                z.append(self.nuovi[self.indice_nuovi[n]])
            else:
                raise NodoNonRegistrato(
                    f"nodo {n} ne' iniziale ne' nuovo in questo modello")
        z = torch.stack(z)
        return z.T.unsqueeze(0).unsqueeze(-1).expand(B, -1, -1, -1)

    def moduli_per_nodo(self):
        return ["iniziali", "nuovi"]

    def descrizione(self):
        return {"tipo": "AdaptedNodeEmbedding",
                "n_iniziali": len(self.registra_ordine),
                "n_nuovi": len(self.nuovi_ordine),
                "parametri_per_nodo": self.uscita,
                "moduli_autorizzati": ["iniziali", "nuovi"],
                "adattabili": int(self.nuovi.numel()),
                "congelati": int(self.iniziali.numel()),
                "nota": ("due tensori FISICAMENTE separati: `iniziali` e' un "
                         "buffer, fuori dall'ottimizzatore")}


def verifica_contratto(modello, fornitore: FornitoreIdentita,
                       K_ammessi: int | None = None) -> dict:
    """I soli parametri indicizzati sul nodo sono quelli AUTORIZZATI.

    Non basta contare gli assi: si confronta l'elenco dichiarato dal fornitore
    con i parametri che hanno il primo asse pari al numero di nodi registrati.
    """
    aut = set(fornitore.moduli_per_nodo())
    n = K_ammessi
    if n is None:
        n = len(getattr(fornitore, "registra_ordine", []) or [])
    sospetti, autorizzati = [], []
    for nome, p in modello.named_parameters():
        if not p.dim():
            continue
        corto = nome.split(".")[-1]
        dentro = any(nome.endswith(x) or f".{x}." in nome or corto == x
                     for x in aut)
        if p.shape[0] == n and n > 0:
            (autorizzati if dentro else sospetti).append(
                {"nome": nome, "forma": list(p.shape)})
        elif dentro:
            autorizzati.append({"nome": nome, "forma": list(p.shape)})
    return {"autorizzati": autorizzati, "non_autorizzati": sospetti,
            "moduli_dichiarati": sorted(aut), "n_nodi": n,
            "conforme": not sospetti}
