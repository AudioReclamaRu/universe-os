"""PHASE B / STAGES F+G — spatial reconstruction and CONTROLLED idealization.

HARD RULES
----------
* Idealization is derived from measured points and is stored as a separate
  model record; the source records are never overwritten.
* Only structures justified by the sampled points are idealized: centroid,
  principal axes, plan hull, spacing, ellipsoidal envelope, trend plane.
* NO terrain mesh, NO monument surface, NO line connecting points by name or
  proximity.  Surfaces require confirmed surface points, compatible horizontal
  and vertical systems, adequate density and coverage — none of which is met.
* Feature-ID groups may form candidate boundary points, never a measured
  contour: the source contains only Point geometry.
* Every model carries the full contract from spatial_geometry.MODEL_RECORD_FIELDS.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import network_idealization as ni
import spatial_geometry as sg
import phase_b_observations as pbo

MODEL_SCHEMA = "phase_b_model_v1"

# Large campaigns have 4-5k stations.  Exact pairwise spacing is O(n^2) either
# way, but calling the general-kernel vector helpers 23M times is needlessly
# expensive.  This is the SAME arithmetic (sqrt of squared coordinate deltas)
# inlined; it removes only call overhead, never a term or a rounding step.
FAST_SPACING_THRESHOLD = 100


def _fast_spacing_statistics(points: Sequence[Tuple[float, float, float]]
                             ) -> Dict[str, Any]:
    count = len(points)
    pairwise: List[float] = []
    nearest: List[float] = []
    knn: List[float] = []
    limit = ni.K_NEAREST
    for i, px in enumerate(points):
        x0, y0, z0 = px
        distances: List[float] = []
        for j, qx in enumerate(points):
            if i == j:
                continue
            x1, y1, z1 = qx
            dx = x0 - x1
            dy = y0 - y1
            dz = z0 - z1
            value = math.sqrt(dx * dx + dy * dy + dz * dz)
            distances.append(value)
            if j > i:
                pairwise.append(value)
        distances.sort()
        _require(len(distances) >= limit,
                 "spacing needs at least %d points" % (limit + 1))
        nearest.append(distances[0])
        knn.append(sum(distances[:limit]) / limit)
    kmean = sum(knn) / len(knn)
    return {
        "pairwise_distance": ni.distance_summary(pairwise),
        "nearest_neighbor_distance": ni.distance_summary(nearest),
        "k_nearest_mean_distance": ni.distance_summary(knn),
        "k_nearest": limit,
        "spacing_density_index": 1.0 / kmean if kmean > 0.0 else None,
        "geometry_status": sg.DERIVED_GEOMETRY,
        "interpretation": "sampling density of control stations; NOT monument density",
        "computation_path": "inlined_exact_euclidean",
    }


def _spacing_statistics(points: Sequence[Tuple[float, float, float]]
                        ) -> Dict[str, Any]:
    if len(points) >= FAST_SPACING_THRESHOLD:
        return _fast_spacing_statistics(points)
    return ni.spacing_statistics(points)


class IdealizationError(ValueError):
    """Raised when idealization inputs or contract are invalid."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IdealizationError(message)


def _points(observations: Sequence[Dict[str, Any]]) -> Tuple[List[Tuple[float, float, float]], List[str]]:
    pts: List[Tuple[float, float, float]] = []
    ids: List[str] = []
    for record in observations:
        coords = record["normalized_coordinates"]
        if coords["elevation"] is None:
            continue  # unknown height => not a valid 3D input; kept as observation
        pts.append((coords["local_easting"], coords["local_northing"],
                    coords["elevation"]))
        ids.append(record["observation_id"])
    return pts, ids


def _model_record(model_id: str, model_type: str, ids: Sequence[str],
                  method: str, parameters: Dict[str, Any],
                  parameter_units: Dict[str, str], assumptions: List[str],
                  fit_residual: Dict[str, Any], uncertainty: Dict[str, Any],
                  validity_domain: str, limitations: List[str],
                  falsification: List[str]) -> Dict[str, Any]:
    record = {
        "model_id": model_id,
        "model_type": model_type,
        "source_ids": list(ids),
        "input_geometry_ids": list(ids),
        "method": method,
        "parameters": parameters,
        "parameter_units": parameter_units,
        "assumptions": assumptions,
        "fit_residual": fit_residual,
        "uncertainty": uncertainty,
        "validity_domain": validity_domain,
        "model_status": sg.IDEALIZED_MODEL,
        "limitations": limitations,
        "falsification_conditions": falsification,
        "schema_version": MODEL_SCHEMA,
        "source_values_unmodified": True,
        "not_terrain": True,
        "not_monument_geometry": True,
    }
    _require(sg.validate_model_record(record),
             "model record %s violates the contract" % model_id)
    return record


def idealize_campaign(campaign_id: str,
                      observations: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Build justified idealized models for a single campaign network."""
    pts, ids = _points(observations)
    _require(len(pts) >= 4,
             "%s has too few valid 3D points for idealization" % campaign_id)
    models: List[Dict[str, Any]] = []
    geometry: Dict[str, Any] = {}

    frame = ni.principal_axes(pts)
    spacing = _spacing_statistics(pts)
    hull = ni.plan_convex_hull(pts)
    centered = sg.center_points(pts)
    plane = sg.fit_plane_least_squares(centered["points"])
    geometry = {
        "point_count": len(pts),
        "centroid": frame["centroid"],
        "principal_axes": frame,
        "plan_convex_hull": hull,
        "spacing": spacing,
        "ellipsoidal_envelope": ni.ellipsoidal_envelope(pts, frame),
        "trend_plane": plane,
    }

    prefix = "IDEAL-B-%s" % campaign_id
    models.append(_model_record(
        "%s-FRAME-001" % prefix, "network_principal_axis_frame", ids,
        "deterministic Jacobi eigen-decomposition of the 3x3 covariance matrix",
        {"centroid": frame["centroid"], "axes": frame["axes"],
         "anisotropy_ratio": frame["anisotropy_ratio"]},
        {"centroid": "source xy/elevation units", "axes": "unitless direction",
         "anisotropy_ratio": "unitless"},
        ["sampled stations represent the network footprint",
         "no datum conversion was applied"],
        {"orthonormality_max_error": frame.get("orthonormality_max_error"),
         "degenerate": frame["degenerate"]},
        {"sampling_uncertainty": None},
        "the sampled stations of %s only" % campaign_id,
        ["directions are not measured structural axes",
         "no physical monument or terrain implied"],
        ["independent stations show a different anisotropy",
         "source coordinates are shown to be non-comparable"]))

    models.append(_model_record(
        "%s-HULL-001" % prefix, "plan_convex_envelope", ids,
        "monotone-chain convex hull in the local Easting/Northing plane",
        {"vertices": hull["vertices"], "vertex_count": hull["vertex_count"],
         "area": hull["area"], "perimeter": hull["perimeter"]},
        {"vertices": "source xy units", "area": "square source xy units",
         "perimeter": "source xy units", "vertex_count": "count"},
        ["plan projection onto the unverified local XY axes is meaningful for "
         "descriptive coverage"],
        {"degenerate": hull.get("degenerate", False)},
        {"sampling_uncertainty": None},
        "planar footprint of sampled %s stations" % campaign_id,
        ["interior of the hull is NOT surveyed surface",
         "vertices are sampled stations, not boundary of an object"],
        ["additional stations lie outside the hull",
         "the campaign is shown to use a different local origin"]))

    models.append(_model_record(
        "%s-SPACING-001" % prefix, "sampling_spacing_distribution", ids,
        "all pairwise distances plus nearest and k=5 nearest neighbour statistics",
        {"pairwise_distance_count": spacing["pairwise_distance"]["count"],
         "nearest_neighbor_median": spacing["nearest_neighbor_distance"]["median"],
         "k_nearest_mean": spacing["k_nearest_mean_distance"]["mean"]},
        {"pairwise_distance_count": "count",
         "nearest_neighbor_median": "source units",
         "k_nearest_mean": "source units"},
        ["Euclidean distance is used only inside one declared local grid"],
        {"min": spacing["pairwise_distance"]["min"],
         "max": spacing["pairwise_distance"]["max"]},
        {"sampling_uncertainty": None},
        "sampling density of %s stations" % campaign_id,
        ["not a density of archaeological objects",
         "does not describe terrain roughness"],
        ["an independent resurvey gives a different spacing distribution"]))

    envelope = geometry["ellipsoidal_envelope"]
    models.append(_model_record(
        "%s-ELLIPSOID-001" % prefix, "descriptive_ellipsoidal_envelope", ids,
        "principal-axis semi-lengths scaled by a declared factor of 2.0",
        {"scale": envelope["scale"],
         "outside_point_indices": envelope["outside_point_indices"],
         "points_outside": envelope["points_outside"]},
        {"scale": "unitless multiplier", "points_outside": "count",
         "outside_point_indices": "index (unitless)"},
        ["the ellipsoid is a description of the sample, not a confidence region"],
        {"outside_positive_residual": envelope["outside_positive_residual"]},
        {"coverage_probability": None},
        "descriptive envelope of %s stations" % campaign_id,
        ["factor 2.0 is a declared choice, not a fitted parameter",
         "points outside are reported as residuals, not deleted"],
        ["a different declared factor changes the envelope",
         "independent stations fall systematically outside"]))

    return {
        "campaign_id": campaign_id,
        "status": sg.IDEALIZED_MODEL,
        "scope": "CAMPAIGN_CONTROL_AND_FEATURE_NETWORK_ONLY",
        "geometry": geometry,
        "models": models,
        "model_ids": [model["model_id"] for model in models],
    }


def build_model_registry(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Idealize only campaigns with justified, self-contained 3D samples."""
    by_campaign: Dict[str, List[Dict[str, Any]]] = {}
    for record in observations:
        by_campaign.setdefault(record["campaign_id"], []).append(record)
    registries: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for campaign in sorted(by_campaign):
        if campaign == "PETRIE":
            skipped.append({
                "campaign_id": campaign,
                "reason": "no elevation: 3D idealization inputs are unavailable; "
                          "2D-only structures withheld until vertical datum is known",
                "status": sg.UNKNOWN,
            })
            continue
        registries.append(idealize_campaign(campaign, by_campaign[campaign]))
    all_models = [model for reg in registries for model in reg["models"]]
    model_ids = [model["model_id"] for model in all_models]
    _require(len(model_ids) == len(set(model_ids)), "duplicate idealization model_id")
    return {
        "report_id": "PHASE_B_MODEL_REGISTRY",
        "schema_version": MODEL_SCHEMA,
        "model_statuses": list(sg.MODEL_STATUSES),
        "model_count": len(all_models),
        "model_ids": model_ids,
        "campaigns": registries,
        "skipped_campaigns": skipped,
        "surfaces": {
            "terrain_mesh": None,
            "monument_surface": None,
            "status": sg.UNKNOWN,
            "reason": (
                "no confirmed surface points, no compatible vertical datum, "
                "no verified coverage density; plain-network points are not "
                "surface samples"),
            "required_before_surface": [
                "confirmed points measured on the target surface",
                "compatible horizontal and vertical reference systems",
                "adequate sampling density and coverage",
                "vertical uncertainty and cross-validation on withheld points",
            ],
        },
        "hypothetical_models": [],
        "boundary": {
            "idealized_is_not_measured": True,
            "envelope_interior_not_surveyed": True,
            "source_coordinates_unmodified": True,
            "lines_between_points": "not_constructed",
        },
        "models": all_models,
    }


if __name__ == "__main__":
    obs = pbo.build_observations()
    registry = build_model_registry(obs["observations"])
    print(json.dumps({
        "model_count": registry["model_count"],
        "skipped": registry["skipped_campaigns"],
        "surfaces": registry["surfaces"]["status"],
    }, indent=2, sort_keys=True))
