"""Structural controls for the single-file GIZA PRIME DUAL ATLAS.

These tests guard the boundary between the evidence-gated relation layer and
the real-but-uncorroborated GPMP spatial layer.  No test here asserts that a
control station is an archaeological object or that a graphic grid is terrain.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_atlas_schematic as atlas  # noqa: E402
import gpmp_spatial_layer as gsl  # noqa: E402


def _temp_dir() -> str:
    preferred = r"F:\Pill\tmp\opencode"
    return preferred if os.path.isdir(preferred) else HERE


class DualAtlasStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = atlas.build_snapshot()
        cls.spatial = atlas.build_spatial_snapshot()
        cls.html = atlas.render_html(cls.snapshot, cls.spatial)
        with open(os.path.join(HERE, atlas.OUTPUT), "r", encoding="utf-8") as handle:
            cls.committed = handle.read()

    def _script(self, identifier):
        match = re.search(
            r'<script id="%s" type="application/json">(.*?)</script>' % identifier,
            self.html, re.S)
        self.assertIsNotNone(match, identifier)
        return json.loads(match.group(1).replace("<\\/", "</"))

    def test_two_independent_layers_in_one_document(self):
        self.assertIn('id="view-relation"', self.html)
        self.assertIn('id="view-spatial"', self.html)
        self.assertIn("01 RELATION SKELETON", self.html)
        self.assertIn("02 SPATIAL 3D SKELETON", self.html)
        self.assertIn('class="layer-view hidden" id="view-spatial"', self.html)
        self.assertIn('id="spatial-canvas"', self.html)

    def test_snapshots_are_separate_documents(self):
        relation = self._script("atlas-snapshot")
        spatial = self._script("spatial-snapshot")
        self.assertNotIn("points", relation)
        self.assertEqual(relation["marking"], "SCHEMATIC / NOT GEODETIC")
        self.assertEqual(spatial["marking"], "SOURCE POINTS / NOT A TERRAIN MODEL")
        self.assertEqual(relation["counts"]["real_objects"], 0)
        self.assertEqual(spatial["counts"]["total"], 41)

    def test_spatial_snapshot_keeps_lon_lat_as_scalars(self):
        spatial = self._script("spatial-snapshot")
        point = spatial["points"][0]
        self.assertIsInstance(point["longitude_latitude"]["longitude"], float)
        self.assertIsInstance(point["longitude_latitude"]["latitude"], float)
        self.assertEqual(point["longitude_latitude"]["kml_z"], 0.0)
        self.assertIs(point["longitude_latitude"]["kml_z_is_elevation"], False)

    def test_no_fabricated_lines_or_terrain_mesh(self):
        spatial = self._script("spatial-snapshot")
        self.assertIs(spatial["render_rules"]["terrain_mesh"], False)
        self.assertIs(spatial["render_rules"]["fabricated_lines"], False)
        self.assertEqual(spatial["render_rules"]["vertical_exaggeration_default"], 1.0)
        self.assertIs(spatial["render_rules"]["grid_is_graphic_support_only"], True)
        self.assertEqual(spatial["separation"]["gpmp_and_arce_sphinx_grid"], "separate")

    def test_interactive_controls_use_no_form_elements_or_inline_handlers(self):
        for token in ("<input", "<button", "onclick", "setInterval",
                      "WebSocket", "fetch(", "startBot", "stopBot"):
            self.assertNotIn(token, self.html, token)
        for token in ('data-toggle="main"', 'data-toggle="secondary"',
                      'data-toggle="labels"', 'data-toggle="grid"',
                      'data-act="reset"', 'data-act="ex-up"', 'data-act="ex-down"',
                      'contenteditable="true"', "addEventListener('wheel'",
                      "addEventListener('mousedown'"):
            self.assertIn(token, self.html, token)

    def test_no_external_dependencies(self):
        for token in ("http://", "https://", "<link ", "src=\"/", "cdn", "unpkg"):
            self.assertNotIn(token, self.html, token)

    def test_relation_map_geometry_unchanged(self):
        for token in ("SCHEMATIC / NOT GEODETIC", "NODE POSITIONS = DISPLAY LAYOUT ONLY",
                      "0 VERIFIED RELATIONS", "cv.offsetHeight", "H*0.46"):
            self.assertIn(token, self.html, token)

    def test_build_is_deterministic_and_matches_file(self):
        self.assertEqual(self.html, self.committed)
        again = atlas.render_html(atlas.build_snapshot(), atlas.build_spatial_snapshot())
        self.assertEqual(self.html, again)

    def test_import_report_records_real_counts(self):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", dir=_temp_dir(), delete=False)
        handle.close()
        try:
            path = atlas.write_import_report(handle.name)
            with open(path, "r", encoding="utf-8") as source:
                report = json.load(source)
            self.assertEqual(report["relation_layer"]["verified_sources"], 0)
            self.assertEqual(report["relation_layer"]["relations"], 0)
            self.assertEqual(report["spatial_layer"]["counts"]["total"], 41)
            self.assertFalse(report["spatial_layer"]["provenance_states"][
                "SOURCE_PROVENANCE_VERIFIED"])
            self.assertEqual(report["build_contract"]["external_requests"], 0)
        finally:
            if os.path.isfile(handle.name):
                os.unlink(handle.name)


@unittest.skipUnless(shutil.which("node"), "Node.js unavailable for syntax check")
class DualAtlasJavascriptTests(unittest.TestCase):
    def test_inline_javascript_parses(self):
        with open(os.path.join(HERE, atlas.OUTPUT), "r", encoding="utf-8") as handle:
            html = handle.read()
        blocks = re.findall(r'<script>(.*?)</script>', html, re.S)
        self.assertTrue(blocks)
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", dir=_temp_dir(), delete=False, encoding="utf-8")
        try:
            handle.write("\n".join(blocks))
            handle.close()
            result = subprocess.run(
                [shutil.which("node"), "--check", handle.name],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            if os.path.isfile(handle.name):
                os.unlink(handle.name)


if __name__ == "__main__":
    unittest.main()
