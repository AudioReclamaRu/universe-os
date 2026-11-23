import unittest

from affine_ifs_adaptive_color_refinement import refine_joint_directed_colours


def two_colour_graph(reverse_relation=False):
    colours = ["red", "red", "blue", "blue"]
    labels = []
    for i in range(4):
        row = []
        for j in range(4):
            same = colours[i] == colours[j]
            is_x = (not same) if reverse_relation else same
            row.append("X" if is_x else "Y")
        labels.append(row)
    return colours, labels


def permute_graph(colours, labels, permutation):
    return (
        [colours[i] for i in permutation],
        [[labels[i][j] for j in permutation] for i in permutation],
    )


class AdaptiveDirectedColourRefinementTests(unittest.TestCase):
    def test_refinement_detects_neighbour_colour_incidence_lost_by_row_profiles(self):
        source_colours, source_edges = two_colour_graph(False)
        target_colours, target_edges = two_colour_graph(True)
        self.assertEqual(
            sorted(tuple(sorted(row)) for row in source_edges),
            sorted(tuple(sorted(row)) for row in target_edges),
        )
        result = refine_joint_directed_colours(
            source_colours, target_colours, source_edges, target_edges
        )
        self.assertTrue(result["stable"])
        self.assertGreaterEqual(result["refinement_rounds"], 1)
        self.assertEqual(result["candidate_edges_after_refinement"], 0)
        self.assertEqual(result["candidate_edges_removed"], 8)
        self.assertTrue(all(not row for row in result["candidate_map_indices"]))

    def test_relabelled_isomorphic_graph_keeps_a_bijective_candidate_relation(self):
        colours, edges = two_colour_graph(False)
        permutation = [2, 0, 3, 1]
        target_colours, target_edges = permute_graph(colours, edges, permutation)
        result = refine_joint_directed_colours(
            colours, target_colours, edges, target_edges
        )
        self.assertTrue(result["stable"])
        self.assertEqual(result["candidate_edges_after_refinement"], 8)
        expected = {source: target for target, source in enumerate(permutation)}
        for source, target in expected.items():
            self.assertIn(target, result["candidate_map_indices"][source])
        self.assertTrue(all(result["candidate_map_indices"]))

    def test_direction_is_retained(self):
        source_colours = ["same", "same", "same"]
        target_colours = ["same", "same", "same"]
        source_edges = [
            ["loop", "a", "b"],
            ["b", "loop", "a"],
            ["a", "b", "loop"],
        ]
        target_edges = [
            ["loop", "b", "a"],
            ["a", "loop", "b"],
            ["b", "a", "loop"],
        ]
        result = refine_joint_directed_colours(
            source_colours, target_colours, source_edges, target_edges
        )
        # This regular control can remain inconclusive; refinement must not
        # invent a negative result where its colour classes remain broad.
        self.assertTrue(result["stable"])
        self.assertTrue(all(result["candidate_map_indices"]))

    def test_self_loops_and_multiplicity_affect_refinement(self):
        source_colours = ["A", "B"]
        target_colours = ["A", "B"]
        source_edges = [["loop-A", "cross"], ["cross", "loop-B"]]
        target_edges = [["loop-B", "cross"], ["cross", "loop-A"]]
        result = refine_joint_directed_colours(
            source_colours, target_colours, source_edges, target_edges
        )
        self.assertEqual(result["candidate_edges_after_refinement"], 0)

    def test_invalid_graph_shapes_rejected(self):
        with self.assertRaises(ValueError):
            refine_joint_directed_colours(["A"], ["A", "B"], [["x"]], [["x", "x"], ["x", "x"]])
        with self.assertRaises(ValueError):
            refine_joint_directed_colours(["A"], ["A"], [], [["x"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
