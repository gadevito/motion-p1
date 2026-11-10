# Incident cards — attribution

The cards `I1.md`, `I2.md`, `I3.md` are a **preliminary verification** of whether incidents can be reconstructed from the repository's traces, carried out on 2026-11-10 before P0 and declared as such in P0 §2.

Attribution, correcting the wording of the message of commit `d4bfd03` («addenda datati dei revisori interni»):

- **Text of the cards**: written by the coordination role (an assistant, under the responsibility of the responsible author), from commands run by the responsible author whose outputs are reported in the cards with path and commit.
- **Dated addenda** at the end of each card (2026-11-10): a documentary verification carried out by an assistant under the responsibility of the internal-review role; the campaigns were not re-run. They do not constitute the external human verification required by P0 §8 (phase 6), and they are kept distinct from every future human verification.
- **Rectification and clarification** at the end of `I3.md` (2026-11-10): by the coordination role, following the addendum; item 33 of the Paper 1 register, proposed by the coordination role on a testimony without an artefact, is retracted by item 34.
- **Human review by the co-authors** of the cards: not yet carried out; when it is, it is added as a separate addendum with role and date.

Testimonies of the responsible author reported in the cards (e.g. «the second machine was another MacBook M3», I3 §7.1) are attributed recollections, not documented statements; where an artefact contradicts them, the artefact prevails (I3, rectification).

## Planned verifications by participants outside the author group

External verification and the P2 audit are planned, not yet carried out. EXT-01 is also explicitly assigned a subsequent, separate task assessing P2 reports together with COD-01. Every completed activity is documented with code, date, activity and outcome; planned assignments do not assert acceptance or completion.

| Code | Organisation | Role | Activity (P0) |
| --- | --- | --- | --- |
| EXT-01 | Kiranet | external verifier, outside the group and the consortium | §8 phase 6: coding of an anonymised sample; phase of introduction on a provenance package; documentary verification of at least one incident on the original evidence. Only after these outputs are frozen: independent assessment of P2 reports with COD-01 (§10) |
| P2-01 | Frontiere | P2 reviewer, inside the consortium | §10: audit of the authentic frozen code |
| P2-02 | Frontiere | P2 reviewer, inside the consortium | §10: audit of the authentic frozen code |
| P2-03 | Mediacom | P2 reviewer, inside the consortium | §10: audit of the authentic frozen code |

The external verification by EXT-01 (P0 §8) and the P2 audit by Frontiere and Mediacom (P0 §10) are different activities with different scopes. In public materials these participants appear only by code, affiliation, role and date; the correspondence with people is kept by the responsible author in a confidential register. This archive is not anonymous: names already present in the cards and in the git history remain as they are.

## Internal assignments and sequencing

- COD-01 and COD-02 are the two human co-author coders, from the internal-review role. Their personal identities are assigned in a confidential allocation note, not in this public README.
- COD-01 and EXT-01 independently assess the P2 reports, then discuss disagreements, preserving the initial assessments. Unresolved disagreements remain unresolved.
- EXT-01 completes and freezes the external verification before receiving P2 reports. The dual role is disclosed; it is not two independent external replications.
- DEP-01 is the MOTION project coordinator, custodian of the signed plan and its dated receipt, with no analytical role under P0.
- P1 and the optional seeded-defect sensitivity exercise are not carried out. External mutant generators are not applicable.
- Participation acceptances are recorded privately before signature. Actual signature and receipt dates and source-snapshot commits are recorded at execution, not prefilled in this draft.

## Language policy

- The Italian cards, with their addenda and rectifications, are the **original source**; they are not translated in full and are not modified.
- Excerpts quoted in the paper are English translations, each linked to the file, the commit and the original passage (section and, where needed, the date of the addendum or rectification). A quotation from a passage later superseded (e.g. I3 §7.1, superseded by the rectification of 2026-11-10) must say so in the paper.
- Translations are checked to preserve the qualifications of evidence status: hypothesis, attributed recollection, conflict, not verified, documented.
- If the external verifier (P0 §8, phase 6) does not read Italian, the materials they need are provided as side-by-side translations, each with the original commit, the public code of the translator and a fidelity check by a second person identified by code; the procedure is fixed in P0 before signature, the translations are prepared when needed.
