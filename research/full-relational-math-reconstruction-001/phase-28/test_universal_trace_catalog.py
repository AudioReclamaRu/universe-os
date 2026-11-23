import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE27 = ROOT / "phase-27"
if str(PHASE27) not in sys.path:
    sys.path.insert(0, str(PHASE27))

from universal_trace_catalog import (
    _canonical_trace_polynomial_signature,
    enumerate_universal_trace_identity_catalog,
    word_catalog,
)


class UniversalTraceCatalogTests(unittest.TestCase):
    def test_word_catalog_is_length_lexicographic_and_noncommutative(self):
        words = word_catalog(2, 2)
        self.assertEqual(
            words,
            [
                ["<0_2|0_3>"],
                ["<1_2|1_3>"],
                ["<0_2|0_3>", "<0_2|0_3>"],
                ["<0_2|0_3>", "<1_2|1_3>"],
                ["<1_2|1_3>", "<0_2|0_3>"],
                ["<1_2|1_3>", "<1_2|1_3>"],
            ],
        )
        self.assertNotEqual(words[3], words[4])

    def test_catalog_enumerates_every_distinct_word_set_and_verifies(self):
        result = enumerate_universal_trace_identity_catalog(
            dimension=2,
            generator_count=2,
            max_word_length=2,
        )
        self.assertEqual(result["status"], "complete_catalog_verified")
        self.assertEqual(result["candidate_substitution_sets"], "<10100_2|202_3>")
        self.assertEqual(result["substitution_sets_processed"], "<10100_2|202_3>")
        self.assertEqual(result["verified_identity_count"], result["unique_nonzero_trace_identities"])
        self.assertEqual(result["rejected_identity_count"], "<0_2|0_3>")
        self.assertEqual(result["unresolved_identity_count"], "<0_2|0_3>")
        self.assertTrue(all(
            entry["status"] == "universally_verified_identity"
            for entry in result["identities"]
        ))

    def test_catalog_is_deterministic(self):
        first = enumerate_universal_trace_identity_catalog(2, 2, 1)
        second = enumerate_universal_trace_identity_catalog(2, 2, 1)
        self.assertEqual(first, second)

    def test_word_catalog_cap_is_unresolved(self):
        result = enumerate_universal_trace_identity_catalog(
            2, 3, 2, max_word_catalog_size=10
        )
        self.assertEqual(result["status"], "unresolved_word_catalog_cap")
        self.assertEqual(result["identities"], [])

    def test_substitution_set_cap_is_unresolved_without_partial_catalog(self):
        result = enumerate_universal_trace_identity_catalog(
            2, 2, 2, max_substitution_sets=19
        )
        self.assertEqual(result["status"], "unresolved_substitution_set_cap")
        self.assertEqual(result["identities"], [])

    def test_permutation_cap_is_unresolved(self):
        result = enumerate_universal_trace_identity_catalog(
            3, 2, 2, max_identity_permutations=10
        )
        self.assertEqual(result["status"], "unresolved_permutation_cap")

    def test_per_identity_expansion_cap_is_unresolved(self):
        result = enumerate_universal_trace_identity_catalog(
            1, 2, 1,
            max_expansion_terms_per_identity=1,
        )
        self.assertEqual(result["status"], "partial_catalog_verification_unresolved")
        self.assertEqual(result["verified_identity_count"], "<0_2|0_3>")
        self.assertEqual(result["unresolved_identity_count"], "<1_2|1_3>")
        self.assertGreaterEqual(len(result["identities"]), 1)
        self.assertTrue(result["identities"][0]["status"].startswith("unresolved_"))

    def test_total_expansion_budget_is_explicit(self):
        result = enumerate_universal_trace_identity_catalog(
            2, 2, 2,
            max_total_expansion_terms=1,
        )
        self.assertEqual(result["status"], "partial_catalog_verification_unresolved")
        self.assertEqual(result["verification_work"]["expanded_index_assignments"], "<0_2|0_3>")
        self.assertGreater(len(result["identities"]), 0)
        self.assertEqual(result["unresolved_identity_count"], result["unique_nonzero_trace_identities"])

    def test_too_few_words_has_complete_empty_catalog(self):
        result = enumerate_universal_trace_identity_catalog(
            dimension=3,
            generator_count=1,
            max_word_length=2,
        )
        self.assertEqual(result["status"], "complete_catalog_no_admissible_substitution_sets")
        self.assertEqual(result["candidate_substitution_sets"], "<0_2|0_3>")
        self.assertEqual(result["identities"], [])

    def test_signature_ignores_trace_cyclic_rotation_and_factor_order(self):
        one = [
            {
                "coefficient": "<1_2|1_3>",
                "trace_factors": [
                    ["<0_2|0_3>", "<1_2|1_3>"],
                    ["<10_2|2_3>"],
                ],
            }
        ]
        reordered_scaled = [
            {
                "coefficient": "-<10_2|2_3>",
                "trace_factors": [
                    ["<10_2|2_3>"],
                    ["<1_2|1_3>", "<0_2|0_3>"],
                ],
            }
        ]
        self.assertEqual(
            _canonical_trace_polynomial_signature(one),
            _canonical_trace_polynomial_signature(reordered_scaled),
        )

    def test_signature_does_not_assume_word_reversal(self):
        forward = [{
            "coefficient": "<1_2|1_3>",
            "trace_factors": [["<0_2|0_3>", "<1_2|1_3>", "<10_2|2_3>"]],
        }]
        reverse = [{
            "coefficient": "<1_2|1_3>",
            "trace_factors": [["<10_2|2_3>", "<1_2|1_3>", "<0_2|0_3>"]],
        }]
        self.assertNotEqual(
            _canonical_trace_polynomial_signature(forward),
            _canonical_trace_polynomial_signature(reverse),
        )

    def test_repeated_generators_inside_words_are_preserved(self):
        words = word_catalog(1, 3)
        self.assertEqual(len(words), 3)
        self.assertEqual(words[2], ["<0_2|0_3>", "<0_2|0_3>", "<0_2|0_3>"])

    def test_paired_configuration_values_are_accepted(self):
        result = enumerate_universal_trace_identity_catalog(
            dimension="<10_2|2_3>",
            generator_count="<10_2|2_3>",
            max_word_length="<10_2|2_3>",
        )
        self.assertEqual(result["status"], "complete_catalog_verified")

    def test_invalid_nonpositive_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            enumerate_universal_trace_identity_catalog(0, 2, 2)
        with self.assertRaises(ValueError):
            enumerate_universal_trace_identity_catalog(2, 0, 2)
        with self.assertRaises(ValueError):
            word_catalog(2, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
