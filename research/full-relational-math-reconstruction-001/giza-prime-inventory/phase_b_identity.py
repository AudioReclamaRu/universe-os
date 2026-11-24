"""PHASE B / STAGE D — deduplication WITHOUT deleting or merging observations.

HARD RULES
----------
* Identity is a separate layer.  All 12,078 observations survive unchanged.
* Name / ID matches are candidates, never proof.
* Euclidean distance is used ONLY as a candidate generator, never as proof of
  physical identity, because datum/CRS compatibility is unverified.
* Documented reshoot notes and documented Feature IDs are recorded as separate
  relation kinds with their own evidence and status.
* Statuses: IDENTITY_CONFIRMED, IDENTITY_PROBABLE, MATCH_CANDIDATE,
  REMEASUREMENT_CANDIDATE, UNRESOLVED, DISTINCT.
"""

from __future__ import annotations

import itertools
import json
from typing import Any, Dict, List, Optional, Tuple

import phase_b_observations as pbo

COORD_TOLERANCE = 0.001  # source precision is 0.001 in local units
FEATURE_KEY = "feature_id"


class IdentityError(ValueError):
    """Raised when the identity layer violates its own contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IdentityError(message)


def _local_key(record: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    coords = record["normalized_coordinates"]
    return (round(coords["local_northing"], 3),
            round(coords["local_easting"], 3))


def _same_name(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    name_a = str(a["original_name"] or "").strip().lower()
    name_b = str(b["original_name"] or "").strip().lower()
    return bool(name_a) and name_a == name_b


def build_identity(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate candidates; confirm nothing automatically."""
    by_coord: Dict[Tuple[float, float], List[Dict[str, Any]]] = {}
    by_name: Dict[str, List[Dict[str, Any]]] = {}
    by_feature: Dict[str, List[Dict[str, Any]]] = {}
    for record in observations:
        key = _local_key(record)
        if key is not None:
            by_coord.setdefault(key, []).append(record)
        name = str(record["original_name"] or "").strip().lower()
        if name:
            by_name.setdefault(name, []).append(record)
        fid = record["derived_links"].get("feature_id")
        if fid:
            by_feature.setdefault(fid, []).append(record)

    groups: List[Dict[str, Any]] = []
    group_counter = 0

    def add_group(kind: str, records: List[Dict[str, Any]], evidence: str,
                  status: str, confidence: str, notes: List[str]) -> None:
        nonlocal group_counter
        if len(records) < 2:
            return
        group_counter += 1
        campaigns = sorted({r["campaign_id"] for r in records})
        groups.append({
            "entity_candidate_id": "EC:%05d" % group_counter,
            "candidate_kind": kind,
            "status": status,
            "confidence": confidence,
            "evidence": evidence,
            "observation_ids": [r["observation_id"] for r in records],
            "campaigns": campaigns,
            "cross_campaign": len(campaigns) > 1,
            "notes": notes,
            "original_records_preserved": True,
            "physical_identity_asserted": status == "IDENTITY_CONFIRMED",
        })

    # 1. Same-name candidates (never proof).
    for name, records in sorted(by_name.items()):
        if len(records) > 1:
            cross = len({r["campaign_id"] for r in records}) > 1
            add_group("SAME_NAME", records, "original_name=%s" % name,
                      "MATCH_CANDIDATE" if cross else "UNRESOLVED",
                      "LOW", [
                          "name equality is a hypothesis only",
                          "no datum compatibility check performed",
                      ])

    # 2. Coordinate coincidence candidates (candidate generator only).
    for key, records in sorted(by_coord.items()):
        if len(records) > 1:
            campaigns = {r["campaign_id"] for r in records}
            cross = len(campaigns) > 1
            doc = all(r["source_provenance"]["provenance_states"][
                          "COORDINATE_SYSTEM_VERIFIED"] is False
                      for r in records)
            add_group("COORDINATE_COINCIDENCE", records,
                      "local(N,E) rounded to 0.001 = %s" % (key,),
                      "MATCH_CANDIDATE" if not cross else "REMEASUREMENT_CANDIDATE",
                      "LOW" if doc else "MEDIUM", [
                          "coordinate coincidence does not prove physical identity",
                          "CRS compatibility unverified; no transform applied",
                          "cross-campaign match is a remeasurement candidate only",
                      ])

    # 3. Documented Feature ID grouping (an actual source relation).
    for fid, records in sorted(by_feature.items()):
        if len(records) > 1:
            add_group("DOCUMENTED_FEATURE_ID", records, "Feature:%s in description" % fid,
                      "IDENTITY_PROBABLE", "MEDIUM", [
                          "feature grouping is documented in the source",
                          "one feature may contain many distinct sample points",
                          "grouping is not a single physical marker",
                      ])

    # 4. Documented reshoot notes (explicit remeasurement relation).
    reshoots: List[Dict[str, Any]] = []
    for record in observations:
        ts = record["derived_links"].get("reshoot_total_station_range")
        if ts:
            reshoots.append({
                "observation_id": record["observation_id"],
                "campaign_id": record["campaign_id"],
                "total_station_range": ts,
                "status": "REMEASUREMENT_CANDIDATE",
                "evidence": "source description: 'reshoot it with TS # ...'",
                "independent_corroboration": False,
            })

    confirmed = sum(1 for group in groups
                    if group["status"] == "IDENTITY_CONFIRMED")
    totals = {
        "source_observations": len(observations),
        "entity_candidates": len(groups),
        "identity_confirmed": confirmed,
        "confirmed_unique_stations": None if confirmed == 0 else confirmed,
        "remeasurement_candidates": sum(
            1 for g in groups if g["status"] == "REMEASUREMENT_CANDIDATE"),
        "match_candidates": sum(
            1 for g in groups if g["status"] == "MATCH_CANDIDATE"),
        "identity_probable": sum(
            1 for g in groups if g["status"] == "IDENTITY_PROBABLE"),
        "unresolved": sum(1 for g in groups if g["status"] == "UNRESOLVED"),
        "distinct": len(observations) - sum(len(g["observation_ids"]) for g in groups),
        "documented_reshoot_notes": len(reshoots),
        "original_observations_removed": 0,
    }
    _require(totals["source_observations"] == 12078,
             "identity layer lost observations")
    return {
        "report_id": "PHASE_B_ENTITY_CANDIDATE_REGISTRY",
        "schema_version": "phase_b_identity_v1",
        "statuses": ["IDENTITY_CONFIRMED", "IDENTITY_PROBABLE", "MATCH_CANDIDATE",
                     "REMEASUREMENT_CANDIDATE", "UNRESOLVED", "DISTINCT"],
        "method": {
            "name_matching": "candidate generator only",
            "coordinate_matching": "rounded local N/E 0.001; candidate generator only",
            "crs_compatibility": "unverified; Euclidean distance NOT used as proof",
            "feature_ids": "documented source relation, not physical identity",
        },
        "totals": totals,
        "entity_candidates": groups,
        "documented_reshoots": reshoots,
        "limitations": [
            "no source was independently corroborated",
            "no datum or coordinate-system compatibility was verified",
            "identity confirmation requires external provenance not available here",
        ],
    }


if __name__ == "__main__":
    obs = pbo.build_observations()
    ident = build_identity(obs["observations"])
    print(json.dumps(ident["totals"], indent=2, sort_keys=True))
