"""Exact finite-support polynomial dependencies between matrix-trace features.

Phase 26 tests whether a candidate trace column is a polynomial of bounded
total degree in previously retained trace columns. Coefficients are exact and
shared across the combined source/target sample support. Such a relation is
local to that finite support, never a universal matrix identity.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations_with_replacement
from math import comb

import affine_ifs_conjugacy as core
from trace_feature_dependencies import insert_feature, new_dependency_basis


def _paired(value):
    return core.paired(value)


def _validate_integer(value, name, minimum, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        upper = f" and <= {maximum}" if maximum is not None else ""
        raise ValueError(f"{name} must be >= {minimum}{upper}")


def _monomial_label(combo, feature_names):
    if not combo:
        return "1"
    powers = Counter(feature_names[index] for index in combo)
    return "*".join(
        name if power == 1 else f"{name}^{power}"
        for name, power in sorted(powers.items())
    )


def _monomial_factors(combo, feature_names):
    if not combo:
        return []
    powers = Counter(feature_names[index] for index in combo)
    return [
        {"feature": name, "power": _paired(power)}
        for name, power in sorted(powers.items())
    ]


def _expected_monomial_count(feature_count, max_degree):
    return sum(
        1 if degree == 0 else comb(feature_count + degree - 1, degree)
        for degree in range(max_degree + 1)
    )


def classify_polynomial_dependency(
    prior_feature_columns,
    prior_feature_names,
    candidate_values,
    candidate_name,
    radical: int,
    max_degree: int = 2,
    max_polynomial_monomials: int = 512,
    min_sample_rows: int = 4,
):
    """Classify a candidate as polynomially dependent, independent, or unresolved.

    Every feature column uses the same row order. Callers comparing two IFS
    families must concatenate source rows and target rows before calling this
    function; coefficients are then shared across both families.

    The exact polynomial basis includes the constant monomial and every
    monomial of total degree <= max_degree. To prevent vacuous interpolation,
    the dependency test is withheld if those monomials span the entire observed
    sample space. A cap or insufficient sample count is unresolved, not
    independent and not negative.
    """
    if not isinstance(prior_feature_columns, (list, tuple)):
        raise TypeError("prior_feature_columns must be a sequence of columns")
    if not isinstance(prior_feature_names, (list, tuple)):
        raise TypeError("prior_feature_names must be a sequence of names")
    if len(prior_feature_columns) != len(prior_feature_names):
        raise ValueError("feature names and columns must have equal lengths")
    if not prior_feature_columns:
        raise ValueError("at least one prior feature is required")
    if any(not isinstance(name, str) or not name for name in prior_feature_names):
        raise ValueError("prior feature names must be nonempty strings")
    if len(set(prior_feature_names)) != len(prior_feature_names):
        raise ValueError("prior feature names must be unique")
    if not isinstance(candidate_name, str) or not candidate_name:
        raise ValueError("candidate_name must be a nonempty string")
    _validate_integer(radical, "radical", 2)
    _validate_integer(max_degree, "max_degree", 1, 3)
    _validate_integer(max_polynomial_monomials, "max_polynomial_monomials", 1)
    _validate_integer(min_sample_rows, "min_sample_rows", 2)

    candidate = list(candidate_values)
    if not candidate:
        raise ValueError("candidate_values must contain at least one sample row")
    row_count = len(candidate)
    columns = [list(column) for column in prior_feature_columns]
    if any(len(column) != row_count for column in columns):
        raise ValueError("all prior and candidate columns must share one sample-row count")

    monomial_count = _expected_monomial_count(len(columns), max_degree)
    common = {
        "candidate_feature": candidate_name,
        "max_total_degree": _paired(max_degree),
        "sample_rows": _paired(row_count),
        "monomial_count": _paired(monomial_count),
        "monomial_cap": _paired(max_polynomial_monomials),
        "universal_identity": False,
        "scope": "combined finite sample support only",
    }
    if row_count < min_sample_rows:
        return {
            **common,
            "status": "unresolved_insufficient_sample_rows",
            "reason": "sample row count is below the configured minimum",
            "minimum_sample_rows": _paired(min_sample_rows),
        }
    if monomial_count > max_polynomial_monomials:
        return {
            **common,
            "status": "unresolved_monomial_cap",
            "reason": "complete monomial basis exceeds the configured cap",
        }

    monomials = []
    for degree in range(max_degree + 1):
        combos = [()] if degree == 0 else list(
            combinations_with_replacement(range(len(columns)), degree)
        )
        for combo in combos:
            name = _monomial_label(combo, prior_feature_names)
            values = []
            for row in range(row_count):
                value = core.O
                for index in combo:
                    value = core.mul(value, columns[index][row], radical)
                values.append(value)
            monomials.append({
                "name": name,
                "degree": degree,
                "factors": _monomial_factors(combo, prior_feature_names),
                "values": values,
            })

    basis = new_dependency_basis()
    monomial_values = {}
    for monomial in monomials:
        monomial_values[monomial["name"]] = monomial["values"]
        insert_feature(
            basis, f"monomial:{monomial['name']}", monomial["values"], radical
        )
    monomial_rank = len(basis)
    common["monomial_rank"] = _paired(monomial_rank)

    if monomial_rank >= row_count:
        return {
            **common,
            "status": "unresolved_monomial_span_saturates_samples",
            "reason": (
                "the exact monomial columns span every observed sample row; "
                "any candidate would then appear dependent by finite interpolation"
            ),
            "monomial_span_saturated": True,
        }

    independent, relation = insert_feature(
        basis,
        f"candidate:{candidate_name}",
        candidate,
        radical,
        include_exact=True,
    )
    if independent:
        return {
            **common,
            "status": "independent_on_finite_support",
            "monomial_span_saturated": False,
            "polynomial_dependency_found": False,
            "logical_status": (
                "No polynomial expression was found within the configured "
                "degree and monomial cap on this finite support; higher degree "
                "and other supports remain untested."
            ),
        }

    exact_terms = relation.pop("exact_equation_terms")
    values_by_name = {
        f"monomial:{name}": values for name, values in monomial_values.items()
    }
    values_by_name[f"candidate:{candidate_name}"] = candidate
    exact_zero_rows = 0
    for row in range(row_count):
        residual = core.Z
        for term in exact_terms:
            residual = core.add(
                residual,
                core.mul(term["coefficient"], values_by_name[term["feature"]][row], radical),
            )
        if not core.zero(residual):
            raise ArithmeticError(
                f"Phase 26 polynomial certificate failed exact verification at sample row {row}"
            )
        exact_zero_rows += 1

    monomial_by_name = {item["name"]: item for item in monomials}
    polynomial_terms = []
    for term in relation["equation_terms"]:
        feature = term["feature"]
        if feature.startswith("candidate:"):
            descriptor = {
                "monomial": candidate_name,
                "factors": [{"feature": candidate_name, "power": _paired(1)}],
                "degree": _paired(1),
                "candidate_term": True,
            }
        else:
            monomial_name = feature[len("monomial:"):]
            item = monomial_by_name[monomial_name]
            descriptor = {
                "monomial": monomial_name,
                "factors": item["factors"],
                "degree": _paired(item["degree"]),
                "candidate_term": False,
            }
        polynomial_terms.append({
            "coefficient": term["coefficient"],
            **descriptor,
        })

    return {
        **common,
        "status": "polynomially_dependent_on_finite_support",
        "monomial_span_saturated": False,
        "polynomial_dependency_found": True,
        "equation": relation["equation"],
        "polynomial_terms": polynomial_terms,
        "certificate": {
            "coefficient_field_radicand": _paired(radical),
            "sample_rows_checked": _paired(row_count),
            "exact_zero_rows": _paired(exact_zero_rows),
            "all_residuals_exactly_zero": exact_zero_rows == row_count,
            "verification": (
                "Every source and target row in the supplied combined support "
                "was recomputed exactly from the displayed polynomial terms."
            ),
        },
        "logical_status": (
            "This polynomial relation is certified only on the combined finite "
            "sample support. It is not a universal trace identity and must not "
            "be extrapolated to unobserved matrix pairs or arbitrary matrices."
        ),
    }
