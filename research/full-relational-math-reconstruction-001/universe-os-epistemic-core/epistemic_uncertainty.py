"""Uncertainty propagation, evidence independence and the evidence gate.

Issue #7 §17.1/§17.2/§18.9/§18.10.  Correlations are preserved, unknown
correlations are not silently replaced by independence, Monte Carlo is
deterministic with a recorded seed, caches are invalidated by dependency
version, and a draft calculation never passes a full-calculation gate.

The six epistemic axes are rubric statuses.  They never enter a Jacobian, a
covariance matrix, or a multiplied "confidence score".
"""

from __future__ import annotations

import math
import random
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from epistemic_types import (
    AXES,
    AXIS_LEVELS,
    AXIS_MISSING_REASONS,
    EPISTEMIC_VERSION,
    EpistemicContractError,
    digest,
    frozen,
    require,
)

METHODS: Sequence[str] = ("delta", "covariance", "interval", "monte_carlo")

AXIS_RANK = {level: index for index, level in enumerate(AXIS_LEVELS)}

AXIS_RUBRICS: Dict[str, Dict[str, Any]] = {
    "source_reliability": {
        "criteria": [
            "traceable provenance", "primary data available", "method documented",
            "calibration documented", "reproducibility", "declared limitations",
        ],
        "insufficient_reputation_alone": True,
    },
    "measurement_uncertainty": {
        "criteria": [
            "instrument", "resolution", "calibration", "sampling",
            "detection_limit", "covariance", "inversion procedure",
        ],
        "not_substituted_by_source_reliability": True,
    },
    "interpretation_confidence": {
        "criteria": [
            "alternative interpretations listed", "discriminating observations",
            "identifiability", "independent checks",
        ],
        "not_equal_to_author_confidence": True,
    },
    "coverage_completeness": {
        "criteria": [
            "declared spatial/temporal/parametric target", "covered fraction",
            "gaps", "blind spots",
        ],
        "not_derived_from_record_count": True,
    },
    "model_validity": {
        "criteria": [
            "verification", "validation", "applicability domain",
            "independent holdout", "residuals", "sensitivity",
            "model discrepancy", "known failure modes",
        ],
    },
    "evidence_connectivity": {
        "criteria": [
            "shared primary datasets", "shared calibrations", "shared transforms",
            "shared models", "shared assumptions", "cycles",
        ],
        "structural_not_a_score": True,
    },
}


def assess_axis(
    graph: Any,
    axis: str,
    *,
    level: str,
    reasons: Sequence[str],
    evidence: Sequence[str],
    author: str,
    independent: bool = False,
    missing_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Store author and independent assessments as separate records (18.9)."""
    require(axis in AXES, f"unknown axis {axis!r}")
    require(level in AXIS_LEVELS, f"unknown axis level {level!r}")
    rubric = AXIS_RUBRICS[axis]
    if level in ("weak", "moderate", "strong", "verified_within_declared_tolerance"):
        require(bool(reasons) and bool(evidence),
                f"level {level!r} needs explicit reasons and evidence")
    if level in ("unknown", "not_assessed", "not_applicable"):
        require(missing_reason in AXIS_MISSING_REASONS or missing_reason == "not_relevant",
                "an unassessed axis needs a formal reason")
    for criterion in rubric["criteria"]:
        pass  # rubric criteria are reported, not silently satisfied
    assessment = {
        "assessment_id": f"AXIS_{axis}_{'IND' if independent else 'AUTHOR'}_{len(graph.events()) + 1:06d}",
        "axis": axis,
        "level": level,
        "reasons": list(reasons),
        "evidence": list(evidence),
        "rubric": list(rubric["criteria"]),
        "rubric_version": EPISTEMIC_VERSION,
        "independent": bool(independent),
        "author": author,
        "missing_reason": missing_reason,
        "numeric_score": None,
    }
    graph.record_event(
        "axis_assessed" if not independent else "axis_independently_verified",
        {"axis": axis, "level": level, "author": author},
        actor=author,
    )
    return assessment


def assert_axes_not_numerical(axis_assessments: Dict[str, Any]) -> bool:
    require(set(axis_assessments) <= set(AXES), "unknown axis in assessment")
    require(not any("numeric_score" in a and a["numeric_score"] is not None
                    for a in axis_assessments.values()),
            "epistemic axes must not be converted to numbers")
    return True


def independent_bases(
    graph: Any,
    claim_id: str,
    *,
    method_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Collapse publications that reuse the same primary dataset (17.1)."""
    from epistemic_claims import PRIMARY_NODE_TYPES, belief_structure

    structure = belief_structure(graph, claim_id)
    bases = set(structure["independent_primary_bases"])
    result: Dict[str, Any] = {
        "claim_id": claim_id,
        "primary_bases": sorted(bases),
        "count": None,
        "status": "not_evaluable",
        "structural_only": True,
    }
    if method_id is None:
        result["reason"] = "no formal method for effective independent count"
        return result
    require(method_id == "shared_primary_datasets_v1", f"unknown method {method_id!r}")
    result["count"] = len(bases)
    result["status"] = "evaluated"
    result["method_id"] = method_id
    result["graph_digest"] = graph.graph_digest()
    return result


class ComputationCache:
    """Version-aware cache: a changed dependency removes only affected entries."""

    def __init__(self) -> None:
        self._entries: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str, graph: Any) -> Optional[Dict[str, Any]]:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if not self.is_current(entry, graph):
            del self._entries[key]
            return None
        return frozen(entry["result"])

    def put(self, key: str, graph: Any, result: Dict[str, Any],
            dependencies: Sequence[str]) -> None:
        self._entries[key] = {
            "result": frozen(result),
            "dependencies": {
                node_id: [v["version"] for v in graph.versions(node_id)]
                for node_id in dependencies
            },
        }

    def is_current(self, entry: Dict[str, Any], graph: Any) -> bool:
        for node_id, versions in entry["dependencies"].items():
            actual = [v["version"] for v in graph.versions(node_id)]
            if actual != versions:
                return False
        return True

    def stale_keys(self, graph: Any) -> List[str]:
        return [key for key, entry in self._entries.items()
                if not self.is_current(entry, graph)]

    def invalidate(self, node_id: str) -> int:
        doomed = [key for key, e in self._entries.items() if node_id in e["dependencies"]]
        for key in doomed:
            del self._entries[key]
        return len(doomed)

    def clear(self) -> None:
        self._entries.clear()

    @property
    def entries(self) -> int:
        return len(self._entries)


def _cholesky(matrix: List[List[float]]) -> List[List[float]]:
    n = len(matrix)
    lower = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            total = sum(lower[i][k] * lower[j][k] for k in range(j))
            if i == j:
                pivot = matrix[i][i] - total
                require(pivot > 0, "covariance matrix is not positive definite")
                lower[i][i] = math.sqrt(pivot)
            else:
                lower[i][j] = (matrix[i][j] - total) / lower[j][j]
    return lower


def covariance_matrix(
    inputs: Dict[str, Dict[str, Any]],
    *,
    assume_independent: bool = False,
    assumption_reason: Optional[str] = None,
) -> Tuple[List[str], List[List[float]], bool]:
    """Build covariance; unknown correlations stay unresolved by default."""
    names = sorted(inputs)
    approximated = False
    matrix = [[0.0] * len(names) for _ in names]
    for i, name in enumerate(names):
        spec = inputs[name]
        require("value" in spec and "sigma" in spec,
                f"input {name} needs value and sigma")
        sigma = float(spec["sigma"])
        require(sigma >= 0, f"input {name} has a negative sigma")
        matrix[i][i] = sigma * sigma
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            left, right = names[i], names[j]
            rho = inputs[left].get("correlation", {}).get(right)
            if rho is None:
                rho = inputs[right].get("correlation", {}).get(left)
            if rho is None and assume_independent:
                require(bool(assumption_reason),
                        "assuming independence requires an explicit reason")
                rho = 0.0
                approximated = True
            require(rho is not None,
                    f"correlation between {left} and {right} is unknown; "
                    "do not assume independence silently")
            require(-1.0 <= float(rho) <= 1.0, "correlation must be in [-1, 1]")
            matrix[i][j] = matrix[j][i] = (
                float(rho) * math.sqrt(matrix[i][i] * matrix[j][j])
            )
    return names, matrix, approximated


class UncertaintyEngine:
    """Deterministic propagation with full traces and disclosure of drafts."""

    def __init__(self, cache: Optional[ComputationCache] = None) -> None:
        self.cache = cache or ComputationCache()
        self._traces: Dict[str, Dict[str, Any]] = {}

    def propagate(
        self,
        graph: Any,
        result_id: str,
        *,
        inputs: Dict[str, Dict[str, Any]],
        coefficients: Sequence[float],
        method: str,
        dependencies: Sequence[str] = (),
        domain: Optional[Dict[str, Any]] = None,
        assume_independent: bool = False,
        assumption_reason: Optional[str] = None,
        seed: Optional[int] = None,
        samples: Optional[int] = None,
        algorithm: Optional[str] = None,
        library_versions: Optional[Dict[str, str]] = None,
        function: Optional[Callable[[Dict[str, float]], float]] = None,
        requires_full: bool = False,
        code_version: str = EPISTEMIC_VERSION,
    ) -> Dict[str, Any]:
        require(method in METHODS, f"unknown propagation method {method!r}")
        require(bool(inputs), "propagation needs inputs")
        require(len(coefficients) == len(inputs), "one coefficient per input is required")
        names, matrix, approximated = covariance_matrix(
            inputs,
            assume_independent=assume_independent,
            assumption_reason=assumption_reason,
        )
        key = digest({
            "result_id": result_id,
            "inputs": inputs,
            "coefficients": list(coefficients),
            "method": method,
            "domain": domain,
            "seed": seed,
            "samples": samples,
            "algorithm": algorithm,
            "library_versions": library_versions,
            "function": repr(function),
            "code_version": code_version,
        })
        cached = self.cache.get(key, graph)
        if cached is not None:
            return cached

        values = [float(inputs[name]["value"]) for name in names]
        if method in ("delta", "covariance"):
            variance = 0.0
            for i, ci in enumerate(coefficients):
                for j, cj in enumerate(coefficients):
                    variance += float(ci) * matrix[i][j] * float(cj)
            variance = max(0.0, variance)
            result_value = sum(c * x for c, x in zip(coefficients, values))
            result: Dict[str, Any] = {
                "value": result_value,
                "variance": variance,
                "sigma": math.sqrt(variance),
            }
            if method == "covariance":
                result["input_covariance"] = frozen(matrix)
                result["coefficients"] = list(coefficients)
        elif method == "interval":
            lower = upper = 0.0
            for name, coefficient in zip(names, coefficients):
                spec = inputs[name]
                interval = spec.get("interval")
                if interval is None:
                    sigma = float(spec["sigma"])
                    interval = [float(spec["value"]) - 2 * sigma,
                                float(spec["value"]) + 2 * sigma]
                candidates = [float(coefficient) * bound for bound in interval]
                lower += min(candidates)
                upper += max(candidates)
            result = {"interval": [lower, upper], "value": (lower + upper) / 2.0}
        else:
            require(seed is not None and samples is not None and samples > 0,
                    "Monte Carlo needs a seed and a positive sample count")
            require(bool(algorithm) and bool(library_versions),
                    "Monte Carlo needs algorithm and library versions recorded")
            evaluate = function or (lambda vector: sum(
                c * vector[name] for c, name in zip(coefficients, names)))
            lower_matrix = _cholesky(matrix)
            rng = random.Random(seed)
            draws: List[float] = []
            for _ in range(samples):
                z = [rng.gauss(0.0, 1.0) for _ in names]
                vector = {}
                for i, name in enumerate(names):
                    vector[name] = values[i] + sum(lower_matrix[i][k] * z[k]
                                                   for k in range(i + 1))
                draws.append(float(evaluate(vector)))
            draws.sort()
            mean = sum(draws) / len(draws)
            variance = sum((d - mean) ** 2 for d in draws) / len(draws)
            result = {
                "value": mean,
                "sigma": math.sqrt(variance),
                "p025": draws[int(0.025 * (len(draws) - 1))],
                "p975": draws[int(0.975 * (len(draws) - 1))],
                "seed": seed,
                "samples": samples,
                "algorithm": algorithm,
                "library_versions": frozen(library_versions),
            }

        approximation = approximated or method in ("interval", "monte_carlo") or bool(
            (domain or {}).get("reduced_scope"))
        if requires_full and approximation:
            raise EpistemicContractError(
                "draft/approximate calculation cannot pass a full-calculation gate"
            )
        trace = {
            "result_id": result_id,
            "method": method,
            "inputs": frozen(inputs),
            "input_covariance": frozen(matrix),
            "coefficients": list(coefficients),
            "domain": frozen(domain or {}),
            "result": frozen(result),
            "approximation_disclosed": approximation,
            "validated": not approximation,
            "assume_independent": bool(assume_independent),
            "assumption_reason": assumption_reason,
            "code_version": code_version,
            "cache_key": key,
            "dependency_nodes": list(dependencies),
        }
        self.cache.put(key, graph, trace, dependencies)
        self._traces[result_id] = frozen(trace)
        return frozen(trace)

    def trace(self, result_id: str) -> Optional[Dict[str, Any]]:
        trace = self._traces.get(result_id)
        return frozen(trace) if trace else None

    @property
    def validated_traces(self) -> int:
        return sum(1 for t in self._traces.values() if t["validated"] is True)


def assert_axes_excluded_from_model(axes: Dict[str, Any], coefficients: Sequence[str]) -> bool:
    require(set(axes) <= set(AXES), "unknown epistemic axis")
    forbidden = set(axes) & set(coefficients)
    require(not forbidden,
            f"epistemic axes must not enter a numerical model: {sorted(forbidden)}")
    return True


def evidence_gate(
    graph: Any,
    claim_id: str,
    *,
    axis_assessments: Dict[str, Any],
    independent_axis_assessments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Weakest necessary link plus dependencies; no aggregate percentage."""
    assert_axes_not_numerical(axis_assessments)
    require(set(axis_assessments) == set(AXES),
            "all six axes must be assessed, even if as unknown")
    levels = {axis: assessment["level"] for axis, assessment in axis_assessments.items()}
    limiting = min(AXES, key=lambda axis: (AXIS_RANK[levels[axis]], AXES.index(axis)))
    conflicts = [
        c["node_id"] for c in graph.nodes("Conflict")
        if claim_id in c["payload"].get("disputed_claims", [])
        and c["payload"]["status"] in ("open", "under_review", "partially_resolved")
    ]
    from epistemic_claims import belief_structure
    structure = belief_structure(graph, claim_id)
    status = levels[limiting]
    if conflicts:
        status = "disputed"
    if status in ("unknown", "not_assessed", "weak"):
        status = "insufficient_grounds"
    if independent_axis_assessments:
        assert_axes_not_numerical(independent_axis_assessments)
    return {
        "claim_id": claim_id,
        "status": status,
        "limiting_axis": limiting,
        "axis_levels": levels,
        "weakest_necessary_link": levels[limiting],
        "open_conflicts": conflicts,
        "critical_dependencies": structure["critical_nodes"],
        "support_chains": len(structure["support_chains"]),
        "quantitative_score": None,
        "rule_version": EPISTEMIC_VERSION,
    }
