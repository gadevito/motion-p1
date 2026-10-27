#!/usr/bin/env python3
"""
E15 — patch letterale: statica a FINESTRA ESPANSIVA come predefinita, braccio C_A, preflight 15.
=================================================================================================
Ogni sostituzione cerca il testo atteso ESATTAMENTE UNA VOLTA e si ferma altrimenti: nessun modulo
viene ricostruito a memoria. Si esegue dalla radice OR3/ sul ramo `esecutore/e15`:

    python3 patch_e15.py

Tocca:
    evoluzione/esperimenti/inserimento.py      variante `espansiva` (predefinita), classe StaticaEspansiva,
                                               `statica_alle_origini`; `nodi_davvero_nuovi` (A, C_A: nessun
                                               nodo nuovo per la statica — lettura 1 del revisore, 27/10)
    evoluzione/esperimenti/addestramento.py    l'addestramento usa il vettore fisso (finestra minima)
    protocol/E15.md                            «Letture del protocollo, 27/10» appese sotto la firma
    evoluzione/componente/valutazione.py       `valuta`: statica per origine quando e' espansiva
    evoluzione/componente/episodio.py          `lotti_episodio`: idem
    evoluzione/componente/bracci.py            riga C_A (nessuna identita', iniziali + nuovi, privilegiato)
    evoluzione/esperimenti/collauda_bracci.py  due verifiche su C_A (39/39)
    checks/preflight.py                        controllo 15 adattato alla finestra espansiva
"""
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent
PATCH = []


def sost(file, vecchio, nuovo, n=1):
    PATCH.append((file, vecchio, nuovo, n))


# ------------------------------------------------------------ inserimento.py --
F = "evoluzione/esperimenti/inserimento.py"
sost(F, '''VARIANTI_STATICA = ("congelata", "causale", "a", "b", "c")
STATICA_PREDEFINITA = "causale"      # dopo E14 (difetto 21): causale; `congelata` riproduce la campagna
L24_STATICA = 96
''', '''VARIANTI_STATICA = ("congelata", "causale", "espansiva", "a", "b", "c")
# dopo E15: `espansiva` (causale, finestra da t0 all'origine corrente, minimo 24 h);
# `causale` e' la finestra fissa di 24 h (variante (a) di E14); `congelata` riproduce la campagna
STATICA_PREDEFINITA = "espansiva"
L24_STATICA = 96
''')
sost(F, '''def variante_statica() -> str:
    """La variante della statica, da `OR3_STATICA`; assente = `causale` (variante (a) di E14).
    `congelata` e' la statica non causale della campagna del Paper 1 (difetto 21)."""
''', '''def variante_statica() -> str:
    """La variante della statica, da `OR3_STATICA`; assente = `espansiva` (E15: causale a finestra
    espansiva). `causale` e' la finestra fissa di 24 h (variante (a) di E14); `congelata` e' la
    statica non causale della campagna del Paper 1 (difetto 21)."""
''')
sost(F, '''                    help=f"statica per nodo: congelata (campagna Paper 1, non causale) oppure causale "
                         f"(predefinita); a, b, c = varianti di E14 (OR3_STATICA)")
''', '''                    help=f"statica per nodo: congelata (campagna Paper 1, non causale); espansiva "
                         f"(predefinita, E15: finestra da t0 all'origine, minimo 24 h); causale "
                         f"(finestra fissa di 24 h, E14); a, b, c = varianti di E14 (OR3_STATICA)")
''')
sost(F, '''        congelata   `stat` com'e' (bit per bit; la campagna del Paper 1, non causale)
        causale, a  iniziali: media di m_r su [0, t0); nn: media su (t0, t0 + 24 h]
''', '''        congelata   `stat` com'e' (bit per bit; la campagna del Paper 1, non causale)
        espansiva   iniziali: media di m_r su [0, t0); nn: FINESTRA ESPANSIVA (E15),
                    all'origine t la media su (t0, max(t, t0 + 24 h)]. L'oggetto
                    restituito e' un vettore (K, 5) alla finestra MINIMA, identico a
                    `causale` (chi non valuta per origine — addestramento, selezione
                    del punto — vede quello), e porta `alle_origini(nodi, istanti)`
                    per chi valuta per origine (`valuta`, `lotti_episodio`)
        causale, a  iniziali: media di m_r su [0, t0); nn: media su (t0, t0 + 24 h]
''')
sost(F, '''    if v in ("causale", "a", "b"):
        cov_c = m[:t0].mean(0)
        stat[:, 0] = cov_c.astype("float32")
        if v in ("causale", "a"):
''', '''    if v in ("causale", "espansiva", "a", "b"):
        cov_c = m[:t0].mean(0)
        stat[:, 0] = cov_c.astype("float32")
        if v == "espansiva":
            return StaticaEspansiva.costruisci(stat, m, nn, t0)
        if v in ("causale", "a"):
''')
sost(F, '''def impronta_nodi(ids) -> str:
''', '''class StaticaEspansiva(np.ndarray):
    """La statica per nodo a FINESTRA ESPANSIVA (E15, `protocol/E15.md`).

    Come array e' la statica alla finestra minima: nodi nuovi con la copertura
    media su (t0, t0 + 24 h], iniziali su [0, t0). `alle_origini(nodi, istanti)`
    da' la statica per origine, (B, n, 5): per i nodi nuovi la copertura media su
    (t0, max(t, t0 + 24 h)], per gli altri il vettore fisso. **Solo l'oggetto
    costruito da `costruisci` porta la finestra**: una vista o una copia
    (`stat[nodi]`, `np.array(stat)`) e' un array e basta, e chiederle le origini
    solleva, anziche' rispondere con la finestra minima in silenzio.
    """

    def __array_finalize__(self, obj):
        self._esp = None

    @classmethod
    def costruisci(cls, stat, m, nn, t0):
        m = np.asarray(m, dtype="float64"); t0 = int(t0); t1 = t0 + L24_STATICA
        nn = np.asarray(nn, dtype="int64")
        if t1 + 1 > m.shape[0]:
            raise ValueError(f"finestra minima oltre la serie: t0 {t0}, T {m.shape[0]}")
        # somme cumulate (una riga di zeri in testa): cs[t + 1] - cs[t0 + 1] = somma su (t0, t]
        cs = np.concatenate([np.zeros((1, len(nn))), np.cumsum(m[:, nn], 0)], 0)
        stat = np.array(stat, dtype="float32", copy=True)
        stat[nn, 0] = ((cs[t1 + 1] - cs[t0 + 1]) / (t1 - t0)).astype("float32")
        s = stat.view(cls)
        s._esp = {"cs": cs, "t0": t0, "t1": t1, "nn": nn,
                  "posizione": {int(n): j for j, n in enumerate(nn)}}
        return s

    def alle_origini(self, nodi, istanti):
        if self._esp is None:
            raise RuntimeError("statica espansiva senza finestra: l'oggetto e' una vista o una "
                               "copia; passare quello restituito da `statica_cella`")
        e = self._esp
        nodi = np.asarray(nodi, dtype="int64"); ist = np.asarray(istanti, dtype="int64")
        S = np.repeat(np.asarray(self)[nodi][None], len(ist), 0)           # (B, n, 5)
        col = [i for i, n in enumerate(nodi) if int(n) in e["posizione"]]
        if col and len(ist):
            j = [e["posizione"][int(nodi[i])] for i in col]
            tt = np.maximum(ist, e["t1"])
            if int(tt.max()) + 1 >= e["cs"].shape[0]:
                raise ValueError(f"origine {int(tt.max())} oltre la serie")
            cov = (e["cs"][tt + 1][:, j] - e["cs"][e["t0"] + 1][j]) / (tt - e["t0"])[:, None]
            S[:, col, 0] = cov.astype("float32")
        return S


def statica_alle_origini(stat, nodi, istanti):
    """(B, n, 5) se `stat` e' la statica espansiva di `statica_cella`, altrimenti None: chi
    valuta per origine la chiama e, con None, usa `stat[nodi]` come prima (bit per bit)."""
    if isinstance(stat, StaticaEspansiva):
        return stat.alle_origini(nodi, istanti)
    return None


def impronta_nodi(ids) -> str:
''')

sost(F, '''def statica_addestramento(D, nodi, cfg, contesto):
    """La statica dell'ADDESTRAMENTO (addestramento.py): `statiche(D)` passata da `statica_cella`
    con i nodi nuovi dichiarati dalla configurazione (vuoti per E, E') e il t0 dell'episodio."""
    nn = np.asarray(cfg.get("nodi_nuovi", []), dtype="int64")
    t0 = t0_installazione(contesto, cfg.get("fine_periodo"))
    return statica_cella(statiche(D), D, nodi, nn, t0, int(cfg.get("seme_dichiarato", 0)))
''', '''def nodi_davvero_nuovi(braccio: str, nn):
    """E15 (lettura 1 del revisore, 27/10): per i bracci a corpus PRIVILEGIATO (A, C_A) i nodi
    "nuovi" sono iniziali a tutti gli effetti — hanno la storia su [0, t0) — e la loro copertura
    si calcola su [0, t0) come per gli altri: nessun nodo nuovo per la statica. Per gli altri
    bracci la finestra (minima 24 h, poi espansiva) vale dove il sensore e' davvero nuovo."""
    if proprieta_braccio(braccio).corpus == "privilegiato":
        return np.zeros(0, dtype="int64")
    return np.asarray(nn, dtype="int64")


def statica_addestramento(D, nodi, cfg, contesto):
    """La statica dell'ADDESTRAMENTO (addestramento.py): `statiche(D)` passata da `statica_cella`
    con i nodi nuovi dichiarati dalla configurazione (vuoti per E, E') e il t0 dell'episodio.
    Per A e C_A (corpus privilegiato) i nodi nuovi non sono nuovi: copertura su [0, t0)."""
    nn = nodi_davvero_nuovi(cfg.get("braccio", "P"), cfg.get("nodi_nuovi", []))
    t0 = t0_installazione(contesto, cfg.get("fine_periodo"))
    return statica_cella(statiche(D), D, nodi, nn, t0, int(cfg.get("seme_dichiarato", 0)))
''')
sost(F, '''    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    stat = statica_cella(statiche(D), D, nodi, nodi["prova"], t0_installazione(c), int(s))
    w = torch.as_tensor(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                        dtype=torch.float32)
    fine = D["r"].shape[0] - max(ORIZZONTI)
''', '''    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    # E15: per A e C_A i nodi di prova sono iniziali (copertura su [0, t0)); per gli altri sono nuovi
    stat = statica_cella(statiche(D), D, nodi, nodi_davvero_nuovi(b, nodi["prova"]),
                         t0_installazione(c), int(s))
    w = torch.as_tensor(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                        dtype=torch.float32)
    fine = D["r"].shape[0] - max(ORIZZONTI)
''')

# ------------------------------------------------------------ addestramento.py --
F = "evoluzione/esperimenti/addestramento.py"
sost(F, '''    stat = torch.as_tensor(statica_addestramento(D, nodi, cfg, E.contesto))   # causale; congelata = campagna
''', '''    # E15: l'addestramento usa il VETTORE FISSO della statica (finestra minima: `espansiva` == `causale`
    # qui), perche' le origini di addestramento e di selezione del punto precedono t0; `congelata` = campagna
    stat = torch.as_tensor(np.asarray(statica_addestramento(D, nodi, cfg, E.contesto)))
''')

# ------------------------------------------------------------ valutazione.py --
F = "evoluzione/componente/valutazione.py"
sost(F, '''    m.eval()
    S = torch.as_tensor(statiche[nodi].astype("float32"))
    with torch.inference_mode():
        for i in range(0, len(ist), lotto):
            blocco = ist[i:i + lotto]
            X, Y, M = _lotto(x, classe, blocco, nodi)
            out = m(X, node_ids=[int(v) for v in nodi],
                    descriptor=descrittore, static_inputs=S)
            for h in range(len(ORIZZONTI)):
''', '''    m.eval()
    # E15: con la statica ESPANSIVA la statica dei nodi nuovi dipende dall'origine,
    # (B, n, 5) per lotto; con un vettore fisso tutto e' come prima, bit per bit
    from evoluzione.esperimenti.inserimento import statica_alle_origini
    S = torch.as_tensor(np.asarray(statiche)[nodi].astype("float32"))
    with torch.inference_mode():
        for i in range(0, len(ist), lotto):
            blocco = ist[i:i + lotto]
            X, Y, M = _lotto(x, classe, blocco, nodi)
            S_o = statica_alle_origini(statiche, nodi, blocco)
            out = m(X, node_ids=[int(v) for v in nodi],
                    descriptor=descrittore,
                    static_inputs=(S if S_o is None else torch.as_tensor(S_o)))
            for h in range(len(ORIZZONTI)):
''')

# --------------------------------------------------------------- episodio.py --
F = "evoluzione/componente/episodio.py"
sost(F, '''    nodi = np.asarray(nodi, dtype="int64")
    X, Y, M = _lotto(x, classe, origini, nodi)
    S = torch.as_tensor(statiche[nodi].astype("float32"))
    if not per_nodo:
        return [(X, [int(v) for v in nodi], Y, M, S)]
    fuori = []
    for i, n in enumerate(nodi):
        if not bool(M[:, i].any()):
            continue
        fuori.append((X[:, :, i:i + 1], [int(n)], Y[:, i:i + 1],
                      M[:, i:i + 1], S[i:i + 1]))
    return fuori
''', '''    nodi = np.asarray(nodi, dtype="int64")
    X, Y, M = _lotto(x, classe, origini, nodi)
    # E15: statica ESPANSIVA -> (B, n, 5), per origine; vettore fisso -> (n, 5) come prima
    from evoluzione.esperimenti.inserimento import statica_alle_origini
    S_o = statica_alle_origini(statiche, nodi, origini)
    S = (torch.as_tensor(np.asarray(statiche)[nodi].astype("float32")) if S_o is None
         else torch.as_tensor(S_o))
    if not per_nodo:
        return [(X, [int(v) for v in nodi], Y, M, S)]
    fuori = []
    for i, n in enumerate(nodi):
        if not bool(M[:, i].any()):
            continue
        fuori.append((X[:, :, i:i + 1], [int(n)], Y[:, i:i + 1],
                      M[:, i:i + 1], S[..., i:i + 1, :]))
    return fuori
''')

# ----------------------------------------------------------------- bracci.py --
F = "evoluzione/componente/bracci.py"
sost(F, '''    A        E sulla rete ampliata, privilegiato  LearnedNodeEmbedding
''', '''    A        E sulla rete ampliata, privilegiato  LearnedNodeEmbedding
    C_A      C sulla rete ampliata, privilegiato  NoIdentity (E15)
''')
sost(F, '''    _b("A", "embedding", popolazione="ampliata", corpus="privilegiato",
       pop_descr=_AMPLIATA_A, corpus_descr=_CORPUS_A),
''', '''    _b("A", "embedding", popolazione="ampliata", corpus="privilegiato",
       pop_descr=_AMPLIATA_A, corpus_descr=_CORPUS_A),
    # E15: C_A isola l'identita' dal dato in piu' — nessuna identita', ma lo
    # stesso corpus privilegiato di A (iniziali + nuovi, con la storia
    # anteriore a t0). A − C_A e' il valore dell'identita'; C_A − C quello del dato.
    _b("C_A", "nessuna", popolazione="ampliata", corpus="privilegiato",
       pop_descr=_AMPLIATA_A, corpus_descr=_CORPUS_A),
''')

# -------------------------------------------------------- collauda_bracci.py --
F = "evoluzione/esperimenti/collauda_bracci.py"
sost(F, '''    v("1q", "rho richiesto da E1 soltanto",
''', '''    v("1s", "C_A (E15): fornitore di C, popolazione e corpus di A",
      T["C_A"].fornitore == T["C"].fornitore
      and T["C_A"].popolazione == T["A"].popolazione == "ampliata"
      and T["C_A"].corpus == T["A"].corpus == "privilegiato"
      and T["C_A"].descrizione_popolazione == T["A"].descrizione_popolazione
      and T["C_A"].descrizione_corpus == T["A"].descrizione_corpus
      and T["C_A"].addestra and T["C_A"].carica_canonico
      and not T["C_A"].usa_descrittore and not T["C_A"].richiede_rho)
    v("1q", "rho richiesto da E1 soltanto",
''')
sost(F, '''    v("3h", "C con nodi nuovi in addestramento e' rifiutato",
''', '''    v("3i", "C_A senza storia anteriore a t0 e' rifiutato come A",
      _solleva(lambda: fasi.controlli_A_R("C_A", ini + nuo, nuo, ist, t0=5),
               fasi.PrerequisitoMancante)
      and _solleva(lambda: fasi.controlli_A_R("C_A", ini, nuo, ist, t0=12),
                   fasi.PrerequisitoMancante))
    v("3h", "C con nodi nuovi in addestramento e' rifiutato",
''')

# ---------------------------------------------------------- checks/preflight.py --
F = "checks/preflight.py"
sost(F, '''    # 15. causalita' della STATICA per nodo (E14, controllo n. 8): con m_r perturbata dopo
    #     t0 + 24 h la statica della cella non cambia di un bit; la statica congelata
    #     (difetto 21) cambia, e qui BLOCCA.
    import os
    from evoluzione.esperimenti.inserimento import (L24_STATICA, statica_cella, statiche,
                                                     t0_installazione, variante_statica)
    v_st = variante_statica(); t0i = t0_installazione(c)
    D3 = {k: (val.copy() if isinstance(val, np.ndarray) else val) for k, val in D.items()}
    D3["m_r"] = D3["m_r"].copy()
    D3["m_r"][t0i + L24_STATICA + 1:] = rng.random(D3["m_r"][t0i + L24_STATICA + 1:].shape) < 0.5
    s1 = statica_cella(statiche(D), D, nodi, nodi["prova"], t0i, a.seme)
    s2 = statica_cella(statiche(D3), D3, nodi, nodi["prova"], t0i, a.seme)
    cong_cambia = not np.array_equal(statiche(D), statiche(D3))
    v("15", "statica per nodo IDENTICA AL BIT con m_r perturbata dopo t0 + 24 h (E14, n. 8)",
      v_st != "congelata" and np.array_equal(s1, s2),
      f"statica «{v_st}», t0 {t0i}, scarto massimo {float(np.abs(s1 - s2).max()):.3e}; "
      f"la statica congelata {'cambia' if cong_cambia else 'non cambia'} con la stessa perturbazione"
      + ("" if v_st != "congelata" else " — congelata = non causale (difetto 21): solo per riprodurre la campagna"))
''', '''    # 15. causalita' della STATICA per nodo (E14, controllo n. 8; E15, finestra espansiva):
    #     (i) il vettore fisso (finestra minima) non cambia di un bit con m_r perturbata dopo
    #     t0 + 24 h; (ii) con la statica ESPANSIVA, a ogni origine t di prova la statica per
    #     origine non cambia con m_r perturbata DOPO t, e cambia con m_r perturbata su (t0, t]
    #     (la finestra si espande davvero). La statica congelata (difetto 21) cambia, e BLOCCA.
    from evoluzione.esperimenti.inserimento import (L24_STATICA, statica_alle_origini,
                                                     statica_cella, statiche, t0_installazione,
                                                     variante_statica)
    v_st = variante_statica(); t0i = t0_installazione(c)

    def perturba(da, a_=None):
        D_ = {k: (val.copy() if isinstance(val, np.ndarray) else val) for k, val in D.items()}
        D_["m_r"] = D_["m_r"].copy()
        D_["m_r"][da:a_] = rng.random(D_["m_r"][da:a_].shape) < 0.5
        return D_
    D3 = perturba(t0i + L24_STATICA + 1)
    s1 = statica_cella(statiche(D), D, nodi, nodi["prova"], t0i, a.seme)
    s2 = statica_cella(statiche(D3), D3, nodi, nodi["prova"], t0i, a.seme)
    cong_cambia = not np.array_equal(statiche(D), statiche(D3))
    fisso_ok = v_st != "congelata" and np.array_equal(np.asarray(s1), np.asarray(s2))
    dett = (f"statica «{v_st}», t0 {t0i}, scarto massimo {float(np.abs(np.asarray(s1) - np.asarray(s2)).max()):.3e}; "
            f"la statica congelata {'cambia' if cong_cambia else 'non cambia'} con la stessa perturbazione")
    esp_ok = True
    if statica_alle_origini(s1, nodi["prova"][:1], [t0i + L24_STATICA]) is not None:
        fine_ = D["r"].shape[0] - GR.MAX_ORIZZ
        prove = sorted({t0i + L24_STATICA, t0i + L24_STATICA + 1, t0i + 672, (t0i + L24_STATICA + fine_ - 1) // 2, fine_ - 1})
        prove = [t for t in prove if t0i + L24_STATICA <= t <= fine_ - 1]
        uguali, diversi = [], []
        for t in prove:
            Dd = perturba(t + 1)                       # dopo l'origine: nulla cambia
            Dp = perturba(t0i + 1, t + 1)              # dentro (t0, t]: la finestra lo vede
            sd = statica_cella(statiche(Dd), Dd, nodi, nodi["prova"], t0i, a.seme)
            sp = statica_cella(statiche(Dp), Dp, nodi, nodi["prova"], t0i, a.seme)
            o1 = statica_alle_origini(s1, nodi["prova"], [t])
            uguali.append(np.array_equal(o1, statica_alle_origini(sd, nodi["prova"], [t])))
            diversi.append(not np.array_equal(o1, statica_alle_origini(sp, nodi["prova"], [t])))
        esp_ok = all(uguali) and all(diversi)
        dett += (f"; finestra espansiva su {len(prove)} origini {prove}: identica con m_r perturbata dopo t "
                 f"in {sum(uguali)}/{len(prove)}, diversa con m_r perturbata su (t0, t] in {sum(diversi)}/{len(prove)}")
    v("15", "statica per nodo causale: IDENTICA AL BIT con m_r perturbata dopo l'origine (E14 n. 8; E15 finestra espansiva)",
      fisso_ok and esp_ok,
      dett + ("" if v_st != "congelata" else " — congelata = non causale (difetto 21): solo per riprodurre la campagna"))
''')


LETTURE = """
## Letture del protocollo, 27/10/2026 (revisore, trascritte alla lettera)

Tre letture, tre risposte:

1. Finestra espansiva. Quasi: per A e C_A i sensori "nuovi" sono sensori iniziali a tutti gli effetti — hanno l'intera storia su [0, t₀) — quindi la loro copertura va calcolata su [0, t₀) come per gli altri, non su 24 h. La finestra minima di 24 h e l'espansione origine per origine valgono dove il sensore è davvero nuovo: valutazione e adattamento di F₀, F₀′, F′ (e la loro selezione, che è sui nodi di validazione, trattati come nuovi dall'inizio del loro episodio). Selezione del checkpoint di A e C_A: sul set di validazione della rete iniziale, come nella campagna, copertura su [0, t₀). Se nel codice attuale A e C_A hanno la finestra di 24 h, va cambiato prima di partire e detto nel congelamento.
2. Differenze congelate accanto alle causali. Sì alla tua scelta: il confronto si fa sulle stesse 54 celle (semi 201–206) dalle predizioni salvate, con le stesse estrazioni del ricampionamento, perché è appaiato. Nel congelamento entrambe le colonne: "congelata, 54 celle" come termine di confronto, "pubblicata, 12 semi" come riferimento; e la differenza fra le due (già nota da E5: +0,013 vs +0,015 a Londra) dichiarata in una riga.
3. Secondaria F′(1 sett.; k). Confermato: griglia {10, 50, 200} di `seleziona_F`, passo congelato per città (0,01/0,01/0,001), selezione sull'episodio di validazione causale con i nodi di validazione, criterio wCE media sulle origini con età > 1 settimana. Scrivi la scelta su file con impronta prima di valutare sul test, come sempre.

Correzione del punto 1 nel codice (prima di partire): `inserimento.nodi_davvero_nuovi` — per i bracci a corpus privilegiato (A, C_A) nessun nodo e' nuovo per la statica, in addestramento, selezione del punto e valutazione.
"""


def main() -> int:
    f_prot = RADICE / "protocol" / "E15.md"
    if "Letture del protocollo, 27/10/2026" in f_prot.read_text():
        print("FERMO: protocol/E15.md contiene gia' le letture del 27/10"); return 1
    for f, vecchio, nuovo, n in PATCH:
        p = RADICE / f
        src = p.read_text()
        k = src.count(vecchio)
        if k != n:
            print(f"FERMO: in {f} il testo atteso compare {k} volte, non {n}:\n---\n{vecchio[:300]}\n---")
            return 1
    for f, vecchio, nuovo, n in PATCH:
        p = RADICE / f
        p.write_text(p.read_text().replace(vecchio, nuovo))
        print(f"  {f}: sostituito")
    f_prot.write_text(f_prot.read_text().rstrip("\n") + "\n" + LETTURE)
    print(f"  protocol/E15.md: letture del 27/10 appese sotto la firma")
    print(f"  {len(PATCH)} sostituzioni applicate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
