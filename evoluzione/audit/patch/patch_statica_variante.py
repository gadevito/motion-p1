#!/usr/bin/env python3
"""
Patch E14 stadio B — la statica per cella ha UNA sede e un interruttore.
==========================================================================
`inserimento.statica_cella(stat, D, nodi, nn, t0, seme)` applica alla statica della cella la
variante letta dalla variabile d'ambiente `OR3_STATICA` ∈ {congelata, a, b, c}; assente o
«congelata» restituisce `stat` com'e' (**bit per bit**: la campagna del Paper 1 non cambia).
Ogni esecutore di valutazione la chiama dove gia' aveva la statica e conosce t₀, i ruoli dei
nodi e il seme della cella: esegui_f0, esegui_e2, ricostruisci_predizioni (E3/E3-bis),
veterani_e3, riselezione_rmon_test, esegui_e4, esegui_e5 (×2), esegui_e6 (×2), esegui_e6a,
esegui_e8. Nei cicli sui semi (E2, E3) la statica si calcola dentro il ciclo, perche' la
variante (c) permuta per seme. Dodici sostituzioni letterali: se un testo atteso non c'e' una
volta sola, si ferma senza toccare nulla.

Non toccati: `adatta_F` e `valuta_prova` di `inserimento.py` (usati solo dagli addestramenti
di E3, che lo stadio B non rifa'): nel branch `esecutore/statica-causale`.

Uso (dalla radice OR3/):

    poetry run python patch_statica_variante.py
"""
from pathlib import Path

SOSTITUZIONI = {
    "evoluzione/esperimenti/inserimento.py": [(
        '''import hashlib
import json
import time
''',
        '''import hashlib
import json
import os
import time
'''), (
        '''def statiche(D):
    K = D["r"].shape[1]
    return np.stack([D["m_r"].mean(0), np.zeros(K), np.ones(K), np.zeros(K),
                     np.ones(K)], 1).astype("float32")
''',
        '''def statiche(D):
    K = D["r"].shape[1]
    return np.stack([D["m_r"].mean(0), np.zeros(K), np.ones(K), np.zeros(K),
                     np.ones(K)], 1).astype("float32")


VARIANTI_STATICA = ("congelata", "a", "b", "c")
L24_STATICA = 96


def variante_statica() -> str:
    """La variante della statica, da `OR3_STATICA` (E14); assente = congelata."""
    v = os.environ.get("OR3_STATICA", "") or "congelata"
    if v not in VARIANTI_STATICA:
        raise ValueError(f"OR3_STATICA={v!r}: ammessi {VARIANTI_STATICA}")
    return v


def statica_cella(stat, D, nodi, nn, t0, seme):
    """E14: la statica della cella secondo la variante (`protocol/E14.md`).

    `stat` e' `statiche(D)`; `nn` sono i nodi inseriti nell'episodio (prova, o
    validazione in un episodio di validazione), `nodi["addestramento"]` gli
    iniziali; `t0` l'installazione; `seme` quello DICHIARATO della cella.
        congelata   `stat` com'e' (bit per bit; la campagna del Paper 1)
        a           iniziali: media di m_r su [0, t0); nn: media su (t0, t0 + 24 h]
        b           iniziali: idem; nn: media delle coperture causali degli iniziali
        c           iniziali: non causale; nn: coperture non causali permutate fra
                    i nn, una permutazione per seme
    """
    v = variante_statica()
    if v == "congelata":
        return stat
    stat = np.array(stat, copy=True)
    m = D["m_r"].astype("float64"); t0 = int(t0)
    nn = np.asarray(nn, dtype="int64")
    ini = np.asarray(nodi["addestramento"], dtype="int64")
    cov_nc = stat[:, 0].astype("float64")
    if v in ("a", "b"):
        cov_c = m[:t0].mean(0)
        stat[:, 0] = cov_c.astype("float32")
        if v == "a":
            stat[nn, 0] = m[t0 + 1:t0 + L24_STATICA + 1, :].mean(0)[nn].astype("float32")
        else:
            stat[nn, 0] = np.float32(cov_c[ini].mean())
    else:
        rng = np.random.default_rng(int(seme))
        stat[nn, 0] = cov_nc[nn][rng.permutation(len(nn))].astype("float32")
    return stat
''')],
    "evoluzione/esperimenti/esegui_f0.py": [(
        '''from evoluzione.esperimenti.inserimento import statiche  # noqa: E402
''',
        '''from evoluzione.esperimenti.inserimento import statica_cella, statiche  # noqa: E402
'''), (
        '''            S = torch.as_tensor(stat[nodi["prova"]])
            for i_s, s in enumerate(semi_t):
                fE = percorso_E(a.out / "E_inserimento_griglia", c, p, int(s))
''',
        '''            stat0 = stat
            for i_s, s in enumerate(semi_t):
                stat = statica_cella(stat0, D, nodi, nodi["prova"], t0, int(dich[i_s]))   # E14
                S = torch.as_tensor(stat[nodi["prova"]])
                fE = percorso_E(a.out / "E_inserimento_griglia", c, p, int(s))
''')],
    "evoluzione/esperimenti/esegui_e2.py": [(
        '''from evoluzione.esperimenti.inserimento import statiche  # noqa: E402
''',
        '''from evoluzione.esperimenti.inserimento import statica_cella, statiche  # noqa: E402
'''), (
        '''            S_nuovi = torch.as_tensor(stat[nodi["prova"]])
            S_vet = torch.as_tensor(stat[nodi["addestramento"]])
            w_pesi = torch.as_tensor(pesi, dtype=torch.float32)
            for i_s, st in enumerate(semi_t):
                s = int(dich[i_s])
''',
        '''            stat0 = stat
            w_pesi = torch.as_tensor(pesi, dtype=torch.float32)
            for i_s, st in enumerate(semi_t):
                s = int(dich[i_s])
                stat = statica_cella(stat0, D, nodi, nodi["prova"], t0, s)               # E14
                S_nuovi = torch.as_tensor(stat[nodi["prova"]])
                S_vet = torch.as_tensor(stat[nodi["addestramento"]])
''')],
    "evoluzione/esperimenti/ricostruisci_predizioni.py": [(
        '''from evoluzione.esperimenti.inserimento import _modello_da_ck, statiche  # noqa
''',
        '''from evoluzione.esperimenti.inserimento import _modello_da_ck, statica_cella, statiche  # noqa
'''), (
        '''            stat = statiche(D)
            pesi = np.asarray(carica_pesi(
                a.out / ("pesi_pems04" if a.pems04 else "pesi_griglia"),
                c, p).vettore(), dtype="float64")
            for s in dich:
''',
        '''            stat0 = statiche(D)
            pesi = np.asarray(carica_pesi(
                a.out / ("pesi_pems04" if a.pems04 else "pesi_griglia"),
                c, p).vettore(), dtype="float64")
            for s in dich:
                stat = statica_cella(stat0, D, nodi, nodi["prova"], t0, int(s))        # E14
''')],
    "evoluzione/esperimenti/veterani_e3.py": [(
        '''    from evoluzione.esperimenti.inserimento import _modello_da_ck, statiche
''',
        '''    from evoluzione.esperimenti.inserimento import _modello_da_ck, statica_cella, statiche
'''), (
        '''        stat = statiche(D)
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                          dtype="float64")
        ini = nodi["addestramento"]
''',
        '''        stat = statica_cella(statiche(D), D, nodi, nodi["prova"], t0, s)          # E14
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                          dtype="float64")
        ini = nodi["addestramento"]
''')],
    "evoluzione/esperimenti/riselezione_rmon_test.py": [(
        '''    from evoluzione.esperimenti.inserimento import _modello_da_ck, statiche
''',
        '''    from evoluzione.esperimenti.inserimento import _modello_da_ck, statica_cella, statiche
'''), (
        '''        stat = statiche(D)
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                          dtype="float64")
        ck = out / ETICHETTA / f"ck_{BRACCIO}_{c}_p{p}_s{s}_u{u_eq}.pt"
''',
        '''        stat = statica_cella(statiche(D), D, nodi, nodi["prova"], t0, s)          # E14
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                          dtype="float64")
        ck = out / ETICHETTA / f"ck_{BRACCIO}_{c}_p{p}_s{s}_u{u_eq}.pt"
''')],
    "evoluzione/esperimenti/esegui_e4.py": [(
        '''    from evoluzione.esperimenti.inserimento import _modello_da_ck, statiche
''',
        '''    from evoluzione.esperimenti.inserimento import _modello_da_ck, statica_cella, statiche
'''), (
        '''        stat = statiche(D)
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
        cfgF = json.loads((out / "selezione_F_griglia" / "configurazione_F.json")
                          .read_text())["scelte"][c]
        st = seme_torch(s)
''',
        '''        stat = statica_cella(statiche(D), D, nodi, nn, t0, s)                      # E14
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
        cfgF = json.loads((out / "selezione_F_griglia" / "configurazione_F.json")
                          .read_text())["scelte"][c]
        st = seme_torch(s)
''')],
    "evoluzione/esperimenti/esegui_e5.py": [(
        '''    from evoluzione.esperimenti.inserimento import statiche
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, seme_torch
''',
        '''    from evoluzione.esperimenti.inserimento import statica_cella, statiche
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, seme_torch
'''), (
        '''    from evoluzione.esperimenti.inserimento import _modello_da_ck, statiche
''',
        '''    from evoluzione.esperimenti.inserimento import _modello_da_ck, statica_cella, statiche
'''), (
        '''        stat = statiche(D)
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
''',
        '''        stat = statica_cella(statiche(D), D, nodi, nn, t0, s)                      # E14
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
'''), (
        '''        stat = statiche(D)
        P_ = carica_pesi(out / et["pesi"], c, p)
''',
        '''        stat = statica_cella(statiche(D), D, nodi, nn, t0, s)                      # E14
        P_ = carica_pesi(out / et["pesi"], c, p)
''')],
    "evoluzione/esperimenti/esegui_e6.py": [(
        '''        pesi = np.asarray(P_.vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
        cfgF = _cfgF(out); scF = cfgF["scelte"]["PEMS08"]
''',
        '''        pesi = np.asarray(P_.vettore(), dtype="float64")
        w_t = torch.as_tensor(pesi, dtype=torch.float32)
        from evoluzione.esperimenti.inserimento import statica_cella
        stat = statica_cella(stat, D, nodi, nn, t0, s)                             # E14
        S = torch.as_tensor(stat[nn])
        cfgF = _cfgF(out); scF = cfgF["scelte"]["PEMS08"]
'''), (
        '''        pesi = np.asarray(P_.vettore(), dtype="float64"); w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
        cfgF = _cfgF(out); scF = cfgF["scelte"]["PEMS08"]
''',
        '''        pesi = np.asarray(P_.vettore(), dtype="float64"); w_t = torch.as_tensor(pesi, dtype=torch.float32)
        from evoluzione.esperimenti.inserimento import statica_cella
        stat = statica_cella(stat, D, nodi, nn, t0, s)                             # E14
        S = torch.as_tensor(stat[nn])
        cfgF = _cfgF(out); scF = cfgF["scelte"]["PEMS08"]
''')],
    "evoluzione/esperimenti/esegui_e6a.py": [(
        '''        pesi = np.asarray(P_.vettore(), dtype="float64"); w_t = torch.as_tensor(pesi, dtype=torch.float32)
        S = torch.as_tensor(stat[nn])
        cfgF = _cfgF(out); scF = cfgF["scelte"]["PEMS04"]
''',
        '''        pesi = np.asarray(P_.vettore(), dtype="float64"); w_t = torch.as_tensor(pesi, dtype=torch.float32)
        from evoluzione.esperimenti.inserimento import statica_cella
        stat = statica_cella(stat, D, nodi, nn, t0, s)                             # E14
        S = torch.as_tensor(stat[nn])
        cfgF = _cfgF(out); scF = cfgF["scelte"]["PEMS04"]
''')],
    "evoluzione/esperimenti/esegui_e8.py": [(
        '''    from evoluzione.esperimenti.inserimento import statiche
''',
        '''    from evoluzione.esperimenti.inserimento import statica_cella, statiche
'''), (
        '''        NORM, nr, nv = _normalizzazione(D, nodi, ist); x = _canali(D, nr, nv); stat = statiche(D)
''',
        '''        NORM, nr, nv = _normalizzazione(D, nodi, ist); x = _canali(D, nr, nv)
        stat = statica_cella(statiche(D), D, nodi, nn, t0, s)                      # E14
''')],
}

for f, subs in SOSTITUZIONI.items():
    p = Path(f); s = p.read_text()
    for vecchio, nuovo in subs:
        n = s.count(vecchio)
        assert n == 1, f"{f}: testo atteso trovato {n} volte, non 1:\\n{vecchio[:120]}"
        s = s.replace(vecchio, nuovo)
    compile(s, f, "exec")
    p.write_text(s)
    print(f"  {f}: {len(subs)} sostituzioni, compila")
print("  fatto: con OR3_STATICA assente il comportamento e' invariato (statica_cella restituisce l'oggetto ricevuto)")
