"""Controls for idealized geometry of the GPMP control network.

These tests enforce the boundary the research contract requires: the network
may be idealized (centre, axes, envelope, spacing, residuals), but the sample
may not be turned into terrain, monument geometry or measured connections.
"""

from __future__ import annotations

import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import gpmp_spatial_layer as gsl  # noqa: E402
import network_idealization as ni  # noqa: E402
import spatial_geometry as sg  # noqa: E402


class SyntheticNetworkTests(unittest.TestCase):
    def test_centroid_and_covariance_are_explicit(self):
        points = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0),
                  (0.0, 4.0, 0.0), (2.0, 4.0, 0.0)]
        self.assertEqual(ni.centroid(points), (1.0, 2.0, 0.0))
        cov = ni.covariance_matrix(points)
        self.assertAlmostEqual(cov[0][0], 1.0)
        self.assertAlmostEqual(cov[1][1], 4.0)
        self.assertAlmostEqual(cov[0][1], 0.0)

    def test_principal_axes_recover_a_known_frame(self):
        points = []
        for i in range(-5, 6):
            points.append((10.0 * i,
                           0.5 * i + 1.7 * ((i * i) % 4),
                           0.1 * i + 0.9 * ((i + 5) % 3)))
        frame = ni.principal_axes(points)
        first = frame["axes"][0]["vector"]
        self.assertGreater(abs(first[0]), 0.99)
        self.assertTrue(frame["orthonormal_basis"])
        self.assertFalse(frame["degenerate"])
        self.assertAlmostEqual(
            sum(a["explained_variance_ratio"] for a in frame["axes"]), 1.0, places=9)
        self.assertGreater(frame["anisotropy_ratio"], 1.0)

    def test_degenerate_sample_is_reported_not_idealized(self):
        frame = ni.principal_axes([(1.0, 2.0, 3.0)] * 4)
        self.assertTrue(frame["degenerate"])
        self.assertIsNone(frame["anisotropy_ratio"])
        with self.assertRaises(ni.IdealizationValidationError):
            ni.build_network_idealization(
                [(1.0, 2.0, 3.0)] * 4, ["A", "B", "C", "D"])

    def test_plan_hull_of_a_square_with_interior_point(self):
        points = [(0.0, 0.0, 1.0), (4.0, 0.0, 2.0), (4.0, 4.0, 3.0),
                  (0.0, 4.0, 4.0), (2.0, 2.0, 99.0)]
        hull = ni.plan_convex_hull(points)
        self.assertEqual(hull["vertex_count"], 4)
        self.assertAlmostEqual(hull["area"], 16.0)
        self.assertAlmostEqual(hull["perimeter"], 16.0)
        self.assertEqual(hull["vertex_elevation_min"], 1.0)
        self.assertEqual(hull["vertex_elevation_max"], 4.0)
        self.assertNotIn([2.0, 2.0, 99.0], hull["vertices"])

    def test_spacing_statistics_are_not_density_of_objects(self):
        points = [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                  (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.5, 0.5, 0.0),
                  (0.25, 0.75, 0.0)]
        stats = ni.spacing_statistics(points)
        self.assertEqual(stats["pairwise_distance"]["count"], 15)
        self.assertEqual(stats["nearest_neighbor_distance"]["count"], 6)
        self.assertLessEqual(stats["nearest_neighbor_distance"]["max"], 1.0)
        self.assertGreater(stats["nearest_neighbor_distance"]["max"], 0.0)
        self.assertIn("NOT", stats["interpretation"])

    def test_ellipsoid_reports_outside_points_as_residuals(self):
        frame = ni.principal_axes([(-3.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
                                   (1.0, 0.0, 0.0), (3.0, 0.0, 0.0),
                                   (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)])
        points = [
            (-3.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (1.0, 0.0, 0.0),
            (3.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)]
        env = ni.ellipsoidal_envelope(points, frame)
        self.assertEqual(env["scale"], ni.ELLIPSOID_SCALE)
        self.assertEqual(len(env["outside_point_indices"]), env["points_outside"])
        self.assertGreaterEqual(env["outside_positive_residual"]["min"], 0.0)
        self.assertTrue(env["interpretation"].endswith("confidence region"))

    def test_distance_summary_rejects_negative_or_nonfinite_values(self):
        with self.assertRaises(ni.IdealizationValidationError):
            ni.distance_summary([1.0, -2.0])
        with self.assertRaises(ni.IdealizationValidationError):
            ni.distance_summary([float("nan")])

    def test_source_id_mismatch_is_rejected(self):
        points = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                  (1.0, 1.0, 0.0), (2.0, 0.5, 0.0)]
        with self.assertRaises(ni.IdealizationValidationError):
            ni.build_network_idealization(points, ["A"])


class RealNetworkIdealizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = gsl.build_spatial_snapshot()
        cls.ideal = cls.snapshot["network_idealization"]
        cls.source_points = [
            (p["local_coordinates"]["easting"],
             p["local_coordinates"]["northing"],
             p["local_coordinates"]["elevation"])
            for p in cls.snapshot["points"]]

    def test_scope_is_control_network_only(self):
        self.assertEqual(self.ideal["scope"], "GPMP_CONTROL_NETWORK_ONLY")
        self.assertEqual(self.ideal["status"], sg.IDEALIZED_MODEL)
        self.assertIs(self.ideal["not_terrain"], True)
        self.assertIs(self.ideal["not_monument_geometry"], True)
        self.assertIs(self.ideal["source_values_unmodified"], True)
        self.assertEqual(self.ideal["point_count"], 41)

    def test_four_complete_model_records(self):
        models = self.ideal["models"]
        self.assertEqual(len(models), 4)
        self.assertEqual(len(self.ideal["model_ids"]), len(set(self.ideal["model_ids"])))
        for record in models:
            self.assertTrue(sg.validate_model_record(record))
            self.assertEqual(record["model_status"], sg.IDEALIZED_MODEL)
            self.assertEqual(set(record["parameters"]), set(record["parameter_units"]))
            self.assertEqual(len(record["source_ids"]), 41)
            self.assertTrue(record["assumptions"])
            self.assertTrue(record["limitations"])
            self.assertTrue(record["falsification_conditions"])
            self.assertTrue(record["validity_domain"])

    def test_expected_model_types_are_present(self):
        types = {record["model_type"] for record in self.ideal["models"]}
        self.assertEqual(types, {
            "principal_axis_network_frame",
            "plan_view_convex_envelope",
            "two_sigma_ellipsoidal_envelope",
            "sampling_spacing_distribution",
        })

    def test_real_metrics_are_derived_from_the_41_points(self):
        geometry = self.ideal["geometry"]
        frame = geometry["principal_axes"]
        self.assertGreater(frame["anisotropy_ratio"], 1.0)
        self.assertTrue(frame["orthonormal_basis"])
        self.assertTrue(math.isfinite(frame["anisotropy_ratio"]))
        hull = geometry["plan_convex_hull"]
        self.assertEqual(hull["vertex_count"], len(hull["vertices"]))
        self.assertGreater(hull["area"], 0.0)
        self.assertGreater(hull["perimeter"], 0.0)
        for vertex in hull["vertices"]:
            self.assertIn(tuple(vertex), self.source_points)
        spacing = geometry["spacing"]
        self.assertEqual(spacing["pairwise_distance"]["count"], 41 * 40 // 2)
        self.assertEqual(spacing["nearest_neighbor_distance"]["count"], 41)
        envelope = geometry["ellipsoidal_envelope"]
        self.assertEqual(len(envelope["outside_point_indices"]),
                         envelope["points_outside"])
        self.assertEqual(envelope["points_outside"], 7)

    def test_build_does_not_modify_source_coordinates(self):
        original = [tuple(p) for p in self.source_points]
        ni.build_network_idealization(self.source_points,
                                      [p["point_id"] for p in self.snapshot["points"]])
        self.assertEqual(self.source_points, original)

    def test_snapshot_exposes_models_without_terrain_claim(self):
        contract = self.snapshot["model_contract"]
        self.assertEqual(contract["instantiated_models_in_this_commit"], 4)
        self.assertEqual(contract["instantiated_model_ids"], self.ideal["model_ids"])
        self.assertEqual(contract["idealized_surface_models"], 0)
        self.assertIn("control_network_only", contract["model_scope"])
        rules = self.snapshot["render_rules"]
        self.assertIs(rules["terrain_mesh"], False)
        self.assertIs(rules["idealized_model_overlays"], True)
        self.assertIs(rules["idealized_overlays_are_not_measurements"], True)


if __name__ == "__main__":
    unittest.main()
