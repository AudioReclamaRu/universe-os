"""Dependency-free geometry kernel for GIZA PRIME derived spatial work.

WHAT THIS MODULE IS
-------------------
A set of explicit, testable mathematical operations that turn *source* points
into *derived* geometry while never overwriting the source values.  Every
operation returns a new record; the caller keeps the original coordinates.

It deliberately contains no terrain reconstruction, no pyramid mesh and no
coordinate-datum conversion.  A datum transform is only legal once a checked
matrix and shared control points exist; this module provides the primitives for
such a transform but never invents its parameters.

STATUS VOCABULARY (never merge these)
-------------------------------------
MEASURED_GEOMETRY   -- value read from a source record
DERIVED_GEOMETRY    -- deterministic computation over measured values
IDEALIZED_MODEL     -- parametric approximation with declared assumptions
HYPOTHETICAL_MODEL  -- competing alternative, not selected by aesthetics
UNKNOWN             -- insufficient constraints; no surface may be drawn
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

Vector = Tuple[float, float, float]
Matrix = Tuple[Vector, Vector, Vector]

MEASURED_GEOMETRY = "MEASURED_GEOMETRY"
DERIVED_GEOMETRY = "DERIVED_GEOMETRY"
IDEALIZED_MODEL = "IDEALIZED_MODEL"
HYPOTHETICAL_MODEL = "HYPOTHETICAL_MODEL"
UNKNOWN = "UNKNOWN"
MODEL_STATUSES = (
    MEASURED_GEOMETRY, DERIVED_GEOMETRY, IDEALIZED_MODEL,
    HYPOTHETICAL_MODEL, UNKNOWN,
)

MODEL_RECORD_FIELDS: Tuple[str, ...] = (
    "model_id", "model_type", "source_ids", "input_geometry_ids", "method",
    "parameters", "parameter_units", "assumptions", "fit_residual",
    "uncertainty", "validity_domain", "model_status", "limitations",
    "falsification_conditions",
)


class GeometryValidationError(ValueError):
    """Raised for non-finite, degenerate or contract-violating geometry input."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GeometryValidationError(message)


def require_vector(value: Sequence[float], label: str = "vector") -> Vector:
    _require(len(value) == 3, "%s must have exactly three components" % label)
    out = tuple(float(v) for v in value)
    _require(all(math.isfinite(v) for v in out), "%s has a non-finite component" % label)
    return out  # type: ignore[return-value]


def vec_sub(a: Sequence[float], b: Sequence[float]) -> Vector:
    x, y = require_vector(a, "a"), require_vector(b, "b")
    return (x[0] - y[0], x[1] - y[1], x[2] - y[2])


def vec_add(a: Sequence[float], b: Sequence[float]) -> Vector:
    x, y = require_vector(a, "a"), require_vector(b, "b")
    return (x[0] + y[0], x[1] + y[1], x[2] + y[2])


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    x, y = require_vector(a, "a"), require_vector(b, "b")
    return x[0] * y[0] + x[1] * y[1] + x[2] * y[2]


def cross(a: Sequence[float], b: Sequence[float]) -> Vector:
    x, y = require_vector(a, "a"), require_vector(b, "b")
    return (x[1] * y[2] - x[2] * y[1],
            x[2] * y[0] - x[0] * y[2],
            x[0] * y[1] - x[1] * y[0])


def norm(v: Sequence[float]) -> float:
    x = require_vector(v, "v")
    return math.sqrt(dot(x, x))


def unit(v: Sequence[float]) -> Vector:
    length = norm(v)
    _require(length > 0.0, "cannot normalize a zero vector")
    x = require_vector(v, "v")
    return (x[0] / length, x[1] / length, x[2] / length)


def distance(a: Sequence[float], b: Sequence[float]) -> float:
    return norm(vec_sub(a, b))


def angle_degrees(a: Sequence[float], b: Sequence[float]) -> float:
    na, nb = norm(a), norm(b)
    _require(na > 0.0 and nb > 0.0, "angle needs two non-zero vectors")
    value = max(-1.0, min(1.0, dot(a, b) / (na * nb)))
    return math.degrees(math.acos(value))


def center_points(points: Iterable[Sequence[float]],
                  origin: Optional[Sequence[float]] = None) -> Dict[str, Any]:
    """Return freshly allocated points translated by ``origin`` (or centroid).

    The input objects are never modified.  ``origin`` itself is reported so a
    derived coordinate set can always be translated back.
    """
    pts = [require_vector(p, "point") for p in points]
    _require(bool(pts), "center_points needs at least one point")
    if origin is None:
        sums = [sum(p[i] for p in pts) for i in range(3)]
        origin_vec = tuple(s / len(pts) for s in sums)
    else:
        origin_vec = require_vector(origin, "origin")
    centered = [vec_sub(p, origin_vec) for p in pts]
    return {"origin": origin_vec, "points": centered, "source_point_count": len(pts)}


def solve_linear_system(matrix: Sequence[Sequence[float]],
                        rhs: Sequence[float]) -> Tuple[float, ...]:
    """Small dense linear solver with partial pivoting; no external libraries."""
    n = len(rhs)
    _require(len(matrix) == n, "matrix/rhs size mismatch")
    rows = []
    for i in range(n):
        row = [float(v) for v in matrix[i]]
        _require(len(row) == n, "matrix must be square")
        _require(all(math.isfinite(v) for v in row), "matrix has non-finite entry")
        rows.append(row + [float(rhs[i])])
    _require(all(math.isfinite(float(v)) for v in rhs), "rhs has non-finite entry")
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(rows[r][col]))
        _require(abs(rows[pivot][col]) > 1e-12, "singular system")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        factor = rows[col][col]
        for j in range(col, n + 1):
            rows[col][j] /= factor
        for r in range(n):
            if r == col:
                continue
            factor = rows[r][col]
            if factor == 0.0:
                continue
            for j in range(col, n + 1):
                rows[r][j] -= factor * rows[col][j]
    return tuple(rows[i][n] for i in range(n))


def fit_plane_least_squares(points: Sequence[Sequence[float]]) -> Dict[str, Any]:
    """Fit z = a*x + b*y + c by ordinary least squares.

    This is a DERIVED plane over supplied points, not a terrain surface.  The
    returned residuals make its limited validity explicit.
    """
    pts = [require_vector(p, "point") for p in points]
    _require(len(pts) >= 3, "plane fit needs at least three points")
    a11 = sum(p[0] * p[0] for p in pts)
    a12 = sum(p[0] * p[1] for p in pts)
    a22 = sum(p[1] * p[1] for p in pts)
    a13 = sum(p[0] for p in pts)
    a23 = sum(p[1] for p in pts)
    a33 = float(len(pts))
    b1 = sum(p[0] * p[2] for p in pts)
    b2 = sum(p[1] * p[2] for p in pts)
    b3 = sum(p[2] for p in pts)
    a, b, c = solve_linear_system(
        ((a11, a12, a13), (a12, a22, a23), (a13, a23, a33)), (b1, b2, b3))
    residuals = [p[2] - (a * p[0] + b * p[1] + c) for p in pts]
    summary = residual_summary(residuals)
    return {
        "coefficient_a": a,
        "coefficient_b": b,
        "intercept_c": c,
        "normal": (-a, -b, 1.0),
        "geometry_status": DERIVED_GEOMETRY,
        "interpretation": "ordinary least-squares plane over control points; NOT terrain",
        "point_count": len(pts),
        "residual_summary": summary,
    }


def project_to_plane(point: Sequence[float], plane: Dict[str, Any]) -> Vector:
    p = require_vector(point, "point")
    a = float(plane["coefficient_a"])
    b = float(plane["coefficient_b"])
    c = float(plane["intercept_c"])
    z = a * p[0] + b * p[1] + c
    return (p[0], p[1], z)


def residual_summary(residuals: Sequence[float]) -> Dict[str, Any]:
    vals = [float(v) for v in residuals]
    _require(all(math.isfinite(v) for v in vals), "residual is non-finite")
    _require(bool(vals), "residual summary needs at least one value")
    mean = sum(vals) / len(vals)
    rms = math.sqrt(sum(v * v for v in vals) / len(vals))
    return {
        "count": len(vals),
        "mean": mean,
        "rms": rms,
        "max_absolute": max(abs(v) for v in vals),
    }


def rotation_matrix(axis: str, theta_radians: float) -> Matrix:
    _require(axis in ("x", "y", "z"), "axis must be x, y or z")
    _require(math.isfinite(theta_radians), "angle must be finite")
    c, s = math.cos(theta_radians), math.sin(theta_radians)
    if axis == "x":
        return ((1.0, 0.0, 0.0), (0.0, c, -s), (0.0, s, c))
    if axis == "y":
        return ((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c))
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def scale_matrix(sx: float, sy: float, sz: float) -> Matrix:
    values = (sx, sy, sz)
    _require(all(math.isfinite(v) for v in values), "scale must be finite")
    return ((sx, 0.0, 0.0), (0.0, sy, 0.0), (0.0, 0.0, sz))


def mat_mul(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> Matrix:
    left = [require_vector(row, "matrix row") for row in a]
    right = [require_vector(row, "matrix row") for row in b]
    _require(len(left) == 3 and len(right) == 3, "matrices must be 3x3")
    cols = tuple(tuple(right[r][c] for r in range(3)) for c in range(3))
    return tuple(tuple(dot(row, col) for col in cols) for row in left)  # type: ignore[return-value]


def mat_vec(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> Vector:
    rows = [require_vector(row, "matrix row") for row in matrix]
    _require(len(rows) == 3, "matrix must be 3x3")
    v = require_vector(vector, "vector")
    return tuple(dot(row, v) for row in rows)  # type: ignore[return-value]


def is_orthogonal(matrix: Sequence[Sequence[float]], tolerance: float = 1e-9) -> bool:
    """True only for an orthonormal basis (unit rows AND pairwise orthogonal).

    A rigid rotation must satisfy this.  A non-uniform scale has orthogonal
    rows but is correctly rejected because it would distort distances.
    """
    rows = [require_vector(row, "matrix row") for row in matrix]
    _require(len(rows) == 3, "matrix must be 3x3")
    _require(tolerance > 0.0, "tolerance must be positive")
    unit_rows = all(abs(norm(row) - 1.0) <= tolerance for row in rows)
    pairwise = all(abs(dot(rows[i], rows[j])) <= tolerance
                   for i in range(3) for j in range(i + 1, 3))
    return unit_rows and pairwise


def apply_transform(point: Sequence[float], matrix: Sequence[Sequence[float]],
                    origin: Sequence[float]) -> Dict[str, Any]:
    """Return a NEW derived coordinate; never write into the source record."""
    centered = vec_sub(point, origin)
    transformed = mat_vec(matrix, centered)
    return {
        "transformed_point": vec_add(transformed, origin),
        "centered_point": centered,
        "geometry_status": DERIVED_GEOMETRY,
        "source_values_unmodified": True,
    }


def _require_pair(value: Sequence[float], label: str) -> Tuple[float, float]:
    _require(len(value) == 2, "%s must have exactly two components" % label)
    out = (float(value[0]), float(value[1]))
    _require(all(math.isfinite(v) for v in out), "%s has a non-finite component" % label)
    return out


def inverse_distance_interpolation(points: Sequence[Sequence[float]],
                                   query_xy: Sequence[float],
                                   power: float = 2.0) -> Dict[str, Any]:
    """Interpolate a scalar z at a query point, with an explicit uncertainty.

    Sparse control stations are not a terrain.  The returned spread is a
    measure of local disagreement, not a validated elevation.
    """
    pts = [require_vector(p, "point") for p in points]
    q = _require_pair(query_xy, "query_xy")
    _require(bool(pts), "interpolation needs at least one point")
    _require(power > 0.0, "power must be positive")
    weights: List[float] = []
    for p in pts:
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        _require(d > 0.0, "query coincides with a control point")
        weights.append(1.0 / (d ** power))
    total = sum(weights)
    value = sum(w * p[2] for w, p in zip(weights, pts)) / total
    spread = math.sqrt(sum(w * (p[2] - value) ** 2
                           for w, p in zip(weights, pts)) / total)
    return {
        "interpolated_z": value,
        "local_spread": spread,
        "geometry_status": DERIVED_GEOMETRY,
        "interpretation": "weighted control-station estimate; NOT a terrain surface",
        "point_count": len(pts),
    }


def make_model_record(model_id: str, model_type: str, source_ids: Sequence[str],
                      input_geometry_ids: Sequence[str], method: str,
                      parameters: Dict[str, float],
                      parameter_units: Dict[str, str],
                      assumptions: Sequence[str], fit_residual: Dict[str, Any],
                      uncertainty: Dict[str, Any], validity_domain: str,
                      model_status: str, limitations: Sequence[str],
                      falsification_conditions: Sequence[str]) -> Dict[str, Any]:
    """Build a model record with every field the research contract demands."""
    _require(bool(model_id), "model_id is required")
    _require(model_status in (IDEALIZED_MODEL, HYPOTHETICAL_MODEL),
             "model records describe idealized or hypothetical models only")
    _require(bool(source_ids) and bool(input_geometry_ids),
             "a model must name its sources and input geometry")
    _require(set(parameters).issubset(set(parameter_units)),
             "every parameter needs a declared unit")
    _require(bool(assumptions) and bool(limitations) and bool(falsification_conditions),
             "assumptions, limitations and falsification conditions are mandatory")
    return {
        "model_id": model_id,
        "model_type": model_type,
        "source_ids": list(source_ids),
        "input_geometry_ids": list(input_geometry_ids),
        "method": method,
        "parameters": dict(parameters),
        "parameter_units": dict(parameter_units),
        "assumptions": list(assumptions),
        "fit_residual": dict(fit_residual),
        "uncertainty": dict(uncertainty),
        "validity_domain": validity_domain,
        "model_status": model_status,
        "limitations": list(limitations),
        "falsification_conditions": list(falsification_conditions),
    }


def validate_model_record(record: Dict[str, Any]) -> bool:
    for field in MODEL_RECORD_FIELDS:
        _require(field in record, "model record missing %s" % field)
    _require(record["model_status"] in (IDEALIZED_MODEL, HYPOTHETICAL_MODEL),
             "measured geometry may not be filed as a model record")
    _require(record["model_status"] != MEASURED_GEOMETRY,
             "model status must stay distinct from MEASURED_GEOMETRY")
    _require(bool(record["source_ids"]), "model has no source")
    _require(set(record["parameters"]).issubset(set(record["parameter_units"])),
             "model parameter without unit")
    _require(bool(record["assumptions"]) and bool(record["falsification_conditions"]),
             "model needs assumptions and falsification conditions")
    return True


__all__ = [name for name in dir() if not name.startswith("_")]
