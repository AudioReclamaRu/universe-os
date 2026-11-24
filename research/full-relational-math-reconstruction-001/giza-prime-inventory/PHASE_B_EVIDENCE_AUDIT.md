# PHASE B — EVIDENCE AUDIT

| Claim | Evidence artifact | Status |
| --- | --- | --- |
| 11,954 GDFS records present and parsed | `derived/phase2/kmz` | OBSERVED_FILE_CONTENT |
| 7 campaign sets total 12,078 observations | `phase_b_source_catalog.json` | OBSERVED_FILE_CONTENT |
| raw archive hashes match declared JSON hashes | `phase_b_source_catalog.json` | DERIVED_CHECKSUM_MATCH |
| campaign schemas differ; separate adapters required | `phase_b_observations.py` | DERIVED_FROM_SOURCE |
| KML Z is not elevation | `phase_b_observations.json` | DERIVED_FROM_SOURCE |
| Petrie height is UNKNOWN, not zero | `phase_b_observations.json` | DERIVED_FROM_SOURCE |
| 9,315 records use the swapped 'LongItude' label | `phase_b_observations.json` | DERIVED_FROM_SOURCE |
| coordinate systems are registered separately | `phase_b_coordinate_system_registry.json` | SOURCE_DOCUMENTATION_ONLY |
| no transform between GPMP and ARCE was performed | `phase_b_coordinate_system_registry.json` | METHOD_DECISION |
| 0 identities confirmed | `phase_b_entity_candidate_registry.json` | NEGATIVE_RESULT |
| 54 documented reshoot notes preserved | `phase_b_entity_candidate_registry.json` | OBSERVED_SOURCE_TEXT |
| all source points are Point geometry | `phase_b_observations.json` | OBSERVED_FILE_CONTENT |
| 24 idealized models with full contracts | `phase_b_model_registry.json` | DERIVED_MODEL |
| ellipsoid scale 2.0 is declared, not fitted | `phase_b_model_registry.json` | METHOD_DECISION |
| no terrain or monument surface exists | `phase_b_model_registry.json` | NEGATIVE_RESULT |
| 154 relation candidates with full contracts | `phase_b_relation_candidates.json` | DERIVED_FROM_SOURCE |
| no acoustic/hydraulic/electromagnetic claim | `phase_b_relation_candidates.json` | NEGATIVE_RESULT |
| source provenance not independently corroborated | `phase_b_epistemic_report.json` | NEGATIVE_RESULT |
| all validation checks hold | `phase_b_validation_report.json` | LOCAL_VALIDATION |
| rebuild is byte-identical | `phase_b_build.py` | LOCAL_VALIDATION |

## Counts used in this audit

- catalog observed total: 12078
- observation count: 12078
- entity candidates: 345
- relation candidates: 154
- idealized models: 24
- source provenance verified: False
- coordinate system verified: False

## Interpretation rule

A structurally valid file is not a corroborated source. A mathematically correct model is not a validated historical object. `OBSERVED_FILE_CONTENT` asserts only what the bytes contain; `DERIVED_*` asserts a deterministic computation; `NEGATIVE_RESULT` asserts that a claim was deliberately withheld.

Local validation checks: all_expected_sets_parsed=True, all_observations_preserved=True, cross_campaign_transform_performed=False, expected_total_matches=True, no_kml_z_promoted=True, no_monument_surface=True, no_terrain_mesh=True, observation_ids_unique=True.
