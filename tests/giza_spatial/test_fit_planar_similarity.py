import csv
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "giza_spatial"))
from fit_planar_similarity import (
    PointPair,
    TransformError,
    calculate_metrics,
    fit_transform,
    read_point_pairs,
    write_outputs,
)


class FitPlanarSimilarityTests(unittest.TestCase):
    def test_recovers_known_similarity_transform(self):
        theta = math.radians(31.5)
        scale = 1.00042
        a, b = scale * math.cos(theta), scale * math.sin(theta)
        tx, ty = 128.4, -52.7
        source = [(-12.0, 4.0), (6.0, 9.0), (13.0, -7.0), (-3.0, -11.0), (4.0, 2.0)]
        pairs = []
        for i, (x, y) in enumerate(source):
            target = (a*x - b*y + tx, b*x + a*y + ty)
            role = "fit" if i < 3 else "check"
            pairs.append(PointPair(str(i), role, x, y, *target))
        transform = fit_transform([p for p in pairs if p.role == "fit"], "similarity")
        self.assertAlmostEqual(transform.a, a, places=10)
        self.assertAlmostEqual(transform.b, b, places=10)
        self.assertAlmostEqual(transform.tx, tx, places=10)
        self.assertAlmostEqual(transform.ty, ty, places=10)
        check = calculate_metrics([p for p in pairs if p.role == "check"], transform)
        self.assertIsNotNone(check)
        self.assertLess(check.rmse_2d, 1e-9)

    def test_rigid_mode_keeps_unit_scale(self):
        source = [(-2.0, 1.0), (3.0, 2.0), (1.0, -4.0), (5.0, -1.0)]
        theta = math.radians(-18.0)
        tx, ty = 7.0, 12.0
        pairs = []
        for i, (x, y) in enumerate(source):
            X = math.cos(theta)*x - math.sin(theta)*y + tx
            Y = math.sin(theta)*x + math.cos(theta)*y + ty
            pairs.append(PointPair(str(i), "fit", x, y, X, Y))
        transform = fit_transform(pairs, "rigid")
        self.assertAlmostEqual(transform.scale, 1.0, places=12)
        self.assertAlmostEqual(transform.rotation_radians, theta, places=10)

    def test_rejects_collinear_fit_points(self):
        pairs = [
            PointPair("a", "fit", 0, 0, 10, 10),
            PointPair("b", "fit", 1, 1, 11, 11),
            PointPair("c", "fit", 2, 2, 12, 12),
        ]
        with self.assertRaises(TransformError):
            fit_transform(pairs)

    def test_reflection_is_not_silently_fitted(self):
        source = [(-2.0, 1.0), (3.0, 2.0), (1.0, -4.0), (5.0, -1.0)]
        pairs = [PointPair(str(i), "fit", x, y, -x, y) for i, (x, y) in enumerate(source)]
        transform = fit_transform(pairs, "similarity")
        metrics = calculate_metrics(pairs, transform)
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.rmse_2d, 0.1)

    def test_csv_pipeline_writes_transform_and_independent_residuals(self):
        theta = math.radians(12.0)
        a, b = math.cos(theta), math.sin(theta)
        tx, ty = 4.5, -8.0
        source = [(-3.0, -2.0), (5.0, -1.0), (1.0, 6.0), (-4.0, 5.0), (7.0, 4.0)]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            csv_path = root / "pairs.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["point_id", "role", "source_x", "source_y", "target_x", "target_y"])
                for i, (x, y) in enumerate(source):
                    X = a*x - b*y + tx
                    Y = b*x + a*y + ty
                    writer.writerow([f"P{i}", "fit" if i < 4 else "check", x, y, X, Y])
            pairs = read_point_pairs(csv_path)
            fit = [p for p in pairs if p.role == "fit"]
            transform = fit_transform(fit, "similarity")
            out_dir = root / "out"
            transform_path, residual_path = write_outputs(
                pairs, transform, out_dir, "local-test-grid", "target-test-grid",
                "metre", "metre", "x=east+, y=north+", csv_path
            )
            payload = json.loads(transform_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "CALCULATED_FROM_SUPPLIED_CONTROL_POINTS_NOT_FIELD_VALIDATED")
            self.assertEqual(len(payload["fit_point_ids"]), 4)
            self.assertEqual(len(payload["check_point_ids"]), 1)
            self.assertEqual(len(payload["input_sha256"]), 64)
            self.assertTrue(residual_path.exists())
            self.assertIsNotNone(payload["check_metrics"])


if __name__ == "__main__":
    unittest.main()
