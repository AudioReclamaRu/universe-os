import copy
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-16", "phase-18", "phase-20"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from affine_ifs_conjugacy import apply_affine_coordinate_change
from affine_ifs_characteristic_partition import (
    characteristic_polynomial,
    compare_ifs_pair_partitioned,
    analyze_payload,
)


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


class CharacteristicPartitionTests(unittest.TestCase):
    def test_exact_three_dimensional_characteristic_polynomial(self):
        diagonal = [[F(1), F(0), F(0)], [F(0), F(2), F(0)], [F(0), F(0), F(3)]]
        signature = characteristic_polynomial(
            [[(v, F(0)) for v in row] for row in diagonal], 3
        )
        self.assertEqual(signature, (
            (F(1), F(0)), (F(-6), F(0)), (F(11), F(0)), (F(-6), F(0))
        ))

    def test_distinct_linear_signatures_reduce_factorial_search(self):
        source = {
            "dimension": 1, "radical": 3, "coordinate_system": "source_line",
            "maps": [
                {"matrix": [["1/2"]], "translation": [0]},
                {"matrix": [["1/3"]], "translation": [0]},
                {"matrix": [["1/4"]], "translation": [0]},
                {"matrix": [["1/5"]], "translation": [0]},
            ],
        }
        # H(x)=2x+3; each scalar linear part is unchanged by 1D conjugacy.
        target = copy.deepcopy(source)
        target["coordinate_system"] = "target_line"
        for item in target["maps"]:
            a = F(item["matrix"][0][0])
            item["translation"] = [str((1-a)*3)]
        result = compare_ifs_pair_partitioned(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(result["candidate_edge_count"], "<100_2|11_3>")
        self.assertEqual(result["unrestricted_permutation_count"], "<11000_2|222_3>")

    def test_same_fixed_point_family_is_still_matched_exactly(self):
        source, target = same_fixed_point_pair()
        result = compare_ifs_pair_partitioned(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(result["candidate_edge_count"], "<10_2|2_3>")
        self.assertEqual(result["map_permutation_target_index_for_each_source"],
                         ["<0_2|0_3>", "<1_2|1_3>"])

    def test_characteristic_invariant_mismatch_proves_no_map_bijection(self):
        source = {
            "dimension": 1, "radical": 3,
            "maps": [
                {"matrix": [["1/2"]], "translation": [0]},
                {"matrix": [["1/4"]], "translation": [1]},
            ],
        }
        target = {
            "dimension": 1, "radical": 3,
            "maps": [
                {"matrix": [["1/2"]], "translation": [0]},
                {"matrix": [["1/3"]], "translation": [1]},
            ],
        }
        result = compare_ifs_pair_partitioned(source, target)
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertTrue(result["search_complete"])
        self.assertEqual(result["candidate_edge_count"], "<1_2|1_3>")

    def test_ambiguous_candidate_graph_search_cap_is_unresolved(self):
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
                {"matrix": [["1/2"]], "translation": [2]},
                {"matrix": [["1/2"]], "translation": [5]},
            ],
        }
        result = compare_ifs_pair_partitioned(source, target, max_candidate_matchings=1)
        self.assertEqual(result["status"], "candidate_matching_search_limit_reached")
        self.assertFalse(result["search"]["search_complete"])

    def test_empty_payload_rejected(self):
        with self.assertRaises(ValueError):
            analyze_payload({})


if __name__ == "__main__":
    unittest.main(verbosity=2)
