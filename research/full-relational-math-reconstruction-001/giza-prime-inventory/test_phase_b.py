"""PHASE B controls: inventory, adapters, identity, CRS, relations, models.

These tests enforce the research boundary: 12,078 observations are preserved,
nothing is promoted to an object, no datum is verified, no surface is built.
"""

from __future__ import annotations

import copy
import json
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import phase_b_source_catalog as pbc  # noqa: E402
import phase_b_observations as pbo  # noqa: E402
import phase_b_coordinate_systems as pcrs  # noqa: E402
import phase_b_identity as pid  # noqa: E402
import phase_b_idealization as pidea  # noqa: E402
import phase_b_relations as prel  # noqa: E402
import spatial_geometry as sg  # noqa: E402


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = pbc.build_catalog()

    def test_expected_roots_exist(self):
        self.assertTrue(os.path.isdir(pbc.RAW_ROOT))
        self.assertTrue(os.path.isdir(pbc.DERIVED_ROOT))

    def test_expected_total_and_zero_delta(self):
        self.assertEqual(self.catalog["counts"]["observed_total"], 12078)
        self.assertEqual(self.catalog["counts"]["delta"], 0)
        self.assertEqual(self.catalog["counts"]["raw_files"], 15)
        self.assertEqual(self.catalog["counts"]["derived_files"], 8)

    def test_all_expected_sets_match_counts(self):
        for item in self.catalog["expected_set_status"].values():
            self.assertTrue(item["found"])
            self.assertTrue(item["parsed"])
            self.assertTrue(item["count_matches"])

    def test_identifiers_are_distinct(self):
        self.assertFalse(self.catalog["identifier_policy"]["interchangeable"])
        entry = next(e for e in self.catalog["derived_files"]
                     if e["name"] == "GPMP-Control-Monuments.json")
        self.assertNotEqual(entry["raw_sha256"], entry["git_blob_sha1"])
        self.assertEqual(len(entry["raw_sha256"]), 64)
        self.assertEqual(len(entry["git_blob_sha1"]), 40)
        self.assertEqual(len(entry["canonical_json_sha256"]), 64)

    def test_archive_reconciliation_all_match(self):
        for row in self.catalog["raw_archive_reconciliation"]:
            self.assertTrue(row["archive_match"], row["derived_json"])

    def test_provenance_not_overstated(self):
        states = self.catalog["provenance_states"]
        self.assertTrue(states["FILE_PRESENT"])
        self.assertFalse(states["SOURCE_PROVENANCE_VERIFIED"])
        self.assertFalse(states["INDEPENDENTLY_CORROBORATED"])


class ObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pbo.build_observations()
        cls.obs = cls.data["observations"]

    def test_all_observations_present(self):
        self.assertEqual(self.data["observation_count"], 12078)
        self.assertEqual(len(self.obs), 12078)
        self.assertEqual(
            len({o["observation_id"] for o in self.obs}), 12078)

    def test_campaign_counts(self):
        expected = {
            "GDFS-2012": 1539, "GDFS-2015": 1100, "GDFS-2016": 4746,
            "GDFS-2018": 4569, "GPMP": 41, "GIZA_CORNER": 15, "PETRIE": 68,
        }
        self.assertEqual(self.data["campaign_counts"], expected)

    def test_missing_elevation_is_null_not_zero(self):
        petrie = [o for o in self.obs if o["campaign_id"] == "PETRIE"]
        self.assertEqual(len(petrie), 68)
        for record in petrie:
            self.assertIsNone(record["normalized_coordinates"]["elevation"])
            self.assertEqual(record["vertical_reference_id"], "UNKNOWN")
            self.assertTrue(any(w.startswith("ELEVATION_ABSENT")
                                for w in record["warnings"]))

    def test_kml_z_never_promoted(self):
        for record in self.obs:
            self.assertIs(record["normalized_coordinates"]["kml_z_is_elevation"],
                          False)
        self.assertEqual(self.data["warning_counts"].get("KML_Z_NONZERO"), None)

    def test_swapped_labels_warned(self):
        self.assertEqual(
            self.data["warning_counts"]["SWAPPED_LONGITUDE_LABEL"], 9315)

    def test_original_records_preserved(self):
        for record in self.obs:
            self.assertIsInstance(record["original_description"], str)
            self.assertTrue(record["original_description"])
            self.assertIsInstance(record["original_coordinates"], list)

    def test_no_automatic_object_assignment(self):
        self.assertTrue(self.data["boundary_rules"]["observation_is_not_object"])
        for record in self.obs:
            self.assertNotIn(record["semantic_type"]["value"],
                             ("pyramid", "sphinx", "temple"))
        self.assertIsNone(next(o for o in self.obs
                               if o["campaign_id"] == "GPMP")["object_link"])

    def test_gdfs_adapters_capture_features_and_reshoots(self):
        g2018 = [o for o in self.obs if o["campaign_id"] == "GDFS-2018"]
        self.assertGreater(sum(1 for o in g2018
                               if o["derived_links"]["feature_id"]), 0)
        self.assertEqual(sum(1 for o in g2018
                             if o["derived_links"]["reshoot_total_station_range"]), 54)


class CRSTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pcrs.build_registry(pbo.build_observations()["observations"])

    def test_systems_are_separate(self):
        self.assertEqual(
            self.data["separation"]["gpmp_vs_arce_sphinx_grid"], "separate")
        self.assertEqual(
            self.data["separation"]["gpmp_to_arce_transform"], "not_performed")

    def test_no_transform_performed(self):
        self.assertEqual(self.data["transformations"]["performed"], [])
        for system in self.data["systems"].values():
            self.assertEqual(system["known_transformations"], [])
            self.assertEqual(system["datum"], "unverified")

    def test_datum_not_promoted(self):
        self.assertTrue(self.data["provenance_states"]["COORDINATE_SYSTEM_DOCUMENTED"])
        self.assertFalse(self.data["provenance_states"]["COORDINATE_SYSTEM_VERIFIED"])

    def test_anomalies_counted(self):
        self.assertEqual(self.data["observed_anomalies"]["elevation_absent_records"], 68)
        self.assertEqual(
            self.data["observed_anomalies"]["swapped_longitude_label_records"], 9315)


class IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pid.build_identity(pbo.build_observations()["observations"])

    def test_no_observation_lost(self):
        self.assertEqual(self.data["totals"]["source_observations"], 12078)
        self.assertEqual(self.data["totals"]["original_observations_removed"], 0)

    def test_no_identity_confirmed(self):
        self.assertEqual(self.data["totals"]["identity_confirmed"], 0)
        self.assertIsNone(self.data["totals"]["confirmed_unique_stations"])
        for group in self.data["entity_candidates"]:
            self.assertFalse(group["physical_identity_asserted"])

    def test_statuses_contract(self):
        expected = {"IDENTITY_CONFIRMED", "IDENTITY_PROBABLE", "MATCH_CANDIDATE",
                    "REMEASUREMENT_CANDIDATE", "UNRESOLVED", "DISTINCT"}
        self.assertEqual(set(self.data["statuses"]), expected)
        for group in self.data["entity_candidates"]:
            self.assertIn(group["status"], expected)

    def test_documented_reshoots_preserved(self):
        self.assertEqual(self.data["totals"]["documented_reshoot_notes"], 54)
        for note in self.data["documented_reshoots"]:
            self.assertEqual(note["status"], "REMEASUREMENT_CANDIDATE")

    def test_coordinate_match_is_candidate_only(self):
        coord_groups = [g for g in self.data["entity_candidates"]
                        if g["candidate_kind"] == "COORDINATE_COINCIDENCE"]
        self.assertTrue(coord_groups)
        for group in coord_groups:
            self.assertIn(group["status"],
                          ("MATCH_CANDIDATE", "REMEASUREMENT_CANDIDATE"))


class RelationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = prel.build_relations(pbo.build_observations()["observations"])

    def test_contract_on_every_relation(self):
        for relation in self.data["relations"]:
            for key in ("formula", "units", "dimensions", "residual",
                        "sensitivity", "alternative_explanation",
                        "independent_check", "falsification_condition"):
                self.assertIn(key, relation)
            self.assertFalse(relation["physical_mechanism_claimed"])

    def test_no_cross_campaign_euclidean_relation(self):
        self.assertEqual(self.data["cross_campaign_geometric_relations"], 0)

    def test_no_physical_claims(self):
        for key, value in self.data["physical_hypotheses"].items():
            if key == "reason":
                continue
            self.assertIsNone(value)

    def test_categories_valid(self):
        for relation in self.data["relations"]:
            self.assertIn(relation["relation_category"],
                          self.data["category_contract"])


class IdealizationTests(unittest.TestCase):
    def test_gpmp_model_contract(self):
        obs = pbo.build_observations()["observations"]
        gpmp = [o for o in obs if o["campaign_id"] == "GPMP"]
        registry = pidea.idealize_campaign("GPMP", gpmp)
        self.assertEqual(len(registry["models"]), 4)
        for model in registry["models"]:
            self.assertTrue(sg.validate_model_record(model))
            self.assertEqual(model["model_status"], sg.IDEALIZED_MODEL)
            self.assertTrue(model["not_terrain"])
            self.assertTrue(model["not_monument_geometry"])
            self.assertTrue(model["source_values_unmodified"])
            self.assertEqual(set(model["parameters"]), set(model["parameter_units"]))

    def test_petrie_withheld(self):
        obs = [o for o in pbo.build_observations()["observations"]
               if o["campaign_id"] == "PETRIE"]
        with self.assertRaises(pidea.IdealizationError):
            pidea.idealize_campaign("PETRIE", obs)

    def test_no_surface_generated(self):
        obs = pbo.build_observations()["observations"]
        registry = pidea.build_model_registry(obs)
        self.assertIsNone(registry["surfaces"]["terrain_mesh"])
        self.assertIsNone(registry["surfaces"]["monument_surface"])
        self.assertEqual(registry["surfaces"]["status"], sg.UNKNOWN)

    def test_source_coordinates_unmodified(self):
        obs = pbo.build_observations()["observations"]
        before = copy.deepcopy(obs)
        pidea.build_model_registry(obs)
        self.assertEqual(obs, before)


class DeterminismTests(unittest.TestCase):
    def test_observations_deterministic(self):
        a = pbo.build_observations()
        b = pbo.build_observations()
        self.assertEqual(json.dumps(a, sort_keys=True),
                         json.dumps(b, sort_keys=True))

    def test_catalog_hashes_stable(self):
        a = pbc.build_catalog()
        b = pbc.build_catalog()
        for left, right in zip(a["derived_files"], b["derived_files"]):
            self.assertEqual(left["raw_sha256"], right["raw_sha256"])
            self.assertEqual(left["canonical_json_sha256"],
                             right["canonical_json_sha256"])


if __name__ == "__main__":
    unittest.main()
