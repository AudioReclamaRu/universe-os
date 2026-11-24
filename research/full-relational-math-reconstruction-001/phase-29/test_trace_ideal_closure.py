import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-27", "phase-28", "phase-29"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from trace_ideal_closure import (
    _insert_exact_basis,
    _verify_linear_certificate,
    build_bounded_trace_relation_space,
    expand_linear_combination_substitution,
)


class BoundedTraceIdealClosureTests(unittest.TestCase):
    def test_linear_combination_substitution_is_universally_verified(self):
        result = expand_linear_combination_substitution(
            dimension=1,
            generator_count=2,
            substitutions=[
                [
                    {"word": [0], "coefficient": 1},
                    {"word": [1], "coefficient": 1},
                ],
                [
                    {"word": [0], "coefficient": 1},
                    {"word": [1], "coefficient": -1},
                ],
            ],
        )
        self.assertEqual(result["status"], "universally_verified_identity")
        self.assertEqual(result["substitution_expansions"], "<100_2|11_3>")
        self.assertTrue(result["verification"]["verified"])
        self.assertEqual(result["verification"]["exact_residual"], "0")

    def test_rational_coefficients_are_expanded_exactly(self):
        result = expand_linear_combination_substitution(
            1,
            2,
            [
                [
                    {"word": [0], "coefficient": {"numerator": 1, "denominator": 2}},
                    {"word": [1], "coefficient": Fraction(1, 3)},
                ],
                [
                    {"word": [0], "coefficient": 1},
                    {"word": [1], "coefficient": 1},
                ],
            ],
        )
        self.assertEqual(result["status"], "universally_verified_identity")
        self.assertTrue(result["verification"]["verified"])

    def test_repeated_linear_arguments_are_retained_and_verified(self):
        same = [
            {"word": [0], "coefficient": 1},
            {"word": [1], "coefficient": 1},
        ]
        result = expand_linear_combination_substitution(
            2, 2, [same, same, same]
        )
        self.assertEqual(result["status"], "universally_verified_identity")
        self.assertTrue(result["primitive_integer_trace_terms"])
        self.assertTrue(result["verification"]["verified"])
        self.assertEqual(result["verification"]["exact_residual"], "0")

    def test_linear_substitution_expansion_cap_is_unresolved(self):
        result = expand_linear_combination_substitution(
            1, 2,
            [
                [{"word": [0], "coefficient": 1}, {"word": [1], "coefficient": 1}],
                [{"word": [0], "coefficient": 1}, {"word": [1], "coefficient": 1}],
            ],
            max_substitution_expansions=3,
        )
        self.assertEqual(result["status"], "unresolved_substitution_expansion_cap")

    def test_zero_support_argument_gives_zero_identity(self):
        result = expand_linear_combination_substitution(
            1, 2, [[], [{"word": [0], "coefficient": 1}]]
        )
        self.assertEqual(result["status"], "identically_zero_due_to_zero_argument")

    def test_bounded_relation_space_has_exact_verified_basis(self):
        result = build_bounded_trace_relation_space(
            dimension=2,
            generator_count=3,
            max_substitution_word_length=1,
            max_multiplier_trace_word_length=1,
            max_multiplier_total_word_degree=1,
        )
        self.assertEqual(result["status"], "complete_bounded_relation_space")
        self.assertNotEqual(result["seed_identity_count"], "<0_2|0_3>")
        self.assertEqual(result["seed_candidate_substitution_sets"], "<1010_2|101_3>")
        self.assertEqual(result["multiplier_monomial_count"], "<100_2|11_3>")
        self.assertEqual(
            result["processed_derived_relations"],
            result["derived_relation_candidate_count"],
        )
        self.assertEqual(result["unresolved_derived_relations"], "<0_2|0_3>")
        self.assertIn("expanded_index_assignments", result["seed_verification_work"])
        decode = lambda value: int(value.split("_2|")[0][1:], 2)
        self.assertEqual(
            decode(result["independent_basis_count"]) + decode(result["exactly_dependent_count"]),
            decode(result["derived_relation_candidate_count"]),
        )
        self.assertTrue(all(
            entry["universal_verification"]["status"] == "universally_verified_identity"
            for entry in result["independent_basis"]
        ))

    def test_derived_relation_cap_is_unresolved(self):
        result = build_bounded_trace_relation_space(
            2, 3, 1, 1, 1, max_derived_relations=3
        )
        self.assertEqual(result["status"], "unresolved_derived_relation_cap")
        self.assertEqual(result["independent_basis"], [])

    def test_multiplier_catalog_cap_is_unresolved(self):
        result = build_bounded_trace_relation_space(
            2, 3, 1, 1, 2, max_multiplier_monomials=2
        )
        self.assertEqual(result["status"], "unresolved_multiplier_monomial_cap")

    def test_seed_word_catalog_cap_is_unresolved(self):
        result = build_bounded_trace_relation_space(
            2, 3, 2, 1, 1, max_word_catalog_size=2
        )
        self.assertEqual(result["status"], "unresolved_seed_catalog")

    def test_multiplier_monomials_are_cyclically_canonical(self):
        result = build_bounded_trace_relation_space(
            1, 2, 1, 2, 2,
            max_multiplier_monomials=64,
            max_derived_relations=1000,
        )
        self.assertEqual(result["status"], "complete_bounded_relation_space")
        cycle_labels = result["trace_cycle_generators"]
        self.assertIn(["<0_2|0_3>", "<1_2|1_3>"], cycle_labels)
        self.assertNotIn(["<1_2|1_3>", "<0_2|0_3>"], cycle_labels)

    def test_exact_linear_dependency_certificate(self):
        basis = []
        candidate_polynomials = {
            "first": {((0,),): Fraction(2)},
            "second": {((0,),): Fraction(4)},
        }
        independent, _, _ = _insert_exact_basis(
            basis, candidate_polynomials["first"], "first"
        )
        self.assertTrue(independent)
        independent, certificate, pivot = _insert_exact_basis(
            basis, candidate_polynomials["second"], "second"
        )
        self.assertFalse(independent)
        self.assertIsNone(pivot)
        self.assertTrue(_verify_linear_certificate(certificate, candidate_polynomials))
        self.assertEqual(certificate["second"], Fraction(1))
        self.assertEqual(certificate["first"], Fraction(-2))

    def test_total_relation_expansion_cap_is_unresolved(self):
        result = build_bounded_trace_relation_space(
            2, 3, 1, 1, 1,
            max_total_relation_expansion_terms=1,
        )
        self.assertEqual(result["status"], "partial_bounded_relation_space_unresolved")
        self.assertEqual(result["processed_derived_relations"], "<0_2|0_3>")
        self.assertEqual(result["unresolved_derived_relations"], result["derived_relation_candidate_count"])

    def test_invalid_rational_denominator_is_rejected(self):
        with self.assertRaises(ZeroDivisionError):
            expand_linear_combination_substitution(
                1, 2,
                [
                    [{"word": [0], "coefficient": {"numerator": 1, "denominator": 0}}],
                    [{"word": [1], "coefficient": 1}],
                ],
            )

    def test_generator_index_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            expand_linear_combination_substitution(
                1, 2,
                [
                    [{"word": [2], "coefficient": 1}],
                    [{"word": [1], "coefficient": 1}],
                ],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
