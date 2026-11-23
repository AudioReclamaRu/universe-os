import copy
import sys
import unittest
from pathlib import Path

PHASE16 = Path(__file__).resolve().parent.parent / "phase-16"
if str(PHASE16) not in sys.path:
    sys.path.insert(0, str(PHASE16))

from affine_ifs_conjugacy import apply_affine_coordinate_change
from affine_ifs_scalable_matching import compare_ifs_pair_scalable, analyze_payload


def gasket():
    return {
        "dimension": 2, "radical": 3, "coordinate_system": "barycentric_triangle",
        "maps": [
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": ["1/2", 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, "1/2"]},
        ],
    }


def menger():
    maps = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if sum(v == 1 for v in (i, j, k)) < 2:
                    maps.append({"matrix": [["1/3", 0, 0], [0, "1/3", 0], [0, 0, "1/3"]],
                                 "translation": [str(i) + "/3", str(j) + "/3", str(k) + "/3"]})
    return {"dimension": 3, "radical": 3, "coordinate_system": "menger_xyz", "maps": maps}


class ScalableAffineIFSMatchingTests(unittest.TestCase):
    def test_gasket_coordinate_change(self):
        source = gasket()
        target = apply_affine_coordinate_change(source, [[2, 1], [1, 2]], [3, -1], "affine_xy")
        result = compare_ifs_pair_scalable(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(result["affine_coordinate_change"]["determinant_P"], "<11_2|10_3>")
        self.assertEqual(result["affine_coordinate_change"]["translation_t"], [
            "<100_2|11_3>",
            "<111_2|21_3>/<11_2|10_3>",
            "<1010_2|101_3>/<11_2|10_3>",
        ])
        self.assertFalse(result["search"]["map_permutation_enumeration"])

    def test_twenty_map_menger_shuffle_without_factorial_permutation_search(self):
        source = menger()
        target = apply_affine_coordinate_change(source, [[2, 1, 0], [0, 2, 1], [1, 0, 2]], [3, -2, 1], "menger_affine_xyz")
        target["maps"] = list(reversed(target["maps"]))
        result = compare_ifs_pair_scalable(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(len(result["map_permutation_target_index_for_each_source"]), 20)
        self.assertFalse(result["search"]["map_permutation_enumeration"])
        self.assertEqual(result["search"]["target_frames_tested"], "<10111_2|212_3>")

    def test_search_cap_is_unresolved(self):
        source = {"dimension": 2, "maps": [
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": ["1/2", 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, "1/2"]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": ["1/4", "1/5"]},
        ]}
        target = apply_affine_coordinate_change(source, [[2, 1], [1, 2]], [3, -1], "xy")
        target["maps"] = list(reversed(target["maps"]))
        result = compare_ifs_pair_scalable(source, target, max_target_frames=1)
        self.assertEqual(result["status"], "target_frame_search_limit_reached")
        self.assertFalse(result["search"]["frame_search_complete"])

    def test_complete_negative_search(self):
        source = gasket()
        target = apply_affine_coordinate_change(source, [[2, 1], [1, 2]], [3, -1], "xy")
        target["maps"][0]["matrix"][0][0] = "2/3"
        result = compare_ifs_pair_scalable(source, target)
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertTrue(result["search"]["frame_search_complete"])

    def test_nonunique_fixed_point_method_is_inconclusive(self):
        source = {"dimension": 1, "maps": [{"matrix": [[1]], "translation": [0]}]}
        self.assertEqual(compare_ifs_pair_scalable(source, source)["status"], "unique_fixed_point_method_not_applicable")

    def test_under_spanned_fixed_point_cloud_is_inconclusive(self):
        source = {"dimension": 2, "maps": [
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [1, 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [2, 0]},
        ]}
        self.assertEqual(compare_ifs_pair_scalable(source, source)["status"], "source_fixed_points_do_not_span_ambient_space")

    def test_map_count_mismatch(self):
        a = gasket(); b = copy.deepcopy(a); b["maps"].pop()
        self.assertEqual(compare_ifs_pair_scalable(a, b)["status"], "map_count_mismatch")

    def test_payload_requires_pair(self):
        with self.assertRaises(ValueError):
            analyze_payload({})

    def test_duplicate_fixed_points_preserve_map_multiplicity(self):
        source = {"dimension": 2, "maps": [
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, 0]},
            {"matrix": [["1/3", 0], [0, "1/3"]], "translation": [0, 0]},
            {"matrix": [["1/4", 0], [0, "1/4"]], "translation": ["3/4", 0]},
            {"matrix": [["1/5", 0], [0, "1/5"]], "translation": [0, "4/5"]},
        ]}
        target = apply_affine_coordinate_change(source, [[2, 1], [1, 2]], [3, -1], "shifted")
        target["maps"] = [target["maps"][2], target["maps"][0], target["maps"][3], target["maps"][1]]
        result = compare_ifs_pair_scalable(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(len(result["map_permutation_target_index_for_each_source"]), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
