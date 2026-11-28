"""Controls for the integrated system cockpit contracts.

These tests guard the honesty boundary of Issue #7 section 14: no simulated
integration, no mixing of physical energy with information, no measured
interpretation of vector 42, and no automatic ASTRAEA trading.
"""

from __future__ import annotations

import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cockpit_engine as ce  # noqa: E402


def sample_event(**overrides):
    event = {
        "event_id": "evt_0001",
        "project_id": "GIZA_PRIME",
        "sector_id": None,
        "entity_id": "synthetic_beam",
        "event_type": "measurement",
        "event_time": None,
        "ingest_time": "2026-11-24T00:00:00Z",
        "source_id": None,
        "payload": {"value": 1.0},
        "units": "W",
        "coordinate_frame": None,
        "model_version": "synthetic",
        "evidence_status": "synthetic_fixture",
        "uncertainty": None,
        "permissions": {"access": "public", "licence": "project"},
    }
    event.update(overrides)
    return event


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = ce.system_contract()

    def test_contract_validates(self):
        self.assertTrue(ce.validate_system_contract(self.contract))

    def test_system_event_fields_exact(self):
        self.assertEqual(len(self.contract["system_event_fields"]), 15)
        self.assertIn("permissions", self.contract["system_event_fields"])
        self.assertIn("uncertainty", self.contract["system_event_fields"])

    def test_rejects_removed_separation_rule(self):
        contract = copy.deepcopy(self.contract)
        contract["separation_rules"]["vector_42_physical_unit_forbidden"] = False
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_system_contract(contract)

    def test_three_unit_classes(self):
        self.assertEqual(set(self.contract["unit_classes"]),
                         {"physical", "informational", "conceptual"})


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = ce.project_registry()
        self.contract = ce.system_contract()

    def test_registry_validates(self):
        self.assertTrue(ce.validate_project_registry(self.registry, self.contract))

    def test_seven_system_nodes(self):
        ids = {node["node_id"] for node in self.registry["nodes"]}
        self.assertEqual(len(ids), 7)
        self.assertIn("MEGABRAIN", ids)
        self.assertIn("EARTH_EAR", ids)

    def test_five_business_sectors(self):
        self.assertEqual(len(self.registry["business_sectors"]), 5)
        for sector in self.registry["business_sectors"]:
            self.assertEqual(sector["metrics_domain"], "informational")
            self.assertNotIn("W", sector["allowed_signals"])
            self.assertNotIn("J", sector["allowed_signals"])

    def test_vector_42_is_conceptual(self):
        vector = self.registry["intent_vector_42"]
        self.assertIsNone(vector["physical_dimension"])
        self.assertEqual(vector["units"], "conceptual")
        self.assertEqual(vector["validation"], "not_validated")

    def test_legacy_is_unavailable(self):
        legacy = next(n for n in self.registry["nodes"] if n["node_id"] == "UNIVERSE_2_0")
        self.assertEqual(legacy["status"], "unavailable")
        forbidden = [p for p in legacy["integration_points"]
                     if p["id"] == "legacy_runtime_import"]
        self.assertEqual(forbidden[0]["status"], "forbidden")

    def test_no_simulated_integration(self):
        summary = ce.adapter_summary(self.registry)
        self.assertEqual(summary["simulated_integrations"], 0)

    def test_rejects_physical_business_unit(self):
        registry = copy.deepcopy(self.registry)
        registry["business_sectors"][0]["metrics_domain"] = "physical"
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_project_registry(registry, self.contract)

    def test_rejects_measured_vector_42(self):
        registry = copy.deepcopy(self.registry)
        registry["intent_vector_42"]["physical_dimension"] = "energy"
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_project_registry(registry, self.contract)


class EventGuardTests(unittest.TestCase):
    def test_physical_event_validates(self):
        self.assertTrue(ce.validate_event(sample_event()))

    def test_rejects_unknown_project(self):
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_event(sample_event(project_id="UNKNOWN"))

    def test_rejects_bad_evidence_status(self):
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_event(sample_event(evidence_status="verified_truth"))

    def test_rejects_unregistered_unit(self):
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_event(sample_event(units="furlong"))

    def test_vector_42_physical_unit_rejected(self):
        event = sample_event(project_id="EARTH_EAR", entity_id="VECTOR_42",
                             units="J", evidence_status="hypothetical")
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_event(event)

    def test_vector_42_conceptual_unit_allowed(self):
        event = sample_event(project_id="EARTH_EAR", entity_id="VECTOR_42",
                             units="conceptual", event_type="signal_observed",
                             evidence_status="hypothetical")
        self.assertTrue(ce.validate_event(event))

    def test_business_physical_unit_rejected(self):
        event = sample_event(project_id="EARTH_EAR", sector_id="WEB_SITES",
                             entity_id="page_view", units="W",
                             event_type="signal_observed",
                             evidence_status="published")
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_event(event)

    def test_business_informational_unit_allowed(self):
        event = sample_event(project_id="EARTH_EAR", sector_id="WEB_SITES",
                             entity_id="page_view", units="count",
                             event_type="signal_observed",
                             evidence_status="published")
        self.assertTrue(ce.validate_event(event))

    def test_missing_permissions_rejected(self):
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_event(sample_event(permissions={}))


class CrossDomainTests(unittest.TestCase):
    def test_rejects_link_without_mechanism(self):
        link = {
            "source_event_id": "a", "target_event_id": "b",
            "mechanism_definition": None, "evidence_status": "hypothetical",
            "uncertainty": None, "permission_scope": "public",
            "alternative_explanations_checked": True,
        }
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_cross_domain_link(link)

    def test_accepts_documented_link(self):
        link = {
            "source_event_id": "a", "target_event_id": "b",
            "mechanism_definition": "documented hydraulic pressure transfer",
            "evidence_status": "inferred", "uncertainty": {"interval": [0, 1]},
            "permission_scope": "public",
            "alternative_explanations_checked": True,
        }
        self.assertTrue(ce.validate_cross_domain_link(link))

    def _astraea_result(self, **overrides):
        result = {"project_id": "ASTRAEA", "mode": "paper",
                  "data_scope": "historical", "auto_trade": False,
                  "claim": "candidate", "null_models_checked": True,
                  "holdout_checked": True}
        result.update(overrides)
        return result

    def test_astraea_candidate_requires_null_and_holdout(self):
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_astraea_result(
                self._astraea_result(null_models_checked=False))

    def test_astraea_auto_trade_forbidden(self):
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_astraea_result(self._astraea_result(auto_trade=True))

    def test_astraea_live_mode_forbidden(self):
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_astraea_result(self._astraea_result(mode="live"))

    def test_astraea_non_historical_scope_forbidden(self):
        with self.assertRaises(ce.CockpitContractError):
            ce.validate_astraea_result(self._astraea_result(data_scope="streaming"))

    def test_astraea_negative_result_is_valid(self):
        self.assertTrue(ce.validate_astraea_result(
            self._astraea_result(claim="negative")))


class ManifestTests(unittest.TestCase):
    def test_manifest_has_ten_views(self):
        manifest = ce.cockpit_manifest()
        self.assertEqual(len(manifest["views"]), 10)
        self.assertEqual({v["id"] for v in manifest["views"]},
                         {"spatial", "system", "relations", "time", "crossdomain",
                          "evidence", "intent", "operations", "business", "versions"})

    def test_manifest_honesty_flags(self):
        manifest = ce.cockpit_manifest()
        self.assertEqual(manifest["verified_geodetic_objects"], 0)
        self.assertEqual(manifest["verified_sources"], 0)
        self.assertFalse(manifest["giza_cosmos_claim"])
        self.assertFalse(manifest["vector_42_is_physical_energy"])
        self.assertFalse(manifest["astraea_auto_trade"])

    def test_manifest_is_deterministic(self):
        self.assertEqual(ce.cockpit_manifest(), ce.cockpit_manifest())

    def test_honesty_assertion(self):
        self.assertTrue(ce.assert_cockpit_honesty())

    def test_write_payload_roundtrip(self):
        path = os.path.join(HERE, "_tmp_cockpit_data.js")
        try:
            ce.write_cockpit_data(path)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("window.COCKPIT_DATA =", text)
            self.assertIn("window.COCKPIT_MANIFEST_SHA256 =", text)
            self.assertIn("UNIVERSE_OS_INTEGRATED_SYSTEM_COCKPIT", text)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_no_empty_atlas_release(self):
        for iteration in ce.KNOWN_ITERATIONS:
            self.assertEqual(iteration["scientific_atlas_version"], "none")


class HtmlShellTests(unittest.TestCase):
    """Static controls for the offline visual shell (no browser is launched)."""

    def setUp(self):
        with open(os.path.join(HERE, "index.html"), "r", encoding="utf-8") as handle:
            self.html = handle.read()

    def test_canvas_stage_exists(self):
        self.assertIn('<canvas id="viewport">', self.html)
        self.assertIn("grid-template-columns:minmax(190px,10fr) minmax(0,80fr) minmax(190px,10fr)",
                      self.html)

    def test_all_nine_views_are_addressable(self):
        manifest = ce.cockpit_manifest()
        for view in manifest["views"]:
            self.assertIn("state.view==='%s'" % view["id"], self.html)

    def test_detail_binding_is_delegated(self):
        self.assertIn("document.addEventListener('click'", self.html)
        self.assertNotIn("querySelectorAll('[data-detail]')", self.html)

    def test_mouse_navigation_is_present(self):
        for token in ("'mousedown'", "'mousemove'", "'wheel'", "'contextmenu'", "resetCamera"):
            self.assertIn(token, self.html)

    def test_no_auto_trade_or_cosmic_claim_in_shell(self):
        lowered = self.html.lower()
        self.assertNotIn("auto_trade=true", lowered.replace(" ", ""))
        self.assertNotIn("giza communicates", lowered)

    def test_crossdomain_shell_guards(self):
        self.assertIn("state.view==='crossdomain'", self.html)
        self.assertIn("THREE DISTINCT ENERGY MARKERS", self.html)
        self.assertIn("NO BIT→JOULE", self.html)
        self.assertIn("EARTH_EAR", self.html)
        self.assertNotIn("digital_domain", self.html)

    def test_generated_payload_digest_matches_manifest(self):
        path = os.path.join(HERE, "cockpit_data.js")
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        json_text = json.dumps(ce.cockpit_manifest(), sort_keys=True, indent=2,
                               ensure_ascii=False, allow_nan=False,
                               default=ce._json_default)
        digest = __import__("hashlib").sha256(json_text.encode("utf-8")).hexdigest()
        self.assertIn('window.COCKPIT_MANIFEST_SHA256 = "%s";' % digest, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
