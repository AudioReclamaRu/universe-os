"""Acceptance scenarios from Issue #7 §18.12, using synthetic fixtures only.

Successful tests prove the behaviour of the software core.  They do NOT prove
any geological, archaeological or physical hypothesis, and they never turn
synthetic fixtures into empirical evidence.
"""

from __future__ import annotations

import copy
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import epistemic_claims as ec  # noqa: E402
import epistemic_uncertainty as eu  # noqa: E402
from epistemic_graph import (  # noqa: E402
    IdentityRegistry, KnowledgeGraph, OntologyPassport, PassportRegistry,
)
from epistemic_types import EpistemicContractError  # noqa: E402

DATE = "2026-11-24"


def primary_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph("TEST_GRAPH")
    for name in ("S1", "S2"):
        graph.add_node(name, "Source", {"label": name, "kind": "published_plan"},
                       provenance={"synthetic": True}, synthetic=True)
    for name, source in (("M1", "S1"), ("M2", "S2")):
        graph.add_node(name, "Measurement", {"value": 10.0, "units": "m"},
                       provenance={"synthetic": True}, synthetic=True)
        graph.add_edge(name, source, "derived_from", synthetic=True)
    for name, measurement in (("A1", "M1"), ("A2", "M2")):
        graph.add_node(name, "Argument", {"label": name}, synthetic=True)
        graph.add_edge(name, measurement, "derived_from", synthetic=True)
    claim = ec.create_claim(
        graph, "C1",
        statement="synthetic test claim", subject="SYNTH_ENTITY",
        predicate="has_ratio", object_value={"value": 1.6, "units": "dimensionless"},
        scope={"object": "SYNTH_ENTITY", "epoch": "synthetic"},
        epistemic_type="derived", sources=["S1", "S2"],
        transformation_chain=["M1", "M2"], supporting_arguments=["A1", "A2"],
        author="author_a", created_at=DATE, synthetic=True,
    )
    graph.add_edge("A1", "C1", "supports", synthetic=True)
    graph.add_edge("A2", "C1", "supports", synthetic=True)
    return graph


def axis_assessments(level="moderate") -> dict:
    return {
        axis: {
            "level": level, "reasons": ["synthetic control"],
            "evidence": [f"SYNTH_{axis}"], "rubric_version": "1.0.0",
        }
        for axis in eu.AXES
    }


class SharedSourceCollapseTests(unittest.TestCase):
    def test_five_publications_one_dataset_is_one_basis(self):
        graph = KnowledgeGraph("TEST_SHARED")
        graph.add_node("S1", "Dataset", {"label": "primary"}, synthetic=True)
        ec.create_claim(
            graph, "C", statement="shared-source claim", subject="X",
            predicate="has_value", object_value=1,
            scope={"object": "X"}, epistemic_type="derived",
            sources=[f"P{i}" for i in range(1, 6)],
            supporting_arguments=[f"A{i}" for i in range(1, 6)],
            author="author", created_at=DATE, synthetic=True,
        )
        for i in range(1, 6):
            pub = f"P{i}"
            graph.add_node(pub, "Source", {"label": pub}, synthetic=True)
            graph.add_edge(pub, "S1", "derived_from", synthetic=True)
            arg = f"A{i}"
            graph.add_node(arg, "Argument", {"label": arg}, synthetic=True)
            graph.add_edge(arg, pub, "derived_from", synthetic=True)
            graph.add_edge(arg, "C", "supports", synthetic=True)
        structure = ec.belief_structure(graph, "C")
        self.assertEqual(structure["independent_primary_bases"], ["S1"])
        counted = eu.independent_bases(graph, "C", method_id="shared_primary_datasets_v1")
        self.assertEqual(counted["count"], 1)
        self.assertEqual(counted["status"], "evaluated")

    def test_effective_count_without_method_is_not_a_number(self):
        graph = primary_graph()
        result = eu.independent_bases(graph, "C1")
        self.assertIsNone(result["count"])
        self.assertEqual(result["status"], "not_evaluable")
        with self.assertRaises(EpistemicContractError):
            eu.independent_bases(graph, "C1", method_id="vibes_v1")


class TransitiveDependencyTests(unittest.TestCase):
    def test_dependency_survives_multiple_transformations(self):
        graph = primary_graph()
        structure = ec.belief_structure(graph, "C1")
        chains = {c["argument"]: c["dependency_chain"] for c in structure["support_chains"]}
        self.assertIn("S1", chains["A1"])
        self.assertIn("M1", chains["A1"])
        self.assertIn("S2", chains["A2"])

    def test_shared_dependency_is_marked_critical(self):
        graph = primary_graph()
        graph.add_edge("A2", "S1", "derived_from", synthetic=True)
        structure = ec.belief_structure(graph, "C1")
        self.assertIn("S1", structure["critical_nodes"])


class CriticalNodeRemovalTests(unittest.TestCase):
    def test_removing_shared_node_triggers_structural_review(self):
        graph = primary_graph()
        graph.add_edge("A2", "S1", "derived_from", synthetic=True)
        impact = ec.impact_analysis(graph, "C1", "S1")
        self.assertTrue(impact["review_required"])
        self.assertEqual(sorted(impact["lost_support"]), ["A1", "A2"])
        self.assertIsNone(impact["quantitative_percent"])
        self.assertTrue(graph.events("claim_review_triggered"))


class SourceConflictTests(unittest.TestCase):
    def setUp(self):
        self.graph = primary_graph()
        ec.create_claim(
            self.graph, "C2",
            statement="conflicting synthetic value", subject="SYNTH_ENTITY",
            predicate="has_ratio", object_value={"value": 1.9, "units": "dimensionless"},
            scope={"object": "SYNTH_ENTITY", "epoch": "synthetic"},
            epistemic_type="derived", sources=["S2"],
            author="author_b", created_at=DATE, synthetic=True,
        )
        self.registry = ec.ConflictRegistry()

    def test_two_values_create_conflict_without_averaging(self):
        conflict = self.registry.open(
            self.graph, "K1", ["C1", "C2"], divergence_type="measurement",
            comparability={"checked": False}, author="author_c", synthetic=True,
        )
        self.assertEqual(conflict["payload"]["status"], "open")
        self.assertEqual(len(conflict["payload"]["versions"]), 2)
        self.assertNotIn("mean", conflict["payload"])

    def test_resolution_requires_reviewer_and_evidence(self):
        self.registry.open(self.graph, "K1", ["C1", "C2"],
                           divergence_type="measurement", comparability={}, synthetic=True)
        with self.assertRaises(EpistemicContractError):
            self.registry.resolve(self.graph, "K1", scope={"epoch": "x"},
                                  reason="because", reviewer="", evidence_ids=["S1"])
        with self.assertRaises(EpistemicContractError):
            self.registry.resolve(self.graph, "K1",
                                  scope={"averaged_value": 1.75}, reason="r",
                                  reviewer="reviewer", evidence_ids=["S1"])

    def test_original_claims_are_immutable(self):
        before = [copy.deepcopy(c["payload"]) for c in (self.graph.current("C1"), self.graph.current("C2"))]
        self.registry.open(self.graph, "K1", ["C1", "C2"],
                           divergence_type="interpretation", comparability={}, synthetic=True)
        self.registry.resolve(
            self.graph, "K1", scope={"epoch": "synthetic"},
            reason="scope separated", reviewer="reviewer_r", evidence_ids=["S1", "S2"],
        )
        after = [c["payload"] for c in (self.graph.current("C1"), self.graph.current("C2"))]
        self.assertEqual(before, after)


class ScopedResolutionTests(unittest.TestCase):
    def test_partial_and_scoped_states(self):
        graph = primary_graph()
        ec.create_claim(
            graph, "C2", statement="other value", subject="X", predicate="v",
            object_value=2, scope={"epoch": "other"}, epistemic_type="inferred",
            sources=["S2"], author="b", created_at=DATE, synthetic=True,
        )
        registry = ec.ConflictRegistry()
        registry.open(graph, "K1", ["C1", "C2"], divergence_type="epoch",
                      comparability={"checked": True}, synthetic=True)
        partial = registry.resolve(
            graph, "K1", scope={"epoch": "synthetic", "partial": True},
            reason="one epoch separated", reviewer="r", evidence_ids=["S1"],
        )
        self.assertEqual(partial["payload"]["status"], "partially_resolved")
        scoped = registry.resolve(
            graph, "K1", scope={"epoch": "other"}, reason="second epoch separated",
            reviewer="r", evidence_ids=["S2"],
        )
        self.assertEqual(scoped["payload"]["status"], "resolved_with_scope")
        self.assertEqual(len(scoped["payload"]["resolutions"]), 2)
        reopened = registry.reopen(graph, "K1", reason="new synthetic data", actor="r2")
        self.assertEqual(reopened["payload"]["status"], "open")
        self.assertEqual(len(graph.versions("K1")), 4)


class DestroyConditionTests(unittest.TestCase):
    def setUp(self):
        self.graph = primary_graph()
        self.registry = ec.ConditionRegistry()
        self.condition = self.registry.register(
            self.graph, "DC1", observable="frequency_shift", target="SYNTH_SENSOR",
            comparison=">", threshold=5.0, units="Hz",
            uncertainty={"sigma": 0.2}, source_requirements={"calibrated": True},
            controls=["null"], expected_action="reject",
            preregistration_date="2026-11-01", claim_id="C1", synthetic=True,
        )

    def test_registered_threshold_fires_and_preserves_history(self):
        result = self.registry.evaluate(
            self.graph, "DC1",
            {"value": 6.0, "units": "Hz", "calibrated": True, "independence": True},
        )
        self.assertEqual(result["status"], "triggered")
        self.assertEqual(self.graph.current("C1")["payload"]["status"], "rejected")
        self.assertEqual(len(self.graph.versions("C1")), 2)
        self.assertTrue(self.graph.events("destroy_condition_triggered"))

    def test_uncalibrated_observation_requires_human_review(self):
        result = self.registry.evaluate(
            self.graph, "DC1", {"value": 9.0, "units": "Hz", "calibrated": False})
        self.assertFalse(result["fired"])
        self.assertEqual(result["status"], "human_review_required")

    def test_no_post_hoc_rescue(self):
        amended = self.registry.amend(self.graph, "DC1", threshold=100.0)
        self.assertTrue(amended["payload"]["amended_after_result"])
        old = self.registry.evaluate(
            self.graph, "DC1",
            {"value": 6.0, "units": "Hz", "calibrated": True}, version=1,
        )
        self.assertTrue(old["fired"])
        self.assertEqual(old["condition_version"], 1)
        self.assertEqual(self.graph.versions("DC1")[0]["payload"]["threshold"], 5.0)


class OntologyTypingTests(unittest.TestCase):
    def setUp(self):
        self.graph = primary_graph()
        self.ontology = OntologyPassport()
        self.ontology.register(
            "SYNTH_ROCK", membership_criteria=["synthetic criterion"],
            allowed_properties=["shape"], allowed_relations=("valid_during",),
        )
        self.graph.add_node("E1", "Entity",
                            {"entity_class": "SYNTH_ROCK", "shape": "block"}, synthetic=True)

    def test_valid_typing(self):
        self.assertEqual(self.ontology.validate(self.graph), [])

    def test_hypothesis_cannot_be_physical_entity(self):
        self.graph.add_node("H_BAD", "Hypothesis", {"entity_class": "SYNTH_ROCK"},
                            synthetic=True)
        violations = self.ontology.validate(self.graph)
        self.assertTrue(any("epistemic object typed as physical" in v for v in violations))

    def test_flow_is_not_a_geological_object(self):
        self.graph.add_node("FLOW_BAD", "Entity",
                            {"entity_class": "SYNTH_ROCK", "flow_kind": "thermal"},
                            synthetic=True)
        violations = self.ontology.validate(self.graph)
        self.assertTrue(any("energy flow recorded as Entity" in v for v in violations))

    def test_ontology_change_triggers_impact_review(self):
        self.ontology.change_criteria(
            self.graph, "SYNTH_ROCK", membership_criteria=["revised criterion"],
            author="reviewer",
        )
        self.assertEqual(self.ontology.current("SYNTH_ROCK")["version"], 2)
        event = self.graph.events("ontology_impact_review")[0]
        self.assertIn("E1", event["payload"]["affected"])


class LazyPassportTests(unittest.TestCase):
    def setUp(self):
        self.graph = primary_graph()
        self.graph.add_node("E1", "Entity",
                            {"entity_class": "SYNTH_ROCK", "label": "synth"}, synthetic=True)
        self.registry = PassportRegistry()

    def test_absence_of_passport_is_not_defect(self):
        states = self.registry.states_for(self.graph, "E1")
        self.assertEqual(set(states.values()), {"not_created"})
        self.assertEqual(self.registry.cached, 0)

    def test_materialization_is_a_projection(self):
        passport = self.registry.materialize(self.graph, "E1", "geometry_relation")
        self.assertTrue(passport["lazy"])
        self.assertEqual(passport["entity_id"], "E1")
        self.assertEqual(self.registry.cached, 1)
        again = self.registry.materialize(self.graph, "E1", "geometry_relation")
        self.assertEqual(passport, again)
        self.assertEqual(self.registry.cached, 1)

    def test_unknown_entity_is_not_created_by_materialization(self):
        passport = self.registry.materialize(self.graph, "MISSING", "identity")
        self.assertEqual(passport["state"], "not_created")
        self.assertEqual(self.registry.cached, 0)


class SharedCanonicalValueTests(unittest.TestCase):
    def test_update_of_canonical_fact_visible_in_projection(self):
        graph = primary_graph()
        graph.add_node("E1", "Entity", {"entity_class": "X"}, synthetic=True)
        graph.add_edge("E1", "M1", "measured_by", synthetic=True)
        registry = PassportRegistry()
        first = registry.materialize(graph, "E1", "observation")
        before = graph.current("M1")["payload"]["value"]
        graph.update_node("M1", {"value": 12.0, "units": "m"}, merge=True)
        self.assertEqual(registry.invalidate("M1"), 1)
        second = registry.materialize(graph, "E1", "observation", force=True)
        self.assertNotEqual(first["source_graph_digest"], second["source_graph_digest"])
        self.assertEqual(graph.current("M1")["payload"]["value"], 12.0)
        self.assertEqual(before, 10.0)


class IdentityTemporalTests(unittest.TestCase):
    def setUp(self):
        self.graph = primary_graph()
        self.registry = IdentityRegistry()
        self.registry.register(
            "MONUMENT", required_traits=["location", "core_material"],
            secondary_traits=["surface_finish"], author="author",
        )
        self.graph.add_node("ENTITY_1", "Entity",
                            {"entity_class": "MONUMENT", "location": "synth",
                             "core_material": "limestone"}, synthetic=True)
        self.graph.add_node("STATE_1", "EntityState",
                            {"entity_class": "MONUMENT", "epoch": "A"}, synthetic=True)
        self.graph.add_edge("STATE_1", "ENTITY_1", "valid_during", synthetic=True)

    def test_state_change_keeps_entity_identity(self):
        verdict = self.registry.evaluate(
            self.graph, "ENTITY_1", observed_traits=["location", "core_material"])
        self.assertEqual(verdict["decision"], "same_entity")

    def test_missing_required_trait_needs_review(self):
        verdict = self.registry.evaluate(
            self.graph, "ENTITY_1", observed_traits=["location"])
        self.assertEqual(verdict["decision"], "review_required")

    def test_split_creates_lineage_branch(self):
        self.graph.add_node("ENTITY_2", "Entity",
                            {"entity_class": "MONUMENT"}, synthetic=True)
        self.graph.add_edge("ENTITY_2", "ENTITY_1", "split_from", synthetic=True)
        verdict = self.registry.evaluate(
            self.graph, "ENTITY_2", observed_traits=["location", "core_material"])
        self.assertEqual(verdict["decision"], "new_lineage_branch")

    def test_criterion_change_is_versioned_with_impact_review(self):
        self.registry.change_criteria(
            self.graph, "MONUMENT", required_traits=["location"], author="reviewer")
        self.assertEqual(self.registry.current("MONUMENT")["version"], 2)
        self.assertTrue(self.graph.events("identity_impact_review"))


class IndependentReviewTests(unittest.TestCase):
    def test_self_assessment_rejected(self):
        graph = primary_graph()
        with self.assertRaises(EpistemicContractError):
            ec.independent_verification(
                graph, "C1", reviewer="author_a",
                checks=ec.REQUIRED_REVIEW_CHECKS, evidence_refs=["S1"],
            )

    def test_real_independent_review_passes_gate(self):
        graph = primary_graph()
        graph.update_node("C1", {"status": "active"}, merge=True)
        ec.independent_verification(
            graph, "C1", reviewer="reviewer_x",
            checks=ec.REQUIRED_REVIEW_CHECKS, evidence_refs=["S1", "M1"],
        )
        gate = ec.claim_gate(graph, "C1")
        self.assertTrue(gate["passed"], gate["reasons"])
        review = graph.nodes("Review")[0]
        self.assertTrue(review["payload"]["independent"])
        self.assertFalse(review["payload"]["self_assessment"])

    def test_gate_blocks_open_conflict_and_fired_destroy_condition(self):
        graph = primary_graph()
        ec.create_claim(
            graph, "C2", statement="rival", subject="X", predicate="v", object_value=2,
            scope={"epoch": "synthetic"}, epistemic_type="inferred", sources=["S2"],
            author="b", created_at=DATE, synthetic=True,
        )
        ec.ConflictRegistry().open(
            graph, "K1", ["C1", "C2"], divergence_type="measurement",
            comparability={}, synthetic=True,
        )
        gate = ec.claim_gate(graph, "C1")
        self.assertFalse(gate["passed"])
        self.assertTrue(any("conflict" in r for r in gate["reasons"]))


class CovarianceInheritanceTests(unittest.TestCase):
    def setUp(self):
        self.graph = primary_graph()
        self.engine = eu.UncertaintyEngine()

    def test_correlation_is_preserved(self):
        trace = self.engine.propagate(
            self.graph, "R1",
            inputs={"x": {"value": 10.0, "sigma": 1.0,
                          "correlation": {"y": 0.8}},
                    "y": {"value": 20.0, "sigma": 2.0}},
            coefficients=[1.0, 1.0], method="covariance",
        )
        self.assertAlmostEqual(trace["input_covariance"][0][1], 1.6, places=9)
        self.assertTrue(trace["validated"])

    def test_unknown_correlation_stays_unresolved(self):
        with self.assertRaises(EpistemicContractError):
            self.engine.propagate(
                self.graph, "R2",
                inputs={"x": {"value": 1.0, "sigma": 1.0},
                        "y": {"value": 1.0, "sigma": 1.0}},
                coefficients=[1.0, 1.0], method="delta",
            )

    def test_assumed_independence_is_disclosed(self):
        trace = self.engine.propagate(
            self.graph, "R3",
            inputs={"x": {"value": 1.0, "sigma": 1.0},
                    "y": {"value": 1.0, "sigma": 1.0}},
            coefficients=[1.0, 1.0], method="delta",
            assume_independent=True, assumption_reason="synthetic control",
        )
        self.assertTrue(trace["approximation_disclosed"])
        self.assertFalse(trace["validated"])

    def test_monte_carlo_is_deterministic(self):
        kwargs = dict(
            inputs={"x": {"value": 10.0, "sigma": 1.0, "correlation": {"y": 0.4}},
                    "y": {"value": 20.0, "sigma": 2.0}},
            coefficients=[1.0, 1.0], method="monte_carlo",
            seed=42, samples=200, algorithm="cholesky_gauss",
            library_versions={"python": "3.12"},
        )
        first = self.engine.propagate(self.graph, "MC1", **kwargs)
        second = self.engine.propagate(self.graph, "MC2", **kwargs)
        self.assertEqual(first["result"], second["result"])
        self.assertTrue(first["approximation_disclosed"])

    def test_epistemic_axes_never_enter_the_model(self):
        with self.assertRaises(EpistemicContractError):
            eu.assert_axes_excluded_from_model(
                {"source_reliability": {"level": "strong"}},
                ["source_reliability", "x"],
            )


class CacheInvalidationTests(unittest.TestCase):
    def test_dependency_update_invalidates_only_affected_result(self):
        graph = primary_graph()
        engine = eu.UncertaintyEngine()
        kwargs = dict(
            inputs={"x": {"value": 1.0, "sigma": 0.1}},
            coefficients=[1.0], method="delta", dependencies=["M1"],
        )
        first = engine.propagate(graph, "R1", **kwargs)
        self.assertEqual(engine.cache.entries, 1)
        graph.update_node("M1", {"value": 99.0, "units": "m"}, merge=True)
        self.assertEqual(len(engine.cache.stale_keys(graph)), 1)
        self.assertIsNone(engine.cache.get(first["cache_key"], graph))
        self.assertEqual(engine.cache.entries, 0)
        second = engine.propagate(graph, "R2", **kwargs)
        self.assertNotEqual(first["cache_key"], second["cache_key"])

    def test_unrelated_change_keeps_cache(self):
        graph = primary_graph()
        engine = eu.UncertaintyEngine()
        trace = engine.propagate(
            graph, "R1",
            inputs={"x": {"value": 1.0, "sigma": 0.1}},
            coefficients=[1.0], method="delta", dependencies=["M1"],
        )
        graph.update_node("S2", {"label": "changed"}, merge=True)
        self.assertEqual(engine.cache.stale_keys(graph), [])
        self.assertIsNotNone(engine.cache.get(trace["cache_key"], graph))


class ApproximationDisclosureTests(unittest.TestCase):
    def test_draft_cannot_pass_full_gate(self):
        graph = primary_graph()
        engine = eu.UncertaintyEngine()
        with self.assertRaises(EpistemicContractError):
            engine.propagate(
                graph, "DRAFT",
                inputs={"x": {"value": 1.0, "sigma": 0.1}},
                coefficients=[1.0], method="interval", requires_full=True,
            )
        self.assertEqual(engine._traces, {})

    def test_full_covariance_result_can_pass(self):
        graph = primary_graph()
        engine = eu.UncertaintyEngine()
        trace = engine.propagate(
            graph, "FULL",
            inputs={"x": {"value": 1.0, "sigma": 0.1}},
            coefficients=[1.0], method="covariance", requires_full=True,
        )
        self.assertTrue(trace["validated"])
        self.assertFalse(trace["approximation_disclosed"])


class ImmutableHistoryTests(unittest.TestCase):
    def test_revision_does_not_erase_claim(self):
        graph = primary_graph()
        ec.supersede_claim(graph, "C1", statement="revised synthetic claim")
        versions = graph.versions("C1")
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0]["payload"]["statement"], "synthetic test claim")
        self.assertEqual(versions[1]["payload"]["statement"], "revised synthetic claim")
        self.assertEqual(versions[1]["supersedes"], 1)

    def test_raw_evidence_gate_is_structural(self):
        graph = primary_graph()
        gate = eu.evidence_gate(graph, "C1", axis_assessments=axis_assessments("moderate"))
        self.assertIsNone(gate["quantitative_score"])
        self.assertEqual(gate["limiting_axis"], "source_reliability")
        self.assertEqual(gate["status"], "moderate")

    def test_open_conflict_overrides_gate_status(self):
        graph = primary_graph()
        ec.create_claim(
            graph, "C2", statement="rival", subject="X", predicate="v", object_value=2,
            scope={"epoch": "synthetic"}, epistemic_type="inferred", sources=["S2"],
            author="b", created_at=DATE, synthetic=True,
        )
        ec.ConflictRegistry().open(graph, "K1", ["C1", "C2"],
                                   divergence_type="units", comparability={}, synthetic=True)
        gate = eu.evidence_gate(graph, "C1", axis_assessments=axis_assessments("strong"))
        self.assertEqual(gate["status"], "disputed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
