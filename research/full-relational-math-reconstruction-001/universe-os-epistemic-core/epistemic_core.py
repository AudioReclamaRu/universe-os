"""Facade: epistemic core manifest, machine invariants and honesty guards.

Issue #7 §18.11-18.13.  The core is implemented here, before any cockpit
projection.  A Claim, Conflict or synthetic fixture never becomes empirical
evidence: verified sources / real objects / live adapters stay at zero until
primary data is actually ingested.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence

import epistemic_claims as claims
import epistemic_principles as principles
import epistemic_uncertainty as uncertainty
from epistemic_types import (
    ACCEPTANCE_SCENARIOS,
    AXES,
    CLAIM_STATUSES,
    EPISTEMIC_TYPES,
    EPISTEMIC_VERSION,
    ENERGY_CHANNELS,
    MACHINE_INVARIANTS,
    PASSPORT_KINDS,
    EpistemicContractError,
    canonical_json,
    frozen,
    require,
)

FORBIDDEN_SCORE_KEYS = (
    "confidence_percent", "trust_score", "belief_probability", "overall_score",
    "universal_confidence", "aggregate_confidence",
)

FORBIDDEN_AVERAGING_KEYS = ("averaged_value", "mean", "average", "chosen_value")


def _node_ids_with_event(graph: Any, event_type: str, key: str) -> List[str]:
    result: List[str] = []
    for event in graph.events(event_type):
        value = event["payload"].get(key)
        if isinstance(value, str):
            result.append(value)
    return result


def _payload_has_forbidden_key(value: Any, forbidden: Sequence[str]) -> bool:
    if isinstance(value, dict):
        return any(key in forbidden or _payload_has_forbidden_key(v, forbidden)
                   for key, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_payload_has_forbidden_key(item, forbidden) for item in value)
    return False


def check_invariants(
    graph: Any,
    *,
    ontology: Optional[Any] = None,
    identity: Optional[Any] = None,
    passports: Optional[Any] = None,
    cache: Optional[Any] = None,
    engine: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Machine-check every invariant from §18.11 against the current graph."""
    checks: Dict[str, Dict[str, Any]] = {
        item["id"]: {"id": item["id"], "rule": item["rule"], "passed": True, "details": []}
        for item in MACHINE_INVARIANTS
    }

    def fail(invariant_id: str, detail: str) -> None:
        checks[invariant_id]["passed"] = False
        checks[invariant_id]["details"].append(detail)

    claims_nodes = [
        n for n in graph.nodes() if n["node_type"] in ("Claim", "Hypothesis")
    ]

    # INV-01 ---------------------------------------------------------------
    for node in claims_nodes:
        payload = node["payload"]
        if not payload.get("scope") or not node["provenance"]:
            fail("INV-01", f"{node['node_id']}: missing scope or provenance")
        if not payload.get("status") or payload["status"] not in CLAIM_STATUSES:
            fail("INV-01", f"{node['node_id']}: missing/invalid status")
        if payload.get("epistemic_type") not in EPISTEMIC_TYPES:
            fail("INV-01", f"{node['node_id']}: missing/invalid epistemic type")
        if node["version"] < 1:
            fail("INV-01", f"{node['node_id']}: missing version")

    # INV-02 ---------------------------------------------------------------
    for node in claims_nodes:
        if node["payload"].get("status") not in ("active", "accepted_within_scope"):
            continue
        structure = claims.belief_structure(graph, node["node_id"])
        if structure["support_chains"] and not structure["independent_primary_bases"]:
            fail("INV-02", f"{node['node_id']}: support does not reach a primary basis")

    # INV-03 ---------------------------------------------------------------
    for node in claims_nodes:
        structure = claims.belief_structure(graph, node["node_id"])
        unique = len({base for chain in structure["support_chains"]
                      for base in chain["primary_bases"]})
        counted = uncertainty.independent_bases(
            graph, node["node_id"], method_id="shared_primary_datasets_v1")["count"]
        if counted is None or counted > unique:
            fail("INV-03", f"{node['node_id']}: shared source counted more than once")

    # INV-04 ---------------------------------------------------------------
    reviewed = set(_node_ids_with_event(graph, "claim_review_triggered", "claim_id"))
    for node in claims_nodes:
        structure = claims.belief_structure(graph, node["node_id"])
        if structure["critical_nodes"] and node["node_id"] not in reviewed:
            fail("INV-04", f"{node['node_id']}: shared dependency did not trigger review")

    # INV-05 ---------------------------------------------------------------
    for conflict in graph.nodes("Conflict"):
        payload = conflict["payload"]
        if _payload_has_forbidden_key(payload.get("resolutions", []),
                                      FORBIDDEN_AVERAGING_KEYS):
            fail("INV-05", f"{conflict['node_id']}: conflict contains an averaged value")
        for side in payload.get("versions", []):
            claim = graph.current(side["claim_id"])
            if claim is None or claim["version"] != side["version"]:
                fail("INV-05", f"{conflict['node_id']}: original claim version was overwritten")

    # INV-06 ---------------------------------------------------------------
    for node_id, versions in graph._nodes.items():
        for version in versions:
            if version["version"] > 1 and version["supersedes"] != version["version"] - 1:
                fail("INV-06", f"{node_id}: broken version chain")
        if len(versions) > 1:
            add_events = [e for e in graph.events("node_added")
                          if e["payload"].get("node_id") == node_id]
            if len(add_events) < len(versions):
                fail("INV-06", f"{node_id}: revision has no event")

    # INV-07 ---------------------------------------------------------------
    human_review_required = set(_node_ids_with_event(
        graph, "condition_human_review_required", "condition_id"))
    for condition in graph.nodes("Condition"):
        linked = graph.outgoing(condition["node_id"], ("tests",))
        if not linked:
            fail("INV-07", f"{condition['node_id']}: condition not linked to a test")
        if not condition["payload"]["machine_checkable"]:
            if condition["node_id"] not in human_review_required:
                # registered but unevaluated informal conditions are allowed
                if graph.events("condition_human_review_required"):
                    fail("INV-07",
                         f"{condition['node_id']}: informal condition lacks human review marker")

    # INV-08 ---------------------------------------------------------------
    for state in graph.nodes("EntityState"):
        linked = (graph.incoming(state["node_id"], ("valid_during",))
                  + graph.outgoing(state["node_id"], ("valid_during",)))
        if not linked and not state["payload"].get("entity_id"):
            fail("INV-08", f"{state['node_id']}: temporal state has no owning Entity")

    # INV-09 ---------------------------------------------------------------
    if ontology is not None:
        for class_id, definition in ontology._classes.items():
            if definition[-1]["version"] > 1:
                events = [e for e in graph.events("ontology_impact_review")
                          if e["payload"].get("class_id") == class_id]
                if not events:
                    fail("INV-09", f"{class_id}: ontology change had no impact review")
    if identity is not None:
        for class_id, versions in identity._criteria.items():
            if versions[-1]["version"] > 1:
                events = [e for e in graph.events("identity_impact_review")
                          if e["payload"].get("class_id") == class_id]
                if not events:
                    fail("INV-09", f"{class_id}: identity criterion change had no impact review")

    # INV-10 ---------------------------------------------------------------
    if passports is not None:
        states = passports.states_for(graph, "NONEXISTENT_ENTITY")
        if any(state != "not_created" for state in states.values()):
            fail("INV-10", "inspecting passport states created a projection")
        for key, passport in passports._cache.items():
            if graph.current(passport["entity_id"]) is None:
                fail("INV-10", f"cached passport {key} has no entity")

    # INV-11 ---------------------------------------------------------------
    for review in graph.nodes("Review"):
        payload = review["payload"]
        if payload.get("independent") is True:
            if payload.get("self_assessment") is not False:
                fail("INV-11", f"{review['node_id']}: independence not separated from self-assessment")
            if payload.get("reviewer") == payload.get("claim_author"):
                fail("INV-11", f"{review['node_id']}: self-assessment marked independent")

    # INV-12 ---------------------------------------------------------------
    if cache is not None:
        for key in cache.stale_keys(graph):
            fail("INV-12", f"stale cache entry {key}")

    # INV-13 ---------------------------------------------------------------
    if engine is not None:
        for result_id, trace in engine._traces.items():
            if trace["approximation_disclosed"] and trace["validated"]:
                fail("INV-13", f"{result_id}: draft presented as validated")
    for event in graph.events():
        if event["event_type"] == "draft_passed_full_gate":
            fail("INV-13", "a draft calculation passed a full-calculation gate")

    # INV-14 ---------------------------------------------------------------
    for node in graph.nodes():
        if _payload_has_forbidden_key(node["payload"], FORBIDDEN_SCORE_KEYS):
            fail("INV-14", f"{node['node_id']}: universal score found in payload")
    for event in graph.events():
        if _payload_has_forbidden_key(event["payload"], FORBIDDEN_SCORE_KEYS):
            fail("INV-14", f"{event['event_id']}: universal score found in event")

    return [checks[item["id"]] for item in MACHINE_INVARIANTS]


def assert_invariants(*args: Any, **kwargs: Any) -> bool:
    failures = [item for item in check_invariants(*args, **kwargs) if not item["passed"]]
    if failures:
        detail = "; ".join(
            f"{item['id']}: {', '.join(item['details'])}" for item in failures
        )
        raise EpistemicContractError(f"machine invariants failed: {detail}")
    return True


def check_principles(graph: Any) -> List[Dict[str, Any]]:
    """Facade for the 15 Section 18 principle consequences."""
    return principles.check_principles(graph)


def assert_principles(graph: Any, *, require_evaluated: bool = False) -> bool:
    return principles.assert_principles(graph, require_evaluated=require_evaluated)


def assert_principles_honesty() -> bool:
    """Facade for the principle manifest's own honesty guard."""
    return principles.assert_principle_manifest_honesty()


def epistemic_manifest() -> Dict[str, Any]:
    return {
        "epistemic_core_version": EPISTEMIC_VERSION,
        "status": "framework_core_before_ui",
        "verified_sources": 0,
        "real_objects": 0,
        "live_adapters": 0,
        "promotable_claims": 0,
        "axes": list(AXES),
        "axis_policy": "six_independent_axes_no_aggregate_score",
        "passport_kinds": list(PASSPORT_KINDS),
        "passport_policy": "lazy_projections_of_one_canonical_graph",
        "energy_channels": list(ENERGY_CHANNELS),
        "claim_statuses": list(CLAIM_STATUSES),
        "epistemic_types": list(EPISTEMIC_TYPES),
        "machine_invariants": list(MACHINE_INVARIANTS),
        "acceptance_scenarios": list(ACCEPTANCE_SCENARIOS),
        "principles_version": principles.EPISTEMIC_PRINCIPLES_VERSION,
        "principles": list(principles.PRINCIPLES),
        "machine_checkable_consequence_count": len(principles.PRINCIPLES),
        "seven_representations": list(principles.SEVEN_REPRESENTATIONS),
        "meta_reasoning": frozen(principles.META_REASONING),
        "observer_non_privilege": list(principles.OBSERVER_NON_PRIVILEGE),
        "statement_statuses": list(principles.STATEMENT_STATUSES),
        "reality_independence_status": principles.REALITY_INDEPENDENCE_STATUS,
        "cross_cases": {
            "A_RICHAT": "not_evaluable_no_primary_sources",
            "B_GIZA": "not_evaluable_no_verified_objects",
            "C_ASTRAEA": "not_evaluable_no_adapter",
        },
        "guards": {
            "no_live_feed": True,
            "no_auto_trade": True,
            "no_bit_to_joule": True,
            "no_cosmic_causality": True,
            "no_universal_confidence_score": True,
            "synthetic_fixture_is_not_evidence": True,
            "conflict_never_auto_averaged": True,
            "core_before_cockpit_panels": True,
            "paper_mode_historical_data_only": True,
            "observer_non_privilege": True,
            "reality_independence_is_commitment_not_fact": True,
            "ontology_insufficient_state": True,
            "paraconsistent_conflict_isolation": True,
            "unknown_never_becomes_false": True,
            "green_test_is_not_physical_confirmation": True,
        },
        "not_implemented": [
            "real source ingestion", "real geodetic objects", "ASTRAEA adapter",
            "live measurement", "physical energy balance of Giza",
            "real Richat/Giza/ASTRAEA cross-case evaluation",
            "Relation Instance and N-ary relation classes",
            "Computational Experiment as a first-class node type",
        ],
    }


def assert_epistemic_honesty() -> bool:
    manifest = epistemic_manifest()
    require(manifest["verified_sources"] == 0, "verified sources must start at zero")
    require(manifest["real_objects"] == 0, "real objects must start at zero")
    require(manifest["live_adapters"] == 0, "no live adapter may be claimed")
    require(manifest["promotable_claims"] == 0, "no claim is promotable without evidence")
    require(len(manifest["axes"]) == 6, "six axes required")
    require(len(manifest["passport_kinds"]) == 10, "ten passport projections required")
    require(len(manifest["machine_invariants"]) == 14, "14 machine invariants required")
    require(len(manifest["acceptance_scenarios"]) == 16, "16 acceptance scenarios required")
    require(len(manifest["seven_representations"]) == 7, "seven representations required")
    require(manifest["meta_reasoning"]["is_eighth_world"] is False,
            "meta-reasoning must not become an eighth world")
    require(manifest["machine_checkable_consequence_count"] == 15,
            "15 machine-checkable principle consequences required")
    require(all(manifest["guards"].values()), "an honesty guard is disabled")
    require(all(value.startswith("not_evaluable")
                for value in manifest["cross_cases"].values()),
            "real cross-cases must not be presented as evaluated")
    assert_principles_honesty()
    return True


def write_epistemic_manifest(path: str) -> str:
    content = canonical_json(epistemic_manifest()) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return content
