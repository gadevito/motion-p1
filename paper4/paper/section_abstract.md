# Paper 4 — draft of the title, abstract and keywords

Draft of 2026-11-08, revised after the internal review of the full draft (items 4 and 13). Numbers come from
the frozen records listed in `paper4/paper/paper_order.md`. The title is a working title.

---

## Title

What a Traffic Sensor Buys: No Forecastable Spatial Signal Beyond the Calendar on Uninstrumented Segments, and
What a Loop Detector Measures of Congestion

## Abstract

A road operator pays for each traffic sensor and covers only part of the network. We ask what sensors buy for
the segments that have none. On three cities of the Traffic4cast benchmark, forecasting congestion in three
classes 15–120 minutes ahead on segments the model never sees, we find no forecastable spatial information
beyond the calendar at any coverage from 10% to 60%. A graph model gains nothing over the same model without
its graph, and predictors without training do no better. Nearby labels do agree within about 250 m, but that
agreement is shared calendar: a table of class frequencies by hour of the week forecasts as well as the trained
model, and the neighbour's class adds nothing to it. Placement changes how close uncovered segments lie to a
sensor, not how well they are forecast. What a sensor buys is the measurement at its own segment. For the loop
detector, against independent speed references, that measurement detects congestion but does not measure its
level. Every experiment was pre-registered and frozen, and the records, the predictions and one script that
regenerates every number are released.

## Keywords

Traffic forecasting, graph neural networks, sensor placement, kriging, loop detectors, congestion detection,
pre-registration.
