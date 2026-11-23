import math
import unittest
from atlas_relation_comparator import BasisSet, PiEntry, compare_report, search_basis


class AtlasRelationComparatorTests(unittest.TestCase):
    def test_product_relation_matches_phi(self):
        phi = (1 + math.sqrt(5)) / 2
        basis = BasisSet("test", "canonical", (
            PiEntry("G1", 2.0, "Π₁", "canonical"),
            PiEntry("G2", phi / 2, "Π₂", "canonical"),
        ))
        candidates = search_basis(basis, max_terms=2, exponent_bound=1)
        product = next(c for c in candidates if c.formula == "G1 * G2")
        self.assertEqual(product.matches[0]["atlas_key"], "constant.phi")

    def test_bases_are_never_mixed(self):
        payload = {
            "canonical_basis": [{"basis_id": "<1_2|1_3>", "expression": "A", "numeric_value_secondary": 2.0}],
            "alternative_basis_examples": [{"basis_id": "<10_2|2_3>", "groups": [
                {"basis_id": "<1_2|1_3>", "expression": "B", "numeric_value_secondary": math.e}
            ]}],
        }
        result = compare_report(payload, max_terms=1, exponent_bound=1)
        self.assertEqual(len(result["basis_results"]), 2)
        for basis in result["basis_results"]:
            self.assertEqual(len(basis["input_groups"]), 1)
            self.assertTrue(all("G2" not in c["formula"] for c in basis["candidates"]))

    def test_non_primitive_power_relations_are_retained(self):
        basis = BasisSet("test", "canonical", (
            PiEntry("G1", 2.0, "Π₁", "canonical"), PiEntry("G2", 3.0, "Π₂", "canonical")))
        candidates = search_basis(basis, max_terms=2, exponent_bound=2)
        self.assertTrue(any(c.exponents == (1, 2) for c in candidates))
        self.assertTrue(any(c.exponents == (2, 2) for c in candidates))

    def test_power_can_match_constant_even_if_base_does_not(self):
        phi = (1 + math.sqrt(5)) / 2
        basis = BasisSet("test", "canonical", (PiEntry("G1", math.sqrt(phi), "Π₁", "canonical"),))
        squared = next(c for c in search_basis(basis, max_terms=1, exponent_bound=2) if c.exponents == (2,))
        self.assertEqual(squared.matches[0]["atlas_key"], "constant.phi")

    def test_extreme_values_are_retained_without_infinite_json_numbers(self):
        basis = BasisSet("test", "canonical", (PiEntry("G1", 1e308, "Π₁", "canonical"),))
        candidates = search_basis(basis, max_terms=1, exponent_bound=2)
        self.assertTrue(any(c.numeric_status == "outside_finite_float_range" and c.value is None for c in candidates))

    def test_invalid_tolerance_rejected(self):
        basis = BasisSet("test", "canonical", (PiEntry("G1", 2.0, "Π₁", "canonical"),))
        with self.assertRaises(ValueError):
            search_basis(basis, tolerance=float("nan"))

    def test_missing_numeric_group_marks_partial_basis(self):
        payload = {"canonical_basis": [
            {"basis_id": "<1_2|1_3>", "expression": "A", "numeric_value_secondary": 2.0},
            {"basis_id": "<10_2|2_3>", "expression": "B", "numeric_value_secondary": None},
        ]}
        basis = compare_report(payload, max_terms=1, exponent_bound=1)["basis_results"][0]
        self.assertEqual(basis["basis_completeness"], "partial_numeric_projection")
        self.assertEqual(basis["omitted_non_numeric_groups"], ["G<10_2|2_3>"])
        self.assertEqual(basis["input_group_count"], "<10_2|2_3>")

    def test_candidate_cap_enforced(self):
        basis = BasisSet("test", "canonical", tuple(
            PiEntry(f"G{i}", float(i + 1), f"Π{i}", "test") for i in range(6)))
        with self.assertRaises(ValueError):
            search_basis(basis, max_terms=3, exponent_bound=2, max_candidates=10)

    def test_paired_count(self):
        payload = {"canonical_basis": [{
            "basis_id": "<1_2|1_3>", "expression": "A", "numeric_value_secondary": math.pi}]}
        result = compare_report(payload, max_terms=1, exponent_bound=1)
        self.assertEqual(result["basis_count"], "<1_2|1_3>")
        self.assertEqual(result["basis_results"][0]["matched_candidate_count"], "<1_2|1_3>")


if __name__ == "__main__":
    unittest.main(verbosity=2)
