"""Exact global rank ledger for a completed two-parameter trace-relation filtration.

Phase 33 consumes completed Phase 30 and Phase 32 results. It never rebuilds the
FTI catalogue and never recomputes a Phase 32 square: every q is read from the
completed Phase 30 cell and every omega is read from the completed Phase 32
mixed-overlap complement, after exact revalidation of its degree metadata.

The ledger proves finite two-dimensional telescoping identities:

    r[L,D] = sum_{i=1..L, j=0..D} (q[i,j] - omega[i,j])

and the corresponding arbitrary-subrectangle and degree-resolved statements.
Formal zero boundary values r[0,D] and r[L,-1] are used only inside those
finite-difference formulas; they are never emitted as computed cells.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _sibling in (
    "phase-27",
    "phase-28",
    "phase-29",
    "phase-30",
    "phase-31",
    "phase-32",
    "phase-33",
):
    _path = _ROOT / _sibling
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import trace_ideal_closure as phase29
import relation_filtration as phase30
import basis_transitions as phase31
import bifiltration_operators as phase32


_SCHEMA = "universe.trace-relation-bifiltration-rank-ledger.v1"
_COMPLETE_STATUS = "complete_exact_bifiltration_rank_ledger"
_FILTRATION_SCHEMA = "universe.trace-relation-filtration.v1"
_BIFILTRATION_SCHEMA = "universe.trace-relation-bifiltration-operators.v1"

DEFAULT_MAX_RECTANGLE_CHECKS = 4096
DEFAULT_MAX_CELLS = 256
DEFAULT_MAX_SQUARES = 256
DEFAULT_MAX_DEGREE_VECTOR_CHECKS = 4096

_SHARED_CONFIG_KEYS = (
    "dimension",
    "generator_count",
    "max_substitution_word_length",
    "max_multiplier_trace_word_length",
    "max_multiplier_total_word_degree",
    "coefficient_field",
)


class LedgerUnresolved(Exception):
    """Internal control flow for a specific unresolved ledger status."""

    def __init__(self, status: str, reason: str, **details):
        super().__init__(reason)
        self.status = status
        self.reason = reason
        self.details = details


def _unresolved(status: str, reason: str, **details):
    result = {
        "schema": _SCHEMA,
        "status": status,
        "reason": reason,
    }
    for key, value in details.items():
        if key not in result:
            result[key] = value
    return result


def _decode(value, name: str, minimum: int = 0) -> int:
    return phase29._integer(value, name, minimum)


def _paired(value: int) -> str:
    return phase29._paired(value)


def _rational_report(value, name: str):
    return phase29._fraction_report(phase29._fraction(value, name))


def _cell_label(key):
    return {
        "substitution_bound": _paired(key[0]),
        "multiplier_bound": _paired(key[1]),
    }


def _cell_id(key) -> str:
    return f"L{_paired(key[0])}D{_paired(key[1])}"


def _parse_cell_key(cell, name: str):
    if not isinstance(cell, dict):
        raise TypeError(f"{name} must be a mapping")
    return (
        _decode(cell["substitution_bound"], f"{name} substitution_bound", 0),
        _decode(cell["multiplier_bound"], f"{name} multiplier_bound", 0),
    )


def _profile_from_report(report, name: str, minimum: int = 0):
    if not isinstance(report, dict):
        raise TypeError(f"{name} must be a mapping")
    profile = {}
    for raw_degree, raw_count in report.items():
        degree = _decode(raw_degree, f"{name} degree", 0)
        count = _decode(raw_count, f"{name} count", minimum)
        if degree in profile:
            raise LedgerUnresolved(
                "unresolved_duplicate_degree_key",
                "a degree profile contains two encodings of the same degree",
                source=name,
                degree=_paired(degree),
            )
        if count:
            profile[degree] = count
    return dict(sorted(profile.items()))


def _profile_report(profile) -> dict:
    return {_paired(degree): _paired(count) for degree, count in sorted(profile.items())}


def _profile_sum(profile) -> int:
    return sum(profile.values())


def _profile_add(target, source, scale: int = 1):
    for degree, count in source.items():
        updated = target.get(degree, 0) + scale * count
        if updated:
            target[degree] = updated
        else:
            target.pop(degree, None)


def _profile_difference(left, right):
    result = {}
    for degree in sorted(set(left) | set(right)):
        difference = left.get(degree, 0) - right.get(degree, 0)
        if difference:
            result[degree] = difference
    return result


def _validate_degree_vector(entry, basis_id: str, source: str, counter):
    if not isinstance(entry, dict):
        raise TypeError(f"{basis_id} must be a mapping")
    terms = entry.get("trace_terms")
    if not isinstance(terms, list):
        raise TypeError(f"{basis_id} trace_terms must be a list")
    counter["count"] += 1
    if counter["count"] > counter["limit"]:
        raise LedgerUnresolved(
            "unresolved_degree_vector_cap",
            "the degree-vector inspection cap was exceeded",
            required=_paired(counter["count"]),
            cap=_paired(counter["limit"]),
            offending_basis_id=basis_id,
            source=source,
        )
    polynomial = phase29._poly_from_terms(terms)
    if not polynomial:
        raise LedgerUnresolved(
            "unresolved_empty_basis_vector",
            "a supplied basis vector has an empty exact trace polynomial",
            offending_basis_id=basis_id,
            source=source,
        )
    try:
        degree = phase30._poly_total_degree(polynomial)
    except ArithmeticError as exc:
        raise LedgerUnresolved(
            "unresolved_nonhomogeneous_basis_vector",
            "a supplied basis vector mixes total matrix-word degrees",
            offending_basis_id=basis_id,
            source=source,
            detail=str(exc),
        ) from None
    if "total_matrix_word_degree" not in entry:
        raise LedgerUnresolved(
            "unresolved_basis_degree_metadata_missing",
            "a supplied basis vector lacks total_matrix_word_degree",
            offending_basis_id=basis_id,
            source=source,
        )
    declared = _decode(
        entry["total_matrix_word_degree"],
        f"{basis_id} total_matrix_word_degree",
        0,
    )
    if declared != degree:
        raise LedgerUnresolved(
            "unresolved_basis_degree_metadata_mismatch",
            "declared and recomputed basis-vector degrees disagree",
            offending_basis_id=basis_id,
            source=source,
            declared_degree=_paired(declared),
            recomputed_degree=_paired(degree),
        )
    return degree


def _index_filtration(filtration_result, counter, max_cells: int):
    if not isinstance(filtration_result, dict):
        raise TypeError("filtration_result must be a mapping")
    if filtration_result.get("schema", _FILTRATION_SCHEMA) != _FILTRATION_SCHEMA:
        raise LedgerUnresolved(
            "unresolved_source_schema",
            "the Phase 30 source schema is not supported",
            source_schema=filtration_result.get("schema"),
        )
    if filtration_result.get("status") != "complete_bounded_filtration":
        return _unresolved(
            "unresolved_source_filtration",
            "Phase 33 requires a complete Phase 30 filtration",
            source_filtration_status=filtration_result.get("status"),
        )
    raw_cells = filtration_result.get("cells")
    if not isinstance(raw_cells, list):
        raise TypeError("completed filtration must contain a cells list")
    if not raw_cells:
        return _unresolved(
            "unresolved_empty_source",
            "the completed Phase 30 filtration contains no cells",
        )
    if len(raw_cells) > max_cells:
        return _unresolved(
            "unresolved_cell_cap",
            "the supplied filtration exceeds max_cells",
            cell_count=_paired(len(raw_cells)),
            cap=_paired(max_cells),
        )

    cells = {}
    for index, cell in enumerate(raw_cells):
        key = _parse_cell_key(cell, f"filtration cell {index}")
        if key in cells:
            return _unresolved(
                "unresolved_duplicate_filtration_cell",
                "the Phase 30 source contains duplicate (L,D) cells",
                cell=_cell_label(key),
            )
        cells[key] = cell

    min_l = min(key[0] for key in cells)
    min_d = min(key[1] for key in cells)
    if min_l != 1 or min_d != 0:
        return _unresolved(
            "unresolved_grid_origin",
            "the supplied grid must start at (L,D)=(1,0)",
            minimum_cell=_cell_label((min_l, min_d)),
        )
    max_l = max(key[0] for key in cells)
    max_d = max(key[1] for key in cells)
    expected = {
        (length, degree)
        for length in range(1, max_l + 1)
        for degree in range(0, max_d + 1)
    }
    if set(cells) != expected:
        return _unresolved(
            "unresolved_non_rectangular_filtration",
            "the supplied Phase 30 cells are not a complete rectangular grid",
            missing_cells=[_cell_label(key) for key in sorted(expected - set(cells))],
            extra_cells=[_cell_label(key) for key in sorted(set(cells) - expected)],
        )

    ranks = {}
    q_reported = {}
    rank_profiles = {}
    q_profiles = {}
    union_profiles = {}
    for key in sorted(cells):
        cell = cells[key]
        ranks[key] = _decode(
            cell["relation_space_dimension"],
            f"{_cell_id(key)} relation_space_dimension",
        )
        q_reported[key] = _decode(
            cell["new_quotient_dimension"],
            f"{_cell_id(key)} new_quotient_dimension",
        )
        rank_profiles[key] = _profile_from_report(
            cell["rank_by_total_word_degree"],
            f"{_cell_id(key)} rank_by_total_word_degree",
        )
        q_profiles[key] = _profile_from_report(
            cell["new_quotient_rank_by_total_word_degree"],
            f"{_cell_id(key)} new_quotient_rank_by_total_word_degree",
        )
        union_profiles[key] = _profile_from_report(
            cell.get("predecessor_union_rank_by_total_word_degree", {}),
            f"{_cell_id(key)} predecessor_union_rank_by_total_word_degree",
        )
        if _profile_sum(rank_profiles[key]) != ranks[key]:
            raise LedgerUnresolved(
                "unresolved_degree_profile_mismatch",
                "a Phase 30 rank profile does not sum to its rank",
                cell=_cell_label(key),
                profile_total=_paired(_profile_sum(rank_profiles[key])),
                rank=_paired(ranks[key]),
            )
        if _profile_sum(q_profiles[key]) != q_reported[key]:
            raise LedgerUnresolved(
                "unresolved_degree_profile_mismatch",
                "a Phase 30 quotient profile does not sum to its quotient dimension",
                cell=_cell_label(key),
                profile_total=_paired(_profile_sum(q_profiles[key])),
                quotient=_paired(q_reported[key]),
            )
        for field in ("basis_entries", "new_directions"):
            entries = cell.get(field, [])
            if not isinstance(entries, list):
                raise TypeError(f"{_cell_id(key)} {field} must be a list")
            for index, entry in enumerate(entries):
                _validate_degree_vector(
                    entry,
                    f"PHASE30:{_cell_id(key)}:{field}:{index:05d}",
                    "phase30",
                    counter,
                )

    for key in sorted(cells):
        length, degree = key
        if length == 1 and degree == 0:
            expected_q = ranks[key]
            expected_profile = dict(rank_profiles[key])
        elif degree == 0:
            expected_q = ranks[key] - ranks[(length - 1, 0)]
            expected_profile = _profile_difference(
                rank_profiles[key], rank_profiles[(length - 1, 0)]
            )
        elif length == 1:
            expected_q = ranks[(1, degree)] - ranks[(1, degree - 1)]
            expected_profile = _profile_difference(
                rank_profiles[(1, degree)], rank_profiles[(1, degree - 1)]
            )
        else:
            continue
        if q_reported[key] != expected_q or q_profiles[key] != expected_profile:
            raise LedgerUnresolved(
                "unresolved_boundary_quotient_mismatch",
                "a Phase 30 axis quotient disagrees with the one-sided rank difference",
                cell=_cell_label(key),
                reported_q=_paired(q_reported[key]),
                derived_q=_paired(expected_q),
                reported_profile=_profile_report(q_profiles[key]),
                derived_profile=_profile_report(expected_profile),
            )

    return {
        "cells": cells,
        "keys": tuple(sorted(cells)),
        "ranks": ranks,
        "q_reported": q_reported,
        "rank_profiles": rank_profiles,
        "q_profiles": q_profiles,
        "union_profiles": union_profiles,
        "config": {
            key: filtration_result[key]
            for key in _SHARED_CONFIG_KEYS
            if key in filtration_result
        },
        "max_l": max_l,
        "max_d": max_d,
    }


def _expected_square_keys(index):
    return {
        (length, degree)
        for length in range(2, index["max_l"] + 1)
        for degree in range(1, index["max_d"] + 1)
    }


def _index_bifiltration(bifiltration_result, filtration_index, counter, max_squares: int):
    if not isinstance(bifiltration_result, dict):
        raise TypeError("bifiltration_result must be a mapping")
    if bifiltration_result.get("schema", _BIFILTRATION_SCHEMA) != _BIFILTRATION_SCHEMA:
        raise LedgerUnresolved(
            "unresolved_source_schema",
            "the Phase 32 source schema is not supported",
            source_schema=bifiltration_result.get("schema"),
        )
    if bifiltration_result.get("status") != "complete_exact_bifiltration_operators":
        return _unresolved(
            "unresolved_source_bifiltration",
            "Phase 33 requires a complete Phase 32 bifiltration result",
            source_bifiltration_status=bifiltration_result.get("status"),
        )
    if bifiltration_result.get("source_filtration_status") != "complete_bounded_filtration":
        raise LedgerUnresolved(
            "unresolved_source_config_mismatch",
            "the Phase 32 source filtration status does not match Phase 30",
            phase32_status=bifiltration_result.get("source_filtration_status"),
            phase30_status="complete_bounded_filtration",
        )
    if bifiltration_result.get("coefficient_field", "Q") != "Q":
        raise LedgerUnresolved(
            "unresolved_source_config_mismatch",
            "the Phase 32 coefficient field is not Q",
            coefficient_field=bifiltration_result.get("coefficient_field"),
        )

    for key in _SHARED_CONFIG_KEYS:
        if (
            key in bifiltration_result
            and key in filtration_result_config(filtration_index)
            and bifiltration_result[key] != filtration_result_config(filtration_index)[key]
        ):
            raise LedgerUnresolved(
                "unresolved_source_config_mismatch",
                "shared Phase 30 and Phase 32 configuration values disagree",
                field=key,
                phase30_value=filtration_result_config(filtration_index)[key],
                phase32_value=bifiltration_result[key],
            )

    cell_count = _decode(
        bifiltration_result["cell_count"], "Phase 32 cell_count", 0
    )
    if cell_count != len(filtration_index["keys"]):
        raise LedgerUnresolved(
            "unresolved_source_config_mismatch",
            "the Phase 32 cell count does not match the Phase 30 grid",
            phase32_cell_count=_paired(cell_count),
            phase30_cell_count=_paired(len(filtration_index["keys"])),
        )
    square_count = _decode(
        bifiltration_result["square_count"], "Phase 32 square_count", 0
    )
    expected_keys = _expected_square_keys(filtration_index)
    if square_count != len(expected_keys):
        raise LedgerUnresolved(
            "unresolved_source_config_mismatch",
            "the Phase 32 square count does not match the Phase 30 grid",
            phase32_square_count=_paired(square_count),
            derived_square_count=_paired(len(expected_keys)),
        )

    raw_squares = bifiltration_result.get("squares")
    if not isinstance(raw_squares, list):
        raise TypeError("completed bifiltration must contain a squares list")
    if not raw_squares:
        return _unresolved(
            "unresolved_empty_source",
            "the completed Phase 32 result contains no unit squares",
        )
    if len(raw_squares) > max_squares:
        return _unresolved(
            "unresolved_square_cap",
            "the supplied bifiltration exceeds max_squares",
            square_count=_paired(len(raw_squares)),
            cap=_paired(max_squares),
        )

    squares = {}
    for index, square in enumerate(raw_squares):
        if not isinstance(square, dict):
            raise TypeError(f"bifiltration square {index} must be a mapping")
        terminal = _parse_cell_key(square.get("terminal_cell"), f"square {index} terminal_cell")
        if terminal in squares:
            raise LedgerUnresolved(
                "unresolved_duplicate_square",
                "the Phase 32 source contains duplicate square terminals",
                cell=_cell_label(terminal),
            )
        expected_edges = {
            "source_cell": (terminal[0] - 1, terminal[1] - 1),
            "left_predecessor": (terminal[0] - 1, terminal[1]),
            "bottom_predecessor": (terminal[0], terminal[1] - 1),
        }
        for field, expected_key in expected_edges.items():
            actual = _parse_cell_key(square.get(field), f"square {index} {field}")
            if actual != expected_key:
                raise LedgerUnresolved(
                    "unresolved_square_grid_mismatch",
                    "a Phase 32 square edge is incompatible with its terminal cell",
                    terminal=_cell_label(terminal),
                    field=field,
                    expected=_cell_label(expected_key),
                    actual=_cell_label(actual),
                )
        squares[terminal] = square

    if set(squares) != expected_keys:
        raise LedgerUnresolved(
            "unresolved_square_grid_mismatch",
            "the Phase 32 square terminals are not the interior cells of the Phase 30 grid",
            missing_squares=[_cell_label(key) for key in sorted(expected_keys - set(squares))],
            extra_squares=[_cell_label(key) for key in sorted(set(squares) - expected_keys)],
        )

    boundary_keys = set(filtration_index["keys"]) - expected_keys
    reported_boundary = set()
    raw_boundary = bifiltration_result.get("boundary_cells", [])
    if not isinstance(raw_boundary, list):
        raise TypeError("Phase 32 boundary_cells must be a list")
    for index, cell in enumerate(raw_boundary):
        reported_boundary.add(_parse_cell_key(cell, f"boundary cell {index}"))
    if reported_boundary != boundary_keys:
        raise LedgerUnresolved(
            "unresolved_boundary_cell_mismatch",
            "the Phase 32 boundary cells do not match the Phase 30 grid axes",
            missing=[_cell_label(key) for key in sorted(boundary_keys - reported_boundary)],
            extra=[_cell_label(key) for key in sorted(reported_boundary - boundary_keys)],
        )

    overlap_index = {}
    for key in sorted(squares):
        square = squares[key]
        dimensions = square.get("dimensions")
        if not isinstance(dimensions, dict):
            raise TypeError(f"{_cell_id(key)} dimensions must be a mapping")
        parsed = {
            name: _decode(
                dimensions[name],
                f"{_cell_id(key)} {name}",
                0 if name != "rank_difference" else None,
            )
            for name in (
                "source",
                "left",
                "bottom",
                "terminal",
                "intersection",
                "union",
                "quotient_q",
                "mixed_overlap_omega",
                "rank_difference",
            )
        }
        expected_ranks = {
            "source": filtration_index["ranks"][(key[0] - 1, key[1] - 1)],
            "left": filtration_index["ranks"][(key[0] - 1, key[1])],
            "bottom": filtration_index["ranks"][(key[0], key[1] - 1)],
            "terminal": filtration_index["ranks"][key],
            "quotient_q": filtration_index["q_reported"][key],
        }
        for name, expected in expected_ranks.items():
            if parsed[name] != expected:
                raise LedgerUnresolved(
                    "unresolved_square_dimension_mismatch",
                    "a Phase 32 dimension disagrees with its Phase 30 source cell",
                    terminal=_cell_label(key),
                    field=name,
                    phase32_value=_paired(parsed[name]),
                    phase30_value=_paired(expected),
                )

        overlap = square.get("mixed_overlap")
        if not isinstance(overlap, dict):
            raise TypeError(f"{_cell_id(key)} mixed_overlap must be a mapping")
        complement = overlap.get("complement_basis")
        if not isinstance(complement, list):
            raise TypeError(f"{_cell_id(key)} complement_basis must be a list")
        omega_profile = {}
        for position, entry in enumerate(complement):
            degree = _validate_degree_vector(
                entry,
                f"PHASE32:{_cell_id(key)}:complement_basis:{position:05d}",
                "phase32",
                counter,
            )
            omega_profile[degree] = omega_profile.get(degree, 0) + 1
        if parsed["mixed_overlap_omega"] != len(complement):
            raise LedgerUnresolved(
                "unresolved_square_dimension_mismatch",
                "the Phase 32 omega does not match its complement basis cardinality",
                terminal=_cell_label(key),
                reported_omega=_paired(parsed["mixed_overlap_omega"]),
                complement_count=_paired(len(complement)),
            )
        identity_checks = {
            "intersection": parsed["intersection"] == parsed["source"] + len(complement),
            "union": parsed["union"] == parsed["left"] + parsed["bottom"] - parsed["intersection"],
            "terminal": parsed["terminal"] == parsed["union"] + parsed["quotient_q"],
            "rank_difference": parsed["rank_difference"]
            == parsed["terminal"] - parsed["left"] - parsed["bottom"] + parsed["source"],
            "q_minus_omega": parsed["rank_difference"]
            == parsed["quotient_q"] - parsed["mixed_overlap_omega"],
        }
        if not all(identity_checks.values()):
            raise LedgerUnresolved(
                "unresolved_square_dimension_mismatch",
                "a Phase 32 square fails its own exact dimension identities",
                terminal=_cell_label(key),
                failed_checks=sorted(name for name, ok in identity_checks.items() if not ok),
                dimensions={name: _paired(value) for name, value in sorted(parsed.items())},
            )
        overlap_index[key] = {
            "omega": len(complement),
            "omega_profile": dict(sorted(omega_profile.items())),
            "dimensions": parsed,
            "complement_count": len(complement),
        }
    return {"squares": squares, "overlap": overlap_index}


def filtration_result_config(filtration_index):
    """Return the configuration fields of the indexed Phase 30 source."""
    return dict(filtration_index.get("config", {}))


def _rank_at(ranks, key):
    length, degree = key
    if length < 1 or degree < 0:
        return 0
    return ranks[(length, degree)]


def _profile_at(profiles, key):
    length, degree = key
    if length < 1 or degree < 0:
        return {}
    return profiles[(length, degree)]


def _rank_difference(ranks, key):
    length, degree = key
    return (
        _rank_at(ranks, (length, degree))
        - _rank_at(ranks, (length - 1, degree))
        - _rank_at(ranks, (length, degree - 1))
        + _rank_at(ranks, (length - 1, degree - 1))
    )


def _rank_difference_profile(rank_profiles, key):
    length, degree = key
    result = {}
    _profile_add(result, _profile_at(rank_profiles, (length, degree)), 1)
    _profile_add(result, _profile_at(rank_profiles, (length - 1, degree)), -1)
    _profile_add(result, _profile_at(rank_profiles, (length, degree - 1)), -1)
    _profile_add(result, _profile_at(rank_profiles, (length - 1, degree - 1)), 1)
    return {d: c for d, c in sorted(result.items()) if c}


def _cell_category(key):
    length, degree = key
    if length == 1 and degree == 0:
        return "origin"
    if length == 1:
        return "multiplier_axis"
    if degree == 0:
        return "substitution_axis"
    return "interior"


def _build_cell_data(filtration_index, bifiltration_index):
    ledger = []
    ranks = filtration_index["ranks"]
    rank_profiles = filtration_index["rank_profiles"]
    q_profiles = filtration_index["q_profiles"]
    delta_profiles = {}
    omega_profiles = {}
    omegas = {}
    for key in filtration_index["keys"]:
        length, degree = key
        category = _cell_category(key)
        overlap = bifiltration_index["overlap"].get(key)
        if category == "interior":
            if overlap is None:
                raise LedgerUnresolved(
                    "unresolved_square_grid_mismatch",
                    "an interior cell has no Phase 32 square",
                    cell=_cell_label(key),
                )
            omega = overlap["omega"]
            omega_profile = dict(overlap["omega_profile"])
            omega_source = "phase32_mixed_overlap_complement"
        else:
            omega = 0
            omega_profile = {}
            omega_source = "boundary_convention_zero"
        q = filtration_index["q_reported"][key]
        delta = q - omega
        rank_diff = _rank_difference(ranks, key)
        if delta != rank_diff:
            raise LedgerUnresolved(
                "unresolved_local_rank_identity_mismatch",
                "q - omega does not equal the mixed rank difference",
                cell=_cell_label(key),
                q=_paired(q),
                omega=_paired(omega),
                rank_difference=_paired(rank_diff),
            )
        delta_profile = _profile_difference(q_profiles[key], omega_profile)
        rank_diff_profile = _rank_difference_profile(rank_profiles, key)
        if delta_profile != rank_diff_profile:
            raise LedgerUnresolved(
                "unresolved_degree_local_mismatch",
                "the degree-resolved q - omega profile does not equal the rank finite difference",
                cell=_cell_label(key),
                delta_profile=_profile_report(delta_profile),
                rank_difference_profile=_profile_report(rank_diff_profile),
            )
        if category == "interior":
            expected_union = {}
            _profile_add(expected_union, rank_profiles[(length - 1, degree)], 1)
            _profile_add(expected_union, rank_profiles[(length, degree - 1)], 1)
            _profile_add(expected_union, rank_profiles[(length - 1, degree - 1)], -1)
            _profile_add(expected_union, omega_profile, -1)
            if filtration_index["union_profiles"][key] != expected_union:
                raise LedgerUnresolved(
                    "unresolved_degree_union_profile_mismatch",
                    "the Phase 30 predecessor-union degree profile disagrees with q and omega",
                    cell=_cell_label(key),
                    reported_profile=_profile_report(filtration_index["union_profiles"][key]),
                    derived_profile=_profile_report(expected_union),
                )
        omegas[key] = omega
        omega_profiles[key] = dict(sorted(omega_profile.items()))
        delta_profiles[key] = dict(sorted(delta_profile.items()))
        ledger.append(
            {
                "cell": _cell_label(key),
                "category": category,
                "actual_phase30_cell": True,
                "terminal_phase32_square": category == "interior",
                "rank": _paired(ranks[key]),
                "rank_by_degree": _profile_report(rank_profiles[key]),
                "q": _paired(q),
                "q_by_degree": _profile_report(q_profiles[key]),
                "omega": _paired(omega),
                "omega_by_degree": _profile_report(omega_profile),
                "omega_source": omega_source,
                "delta": _paired(delta),
                "delta_by_degree": _profile_report(delta_profile),
                "mixed_rank_difference": _paired(rank_diff),
                "mixed_rank_difference_by_degree": _profile_report(rank_diff_profile),
                "local_identity_verified": True,
            }
        )
    return {
        "ledger": ledger,
        "ranks": ranks,
        "rank_profiles": rank_profiles,
        "q_profiles": q_profiles,
        "q_reported": filtration_index["q_reported"],
        "omegas": omegas,
        "omega_profiles": omega_profiles,
        "delta_profiles": delta_profiles,
    }


def _rect_sum(profile_map, a, b, c, d):
    result = {}
    for length in range(a, b + 1):
        for degree in range(c, d + 1):
            _profile_add(result, profile_map[(length, degree)], 1)
    return {key: value for key, value in sorted(result.items()) if value}


def _prefix_certificates(data):
    certificates = []
    for length in range(1, data["max_l"] + 1):
        for degree in range(0, data["max_d"] + 1):
            endpoint = (length, degree)
            summed_profile = _rect_sum(data["delta_profiles"], 1, length, 0, degree)
            summed = sum(data["q_reported"][key] - data["omegas"][key]
                         for key in data["delta_profiles"]
                         if 1 <= key[0] <= length and 0 <= key[1] <= degree)
            expected = data["ranks"][endpoint]
            expected_profile = dict(data["rank_profiles"][endpoint])
            if summed != expected or summed_profile != expected_profile:
                raise LedgerUnresolved(
                    "unresolved_prefix_identity_mismatch",
                    "a prefix telescoping identity failed",
                    endpoint=_cell_label(endpoint),
                    summed=_paired(summed),
                    rank=_paired(expected),
                    summed_profile=_profile_report(summed_profile),
                    rank_profile=_profile_report(expected_profile),
                )
            certificates.append(
                {
                    "endpoint": _cell_label(endpoint),
                    "sum_delta": _paired(summed),
                    "rank": _paired(expected),
                    "sum_delta_by_degree": _profile_report(summed_profile),
                    "rank_by_degree": _profile_report(expected_profile),
                    "verified": True,
                }
            )
    return certificates


def _rectangle_bounds(rectangle, data, name: str):
    if isinstance(rectangle, dict):
        values = (
            rectangle.get("substitution_min"),
            rectangle.get("substitution_max"),
            rectangle.get("multiplier_min"),
            rectangle.get("multiplier_max"),
        )
    elif isinstance(rectangle, (tuple, list)) and len(rectangle) == 4:
        values = rectangle
    else:
        raise TypeError(f"{name} must be a four-item mapping or sequence")
    a = _decode(values[0], f"{name} substitution_min", 0)
    b = _decode(values[1], f"{name} substitution_max", 0)
    c = _decode(values[2], f"{name} multiplier_min", 0)
    d = _decode(values[3], f"{name} multiplier_max", 0)
    if not (1 <= a <= b <= data["max_l"] and 0 <= c <= d <= data["max_d"]):
        raise LedgerUnresolved(
            "unresolved_rectangle_out_of_range",
            "a requested rectangle is not valid inside the supplied grid",
            rectangle={"a": _paired(a), "b": _paired(b), "c": _paired(c), "d": _paired(d)},
        )
    return (a, b, c, d)


def _all_rectangle_bounds(data):
    return [
        (a, b, c, d)
        for a in range(1, data["max_l"] + 1)
        for b in range(a, data["max_l"] + 1)
        for c in range(0, data["max_d"] + 1)
        for d in range(c, data["max_d"] + 1)
    ]


def _corner_rectangle_bounds(data):
    length = data["max_l"]
    degree = data["max_d"]
    candidates = [
        (1, 1, 0, 0),
        (length, length, 0, 0),
        (1, 1, degree, degree),
        (1, length, 0, 0),
        (1, 1, 0, degree),
        (1, length, 0, degree),
    ]
    result = []
    for bounds in candidates:
        if bounds not in result:
            result.append(bounds)
    return result


def _rectangle_certificate(data, bounds, source: str):
    a, b, c, d = bounds
    summed_profile = _rect_sum(data["delta_profiles"], a, b, c, d)
    summed = sum(data["q_reported"][key] - data["omegas"][key]
                 for key in data["delta_profiles"]
                 if a <= key[0] <= b and c <= key[1] <= d)
    rhs = (
        _rank_at(data["ranks"], (b, d))
        - _rank_at(data["ranks"], (a - 1, d))
        - _rank_at(data["ranks"], (b, c - 1))
        + _rank_at(data["ranks"], (a - 1, c - 1))
    )
    rhs_profile = {}
    _profile_add(rhs_profile, _profile_at(data["rank_profiles"], (b, d)), 1)
    _profile_add(rhs_profile, _profile_at(data["rank_profiles"], (a - 1, d)), -1)
    _profile_add(rhs_profile, _profile_at(data["rank_profiles"], (b, c - 1)), -1)
    _profile_add(rhs_profile, _profile_at(data["rank_profiles"], (a - 1, c - 1)), 1)
    rhs_profile = {key: value for key, value in sorted(rhs_profile.items()) if value}
    if summed != rhs or summed_profile != rhs_profile:
        raise LedgerUnresolved(
            "unresolved_rectangle_identity_mismatch",
            "a subrectangle telescoping identity failed",
            rectangle={"a": _paired(a), "b": _paired(b), "c": _paired(c), "d": _paired(d)},
            sum_delta=_paired(summed),
            rank_difference=_paired(rhs),
            sum_delta_by_degree=_profile_report(summed_profile),
            rank_difference_by_degree=_profile_report(rhs_profile),
        )
    return {
        "rectangle": {
            "substitution_min": _paired(a),
            "substitution_max": _paired(b),
            "multiplier_min": _paired(c),
            "multiplier_max": _paired(d),
        },
        "sum_delta": _paired(summed),
        "rank_difference": _paired(rhs),
        "sum_delta_by_degree": _profile_report(summed_profile),
        "rank_difference_by_degree": _profile_report(rhs_profile),
        "verified": True,
        "check_source": source,
    }


def _rectangle_certificates(data, rectangles, exhaustive: bool, cap: int):
    corner_bounds = _corner_rectangle_bounds(data)
    selected_bounds = []
    if rectangles is not None:
        if not isinstance(rectangles, (list, tuple)):
            raise TypeError("rectangles must be a list, tuple, or None")
        for index, rectangle in enumerate(rectangles):
            selected_bounds.append(
                _rectangle_bounds(rectangle, data, f"rectangles[{index}]")
            )
    exhaustive_bounds = _all_rectangle_bounds(data) if exhaustive else []
    exhaustive_count = len(exhaustive_bounds)

    if exhaustive:
        if exhaustive_count > cap:
            available_corners = corner_bounds[:cap]
            corner_note = (
                "All deterministic corners were checked."
                if len(available_corners) == len(corner_bounds)
                else "The cap is smaller than the deterministic corner family; only its "
                     "first entries were checked."
            )
            return {
                "status": "unresolved_rectangle_cap",
                "scope": "corner_only_exhaustion_capped",
                "exhaustive": True,
                "required_checks": _paired(exhaustive_count),
                "cap": _paired(cap),
                "checked_count": _paired(len(available_corners)),
                "corner_checks": [
                    _rectangle_certificate(data, bounds, "corner")
                    for bounds in available_corners
                ],
                "selected_checks": [],
                "exhaustive_checks": [],
                "unresolved_semantics": (
                    "Exhaustive enumeration was not performed; these deterministic corner "
                    "certificates do not imply completion. " + corner_note
                ),
            }
        all_bounds = list(exhaustive_bounds)
        for bounds in corner_bounds + selected_bounds:
            if bounds not in all_bounds:
                all_bounds.append(bounds)
        if len(all_bounds) > cap:
            raise LedgerUnresolved(
                "unresolved_rectangle_cap",
                "the requested rectangle checks exceed max_rectangle_checks",
                required=_paired(len(all_bounds)),
                cap=_paired(cap),
            )
        return {
            "status": "complete_rectangle_checks",
            "scope": "exhaustive_plus_selected",
            "exhaustive": True,
            "required_checks": _paired(exhaustive_count),
            "cap": _paired(cap),
            "checked_count": _paired(len(all_bounds)),
            "corner_checks": [
                _rectangle_certificate(data, bounds, "corner") for bounds in corner_bounds
            ],
            "selected_checks": [
                _rectangle_certificate(data, bounds, "selected") for bounds in selected_bounds
            ],
            "exhaustive_checks": [
                _rectangle_certificate(data, bounds, "exhaustive") for bounds in exhaustive_bounds
            ],
            "unresolved_semantics": (
                "All valid subrectangles of the supplied grid were checked exactly."
            ),
        }

    all_bounds = list(corner_bounds)
    for bounds in selected_bounds:
        if bounds not in all_bounds:
            all_bounds.append(bounds)
    if len(all_bounds) > cap:
        raise LedgerUnresolved(
            "unresolved_rectangle_cap",
            "the requested rectangle checks exceed max_rectangle_checks",
            required=_paired(len(all_bounds)),
            cap=_paired(cap),
        )
    return {
        "status": "complete_selected_rectangle_checks",
        "scope": "selected_plus_corners",
        "exhaustive": False,
        "required_checks": _paired(len(all_bounds)),
        "cap": _paired(cap),
        "checked_count": _paired(len(all_bounds)),
        "corner_checks": [
            _rectangle_certificate(data, bounds, "corner") for bounds in corner_bounds
        ],
        "selected_checks": [
            _rectangle_certificate(data, bounds, "selected") for bounds in selected_bounds
        ],
        "exhaustive_checks": [],
        "unresolved_semantics": (
            "Completion refers only to the explicitly requested rectangles and "
            "deterministic corners; it is not an exhaustive claim."
        ),
    }


def _row_column_accumulations(data):
    rows = []
    columns = []
    for length in range(1, data["max_l"] + 1):
        running = 0
        profile = {}
        for degree in range(0, data["max_d"] + 1):
            key = (length, degree)
            running += data["q_reported"][key] - data["omegas"][key]
            _profile_add(profile, data["delta_profiles"][key], 1)
            edge = data["ranks"][(length, degree)] - _rank_at(
                data["ranks"], (length - 1, degree)
            )
            edge_profile = _profile_difference(
                data["rank_profiles"][(length, degree)],
                _profile_at(data["rank_profiles"], (length - 1, degree)),
            )
            if running != edge or profile != edge_profile:
                raise LedgerUnresolved(
                    "unresolved_row_accumulation_mismatch",
                    "a row cumulative increment does not equal the rank edge difference",
                    cell=_cell_label(key),
                    cumulative=_paired(running),
                    edge_difference=_paired(edge),
                )
            rows.append(
                {
                    "substitution_bound": _paired(length),
                    "multiplier_upper": _paired(degree),
                    "cumulative_delta": _paired(running),
                    "rank_edge_difference": _paired(edge),
                    "cumulative_delta_by_degree": _profile_report(profile),
                    "rank_edge_difference_by_degree": _profile_report(edge_profile),
                    "verified": True,
                }
            )
    for degree in range(0, data["max_d"] + 1):
        running = 0
        profile = {}
        for length in range(1, data["max_l"] + 1):
            key = (length, degree)
            running += data["q_reported"][key] - data["omegas"][key]
            _profile_add(profile, data["delta_profiles"][key], 1)
            edge = data["ranks"][(length, degree)] - _rank_at(
                data["ranks"], (length, degree - 1)
            )
            edge_profile = _profile_difference(
                data["rank_profiles"][(length, degree)],
                _profile_at(data["rank_profiles"], (length, degree - 1)),
            )
            if running != edge or profile != edge_profile:
                raise LedgerUnresolved(
                    "unresolved_column_accumulation_mismatch",
                    "a column cumulative increment does not equal the rank edge difference",
                    cell=_cell_label(key),
                    cumulative=_paired(running),
                    edge_difference=_paired(edge),
                )
            columns.append(
                {
                    "multiplier_bound": _paired(degree),
                    "substitution_upper": _paired(length),
                    "cumulative_delta": _paired(running),
                    "rank_edge_difference": _paired(edge),
                    "cumulative_delta_by_degree": _profile_report(profile),
                    "rank_edge_difference_by_degree": _profile_report(edge_profile),
                    "verified": True,
                }
            )
    return {"rows": rows, "columns": columns}


def _degree_profiles(data):
    cells = {}
    q_totals = {}
    omega_totals = {}
    delta_totals = {}
    for key in data["ranks"]:
        q_profile = data["q_profiles"][key]
        omega_profile = data["omega_profiles"][key]
        delta_profile = data["delta_profiles"][key]
        _profile_add(q_totals, q_profile, 1)
        _profile_add(omega_totals, omega_profile, 1)
        _profile_add(delta_totals, delta_profile, 1)
        cells[_cell_id(key)] = {
            "cell": _cell_label(key),
            "rank_by_degree": _profile_report(data["rank_profiles"][key]),
            "q_by_degree": _profile_report(q_profile),
            "omega_by_degree": _profile_report(omega_profile),
            "delta_by_degree": _profile_report(delta_profile),
        }
    terminal = (data["max_l"], data["max_d"])
    final_profile = dict(data["rank_profiles"][terminal])
    if delta_totals != final_profile:
        raise LedgerUnresolved(
            "unresolved_degree_total_mismatch",
            "summing degree-resolved increments does not reproduce the terminal rank profile",
            delta_totals=_profile_report(delta_totals),
            terminal_rank_profile=_profile_report(final_profile),
        )
    return {
        "cells": cells,
        "totals": {
            "q_by_degree": _profile_report(q_totals),
            "omega_by_degree": _profile_report(omega_totals),
            "delta_by_degree": _profile_report(delta_totals),
            "terminal_rank_by_degree": _profile_report(final_profile),
            "degree_totals_verified": True,
        },
        "aggregation_semantics": (
            "Per-degree profiles are added degree by degree; no coercion, bucket "
            "merging or floating-point tolerance is used."
        ),
    }


def _totals(data):
    sum_q = sum(data["q_reported"].values())
    sum_omega = sum(data["omegas"].values())
    sum_delta = sum_q - sum_omega
    final_rank = data["ranks"][(data["max_l"], data["max_d"])]
    if sum_delta != final_rank:
        raise LedgerUnresolved(
            "unresolved_total_reconciliation_mismatch",
            "sum(q - omega) does not equal the terminal rank",
            sum_q=_paired(sum_q),
            sum_omega=_paired(sum_omega),
            sum_delta=_paired(sum_delta),
            final_rank=_paired(final_rank),
        )
    return {
        "sum_q": _paired(sum_q),
        "sum_omega": _paired(sum_omega),
        "sum_delta": _paired(sum_delta),
        "final_rank": _paired(final_rank),
        "equality_verified": True,
        "sum_q_semantics": (
            "sum_q is only the total of finite predecessor-union quotient "
            "increments over the supplied grid, not a set of infinite ideal generators."
        ),
    }


def _caps_report(max_rectangle_checks, max_cells, max_squares, max_degree_vector_checks):
    return {
        "max_rectangle_checks": _paired(max_rectangle_checks),
        "max_cells": _paired(max_cells),
        "max_squares": _paired(max_squares),
        "max_degree_vector_checks": _paired(max_degree_vector_checks),
    }


def analyze_exact_bifiltration_rank_ledger(
    filtration_result,
    bifiltration_result,
    *,
    max_rectangle_checks: int = DEFAULT_MAX_RECTANGLE_CHECKS,
    max_cells: int = DEFAULT_MAX_CELLS,
    max_squares: int = DEFAULT_MAX_SQUARES,
    max_degree_vector_checks: int = DEFAULT_MAX_DEGREE_VECTOR_CHECKS,
    rectangles=None,
    verify_all_rectangles: bool = True,
):
    """Build an exact rank ledger from completed Phase 30 and Phase 32 results.

    ``rectangles`` is an optional collection of selected subrectangles; each may
    be ``(a, b, c, d)`` or a mapping with ``substitution_min``,
    ``substitution_max``, ``multiplier_min`` and ``multiplier_max``. With
    ``verify_all_rectangles=True`` every valid subrectangle of small grids is
    checked; when the enumerated count exceeds ``max_rectangle_checks`` the
    status is explicitly unresolved and only deterministic corners are checked.
    """
    max_rectangle_checks = _decode(max_rectangle_checks, "max_rectangle_checks", 1)
    max_cells = _decode(max_cells, "max_cells", 1)
    max_squares = _decode(max_squares, "max_squares", 1)
    max_degree_vector_checks = _decode(
        max_degree_vector_checks, "max_degree_vector_checks", 1
    )
    caps = _caps_report(
        max_rectangle_checks, max_cells, max_squares, max_degree_vector_checks
    )
    counter = {"count": 0, "limit": max_degree_vector_checks}
    try:
        filtration_index = _index_filtration(filtration_result, counter, max_cells)
        if isinstance(filtration_index, dict) and filtration_index.get("schema") == _SCHEMA:
            return {**filtration_index, "caps": caps}
        bifiltration_index = _index_bifiltration(
            bifiltration_result, filtration_index, counter, max_squares
        )
        if isinstance(bifiltration_index, dict) and bifiltration_index.get("schema") == _SCHEMA:
            return {**bifiltration_index, "caps": caps}
        data = _build_cell_data(filtration_index, bifiltration_index)
        data["max_l"] = filtration_index["max_l"]
        data["max_d"] = filtration_index["max_d"]
        degree_profiles = _degree_profiles(data)
        prefix_certificates = _prefix_certificates(data)
        row_column = _row_column_accumulations(data)
        totals = _totals(data)
        rectangle_checks = _rectangle_certificates(
            data, rectangles, bool(verify_all_rectangles), max_rectangle_checks
        )
    except LedgerUnresolved as exc:
        return _unresolved(exc.status, exc.reason, caps=caps, **exc.details)

    status = (
        _COMPLETE_STATUS
        if rectangle_checks["status"]
        in ("complete_rectangle_checks", "complete_selected_rectangle_checks")
        else rectangle_checks["status"]
    )
    return {
        "schema": _SCHEMA,
        "status": status,
        "coefficient_field": "Q",
        "floating_point_used": False,
        "source_schemas": {
            "filtration": _FILTRATION_SCHEMA,
            "bifiltration": _BIFILTRATION_SCHEMA,
        },
        "source_statuses": {
            "filtration": filtration_result["status"],
            "bifiltration": bifiltration_result["status"],
        },
        "source_configuration": {
            "filtration": filtration_result_config(filtration_index),
            "bifiltration": {
                key: bifiltration_result[key]
                for key in (
                    "cell_count",
                    "square_count",
                    "coefficient_field",
                    "caps",
                )
                if key in bifiltration_result
            },
        },
        "grid": {
            "substitution_min": _paired(1),
            "substitution_max": _paired(data["max_l"]),
            "multiplier_min": _paired(0),
            "multiplier_max": _paired(data["max_d"]),
            "actual_cell_count": _paired(len(data["ranks"])),
            "interior_square_count": _paired(len(bifiltration_index["overlap"])),
        },
        "cell_ledger": data["ledger"],
        "degree_profiles": degree_profiles,
        "prefix_certificates": prefix_certificates,
        "rectangle_checks": rectangle_checks,
        "row_column_accumulations": row_column,
        "totals": totals,
        "caps": caps,
        "boundary_conventions": {
            "formal_zero_values": ["r[0,D] = 0", "r[L,-1] = 0"],
            "formal_zero_usage": (
                "Used only inside prefix, subrectangle and row/column finite-difference "
                "formulas. No formal boundary value is emitted as a Phase 30 cell."
            ),
            "axis_q": [
                "q[1,0] = r[1,0]",
                "q[L,0] = r[L,0] - r[L-1,0] for L > 1",
                "q[1,D] = r[1,D] - r[1,D-1] for D > 0",
            ],
            "axis_omega": (
                "omega = 0 on L=1 or D=0 solely because no Phase 32 unit square "
                "exists there."
            ),
            "actual_cells_only": [_cell_label(key) for key in filtration_index["keys"]],
            "no_fabricated_cells": True,
        },
        "public_query_api": {
            "function": "check_rectangle",
            "semantics": (
                "check_rectangle(analysis, a, b, c, d) validates one selected "
                "subrectangle against the returned ledger, without sampling."
            ),
        },
        "cap_semantics": {
            "max_rectangle_checks": (
                "If exhaustive rectangle enumeration exceeds this cap, status is "
                "explicitly unresolved_rectangle_cap and only deterministic corners "
                "are reported; this is never presented as exhaustive completion."
            ),
            "max_cells": "Rejects filtrations larger than the declared grid budget.",
            "max_squares": "Rejects bifiltrations larger than the declared square budget.",
            "max_degree_vector_checks": (
                "Bounds exact homogeneity inspection of Phase 30 and Phase 32 basis vectors."
            ),
        },
        "exact_rational_conventions": {
            "integer_encoding": "paired binary/ternary strings via phase29._paired",
            "rational_encoding": "exact numerator/denominator paired-integer reports",
            "example_one_half": _rational_report(Fraction(1, 2), "example rational"),
            "rank_identities_use_integers_only": True,
        },
        "epistemic_boundary": (
            "Finite telescoping over the supplied completed grid only. No claim of "
            "an infinite Hilbert series, global recurrence, distributivity or minimal "
            "generating set of the infinite T-ideal is made."
        ),
    }


def check_rectangle(analysis, a, b, c, d):
    """Validate one selected subrectangle against a returned analysis dict."""
    if not isinstance(analysis, dict):
        raise TypeError("analysis must be the mapping returned by the ledger analyzer")
    if "cell_ledger" not in analysis or "degree_profiles" not in analysis:
        raise ValueError("analysis is missing the cell ledger or degree profiles")
    required = {"substitution_min", "substitution_max", "multiplier_min", "multiplier_max"}
    if not required.issubset(set(analysis.get("grid", {}))):
        raise ValueError("analysis grid metadata is incomplete")
    data = {
        "max_l": _decode(analysis["grid"]["substitution_max"], "grid substitution_max", 0),
        "max_d": _decode(analysis["grid"]["multiplier_max"], "grid multiplier_max", 0),
        "ranks": {},
        "rank_profiles": {},
        "q_reported": {},
        "omegas": {},
        "delta_profiles": {},
    }
    for row in analysis["cell_ledger"]:
        label = row["cell"]
        key = (
            _decode(label["substitution_bound"], "substitution_bound", 0),
            _decode(label["multiplier_bound"], "multiplier_bound", 0),
        )
        data["ranks"][key] = _decode(row["rank"], "rank", 0)
        data["rank_profiles"][key] = _profile_from_report(
            row["rank_by_degree"], "rank_by_degree"
        )
        data["q_reported"][key] = _decode(row["q"], "q", 0)
        data["omegas"][key] = _decode(row["omega"], "omega", 0)
        data["delta_profiles"][key] = _profile_from_report(
            row["delta_by_degree"], "delta_by_degree", minimum=None
        )
    bounds = _rectangle_bounds((a, b, c, d), data, "check_rectangle")
    try:
        return _rectangle_certificate(data, bounds, "query")
    except LedgerUnresolved as exc:
        return _unresolved(exc.status, exc.reason, **exc.details)


def analyze_bounded_exact_bifiltration_rank_ledger(
    filtration_options,
    *,
    max_rectangle_checks: int = DEFAULT_MAX_RECTANGLE_CHECKS,
    max_cells: int = DEFAULT_MAX_CELLS,
    max_squares: int = DEFAULT_MAX_SQUARES,
    max_degree_vector_checks: int = DEFAULT_MAX_DEGREE_VECTOR_CHECKS,
    rectangles=None,
    verify_all_rectangles: bool = True,
):
    """Explicitly run Phase 30, Phase 31 and Phase 32, then build the ledger.

    This wrapper is the only API in this module that recomputes upstream stages;
    the main analyzer consumes already completed results and never rebuilds an
    FTI catalogue or a Phase 32 square.
    """
    if not isinstance(filtration_options, dict):
        raise TypeError("filtration_options must be a mapping of Phase 30 keyword arguments")
    filtration = phase30.analyze_bounded_relation_filtration(**filtration_options)
    if filtration.get("status") != "complete_bounded_filtration":
        return _unresolved(
            "unresolved_source_filtration",
            "the explicitly requested Phase 30 run did not complete",
            source_filtration_status=filtration.get("status"),
        )
    transitions = phase31.analyze_exact_basis_transitions(filtration)
    if transitions.get("status") != "complete_exact_basis_transitions":
        return _unresolved(
            "unresolved_source_transitions",
            "the explicitly requested Phase 31 run did not complete",
            source_transition_status=transitions.get("status"),
        )
    bifiltration = phase32.analyze_exact_bifiltration_operators(filtration, transitions)
    return analyze_exact_bifiltration_rank_ledger(
        filtration,
        bifiltration,
        max_rectangle_checks=max_rectangle_checks,
        max_cells=max_cells,
        max_squares=max_squares,
        max_degree_vector_checks=max_degree_vector_checks,
        rectangles=rectangles,
        verify_all_rectangles=verify_all_rectangles,
    )


__all__ = [
    "analyze_exact_bifiltration_rank_ledger",
    "analyze_bounded_exact_bifiltration_rank_ledger",
    "check_rectangle",
    "DEFAULT_MAX_RECTANGLE_CHECKS",
    "DEFAULT_MAX_CELLS",
    "DEFAULT_MAX_SQUARES",
    "DEFAULT_MAX_DEGREE_VECTOR_CHECKS",
]
