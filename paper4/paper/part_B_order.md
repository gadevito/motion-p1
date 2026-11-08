# Paper 4 — Part B, order of reading

Draft of 2026-11-08, on the decision of the internal review of 2026-11-08 (13:00). Part B reads in this order:

| Step | Sections | What they establish |
|---|---|---|
| 1 | `section_E11.md`, `section_E9.md` | the models gain nothing from the graph, at any spacing or coverage tested |
| 2 | `section_E12.md` | the labels carry a spatial signal: it exists, it is short (about 250 m) and it is weak |
| 3 | `section_E12bis.md`, `section_E12ter.md` | what that signal is worth in wCE at best, without a model |
| 4 | `section_E10geo.md` | how far each placement rule brings uncovered segments within the radius of the signal |

The question "where" gets its answer at the end of step 4. Placement matters for where the network measures. It
does not matter for what is forecast elsewhere. With E12-ter frozen (dda3b8f), the sentence is final: net of the
calendar, the neighbour's class is worth nothing within 250 m, so the proximity that placement changes buys no
forecast.

Figure of step 4: `paper4/congelamenti/e10geo_curva.svg`.
