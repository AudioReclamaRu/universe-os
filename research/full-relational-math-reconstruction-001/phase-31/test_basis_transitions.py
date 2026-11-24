import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-27", "phase-28", "phase-29", "phase-30", "phase-31"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from basis_transitions import (
    _canonical_rref,
    _matrix_multiply,
    _identity,
    analyze_bounded_basis_transitions,
    analyze_exact_basis_transitions,
)


def small_grid(**overrides):
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
    return analyze_bounded_basis_transitions(**arguments)


def decode_pair(value):
    body = value[1:value.index("_2|")]
    return int(body, 2)


class BasisTransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = small_grid()
        if cls.result["status"] != "complete_exact_basis_transitions":
            raise AssertionError(cls.result)

    def test_complete_grid_has_four_cells(self):
        self.assertEqual(len(self.result["cells"]), 4)
        bounds = {
            (decode_pair(cell["substitution_bound"]), decode_pair(cell["multiplier_bound"]))
            for cell in self.result["cells"]
        }
        self.assertEqual(bounds, {(1, 0), (1, 1), (2, 0), (2, 1)})

    def test_canonical_basis_rank_matches_phase30(self):
        for cell in self.result["cells"]:
            rank = decode_pair(cell["relation_space_dimension"])
            self.assertEqual(len(cell["canonical_basis"]), rank)
            self.assertEqual(
                decode_pair(cell["adapted_basis_transition"]["adapted_basis_dimension"]),
                rank,
            )

    def test_inclusion_maps_are_injective_and_exact(self):
        for cell in self.result["cells"]:
            target_rank = decode_pair(cell["relation_space_dimension"])
            for mapping in cell["inclusion_maps"]:
                source_rank = decode_pair(mapping["source_dimension"])
                self.assertEqual(decode_pair(mapping["matrix_rank"]), source_rank)
                self.assertEqual(decode_pair(mapping["kernel_dimension"]), 0)
                self.assertEqual(
                    decode_pair(mapping["cokernel_dimension"]),
                    target_rank - source_rank,
                )
                matrix = mapping["coordinates_in_target_canonical_basis"]
                self.assertEqual(len(matrix), source_rank)
                self.assertTrue(mapping["exact_reconstruction_verified"])

    def test_two_predecessor_intersections_match_phase30(self):
        cell = next(
            item for item in self.result["cells"]
            if decode_pair(item["substitution_bound"]) == 2
            and decode_pair(item["multiplier_bound"]) == 1
        )
        intersection = cell["predecessor_intersection"]
        rank = decode_pair(intersection["dimension"])
        self.assertEqual(
            rank,
            decode_pair(cell["predecessor_intersection_dimension"]),
        )
        self.assertEqual(
            decode_pair(intersection["kernel_dimension_of_[left_basis|-bottom_basis]"]),
            rank,
        )
        self.assertEqual(len(intersection["basis"]), rank)
        self.assertTrue(intersection["exact_equality_and_coordinate_reconstruction_verified"])

    def test_intersection_coordinates_are_rank_revealing(self):
        cell = self.result["cells"][-1]
        intersection = cell["predecessor_intersection"]
        rank = decode_pair(intersection["dimension"])
        self.assertEqual(len(intersection["coordinates_in_left_predecessor_basis"]), rank)
        self.assertEqual(len(intersection["coordinates_in_bottom_predecessor_basis"]), rank)

    def test_quotient_complement_has_exact_dimension(self):
        for cell in self.result["cells"]:
            quotient_rank = decode_pair(cell["quotient_dimension"])
            self.assertEqual(len(cell["quotient_complement_basis"]), quotient_rank)
            self.assertEqual(
                decode_pair(cell["predecessor_union_dimension"]) + quotient_rank,
                decode_pair(cell["relation_space_dimension"]),
            )

    def test_adapted_basis_change_is_exactly_invertible(self):
        for cell in self.result["cells"]:
            transition = cell["adapted_basis_transition"]
            forward = transition["adapted_to_canonical_matrix"]
            inverse = transition["canonical_to_adapted_matrix"]
            size = decode_pair(transition["adapted_basis_dimension"])
            self.assertEqual(len(forward), size)
            self.assertEqual(len(inverse), size)
            self.assertTrue(transition["both_products_are_exact_identity"])
            self.assertTrue(transition["determinant_nonzero"])

    def test_rref_is_independent_of_input_order(self):
        first = {
            ((0,),): Fraction(1),
            ((1,),): Fraction(2),
        }
        second = {
            ((0,),): Fraction(3),
            ((1,),): Fraction(6),
            ((0, 1),): Fraction(1),
        }
        self.assertEqual(
            _canonical_rref([first, second]),
            _canonical_rref([second, first]),
        )

    def test_boundary_cell_has_no_artificial_predecessor_maps(self):
        result = small_grid(
            max_substitution_word_length=1,
            max_multiplier_total_word_degree=0,
            max_filtration_cells=1,
        )
        self.assertEqual(result["status"], "complete_exact_basis_transitions")
        cell = result["cells"][0]
        self.assertEqual(cell["inclusion_maps"], [])
        self.assertEqual(decode_pair(cell["predecessor_union_dimension"]), 0)
        self.assertEqual(
            decode_pair(cell["quotient_dimension"]),
            decode_pair(cell["relation_space_dimension"]),
        )

    def test_unresolved_phase30_bounds_remain_unresolved(self):
        result = small_grid(max_filtration_cells=1)
        self.assertEqual(result["status"], "unresolved_source_filtration")
        self.assertEqual(result["source_filtration_status"], "unresolved_filtration_cell_cap")
        self.assertEqual(result["cells"], [])

    def test_transition_analysis_is_deterministic(self):
        from relation_filtration import analyze_bounded_relation_filtration
        filtration = analyze_bounded_relation_filtration(
            dimension=2,
            generator_count=2,
            max_substitution_word_length=1,
            max_multiplier_trace_word_length=1,
            max_multiplier_total_word_degree=0,
            max_filtration_cells=1,
            max_word_catalog_size=8,
            max_substitution_sets=100,
            max_multiplier_monomials=8,
            max_derived_relations=1000,
            max_seed_expansion_terms_per_identity=100_000,
            max_seed_expansion_terms_per_cell=1_000_000,
            max_relation_expansion_terms_per_relation=100_000,
            max_relation_expansion_terms_per_cell=1_000_000,
            max_aggregate_seed_expansion_terms=2_000_000,
            max_aggregate_relation_expansion_terms=2_000_000,
        )
        self.assertEqual(
            analyze_exact_basis_transitions(filtration),
            analyze_exact_basis_transitions(filtration),
        )

    def test_malformed_filtration_is_rejected(self):
        with self.assertRaises(TypeError):
            analyze_exact_basis_transitions(None)
        with self.assertRaises(ValueError):
            analyze_exact_basis_transitions({
                "status": "complete_bounded_filtration",
                "cells": [],
            })


if __name__ == "__main__":
    unittest.main(verbosity=2)
