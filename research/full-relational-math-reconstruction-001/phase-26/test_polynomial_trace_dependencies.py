import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in ("phase-16", "phase-25", "phase-26"):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from polynomial_trace_dependencies import classify_polynomial_dependency


def qcolumn(values):
    return [core.q(value) for value in values]


class ExactPolynomialTraceDependencyTests(unittest.TestCase):
    def test_exact_quadratic_dependency_has_rowwise_certificate(self):
        x = qcolumn([1, 2, 3, 4, 5])
        x_squared = [core.mul(value, value, 3) for value in x]
        result = classify_polynomial_dependency(
            [x], ["trace:x"], x_squared, "trace:w", 3
        )
        self.assertEqual(result["status"], "polynomially_dependent_on_finite_support")
        self.assertTrue(result["certificate"]["all_residuals_exactly_zero"])
        self.assertEqual(result["certificate"]["sample_rows_checked"], core.paired(5))
        self.assertEqual(result["certificate"]["exact_zero_rows"], core.paired(5))
        self.assertTrue(any(
            term["monomial"] == "trace:x^2" and not term["candidate_term"]
            for term in result["polynomial_terms"]
        ))

    def test_degree_one_does_not_claim_a_quadratic_dependency(self):
        x = qcolumn([1, 2, 3, 4, 5])
        x_squared = [core.mul(value, value, 3) for value in x]
        result = classify_polynomial_dependency(
            [x], ["trace:x"], x_squared, "trace:w", 3, max_degree=1
        )
        self.assertEqual(result["status"], "independent_on_finite_support")
        self.assertFalse(result["polynomial_dependency_found"])

    def test_source_and_target_must_share_one_polynomial(self):
        x_source = qcolumn([1, 2, 3, 4, 5])
        x_target = qcolumn([1, 2, 3, 4, 5])
        x = x_source + x_target
        source_y = [core.mul(value, value, 3) for value in x_source]
        target_y = [core.mul(core.q(2), core.mul(value, value, 3), 3) for value in x_target]
        result = classify_polynomial_dependency(
            [x], ["trace:x"], source_y + target_y, "trace:y", 3
        )
        self.assertEqual(result["status"], "independent_on_finite_support")

    def test_monomial_span_saturation_is_unresolved_not_false_dependence(self):
        x = qcolumn([0, 0, 1, 1])
        y = qcolumn([0, 1, 0, 1])
        z = qcolumn([0, 0, 0, 1])
        candidate = qcolumn([3, 7, 11, 19])
        result = classify_polynomial_dependency(
            [x, y, z], ["x", "y", "z"], candidate, "w", 3
        )
        self.assertEqual(result["status"], "unresolved_monomial_span_saturates_samples")
        self.assertTrue(result["monomial_span_saturated"])

    def test_monomial_cap_is_unresolved(self):
        x = qcolumn([1, 2, 3, 4, 5])
        y = qcolumn([2, 3, 5, 7, 11])
        result = classify_polynomial_dependency(
            [x, y], ["x", "y"], qcolumn([1, 4, 9, 16, 25]), "w", 3,
            max_polynomial_monomials=5,
        )
        self.assertEqual(result["status"], "unresolved_monomial_cap")

    def test_finite_support_relation_does_not_survive_changed_sample_row(self):
        x = qcolumn([1, 2, 3, 4, 5])
        y = [core.mul(value, value, 3) for value in x]
        found = classify_polynomial_dependency(
            [x], ["x"], y, "y", 3
        )
        x_extended = x + [core.q(6)]
        y_extended = y + [core.q(40)]
        changed = classify_polynomial_dependency(
            [x_extended], ["x"], y_extended, "y", 3
        )
        self.assertEqual(found["status"], "polynomially_dependent_on_finite_support")
        self.assertEqual(changed["status"], "independent_on_finite_support")
        self.assertFalse(found["universal_identity"])

    def test_invalid_degree_rejected(self):
        with self.assertRaises(ValueError):
            classify_polynomial_dependency(
                [qcolumn([1, 2, 3, 4])], ["x"], qcolumn([1, 4, 9, 16]),
                "y", 3, max_degree=4,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
