import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-16", "phase-24", "phase-25"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from trace_feature_dependencies import (
    BASELINE_WORDS,
    COMMUTATOR_IDENTITY,
    compress_phase21_edges,
    insert_feature,
    new_dependency_basis,
)


class ExactTraceFeatureDependencyTests(unittest.TestCase):
    def test_phase21_commutator_square_is_exact_universal_reduction(self):
        A = [[core.q("1/2"), core.q("1/3")], [core.q("1/5"), core.q("1/4")]]
        B = [[core.q("1/3"), core.q("1/7")], [core.q("1/6"), core.q("1/5")]]
        from affine_ifs_joint_trace_partition import _pair_relation_record
        record = _pair_relation_record(A, B, 3)
        edges = [[record]]
        compressed = compress_phase21_edges(edges, 3)
        self.assertEqual(len(compressed[0][0]), 5)
        expected = core.mul(core.q(2), core.sub(record[3], record[4]), 3)
        self.assertEqual(record[5], expected)
        self.assertEqual(
            COMMUTATOR_IDENTITY["equation"],
            "tr([A,B]^2) - 2 tr(ABAB) + 2 tr(AABB) = 0",
        )
        self.assertEqual(len(BASELINE_WORDS), 5)

    def test_invalid_phase21_identity_is_not_silently_compressed(self):
        bad = [[(core.Z, core.Z, core.Z, core.Z, core.Z, core.O)]]
        with self.assertRaises(ArithmeticError):
            compress_phase21_edges(bad, 3)

    def test_exact_dependency_returns_shared_coefficients_for_all_samples(self):
        # f2 = 2*f0 - 3*f1 at every combined sample row.
        f0 = [core.q(1), core.q(2), core.q(4), core.q(5)]
        f1 = [core.q(2), core.q(0), core.q(1), core.q(3)]
        f2 = [
            core.add(core.mul(core.q(2), a, 3), core.mul(core.q(-3), b, 3))
            for a, b in zip(f0, f1)
        ]
        basis = new_dependency_basis()
        self.assertTrue(insert_feature(basis, "trace:u", f0, 3)[0])
        self.assertTrue(insert_feature(basis, "trace:v", f1, 3)[0])
        independent, relation = insert_feature(basis, "trace:w", f2, 3)
        self.assertFalse(independent)
        self.assertEqual(
            {item["feature"]: item["coefficient"] for item in relation["equation_terms"]},
            {"trace:u": "<10_2|2_3>", "trace:v": "-<11_2|10_3>", "trace:w": "<1_2|1_3>"},
        )

    def test_local_dependency_is_explicitly_not_a_universal_identity(self):
        basis = new_dependency_basis()
        self.assertTrue(insert_feature(
            basis, "trace:01", [core.q(7), core.q(7)], 3
        )[0])
        independent, relation = insert_feature(
            basis, "trace:00101", [core.q(14), core.q(14)], 3
        )
        self.assertFalse(independent)
        self.assertIn("finite comparison", relation["logical_status"])
        self.assertIn("active ordered-pair support", relation["logical_status"])

    def test_independent_candidate_is_retained_in_exact_basis(self):
        basis = new_dependency_basis()
        self.assertTrue(insert_feature(
            basis, "trace:01", [core.q(1), core.q(0), core.q(2)], 3
        )[0])
        self.assertTrue(insert_feature(
            basis, "trace:001", [core.q(0), core.q(1), core.q(2)], 3
        )[0])
        self.assertEqual(len(basis), 2)

    def test_field_validation(self):
        with self.assertRaises(ValueError):
            insert_feature(new_dependency_basis(), "trace:x", [core.q(1)], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
