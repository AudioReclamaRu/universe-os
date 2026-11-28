import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-16", "phase-18", "phase-20", "phase-21"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from affine_ifs_conjugacy import apply_affine_coordinate_change
from affine_ifs_joint_trace_partition import (
    compare_ifs_pair_trace_partitioned,
    relational_trace_profiles,
    analyze_payload,
)


def shared_fixed_point_nonconjugate_pair():
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


def same_slope_translation_pair():
    source = {
        "dimension": 1, "radical": 3, "coordinate_system": "source_line",
        "maps": [
            {"matrix": [["1/2"]], "translation": [0]},
            {"matrix": [["1/2"]], "translation": [1]},
        ],
    }
    target = {
        "dimension": 1, "radical": 3, "coordinate_system": "target_line",
        "maps": [
            {"matrix": [["1/2"]], "translation": ["3/2"]},
            {"matrix": [["1/2"]], "translation": ["7/2"]},
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


class JointTracePartitionTests(unittest.TestCase):
    def test_joint_trace_profiles_prune_equal_charpoly_but_incompatible_families(self):
        source, target = shared_fixed_point_nonconjugate_pair()
        result = compare_ifs_pair_trace_partitioned(source, target)
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertEqual(
            result["candidate_filter"]["characteristic_polynomial_edges"],
            "<100_2|11_3>",
        )
        self.assertEqual(
            result["candidate_filter"]["edges_after_refinement"],
            "<0_2|0_3>",
        )
        self.assertEqual(
            result["joint_relational_trace_filter"]["source_profile_class_count"],
            "<1_2|1_3>",
        )

    def test_same_linear_parts_remain_valid_under_affine_translation(self):
        source, target = same_slope_translation_pair()
        result = compare_ifs_pair_trace_partitioned(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(
            result["joint_relational_trace_filter"]["candidate_edges_after_relational_filter"],
            "<100_2|11_3>",
        )
        self.assertEqual(result["affine_coordinate_change"]["matrix_P"], [["<10_2|2_3>"]])
        self.assertEqual(result["affine_coordinate_change"]["translation_t"], ["<11_2|10_3>"])

    def test_map_order_permutation_does_not_change_trace_profiles(self):
        source, target = same_slope_translation_pair()
        target["maps"].reverse()
        result = compare_ifs_pair_trace_partitioned(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(
            result["joint_relational_trace_filter"]["candidate_edges_after_relational_filter"],
            "<100_2|11_3>",
        )

    def test_profile_multiset_preserves_map_multiplicity(self):
        source, target = shared_fixed_point_nonconjugate_pair()
        _, source_radical, _, source_maps = core._parse(source)
        _, target_radical, _, target_maps = core._parse(target)
        source_profiles = relational_trace_profiles(source_maps, source_radical)
        target_profiles = relational_trace_profiles(target_maps, target_radical)
        self.assertEqual(len(source_profiles), 2)
        self.assertEqual(len(target_profiles), 2)
        self.assertNotEqual(source_profiles[0], target_profiles[0])

    def test_ambiguous_matchings_respect_search_cap(self):
        source, target = ambiguous_nonconjugate_translation_pair()
        result = compare_ifs_pair_trace_partitioned(
            source, target, max_candidate_matchings=1
        )
        self.assertEqual(result["status"], "candidate_matching_search_limit_reached")
        self.assertFalse(result["search"]["search_complete"])

    def test_complete_search_reports_negative_only_after_all_matchings(self):
        source, target = ambiguous_nonconjugate_translation_pair()
        result = compare_ifs_pair_trace_partitioned(
            source, target, max_candidate_matchings=6
        )
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertTrue(result["search"]["search_complete"])

    def test_payload_requires_pairs(self):
        with self.assertRaises(ValueError):
            analyze_payload({})


if __name__ == "__main__":
    unittest.main(verbosity=2)
