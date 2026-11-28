"""Controls for GPMP source parsing: no invented values, no KML Z elevation."""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import gpmp_spatial_layer as gsl  # noqa: E402


def _temp_dir() -> str:
    preferred = r"F:\Pill\tmp\opencode"
    return preferred if os.path.isdir(preferred) else HERE


class GpmpParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = gsl.load_source()
        cls.snapshot = gsl.build_spatial_snapshot()

    def test_control_counts_and_unique_names(self):
        counts = self.snapshot["counts"]
        self.assertEqual(counts["total"], 41)
        self.assertEqual(counts["main_traverse"], 11)
        self.assertEqual(counts["secondary_network"], 30)
        names = [p["name"] for p in self.snapshot["points"]]
        self.assertEqual(len(names), len(set(names)))
        ids = [p["point_id"] for p in self.snapshot["points"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_control_ranges_match_declared_values(self):
        ranges = self.snapshot["control_ranges"]
        expected = {
            "northing": (98399.708, 100154.421),
            "easting": (498718.109, 500634.775),
            "elevation": (19.570, 197.555),
            "longitude": (31.1209192, 31.14077838),
            "latitude": (29.96474083, 29.98056996),
        }
        for key, (lo, hi) in expected.items():
            self.assertAlmostEqual(ranges[key]["min"], lo, places=3)
            self.assertAlmostEqual(ranges[key]["max"], hi, places=3)

    def test_elevation_comes_from_description_not_kml_z(self):
        for point in self.snapshot["points"]:
            desc_value = gsl.parse_elevation(point["description"])
            self.assertAlmostEqual(
                point["local_coordinates"]["elevation"], desc_value, places=6)
            self.assertEqual(point["longitude_latitude"]["kml_z"], 0.0)
            self.assertIs(point["longitude_latitude"]["kml_z_is_elevation"], False)

    def test_kml_z_zero_is_rejected_as_height(self):
        sample = self.payload["placemarks"][0]
        lon, lat, z = gsl.parse_longitude_latitude(sample)
        self.assertEqual(z, 0.0)
        elevation = gsl.parse_elevation(sample["description"])
        self.assertNotEqual(elevation, z)

    def test_elevation_missing_from_description_is_an_error(self):
        broken = self.payload["placemarks"][0]["description"].replace(
            "Elevation; 60.000", "Height 60.000")
        with self.assertRaises(gsl.SpatialValidationError):
            gsl.parse_elevation(broken)

    def test_raw_description_is_preserved_verbatim(self):
        for point, source in zip(self.snapshot["points"], self.payload["placemarks"]):
            self.assertEqual(point["description"], source["description"])

    def test_all_points_keep_easting_northing_and_lon_lat(self):
        for point in self.snapshot["points"]:
            local = point["local_coordinates"]
            self.assertIn("easting", local)
            self.assertIn("northing", local)
            self.assertIn("elevation", local)
            geo = point["longitude_latitude"]
            self.assertIn("longitude", geo)
            self.assertIn("latitude", geo)
            self.assertEqual(point["datum_status"], "unverified")

    def test_no_gpmp_object_records_or_relations_created(self):
        counts = self.snapshot["counts"]
        self.assertEqual(counts["real_objects"], 0)
        self.assertEqual(counts["relations"], 0)
        self.assertEqual(self.snapshot["separation"]["object_link"], "UNRESOLVED")
        self.assertTrue(self.snapshot["separation"][
            "control_points_are_not_archaeological_objects"])

    def test_no_terrain_mesh_or_fabricated_lines(self):
        rules = self.snapshot["render_rules"]
        self.assertIs(rules["terrain_mesh"], False)
        self.assertIs(rules["fabricated_lines"], False)
        self.assertEqual(rules["vertical_exaggeration_default"], 1.0)

    def test_provenance_states_are_not_merged(self):
        states = self.snapshot["provenance_states"]
        self.assertTrue(states["SOURCE_FILE_PRESENT"])
        self.assertTrue(states["SOURCE_CONTENT_PARSED"])
        self.assertTrue(states["STRUCTURE_VALIDATED"])
        self.assertFalse(states["SOURCE_PROVENANCE_VERIFIED"])
        self.assertFalse(states["INDEPENDENTLY_CORROBORATED"])

    def test_committed_json_sha_is_platform_independent(self):
        source = self.snapshot["source"]
        self.assertEqual(source["sha256_of_committed_json"],
                         gsl.canonical_json_sha256(self.payload))
        self.assertNotEqual(source["sha256_of_committed_json"],
                            source["sha256_of_kml"])
        self.assertIn("line endings", source["sha256_method"])

    def test_coordinate_system_is_not_guessed(self):
        system = self.snapshot["coordinate_system"]
        self.assertEqual(system["datum_status"], "unverified")
        self.assertEqual(system["conversion_to_epsg_wgs84"], "not_performed")
        self.assertEqual(system["helmert_spheroid_of_reference_transform"], "not_performed")

    def test_derived_plane_is_marked_derived_not_terrain(self):
        plane = self.snapshot["derived_geometry"]["least_squares_plane"]
        self.assertEqual(plane["geometry_status"], "DERIVED_GEOMETRY")
        self.assertTrue(self.snapshot["derived_geometry"]["not_terrain"])
        self.assertGreater(plane["residual_summary"]["rms"], 0.0)


class GpmpNegativeTests(unittest.TestCase):
    def _write(self, payload):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", dir=_temp_dir(), delete=False,
            encoding="utf-8")
        try:
            json.dump(payload, handle)
            handle.close()
            return handle.name
        except Exception:
            os.unlink(handle.name)
            raise

    def _cleanup(self, path):
        if os.path.isfile(path):
            os.unlink(path)

    def test_placemark_count_mismatch_is_detected(self):
        payload = copy.deepcopy(gsl.load_source())
        payload["placemark_count"] = 40
        path = self._write(payload)
        try:
            with self.assertRaises(gsl.SpatialValidationError):
                gsl.build_spatial_snapshot(path)
        finally:
            self._cleanup(path)

    def test_wrong_placemark_total_is_detected(self):
        payload = copy.deepcopy(gsl.load_source())
        payload["placemarks"] = payload["placemarks"][:-1]
        payload["placemark_count"] = 40
        path = self._write(payload)
        try:
            with self.assertRaises(gsl.SpatialValidationError):
                gsl.build_spatial_snapshot(path)
        finally:
            self._cleanup(path)

    def test_duplicate_id_is_detected(self):
        payload = copy.deepcopy(gsl.load_source())
        payload["placemarks"][1]["name"] = payload["placemarks"][0]["name"]
        path = self._write(payload)
        try:
            with self.assertRaises(gsl.SpatialValidationError):
                gsl.build_spatial_snapshot(path)
        finally:
            self._cleanup(path)

    def test_corrupted_coordinate_does_not_become_zero(self):
        payload = copy.deepcopy(gsl.load_source())
        desc = payload["placemarks"][0]["description"]
        payload["placemarks"][0]["description"] = desc.replace(
            "Northing: 99909.360", "Northing: NOT_A_NUMBER")
        path = self._write(payload)
        try:
            with self.assertRaises(gsl.SpatialValidationError):
                gsl.build_spatial_snapshot(path)
        finally:
            self._cleanup(path)

    def test_nonzero_kml_z_is_still_not_elevation(self):
        point = copy.deepcopy(gsl.load_source()["placemarks"][0])
        point["coordinates"][0][2] = 777.0
        lon, lat, z = gsl.parse_longitude_latitude(point)
        self.assertEqual(z, 777.0)
        self.assertNotEqual(z, gsl.parse_elevation(point["description"]))

    def test_unknown_network_label_is_rejected(self):
        with self.assertRaises(gsl.SpatialValidationError):
            gsl.classify_network("Point No. X Description: Unknown Northing: 1 Easting: 2")

    def test_line_ending_variants_give_identical_canonical_hash(self):
        payload = gsl.load_source()
        hashes = []
        for newline in ("\n", "\r\n"):
            handle = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", dir=_temp_dir(), delete=False,
                encoding="utf-8", newline=newline)
            try:
                json.dump(payload, handle)
                handle.close()
                hashes.append(gsl.build_spatial_snapshot(handle.name)[
                    "source"]["sha256_of_committed_json"])
            finally:
                if os.path.isfile(handle.name):
                    os.unlink(handle.name)
        self.assertEqual(hashes[0], hashes[1])

    def test_missing_source_file_is_an_error(self):
        with self.assertRaises(gsl.SpatialValidationError):
            gsl.load_source(os.path.join(_temp_dir(), "does_not_exist_gpmp.json"))


if __name__ == "__main__":
    unittest.main()
