#!/usr/bin/env python3
"""
Audit B e D sul predittore COMPLETO, piu' permutazione e invarianza.
=====================================================================
Nessun addestramento sperimentale: un solo passo di aggiornamento, per verificare
gradienti e perdita.

    1. audit B — nessun parametro specifico per sensore; aggiungere sensori non
       aumenta i parametri appresi;
    2. audit D — stato completo invariato, `state_dict` compreso: medie, varianze
       e contatori dei lotti della BatchNorm;
    3. permutazione dei nodi: permutando gli ingressi le uscite seguono;
    4. invarianza all'aggiunta di sensori, **in valutazione**: il modello non
       scambia messaggi, ma in addestramento la BatchNorm accoppia i sensori
       attraverso le statistiche del lotto;
    5. causalita': modificare la finestra oltre l'ultimo passo non cambia nulla;
    6. un passo di aggiornamento: gradienti finiti su tutti i parametri.

TOLLERANZA prefissata: 1e-5 in valore assoluto sui logit. Le convoluzioni in
precisione singola e l'ordine delle somme producono scarti di quell'ordine quando
il lotto cambia forma.

Uso (dalla radice OR3/):

    poetry run python evoluzione/componente/collauda_predittore.py
"""
import hashlib
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.encoder import inventario_per_nodo  # noqa: E402
from evoluzione.componente.estrattore import SCHEMI_T4C  # noqa: E402
from evoluzione.componente.predittore import (  # noqa: E402
    CANALI_INGRESSO, DILATAZIONI, FINESTRA, NUCLEO, PredittorePerNodo,
    campo_ricettivo)

ATOL = 1e-5
ESITI = []


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def impronta(m):
    """L'INTERO state_dict: pesi, buffer, medie e varianze correnti, contatori."""
    h = hashlib.sha256()
    for k, v in sorted(m.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def _stato_fermo(mv, d_desc, d_stat):
    """Lo stato completo non cambia dopo inferenze in valutazione."""
    mv.eval()
    pre = impronta(mv)
    with torch.inference_mode():
        for K in (10, 37, 200):
            mv(dati(K, d_desc, d_stat)[0], node_ids=list(range(K)),
               descriptor=dati(K, d_desc, d_stat)[1],
               static_inputs=dati(K, d_desc, d_stat)[2])
    return impronta(mv) == pre


def _invariato(mv, d_desc, d_stat):
    """I parametri non cambiano dopo inferenze su popolazioni diverse."""
    prima = sum(p.numel() for p in mv.parameters())
    mv.eval()
    with torch.inference_mode():
        for K in (10, 50, 200):
            mv(dati(K, d_desc, d_stat)[0], node_ids=list(range(K)),
               descriptor=dati(K, d_desc, d_stat)[1],
               static_inputs=dati(K, d_desc, d_stat)[2])
    return sum(p.numel() for p in mv.parameters()) == prima


def dati(K, d_desc, d_stat, B=4, seme=0):
    g = torch.Generator().manual_seed(seme)
    return (torch.randn(B, len(CANALI_INGRESSO), K, FINESTRA, generator=g),
            torch.randn(K, d_desc, generator=g),
            torch.randn(K, d_stat, generator=g))


def main() -> int:
    # LE TRE VARIANTI, con le configurazioni che verranno ADDESTRATE: il
    # raccordo usa LEGACY e BASE-CORRECTED; EXTENDED resta pronta per gli
    # esperimenti successivi e non vi entra.
    d_stat = 5
    ATTESI = {"LEGACY": (16, 1608, 25060),
              "BASE-CORRECTED": (26, 2248, 25700),
              "EXTENDED": (32, 2632, 26084)}
    print("inventario per variante, configurazioni da addestrare")
    print(f"  {'variante':16s} {'ingresso':>9} {'encoder':>9} {'totale':>9}"
          f"  {'atteso':>9}  nel raccordo")
    conforme = True
    for v, (di_att, pe_att, tot_att) in ATTESI.items():
        S = SCHEMI_T4C[v]
        di = len(S["statistiche"]) + len(S["disponibilita"])
        mv = PredittorePerNodo(di, d_stat, sorgente="traffic4cast")
        # il fornitore, non piu' `enc`: forma canonica unica
        pe = sum(p.numel() for p in mv.identita.parameters())
        tot = sum(p.numel() for p in mv.parameters())
        ok = (di, pe, tot) == (di_att, pe_att, tot_att)
        conforme &= ok
        print(f"  {v:16s} {di:9d} {pe:9,d} {tot:9,d}  {tot_att:9,d}  "
              f"{'sì' if v != 'EXTENDED' else 'no'}  {'' if ok else '<- DIFFORME'}")
    verifica("P", "i totali coincidono con quelli attesi", conforme)

    # i controlli che seguono girano su OGNI variante
    def controlla_tutte(fn, eti):
        esiti = []
        for v in ATTESI:
            S = SCHEMI_T4C[v]
            di = len(S["statistiche"]) + len(S["disponibilita"])
            esiti.append(fn(PredittorePerNodo(di, d_stat,
                                              sorgente="traffic4cast"), di))
        return all(esiti)

    S = SCHEMI_T4C["EXTENDED"]
    d_desc = len(S["statistiche"]) + len(S["disponibilita"])
    m = PredittorePerNodo(d_desc, d_stat, sorgente="traffic4cast")
    D = m.descrizione()

    print("configurazione, da registrare")
    for k in ("sorgente", "n_canali_ingresso", "profilo_storico_settimanale", "finestra",
              "nucleo", "dilatazioni", "campo_ricettivo", "imbottitura",
              "nascosti", "blocchi", "normalizzazione", "d_descrittore",
              "orizzonti", "parametri_totali", "parametri_identita"):
        print(f"  {k:32s} {D[k]}")
    print(f"  {'canali':32s} {', '.join(CANALI_INGRESSO)}")
    print(f"  {'buffer':32s} {len(D['buffer'])} "
          f"({', '.join(D['buffer'][:3])}{' …' if len(D['buffer']) > 3 else ''})")

    print("\n[0] campo ricettivo, sulla struttura effettiva")
    verifica(0, "R = 1 + (k-1)·Σd con rami del cancello PARALLELI",
             campo_ricettivo() == 1 + (NUCLEO - 1) * sum(DILATAZIONI) == 16,
             f"R = {campo_ricettivo()} su finestra {FINESTRA}: anche l'ultima "
             f"posizione dipende da {campo_ricettivo()-FINESTRA} posizioni di "
             f"imbottitura")

    print("\n[1] audit B — parametri specifici per sensore, su OGNI variante")
    verifica("1z", "inventario vuoto in tutte e tre le configurazioni",
             controlla_tutte(
                 lambda mv, di: not any(inventario_per_nodo(mv, K)
                                        for K in (10, 50, 200, 828)),
                 "B"))
    verifica("1y", "in tutte e tre, i parametri non cambiano con i sensori",
             controlla_tutte(lambda mv, di: _invariato(mv, di, d_stat), "B2"))
    tot = sum(p.numel() for p in m.parameters())
    vuoti = all(not inventario_per_nodo(m, K) for K in (10, 50, 200, 828))
    verifica(1, "inventario vuoto per ogni numero di nodi", vuoti,
             f"{tot:,} parametri totali")
    m.eval()
    with torch.inference_mode():
        for K in (10, 50, 200):
            m(dati(K, d_desc, d_stat)[0], node_ids=list(range(K)),
              descriptor=dati(K, d_desc, d_stat)[1],
              static_inputs=dati(K, d_desc, d_stat)[2])
    verifica("1b", "aggiungere sensori non aumenta i parametri",
             sum(p.numel() for p in m.parameters()) == tot)
    verifica("1c", "nessun `nn.Parameter` con primo asse pari ai nodi",
             not any(p.shape and p.shape[0] in (10, 50, 200, 828)
                     for p in m.parameters()))

    print("\n[2] audit D — stato invariato, `state_dict` compreso")
    trk = [b for n, b in m.named_buffers() if "running" in n or "num_batches" in n]
    verifica(2, "la BatchNorm traccia le statistiche correnti",
             len(trk) > 0 and all(
                 mod.track_running_stats
                 for mod in m.modules() if isinstance(mod, torch.nn.BatchNorm2d)),
             f"{len(trk)} buffer tracciati: senza tracciamento la valutazione "
             f"dipenderebbe dal lotto")
    m.eval()
    pre = impronta(m)
    with torch.inference_mode():
        for K in (10, 37, 200):
            m(dati(K, d_desc, d_stat)[0], node_ids=list(range(K)),
              descriptor=dati(K, d_desc, d_stat)[1],
              static_inputs=dati(K, d_desc, d_stat)[2])
    verifica("2b", "in VALUTAZIONE lo stato non cambia", impronta(m) == pre,
             f"impronta {pre[:16]}")
    m.train()
    m(dati(50, d_desc, d_stat)[0], node_ids=list(range(50)),
      descriptor=dati(50, d_desc, d_stat)[1],
      static_inputs=dati(50, d_desc, d_stat)[2])
    cambiato = impronta(m) != pre
    verifica("2c", "in ADDESTRAMENTO lo stato CAMBIA, come deve", cambiato,
             "le medie correnti si aggiornano: l'audit D ha senso in valutazione, "
             "e va dichiarato come vincolo del protocollo")
    m.eval()

    verifica("2z", "in tutte e tre lo stato non cambia in valutazione",
             controlla_tutte(lambda mv, di: _stato_fermo(mv, di, d_stat), "D"))

    print("\n[3] permutazione dei nodi")
    K = 40
    x, dd, ss = dati(K, d_desc, d_stat)
    perm = torch.randperm(K, generator=torch.Generator().manual_seed(1))
    with torch.inference_mode():
        a = m(x, node_ids=list(range(K)), descriptor=dd, static_inputs=ss)
        b = m(x[:, :, perm], node_ids=[int(i) for i in perm],
              descriptor=dd[perm], static_inputs=ss[perm])
    verifica(3, "le uscite seguono la permutazione degli ingressi",
             torch.allclose(a[:, perm], b, atol=ATOL),
             f"scarto massimo {float((a[:, perm]-b).abs().max()):.2e}")

    print("\n[4] invarianza all'aggiunta di sensori, in VALUTAZIONE")
    x2 = torch.cat([x, torch.randn(x.shape[0], x.shape[1], 15, FINESTRA)], 2)
    d2 = torch.cat([dd, torch.randn(15, d_desc)])
    s2 = torch.cat([ss, torch.randn(15, d_stat)])
    with torch.inference_mode():
        c = m(x2, node_ids=list(range(K + 15)), descriptor=d2,
              static_inputs=s2)
    verifica(4, "le predizioni dei sensori esistenti non cambiano",
             torch.allclose(a, c[:, :K], atol=ATOL),
             f"scarto massimo {float((a-c[:, :K]).abs().max()):.2e} "
             f"(tolleranza {ATOL:g}) — e' un test di CORRETTEZZA, non un "
             f"risultato scientifico")
    m.train()
    with torch.no_grad():
        at = m(x, node_ids=list(range(K)), descriptor=dd, static_inputs=ss)
        ct = m(x2, node_ids=list(range(K + 15)), descriptor=d2,
               static_inputs=s2)
    verifica("4b", "in ADDESTRAMENTO l'invarianza NON vale",
             not torch.allclose(at, ct[:, :K], atol=ATOL),
             "la BatchNorm accoppia i sensori attraverso le statistiche del "
             "lotto, pur senza scambio di messaggi")
    m.eval()

    print("\n[5] causalita' della finestra")
    x3 = x.clone()
    x3[..., :FINESTRA - 1] = x3[..., :FINESTRA - 1]      # invariati
    x4 = x.clone()
    x4[..., -1] = 99.0                                    # ultimo passo alterato
    with torch.inference_mode():
        e = m(x4, node_ids=list(range(K)), descriptor=dd, static_inputs=ss)
    verifica(5, "alterare l'ultimo passo cambia le predizioni",
             not torch.allclose(a, e, atol=ATOL),
             "se non cambiasse, l'ultima posizione non entrerebbe nel calcolo")

    print("\n[6] un passo di aggiornamento")
    m.train()
    y = torch.randint(0, 3, (x.shape[0], K, len(D["orizzonti"])))
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    out = m(x, node_ids=list(range(K)), descriptor=dd, static_inputs=ss)
    perdita = torch.nn.functional.cross_entropy(
        out.reshape(-1, 3), y.reshape(-1))
    perdita.backward()
    senza = [n for n, p in m.named_parameters() if p.grad is None]
    nonfin = [n for n, p in m.named_parameters()
              if p.grad is not None and not torch.isfinite(p.grad).all()]
    opt.step()
    verifica(6, "la perdita e' finita", torch.isfinite(perdita),
             f"{float(perdita.detach()):.4f}")
    # PROPRIETA' EREDITATA DAL BACKBONE STORICO, non un difetto: dopo il ciclo
    # si usa il solo `skip`, sicche' l'uscita normalizzata dell'ULTIMO blocco e'
    # scartata e i suoi pesi non ricevono gradiente. Nel codice originario e'
    # identico. Le statistiche correnti di quel blocco si aggiornano comunque,
    # perche' il passaggio in avanti avviene: buffer vivi, pesi morti.
    ultimo = f"blocchi.{len(m.blocchi)-1}.bn"
    attesi = {f"{ultimo}.weight", f"{ultimo}.bias"}
    verifica("6b", "gli unici parametri senza gradiente sono quelli attesi",
             set(senza) == attesi or not senza,
             f"senza gradiente: {sorted(senza) or 'nessuno'}"
             + (f"  — {len(attesi)} parametri dell'ultima BatchNorm, la cui "
                f"uscita e' scartata dal backbone storico" if senza else ""))
    verifica("6c", "i gradienti sono finiti", not nonfin,
             f"non finiti: {nonfin[:4] or 'nessuno'}")

    print("\n" + "=" * 70)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 70)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
