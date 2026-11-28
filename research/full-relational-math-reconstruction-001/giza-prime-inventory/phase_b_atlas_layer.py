"""PHASE B atlas layer — compact, validated projection of observation records.

HARD RULES
----------
* The atlas receives a *compact* copy: one campaign is displayed at a time.
  Showing two campaigns in one coordinate frame would imply CRS compatibility
  that was never verified.
* Every invariant is re-checked at load time.  A damaged or edited artifact
  aborts the atlas build instead of being silently displayed.
* Unknown elevation stays null.  KML Z is never substituted.
* Relation Skeleton (Layer 01) is untouched: this module only feeds Layer 03.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))

EXPECTED_COUNTS = {
    "GDFS-2012": 1539,
    "GDFS-2015": 1100,
    "GDFS-2016": 4746,
    "GDFS-2018": 4569,
    "GPMP": 41,
    "GIZA_CORNER": 15,
    "PETRIE": 68,
}
EXPECTED_TOTAL = 12078


class PhaseBAtlasError(ValueError):
    """Raised when a Phase B artifact violates the display contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PhaseBAtlasError(message)


def _load(name: str) -> Any:
    path = os.path.join(HERE, name)
    if not os.path.isfile(path):
        raise PhaseBAtlasError("required Phase B artifact absent: %s" % path)
    with open(path, "r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            raise PhaseBAtlasError("damaged artifact %s: %s" % (name, exc)) from exc


def _canonical_sha(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_campaign_snapshot() -> Dict[str, Any]:
    """Validate all Phase B artifacts and emit a compact layer payload."""
    observations = _load("phase_b_observations.json")
    catalog = _load("phase_b_source_catalog.json")
    crs = _load("phase_b_coordinate_system_registry.json")
    identity = _load("phase_b_entity_candidate_registry.json")
    relations = _load("phase_b_relation_candidates.json")
    models = _load("phase_b_model_registry.json")
    validation = _load("phase_b_validation_report.json")
    epistemic = _load("phase_b_epistemic_report.json")

    _require(observations["observation_count"] == EXPECTED_TOTAL,
             "observation count drift")
    _require(observations["campaign_counts"] == EXPECTED_COUNTS,
             "campaign count drift")
    _require(catalog["counts"]["observed_total"] == EXPECTED_TOTAL,
             "catalog count drift")
    _require(identity["totals"]["source_observations"] == EXPECTED_TOTAL,
             "identity layer lost observations")
    _require(identity["totals"]["identity_confirmed"] == 0,
             "unexpected confirmed identity")
    _require(models["surfaces"]["terrain_mesh"] is None,
             "terrain mesh must not exist")
    _require(models["surfaces"]["monument_surface"] is None,
             "monument surface must not exist")
    _require(relations["cross_campaign_geometric_relations"] == 0,
             "cross-campaign relation must not exist")
    _require(crs["transformations"]["performed"] == [],
             "coordinate transform must not exist")
    expected_checks = {
        "expected_total_matches": True,
        "all_expected_sets_parsed": True,
        "observation_ids_unique": True,
        "no_kml_z_promoted": True,
        "all_observations_preserved": True,
        "no_terrain_mesh": True,
        "no_monument_surface": True,
        "cross_campaign_transform_performed": False,
    }
    _require(validation["checks"] == expected_checks,
             "validation report drifted from the expected contract")
    _require(epistemic["states"]["SOURCE_PROVENANCE_VERIFIED"] is False,
             "provenance cannot be verified from these sources")

    records = observations["observations"]
    _require(len(records) == EXPECTED_TOTAL, "record list count drift")
    campaigns: Dict[str, Dict[str, Any]] = {}
    for record in records:
        cid = record["campaign_id"]
        _require(cid in EXPECTED_COUNTS, "unexpected campaign %s" % cid)
        entry = campaigns.setdefault(cid, {
            "campaign_id": cid,
            "year": record["campaign_year"],
            "source_file": record["source_file_id"],
            "source_sha256": record["source_provenance"]["source_sha256"],
            "network": record["source_provenance"]["network"],
            "crs": record["coordinate_system_id"],
            "vertical_reference": record["vertical_reference_id"],
            "semantic_role": record["semantic_type"]["value"],
            "geometry_role": record["geometry_role"],
            "coordinate_semantics": record["coordinate_system_id"],
            "status": record["validation_status"],
            "geometry": record["normalized_geometry_type"],
            "source_units": record["units"]["local_xy"],
            "points": [],
            "extent": None,
        })
        coords = record["normalized_coordinates"]
        x, y, z = (coords["local_easting"], coords["local_northing"],
                   coords["elevation"])
        _require(math.isfinite(x) and math.isfinite(y),
                 "non-finite plan coordinate in %s" % record["observation_id"])
        _require(z is None or math.isfinite(z),
                 "non-finite elevation in %s" % record["observation_id"])
        if cid == "PETRIE":
            _require(z is None, "Petrie elevation must stay UNKNOWN")
        else:
            _require(z is not None, "missing elevation in %s" % cid)
        _require(record["normalized_geometry_type"] == "Point",
                 "only Point geometry is permitted")
        _require(record["validation_status"] == "MEASURED_GEOMETRY",
                 "observation status must stay MEASURED_GEOMETRY")
        _require(record["normalized_coordinates"]["kml_z_is_elevation"] is False,
                 "KML Z must not be promoted")
        entry["points"].append([
            record["observation_id"], x, y, z,
            record["derived_links"].get("feature_id") or "",
        ])

    ordered: List[Dict[str, Any]] = []
    for cid in sorted(campaigns):
        entry = campaigns[cid]
        xs = [point[1] for point in entry["points"]]
        ys = [point[2] for point in entry["points"]]
        entry["extent"] = {
            "easting_min": min(xs), "easting_max": max(xs),
            "northing_min": min(ys), "northing_max": max(ys),
        }
        ordered.append(entry)

    model_summary = []
    for campaign in models["campaigns"]:
        model_summary.append({
            "campaign_id": campaign["campaign_id"],
            "model_ids": campaign["model_ids"],
            "status": campaign["status"],
            "scope": campaign["scope"],
        })

    payload = {
        "report_id": "PHASE_B_ATLAS_CAMPAIGN_LAYER",
        "schema_version": "phase_b_atlas_layer_v1",
        "observation_count": EXPECTED_TOTAL,
        "campaign_count": len(ordered),
        "campaigns": ordered,
        "campaign_order": [entry["campaign_id"] for entry in ordered],
        "coordinate_systems": {
            "registered": sorted(crs["systems"]),
            "separation": crs["separation"],
            "transformations_performed": crs["transformations"]["performed"],
            "datum_verified": crs["provenance_states"]["COORDINATE_SYSTEM_VERIFIED"],
        },
        "identity": identity["totals"],
        "relations": {
            "relation_count": relations["relation_count"],
            "categories": relations["categories_present"],
            "cross_campaign_geometric_relations": 0,
        },
        "models": {
            "model_count": models["model_count"],
            "campaigns": model_summary,
            "skipped": models["skipped_campaigns"],
            "surface_status": models["surfaces"]["status"],
        },
        "epistemic": {
            "source_provenance_verified": epistemic["states"][
                "SOURCE_PROVENANCE_VERIFIED"],
            "coordinate_system_verified": epistemic["states"][
                "COORDINATE_SYSTEM_VERIFIED"],
            "independently_corroborated": epistemic["states"][
                "INDEPENDENTLY_CORROBORATED"],
            "model_validated": epistemic["states"]["MODEL_VALIDATED"],
        },
        "display_contract": {
            "one_campaign_at_a_time": True,
            "no_cross_campaign_projection": True,
            "no_terrain_mesh": True,
            "no_monument_surface": True,
            "no_transform": True,
            "kml_z_is_elevation": False,
            "unknown_height_is_null": True,
            "relation_skeleton_untouched": True,
        },
    }
    payload["canonical_sha256"] = _canonical_sha(payload)
    return payload


if __name__ == "__main__":
    snapshot = build_campaign_snapshot()
    print(snapshot["observation_count"], snapshot["campaign_count"],
          snapshot["canonical_sha256"][:12])
