"""Compare dimensionless groups and bounded monomial relations with numeric Atlas references."""
from __future__ import annotations
import argparse
import itertools
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

PHASE08 = Path(__file__).resolve().parents[1] / "phase-08"
if str(PHASE08) not in sys.path:
    sys.path.insert(0, str(PHASE08))
try:
    from relation_discovery import REFS as ATLAS_NUMERIC_REFERENCES
except ImportError as exc:
    raise RuntimeError("Phase 08 relation_discovery.py is required beside Phase 10") from exc


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


@dataclass(frozen=True)
class PiEntry:
    name: str
    value: float
    expression: str
    provenance: str


@dataclass(frozen=True)
class BasisSet:
    basis_id: str
    basis_type: str
    groups: tuple[PiEntry, ...]
    omitted_group_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class Candidate:
    basis_id: str
    basis_type: str
    formula: str
    exponents: tuple[int, ...]
    value: float | None
    matches: tuple[dict[str, Any], ...]
    numeric_status: str


def _parse_basis(basis_id: str, basis_type: str, raw_groups: Sequence[Mapping[str, Any]], provenance: str) -> BasisSet:
    groups = []
    omitted = []
    for index, group in enumerate(raw_groups):
        name = f"G{group.get('basis_id', paired(index + 1))}"
        numeric_value = group.get("numeric_value_secondary")
        if numeric_value is None:
            omitted.append(name)
            continue
        groups.append(PiEntry(name, float(numeric_value), str(group.get("expression", "")), provenance))
    if not raw_groups:
        raise ValueError(f"basis {basis_id} contains no Pi group entries")
    if any(not math.isfinite(group.value) for group in groups):
        raise ValueError(f"basis {basis_id} contains a non-finite dimensionless value")
    return BasisSet(basis_id, basis_type, tuple(groups), tuple(omitted))


def load_basis_sets(payload: Mapping[str, Any]) -> tuple[BasisSet, ...]:
    result = []
    canonical = payload.get("canonical_basis", [])
    if canonical:
        result.append(_parse_basis("canonical", "canonical", canonical, "canonical_basis"))
    for alternative in payload.get("alternative_basis_examples", []):
        basis_id = str(alternative.get("basis_id", "alternative"))
        result.append(_parse_basis(basis_id, "alternative", alternative.get("groups", []), f"alternative_basis:{basis_id}"))
    if not result:
        raise ValueError("input report contains no Pi bases")
    return tuple(result)


def atlas_matches(value: float, tolerance: float) -> tuple[dict[str, Any], ...]:
    matches = []
    for reference in ATLAS_NUMERIC_REFERENCES:
        error = abs(value - reference.value) / abs(reference.value) if reference.value else abs(value)
        if error <= tolerance:
            matches.append({
                "atlas_key": reference.key,
                "symbol": reference.symbol,
                "exact_expression": reference.expression,
                "family": reference.family,
                "relative_error_numeric_secondary": error,
            })
    return tuple(sorted(matches, key=lambda item: item["relative_error_numeric_secondary"]))


def search_basis(basis: BasisSet, *, tolerance: float = 1e-4, max_terms: int = 3,
                 exponent_bound: int = 2, max_candidates: int = 20000) -> list[Candidate]:
    if not 1 <= max_terms <= len(basis.groups):
        raise ValueError("max_terms must be between 1 and the number of groups in the basis")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be positive and finite")
    if exponent_bound < 1 or max_candidates < 1:
        raise ValueError("exponent_bound and max_candidates must be positive")
    candidates = []
    n = len(basis.groups)
    for count in range(1, max_terms + 1):
        for indices in itertools.combinations(range(n), count):
            for selected in itertools.product(range(-exponent_bound, exponent_bound + 1), repeat=count):
                if any(power == 0 for power in selected):
                    continue
                exponents = [0] * n
                for index, power in zip(indices, selected):
                    exponents[index] = power
                selected_groups = [(group, power) for group, power in zip(basis.groups, exponents) if power]
                zero_denominator = any(group.value == 0 and power < 0 for group, power in selected_groups)
                zero_numerator = any(group.value == 0 and power > 0 for group, power in selected_groups)
                if zero_denominator:
                    value = None
                    numeric_status = "undefined_zero_denominator"
                    matches = ()
                elif zero_numerator:
                    value = 0.0
                    numeric_status = "evaluated_finite_float"
                    matches = atlas_matches(value, tolerance)
                else:
                    log_value = sum(power * math.log(abs(group.value)) for group, power in selected_groups)
                    sign = -1.0 if sum(power for group, power in selected_groups if group.value < 0) % 2 else 1.0
                    min_log = math.log(float.fromhex("0x0.0000000000001p-1022"))
                    max_log = math.log(float.fromhex("0x1.fffffffffffffp+1023"))
                    if min_log <= log_value <= max_log:
                        value = sign * math.exp(log_value)
                        numeric_status = "evaluated_finite_float"
                        matches = atlas_matches(value, tolerance)
                    else:
                        value = None
                        numeric_status = "outside_finite_float_range"
                        matches = ()
                parts = [group.name if power == 1 else f"{group.name}^{power}"
                         for group, power in zip(basis.groups, exponents) if power]
                candidates.append(Candidate(basis.basis_id, basis.basis_type, " * ".join(parts),
                                            tuple(exponents), value, matches, numeric_status))
                if len(candidates) > max_candidates:
                    raise ValueError(f"candidate cap exceeded ({max_candidates}); reduce max_terms or exponent_bound")
    return sorted(candidates, key=lambda item: (
        not bool(item.matches),
        item.matches[0]["relative_error_numeric_secondary"] if item.matches else math.inf,
        item.basis_id, item.formula))


def compare_report(payload: Mapping[str, Any], *, tolerance: float = 1e-4, max_terms: int = 3,
                   exponent_bound: int = 2, max_candidates: int = 20000) -> dict[str, Any]:
    bases = load_basis_sets(payload)
    basis_results = []
    total = 0
    for basis in bases:
        candidates = search_basis(basis, tolerance=tolerance, max_terms=min(max_terms, len(basis.groups)),
                                  exponent_bound=exponent_bound, max_candidates=max_candidates) if basis.groups else []
        total += len(candidates)
        completeness = ("no_numeric_values" if not basis.groups else
                        ("partial_numeric_projection" if basis.omitted_group_names else "complete_numeric_basis"))
        basis_results.append({
            "basis_id": basis.basis_id,
            "basis_type": basis.basis_type,
            "basis_completeness": completeness,
            "omitted_non_numeric_groups": list(basis.omitted_group_names),
            "input_group_count": paired(len(basis.groups) + len(basis.omitted_group_names)),
            "numerically_evaluable_group_count": paired(len(basis.groups)),
            "input_groups": [{"name": g.name, "value_numeric_secondary": g.value,
                              "source_expression": g.expression, "provenance": g.provenance}
                             for g in basis.groups],
            "candidate_count": paired(len(candidates)),
            "matched_candidate_count": paired(sum(bool(c.matches) for c in candidates)),
            "candidates": [{
                "candidate_id": paired(i + 1),
                "formula": c.formula,
                "exponent_vector": {g.name: e for g, e in zip(basis.groups, c.exponents) if e},
                "value_numeric_secondary": c.value,
                "numeric_evaluation_status": c.numeric_status,
                "matches": list(c.matches),
                "status": "derived_relation_candidate",
                "interpretation_guard": "atlas_match_is_not_symbolic_identity_or_causation",
            } for i, c in enumerate(candidates)],
        })
    return {
        "schema": "universe.atlas-relation-comparison.v1",
        "basis_count": paired(len(bases)),
        "total_candidate_count": paired(total),
        "numeric_atlas_reference_count": paired(len(ATLAS_NUMERIC_REFERENCES)),
        "search": {"relative_tolerance": tolerance, "max_nonzero_terms": paired(max_terms),
                   "max_abs_integer_exponent": paired(exponent_bound),
                   "max_candidates_per_basis": paired(max_candidates)},
        "basis_separation_rule": "Each canonical or alternative Pi basis is searched independently. Groups from different bases are never combined.",
        "missing_numeric_rule": "If a Pi group has no numeric value, it is retained in the report as omitted and the search is labelled as a partial numeric projection of that basis. A basis with no numeric values remains listed but has no numeric candidates.",
        "scope_note": "Only the numeric machine-readable Atlas subset is compared here. Structural Atlas families require dedicated comparators.",
        "statistics_note": "Matches are an uncorrected exploratory screen. Tolerance and the number of tested candidates are reported; no significance or causal claim is inferred.",
        "numeric_range_note": "Candidates outside finite floating-point range are retained symbolically with numeric value null. Negative groups use integer-power sign rules; a zero group with a negative exponent is retained but marked undefined.",
        "basis_results": basis_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Phase 09 Buckingham-Pi JSON report")
    parser.add_argument("--output", type=Path, default=Path("atlas_comparison.json"))
    parser.add_argument("--tolerance", type=float, default=1e-4)
    parser.add_argument("--max-terms", type=int, default=3)
    parser.add_argument("--exponent-bound", type=int, default=2)
    parser.add_argument("--max-candidates", type=int, default=20000)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = compare_report(payload, tolerance=args.tolerance, max_terms=args.max_terms,
                            exponent_bound=args.exponent_bound, max_candidates=args.max_candidates)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
