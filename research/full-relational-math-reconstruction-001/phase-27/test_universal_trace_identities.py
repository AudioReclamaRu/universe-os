import unittest

from universal_trace_identities import (
    _canonical_cyclic_word,
    generate_fundamental_trace_identity,
    prove_fundamental_trace_identity,
    verify_trace_polynomial_identity,
)


class UniversalTraceIdentityTests(unittest.TestCase):
    def test_dimension_one_fundamental_identity(self):
        result = prove_fundamental_trace_identity(1, [[0], [1]])
        self.assertEqual(result["status"], "universally_verified_identity")
        self.assertTrue(result["verification"]["verified"])
        self.assertEqual(result["verification"]["exact_residual"], "0")

    def test_dimension_two_three_matrix_fundamental_identity(self):
        result = prove_fundamental_trace_identity(2, [[0], [1], [2]])
        self.assertEqual(result["status"], "universally_verified_identity")
        self.assertGreater(
            len(result["identity"]["terms"]), 0
        )
        self.assertEqual(
            result["verification"]["nonzero_residual_monomials"],
            "<0_2|0_3>",
        )

    def test_dimension_three_fundamental_identity(self):
        result = prove_fundamental_trace_identity(3, [[0], [1], [2], [3]])
        self.assertEqual(result["status"], "universally_verified_identity")
        self.assertTrue(result["verification"]["certificate"]["all_sparse_polynomial_coefficients_zero"])

    def test_noncommutative_word_substitutions_are_verified(self):
        result = prove_fundamental_trace_identity(
            2, [[0, 1], [1, 0], [0, 0, 1]]
        )
        self.assertEqual(result["status"], "universally_verified_identity")

    def test_trace_cyclic_rotation_is_canonical_but_reversal_is_not(self):
        self.assertEqual(_canonical_cyclic_word((0, 1, 2)), _canonical_cyclic_word((1, 2, 0)))
        self.assertNotEqual(_canonical_cyclic_word((0, 1, 2)), _canonical_cyclic_word((0, 2, 1)))

    def test_trace_cyclicity_is_verified_for_generic_matrices(self):
        result = verify_trace_polynomial_identity(
            3,
            [
                {"coefficient": 1, "trace_factors": [[0, 1, 2]]},
                {"coefficient": -1, "trace_factors": [[1, 2, 0]]},
            ],
        )
        self.assertEqual(result["status"], "universally_verified_identity")
        self.assertTrue(result["universal_identity"])

    def test_scalar_trace_factors_are_commutative(self):
        result = verify_trace_polynomial_identity(
            2,
            [
                {"coefficient": 1, "trace_factors": [[0], [1]]},
                {"coefficient": -1, "trace_factors": [[1], [0]]},
            ],
        )
        self.assertEqual(result["status"], "universally_verified_identity")

    def test_false_trace_identity_is_rejected(self):
        result = verify_trace_polynomial_identity(
            2,
            [{"coefficient": 1, "trace_factors": [[0]]}],
        )
        self.assertEqual(result["status"], "identity_rejected_nonzero_generic_residual")
        self.assertFalse(result["verified"])
        self.assertEqual(result["nonzero_residual_monomials"], "<10_2|2_3>")
        paired_count = verify_trace_polynomial_identity(
            2,
            [{"coefficient": 1, "trace_factors": [[0]]}],
            matrix_count="<1_2|1_3>",
        )
        self.assertEqual(paired_count["matrix_count"], "<1_2|1_3>")
        with self.assertRaises(ValueError):
            verify_trace_polynomial_identity(
                2,
                [{"coefficient": 1, "trace_factors": [["<10_2|5_3>"]]}],
            )

    def test_expansion_cap_is_unresolved(self):
        result = prove_fundamental_trace_identity(
            3, [[0], [1], [2], [3]], max_expansion_terms=10
        )
        self.assertEqual(result["status"], "unresolved_expansion_cap")
        self.assertEqual(result["verification"]["status"], "unresolved_expansion_cap")

    def test_permutation_cap_is_unresolved(self):
        result = generate_fundamental_trace_identity(
            3, [[0], [1], [2], [3]], max_identity_permutations=10
        )
        self.assertEqual(result["status"], "unresolved_permutation_cap")
        self.assertTrue(result["universal_identity"])

    def test_substitution_count_must_be_dimension_plus_one(self):
        with self.assertRaises(ValueError):
            generate_fundamental_trace_identity(2, [[0], [1]])

    def test_paired_integer_inputs_are_checked(self):
        result = verify_trace_polynomial_identity(
            "<10_2|2_3>",
            [{"coefficient": "<1_2|1_3>", "trace_factors": [["<0_2|0_3>"]]}],
        )
        self.assertEqual(result["status"], "identity_rejected_nonzero_generic_residual")
        with self.assertRaises(ValueError):
            verify_trace_polynomial_identity(
                2,
                [{"coefficient": 1, "trace_factors": [["<10_2|5_3>"]]}],
            )

    def test_matrix_count_bounds_generator_indices(self):
        with self.assertRaises(ValueError):
            verify_trace_polynomial_identity(
                2,
                [{"coefficient": 1, "trace_factors": [[1]]}],
                matrix_count=1,
            )

    def test_fundamental_identity_terms_are_integer_exact(self):
        identity = generate_fundamental_trace_identity(2, [[0], [1], [2]])
        self.assertEqual(identity["status"], "identity_constructed")
        self.assertTrue(all(term["coefficient"].startswith(("<", "-<")) for term in identity["terms"]))

    def test_fundamental_trace_identity_is_symmetric_in_arguments(self):
        forward = generate_fundamental_trace_identity(2, [[0], [1], [2]])
        swapped = generate_fundamental_trace_identity(2, [[1], [0], [2]])
        self.assertEqual(forward["status"], "identity_constructed")
        self.assertEqual(swapped["status"], "identity_constructed")
        self.assertEqual(forward["terms"], swapped["terms"])

    def test_repeated_arguments_are_retained_and_universally_verified(self):
        result = prove_fundamental_trace_identity(2, [[0], [0], [0]])
        self.assertEqual(result["status"], "universally_verified_identity")
        self.assertGreater(len(result["identity"]["terms"]), 0)
        self.assertTrue(result["verification"]["verified"])
        self.assertEqual(result["verification"]["exact_residual"], "0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
