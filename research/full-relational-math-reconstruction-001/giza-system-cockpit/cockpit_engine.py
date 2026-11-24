"""GIZA PRIME x UNIVERSE OS — integrated system cockpit (Stage A + Stage G core).

This module builds the machine-readable manifest consumed by ``index.html``.
It is the single source of truth for what the cockpit may display:

* project / sector registry with honest adapter statuses;
* the versioned SystemEvent contract (Issue #7, section 14.4);
* strict separation of physical, informational and conceptual channels;
* domain guards that reject unit mixing, fake causality, auto-trading and a
  measured-physical interpretation of intent vector 42;
* a deterministic, offline-capable data payload for the visual shell.

No GUI is launched here.  No integration is simulated: a missing adapter is
reported as ``not_implemented`` / ``unavailable`` / ``conceptual``.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))


class CockpitContractError(ValueError):
    """Raised when a cockpit artifact or an event violates its contract."""


def load_json(filename: str) -> Dict[str, Any]:
    with open(os.path.join(HERE, filename), "r", encoding="utf-8") as handle:
        return json.load(handle)


def system_contract() -> Dict[str, Any]:
    return load_json("system_contract.json")


def project_registry() -> Dict[str, Any]:
    return load_json("project_registry.json")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CockpitContractError(message)


def _unit_class(unit: Optional[str], contract: Dict[str, Any]) -> Optional[str]:
    if unit is None:
        return None
    for class_name, units in contract["unit_classes"].items():
        if unit in units:
            return class_name
    raise CockpitContractError("unregistered unit: %r" % unit)


def validate_system_contract(contract: Optional[Dict[str, Any]] = None) -> bool:
    contract = system_contract() if contract is None else contract
    required = (
        "event_id", "project_id", "sector_id", "entity_id", "event_type",
        "event_time", "ingest_time", "source_id", "payload", "units",
        "coordinate_frame", "model_version", "evidence_status", "uncertainty",
        "permissions",
    )
    _require(tuple(contract["system_event_fields"]) == required,
             "SystemEvent field list must match section 14.4")
    rules = contract["separation_rules"]
    for key in (
        "no_physical_information_mixing", "vector_42_is_conceptual_until_measured",
        "vector_42_physical_unit_forbidden", "business_metrics_are_not_physical_energy",
        "astraea_correlation_is_not_causality", "astraea_auto_trade_forbidden",
        "cross_domain_link_requires_mechanism_and_evidence",
        "unknown_uncertainty_is_not_zero", "synthetic_fixture_never_verified",
        "no_pyramid_to_planetary_or_cosmic_bridge",
    ):
        _require(rules.get(key) is True, "separation rule %s must be true" % key)
    _require("physical" in contract["unit_classes"]
             and "informational" in contract["unit_classes"]
             and "conceptual" in contract["unit_classes"],
             "three unit classes are required")
    return True


def validate_project_registry(registry: Optional[Dict[str, Any]] = None,
                              contract: Optional[Dict[str, Any]] = None) -> bool:
    registry = project_registry() if registry is None else registry
    contract = system_contract() if contract is None else contract
    nodes = {node["node_id"] for node in registry["nodes"]}
    expected = {"MEGABRAIN", "UNIVERSE_OS", "UNIVERSE_2_0", "UNIVERSE_3_0",
                "GIZA_PRIME", "ASTRAEA", "EARTH_EAR"}
    _require(nodes == expected, "registry must declare exactly seven system nodes")
    for node in registry["nodes"]:
        _require(node["status"] in registry["status_vocabulary"],
                 "unknown node status for %s" % node["node_id"])
        for point in node["integration_points"]:
            _require(point["status"] in set(registry["status_vocabulary"]) | {"forbidden", "empty"},
                     "unknown adapter status for %s/%s" % (node["node_id"], point["id"]))
    sectors = {sector["sector_id"] for sector in registry["business_sectors"]}
    _require(len(sectors) == len(registry["business_sectors"]), "duplicate sector id")
    _require({"WEB_SITES", "TG_CULTURE_OF_VOICE", "TG_PRIMARY_SOURCE",
              "SOCIAL_NETWORKS", "BUSINESS_ASSISTANT"}.issubset(sectors),
             "business sector list is incomplete")
    for sector in registry["business_sectors"]:
        _require(sector["metrics_domain"] == "informational",
                 "business metrics must stay informational: %s" % sector["sector_id"])
    _require(registry["intent_vector_42"]["physical_dimension"] is None,
             "vector 42 must not declare a physical dimension")
    _require(registry["intent_vector_42"]["units"] == "conceptual",
             "vector 42 must remain conceptual")
    physical = registry["energy_domain_separation"]["physical_channels"]
    informational = registry["energy_domain_separation"]["informational_channels"]
    for channel in physical:
        _require(_unit_class(channel["unit"], contract) == "physical",
                 "physical channel has non-physical unit: %s" % channel["id"])
    for channel in informational:
        _require(_unit_class(channel["unit"], contract) in ("informational", "conceptual"),
                 "informational channel has physical unit: %s" % channel["id"])
    _require(registry["energy_domain_separation"]["mixing_forbidden"] is True,
             "channel mixing must be forbidden")
    return True


def validate_event(event: Dict[str, Any],
                   contract: Optional[Dict[str, Any]] = None) -> bool:
    """Validate a single SystemEvent against the common contract."""
    contract = system_contract() if contract is None else contract
    registry = project_registry()
    for field in contract["system_event_fields"]:
        _require(field in event, "SystemEvent missing %s" % field)
    _require(not event["event_id"] or isinstance(event["event_id"], str),
             "event_id must be a string")
    node_ids = {node["node_id"] for node in registry["nodes"]}
    _require(event["project_id"] in node_ids, "unknown project_id %r" % event["project_id"])
    if event["sector_id"] is not None:
        sector_ids = {s["sector_id"] for s in registry["business_sectors"]}
        _require(event["sector_id"] in sector_ids,
                 "unknown sector_id %r" % event["sector_id"])
    _require(event["event_type"] in contract["event_types"],
             "unknown event_type %r" % event["event_type"])
    _require(event["evidence_status"] in contract["evidence_statuses"],
             "unknown evidence_status %r" % event["evidence_status"])
    unit_class = _unit_class(event["units"], contract)
    if event["project_id"] == "EARTH_EAR" and event["entity_id"] == "VECTOR_42":
        _require(event["units"] in (None, "conceptual"),
                 "vector 42 may not carry a physical unit")
        _require(unit_class in (None, "conceptual"),
                 "vector 42 may not carry a physical unit class")
    if event["sector_id"] is not None:
        _require(unit_class in (None, "informational", "conceptual"),
                 "business sector event may not carry a physical unit")
    _require(bool(event["permissions"]), "permissions record is required")
    _require(event["uncertainty"] != 0 or event["uncertainty"] is None,
             "unknown uncertainty must be null, not zero")
    return True


def validate_cross_domain_link(link: Dict[str, Any],
                               contract: Optional[Dict[str, Any]] = None) -> bool:
    contract = system_contract() if contract is None else contract
    for field in contract["cross_domain_link_requirements"]:
        _require(bool(link.get(field)), "cross-domain link missing %s" % field)
    _require(bool(link.get("mechanism_definition")),
             "cross-domain link requires a concrete mechanism")
    _require(bool(link.get("alternative_explanations_checked")),
             "cross-domain link requires alternative explanations")
    return True


def validate_astraea_result(result: Dict[str, Any],
                            contract: Optional[Dict[str, Any]] = None) -> bool:
    """Astraea may report candidates; it may never become a trade command."""
    contract = system_contract() if contract is None else contract
    _require(result.get("project_id") == "ASTRAEA", "not an ASTRAEA result")
    _require(result.get("auto_trade") is False,
             "ASTRAEA result must not authorize automatic trading")
    _require(result.get("claim") in ("candidate", "negative", "inconclusive"),
             "ASTRAEA claim must stay research-grade")
    _require(bool(result.get("null_models_checked")),
             "ASTRAEA candidate requires null-model checks")
    _require(bool(result.get("holdout_checked")),
             "ASTRAEA candidate requires holdout confirmation")
    return True


def adapter_summary(registry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    registry = project_registry() if registry is None else registry
    counts: Dict[str, int] = {}
    for node in registry["nodes"]:
        for point in node["integration_points"]:
            counts[point["status"]] = counts.get(point["status"], 0) + 1
    for sector in registry["business_sectors"]:
        counts[sector["status"]] = counts.get(sector["status"], 0) + 1
    return {
        "counts": counts,
        "simulated_integrations": 0,
        "policy": registry["note"],
        "read_only_unknown_integrations": True,
    }


VIEWS: Sequence[Dict[str, str]] = (
    {"id": "spatial", "label": "SPATIAL", "node": "GIZA_PRIME"},
    {"id": "system", "label": "SYSTEM ARCHITECTURE", "node": "MEGABRAIN"},
    {"id": "relations", "label": "RELATION GRAPH", "node": "GIZA_PRIME"},
    {"id": "time", "label": "TIME / SYNC", "node": "ASTRAEA"},
    {"id": "evidence", "label": "EVIDENCE / PROVENANCE", "node": "UNIVERSE_OS"},
    {"id": "intent", "label": "INTENT / VECTOR 42", "node": "EARTH_EAR"},
    {"id": "operations", "label": "OPERATIONS", "node": "MEGABRAIN"},
    {"id": "business", "label": "BUSINESS SECTORS", "node": "EARTH_EAR"},
    {"id": "versions", "label": "VERSION COMPARE", "node": "UNIVERSE_OS"},
)

# Known, verifiable software iterations.  These are software releases, not new
# scientific atlas versions: no verified geodetic source has been added.
KNOWN_ITERATIONS: Sequence[Dict[str, str]] = (
    {
        "id": "SW-REL-001",
        "commit": "9352ffd29a44316e92c9bff976ce4c9ae7c91cfc",
        "kind": "software",
        "label": "corrected physics + open landscape architecture",
        "scientific_atlas_version": "none",
    },
    {
        "id": "SW-REL-002",
        "commit": "beab007f5ed92b59e8b010c2d5f885357d347c1b",
        "kind": "software",
        "label": "cross-version float-repr report comparison",
        "scientific_atlas_version": "none",
    },
    {
        "id": "SW-STAGE-INVENTORY",
        "commit": "working_tree",
        "kind": "framework",
        "label": "real landscape inventory ingestion framework (0 verified sources)",
        "scientific_atlas_version": "none",
    },
    {
        "id": "SW-STAGE-COCKPIT",
        "commit": "working_tree",
        "kind": "framework",
        "label": "Stage A contracts + Stage G visual cockpit shell",
        "scientific_atlas_version": "none",
    },
)


def cockpit_manifest() -> Dict[str, Any]:
    contract = system_contract()
    registry = project_registry()
    return {
        "schema_version": "1.0",
        "manifest_id": "UNIVERSE_OS_INTEGRATED_SYSTEM_COCKPIT",
        "architecture_version": contract["architecture_version"],
        "status": "framework_no_live_integration_no_verified_geodetic_data",
        "human_owner": registry["human_owner"],
        "coordination_layer": registry["coordination_layer"],
        "views": list(VIEWS),
        "nodes": registry["nodes"],
        "business_sectors": registry["business_sectors"],
        "intent_vector_42": registry["intent_vector_42"],
        "energy_domains": registry["energy_domain_separation"],
        "system_event_fields": contract["system_event_fields"],
        "evidence_statuses": contract["evidence_statuses"],
        "unit_classes": contract["unit_classes"],
        "separation_rules": contract["separation_rules"],
        "adapters": adapter_summary(registry),
        "iterations": list(KNOWN_ITERATIONS),
        "verified_geodetic_objects": 0,
        "verified_sources": 0,
        "synthetic_fixture_available": True,
        "giza_cosmos_claim": False,
        "vector_42_is_physical_energy": False,
        "astraea_auto_trade": False,
    }


def _json_default(value: Any) -> str:
    return str(value)


def write_cockpit_data(path: str) -> str:
    """Write an offline-loadable JS payload so index.html works from file://."""
    payload = cockpit_manifest()
    json_text = json.dumps(payload, sort_keys=True, indent=2,
                           ensure_ascii=False, allow_nan=False,
                           default=_json_default)
    digest = hashlib.sha256(json_text.encode("utf-8")).hexdigest()
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("/* generated by cockpit_engine.py — do not edit by hand */\n")
        handle.write("window.COCKPIT_MANIFEST_SHA256 = %s;\n" % json.dumps(digest))
        handle.write("window.COCKPIT_DATA = %s;\n" % json_text)
    return path


def assert_cockpit_honesty() -> bool:
    contract = system_contract()
    registry = project_registry()
    manifest = cockpit_manifest()
    checks = (
        validate_system_contract(contract),
        validate_project_registry(registry, contract),
        manifest["verified_geodetic_objects"] == 0,
        manifest["verified_sources"] == 0,
        manifest["giza_cosmos_claim"] is False,
        manifest["vector_42_is_physical_energy"] is False,
        manifest["astraea_auto_trade"] is False,
        adapter_summary(registry)["simulated_integrations"] == 0,
    )
    _require(all(checks), "cockpit honesty check failed")
    return True


__all__ = [name for name in dir() if not name.startswith("_")]
