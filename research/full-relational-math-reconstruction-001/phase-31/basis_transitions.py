"""Exact basis transitions for the bounded trace-relation filtration.

Phase 31 converts the finite R[L,D] slices from Phase 30 into canonical
rational row-reduced bases and exposes exact inclusion, intersection, quotient
complement and adapted-basis transition matrices. All linear algebra is over Q.
No infinite recurrence, stabilization or T-ideal minimal-generator claim is
made.
"""
from __future__ import annotations

from fractions import Fraction

import relation_filtration as phase30
import trace_ideal_closure as phase29


def _decode(value, name: str) -> int:
    return phase29._integer(value, name, minimum=0)


def _poly(entry):
    return phase29._poly_from_terms(entry["trace_terms"])


def _canonical_rref(polynomials):
    """Return the unique sparse RREF basis for a row space and lex column order."""
    rows = [
        {key: Fraction(value) for key, value in poly.items() if value}
        for poly in polynomials
        if poly
    ]
    columns = sorted({column for row in rows for column in row})
    pivot_row = 0
    pivot_columns = []

    for column in columns:
        selected = next(
            (index for index in range(pivot_row, len(rows)) if rows[index].get(column)),
            None,
        )
        if selected is None:
            continue
        rows[pivot_row], rows[selected] = rows[selected], rows[pivot_row]
        pivot_value = rows[pivot_row][column]
        rows[pivot_row] = {
            key: value / pivot_value
            for key, value in rows[pivot_row].items()
            if value
        }

        # Reduced, rather than merely echelon, form makes the basis independent
        # of the order in which a spanning family was presented.
        pivot = rows[pivot_row]
        for index in range(len(rows)):
            if index == pivot_row:
                continue
            factor = rows[index].get(column, Fraction(0))
            if not factor:
                continue
            updated = dict(rows[index])
            for key, value in pivot.items():
                coefficient = updated.get(key, Fraction(0)) - factor * value
                if coefficient:
                    updated[key] = coefficient
                else:
                    updated.pop(key, None)
            rows[index] = updated

        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == len(rows):
            break

    return [
        {"pivot": pivot_columns[index], "vector": rows[index]}
        for index in range(pivot_row)
    ]


def _coordinates_in_rref(polynomial, basis):
    """Coordinates of a vector in a reduced row-echelon basis, with exact check."""
    coordinates = [
        polynomial.get(row["pivot"], Fraction(0))
        for row in basis
    ]
    residual = dict(polynomial)
    for coefficient, row in zip(coordinates, basis):
        if not coefficient:
            continue
        for monomial, value in row["vector"].items():
            updated = residual.get(monomial, Fraction(0)) - coefficient * value
            if updated:
                residual[monomial] = updated
            else:
                residual.pop(monomial, None)
    if residual:
        raise ArithmeticError("a claimed subspace vector does not reconstruct in the target basis")
    return coordinates


def _rref_dense(matrix, ncols=None):
    if ncols is None:
        ncols = len(matrix[0]) if matrix else 0
    rows = [[Fraction(value) for value in row] for row in matrix]
    if any(len(row) != ncols for row in rows):
        raise ValueError("dense matrix rows must all have the declared column count")
    pivot_columns = []
    pivot_row = 0
    for column in range(ncols):
        selected = next(
            (index for index in range(pivot_row, len(rows)) if rows[index][column]),
            None,
        )
        if selected is None:
            continue
        rows[pivot_row], rows[selected] = rows[selected], rows[pivot_row]
        pivot_value = rows[pivot_row][column]
        rows[pivot_row] = [value / pivot_value for value in rows[pivot_row]]
        for index in range(len(rows)):
            if index == pivot_row:
                continue
            factor = rows[index][column]
            if factor:
                rows[index] = [
                    left - factor * right
                    for left, right in zip(rows[index], rows[pivot_row])
                ]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == len(rows):
            break
    return rows, pivot_columns


def _matrix_rank(matrix, ncols=None):
    return len(_rref_dense(matrix, ncols)[1])


def _nullspace(matrix, ncols):
    reduced, pivots = _rref_dense(matrix, ncols)
    free_columns = [column for column in range(ncols) if column not in pivots]
    result = []
    for free in free_columns:
        vector = [Fraction(0) for _ in range(ncols)]
        vector[free] = Fraction(1)
        for row_index, pivot in enumerate(pivots):
            vector[pivot] = -reduced[row_index][free]
        result.append(vector)
    return result


def _matrix_inverse(matrix):
    size = len(matrix)
    if any(len(row) != size for row in matrix):
        raise ValueError("only square matrices can be inverted")
    if size == 0:
        return []
    augmented = [
        [Fraction(value) for value in row]
        + [Fraction(int(row_index == column)) for column in range(size)]
        for row_index, row in enumerate(matrix)
    ]
    reduced, pivots = _rref_dense(augmented, 2 * size)
    if pivots[:size] != list(range(size)):
        raise ArithmeticError("adapted basis transition matrix is singular")
    inverse = [row[size:] for row in reduced]
    if _matrix_multiply(matrix, inverse) != _identity(size):
        raise ArithmeticError("computed inverse failed exact right-product verification")
    if _matrix_multiply(inverse, matrix) != _identity(size):
        raise ArithmeticError("computed inverse failed exact left-product verification")
    return inverse


def _matrix_multiply(left, right):
    if not left:
        return []
    if not right:
        if len(left[0]) != 0:
            raise ValueError("matrix dimensions do not conform")
        return [[] for _ in left]
    if len(left[0]) != len(right):
        raise ValueError("matrix dimensions do not conform")
    columns = len(right[0])
    return [
        [
            sum(
                (left[row][inner] * right[inner][column] for inner in range(len(right))),
                Fraction(0),
            )
            for column in range(columns)
        ]
        for row in range(len(left))
    ]


def _identity(size):
    return [
        [Fraction(int(row == column)) for column in range(size)]
        for row in range(size)
    ]


def _matrix_report(matrix):
    return [
        [phase29._fraction_report(value) for value in row]
        for row in matrix
    ]


def _serialize_poly(polynomial):
    return [
        {
            "coefficient": phase29._fraction_report(coefficient),
            "trace_factors": [
                [phase29._paired(generator) for generator in word]
                for word in monomial
            ],
        }
        for monomial, coefficient in sorted(polynomial.items())
        if coefficient
    ]


def _serialize_basis(basis, prefix):
    result = []
    for index, row in enumerate(basis):
        polynomial = row["vector"]
        result.append({
            "basis_id": f"{prefix}{index:05d}",
            "pivot_trace_monomial": phase29._trace_monomial_label(row["pivot"]),
            "total_matrix_word_degree": phase29._paired(
                phase30._poly_total_degree(polynomial)
            ),
            "trace_terms": _serialize_poly(polynomial),
        })
    return result


def _inclusion_record(source_name, source_basis, target_basis):
    matrix = [
        _coordinates_in_rref(row["vector"], target_basis)
        for row in source_basis
    ]
    source_rank = len(source_basis)
    target_rank = len(target_basis)
    rank = _matrix_rank(matrix, target_rank)
    if rank != source_rank:
        raise ArithmeticError(
            f"{source_name} inclusion map lost rank: expected {source_rank}, got {rank}"
        )
    return {
        "source_slice": source_name,
        "source_dimension": phase29._paired(source_rank),
        "target_dimension": phase29._paired(target_rank),
        "matrix_orientation": (
            "rows are canonical source-basis vectors; columns are coordinates "
            "in the canonical target basis"
        ),
        "coordinates_in_target_canonical_basis": _matrix_report(matrix),
        "matrix_rank": phase29._paired(rank),
        "kernel_dimension": phase29._paired(source_rank - rank),
        "cokernel_dimension": phase29._paired(target_rank - rank),
        "exact_reconstruction_verified": True,
    }


def _intersection(left_basis, right_basis):
    left_rank = len(left_basis)
    right_rank = len(right_basis)
    monomials = sorted({
        monomial
        for row in left_basis + right_basis
        for monomial in row["vector"]
    })
    equations = []
    variable_count = left_rank + right_rank
    for monomial in monomials:
        equation = [
            row["vector"].get(monomial, Fraction(0))
            for row in left_basis
        ] + [
            -row["vector"].get(monomial, Fraction(0))
            for row in right_basis
        ]
        if any(equation):
            equations.append(equation)

    kernel = _nullspace(equations, variable_count)
    common_vectors = []
    for kernel_vector in kernel:
        left_coordinates = kernel_vector[:left_rank]
        right_coordinates = kernel_vector[left_rank:]
        left_vector = {}
        right_vector = {}
        for coefficient, row in zip(left_coordinates, left_basis):
            phase29._poly_add_scaled(left_vector, row["vector"], coefficient)
        for coefficient, row in zip(right_coordinates, right_basis):
            phase29._poly_add_scaled(right_vector, row["vector"], coefficient)
        if left_vector != right_vector:
            raise ArithmeticError("intersection kernel vector failed exact left/right equality")
        if left_vector:
            common_vectors.append(left_vector)

    common_basis = _canonical_rref(common_vectors)
    if len(common_basis) != len(kernel):
        raise ArithmeticError("intersection kernel dimension does not equal common-subspace rank")
    left_coordinates = [
        _coordinates_in_rref(row["vector"], left_basis)
        for row in common_basis
    ]
    right_coordinates = [
        _coordinates_in_rref(row["vector"], right_basis)
        for row in common_basis
    ]
    if _matrix_rank(left_coordinates, left_rank) != len(common_basis):
        raise ArithmeticError("intersection coordinates are not independent in the left predecessor")
    if _matrix_rank(right_coordinates, right_rank) != len(common_basis):
        raise ArithmeticError("intersection coordinates are not independent in the right predecessor")
    return {
        "basis": common_basis,
        "left_coordinates": left_coordinates,
        "right_coordinates": right_coordinates,
        "kernel_dimension": len(kernel),
    }


def _cell_polynomials(cell, field):
    entries = cell.get(field)
    if not isinstance(entries, list):
        raise ValueError(f"filtration cell is missing list field {field!r}")
    return [_poly(entry) for entry in entries]


def analyze_exact_basis_transitions(filtration_result):
    """Expose canonical bases and exact maps for a completed Phase 30 filtration."""
    if not isinstance(filtration_result, dict):
        raise TypeError("filtration_result must be a mapping")
    if filtration_result.get("status") != "complete_bounded_filtration":
        return {
            "schema": "universe.trace-relation-basis-transitions.v1",
            "status": "unresolved_source_filtration",
            "source_filtration_status": filtration_result.get("status"),
            "reason": "Phase 31 requires every requested Phase 30 cell to be complete",
            "cells": [],
        }
    raw_cells = filtration_result.get("cells")
    if not isinstance(raw_cells, list):
        raise ValueError("completed filtration must contain a cells list")

    indexed = {}
    for cell in raw_cells:
        key = (
            _decode(cell["substitution_bound"], "substitution_bound"),
            _decode(cell["multiplier_bound"], "multiplier_bound"),
        )
        if key in indexed:
            raise ValueError("filtration contains duplicate (L,D) cells")
        indexed[key] = cell

    output_cells = []
    for key in sorted(indexed):
        substitution_bound, multiplier_bound = key
        cell = indexed[key]
        current_polynomials = _cell_polynomials(cell, "basis_entries")
        current_basis = _canonical_rref(current_polynomials)
        current_rank = len(current_basis)
        reported_rank = _decode(cell["relation_space_dimension"], "relation_space_dimension")
        if current_rank != reported_rank:
            raise ArithmeticError("canonical Phase 31 basis rank disagrees with Phase 30")

        left_key = (substitution_bound - 1, multiplier_bound)
        bottom_key = (substitution_bound, multiplier_bound - 1)
        has_left = left_key in indexed
        has_bottom = bottom_key in indexed
        left_basis = (
            _canonical_rref(_cell_polynomials(indexed[left_key], "basis_entries"))
            if has_left else []
        )
        bottom_basis = (
            _canonical_rref(_cell_polynomials(indexed[bottom_key], "basis_entries"))
            if has_bottom else []
        )

        inclusion_maps = []
        if has_left:
            inclusion_maps.append(
                _inclusion_record(
                    f"R[{left_key[0]},{left_key[1]}]",
                    left_basis,
                    current_basis,
                )
            )
        if has_bottom:
            inclusion_maps.append(
                _inclusion_record(
                    f"R[{bottom_key[0]},{bottom_key[1]}]",
                    bottom_basis,
                    current_basis,
                )
            )

        union_basis = _canonical_rref(
            [row["vector"] for row in left_basis + bottom_basis]
        )
        reported_union_rank = _decode(
            cell["predecessor_union_dimension"], "predecessor_union_dimension"
        )
        if len(union_basis) != reported_union_rank:
            raise ArithmeticError("canonical predecessor-union rank disagrees with Phase 30")

        intersection = _intersection(left_basis, bottom_basis)
        reported_intersection_rank = _decode(
            cell["predecessor_intersection_dimension"],
            "predecessor_intersection_dimension",
        )
        if len(intersection["basis"]) != reported_intersection_rank:
            raise ArithmeticError("exact predecessor intersection disagrees with Phase 30")

        quotient_polynomials = _cell_polynomials(cell, "new_directions")
        quotient_rank = len(quotient_polynomials)
        reported_quotient_rank = _decode(
            cell["new_quotient_dimension"], "new_quotient_dimension"
        )
        if quotient_rank != reported_quotient_rank:
            raise ArithmeticError("Phase 30 quotient complement cardinality is inconsistent")

        # The union basis followed by the Phase 30 quotient complement is an
        # adapted basis of R[L,D]. Build both exact directions of this change.
        adapted_polynomials = (
            [row["vector"] for row in union_basis] + quotient_polynomials
        )
        adapted_coordinates = [
            _coordinates_in_rref(polynomial, current_basis)
            for polynomial in adapted_polynomials
        ]
        if len(adapted_coordinates) != current_rank:
            raise ArithmeticError("predecessor basis plus quotient complement has wrong cardinality")
        if _matrix_rank(adapted_coordinates, current_rank) != current_rank:
            raise ArithmeticError("predecessor basis plus quotient complement is not independent")
        inverse_coordinates = _matrix_inverse(adapted_coordinates)

        quotient_coordinates = adapted_coordinates[len(union_basis):]
        output_cells.append({
            "substitution_bound": phase29._paired(substitution_bound),
            "multiplier_bound": phase29._paired(multiplier_bound),
            "relation_space_dimension": phase29._paired(current_rank),
            "predecessor_union_dimension": phase29._paired(len(union_basis)),
            "predecessor_intersection_dimension": phase29._paired(
                len(intersection["basis"])
            ),
            "quotient_dimension": phase29._paired(quotient_rank),
            "canonicalization": {
                "method": "unique reduced row-echelon form over Q",
                "column_order": "lexicographic order of canonical trace-monomial tuples",
                "pivot_normalization": "each pivot coefficient is exactly 1",
                "basis_order_independent_of_input_order": True,
            },
            "canonical_basis": _serialize_basis(current_basis, "CB"),
            "inclusion_maps": inclusion_maps,
            "predecessor_union_basis": _serialize_basis(union_basis, "PU"),
            "predecessor_intersection": {
                "dimension": phase29._paired(len(intersection["basis"])),
                "basis": _serialize_basis(intersection["basis"], "IX"),
                "coordinates_in_left_predecessor_basis": _matrix_report(
                    intersection["left_coordinates"]
                ),
                "coordinates_in_bottom_predecessor_basis": _matrix_report(
                    intersection["right_coordinates"]
                ),
                "kernel_dimension_of_[left_basis|-bottom_basis]": phase29._paired(
                    intersection["kernel_dimension"]
                ),
                "exact_equality_and_coordinate_reconstruction_verified": True,
            },
            "quotient_complement_basis": [
                {
                    "complement_id": f"QD{index:05d}",
                    "trace_terms": _serialize_poly(polynomial),
                    "coordinates_in_current_canonical_basis": _matrix_report([
                        quotient_coordinates[index]
                    ])[0],
                }
                for index, polynomial in enumerate(quotient_polynomials)
            ],
            "adapted_basis_transition": {
                "basis_order": (
                    "canonical predecessor-union basis, followed by the Phase 30 "
                    "quotient complement in its deterministic candidate order"
                ),
                "adapted_basis_dimension": phase29._paired(len(adapted_polynomials)),
                "adapted_to_canonical_matrix": _matrix_report(adapted_coordinates),
                "canonical_to_adapted_matrix": _matrix_report(inverse_coordinates),
                "both_products_are_exact_identity": True,
                "determinant_nonzero": True,
            },
            "rank_nullity_checks": {
                "left_inclusion_kernel_dimension": (
                    inclusion_maps[0]["kernel_dimension"] if has_left else phase29._paired(0)
                ),
                "bottom_inclusion_kernel_dimension": (
                    inclusion_maps[-1]["kernel_dimension"] if has_bottom else phase29._paired(0)
                ),
                "left_inclusion_cokernel_dimension": (
                    inclusion_maps[0]["cokernel_dimension"] if has_left else phase29._paired(current_rank)
                ),
                "bottom_inclusion_cokernel_dimension": (
                    inclusion_maps[-1]["cokernel_dimension"] if has_bottom else phase29._paired(current_rank)
                ),
                "dimension_identity": (
                    "dim R[L,D] = dim(R[L-1,D]+R[L,D-1]) + dim quotient"
                ),
                "verified": (
                    len(union_basis) + quotient_rank == current_rank
                    and all(_decode(item["kernel_dimension"], "kernel_dimension") == 0
                            for item in inclusion_maps)
                ),
            },
        })

    return {
        "schema": "universe.trace-relation-basis-transitions.v1",
        "status": "complete_exact_basis_transitions",
        "coefficient_field": "Q",
        "source_filtration_status": filtration_result["status"],
        "filtration_configuration": {
            key: value
            for key, value in filtration_result.items()
            if key not in {"cells", "status"}
        },
        "transition_semantics": (
            "Every matrix is an exact rational coordinate map between finite canonical "
            "bases. These are finite slice transitions, not a recurrence or extrapolation "
            "to unsearched L,D values."
        ),
        "cells": output_cells,
        "minimality_boundary": (
            "Canonical bases have minimum cardinality as bases of their finite vector spaces. "
            "The quotient complement is minimal relative to the predecessor sum only; no "
            "minimal generating set of the infinite T-ideal is established."
        ),
        "structural_boundary": (
            "Exact transition matrices and finite rank/nullity identities do not establish "
            "eventual stabilization, a universal recurrence, or an infinite Hilbert series."
        ),
    }


def analyze_bounded_basis_transitions(**filtration_options):
    """Run Phase 30 with the supplied bounds, then compute Phase 31 transitions."""
    filtration = phase30.analyze_bounded_relation_filtration(**filtration_options)
    return analyze_exact_basis_transitions(filtration)
