"""Analyze explicitly paired spatial-length / temporal-duration scaling data."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

PHASE08 = Path(__file__).resolve().parents[1] / "phase-08"
if str(PHASE08) not in sys.path:
    sys.path.insert(0, str(PHASE08))
try:
    from relation_discovery import REFS as ATLAS_NUMERIC_REFERENCES
except ImportError as exc:
    raise RuntimeError("Phase 08 relation_discovery.py is required beside Phase 13") from exc


def paired(n: int) -> str:
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("integer key required")
    if n < 0:
        return "-" + paired(-n)
    def digits(v: int, base: int) -> str:
        if v == 0:
            return "0"
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        out = ""
        while v:
            v, r = divmod(v, base)
            out = alphabet[r] + out
        return out
    return f"<{digits(n, 2)}_2|{digits(n, 3)}_3>"


def atlas_matches(value: float, tolerance: float) -> list[dict[str, Any]]:
    found = []
    for ref in ATLAS_NUMERIC_REFERENCES:
        error = abs(value - ref.value) / abs(ref.value) if ref.value else abs(value)
        if error <= tolerance:
            found.append({"atlas_key": ref.key, "symbol": ref.symbol,
                          "exact_expression": ref.expression, "family": ref.family,
                          "relative_error_numeric_secondary": error})
    return sorted(found, key=lambda x: x["relative_error_numeric_secondary"])


def _weighted_line(x: Sequence[float], y: Sequence[float], variances: Sequence[float] | None):
    weights = [1.0 / v for v in variances] if variances is not None else [1.0] * len(x)
    s0 = sum(weights)
    sx = sum(w * v for w, v in zip(weights, x))
    sy = sum(w * v for w, v in zip(weights, y))
    sxx = sum(w * a * a for w, a in zip(weights, x))
    sxy = sum(w * a * b for w, a, b in zip(weights, x, y))
    determinant = s0 * sxx - sx * sx
    if determinant <= 1e-18 * max(1.0, s0 * sxx):
        raise ValueError("spatial observations do not span enough range for a slope")
    intercept = (sy * sxx - sx * sxy) / determinant
    slope = (s0 * sxy - sx * sy) / determinant
    residuals = [b - intercept - slope * a for a, b in zip(x, y)]
    rss = sum(w * r * r for w, r in zip(weights, residuals))
    covariance = ((sxx / determinant, -sx / determinant),
                  (-sx / determinant, s0 / determinant))
    return intercept, slope, residuals, rss, covariance


def _validate_array(name: str, values: Any, n: int, *, positive: bool = False,
                    lower: float | None = None, upper: float | None = None) -> list[float] | None:
    if values is None:
        return None
    result = [float(v) for v in values]
    if len(result) != n or any(not math.isfinite(v) for v in result):
        raise ValueError(f"{name} must contain {n} finite values")
    if positive and any(v <= 0 for v in result):
        raise ValueError(f"{name} values must be positive")
    if lower is not None and any(v < lower for v in result):
        raise ValueError(f"{name} values must be >= {lower}")
    if upper is not None and any(v > upper for v in result):
        raise ValueError(f"{name} values must be <= {upper}")
    return result


def prepare_dataset(dataset: Mapping[str, Any]):
    length = [float(v) for v in dataset["length"]]
    duration = [float(v) for v in dataset["time"]]
    n = len(length)
    if n != len(duration) or n < 3:
        raise ValueError("paired length/time arrays must have equal length and at least three observations")
    if any(not math.isfinite(v) or v <= 0 for v in length + duration):
        raise ValueError("length and time observations must be positive and finite")
    sigma_l = _validate_array("sigma_log_length", dataset.get("sigma_log_length"), n, positive=True)
    sigma_t = _validate_array("sigma_log_time", dataset.get("sigma_log_time"), n, positive=True)
    rho = _validate_array("rho_log_length_time", dataset.get("rho_log_length_time"), n,
                          lower=-1.0, upper=1.0)
    if sigma_l is not None and sigma_t is None:
        raise ValueError("sigma_log_length requires sigma_log_time for the effective-variance fit")
    if rho is not None and (sigma_l is None or sigma_t is None):
        raise ValueError("rho_log_length_time requires both sigma_log_length and sigma_log_time")
    rho = rho if rho is not None else [0.0] * n
    rows = list(zip(length, duration,
                    sigma_l if sigma_l is not None else [None] * n,
                    sigma_t if sigma_t is not None else [None] * n,
                    rho))
    rows.sort(key=lambda r: r[0])
    sorted_length = [row[0] for row in rows]
    sorted_duration = [row[1] for row in rows]
    sorted_sigma_l = None if sigma_l is None else [row[2] for row in rows]
    sorted_sigma_t = None if sigma_t is None else [row[3] for row in rows]
    sorted_rho = [row[4] for row in rows]
    return sorted_length, sorted_duration, sorted_sigma_l, sorted_sigma_t, sorted_rho


def analyze_dataset(dataset: Mapping[str, Any], *, tolerance: float = 1e-4,
                    max_iterations: int = 100, convergence_tolerance: float = 1e-10) -> dict[str, Any]:
    length, duration, sigma_l, sigma_t, rho = prepare_dataset(dataset)
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Atlas relative tolerance must be positive and finite")
    if max_iterations < 1 or not math.isfinite(convergence_tolerance) or convergence_tolerance <= 0:
        raise ValueError("iteration count and convergence tolerance must be positive")

    log_l = [math.log(v) for v in length]
    log_t = [math.log(v) for v in duration]
    l_ref = math.exp(sum(log_l) / len(log_l))
    t_ref = math.exp(sum(log_t) / len(log_t))
    x = [v - math.log(l_ref) for v in log_l]
    y = [v - math.log(t_ref) for v in log_t]

    variances = [s * s for s in sigma_t] if sigma_t is not None else None
    intercept, slope, residuals, rss, covariance = _weighted_line(x, y, variances)
    converged = True
    iterations = 1
    fit_method = "ordinary_least_squares" if sigma_t is None else "weighted_least_squares_time_uncertainty"
    if sigma_l is not None and sigma_t is not None:
        fit_method = "iterative_effective_variance_errors_in_variables"
        converged = False
        for iteration in range(1, max_iterations + 1):
            effective = []
            for sx, sy, correlation in zip(sigma_l, sigma_t, rho):
                covariance_xy = correlation * sx * sy
                variance = sy * sy + slope * slope * sx * sx - 2.0 * slope * covariance_xy
                if not math.isfinite(variance) or variance <= 0:
                    raise ValueError("effective log-residual variance is nonpositive; inspect uncertainties and correlation")
                effective.append(variance)
            new_intercept, new_slope, new_residuals, new_rss, new_covariance = _weighted_line(x, y, effective)
            iterations = iteration
            if abs(new_slope - slope) <= convergence_tolerance * max(1.0, abs(slope)):
                intercept, slope, residuals, rss, covariance = (
                    new_intercept, new_slope, new_residuals, new_rss, new_covariance
                )
                converged = True
                break
            intercept, slope, residuals, rss, covariance = (
                new_intercept, new_slope, new_residuals, new_rss, new_covariance
            )

    n = len(length)
    if sigma_t is not None:
        slope_se = math.sqrt(max(0.0, covariance[1][1]))
        uncertainty_basis = "provided measurement covariance; conditional on effective-variance approximation"
    else:
        residual_variance = sum(r * r for r in residuals) / max(1, n - 2)
        slope_se = math.sqrt(max(0.0, covariance[1][1] * residual_variance))
        uncertainty_basis = "residual-based OLS estimate; assumes independent homoscedastic log residuals"
    mean_y = sum(y) / n
    total_y = sum((v - mean_y) ** 2 for v in y)
    residual_sum = sum(r * r for r in residuals)
    r_squared = 1.0 if total_y == 0 and residual_sum == 0 else (0.0 if total_y == 0 else 1.0 - residual_sum / total_y)

    return {
        "name": dataset.get("name", "paired_space_time_dataset"),
        "length_name": dataset.get("length_name", "characteristic_length"),
        "time_name": dataset.get("time_name", "characteristic_time"),
        "length_unit": dataset.get("length_unit"),
        "time_unit": dataset.get("time_unit"),
        "observation_count": paired(n),
        "paired_observation_rule": "Each length is paired with the time at the same observation index before sorting; no unpaired dataset comparison is performed.",
        "length_reference_geometric_mean": l_ref,
        "time_reference_geometric_mean": t_ref,
        "dynamic_scaling_exponent_z": slope,
        "reference_amplitude": math.exp(intercept),
        "reference_relation": f"time/time_ref = {math.exp(intercept):.12g} * (length/length_ref)^{slope:.12g}",
        "r_squared_log_space": r_squared,
        "log_residual_sum_squares": residual_sum,
        "slope_standard_uncertainty": slope_se,
        "uncertainty_basis": uncertainty_basis,
        "fit_method": fit_method,
        "iterations": paired(iterations),
        "converged": converged,
        "atlas_matches_for_dynamic_exponent": atlas_matches(slope, tolerance),
        "effective_variance_rule": "Var(log time - z log length) = sigma_log_time^2 + z^2 sigma_log_length^2 - 2 z Cov(log length, log time).",
        "limits": [
            "A dynamic exponent is meaningful only for explicitly paired characteristic length/time observations from a comparable process or defined ensemble.",
            "The effective-variance errors-in-variables fit is a first-order iterative approximation, not a full latent-variable likelihood model.",
            "The residual-based OLS slope uncertainty assumes independent homoscedastic log residuals.",
            "Shared calibration errors, between-process heterogeneity and model discrepancy require explicit covariance or hierarchical models.",
            "An Atlas match for z is exploratory and is not evidence of a universal dynamic law or causal mechanism."
        ]
    }


def analyze_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    tolerance = float(payload.get("atlas_relative_tolerance", 1e-4))
    datasets = payload.get("paired_datasets", [])
    if not datasets:
        raise ValueError("at least one explicitly paired space-time dataset is required")
    results = [analyze_dataset(dataset, tolerance=tolerance) for dataset in datasets]
    return {
        "schema": "universe.paired-space-time-scaling.v1",
        "dataset_count": paired(len(results)),
        "atlas_numeric_reference_count": paired(len(ATLAS_NUMERIC_REFERENCES)),
        "atlas_relative_tolerance": tolerance,
        "spacetime_pairing_rule": "Only paired length/time measurements within each dataset are used to estimate a dynamic exponent. Independent spatial and temporal series are never paired by matching array length or index across datasets.",
        "dimensional_rule": "The fitted exponent is based on ratios to geometric reference scales; unit changes alter reference scales/intercept but not the exponent.",
        "datasets": results,
        "global_guard": "A fitted z is a candidate dynamic scaling exponent over the observed domain and time window; it is not assumed universal."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("space_time_scaling_report.json"))
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze_payload(payload)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
