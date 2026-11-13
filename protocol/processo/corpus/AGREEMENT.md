# Agreement between the two independent codings (P0 §8, phase 5)

Forms: `COD-01` sha256 `d8c704583dc9cfd7280fbbc7240cfcdee590387783223a14a1fa8909fc3518e4`; `COD-02` sha256 `12854dac98ff92e06f7454f48ad551993751d30df0b492df2a0d2704cf6392f4`. 108 problems. Cohen's κ per field, unweighted; raw agreement = fraction of problems coded identically.

## κ per field

| Field | Raw agreement | Expected by chance | κ |
| --- | --- | --- | --- |
| phase_of_introduction | 98/108 | 0.43 | 0.84 |
| artefact | 102/108 | 0.35 | 0.91 |
| primary_type | 99/108 | 0.13 | 0.90 |
| secondary_type | 106/108 | 0.91 | 0.79 |
| stage_of_detection | 88/108 | 0.14 | 0.78 |
| first_observed_detector | 85/108 | 0.23 | 0.72 |
| detection_capability_of_other_controls | 81/108 | 0.50 | 0.50 |
| observed_effect | 87/108 | 0.46 | 0.64 |
| assistant_at_introduction | 108/108 | 0.98 | 1.00 |
| assistant_at_detection | 107/108 | 0.97 | 0.66 |
| evidence_status (all coded fields) | 914/1080 | 0.49 | 0.70 |

## Marginal distributions

**phase_of_introduction**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| deliverable | 23 | 22 |
| manuscript preparation | 15 | 22 |
| preliminary reconstruction | 1 | 1 |
| regeneration | 67 | 63 |
| unknown | 2 | 0 |

**artefact**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| code | 59 | 57 |
| environment/repository | 6 | 4 |
| manuscript | 7 | 7 |
| protocol | 13 | 13 |
| record | 20 | 24 |
| register or note | 3 | 3 |

**primary_type**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| 1 leakage | 4 | 5 |
| 10 environment and dependencies | 4 | 4 |
| 11 other | 9 | 7 |
| 2 indexing and alignment | 13 | 16 |
| 3 silent loss | 5 | 6 |
| 4a metric declared != implemented | 2 | 2 |
| 4b inadequate metric implemented faithfully | 1 | 2 |
| 4c scoring not comparable across configurations | 2 | 1 |
| 5 budget, selection and convergence | 8 | 5 |
| 6 unsupported statement in the text | 4 | 4 |
| 7 provenance and traceability | 31 | 30 |
| 7d documentary | 9 | 9 |
| 8a defective control: false positive | 6 | 6 |
| 8b defective control: false negative or blind | 9 | 9 |
| 9 procedural violation | 1 | 2 |

**secondary_type**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| 10 environment and dependencies | 3 | 3 |
| 3 silent loss | 1 | 2 |
| 7 provenance and traceability | 1 | 0 |
| none | 103 | 103 |

**stage_of_detection**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| execution | 21 | 16 |
| freeze | 5 | 4 |
| internal review | 6 | 12 |
| pre-registration | 11 | 17 |
| preflight | 12 | 16 |
| preliminary reconstruction | 2 | 3 |
| regeneration | 27 | 23 |
| submission | 1 | 1 |
| text check | 17 | 14 |
| unknown | 6 | 2 |

**first_observed_detector**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| drafting | 18 | 26 |
| execution | 25 | 19 |
| external | 4 | 0 |
| internal review | 5 | 9 |
| mechanical control | 10 | 11 |
| protocol review | 2 | 1 |
| regeneration on another machine | 3 | 4 |
| unknown | 41 | 38 |

**detection_capability_of_other_controls**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| hypothesised | 53 | 72 |
| not applicable | 55 | 36 |

**observed_effect**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| none | 71 | 64 |
| not measured | 15 | 13 |
| numbers changed | 22 | 31 |

**assistant_at_introduction**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| unknown | 107 | 107 |
| yes | 1 | 1 |

**assistant_at_detection**

| Value | COD-01 | COD-02 |
| --- | --- | --- |
| unknown | 106 | 107 |
| yes | 2 | 1 |

## Disagreements: 119 field-level, on 69 of 108 problems

| Problem | Field | COD-01 | COD-02 | evidence COD-01 / COD-02 |
| --- | --- | --- | --- | --- |
| P1-021 | phase_of_introduction | unknown | regeneration | hypothesis / hypothesis |
| P1-035 | phase_of_introduction | deliverable | regeneration | documented / documented |
| P1-037 | phase_of_introduction | unknown | regeneration | hypothesis / documented |
| P1-041 | phase_of_introduction | regeneration | manuscript preparation | documented / documented |
| P1-042 | phase_of_introduction | regeneration | manuscript preparation | documented / documented |
| P1-043 | phase_of_introduction | regeneration | manuscript preparation | documented / documented |
| P1-064 | phase_of_introduction | regeneration | manuscript preparation | documented / documented |
| P1-072 | phase_of_introduction | regeneration | manuscript preparation | documented / documented |
| P1-073 | phase_of_introduction | regeneration | manuscript preparation | documented / documented |
| P1-075 | phase_of_introduction | regeneration | manuscript preparation | documented / documented |
| P1-072 | artefact | code | record | documented / documented |
| P1-073 | artefact | record | code | documented / documented |
| P4-016 | artefact | code | record | documented / documented |
| P4-027 | artefact | code | record | documented / documented |
| P4-046 | artefact | environment/repository | record | documented / documented |
| P4-048 | artefact | environment/repository | record | documented / documented |
| P1-004 | primary_type | 5 budget, selection and convergence | 2 indexing and alignment | documented / documented |
| P1-020 | primary_type | 2 indexing and alignment | 1 leakage | documented / documented |
| P1-026 | primary_type | 11 other | 2 indexing and alignment | documented / documented |
| P1-027 | primary_type | 5 budget, selection and convergence | 4b inadequate metric implemented faithfully | hypothesis / hypothesis |
| P1-030 | primary_type | 4c scoring not comparable across configurations | 2 indexing and alignment | documented / hypothesis |
| P1-051 | primary_type | 5 budget, selection and convergence | 9 procedural violation | hypothesis / hypothesis |
| P1-055 | primary_type | 5 budget, selection and convergence | 2 indexing and alignment | documented / documented |
| P1-057 | primary_type | 11 other | 5 budget, selection and convergence | documented / hypothesis |
| P1-073 | primary_type | 7 provenance and traceability | 3 silent loss | documented / documented |
| P1-065 | secondary_type | 7 provenance and traceability | none | hypothesis / documented |
| P4-039 | secondary_type | none | 3 silent loss | hypothesis / documented |
| P1-007 | stage_of_detection | unknown | internal review | hypothesis / documented |
| P1-013 | stage_of_detection | freeze | unknown | hypothesis / hypothesis |
| P1-015 | stage_of_detection | unknown | internal review | hypothesis / documented |
| P1-019 | stage_of_detection | execution | preflight | hypothesis / hypothesis |
| PC-002 | stage_of_detection | execution | preflight | hypothesis / hypothesis |
| P1-030 | stage_of_detection | text check | internal review | hypothesis / documented |
| P1-031 | stage_of_detection | text check | internal review | documented / documented |
| P1-048 | stage_of_detection | preflight | execution | hypothesis / hypothesis |
| P1-053 | stage_of_detection | execution | preflight | hypothesis / hypothesis |
| P1-055 | stage_of_detection | execution | preflight | hypothesis / hypothesis |
| P1-065 | stage_of_detection | unknown | preliminary reconstruction | hypothesis / hypothesis |
| P1-066 | stage_of_detection | unknown | internal review | hypothesis / hypothesis |
| P1-067 | stage_of_detection | unknown | internal review | hypothesis / documented |
| P4-004 | stage_of_detection | execution | preflight | documented / hypothesis |
| P4-027 | stage_of_detection | regeneration | pre-registration | hypothesis / hypothesis |
| P4-033 | stage_of_detection | execution | pre-registration | hypothesis / hypothesis |
| P4-035 | stage_of_detection | text check | pre-registration | hypothesis / hypothesis |
| P4-046 | stage_of_detection | regeneration | pre-registration | hypothesis / hypothesis |
| P4-047 | stage_of_detection | regeneration | pre-registration | hypothesis / hypothesis |
| P4-048 | stage_of_detection | regeneration | pre-registration | hypothesis / hypothesis |
| P1-001 | first_observed_detector | unknown | drafting | hypothesis / hypothesis |
| P1-002 | first_observed_detector | unknown | drafting | hypothesis / hypothesis |
| P1-007 | first_observed_detector | external | unknown | documented / hypothesis |
| P1-015 | first_observed_detector | external | unknown | documented / hypothesis |
| P1-016 | first_observed_detector | unknown | mechanical control | hypothesis / hypothesis |
| P1-017 | first_observed_detector | unknown | mechanical control | hypothesis / hypothesis |
| P1-019 | first_observed_detector | mechanical control | unknown | hypothesis / hypothesis |
| P1-027 | first_observed_detector | protocol review | internal review | hypothesis / documented |
| P1-030 | first_observed_detector | drafting | internal review | hypothesis / hypothesis |
| P1-031 | first_observed_detector | drafting | internal review | hypothesis / hypothesis |
| P1-043 | first_observed_detector | unknown | mechanical control | hypothesis / hypothesis |
| P1-055 | first_observed_detector | unknown | execution | hypothesis / hypothesis |
| P1-059 | first_observed_detector | mechanical control | regeneration on another machine | documented / documented |
| P1-066 | first_observed_detector | external | unknown | documented / hypothesis |
| P1-067 | first_observed_detector | external | internal review | documented / hypothesis |
| P4-005 | first_observed_detector | unknown | drafting | hypothesis / hypothesis |
| P4-027 | first_observed_detector | execution | drafting | hypothesis / hypothesis |
| P4-038 | first_observed_detector | execution | drafting | hypothesis / hypothesis |
| P4-039 | first_observed_detector | execution | drafting | hypothesis / hypothesis |
| P4-040 | first_observed_detector | execution | drafting | hypothesis / hypothesis |
| P4-046 | first_observed_detector | execution | drafting | hypothesis / hypothesis |
| P4-047 | first_observed_detector | execution | drafting | hypothesis / hypothesis |
| P4-048 | first_observed_detector | execution | drafting | hypothesis / hypothesis |
| P1-003 | detection_capability_of_other_controls | hypothesised | not applicable | hypothesis / hypothesis |
| P1-009 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-014 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-016 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-017 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| PC-002 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-020 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-021 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-025 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-026 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-030 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-036 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-038 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-055 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-060 | detection_capability_of_other_controls | hypothesised | not applicable | hypothesis / hypothesis |
| P1-062 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-066 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-067 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-073 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P4-005 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P4-010 | detection_capability_of_other_controls | hypothesised | not applicable | hypothesis / hypothesis |
| P4-023 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P4-024 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P4-025 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P4-026 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P4-040 | detection_capability_of_other_controls | hypothesised | not applicable | hypothesis / hypothesis |
| P4-043 | detection_capability_of_other_controls | not applicable | hypothesised | hypothesis / hypothesis |
| P1-001 | observed_effect | not measured | none | hypothesis / documented |
| P1-002 | observed_effect | not measured | none | hypothesis / documented |
| P1-003 | observed_effect | not measured | none | hypothesis / documented |
| P1-022 | observed_effect | none | not measured | hypothesis / hypothesis |
| P1-024 | observed_effect | not measured | none | hypothesis / hypothesis |
| P1-055 | observed_effect | not measured | none | hypothesis / documented |
| P1-058 | observed_effect | numbers changed | none | documented / documented |
| P1-073 | observed_effect | none | numbers changed | hypothesis / documented |
| P4-016 | observed_effect | none | numbers changed | documented / documented |
| P4-017 | observed_effect | none | numbers changed | documented / documented |
| P4-018 | observed_effect | none | numbers changed | documented / documented |
| P4-019 | observed_effect | none | numbers changed | documented / documented |
| P4-020 | observed_effect | none | numbers changed | documented / documented |
| P4-022 | observed_effect | none | numbers changed | documented / documented |
| P4-023 | observed_effect | none | numbers changed | documented / documented |
| P4-024 | observed_effect | none | numbers changed | documented / documented |
| P4-025 | observed_effect | none | numbers changed | documented / documented |
| P4-027 | observed_effect | none | not measured | documented / hypothesis |
| P4-043 | observed_effect | not measured | none | hypothesis / documented |
| P4-047 | observed_effect | none | not measured | documented / hypothesis |
| P4-048 | observed_effect | none | not measured | documented / hypothesis |
| P4-002 | assistant_at_detection | yes | unknown | hypothesis / hypothesis |

Problems with no disagreement on any field: 39.
Resolution: discussion between the coders with minutes (`MINUTES_PHASE5.md`); the two delivered forms stay unchanged; the resolved coding is `CODING_RESOLVED.json`; unresolved disagreements stay `conflict`.
