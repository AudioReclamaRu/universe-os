"""Bidirectional cross-domain validation: GIZA PRIME <-> ASTRAEA.

The two domains exchange *hypotheses*, never commands, never physical energy
and never a live feed.  A candidate that succeeds in one domain must be
independently checked in the other before it can be promoted.  A negative or
inconclusive result is a valid result and is preserved as evidence.

Everything here is a contract plus deterministic capability fixtures.  No
ASTRAEA adapter is implemented, no verified Giza source is attached, and no
GUI, network or trading runtime is touched.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))

DOMAINS: Sequence[str] = ("GIZA_PRIME", "ASTRAEA")
MODES: Sequence[str] = ("paper",)
DATA_SCOPES: Sequence[str] = ("historical",)
CLAIMS: Sequence[str] = ("candidate", "negative", "inconclusive")
INVARIANT_KINDS: Sequence[str] = (
    "dimensionless_ratio", "phase_lag", "rank_order", "structural_match",
)
STAGES: Sequence[str] = (
    "quantity_typed",
    "units_separated",
    "mechanism_defined",
    "null_models_checked",
    "holdout_checked",
    "multiple_testing_checked",
    "alternatives_checked",
    "falsifier_defined",
    "uncertainty_explicit",
    "permission_scope_defined",
    "target_domain_checked",
)

CANDIDATE_FIELDS: Sequence[str] = (
    "candidate_id", "source_domain", "target_domain", "mode", "data_scope",
    "model_id", "invariant", "mechanism_definition", "alternative_explanations",
    "null_models", "holdout_checked", "multiple_testing_checked", "falsifier",
    "uncertainty", "evidence_status", "permissions", "claim", "auto_trade",
    "verified_giza_data", "synthetic_fixture", "target_check",
)

# Three pyramids of the unified system.  The comparator is the middle one:
# it is the mathematical model through which the sensor and physical reference
# exchange hypotheses.  MEGABRAIN orchestrates but owns no scientific claim.
PYRAMIDS: Sequence[Dict[str, str]] = (
    {
        "id": "ASTRAEA",
        "role": "sensor",
        "signal_domain": "informational",
        "mode": "paper",
        "data_scope": "historical",
        "note": "observes its own environment; never a trade command source",
    },
    {
        "id": "COMPARATOR",
        "role": "mathematical_model",
        "signal_domain": "dimensionless_invariant",
        "mode": "paper",
        "data_scope": "historical",
        "note": "hypothesis generator and bidirectional validator (OpenCode/cockpit)",
    },
    {
        "id": "NATURAL_PHYSICS",
        "role": "reference_system",
        "signal_domain": "physical",
        "mode": "observation",
        "data_scope": "as_documented",
        "note": "Giza and the aggregate model of the already operating Universe",
    },
)
ORCHESTRATOR: Dict[str, str] = {
    "id": "MEGABRAIN",
    "role": "orchestration",
    "authority": "coordination_only",
    "human_owned": "goals_policies_approval_gates",
    "autonomous_goal_change": False,
    "owns_scientific_claim": False,
}

# Three worlds joined by the comparator.  Each is a *separate energy marker*;
# the bridge is logical and only evaluates declared dimensionless ratios.
# It is never a physical transducer and never reduces one world to another.
WORLDS: Sequence[Dict[str, Any]] = (
    {
        "id": "BITCOIN",
        "world": "digital",
        "marker_class": "informational",
        "distinct_energy_marker": True,
        "note": "digital informational marker; never a trade command source",
    },
    {
        "id": "UNIVERSE",
        "world": "analog",
        "marker_class": "physical",
        "distinct_energy_marker": True,
        "note": "already operating Universe; Giza is one research organ of it",
    },
    {
        "id": "EARTH_EAR",
        "world": "informational",
        "marker_class": "informational",
        "distinct_energy_marker": True,
        "note": "Ухо Планеты: its own informational energy marker, not derived from the other two",
    },
)

WORLD_BRIDGE: Dict[str, Any] = {
    "bridge_id": "LOGICAL_BRIDGE_THREE_WORLDS",
    "worlds": [w["id"] for w in WORLDS],
    "world_records": list(WORLDS),
    "bridge_kind": "logical_dimensionless_model",
    "medium": "declared_dimensionless_energy_ratios_only",
    "comparison_subject": "dimensionless ratios of energy-like markers across digital, analog and informational worlds",
    "operations": [
        "ratio_evaluate", "cross_world_compare", "consistency_check",
        "rank_order", "phase_lag", "structural_match",
    ],
    "pairwise": [
        ["BITCOIN", "UNIVERSE"],
        ["EARTH_EAR", "UNIVERSE"],
        ["BITCOIN", "EARTH_EAR"],
    ],
    "each_world_is_distinct_energy_marker": True,
    "no_world_reduced_to_another": True,
    "physical_energy_transfer_claimed": False,
    "unit_equivalence_claimed": False,
    "informational_energy_is_not_physical_energy": True,
    "conversion": None,
    "bidirectional": True,
    "verification": "paper_mode_historical_data_only",
    "status": "logical_model_framework_no_validated_bridge",
}

BRIDGE_GUARDS: Sequence[str] = (
    "comparator_never_emits_trade_commands",
    "comparator_never_converts_information_to_joules",
    "bridge_observes_dimensionless_energy_ratios_not_energy_transfer",
    "each_world_is_a_distinct_energy_marker",
    "no_world_is_reduced_to_another",
    "informational_energy_is_not_physical_energy",
    "bridge_is_logical_not_physical_transduction",
    "megabrain_coordinates_but_does_not_decide_science",
    "bidirectional_check_required_before_promotion",
    "negative_result_is_valid_evidence",
)


def _engine():
    """Late import avoids a circular import with cockpit_engine."""
    import cockpit_engine
    return cockpit_engine


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise _engine().CockpitContractError(message)


def _unit_class(unit: Optional[str]) -> Optional[str]:
    contract = _engine().system_contract()
    return _engine()._unit_class(unit, contract)


def validate_candidate(candidate: Dict[str, Any]) -> bool:
    """Validate one cross-domain hypothesis against the shared contract."""
    contract = _engine().system_contract()
    for field in CANDIDATE_FIELDS:
        _require(field in candidate, "cross-domain candidate missing %s" % field)
    _require(isinstance(candidate["candidate_id"], str) and candidate["candidate_id"],
             "candidate_id must be a non-empty string")
    _require(isinstance(candidate["model_id"], str) and candidate["model_id"],
             "model_id must be a non-empty string")
    _require(candidate["source_domain"] in DOMAINS
             and candidate["target_domain"] in DOMAINS
             and candidate["source_domain"] != candidate["target_domain"],
             "a cross-domain candidate needs both distinct registered domains")
    _require(candidate["mode"] in MODES,
             "cross-domain hypotheses are only allowed in paper mode")
    _require(candidate["data_scope"] in DATA_SCOPES,
             "cross-domain hypotheses are only allowed on historical data")
    _require(candidate["claim"] in CLAIMS, "unsupported cross-domain claim")
    _require(candidate["auto_trade"] is False,
             "a cross-domain hypothesis may never authorize trading")
    _require(isinstance(candidate["evidence_status"], str)
             and candidate["evidence_status"] in contract["evidence_statuses"],
             "unknown evidence status")
    _require(bool(candidate["permissions"]), "permission scope is required")

    invariant = candidate["invariant"]
    _require(isinstance(invariant, dict), "invariant must be a typed record")
    _require(invariant.get("kind") in INVARIANT_KINDS, "unknown invariant kind")
    source_class = _unit_class(invariant.get("source_units"))
    target_class = _unit_class(invariant.get("target_units"))
    _require(source_class is not None and target_class is not None,
             "both invariant unit records must resolve")
    if source_class != target_class:
        _require(invariant.get("dimensionless") is True,
                 "physical/informational units may only be compared through a declared dimensionless invariant")
        _require(invariant.get("conversion") is None,
                 "no unit conversion may equate physical energy with information")
    if candidate["target_domain"] == "ASTRAEA":
        _require(target_class in ("informational", "conceptual")
                 or invariant.get("dimensionless") is True,
                 "ASTRAEA observations must stay informational or dimensionless")
    else:
        _require(source_class in ("informational", "conceptual")
                 or invariant.get("dimensionless") is True,
                 "ASTRAEA source must stay informational or dimensionless when targeting GIZA")

    _require(bool(candidate["mechanism_definition"]),
             "cross-domain hypothesis requires an explicit mechanism")
    _require(isinstance(candidate["alternative_explanations"], (list, tuple))
             and len(candidate["alternative_explanations"]) >= 2,
             "at least two alternative explanations are required")
    _require(isinstance(candidate["null_models"], (list, tuple))
             and len(candidate["null_models"]) >= 1,
             "at least one null model is required")
    _require(isinstance(candidate["holdout_checked"], bool),
             "holdout_checked must be an explicit boolean")
    _require(isinstance(candidate["multiple_testing_checked"], bool),
             "multiple_testing_checked must be an explicit boolean")
    _require(bool(candidate["falsifier"]), "a falsifier is required")
    _require(candidate["uncertainty"] is None
             or isinstance(candidate["uncertainty"], dict),
             "uncertainty must be an explicit record or null")
    _require(isinstance(candidate["verified_giza_data"], bool),
             "verified_giza_data must be an explicit boolean")
    _require(isinstance(candidate["synthetic_fixture"], bool),
             "synthetic_fixture must be an explicit boolean")

    target_check = candidate["target_check"]
    _require(isinstance(target_check, dict), "target_check must be a record")
    _require(isinstance(target_check.get("run"), bool), "target_check.run must be explicit")
    _require(isinstance(target_check.get("stages_passed"), (list, tuple)),
             "target_check.stages_passed must be a list")
    for stage in target_check["stages_passed"]:
        _require(stage in STAGES, "unknown validation stage %r" % stage)
    _require(len(set(target_check["stages_passed"]))
             == len(target_check["stages_passed"]),
             "duplicate validation stage")
    _require(target_check.get("result") in (None,) + CLAIMS,
             "unknown target_check result")
    return True


def _all_stages(candidate: Dict[str, Any]) -> bool:
    return set(candidate["target_check"]["stages_passed"]) == set(STAGES)


def validate_pair(forward: Dict[str, Any], reverse: Dict[str, Any]) -> Dict[str, Any]:
    """Check that a positive hypothesis was tested in *both* directions.

    Promotion is deliberately strict: both directions must run, all stages
    must pass, both claims must be candidates, holdout/multiple-testing must
    be confirmed, and the Giza side must rest on verified data.  Negative and
    inconclusive results remain valid evidence and are never promoted.
    """
    validate_candidate(forward)
    validate_candidate(reverse)
    _require(forward["source_domain"] == "GIZA_PRIME"
             and forward["target_domain"] == "ASTRAEA"
             and reverse["source_domain"] == "ASTRAEA"
             and reverse["target_domain"] == "GIZA_PRIME",
             "a pair must contain GIZA->ASTRAEA and ASTRAEA->GIZA")
    _require(forward["model_id"] == reverse["model_id"],
             "both directions must test the same mathematical model")
    _require(forward["candidate_id"] != reverse["candidate_id"],
             "each direction needs its own candidate id")

    reasons: List[str] = []
    for label, candidate in (("GIZA->ASTRAEA", forward), ("ASTRAEA->GIZA", reverse)):
        check = candidate["target_check"]
        if not check["run"]:
            reasons.append("%s: target check not run (%s)" % (
                label, check.get("reason") or "no reason recorded"))
        if not _all_stages(candidate):
            reasons.append("%s: incomplete stage coverage" % label)
        if candidate["claim"] != "candidate":
            reasons.append("%s: claim=%s" % (label, candidate["claim"]))
        if not candidate["holdout_checked"]:
            reasons.append("%s: holdout not checked" % label)
        if not candidate["multiple_testing_checked"]:
            reasons.append("%s: multiple testing not corrected" % label)
        if candidate["synthetic_fixture"]:
            reasons.append("%s: synthetic capability fixture only" % label)
        if not candidate["verified_giza_data"]:
            reasons.append("%s: no verified Giza data attached" % label)
        if candidate["uncertainty"] is None:
            reasons.append("%s: uncertainty unknown, not promoted" % label)

    promotable = not reasons
    if promotable:
        status = "promotable_candidate"
    elif any(not c["target_check"]["run"] for c in (forward, reverse)):
        status = "incomplete_bidirectional_check"
    elif any(c["claim"] == "negative" for c in (forward, reverse)):
        status = "negative_result"
    else:
        status = "inconclusive"
    return {
        "status": status,
        "promotable": promotable,
        "model_id": forward["model_id"],
        "directions": [forward["candidate_id"], reverse["candidate_id"]],
        "reasons": reasons,
        "note": "Promotion requires success in both directions. A negative result is valid evidence.",
    }


def cross_domain_manifest() -> Dict[str, Any]:
    return {
        "protocol_id": "UNIVERSE_OS_BIDIRECTIONAL_CROSS_DOMAIN_VALIDATION",
        "domains": list(DOMAINS),
        "directions": ["GIZA_PRIME->ASTRAEA", "ASTRAEA->GIZA_PRIME"],
        "mode": "paper",
        "data_scope": "historical",
        "live_feed_forbidden": True,
        "auto_trade_forbidden": True,
        "physical_information_unit_equivalence_forbidden": True,
        "causality_from_resemblance_forbidden": True,
        "required_stages": list(STAGES),
        "promotion_rule": (
            "A positive candidate in either domain must be independently checked in the "
            "other before promotion; negative and inconclusive results stay valid evidence."
        ),
        "verified_giza_sources": 0,
        "astraea_adapter_status": "not_implemented",
        "status": "framework_ready_no_verified_data_no_live_integration",
        "promotable_candidates": 0,
        "synthetic_capability_only": True,
    }


def synthetic_pair() -> Dict[str, Any]:
    """Deterministic capability fixture.  It proves the gate, not a result."""
    base = {
        "mode": "paper",
        "data_scope": "historical",
        "model_id": "synthetic_bidirectional_model_fixture",
        "mechanism_definition": "declared only as a fixture; no physical mechanism established",
        "alternative_explanations": ["common driver", "selection effect"],
        "null_models": ["phase-randomized surrogate"],
        "holdout_checked": False,
        "multiple_testing_checked": False,
        "falsifier": "predefined negative control fails",
        "uncertainty": None,
        "evidence_status": "synthetic_fixture",
        "permissions": {"access": "public", "licence": "project"},
        "claim": "inconclusive",
        "auto_trade": False,
        "verified_giza_data": False,
        "synthetic_fixture": True,
        "target_check": {
            "run": False,
            "stages_passed": [],
            "result": None,
            "reason": "no verified Giza source and no implemented ASTRAEA adapter",
        },
    }
    forward = dict(base)
    forward.update({
        "candidate_id": "synthetic_giza_to_astraea",
        "source_domain": "GIZA_PRIME",
        "target_domain": "ASTRAEA",
        "invariant": {
            "kind": "dimensionless_ratio",
            "source_units": "Hz",
            "target_units": "count",
            "dimensionless": True,
            "conversion": None,
        },
    })
    reverse = dict(base)
    reverse.update({
        "candidate_id": "synthetic_astraea_to_giza",
        "source_domain": "ASTRAEA",
        "target_domain": "GIZA_PRIME",
        "invariant": {
            "kind": "rank_order",
            "source_units": "ratio",
            "target_units": "m",
            "dimensionless": True,
            "conversion": None,
        },
    })
    return {
        "forward": forward,
        "reverse": reverse,
        "assessment": validate_pair(forward, reverse),
    }


def validate_bridge(bridge: Dict[str, Any]) -> bool:
    """The three-world bridge must stay logical, dimensionless and inert."""
    records = bridge.get("world_records")
    _require(isinstance(records, (list, tuple)) and len(records) == 3,
             "the bridge must declare exactly three worlds")
    _require({w["id"] for w in records} == {"BITCOIN", "UNIVERSE", "EARTH_EAR"},
             "digital, analog and informational worlds are all required")
    _require({w["world"] for w in records} == {"digital", "analog", "informational"},
             "each world must have its own kind")
    _require(all(w.get("distinct_energy_marker") is True for w in records),
             "each world is a separate energy marker")
    markers = {w["id"]: w["marker_class"] for w in records}
    _require(markers["UNIVERSE"] == "physical"
             and markers["BITCOIN"] == "informational"
             and markers["EARTH_EAR"] == "informational",
             "world marker classes must stay separated")
    _require(bridge.get("worlds") == [w["id"] for w in records],
             "world id list must match the world records")
    pairs = {frozenset(p) for p in bridge.get("pairwise", [])}
    _require(len(pairs) == 3 and all(len(p) == 2 for p in pairs),
             "all three world pairs must be declared")
    _require(bridge.get("bridge_kind") == "logical_dimensionless_model",
             "bridge must be a logical dimensionless model")
    _require(bridge.get("each_world_is_distinct_energy_marker") is True,
             "distinct marker invariant is required")
    _require(bridge.get("no_world_reduced_to_another") is True,
             "no world may be reduced to another")
    _require(bridge.get("physical_energy_transfer_claimed") is False,
             "the logical bridge may not claim physical energy transfer")
    _require(bridge.get("unit_equivalence_claimed") is False,
             "bits may not be equated with joules")
    _require(bridge.get("informational_energy_is_not_physical_energy") is True,
             "informational energy is not physical energy")
    _require(bridge.get("conversion") is None,
             "the bridge declares no physical conversion")
    _require(bridge.get("bidirectional") is True,
             "the bridge must be usable in both directions")
    _require(bridge.get("verification") == "paper_mode_historical_data_only",
             "bridge verification is restricted to paper mode and historical data")
    return True


def tri_pyramid_manifest() -> Dict[str, Any]:
    """Machine-readable statement of the three-pyramid architecture."""
    return {
        "model_id": "UNIVERSE_OS_TRI_PYRAMID_COMPARATOR",
        "pyramids": list(PYRAMIDS),
        "orchestrator": dict(ORCHESTRATOR),
        "world_bridge": dict(WORLD_BRIDGE),
        "bridge_guards": list(BRIDGE_GUARDS),
        "flows": [
            "ASTRAEA->COMPARATOR", "NATURAL_PHYSICS->COMPARATOR",
            "COMPARATOR->ASTRAEA", "COMPARATOR->NATURAL_PHYSICS",
            "BITCOIN<->UNIVERSE", "EARTH_EAR<->UNIVERSE", "BITCOIN<->EARTH_EAR",
        ],
        "status": "framework_ready_no_validated_bridge_no_live_integration",
    }


__all__ = [
    "DOMAINS", "MODES", "DATA_SCOPES", "CLAIMS", "INVARIANT_KINDS", "STAGES",
    "CANDIDATE_FIELDS", "PYRAMIDS", "ORCHESTRATOR", "WORLDS", "WORLD_BRIDGE",
    "BRIDGE_GUARDS", "validate_candidate", "validate_pair", "validate_bridge",
    "cross_domain_manifest", "tri_pyramid_manifest", "synthetic_pair",
]
