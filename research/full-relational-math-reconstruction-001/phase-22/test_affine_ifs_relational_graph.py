import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-16", "phase-18", "phase-20", "phase-21", "phase-22"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from affine_ifs_conjugacy import apply_affine_coordinate_change
from affine_ifs_relational_graph import (
    compare_ifs_pair_relational_graph,
    analyze_payload,
)


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


def equal_charpoly_relational_mismatch():
    source = {
        "dimension": 2, "radical": 3,
        "coordinate_system": "two_source_operators",
        "maps": [
            {"matrix": [["1/2", 0], [0, "1/3"]], "translation": [0, 0]},
            {"matrix": [["1/3", 0], [0, "1/2"]], "translation": [0, 0]},
        ],
    }
    repeated = [["1/2", 0], [0, "1/3"]]
    target = {
        "dimension": 2, "radical": 3,
        "coordinate_system": "repeated_target_operator",
        "maps": [
            {"matrix": repeated, "translation": [0, 0]},
            {"matrix": copy.deepcopy(repeated), "translation": [0, 0]},
        ],
    }
    return source, target


def gasket():
    return {
        "dimension": 2, "radical": 3, "coordinate_system": "barycentric_triangle",
        "maps": [
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": ["1/2", 0]},
            {"matrix": [["1/2", 0], [0, "1/2"]], "translation": [0, "1/2"]},
        ],
    }



def higher_word_collision_pair():
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
    return (
        {
            "dimension": 3, "radical": 3, "coordinate_system": "source_contracting_operators",
            "maps": [
                {"matrix": copy.deepcopy(source_a), "translation": [0, 0, 0]},
                {"matrix": copy.deepcopy(source_a), "translation": [0, 0, 0]},
                {"matrix": source_b, "translation": [0, 0, 0]},
            ],
        },
        {
            "dimension": 3, "radical": 3, "coordinate_system": "target_contracting_operators",
            "maps": [
                {"matrix": copy.deepcopy(target_a), "translation": [0, 0, 0]},
                {"matrix": copy.deepcopy(target_a), "translation": [0, 0, 0]},
                {"matrix": target_b, "translation": [0, 0, 0]},
            ],
        },
    )

class RelationalGraphConjugacyTests(unittest.TestCase):
    def test_recovers_exact_common_affine_transform(self):
        source, target = same_slope_translation_pair()
        result = compare_ifs_pair_relational_graph(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertIn("adaptive_colour_refinement", result)
        self.assertTrue(result["adaptive_colour_refinement"]["stable"])
        self.assertEqual(result["affine_coordinate_change"]["matrix_P"], [["<10_2|2_3>"]])
        self.assertEqual(result["affine_coordinate_change"]["translation_t"], ["<11_2|10_3>"])
        self.assertEqual(result["map_permutation_target_index_for_each_source"],
                         ["<0_2|0_3>", "<1_2|1_3>"])
        self.assertTrue(result["verification"].startswith("Every affine map equation"))

    def test_target_map_order_is_permutation_invariant(self):
        source, target = same_slope_translation_pair()
        target["maps"].reverse()
        result = compare_ifs_pair_relational_graph(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(
            sorted(result["map_permutation_target_index_for_each_source"]),
            ["<0_2|0_3>", "<1_2|1_3>"],
        )
        self.assertTrue(result["verification"].startswith("Every affine map equation"))

    def test_full_relational_graph_rejects_equal_vertex_spectra_incompatible_family(self):
        source, target = equal_charpoly_relational_mismatch()
        result = compare_ifs_pair_relational_graph(source, target)
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertTrue(result["search"]["graph_search_complete"])
        self.assertEqual(result["candidate_edge_count"], "<0_2|0_3>")
        self.assertEqual(
            result["adaptive_colour_refinement"]["candidate_edges_after_refinement"],
            "<0_2|0_3>",
        )

    def test_complete_negative_after_all_relational_isomorphisms(self):
        source, target = ambiguous_nonconjugate_translation_pair()
        result = compare_ifs_pair_relational_graph(
            source, target,
            max_candidate_isomorphisms=6,
        )
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        self.assertTrue(result["search"]["graph_search_complete"])
        self.assertEqual(result["search"]["candidate_isomorphisms_tested"], "<110_2|20_3>")

    def test_graph_search_cap_is_unresolved_not_negative(self):
        source, target = ambiguous_nonconjugate_translation_pair()
        result = compare_ifs_pair_relational_graph(
            source, target,
            max_graph_nodes=1,
        )
        self.assertEqual(result["status"], "relational_graph_search_limit_reached")
        self.assertFalse(result["search"]["graph_search_complete"])

    def test_gasket_family_remains_exactly_conjugate(self):
        source = gasket()
        target = apply_affine_coordinate_change(
            source, [[2, 1], [1, 2]], [3, -1], "affine_gasket_frame"
        )
        target["maps"] = list(reversed(target["maps"]))
        result = compare_ifs_pair_relational_graph(source, target)
        self.assertEqual(result["status"], "affine_conjugacy_verified")
        self.assertEqual(len(result["map_permutation_target_index_for_each_source"]), 3)


    def test_phase24_higher_word_prunes_ambiguous_class_after_length_six(self):
        source, target = higher_word_collision_pair()
        result = compare_ifs_pair_relational_graph(source, target)
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        report = result["adaptive_matrix_word_refinement"]
        applied = [tier for tier in report["additional_word_tiers"] if tier["applied"]]
        self.assertEqual([tier["length"] for tier in applied], ["<101_2|12_3>", "<110_2|20_3>"])
        self.assertEqual(applied[0]["candidate_edges_after"], applied[1]["candidate_edges_before"])
        self.assertEqual(applied[0]["candidate_edges_after"], "<101_2|12_3>")
        self.assertEqual(applied[1]["candidate_edges_after"], "<0_2|0_3>")
        self.assertIn("001011", applied[1]["words"])
        self.assertEqual(result["search"]["affine_families_solved"], "<0_2|0_3>")
        self.assertEqual(report["expansion_status"], "no_compatible_colour_bijection")

    def test_phase24_budget_skips_whole_word_tier_and_exact_solver_remains_decisive(self):
        source, target = higher_word_collision_pair()
        result = compare_ifs_pair_relational_graph(
            source, target, max_matrix_products=479, max_word_length=6
        )
        self.assertEqual(result["status"], "no_affine_conjugacy_found")
        report = result["adaptive_matrix_word_refinement"]
        tiers = report["additional_word_tiers"]
        self.assertEqual(len(tiers), 1)
        self.assertFalse(tiers[0]["applied"])
        self.assertEqual(tiers[0]["required_matrix_products"], "<111011111_2|121112_3>")
        self.assertEqual(report["matrix_product_budget"]["used"], "<0_2|0_3>")
        self.assertTrue(result["search"]["graph_search_complete"])

    def test_empty_payload_rejected(self):
        with self.assertRaises(ValueError):
            analyze_payload({})


if __name__ == "__main__":
    unittest.main(verbosity=2)
