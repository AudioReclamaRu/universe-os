import copy
import sys
import unittest
from pathlib import Path

PHASE16 = Path(__file__).resolve().parent.parent / "phase-16"
if str(PHASE16) not in sys.path:
    sys.path.insert(0, str(PHASE16))

from affine_ifs_underdetermined import compare_ifs_pair, analyze_payload


def same_fixed_point_control():
    source = {
        "dimension": 2,
        "radical": 3,
        "coordinate_system": "same_fixed_point_at_origin",
        "maps": [
            {"matrix": [["1/2", 0], [0, "1/3"]], "translation": [0, 0]},
            {"matrix": [["1/4", 0], [0, "1/5"]], "translation": [0, 0]},
        ],
    }
    target = {
        "dimension": 2,
        "radical": 3,
        "coordinate_system": "affine_transformed_same_fixed_point_cloud",
        "maps": [
            {"matrix": [["5/9", "-1/9"], ["1/9", "5/18"]],
             "translation": ["11/9", "-19/18"]},
            {"matrix": [["4/15", "-1/30"], ["1/30", "11/60"]],
             "translation": ["13/6", "-11/12"]},
        ],
    }
    return source, target


def affine_transform_1d(raw, scale, shift, coordinate_system):
    transformed = []
    for item in raw["maps"]:
        a = item["matrix"][0][0]
        b = item["translation"][0]
        # H(F(x)) = G(H(x)) for H(x)=scale*x+shift.
        c = a
        d = str(scale * __import__("fractions").Fraction(str(b)) +
                __import__("fractions").Fraction(str(shift)) -
                __import__("fractions").Fraction(str(c)) * __import__("fractions").Fraction(str(shift)))
        transformed.append({"matrix": [[str(c)]], "translation": [d]})
    return {"dimension": 1, "radical": raw.get("radical", 3),
            "coordinate_system": coordinate_system, "maps": transformed}


class UnderdeterminedAffineIFSTests(unittest.TestCase):
    def test_recovers_invertible_witness_when_fixed_points_do_not_span(self):
        source, target = same_fixed_point_control()
        result = compare_ifs_pair(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(result["linear_solution_family"]["free_parameter_count"], "<10_2|2_3>")
        self.assertNotEqual(result["affine_coordinate_change"]["determinant_P"], "<0_2|0_3>")
        self.assertTrue(result["verification"].startswith("Every affine map"))

    def test_one_dimensional_free_scale_is_constructively_resolved(self):
        source = {
            "dimension": 1, "radical": 3,
            "maps": [{"matrix": [["1/2"]], "translation": [0]}],
        }
        result = compare_ifs_pair(source, copy.deepcopy(source))
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(result["linear_solution_family"]["parameter_assignment"], ["<1_2|1_3>"])

    def test_identically_zero_determinant_family_is_rejected(self):
        source = {
            "dimension": 2, "radical": 3,
            "maps": [{"matrix": [[1, 0], [0, 1]], "translation": [0, 0]}],
        }
        target = {
            "dimension": 2, "radical": 3,
            "maps": [{"matrix": [[0, 0], [0, 0]], "translation": [0, 0]}],
        }
        result = compare_ifs_pair(source, target)
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertTrue(result["search"]["search_complete"])

    def test_permutation_limit_is_unresolved_not_negative(self):
        source = {
            "dimension": 1, "radical": 3,
            "maps": [
                {"matrix": [["1/2"]], "translation": [0]},
                {"matrix": [["1/4"]], "translation": [1]},
            ],
        }
        target = affine_transform_1d(source, 2, 3, "other_coordinates")
        target["maps"].reverse()
        limited = compare_ifs_pair(source, target, max_permutations=1)
        self.assertEqual(limited["status"], "permutation_search_limit_reached")
        self.assertFalse(limited["search"]["search_complete"])
        complete = compare_ifs_pair(source, target, max_permutations=2)
        self.assertEqual(complete["status"], "affine_conjugacy_verified")

    def test_unique_solution_case_remains_supported(self):
        source = {
            "dimension": 1, "radical": 3,
            "maps": [{"matrix": [["1/2"]], "translation": ["1/3"]}],
        }
        target = affine_transform_1d(source, 2, 3, "translated_scaled_line")
        result = compare_ifs_pair(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")

    def test_payload_requires_at_least_one_pair(self):
        with self.assertRaises(ValueError):
            analyze_payload({})


if __name__ == "__main__":
    unittest.main(verbosity=2)
