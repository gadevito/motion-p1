# Paper 4 — draft of the title, abstract and keywords

Draft of 2026-11-08, for the reading of the full draft by the internal review. Numbers come from the frozen
records listed in `paper4/paper/paper_order.md`. The title is a working title.

---

## Title

What a Traffic Sensor Buys: No Forecastable Spatial Signal Beyond the Calendar on Uninstrumented Segments, and
What a Loop Detector Measures of Congestion

## Abstract

A road operator pays for each traffic sensor and covers only part of the network. We ask what sensors buy for
the segments that have none, and what the most common urban sensor measures. On three cities of the
Traffic4cast benchmark (Madrid, London, Melbourne), we forecast congestion in three classes 15–120 minutes
ahead on segments the model never sees. A graph model gains nothing over the same model without its graph, at
any spacing from 43 to 397 m and any coverage from 10% to 60%. The labels of nearby segments agree within about
250 m, but calibrated, that agreement stays 1–3 points below the model without spatial exchange, and net of the
hour of the week it adds nothing. Placement changes how many uncovered segments lie near a sensor, not how well
they are forecast. Against independent speed references in Madrid and Austin, a loop detector detects
congestion (area under the curve 0.984) but ranks its level poorly (rank correlation +0.249); matching loops to
road segments accounts for about half of their disagreement with probe speeds on arterials; and aggregating
lanes hides episodes on one lane. Every experiment was pre-registered and frozen, and one script regenerates
every number.

## Keywords

Traffic forecasting, graph neural networks, sensor placement, kriging, loop detectors, congestion detection,
pre-registration.
