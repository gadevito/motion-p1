# E12-quater — The neighbour net of the calendar, with a symmetric fallback

**Pre-registration.** Date ____ · commit 656c409 (code `e12quater.py` 461899633f189f8a, `e12ter.py` e8c8d17e99e4008b,
`e12bis.py` 27adfe03f24647e8, `e12.py` 3ec453d15372b217, `p4b.py` 926061038a7472a3, `e9.py` 4dd5628af8879511;
preflight log `e12quater_preflight.log` e537ad3752ef9299) · launched by Fabio Palomba (Mac M3 Max, CPU) · preflight
8/8 · cost ≤ 7.2 s per (city, *f*, seed), ≈ 0.12 h for the 60 pairs (`e12quater_costo.json` 99821e3bc2028e60; load
average 3.1–3.7: an upper bound).

Draft of 2026-11-08, on the decision of the internal review of 2026-11-08 (21:45, item 2); approved at 22:00 with
the full fallback chain and a control for each link. No training. **No
computation on test before the signature**, except the preflight, which reads no test target. E12-ter stays as it
is (frozen record dda3b8f); E12-quater is a new, declared analysis.

signed: ____

## Question

In E12-ter, a row of the table with the neighbour (slot, neighbour's class, distance bin, horizon) with fewer than
20 pairs falls back to the E12-bis row, which has no calendar, while the calendar-only table keeps the calendar.
The difference between the two tables therefore mixes the value of the neighbour with the loss of the calendar
wherever rows are thin: overall 6–66% of the test lookups fall back, and up to 94% of the validation lookups in
the outer bins of Madrid and London (E12-ter preflight). E12-quater removes that asymmetry. It asks:

- net of the calendar, what is the neighbour's class worth when a thin row falls back to the calendar itself?
- does the reading of E12-ter within 250 m change?
- what remains, beyond 250 m, of the losses that E12-ter reported?

## Design

**Identical to E12-ter** (perimeter, pairs, slots of *t* + *h*, 168 hour-of-week slots, distance bins, N_min = 20,
ε = 0.05, transformation *q*′ = 0.95·*q* + 0.05·prior and *p* ∝ W·*q*′, metrics, resample, replicate indices),
with one change, chosen before the signature:

**Fallback (the one change): the full chain.** For a hidden segment at origin *t* and horizon *h*:

1. **neighbour row** (slot(*t* + *h*), *b*, bin(*d*), *h*), if a neighbour with a valid class exists and the row
   holds at least N_min pairs;
2. otherwise the **calendar row** (slot(*t* + *h*), *h*), if it holds at least N_min pairs (this includes the case
   with no valid neighbour, which in E12-ter went to the prior);
3. otherwise the **prior**.

The calendar-only table uses links 2 and 3 only. Wherever link 1 is not used, E12-quater and the calendar-only
table therefore give the same forecast, whether the calendar row is used or itself falls back to the prior; their
difference comes only from rows that carry the neighbour.

Alternative considered and not chosen: shrinkage of every row towards the calendar-only row,
*q* = (*n*·*q*_row + κ·*q*_cal)/(*n* + κ). It adds a parameter κ that would have to be fixed without test data; the
fallback keeps the threshold of E12-ter and changes only its target. Choice confirmed by the internal review
(2026-11-08).

**Shares of the links before the signature** (preflight, validation lookups, seed 0, no target read): in the
0–250 m bin the neighbour row serves 93–100% of the lookups and the calendar row the rest; in the outer bins of
Madrid and London the calendar row serves up to 95%; the prior is never reached (0.000 everywhere).

**Fallback shares, reported.** For every (city, *f*), overall and per distance bin: the share of test lookups
served by each link of the chain (neighbour row, calendar row, prior). The same shares for E12-ter are reported beside them, from
its run records.

## Metrics and resample

As E12-ter: wCE on test-hidden segments, mean over the four horizons; V against G0 of E9; 4,000 replicates, seeds
× corridor blocks, with E12-ter's replicate indices, so that every difference with E12-ter is paired.

## Criterion, with threshold (identical to E12-ter)

**"Neighbour and calendar buy wCE"** if V(E12-quater) is favourable (L > 0) and V ≥ 3 points in the 0–250 m bin,
in at least 2 of the 3 cities, at some level *f*; **"do not buy wCE"** if U < 3 in the 0–250 m bin in every city
and at every *f*; **"undetermined"** otherwise. No correction for multiple comparisons, as in E12-ter.

**Secondary, the purpose of E12-quater:** D′ = V(E12-quater) − V(calendar only), overall and per bin, with paired
interval, read on the two scales of E12-ter (adds: L > 0; removes: U < 0; inconclusive otherwise; 3-point margin
attained if D′ ≥ 3, excluded if U < 3). Reported beside D of E12-ter, with D′ − D paired.

**Reported without a criterion:** V per horizon; the unweighted column; red recall at 5% false alarms with the
realised false-alarm rate (descriptive, thresholds on validation-hidden segments).

## Mandatory controls (preflight, reading no test target)

1. Node sets, origins, class weights and the two tables identical to the E12-ter run records for the 60
   (city, *f*, seed) pairs (fingerprints).
2. **Link 1:** where the neighbour row is used, the E12-quater forecast equals the E12-ter forecast to the bit
   (E12-ter uses the same row there).
3. **Link 2:** where the neighbour row is not used and the calendar row is, the E12-quater forecast equals the
   calendar forecast to the bit.
4. **Link 3:** where neither is used, both E12-quater and the calendar forecast equal the prior to the bit.
   Controls 2–4 run on validation cells, and the three links together cover every lookup.
5. The shares of each link on validation lookups, per bin, are logged before the signature.
6. Causality and probabilities as in E12-ter (controls 3–5).
7. Red-recall thresholds chosen on validation-hidden segments and saved with fingerprint before any test metric.

## What invalidates the experiment

Any change to N_min, the bins, ε, the slots, the transformation or the fallback rule after a test number; any
table cell estimated from hidden segments or from validation or test periods; node sets, origins or G0 other
than E9's.

## Cost

No training; as E12-ter (≈ 0.11 h for the 60 pairs, an upper bound). Measured in the preflight.

## What changes in the paper

- **D′ within 250 m as D:** the reading of E12-ter within 250 m stands; the text reports the fallbacks.
- **D′ within 250 m better than D** (paired D′ − D with L > 0): the fallback of E12-ter was masking a value of the
  neighbour within 250 m; this is stated, with D′, and the sentences on the neighbour net of the calendar are
  revised accordingly.
- **D′ beyond 250 m close to zero:** the losses of E12-ter beyond 250 m came from the fallback, not from the
  neighbour; the sentence on the outer bins is withdrawn.
- **D′ beyond 250 m below zero:** a thin conditioning on a distant neighbour costs wCE even against the calendar;
  stated with D′.

## Files

- **Inputs:** as E12-ter, plus the E12-ter run records.
- **Code:** `paper4/code/e12quater.py`, importing `e12ter.py`, `e12bis.py`, `e12.py`, `p4b.py` and `e9.py`
  unchanged.
- **Outputs:** `paper4/runs/e12quater/`; `CONGELAMENTO_E12quater.md` generated by script.

## Deviations

None.
