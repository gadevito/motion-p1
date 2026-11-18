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

## Candidate 1 — WebTRIS (National Highways, England) — PROBED, NOT ACQUIRED

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
| C4 | never used by us; not a benchmark of MoGERNN (METR-LA and PEMS only, `evoluzione/audit/AUDIT_MoGERNN.md`, checked 2026-11-16) → ideal |
| C5 | open API, no key, Open Government Licence → ideal |
| C6 | motorway corridor network → minimum, declared: spatial propagation along a line is physically stronger than in a city; a different regime, not a repeat of the urban setting |
| verdict | **passes the minimum on every criterion; ideal on C1 (with caveat), C3, C5; not urban (C6)** |

Open items: retry the 6 sites with empty API replies (10715, 10717, 10718, 10769, 10774, 10776); confirm C4 against the model audits; decide whether slip-road sites are nodes of the graph or excluded.

## Candidate 2 — NDW, Rotterdam (Netherlands) — PROBED AND ACQUIRED

Probes 2026-11-16/17: site configuration (20 619 sites nationwide, all 60-s, flow + speed); one-week Expert export (1–8 Sept 2025, nationwide, 35 GB) filtered to the Rotterdam bbox 51.85–51.98 N, 4.35–4.60 E; annual data-quality sheet for 20 municipal sites; then the full acquisition 1 June – 31 Dec 2025 in 31 seven-day exports, filtered to the same bbox and frozen (`pacchetto_ndw_rotterdam_2025/`, file `ndw_rotterdam_2025-06-01_2025-12-31.csv.gz`, 402 509 566 site-minutes, sha256 `16acf38e13c4ff780bdb94bdc335f89875c5b4901b166f301ad9e01c8a4d82a6`, `MANIFEST.tsv`, `PROVENIENZA.md`).

| | Finding |
| --- | --- |
| sites in the bbox | 1 628 in the configuration, 1 625 with data: 1 266 motorway ring (RWS01: A4/A13/A15/A16/A20), 359 urban (Rotterdam municipality GRT02 194, MRDH region RDH01 54, port HBR01 46, neighbouring municipalities GEO* 63, GRT06 2), 18 provincial |
| cadence, fields | 1 min; flow per vehicle class and lane, speed per class and lane with number of vehicles used; aggregated by us to site-minute (total flow; flow-weighted mean of valid speeds) |
| period | 1 June – 31 Dec 2025, 215 days, continuous; the export omits every day 00:00–01:59 local until 25 Oct and 00:00–00:59 local from 26 Oct (fixed nightly gap) — fewer hours missing than the T4C cities themselves lack (~12 h/day covered there) |
| availability, urban sites | present ≥ 90 % of the period's minutes: 357/359; valid speed ≥ 70 % of minutes: 273; ≥ 80 %: 195 (missing minutes are mostly nights with no vehicle in the minute; at 15 min this rises) |
| availability, motorway | 940 present ≥ 90 %; ~320 RWS sites start publishing in late October (structural change, documented); 876 with valid speed ≥ 70 % |
| annual quality (operator's sheet, 20 municipal sites) | 15 without any technical exclusion in 2025, 4 with 7–28 days excluded, 1 dead since 2020; 3 flagged "deviating location" (near signals) |
| C1 | speed limits not in the NDW configuration; derivable per site from OSM `maxspeed` or from the NDW traffic-signs dataset (`verkeersborden`, same portal) → minimum, possibly ideal after that check; urban limits 50/70 km/h, ring 80–100 |
| C2 | yes: stable ids, coordinates, lanes, carriageway; topology from OSM |
| C3 | 7 months (same length and season as Madrid/Melbourne), 273 urban + 876 motorway sites → ideal |
| C4 | never used by us; not a benchmark of MoGERNN (METR-LA/PEMS only, per `AUDIT_MoGERNN.md`) → ideal |
| C5 | open Dexter export without account (Expert module, 8-day limit, captcha); licence **CC0 1.0** per the NDW open-data terms of use (https://docs.ndw.nu/algemeen/data-gebruiksvoorwaarden/, checked 2026-11-18), attribution appreciated, not required → ideal |
| C6 | **urban network** (arterials of a city of 650 000, with the motorway ring available as a separate layer) → ideal |
| verdict | **passes the minimum on every criterion; ideal on C3, C4, C5, C6; C1 after the limits are derived. The only urban candidate.** |

Site-selection rule for the replication, fixed now and applied only in E15: presence ≥ 90 % of the period's minutes and valid speed ≥ 70 %; urban layer primary, motorway ring as a declared secondary layer or excluded. Hours of day restricted to those covered by the T4C cities.

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

## Outcome (2026-11-18)

NDW-Rotterdam is ideal on C3, C4, C5 and C6 and acquired; C1 (per-site limits from OSM or the NDW traffic-signs dataset) is the one open item, resolvable without new data. WebTRIS is verified and ideal on C1/C3/C5 but is a motorway corridor (C6 minimum): it stays as the second replication if the co-authors decide to fund it (+50 final fits), otherwise as the archived alternative. M-30 is the reserve. Decision requested from the co-authors: NDW-Rotterdam only, or NDW-Rotterdam + WebTRIS.
