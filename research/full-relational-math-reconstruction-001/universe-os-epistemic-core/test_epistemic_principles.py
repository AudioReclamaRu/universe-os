"""Acceptance controls for Section 18 final formalisation.

Every principle has a machine-checkable consequence with at least one negative
control.  A structural pass is explicitly NOT physical confirmation.  The three
real cross-cases are declared not_evaluable: no primary sources are available.
"""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import epistemic_claims as ec  # noqa: E402
import epistemic_principles as ep  # noqa: E402
from epistemic_types import EpistemicContractError  # noqa: E402
from test_epistemic_core import DATE, primary_graph  # noqa: E402


def result_for(graph, check_name):
    return next(r for r in ep.check_principles(graph)
                if r["name"].lower().replace(" ", "_").replace("-", "_") == check_name
                or r["name"] == check_name)


def by_id(graph, principle_id):
    return next(r for r in ep.check_principles(graph) if r["id"] == principle_id)


class MetaArchitectureTests(unittest.TestCase):
    def test_seven_representations_not_six(self):
        manifest = ep.principles_manifest()
        self.assertEqual(len(manifest["seven_representations"]), 7)
        names = [item["name"] for item in manifest["seven_representations"]]
        self.assertIn("AGENCY & ACTION GRAPH", names)
        self.assertIn("ONTOLOGY & SEMANTIC GRAPH", names)

    def test_meta_reasoning_is_cross_cutting_not_eighth_world(self):
        manifest = ep.principles_manifest()
        self.assertFalse(manifest["meta_reasoning"]["is_eighth_world"])
        self.assertTrue(manifest["meta_reasoning"]["must_be_versioned"])

    def test_one_core_with_shared_ids_versions_provenance(self):
        manifest = ep.principles_manifest()
        self.assertTrue(manifest["shared_core_ids"])
        self.assertTrue(manifest["shared_versions"])
        self.assertTrue(manifest["shared_provenance"])

    def test_reality_independence_is_commitment_not_fact_or_axiom(self):
        manifest = ep.principles_manifest()
        self.assertIn(manifest["reality_independence_status"],
                      ("methodological_commitment", "metaphysical_commitment"))
        self.assertTrue(manifest["model_to_world_bridge_required"])

    def test_every_principle_has_a_consequence(self):
        for item in ep.PRINCIPLES:
            self.assertTrue(item["statement"])
            self.assertTrue(item["machine_checkable_consequence"])
            self.assertTrue(item["check"])

    def test_manifest_is_deterministic_and_honest(self):
        self.assertEqual(ep.principles_manifest(), ep.principles_manifest())
        self.assertTrue(ep.assert_principle_manifest_honesty())
        self.assertEqual(len(ep.principles_digest()), 64)
        for value in ep.principles_manifest()["cross_cases"].values():
            self.assertTrue(value.startswith("not_evaluable"))

    def test_vacuous_results_are_marked_not_silently_green(self):
        graph = primary_graph()
        results = ep.check_principles(graph)
        self.assertEqual(len(results), 15)
        self.assertTrue(all(r["status"] == "vacuous" for r in results))
        self.assertTrue(all(r["passed"] for r in results))
        self.assertTrue(all(r["evidentiary_status"] == "not_evaluable" for r in results))
        with self.assertRaises(EpistemicContractError):
            ep.assert_principles(graph, require_evaluated=True)

    def test_paraconsistent_inference_engine_remains_not_implemented(self):
        manifest = ep.principles_manifest()
        self.assertEqual(manifest["inference_engine_status"], "not_implemented")
        self.assertTrue(any("paraconsistent" in item for item in manifest["not_implemented"]))
        self.assertTrue(ep.assert_principle_manifest_honesty())

    def test_four_evaluation_states_stay_distinct(self):
        graph = primary_graph()
        first = ep.check_principles(graph)[0]
        self.assertEqual(first["evaluation_status"], "not_exercised")
        ep.record_existence_grounding(
            graph, "C1", grounding="evidence", sources=["S1"], asserts_existence=True)
        pr01 = next(r for r in ep.check_principles(graph) if r["id"] == "PR-01")
        self.assertEqual(pr01["evaluation_status"], "synthetic_control_passed")
        self.assertEqual(pr01["evidentiary_status"], "not_evaluable")
        self.assertEqual(pr01["empirical_status"], "empirical_application_not_evaluable")
        self.assertEqual(len(ep.principles_manifest()["evaluation_states"]), 4)
        with self.assertRaises(EpistemicContractError):
            ep.assert_principles(graph, require_evaluated=True)


class PrincipleConsequenceTests(unittest.TestCase):
    def setUp(self):
        self.graph = primary_graph()

    def test_pr01_existence_requires_evidence(self):
        ep.record_existence_grounding(
            self.graph, "C1", grounding="evidence", sources=["S1"], asserts_existence=True)
        self.assertTrue(by_id(self.graph, "PR-01")["passed"])
        ep.record_existence_grounding(
            self.graph, "C2", grounding="graph_record", sources=[], asserts_existence=True)
        failed = by_id(self.graph, "PR-01")
        self.assertFalse(failed["passed"])
        self.assertTrue(any("graph_record" in d or "C2" in d for d in failed["details"]))
        # Direct injection bypassing the recorder must still be caught.
        self.graph.record_event("existence_grounding", {
            "claim_id": "C1", "grounding": "evidence",
            "sources": ["DOES_NOT_EXIST"], "asserts_existence": True,
        })
        injected = by_id(self.graph, "PR-01")
        self.assertFalse(injected["passed"])
        self.assertTrue(any("DOES_NOT_EXIST" in d for d in injected["details"]))

    def test_pr02_no_unearned_perspective_privilege(self):
        ep.record_perspective_comparison(self.graph, "E1", perspectives=[
            {"id": "frame_a", "conditions": {"frame": "A"}},
            {"id": "frame_b", "conditions": {"frame": "B"}},
        ])
        self.assertTrue(by_id(self.graph, "PR-02")["passed"])
        ep.record_perspective_comparison(
            self.graph, "E2", perspectives=[{"id": "only", "conditions": {}}])
        self.assertFalse(by_id(self.graph, "PR-02")["passed"])
        ep.record_perspective_comparison(
            self.graph, "E3", perspectives=[
                {"id": "a", "conditions": {"x": 1}}, {"id": "b", "conditions": {"x": 2}}],
            preferred="a")
        self.assertFalse(by_id(self.graph, "PR-02")["passed"])

    def test_pr03_observation_impact_requires_before_during_after(self):
        with self.assertRaises(EpistemicContractError):
            ep.record_observation_context(
                self.graph, "OBS1", conditions={"instrument": "synth"},
                impact="physical", system_states=["before"])
        ep.record_observation_context(
            self.graph, "OBS1", conditions={"instrument": "synth"},
            impact="physical", system_states=["before", "during", "after"])
        self.assertTrue(by_id(self.graph, "PR-03")["passed"])
        # A raw event with an incomplete state triple must be rejected too.
        self.graph.record_event("observation_context", {
            "observation_id": "OBS2", "conditions": {"instrument": "synth"},
            "impact": "physical", "system_states": ["before"],
        })
        self.assertFalse(by_id(self.graph, "PR-03")["passed"])

    def test_pr04_representation_is_not_the_entity(self):
        self.graph.add_node("REP_1", "Model", {"label": "digital twin"}, synthetic=True)
        ep.record_representation(self.graph, "REP_1", represents="E1")
        self.assertTrue(by_id(self.graph, "PR-04")["passed"])
        self.graph.add_node("E_REP_BAD", "Entity",
                            {"representation_of": "E1"}, synthetic=True)
        self.assertFalse(by_id(self.graph, "PR-04")["passed"])

    def test_pr05_transformation_set_frozen_before_test(self):
        ep.record_transformation_freeze(
            self.graph, "FREEZE_1", transforms=["invariant", "covariant"])
        ep.record_invariance_check(
            self.graph, "C1", transform_classes=["invariant", "covariant"],
            frozen_sequence=1, outcome="invariance_detected", freeze_token="FREEZE_1")
        self.assertTrue(by_id(self.graph, "PR-05")["passed"])
        with self.assertRaises(EpistemicContractError):
            ep.record_invariance_check(
                self.graph, "C1", transform_classes=["nonsense"],
                frozen_sequence=0, outcome="invariance_detected", freeze_token="FREEZE_1")
        # A sequence number alone is not a frozen set: the token must exist.
        self.graph.record_event("invariance_check", {
            "subject_id": "C1", "frozen_sequence": 0,
            "outcome": "invariance_detected", "freeze_token": "NEVER_RECORDED",
        })
        self.assertFalse(by_id(self.graph, "PR-05")["passed"])

    def test_pr06_unknown_never_becomes_false(self):
        self.graph.record_event("absence_inferred", {"subject": "S1"})
        failed = by_id(self.graph, "PR-06")
        self.assertFalse(failed["passed"])
        self.assertTrue(any("absence" in d for d in failed["details"]))

    def test_pr07_green_test_is_not_physical_confirmation(self):
        for kind in ep.SELF_APPLICATION_KINDS:
            ep.record_system_state(
                self.graph, kind, description="synthetic",
                artifact_ref=f"ce5c38b::{kind}")
        self.assertTrue(by_id(self.graph, "PR-07")["passed"])
        self.graph.record_event("system_self_state", {
            "kind": "system_limitation", "description": "unbound state",
        })
        self.assertFalse(by_id(self.graph, "PR-07")["passed"])
        ep.record_green_test(self.graph, "T1", physical_confirmation=True)
        self.assertFalse(by_id(self.graph, "PR-07")["passed"])

    def test_pr08_trace_survival_filters(self):
        ep.record_trace_filters(
            self.graph, "S1", stages=list(ep.TRACE_REQUIRED_STAGES))
        self.assertTrue(by_id(self.graph, "PR-08")["passed"])
        ep.record_trace_filters(self.graph, "S2", stages=["detection"],
                                absence_inferred_from_no_trace=True)
        self.assertFalse(by_id(self.graph, "PR-08")["passed"])

    def test_pr09_classification_change_keeps_identity(self):
        self.graph.add_node(
            "ENT1", "Entity", {"label": "synthetic physical object"}, synthetic=True)
        ec.supersede_claim(self.graph, "C1", statement="reclassified synthetic claim")
        revision_id = self.graph.events("claim_revised")[-1]["event_id"]
        ep.record_classification_change(
            self.graph, "ENT1", claim_id="C1", claim_revision_event=revision_id,
            old_class="X", new_class="Y")
        self.assertTrue(by_id(self.graph, "PR-09")["passed"])
        # Classification without a revision belonging to this claim is rejected,
        # including when injected directly into the graph.
        self.graph.record_event("classification_changed", {
            "entity_id": "ENT1", "claim_id": "C1",
            "claim_revision_event": "V000001", "new_class": "Z",
            "physical_identity_unchanged": True,
        })
        self.assertFalse(by_id(self.graph, "PR-09")["passed"])

    def test_pr10_concept_evolution_is_not_reality_evolution(self):
        ep.record_concept_evolution(
            self.graph, "ether", to_concept="em_field", relation="replaced_by")
        self.assertTrue(by_id(self.graph, "PR-10")["passed"])
        with self.assertRaises(EpistemicContractError):
            ep.record_concept_evolution(
                self.graph, "a", to_concept="b", relation="connected_to")

    def test_pr11_conflict_does_not_explode_the_graph(self):
        ec.create_claim(
            self.graph, "C2", statement="rival", subject="X", predicate="v",
            object_value=2, scope={"epoch": "synthetic"}, epistemic_type="inferred",
            sources=["S2"], author="b", created_at=DATE, synthetic=True,
        )
        ec.ConflictRegistry().open(
            self.graph, "K1", ["C1", "C2"], divergence_type="interpretation",
            comparability={}, synthetic=True,
        )
        ep.record_inference_isolation(
            self.graph, "K1", engine="synthetic_paraconsistent_engine_v1")
        self.assertTrue(by_id(self.graph, "PR-11")["passed"])
        self.graph.record_event("conflict_propagation",
                                {"conflict_id": "K1", "target": "INDEPENDENT_CLAIM"})
        self.assertFalse(by_id(self.graph, "PR-11")["passed"])
        self.graph.record_event("conflict_propagation",
                                {"conflict_id": "K1", "target": "C1"})
        # A registered propagation still needs the isolation contract.
        self.graph.record_event("inference_isolation", {
            "conflict_id": "K1", "engine": "", "isolated": True,
        })
        self.assertFalse(by_id(self.graph, "PR-11")["passed"])

    def test_pr12_valid_time_and_transaction_time_are_distinct(self):
        ep.record_bitemporal(
            self.graph, "C1", valid_time="100000000 BCE",
            transaction_time="2026-11-24")
        self.assertTrue(by_id(self.graph, "PR-12")["passed"])
        self.graph.record_event("bitemporal_recorded", {
            "claim_id": "C2", "valid_time": "x", "transaction_time": "y",
            "axes_are_distinct": False,
        })
        self.assertFalse(by_id(self.graph, "PR-12")["passed"])

    def test_pr13_computation_is_replayable_and_distinguished(self):
        ep.record_computational_experiment(
            self.graph, "EXP1", distinction="computational_experiment",
            code_version="1.0.0", environment="python3.12", dependencies={"numpy": "1.26"},
            input_checksums={"in.csv": "abc"}, parameters={"n": 10},
            algorithm_version="delta_v1", solver_settings={"tol": 1e-9},
            convergence={"residual": 1e-10}, discretization_error={"dx": 0.01},
            outputs={"out.csv": "def"}, replayable=True,
        )
        self.assertTrue(by_id(self.graph, "PR-13")["passed"])
        with self.assertRaises(EpistemicContractError):
            ep.record_computational_experiment(
                self.graph, "EXP2", distinction="real_object", code_version="1")
        # Every key can be present while replayability is explicitly false.
        payload = {
            "experiment_id": "EXP_BAD", "distinction": "synthetic",
            "code_version": "1", "environment": "python", "dependencies": {},
            "input_checksums": {}, "parameters": {}, "algorithm_version": "v1",
            "solver_settings": {}, "convergence": {}, "discretization_error": {},
            "outputs": {}, "replayable": False,
        }
        self.graph.record_event("computational_experiment", payload)
        failed = by_id(self.graph, "PR-13")
        self.assertFalse(failed["passed"])
        self.assertTrue(any("replayable" in d for d in failed["details"]))

    def test_pr14_future_option_value_is_not_one_number(self):
        ep.record_intervention(self.graph, "I1", option_value={
            "lost_future_methods": ["method_not_yet_invented"],
            "irreversibility": "physical", "physical_damage": "sample_removed",
            "original_state_loss": "structure_destroyed",
            "legal_cultural_limits": ["heritage_permit_required"],
        })
        self.assertTrue(by_id(self.graph, "PR-14")["passed"])
        with self.assertRaises(EpistemicContractError):
            ep.record_intervention(self.graph, "I2", option_value=0.7)
        # Keys present with empty content are still not a structural option value.
        self.graph.record_event("intervention_evaluated", {
            "intervention_id": "I_BAD",
            "option_value": {field: "" for field in ep.OPTION_VALUE_FIELDS},
        })
        failed = by_id(self.graph, "PR-14")
        self.assertFalse(failed["passed"])
        self.assertTrue(any("empty" in d for d in failed["details"]))

    def test_pr15_system_can_declare_ontology_insufficient(self):
        ep.declare_ontology_insufficient(
            self.graph, "PHENOMENON_1",
            reason="new_phenomenon_outside_classes", raw_data_refs=["S1"],
            proposed_extension={"checks": list(ep.EXTENSION_CHECKS), "status": "proposed"},
        )
        self.assertTrue(by_id(self.graph, "PR-15")["passed"])
        self.graph.record_event("ontology_insufficient", {
            "subject_id": "PHENOMENON_2", "status": ep.ONTOLOGY_INSUFFICIENT,
            "reason": "definitions_conflict", "raw_data_preserved": False,
            "forced_classification": True,
        })
        failed = by_id(self.graph, "PR-15")
        self.assertFalse(failed["passed"])
        self.assertTrue(any("forced" in d or "raw data" in d for d in failed["details"]))

        # A genuine approval is a real, authorised, linked event with all four checks.
        self.graph.add_node("DEC1", "Decision", {
            "approved_by": "owner", "scope": "NEW_CLASS",
        }, synthetic=True)
        offset = len(self.graph.events())
        insufficiency_id = f"V{offset + 1:06d}"
        approval_id = f"V{offset + 2:06d}"
        ep.declare_ontology_insufficient(
            self.graph, "PHENOMENON_3", reason="relation_not_describable",
            raw_data_refs=["S1"], proposed_extension={
                "extension_id": "NEW_CLASS", "extension_version": 1,
                "checks": list(ep.EXTENSION_CHECKS), "status": "accepted",
                "approval_event": approval_id,
            },
        )
        approval = ep.record_ontology_approval(
            self.graph, "AP1", extension_id="NEW_CLASS", extension_version=1,
            approver="owner", authorization="DEC1", subject_id="PHENOMENON_3",
            insufficiency_event=insufficiency_id, checks=list(ep.EXTENSION_CHECKS),
        )
        self.assertEqual(approval["event_id"], approval_id)

        # A fabricated approval string, even with a full check list, is rejected.
        ep.declare_ontology_insufficient(
            self.graph, "PHENOMENON_4", reason="missing_required_dimension",
            raw_data_refs=["S1"], proposed_extension={
                "extension_id": "FAKE_CLASS", "extension_version": 1,
                "checks": list(ep.EXTENSION_CHECKS), "status": "accepted",
                "approval_event": "V999999",
            },
        )
        forged = by_id(self.graph, "PR-15")
        self.assertFalse(forged["passed"])
        self.assertTrue(any("approval" in d for d in forged["details"]))

    def test_assert_principles_reports_violations(self):
        ep.record_green_test(self.graph, "T1", physical_confirmation=True)
        with self.assertRaises(EpistemicContractError) as context:
            ep.assert_principles(self.graph)
        self.assertIn("PR-07", str(context.exception))

    def test_all_fifteen_principles_have_distinct_machine_checks(self):
        ids = [p["id"] for p in ep.PRINCIPLES]
        self.assertEqual(len(ids), 15)
        self.assertEqual(len(set(ids)), 15)
        self.assertEqual(len(ep.PRINCIPLE_CHECKS), 15)
        self.assertEqual(len(set(ep.PRINCIPLE_CHECKS)), 15)


class FacadeIntegrationTests(unittest.TestCase):
    def test_facade_exposes_principles(self):
        import epistemic_core as core

        graph = primary_graph()
        results = core.check_principles(graph)
        self.assertEqual(len(results), 15)
        self.assertTrue(all(r["evidentiary_status"] == "not_evaluable" for r in results))
        self.assertTrue(core.assert_principles(graph))
        self.assertTrue(core.assert_principles_honesty())

    def test_manifest_includes_seven_representations_and_principles(self):
        import epistemic_core as core

        manifest = core.epistemic_manifest()
        self.assertEqual(len(manifest["seven_representations"]), 7)
        self.assertEqual(manifest["machine_checkable_consequence_count"], 15)
        self.assertIn("AGENCY & ACTION GRAPH",
                      [r["name"] for r in manifest["seven_representations"]])
        self.assertTrue(manifest["guards"]["observer_non_privilege"])
        self.assertTrue(core.assert_epistemic_honesty())
        self.assertEqual(core.epistemic_manifest(), core.epistemic_manifest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
