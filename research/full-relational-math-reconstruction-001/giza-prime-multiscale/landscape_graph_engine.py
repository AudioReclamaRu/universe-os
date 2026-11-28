"""Open functional-landscape graph engine for GIZA PRIME.

SCIENTIFIC STATUS
-----------------
This module is an ARCHITECTURE layer, not a historical reconstruction.  It
stores the open graph G = (V, E, I, P, T, Theta), discovers candidate ensembles
from declared relations, and reports coverage gaps.  It does not attach sources,
coordinates, measurements or real-world object identities.

The existing nine-DOF mechanics package is a *synthetic projection* of this
graph, not the graph itself and not a privileged core.  PRIME is defined here
as a property of discovered interaction ensembles; no object set and no
frequency is presupposed.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))

LANDSCAPE_CATEGORIES: Tuple[str, ...] = (
    "monumental", "architectural", "linear", "subsurface", "geological",
    "hydrological", "infrastructural", "natural", "nonobvious", "interface",
)
MODEL_FAMILIES: Tuple[str, ...] = (
    "mechanical", "acoustic", "hydraulic", "thermal", "gas_dynamic",
    "electromagnetic", "combined",
)
PHYSICAL_RELATION_CLASSES: Tuple[str, ...] = (
    "mechanical_contact", "hydraulic_connection", "acoustic_coupling",
    "thermal_exchange", "electromagnetic_coupling", "mass_transfer",
    "momentum_transfer", "functional_ensemble_membership", "temporal_succession",
)
ALLOWED_STATUSES: Tuple[str, ...] = (
    "measured", "literature_supported", "model_supported", "idealized_model_only",
    "conservation_bounded_not_attributed", "analogy_only", "hypothesis_unverified",
    "not_evaluable_missing_data",
)
PROVENANCE_RESTRICTED_CLASSES: Tuple[str, ...] = (
    "measured_current", "published_measurement", "historical_record",
    "geologically_inferred", "reconstructed_uncertain",
)


class LandscapeValidationError(ValueError):
    """Raised when a landscape artifact violates its declared contract."""


def load_json(filename: str) -> Dict[str, Any]:
    path = os.path.join(HERE, filename)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def functional_landscape_graph() -> Dict[str, Any]:
    return load_json("functional_landscape_graph.json")


def inventory_coverage_register() -> Dict[str, Any]:
    return load_json("inventory_coverage_register.json")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LandscapeValidationError(message)


def _require_keys(payload: Dict[str, Any], keys: Iterable[str], label: str) -> None:
    for key in keys:
        _require(key in payload, "%s missing %r" % (label, key))


def validate_functional_landscape_graph(graph: Optional[Dict[str, Any]] = None) -> bool:
    graph = functional_landscape_graph() if graph is None else graph
    _require_keys(graph, (
        "graph_id", "architecture_version", "scientific_status",
        "external_citations_attached", "open_world", "no_primordial_core",
        "coverage_status", "formal_object", "categories", "V", "E", "I", "P", "T",
        "Theta", "model_projections", "discovery_rules", "prime_definition",
    ), "functional_landscape_graph")
    _require(graph["external_citations_attached"] is False,
             "landscape graph may not claim external citations")
    _require(graph["open_world"] is True, "landscape graph must be open-world")
    _require(graph["no_primordial_core"] is True, "no primordial object set is allowed")
    _require(set(graph["categories"]) == set(LANDSCAPE_CATEGORIES),
             "category set must match the declared functional landscape categories")

    nodes = graph["V"]
    _require(isinstance(nodes, list) and nodes, "V must be a nonempty list")
    node_ids = [node["node_id"] for node in nodes]
    _require(len(node_ids) == len(set(node_ids)), "duplicate node_id in V")
    known = set(node_ids)
    for category in LANDSCAPE_CATEGORIES:
        accepted_kinds = ("object_class", "interface_class") if category == "interface" else ("object_class",)
        _require(any(node.get("node_kind") in accepted_kinds and
                     node.get("category") == category for node in nodes),
                 "missing object class for %s" % category)
    _require(any(node.get("node_kind") == "interface_class" for node in nodes),
             "interfaces must be first-class nodes")
    seeds = [node for node in nodes if node.get("node_kind") == "synthetic_seed_instance"]
    _require(seeds, "at least one synthetic seed instance is required")
    for node in nodes:
        _require(node.get("evidence_class") not in PROVENANCE_RESTRICTED_CLASSES,
                 "provenance-bearing evidence class is forbidden with zero sources")
        if node.get("node_kind") == "synthetic_seed_instance":
            _require(node.get("evidence_class") == "idealized_design",
                     "seed instances must be idealized_design")
            _require(node.get("source_id") == "synthetic_reference_fixture",
                     "seed instances must use the synthetic fixture source id")
            _require(node.get("real_world_claim") is False,
                     "seed instances may not claim real-world identity")

    edges = graph["E"]
    _require(isinstance(edges, list) and edges, "E must be a nonempty list")
    edge_ids = [edge["edge_id"] for edge in edges]
    _require(len(edge_ids) == len(set(edge_ids)), "duplicate edge_id in E")
    for edge in edges:
        _require_keys(edge, ("edge_id", "source", "target", "relation_class",
                             "carrier", "status", "direction"), "edge")
        _require(edge["source"] in known and edge["target"] in known,
                 "edge %s references unknown node" % edge["edge_id"])
        _require(edge["relation_class"] in PHYSICAL_RELATION_CLASSES + ("class_membership",),
                 "unknown relation_class in %s" % edge["edge_id"])
        _require(edge["status"] in ALLOWED_STATUSES,
                 "unknown edge status in %s" % edge["edge_id"])

    interfaces = graph["I"]
    _require(isinstance(interfaces, list) and interfaces, "I must be a nonempty list")
    for item in interfaces:
        _require_keys(item, ("interface_id", "label", "carrier", "status",
                             "interface_first", "required_measurements"), "interface")
        _require(item["interface_first"] is True, "interfaces must be first-class")
        _require(item["status"] == "not_evaluable_missing_data",
                 "unmeasured interface may not be promoted")
        _require(bool(item["required_measurements"]), "interface needs discriminating measurements")

    processes = graph["P"]
    _require(isinstance(processes, list) and processes, "P must be a nonempty list")
    for item in processes:
        _require_keys(item, ("process_id", "label", "conserved_quantities",
                             "operator_family", "current_evaluable", "status"), "process")
        _require(bool(item["conserved_quantities"]), "process needs conserved quantities")
        _require(item["operator_family"] in MODEL_FAMILIES,
                 "unknown process operator family")
    families = {item["operator_family"] for item in processes}
    _require(set(MODEL_FAMILIES).issubset(families), "processes must cover every model family")

    states = graph["T"]
    _require(isinstance(states, list) and states, "T must be a nonempty list")
    state_ids = {item["state_id"] for item in states}
    _require(len(state_ids) == len(states), "duplicate state_id in T")
    for item in states:
        _require_keys(item, ("state_id", "label", "synchrony_assumption",
                             "allowed_transitions"), "temporal state")
        _require(item["synchrony_assumption"] is False,
                 "diachronous objects must not be assumed synchronous")
        for target in item["allowed_transitions"]:
            _require(target in state_ids, "unknown temporal transition target")

    theta = graph["Theta"]
    _require_keys(theta, ("coverage_register_ref", "parameter_registry_ref",
                          "source_register_ref", "real_source_ingestion_contract_ref",
                          "functional_object_registry_ref", "coverage_completeness",
                          "uncertainty_policy", "missing_evidence_rule",
                          "promotion_rule", "priority_rule"), "Theta")
    _require(theta["coverage_completeness"] == "incomplete_unknown",
             "coverage may not be claimed complete")

    projections = graph["model_projections"]
    _require({item["family"] for item in projections} == set(MODEL_FAMILIES),
             "model projections must cover every declared family")
    evaluable = [item["family"] for item in projections if item["current_evaluable"]]
    _require(evaluable == ["mechanical"],
             "only the synthetic mechanical projection may be currently evaluable")

    rules = graph["discovery_rules"]
    for key in ("no_primordial_core", "priority_by_interaction_topology_only",
                "size_fame_or_tradition_priority_forbidden", "multi_membership_allowed",
                "overlapping_ensembles_allowed", "interface_priority_allowed",
                "synchrony_must_be_justified", "missing_object_not_missing_from_system"):
        _require(rules.get(key) is True, "discovery rule %s must be true" % key)

    prime = graph["prime_definition"]
    _require(prime["scope"] == "emergent_property_of_interaction_ensemble",
             "PRIME must be defined on discovered ensembles")
    _require(prime["preset_object_set_forbidden"] is True,
             "PRIME may not use a preset object set")
    _require(prime["hardcoded_frequency_hz"] is None,
             "PRIME may not have a hardcoded frequency")
    return True


def validate_inventory_coverage_register(register: Optional[Dict[str, Any]] = None) -> bool:
    register = inventory_coverage_register() if register is None else register
    _require_keys(register, (
        "register_id", "architecture_version", "external_citations_attached",
        "catalogued_real_objects", "coverage_basis", "coverage_completeness",
        "synthetic_seed_objects_only", "absence_rule", "promotion_gate", "categories",
    ), "inventory_coverage_register")
    _require(register["external_citations_attached"] is False,
             "coverage register may not claim external citations")
    _require(register["catalogued_real_objects"] == 0,
             "no real object may be catalogued without sources")
    _require(register["coverage_completeness"] == "incomplete_unknown",
             "coverage may not be claimed complete")
    _require(register["synthetic_seed_objects_only"] is True,
             "only synthetic seeds may populate the current graph")
    categories = register["categories"]
    _require({item["category"] for item in categories} == set(LANDSCAPE_CATEGORIES),
             "coverage register must cover every landscape category")
    for item in categories:
        _require_keys(item, ("category", "label", "catalogued_real_objects",
                             "coverage_status", "coverage_confidence", "known_gap",
                             "required_survey_layer", "promotion_gate"), "coverage category")
        _require(item["catalogued_real_objects"] == 0,
                 "category %s cannot catalog real objects" % item["category"])
        _require(item["coverage_status"] == "not_inventoried",
                 "category %s may not claim inventory" % item["category"])
        _require(item["coverage_confidence"] == "unknown",
                 "category %s coverage confidence must be unknown" % item["category"])
        _require(bool(item["known_gap"]), "category %s needs an explicit gap" % item["category"])
    return True


def landscape_signature(graph: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    graph = functional_landscape_graph() if graph is None else graph
    node_kinds: Dict[str, int] = {}
    for node in graph["V"]:
        node_kinds[node["node_kind"]] = node_kinds.get(node["node_kind"], 0) + 1
    relation_classes: Dict[str, int] = {}
    for edge in graph["E"]:
        relation_classes[edge["relation_class"]] = relation_classes.get(edge["relation_class"], 0) + 1
    return {
        "architecture_version": graph["architecture_version"],
        "categories": len(graph["categories"]),
        "node_count": len(graph["V"]),
        "node_kinds": dict(sorted(node_kinds.items())),
        "edge_count": len(graph["E"]),
        "relation_classes": dict(sorted(relation_classes.items())),
        "interface_count": len(graph["I"]),
        "process_count": len(graph["P"]),
        "temporal_state_count": len(graph["T"]),
        "model_family_count": len(graph["model_projections"]),
        "external_citations_attached": graph["external_citations_attached"],
    }


def discover_candidate_ensembles(graph: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Derive topology-only ensemble candidates; no physical priority is assigned."""
    graph = functional_landscape_graph() if graph is None else graph
    nodes = {node["node_id"]: node for node in graph["V"]}
    seeds = sorted(node_id for node_id, node in nodes.items()
                   if node.get("node_kind") == "synthetic_seed_instance")
    adjacency: Dict[str, Set[str]] = {seed: set() for seed in seeds}
    for edge in graph["E"]:
        if edge["relation_class"] not in PHYSICAL_RELATION_CLASSES:
            continue
        if edge["source"] in adjacency and edge["target"] in adjacency:
            adjacency[edge["source"]].add(edge["target"])
            adjacency[edge["target"]].add(edge["source"])

    components: List[List[str]] = []
    unseen = set(seeds)
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        component: Set[str] = {start}
        while stack:
            current = stack.pop()
            for neighbour in sorted(adjacency[current]):
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    component.add(neighbour)
                    stack.append(neighbour)
        components.append(sorted(component))

    class_groups: Dict[str, List[str]] = {}
    for seed in seeds:
        for edge in graph["E"]:
            if (edge["relation_class"] == "class_membership" and edge["source"] == seed):
                class_groups.setdefault(edge["target"], []).append(seed)
    shared_class = [{"class_node": key, "members": sorted(set(value))}
                    for key, value in sorted(class_groups.items()) if len(set(value)) > 1]

    seed_interfaces = sorted({edge["relation_class"] for edge in graph["E"]
                              if edge["relation_class"] in PHYSICAL_RELATION_CLASSES})

    return {
        "discovery_basis": "declared_interaction_topology_only",
        "ranking_by_size_fame_tradition": False,
        "overlapping_membership_allowed": True,
        "physical_claim": False,
        "status": "structural_candidate_not_physical_evidence",
        "seed_count": len(seeds),
        "connected_ensemble_candidates": components,
        "shared_class_candidates": shared_class,
        "interface_carrier_classes": seed_interfaces,
        "caveat": "Candidates are graph-topology hypotheses; they are not discovered historical functions.",
    }


def model_projection_summary(graph: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    graph = functional_landscape_graph() if graph is None else graph
    rows = [{
        "family": item["family"],
        "current_evaluable": item["current_evaluable"],
        "projection_scope": item["projection_scope"],
        "status": item["status"],
        "operator_space": list(item["operator_space"]),
    } for item in graph["model_projections"]]
    return {
        "families": rows,
        "evaluable_families": [row["family"] for row in rows if row["current_evaluable"]],
        "non_evaluable_families": [row["family"] for row in rows if not row["current_evaluable"]],
        "no_single_model_claims_whole_landscape": True,
    }


def projection_to_mechanics(functional_objects: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Expose the current nine-DOF solver as one explicitly bounded projection."""
    functional_objects = (functional_objects if functional_objects is not None
                          else load_json("functional_objects.json"))
    object_ids = [item["id"] for item in functional_objects["objects"]]
    return {
        "projection_scope": "synthetic_fixture_only",
        "object_ids": object_ids,
        "dof_count": len(object_ids),
        "general_landscape_model_claim": False,
        "primordial_core_claim": False,
        "coverage_completeness": "incomplete_unknown",
        "note": "Variable-size graph is primary; this DOF set is only the currently evaluable synthetic projection.",
    }


def coverage_gap_report(register: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    register = inventory_coverage_register() if register is None else register
    return {
        "coverage_completeness": register["coverage_completeness"],
        "catalogued_real_objects": register["catalogued_real_objects"],
        "absence_rule": register["absence_rule"],
        "gaps": [{
            "category": item["category"],
            "coverage_status": item["coverage_status"],
            "known_gap": item["known_gap"],
            "required_survey_layer": item["required_survey_layer"],
        } for item in register["categories"]],
    }


def landscape_architecture_summary() -> Dict[str, Any]:
    graph = functional_landscape_graph()
    register = inventory_coverage_register()
    return {
        "architecture_version": graph["architecture_version"],
        "scientific_status": graph["scientific_status"],
        "external_citations_attached": graph["external_citations_attached"],
        "open_world": graph["open_world"],
        "no_primordial_core": graph["no_primordial_core"],
        "signature": landscape_signature(graph),
        "prime_definition": graph["prime_definition"],
        "discovery_rules": graph["discovery_rules"],
        "candidate_ensembles": discover_candidate_ensembles(graph),
        "model_projections": model_projection_summary(graph),
        "mechanics_projection": projection_to_mechanics(),
        "coverage_gaps": coverage_gap_report(register),
        "validation": {
            "functional_landscape_graph": validate_functional_landscape_graph(graph),
            "inventory_coverage_register": validate_inventory_coverage_register(register),
        },
    }


__all__ = [name for name in dir() if not name.startswith("_")]
