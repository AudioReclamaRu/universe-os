import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-16", "phase-20", "phase-21", "phase-23", "phase-24"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from affine_ifs_characteristic_partition import characteristic_polynomial
from affine_ifs_joint_trace_partition import _pair_relation_record
from adaptive_matrix_word_refinement import (
    canonical_cyclic_word,
    matrix_word_tiers,
    trace_matrix_word,
    refine_ambiguous_matrix_word_graph,
)


def qmatrix(rows):
    return [[core.q(value) for value in row] for row in rows]


def discriminating_matrices():
    source_a = qmatrix([
        ["3/4", "3/4", "1/2"],
        [0, "1/2", 0],
        [0, "-1/2", "1/4"],
    ])
    source_b = qmatrix([
        ["3/4", 0, 0],
        ["-1/4", "1/2", 0],
        ["-1/2", 0, "1/4"],
    ])
    target_a = qmatrix([
        ["3/4", 0, "-1/2"],
        [0, "1/2", "1/4"],
        [0, 0, "1/4"],
    ])
    target_b = qmatrix([
        ["1/4", 0, 0],
        ["-1/4", "1/2", 0],
        ["1/4", "-1/4", "3/4"],
    ])
    return source_a, source_b, target_a, target_b


def baseline_edges(matrices):
    return [
        [_pair_relation_record(A, B, 3) for B in matrices]
        for A in matrices
    ]


class AdaptiveMatrixWordRefinementTests(unittest.TestCase):
    def test_cyclic_word_catalog_is_deduplicated_and_baseline_excluded(self):
        self.assertEqual(canonical_cyclic_word("10100"), "00101")
        tiers = matrix_word_tiers(8)
        self.assertEqual([tier["length"] for tier in tiers], [5, 6, 7, 8])
        self.assertEqual([len(tier["words"]) for tier in tiers], [6, 12, 18, 34])
        self.assertIn("001011", tiers[1]["words"])
        self.assertNotIn("0011", [word for tier in tiers for word in tier["words"]])

    def test_trace_word_is_exactly_invariant_under_common_similarity(self):
        source_a, source_b, _, _ = discriminating_matrices()
        P = qmatrix([[1, 1, 0], [0, 1, 1], [0, 0, 1]])
        Pinv = core._inv(P, 3)
        target_a = core._mm(core._mm(P, source_a, 3), Pinv, 3)
        target_b = core._mm(core._mm(P, source_b, 3), Pinv, 3)
        for word in ("00001", "001011", "010111", "01111111"):
            self.assertEqual(
                trace_matrix_word(source_a, source_b, word, 3),
                trace_matrix_word(target_a, target_b, word, 3),
            )

    def test_length_six_word_distinguishes_pair_invisible_to_phase21_words(self):
        source_a, source_b, target_a, target_b = discriminating_matrices()
        baseline_words = ("01", "001", "011", "0101", "0011")
        for word in baseline_words:
            self.assertEqual(
                trace_matrix_word(source_a, source_b, word, 3),
                trace_matrix_word(target_a, target_b, word, 3),
            )
        self.assertEqual(trace_matrix_word(source_a, source_b, "001011", 3), core.q("-179/4096"))
        self.assertEqual(trace_matrix_word(target_a, target_b, "001011", 3), core.q("-175/4096"))
        self.assertNotEqual(
            trace_matrix_word(source_a, source_b, "001011", 3),
            trace_matrix_word(target_a, target_b, "001011", 3),
        )

    def test_adaptive_expansion_is_budget_atomic(self):
        source_a, source_b, target_a, target_b = discriminating_matrices()
        matrices_s = [source_a, source_a, source_b]
        matrices_t = [target_a, target_a, target_b]
        chars_s = [characteristic_polynomial(A, 3) for A in matrices_s]
        chars_t = [characteristic_polynomial(A, 3) for A in matrices_t]
        edges_s = baseline_edges(matrices_s)
        edges_t = baseline_edges(matrices_t)
        result = refine_ambiguous_matrix_word_graph(
            matrices_s, matrices_t, chars_s, chars_t, edges_s, edges_t, 3,
            max_matrix_products=479, max_word_length=6,
        )
        tiers = result["adaptive_matrix_word_refinement"]["additional_word_tiers"]
        self.assertEqual(len(tiers), 1)
        self.assertFalse(tiers[0]["applied"])
        self.assertEqual(tiers[0]["required_matrix_products"], core.paired(480))
        self.assertEqual(result["adaptive_matrix_word_refinement"]["matrix_product_budget"]["used"], core.paired(0))

    def test_adaptive_words_are_calculated_only_on_ambiguous_vertex_incidence(self):
        source_a, source_b, target_a, target_b = discriminating_matrices()
        matrices_s = [source_a, source_a, source_b]
        matrices_t = [target_a, target_a, target_b]
        chars_s = [characteristic_polynomial(A, 3) for A in matrices_s]
        chars_t = [characteristic_polynomial(A, 3) for A in matrices_t]
        result = refine_ambiguous_matrix_word_graph(
            matrices_s, matrices_t, chars_s, chars_t,
            baseline_edges(matrices_s), baseline_edges(matrices_t), 3,
            max_matrix_products=5000, max_word_length=6,
        )
        report = result["adaptive_matrix_word_refinement"]
        applied = [tier for tier in report["additional_word_tiers"] if tier["applied"]]
        self.assertEqual([tier["length"] for tier in applied], [core.paired(5), core.paired(6)])
        self.assertEqual(applied[0]["source_ordered_pairs"], core.paired(8))
        self.assertEqual(applied[0]["target_ordered_pairs"], core.paired(8))
        self.assertEqual(result["candidate_edges_after_refinement"], 0)
        self.assertEqual(applied[0]["candidate_edges_after"], applied[1]["candidate_edges_before"])

    def test_polynomial_cap_is_unresolved_and_candidate_features_are_retained(self):
        source_a, source_b, target_a, target_b = discriminating_matrices()
        matrices_s = [source_a, source_a, source_b]
        matrices_t = [target_a, target_a, target_b]
        chars_s = [characteristic_polynomial(A, 3) for A in matrices_s]
        chars_t = [characteristic_polynomial(A, 3) for A in matrices_t]
        result = refine_ambiguous_matrix_word_graph(
            matrices_s, matrices_t, chars_s, chars_t,
            baseline_edges(matrices_s), baseline_edges(matrices_t), 3,
            max_matrix_products=5000, max_word_length=5,
            max_polynomial_monomials=1,
        )
        report = result["adaptive_matrix_word_refinement"]
        tier = report["additional_word_tiers"][0]
        unresolved = tier["polynomial_unresolved_words"]
        self.assertTrue(unresolved)
        self.assertTrue(all(
            item["status"] == "unresolved_monomial_cap" for item in unresolved
        ))
        unresolved_names = {
            item["candidate_feature"].removeprefix("trace:")
            for item in unresolved
        }
        self.assertTrue(unresolved_names.issubset(set(tier["retained_words"])))
        self.assertEqual(
            report["polynomial_trace_dependency_reduction"]["unresolved_policy"],
            "retain_candidate_feature_and_report_unresolved",
        )

    def test_invalid_polynomial_degree_rejected(self):
        source_a, source_b, _, _ = discriminating_matrices()
        matrices = [source_a, source_a, source_b]
        chars = [characteristic_polynomial(A, 3) for A in matrices]
        edges = baseline_edges(matrices)
        with self.assertRaises(ValueError):
            refine_ambiguous_matrix_word_graph(
                matrices, matrices, chars, chars, edges, edges, 3,
                max_polynomial_degree=4,
            )

    def test_invalid_budgets_and_word_lengths_rejected(self):
        with self.assertRaises(ValueError):
            matrix_word_tiers(13)
        with self.assertRaises(ValueError):
            refine_ambiguous_matrix_word_graph([], [], [], [], [], [], 3)
        source_a, source_b, _, _ = discriminating_matrices()
        matrices = [source_a, source_a, source_b]
        chars = [characteristic_polynomial(A, 3) for A in matrices]
        edges = baseline_edges(matrices)
        with self.assertRaises(ValueError):
            refine_ambiguous_matrix_word_graph(
                matrices, matrices, chars, chars, edges, edges, 3,
                max_matrix_products=0,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
