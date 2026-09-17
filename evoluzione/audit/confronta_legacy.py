#!/usr/bin/env python3
"""
LEGACY contro le funzioni storiche, senza addestramento.
=========================================================
Le funzioni `hist_summary` e `hist_bands` sono qui riscritte per intero dal
registro delle sessioni, come riferimento INDIPENDENTE: non si importa
`gomo_onboard.py`, che costruisce lo stato globale — somme cumulate, parametri di
normalizzazione, numero di nodi — all'avvio dello script e non e' isolabile senza
modificarlo.

IL CONFRONTO E' COMPONENTE PER COMPONENTE, non sul solo massimo: una differenza
concentrata su una caratteristica ha una causa diversa da un rumore diffuso.

L'ORDINE DELLE COMPONENTI STORICHE, in modalita' `both`:

    0,1   media e deviazione di r      standardizzate con i parametri di r
    2,3   media e deviazione di f
    4,5   media e deviazione di o
    6     quota di validi sulla LUNGHEZZA della finestra, non sulle osservazioni
    7     codice di durata, log1p(L)/log1p(672); vale 1 con L = -1
    8..15 otto fasce di tre ore dell'ora locale

DUE CONVENZIONI STORICHE DA RIPRODURRE ESATTAMENTE:

  * il denominatore e' `max(conteggio, 1)`: un canale senza osservazioni valide
    ha somma nulla, media zero, e dopo la standardizzazione il valore -mu/sd, che
    NON e' zero ed e' indistinguibile da una media osservata che vi coincida;
  * una fascia mai osservata e' riempita con la media GLOBALE di addestramento,
    non con la media della finestra: dopo la standardizzazione vale esattamente
    zero.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/confronta_legacy.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import (  # noqa: E402
    Osservazioni, estrai_diretto)
from evoluzione.componente.estrattore_incrementale import (  # noqa: E402
    EstrattoreIncrementale)

ESITI = []


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


# ============================ le funzioni storiche, riscritte dal registro ===
def padcs(a, msk, N):
    a0 = np.where(msk, a, 0.0).astype("float64")
    return (np.concatenate([np.zeros((1, N)), np.cumsum(a0, 0)]),
            np.concatenate([np.zeros((1, N)), np.cumsum(a0 ** 2, 0)]),
            np.concatenate([np.zeros((1, N)), np.cumsum(msk.astype("float64"), 0)]))


class Storica:
    """Riproduzione fedele di `hist_summary` in modalita' `both`."""

    def __init__(self, r, flow, occ, ore, F_MU):
        self.N = r.shape[1]
        self.CSr, self.CSr2, self.CNr = padcs(r, np.isfinite(r), self.N)
        self.CSf, self.CSf2, self.CNf = padcs(flow, np.isfinite(flow), self.N)
        self.CSo, self.CSo2, self.CNo = padcs(occ, np.isfinite(occ), self.N)
        self.F_MU = F_MU
        hb = ore // 3
        self.CSB, self.CNB = [], []
        for k in range(8):
            mk = np.isfinite(r) & (hb[:, None] == k)
            a0 = np.where(mk, r, 0.0)
            self.CSB.append(np.concatenate([np.zeros((1, self.N)),
                                            np.cumsum(a0, 0)]))
            self.CNB.append(np.concatenate([np.zeros((1, self.N)),
                                            np.cumsum(mk.astype("float64"), 0)]))

    def bands(self, bt, L):
        b = bt + 1
        a = 0 if L == -1 else max(b - L, 0)
        mu, sd = self.F_MU["r"]
        out = np.zeros((self.N, 8), dtype="float64")
        for k in range(8):
            sb = self.CSB[k][b] - self.CSB[k][a]
            cb = self.CNB[k][b] - self.CNB[k][a]
            mband = np.where(cb > 0, sb / np.maximum(cb, 1), mu)
            out[:, k] = (mband - mu) / sd
        return out

    def summary(self, bt, L):
        if L == 0:
            return np.zeros((self.N, 16), dtype="float64")
        b = bt + 1
        a = 0 if L == -1 else max(b - L, 0)
        out = np.zeros((self.N, 16), dtype="float64")
        for j, (CS, CS2, CN, key) in enumerate(
                [(self.CSr, self.CSr2, self.CNr, "r"),
                 (self.CSf, self.CSf2, self.CNf, "f"),
                 (self.CSo, self.CSo2, self.CNo, "o")]):
            s = CS[b] - CS[a]
            s2 = CS2[b] - CS2[a]
            c = np.maximum(CN[b] - CN[a], 1)
            mu, sd = self.F_MU[key]
            m = s / c
            v = np.sqrt(np.maximum(s2 / c - m ** 2, 0))
            out[:, 2 * j] = (m - mu) / sd
            out[:, 2 * j + 1] = v / sd
        Lw = float(b - a)
        out[:, 6] = (self.CNr[b] - self.CNr[a]) / max(Lw, 1)
        out[:, 7] = 1.0 if L == -1 else np.log1p(L) / np.log1p(672)
        out[:, 8:16] = self.bands(bt, L)
        return out


# ============================================================ confronto ======
# LEGACY conserva i tre canali storici, con i nomi della sorgente GO-MO: la sua
# funzione e' la fedelta' alle funzioni precedenti, non la coerenza con il dato
ORDINE = (["media_r", "dev_r", "media_conteggio", "dev_conteggio",
           "media_occupazione", "dev_occupazione"]
          + ["quota_validi", "codice_durata"]
          + [f"banda_{b}" for b in range(8)])


def main() -> int:
    rng = np.random.default_rng(0)
    T, N = 900, 6
    r = rng.uniform(0.2, 1.1, (T, N)); r[rng.random((T, N)) < 0.18] = np.nan
    flow = rng.uniform(50, 200, (T, N)); flow[rng.random((T, N)) < 0.05] = np.nan
    occ = rng.uniform(1, 30, (T, N))
    ore = ((np.arange(T) // 4) % 24)
    cls = rng.choice([0, 1, 2, 3], (T, N))
    # parametri di normalizzazione: sul periodo di addestramento
    reg = slice(0, int(T * 0.7))
    F_MU = {"r": (float(np.nanmean(r[reg])), float(np.nanstd(r[reg])) + 1e-6),
            "f": (float(np.nanmean(flow[reg])), float(np.nanstd(flow[reg])) + 1e-6),
            "o": (float(np.nanmean(occ[reg])), float(np.nanstd(occ[reg])) + 1e-6)}
    # le chiavi di `norm` seguono i NOMI DI CANALE dello schema, non le sigle
    # storiche: con chiavi sbagliate la standardizzazione non si applica e lo
    # scarto risulta dell'ordine dei valori grezzi
    norm = {"media_r": F_MU["r"], "media_conteggio": F_MU["f"],
            "media_occupazione": F_MU["o"]}
    S = Storica(r, flow, occ, ore, F_MU)

    # una fascia deliberatamente mai osservata sul primo sensore
    r2 = r.copy()
    r2[(ore // 3) == 5, 0] = np.nan
    S2 = Storica(r2, flow, occ, ore, F_MU)

    print("LEGACY contro `hist_summary` in modalita' `both`")
    print("=" * 74)
    peggio = {k: 0.0 for k in ORDINE}
    tot = ok = 0
    for usa_lacuna, Sx, rr in ((False, S, r), (True, S2, S2 and r2)):
        for bt in (200, 500, 899):
            for L in (8, 96, 672, -1):
                for n in range(N):
                    O = Osservazioni(np.arange(T), rr[:, n], flow[:, n], occ[:, n],
                                     cls[:, n], ore, t0=0)
                    a = estrai_diretto(O, t=bt, L=L, schema="LEGACY", norm=norm)
                    b = Sx.summary(bt, L)[n]
                    # riordino: LEGACY ha statistiche e disponibilita' separate
                    mio = list(a.statistics[:6]) + list(a.availability) \
                        + list(a.statistics[6:14])
                    tot += 1
                    d = np.abs(np.array(mio) - b)
                    for k, x in zip(ORDINE, d):
                        peggio[k] = max(peggio[k], float(x))
                    if d.max() <= 1e-9:
                        ok += 1

    print(f"\n  {ok}/{tot} estrazioni identiche entro 1e-9")
    print(f"\n  {'componente':16s} {'scarto massimo':>16}")
    for k in ORDINE:
        seg = "" if peggio[k] <= 1e-9 else "   <-- DIFFERISCE"
        print(f"  {k:16s} {peggio[k]:16.3e}{seg}")
    verifica(1, "LEGACY riproduce le funzioni storiche", ok == tot,
             f"scarto massimo complessivo {max(peggio.values()):.3e}")

    # -- e l'incrementale deve riprodurre LEGACY allo stesso modo ------------
    O = Osservazioni(np.arange(T), r[:, 0], flow[:, 0], occ[:, 0], cls[:, 0],
                     ore, t0=0)
    a = estrai_diretto(O, t=500, L=96, schema="LEGACY", norm=norm)
    E = EstrattoreIncrementale(t0=0, L=96, schema="LEGACY", norm=norm)
    E.ingest_batch([(i, r[i, 0], flow[i, 0], occ[i, 0], cls[i, 0], ore[i])
                    for i in range(501)])
    verifica(2, "l'incrementale riproduce LEGACY",
             np.allclose(a.statistics, E.estrai().statistics, atol=1e-9)
             and np.allclose(a.availability, E.estrai().availability, atol=1e-9))

    print("\n" + "=" * 74)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 74)
    print("\n  Una differenza va classificata fra convenzione numerica, finestra,")
    print("  denominatore, trattamento dei mancanti e difetto della precedente")
    print("  implementazione. La specifica nuova NON si modifica per riprodurre")
    print("  un comportamento storico errato: e' LEGACY a doverlo riprodurre.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
