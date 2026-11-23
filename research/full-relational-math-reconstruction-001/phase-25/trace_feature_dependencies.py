"""Exact finite-family trace-feature dependence and safe edge-label reduction.

Universal cyclic-trace identities are separated from dependencies detected
only on the combined active edge support of one source/target comparison.
"""
from __future__ import annotations

from fractions import Fraction

import affine_ifs_conjugacy as core


BASELINE_WORDS = ("01", "001", "011", "0101", "0011")
COMMUTATOR_IDENTITY = {
    "left": "tr([A,B]^2)",
    "right_coefficients": {
        "0101": "2",
        "0011": "-2",
    },
    "equation": "tr([A,B]^2) - 2 tr(ABAB) + 2 tr(AABB) = 0",
}


def compress_phase21_edges(edges, radical: int):
    """Remove the universally redundant commutator-square coordinate.

    For any square A,B, cyclicity of trace gives
    tr((AB-BA)^2)=2 tr(ABAB)-2 tr(AABB).
    The six Phase 21 fields are checked exactly before retaining the five
    binary-word coordinates.
    """
    compressed = []
    for i, row in enumerate(edges):
        out_row = []
        for j, edge in enumerate(row):
            if len(edge) != 6:
                raise ValueError(f"Phase 21 edge label ({i},{j}) must contain six exact traces")
            expected = core.mul(core.q(2), core.sub(edge[3], edge[4]), radical)
            if edge[5] != expected:
                raise ArithmeticError(
                    f"Phase 21 commutator trace identity failed at ordered pair ({i},{j})"
                )
            out_row.append(tuple(edge[:5]))
        compressed.append(out_row)
    return compressed


def feature_vector(edges, ordered_pairs, feature_index):
    values = []
    for i, j in ordered_pairs:
        label = edges[i][j]
        if feature_index >= len(label):
            raise ValueError(
                f"missing prior trace feature at ordered pair ({i},{j}); "
                "active-pair supports must be nested across refinement tiers"
            )
        values.append(label[feature_index])
    return values


def _subtract_expression(left, factor, right, radical):
    result = dict(left)
    for name, coefficient in right.items():
        product = core.mul(factor, coefficient, radical)
        result[name] = core.sub(result.get(name, core.Z), product)
        if core.zero(result[name]):
            del result[name]
    return result


def new_dependency_basis():
    return []


def insert_feature(basis, feature_name: str, values, radical: int):
    """Insert a feature column into exact row-echelon form.

    Returns (independent, relation). For a dependent candidate, relation is
    an exact equation candidate + sum(c_i * prior_i) = 0 over every supplied
    sample row. Coefficients are field-exact and common to all rows.
    """
    if isinstance(radical, bool) or not isinstance(radical, int) or radical < 2:
        raise ValueError("radical must be an integer >= 2")
    vector = list(values)
    if not vector:
        raise ValueError("dependency feature vector must contain at least one sample row")
    if basis and len(vector) != len(basis[0]["vector"]):
        raise ValueError("all dependency feature vectors must share one sample-row count")
    expression = {feature_name: core.O}
    for entry in basis:
        factor = vector[entry["pivot"]]
        if core.zero(factor):
            continue
        vector = [
            core.sub(value, core.mul(factor, basis_value, radical))
            for value, basis_value in zip(vector, entry["vector"])
        ]
        expression = _subtract_expression(
            expression, factor, entry["expression"], radical
        )

    pivot = next((i for i, value in enumerate(vector) if not core.zero(value)), None)
    if pivot is None:
        relation = [
            {"feature": name, "coefficient": core.fmt(value)}
            for name, value in sorted(expression.items())
        ]
        return False, {
            "candidate_feature": feature_name,
            "equation_terms": relation,
            "equation": " + ".join(
                f"({term['coefficient']})*{term['feature']}"
                for term in relation
            ) + " = 0",
            "scope": "exact dependency on the combined sample rows supplied to this comparison",
            "logical_status": (
                "Safe to omit only within this finite comparison and this active "
                "ordered-pair support; not asserted as a universal matrix identity."
            ),
        }

    pivot_value = vector[pivot]
    normalized_vector = [
        core.div(value, pivot_value, radical) for value in vector
    ]
    normalized_expression = {
        name: core.div(value, pivot_value, radical)
        for name, value in expression.items()
    }
    basis.append({
        "pivot": pivot,
        "vector": normalized_vector,
        "expression": normalized_expression,
        "feature": feature_name,
    })
    return True, None


def dependency_basis_from_edges(
    source_edges,
    target_edges,
    source_pairs,
    target_pairs,
    applied_words,
    radical: int,
):
    """Build a common exact basis from currently available earlier features."""
    basis = new_dependency_basis()
    dependencies = []
    samples = [
        ("source", source_edges, source_pairs),
        ("target", target_edges, target_pairs),
    ]
    feature_names = list(BASELINE_WORDS) + list(applied_words)
    for feature_index, word in enumerate(feature_names):
        values = []
        for _side, edges, pairs in samples:
            values.extend(feature_vector(edges, pairs, feature_index))
        independent, relation = insert_feature(
            basis, f"trace:{word}", values, radical
        )
        if not independent:
            dependencies.append({
                "stage": "prior_feature_basis",
                "feature": word,
                **relation,
            })
    return basis, dependencies


def reduce_candidate_words(
    basis,
    candidate_values,
    candidate_words,
    radical: int,
):
    """Classify candidate word columns against one common exact basis."""
    retained = []
    dependencies = []
    for word in candidate_words:
        values = candidate_values[word]
        independent, relation = insert_feature(
            basis, f"trace:{word}", values, radical
        )
        if independent:
            retained.append(word)
        else:
            dependencies.append(relation)
    return retained, dependencies
