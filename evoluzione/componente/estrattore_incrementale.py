#!/usr/bin/env python3
"""
Estrattore unificato — aggiornamento INCREMENTALE.
==================================================
Mantiene accumulatori correnti aggiornati a ogni osservazione, con rimozione
quando un campione esce dalla finestra.

NON RIUSA LA LOGICA DEL CALCOLO DIRETTO. Condivide con esso lo schema delle
caratteristiche e le convenzioni temporali — che devono coincidere — ma non
l'accumulazione: se la condividessero, condividerebbero anche l'errore, e il
confronto fra i due non proverebbe nulla.

GLI ACCUMULATORI. Per ciascun canale numerosita' e somme di primo e secondo
ordine; per ciascuna banda dell'ora locale numerosita', somma e passi attesi;
per le classi i conteggi; per le coppie consecutive le sei grandezze che
l'autocorrelazione richiede, piu' i conteggi di incremento e decremento.

LE COPPIE SONO LA PARTE DELICATA. Una coppia esiste fra due osservazioni
adiacenti nel deposito e distanti esattamente un passo, con entrambi gli estremi
validi. Quando un campione entra, puo' creare una coppia con il precedente;
quando esce, la distrugge con il successivo. Sbagliare uno dei due versi produce
un'autocorrelazione che deriva lentamente, ed e' il difetto che il confronto con
l'oracolo intercetta.

MEMORIA LIMITATA. Il deposito conserva al piu' `l_max` osservazioni: e' la
capacita' dichiarata, non una storia illimitata.

Uso:

    e = EstrattoreIncrementale(t0=50, L=96, schema="EXTENDED")
    for istante, r, f, o, cls, ora in flusso:
        e.ingest(istante, r, f, o, cls, ora)
    est = e.estrai(sensor_id="S1")
"""
from __future__ import annotations

from collections import deque

import numpy as np

from evoluzione.componente.estrattore import (
    CANALI, L_MAX, N_BANDE, NON_STIMABILE, SCHEMA_VERSIONE, SCHEMI, TAU,
    VERSIONE_IMPLEMENTAZIONE, Estrazione)


class EstrattoreIncrementale:
    def __init__(self, t0: int, L: int, schema: str = "EXTENDED",
                 l_max: int = L_MAX, reference_version: str = "",
                 norm: dict | None = None, canali_costanti=frozenset()):
        if schema not in SCHEMI:
            raise ValueError(f"schema ignoto: {schema}")
        if L > l_max:
            raise ValueError(f"finestra richiesta {L} oltre la capacita' {l_max}")
        self.t0, self.L, self.schema = int(t0), int(L), schema
        self.l_max, self.reference_version = int(l_max), reference_version
        self.norm = norm or {}
        self.canali_costanti = frozenset(canali_costanti)
        self.ns = SCHEMI[schema]["statistiche"]
        self.nq = SCHEMI[schema]["disponibilita"]
        self._dep = deque()                 # (istante, r, f, o, classe, ora)
        self._ultimo = None
        self.troncata = False
        # -- accumulatori ---------------------------------------------------
        # ACCUMULATORI TRASLATI. Calcolare la varianza come E[x^2] - E[x]^2 su
        # somme non traslate perde tutte le cifre significative quando la media
        # domina la dispersione: con media 1e6 e deviazione 1e-3 i due termini
        # coincidono nelle prime undici cifre. Si accumula (x - k), con k
        # fissato alla PRIMA osservazione valida del canale: la traslazione non
        # cambia la varianza ed e' compatibile con la rimozione, purche' k resti
        # costante per tutta la vita dell'accumulatore.
        self._n = {c: 0 for c in CANALI}
        self._s1 = {c: 0.0 for c in CANALI}
        self._s2 = {c: 0.0 for c in CANALI}
        self._k = {c: None for c in CANALI}
        self._kr = None      # traslazione del canale r, per bande e coppie
        self._bn = np.zeros(N_BANDE, dtype="int64")      # validi per banda
        self._bs = np.zeros(N_BANDE, dtype="float64")
        self._batt = np.zeros(N_BANDE, dtype="int64")    # passi attesi per banda
        self._cls = {1: 0, 2: 0, 3: 0}
        self._ncls = 0
        self._passi = 0
        # coppie consecutive: m, A, B, AA, BB, AB, incrementi, decrementi
        self._m = 0
        self._A = self._B = self._AA = self._BB = self._AB = 0.0
        self._inc = self._dec = 0

    # -- ingestione ---------------------------------------------------------
    def ingest(self, istante, r, f, o, classe, ora_locale):
        """Una misura alla volta. Rifiuta duplicati e fuori ordine."""
        istante = int(istante)
        if self._ultimo is not None and istante <= self._ultimo:
            raise ValueError(
                f"istante {istante} non successivo a {self._ultimo}: questa "
                "versione rifiuta duplicati e fuori ordine")
        if istante < self.t0:
            return self          # anteriore all'installazione: non entra
        self._ultimo = istante
        rec = (istante, float(r), float(f), float(o), int(classe), int(ora_locale))
        self._aggiungi(rec)
        self._pota()
        return self

    def ingest_batch(self, righe):
        for x in righe:
            self.ingest(*x)
        return self

    # -- accumulo -----------------------------------------------------------
    def _aggiungi(self, rec):
        ist, r, f, o, cls, ora = rec
        # la coppia si forma con il precedente, se adiacente di un passo
        if self._dep:
            pi, pr, *_ = self._dep[-1]
            if ist - pi == 1 and np.isfinite(pr) and np.isfinite(r):
                self._coppia(pr, r, +1)
        self._dep.append(rec)
        self._passi += 1
        for c, v in zip(CANALI, (r, f, o)):
            if np.isfinite(v):
                if self._k[c] is None:
                    self._k[c] = v
                d = v - self._k[c]
                self._n[c] += 1
                self._s1[c] += d
                self._s2[c] += d * d
        b = ora // 3
        self._batt[b] += 1
        if np.isfinite(r):
            if self._kr is None:
                self._kr = r
            self._bn[b] += 1
            self._bs[b] += r - self._kr
        if cls > 0:
            self._ncls += 1
            if cls in self._cls:
                self._cls[cls] += 1

    def _rimuovi(self):
        rec = self._dep.popleft()
        ist, r, f, o, cls, ora = rec
        # la coppia con il successivo si distrugge
        if self._dep:
            si, sr, *_ = self._dep[0]
            if si - ist == 1 and np.isfinite(r) and np.isfinite(sr):
                self._coppia(r, sr, -1)
        self._passi -= 1
        for c, v in zip(CANALI, (r, f, o)):
            if np.isfinite(v):
                d = v - self._k[c]
                self._n[c] -= 1
                self._s1[c] -= d
                self._s2[c] -= d * d
        b = ora // 3
        self._batt[b] -= 1
        if np.isfinite(r):
            self._bn[b] -= 1
            self._bs[b] -= r - self._kr
        if cls > 0:
            self._ncls -= 1
            if cls in self._cls:
                self._cls[cls] -= 1

    def _coppia(self, x, y, segno):
        if self._kr is None:
            self._kr = x
        d0 = y - x                      # la differenza NON va traslata
        x, y = x - self._kr, y - self._kr
        self._m += segno
        self._A += segno * x
        self._B += segno * y
        self._AA += segno * x * x
        self._BB += segno * y * y
        self._AB += segno * x * y
        if d0 > TAU:
            self._inc += segno
        elif d0 < -TAU:
            self._dec += segno

    def _pota(self):
        """Toglie i campioni usciti dalla finestra, e rispetta la capacita'."""
        t = self._ultimo
        span = (t - self.t0 + 1) if self.L < 0 else self.L
        if self.L < 0 and span > self.l_max:
            self.troncata = True
        span = min(span, self.l_max)
        basso = max(t - span, self.t0 - 1)
        while self._dep and self._dep[0][0] <= basso:
            self._rimuovi()

    # -- estrazione ---------------------------------------------------------
    def estrai(self, sensor_id: str = "") -> Estrazione:
        s = np.full(len(self.ns), NON_STIMABILE, dtype="float64")
        q = np.zeros(len(self.nq), dtype="float64")
        S = {k: i for i, k in enumerate(self.ns)}
        Q = {k: i for i, k in enumerate(self.nq)}
        manc = []
        P = self._passi

        def std(nome, x, centra=True):
            """La media si centra e si scala, la deviazione si scala soltanto."""
            mu, sd = self.norm.get(nome, (0.0, 1.0))
            sd = sd if sd else 1.0
            return (x - mu) / sd if centra else x / sd

        legacy = self.schema == "LEGACY"
        # media GLOBALE di addestramento, non della finestra: vedi la nota nel
        # calcolo diretto
        mu_glob = float(self.norm.get("media_r", (0.0, 1.0))[0]) if legacy else 0.0

        for c in CANALI:
            n = self._n[c]
            if f"copertura_{c}" in Q:
                q[Q[f"copertura_{c}"]] = n / P if P else 0.0
            if c == "r" and "copertura_r" in Q:
                q[Q["copertura_r"]] = n / P if P else 0.0
            if legacy:
                den = max(n, 1)
                k = self._k[c] if self._k[c] is not None else 0.0
                mu = k + self._s1[c] / den if n else 0.0
                var = max(self._s2[c] / den - (self._s1[c] / den) ** 2, 0.0)
                s[S[f"media_{c}"]] = std(f"media_{c}", mu)
                s[S[f"dev_{c}"]] = std(f"media_{c}", float(np.sqrt(var)),
                                       centra=False)
            elif n >= 1:
                mu = self._k[c] + self._s1[c] / n
                s[S[f"media_{c}"]] = std(f"media_{c}", mu)
                if n >= 2:
                    var = max(self._s2[c] / n - (self._s1[c] / n) ** 2, 0.0)
                    s[S[f"dev_{c}"]] = std(f"media_{c}", float(np.sqrt(var)),
                                           centra=False)
                else:
                    manc.append(f"dev_{c}")
            else:
                manc += [f"media_{c}", f"dev_{c}"]

        for b in range(N_BANDE):
            if f"disponibilita_banda_{b}" in Q:
                q[Q[f"disponibilita_banda_{b}"]] = (
                    self._bn[b] / self._batt[b] if self._batt[b] else 0.0)
            if self._bn[b]:
                s[S[f"banda_{b}"]] = std("media_r",
                                         self._kr + self._bs[b] / self._bn[b])
            elif legacy:
                s[S[f"banda_{b}"]] = std("media_r", mu_glob)
            else:
                manc.append(f"banda_{b}")

        # la copertura delle coppie appartiene al blocco CONDIVISO
        if "copertura_coppie" in Q:
            q[Q["copertura_coppie"]] = (self._m / max(P - 1, 1)
                                        if P > 1 else 0.0)

        if self.schema == "EXTENDED":
            for k in (1, 2, 3):
                if self._ncls:
                    s[S[f"freq_classe_{k}"]] = self._cls[k] / self._ncls
                else:
                    manc.append(f"freq_classe_{k}")
            m = self._m
            if m >= 2:
                mx, my = self._A / m, self._B / m
                vx = max(self._AA / m - mx * mx, 0.0)
                vy = max(self._BB / m - my * my, 0.0)
                cov = self._AB / m - mx * my
                if vx > 0 and vy > 0:
                    s[S["autocorr_1"]] = float(cov / np.sqrt(vx * vy))
                else:
                    manc.append("autocorr_1")
            else:
                manc.append("autocorr_1")
            if m >= 1:
                s[S["quota_incremento"]] = self._inc / m
                s[S["quota_decremento"]] = self._dec / m
            else:
                manc += ["quota_incremento", "quota_decremento"]

        if legacy:
            q[Q["quota_validi"]] = self._n["r"] / P if P else 0.0
            q[Q["codice_durata"]] = (1.0 if self.L < 0 else
                                     np.log1p(self.L) / np.log1p(672))
            manc = []
        t = self._ultimo
        eff = 0 if t is None else max(
            min(self.l_max if self.L < 0 else self.L, t - self.t0 + 1), 0)
        if "durata_nominale" in Q:
            nl = eff if self.L < 0 else self.L
            q[Q["durata_nominale"]] = np.log1p(min(nl, self.l_max)) / np.log1p(self.l_max)
        if "durata_effettiva" in Q:
            q[Q["durata_effettiva"]] = np.log1p(eff) / np.log1p(self.l_max)
        if "n_valide" in Q:
            q[Q["n_valide"]] = np.log1p(self._n["r"]) / np.log1p(self.l_max)

        return Estrazione(
            sensor_id=sensor_id, schema_version=SCHEMA_VERSIONE,
            implementation_version=VERSIONE_IMPLEMENTAZIONE,
            schema_name=self.schema, feature_names_and_order=self.ns,
            statistics=s, availability_names_and_order=self.nq, availability=q,
            requested_duration=self.L, effective_duration=eff,
            window_start=self._dep[0][0] if self._dep else None,
            window_end=self._dep[-1][0] if self._dep else None,
            reference_version=self.reference_version,
            n_osservazioni_finestra=P, non_stimabili=manc,
            note=("finestra vuota: nessuna statistica stimabile" if not P else
                  f"storia troncata alla capacita' del buffer "
                  f"({self.l_max} passi)" if self.troncata else ""))
