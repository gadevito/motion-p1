# Phase 6 — Instructions for the external verifier EXT-01 (P0 §8 phase 6)

2026-11-13, coordination role. EXT-01 is a person outside the author group and outside the consortium's OR3 work, identified by code in all public materials; identity, acceptance and declaration of previous involvement are kept by the responsible author in a confidential register. These instructions implement P0 as signed (`protocol/processo/P0.md`, commit `2ab032b`); P0 prevails where they differ.

## 1. What is asked, in three parts, in this order

| Part | Material received | Task | Delivered file |
| --- | --- | --- | --- |
| (a) | `EXT01_sample_anonymised.json` | for each of the 33 sampled problems, assign a **primary type** (taxonomy below) and a **status** (defect · deviation · violation), with an evidence status and notes | `EXT01_form_type_status.json` |
| (b) | `EXT01_sample_provenance.json` (sent only after (a) is delivered) | for the same 33 problems, assign the **phase of introduction** | `EXT01_form_phase.json` |
| (c) | the public repository, at the commits given below | choose **one** incident card among `protocol/processo/incidenti/I1.md`, `I2.md`, `I3.md` (in Italian) and verify its reconstruction on the original evidence (commits, records, reports, registers); write a dated addendum | `EXT01_addendum_I<n>.md` |

Part (b) is sent only after (a) is delivered, and parts (a)–(c) are delivered **before** EXT-01 receives any coder value, agreement figure or minutes of phases 3 and 5. After all three are delivered and frozen, EXT-01 may be asked, as a separate task, to assess the reports of the P2 audit together with COD-01 (P0 §10); that task is not part of phase 6.

## 2. Independence

EXT-01 does not discuss the problems with the authors during the work. Questions go to the responsible author in writing and are appended to the phase-6 record with the answer. EXT-01 does not read `CODING_*.json`, `AGREEMENT.md`, `MINUTES_PHASE5.md` or `CODING_RESOLVED.json` until phase 6 is delivered; the responsible author sends the sample files directly, not a repository checkout containing those files. For part (c), EXT-01 clones the public repository and reads any file it needs, including those just named if unavoidable, **after** (a) and (b) are delivered.

## 3. Part (a): type and status on the anonymised sample

Each sampled problem gives: a one-line summary; the verbatim texts of its register rows, declared deviations, record notes and commit messages, with hashes, dates, names and role words replaced by `<hash>`, `<date>`, `<name>`, `<role>`; and the count of other traces (tag diffs, report flags) not shown. Nothing else is given on purpose: the sample is anonymised so that the type is judged from what happened, not from who found it or when.

**Status** (P0 §4): `defect` — the outcome differed from what protocol, code or text prescribed; `deviation` — a declared post-signature choice with no outcome different from what was prescribed; `violation` — a process rule not followed, whatever the outcome.

**Primary type** (P0 §5.3), one value:

1. leakage — test information in training, normalisation, weights or selection
2. indexing and alignment — windows, calendar jumps, joins, populations
3. silent loss — filters, masks, fallbacks that discard or substitute without flagging
4a. metric declared ≠ implemented · 4b. inadequate metric implemented faithfully · 4c. scoring not comparable across configurations
5. budget, selection and convergence — epochs, checkpoints, thresholds chosen in sample
6. unsupported statement in the manuscript text
7. provenance and traceability — generator not found, number not traced, hash not linked · 7d. documentary: wrong date, cause or attribution in a register, protocol or note
8a. defective control: false positive · 8b. defective control: false negative or blind to a class of changes
9. procedural violation — role beyond its permissions, order of phases, signature
10. environment and dependencies — versions, third-party licences, non-determinism across machines
11. other, with a reason in `notes`

**Precedence rules**, applied in order when several types fit: (i) an error in a date, cause or attribution in a document → 7d; (ii) a process rule not followed → 9; (iii) a control that flagged wrongly or stayed silent → 8a/8b; (iv) test information influencing training or selection → 1, not 5; (v) a wrong alignment that discards data → 2; 3 only when alignment is correct; (vi) 4c over 4b when the problem exists only across configurations; (vii) 6 only for the manuscript text; a wrong sentence in a record → 7.

**Evidence status** for the type: `documented` if the given texts state the mechanism; `hypothesis` if inferred from them; `conflict` if the texts disagree; `attributed recollection` does not apply to EXT-01.

## 4. Part (b): phase of introduction on the provenance package

The provenance package gives, for the same 33 problems, the candidates with their paths, commits, dates and full texts. Assign `phase_of_introduction`: `deliverable` (the problem existed before the workflow, in the project deliverables or their code); `regeneration` (introduced in the workflow's campaigns, records or scripts); `manuscript preparation`; `preliminary reconstruction` (introduced by the cards or register items written for this study); `unknown` if the sources do not say. Evidence status as above. `git show <commit>:<path>` in a clone of the public repository gives any cited file at its commit.

## 5. Part (c): documentary verification of one incident

Choose one of I1, I2, I3. For every statement in the card that cites a path or a commit, check it against the repository at the commits of P0 (`main` aa9f478b3fa8, `paper4` ef31396c28cf) and at the commits the card cites. Write `EXT01_addendum_I<n>.md` with: date; the card's version (commit); for each checked statement, confirmed / not confirmed / not checkable, with the artefact; any statement that exceeds its evidence; alternative explanations not listed. Do not modify the card. The addenda already present at the end of each card were written by an assistant under the responsibility of the internal reviewers, not by a human verifier: EXT-01's addendum is the first human external verification and must be labelled as such.

## 6. Delivery

Forms: fill every field; `date_started` and `date_delivered`; send to the responsible author. The coordination role validates (`external_sample.py validate`) and returns errors, if any, to EXT-01 only. Once (a), (b) and (c) are delivered, they are committed with their fingerprints, and the comparison with the authors' resolved coding (κ per part) is computed and published in `AGREEMENT_EXT01.md`; EXT-01 receives it then.

Expected time: (a) 33 problems, half a day; (b) half a day; (c) half a day to a day.
