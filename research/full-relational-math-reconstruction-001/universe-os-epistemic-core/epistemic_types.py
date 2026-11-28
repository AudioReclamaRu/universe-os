"""Shared vocabulary and contracts for the UNIVERSE OS epistemic core.

This module contains no research data.  It only declares the typed vocabulary
of the versioned Knowledge Graph, the six confidence axes, the ten passport
projections and the machine-checkable rules from Issue #7 sections 16-18.

Nothing here turns a synthetic fixture into evidence, and nothing collapses the
six axes into a single trust score.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional, Sequence

EPISTEMIC_VERSION = "1.0.0"


class EpistemicContractError(ValueError):
    """Raised when a record violates the declared epistemic contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EpistemicContractError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def frozen(value: Any) -> Any:
    """Return an immutable-by-copy value suitable for an append-only store."""
    return copy.deepcopy(value)


# ---------------------------------------------------------------------------
# 18.1 Canonical graph vocabulary
# ---------------------------------------------------------------------------

NODE_TYPES: Sequence[str] = (
    "Entity", "EntityState", "Process", "Event", "Source", "Dataset",
    "Observation", "Measurement", "Transformation", "Model", "Method",
    "Instrument", "Claim", "Hypothesis", "Argument", "Assumption",
    "Prediction", "Condition", "Conflict", "Review", "Decision", "Actor",
    "Interface", "ControlVolume",
)

EDGE_TYPES: Sequence[str] = (
    "observed_by", "measured_by", "derived_from", "transformed_by",
    "calibrated_by", "supports", "contradicts", "refutes", "depends_on", "assumes",
    "predicts", "tests", "applies_to", "valid_during", "part_of",
    "interacts_with", "supersedes", "split_from", "merged_from",
    "same_lineage_as", "reviewed_by", "resolved_by",
    # Evidence dependency graph (17.1) uses the same typed-edge space.
    "reused_by", "cites", "shares_control_network", "shares_assumption",
)

DEPENDENCY_EDGES: Sequence[str] = (
    "derived_from", "calibrated_by", "depends_on", "assumes",
    "observed_by", "measured_by", "transformed_by", "reused_by", "cites",
    "shares_control_network", "shares_assumption",
)

SUPPORT_EDGES: Sequence[str] = ("supports",)
ATTACK_EDGES: Sequence[str] = ("contradicts", "refutes")

# A universal, unlabelled "related_to" edge is forbidden by 18.1.
FORBIDDEN_EDGE_TYPES: Sequence[str] = ("related_to", "connected_to", "linked_to", "")

# ---------------------------------------------------------------------------
# 18.2 Claim vocabulary -- epistemic type is NOT status
# ---------------------------------------------------------------------------

EPISTEMIC_TYPES: Sequence[str] = (
    "direct_observation", "reported", "measured", "derived", "inferred",
    "hypothesis", "model_result",
)

CLAIM_STATUSES: Sequence[str] = (
    "draft", "active", "disputed", "suspended", "rejected",
    "accepted_within_scope", "superseded",
)

CLAIM_REQUIRED_FIELDS: Sequence[str] = (
    "claim_id", "statement", "subject", "predicate", "object_value",
    "scope", "epistemic_type", "sources", "transformation_chain",
    "supporting_arguments", "contradicting_arguments", "assumptions",
    "status", "author", "created_at", "method_version", "revision_conditions",
)

# ---------------------------------------------------------------------------
# 18.4 Conflict vocabulary
# ---------------------------------------------------------------------------

CONFLICT_STATES: Sequence[str] = (
    "open", "under_review", "partially_resolved", "resolved_with_scope",
    "unresolved_due_to_insufficient_data", "superseded", "closed_with_reason",
)

CONFLICT_DIVERGENCE_TYPES: Sequence[str] = (
    "measurement", "units", "datum_crs", "epoch", "object_definition",
    "method", "model", "interpretation", "scope", "other",
)

# ---------------------------------------------------------------------------
# 17.1 / 18.9 Six independent axes -- never one confidence score
# ---------------------------------------------------------------------------

AXES: Sequence[str] = (
    "source_reliability",
    "measurement_uncertainty",
    "interpretation_confidence",
    "coverage_completeness",
    "model_validity",
    "evidence_connectivity",
)

AXIS_LEVELS: Sequence[str] = (
    "unknown", "not_assessed", "not_applicable", "weak", "moderate",
    "strong", "verified_within_declared_tolerance",
)

AXIS_MISSING_REASONS: Sequence[str] = (
    "missing_primary_data", "missing_calibration", "missing_coverage_map",
    "missing_independent_test", "dependency_unknown", "not_relevant",
)

# ---------------------------------------------------------------------------
# 17.17 / 18.8 Passport projections
# ---------------------------------------------------------------------------

PASSPORT_KINDS: Sequence[str] = (
    "geometry_relation",
    "energy_environment",
    "uncertainty_evidence",
    "temporal_state",
    "observation",
    "genesis",
    "identity",
    "conservation",
    "dynamic_regime",
    "boundary_coupling",
)

PASSPORT_STATES: Sequence[str] = (
    "not_created", "partial", "unknown", "not_applicable", "blocked", "complete",
)

# Source data modes from 16.2.  Scenario assumptions are not facts.
DATA_MODES: Sequence[str] = (
    "source_measured", "source_published", "digitized_approximation",
    "derived_from_verified_inputs", "inferred_interval", "scenario_assumption",
    "unknown", "not_evaluable",
)

NON_FACT_DATA_MODES: Sequence[str] = (
    "scenario_assumption", "unknown", "not_evaluable",
)

# Energy channels from 16.5.  Unapplicable fields stay null, never invented.
ENERGY_CHANNELS: Sequence[str] = (
    "electromagnetic", "thermal", "acoustic", "mechanical", "seismic",
    "hydraulic", "gas_dynamic", "chemical", "gravitational", "biological",
)

ENERGY_ROLES: Sequence[str] = (
    "absorber", "reflector", "transmitter", "converter", "storage",
    "dissipator", "resonator", "filter", "waveguide", "source",
)

REVIEW_ACTIONS: Sequence[str] = (
    "review_required", "suspend", "dispute", "reject", "accept_within_scope",
)

COMPARISON_OPERATORS: Sequence[str] = ("<", "<=", ">", ">=", "==", "!=")

# ---------------------------------------------------------------------------
# Invariants (18.11) and the acceptance scenarios (18.12)
# ---------------------------------------------------------------------------

MACHINE_INVARIANTS: Sequence[Dict[str, str]] = (
    {"id": "INV-01", "rule": "every_material_claim_has_scope_provenance_version_status"},
    {"id": "INV-02", "rule": "support_traces_to_primary_observation_through_transformations"},
    {"id": "INV-03", "rule": "shared_dataset_never_counts_as_independent_confirmation"},
    {"id": "INV-04", "rule": "new_dependency_rebuilds_argument_and_triggers_review"},
    {"id": "INV-05", "rule": "conflicting_values_are_never_averaged_or_deleted"},
    {"id": "INV-06", "rule": "revision_creates_event_and_new_version_without_erasing_history"},
    {"id": "INV-07", "rule": "formal_conditions_link_to_tests_informal_ones_require_human_review"},
    {"id": "INV-08", "rule": "entity_state_does_not_replace_entity_or_auto_merge_it"},
    {"id": "INV-09", "rule": "ontology_and_identity_criteria_are_versioned_and_trigger_impact_review"},
    {"id": "INV-10", "rule": "passports_are_lazy_absence_is_not_absence_of_object_or_data"},
    {"id": "INV-11", "rule": "independent_verification_cannot_be_self_assessment"},
    {"id": "INV-12", "rule": "cached_result_never_used_after_dependency_change"},
    {"id": "INV-13", "rule": "draft_approximation_never_passes_a_full_calculation_gate"},
    {"id": "INV-14", "rule": "no_single_score_hides_axes_conflicts_unknowns_or_dependencies"},
)

ACCEPTANCE_SCENARIOS: Sequence[str] = (
    "shared_source_collapse",
    "transitive_dependency",
    "critical_node_removal",
    "source_conflict",
    "scoped_resolution",
    "destroy_condition",
    "no_post_hoc_rescue",
    "ontology_typing",
    "lazy_passport",
    "shared_canonical_value",
    "identity_temporal",
    "independent_review",
    "covariance_inheritance",
    "cache_invalidation",
    "approximation_disclosure",
    "immutable_history",
)
