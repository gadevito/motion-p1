# Paper 4 — draft of the setting and protocol of Part B

Draft of 2026-11-08, after the internal review of the full draft (items 1–3): the regime, the data and the
scales shared by every experiment of Part B, stated once. Numbers from the frozen records of E11 and E9 and the
pilot of E11 (declared provenance in `paper4/analysis/main.py`).

---

## Setting and protocol

**Task and data.** We forecast the congestion class (free flow, slowed, congested) of a road segment 15, 30, 60
and 120 minutes ahead, from the measured speeds of the Traffic4cast benchmark [neun2023t4c] in Madrid, London
and Melbourne (828, 774 and 587 segments). The classes come from a congestion factor relative to free flow. The
series are one-week blocks separated by gaps; only origins whose input window and targets keep the 15-minute
cadence are used. The forecast is scored by weighted cross-entropy (wCE): the cross-entropy of the predicted
class probabilities, with class weights that give the rare congested class the same total weight as the others.

**The inductive regime.** The segments of a city are split into instrumented (observed), validation-hidden and
test-hidden sets, each made of whole blocks of a grid, so that a hidden segment is not surrounded by observed
ones by construction. A hidden segment never enters the model: not as input, not as a training target, not in
the normalisation or in the class weights. The model must forecast a segment it has never seen, from its
instrumented neighbours and from the calendar alone.

**The reference.** G0 is Graph WaveNet [wu2019gwnet] with its graph removed: the same temporal network, with no
spatial exchange. G1 is the same model with the road graph. In this regime the forecast is close to the
uniform predictor: on the pilot configuration (Madrid, a compact sub-network of 95 nodes), the best validation
wCE of G0 and G1 was 1.066–1.071, about 3% below ln 3 = 1.099.

**A positive control.** The pipeline is not what limits the forecast. When the hidden nodes of the same
configuration enter the loss as training targets, never as input, the same model reaches 0.94 with a monotone
learning curve, against 1.07 when they are truly unseen. Propagation gains reported for hidden segments that
are training targets measure that condition, not an installation.

**Scales of reading.** V is the difference in wCE from G0, in points of the G0 wCE (percent), positive when the
compared arm is better. Intervals are 95%, from a joint resample of seeds and blocks of the network. Each
pre-registration reads two scales: the sign of the interval, and a margin of 3 points. A statement is
"undetermined" when the pre-registered condition can be neither met nor excluded everywhere. All experiments
were run on one machine (Mac M3 Max) and signed before any test metric was computed.
