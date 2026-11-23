"""Analyze power-law regimes, crossovers and discrete-scale log-periodicity."""
from __future__ import annotations
import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

PHASE08 = Path(__file__).resolve().parents[1] / "phase-08"
if str(PHASE08) not in sys.path:
    sys.path.insert(0, str(PHASE08))
try:
    from relation_discovery import REFS as ATLAS_NUMERIC_REFERENCES
except ImportError as exc:
    raise RuntimeError("Phase 08 relation_discovery.py is required beside Phase 12") from exc


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


def solve_linear(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    n = len(vector)
    a = [list(matrix[i]) + [float(vector[i])] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-14:
            raise ArithmeticError("singular normal-equation matrix")
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [v / scale for v in a[col]]
        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            a[row] = [x - factor * y for x, y in zip(a[row], a[col])]
    return [a[i][-1] for i in range(n)]


def weighted_least_squares(design: Sequence[Sequence[float]], y: Sequence[float],
                           sigma: Sequence[float] | None = None):
    n, p = len(y), len(design[0])
    weights = [1.0 / (s * s) for s in sigma] if sigma is not None else [1.0] * n
    gram = [[sum(weights[r] * design[r][i] * design[r][j] for r in range(n))
             for j in range(p)] for i in range(p)]
    rhs = [sum(weights[r] * design[r][i] * y[r] for r in range(n)) for i in range(p)]
    beta = solve_linear(gram, rhs)
    residuals = [y[r] - sum(design[r][i] * beta[i] for i in range(p)) for r in range(n)]
    rss = sum(weights[i] * residuals[i] ** 2 for i in range(n))
    return beta, residuals, rss


def model_bic(residuals: Sequence[float], sigma: Sequence[float] | None, params: int) -> float:
    n = len(residuals)
    if sigma is not None:
        loss = sum(math.log(s * s) + (r / s) ** 2 for r, s in zip(residuals, sigma))
    else:
        rss = sum(r * r for r in residuals)
        rss = max(rss, 1e-300)
        loss = n * math.log(rss / n)
    return loss + params * math.log(n)


def prepare_dataset(dataset: Mapping[str, Any]):
    x = [float(v) for v in dataset["x"]]
    y = [float(v) for v in dataset["y"]]
    if len(x) != len(y) or len(x) < 4:
        raise ValueError("x and y must have equal length and at least four paired values")
    if any(not math.isfinite(v) or v <= 0 for v in x + y):
        raise ValueError("power-law analysis requires positive finite x and y values")
    sigma = dataset.get("sigma_log_y")
    if sigma is not None:
        sigma = [float(v) for v in sigma]
        if len(sigma) != len(x) or any(not math.isfinite(v) or v <= 0 for v in sigma):
            raise ValueError("sigma_log_y must contain positive finite log-standard uncertainties")
    rows = sorted(zip(x, y, sigma if sigma is not None else [None] * len(x)), key=lambda r: r[0])
    x, y, sig = [r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows]
    if len(set(x)) != len(x):
        raise ValueError("x values must be unique; aggregate repeated x measurements before analysis")
    if sigma is None:
        sig = None
    return x, y, sig


def analyze_dataset(dataset: Mapping[str, Any], *, tolerance: float = 1e-4,
                    min_points_per_regime: int = 4, dsi_grid_size: int = 512) -> dict[str, Any]:
    x, y, sigma = prepare_dataset(dataset)
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Atlas relative tolerance must be positive and finite")
    if min_points_per_regime < 3:
        raise ValueError("min_points_per_regime must be at least three")
    if dsi_grid_size < 16:
        raise ValueError("dsi_grid_size must be at least sixteen")
    lx = [math.log(v) for v in x]
    ly = [math.log(v) for v in y]
    x_ref = math.exp(sum(lx) / len(lx))
    y_ref = math.exp(sum(ly) / len(ly))
    x_center = math.log(x_ref)
    z_y = [v - math.log(y_ref) for v in ly]
    dx = [v - x_center for v in lx]

    global_design = [[1.0, v] for v in dx]
    beta, residuals, rss = weighted_least_squares(global_design, z_y, sigma)
    global_slope = beta[1]
    global_bic = model_bic(residuals, sigma, 2)
    global_result = {
        "exponent": global_slope,
        "amplitude_at_reference": y_ref,
        "reference_x": x_ref,
        "reference_relation": f"y/reference_y = (x/reference_x)^{global_slope:.12g}",
        "weighted_or_unweighted_rss": rss,
        "bic": global_bic,
        "atlas_matches_for_exponent": atlas_matches(global_slope, tolerance),
    }

    best_piecewise = None
    n = len(x)
    if n >= 2 * min_points_per_regime:
        for split in range(min_points_per_regime - 1, n - min_points_per_regime):
            knot = lx[split]
            design = [[1.0, value - x_center, max(0.0, value - knot)] for value in lx]
            try:
                coeff, res, piece_rss = weighted_least_squares(design, z_y, sigma)
            except ArithmeticError:
                continue
            bic = model_bic(res, sigma, 4)
            candidate = (bic, knot, coeff, res, piece_rss)
            if best_piecewise is None or candidate[0] < best_piecewise[0]:
                best_piecewise = candidate
    if best_piecewise is None:
        piecewise_result = {"available": False, "reason": "insufficient_points_for_two_regimes"}
    else:
        bic, knot, coeff, piece_residuals, piece_rss = best_piecewise
        before = coeff[1]
        after = coeff[1] + coeff[2]
        piecewise_result = {
            "available": True,
            "break_x": math.exp(knot),
            "exponent_before": before,
            "exponent_after": after,
            "exponent_change": after - before,
            "weighted_or_unweighted_rss": piece_rss,
            "bic": bic,
            "delta_bic_piecewise_minus_global": bic - global_bic,
            "atlas_matches_before": atlas_matches(before, tolerance),
            "atlas_matches_after": atlas_matches(after, tolerance),
            "interpretation": "exploratory continuous two-regime hinge fit; breakpoint and model-selection evidence require independent validation",
        }

    # Select the best non-periodic trend before scanning for log-periodicity.
    # This avoids treating a piecewise crossover residual as a periodic signal.
    baseline_design = global_design
    baseline_residuals = residuals
    baseline_bic = global_bic
    baseline_params = 2
    baseline_name = "global_power_law"
    if best_piecewise is not None and best_piecewise[0] < global_bic:
        _, knot, _, _, _ = best_piecewise
        baseline_design = [[1.0, value - x_center, max(0.0, value - knot)] for value in lx]
        _, baseline_residuals, _ = weighted_least_squares(baseline_design, z_y, sigma)
        baseline_bic = best_piecewise[0]
        baseline_params = 4
        baseline_name = "two_regime_crossover"

    dsi_result = {"available": False, "reason": "insufficient_log_span_or_points"}
    if n >= 8:
        span = lx[-1] - lx[0]
        gaps = [lx[i + 1] - lx[i] for i in range(n - 1)]
        median_gap = statistics.median(gaps)
        if span > 0 and median_gap > 0:
            omega_min = 2 * math.pi / span
            omega_max = math.pi / median_gap
            if omega_max > omega_min:
                best = None
                for index in range(dsi_grid_size):
                    omega = omega_min + (omega_max - omega_min) * index / (dsi_grid_size - 1)
                    cosine = [math.cos(omega * value) for value in lx]
                    sine = [math.sin(omega * value) for value in lx]
                    design = [baseline_design[i] + [cosine[i], sine[i]] for i in range(n)]
                    try:
                        coeff, dsi_residuals, dsi_rss = weighted_least_squares(design, z_y, sigma)
                    except ArithmeticError:
                        continue
                    if best is None or dsi_rss < best[0]:
                        best = (dsi_rss, omega, coeff, dsi_residuals)
                if best is not None:
                    dsi_rss, omega, coeff, dsi_residuals = best
                    base_weighted_rss = sum(
                        (1.0 / (s0 * s0) if sigma is not None else 1.0) * r * r
                        for r, s0 in zip(baseline_residuals, sigma if sigma is not None else [1.0] * n)
                    )
                    improvement = max(0.0, 1.0 - dsi_rss / max(base_weighted_rss, 1e-300))
                    log_period = 2 * math.pi / omega
                    scale_factor = (
                        math.exp(log_period)
                        if log_period < math.log(float.fromhex("0x1.fffffffffffffp+1023"))
                        else None
                    )
                    # Two harmonic coefficients plus scanned frequency are counted.
                    dsi_bic = model_bic(dsi_residuals, sigma, baseline_params + 3)
                    delta_bic = dsi_bic - baseline_bic
                    supported = delta_bic < -6.0
                    dsi_result = {
                        "available": True,
                        "trend_baseline": baseline_name,
                        "angular_frequency_in_log_x": omega,
                        "log_period": log_period,
                        "discrete_scale_factor_candidate": scale_factor,
                        "sinusoid_amplitude_in_log_y": math.hypot(coeff[-2], coeff[-1]),
                        "residual_variance_fraction_removed": improvement,
                        "baseline_bic": baseline_bic,
                        "log_periodic_model_bic": dsi_bic,
                        "delta_bic_log_periodic_minus_baseline": delta_bic,
                        "frequency_grid_trials": paired(dsi_grid_size),
                        "candidate_status": (
                            "supported_exploratory_candidate"
                            if supported
                            else "not_supported_against_best_nonperiodic_trend"
                        ),
                        "atlas_matches_for_scale_factor": (
                            atlas_matches(scale_factor, tolerance) if scale_factor and supported else []
                        ),
                        "interpretation": "exploratory log-periodic residual candidate; BIC is approximate and frequency-grid multiple testing is not fully corrected",
                    }

    return {
        "name": dataset.get("name", "unnamed_dataset"),
        "x_name": dataset.get("x_name", "x"),
        "y_name": dataset.get("y_name", "y"),
        "x_domain": dataset.get("x_domain", "unspecified"),
        "y_domain": dataset.get("y_domain", "unspecified"),
        "x_unit": dataset.get("x_unit"),
        "y_unit": dataset.get("y_unit"),
        "sample_count": paired(n),
        "input_order": "sorted by x; original source order is not inferred",
        "global_power_law": global_result,
        "two_regime_crossover": piecewise_result,
        "discrete_scale_invariance_candidate": dsi_result,
        "limitations": [
            "Power-law slopes are empirical over the supplied finite observation window.",
            "Optional sigma_log_y weights uncertainty only in log(y); uncertainty in x is not yet modelled.",
            "Breakpoint and log-periodic searches are exploratory and need null models and out-of-sample validation; frequency-grid multiple testing is not fully corrected.",
            "An Atlas numerical match is not an exact symbolic identity or physical causal mechanism.",
        ],
    }


def analyze_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    tolerance = float(payload.get("atlas_relative_tolerance", 1e-4))
    min_points = int(payload.get("min_points_per_regime", 4))
    grid_size = int(payload.get("dsi_grid_size", 512))
    datasets = payload.get("datasets", [])
    if not datasets:
        raise ValueError("at least one dataset is required")
    results = [analyze_dataset(d, tolerance=tolerance, min_points_per_regime=min_points,
                               dsi_grid_size=grid_size) for d in datasets]
    return {
        "schema": "universe.scale-flow-analysis.v1",
        "dataset_count": paired(len(results)),
        "atlas_numeric_reference_count": paired(len(ATLAS_NUMERIC_REFERENCES)),
        "atlas_relative_tolerance": tolerance,
        "regime_minimum_points": paired(min_points),
        "dsi_frequency_grid_size": paired(grid_size),
        "space_time_rule": "Each x/y dataset is fitted independently. Space-time dynamic scaling is tested only when a dataset explicitly supplies paired characteristic length and time values.",
        "statistical_guard": "No p-values, confidence claims or causal mechanisms are inferred by these exploratory fits.",
        "datasets": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("scale_flow_report.json"))
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze_payload(payload)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
