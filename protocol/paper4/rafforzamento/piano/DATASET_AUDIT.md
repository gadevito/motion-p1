# External dataset audit for the replication (plan §3)

Started 2026-11-16. Metadata and availability only: no target statistics, no thresholds, no model. Each candidate is scored on the criteria fixed before any candidate was looked at (plan §2–3); the ranking is written here before any forecasting metric exists. Files of every probe are kept with their fingerprints under `~/webtris_sonda/` (and the equivalent folders for the other candidates), outside the repository until the choice is frozen.

## Criteria (fixed) and what "ideal" means

| # | Criterion | Ideal | Minimum |
| --- | --- | --- | --- |
| C1 | reference required by the chosen outcome (speed limit per site, official source) | published per site by the data owner | derivable from a verifiable source (OSM `maxspeed`, national rule) |
| C2 | speed with interpretable units, timestamps, stable site ids, verifiable geography/topology | all four, documented | all four, partly reconstructed |
| C3 | duration and coverage | ≥ 12 months, ≥ 100 sites with ≥ 90 % of days at good quality, 15 min or finer | ≥ 9 months, ≥ 100 sites, ≤ 15 min |
| C4 | independence from data already analysed by us and from the development of the candidate model | never used by us; not among the benchmarks of MoGERNN/UIGNN | used by us only for a different question, declared |
| C5 | access and reproducibility | open API or bulk download, open licence, no account | free account, documented export |
| C6 | network type relative to the three T4C cities (urban arterials) | urban network | motorway corridor network, declared as a different regime |

Decision rule (plan §3): no candidate is chosen on model performance or on the ease of an outcome; if several pass the minimum, the ranking is C4, then C6, then C1, then C3; candidates and reasons for exclusion are archived.

## Candidate 1 — WebTRIS (National Highways, England) — PROBED

Probe 2026-11-16, bbox 52.35,-2.10 → 52.60,-1.70 (Birmingham: M6, M42, M5), September 2025 at 15 min for all 583 "Active" sites; daily quality January–October 2025 for the 261 sites with ≥ 95 % non-zero rows in September.

| | Finding |
| --- | --- |
| sites | 20 076 in England, 11 234 flagged Active; the flag is unreliable: 276 of 583 Active sites in the bbox returned zero data for the whole month |
| usable sites | 261 with ≥ 95 % non-zero 15-min rows in September; over Jan–Oct 2025, **188 with ≥ 90 % of days at quality ≥ 90** (157 at ≥ 95 %); 16 below 50 % |
| of which | main carriageways (A/B suffix): M6 66, M42 54, M5 29; slip roads (J/K/L/M): 38 |
| cadence, fields | 96 rows/day; `Avg mph`, `Total Volume`, volumes by 4 length classes and 12 speed bins; night rows with zero vehicles have speed 0 (to be treated as missing, not as 0 mph) |
| geography | MIDAS loops every ~500 m per direction; 156 of 261 sites have their opposite-direction twin within 100 m; three chains joined at the M6/M42, M5/M6 and M42/M5 junctions; extent ~25 × 28 km |
| C1 | national limit 70 mph on all three motorways: known for every site without history. **Caveat:** M42 J3a–J7 and M6 J4–J10a are smart motorways with variable mandatory limits on gantries, not in WebTRIS; the static limit is the reference, the effective one varies |
| C2 | yes; site ids stable (MIDAS road/chainage/direction), coordinates given; topology = road order by chainage + junction links, to be built from chainage and OSM |
| C3 | ≥ 12 months available (API back to 2015); 188 good sites ≥ 90 % of days; 15 min → ideal |
| C4 | never used by us; not a benchmark of MoGERNN or UIGNN (to be confirmed against `evoluzione/audit/AUDIT_MoGERNN.md` and the UIGNN paper) → ideal, pending that check |
| C5 | open API, no key, Open Government Licence → ideal |
| C6 | motorway corridor network → minimum, declared: spatial propagation along a line is physically stronger than in a city; a different regime, not a repeat of the urban setting |
| verdict | **passes the minimum on every criterion; ideal on C1 (with caveat), C3, C5; not urban (C6)** |

Open items: retry the 6 sites with empty API replies (10715, 10717, 10718, 10769, 10774, 10776); confirm C4 against the model audits; decide whether slip-road sites are nodes of the graph or excluded.

## Candidate 2 — NDW (Netherlands) — TO PROBE

What is known: national open data of loop detectors (`meetlocaties`), speed and flow per minute per lane, motorways **and** urban/provincial roads; historical export through Dexter (free account); site metadata with coordinates and road id. To verify: whether the per-site speed limit is in the site metadata or must come from NWB/OSM (C1); number of urban sites in one city with ≥ 90 % availability over 2025 (C3, C6); licence (C5); use by the candidate models (C4).

Probe to run: export one day (any) of one province to learn the schema, then availability of 2025 for the sites of one urban area (Rotterdam or Utrecht), metadata only.

## Candidate 3 — Flanders Verkeerscentrum (Belgium) — TO PROBE (cheap)

Open per-minute loop data (speed per vehicle class, counts) for Flemish motorways; XML feed and historical files. Motorway network like WebTRIS (C6 minimum), so useful only if WebTRIS fails C4 or C3. Probe only after NDW.

## Candidate 4 — Austin radar sensors (USA) — TO CHECK BEFORE PROBING

Open data portal, Wavetronix radar, 15-min speed and volume on urban arterials (~70–100 sensors). **A file `OLD/austin/radar/radar_completo.json` exists in the OR3 deliverable inputs (PROTOCOLLO.md line 251)**: its previous use must be established before anything else (C4). If used only for the measurement study, it is in the same position as M-30; if used in model development, excluded.

## Candidate 5 — Madrid M-30 2024 (reserve, already analysed)

284 loops, full year 2024 at 15 min, speed/flow/occupancy. Used in P4A (measurement comparison): C4 minimum, declared. C1: speed limits of the M-30 (70–90 km/h) verifiable from OSM. C6: ring motorway. Reserve.

## Excluded without probing

- PEMS-BAY, METR-LA, PEMS03/04/07/08 (California): standard benchmarks of inductive models, including (to confirm) MoGERNN → fail C4.
- HERE Baronissi collection: variable segment set, 9 of 406 segments ≥ 90 % coverage, 103 interruptions, two collection regimes → fail C2, C3 (`FATTIBILITA_HERE_BARONISSI_20261116.md`).
- Madrid urban loops (open portal, new period): intensity/occupancy/load, speed only on M-30 → fail C2 for a speed outcome.
- Paris, Dublin, London TfL counts: no speed → fail C2.

## Stop rule

The audit stops when a candidate is ideal on C4, C6, C1 and C3 (an urban network, never used by us or by the model, with per-site limits and a year of good data). If none is, the choice is between the best motorway candidate (WebTRIS, if C4 is confirmed) and M-30, decided by the co-authors on this sheet. Two replications (one urban, one motorway) are a budget decision, not a default.
