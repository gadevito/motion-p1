# Phase 5 — Instructions for COD-01 and COD-02 (P0 §5, §8 phase 5)

2026-11-11, coordination role. These instructions implement P0 as signed; where they differ from P0, P0 prevails and the difference is reported to the responsible author before continuing.

## 1. What phase 5 is, and the one rule that matters

You code, **each on your own**, every one of the 108 counted problems of the frozen corpus (`CORPUS.json`, sha256 `916391655be2aeba47e888fbcb034cd22becf2f8d15cf16b8331991749cf76f7`, commit `5310383`) with the fields of P0 §5.1. The agreement between your two codings (Cohen's κ) is a measure of the paper: **from the moment you open your form until both forms are delivered, you do not discuss the problems, the fields, the rules or any doubt with each other.** Questions go to the responsible author in writing; the answer is given to both of you identically and appended to the minutes. After delivery, disagreements are discussed and resolved with minutes (phase 5, second part), and the codings before discussion are kept.

The 19 excluded entries are not coded.

## 2. What you receive

| File | Use |
| --- | --- |
| `protocol/processo/corpus/CODING_COD-01.json` / `CODING_COD-02.json` | your form: one entry per problem with `id`, `paper`, `status`, `summary`, `candidates` copied from the corpus (do not change them), every coding field empty, and the allowed values in `_allowed`, `_evidence_status_values`, `_free_text_fields` |
| `protocol/processo/corpus/CORPUS.json`, `MINUTES_PHASE3.md`, `CANDIDATES.md` | the problems, your phase-3 decisions, the verbatim candidates |
| `protocol/processo/P0.md` §5.1 (fields), §5.2 (rules on sources), §5.3 (taxonomy and precedence rules) | the rules |
| the sources at the P0 commits (`main` aa9f478b3fa8, `paper4` ef31396c28cf) | to read a problem in context |

Do not use the incident cards I1–I3 to decide a coding; you may read them, and if they change a decision, say so in `notes`.

## 3. The fields, one by one

Coded fields (pick one allowed value; `unknown` only where listed):

| Field | What it asks | How to decide |
| --- | --- | --- |
| `phase_of_introduction` | when the problem entered | `deliverable`: it existed before the workflow (in the project deliverables or their code); `regeneration`: introduced in the campaigns, records or scripts of the workflow; `manuscript preparation`: introduced in the manuscript or its tooling; `preliminary reconstruction`: introduced by the cards or register items written for this paper (e.g. the retracted item 33); `unknown` if the sources do not say |
| `artefact` | where it lived | the artefact that was wrong, not the one that revealed it |
| `primary_type` | P0 §5.3 | apply the precedence rules (i)–(vii) **in order** and write the rule used in `notes` when more than one type fits |
| `secondary_type` | a second type, if the rules say so | `none` otherwise; never equal to the primary |
| `stage_of_detection` | the stage of the workflow at which it was first noticed | from the sources (register «found by», commit dates, protocol notes) |
| `first_observed_detector` | who or what noticed it first | the role or control named by the sources; `mechanical control` only if a script or check flagged it (name it in `mechanical_control_which`); `regeneration on another machine` when the trigger was a run on a different machine; `external` for anyone outside the authors; `unknown` if the sources do not say |
| `detection_capability_of_other_controls` | could a control available at the time have caught it | `corroborated` only if the historical version was re-run on the defective state (it will almost never be); otherwise `hypothesised`; `not applicable` if no other control existed |
| `observed_effect` | did numbers in records or manuscript change when corrected | `numbers changed`, `none`, `not measured` (detail in `observed_effect_detail`) |
| `assistant_at_introduction` / `assistant_at_detection` | was the role that introduced / detected the problem held by an assistant at that moment | from the role, not from the committer name; `unknown` if the role is unknown |

Free-text fields (all mandatory except `notes`; write `not applicable`, `none known`, `none recorded` where the form says so):

- `mechanical_control_which`, `controls_available_at_the_time` (list each control with its version or date and whether it was run, not run, or added later), `observed_effect_detail`, `potential_impact` (what would have reached the paper; never «consequence averted»), `measured_resources` (only what logs and timestamps record), `other_reason` (for `11 other`), `notes`.

**Evidence status** (P0 §5.2): for each coded field, one of `documented` (an artefact supports that value), `attributed recollection` (you know it from memory; say whose, in `notes`), `hypothesis` (inferred), `conflict` (sources disagree). A value you are sure of but cannot point to an artefact for is a `recollection` or a `hypothesis`, not `documented`.

## 4. Precedence rules, restated (P0 §5.3)

(i) an error in a date, cause or attribution in a document → `7d documentary`; (ii) a process rule not followed → `9`, other type secondary; (iii) a control that flagged wrongly or stayed silent → `8a`/`8b`, environmental cause as `10` secondary; (iv) test information influencing training or selection → `1`, not `5`; (v) wrong alignment causing discarded data → `2` with `3` secondary; `3` primary only when alignment is correct; (vi) `4c` over `4b` when the problem exists only across configurations; (vii) `6` only for the manuscript text; a wrong sentence in a record → `7`.

## 5. Order of work and time

Go through the problems in the order of the form (P1 then PC then P4). Code the easy ones first if you prefer, but do not leave any field empty: the validator rejects an incomplete form. Expected time: 108 problems × a few minutes = one to two working days each. Write `date_started` when you open the form and `date_delivered` when you send it.

## 6. Delivery and validation

Send your `CODING_COD-0n.json` to the responsible author. The coordination role runs

```
python3 protocol/processo/analisi/coding_forms.py validate --corpus protocol/processo/corpus/CORPUS.json --form CODING_COD-0n.json
```

and returns the list of errors, if any, to you alone (not to the other coder). Only when both forms are valid are they committed together, with their fingerprints, and compared: κ per field, then the list of disagreements for the discussion. Your delivered form is kept unchanged; the resolved coding is a third file.

## 7. What not to do

- Do not talk to the other coder about the work until both forms are delivered; do not share drafts.
- Do not change the copied fields (`id`, `paper`, `status`, `summary`, `candidates`); if you think a phase-3 decision was wrong, write it in `notes` and code the problem as it stands.
- Do not mark `documented` without an artefact you could cite.
- Do not use conversations or messages as sources.
