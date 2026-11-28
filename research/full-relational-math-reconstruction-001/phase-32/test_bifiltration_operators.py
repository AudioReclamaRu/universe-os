import copy
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-27", "phase-28", "phase-29", "phase-30", "phase-31", "phase-32"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import basis_transitions as phase31
import relation_filtration as phase30
import trace_ideal_closure as phase29

from bifiltration_operators import (
    analyze_bounded_bifiltration_operators,
    analyze_exact_bifiltration_operators,
    _matrix_from_report,
)


def decode_pair(value):
    sign = -1 if value.startswith("-") else 1
    body = value.lstrip("-")
    return sign * int(body[1:body.index("_2|")], 2)


def paired(value):
    return phase29._paired(value)


def term(coefficient, *words):
    return {
        "coefficient": Fraction(coefficient),
        "trace_factors": [list(word) for word in words],
    }


def cell(substitution_bound, multiplier_bound, polynomials, rank, union, intersection, quotient):
    return {
        "substitution_bound": paired(substitution_bound),
        "multiplier_bound": paired(multiplier_bound),
        "status": "complete_bounded_relation_space",
        "relation_space_dimension": paired(rank),
        "predecessor_union_dimension": paired(union),
        "predecessor_intersection_dimension": paired(intersection),
        "new_quotient_dimension": paired(quotient),
        "basis_entries": [
            {"trace_terms": list(terms)}
            for terms in polynomials
        ],
        "new_directions": [],
    }


# Six distinct homogeneous degree-2 trace monomials. Keeping the synthetic
# fixtures homogeneous lets the existing Phase 31 serializers be reused.
M00_M00 = term(1, (0,), (0,))
M00_M01 = term(1, (0,), (1,))
M0_M0 = term(1, (0, 0))
M0_M1 = term(1, (0, 1))
M11_M11 = term(1, (1,), (1,))
M1_M1 = term(1, (1, 1))
U = term(1, (0,), (0,))
U_SECOND = term(Fraction(1, 2), (0,), (1,))


def nonzero_overlap_filtration(extend_l3=False):
    """Fixture with C=span{u}, A∩B=span{m00m00,m00m01}, omega=1."""
    u = [U, U_SECOND]
    cells = [
        cell(1, 0, [u], 1, 0, 0, 1),
        cell(1, 1, [[M00_M00], [M00_M01], [M11_M11]], 3, 1, 0, 2),
        cell(2, 0, [[M00_M00], [M00_M01], [M1_M1]], 3, 1, 0, 2),
        cell(2, 1, [[M00_M00], [M00_M01], [M11_M11], [M1_M1]], 4, 4, 2, 0),
    ]
    if extend_l3:
        cells.extend([
            cell(
                3,
                0,
                [[M00_M00], [M00_M01], [M1_M1], [M0_M0]],
                4,
                3,
                0,
                1,
            ),
            cell(
                3,
                1,
                [[M00_M00], [M00_M01], [M0_M0], [M11_M11], [M1_M1]],
                5,
                5,
                3,
                0,
            ),
        ])
    return {
        "status": "complete_bounded_filtration",
        "schema": "universe.trace-relation-filtration.v1",
        "cells": cells,
    }


def zero_overlap_filtration():
    """Fixture where A∩B is exactly the southwest predecessor C."""
    return {
        "status": "complete_bounded_filtration",
        "schema": "universe.trace-relation-filtration.v1",
        "cells": [
            cell(1, 0, [[M00_M00]], 1, 0, 0, 1),
            cell(1, 1, [[M00_M00], [M00_M01]], 2, 1, 0, 1),
            cell(2, 0, [[M00_M00], [M11_M11]], 2, 1, 0, 1),
            cell(2, 1, [[M00_M00], [M00_M01], [M11_M11]], 3, 3, 1, 0),
        ],
    }


def physical_arguments(**overrides):
    arguments = {
        "dimension": 2,
        "generator_count": 2,
        "max_substitution_word_length": 2,
        "max_multiplier_trace_word_length": 1,
        "max_multiplier_total_word_degree": 1,
        "max_filtration_cells": 4,
        "max_word_catalog_size": 8,
        "max_substitution_sets": 1000,
        "max_multiplier_monomials": 16,
        "max_derived_relations": 5000,
        "max_seed_expansion_terms_per_identity": 100_000,
        "max_seed_expansion_terms_per_cell": 2_000_000,
        "max_relation_expansion_terms_per_relation": 100_000,
        "max_relation_expansion_terms_per_cell": 2_000_000,
        "max_aggregate_seed_expansion_terms": 8_000_000,
        "max_aggregate_relation_expansion_terms": 12_000_000,
    }
    arguments.update(overrides)
    return arguments


def contains_float(value):
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(contains_float(item) for item in value)
    return False


class BifiltrationOperatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.physical_filtration = phase30.analyze_bounded_relation_filtration(
            **physical_arguments()
        )
        if cls.physical_filtration["status"] != "complete_bounded_filtration":
            raise AssertionError(cls.physical_filtration)
        cls.physical_transitions = phase31.analyze_exact_basis_transitions(
            cls.physical_filtration
        )
        if cls.physical_transitions["status"] != "complete_exact_basis_transitions":
            raise AssertionError(cls.physical_transitions)
        cls.physical_result = analyze_exact_bifiltration_operators(
            cls.physical_filtration, cls.physical_transitions
        )
        cls.nonzero_result = analyze_exact_bifiltration_operators(
            nonzero_overlap_filtration()
        )
        cls.zero_result = analyze_exact_bifiltration_operators(
            zero_overlap_filtration()
        )

    def test_small_completed_grid_commutes_and_direct_map_matches(self):
        self.assertEqual(
            self.physical_result["status"],
            "complete_exact_bifiltration_operators",
        )
        self.assertEqual(decode_pair(self.physical_result["square_count"]), 1)
        square = self.physical_result["squares"][0]
        proof = square["commutative_square"]
        bottom_path = _matrix_from_report(proof["bottom_path_product"], "bottom")
        left_path = _matrix_from_report(proof["left_path_product"], "left")
        direct = _matrix_from_report(proof["direct_source_to_terminal"], "direct")
        self.assertEqual(bottom_path, left_path)
        self.assertEqual(bottom_path, direct)
        self.assertTrue(proof["all_paths_equal_exactly"])

    def test_nonzero_mixed_overlap_fixture_is_detected(self):
        self.assertEqual(self.nonzero_result["status"], "complete_exact_bifiltration_operators")
        square = self.nonzero_result["squares"][0]
        dimensions = square["dimensions"]
        self.assertEqual(decode_pair(dimensions["mixed_overlap_omega"]), 1)
        self.assertEqual(
            square["mixed_overlap"]["status"],
            "nonzero_mixed_overlap",
        )
        self.assertEqual(
            len(square["mixed_overlap"]["complement_basis"]),
            decode_pair(dimensions["mixed_overlap_omega"]),
        )
        self.assertEqual(
            decode_pair(dimensions["source"]),
            1,
        )
        self.assertEqual(
            decode_pair(dimensions["intersection"]),
            2,
        )

    def test_zero_mixed_overlap_fixture_is_detected(self):
        self.assertEqual(self.zero_result["status"], "complete_exact_bifiltration_operators")
        square = self.zero_result["squares"][0]
        self.assertEqual(decode_pair(square["dimensions"]["mixed_overlap_omega"]), 0)
        self.assertEqual(
            square["mixed_overlap"]["status"],
            "zero_mixed_overlap",
        )
        self.assertEqual(square["mixed_overlap"]["complement_basis"], [])
        self.assertEqual(
            decode_pair(square["dimensions"]["intersection"]),
            decode_pair(square["dimensions"]["source"]),
        )

    def test_complement_is_independent_and_spans_the_quotient(self):
        for result in (self.nonzero_result, self.zero_result):
            square = result["squares"][0]
            overlap = square["mixed_overlap"]
            intersection_dimension = decode_pair(square["dimensions"]["intersection"])
            source_dimension = decode_pair(square["dimensions"]["source"])
            omega = decode_pair(square["dimensions"]["mixed_overlap_omega"])
            source_coordinates = _matrix_from_report(
                overlap["source_coordinates_in_intersection_basis"], "source coords"
            )
            complement_coordinates = _matrix_from_report(
                overlap["complement_coordinates_in_intersection_basis"], "complement coords"
            )
            self.assertEqual(
                phase31._matrix_rank(source_coordinates, intersection_dimension),
                source_dimension,
            )
            self.assertEqual(
                phase31._matrix_rank(complement_coordinates, intersection_dimension),
                omega,
            )
            self.assertEqual(
                phase31._matrix_rank(
                    source_coordinates + complement_coordinates,
                    intersection_dimension,
                ),
                intersection_dimension,
            )
            self.assertTrue(overlap["exact_independence_and_spanning_verified"])

    def test_all_rank_identities_hold_for_physical_and_synthetic_squares(self):
        extended = analyze_exact_bifiltration_operators(
            nonzero_overlap_filtration(extend_l3=True)
        )
        self.assertEqual(
            extended["status"],
            "complete_exact_bifiltration_operators",
        )
        self.assertEqual(decode_pair(extended["square_count"]), 2)
        for result in (self.physical_result, self.nonzero_result, self.zero_result, extended):
            for square in result["squares"]:
                dimensions = square["dimensions"]
                source = decode_pair(dimensions["source"])
                left = decode_pair(dimensions["left"])
                bottom = decode_pair(dimensions["bottom"])
                terminal = decode_pair(dimensions["terminal"])
                intersection = decode_pair(dimensions["intersection"])
                union = decode_pair(dimensions["union"])
                q = decode_pair(dimensions["quotient_q"])
                omega = decode_pair(dimensions["mixed_overlap_omega"])
                rank_difference = decode_pair(dimensions["rank_difference"])
                self.assertEqual(intersection, source + omega)
                self.assertEqual(union, left + bottom - intersection)
                self.assertEqual(terminal, left + bottom - source - omega + q)
                self.assertEqual(rank_difference, terminal - left - bottom + source)
                self.assertEqual(rank_difference, q - omega)
                self.assertTrue(square["rank_identities"]["all_identities_verified_exactly"])

    def test_non_integer_rational_coordinates_are_exact(self):
        square = self.nonzero_result["squares"][0]
        direct = _matrix_from_report(
            square["commutative_square"]["direct_source_to_terminal"], "direct"
        )
        flat = [coefficient for row in direct for coefficient in row]
        self.assertTrue(any(coefficient.denominator != 1 for coefficient in flat))
        self.assertIn(Fraction(1, 2), flat)
        self.assertFalse(contains_float(self.nonzero_result))

    def test_boundary_cells_are_explicit_and_no_square_is_fabricated(self):
        tiny = phase30.analyze_bounded_relation_filtration(
            **physical_arguments(
                max_substitution_word_length=1,
                max_multiplier_total_word_degree=0,
                max_filtration_cells=1,
            )
        )
        result = analyze_exact_bifiltration_operators(tiny)
        self.assertEqual(result["status"], "complete_exact_bifiltration_operators")
        self.assertEqual(decode_pair(result["square_count"]), 0)
        self.assertEqual(result["squares"], [])
        self.assertEqual(len(result["boundary_cells"]), 1)
        self.assertFalse(result["boundary_cells"][0]["zero_subspace_injected"])
        self.assertIn("D=0", result["boundary_cells"][0]["reason"])

    def test_missing_duplicate_and_partial_sources_are_unresolved_or_invalid(self):
        partial = analyze_exact_bifiltration_operators({
            "status": "partial_filtration_cell_unresolved",
            "cells": [],
        })
        self.assertEqual(partial["status"], "unresolved_source_filtration")

        source = nonzero_overlap_filtration()
        missing = copy.deepcopy(source)
        missing["cells"] = [
            cell_data
            for cell_data in missing["cells"]
            if decode_pair(cell_data["substitution_bound"]) != 2
            or decode_pair(cell_data["multiplier_bound"]) != 1
        ]
        missing_result = analyze_exact_bifiltration_operators(missing)
        self.assertEqual(missing_result["status"], "unresolved_non_rectangular_filtration")

        duplicate = copy.deepcopy(source)
        duplicate["cells"].append(copy.deepcopy(duplicate["cells"][0]))
        with self.assertRaises(ValueError):
            analyze_exact_bifiltration_operators(duplicate)

        with self.assertRaises(TypeError):
            analyze_exact_bifiltration_operators(None)
        with self.assertRaises(ValueError):
            analyze_exact_bifiltration_operators({
                "status": "complete_bounded_filtration",
                "cells": [],
            })

    def test_unresolved_transition_source_is_propagated(self):
        result = analyze_exact_bifiltration_operators(
            nonzero_overlap_filtration(),
            {"status": "unresolved_source_filtration", "cells": []},
        )
        self.assertEqual(result["status"], "unresolved_source_transitions")

    def test_phase31_matrices_are_independently_verified(self):
        self.assertTrue(
            self.physical_result["squares"][0]["commutative_square"][
                "phase31_matrices_independently_recomputed"
            ]
        )
        corrupted = copy.deepcopy(self.physical_transitions)
        for transition_cell in corrupted["cells"]:
            for mapping in transition_cell.get("inclusion_maps", []):
                report = mapping["coordinates_in_target_canonical_basis"]
                if not report or not report[0]:
                    continue
                old = phase29._fraction(report[0][0], "old coefficient")
                report[0][0] = {
                    "numerator": paired(old.numerator + 1),
                    "denominator": paired(old.denominator),
                }
                with self.assertRaises(ArithmeticError):
                    analyze_exact_bifiltration_operators(
                        self.physical_filtration, corrupted
                    )
                return
        self.fail("no Phase 31 inclusion matrix was available for the corruption control")

    def test_deterministic_and_input_order_independent(self):
        source = nonzero_overlap_filtration()
        reversed_source = copy.deepcopy(source)
        reversed_source["cells"].reverse()
        self.assertEqual(
            analyze_exact_bifiltration_operators(source),
            analyze_exact_bifiltration_operators(source),
        )
        self.assertEqual(
            analyze_exact_bifiltration_operators(source),
            analyze_exact_bifiltration_operators(reversed_source),
        )

    def test_resource_caps_are_explicit_and_unresolved(self):
        source = nonzero_overlap_filtration(extend_l3=True)
        capped_cells = analyze_exact_bifiltration_operators(source, max_cells=1)
        self.assertEqual(capped_cells["status"], "unresolved_cell_cap")
        capped_squares = analyze_exact_bifiltration_operators(source, max_squares=1)
        self.assertEqual(capped_squares["status"], "unresolved_square_cap")
        with self.assertRaises(ValueError):
            analyze_exact_bifiltration_operators(source, max_squares=0)

    def test_bounded_convenience_api_agrees_with_composed_stages(self):
        direct = analyze_bounded_bifiltration_operators(**physical_arguments())
        composed = analyze_exact_bifiltration_operators(
            self.physical_filtration, self.physical_transitions
        )
        self.assertEqual(direct, composed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
