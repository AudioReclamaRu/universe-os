"""PHASE B portable CI contour — reproducible without personal source trees.

Two contours are deliberately separate:

* ``test_phase_b_portable.py`` (this module) always runs.  It exercises every
  adapter, the geometry kernel, CRS, identity, relations, idealization and data
  error handling with tiny deterministic fixtures, then checks the already
  published canonical Phase B registries and their evidential constraints.
* ``test_phase_b.py`` rebuilds from the two nominated source directories.  Its
  source-dependent classes report ``SKIPPED — SOURCE DATA NOT MOUNTED`` when
  those directories are absent, and fail hard when
  ``GIZA_PRIME_REQUIRE_FULL_SOURCE=1`` is set.

No test here reads ``E:\\...`` or any other machine-specific path.  Source
roots, when used at all, come from ``phase_b_source_catalog.source_roots()``.
"""

from __future__ import annotations

import copy
import json
import math
import os
import sys
import unittest
from typing import Any, Dict, List

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

PLACEHOLDER_SHA = "0" * 64
EXPECTED_CAMPAIGN_COUNTS = {
    "GDFS-2012": 1539, "GDFS-2015": 1100, "GDFS-2016": 4746,
    "GDFS-2018": 4569, "GPMP": 41, "GIZA_CORNER": 15, "PETRIE": 68,
}
RELATION_CONTRACT_KEYS = (
    "formula", "units", "dimensions", "residual", "sensitivity",
    "alternative_explanation", "independent_check", "falsification_condition",
)


def _load(name: str) -> Dict[str, Any]:
    with open(os.path.join(HERE, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _placemark(name: str, description: str, lon: float, lat: float,
               z: float = 0.0) -> Dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "geometry": "Point",
        "coordinates": [[lon, lat, z]],
        "extended": {},
        "folder": "PORTABLE_CI_FIXTURE",
        "crs_hints": ["Easting", "Northing"],
    }


def _fixture(source_file: str, index: int = 0) -> Dict[str, Any]:
    """Build one valid placemark per campaign without touching source files."""
    campaign = pbo.CAMPAIGNS[source_file]
    cid = campaign["campaign_id"]
    easting = 2000.0 + index * 10.0
    northing = 1000.0 + index * 7.0 + (index % 3) * 11.0
    elevation = 10.0 + (index % 4) * 1.5
    lon = 31.10 + index * 0.001
    lat = 29.90 + index * 0.001
    if cid == "PETRIE":
        description = (
            "Place: Portable fixture %d Petrie N-S: %d Petrie E-W: %d "
            "GPMP Northing: %.3f GPMP Easting: %.3f "
            "Longitude: %.6f Latitude: %.6f" % (
                index, 400000 + index, 900000 + index,
                northing, easting, lon, lat))
    elif cid in ("GDFS-2016", "GDFS-2018"):
        description = (
            "Point No. %d Description: Portable feature fixture "
            "Northing: %.3f Easting: %.3f Elevation; %.3f "
            "LongItude: %.6f Latitude: %.6f Feature: %d%s" % (
                index, northing, easting, elevation, lat, lon,
                50000 + index,
                " reshoot it with TS # 100 - 110" if cid == "GDFS-2018" else ""))
    elif cid == "GPMP":
        description = (
            "Point No. GEF%d Description: Secondary Network "
            "Northing: %.3f Easting: %.3f Elevation; %.3f "
            "Longitude: %.6f Latitude: %.6f" % (
                index, northing, easting, elevation, lon, lat))
    elif cid == "GIZA_CORNER":
        description = (
            "Description: Casing Corner Northing: %.3f Easting: %.3f "
            "Elevation; %.3f Longitude: %.6f Latitude: %.6f" % (
                northing, easting, elevation, lon, lat))
    else:
        description = (
            "Point No. %d Description: Portable survey fixture "
            "Northing: %.3f Easting: %.3f Elevation; %.3f "
            "Longitude: %.6f Latitude: %.6f" % (
                index, northing, easting, elevation, lon, lat))
    return pbo.adapt(
        source_file,
        _placemark("FIXTURE-%s-%d" % (cid, index), description, lon, lat),
        index,
        PLACEHOLDER_SHA,
    )


class PublishedRegistryTests(unittest.TestCase):
    """Check the committed registries themselves, not the owner's disk."""

    @classmethod
    def setUpClass(cls):
        cls.observations = _load("phase_b_observations.json")
        cls.catalog = _load("phase_b_source_catalog.json")
        cls.crs = _load("phase_b_coordinate_system_registry.json")
        cls.identity = _load("phase_b_entity_candidate_registry.json")
        cls.relations = _load("phase_b_relation_candidates.json")
        cls.models = _load("phase_b_model_registry.json")
        cls.validation = _load("phase_b_validation_report.json")
        cls.import_report = _load("phase_b_import_report.json")
        cls.epistemic = _load("phase_b_epistemic_report.json")
        cls.obs = cls.observations["observations"]

    def test_published_observation_envelope(self):
        self.assertEqual(self.observations["observation_count"], 12078)
        self.assertEqual(len(self.obs), 12078)
        self.assertEqual(len({o["observation_id"] for o in self.obs}), 12078)
        self.assertEqual(self.observations["campaign_counts"],
                         EXPECTED_CAMPAIGN_COUNTS)
        self.assertEqual(self.observations["boundary_rules"], {
            "observation_is_not_object": True,
            "control_point_is_not_archaeological_object": True,
            "survey_marker_is_not_terrain_sample": True,
            "coordinate_is_not_physical_relation": True,
            "proximity_is_not_functional_coupling": True,
            "kml_z_is_elevation": False,
            "unknown_replaced_by_zero": False,
        })
        for record in self.obs:
            self.assertIn(record["source_file_id"], pbo.CAMPAIGNS)
            self.assertTrue(record["original_description"])
            coords = record["normalized_coordinates"]
            self.assertTrue(math.isfinite(coords["local_easting"]))
            self.assertTrue(math.isfinite(coords["local_northing"]))
            self.assertFalse(coords["kml_z_is_elevation"])

    def test_warnings_and_missing_values_are_preserved(self):
        self.assertEqual(self.observations["warning_counts"], {
            "ELEVATION_ABSENT": 68, "SWAPPED_LONGITUDE_LABEL": 9315})
        petrie = [o for o in self.obs if o["campaign_id"] == "PETRIE"]
        self.assertEqual(len(petrie), 68)
        for record in petrie:
            self.assertIsNone(record["normalized_coordinates"]["elevation"])
            self.assertEqual(record["vertical_reference_id"], "UNKNOWN")
            self.assertTrue(any(w.startswith("ELEVATION_ABSENT")
                                for w in record["warnings"]))
        self.assertFalse(any(o["normalized_coordinates"]["kml_z"] != 0.0
                             for o in self.obs))

    def test_no_object_or_mechanism_promoted(self):
        for record in self.obs:
            self.assertNotIn(record["semantic_type"]["value"],
                             ("pyramid", "sphinx", "temple"))
        gpmp = next(o for o in self.obs if o["campaign_id"] == "GPMP")
        self.assertIsNone(gpmp["object_link"])

    def test_catalog_inventory_contract(self):
        counts = self.catalog["counts"]
        self.assertEqual(counts["raw_files"], 15)
        self.assertEqual(counts["derived_files"], 8)
        self.assertEqual(counts["observed_total"], 12078)
        self.assertEqual(counts["delta"], 0)
        self.assertFalse(self.catalog["identifier_policy"]["interchangeable"])
        for status in self.catalog["expected_set_status"].values():
            self.assertTrue(status["found"])
            self.assertTrue(status["parsed"])
            self.assertTrue(status["count_matches"])
        self.assertTrue(all(r["archive_match"]
                            for r in self.catalog["raw_archive_reconciliation"]))
        provenance = self.catalog["provenance_states"]
        self.assertFalse(provenance["SOURCE_PROVENANCE_VERIFIED"])
        self.assertFalse(provenance["INDEPENDENTLY_CORROBORATED"])
        canonical_hashes = 0
        for entry in self.catalog["derived_files"]:
            self.assertEqual(len(entry["raw_sha256"]), 64)
            self.assertEqual(len(entry["git_blob_sha1"]), 40)
            value = entry["canonical_json_sha256"]
            if value is not None:
                self.assertEqual(len(value), 64)
                canonical_hashes += 1
        self.assertEqual(canonical_hashes, 7)

    def test_crs_registry_contract(self):
        self.assertEqual(len(self.crs["systems"]), 5)
        self.assertEqual(self.crs["transformations"]["performed"], [])
        self.assertEqual(self.crs["separation"]["gpmp_vs_arce_sphinx_grid"],
                         "separate")
        self.assertEqual(self.crs["separation"]["gpmp_to_arce_transform"],
                         "not_performed")
        for system in self.crs["systems"].values():
            self.assertEqual(system["datum"], "unverified")
            self.assertEqual(system["known_transformations"], [])
        self.assertEqual(self.crs["observed_anomalies"], {
            "elevation_absent_records": 68,
            "kml_z_nonzero_records": 0,
            "swapped_longitude_label_records": 9315})
        self.assertFalse(self.crs["provenance_states"][
            "COORDINATE_SYSTEM_VERIFIED"])

    def test_identity_registry_contract(self):
        totals = self.identity["totals"]
        self.assertEqual(totals["source_observations"], 12078)
        self.assertEqual(totals["original_observations_removed"], 0)
        self.assertEqual(totals["identity_confirmed"], 0)
        self.assertEqual(totals["entity_candidates"], 345)
        self.assertEqual(totals["remeasurement_candidates"], 5)
        self.assertEqual(totals["documented_reshoot_notes"], 54)
        self.assertIsNone(totals["confirmed_unique_stations"])
        for group in self.identity["entity_candidates"]:
            self.assertFalse(group["physical_identity_asserted"])
            self.assertTrue(group["original_records_preserved"])

    def test_relation_registry_contract(self):
        self.assertEqual(self.relations["relation_count"], 154)
        self.assertEqual(len(self.relations["relations"]), 154)
        self.assertEqual(self.relations["cross_campaign_geometric_relations"], 0)
        for relation in self.relations["relations"]:
            for key in RELATION_CONTRACT_KEYS:
                self.assertIn(key, relation)
            self.assertFalse(relation["physical_mechanism_claimed"])
            self.assertIn(relation["relation_category"],
                          self.relations["category_contract"])
        for key, value in self.relations["physical_hypotheses"].items():
            if key == "reason":
                continue
            self.assertIsNone(value)

    def test_model_registry_contract(self):
        models = self.models
        self.assertEqual(models["model_count"], 24)
        self.assertEqual(len(models["models"]), 24)
        self.assertEqual(models["hypothetical_models"], [])
        self.assertEqual(models["model_statuses"], list(sg.MODEL_STATUSES))
        self.assertEqual(models["skipped_campaigns"][0]["campaign_id"], "PETRIE")
        self.assertEqual(models["skipped_campaigns"][0]["status"], sg.UNKNOWN)
        for model in models["models"]:
            self.assertTrue(sg.validate_model_record(model))
            self.assertEqual(model["model_status"], sg.IDEALIZED_MODEL)
            self.assertTrue(model["not_terrain"])
            self.assertTrue(model["not_monument_geometry"])
        self.assertIsNone(models["surfaces"]["terrain_mesh"])
        self.assertIsNone(models["surfaces"]["monument_surface"])
        self.assertEqual(models["surfaces"]["status"], sg.UNKNOWN)
        ellipsoid = [m for m in models["models"]
                     if m["model_type"] == "descriptive_ellipsoidal_envelope"]
        self.assertTrue(ellipsoid)
        self.assertTrue(all(m["parameters"]["scale"] == 2.0
                            for m in ellipsoid))

    def test_validation_import_and_epistemic_reports(self):
        self.assertEqual(self.validation["checks"], {
            "expected_total_matches": True,
            "all_expected_sets_parsed": True,
            "observation_ids_unique": True,
            "no_kml_z_promoted": True,
            "all_observations_preserved": True,
            "no_terrain_mesh": True,
            "no_monument_surface": True,
            "cross_campaign_transform_performed": False,
        })
        states = self.epistemic["states"]
        for key in ("SOURCE_PROVENANCE_VERIFIED", "COORDINATE_SYSTEM_VERIFIED",
                    "INDEPENDENTLY_CORROBORATED", "MODEL_VALIDATED"):
            self.assertFalse(states[key])
        self.assertEqual(self.import_report["observation_count"], 12078)
        self.assertEqual(self.import_report["relation_count"], 154)
        self.assertEqual(self.import_report["idealization_model_count"], 24)
        self.assertEqual(self.import_report["entity_candidate_count"], 345)
        self.assertFalse(self.import_report["import_contract"]["sources_copied"])
        self.assertEqual(
            self.import_report["import_contract"]["source_bytes_modified"], 0)


class PortableAdapterTests(unittest.TestCase):
    """All seven adapters and their data-error paths, from tiny fixtures."""

    def test_all_seven_adapters_produce_valid_records(self):
        self.assertEqual(len(pbo.CAMPAIGNS), 7)
        for source_file in sorted(pbo.CAMPAIGNS):
            record = _fixture(source_file, 0)
            self.assertEqual(record["source_file_id"], source_file)
            self.assertEqual(record["campaign_id"],
                             pbo.CAMPAIGNS[source_file]["campaign_id"])
            self.assertEqual(
                record["source_provenance"]["source_sha256"], PLACEHOLDER_SHA)
            self.assertEqual(record["validation_status"], sg.MEASURED_GEOMETRY)
            coords = record["normalized_coordinates"]
            self.assertTrue(math.isfinite(coords["local_easting"]))
            self.assertTrue(math.isfinite(coords["local_northing"]))
            self.assertEqual(coords["kml_z"], 0.0)

    def test_campaign_specific_adapter_contracts(self):
        gpmp = _fixture("GPMP-Control-Monuments.json", 0)
        self.assertEqual(gpmp["semantic_type"]["value"],
                         "secondary_network_control")
        self.assertEqual(gpmp["identity_status"], "OBSERVED_CONTROL_POINT")
        corner = _fixture("Giza-Corner-Points-2v17.json", 0)
        self.assertEqual(corner["semantic_type"]["value"],
                         "building_corner_candidate")
        petrie = _fixture("Petries-Stations.json", 0)
        self.assertEqual(petrie["coordinate_system_id"],
                         "PETRIE_LOCAL_GRID_UNRESOLVED")
        self.assertIsNone(petrie["normalized_coordinates"]["elevation"])
        for source_file in ("GDFS-2016-23ix18.json", "GDFS-2018-12xii18.json"):
            record = _fixture(source_file, 1)
            self.assertEqual(record["derived_links"]["feature_id"], "50001")
            self.assertTrue(record["semantic_type"]["alternatives"])
        reshoot = _fixture("GDFS-2018-12xii18.json", 0)
        self.assertEqual(
            reshoot["derived_links"]["reshoot_total_station_range"], "100 - 110")

    def test_swapped_longitude_label_and_kml_z_are_reported(self):
        swapped = _fixture("GDFS-2016-23ix18.json", 0)
        self.assertTrue(any(w.startswith("SWAPPED_LONGITUDE_LABEL")
                            for w in swapped["warnings"]))
        self.assertFalse(swapped["normalized_coordinates"]["kml_z_is_elevation"])
        base = _fixture("GDFS-2012-for-GE-21vii18.json", 0)
        nonzero = _placemark("FIXTURE-NONZERO-Z", base["original_description"],
                             31.1, 29.9, 12.0)
        adapted = pbo.adapt("GDFS-2012-for-GE-21vii18.json", nonzero, 0,
                            PLACEHOLDER_SHA)
        self.assertTrue(any(w.startswith("KML_Z_NONZERO")
                            for w in adapted["warnings"]))
        self.assertFalse(adapted["normalized_coordinates"]["kml_z_is_elevation"])

    def test_bad_source_records_are_errors_not_zeroes(self):
        source = "GDFS-2012-for-GE-21vii18.json"
        good = _placemark("X", "Northing: 1.0 Easting: 2.0", 31.1, 29.9)
        no_description = dict(good, description="")
        no_northing = dict(good, description="Easting: 2.0")
        non_finite = dict(good, description=(
            "Northing: %s Easting: 2.0" % ("9" * 400)))
        bad_coords = dict(good, coordinates=[[float("nan"), 29.9, 0.0]])
        for placemark in (no_description, no_northing, non_finite, bad_coords):
            with self.assertRaises(pbo.ObservationError):
                pbo.adapt(source, placemark, 0, PLACEHOLDER_SHA)
        with self.assertRaises(pbo.ObservationError):
            pbo.adapt("NOT-A-CAMPAIGN.json", good, 0, PLACEHOLDER_SHA)


class PortableAlgorithmTests(unittest.TestCase):
    """Geometry, CRS, identity, relations and idealization on tiny fixtures."""

    @classmethod
    def setUpClass(cls):
        cls.gpmp = [_fixture("GPMP-Control-Monuments.json", i)
                    for i in range(8)]
        # Three self-contained grids with enough points for spacing statistics,
        # plus one Petrie station that must be withheld from idealization.
        cls.mixed = [
            _fixture("GPMP-Control-Monuments.json", i) for i in range(8)
        ] + [
            _fixture("GDFS-2012-for-GE-21vii18.json", i) for i in range(8)
        ] + [
            _fixture("GDFS-2016-23ix18.json", i) for i in range(8)
        ] + [
            _fixture("Petries-Stations.json", 0),
        ]

    def test_geometry_kernel_primitives(self):
        self.assertAlmostEqual(sg.distance((0, 0, 0), (3, 4, 0)), 5.0)
        self.assertAlmostEqual(sg.angle_degrees((1, 0, 0), (0, 1, 0)), 90.0)
        centered = sg.center_points([(0, 0, 0), (2, 0, 0)])
        self.assertEqual(centered["origin"], (1.0, 0.0, 0.0))
        with self.assertRaises(sg.GeometryValidationError):
            sg.require_vector((1.0, float("nan"), 2.0))

    def test_model_record_contract(self):
        model = sg.make_model_record(
            "PORTABLE-001", "sampling_spacing_distribution", ["A"], ["A"],
            "fixture", {"count": 1}, {"count": "count"}, ["fixture"],
            {"min": 0.0, "max": 1.0}, {"sigma": None}, "fixture",
            sg.IDEALIZED_MODEL, ["not a monument"], ["falsifier"])
        self.assertTrue(sg.validate_model_record(model))
        self.assertEqual(model["model_status"], sg.IDEALIZED_MODEL)
        broken = dict(model)
        broken.pop("falsification_conditions")
        with self.assertRaises(sg.GeometryValidationError):
            sg.validate_model_record(broken)

    def test_crs_from_fixtures(self):
        registry = pcrs.build_registry(self.mixed)
        self.assertEqual(len(registry["systems"]), 5)
        self.assertEqual(registry["transformations"]["performed"], [])
        self.assertEqual(registry["observed_anomalies"]["elevation_absent_records"], 1)
        self.assertEqual(
            registry["observed_anomalies"]["swapped_longitude_label_records"], 8)
        self.assertFalse(registry["provenance_states"][
            "COORDINATE_SYSTEM_VERIFIED"])

    def test_identity_from_fixtures(self):
        identity = pid.build_identity(self.mixed, expected_total=len(self.mixed))
        self.assertEqual(identity["totals"]["source_observations"],
                         len(self.mixed))
        self.assertEqual(identity["totals"]["original_observations_removed"], 0)
        self.assertEqual(identity["totals"]["identity_confirmed"], 0)
        for group in identity["entity_candidates"]:
            self.assertFalse(group["physical_identity_asserted"])

    def test_relations_from_fixtures(self):
        relations = prel.build_relations(self.mixed)
        self.assertEqual(relations["cross_campaign_geometric_relations"], 0)
        for relation in relations["relations"]:
            for key in RELATION_CONTRACT_KEYS:
                self.assertIn(key, relation)
            self.assertFalse(relation["physical_mechanism_claimed"])

    def test_idealization_from_fixtures(self):
        registry = pidea.idealize_campaign("GPMP", self.gpmp)
        self.assertEqual(len(registry["models"]), 4)
        for model in registry["models"]:
            self.assertTrue(sg.validate_model_record(model))
            self.assertEqual(model["model_status"], sg.IDEALIZED_MODEL)
            self.assertTrue(model["not_terrain"])
            self.assertEqual(set(model["parameters"]),
                             set(model["parameter_units"]))
        with self.assertRaises(pidea.IdealizationError):
            pidea.idealize_campaign("PETRIE", [
                _fixture("Petries-Stations.json", 0)])

    def test_model_registry_never_builds_surfaces(self):
        registry = pidea.build_model_registry(self.mixed)
        self.assertIsNone(registry["surfaces"]["terrain_mesh"])
        self.assertIsNone(registry["surfaces"]["monument_surface"])
        self.assertEqual(registry["skipped_campaigns"][0]["campaign_id"],
                         "PETRIE")
        before = copy.deepcopy(self.mixed)
        pidea.build_model_registry(self.mixed)
        self.assertEqual(self.mixed, before)

    def test_algorithms_are_deterministic(self):
        def canonical(value: Any) -> str:
            return json.dumps(value, sort_keys=True, ensure_ascii=False,
                              allow_nan=False)
        self.assertEqual(canonical(pcrs.build_registry(self.mixed)),
                         canonical(pcrs.build_registry(self.mixed)))
        self.assertEqual(
            canonical(pid.build_identity(self.mixed,
                                         expected_total=len(self.mixed))),
            canonical(pid.build_identity(self.mixed,
                                         expected_total=len(self.mixed))))
        self.assertEqual(canonical(prel.build_relations(self.mixed)),
                         canonical(prel.build_relations(self.mixed)))

    def test_portability_contract(self):
        status = pbc.source_status()
        self.assertIn("mounted", status)
        self.assertIn("skip_status", status)
        raw_root, derived_root = pbc.source_roots()
        self.assertEqual(raw_root,
                         os.environ.get(pbc.ENV_RAW_ROOT) or pbc.RAW_ROOT)
        self.assertEqual(derived_root,
                         os.environ.get(pbc.ENV_DERIVED_ROOT) or pbc.DERIVED_ROOT)


if __name__ == "__main__":
    unittest.main()
