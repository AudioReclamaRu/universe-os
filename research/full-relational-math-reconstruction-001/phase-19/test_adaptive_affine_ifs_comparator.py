import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-16", "phase-17", "phase-18", "phase-20"):
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
                        "translation": [f"{i}/3", f"{j}/3", f"{k}/3"],
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


def ambiguous_no_conjugacy_pair():
    # Both source maps fix the origin and have the same characteristic polynomial,
    # but they are distinct diagonal matrices. Both targets repeat only A1.
    # No single invertible P can conjugate both source maps to the same target matrix.
    a1 = [["1/2", 0], [0, "1/3"]]
    a2 = [["1/3", 0], [0, "1/2"]]
    target_matrix = [["1/2", 0], [0, "1/3"]]
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
            {"matrix": target_matrix, "translation": [0, 0]},
            {"matrix": copy.deepcopy(target_matrix), "translation": [0, 0]},
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

    def test_falls_back_to_phase20_partition_and_phase18_solver(self):
        source, target = same_fixed_point_pair()
        result = compare_ifs_pair_adaptive(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(
            result["selected_method"],
            "phase20_characteristic_partition_plus_phase18_exact_solver",
        )
        self.assertEqual(result["attempt_count"], "<10_2|2_3>")
        self.assertEqual(
            result["attempts"][0]["status"],
            "source_fixed_points_do_not_span_ambient_space",
        )
        self.assertEqual(result["attempts"][1]["result"]["candidate_edge_count"],
                         "<10_2|2_3>")

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

    def test_phase20_candidate_matching_cap_remains_unresolved(self):
        source, target = ambiguous_no_conjugacy_pair()
        result = compare_ifs_pair_adaptive(source, target, max_candidate_matchings=1)
        self.assertEqual(
            result["selected_method"],
            "phase20_characteristic_partition_plus_phase18_exact_solver",
        )
        self.assertEqual(result["status"], "candidate_matching_search_limit_reached")
        self.assertFalse(result["final_result"]["search"]["search_complete"])

    def test_complete_phase20_candidate_search_can_return_negative(self):
        source, target = ambiguous_no_conjugacy_pair()
        result = compare_ifs_pair_adaptive(source, target, max_candidate_matchings=2)
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertTrue(result["final_result"]["search"]["search_complete"])

    def test_empty_payload_rejected(self):
        with self.assertRaises(ValueError):
            analyze_payload({})


if __name__ == "__main__":
    unittest.main(verbosity=2)
