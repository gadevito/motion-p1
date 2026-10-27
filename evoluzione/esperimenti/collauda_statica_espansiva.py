#!/usr/bin/env python3
"""
Collaudo della statica a FINESTRA ESPANSIVA (E15) e dei consumatori per origine.
=================================================================================
Dati sintetici (nessun risultato della campagna), tre varianti a confronto:

    congelata   `statica_cella` restituisce lo STESSO oggetto, bit per bit
    causale     vettore fisso, finestra di 24 h
    espansiva   vettore fisso IDENTICO a `causale`; `alle_origini` espande la finestra

Poi `lotti_episodio` e `valuta` con un modello giocattolo che legge la statica: con la
espansiva il risultato coincide con quello ottenuto origine per origine passando la
statica fissa di quell'origine; con un vettore fisso tutto coincide bit per bit con prima.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_statica_espansiva.py
"""
import os
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ESITI = []


def v(n, titolo, cond, dett=""):
    ESITI.append((n, bool(cond)))
    print(f"  [{n:3s}] {'PASSA' if cond else 'FALLISCE'}  {titolo}" + (f"\n          {dett}" if dett else ""))


def con_variante(nome):
    os.environ["OR3_STATICA"] = nome


def main() -> int:
    from evoluzione.componente.episodio import lotti_episodio
    from evoluzione.componente.predittore import FINESTRA, ORIZZONTI
    from evoluzione.componente.valutazione import valuta
    from evoluzione.esperimenti.inserimento import (
        L24_STATICA, StaticaEspansiva, statica_alle_origini, statica_cella, statiche)
    print("=" * 84)
    print("COLLAUDO — statica a finestra espansiva (E15)")
    print("=" * 84)
    rng = np.random.default_rng(15)
    T, K, C = 2000, 40, 9
    m_r = rng.random((T, K)) < rng.random(K)                 # maschera booleana, come in D
    D = {"m_r": m_r, "r": rng.normal(size=(T, K)).astype("float32")}
    perm = rng.permutation(K)
    nodi = {"addestramento": np.sort(perm[:28]), "validazione": np.sort(perm[28:34]),
            "prova": np.sort(perm[34:])}
    nn = nodi["prova"]; t0 = 900; t1 = t0 + L24_STATICA
    base = statiche(D)

    # -- 1. le tre varianti -------------------------------------------------------
    con_variante("congelata"); s_c = statica_cella(base, D, nodi, nn, t0, 7)
    v("1a", "congelata: lo stesso oggetto, bit per bit", s_c is base and np.array_equal(s_c, base))
    con_variante("causale"); s_24 = statica_cella(base, D, nodi, nn, t0, 7)
    con_variante("espansiva"); s_e = statica_cella(base, D, nodi, nn, t0, 7)
    v("1b", "espansiva: e' una StaticaEspansiva con la finestra",
      isinstance(s_e, StaticaEspansiva) and s_e._esp is not None and s_e.dtype == np.float32)
    v("1c", "espansiva come vettore fisso == causale, bit per bit",
      np.array_equal(np.asarray(s_e), s_24) and type(s_24) is np.ndarray)
    v("1d", "iniziali: media di m_r su [0, t0) (float32)",
      np.array_equal(np.asarray(s_e)[nodi["addestramento"], 0],
                     m_r[:t0].astype("float64").mean(0)[nodi["addestramento"]].astype("float32")))
    v("1e", "nuovi alla finestra minima: media su (t0, t0 + 24 h]",
      np.array_equal(np.asarray(s_e)[nn, 0], m_r[t0 + 1:t1 + 1].astype("float64").mean(0)[nn].astype("float32")))
    v("1f", "le colonne 1..4 non cambiano", np.array_equal(np.asarray(s_e)[:, 1:], base[:, 1:]))

    # -- 2. alle_origini ----------------------------------------------------------
    ist = np.array([t0 + 1, t1 - 3, t1, t1 + 1, t1 + 100, t0 + 672, T - 10])
    S = statica_alle_origini(s_e, nn, ist)
    v("2a", "forma (B, n, 5) e float32", S.shape == (len(ist), len(nn), 5) and S.dtype == np.float32)
    att = np.stack([m_r[t0 + 1:max(t, t1) + 1].astype("float64").mean(0)[nn] for t in ist]).astype("float32")
    v("2b", "copertura dei nuovi = media su (t0, max(t, t0 + 24 h)], bit per bit",
      np.array_equal(S[:, :, 0], att), f"scarto massimo {float(np.abs(S[:, :, 0] - att).max()):.3e}")
    v("2c", "a t <= t0 + 24 h coincide con il vettore fisso",
      all(np.array_equal(S[i], np.asarray(s_e)[nn]) for i, t in enumerate(ist) if t <= t1))
    v("2d", "a t > t0 + 24 h la copertura dei nuovi cambia davvero",
      any(not np.array_equal(S[i], np.asarray(s_e)[nn]) for i, t in enumerate(ist) if t > t1))
    misti = np.concatenate([nodi["addestramento"][:3], nn[:2]])
    Sm = statica_alle_origini(s_e, misti, ist)
    v("2e", "nodi non nuovi: il vettore fisso a ogni origine; nuovi: la finestra",
      np.array_equal(Sm[:, :3], np.repeat(np.asarray(s_e)[misti[:3]][None], len(ist), 0))
      and np.array_equal(Sm[:, 3:, 0], att[:, :2]))
    v("2f", "un vettore fisso non ha origini (None)", statica_alle_origini(s_24, nn, ist) is None
      and statica_alle_origini(base, nn, ist) is None)
    vista = s_e[nn]; copia = np.array(s_e)
    try:
        statica_alle_origini(vista, nn, ist); solleva = False
    except RuntimeError:
        solleva = True
    v("2g", "una vista perde la finestra e SOLLEVA; una copia e' un array e basta",
      solleva and type(copia) is np.ndarray and np.array_equal(copia, np.asarray(s_e)))

    # -- 3. causalita' ------------------------------------------------------------
    def perturba(da, a_=None):
        D_ = {k: (z.copy() if isinstance(z, np.ndarray) else z) for k, z in D.items()}
        D_["m_r"][da:a_] = rng.random(D_["m_r"][da:a_].shape) < 0.5
        return D_
    t = t0 + 300
    Dd, Dp = perturba(t + 1), perturba(t0 + 1, t + 1)
    sd = statica_cella(statiche(Dd), Dd, nodi, nn, t0, 7); sp = statica_cella(statiche(Dp), Dp, nodi, nn, t0, 7)
    v("3a", "m_r perturbata DOPO t: statica all'origine t identica al bit",
      np.array_equal(statica_alle_origini(s_e, nn, [t]), statica_alle_origini(sd, nn, [t])))
    v("3b", "m_r perturbata su (t0, t]: statica all'origine t diversa",
      not np.array_equal(statica_alle_origini(s_e, nn, [t]), statica_alle_origini(sp, nn, [t])))
    v("3c", "il vettore fisso non cambia con m_r perturbata dopo t0 + 24 h",
      np.array_equal(np.asarray(s_e), np.asarray(statica_cella(statiche(Dd), Dd, nodi, nn, t0, 7))) if t + 1 > t1 else True)

    # -- 4. lotti_episodio e valuta -----------------------------------------------
    x = rng.normal(size=(T, C, K)).astype("float32")
    classe = rng.integers(0, 4, size=(T, K)).astype("int64")
    pesi = torch.tensor([1.0, 2.0, 3.0])
    orig = [int(z) for z in range(t1 + 1, t1 + 40)]
    L_fix = lotti_episodio(x, classe, s_24, nn, orig)
    L_esp = lotti_episodio(x, classe, s_e, nn, orig)
    v("4a", "lotti_episodio con vettore fisso: S (n, 5) come prima", L_fix[0][4].shape == (len(nn), 5)
      and torch.equal(L_fix[0][4], torch.as_tensor(s_24[nn])))
    v("4b", "lotti_episodio con espansiva: S (B, n, 5) = alle_origini",
      L_esp[0][4].shape == (len(orig), len(nn), 5)
      and torch.equal(L_esp[0][4], torch.as_tensor(statica_alle_origini(s_e, nn, orig))))
    Ln = lotti_episodio(x, classe, s_e, nn, orig, per_nodo=True)
    v("4c", "per_nodo con espansiva: S (B, 1, 5) per nodo", all(l_[4].shape == (len(orig), 1, 5) for l_ in Ln))

    class Giocattolo(torch.nn.Module):
        """Logit che dipendono dalla statica (copertura) e dall'ingresso: (B, K, H, 3)."""
        def __init__(self):
            super().__init__(); self.w = torch.nn.Parameter(torch.tensor([0.3, -0.2, 0.1]))

        def forward(self, X, *, node_ids, descriptor=None, static_inputs=None):
            B, _, K_, _ = X.shape
            s = static_inputs
            if s.dim() == 2:
                s = s.unsqueeze(0).expand(B, -1, -1)
            cov = s[..., 0]                                            # (B, K)
            base_ = X[:, 0, :, -1]                                     # (B, K)
            z = (cov + base_)[..., None, None] * self.w                # (B, K, 1, 3)
            return z.expand(B, K_, len(ORIZZONTI), 3).contiguous()
    m = Giocattolo()
    per = np.array(orig + [t0 + 500, t0 + 700, T - 12])
    r_esp = valuta(m, x, classe, s_e, nn, per, pesi)
    r_fix = valuta(m, x, classe, s_24, nn, per, pesi)
    v("4d", "valuta con espansiva differisce dal vettore fisso (le origini oltre 24 h contano)",
      r_esp["perdita"] != r_fix["perdita"])
    # origine per origine, con la statica FISSA di quell'origine: stessi accumulatori
    A = np.zeros(len(ORIZZONTI)); Bm = np.zeros(len(ORIZZONTI))
    for t in per:
        st_t = np.asarray(s_e).copy(); st_t[nn] = statica_alle_origini(s_e, nn, [t])[0]
        r_t = valuta(m, x, classe, st_t, nn, [int(t)], pesi)
        A += np.array(r_t["per_orizzonte"]) * np.array(r_t["massa_pesi"]); Bm += np.array(r_t["massa_pesi"])
    v("4e", "valuta con espansiva == origine per origine con la statica di quell'origine",
      np.allclose(np.array(r_esp["per_orizzonte"]), A / Bm, rtol=1e-9, atol=0)
      and np.allclose(np.array(r_esp["massa_pesi"]), Bm, rtol=0, atol=0),
      f"scarto relativo massimo {float(np.abs(np.array(r_esp['per_orizzonte']) / (A / Bm) - 1).max()):.2e}")
    # con un vettore fisso il percorso e' quello di prima: lotto unico contro lotti piccoli
    r_1 = valuta(m, x, classe, s_24, nn, per, pesi, lotto=7)
    v("4f", "vettore fisso: risultato indipendente dalla dimensione del lotto (come prima)",
      abs(r_1["perdita"] - r_fix["perdita"]) <= 1e-12 * abs(r_fix["perdita"]))
    r_2 = valuta(m, x, classe, s_e, nn, per, pesi, lotto=7)
    v("4g", "espansiva: idem", abs(r_2["perdita"] - r_esp["perdita"]) <= 1e-12 * abs(r_esp["perdita"]))
    # la finestra minima dentro le 24 h: espansiva == causale sulle origini d'acquisizione
    o_acq = [int(z) for z in range(t0 + FINESTRA, t1 + 1)]
    v("4h", "sulle origini entro t0 + 24 h espansiva == causale, bit per bit",
      valuta(m, x, classe, s_e, nn, o_acq, pesi)["perdita"] == valuta(m, x, classe, s_24, nn, o_acq, pesi)["perdita"])

    n_ok = sum(1 for _, o in ESITI if o)
    print("=" * 84)
    print(f"  {n_ok}/{len(ESITI)} verifiche superate")
    print("=" * 84)
    os.environ.pop("OR3_STATICA", None)
    return 0 if n_ok == len(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
