"""Section 18 final formalisation: principles with machine-checkable consequences.

This module deliberately does NOT add a new taxonomic class for every idea in
the audit.  It formalises the *rules* of the meta-ontology and attaches to each
one a consequence that can be checked against the canonical graph and its
event history.  New classes must be introduced only after the three cross-case
tests (Richat / Giza / ASTRAEA) show that an existing representation genuinely
cannot describe an aspect of reality.

Honesty rule: a green structural check is NOT physical confirmation.  Every
result therefore carries ``evidentiary_status = "not_evaluable"`` until real
primary sources are ingested.  Real cases are specified, not evaluated here.

Core commitments:
  * Reality is primary; observation is a physical relation inside reality.
  * No point of observation has ontological privilege.
  * Knowledge can arise without a human observer (traces, instruments,
    computation, comparison of processes); Observation Graph describes an
    information-access relation, not a mandatory human.
  * Absence of knowledge is not evidence of absence.
  * The system must be able to say "ONTOLOGY INSUFFICIENT".
"""

from __future__ import annotations

import re

from typing import Any, Dict, List, Optional, Sequence, Tuple

from epistemic_types import (
    NON_FACT_DATA_MODES,
    EpistemicContractError,
    canonical_json,
    digest,
    frozen,
    require,
)

EPISTEMIC_PRINCIPLES_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Meta-architecture: seven representations of ONE typed core (not seven DBs)
# ---------------------------------------------------------------------------

SEVEN_REPRESENTATIONS: Sequence[Dict[str, str]] = (
    {"id": "R0", "name": "ONTOLOGY & SEMANTIC GRAPH",
     "scope": "types, definitions, relations, dimensions, logic, inference rules"},
    {"id": "R1", "name": "REALITY GRAPH",
     "scope": "physical objects, fields, processes, events, states, media, interactions"},
    {"id": "R2", "name": "OBSERVATION & REPRESENTATION GRAPH",
     "scope": "observations, instruments, data, images, maps, digital twins, artefacts"},
    {"id": "R3", "name": "KNOWLEDGE & CLAIMS GRAPH",
     "scope": "hypotheses, claims, arguments, evidence, conflicts, errors, assessments"},
    {"id": "R4", "name": "CAUSAL & EXPERIMENT GRAPH",
     "scope": "mechanisms, interventions, tests, predictions, simulations, replications"},
    {"id": "R5", "name": "NORMATIVE & VALUE GRAPH",
     "scope": "goals, values, priorities, risks, cost, legal limits, ethics, choice criteria"},
    {"id": "R6", "name": "AGENCY & ACTION GRAPH",
     "scope": "people, agents, institutions, authority, decisions, tasks, actions, accountability"},
)

META_REASONING: Dict[str, Any] = {
    "id": "META",
    "name": "META-REASONING & RESEARCH STRATEGY",
    "scope": "cross-cutting analysis of all seven representations",
    "is_eighth_world": False,
    "must_be_modeled": True,
    "must_be_verifiable": True,
    "must_be_versioned": True,
}

SHARED_CORE_IDS = True
SHARED_VERSIONS = True
SHARED_PROVENANCE = True


# ---------------------------------------------------------------------------
# Observer Non-Privilege Principle (methodological, not a physical law)
# ---------------------------------------------------------------------------

OBSERVER_NON_PRIVILEGE: Sequence[Dict[str, str]] = (
    {"id": "ONP-1", "name": "Reality Independence",
     "statement": "Existence and evolution of processes do not depend on being observed."},
    {"id": "ONP-2", "name": "Observer Non-Privilege",
     "statement": "Human, instrument, algorithm and reference frame have no prior advantage."},
    {"id": "ONP-3", "name": "Observation as Physical Relation",
     "statement": "Observation is itself an interaction/trace with conditions and possible impact."},
    {"id": "ONP-4", "name": "Representation Non-Identity",
     "statement": "Map, model, image, measurement, twin are not the object itself."},
    {"id": "ONP-5", "name": "Perspective Invariance",
     "statement": "Check what is preserved or lawfully transformed across perspectives."},
    {"id": "ONP-6", "name": "Epistemic Humility",
     "statement": "Unknown stays unknown; absence of knowledge is not absence of phenomenon."},
)


# ---------------------------------------------------------------------------
# Vocabularies of the final formalisation (rules, not new classes)
# ---------------------------------------------------------------------------

STATEMENT_STATUSES: Sequence[str] = (
    "empirical_claim", "mathematical_theorem", "formal_axiom",
    "methodological_commitment", "metaphysical_commitment",
    "definition", "convention", "prescription",
)

# Reality Independence is NOT an empirical fact and not necessarily a formal
# axiom.  It is a methodological/metaphysical commitment; no theorem about
# Sphinx/Richat follows from it without an explicit model-to-world bridge.
REALITY_INDEPENDENCE_STATUS = "metaphysical_commitment"
REALITY_INDEPENDENCE_SECONDARY_STATUS = "methodological_commitment"
MODEL_TO_WORLD_BRIDGE_REQUIRED = True

TRANSFORM_CLASSES: Sequence[str] = ("invariant", "covariant", "equivariant")
TRANSFORM_OUTCOMES: Sequence[str] = (
    "invariance_detected",
    "invariance_not_detected_in_declared_class",
    "check_not_performed_or_insufficient",
)
TRANSFORM_SET_FROZEN_BEFORE_TEST = True
NOT_FOUND_IS_NOT_FALSE = True

CONCEPT_EVOLUTION_RELATIONS: Sequence[str] = (
    "refined_into", "replaced_by", "split_into", "merged_into",
    "partially_overlaps", "rejected_as", "reinterpreted_as",
)
CONCEPT_EVOLUTION_IS_NOT_REALITY_EVOLUTION = True

TRACE_STAGES: Sequence[str] = (
    "process_or_event", "trace_formation", "preservation_or_destruction",
    "exposure_or_access", "detection", "selection_and_recording",
    "publication_and_transfer", "archive_survival",
)
TRACE_REQUIRED_STAGES: Sequence[str] = (
    "trace_formation", "preservation_or_destruction", "detection",
    "selection_and_recording",
)

SELF_APPLICATION_KINDS: Sequence[str] = (
    "system_model", "system_implementation", "system_execution",
    "system_capability", "system_limitation", "system_blind_spot",
)

COMPUTATIONAL_REQUIRED_FIELDS: Sequence[str] = (
    "code_version", "environment", "dependencies", "input_checksums",
    "parameters", "algorithm_version", "solver_settings", "convergence",
    "discretization_error", "outputs", "replayable",
)
COMPUTATION_DISTINCTIONS: Sequence[str] = (
    "synthetic", "computational_experiment", "reconstruction", "real_object",
)

ONTOLOGY_INSUFFICIENT = "ONTOLOGY_INSUFFICIENT"
INSUFFICIENCY_REASONS: Sequence[str] = (
    "new_phenomenon_outside_classes", "definitions_conflict",
    "relation_not_describable", "missing_required_dimension",
    "identity_not_establishable", "inference_rules_ambiguous",
)
PROPOSED_EXTENSION_STATUSES: Sequence[str] = ("proposed", "accepted", "rejected")
EXTENSION_CHECKS: Sequence[str] = ("necessity", "consistency", "compatibility", "backward_impact")

OPTION_VALUE_FIELDS: Sequence[str] = (
    "lost_future_methods", "irreversibility", "physical_damage",
    "original_state_loss", "legal_cultural_limits",
)
OPTION_VALUE_NOT_A_SINGLE_NUMBER = True


# ---------------------------------------------------------------------------
# The principles and their machine-checkable consequences
# ---------------------------------------------------------------------------

PRINCIPLES: Sequence[Dict[str, str]] = (
    {
        "id": "PR-01", "name": "Reality Independence",
        "statement": "Do not derive physical existence from the presence of a record.",
        "machine_checkable_consequence":
            "A claim asserting existence must reference source-backed evidence; "
            "grounding='graph_record' or existence=true with no sources is rejected.",
        "check": "pr01",
    },
    {
        "id": "PR-02", "name": "Observer Non-Privilege",
        "statement": "Compare admissible perspectives without auto-preferring one.",
        "machine_checkable_consequence":
            "A perspective comparison must contain >=2 perspectives, each with "
            "recorded conditions, and no unearned preferred perspective.",
        "check": "pr02",
    },
    {
        "id": "PR-03", "name": "Observation as Physical Relation",
        "statement": "Observation is an interaction with conditions and possible impact.",
        "machine_checkable_consequence":
            "Observation context records conditions and impact; when impact is "
            "non-none, system-before/during/after are distinguished.",
        "check": "pr03",
    },
    {
        "id": "PR-04", "name": "Representation Non-Identity",
        "statement": "A representation is never the physical entity it represents.",
        "machine_checkable_consequence":
            "Nodes carrying representation_of cannot be typed as the represented "
            "Entity/EntityState and must declare representation_non_identity.",
        "check": "pr04",
    },
    {
        "id": "PR-05", "name": "Perspective Invariance",
        "statement": "Preservation or lawful transformation across fixed perspectives.",
        "machine_checkable_consequence":
            "Transformation set is frozen before the test; outcome is one of three "
            "explicit states; 'not detected' is never encoded as false/absent.",
        "check": "pr05",
    },
    {
        "id": "PR-06", "name": "Epistemic Humility",
        "statement": "Our ignorance is not a property of reality.",
        "machine_checkable_consequence":
            "non-fact data modes never become verified; absence-inference events "
            "are rejected; unknown is not converted to false or zero.",
        "check": "pr06",
    },
    {
        "id": "PR-07", "name": "Self-Application",
        "statement": "Apply our own criteria to our own ontology and implementation.",
        "machine_checkable_consequence":
            "System Model/Implementation/Execution/Capability/Limitation/Blind Spot "
            "stay distinct; a green test never carries physical_confirmation=True.",
        "check": "pr07",
    },
    {
        "id": "PR-08", "name": "Trace Survival",
        "statement": "Record the filters between event and available evidence.",
        "machine_checkable_consequence":
            "Trace records include formation/preservation/detection/selection stages; "
            "absence of trace is never recorded as absence of phenomenon.",
        "check": "pr08",
    },
    {
        "id": "PR-09", "name": "Classification Is a Claim",
        "statement": "Reclassification changes our claim, not physical identity.",
        "machine_checkable_consequence":
            "A classification change must reference a claim revision and keep the "
            "physical entity_id unchanged.",
        "check": "pr09",
    },
    {
        "id": "PR-10", "name": "Ontology Evolution",
        "statement": "Keep concept evolution separate from reality evolution.",
        "machine_checkable_consequence":
            "Concept changes use one of seven typed relations and do not silently "
            "mutate Entity payloads; they record reality_changed=False by default.",
        "check": "pr10",
    },
    {
        "id": "PR-11", "name": "Paraconsistent Isolation",
        "statement": "One unresolved conflict must not contaminate independent branches.",
        "machine_checkable_consequence":
            "Conflict propagation targets must be within disputed claims; no "
            "explosion event is allowed.",
        "check": "pr11",
    },
    {
        "id": "PR-12", "name": "Bitemporal Honesty",
        "statement": "Valid Time and Transaction Time are different axes.",
        "machine_checkable_consequence":
            "A claim carrying valid_time must also carry transaction_time; the "
            "knowledge date is never recorded as the event date.",
        "check": "pr12",
    },
    {
        "id": "PR-13", "name": "Computational Reproducibility",
        "statement": "A computation must be replayable years later.",
        "machine_checkable_consequence":
            "Computational experiment records code/env/deps/checksums/params/algorithm/"
            "solver/convergence/discretisation/outputs/replayable and declares its "
            "distinction from synthetic models and reconstructions.",
        "check": "pr13",
    },
    {
        "id": "PR-14", "name": "Future Research Option Value",
        "statement": "Preserving future research options can beat today's intervention.",
        "machine_checkable_consequence":
            "An intervention records option loss structurally (not one number) with "
            "lost future methods, irreversibility, damage and legal/cultural limits.",
        "check": "pr14",
    },
    {
        "id": "PR-15", "name": "Ontology Insufficient",
        "statement": "The system must admit its categories are inadequate.",
        "machine_checkable_consequence":
            "An insufficiency event carries a declared reason, preserves raw data, "
            "forbids forced classification, and any proposed extension stays "
            "'proposed' until separately approved.",
        "check": "pr15",
    },
)

PRINCIPLE_CHECKS = tuple(item["check"] for item in PRINCIPLES)


# ---------------------------------------------------------------------------
# Recorders: produce the structured evidence that the checks consume
# ---------------------------------------------------------------------------

def _record(
    graph: Any, event_type: str, payload: Dict[str, Any], actor: str,
    *, synthetic: Optional[bool] = None,
) -> Dict[str, Any]:
    """Write an event with an explicit synthetic marker.

    When a caller does not state the marker it is inferred conservatively from
    the graph objects the event references.  A synthetic control can therefore
    never be silently promoted to an evaluated principle.
    """
    marker = _infer_synthetic(graph, {"payload": payload}) if synthetic is None else bool(synthetic)
    return graph.record_event(event_type, frozen(payload), actor=actor, synthetic=marker)


def record_existence_grounding(
    graph: Any, claim_id: str, *, grounding: str, sources: Sequence[str],
    asserts_existence: bool, actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(grounding in ("evidence", "graph_record", "unknown"),
            "unknown existence grounding")
    return _record(graph, "existence_grounding", {
        "claim_id": claim_id, "grounding": grounding, "sources": list(sources),
        "asserts_existence": bool(asserts_existence),
    }, actor)


def record_perspective_comparison(
    graph: Any, subject_id: str, *, perspectives: Sequence[Dict[str, Any]],
    preferred: Optional[str] = None, preference_reason: Optional[str] = None,
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    return _record(graph, "perspective_compared", {
        "subject_id": subject_id, "perspectives": frozen(perspectives),
        "preferred": preferred, "preference_reason": preference_reason,
    }, actor)


def record_observation_context(
    graph: Any, observation_id: str, *, conditions: Dict[str, Any],
    impact: str, system_states: Sequence[str] = (),
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(impact in ("none", "physical", "informational", "unknown"),
            "unknown observation impact")
    payload: Dict[str, Any] = {
        "observation_id": observation_id, "conditions": frozen(conditions),
        "impact": impact, "system_states": list(system_states),
    }
    if impact != "none":
        require(set(("before", "during", "after")) <= set(system_states),
                "non-neutral observation must distinguish before/during/after")
    return _record(graph, "observation_context", payload, actor)


def record_representation(
    graph: Any, representation_id: str, *, represents: str,
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    return _record(graph, "representation_declared", {
        "representation_id": representation_id, "represents": represents,
        "relation": "representation_non_identity",
    }, actor)


def record_transformation_freeze(
    graph: Any, freeze_token: str, *, transforms: Sequence[str],
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(bool(freeze_token), "freeze token required")
    require(bool(transforms), "frozen transformation set required")
    unknown = set(transforms) - set(TRANSFORM_CLASSES)
    require(not unknown, f"unknown transformation class {sorted(unknown)}")
    return _record(graph, "transformation_frozen", {
        "freeze_token": freeze_token, "transforms": list(transforms),
    }, actor)


def record_invariance_check(
    graph: Any, subject_id: str, *, transform_classes: Sequence[str],
    frozen_sequence: int, outcome: str, freeze_token: str,
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(outcome in TRANSFORM_OUTCOMES, "unknown invariance outcome")
    require(frozen_sequence <= len(graph.events()),
            "transformation set must be frozen before the check")
    unknown = set(transform_classes) - set(TRANSFORM_CLASSES)
    require(not unknown, f"unknown transformation class {sorted(unknown)}")
    return _record(graph, "invariance_check", {
        "subject_id": subject_id, "transform_classes": list(transform_classes),
        "frozen_sequence": frozen_sequence, "outcome": outcome,
        "freeze_token": freeze_token,
    }, actor)


def record_inference_isolation(
    graph: Any, conflict_id: str, *, engine: str,
    isolated: bool = True, actor: str = "epistemic_core",
) -> Dict[str, Any]:
    """Register the isolation contract that PR-11 checks on every propagation."""
    require(bool(engine), "isolation engine must be identified")
    return _record(graph, "inference_isolation", {
        "conflict_id": conflict_id, "engine": engine, "isolated": bool(isolated),
    }, actor)


def record_ontology_approval(
    graph: Any, approval_id: str, *, extension_id: str,
    extension_version: int, approver: str, authorization: str,
    subject_id: str, insufficiency_event: str,
    checks: Sequence[str], decision: str = "approved",
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(bool(approver) and approver not in ("unspecified", "epistemic_core"),
            "approval needs an authorized decision subject")
    require(set(EXTENSION_CHECKS) <= set(checks), "all extension checks required")
    return _record(graph, "ontology_extension_approved", {
        "approval_id": approval_id, "extension_id": extension_id,
        "extension_version": extension_version, "approver": approver,
        "authorization": authorization, "subject_id": subject_id,
        "insufficiency_event": insufficiency_event,
        "checks": list(checks), "decision": decision,
    }, actor=approver, synthetic=False)


def record_system_state(
    graph: Any, kind: str, *, description: str, artifact_ref: str,
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(kind in SELF_APPLICATION_KINDS, f"unknown self-application kind {kind!r}")
    require(bool(artifact_ref), "system state must bind to a code/build/run artifact")
    return _record(graph, "system_self_state", {
        "kind": kind, "description": description,
        "artifact_ref": artifact_ref, "not_interchangeable": True,
    }, actor)


def record_green_test(
    graph: Any, test_id: str, *, physical_confirmation: bool = False,
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    return _record(graph, "green_test", {
        "test_id": test_id, "physical_confirmation": bool(physical_confirmation),
        "structural_only": True,
    }, actor)


def record_trace_filters(
    graph: Any, subject_id: str, *, stages: Sequence[str],
    absence_inferred_from_no_trace: bool = False,
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(set(stages) <= set(TRACE_STAGES), "unknown trace stage")
    return _record(graph, "trace_filters", {
        "subject_id": subject_id, "stages": list(stages),
        "absence_inferred_from_no_trace": bool(absence_inferred_from_no_trace),
    }, actor)


def record_classification_change(
    graph: Any, entity_id: str, *, claim_id: str, claim_revision_event: str,
    old_class: str, new_class: str, actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(bool(claim_revision_event), "classification needs a linked claim revision")
    return _record(graph, "classification_changed", {
        "entity_id": entity_id, "claim_id": claim_id,
        "claim_revision_event": claim_revision_event,
        "old_class": old_class, "new_class": new_class,
        "physical_identity_unchanged": True,
    }, actor)


def record_concept_evolution(
    graph: Any, from_concept: str, *, to_concept: str, relation: str,
    reality_changed: bool = False, actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(relation in CONCEPT_EVOLUTION_RELATIONS, f"unknown concept relation {relation!r}")
    return _record(graph, "concept_evolution", {
        "from_concept": from_concept, "to_concept": to_concept,
        "relation": relation, "reality_changed": bool(reality_changed),
    }, actor)


def record_bitemporal(
    graph: Any, claim_id: str, *, valid_time: str, transaction_time: str,
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(bool(valid_time) and bool(transaction_time), "both time axes required")
    return _record(graph, "bitemporal_recorded", {
        "claim_id": claim_id, "valid_time": valid_time,
        "transaction_time": transaction_time,
        "axes_are_distinct": True,
    }, actor)


def record_computational_experiment(
    graph: Any, experiment_id: str, *, distinction: str, **fields: Any,
) -> Dict[str, Any]:
    require(distinction in COMPUTATION_DISTINCTIONS, "unknown computation distinction")
    missing = [name for name in COMPUTATIONAL_REQUIRED_FIELDS if name not in fields]
    require(not missing, f"computational experiment missing {missing}")
    payload = {"experiment_id": experiment_id, "distinction": distinction}
    payload.update(frozen(fields))
    return _record(graph, "computational_experiment", payload,
                   actor=fields.get("author", "epistemic_core"))


def record_intervention(
    graph: Any, intervention_id: str, *, option_value: Dict[str, Any],
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(isinstance(option_value, dict), "option value must be structural, not a number")
    require(set(OPTION_VALUE_FIELDS) <= set(option_value),
            "option value must list lost methods, irreversibility, damage and limits")
    return _record(graph, "intervention_evaluated", {
        "intervention_id": intervention_id, "option_value": frozen(option_value),
        "not_a_single_number": True,
    }, actor)


def declare_ontology_insufficient(
    graph: Any, subject_id: str, *, reason: str, raw_data_refs: Sequence[str],
    proposed_extension: Optional[Dict[str, Any]] = None,
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    require(reason in INSUFFICIENCY_REASONS, "unknown insufficiency reason")
    require(bool(raw_data_refs), "raw data must be preserved on insufficiency")
    payload: Dict[str, Any] = {
        "subject_id": subject_id, "status": ONTOLOGY_INSUFFICIENT,
        "reason": reason, "raw_data_preserved": True,
        "raw_data_refs": list(raw_data_refs), "forced_classification": False,
    }
    if proposed_extension is not None:
        require(bool(proposed_extension.get("checks")), "extension needs checks")
        require(set(proposed_extension["checks"]) <= set(EXTENSION_CHECKS),
                "unknown extension check")
        status = proposed_extension.get("status", "proposed")
        require(status in PROPOSED_EXTENSION_STATUSES, "unknown extension status")
        if status == "accepted":
            require(bool(proposed_extension.get("approval_event")),
                    "extension cannot self-accept")
            require(bool(proposed_extension.get("extension_id")),
                    "accepted extension needs a stable extension_id")
            require(bool(proposed_extension.get("extension_version")),
                    "accepted extension needs a version")
        payload["proposed_extension"] = frozen(proposed_extension)
    return _record(graph, "ontology_insufficient", payload, actor)


# ---------------------------------------------------------------------------
# Enforcement audit (2026-11-24)
#
# A recorder helper is a convenience, never the sole enforcement point.  Every
# event is validated against the single registry below, including events that
# bypassed a recorder and were injected straight into the graph.  No new node
# classes and no new physical claims are introduced by this layer.
# ---------------------------------------------------------------------------

EVALUATION_NOT_EXERCISED = "not_exercised"
EVALUATION_SYNTHETIC_CONTROL = "synthetic_control_passed"
EVALUATION_STRUCTURAL = "structural_evaluation_passed"
EVALUATION_EMPIRICAL_NOT_EVALUABLE = "empirical_application_not_evaluable"
EVALUATION_STATES: Sequence[str] = (
    EVALUATION_NOT_EXERCISED,
    EVALUATION_SYNTHETIC_CONTROL,
    EVALUATION_STRUCTURAL,
    EVALUATION_EMPIRICAL_NOT_EVALUABLE,
)

PRINCIPLE_ID_BY_CHECK = {item["check"]: item["id"] for item in PRINCIPLES}

REFERENCE_KEYS: Sequence[str] = (
    "claim_id", "entity_id", "subject_id", "observation_id", "representation_id",
    "conflict_id", "target", "from_concept", "to_concept", "experiment_id",
    "intervention_id", "approval_id", "extension_id", "authorization",
    "insufficiency_event", "freeze_token", "artifact_ref", "claim_revision_event",
)


def _nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return value is not None


def _reference_ids(payload: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    for key in REFERENCE_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value:
            ids.append(value)
    for key in ("sources", "raw_data_refs"):
        for value in payload.get(key) or ():
            if isinstance(value, str) and value:
                ids.append(value)
    extension = payload.get("proposed_extension")
    if isinstance(extension, dict) and isinstance(extension.get("approval_event"), str):
        ids.append(extension["approval_event"])
    return ids


def _referenced_nodes(graph: Any, event: Dict[str, Any]) -> List[Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = []
    for node_id in _reference_ids(event["payload"]):
        node = graph.current(node_id)
        if node is not None:
            nodes.append(node)
    return nodes


def _event_state(graph: Any, event: Dict[str, Any]) -> str:
    """Classify one event as synthetic control, structural or not evaluable."""
    if event.get("synthetic") is True:
        return EVALUATION_SYNTHETIC_CONTROL
    nodes = _referenced_nodes(graph, event)
    if nodes and all(bool(node["synthetic"]) for node in nodes):
        return EVALUATION_SYNTHETIC_CONTROL
    if any(not bool(node["synthetic"]) for node in nodes):
        return EVALUATION_STRUCTURAL
    return EVALUATION_EMPIRICAL_NOT_EVALUABLE


def _infer_synthetic(graph: Any, event: Dict[str, Any]) -> bool:
    """Conservative marker used when a recorder does not state syntheticness."""
    return _event_state(graph, event) in (
        EVALUATION_SYNTHETIC_CONTROL, EVALUATION_EMPIRICAL_NOT_EVALUABLE,
    )


# -- event contract validators ---------------------------------------------

def _contract_existence_grounding(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    claim = graph.current(payload.get("claim_id"))
    if claim is None or claim["node_type"] not in ("Claim", "Hypothesis"):
        bad.append(
            f"{event['event_id']}: claim {payload.get('claim_id')!r} does not resolve "
            "to a Claim/Hypothesis"
        )
    if payload.get("asserts_existence"):
        if payload.get("grounding") != "evidence":
            bad.append(
                f"{event['event_id']}: existence asserted from "
                f"{payload.get('grounding')!r}, not from evidence"
            )
        sources = payload.get("sources") or []
        if not sources:
            bad.append(f"{event['event_id']}: no evidence sources")
        for source_id in sources:
            node = graph.current(source_id)
            if node is None or node["node_type"] not in ("Source", "Dataset"):
                bad.append(
                    f"{event['event_id']}: source {source_id!r} is not a Source/Dataset node"
                )
                continue
            provenance = [
                edge for edge in graph.edges()
                if edge["to_id"] == source_id
                and edge["edge_type"] in ("derived_from", "cites")
            ]
            if not provenance:
                bad.append(
                    f"{event['event_id']}: source {source_id!r} has no traceable path "
                    "to a primary observation"
                )
    return bad


def _contract_perspective(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    perspectives = payload.get("perspectives") or []
    if len(perspectives) < 2:
        bad.append(f"{event['event_id']}: fewer than two admissible perspectives")
    for item in perspectives:
        if not isinstance(item, dict) or not _nonempty(item.get("conditions")):
            bad.append(f"{event['event_id']}: perspective without recorded conditions")
    if _nonempty(payload.get("preferred")):
        reason = payload.get("preference_reason")
        if not _nonempty(reason):
            bad.append(f"{event['event_id']}: preferred perspective without a reason")
        else:
            condition_keys: set = set()
            for item in perspectives:
                if isinstance(item, dict) and isinstance(item.get("conditions"), dict):
                    condition_keys.update(item["conditions"].keys())
            tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", reason))
            if not (tokens & condition_keys):
                bad.append(
                    f"{event['event_id']}: preference reason not grounded in recorded conditions"
                )
    return bad


def _contract_observation(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    if not _nonempty(payload.get("conditions")):
        bad.append(f"{event['event_id']}: no observation conditions")
    if payload.get("impact") not in ("none", "physical", "informational", "unknown"):
        bad.append(f"{event['event_id']}: invalid observation impact")
    if payload.get("impact") != "none" and not set(("before", "during", "after")) <= set(
            payload.get("system_states") or ()):
        bad.append(
            f"{event['event_id']}: non-neutral observation lacks before/during/after"
        )
    return bad


def _contract_representation(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    if payload.get("relation") != "representation_non_identity":
        bad.append(f"{event['event_id']}: representation non-identity not declared")
    node = graph.current(payload.get("representation_id"))
    if node is not None and node["node_type"] in ("Entity", "EntityState"):
        bad.append(f"{event['event_id']}: representation typed as a physical entity")
    return bad


def _contract_transformation_freeze(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    if not _nonempty(payload.get("freeze_token")):
        bad.append(f"{event['event_id']}: freeze token missing")
    if not _nonempty(payload.get("transforms")):
        bad.append(f"{event['event_id']}: frozen transformation set is empty")
    return bad


def _contract_invariance(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    if payload.get("outcome") not in TRANSFORM_OUTCOMES:
        bad.append(f"{event['event_id']}: invalid invariance outcome")
    sequence = payload.get("frozen_sequence")
    if not isinstance(sequence, int) or sequence > event["sequence"]:
        bad.append(f"{event['event_id']}: transformation set not frozen before test")
    token = payload.get("freeze_token")
    if not _nonempty(token):
        bad.append(f"{event['event_id']}: no recorded frozen transformation set")
    else:
        freezes = [
            prior for prior in graph.events()
            if prior["event_type"] == "transformation_frozen"
            and prior["payload"].get("freeze_token") == token
            and prior["sequence"] <= event["sequence"]
        ]
        if not freezes:
            bad.append(f"{event['event_id']}: freeze token {token!r} not on record")
    return bad


def _contract_absence_inference(event: Dict[str, Any], graph: Any) -> List[str]:
    return [f"{event['event_id']}: {event['event_type']} converts unknown into false"]


def _contract_self_state(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    if payload.get("kind") not in SELF_APPLICATION_KINDS:
        bad.append(f"{event['event_id']}: unknown self-application kind")
    if not _nonempty(payload.get("description")):
        bad.append(f"{event['event_id']}: system state has no description")
    if not _nonempty(payload.get("artifact_ref")):
        bad.append(f"{event['event_id']}: system state not bound to a code/build/run artifact")
    return bad


def _contract_green_test(event: Dict[str, Any], graph: Any) -> List[str]:
    if event["payload"].get("physical_confirmation") is True:
        return [f"{event['event_id']}: green test claims physical confirmation"]
    return []


def _contract_trace(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    stages = set(payload.get("stages") or ())
    missing = [stage for stage in TRACE_REQUIRED_STAGES if stage not in stages]
    if missing:
        bad.append(f"{event['event_id']}: missing trace stages {missing}")
    if payload.get("absence_inferred_from_no_trace") is True:
        bad.append(f"{event['event_id']}: no trace converted into no phenomenon")
    return bad


def _contract_classification(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    entity = graph.current(payload.get("entity_id"))
    if entity is None or entity["node_type"] not in ("Entity", "EntityState"):
        bad.append(f"{event['event_id']}: entity {payload.get('entity_id')!r} does not resolve")
    claim = graph.current(payload.get("claim_id"))
    if claim is None or claim["node_type"] not in ("Claim", "Hypothesis"):
        bad.append(f"{event['event_id']}: claim {payload.get('claim_id')!r} does not resolve")
    if payload.get("physical_identity_unchanged") is not True:
        bad.append(f"{event['event_id']}: physical identity changed with classification")
    revision_id = payload.get("claim_revision_event")
    revision = next(
        (item for item in graph.events() if item["event_id"] == revision_id), None
    )
    if revision is None or revision["event_type"] != "claim_revised":
        bad.append(f"{event['event_id']}: no linked claim revision event")
    elif revision["payload"].get("claim_id") != payload.get("claim_id"):
        bad.append(f"{event['event_id']}: linked revision belongs to another claim")
    return bad


def _contract_concept_evolution(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    if payload.get("relation") not in CONCEPT_EVOLUTION_RELATIONS:
        bad.append(f"{event['event_id']}: invalid concept evolution relation")
    if "reality_changed" not in payload:
        bad.append(f"{event['event_id']}: reality_changed not declared")
    return bad


def _contract_inference_isolation(event: Dict[str, Any], graph: Any) -> List[str]:
    """Check the *registered* isolation contract (PR-11).

    Honesty limit: the actual paraconsistent logical inference engine is
    ``not_implemented``.  This validator proves that a propagation outside the
    disputed set is rejected and that an isolation contract is on record; it
    does not prove the behaviour of a real inference engine.
    """
    payload = event["payload"]
    bad: List[str] = []
    conflict = graph.current(payload.get("conflict_id"))
    if conflict is None or conflict["node_type"] != "Conflict":
        bad.append(f"{event['event_id']}: conflict does not resolve")
    if not _nonempty(payload.get("engine")):
        bad.append(f"{event['event_id']}: isolation engine not identified")
    if payload.get("isolated") is not True:
        bad.append(f"{event['event_id']}: conflict isolation not asserted")
    return bad


def _contract_conflict_propagation(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    record = graph.current(payload.get("conflict_id"))
    disputed = (record or {}).get("payload", {}).get("disputed_claims", [])
    if payload.get("target") not in disputed:
        return [f"{event['event_id']}: propagation to non-disputed claim"]
    isolation = [
        item for item in graph.events()
        if item["event_type"] == "inference_isolation"
        and item["payload"].get("conflict_id") == payload.get("conflict_id")
    ]
    if not isolation:
        return [f"{event['event_id']}: no isolation contract for the conflict"]
    return []


def _contract_bitemporal(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    valid = payload.get("valid_time")
    transaction = payload.get("transaction_time")
    if not _nonempty(valid) or not _nonempty(transaction):
        bad.append(f"{event['event_id']}: incomplete bitemporal record")
    elif valid == transaction:
        bad.append(f"{event['event_id']}: knowledge date recorded as event date")
    if payload.get("axes_are_distinct") is not True:
        bad.append(f"{event['event_id']}: time axes collapsed")
    return bad


def _contract_computation(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    missing = [name for name in COMPUTATIONAL_REQUIRED_FIELDS if name not in payload]
    if missing:
        bad.append(f"{event['event_id']}: missing {missing}")
    for name in ("code_version", "environment", "algorithm_version"):
        if not _nonempty(payload.get(name)):
            bad.append(f"{event['event_id']}: empty {name}")
    for name in ("dependencies", "input_checksums", "parameters", "solver_settings",
                 "convergence", "discretization_error", "outputs"):
        if name in payload and not isinstance(payload[name], dict):
            bad.append(f"{event['event_id']}: {name} is not a mapping")
    if payload.get("distinction") not in COMPUTATION_DISTINCTIONS:
        bad.append(f"{event['event_id']}: computation/reality distinction missing")
    if payload.get("replayable") is not True:
        bad.append(f"{event['event_id']}: computational experiment is not replayable")
    return bad


def _contract_intervention(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    value = payload.get("option_value")
    if not isinstance(value, dict):
        return [f"{event['event_id']}: option value is a single number"]
    empty = [name for name in OPTION_VALUE_FIELDS if not _nonempty(value.get(name))]
    if empty:
        return [f"{event['event_id']}: empty option value fields {empty}"]
    return []


def _contract_extension_approval(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    for field in ("approval_id", "extension_id", "approver", "authorization", "subject_id"):
        if not _nonempty(payload.get(field)):
            bad.append(f"{event['event_id']}: approval missing {field}")
    if payload.get("approver") in ("unspecified", "epistemic_core"):
        bad.append(f"{event['event_id']}: approver is not an authorized decision subject")
    missing = [name for name in EXTENSION_CHECKS if name not in (payload.get("checks") or ())]
    if missing:
        bad.append(f"{event['event_id']}: extension checks incomplete {missing}")
    if payload.get("decision") != "approved":
        bad.append(f"{event['event_id']}: extension decision not approved")
    decision = graph.current(payload.get("authorization"))
    if decision is None or decision["node_type"] != "Decision":
        bad.append(f"{event['event_id']}: authorization does not resolve to a Decision")
    elif decision["payload"].get("approved_by") != payload.get("approver"):
        bad.append(f"{event['event_id']}: authorization names another approver")
    insufficiency = next(
        (item for item in graph.events()
         if item["event_id"] == payload.get("insufficiency_event")), None
    )
    if insufficiency is None or insufficiency["event_type"] != "ontology_insufficient":
        bad.append(f"{event['event_id']}: approval is not linked to an insufficiency event")
    return bad


def _contract_insufficiency(event: Dict[str, Any], graph: Any) -> List[str]:
    payload = event["payload"]
    bad: List[str] = []
    if payload.get("status") != ONTOLOGY_INSUFFICIENT:
        bad.append(f"{event['event_id']}: insufficient state not declared")
    if payload.get("reason") not in INSUFFICIENCY_REASONS:
        bad.append(f"{event['event_id']}: unknown insufficiency reason")
    if not _nonempty(payload.get("raw_data_refs")):
        bad.append(f"{event['event_id']}: raw data not preserved")
    if payload.get("forced_classification") is True:
        bad.append(f"{event['event_id']}: phenomenon forcibly classified")
    extension = payload.get("proposed_extension")
    if isinstance(extension, dict):
        if extension.get("status") not in PROPOSED_EXTENSION_STATUSES:
            bad.append(f"{event['event_id']}: unknown extension status")
        missing = [name for name in EXTENSION_CHECKS if name not in (extension.get("checks") or ())]
        if missing:
            bad.append(f"{event['event_id']}: extension checks incomplete {missing}")
        if extension.get("status") == "accepted":
            approval_id = extension.get("approval_event")
            approval = next(
                (item for item in graph.events() if item["event_id"] == approval_id), None
            )
            if approval is None or approval["event_type"] != "ontology_extension_approved":
                bad.append(f"{event['event_id']}: approval does not resolve to a real event")
            else:
                values = approval["payload"]
                if values.get("extension_id") != extension.get("extension_id"):
                    bad.append(f"{event['event_id']}: approval refers to another extension")
                if values.get("extension_version") != extension.get("extension_version"):
                    bad.append(f"{event['event_id']}: approval refers to another version")
                if values.get("insufficiency_event") != event["event_id"]:
                    bad.append(f"{event['event_id']}: approval belongs to another insufficiency")
                bad.extend(_contract_extension_approval(approval, graph))
    return bad


def _contract_ontology_registration(event: Dict[str, Any], graph: Any) -> List[str]:
    """A graph-linked extension must carry a real approval, not a bare claim."""
    payload = event["payload"]
    if payload.get("extension_source") != "insufficiency":
        return []  # base ontology registration, not a proposed extension
    bad: List[str] = []
    approval_id = payload.get("approval_event")
    approval = next(
        (item for item in graph.events() if item["event_id"] == approval_id), None
    )
    if approval is None or approval["event_type"] != "ontology_extension_approved":
        bad.append(f"{event['event_id']}: extension registration has no real approval")
    elif approval["payload"].get("extension_id") != payload.get("class_id"):
        bad.append(f"{event['event_id']}: approval names another extension")
    return bad


EVENT_CONTRACT_VALIDATORS = {
    "ontology_class_registered": _contract_ontology_registration,
    "existence_grounding": _contract_existence_grounding,
    "perspective_compared": _contract_perspective,
    "observation_context": _contract_observation,
    "representation_declared": _contract_representation,
    "transformation_frozen": _contract_transformation_freeze,
    "invariance_check": _contract_invariance,
    "absence_inferred": _contract_absence_inference,
    "unknown_became_false": _contract_absence_inference,
    "system_self_state": _contract_self_state,
    "green_test": _contract_green_test,
    "trace_filters": _contract_trace,
    "classification_changed": _contract_classification,
    "concept_evolution": _contract_concept_evolution,
    "conflict_propagation": _contract_conflict_propagation,
    "inference_isolation": _contract_inference_isolation,
    "bitemporal_recorded": _contract_bitemporal,
    "computational_experiment": _contract_computation,
    "intervention_evaluated": _contract_intervention,
    "ontology_insufficient": _contract_insufficiency,
    "ontology_extension_approved": _contract_extension_approval,
}

EVENT_TO_PRINCIPLE_CHECK = {
    "ontology_class_registered": "pr15",
    "existence_grounding": "pr01",
    "perspective_compared": "pr02",
    "observation_context": "pr03",
    "representation_declared": "pr04",
    "transformation_frozen": "pr05",
    "invariance_check": "pr05",
    "absence_inferred": "pr06",
    "unknown_became_false": "pr06",
    "system_self_state": "pr07",
    "green_test": "pr07",
    "trace_filters": "pr08",
    "classification_changed": "pr09",
    "concept_evolution": "pr10",
    "conflict_propagation": "pr11",
    "inference_isolation": "pr11",
    "bitemporal_recorded": "pr12",
    "computational_experiment": "pr13",
    "intervention_evaluated": "pr14",
    "ontology_insufficient": "pr15",
    "ontology_extension_approved": "pr15",
}

PRINCIPLE_EVENT_TYPES = {
    "pr01": ("existence_grounding",),
    "pr02": ("perspective_compared",),
    "pr03": ("observation_context",),
    "pr04": ("representation_declared",),
    "pr05": ("transformation_frozen", "invariance_check"),
    "pr06": ("absence_inferred", "unknown_became_false"),
    "pr07": ("system_self_state", "green_test"),
    "pr08": ("trace_filters",),
    "pr09": ("classification_changed",),
    "pr10": ("concept_evolution",),
    "pr11": ("conflict_propagation", "inference_isolation"),
    "pr12": ("bitemporal_recorded",),
    "pr13": ("computational_experiment",),
    "pr14": ("intervention_evaluated",),
    "pr15": ("ontology_insufficient", "ontology_extension_approved",
             "ontology_class_registered"),
}


# ---------------------------------------------------------------------------
# Checks: each principle's machine-checkable consequence
# ---------------------------------------------------------------------------

def _ev(index: int, principle: Dict[str, str], status: str, details: Sequence[str]) -> Dict[str, Any]:
    return {
        "index": index,
        "id": principle["id"],
        "name": principle["name"],
        "statement": principle["statement"],
        "machine_checkable_consequence": principle["machine_checkable_consequence"],
        "status": status,
        "passed": status in ("evaluated", "vacuous"),
        "details": list(details),
        # Four distinct states replace the old binary evaluated/vacuous claim.
        "evaluation_status": EVALUATION_NOT_EXERCISED,
        # A structural pass is never physical confirmation.
        "evidentiary_status": "not_evaluable",
        "empirical_status": EVALUATION_EMPIRICAL_NOT_EVALUABLE,
        "rule_version": EPISTEMIC_PRINCIPLES_VERSION,
    }


def check_principles(graph: Any) -> List[Dict[str, Any]]:
    """Evaluate all 15 consequences.  Vacuous results are marked, not hidden."""
    events = graph.events()
    results: List[Dict[str, Any]] = []

    def add(name: str, status: str, details: Sequence[str]) -> None:
        principle = next(p for p in PRINCIPLES if p["check"] == name)
        effective = "failed" if details else status
        results.append(_ev(len(results), principle, effective, details))

    # PR-01 -----------------------------------------------------------------
    grounding = events and [e for e in events if e["event_type"] == "existence_grounding"] or []
    bad = [
        f"{e['event_id']}: existence from grounding "
        f"{e['payload'].get('grounding')!r} without source evidence"
        for e in grounding
        if e["payload"].get("asserts_existence")
        and (e["payload"].get("grounding") != "evidence" or not e["payload"].get("sources"))
    ]
    for claim in [n for n in graph.nodes()
                  if n["node_type"] in ("Claim", "Hypothesis")]:
        payload = claim["payload"]
        if payload.get("asserts_existence") is True and not payload.get("sources"):
            bad.append(f"{claim['node_id']}: asserted existence without sources")
    add("pr01", "evaluated" if grounding else "vacuous", bad)

    # PR-02 -----------------------------------------------------------------
    comparisons = [e for e in events if e["event_type"] == "perspective_compared"]
    bad = []
    for event in comparisons:
        payload = event["payload"]
        perspectives = payload.get("perspectives", [])
        if len(perspectives) < 2:
            bad.append(f"{event['event_id']}: fewer than two perspectives")
        for perspective in perspectives:
            if not perspective.get("conditions"):
                bad.append(f"{event['event_id']}: perspective without conditions")
        if payload.get("preferred") and not payload.get("preference_reason"):
            bad.append(f"{event['event_id']}: unearned preferred perspective")
    add("pr02", "evaluated" if comparisons else "vacuous", bad)

    # PR-03 -----------------------------------------------------------------
    contexts = [e for e in events if e["event_type"] == "observation_context"]
    bad = []
    for event in contexts:
        payload = event["payload"]
        if not payload.get("conditions"):
            bad.append(f"{event['event_id']}: no observation conditions")
        if payload.get("impact") == "none" and payload.get("system_states"):
            bad.append(f"{event['event_id']}: neutral impact but states recorded")
    add("pr03", "evaluated" if contexts else "vacuous", bad)

    # PR-04 -----------------------------------------------------------------
    representations = [e for e in events if e["event_type"] == "representation_declared"]
    bad = []
    for event in representations:
        payload = event["payload"]
        rep = graph.current(payload.get("representation_id"))
        if payload.get("relation") != "representation_non_identity":
            bad.append(f"{event['event_id']}: representation non-identity not declared")
        if rep and rep["node_type"] in ("Entity", "EntityState"):
            bad.append(f"{event['event_id']}: representation typed as a physical entity")
    for node in graph.nodes():
        if node["payload"].get("representation_of") and \
                node["node_type"] in ("Entity", "EntityState"):
            bad.append(f"{node['node_id']}: representation_of on a physical entity")
    add("pr04", "evaluated" if representations else "vacuous", bad)

    # PR-05 -----------------------------------------------------------------
    invariance = [e for e in events if e["event_type"] == "invariance_check"]
    bad = []
    for event in invariance:
        payload = event["payload"]
        if payload.get("frozen_sequence", 10**9) > event["sequence"]:
            bad.append(f"{event['event_id']}: transformation set not frozen before test")
        if payload.get("outcome") not in TRANSFORM_OUTCOMES:
            bad.append(f"{event['event_id']}: invalid invariance outcome")
    add("pr05", "evaluated" if invariance else "vacuous", bad)

    # PR-06 -----------------------------------------------------------------
    bad = []
    for event in events:
        if event["event_type"] in ("absence_inferred", "unknown_became_false"):
            bad.append(
                f"{event['event_id']}: {event['event_type']} converts unknown to false"
            )
    for claim in [n for n in graph.nodes()
                  if n["node_type"] in ("Claim", "Hypothesis")]:
        payload = claim["payload"]
        if payload.get("data_mode") in NON_FACT_DATA_MODES \
                and payload.get("status") in ("verified", "active"):
            bad.append(f"{claim['node_id']}: non-fact data mode marked verified")
    add("pr06", "evaluated" if bad else "vacuous", bad)

    # PR-07 -----------------------------------------------------------------
    self_states = [e for e in events if e["event_type"] == "system_self_state"]
    bad = [e["event_id"] for e in self_states if e["payload"].get("kind") not in SELF_APPLICATION_KINDS]
    bad += [e["event_id"] for e in events if e["event_type"] == "green_test"
            and e["payload"].get("physical_confirmation") is True]
    add("pr07", "evaluated" if self_states else "vacuous", bad)

    # PR-08 -----------------------------------------------------------------
    traces = [e for e in events if e["event_type"] == "trace_filters"]
    bad = []
    for event in traces:
        payload = event["payload"]
        missing = [stage for stage in TRACE_REQUIRED_STAGES
                   if stage not in payload.get("stages", [])]
        if missing:
            bad.append(f"{event['event_id']}: missing trace stages {missing}")
        if payload.get("absence_inferred_from_no_trace") is True:
            bad.append(f"{event['event_id']}: no-trace became no-phenomenon")
    add("pr08", "evaluated" if traces else "vacuous", bad)

    # PR-09 -----------------------------------------------------------------
    classifications = [e for e in events if e["event_type"] == "classification_changed"]
    bad = []
    for event in classifications:
        payload = event["payload"]
        if payload.get("physical_identity_unchanged") is not True:
            bad.append(f"{event['event_id']}: physical identity changed with classification")
        revisions = [r for r in events
                     if r["event_type"] == "claim_revised"
                     and r["payload"].get("claim_id") == payload.get("claim_id")]
        if not revisions:
            bad.append(f"{event['event_id']}: classification without claim revision")
    add("pr09", "evaluated" if classifications else "vacuous", bad)

    # PR-10 -----------------------------------------------------------------
    evolutions = [e for e in events if e["event_type"] == "concept_evolution"]
    bad = []
    for event in evolutions:
        payload = event["payload"]
        if payload.get("relation") not in CONCEPT_EVOLUTION_RELATIONS:
            bad.append(f"{event['event_id']}: invalid concept evolution relation")
        if "reality_changed" not in payload:
            bad.append(f"{event['event_id']}: reality_changed not declared")
    add("pr10", "evaluated" if evolutions else "vacuous", bad)

    # PR-11 -----------------------------------------------------------------
    conflicts = graph.nodes("Conflict")
    bad = [c["node_id"] for c in conflicts
           if c["payload"].get("status") in ("open", "under_review")
           and c["payload"].get("explodes_graph") is True]
    for event in events:
        if event["event_type"] in ("conflict_explosion", "explodes_graph"):
            bad.append(f"{event['event_id']}: conflict explosion event is forbidden")
        if event["event_type"] != "conflict_propagation":
            continue
        conflict_id = event["payload"].get("conflict_id")
        target = event["payload"].get("target")
        record = graph.current(conflict_id)
        disputed = (record or {}).get("payload", {}).get("disputed_claims", [])
        if target not in disputed:
            bad.append(f"{event['event_id']}: propagation to non-disputed claim {target}")
    add("pr11", "evaluated" if conflicts else "vacuous", bad)

    # PR-12 -----------------------------------------------------------------
    bitemporal = [e for e in events if e["event_type"] == "bitemporal_recorded"]
    bad = []
    for event in bitemporal:
        payload = event["payload"]
        if not payload.get("valid_time") or not payload.get("transaction_time"):
            bad.append(f"{event['event_id']}: incomplete bitemporal record")
        if payload.get("axes_are_distinct") is not True:
            bad.append(f"{event['event_id']}: time axes collapsed")
    for claim in [n for n in graph.nodes() if n["node_type"] in ("Claim", "Hypothesis")]:
        payload = claim["payload"]
        if "valid_time" in payload and "transaction_time" not in payload:
            bad.append(f"{claim['node_id']}: valid_time without transaction_time")
        elif "valid_time" in payload and payload.get("valid_time") == payload.get("transaction_time"):
            bad.append(f"{claim['node_id']}: knowledge date recorded as event date")
    add("pr12", "evaluated" if bitemporal else "vacuous", bad)

    # PR-13 -----------------------------------------------------------------
    computations = [e for e in events if e["event_type"] == "computational_experiment"]
    bad = []
    for event in computations:
        payload = event["payload"]
        missing = [name for name in COMPUTATIONAL_REQUIRED_FIELDS if name not in payload]
        if missing:
            bad.append(f"{event['event_id']}: missing {missing}")
        if payload.get("distinction") not in COMPUTATION_DISTINCTIONS:
            bad.append(f"{event['event_id']}: computation/reality distinction missing")
    add("pr13", "evaluated" if computations else "vacuous", bad)

    # PR-14 -----------------------------------------------------------------
    interventions = [e for e in events if e["event_type"] == "intervention_evaluated"]
    bad = []
    for event in interventions:
        payload = event["payload"].get("option_value", {})
        if not isinstance(payload, dict):
            bad.append(f"{event['event_id']}: option value is a single number")
        else:
            missing = [name for name in OPTION_VALUE_FIELDS if name not in payload]
            if missing:
                bad.append(f"{event['event_id']}: option value missing {missing}")
    add("pr14", "evaluated" if interventions else "vacuous", bad)

    # PR-15 -----------------------------------------------------------------
    insufficiencies = [e for e in events if e["event_type"] == "ontology_insufficient"]
    bad = []
    for event in insufficiencies:
        payload = event["payload"]
        if payload.get("status") != ONTOLOGY_INSUFFICIENT:
            bad.append(f"{event['event_id']}: insufficient state not declared")
        if payload.get("forced_classification") is True:
            bad.append(f"{event['event_id']}: phenomenon forcibly classified")
        if payload.get("raw_data_preserved") is not True:
            bad.append(f"{event['event_id']}: raw data not preserved")
        extension = payload.get("proposed_extension")
        if extension and extension.get("status") == "accepted" \
                and not extension.get("approval_event"):
            bad.append(f"{event['event_id']}: extension self-accepted")
    add("pr15", "evaluated" if insufficiencies else "vacuous", bad)

    # Enforcement audit: the contract registry is authoritative for EVERY
    # event, including events injected directly through record_event().  A
    # violation found here overrides the recorder-level verdict above.
    by_id = {item["id"]: item for item in results}
    for event in events:
        validator = EVENT_CONTRACT_VALIDATORS.get(event["event_type"])
        check_name = EVENT_TO_PRINCIPLE_CHECK.get(event["event_type"])
        if validator is None or check_name is None:
            continue
        messages = validator(event, graph)
        if not messages:
            continue
        target = by_id[PRINCIPLE_ID_BY_CHECK[check_name]]
        target["details"].extend(messages)
        target["passed"] = False
        target["status"] = "failed"

    # Replace the old binary evaluated/vacuous claim with four honest states.
    for principle in PRINCIPLES:
        target = by_id[principle["id"]]
        related = [
            event for event in events
            if event["event_type"] in PRINCIPLE_EVENT_TYPES[principle["check"]]
        ]
        if not related:
            state = EVALUATION_NOT_EXERCISED
        else:
            states = {_event_state(graph, event) for event in related}
            if EVALUATION_STRUCTURAL in states:
                state = EVALUATION_STRUCTURAL
            elif states == {EVALUATION_SYNTHETIC_CONTROL}:
                state = EVALUATION_SYNTHETIC_CONTROL
            else:
                state = EVALUATION_EMPIRICAL_NOT_EVALUABLE
        target["evaluation_status"] = state

    return results


def assert_principles(graph: Any, *, require_evaluated: bool = False) -> bool:
    """Assert no violation.  require_evaluated prevents vacuous greenwashing.

    ``require_evaluated`` now means: every principle was exercised through a
    non-synthetic graph artefact (``structural_evaluation_passed``).  It never
    asserts an empirical application; empirical confirmation remains permanently
    ``not_evaluable`` in the honest-zero state.
    """
    results = check_principles(graph)
    violations = [item for item in results if not item["passed"]]
    if violations:
        detail = "; ".join(
            f"{item['id']}: {', '.join(item['details'])}" for item in violations
        )
        raise EpistemicContractError(f"principles violated: {detail}")
    if require_evaluated:
        unevaluated = [
            item["id"] for item in results
            if item["evaluation_status"] != EVALUATION_STRUCTURAL
        ]
        if unevaluated:
            raise EpistemicContractError(
                f"principles not evaluated on real cases: {', '.join(unevaluated)}"
            )
    return True


def principles_manifest() -> Dict[str, Any]:
    return {
        "principles_version": EPISTEMIC_PRINCIPLES_VERSION,
        "seven_representations": list(SEVEN_REPRESENTATIONS),
        "meta_reasoning": frozen(META_REASONING),
        "shared_core_ids": SHARED_CORE_IDS,
        "shared_versions": SHARED_VERSIONS,
        "shared_provenance": SHARED_PROVENANCE,
        "observer_non_privilege": list(OBSERVER_NON_PRIVILEGE),
        "statement_statuses": list(STATEMENT_STATUSES),
        "reality_independence_status": REALITY_INDEPENDENCE_STATUS,
        "reality_independence_secondary_status": REALITY_INDEPENDENCE_SECONDARY_STATUS,
        "model_to_world_bridge_required": MODEL_TO_WORLD_BRIDGE_REQUIRED,
        "transform_classes": list(TRANSFORM_CLASSES),
        "transform_outcomes": list(TRANSFORM_OUTCOMES),
        "concept_evolution_relations": list(CONCEPT_EVOLUTION_RELATIONS),
        "trace_stages": list(TRACE_STAGES),
        "self_application_kinds": list(SELF_APPLICATION_KINDS),
        "ontology_insufficient_state": ONTOLOGY_INSUFFICIENT,
        "principles": list(PRINCIPLES),
        "machine_checkable_consequence_count": len(PRINCIPLES),
        "evaluation_states": list(EVALUATION_STATES),
        "event_contract_count": len(EVENT_CONTRACT_VALIDATORS),
        "enforcement_policy":
            "every event is validated against one registry, including direct injection",
        "inference_engine_status": "not_implemented",
        "not_implemented": [
            "actual paraconsistent logical inference engine "
            "(PR-11 checks the registered isolation contract only)",
        ],
        "evidentiary_status": "not_evaluable",
        "cross_cases": {
            "A_RICHAT": "not_evaluable_no_primary_sources",
            "B_GIZA": "not_evaluable_no_verified_objects",
            "C_ASTRAEA": "not_evaluable_no_adapter",
        },
        "class_expansion_policy":
            "new classes only after cross-case tests expose an undescribable aspect",
        "guards": {
            "observer_not_center": True,
            "reality_independence_is_commitment_not_fact": True,
            "paraconsistent_conflict_isolation": True,
            "unknown_never_becomes_false": True,
            "green_test_is_not_physical_confirmation": True,
            "reconstruction_is_not_restoration": True,
            "option_value_not_one_number": True,
        },
    }


def assert_principle_manifest_honesty() -> bool:
    manifest = principles_manifest()
    require(len(manifest["principles"]) == 15, "15 principles required")
    require(len(manifest["seven_representations"]) == 7, "seven representations required")
    require(manifest["meta_reasoning"]["is_eighth_world"] is False,
            "meta-reasoning must stay cross-cutting, not an eighth world")
    require(manifest["reality_independence_status"] in
            ("methodological_commitment", "metaphysical_commitment"),
            "Reality Independence must not be an empirical claim or formal axiom")
    require(all(value.startswith("not_evaluable")
                for value in manifest["cross_cases"].values()),
            "real cross-cases must not be presented as evaluated")
    require(manifest["evidentiary_status"] == "not_evaluable",
            "structural checks must not claim evidentiary force")
    require(len(manifest["evaluation_states"]) == 4,
            "four distinct evaluation states are required")
    require(manifest["event_contract_count"] >= 15,
            "event contract registry must cover the principle events")
    require(manifest["inference_engine_status"] == "not_implemented",
            "the actual paraconsistent inference engine is not implemented; "
            "PR-11 only checks the registered isolation contract")
    require(all(manifest["guards"].values()), "a principle guard is disabled")
    return True


def principles_digest() -> str:
    return digest(principles_manifest())
