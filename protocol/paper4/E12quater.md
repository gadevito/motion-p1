# E12-quater — The neighbour net of the calendar, with a symmetric fallback

**Pre-registration.** Date ____ · commit ____ (code `e12quater.py` ____, `e12ter.py` e8c8d17e99e4008b,
`e12bis.py` 27adfe03f24647e8, `e12.py` 3ec453d15372b217, `p4b.py` 926061038a7472a3, `e9.py` 4dd5628af8879511;
preflight log `e12quater_preflight.log` ____) · launched by ____ (Mac M3 Max, CPU) · preflight ____ · cost ____.

Draft of 2026-11-08, on the decision of the internal review of 2026-11-08 (21:45, item 2). No training. **No
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

**Fallback (the one change).** A row of the table with the neighbour with fewer than N_min pairs falls back to the
**calendar-only row** (slot, *h*), not to the E12-bis row. A calendar row with fewer than N_min pairs falls back
to the prior, as in E12-ter. Where the fallback applies, E12-quater and the calendar-only table give the same
forecast, so their difference comes only from rows that carry the neighbour.

Alternative considered and not chosen: shrinkage of every row towards the calendar-only row,
*q* = (*n*·*q*_row + κ·*q*_cal)/(*n* + κ). It adds a parameter κ that would have to be fixed without test data; the
fallback keeps the threshold of E12-ter and changes only its target.

**Fallback shares, reported.** For every (city, *f*), overall and per distance bin: the share of test lookups
that fall back to the calendar row, and to the prior. The same shares for E12-ter are reported beside them, from
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
2. Where a row falls back, the E12-quater forecast equals the calendar forecast to the bit (on validation cells).
3. Where no row falls back, the E12-quater forecast equals the E12-ter forecast to the bit (on validation cells).
4. The fallback shares on validation lookups, per bin, are logged before the signature.
5. Causality and probabilities as in E12-ter (controls 3–5).
6. Red-recall thresholds chosen on validation-hidden segments and saved with fingerprint before any test metric.

## What invalidates the experiment

Any change to N_min, the bins, ε, the slots, the transformation or the fallback rule after a test number; any
table cell estimated from hidden segments or from validation or test periods; node sets, origins or G0 other
than E9's.

## Cost

No training; as E12-ter (≈ 0.11 h for the 60 pairs, an upper bound). Measured in the preflight.

## What changes in the paper

- **D′ within 250 m as D:** the reading of E12-ter within 250 m stands; the text reports the fallbacks.
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
