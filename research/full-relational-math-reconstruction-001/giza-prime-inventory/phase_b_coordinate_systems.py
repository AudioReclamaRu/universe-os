"""PHASE B / STAGE E — coordinate system registry.

HARD RULES
----------
* Every campaign is registered separately.  Similar numeric ranges are NOT
  proof that two campaigns share a mathematical system.
* datum is never promoted without documentation.  All datums here remain
  unverified.
* Vertical reference is a separate axis and is unknown for Petrie stations.
* No Helmert / similarity / affine transform is performed: there is no verified
  set of common control points with documented compatibility.
* GPMP and ARCE Sphinx Grid remain separate systems.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import phase_b_observations as pbo

SYSTEMS: Dict[str, Dict[str, Any]] = {
    "LOCAL_GRID_UNVERIFIED": {
        "system_name": "Dash Foundation local Easting/Northing grid",
        "documentation": "campaign KML descriptions only; no CRS document in archive",
        "coordinate_type": "local projected-like planar grid",
        "axis_order": "X=Easting, Y=Northing, Z=description Elevation",
        "units": "source units (metres claimed by publication, unverified)",
        "datum": "unverified",
        "ellipsoid": "unknown / not declared",
        "projection": "unknown / not declared",
        "local_origin": "unknown",
        "orientation": "unknown",
        "vertical_system": "description Elevation; reference unknown",
        "epoch": None,
        "known_transformations": [],
        "confirmation_status": "DOCUMENTED_IN_DESCRIPTION_ONLY",
        "campaigns": ["GDFS-2012", "GDFS-2015", "GDFS-2016", "GDFS-2018",
                      "GIZA_CORNER"],
    },
    "GPMP_CONTROL_GRID": {
        "system_name": "GPMP Control Monuments local Northing/Easting",
        "documentation": "GPMP source description; existing Phase A layer",
        "coordinate_type": "geodetic control network local grid",
        "axis_order": "X=Easting, Y=Northing, Z=description Elevation",
        "units": "source units (metres claimed, unverified)",
        "datum": "unverified",
        "ellipsoid": "unknown",
        "projection": "unknown",
        "local_origin": "unknown",
        "orientation": "unknown",
        "vertical_system": "description Elevation; reference unknown",
        "epoch": None,
        "known_transformations": [],
        "confirmation_status": "DOCUMENTED_IN_DESCRIPTION_ONLY",
        "campaigns": ["GPMP"],
    },
    "PETRIE_LOCAL_GRID_UNRESOLVED": {
        "system_name": "Petrie N-S / E-W historical station grid",
        "documentation": "Petrie Stations source description",
        "coordinate_type": "historical local station grid",
        "axis_order": "N-S, E-W as printed in source; GPMP pair given separately",
        "units": "source units (unverified)",
        "datum": "unverified",
        "ellipsoid": "unknown",
        "projection": "unknown",
        "local_origin": "unknown",
        "orientation": "unknown",
        "vertical_system": "UNKNOWN — no elevation in source",
        "epoch": None,
        "known_transformations": [],
        "confirmation_status": "UNRESOLVED_HISTORICAL_GRID",
        "campaigns": ["PETRIE"],
    },
    "KML_GEOGRAPHIC_PAIR": {
        "system_name": "KML coordinates[0][0:2] geographic pair",
        "documentation": "KML coordinate tuple in every source KMZ",
        "coordinate_type": "geographic longitude/latitude",
        "axis_order": "[longitude, latitude, Z]",
        "units": "decimal degrees",
        "datum": "unverified",
        "ellipsoid": "unknown",
        "projection": "not applicable",
        "local_origin": "not applicable",
        "orientation": "not applicable",
        "vertical_system": "KML Z is NOT elevation (all observed Z = 0.0)",
        "epoch": None,
        "known_transformations": [],
        "confirmation_status": "AXIS_ORDER_OBSERVED_DATUM_UNVERIFIED",
        "campaigns": ["GDFS-2012", "GDFS-2015", "GDFS-2016", "GDFS-2018",
                      "GPMP", "GIZA_CORNER", "PETRIE"],
    },
    "ARCE_Sphinx_GRID_SEPARATE": {
        "system_name": "ARCE Sphinx Grid (SRI 1978 historical methodology)",
        "documentation": "archival methodological description; NOT present as coordinates here",
        "coordinate_type": "local archaeological grid",
        "axis_order": "historical SRI 1978 axes",
        "units": "unverified",
        "datum": "unverified",
        "ellipsoid": "unknown",
        "projection": "unknown",
        "local_origin": "described historically as a point near the front paws of the Sphinx",
        "orientation": "described historically as related to magnetic north",
        "vertical_system": "historical transfer procedure described; not recomputed",
        "epoch": None,
        "known_transformations": [],
        "confirmation_status": "HISTORICAL_DESCRIPTION_ONLY_NO_TRANSFORM",
        "campaigns": [],
    },
}


def build_registry(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Register systems and count observed coordinate anomalies."""
    swapped = 0
    elevation_absent = 0
    kml_z_nonzero = 0
    for record in observations:
        warnings = record["warnings"]
        swapped += int(any(w.startswith("SWAPPED_LONGITUDE_LABEL") for w in warnings))
        elevation_absent += int(any(w.startswith("ELEVATION_ABSENT") for w in warnings))
        kml_z_nonzero += int(any(w.startswith("KML_Z_NONZERO") for w in warnings))
    registry: Dict[str, Any] = {}
    for key, value in SYSTEMS.items():
        entry = dict(value)
        entry["common_control_points"] = 0
        entry["transform_to_other_system"] = "not_performed"
        registry[key] = entry
    return {
        "report_id": "PHASE_B_COORDINATE_SYSTEM_REGISTRY",
        "schema_version": "phase_b_crs_v1",
        "systems": registry,
        "separation": {
            "gpmp_vs_arce_sphinx_grid": "separate",
            "gpmp_to_arce_transform": "not_performed",
            "gdfs_2012_vs_2015_vs_2016_vs_2018": (
                "separately registered; numeric-range similarity is not proof "
                "of a shared mathematical system"),
            "local_grid_vs_geographic_pair": "relation_unresolved",
            "petrie_historical_vs_local_grid": "relation_unresolved",
        },
        "transformations": {
            "performed": [],
            "reason": (
                "no verified common control points with documented coordinate "
                "compatibility; 2D/3D similarity, Helmert and affine fits are "
                "withheld to avoid fabricating a datum relationship"),
            "required_for_future_transform": [
                "documented common control points in both systems",
                "declared units and datum for each system",
                "residual analysis on withheld control points",
                "explicit vertical transformation if heights are involved",
            ],
        },
        "observed_anomalies": {
            "swapped_longitude_label_records": swapped,
            "elevation_absent_records": elevation_absent,
            "kml_z_nonzero_records": kml_z_nonzero,
        },
        "provenance_states": {
            "COORDINATE_SYSTEM_DOCUMENTED": True,
            "COORDINATE_SYSTEM_VERIFIED": False,
            "VERTICAL_REFERENCE_DOCUMENTED": True,
            "VERTICAL_REFERENCE_VERIFIED": False,
        },
    }


if __name__ == "__main__":
    obs = pbo.build_observations()
    data = build_registry(obs["observations"])
    print(json.dumps(data["observed_anomalies"], indent=2, sort_keys=True))
