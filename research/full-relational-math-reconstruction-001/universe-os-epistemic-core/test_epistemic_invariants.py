"""Machine invariants §18.11, manifest and honesty controls."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import epistemic_claims as ec  # noqa: E402
import epistemic_uncertainty as eu  # noqa: E402
import epistemic_core as core  # noqa: E402
from epistemic_graph import (  # noqa: E402
    IdentityRegistry, KnowledgeGraph, OntologyPassport, PassportRegistry,
)
from epistemic_types import (  # noqa: E402
    ACCEPTANCE_SCENARIOS, AXES, MACHINE_INVARIANTS, EPISTEMIC_VERSION,
    EpistemicContractError,
)
from test_epistemic_core import DATE, primary_graph  # noqa: E402


class InvariantTests(unittest.TestCase):
    def setUp(self):
        self.graph = primary_graph()
        self.ontology = OntologyPassport()
        self.identity = IdentityRegistry()
        self.passports = PassportRegistry()
        self.cache = eu.ComputationCache()
        self.engine = eu.UncertaintyEngine(self.cache)
        self.kwargs = dict(
            graph=self.graph, ontology=self.ontology, identity=self.identity,
            passports=self.passports, cache=self.cache, engine=self.engine,
        )

    def result_for(self, invariant_id):
        return next(item for item in core.check_invariants(**self.kwargs)
                    if item["id"] == invariant_id)

    def test_clean_synthetic_graph_passes_all_invariants(self):
        results = core.check_invariants(**self.kwargs)
        self.assertEqual([r["id"] for r in results],
                         [item["id"] for item in MACHINE_INVARIANTS])
        failures = [r for r in results if not r["passed"]]
        self.assertEqual(failures, [])
        self.assertTrue(core.assert_invariants(**self.kwargs))

    def test_inv01_bad_claim_scope(self):
        self.graph.update_node("C1", {"scope": {}}, merge=True)
        self.assertFalse(self.result_for("INV-01")["passed"])

    def test_inv02_active_claim_without_primary_grounding(self):
        self.graph.update_node("C1", {"status": "active"}, merge=True)
        self.graph._edges = [
            e for e in self.graph._edges
            if not (e["edge_type"] == "derived_from"
                    and e["from_id"] in ("A1", "A2"))
        ]
        result = self.result_for("INV-02")
        self.assertFalse(result["passed"])

    def test_inv04_shared_dependency_without_review(self):
        self.graph.add_edge("A2", "S1", "derived_from", synthetic=True)
        self.assertFalse(self.result_for("INV-04")["passed"])

    def test_inv05_averaged_conflict_value(self):
        ec.create_claim(
            self.graph, "C2", statement="rival", subject="X", predicate="v",
            object_value=2, scope={"epoch": "synthetic"},
            epistemic_type="inferred", sources=["S2"], author="b",
            created_at=DATE, synthetic=True,
        )
        ec.ConflictRegistry().open(
            self.graph, "K1", ["C1", "C2"], divergence_type="units",
            comparability={}, synthetic=True,
        )
        self.graph.update_node(
            "K1",
            {"resolutions": [{"averaged_value": 1.75, "scope": {}}]},
            merge=True,
        )
        self.assertFalse(self.result_for("INV-05")["passed"])

    def test_inv06_revision_without_event(self):
        self.graph.update_node("M1", {"value": 11.0}, merge=True)
        self.graph._events = [
            e for e in self.graph._events
            if not (e["event_type"] == "node_added"
                    and e["payload"].get("node_id") == "M1")
        ]
        self.assertFalse(self.result_for("INV-06")["passed"])

    def test_inv07_condition_not_linked_to_test(self):
        self.graph.add_node(
            "COND_BAD", "Condition",
            {"claim_id": "C1", "observable": "x", "target": "y", "comparison": ">",
             "threshold": 1, "units": "Hz", "uncertainty": {},
             "source_requirements": [], "controls": [], "expected_action": "suspend",
             "preregistration_date": DATE, "machine_checkable": False},
            synthetic=True,
        )
        self.graph.record_event("condition_human_review_required", {"condition_id": "OTHER"})
        self.assertFalse(self.result_for("INV-07")["passed"])

    def test_inv08_state_without_owning_entity(self):
        self.graph.add_node("STATE_X", "EntityState", {"epoch": "A"}, synthetic=True)
        self.assertFalse(self.result_for("INV-08")["passed"])

    def test_inv09_criteria_change_without_impact_review(self):
        self.ontology.register("CLASS_X", membership_criteria=["c"])
        self.ontology.register("CLASS_X", membership_criteria=["c2"], migration_from=1)
        self.assertFalse(self.result_for("INV-09")["passed"])

    def test_inv10_cached_passport_for_missing_entity(self):
        self.passports._cache["BAD"] = {
            "entity_id": "MISSING", "kind": "identity", "state": "complete",
            "fields": {}, "canonical_refs": [], "source_graph_digest": "x", "lazy": True,
        }
        self.assertFalse(self.result_for("INV-10")["passed"])

    def test_inv11_self_assessment_marked_independent(self):
        self.graph.add_node(
            "REVIEW_BAD", "Review",
            {"reviewer": "author_a", "claim_author": "author_a",
             "independent": True, "self_assessment": False},
            synthetic=True,
        )
        self.assertFalse(self.result_for("INV-11")["passed"])

    def test_inv12_stale_cache_entry(self):
        self.engine.propagate(
            self.graph, "R1",
            inputs={"x": {"value": 1.0, "sigma": 0.1}},
            coefficients=[1.0], method="delta", dependencies=["M1"],
        )
        self.graph.update_node("M1", {"value": 2.0}, merge=True)
        self.assertFalse(self.result_for("INV-12")["passed"])

    def test_inv13_draft_marked_validated(self):
        self.engine._traces["BAD"] = {
            "approximation_disclosed": True, "validated": True,
        }
        self.assertFalse(self.result_for("INV-13")["passed"])

    def test_inv14_universal_score_in_payload(self):
        self.graph.add_node("SCORE_BAD", "Claim",
                            {"overall_score": 0.95}, synthetic=True)
        self.assertFalse(self.result_for("INV-14")["passed"])

    def test_assert_invariants_raises_with_details(self):
        self.graph.add_node("SCORE_BAD", "Claim", {"trust_score": 0.9}, synthetic=True)
        with self.assertRaises(EpistemicContractError) as context:
            core.assert_invariants(**self.kwargs)
        self.assertIn("INV-14", str(context.exception))


class ManifestTests(unittest.TestCase):
    def test_manifest_declares_framework_not_evidence(self):
        manifest = core.epistemic_manifest()
        self.assertEqual(manifest["status"], "framework_core_before_ui")
        self.assertEqual(manifest["verified_sources"], 0)
        self.assertEqual(manifest["real_objects"], 0)
        self.assertEqual(manifest["live_adapters"], 0)
        self.assertEqual(manifest["promotable_claims"], 0)

    def test_manifest_counts(self):
        manifest = core.epistemic_manifest()
        self.assertEqual(len(manifest["axes"]), 6)
        self.assertEqual(len(manifest["passport_kinds"]), 10)
        self.assertEqual(len(manifest["machine_invariants"]), 14)
        self.assertEqual(len(manifest["acceptance_scenarios"]), 16)
        self.assertEqual(len(manifest["energy_channels"]), 10)

    def test_manifest_is_deterministic(self):
        self.assertEqual(core.epistemic_manifest(), core.epistemic_manifest())

    def test_honesty_assertion(self):
        self.assertTrue(core.assert_epistemic_honesty())

    def test_written_manifest_is_current_and_stable(self):
        path = os.path.join(HERE, "epistemic_manifest.json")
        first = core.write_epistemic_manifest(path)
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), first)
        second = core.write_epistemic_manifest(path)
        self.assertEqual(first, second)
        self.assertIn(EPISTEMIC_VERSION, first)

    def test_scenario_names_are_unique(self):
        self.assertEqual(len(ACCEPTANCE_SCENARIOS), len(set(ACCEPTANCE_SCENARIOS)))
        self.assertEqual(set(AXES), {
            "source_reliability", "measurement_uncertainty",
            "interpretation_confidence", "coverage_completeness",
            "model_validity", "evidence_connectivity",
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
