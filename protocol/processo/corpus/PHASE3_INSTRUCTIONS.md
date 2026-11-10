# Phase 3 — Instructions for COD-01 and COD-02 (P0 §4, §8 phase 3)

2026-11-10, coordination role. These instructions implement P0 as signed (`protocol/processo/P0.md`, commit `2ab032b`); where they differ from P0, P0 prevails and the difference is reported to the responsible author before continuing.

## 1. What phase 3 is

You turn the **candidate items** of phase 2 into the **problems** of the corpus. A candidate is a verbatim extract from a source (a register row, a deviation, a commit message, a note in a frozen record, a verdict in a report, a file changed between two tags). A problem is a distinct defect, deviation or violation. Your job is to decide, for every candidate, **how many problems it contains, whether it duplicates or shares another, and its status** — and to write down every non-trivial decision. You do **not** assign a type, a phase of introduction, a detector or a cause: those are phase 5, done independently. You work **together**, in the same session, and you both sign the minutes.

## 2. What you receive

All in the public repository `OR3`, branch `main`, at the commit the responsible author indicates to you (after the merge of phase 2):

| File | Use |
| --- | --- |
| `protocol/processo/corpus/CANDIDATES.md` | the 672 candidates, readable, grouped by branch and class; each has an ID (`C-main-REG-001`, …), path, locator, verbatim text |
| `protocol/processo/corpus/candidates.json` | the same, machine-readable (sha256 `ca536a86ef157201923bf80010348c662057785044922a32aedb532420b30173`) |
| `protocol/processo/corpus/NOTE_INVENTORY.md`, `NOTE_CANDIDATES.md` | known residues and counting notes of phases 1–2 |
| `protocol/processo/P0.md` §4 (unit of analysis, status, deduplication) and §8 phase 3 | the rules |
| the sources themselves (registers, protocols, records, reports, git history) | to read a candidate in context whenever the extract is not enough; always at the commits of P0: `main` aa9f478b3fa8, `paper4` ef31396c28cf (`git show <commit>:<path>`) |

Counts per class: register rows 61 (35 Paper 1, 26 Paper 4); deviations 8; git commits 75 (50 + 25); record notes 25; report flags 2; tag diffs 501.

## 3. What you produce

Two files, handed to the responsible author, who commits them (you do not commit):

**`protocol/processo/corpus/MINUTES_PHASE3.md`** — the minutes. Header: date(s), participants by code (COD-01, COD-02), the commit of `candidates.json` used, the sha256 above. Then one line per **non-trivial** decision, in this form:

```
| C-main-REG-017 | split into 2 | 17a and 17b describe two defects (generator; manuscript attribution) | P1-017, P1-018 |
| C-main-GIT-012 | duplicate of | names «voce 22»; same correction as C-main-REG-022 | P1-022 |
| C-main-TAG-001..C-main-TAG-426 (status A only) | excluded, block | files only added between tags, never modified: not corrections; none is a protocol or a record (checked: list in §6) | — |
| C-paper4-DEV-002 | excluded | cross-reference «Deviations, item 1.», not a deviation (NOTE_CANDIDATES) | — |
```

Columns: candidate ID(s) · decision (`1 problem` · `split into n` · `duplicate of` · `shared with` · `excluded` · `excluded, block`) · reason · problem ID(s). Trivial decisions («1 problem», no doubt) need no line: they are implied by `CORPUS.json`. Disagreements between you two that remain after discussion: write both positions and mark `unresolved`; the responsible author does not decide them, they stay unresolved in the corpus (status `conflict`).

**`protocol/processo/corpus/CORPUS.json`** — the corpus. One entry per problem:

```json
{
 "id": "P1-022",
 "status": "defect",
 "candidates": ["C-main-REG-022", "C-main-GIT-012", "C-main-REC-009"],
 "paper": "paper1",
 "shared_with": null,
 "summary": "pairing check with rtol 1e-12 fails across machines (register item 22)",
 "reason": null
}
```

Fields: `id` (`P1-nn` for Paper 1, `P4-nn` for Paper 4, `PC-nn` for problems registered in both; numbering in the order of first appearance in `CANDIDATES.md`); `status` (`defect` · `deviation` · `violation` · `excluded` · `conflict`); `candidates` (every candidate ID that refers to this problem: this is how duplicates are recorded — a candidate appears in exactly one problem, or in an `excluded` entry); `paper`; `shared_with` (the other paper's register item, for `PC-`); `summary` (one line, **quoting or paraphrasing the source, no interpretation**: say what happened, not why); `reason` (mandatory for `excluded` and `conflict`, otherwise null). Excluded candidates go into entries with `status: "excluded"`; a block exclusion is one entry listing all its candidates.

The responsible author freezes `CORPUS.json` with its sha256 (phase 4); after that the denominator does not change.

## 4. Rules for the status (P0 §4)

| Status | When | Example from the known cases |
| --- | --- | --- |
| **defect** | the outcome differed from what protocol, code or text prescribed | AUC computed on 19 thresholds (item 29); scoring with design-specific weights (Paper 4 item 23); a wrong time in a register item (Paper 4 item 26) is a defect of the register |
| **deviation** | a post-signature choice, declared, with no outcome different from what was prescribed | E9: a declared change of a parameter before the run with the reason dated; P4A: the per-figure CSVs announced and not written, no number affected |
| **violation** | a process rule not followed, whatever the outcome | a tag created by a role not allowed to; a commit of the drafting role on an executor branch; a protocol run before signature (none known) |
| **excluded** | improvement, change of specification, editorial note, cross-reference, generation line, data file added, duplicate extract of a problem already entered | the 426 added-only tag diffs; «Congelato il …» lines; the E9 cross-reference |
| **conflict** | you two disagree after discussion | — |

«No effect on the numbers» does **not** make something a deviation: a defect with no effect on the numbers is still a defect (e.g. item 25 of Paper 1: wrong order of phases, no effect). A retracted register item (Paper 1 item 33, retracted by 34) is a **defect of the register**, one problem, with candidates 33 and 34 both attached.

## 5. Rules for separation and deduplication (P0 §4)

1. **One error, several traces → one problem.** A register row, the commit that fixed it, the dated note in the record and the tag diff of the file are the same problem: attach all their candidate IDs to it.
2. **One row, several errors → several problems.** Split when the row describes distinct outcomes with distinct corrections (17a/17b of Paper 1 are already two rows; a row like item 20 of Paper 4 may contain two: the section count and the unreproduced correlation — decide and write why).
3. **A documentary error is its own problem.** A wrong date, cause or attribution in a register item or protocol (Paper 4 item 26; Paper 1 items 28, 33/34) is a problem distinct from the one it documents, with status `defect`; link it in the `summary` («documents P4-023»).
4. **Shared problems count once.** A problem registered in both registers (e.g. MoGERNN code: Paper 1 item 32 and Paper 4 item 25) is one `PC-nn` entry with `shared_with` and both candidates.
5. **Propagation is not multiplication.** The same error present in 13 tags is one problem; the tag diffs of those tags are attached as candidates, not counted.
6. **Commits.** A commit naming «voce n»/«item n» is attached to that problem. A commit with keywords but naming no item (`register_ref: unregistered`) is a **candidate for an unregistered problem**: read the commit (`git show <hash>`); if it corrects something not in the registers, it is a new problem (status by §4) with the commit as its only candidate; if it is a routine fix of wording, build or tooling, exclude it with the reason. Do not skip these: unregistered problems are a result of the paper.
7. **Report flags and record notes.** Attach to the problem they refer to; the two report verdicts (`l-pub2` r. 5, `20261110T084415Z` r. 167) are candidates of the problems they report (read the report to find which).
8. **Tag diffs.** Exclude the added-only files as a block **after** checking the list for protocols, records or registers added between tags (an added protocol is not a problem either, but say you checked). For modified files, attach each to the problem(s) its changes belong to (the commit messages between the two tags say which); a modified file whose changes belong to no problem is excluded with the reason «no correction».

## 6. Order of work

1. Register rows, Paper 1 then Paper 4 (61): create the problems; decide splits; mark shared ones. This is the body of the corpus.
2. Deviations (8): one problem each unless already covered by a register row (then attach); the E9 cross-reference excluded.
3. Git commits (75): attach the ones naming items; read the unregistered ones.
4. Record notes (25) and report flags (2): attach; the two residues of `NOTE_CANDIDATES.md` excluded with the reason there.
5. The two sections flagged in `NOTE_CANDIDATES.md` (`CONGELAMENTO_E15.md` §7-bis, `CONGELAMENTO_E18TER.md` §4): read in full; anything not yet covered becomes a problem with the section as its candidate (cite path and lines in the minutes).
6. Tag diffs (501): block exclusion of the added-only files; attach or exclude the rest.
7. Re-read `CORPUS.json`: every candidate ID of `candidates.json` must appear exactly once (the responsible author will check this mechanically; a missing or duplicated ID returns the file to you).

## 7. What not to do

- Do not assign a type (leakage, metric, …), a phase of introduction, a detector or a cause, even when obvious: phase 5, independently.
- Do not interpret in the `summary`: «the control did not see X» is interpretation; «X was computed on 19 thresholds; corrected in E18» is a summary.
- Do not correct the sources, the registers or the scripts; if a source is wrong, it is a problem (documentary) — write it.
- Do not use conversations, messages or memory as sources; a recollection that helps you find an artefact is fine, the artefact is the source.
- Do not consult the incident cards I1–I3 for the status of their problems: decide from the sources; you may read the cards afterwards to check that nothing was missed, and say in the minutes if they changed a decision.

## 8. Hand-back

Send `MINUTES_PHASE3.md` and `CORPUS.json` to the responsible author with the date, both codes and the commit you worked on. The coordination role runs the completeness check (§6.7) and reports; the responsible author commits and freezes (phase 4). Questions during the work go to the responsible author in writing and are appended to the minutes with the answer.

## Clarification, 2026-11-10 (question from COD-01/COD-02)

§3 («a candidate appears in exactly one problem») and §5.2 (splitting) conflict for a candidate that contains several problems. Resolution: a split candidate appears in the `candidates` list of **every** problem it supports; each such repetition must correspond to a `split into n` line in the minutes naming that candidate ID. The completeness check of §6.7 becomes: every candidate ID of `candidates.json` appears **at least once** in `CORPUS.json`; an ID appearing more than once is accepted only if the minutes contain a split line for it; no ID appears in more than one `excluded` entry, and an ID in an `excluded` entry appears nowhere else. P0 §4 is unchanged.
