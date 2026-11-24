import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-27", "phase-28", "phase-29", "phase-30"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from relation_filtration import analyze_bounded_relation_filtration


def small_filtration(**overrides):
    arguments = {
        "dimension": 2,
        "generator_count": 3,
        "max_substitution_word_length": 1,
        "max_multiplier_trace_word_length": 1,
        "max_multiplier_total_word_degree": 1,
        "max_filtration_cells": 4,
        "max_word_catalog_size": 8,
        "max_substitution_sets": 100,
        "max_multiplier_monomials": 16,
        "max_derived_relations": 1000,
        "max_seed_expansion_terms_per_identity": 100_000,
        "max_seed_expansion_terms_per_cell": 1_000_000,
        "max_relation_expansion_terms_per_relation": 100_000,
        "max_relation_expansion_terms_per_cell": 1_000_000,
        "max_aggregate_seed_expansion_terms": 2_000_000,
        "max_aggregate_relation_expansion_terms": 2_000_000,
    }
    arguments.update(overrides)
    return analyze_bounded_relation_filtration(**arguments)


def decode_pair(value):
    return int(value.split("_2|")[0][1:], 2)


class RelationFiltrationTests(unittest.TestCase):
    def test_complete_nested_filtration_and_exact_quotients(self):
        result = small_filtration()
        self.assertEqual(result["status"], "complete_bounded_filtration")
        self.assertEqual(len(result["cells"]), 2)
        first, second = result["cells"]
        self.assertEqual(first["substitution_bound"], "<1_2|1_3>")
        self.assertEqual(first["multiplier_bound"], "<0_2|0_3>")
        self.assertEqual(first["predecessor_union_dimension"], "<0_2|0_3>")
        self.assertEqual(
            first["new_quotient_dimension"],
            first["relation_space_dimension"],
        )
        self.assertEqual(
            second["predecessor_union_dimension"],
            second["predecessor_bottom_dimension"],
        )
        self.assertEqual(
            decode_pair(second["predecessor_intersection_dimension"]),
            0,
        )
        self.assertEqual(
            decode_pair(second["relation_space_dimension"]),
            decode_pair(second["predecessor_union_dimension"])
            + decode_pair(second["new_quotient_dimension"]),
        )

    def test_rank_profiles_are_homogeneous_and_reconcile(self):
        result = small_filtration()
        for cell in result["cells"]:
            self.assertEqual(
                sum(decode_pair(value) for value in cell["rank_by_total_word_degree"].values()),
                decode_pair(cell["relation_space_dimension"]),
            )
            self.assertEqual(
                sum(decode_pair(value) for value in cell["predecessor_union_rank_by_total_word_degree"].values()),
                decode_pair(cell["predecessor_union_dimension"]),
            )
            self.assertEqual(
                sum(decode_pair(value) for value in cell["new_quotient_rank_by_total_word_degree"].values()),
                decode_pair(cell["new_quotient_dimension"]),
            )

    def test_each_cell_returns_a_cardinality_minimal_q_basis(self):
        result = small_filtration()
        for cell in result["cells"]:
            self.assertEqual(
                len(cell["basis_entries"]),
                decode_pair(cell["relation_space_dimension"]),
            )
            self.assertEqual(
                cell["basis_minimality"]["basis_cardinality"],
                cell["basis_minimality"]["rank"],
            )
            self.assertTrue(cell["basis_minimality"]["not_an_ideal_generator_minimality_claim"])
            self.assertTrue(all(
                entry["universal_verification"]["status"] == "universally_verified_identity"
                for entry in cell["basis_entries"]
            ))

    def test_quotient_certificates_have_exact_zero_residuals(self):
        result = small_filtration()
        for cell in result["cells"]:
            for certificate in (
                cell["overlap_certificates"] + cell["quotient_dependency_certificates"]
            ):
                self.assertEqual(certificate["recomputed_residual"], "0")
                self.assertTrue(certificate["linear_dependency_certificate"])

    def test_rank_is_monotone_in_multiplier_bound(self):
        result = small_filtration()
        cells = {
            (decode_pair(cell["substitution_bound"]), decode_pair(cell["multiplier_bound"])): cell
            for cell in result["cells"]
        }
        rank_d0 = decode_pair(cells[(1, 0)]["relation_space_dimension"])
        rank_d1 = decode_pair(cells[(1, 1)]["relation_space_dimension"])
        self.assertGreaterEqual(rank_d1, rank_d0)

    def test_rank_is_monotone_in_substitution_word_bound(self):
        result = analyze_bounded_relation_filtration(
            dimension=2,
            generator_count=2,
            max_substitution_word_length=2,
            max_multiplier_trace_word_length=1,
            max_multiplier_total_word_degree=0,
            max_filtration_cells=2,
            max_word_catalog_size=8,
            max_substitution_sets=100,
            max_multiplier_monomials=8,
            max_derived_relations=1000,
            max_seed_expansion_terms_per_identity=100_000,
            max_seed_expansion_terms_per_cell=2_000_000,
            max_relation_expansion_terms_per_relation=100_000,
            max_relation_expansion_terms_per_cell=2_000_000,
            max_aggregate_seed_expansion_terms=4_000_000,
            max_aggregate_relation_expansion_terms=4_000_000,
        )
        self.assertEqual(result["status"], "complete_bounded_filtration")
        cells = result["cells"]
        rank_l1 = decode_pair(cells[0]["relation_space_dimension"])
        rank_l2 = decode_pair(cells[1]["relation_space_dimension"])
        self.assertGreaterEqual(rank_l2, rank_l1)

    def test_final_step_diagnostic_is_not_a_stabilization_claim(self):
        result = analyze_bounded_relation_filtration(
            dimension=2,
            generator_count=2,
            max_substitution_word_length=2,
            max_multiplier_trace_word_length=1,
            max_multiplier_total_word_degree=0,
            max_filtration_cells=2,
            max_word_catalog_size=8,
            max_substitution_sets=100,
            max_multiplier_monomials=8,
            max_derived_relations=1000,
            max_seed_expansion_terms_per_identity=100_000,
            max_seed_expansion_terms_per_cell=2_000_000,
            max_relation_expansion_terms_per_relation=100_000,
            max_relation_expansion_terms_per_cell=2_000_000,
            max_aggregate_seed_expansion_terms=4_000_000,
            max_aggregate_relation_expansion_terms=4_000_000,
        )
        self.assertIn("<0_2|0_3>", result["stability_diagnostic"])
        self.assertIn(
            "no inference of stabilization",
            result["stability_diagnostic"]["<0_2|0_3>"]["interpretation"],
        )

    def test_filtration_cell_cap_is_unresolved(self):
        result = small_filtration(max_filtration_cells=1)
        self.assertEqual(result["status"], "unresolved_filtration_cell_cap")
        self.assertEqual(result["cells"], [])

    def test_aggregate_seed_budget_is_unresolved(self):
        result = small_filtration(max_aggregate_seed_expansion_terms=1)
        self.assertEqual(
            result["status"],
            "partial_filtration_cell_unresolved",
        )
        self.assertTrue(result["unresolved_cell"])
        self.assertEqual(result["cells"], [])

    def test_aggregate_relation_budget_is_unresolved(self):
        result = small_filtration(max_aggregate_relation_expansion_terms=1)
        self.assertEqual(
            result["status"],
            "partial_filtration_cell_unresolved",
        )
        self.assertTrue(result["unresolved_cell"])

    def test_certificate_cap_is_unresolved(self):
        result = small_filtration(max_certificate_records=1)
        self.assertIn(
            result["status"],
            {
                "complete_bounded_filtration",
                "partial_filtration_certificate_cap_unresolved",
            },
        )
        if result["status"].startswith("partial_"):
            self.assertTrue(result["unresolved_cell"])

    def test_deterministic_output(self):
        self.assertEqual(small_filtration(), small_filtration())

    def test_invalid_positive_bounds_are_rejected(self):
        with self.assertRaises(ValueError):
            analyze_bounded_relation_filtration(0)
        with self.assertRaises(ValueError):
            analyze_bounded_relation_filtration(
                2, max_substitution_word_length=0
            )
        with self.assertRaises(ValueError):
            analyze_bounded_relation_filtration(
                2, max_multiplier_total_word_degree=-1
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
