"""Exact bifiltration squares, mixed overlap and rank-difference operators.

Phase 30 supplies the completed finite filtration R[L,D] and Phase 31 supplies
canonical rational bases and inclusion-coordinate matrices. This module studies
one unit square at a time:

    C = R[L-1,D-1]  ->  A = R[L-1,D]
    |                   |
    v                   v
    B = R[L,D-1]   ->  R = R[L,D]

It computes A∩B over Q, a deterministic complement of C inside A∩B, and checks
the two composed inclusion paths against the direct C -> R coordinates. Every
identity is exact over Q; no floats, sampling, or infinite extrapolation are
used.
"""
from __future__ import annotations

import re
from fractions import Fraction

import basis_transitions as phase31
import relation_filtration as phase30
import trace_ideal_closure as phase29


_SCHEMA = "universe.trace-relation-bifiltration-operators.v1"
_COMPLETE_STATUS = "complete_exact_bifiltration_operators"
_SOURCE_LABEL_RE = re.compile(r"R\[(\d+),(\d+)\]")


def _decode(value, name: str, minimum: int = 0) -> int:
    return phase29._integer(value, name, minimum)


def _paired(value: int) -> str:
    return phase29._paired(value)


def _cell_label(key):
    return {
        "substitution_bound": _paired(key[0]),
        "multiplier_bound": _paired(key[1]),
    }


def _matrix_from_report(report, name: str):
    if not isinstance(report, list):
        raise TypeError(f"{name} must be a matrix report list")
    matrix = []
    for row_index, row in enumerate(report):
        if not isinstance(row, list):
            raise TypeError(f"{name} row {row_index} must be a list")
        converted = []
        for column_index, value in enumerate(row):
            if not isinstance(value, dict) or set(value) != {"numerator", "denominator"}:
                raise ValueError(
                    f"{name}[{row_index}][{column_index}] must be an exact rational report"
                )
            converted.append(
                phase29._fraction(value, f"{name}[{row_index}][{column_index}]")
            )
        matrix.append(converted)
    if matrix and any(len(row) != len(matrix[0]) for row in matrix):
        raise ValueError(f"{name} rows must all have the same length")
    return matrix


def _require_shape(matrix, rows, columns, name: str):
    if len(matrix) != rows or any(len(row) != columns for row in matrix):
        raise ArithmeticError(
            f"{name} has shape ({len(matrix)}, {[len(row) for row in matrix]}) "
            f"but expected ({rows}, {columns})"
        )


def _canonical_basis(cell):
    return phase31._canonical_rref(phase31._cell_polynomials(cell, "basis_entries"))


def _inclusion(source_basis, target_basis, source_key, target_key):
    """Return the raw matrix and the Phase 31-style report for one inclusion."""
    matrix = [
        phase31._coordinates_in_rref(row["vector"], target_basis)
        for row in source_basis
    ]
    source_rank = len(source_basis)
    target_rank = len(target_basis)
    _require_shape(matrix, source_rank, target_rank, "inclusion matrix")
    if phase31._matrix_rank(matrix, target_rank) != source_rank:
        raise ArithmeticError("an inclusion map lost rank")
    source_name = f"R[{source_key[0]},{source_key[1]}]"
    report = phase31._inclusion_record(source_name, source_basis, target_basis)
    return matrix, report


def _index_filtration(filtration_result):
    if not isinstance(filtration_result, dict):
        raise TypeError("filtration_result must be a mapping")
    if filtration_result.get("status") != "complete_bounded_filtration":
        return None, {
            "status": "unresolved_source_filtration",
            "source_filtration_status": filtration_result.get("status"),
            "reason": "Phase 32 requires a complete Phase 30 filtration",
            "cells": [],
        }
    raw_cells = filtration_result.get("cells")
    if not isinstance(raw_cells, list):
        raise ValueError("completed filtration must contain a cells list")
    if not raw_cells:
        raise ValueError("completed filtration must contain at least one cell")

    indexed = {}
    for cell in raw_cells:
        if not isinstance(cell, dict):
            raise TypeError("each filtration cell must be a mapping")
        key = (
            _decode(cell["substitution_bound"], "substitution_bound"),
            _decode(cell["multiplier_bound"], "multiplier_bound"),
        )
        if key in indexed:
            raise ValueError("filtration contains duplicate (L,D) cells")
        indexed[key] = cell

    min_l = min(key[0] for key in indexed)
    min_d = min(key[1] for key in indexed)
    if min_l < 1:
        raise ValueError("substitution_bound must be at least 1")
    if min_d < 0:
        raise ValueError("multiplier_bound must be at least 0")
    max_l = max(key[0] for key in indexed)
    max_d = max(key[1] for key in indexed)
    expected = {
        (length, degree)
        for length in range(min_l, max_l + 1)
        for degree in range(min_d, max_d + 1)
    }
    if set(indexed) != expected:
        missing = sorted(expected - set(indexed))
        return None, {
            "status": "unresolved_non_rectangular_filtration",
            "reason": "the supplied Phase 30 cells are not a complete rectangular grid",
            "missing_cells": [_cell_label(key) for key in missing],
            "cells": [],
        }
    return indexed, None


def _index_transitions(transition_result):
    if transition_result is None:
        return None, None
    if not isinstance(transition_result, dict):
        raise TypeError("transition_result must be a mapping or None")
    if transition_result.get("status") != "complete_exact_basis_transitions":
        return None, {
            "status": "unresolved_source_transitions",
            "source_transition_status": transition_result.get("status"),
            "reason": "Phase 32 requires complete Phase 31 transitions when they are supplied",
            "cells": [],
        }
    raw_cells = transition_result.get("cells")
    if not isinstance(raw_cells, list) or not raw_cells:
        raise ValueError("completed transition result must contain a nonempty cells list")
    indexed = {}
    for cell in raw_cells:
        if not isinstance(cell, dict):
            raise TypeError("each transition cell must be a mapping")
        key = (
            _decode(cell["substitution_bound"], "substitution_bound"),
            _decode(cell["multiplier_bound"], "multiplier_bound"),
        )
        if key in indexed:
            raise ValueError("transition result contains duplicate (L,D) cells")
        indexed[key] = cell
    return indexed, None


def _transition_inclusion(target_cell, source_key):
    maps = target_cell.get("inclusion_maps")
    if not isinstance(maps, list):
        raise ValueError("transition cell is missing its inclusion_maps list")
    for mapping in maps:
        if not isinstance(mapping, dict):
            raise TypeError("each inclusion map must be a mapping")
        label = mapping.get("source_slice")
        match = _SOURCE_LABEL_RE.fullmatch(label) if isinstance(label, str) else None
        if match and (int(match.group(1)), int(match.group(2))) == source_key:
            return mapping
    raise ArithmeticError(
        f"Phase 31 transition is missing the inclusion map from R[{source_key[0]},{source_key[1]}]"
    )


def _verify_supplied_transitions(transition_index, edge_records):
    for (source_key, target_key), (matrix, _report) in sorted(edge_records.items()):
        target_cell = transition_index.get(target_key)
        if target_cell is None:
            raise ArithmeticError("Phase 31 transition result is missing a required target cell")
        mapping = _transition_inclusion(target_cell, source_key)
        reported = _matrix_from_report(
            mapping.get("coordinates_in_target_canonical_basis"),
            "Phase 31 inclusion matrix",
        )
        _require_shape(reported, len(matrix), len(matrix[0]), "Phase 31 inclusion matrix")
        if reported != matrix:
            raise ArithmeticError(
                "supplied Phase 31 inclusion matrix disagrees with the exact recomputation"
            )
        if mapping.get("exact_reconstruction_verified") is not True:
            raise ArithmeticError("supplied Phase 31 inclusion map lacks exact verification")
        if _decode(mapping["kernel_dimension"], "kernel_dimension") != 0:
            raise ArithmeticError("supplied Phase 31 inclusion map has a nonzero kernel")


def _boundary_reason(key):
    length, degree = key
    reasons = []
    if length < 2:
        reasons.append("L=1 has no L-predecessor and therefore no unit square")
    if degree < 1:
        reasons.append("D=0 has no D-predecessor and therefore no unit square")
    if not reasons:
        reasons.append("cell is not an interior terminal cell of the supplied rectangular grid")
    return "; ".join(reasons)


def analyze_exact_bifiltration_operators(
    filtration_result,
    transition_result=None,
    *,
    max_cells: int = 256,
    max_squares: int = 64,
):
    """Compute exact square operators and mixed overlap for a completed filtration.

    ``transition_result`` may be the output of Phase 31. Its inclusion matrices
    are independently recomputed and must agree exactly. When it is omitted,
    the same Phase 31 primitives are used to derive the maps from the Phase 30
    bases. No source generators are duplicated or re-enumerated here.
    """
    max_cells = _decode(max_cells, "max_cells", 1)
    max_squares = _decode(max_squares, "max_squares", 1)
    configuration = {
        "cell_count_cap": _paired(max_cells),
        "square_count_cap": _paired(max_squares),
    }

    indexed, unresolved = _index_filtration(filtration_result)
    if unresolved is not None:
        return {
            "schema": _SCHEMA,
            **unresolved,
            "caps": configuration,
        }
    if len(indexed) > max_cells:
        return {
            "schema": _SCHEMA,
            "status": "unresolved_cell_cap",
            "reason": "the supplied filtration exceeds max_cells",
            "cell_count": _paired(len(indexed)),
            "cells": [],
            "caps": configuration,
        }

    transition_index, unresolved_transition = _index_transitions(transition_result)
    if unresolved_transition is not None:
        return {
            "schema": _SCHEMA,
            **unresolved_transition,
            "source_filtration_status": filtration_result["status"],
            "cell_count": _paired(len(indexed)),
            "caps": configuration,
        }

    min_l = min(key[0] for key in indexed)
    max_l = max(key[0] for key in indexed)
    min_d = min(key[1] for key in indexed)
    max_d = max(key[1] for key in indexed)

    square_keys = []
    missing_predecessors = []
    for length in range(max(2, min_l), max_l + 1):
        for degree in range(max(1, min_d), max_d + 1):
            required = (
                (length, degree),
                (length - 1, degree),
                (length, degree - 1),
                (length - 1, degree - 1),
            )
            if all(key in indexed for key in required):
                square_keys.append((length, degree))
            else:
                missing_predecessors.append(_cell_label((length, degree)))

    if missing_predecessors:
        return {
            "schema": _SCHEMA,
            "status": "unresolved_missing_square_predecessors",
            "reason": "one or more interior cells lack an actual Phase 30 predecessor cell",
            "missing_predecessor_terminals": missing_predecessors,
            "cells": [],
            "caps": configuration,
        }
    if len(square_keys) > max_squares:
        return {
            "schema": _SCHEMA,
            "status": "unresolved_square_cap",
            "reason": "the number of interior unit squares exceeds max_squares",
            "square_count": _paired(len(square_keys)),
            "squares": [],
            "caps": configuration,
        }

    canonical = {key: _canonical_basis(indexed[key]) for key in sorted(indexed)}
    for key, basis in canonical.items():
        reported = _decode(indexed[key]["relation_space_dimension"], "relation_space_dimension")
        if len(basis) != reported:
            raise ArithmeticError("canonical Phase 31 basis rank disagrees with Phase 30")

    edge_records = {}
    for length, degree in square_keys:
        source = (length - 1, degree - 1)
        left = (length - 1, degree)
        bottom = (length, degree - 1)
        terminal = (length, degree)
        for edge in ((source, bottom), (bottom, terminal), (source, left), (left, terminal)):
            if edge not in edge_records:
                edge_records[edge] = _inclusion(
                    canonical[edge[0]], canonical[edge[1]], edge[0], edge[1]
                )
    if transition_index is not None:
        _verify_supplied_transitions(transition_index, edge_records)

    square_reports = []
    for length, degree in square_keys:
        source_key = (length - 1, degree - 1)
        left_key = (length - 1, degree)
        bottom_key = (length, degree - 1)
        terminal_key = (length, degree)
        source_basis = canonical[source_key]
        left_basis = canonical[left_key]
        bottom_basis = canonical[bottom_key]
        terminal_basis = canonical[terminal_key]

        source_in_left = [
            phase31._coordinates_in_rref(row["vector"], left_basis) for row in source_basis
        ]
        source_in_bottom = [
            phase31._coordinates_in_rref(row["vector"], bottom_basis) for row in source_basis
        ]
        left_in_terminal = [
            phase31._coordinates_in_rref(row["vector"], terminal_basis) for row in left_basis
        ]
        bottom_in_terminal = [
            phase31._coordinates_in_rref(row["vector"], terminal_basis) for row in bottom_basis
        ]

        intersection = phase31._intersection(left_basis, bottom_basis)
        intersection_basis = intersection["basis"]
        dim_source = len(source_basis)
        dim_left = len(left_basis)
        dim_bottom = len(bottom_basis)
        dim_terminal = len(terminal_basis)
        dim_intersection = len(intersection_basis)
        reported_intersection = _decode(
            indexed[terminal_key]["predecessor_intersection_dimension"],
            "predecessor_intersection_dimension",
        )
        if dim_intersection != reported_intersection:
            raise ArithmeticError("exact A∩B rank disagrees with Phase 30")

        union_basis = phase31._canonical_rref(
            [row["vector"] for row in left_basis + bottom_basis]
        )
        union_rank = len(union_basis)
        reported_union = _decode(
            indexed[terminal_key]["predecessor_union_dimension"],
            "predecessor_union_dimension",
        )
        if union_rank != reported_union:
            raise ArithmeticError("exact predecessor-union rank disagrees with Phase 30")
        quotient_q = _decode(
            indexed[terminal_key]["new_quotient_dimension"],
            "new_quotient_dimension",
        )
        if union_rank + quotient_q != dim_terminal:
            raise ArithmeticError("Phase 30 quotient increment does not reconcile with canonical rank")

        if dim_source > dim_intersection:
            raise ArithmeticError("C is larger than the computed predecessor intersection")
        source_in_intersection = [
            phase31._coordinates_in_rref(row["vector"], intersection_basis)
            for row in source_basis
        ]
        if phase31._matrix_rank(source_in_intersection, dim_intersection) != dim_source:
            raise ArithmeticError("C does not inject into the exact predecessor intersection")

        # Deterministic complement of C inside A∩B. The seed basis is the
        # canonical C basis; the candidates are the canonical intersection
        # vectors. Exact insertion turns each accepted candidate into a pivot.
        seed_basis = []
        for index, row in enumerate(source_basis):
            seed_basis.append({
                "pivot": row["pivot"],
                "vector": dict(row["vector"]),
                "representation": {f"C{index:05d}": Fraction(1)},
            })
        complement = []
        complement_ids = []
        for index, row in enumerate(intersection_basis):
            candidate_id = f"I{index:05d}"
            existing_rows = {id(item) for item in seed_basis}
            independent, _relation, _pivot = phase29._insert_exact_basis(
                seed_basis, row["vector"], candidate_id
            )
            if independent:
                # _insert_exact_basis keeps the seed sorted by pivot, so the
                # accepted row is not necessarily the last list element.
                newest = next(item for item in seed_basis if id(item) not in existing_rows)
                complement.append({"pivot": newest["pivot"], "vector": newest["vector"]})
                complement_ids.append(candidate_id)

        omega = dim_intersection - dim_source
        if len(complement) != omega:
            raise ArithmeticError("mixed-overlap complement cardinality is inconsistent")
        combined_rows = [row["vector"] for row in source_basis] + [
            row["vector"] for row in complement
        ]
        combined_canonical = phase31._canonical_rref(combined_rows)
        if len(combined_canonical) != dim_intersection:
            raise ArithmeticError("C plus the complement does not span A∩B")
        combined_in_intersection = [
            phase31._coordinates_in_rref(polynomial, intersection_basis)
            for polynomial in combined_rows
        ]
        if phase31._matrix_rank(combined_in_intersection, dim_intersection) != dim_intersection:
            raise ArithmeticError("C plus the complement is not independent in A∩B")
        complement_in_intersection = combined_in_intersection[dim_source:]
        if phase31._matrix_rank(complement_in_intersection, dim_intersection) != omega:
            raise ArithmeticError("mixed-overlap complement is not independent modulo C")
        for row in intersection_basis:
            phase31._coordinates_in_rref(row["vector"], combined_canonical)

        complement_in_left = [
            phase31._coordinates_in_rref(row["vector"], left_basis) for row in complement
        ]
        complement_in_bottom = [
            phase31._coordinates_in_rref(row["vector"], bottom_basis) for row in complement
        ]

        # Commutativity: C -> B -> R must equal C -> A -> R and the direct map.
        source_to_bottom = edge_records[(source_key, bottom_key)][0]
        bottom_to_terminal = edge_records[(bottom_key, terminal_key)][0]
        source_to_left = edge_records[(source_key, left_key)][0]
        left_to_terminal = edge_records[(left_key, terminal_key)][0]
        bottom_path = phase31._matrix_multiply(source_to_bottom, bottom_to_terminal)
        left_path = phase31._matrix_multiply(source_to_left, left_to_terminal)
        direct = [
            phase31._coordinates_in_rref(row["vector"], terminal_basis)
            for row in source_basis
        ]
        _require_shape(bottom_path, dim_source, dim_terminal, "C->B->R product")
        _require_shape(left_path, dim_source, dim_terminal, "C->A->R product")
        _require_shape(direct, dim_source, dim_terminal, "direct C->R map")
        if bottom_path != left_path or bottom_path != direct:
            raise ArithmeticError("the bifiltration square is not commutative over Q")

        if dim_intersection != dim_source + omega:
            raise ArithmeticError("dim(A∩B)=dim C+omega failed")
        if dim_left + dim_bottom - dim_intersection != union_rank:
            raise ArithmeticError("dim(A+B)=dim A+dim B-dim(A∩B) failed")
        if dim_terminal != dim_left + dim_bottom - dim_source - omega + quotient_q:
            raise ArithmeticError("dim R = dim A+dim B-dim C-omega+q failed")
        rank_difference = dim_terminal - dim_left - dim_bottom + dim_source
        if rank_difference != quotient_q - omega:
            raise ArithmeticError("Delta_L Delta_D r = q-omega failed")

        square_reports.append({
            "terminal_cell": _cell_label(terminal_key),
            "source_cell": _cell_label(source_key),
            "left_predecessor": _cell_label(left_key),
            "bottom_predecessor": _cell_label(bottom_key),
            "dimensions": {
                "source": _paired(dim_source),
                "left": _paired(dim_left),
                "bottom": _paired(dim_bottom),
                "terminal": _paired(dim_terminal),
                "intersection": _paired(dim_intersection),
                "union": _paired(union_rank),
                "quotient_q": _paired(quotient_q),
                "mixed_overlap_omega": _paired(omega),
                "rank_difference": _paired(rank_difference),
            },
            "mixed_overlap": {
                "status": "nonzero_mixed_overlap" if omega else "zero_mixed_overlap",
                "omega": _paired(omega),
                "source_basis": phase31._serialize_basis(source_basis, "SW"),
                "intersection_basis": phase31._serialize_basis(intersection_basis, "IX"),
                "intersection_coordinates_in_left_predecessor_basis": phase31._matrix_report(
                    intersection["left_coordinates"]
                ),
                "intersection_coordinates_in_bottom_predecessor_basis": phase31._matrix_report(
                    intersection["right_coordinates"]
                ),
                "source_coordinates_in_intersection_basis": phase31._matrix_report(
                    source_in_intersection
                ),
                "complement_ids": complement_ids,
                "complement_basis": phase31._serialize_basis(complement, "MO"),
                "complement_coordinates_in_left_predecessor_basis": phase31._matrix_report(
                    complement_in_left
                ),
                "complement_coordinates_in_bottom_predecessor_basis": phase31._matrix_report(
                    complement_in_bottom
                ),
                "complement_coordinates_in_intersection_basis": phase31._matrix_report(
                    complement_in_intersection
                ),
                "exact_independence_and_spanning_verified": True,
                "exact_source_embedding_verified": True,
            },
            "commutative_square": {
                "orientation": (
                    "rows are canonical source-basis vectors; columns are coordinates "
                    "in the canonical target basis"
                ),
                "source_to_bottom_matrix": phase31._matrix_report(source_to_bottom),
                "bottom_to_terminal_matrix": phase31._matrix_report(bottom_to_terminal),
                "source_to_left_matrix": phase31._matrix_report(source_to_left),
                "left_to_terminal_matrix": phase31._matrix_report(left_to_terminal),
                "bottom_path_product": phase31._matrix_report(bottom_path),
                "left_path_product": phase31._matrix_report(left_path),
                "direct_source_to_terminal": phase31._matrix_report(direct),
                "all_paths_equal_exactly": True,
                "phase31_matrices_independently_recomputed": transition_index is not None,
            },
            "rank_identities": {
                "intersection_identity": "dim(A∩B) = dim C + omega",
                "union_identity": "dim(A+B) = dim A + dim B - dim(A∩B)",
                "terminal_identity": "dim R = dim A + dim B - dim C - omega + q",
                "rank_difference_identity": "Delta_L Delta_D r = q - omega",
                "all_identities_verified_exactly": True,
            },
        })

    boundary_cells = []
    for key in sorted(indexed):
        if key not in square_keys:
            boundary_cells.append({
                **_cell_label(key),
                "status": "boundary_cell_no_square",
                "reason": _boundary_reason(key),
                "zero_subspace_injected": False,
            })

    return {
        "schema": _SCHEMA,
        "status": _COMPLETE_STATUS,
        "coefficient_field": "Q",
        "source_filtration_status": filtration_result["status"],
        "source_transition_status": (
            transition_result["status"]
            if transition_result is not None
            else "derived_from_complete_phase30_filtration"
        ),
        "matrix_orientation": (
            "rows are canonical source-basis vectors; columns are coordinates "
            "in the canonical target basis"
        ),
        "cell_count": _paired(len(indexed)),
        "square_count": _paired(len(square_keys)),
        "caps": configuration,
        "boundary_cells": boundary_cells,
        "squares": square_reports,
        "proof_checks": {
            "exact_field": "Q",
            "floating_point_used": False,
            "sampled_matrix_substitution_used": False,
            "all_square_paths_equal": True,
            "all_rank_identities_equal": True,
            "all_mixed_overlap_complements_independent_and_spanning": True,
        },
        "structural_boundary": (
            "q is a finite predecessor-union quotient increment and omega is a finite "
            "local overlap correction. Neither proves stabilization, a universal "
            "recurrence, global distributivity, an infinite Hilbert series or a "
            "minimal generating set of the infinite T-ideal."
        ),
    }


def analyze_bounded_bifiltration_operators(**filtration_options):
    """Run Phase 30, Phase 31 and Phase 32 for one bounded (L,D) grid."""
    filtration = phase30.analyze_bounded_relation_filtration(**filtration_options)
    transitions = phase31.analyze_exact_basis_transitions(filtration)
    return analyze_exact_bifiltration_operators(filtration, transitions)
