"""Controls for the dependency-free derived-geometry kernel."""

from __future__ import annotations

import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import spatial_geometry as sg  # noqa: E402


class VectorTests(unittest.TestCase):
    def test_vector_operations(self):
        self.assertEqual(sg.vec_sub((3, 4, 5), (1, 2, 3)), (2, 2, 2))
        self.assertEqual(sg.vec_add((3, 4, 5), (1, 2, 3)), (4, 6, 8))
        self.assertEqual(sg.dot((1, 0, 0), (0, 1, 0)), 0.0)
        self.assertEqual(sg.cross((1, 0, 0), (0, 1, 0)), (0, 0, 1))
        self.assertAlmostEqual(sg.norm((3, 4, 0)), 5.0)
        self.assertAlmostEqual(sg.distance((0, 0, 0), (3, 4, 0)), 5.0)

    def test_angle_and_unit(self):
        self.assertAlmostEqual(sg.angle_degrees((1, 0, 0), (0, 1, 0)), 90.0)
        self.assertAlmostEqual(sg.angle_degrees((1, 0, 0), (1, 0, 0)), 0.0)
        u = sg.unit((0, 0, 7))
        self.assertAlmostEqual(u[2], 1.0)

    def test_non_finite_input_is_rejected(self):
        with self.assertRaises(sg.GeometryValidationError):
            sg.require_vector((1.0, float("nan"), 0.0))
        with self.assertRaises(sg.GeometryValidationError):
            sg.require_vector((1.0, 2.0))

    def test_zero_vector_normalization_is_rejected(self):
        with self.assertRaises(sg.GeometryValidationError):
            sg.unit((0, 0, 0))


class TransformTests(unittest.TestCase):
    def test_centering_keeps_original_values(self):
        original = [(1.0, 2.0, 3.0), (3.0, 4.0, 5.0)]
        centered = sg.center_points(original)
        self.assertEqual(original, [(1.0, 2.0, 3.0), (3.0, 4.0, 5.0)])
        self.assertEqual(centered["origin"], (2.0, 3.0, 4.0))
        self.assertEqual(centered["points"][0], (-1.0, -1.0, -1.0))

    def test_rotation_matrix_is_orthogonal(self):
        for axis in ("x", "y", "z"):
            matrix = sg.rotation_matrix(axis, 0.37)
            self.assertTrue(sg.is_orthogonal(matrix))
        self.assertTrue(sg.is_orthogonal(sg.scale_matrix(1.0, 1.0, 1.0)))
        self.assertFalse(sg.is_orthogonal(sg.scale_matrix(1.0, 1.0, 2.0)))

    def test_transform_returns_new_derived_point(self):
        source = (500365.8, 99909.36, 60.0)
        origin = (500365.8, 99909.36, 60.0)
        result = sg.apply_transform(source, sg.scale_matrix(2, 2, 2), origin)
        self.assertEqual(result["transformed_point"], source)
        self.assertEqual(result["geometry_status"], sg.DERIVED_GEOMETRY)
        self.assertTrue(result["source_values_unmodified"])
        self.assertEqual(source, (500365.8, 99909.36, 60.0))

    def test_matrix_operations(self):
        identity = sg.rotation_matrix("z", 0.0)
        self.assertEqual(sg.mat_vec(identity, (1, 2, 3)), (1, 2, 3))
        composed = sg.mat_mul(identity, identity)
        self.assertEqual(sg.mat_vec(composed, (1, 2, 3)), (1, 2, 3))


class FitAndModelTests(unittest.TestCase):
    def test_exact_plane_fit(self):
        points = [(x, y, 2 * x - y + 3) for x in range(-2, 3) for y in range(-2, 3)]
        plane = sg.fit_plane_least_squares(points)
        self.assertAlmostEqual(plane["coefficient_a"], 2.0, places=9)
        self.assertAlmostEqual(plane["coefficient_b"], -1.0, places=9)
        self.assertAlmostEqual(plane["intercept_c"], 3.0, places=9)
        self.assertAlmostEqual(plane["residual_summary"]["rms"], 0.0, places=9)
        self.assertEqual(plane["geometry_status"], sg.DERIVED_GEOMETRY)

    def test_imprecise_fit_reports_residual(self):
        points = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 10)]
        plane = sg.fit_plane_least_squares(points)
        self.assertGreater(plane["residual_summary"]["rms"], 0.0)

    def test_projection_uses_fitted_plane(self):
        plane = sg.fit_plane_least_squares([(0, 0, 1), (1, 0, 3), (0, 1, 5), (1, 1, 7)])
        projected = sg.project_to_plane((5, 6, 0), plane)
        self.assertAlmostEqual(projected[2], 1 + 2 * 5 + 4 * 6)

    def test_interpolation_reports_spread(self):
        points = [(0, 0, 0), (2, 0, 10), (0, 2, 20)]
        result = sg.inverse_distance_interpolation(points, (1, 1))
        self.assertEqual(result["geometry_status"], sg.DERIVED_GEOMETRY)
        self.assertGreaterEqual(result["local_spread"], 0.0)
        with self.assertRaises(sg.GeometryValidationError):
            sg.inverse_distance_interpolation(points, (0, 0))

    def test_model_record_requires_full_contract(self):
        record = sg.make_model_record(
            model_id="IDEAL-TEST-001",
            model_type="parametric_surface",
            source_ids=["GPMP:GP1"],
            input_geometry_ids=["GPMP-CONTROL-NETWORK"],
            method="least-squares plane",
            parameters={"a": 1.0},
            parameter_units={"a": "dimensionless"},
            assumptions=["planar approximation over local control"],
            fit_residual={"rms": 1.0},
            uncertainty={"rms": 1.0},
            validity_domain="local control network only",
            model_status=sg.IDEALIZED_MODEL,
            limitations=["not terrain", "not monument geometry"],
            falsification_conditions=["new control points outside residual bounds"],
        )
        self.assertTrue(sg.validate_model_record(record))
        self.assertNotEqual(record["model_status"], sg.MEASURED_GEOMETRY)

    def test_measured_geometry_cannot_be_filed_as_model(self):
        with self.assertRaises(sg.GeometryValidationError):
            sg.make_model_record(
                model_id="BAD", model_type="plane",
                source_ids=["S"], input_geometry_ids=["G"], method="m",
                parameters={}, parameter_units={}, assumptions=["a"],
                fit_residual={}, uncertainty={}, validity_domain="d",
                model_status=sg.MEASURED_GEOMETRY,
                limitations=["l"], falsification_conditions=["f"])

    def test_model_without_units_is_rejected(self):
        with self.assertRaises(sg.GeometryValidationError):
            sg.make_model_record(
                model_id="BAD2", model_type="plane",
                source_ids=["S"], input_geometry_ids=["G"], method="m",
                parameters={"a": 1.0}, parameter_units={}, assumptions=["a"],
                fit_residual={}, uncertainty={}, validity_domain="d",
                model_status=sg.IDEALIZED_MODEL,
                limitations=["l"], falsification_conditions=["f"])

    def test_incomplete_geometry_is_not_a_confident_surface(self):
        with self.assertRaises(sg.GeometryValidationError):
            sg.fit_plane_least_squares([(0, 0, 0), (1, 1, 1)])

    def test_singular_system_is_rejected(self):
        with self.assertRaises(sg.GeometryValidationError):
            sg.solve_linear_system(((1, 2), (2, 4)), (1, 2))


if __name__ == "__main__":
    unittest.main()
