import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-16", "phase-17", "phase-18", "phase-22"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from affine_ifs_conjugacy import apply_affine_coordinate_change
from adaptive_affine_ifs_comparator import compare_ifs_pair_adaptive, analyze_payload


def same_fixed_point_pair():
    source = {
        "dimension": 2, "radical": 3,
        "coordinate_system": "same_fixed_point_at_origin",
        "maps": [
            {"matrix": [["1/2", 0], [0, "1/3"]], "translation": [0, 0]},
            {"matrix": [["1/4", 0], [0, "1/5"]], "translation": [0, 0]},
        ],
    }
    target = {
        "dimension": 2, "radical": 3,
        "coordinate_system": "affine_transformed_same_fixed_point_cloud",
        "maps": [
            {"matrix": [["5/9", "-1/9"], ["1/9", "5/18"]],
             "translation": ["11/9", "-19/18"]},
            {"matrix": [["4/15", "-1/30"], ["1/30", "11/60"]],
             "translation": ["13/6", "-11/12"]},
        ],
    }
    return source, target


def menger_control():
    source_maps = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if sum(v == 1 for v in (i, j, k)) < 2:
                    source_maps.append({
                        "matrix": [["1/3", 0, 0], [0, "1/3", 0], [0, 0, "1/3"]],
                        "translation": [str(i) + "/3", str(j) + "/3", str(k) + "/3"],
                    })
    source = {
        "dimension": 3, "radical": 3, "coordinate_system": "menger_xyz",
        "maps": source_maps,
    }
    target = apply_affine_coordinate_change(
        source, [[2, 1, 0], [0, 2, 1], [1, 0, 2]], [3, -2, 1],
        "menger_affine_xyz",
    )
    target["maps"].reverse()
    return source, target


def equal_charpoly_relational_mismatch():
    a1 = [["1/2", 0], [0, "1/3"]]
    a2 = [["1/3", 0], [0, "1/2"]]
    repeated = [["1/2", 0], [0, "1/3"]]
    source = {
        "dimension": 2, "radical": 3, "coordinate_system": "two_source_operators",
        "maps": [
            {"matrix": a1, "translation": [0, 0]},
            {"matrix": a2, "translation": [0, 0]},
        ],
    }
    target = {
        "dimension": 2, "radical": 3, "coordinate_system": "repeated_target_operator",
        "maps": [
            {"matrix": repeated, "translation": [0, 0]},
            {"matrix": copy.deepcopy(repeated), "translation": [0, 0]},
        ],
    }
    return source, target


def ambiguous_nonconjugate_translation_pair():
    source = {
        "dimension": 1, "radical": 3,
        "maps": [
            {"matrix": [["1/2"]], "translation": [0]},
            {"matrix": [["1/2"]], "translation": [1]},
            {"matrix": [["1/2"]], "translation": [2]},
        ],
    }
    target = {
        "dimension": 1, "radical": 3,
        "maps": [
            {"matrix": [["1/2"]], "translation": [0]},
            {"matrix": [["1/2"]], "translation": [1]},
            {"matrix": [["1/2"]], "translation": [4]},
        ],
    }
    return source, target


def nonunique_fixed_point_nonconjugate_pair():
    identity = [[1, 0], [0, 1]]
    jordan = [[1, 1], [0, 1]]
    source = {
        "dimension": 2, "radical": 3, "coordinate_system": "identity_operator_family",
        "maps": [
            {"matrix": identity, "translation": [0, 0]},
            {"matrix": copy.deepcopy(identity), "translation": [0, 0]},
            {"matrix": copy.deepcopy(identity), "translation": [0, 0]},
        ],
    }
    target = {
        "dimension": 2, "radical": 3, "coordinate_system": "jordan_operator_family",
        "maps": [
            {"matrix": jordan, "translation": [0, 0]},
            {"matrix": copy.deepcopy(jordan), "translation": [0, 0]},
            {"matrix": copy.deepcopy(jordan), "translation": [0, 0]},
        ],
    }
    return source, target


class AdaptiveAffineIFSComparatorTests(unittest.TestCase):
    def test_uses_phase17_for_full_rank_menger_fixed_point_cloud(self):
        source, target = menger_control()
        result = compare_ifs_pair_adaptive(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(result["selected_method"], "phase17_exact_fixed_point_frames")
        self.assertEqual(result["attempt_count"], "<1_2|1_3>")
        self.assertEqual(
            result["final_result"]["search"]["target_frames_tested"],
            "<10111_2|212_3>",
        )

    def test_falls_back_to_phase22_relational_graph(self):
        source, target = same_fixed_point_pair()
        result = compare_ifs_pair_adaptive(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(
            result["selected_method"],
            "phase22_edge_labelled_relational_graph_plus_exact_affine_solver",
        )
        self.assertEqual(result["attempt_count"], "<10_2|2_3>")
        self.assertEqual(
            result["attempts"][0]["status"],
            "source_fixed_points_do_not_span_ambient_space",
        )
        self.assertTrue(result["final_result"]["verification"].startswith("Every affine map"))

    def test_phase17_frame_cap_remains_unresolved_without_fallback(self):
        source, target = menger_control()
        result = compare_ifs_pair_adaptive(source, target, max_target_frames=1)
        self.assertEqual(result["status"], "target_frame_search_limit_reached")
        self.assertEqual(result["attempt_count"], "<1_2|1_3>")
        self.assertIn("unresolved", result["decision"])

    def test_complete_phase17_negative_result_is_terminal(self):
        source = {
            "dimension": 1, "radical": 3, "coordinate_system": "source_line",
            "maps": [
                {"matrix": [["1/2"]], "translation": [0]},
                {"matrix": [["1/4"]], "translation": [1]},
            ],
        }
        target = {
            "dimension": 1, "radical": 3, "coordinate_system": "target_line",
            "maps": [
                {"matrix": [["1/2"]], "translation": [0]},
                {"matrix": [["1/3"]], "translation": [1]},
            ],
        }
        result = compare_ifs_pair_adaptive(source, target)
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertEqual(result["attempt_count"], "<1_2|1_3>")

    def test_input_mismatch_does_not_trigger_fallback(self):
        source = {"dimension": 1, "maps": [{"matrix": [["1/2"]], "translation": [0]}]}
        target = {"dimension": 2, "maps": [{"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, 0]}]}
        result = compare_ifs_pair_adaptive(source, target)
        self.assertEqual(result["status"], "dimension_mismatch")
        self.assertEqual(result["attempt_count"], "<1_2|1_3>")

    def test_phase22_rejects_equal_charpoly_incompatible_relational_graph(self):
        source, target = equal_charpoly_relational_mismatch()
        result = compare_ifs_pair_adaptive(source, target)
        self.assertEqual(
            result["selected_method"],
            "phase22_edge_labelled_relational_graph_plus_exact_affine_solver",
        )
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertEqual(result["final_result"]["candidate_edge_count"], "<0_2|0_3>")

    def test_phase22_graph_cap_remains_unresolved(self):
        source, target = nonunique_fixed_point_nonconjugate_pair()
        result = compare_ifs_pair_adaptive(source, target, max_graph_nodes=1)
        self.assertEqual(
            result["attempts"][0]["status"],
            "unique_fixed_point_method_not_applicable",
        )
        self.assertEqual(result["status"], "relational_graph_search_limit_reached")
        self.assertFalse(result["final_result"]["search"]["graph_search_complete"])


    def test_phase24_budget_is_forwarded_through_adaptive_controller(self):
        source, target = same_fixed_point_pair()
        result = compare_ifs_pair_adaptive(
            source, target, max_matrix_products=1, max_word_length=5
        )
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        budget = result["final_result"]["adaptive_matrix_word_refinement"]["matrix_product_budget"]
        self.assertEqual(budget["limit"], "<1_2|1_3>")
        self.assertEqual(result["selected_method"],
                         "phase22_edge_labelled_relational_graph_plus_exact_affine_solver")

    def test_phase26_polynomial_controls_forward_through_adaptive_controller(self):
        source_a = [
            ["3/4", "3/4", "1/2"],
            [0, "1/2", 0],
            [0, "-1/2", "1/4"],
        ]
        source_b = [
            ["3/4", 0, 0],
            ["-1/4", "1/2", 0],
            ["-1/2", 0, "1/4"],
        ]
        target_a = [
            ["3/4", 0, "-1/2"],
            [0, "1/2", "1/4"],
            [0, 0, "1/4"],
        ]
        target_b = [
            ["1/4", 0, 0],
            ["-1/4", "1/2", 0],
            ["1/4", "-1/4", "3/4"],
        ]
        zero = [0, 0, 0]
        source = {
            "dimension": 3, "radical": 3,
            "coordinate_system": "phase26_source_control",
            "maps": [
                {"matrix": source_a, "translation": zero},
                {"matrix": source_a, "translation": zero},
                {"matrix": source_b, "translation": zero},
            ],
        }
        target = {
            "dimension": 3, "radical": 3,
            "coordinate_system": "phase26_target_control",
            "maps": [
                {"matrix": target_a, "translation": zero},
                {"matrix": target_a, "translation": zero},
                {"matrix": target_b, "translation": zero},
            ],
        }
        result = compare_ifs_pair_adaptive(
            source, target, max_matrix_products=5000, max_word_length=6,
            max_polynomial_monomials=1,
        )
        self.assertEqual(
            result["selected_method"],
            "phase22_edge_labelled_relational_graph_plus_exact_affine_solver",
        )
        report = result["final_result"]["adaptive_matrix_word_refinement"]
        self.assertEqual(
            report["polynomial_trace_dependency_reduction"]["max_polynomial_monomials"],
            "<1_2|1_3>",
        )
        unresolved = [
            item
            for tier in report["additional_word_tiers"]
            for item in tier["polynomial_unresolved_words"]
        ]
        self.assertTrue(unresolved)
        self.assertTrue(all(
            item["status"] == "unresolved_monomial_cap" for item in unresolved
        ))

    def test_empty_payload_rejected(self):
        with self.assertRaises(ValueError):
            analyze_payload({})


if __name__ == "__main__":
    unittest.main(verbosity=2)
