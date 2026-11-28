"""Controls for the static relation-first atlas snapshot.

The atlas is a *display* of the evidence gate.  These tests guard the boundary:
no fabricated coordinates, no implied relations, no network runtime and no
claim that the schematic layout is geography.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_atlas_schematic as atlas  # noqa: E402
import inventory_engine as ie  # noqa: E402


class AtlasSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = atlas.build_snapshot()
        with open(os.path.join(HERE, atlas.OUTPUT), "r", encoding="utf-8") as handle:
            self.html = handle.read()

    def test_honesty_gate_is_called(self):
        self.assertTrue(self.snapshot["honesty"]["assert_inventory_honesty"])
        with mock.patch.object(ie, "assert_inventory_honesty", return_value=False):
            with self.assertRaises(ie.InventoryValidationError):
                atlas.build_snapshot()

    def test_zero_registers_are_preserved(self):
        counts = self.snapshot["counts"]
        for key in ("verified_sources", "real_objects", "natural_structures", "relations"):
            self.assertEqual(counts[key], 0, key)
        self.assertEqual(counts["inventory_slots"], 14)
        self.assertEqual(counts["relation_classes"], 9)
        self.assertFalse(self.snapshot["external_citations_attached"])
        self.assertFalse(self.snapshot["coordinate_claims"])

    def test_cross_cases_remain_not_evaluable(self):
        for value in self.snapshot["honesty"]["cross_cases"].values():
            self.assertTrue(value.startswith("not_evaluable"))
        self.assertEqual(self.snapshot["honesty"]["promotable_claims"], 0)
        self.assertEqual(self.snapshot["honesty"]["live_adapters"], 0)

    def test_cross_cases_are_read_from_epistemic_manifest(self):
        with open(atlas.EPISTEMIC_MANIFEST, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(self.snapshot["honesty"]["cross_cases"], manifest["cross_cases"])
        self.assertEqual(self.snapshot["honesty"]["live_adapters"], manifest["live_adapters"])

    def test_no_coordinate_values_or_geometry_emitted(self):
        embedded = re.search(
            r'<script id="atlas-snapshot" type="application/json">(.*?)</script>',
            self.html, re.S,
        )
        self.assertIsNotNone(embedded)
        data = embedded.group(1)
        for key in ("latitude", "longitude", "easting", "northing", "geometry_value"):
            self.assertNotRegex(data, r'"%s"\s*:' % key)
        self.assertNotIn('"coordinates": {', data)
        self.assertNotIn('"elevations": [', data)
        # Slot rows carry status text only, never a numeric position.
        self.assertNotRegex(self.html, r'\b[234][0-9]\.\d{4,}\s*,\s*[0-9]{1,3}\.\d{4,}')

    def test_all_slots_and_relation_families_rendered(self):
        for slot in self.snapshot["slots"]:
            self.assertIn(slot["slot_id"], self.html)
        for item in self.snapshot["relation_classes"]:
            self.assertIn(item["class_id"], self.html)

    def test_marking_and_status_present(self):
        self.assertIn("SCHEMATIC / NOT GEODETIC", self.html)
        self.assertIn("NOT_EVALUABLE", self.html)
        self.assertIn("0 VERIFIED RELATIONS", self.html)
        self.assertIn("NODE POSITIONS = DISPLAY LAYOUT ONLY", self.html)

    def test_no_network_runtime_or_controls(self):
        forbidden = ("http://", "https://", "WebSocket", "fetch(", "setInterval",
                     "startBot", "stopBot", "onclick", "<input", "<button")
        for token in forbidden:
            self.assertNotIn(token, self.html, token)

    def test_preferred_design_tokens_present(self):
        for token in ("#09090f", "#f5a623", "#ffcc44", "#39ff7a", "#ff3c54",
                      "#00d4ff", "#8855ff", "Martian Mono", "Unbounded",
                      "scanH", "repeating-linear-gradient",
                      "grid-template-columns:340px 1fr 340px",
                      "font-size:14px",
                      "flex:1 1 auto",
                      "cv.offsetHeight"):
            self.assertIn(token, self.html, token)

    def test_center_column_is_map_only_and_map_fills_height(self):
        start = self.html.index('<div class="col" id="center-col">')
        end = self.html.index('<div class="col">', start)
        center = self.html[start:end]
        self.assertIn("RELATION MAP", center)
        self.assertNotIn("SLOT REGISTER", center)
        self.assertIn("flex:1 1 auto", self.html)
        self.assertIn("H*0.46", self.html)
        self.assertIn("cv.offsetHeight", self.html)

    def test_build_is_deterministic_and_matches_committed_file(self):
        first = atlas.render_html(self.snapshot)
        second = atlas.render_html(atlas.build_snapshot())
        self.assertEqual(first, second)
        self.assertEqual(first, self.html)


if __name__ == "__main__":
    unittest.main()
