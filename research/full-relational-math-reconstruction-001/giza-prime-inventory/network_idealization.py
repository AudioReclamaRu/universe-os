"""Idealized geometry of the GPMP *control network*, not of the landscape.

SCOPE
-----
This module idealizes the surveyed control stations themselves: their centre,
principal axes, plan-view convex envelope, spacing and the residuals between a
declared ellipsoidal envelope and the measured points.  It never produces a
terrain mesh, a monument surface, a datum transform or a connection between
control stations asserted as a measurement.

Every returned geometry is a NEW derived record.  The source coordinates are
never overwritten.  Each idealized construct is filed as an IDEALIZED_MODEL
record with the full research contract (method, parameters, units, assumptions,
residual, uncertainty, validity domain, limitations, falsification conditions).

No external libraries are used.  The eigendecomposition is a deterministic
Jacobi rotation on a symmetric 3x3 covariance matrix; the plan-view hull uses
the monotone-chain algorithm with exact double comparisons.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import spatial_geometry as sg

Vector = Tuple[float, float, float]

NETWORK_ID = "GPMP-CONTROL-NETWORK-41"
SOURCE_GEOMETRY_IDS = (
    NETWORK_ID,
    "GPMP-CENTERED-POINTS",
    "GPMP-LEAST-SQUARES-PLANE",
)
ELLIPSOID_SCALE = 2.0
K_NEAREST = 5
EIGEN_TOLERANCE = 1e-13
MAX_SWEEPS = 100


class IdealizationValidationError(ValueError):
    """Raised for degenerate or contract-violating network idealization input."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IdealizationValidationError(message)


def _points3(points: Sequence[Sequence[float]]) -> List[Vector]:
    _require(len(points) >= 3, "network idealization needs at least three points")
    return [sg.require_vector(p, "network point") for p in points]


def centroid(points: Sequence[Sequence[float]]) -> Vector:
    """Arithmetic centre of the sampled control stations."""
    pts = _points3(points)
    return tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))  # type: ignore[return-value]


def covariance_matrix(points: Sequence[Sequence[float]],
                      centre: Optional[Sequence[float]] = None) -> Tuple[
                          Tuple[float, float, float], ...]:
    """Population covariance (divide by n) about an explicit centre."""
    pts = _points3(points)
    c = sg.require_vector(centre, "centre") if centre is not None else centroid(pts)
    values = [[0.0] * 3 for _ in range(3)]
    for p in pts:
        d = sg.vec_sub(p, c)
        for i in range(3):
            for j in range(3):
                values[i][j] += d[i] * d[j]
    n = float(len(pts))
    return tuple(tuple(v / n for v in row) for row in values)  # type: ignore[return-value]


def principal_axes(points: Sequence[Sequence[float]]) -> Dict[str, Any]:
    """Deterministic Jacobi eigendecomposition of the covariance matrix.

    Eigenvectors are unit length and mutually orthogonal.  A degenerate
    (coincident or collinear) sample is reported, never given a confident
    anisotropy value.
    """
    pts = _points3(points)
    c = centroid(pts)
    matrix = covariance_matrix(pts, c)
    a = [list(row) for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]

    converged = False
    for _ in range(MAX_SWEEPS):
        off = max(abs(a[p][q]) for p in range(3) for q in range(p + 1, 3))
        if off <= EIGEN_TOLERANCE:
            converged = True
            break
        for p in range(3):
            for q in range(p + 1, 3):
                apq = a[p][q]
                if abs(apq) <= EIGEN_TOLERANCE:
                    continue
                tau = (a[q][q] - a[p][p]) / (2.0 * apq)
                sign = 1.0 if tau >= 0.0 else -1.0
                t = sign / (abs(tau) + math.sqrt(1.0 + tau * tau))
                co = 1.0 / math.sqrt(1.0 + t * t)
                si = t * co
                for k in range(3):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = co * akp - si * akq, si * akp + co * akq
                for k in range(3):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = co * apk - si * aqk, si * apk + co * aqk
                for k in range(3):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p], v[k][q] = co * vkp - si * vkq, si * vkp + co * vkq
    _require(converged, "Jacobi eigendecomposition did not converge")

    pairs = []
    for i in range(3):
        axis = tuple(v[k][i] for k in range(3))
        # Fix the sign so repeated builds report the same oriented frame.
        pivot = max(range(3), key=lambda k: abs(axis[k]))
        if axis[pivot] < 0.0:
            axis = tuple(-x for x in axis)
        pairs.append((max(0.0, a[i][i]), axis))
    pairs.sort(key=lambda item: (-item[0], item[1]))

    axes = []
    for index, (value, axis) in enumerate(pairs, start=1):
        axes.append({
            "axis_id": "PC%d" % index,
            "vector": list(axis),
            "eigenvalue": value,
            "sqrt_eigenvalue": math.sqrt(value),
        })
    total = sum(item["eigenvalue"] for item in axes)
    for item in axes:
        item["explained_variance_ratio"] = (
            item["eigenvalue"] / total if total > 0.0 else None
        )
    basis = tuple(tuple(item["vector"]) for item in axes)
    orthogonal = sg.is_orthogonal(basis, tolerance=1e-8)
    degenerate = total <= 1e-12 or not orthogonal
    smallest = axes[-1]["eigenvalue"]
    return {
        "centroid": list(c),
        "axes": axes,
        "total_variance": total,
        "anisotropy_ratio": (
            axes[0]["eigenvalue"] / smallest if smallest > 1e-12 else None
        ),
        "orthonormal_basis": orthogonal,
        "degenerate": degenerate,
        "geometry_status": sg.DERIVED_GEOMETRY,
        "interpretation": "descriptive frame of sampled control stations; NOT terrain",
    }


def _cross2(o: Tuple[float, float], a: Tuple[float, float],
            b: Tuple[float, float]) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def plan_convex_hull(points: Sequence[Sequence[float]]) -> Dict[str, Any]:
    """Monotone-chain hull of the Easting/Northing footprint.

    Hull vertices are actual measured stations.  The polygon is a boundary of
    the sampled footprint only; the interior is not surveyed and is not a
    surface.
    """
    pts = _points3(points)
    by_plan: Dict[Tuple[float, float], Vector] = {}
    for p in pts:
        key = (p[0], p[1])
        if key not in by_plan:
            by_plan[key] = p
    plan = sorted(by_plan)
    _require(len(plan) >= 3, "plan hull needs three distinct plan positions")

    lower: List[Tuple[float, float]] = []
    for p in plan:
        while len(lower) >= 2 and _cross2(lower[-2], lower[-1], p) <= 0.0:
            lower.pop()
        lower.append(p)
    upper: List[Tuple[float, float]] = []
    for p in reversed(plan):
        while len(upper) >= 2 and _cross2(upper[-2], upper[-1], p) <= 0.0:
            upper.pop()
        upper.append(p)
    ring = lower[:-1] + upper[:-1]
    _require(len(ring) >= 3, "degenerate plan hull")

    vertices = [list(by_plan[(x, y)]) for x, y in ring]
    twice_area = 0.0
    perimeter = 0.0
    for i, vertex in enumerate(vertices):
        nxt = vertices[(i + 1) % len(vertices)]
        twice_area += vertex[0] * nxt[1] - nxt[0] * vertex[1]
        perimeter += math.hypot(nxt[0] - vertex[0], nxt[1] - vertex[1])
    elevations = [v[2] for v in vertices]
    return {
        "vertices": vertices,
        "vertex_count": len(vertices),
        "area": abs(twice_area) / 2.0,
        "perimeter": perimeter,
        "vertex_elevation_min": min(elevations),
        "vertex_elevation_max": max(elevations),
        "coordinate_plane": "X=Easting, Y=Northing",
        "geometry_status": sg.DERIVED_GEOMETRY,
        "interpretation": "boundary of sampled plan footprint; interior NOT surveyed",
    }


def distance_summary(values: Sequence[float]) -> Dict[str, float]:
    vals = [float(v) for v in values]
    _require(bool(vals), "distance summary needs at least one value")
    _require(all(math.isfinite(v) and v >= 0.0 for v in vals),
             "distance must be finite and non-negative")
    ordered = sorted(vals)
    mid = len(ordered) // 2
    median = (ordered[mid] if len(ordered) % 2
              else (ordered[mid - 1] + ordered[mid]) / 2.0)
    return {
        "count": len(vals),
        "min": ordered[0],
        "max": ordered[-1],
        "mean": sum(vals) / len(vals),
        "median": median,
        "rms": math.sqrt(sum(v * v for v in vals) / len(vals)),
    }


def spacing_statistics(points: Sequence[Sequence[float]]) -> Dict[str, Any]:
    """Pairwise, nearest-neighbour and k-nearest spacing of the sample."""
    pts = _points3(points)
    pairwise: List[float] = []
    nearest: List[float] = []
    knn: List[float] = []
    for i, p in enumerate(pts):
        distances = []
        for j, q in enumerate(pts):
            if i == j:
                continue
            value = sg.distance(p, q)
            distances.append(value)
            if j > i:
                pairwise.append(value)
        distances.sort()
        _require(len(distances) >= K_NEAREST,
                 "spacing needs at least %d points" % (K_NEAREST + 1))
        nearest.append(distances[0])
        knn.append(sum(distances[:K_NEAREST]) / K_NEAREST)
    kmean = sum(knn) / len(knn)
    return {
        "pairwise_distance": distance_summary(pairwise),
        "nearest_neighbor_distance": distance_summary(nearest),
        "k_nearest_mean_distance": distance_summary(knn),
        "k_nearest": K_NEAREST,
        "spacing_density_index": 1.0 / kmean if kmean > 0.0 else None,
        "geometry_status": sg.DERIVED_GEOMETRY,
        "interpretation": "sampling density of control stations; NOT monument density",
    }


def ellipsoidal_envelope(points: Sequence[Sequence[float]],
                         frame: Dict[str, Any],
                         scale: float = ELLIPSOID_SCALE) -> Dict[str, Any]:
    """Declared ellipsoid around the centroid, with honest outside-point residuals."""
    pts = _points3(points)
    _require(scale > 0.0, "ellipsoid scale must be positive")
    centre = tuple(frame["centroid"])
    axes = frame["axes"]
    semi_axes = [scale * math.sqrt(max(0.0, float(axis["eigenvalue"])))
                 for axis in axes]
    radial: List[float] = []
    positive: List[float] = []
    outside_ids: List[int] = []
    for index, p in enumerate(pts):
        offset = sg.vec_sub(p, centre)
        total = 0.0
        usable = True
        for axis, semi in zip(axes, semi_axes):
            projection = sg.dot(offset, axis["vector"])
            if semi <= 1e-12:
                if abs(projection) > 1e-12:
                    usable = False
                continue
            ratio = projection / semi
            total += ratio * ratio
        value = math.sqrt(total) if usable else float("inf")
        _require(math.isfinite(value), "degenerate ellipsoid has no finite residual")
        radial.append(value)
        if value > 1.0:
            outside_ids.append(index)
            positive.append(value - 1.0)
    return {
        "scale": scale,
        "semi_axes": semi_axes,
        "normalized_radial_distance": distance_summary(radial),
        "points_outside": len(outside_ids),
        "outside_point_indices": outside_ids,
        "outside_positive_residual": (
            distance_summary(positive) if positive else
            {"count": 0, "min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0, "rms": 0.0}
        ),
        "geometry_status": sg.DERIVED_GEOMETRY,
        "interpretation": "descriptive envelope of sampled stations; NOT a terrain surface "
                          "and NOT a statistical confidence region",
    }


def _units_for_axes(prefix: str) -> Dict[str, str]:
    units: Dict[str, str] = {"anisotropy_ratio": "dimensionless"}
    for index in range(1, 4):
        for component in ("x", "y", "z"):
            units["%s%d_%s" % (prefix, index, component)] = "dimensionless"
        units["%s%d_eigenvalue" % (prefix, index)] = "source units squared"
    return units


def _build_model_records(ids: Sequence[str], frame: Dict[str, Any],
                         hull: Dict[str, Any], spacing: Dict[str, Any],
                         envelope: Dict[str, Any]) -> List[Dict[str, Any]]:
    axes = frame["axes"]
    frame_params: Dict[str, float] = {}
    for index, axis in enumerate(axes, start=1):
        for component, value in zip("xyz", axis["vector"]):
            frame_params["pc%d_%s" % (index, component)] = float(value)
        frame_params["pc%d_eigenvalue" % index] = float(axis["eigenvalue"])
    frame_params["anisotropy_ratio"] = float(frame["anisotropy_ratio"] or 0.0)

    hull_params = {
        "vertex_count": float(hull["vertex_count"]),
        "area": float(hull["area"]),
        "perimeter": float(hull["perimeter"]),
        "vertex_elevation_min": float(hull["vertex_elevation_min"]),
        "vertex_elevation_max": float(hull["vertex_elevation_max"]),
    }
    envelope_params = {
        "scale": float(envelope["scale"]),
        "semi_axis_1": float(envelope["semi_axes"][0]),
        "semi_axis_2": float(envelope["semi_axes"][1]),
        "semi_axis_3": float(envelope["semi_axes"][2]),
        "points_outside": float(envelope["points_outside"]),
    }
    spacing_params = {
        "pairwise_count": float(spacing["pairwise_distance"]["count"]),
        "nearest_median": float(spacing["nearest_neighbor_distance"]["median"]),
        "k_nearest_mean": float(spacing["k_nearest_mean_distance"]["mean"]),
        "density_index": float(spacing["spacing_density_index"] or 0.0),
    }
    source_units = "source units (metres claimed by publication; unverified here)"

    records = [
        sg.make_model_record(
            model_id="IDEAL-GPMP-NETWORK-FRAME-001",
            model_type="principal_axis_network_frame",
            source_ids=list(ids),
            input_geometry_ids=list(SOURCE_GEOMETRY_IDS),
            method="Jacobi eigendecomposition of the population covariance matrix",
            parameters=frame_params,
            parameter_units=_units_for_axes("pc"),
            assumptions=[
                "the 41 stations are one sampled network, not one population of terrain points",
                "source units are used without datum conversion",
                "the frame is descriptive of the sample only",
            ],
            fit_residual={
                "orthonormal_basis": frame["orthonormal_basis"],
                "total_variance": frame["total_variance"],
            },
            uncertainty={
                "degenerate_sample": frame["degenerate"],
                "explained_variance_ratio": [
                    a["explained_variance_ratio"] for a in axes],
            },
            validity_domain="sampled GPMP control network only",
            model_status=sg.IDEALIZED_MODEL,
            limitations=[
                "no terrain, monument or surface geometry is implied",
                "no datum or CRS conversion was performed",
                "principal axes are not archaeological orientations",
            ],
            falsification_conditions=[
                "additional control stations move the frame outside its residual bounds",
                "an independently verified datum changes the axis ordering",
            ],
        ),
        sg.make_model_record(
            model_id="IDEAL-GPMP-NETWORK-HULL-001",
            model_type="plan_view_convex_envelope",
            source_ids=list(ids),
            input_geometry_ids=list(SOURCE_GEOMETRY_IDS),
            method="monotone-chain convex hull in Easting/Northing through measured vertices",
            parameters=hull_params,
            parameter_units={
                "vertex_count": "count",
                "area": "source units squared",
                "perimeter": source_units,
                "vertex_elevation_min": source_units,
                "vertex_elevation_max": source_units,
            },
            assumptions=[
                "the plan footprint boundary is meaningful for control stations",
                "the hull interior is unsurveyed and carries no elevation claim",
            ],
            fit_residual={"vertices_reused_from_source": hull["vertex_count"]},
            uncertainty={
                "coordinate_plane": hull["coordinate_plane"],
                "interior_sampled": False,
            },
            validity_domain="boundary of the sampled plan footprint only",
            model_status=sg.IDEALIZED_MODEL,
            limitations=[
                "not a terrain boundary, site boundary or monument outline",
                "no surface is drawn inside the polygon",
            ],
            falsification_conditions=[
                "a new station lies outside the declared hull",
                "an independent survey redefines the plan footprint",
            ],
        ),
        sg.make_model_record(
            model_id="IDEAL-GPMP-NETWORK-ELLIPSOID-001",
            model_type="two_sigma_ellipsoidal_envelope",
            source_ids=list(ids),
            input_geometry_ids=list(SOURCE_GEOMETRY_IDS),
            method="centroid plus principal axes scaled by the declared factor",
            parameters=envelope_params,
            parameter_units={
                "scale": "dimensionless",
                "semi_axis_1": source_units,
                "semi_axis_2": source_units,
                "semi_axis_3": source_units,
                "points_outside": "count",
            },
            assumptions=[
                "the scale factor is a descriptive envelope choice, not a fitted confidence level",
                "station scatter is treated symmetrically around the sample centroid",
            ],
            fit_residual=envelope["outside_positive_residual"],
            uncertainty={
                "normalized_radial_distance": envelope["normalized_radial_distance"],
                "outside_point_indices": envelope["outside_point_indices"],
            },
            validity_domain="sampled control stations only",
            model_status=sg.IDEALIZED_MODEL,
            limitations=[
                "not a statistical confidence region for a wider population",
                "not a landscape or monument surface",
            ],
            falsification_conditions=[
                "a measured station falls outside the envelope beyond its declared residual",
                "a different scale factor is required by an independently stated criterion",
            ],
        ),
        sg.make_model_record(
            model_id="IDEAL-GPMP-NETWORK-SPACING-001",
            model_type="sampling_spacing_distribution",
            source_ids=list(ids),
            input_geometry_ids=list(SOURCE_GEOMETRY_IDS),
            method="all pairwise distances plus nearest and k-nearest station distances",
            parameters=spacing_params,
            parameter_units={
                "pairwise_count": "count",
                "nearest_median": source_units,
                "k_nearest_mean": source_units,
                "density_index": "inverse source units",
            },
            assumptions=[
                "the sample spacing describes survey density, not object density",
                "source distances are used without a verified datum transform",
            ],
            fit_residual={
                "nearest_neighbor_distance": spacing["nearest_neighbor_distance"],
            },
            uncertainty={
                "k_nearest": spacing["k_nearest"],
                "k_nearest_mean_distance": spacing["k_nearest_mean_distance"],
            },
            validity_domain="sampled control network only",
            model_status=sg.IDEALIZED_MODEL,
            limitations=[
                "not the density of monuments, settlements or terrain samples",
                "uneven campaign strategy is not removed by this statistic",
            ],
            falsification_conditions=[
                "new stations materially shift the median nearest-neighbour distance",
                "an independent survey shows the spacing is an acquisition artefact",
            ],
        ),
    ]
    return records


def build_network_idealization(points: Sequence[Sequence[float]],
                               source_ids: Sequence[str]) -> Dict[str, Any]:
    """Build and validate every network-level idealized model record."""
    pts = _points3(points)
    _require(len(source_ids) == len(pts), "one source id is required per point")
    frame = principal_axes(pts)
    _require(not frame["degenerate"], "degenerate network cannot be idealized confidently")
    hull = plan_convex_hull(pts)
    spacing = spacing_statistics(pts)
    envelope = ellipsoidal_envelope(pts, frame)
    models = _build_model_records(source_ids, frame, hull, spacing, envelope)
    for record in models:
        sg.validate_model_record(record)
        _require(record["model_status"] == sg.IDEALIZED_MODEL,
                 "network idealization may not be filed as hypothetical")
    return {
        "scope": "GPMP_CONTROL_NETWORK_ONLY",
        "status": sg.IDEALIZED_MODEL,
        "not_terrain": True,
        "not_monument_geometry": True,
        "source_values_unmodified": True,
        "point_count": len(pts),
        "geometry": {
            "centroid": frame["centroid"],
            "principal_axes": frame,
            "plan_convex_hull": hull,
            "spacing": spacing,
            "ellipsoidal_envelope": envelope,
        },
        "models": models,
        "model_ids": [record["model_id"] for record in models],
        "validation": {
            "all_records_valid": True,
            "record_count": len(models),
            "statuses": sorted({record["model_status"] for record in models}),
            "full_contract_fields": list(sg.MODEL_RECORD_FIELDS),
        },
    }


__all__ = [name for name in dir() if not name.startswith("_")]
