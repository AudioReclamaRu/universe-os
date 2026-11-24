"""Controls for the real-landscape inventory and relation-discovery framework.

These tests guard the honesty boundary: zero verified sources means zero real
objects, zero relations and symbolic-only modelling.  The capability
demonstration is explicitly synthetic and makes no Giza claim.
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

import inventory_engine as ie  # noqa: E402


class SourceContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = ie.inventory_source_contract()

    def test_contract_validates(self):
        self.assertTrue(ie.validate_source_contract(self.contract))

    def test_no_sources_attached(self):
        self.assertEqual(self.contract["attached_sources"], [])
        self.assertEqual(self.contract["verified_source_count"], 0)
        self.assertFalse(self.contract["external_citations_attached"])

    def test_required_source_fields(self):
        fields = self.contract["required_source_fields"]
        self.assertTrue({"source_id", "source_type", "bibliographic_ref", "datum",
                         "retrieved_at", "verification_state"}.issubset(set(fields)))

    def test_rejects_attached_source_without_verification(self):
        contract = copy.deepcopy(self.contract)
        contract["attached_sources"] = [{"source_id": "fabricated"}]
        with self.assertRaises(ie.InventoryValidationError):
            ie.validate_source_contract(contract)

    def test_rejects_missing_gate_flag(self):
        contract = copy.deepcopy(self.contract)
        contract["gate"]["no_source_no_record"] = False
        with self.assertRaises(ie.InventoryValidationError):
            ie.validate_source_contract(contract)

    def test_rejects_fabricated_substitute(self):
        contract = copy.deepcopy(self.contract)
        contract["gate"]["no_fabricated_substitute"] = False
        with self.assertRaises(ie.InventoryValidationError):
            ie.validate_source_contract(contract)


class ObjectRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = ie.object_registry()

    def test_registry_validates(self):
        self.assertTrue(ie.validate_object_registry(self.registry))

    def test_real_registers_empty(self):
        self.assertEqual(self.registry["objects"], [])
        self.assertEqual(self.registry["natural_structures"], [])
        self.assertEqual(self.registry["verified_source_count"], 0)

    def test_slots_cover_all_required_categories(self):
        slot_ids = {slot["slot_id"] for slot in self.registry["inventory_slots"]}
        self.assertTrue(set(ie.REQUIRED_SLOT_IDS).issubset(slot_ids))

    def test_slots_unique_with_explicit_gaps(self):
        slots = self.registry["inventory_slots"]
        ids = [slot["slot_id"] for slot in slots]
        self.assertEqual(len(ids), len(set(ids)))
        for slot in slots:
            self.assertEqual(slot["coverage_status"], "not_inventoried")
            self.assertEqual(slot["verified_object_count"], 0)
            self.assertTrue(slot["known_gap"])
            self.assertTrue(slot["required_survey_layer"])
            self.assertTrue(slot["targets_to_seek"])

    def test_natural_structures_are_first_class_slots(self):
        natural = [slot["slot_id"] for slot in self.registry["inventory_slots"]
                   if slot["natural_structure"] is True]
        self.assertIn("bedrock_massifs_fractures_faults", natural)
        self.assertIn("ancient_channels_hydrogeology", natural)
        self.assertIn("natural_processes", natural)
        self.assertIn("interfaces_boundaries", natural)

    def test_no_preselected_core(self):
        self.assertTrue(self.registry["gate"]["no_preselected_core"])
        for slot in self.registry["inventory_slots"]:
            self.assertNotIn("core", slot)
            self.assertNotIn("priority", slot)

    def test_field_contract_requires_coordinates_and_sources(self):
        fields = self.registry["record_field_contract"]["required_fields"]
        for field in ie.NUMERIC_FIELDS + ("source_ids",):
            self.assertIn(field, fields)

    def test_rejects_injected_real_object(self):
        registry = copy.deepcopy(self.registry)
        registry["objects"] = [{"object_id": "invented_object"}]
        with self.assertRaises(ie.InventoryValidationError):
            ie.validate_object_registry(registry)

    def test_rejects_claimed_verified_slot(self):
        registry = copy.deepcopy(self.registry)
        registry["inventory_slots"][0]["verified_object_count"] = 1
        with self.assertRaises(ie.InventoryValidationError):
            ie.validate_object_registry(registry)


class RelationGraphTests(unittest.TestCase):
    def setUp(self):
        self.graph = ie.relation_graph()

    def test_graph_validates(self):
        self.assertTrue(ie.validate_relation_graph(self.graph))

    def test_nine_typed_relation_classes(self):
        self.assertEqual(set(self.graph["relation_classes"]), set(ie.RELATION_CLASSES))
        self.assertEqual(len(self.graph["relation_classes"]), 9)

    def test_three_epistemic_statuses(self):
        self.assertEqual(set(self.graph["epistemic_statuses"]), set(ie.EPISTEMIC_STATUSES))

    def test_relations_empty(self):
        self.assertEqual(self.graph["relations"], [])
        self.assertFalse(self.graph["external_citations_attached"])

    def test_separation_rule_forbids_merging(self):
        self.assertIn("must never be merged", self.graph["separation_rule"])

    def test_no_cosmic_bridge_flag(self):
        self.assertTrue(self.graph["ingestion_gate"]["no_direct_pyramid_to_planetary_or_cosmic_bridge"])

    def test_rejects_injected_relation(self):
        graph = copy.deepcopy(self.graph)
        graph["relations"] = [{"relation_id": "invented",
                               "relation_class": "mechanical",
                               "epistemic_status": "established_documented"}]
        with self.assertRaises(ie.InventoryValidationError):
            ie.validate_relation_graph(graph)

    def test_rejects_removed_separation_rule(self):
        graph = copy.deepcopy(self.graph)
        graph["separation_rule"] = "relations may be merged"
        with self.assertRaises(ie.InventoryValidationError):
            ie.validate_relation_graph(graph)


class IncompletenessMapTests(unittest.TestCase):
    def setUp(self):
        self.mapping = ie.incompleteness_map()

    def test_map_validates(self):
        self.assertTrue(ie.validate_incompleteness_map(self.mapping))

    def test_five_coverage_states(self):
        self.assertEqual(set(self.mapping["states"]), set(ie.COVERAGE_STATES))
        self.assertEqual(len(self.mapping["states"]), 5)

    def test_all_slots_unknown(self):
        rows = self.mapping["coverage_by_slot"]
        self.assertEqual(len(rows), len(ie.REQUIRED_SLOT_IDS))
        for row in rows:
            self.assertEqual(row["state"], "unknown")
            self.assertEqual(row["verified_object_count"], 0)
            self.assertTrue(row["required_next_step"])

    def test_rejects_complete_coverage(self):
        mapping = copy.deepcopy(self.mapping)
        mapping["coverage_completeness"] = "complete"
        with self.assertRaises(ie.InventoryValidationError):
            ie.validate_incompleteness_map(mapping)

    def test_rejects_plausible_number_substitution(self):
        mapping = copy.deepcopy(self.mapping)
        mapping["rules"]["unknown_must_not_be_replaced_by_plausible_number"] = False
        with self.assertRaises(ie.InventoryValidationError):
            ie.validate_incompleteness_map(mapping)


class AdaptiveModelingTests(unittest.TestCase):
    def test_symbolic_when_no_source(self):
        result = ie.modeling_tier_for({})
        self.assertEqual(result["tier"], "symbolic")
        self.assertEqual(result["reason"], "no_verified_source")

    def test_numeric_with_complete_verified_record(self):
        record = {field: "value" for field in ie.NUMERIC_FIELDS}
        record["source_ids"] = ["src_1"]
        result = ie.modeling_tier_for(record, ["src_1"])
        self.assertEqual(result["tier"], "numeric")

    def test_interval_with_bounds(self):
        record = {"source_ids": ["src_1"],
                  "bounded_geometry": {"x": [0, 1]},
                  "elevation_range": [10, 20]}
        result = ie.modeling_tier_for(record, ["src_1"])
        self.assertEqual(result["tier"], "interval")

    def test_symbolic_with_partial_verified_record(self):
        record = {"source_ids": ["src_1"], "coordinates": [1, 2]}
        result = ie.modeling_tier_for(record, ["src_1"])
        self.assertEqual(result["tier"], "symbolic")

    def test_rejects_unverified_source(self):
        record = {"source_ids": ["unverified"]}
        result = ie.modeling_tier_for(record, ["src_1"])
        self.assertEqual(result["tier"], "rejected")
        self.assertEqual(result["reason"], "source_not_verified")

    def test_tier_summary_all_symbolic(self):
        summary = ie.tier_summary()
        self.assertEqual(summary["counts"]["symbolic"], len(ie.REQUIRED_SLOT_IDS))
        self.assertEqual(summary["real_numeric_records"], 0)
        self.assertEqual(summary["fabricated_parameters"], 0)


class EnsembleDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ie.SYNTHETIC_DEMONSTRATION
        self.result = ie.discover_all_ensembles()

    def test_fixture_is_explicitly_synthetic(self):
        self.assertTrue(self.fixture["synthetic"])
        self.assertFalse(self.fixture["physical_claim"])

    def test_feature_specific_candidates(self):
        per_feature = self.result["per_feature"]
        self.assertEqual(set(per_feature), {"hydraulic", "geological", "spatial", "mechanical"})
        hydraulic = per_feature["hydraulic"]["candidates"]
        self.assertIn(["bedrock_fracture_B", "drainage_channel_A", "well_F"], hydraulic)

    def test_overlapping_members(self):
        self.assertEqual(self.result["overlap_count"], 6)
        memberships = self.result["overlapping_members"]["bedrock_fracture_B"]
        features = {row["feature"] for row in memberships}
        self.assertEqual(features, {"hydraulic", "geological", "mechanical"})

    def test_no_preselected_core(self):
        self.assertTrue(self.result["no_preselected_core"])
        for feature in self.result["per_feature"].values():
            self.assertTrue(feature["no_preselected_core"])
            self.assertFalse(feature["ranking_by_size_fame_tradition"])
            self.assertFalse(feature["physical_claim"])

    def test_discovery_does_not_start_from_prominent_objects(self):
        for feature in self.result["per_feature"].values():
            for candidate in feature["candidates"]:
                self.assertEqual(candidate, sorted(candidate))

    def test_epistemic_statuses_separated(self):
        mechanical = self.result["per_feature"]["mechanical"]["relations_by_epistemic_status"]
        self.assertEqual(mechanical["inferred_indirect"], [])
        self.assertEqual(mechanical["hypothesized_unverified"], ["r6", "r7"])
        self.assertEqual(mechanical["established_documented"], [])

    def test_discovery_is_deterministic(self):
        first = ie.discover_all_ensembles()
        second = ie.discover_all_ensembles()
        self.assertEqual(first, second)

    def test_real_discovery_is_empty(self):
        real = ie.discover_real_ensembles()
        self.assertEqual(real["verified_objects"], 0)
        self.assertEqual(real["verified_relations"], 0)
        self.assertEqual(real["ensembles_discovered"], 0)
        self.assertEqual(real["status"], "no_verified_data_no_discovery")


class ReportTests(unittest.TestCase):
    def test_report_has_five_results(self):
        report = ie.build_inventory_report()
        self.assertEqual(len(report["five_results"]), 5)
        self.assertIn("1_object_registry", report["five_results"])
        self.assertIn("5_incompleteness_map", report["five_results"])

    def test_report_honesty_flags(self):
        report = ie.build_inventory_report()
        self.assertTrue(report["no_fabricated_parameters"])
        self.assertTrue(report["no_preselected_core"])
        self.assertFalse(report["giza_cosmos_claim"])
        self.assertFalse(report["external_citations_attached"])

    def test_report_validation_all_true(self):
        report = ie.build_inventory_report()
        self.assertTrue(all(report["validation"].values()))

    def test_report_is_byte_deterministic(self):
        first = json.dumps(ie.build_inventory_report(), sort_keys=True, indent=2)
        second = json.dumps(ie.build_inventory_report(), sort_keys=True, indent=2)
        self.assertEqual(first, second)

    def test_write_report_roundtrip(self):
        path = os.path.join(HERE, "_tmp_inventory_report.json")
        try:
            ie.write_inventory_report(path)
            with open(path, "r", encoding="utf-8") as handle:
                written = json.load(handle)
            self.assertEqual(written["report_id"], "GIZA_REAL_LANDSCAPE_INVENTORY_FRAMEWORK_REPORT")
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
