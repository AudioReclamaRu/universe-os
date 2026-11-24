"""Controls for the open GIZA functional-landscape graph architecture.

These tests validate architecture semantics only.  They do not assert any
historical object, measured property, real interface or Giza-cosmos coupling.
"""

from __future__ import annotations

import copy
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import landscape_graph_engine as lge  # noqa: E402


class LandscapeGraphContractTests(unittest.TestCase):
    def setUp(self):
        self.graph = lge.functional_landscape_graph()

    def test_graph_validates(self):
        self.assertTrue(lge.validate_functional_landscape_graph(self.graph))

    def test_open_world_no_core_and_no_citations(self):
        self.assertTrue(self.graph["open_world"])
        self.assertTrue(self.graph["no_primordial_core"])
        self.assertFalse(self.graph["external_citations_attached"])

    def test_signature_counts(self):
        signature = lge.landscape_signature(self.graph)
        self.assertEqual(signature["categories"], len(lge.LANDSCAPE_CATEGORIES))
        self.assertEqual(signature["categories"], 10)
        self.assertEqual(signature["node_count"], 19)
        self.assertEqual(signature["node_kinds"]["object_class"], 9)
        self.assertEqual(signature["node_kinds"]["interface_class"], 1)
        self.assertEqual(signature["node_kinds"]["synthetic_seed_instance"], 9)
        self.assertEqual(signature["interface_count"], 6)
        self.assertEqual(signature["process_count"], 8)
        self.assertEqual(signature["temporal_state_count"], 9)
        self.assertEqual(signature["model_family_count"], 7)

    def test_categories_cover_full_functional_landscape(self):
        self.assertEqual(set(self.graph["categories"]), set(lge.LANDSCAPE_CATEGORIES))
        for name in ("monumental", "linear", "subsurface", "geological", "hydrological",
                     "infrastructural", "natural", "nonobvious", "interface"):
            self.assertIn(name, self.graph["categories"])

    def test_interfaces_are_first_class_not_evaluable(self):
        for item in self.graph["I"]:
            self.assertTrue(item["interface_first"])
            self.assertEqual(item["status"], "not_evaluable_missing_data")
            self.assertTrue(item["required_measurements"])

    def test_processes_cover_conservation_and_model_families(self):
        families = {item["operator_family"] for item in self.graph["P"]}
        self.assertTrue(set(lge.MODEL_FAMILIES).issubset(families))
        conserved = set()
        for item in self.graph["P"]:
            conserved.update(item["conserved_quantities"])
        self.assertTrue({"energy", "mass", "momentum"}.issubset(conserved))

    def test_temporal_states_reject_synchrony(self):
        ids = {item["state_id"] for item in self.graph["T"]}
        self.assertTrue({"G0_GEOLOGY", "G1_ANTHROPOGENIC", "G2_ADAPTATION",
                         "G3_DAMAGE_BURIAL", "S0_PRESENT", "S2_IDEALIZED",
                         "S3_NULL", "S4_HYPOTHESES", "S5_ENVIRONMENT"}.issubset(ids))
        for item in self.graph["T"]:
            self.assertFalse(item["synchrony_assumption"])
            for target in item["allowed_transitions"]:
                self.assertIn(target, ids)

    def test_theta_declares_incomplete_coverage_and_links(self):
        theta = self.graph["Theta"]
        self.assertEqual(theta["coverage_completeness"], "incomplete_unknown")
        for key in ("coverage_register_ref", "parameter_registry_ref", "source_register_ref",
                    "real_source_ingestion_contract_ref", "functional_object_registry_ref"):
            self.assertTrue(theta[key])
        self.assertIn("not evidence of absence", theta["missing_evidence_rule"])

    def test_discovery_rules_forbid_priority_by_prominence(self):
        rules = self.graph["discovery_rules"]
        self.assertTrue(rules["no_primordial_core"])
        self.assertTrue(rules["priority_by_interaction_topology_only"])
        self.assertTrue(rules["size_fame_or_tradition_priority_forbidden"])
        self.assertTrue(rules["multi_membership_allowed"])
        self.assertTrue(rules["overlapping_ensembles_allowed"])
        self.assertTrue(rules["interface_priority_allowed"])
        self.assertTrue(rules["missing_object_not_missing_from_system"])

    def test_prime_is_emergent_not_preset(self):
        prime = self.graph["prime_definition"]
        self.assertEqual(prime["scope"], "emergent_property_of_interaction_ensemble")
        self.assertTrue(prime["preset_object_set_forbidden"])
        self.assertIsNone(prime["hardcoded_frequency_hz"])
        self.assertTrue(prime["requires_discovered_ensembles_and_model_projections"])

    def test_seed_nodes_are_idealized_not_real(self):
        seeds = [node for node in self.graph["V"]
                 if node["node_kind"] == "synthetic_seed_instance"]
        self.assertEqual(len(seeds), 9)
        for node in seeds:
            self.assertEqual(node["evidence_class"], "idealized_design")
            self.assertEqual(node["source_id"], "synthetic_reference_fixture")
            self.assertFalse(node["real_world_claim"])

    def test_validator_rejects_fabricated_citation(self):
        graph = copy.deepcopy(self.graph)
        graph["external_citations_attached"] = True
        with self.assertRaises(lge.LandscapeValidationError):
            lge.validate_functional_landscape_graph(graph)

    def test_validator_rejects_provenance_bearing_node(self):
        graph = copy.deepcopy(self.graph)
        graph["V"][0]["evidence_class"] = "geologically_inferred"
        with self.assertRaises(lge.LandscapeValidationError):
            lge.validate_functional_landscape_graph(graph)

    def test_validator_rejects_primordial_core(self):
        graph = copy.deepcopy(self.graph)
        graph["no_primordial_core"] = False
        with self.assertRaises(lge.LandscapeValidationError):
            lge.validate_functional_landscape_graph(graph)

    def test_validator_rejects_preset_prime(self):
        graph = copy.deepcopy(self.graph)
        graph["prime_definition"]["preset_object_set_forbidden"] = False
        with self.assertRaises(lge.LandscapeValidationError):
            lge.validate_functional_landscape_graph(graph)

    def test_validator_rejects_synchronous_state(self):
        graph = copy.deepcopy(self.graph)
        graph["T"][0]["synchrony_assumption"] = True
        with self.assertRaises(lge.LandscapeValidationError):
            lge.validate_functional_landscape_graph(graph)


class EnsembleDiscoveryTests(unittest.TestCase):
    def test_discovery_is_deterministic_and_nonphysical(self):
        first = lge.discover_candidate_ensembles()
        second = lge.discover_candidate_ensembles()
        self.assertEqual(first, second)
        self.assertEqual(first["discovery_basis"], "declared_interaction_topology_only")
        self.assertFalse(first["ranking_by_size_fame_tradition"])
        self.assertFalse(first["physical_claim"])
        self.assertEqual(first["status"], "structural_candidate_not_physical_evidence")

    def test_discovery_finds_connected_and_overlapping_candidates(self):
        result = lge.discover_candidate_ensembles()
        self.assertTrue(result["connected_ensemble_candidates"])
        self.assertTrue(result["shared_class_candidates"])
        self.assertTrue(result["overlapping_membership_allowed"])
        monumental = next(row for row in result["shared_class_candidates"]
                          if row["class_node"] == "class_monumental")
        self.assertEqual(len(monumental["members"]), 4)

    def test_discovery_uses_only_declared_physical_relations(self):
        result = lge.discover_candidate_ensembles()
        self.assertIn("mechanical_contact", result["interface_carrier_classes"])
        self.assertNotIn("class_membership", result["interface_carrier_classes"])


class ModelProjectionTests(unittest.TestCase):
    def test_only_mechanical_projection_is_evaluable(self):
        summary = lge.model_projection_summary()
        self.assertEqual(summary["evaluable_families"], ["mechanical"])
        self.assertEqual(set(summary["non_evaluable_families"]),
                         set(lge.MODEL_FAMILIES) - {"mechanical"})
        self.assertTrue(summary["no_single_model_claims_whole_landscape"])

    def test_mechanics_projection_is_fixture_only(self):
        projection = lge.projection_to_mechanics()
        self.assertEqual(projection["projection_scope"], "synthetic_fixture_only")
        self.assertEqual(projection["dof_count"], 9)
        self.assertFalse(projection["general_landscape_model_claim"])
        self.assertFalse(projection["primordial_core_claim"])

    def test_projection_accepts_variable_object_count(self):
        custom = {"objects": [{"id": "alpha"}, {"id": "beta"}, {"id": "gamma"}]}
        projection = lge.projection_to_mechanics(custom)
        self.assertEqual(projection["object_ids"], ["alpha", "beta", "gamma"])
        self.assertEqual(projection["dof_count"], 3)
        self.assertFalse(projection["general_landscape_model_claim"])


class InventoryCoverageTests(unittest.TestCase):
    def setUp(self):
        self.register = lge.inventory_coverage_register()

    def test_register_validates(self):
        self.assertTrue(lge.validate_inventory_coverage_register(self.register))

    def test_no_real_objects_catalogued(self):
        self.assertEqual(self.register["catalogued_real_objects"], 0)
        self.assertTrue(self.register["synthetic_seed_objects_only"])
        self.assertEqual(self.register["coverage_basis"], "none_attached")
        for item in self.register["categories"]:
            self.assertEqual(item["catalogued_real_objects"], 0)
            self.assertEqual(item["coverage_status"], "not_inventoried")
            self.assertEqual(item["coverage_confidence"], "unknown")

    def test_absence_is_not_evidence_of_absence(self):
        self.assertIn("not evidence of absence", self.register["absence_rule"])
        report = lge.coverage_gap_report(self.register)
        self.assertIn("not evidence of absence", report["absence_rule"])
        self.assertEqual(len(report["gaps"]), len(lge.LANDSCAPE_CATEGORIES))
        for gap in report["gaps"]:
            self.assertTrue(gap["known_gap"])
            self.assertTrue(gap["required_survey_layer"])

    def test_register_rejects_fabricated_citation(self):
        register = copy.deepcopy(self.register)
        register["external_citations_attached"] = True
        with self.assertRaises(lge.LandscapeValidationError):
            lge.validate_inventory_coverage_register(register)

    def test_register_rejects_claimed_inventory(self):
        register = copy.deepcopy(self.register)
        register["categories"][0]["catalogued_real_objects"] = 1
        with self.assertRaises(lge.LandscapeValidationError):
            lge.validate_inventory_coverage_register(register)

    def test_register_rejects_complete_coverage(self):
        register = copy.deepcopy(self.register)
        register["coverage_completeness"] = "complete"
        with self.assertRaises(lge.LandscapeValidationError):
            lge.validate_inventory_coverage_register(register)


class ArchitectureSummaryTests(unittest.TestCase):
    def test_summary_validates_all_artifacts(self):
        summary = lge.landscape_architecture_summary()
        self.assertTrue(all(summary["validation"].values()))
        self.assertFalse(summary["external_citations_attached"])
        self.assertTrue(summary["open_world"])
        self.assertTrue(summary["no_primordial_core"])

    def test_summary_separates_projection_from_landscape(self):
        summary = lge.landscape_architecture_summary()
        self.assertFalse(summary["model_projections"]["no_single_model_claims_whole_landscape"] is False)
        self.assertFalse(summary["mechanics_projection"]["general_landscape_model_claim"])
        self.assertEqual(summary["prime_definition"]["scope"],
                         "emergent_property_of_interaction_ensemble")


if __name__ == "__main__":
    unittest.main(verbosity=2)
