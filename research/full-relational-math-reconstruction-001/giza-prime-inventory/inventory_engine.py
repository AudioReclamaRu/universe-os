"""GIZA PRIME stage 2: real landscape inventory and relation discovery.

SCIENTIFIC STATUS
-----------------
This is an INGESTION FRAMEWORK, not a populated inventory.  Zero verified
sources are attached, therefore zero real objects, natural structures and
relations exist in the registers.  Nothing is inferred from prominence, shape
or traditional classification, and no missing value is replaced by a plausible
number.

The framework implements the five required results:
  1. object registry with a strict per-record field contract;
  2. natural-structure registry with geological and subsurface structures as
     first-class elements;
  3. typed relation graph with separate spatial / geological / mechanical /
     acoustic / hydraulic / thermal / gas-dynamic / electromagnetic / functional
     relations and strict separation of established from inferred claims;
  4. automatic, topology-based discovery of overlapping ensembles that does not
     start from a preselected set of monuments;
  5. an incompleteness map covering surveyed, source-known, indirectly
     detected, hidden/destroyed and unknown states.

Adaptive modelling is expressed as numeric / interval / symbolic tiers.  Only a
complete record backed by a verified source can reach the numeric tier.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))

RELATION_CLASSES: Tuple[str, ...] = (
    "spatial", "geological", "mechanical", "acoustic", "hydraulic",
    "thermal", "gas_dynamic", "electromagnetic", "functional",
)
EPISTEMIC_STATUSES: Tuple[str, ...] = (
    "established_documented", "inferred_indirect", "hypothesized_unverified",
)
COVERAGE_STATES: Tuple[str, ...] = (
    "surveyed", "source_known", "indirectly_detected", "hidden_or_destroyed", "unknown",
)
MODELING_TIERS: Tuple[str, ...] = ("numeric", "interval", "symbolic")
REQUIRED_SLOT_IDS: Tuple[str, ...] = (
    "large_pyramid_complexes",
    "small_satellite_unfinished_pyramids",
    "mastabas_necropolis_fields",
    "mortuary_valley_temples",
    "platforms_enclosures_walls",
    "sphinx_and_temple_complex",
    "causeways_roads_ramps_passages",
    "boat_pits_shafts_wells_chambers_galleries",
    "quarries_workshops_settlements_storage",
    "ancient_channels_hydrogeology",
    "bedrock_massifs_fractures_faults",
    "natural_processes",
    "destroyed_buried_ambiguous",
    "interfaces_boundaries",
)
NUMERIC_FIELDS: Tuple[str, ...] = (
    "coordinates", "coordinate_system", "geometry", "elevations", "material",
    "preservation_state", "temporal_intervals",
)


class InventoryValidationError(ValueError):
    """Raised when an inventory artifact violates its declared contract."""


def load_json(filename: str) -> Dict[str, Any]:
    with open(os.path.join(HERE, filename), "r", encoding="utf-8") as handle:
        return json.load(handle)


def inventory_source_contract() -> Dict[str, Any]:
    return load_json("inventory_source_contract.json")


def object_registry() -> Dict[str, Any]:
    return load_json("object_registry.json")


def relation_graph() -> Dict[str, Any]:
    return load_json("relation_graph.json")


def incompleteness_map() -> Dict[str, Any]:
    return load_json("incompleteness_map.json")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryValidationError(message)


def _require_keys(payload: Dict[str, Any], keys: Iterable[str], label: str) -> None:
    for key in keys:
        _require(key in payload, "%s missing %r" % (label, key))


def _populated(value: Any) -> bool:
    return value not in (None, "", [], {})


def validate_source_contract(contract: Optional[Dict[str, Any]] = None) -> bool:
    contract = inventory_source_contract() if contract is None else contract
    _require_keys(contract, (
        "contract_id", "external_citations_attached", "attached_sources",
        "verified_source_count", "required_source_fields", "accepted_source_types",
        "verification_states", "gate",
    ), "inventory_source_contract")
    _require(contract["external_citations_attached"] is False,
             "source contract may not claim external citations")
    _require(contract["attached_sources"] == [], "no source may be attached without verification")
    _require(contract["verified_source_count"] == 0, "verified source count must be zero")
    for field in ("source_id", "source_type", "bibliographic_ref", "datum",
                  "retrieved_at", "verification_state"):
        _require(field in contract["required_source_fields"], "missing source field %s" % field)
    for state in ("verified", "pending", "rejected"):
        _require(state in contract["verification_states"], "missing verification state %s" % state)
    gate = contract["gate"]
    for key in ("no_source_no_record", "pending_is_not_evidence", "rejected_is_not_evidence",
                "no_fabricated_substitute"):
        _require(gate.get(key) is True, "source gate %s must be true" % key)
    return True


def validate_object_registry(registry: Optional[Dict[str, Any]] = None,
                             contract: Optional[Dict[str, Any]] = None) -> bool:
    registry = object_registry() if registry is None else registry
    contract = inventory_source_contract() if contract is None else contract
    _require_keys(registry, (
        "registry_id", "external_citations_attached", "verified_source_count",
        "objects", "natural_structures", "inventory_slots", "record_field_contract",
        "modeling_tiers", "gate",
    ), "object_registry")
    _require(registry["external_citations_attached"] is False,
             "object registry may not claim external citations")
    _require(contract["attached_sources"] == [] and registry["verified_source_count"] == 0,
             "real records require verified sources; none are attached")
    _require(registry["objects"] == [], "real object records forbidden without verified sources")
    _require(registry["natural_structures"] == [],
             "real natural-structure records forbidden without verified sources")

    slots = registry["inventory_slots"]
    _require(isinstance(slots, list) and slots, "inventory_slots must be nonempty")
    slot_ids = [slot["slot_id"] for slot in slots]
    _require(len(slot_ids) == len(set(slot_ids)), "duplicate slot_id")
    _require(set(REQUIRED_SLOT_IDS).issubset(set(slot_ids)), "inventory slot list is incomplete")
    for slot in slots:
        _require_keys(slot, ("slot_id", "landscape_category", "label", "targets_to_seek",
                             "natural_structure", "verified_object_count", "coverage_status",
                             "known_gap", "required_survey_layer"), "inventory slot")
        _require(slot["verified_object_count"] == 0, "slot may not claim verified objects")
        _require(slot["coverage_status"] == "not_inventoried", "slot may not claim inventory")
        _require(bool(slot["known_gap"]), "slot must declare a known gap")
        _require(bool(slot["required_survey_layer"]), "slot must declare a required survey layer")
        _require(bool(slot["targets_to_seek"]), "slot must declare what to seek")
    natural = [slot for slot in slots if slot["natural_structure"] is True]
    _require(len(natural) >= 3, "natural structures must be first-class inventory slots")

    fields = registry["record_field_contract"]["required_fields"]
    for field in NUMERIC_FIELDS + ("source_ids",):
        _require(field in fields, "record field contract missing %s" % field)
    _require(set(registry["modeling_tiers"]) == set(MODELING_TIERS),
             "modeling tiers must be numeric, interval and symbolic")
    gate = registry["gate"]
    for key in ("real_records_require_verified_source", "no_preselected_core",
                "no_fabricated_coordinates", "no_fabricated_elevations",
                "no_fabricated_material", "absence_from_catalogue_is_not_absence_from_system"):
        _require(gate.get(key) is True, "registry gate %s must be true" % key)
    return True


def validate_relation_graph(graph: Optional[Dict[str, Any]] = None,
                            contract: Optional[Dict[str, Any]] = None) -> bool:
    graph = relation_graph() if graph is None else graph
    contract = inventory_source_contract() if contract is None else contract
    _require_keys(graph, (
        "graph_id", "external_citations_attached", "verified_source_count",
        "relation_classes", "epistemic_statuses", "relations", "relation_record_fields",
        "separation_rule", "ingestion_gate",
    ), "relation_graph")
    _require(graph["external_citations_attached"] is False,
             "relation graph may not claim external citations")
    _require(contract["attached_sources"] == [] and graph["verified_source_count"] == 0,
             "relation source count inconsistent with contract")
    _require(graph["relations"] == [], "relations forbidden without verified sources")
    _require(set(graph["relation_classes"]) == set(RELATION_CLASSES),
             "relation classes must cover all nine typed families")
    _require(set(graph["epistemic_statuses"]) == set(EPISTEMIC_STATUSES),
             "epistemic statuses must cover all three states")
    _require("must never be merged" in graph["separation_rule"],
             "separation rule must forbid merging established and inferred relations")
    gate = graph["ingestion_gate"]
    for key in ("require_verified_source_ids", "require_epistemic_status",
                "synthetic_relation_cannot_be_established",
                "inferred_cannot_be_promoted_without_new_evidence",
                "no_direct_pyramid_to_planetary_or_cosmic_bridge"):
        _require(gate.get(key) is True, "relation gate %s must be true" % key)
    return True


def validate_incompleteness_map(mapping: Optional[Dict[str, Any]] = None,
                                registry: Optional[Dict[str, Any]] = None) -> bool:
    mapping = incompleteness_map() if mapping is None else mapping
    registry = object_registry() if registry is None else registry
    _require_keys(mapping, (
        "map_id", "external_citations_attached", "coverage_completeness",
        "states", "state_definitions", "coverage_by_slot", "rules",
    ), "incompleteness_map")
    _require(mapping["external_citations_attached"] is False,
             "incompleteness map may not claim external citations")
    _require(mapping["coverage_completeness"] == "incomplete_unknown",
             "coverage may not be claimed complete")
    _require(set(mapping["states"]) == set(COVERAGE_STATES),
             "coverage states must cover all five categories")
    expected = {slot["slot_id"] for slot in registry["inventory_slots"]}
    rows = mapping["coverage_by_slot"]
    _require({row["slot_id"] for row in rows} == expected,
             "incompleteness map must cover exactly the registry slots")
    for row in rows:
        _require(row["state"] == "unknown", "slot may not claim coverage without sources")
        _require(row["verified_object_count"] == 0, "slot may not claim verified objects")
        _require(bool(row["required_next_step"]), "slot must name its next survey step")
    for key in ("absence_from_catalogue_is_not_absence_from_system",
                "unknown_must_not_be_replaced_by_plausible_number",
                "destroyed_or_buried_remains_in_scope",
                "no_completeness_claim_without_verified_sources"):
        _require(mapping["rules"].get(key) is True, "incompleteness rule %s must be true" % key)
    return True


def assert_inventory_honesty() -> bool:
    return all((
        validate_source_contract(),
        validate_object_registry(),
        validate_relation_graph(),
        validate_incompleteness_map(),
    ))


def modeling_tier_for(record: Dict[str, Any],
                      verified_sources: Optional[Sequence[str]] = None) -> Dict[str, str]:
    """Assign numeric / interval / symbolic tier without inventing any value."""
    source_ids = record.get("source_ids") or []
    if not source_ids:
        return {"tier": "symbolic", "reason": "no_verified_source"}
    verified = set(verified_sources or [])
    if verified and not set(source_ids).issubset(verified):
        return {"tier": "rejected", "reason": "source_not_verified"}
    if all(_populated(record.get(field)) for field in NUMERIC_FIELDS):
        return {"tier": "numeric", "reason": "complete_verified_record"}
    if _populated(record.get("bounded_geometry")) and _populated(record.get("elevation_range")):
        return {"tier": "interval", "reason": "bounded_verified_record"}
    return {"tier": "symbolic", "reason": "partial_unresolved_record"}


def tier_summary(registry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    registry = object_registry() if registry is None else registry
    by_slot = [{"slot_id": slot["slot_id"], **modeling_tier_for({})}
               for slot in registry["inventory_slots"]]
    counts = {tier: sum(1 for row in by_slot if row["tier"] == tier)
              for tier in MODELING_TIERS}
    return {
        "tiers": list(MODELING_TIERS),
        "by_slot": by_slot,
        "counts": counts,
        "real_numeric_records": 0,
        "real_interval_records": 0,
        "fabricated_parameters": 0,
        "rule": "Numeric tier is unreachable without a complete verified record.",
    }


def discover_ensembles(objects: Sequence[str],
                       relations: Sequence[Dict[str, Any]],
                       feature: str) -> Dict[str, Any]:
    """Discover candidate ensembles from declared relations of one feature.

    No object is seeded by name, size, fame or traditional class.  Candidate
    groups are connected components of the typed relation graph only.
    """
    allowed = set(objects)
    selected = [rel for rel in relations
                if feature == "all" or rel.get("relation_class") == feature]
    participants: Set[str] = set()
    for rel in selected:
        source = rel.get("source_object_id")
        target = rel.get("target_object_id")
        if source in allowed and target in allowed and source != target:
            participants.add(source)
            participants.add(target)
    adjacency: Dict[str, Set[str]] = {oid: set() for oid in participants}
    for rel in selected:
        source = rel.get("source_object_id")
        target = rel.get("target_object_id")
        if source in participants and target in participants and source != target:
            adjacency[source].add(target)
            adjacency[target].add(source)

    # An isolated object is not an ensemble; only declared relations create one.
    components: List[List[str]] = []
    unseen = set(participants)
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        component = {start}
        while stack:
            current = stack.pop()
            for neighbour in sorted(adjacency[current]):
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    component.add(neighbour)
                    stack.append(neighbour)
        components.append(sorted(component))

    by_status: Dict[str, List[str]] = {status: [] for status in EPISTEMIC_STATUSES}
    for rel in selected:
        status = rel.get("epistemic_status")
        if status in by_status:
            by_status[status].append(rel["relation_id"])

    return {
        "feature": feature,
        "candidates": components,
        "relations_by_epistemic_status": by_status,
        "no_preselected_core": True,
        "ranking_by_size_fame_tradition": False,
        "physical_claim": False,
        "status": "structural_candidate_only",
    }


SYNTHETIC_DEMONSTRATION: Dict[str, Any] = {
    "synthetic": True,
    "physical_claim": False,
    "label": "capability demonstration only — not Giza inventory data",
    "objects": [
        "major_pyramid_D", "small_pyramid_C", "sphinx_E",
        "bedrock_fracture_B", "drainage_channel_A", "well_F", "quarry_G",
    ],
    "relations": [
        {"relation_id": "r1", "source_object_id": "drainage_channel_A", "target_object_id": "well_F", "relation_class": "hydraulic", "epistemic_status": "hypothesized_unverified"},
        {"relation_id": "r2", "source_object_id": "drainage_channel_A", "target_object_id": "bedrock_fracture_B", "relation_class": "hydraulic", "epistemic_status": "hypothesized_unverified"},
        {"relation_id": "r3", "source_object_id": "bedrock_fracture_B", "target_object_id": "quarry_G", "relation_class": "geological", "epistemic_status": "inferred_indirect"},
        {"relation_id": "r4", "source_object_id": "bedrock_fracture_B", "target_object_id": "major_pyramid_D", "relation_class": "geological", "epistemic_status": "inferred_indirect"},
        {"relation_id": "r5", "source_object_id": "small_pyramid_C", "target_object_id": "major_pyramid_D", "relation_class": "spatial", "epistemic_status": "inferred_indirect"},
        {"relation_id": "r6", "source_object_id": "sphinx_E", "target_object_id": "bedrock_fracture_B", "relation_class": "mechanical", "epistemic_status": "hypothesized_unverified"},
        {"relation_id": "r7", "source_object_id": "quarry_G", "target_object_id": "small_pyramid_C", "relation_class": "mechanical", "epistemic_status": "hypothesized_unverified"},
        {"relation_id": "r8", "source_object_id": "well_F", "target_object_id": "drainage_channel_A", "relation_class": "spatial", "epistemic_status": "inferred_indirect"},
    ],
}


def discover_all_ensembles(fixture: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Discover overlapping ensembles across every typed relation family."""
    fixture = SYNTHETIC_DEMONSTRATION if fixture is None else fixture
    objects = fixture["objects"]
    relations = fixture["relations"]
    features = sorted({rel["relation_class"] for rel in relations})
    per_feature = {feature: discover_ensembles(objects, relations, feature)
                   for feature in features}
    membership: Dict[str, List[Dict[str, Any]]] = {}
    for feature, result in per_feature.items():
        for index, component in enumerate(result["candidates"]):
            for object_id in component:
                membership.setdefault(object_id, []).append(
                    {"feature": feature, "ensemble_index": index}
                )
    multi = {oid: rows for oid, rows in sorted(membership.items()) if len(rows) > 1}
    return {
        "synthetic": fixture.get("synthetic", False),
        "physical_claim": False,
        "per_feature": per_feature,
        "overlapping_members": multi,
        "overlap_count": len(multi),
        "no_preselected_core": True,
        "discovery_basis": "declared_relation_topology_only",
        "caveat": "Demonstrates capability only; no relation here is Giza evidence.",
    }


def discover_real_ensembles() -> Dict[str, Any]:
    """Discovery on the current verified registers: necessarily empty."""
    registry = object_registry()
    graph = relation_graph()
    object_ids = ([row["object_id"] for row in registry["objects"]]
                  + [row["structure_id"] for row in registry["natural_structures"]])
    by_feature = {feature: discover_ensembles(object_ids, graph["relations"], feature)
                  for feature in RELATION_CLASSES}
    return {
        "verified_objects": len(object_ids),
        "verified_relations": len(graph["relations"]),
        "ensembles_discovered": 0,
        "per_feature": {key: value["candidates"] for key, value in by_feature.items()},
        "status": "no_verified_data_no_discovery",
        "no_preselected_core": True,
    }


def incompleteness_report() -> Dict[str, Any]:
    mapping = incompleteness_map()
    counts = {state: sum(1 for row in mapping["coverage_by_slot"] if row["state"] == state)
              for state in COVERAGE_STATES}
    return {
        "coverage_completeness": mapping["coverage_completeness"],
        "states": list(COVERAGE_STATES),
        "slot_counts": counts,
        "rows": mapping["coverage_by_slot"],
        "absence_rule": mapping["rules"]["absence_from_catalogue_is_not_absence_from_system"],
    }


def build_inventory_report() -> Dict[str, Any]:
    registry = object_registry()
    graph = relation_graph()
    contract = inventory_source_contract()
    return {
        "schema_version": "1.0",
        "report_id": "GIZA_REAL_LANDSCAPE_INVENTORY_FRAMEWORK_REPORT",
        "stage": "REAL_LANDSCAPE_INVENTORY_AND_RELATION_DISCOVERY",
        "architecture_version": registry["architecture_version"],
        "scientific_status": "ingestion_framework_not_a_reconstruction",
        "external_citations_attached": False,
        "five_results": {
            "1_object_registry": {
                "registry_id": registry["registry_id"],
                "verified_objects": len(registry["objects"]),
                "slot_count": len(registry["inventory_slots"]),
                "required_fields": registry["record_field_contract"]["required_fields"],
            },
            "2_natural_structures_registry": {
                "verified_natural_structures": len(registry["natural_structures"]),
                "natural_structure_slots": [slot["slot_id"] for slot in registry["inventory_slots"]
                                            if slot["natural_structure"] is True],
            },
            "3_relation_graph": {
                "graph_id": graph["graph_id"],
                "relation_classes": graph["relation_classes"],
                "epistemic_statuses": graph["epistemic_statuses"],
                "verified_relations": len(graph["relations"]),
                "separation_rule": graph["separation_rule"],
            },
            "4_automatic_ensemble_discovery": discover_real_ensembles(),
            "5_incompleteness_map": incompleteness_report(),
        },
        "adaptive_modeling": tier_summary(registry),
        "capability_demonstration": discover_all_ensembles(),
        "validation": {
            "source_contract": validate_source_contract(contract),
            "object_registry": validate_object_registry(registry, contract),
            "relation_graph": validate_relation_graph(graph, contract),
            "incompleteness_map": validate_incompleteness_map(),
            "inventory_honesty": assert_inventory_honesty(),
        },
        "no_fabricated_parameters": True,
        "no_preselected_core": True,
        "giza_cosmos_claim": False,
    }


def write_inventory_report(path: str) -> str:
    payload = build_inventory_report()
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    return path


__all__ = [name for name in dir() if not name.startswith("_")]
