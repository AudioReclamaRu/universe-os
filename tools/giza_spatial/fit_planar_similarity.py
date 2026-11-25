#!/usr/bin/env python3
"""Fit a documented 2D rigid/similarity transform from paired control points.

Input CSV columns:
  point_id, role, source_x, source_y, target_x, target_y
where role is fit or check.

The script intentionally does not infer axis order, axis direction, CRS, units,
magnetic declination, or vertical datum. Those must be normalized/documented
before coordinates are supplied. Reflection is not fitted; any axis reversal
must be explicit in the source-axis mapping.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable, Sequence

REQUIRED_COLUMNS = {
    "point_id", "role", "source_x", "source_y", "target_x", "target_y"
}


class TransformError(ValueError):
    """Raised when input geometry is insufficient or inconsistent."""


@dataclass(frozen=True)
class PointPair:
    point_id: str
    role: str
    source_x: float
    source_y: float
    target_x: float
    target_y: float


@dataclass(frozen=True)
class Transform2D:
    model: str
    a: float
    b: float
    tx: float
    ty: float
    scale: float
    rotation_radians: float

    @property
    def matrix(self) -> list[list[float]]:
        return [[self.a, -self.b], [self.b, self.a]]

    def apply(self, x: float, y: float) -> tuple[float, float]:
        return (self.a * x - self.b * y + self.tx,
                self.b * x + self.a * y + self.ty)


@dataclass(frozen=True)
class Metrics:
    count: int
    bias_x: float
    bias_y: float
    rmse_x: float
    rmse_y: float
    rmse_2d: float
    max_error_2d: float


def _finite_number(value: str, column: str, row_number: int) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TransformError(
            f"Row {row_number}: {column} is not numeric: {value!r}"
        ) from exc
    if not math.isfinite(result):
        raise TransformError(f"Row {row_number}: {column} must be finite")
    return result


def read_point_pairs(path: Path) -> list[PointPair]:
    if not path.is_file():
        raise TransformError(f"Input CSV does not exist: {path}")
    pairs: list[PointPair] = []
    seen_ids: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise TransformError(
                "Missing CSV columns: " + ", ".join(sorted(missing))
            )
        for row_number, row in enumerate(reader, start=2):
            point_id = (row.get("point_id") or "").strip()
            role = (row.get("role") or "").strip().lower()
            if not point_id:
                raise TransformError(f"Row {row_number}: point_id is empty")
            if point_id in seen_ids:
                raise TransformError(f"Row {row_number}: duplicate point_id {point_id!r}")
            seen_ids.add(point_id)
            if role not in {"fit", "check"}:
                raise TransformError(
                    f"Row {row_number}: role must be 'fit' or 'check', got {role!r}"
                )
            pairs.append(PointPair(
                point_id=point_id,
                role=role,
                source_x=_finite_number(row.get("source_x"), "source_x", row_number),
                source_y=_finite_number(row.get("source_y"), "source_y", row_number),
                target_x=_finite_number(row.get("target_x"), "target_x", row_number),
                target_y=_finite_number(row.get("target_y"), "target_y", row_number),
            ))
    fit = [p for p in pairs if p.role == "fit"]
    if len(fit) < 3:
        raise TransformError("At least 3 fit points are required; keep check points separate")
    return pairs


def _assert_2d_spread(points: Sequence[tuple[float, float]], label: str) -> None:
    mx = mean(p[0] for p in points)
    my = mean(p[1] for p in points)
    xx = sum((x - mx) ** 2 for x, _ in points)
    yy = sum((y - my) ** 2 for _, y in points)
    xy = sum((x - mx) * (y - my) for x, y in points)
    det = xx * yy - xy * xy
    scale = max((xx + yy) ** 2, 1.0)
    if xx + yy <= 1e-15 or det <= 1e-12 * scale:
        raise TransformError(
            f"{label} points do not span a stable 2D area; check geometry and distribution"
        )


def fit_transform(fit_pairs: Sequence[PointPair], model: str = "similarity") -> Transform2D:
    if model not in {"rigid", "similarity"}:
        raise TransformError("model must be 'rigid' or 'similarity'")
    if len(fit_pairs) < 3:
        raise TransformError("At least 3 fit points are required")

    src = [(p.source_x, p.source_y) for p in fit_pairs]
    dst = [(p.target_x, p.target_y) for p in fit_pairs]
    _assert_2d_spread(src, "Source")
    _assert_2d_spread(dst, "Target")

    sx = mean(x for x, _ in src)
    sy = mean(y for _, y in src)
    tx_mean = mean(x for x, _ in dst)
    ty_mean = mean(y for _, y in dst)

    denominator = sum((x - sx) ** 2 + (y - sy) ** 2 for x, y in src)
    if denominator <= 1e-15:
        raise TransformError("Source fit points have zero spread")

    dot = 0.0
    cross = 0.0
    for (x, y), (u, v) in zip(src, dst):
        x0, y0 = x - sx, y - sy
        u0, v0 = u - tx_mean, v - ty_mean
        dot += x0 * u0 + y0 * v0
        cross += x0 * v0 - y0 * u0

    a_raw = dot / denominator
    b_raw = cross / denominator
    estimated_scale = math.hypot(a_raw, b_raw)
    if estimated_scale <= 1e-15:
        raise TransformError("Estimated transform scale is zero")

    if model == "rigid":
        a = a_raw / estimated_scale
        b = b_raw / estimated_scale
        scale = 1.0
    else:
        a, b = a_raw, b_raw
        scale = estimated_scale

    tx = tx_mean - (a * sx - b * sy)
    ty = ty_mean - (b * sx + a * sy)
    rotation = math.atan2(b, a)
    return Transform2D(model, a, b, tx, ty, scale, rotation)


def calculate_metrics(pairs: Sequence[PointPair], transform: Transform2D) -> Metrics | None:
    if not pairs:
        return None
    dxs: list[float] = []
    dys: list[float] = []
    radial: list[float] = []
    for p in pairs:
        px, py = transform.apply(p.source_x, p.source_y)
        dx = px - p.target_x
        dy = py - p.target_y
        dxs.append(dx)
        dys.append(dy)
        radial.append(math.hypot(dx, dy))
    return Metrics(
        count=len(pairs),
        bias_x=mean(dxs),
        bias_y=mean(dys),
        rmse_x=math.sqrt(mean(v * v for v in dxs)),
        rmse_y=math.sqrt(mean(v * v for v in dys)),
        rmse_2d=math.sqrt(mean(v * v for v in radial)),
        max_error_2d=max(radial),
    )


def residual_rows(pairs: Iterable[PointPair], transform: Transform2D) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for p in pairs:
        px, py = transform.apply(p.source_x, p.source_y)
        dx, dy = px - p.target_x, py - p.target_y
        rows.append({
            "point_id": p.point_id,
            "role": p.role,
            "source_x": p.source_x,
            "source_y": p.source_y,
            "target_x": p.target_x,
            "target_y": p.target_y,
            "transformed_x": px,
            "transformed_y": py,
            "residual_x": dx,
            "residual_y": dy,
            "residual_2d": math.hypot(dx, dy),
        })
    return rows


def write_outputs(
    pairs: Sequence[PointPair], transform: Transform2D, output_dir: Path,
    source_crs: str, target_crs: str, source_unit: str, target_unit: str,
    axis_mapping: str, input_path: Path
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    transform_path = output_dir / "transform.json"
    residual_path = output_dir / "residuals.csv"
    if transform_path.exists() or residual_path.exists():
        raise TransformError(
            f"Output exists in {output_dir}; choose a new directory to preserve previous results"
        )

    fit = [p for p in pairs if p.role == "fit"]
    check = [p for p in pairs if p.role == "check"]
    residuals = residual_rows(pairs, transform)
    input_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()
    result = {
        "schema_version": "1.0",
        "status": "CALCULATED_FROM_SUPPLIED_CONTROL_POINTS_NOT_FIELD_VALIDATED",
        "input_csv": str(input_path),
        "input_sha256": input_sha256,
        "source_crs_label": source_crs,
        "target_crs_label": target_crs,
        "source_unit": source_unit,
        "target_unit": target_unit,
        "source_axis_mapping_and_normalization": axis_mapping,
        "axis_mapping_warning": (
            "Axis order and direction must be normalized explicitly before input. "
            "This script does not infer CRS, axis flips, magnetic declination, or vertical datum."
        ),
        "model": transform.model,
        "matrix_2x2": transform.matrix,
        "translation": {"x": transform.tx, "y": transform.ty},
        "parameters": {
            "a": transform.a,
            "b": transform.b,
            "scale": transform.scale,
            "rotation_radians": transform.rotation_radians,
            "rotation_degrees": math.degrees(transform.rotation_radians),
        },
        "fit_point_ids": [p.point_id for p in fit],
        "check_point_ids": [p.point_id for p in check],
        "fit_metrics": asdict(calculate_metrics(fit, transform)),
        "check_metrics": (
            asdict(calculate_metrics(check, transform)) if check else None
        ),
        "limitations": [
            "2D horizontal transformation only; no vertical datum conversion.",
            "No reflection is estimated; source-axis mapping must be explicit.",
            "Fit residuals are not independent validation; use separate check points.",
            "Numerical output is not an authoritative CRS transformation without source metadata and survey review.",
        ],
    }
    transform_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with residual_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(residuals[0].keys()))
        writer.writeheader()
        writer.writerows(residuals)
    return transform_path, residual_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV with paired fit/check points")
    parser.add_argument("--out-dir", type=Path, required=True, help="New output directory")
    parser.add_argument("--source-crs", required=True, help="Exact source grid/CRS label")
    parser.add_argument("--target-crs", required=True, help="Exact target grid/CRS label")
    parser.add_argument("--source-unit", required=True, help="Source horizontal coordinate unit")
    parser.add_argument("--target-unit", required=True, help="Target horizontal coordinate unit")
    parser.add_argument("--axis-mapping", required=True, help="Explicit source axis order/direction normalization")
    parser.add_argument("--model", choices=("rigid", "similarity"), default="similarity")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        pairs = read_point_pairs(args.input)
        fit = [p for p in pairs if p.role == "fit"]
        check = [p for p in pairs if p.role == "check"]
        transform = fit_transform(fit, args.model)
        transform_path, residual_path = write_outputs(
            pairs, transform, args.out_dir, args.source_crs,
            args.target_crs, args.source_unit, args.target_unit,
            args.axis_mapping, args.input
        )
        print(f"Transform: {transform_path}")
        print(f"Residuals: {residual_path}")
        print(f"Fit points: {len(fit)}; independent check points: {len(check)}")
        print(f"Model: {transform.model}; scale: {transform.scale:.12g}; "
              f"rotation: {math.degrees(transform.rotation_radians):.9f} deg")
        if check:
            metrics = calculate_metrics(check, transform)
            assert metrics is not None
            print(f"Independent check RMSE 2D: {metrics.rmse_2d:.6g}; "
                  f"max: {metrics.max_error_2d:.6g}")
        else:
            print("WARNING: no independent check points supplied")
        return 0
    except (TransformError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
