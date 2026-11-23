import copy
import unittest

from affine_ifs_conjugacy import (
    analyze_payload, apply_affine_coordinate_change, compare_ifs_pair,
    paired,
)


def gasket():
    return {
        "dimension": 2,
        "radical": 3,
        "coordinate_system": "barycentric_triangle",
        "maps": [
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": ["1/2", 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, "1/2"]},
        ],
    }


class AffineIFSConjugacyTests(unittest.TestCase):
    def test_exact_affine_conjugacy_across_coordinate_systems(self):
        source = gasket()
        target = apply_affine_coordinate_change(
            source, [[2, 1], [1, 2]], [3, -1], "affine_demo_coordinates"
        )
        result = compare_ifs_pair(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(result["source_coordinate_system"], "barycentric_triangle")
        self.assertEqual(result["target_coordinate_system"], "affine_demo_coordinates")
        self.assertNotEqual(result["affine_coordinate_change"]["determinant_P"], "<0_2|0_3>")
        self.assertTrue(result["verification"].startswith("Every affine map"))

    def test_map_order_is_irrelevant(self):
        source = gasket()
        target = apply_affine_coordinate_change(source, [[2, 1], [1, 2]], [3, -1], "xy")
        target["maps"] = list(reversed(target["maps"]))
        self.assertEqual(compare_ifs_pair(source, target)["status"], "affine_conjugacy_verified")

    def test_quadratic_field_coefficients_are_exact(self):
        source = {
            "dimension": 1, "radical": 3, "coordinate_system": "u",
            "maps": [
                {"matrix": [["1/3"]], "translation": [{"rational": "0", "radical": "1/6"}]},
                {"matrix": [["1/3"]], "translation": [{"rational": "2/3", "radical": "-1/6"}]},
            ],
        }
        target = apply_affine_coordinate_change(source, [[2]], [1], "v")
        result = compare_ifs_pair(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(result["exact_field"], "Q(√3)")

    def test_exact_same_maps_need_not_produce_unique_transform(self):
        source = {
            "dimension": 1, "radical": 3, "coordinate_system": "x",
            "maps": [{"matrix": [["1/2"]], "translation": [0]}],
        }
        result = compare_ifs_pair(source, copy.deepcopy(source))
        self.assertEqual(result["status"], "affine_solution_underdetermined")

    def test_no_conjugacy_is_reported_only_after_complete_search(self):
        source = gasket()
        target = apply_affine_coordinate_change(source, [[2, 1], [1, 2]], [3, -1], "xy")
        target["maps"][0]["matrix"][0][0] = "2/3"
        result = compare_ifs_pair(source, target)
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertTrue(result["search"]["search_complete"])

    def test_search_cap_is_not_a_negative_result(self):
        source = {
            "dimension": 1, "radical": 3, "coordinate_system": "line_a",
            "maps": [
                {"matrix": [["1/2"]], "translation": [0]},
                {"matrix": [["1/2"]], "translation": [1]},
                {"matrix": [["1/2"]], "translation": [3]},
            ],
        }
        target = apply_affine_coordinate_change(source, [[2]], [1], "line_b")
        target["maps"] = list(reversed(target["maps"]))
        result = compare_ifs_pair(source, target, max_permutations=1)
        self.assertEqual(result["status"], "permutation_search_limit_reached")
        self.assertFalse(result["search"]["search_complete"])

    def test_dimension_mismatch(self):
        a = gasket()
        b = {"dimension": 1, "maps": [{"matrix": [["1/2"]], "translation": [0]}]}
        self.assertEqual(compare_ifs_pair(a, b)["status"], "dimension_mismatch")

    def test_quadratic_field_mismatch(self):
        a = gasket()
        b = copy.deepcopy(a); b["radical"] = 2
        self.assertEqual(compare_ifs_pair(a, b)["status"], "quadratic_field_mismatch")

    def test_map_count_mismatch(self):
        a = gasket(); b = copy.deepcopy(a); b["maps"].pop()
        self.assertEqual(compare_ifs_pair(a, b)["status"], "map_count_mismatch")

    def test_transform_rejects_singular_coordinate_matrix(self):
        with self.assertRaises(ValueError):
            apply_affine_coordinate_change(gasket(), [[1, 2], [2, 4]], [0, 0], "bad")

    def test_transform_rejects_wrong_dimensions(self):
        with self.assertRaises(ValueError):
            apply_affine_coordinate_change(gasket(), [[1]], [0], "bad")

    def test_invalid_radicand_rejected(self):
        bad = gasket(); bad["radical"] = 4
        with self.assertRaises(ValueError):
            compare_ifs_pair(bad, bad)

    def test_payload_requires_pairs(self):
        with self.assertRaises(ValueError):
            analyze_payload({})

    def test_paired_integer_encoding(self):
        self.assertEqual(paired(7), "<111_2|21_3>")

    def test_paired_integer_and_fraction_inputs_are_accepted(self):
        source = {
            "dimension": 1, "radical": 3, "coordinate_system": "paired",
            "maps": [{"matrix": [["<1_2|1_3>/<10_2|2_3>"]],
                      "translation": ["<0_2|0_3>"]}],
        }
        self.assertEqual(compare_ifs_pair(source, copy.deepcopy(source))["status"], "affine_solution_underdetermined")

    def test_inconsistent_paired_integer_is_rejected(self):
        source = {
            "dimension": 1, "radical": 3,
            "maps": [{"matrix": [["<1_2|2_3>"]], "translation": [0]}],
        }
        with self.assertRaises(ValueError):
            compare_ifs_pair(source, source)

    def test_nonsquarefree_radical_is_rejected(self):
        source = {"dimension": 1, "radical": 12,
                  "maps": [{"matrix": [["1/2"]], "translation": [0]}]}
        with self.assertRaises(ValueError):
            compare_ifs_pair(source, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
