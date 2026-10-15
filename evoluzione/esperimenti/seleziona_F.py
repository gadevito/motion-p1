#!/usr/bin/env python3
"""
Fase 2 — selezione della configurazione di adattamento di F.
=============================================================
Sei combinazioni per ciascun GRUPPO (citta', partizione, seme), valutate su un
**episodio di validazione** separato dal test. **UNA configurazione per citta'.**

    passo di apprendimento   1e-3, 1e-2
    aggiornamenti massimi    10, 50, 200

IL PERIMETRO DI VALUTAZIONE e' la GIORNATA prescritta: ventiquattro ore dopo
l'acquisizione, con le sole origini i cui bersagli fino a due ore vi ricadano.
**Non il resto della validazione**: usarlo sarebbe un'estensione
dell'emendamento, non un riallineamento.

**ORIGINE = timestamp previsionale distinto.** Il manifesto riporta
separatamente timestamp distinti, istanze nodo-timestamp e celle per orizzonte.

LA REGOLA, dichiarata qui: wCE mediata sui quattro orizzonti, poi sulle
inizializzazioni, poi sulle tre partizioni con uguale peso. **A parita' numerica
si preferisce, nell'ordine: meno aggiornamenti, poi passo minore.**

I CINQUE VINCOLI, verificati a ogni candidato:

    1. ogni combinazione RIPARTE da E: nessun adattamento cumulativo;
    2. ottimizzatore NUOVO per ciascuna;
    3. al test si trasferiscono i soli IPERPARAMETRI;
    4. il punto di controllo E resta IMMUTATO;
    5. nodi di validazione e test hanno REGISTRI DISTINTI.

**Le copie si eseguono in sequenza**: non risiedono tutte in memoria.

IL MANIFESTO e' **uno per gruppo**, con le sei combinazioni dentro: griglia,
aggiornamenti eseguiti, seme, impronte iniziale e finale, costo, metrica di
validazione e regola applicata.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/seleziona_F.py --piano
    poetry run python evoluzione/esperimenti/seleziona_F.py
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.fasi import (  # noqa: E402
    CONTESTI, PARTIZIONI, PrerequisitoMancante, percorso_E,
    verifica_selezione_F)
from evoluzione.esperimenti.semi import (  # noqa: E402
    SEME_PARTIZIONE, configurazione)
from evoluzione.componente.adattamento import (  # noqa: E402
    adatta, carica_E, copia_da_E, verifica_vincoli)
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.componente.episodio import (  # noqa: E402
    EpisodioVuoto, giornata_valutazione, lotti_episodio, origini_adattamento,
    origini_valutazione, riepilogo)
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _canali, _carica, _normalizzazione, _partizioni, _perdita)
from evoluzione.analisi.pesi import carica as carica_pesi  # noqa: E402

PASSI = (1e-3, 1e-2)
AGGIORNAMENTI = (10, 50, 200)
L24 = 96
# il calendario dell'episodio di VALIDAZIONE, congelato nel disegno 2.4 dal
# requisito di ammissibilita': primo t0 con almeno 90 marche in 24 ore
CALENDARIO_VAL = {"Madrid": (7392, 7488), "Londra": (7389, 7485),
                  "Melbourne": (7251, 7347)}
# il confine superiore del periodo di validazione, oltre il quale non si valuta
FINE_VAL = {"Madrid": 8887, "Londra": 8966, "Melbourne": 8806}
# IL CALENDARIO CON LA REGOLA APPROVATA: tutti i 96 intervalli di (t0, t1]
# e la giornata successiva completa. Melbourne cambia rispetto al calendario
# precedente (7251), che violava la condizione sulla giornata di valutazione.
# Si RICALCOLA a ogni esecuzione e si confronta con questa tabella.
CALENDARIO_VAL_GRIGLIA = {"Madrid": (7392, 7488), "Londra": (7389, 7485),
                          "Melbourne": (7392, 7488)}


def griglia():
    """L'ordine di preferenza a parita': meno aggiornamenti, poi passo minore."""
    return [(b, e) for b in AGGIORNAMENTI for e in PASSI]


def scegli(punteggi):
    """Il minimo; a parita' entro 1e-9, il primo della griglia."""
    if not punteggi:
        return None
    m = min(punteggi.values())
    for k in griglia():
        if k in punteggi and punteggi[k] - m <= 1e-9:
            return k
    return None


def aggrega(per_gruppo, contesto):
    """wCE media sugli orizzonti (gia' fatta), poi sui semi, poi sulle
    partizioni con UGUALE PESO."""
    fuori = {}
    for k in griglia():
        per_part = []
        for p in PARTIZIONI:
            v = [d["punteggi"].get(str(k), d["punteggi"].get(k))
                 for (c, pp, _), d in per_gruppo.items()
                 if c == contesto and pp == p]
            v = [x for x in v if x is not None and np.isfinite(x)]
            if v:
                per_part.append(float(np.mean(v)))      # media sui semi
        if per_part:
            fuori[k] = float(np.mean(per_part))         # poi sulle partizioni
    return fuori


def main() -> int:
    ap = argparse.ArgumentParser(description="fase 2: selezione di F")
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--protocollo", default="griglia",
                    choices=("griglia", "principale", "storico"),
                    help="quali punti E usare; la selezione storica non si "
                         "sovrascrive")
    from evoluzione.esperimenti.inserimento import applica_statica, argomento_statica
    argomento_statica(ap)
    a = ap.parse_args()
    applica_statica(a.statica)

    _, dich, semi_torch = configurazione(inserimento=True)
    # LE DUE SERIE IN CARTELLE DISTINTE: la selezione storica, fatta sui punti
    # E a 35 aggiornamenti, e' un risultato della procedura precedente e non si
    # sovrascrive. La scelta `(200, 0.01)` NON si trasferisce ai nuovi E.
    dir_E = a.out / {"storico": "E_inserimento",
                     "principale": "E_inserimento_principale",
                     "griglia": "E_inserimento_griglia"}[a.protocollo]
    dir_sel = a.out / {"storico": "selezione_F",
                       "principale": "selezione_F_principale",
                       "griglia": "selezione_F_griglia"}[a.protocollo]

    print("=" * 84)
    print("FASE 2 — SELEZIONE DELLA CONFIGURAZIONE DI F")
    print("=" * 84)
    print(f"  griglia: {len(griglia())} combinazioni, ordine di preferenza")
    print(f"     " + ", ".join(f"({b},{e:g})" for b, e in griglia()))
    print(f"  **UNA configurazione per citta'**, non per nodo")
    print(f"  regola: wCE media sugli orizzonti, poi sui semi, poi sulle "
          f"partizioni")
    print(f"  a parita': meno aggiornamenti, poi passo minore")
    n = len(a.contesto) * len(PARTIZIONI) * len(semi_torch)
    print(f"\n  gruppi di sei candidati: {n} | adattamenti: {n * len(griglia()):,}")

    try:
        r = verifica_selezione_F(dir_E, semi_torch, a.contesto)
        # NEL PRINCIPALE non basta che il file dei pesi esista: il ciclo salva
        # il migliore a ogni miglioramento, e un'esecuzione interrotta ne
        # lascia uno che SEMBRA completo. Serve il marcatore `.fatto`.
        if a.protocollo in ("principale", "griglia"):
            senza = [percorso_E(dir_E, c, p, int(s)).name
                     for c in a.contesto for p in PARTIZIONI
                     for s in semi_torch
                     if not percorso_E(dir_E, c, p, int(s)).with_name(
                         percorso_E(dir_E, c, p, int(s)).name + ".fatto"
                     ).exists()]
            if senza:
                raise PrerequisitoMancante(
                    f"{len(senza)} punti E SENZA marcatore di completamento, "
                    f"per esempio {senza[:3]}: possono essere addestramenti "
                    f"interrotti. Completare prima la fase E.")
        print(f"\n  prerequisiti verificati: {r['punti_di_controllo']} punti di "
              f"controllo E, leggibili e con la mappa nodo-riga")
    except PrerequisitoMancante as e:
        print(f"\n{e}")
        return 1

    if a.piano:
        print(f"\n  --piano: nessuna esecuzione avviata.")
        print(f"  ogni gruppo produce UN manifesto con le sei combinazioni "
              f"dentro")
        return 0

    dir_sel.mkdir(parents=True, exist_ok=True)
    per_gruppo, tempi, guai = {}, [], []
    n_fatte = 0
    for c in a.contesto:
        D = _carica(c, a.out / "maschere")
        ok_g = GR.passi_regolari(D["ts"]) if a.protocollo == "griglia" else None
        if ok_g is not None:
            t0v, t1v = CALENDARIO_VAL_GRIGLIA[c]
            e_ = D["r"].shape[0] - GR.MAX_ORIZZ
            ricalc = GR.primo_t0(D["ts"], ok_g, int(e_ * .70), int(e_ * .85),
                                 giornata_dopo=True)
            if ricalc != t0v:
                raise PrerequisitoMancante(
                    f"{c}: la regola approvata da' t0={ricalc}, la tabella "
                    f"dice {t0v}. Il calendario va verificato prima di "
                    f"selezionare.")
        else:
            t0v, t1v = CALENDARIO_VAL[c]
        for p in PARTIZIONI:
            gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])}
            nodi, ist = _partizioni(D, gen)
            NORM, nr, nv = _normalizzazione(D, nodi, ist)
            x = _canali(D, nr, nv)
            # le STATICHE, costruite come nell'addestramento: la copertura
            # media della sorgente piu' quattro colonne fisse
            from evoluzione.esperimenti.inserimento import statica_cella, statiche
            stat = statica_cella(statiche(D), D, nodi, nodi["validazione"], t0v, 0)
            # la firma e' (dir_pesi, contesto, partizione)
            w = torch.as_tensor(
                # I PESI DELLA STESSA PIPELINE dei punti E: con la griglia sono
                # ricalcolati sulle origini ammissibili
                carica_pesi(a.out / ("pesi_griglia" if a.protocollo == "griglia"
                                     else "pesi"), c, p).vettore(),
                dtype=torch.float32)
            # I NODI DELL'EPISODIO sono quelli di VALIDAZIONE INDUTTIVA
            nodi_ep = nodi["validazione"]
            # CONVENZIONE (t0, t1] e GRIGLIA: la riga t0 non si usa, e nessuna
            # finestra attraversa un salto
            o_ad = (GR.origini_acquisizione(ok_g, t0v, t1v) if ok_g is not None
                    else origini_adattamento(t0v, t1v))
            # LA GIORNATA prescritta, non il resto della validazione
            fine_g = giornata_valutazione(D["ts"], t1v, FINE_VAL[c])
            o_va = (GR.origini_dopo(ok_g, t1v, fine_g + 1) if ok_g is not None
                    else origini_valutazione(D["ts"], t1v, FINE_VAL[c]))
            for s in semi_torch:
                f_man = dir_sel / f"sel_{c}_p{p}_s{s}.json"
                if f_man.exists():
                    per_gruppo[(c, p, int(s))] = json.loads(f_man.read_text())
                    continue
                fE = percorso_E(dir_E, c, p, int(s))
                dE, nodi_in, imp_E = carica_E(fE, 5)
                punteggi, dettagli = {}, []
                t_gruppo = time.time()
                # I LOTTI, costruiti UNA VOLTA per gruppo. **Non `per_nodo`**:
                # l'adattamento e' vettorizzato ed equivalente, e un lotto per
                # nodo costava 135 passaggi in avanti per aggiornamento.
                lotti = lotti_episodio(x, D["classe"], stat, nodi_ep, o_ad)
                lotti_val = lotti_episodio(x, D["classe"], stat, nodi_ep,
                                           o_va)
                for b, e in griglia():
                    # COPIA INDIPENDENTE, in sequenza: nessun adattamento
                    # cumulativo, ottimizzatore nuovo
                    mF, forn = copia_da_E(dE, nodi_in, nodi_ep, 5)
                    imp_ini = float(forn.nuovi.detach().abs().sum())
                    reg_ad = []
                    t_c = time.time()
                    print(f"    {c[:3]} p{p} s{int(s):<11d} "
                          f"({b:3d},{e:g})", end="", flush=True)
                    n_agg = adatta(mF, forn, lotti, w, e, b, reg_ad)
                    dt = time.time() - t_c
                    mF.eval()
                    with torch.inference_mode():
                        L = []
                        for Xv, nv_, Yv, Mv, Sv in lotti_val:
                            out = mF(Xv, node_ids=nv_, static_inputs=Sv)
                            lv, _ = _perdita(out, Yv, Mv, w)
                            L.append(float(lv))
                    punteggi[(b, e)] = float(np.mean(L)) if L else float("nan")
                    print(f"  wCE {punteggi[(b, e)]:.5f}  {dt:5.1f}s",
                          flush=True)
                    verifica_vincoli(mF, forn, dE, imp_E,
                                     dE["state_dict"]["identita.embedding"], fE)
                    dettagli.append({
                        "aggiornamenti_richiesti": b, "passo": e,
                        "aggiornamenti_eseguiti": n_agg,
                        "impronta_iniziale": imp_ini,
                        "impronta_finale": float(
                            forn.nuovi.detach().abs().sum()),
                        "wCE_validazione": punteggi[(b, e)],
                        "secondi": dt, "nodi_adattati": len(lotti),
                        "registro_adattamento": reg_ad})
                    del mF, forn
                rip_ac = riepilogo(D["classe"], nodi_ep, o_ad, t0v, t1v)
                rip_va = riepilogo(D["classe"], nodi_ep, o_va, t1v, fine_g)
                man = {"contesto": c, "partizione": p, "seme": int(s),
                       "acquisizione": {
                           "inizio": int(t0v), "fine": int(t1v),
                           "istante_inizio": str(D["ts"][t0v]),
                           "istante_fine": str(D["ts"][t1v]), **rip_ac},
                       "valutazione": {
                           "inizio": int(t1v), "fine": int(fine_g),
                           "istante_inizio": str(D["ts"][t1v]),
                           "istante_fine": str(D["ts"][fine_g]), **rip_va},
                       "impronta_E": imp_E, "punto_di_controllo_E": fE.name,
                       "punteggi": {str(k): v for k, v in punteggi.items()},
                       "candidati": dettagli,
                       "regola": "wCE media sugli orizzonti, poi sui semi, poi "
                                 "sulle partizioni; a parita': meno "
                                 "aggiornamenti, poi passo minore",
                       "versione_protocollo": "2.4",
         "protocollo_E": a.protocollo,
         "cartella_E": str(dir_E),
                       "protocollo_E": a.protocollo,
                       "istante": datetime.now(timezone.utc).isoformat()}
                f_man.write_text(json.dumps(man, indent=2, ensure_ascii=False))
                per_gruppo[(c, p, int(s))] = man
                tempi.append(time.time() - t_gruppo)
                n_fatte += 1
                print(f"  {c:11s} p{p} s{int(s):11d}  "
                      + " ".join(f"{punteggi[k]:.4f}" for k in griglia())
                      + f"  {tempi[-1]:5.1f}s")

    # ---- l'aggregazione e la scelta, UNA per citta' ----------------------
    print(f"\n{'=' * 84}\nSCELTA PER CITTA'\n{'=' * 84}")
    # le scelte gia' congelate in esecuzioni precedenti si CONSERVANO: una
    # esecuzione su una citta' sola non deve cancellare le altre
    f_pre = dir_sel / "configurazione_F.json"
    pre = json.loads(f_pre.read_text()) if f_pre.exists() else {}
    scelte = dict(pre.get("scelte", {}))
    aggregati = dict(pre.get("aggregati", {}))
    for c in a.contesto:
        gruppi = {k: v for k, v in per_gruppo.items() if k[0] == c}
        attese = len(PARTIZIONI) * len(semi_torch)
        if len(gruppi) < attese:
            print(f"  {c}: {len(gruppi)}/{attese} gruppi — SELEZIONE SOSPESA")
            print(f"     non si sceglie su un insieme incompleto")
            continue
        agg = aggrega(gruppi, c)
        aggregati[c] = {str(k): v for k, v in agg.items()}
        k = scegli(agg)
        scelte[c] = {"aggiornamenti": k[0], "passo": k[1],
                     "wCE": agg[k], "gruppi": len(gruppi)}
        print(f"\n  {c}")
        for kk in griglia():
            m = " <- SCELTA" if kk == k else ""
            print(f"     ({kk[0]:3d}, {kk[1]:g})  {agg.get(kk, float('nan')):.6f}{m}")

    # LA CONFIGURAZIONE SI CONGELA SOLO SE COMPLETA su TUTTE le citta' del
    # protocollo, non su quelle di questa esecuzione: con `--contesto Madrid`
    # il confronto con `a.contesto` sarebbe soddisfatto da una citta' sola, e
    # la fase di prova partirebbe senza le altre due.
    completa = all(c in scelte for c in CONTESTI)
    f_cfg = dir_sel / "configurazione_F.json"
    f_cfg.write_text(json.dumps(
        {"congelata": completa,
         "citta_del_protocollo": list(CONTESTI),
         "citta_con_scelta": sorted(scelte),
         "mancanti": [c for c in CONTESTI if c not in scelte],
         "scelte": scelte, "aggregati": aggregati,
         "griglia": [list(k) for k in griglia()],
         "regola_spareggio": "meno aggiornamenti, poi passo minore",
         "calendario_validazione": (CALENDARIO_VAL_GRIGLIA
                                    if a.protocollo == "griglia"
                                    else CALENDARIO_VAL),
         "griglia_temporale": ("reale" if a.protocollo == "griglia"
                               else "indice"),
         "convenzione_estremi": ("(t0, t1]" if a.protocollo == "griglia"
                                 else "[t0, t1], storica"),
         "versione_protocollo": "2.4",
         "istante": datetime.now(timezone.utc).isoformat()},
        indent=2, ensure_ascii=False))
    print(f"\n  {n_fatte} gruppi eseguiti")
    if tempi:
        print(f"  COSTO: mediana {np.median(tempi):.1f}s per gruppo "
              f"({len(griglia())} adattamenti), proiezione per 108: "
              f"{108 * np.median(tempi) / 60:.0f} minuti")
    manca = [c for c in CONTESTI if c not in scelte]
    print(f"  configurazione in {f_cfg}, "
          f"{'CONGELATA' if completa else 'NON congelata'}")
    if manca:
        print(f"  mancano: {manca} — la fase di prova NON parte finche' la")
        print(f"  configurazione non e' completa su tutte e tre le citta'.")
    return 0 if completa else 1


if __name__ == "__main__":
    raise SystemExit(main())
