"""PHASE B / STAGE H — geometric relation system with explicit categories.

HARD RULES
----------
* A numerical coincidence is never promoted to a physical mechanism.
* Each candidate carries formula, units, dimensions, inputs, method, residual,
  sensitivity, alternative explanation, independent check and falsifier.
* No frequency / acoustic / hydraulic / electromagnetic claim is made.  The
  directives of section 20 remain binding.
* Relations are computed only inside a declared local grid; cross-campaign
  Euclidean comparison is withheld while CRS compatibility is unverified.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import phase_b_observations as pbo

CATEGORY = {
    "EXACT_IDENTITY", "MEASURED_CORRESPONDENCE", "NUMERICAL_APPROXIMATION",
    "STATISTICAL_PATTERN", "IDEALIZED_INVARIANT", "HYPOTHESIS",
    "COINCIDENCE_CANDIDATE", "REJECTED",
}


class RelationError(ValueError):
    """Raised when a relation record violates the contract."""


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise RelationError(msg)


def _make_relation(relation_id: str, category: str, kind: str,
                   inputs: List[str], formula: str, units: str,
                   dimensions: str, value: Dict[str, Any],
                   residual: Optional[Dict[str, Any]],
                   sensitivity: str, alternative: str,
                   independent_check: str, falsifier: str,
                   status: str) -> Dict[str, Any]:
    _require(category in CATEGORY, "unknown relation category %s" % category)
    record = {
        "relation_id": relation_id,
        "relation_category": category,
        "relation_kind": kind,
        "input_observation_ids": inputs,
        "formula": formula,
        "units": units,
        "dimensions": dimensions,
        "value": value,
        "residual": residual,
        "sensitivity": sensitivity,
        "alternative_explanation": alternative,
        "independent_check": independent_check,
        "falsification_condition": falsifier,
        "status": status,
        "physical_mechanism_claimed": False,
    }
    return record


def build_relations(observations: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute documented and derived relations inside compatible grids only."""
    relations: List[Dict[str, Any]] = []
    by_campaign: Dict[str, List[Dict[str, Any]]] = {}
    for record in observations:
        by_campaign.setdefault(record["campaign_id"], []).append(record)

    # Documented Feature-ID relations are correspondences in the source, not
    # physical mechanisms and not measured contours.
    by_feature: Dict[str, List[Dict[str, Any]]] = {}
    for record in observations:
        fid = record["derived_links"].get("feature_id")
        if fid:
            by_feature.setdefault(fid, []).append(record)
    for fid, records in sorted(by_feature.items())[:400]:
        if len(records) < 2:
            continue
        coords = [
            (r["normalized_coordinates"]["local_easting"],
             r["normalized_coordinates"]["local_northing"])
            for r in records if r["normalized_coordinates"]["elevation"] is not None]
        if len(coords) < 2:
            continue
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        span = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
        relations.append(_make_relation(
            "REL-FEATURE-%s" % fid, "MEASURED_CORRESPONDENCE",
            "documented_feature_grouping",
            [r["observation_id"] for r in records],
            "group members share Feature:%s in the source description" % fid,
            "source xy units", "count / length",
            {"member_count": len(records), "plan_span": span},
            None,
            "span depends on the single unverified local grid",
            "feature label may be a cataloguing class, not one physical object",
            "re-read the original KMZ description for this feature",
            "independent survey shows members belong to different features",
            "DERIVED_FROM_SOURCE"))

    # Documented reshoots are remeasurement candidates only.
    for record in observations:
        ts = record["derived_links"].get("reshoot_total_station_range")
        if not ts:
            continue
        relations.append(_make_relation(
            "REL-RESHOOT-%s" % record["observation_id"].replace(":", "-"),
            "HYPOTHESIS", "documented_remeasurement_note",
            [record["observation_id"]],
            "source note: 'reshoot it with TS # %s'" % ts,
            "station range (unitless)", "count",
            {"total_station_range": ts}, None,
            "station range is a label; no measured coordinates for those stations",
            "note may refer to a separate campaign not present in these files",
            "read the original KMZ description",
            "the referenced stations are shown to be a different physical set",
            "CANDIDATE_ONLY"))

    # Within-campaign nearest-neighbour statistics: descriptive, not functional.
    for campaign, records in sorted(by_campaign.items()):
        pts = [(r["normalized_coordinates"]["local_easting"],
                r["normalized_coordinates"]["local_northing"])
               for r in records]
        if len(pts) < 2:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        relations.append(_make_relation(
            "REL-EXTENT-%s" % campaign, "STATISTICAL_PATTERN",
            "within_campaign_plan_extent",
            [r["observation_id"] for r in records[:5]],
            "axis-aligned extents of sampled stations in the declared local grid",
            "source xy units", "length",
            {"easting_min": min(xs), "easting_max": max(xs),
             "northing_min": min(ys), "northing_max": max(ys),
             "sample_count": len(pts)},
            None,
            "extents depend on campaign coverage, not on monument boundaries",
            "coverage may reflect survey logistics rather than site structure",
            "compare against the original KMZ point cloud",
            "a new station extends the observed envelope",
            "DESCRIPTIVE_ONLY"))

    categories = {r["relation_category"] for r in relations}
    _require(categories.issubset(CATEGORY), "invalid relation category emitted")
    return {
        "report_id": "PHASE_B_RELATION_CANDIDATES",
        "schema_version": "phase_b_relations_v1",
        "category_contract": sorted(CATEGORY),
        "relation_count": len(relations),
        "categories_present": sorted(categories),
        "cross_campaign_geometric_relations": 0,
        "cross_campaign_reason": (
            "no verified coordinate-system compatibility; Euclidean distance "
            "across campaigns is withheld as proof of any physical relation"),
        "physical_hypotheses": {
            "acoustic": None, "hydraulic": None, "electromagnetic": None,
            "frequency_assignment": None,
            "reason": "section 20: geometry, materials and boundary conditions "
                      "are not yet established",
        },
        "relations": relations,
    }


if __name__ == "__main__":
    obs = pbo.build_observations()
    data = build_relations(obs["observations"])
    print(json.dumps({
        "relation_count": data["relation_count"],
        "categories_present": data["categories_present"],
    }, indent=2, sort_keys=True))
