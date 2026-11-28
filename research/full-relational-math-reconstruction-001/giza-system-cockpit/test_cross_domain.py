"""Controls for bidirectional GIZA <-> ASTRAEA validation and the three-world bridge.

No ASTRAEA adapter, live feed, trading runtime or GUI is used here.  These are
deterministic contract tests only.
"""

from __future__ import annotations

import copy
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cockpit_engine as ce  # noqa: E402
import cross_domain as xd  # noqa: E402


def valid_candidate(**overrides):
    candidate = {
        "candidate_id": "c_giza_astraea",
        "source_domain": "GIZA_PRIME",
        "target_domain": "ASTRAEA",
        "mode": "paper",
        "data_scope": "historical",
        "model_id": "MODEL_A",
        "invariant": {
            "kind": "dimensionless_ratio",
            "source_units": "Hz",
            "target_units": "count",
            "dimensionless": True,
            "conversion": None,
        },
        "mechanism_definition": "declared structural invariant, not a causal bridge",
        "alternative_explanations": ["common driver", "selection effect"],
        "null_models": ["phase-randomized surrogate"],
        "holdout_checked": True,
        "multiple_testing_checked": True,
        "falsifier": "predefined negative control fails",
        "uncertainty": {"interval": [0.0, 1.0]},
        "evidence_status": "inferred",
        "permissions": {"access": "public", "licence": "project"},
        "claim": "candidate",
        "auto_trade": False,
        "verified_giza_data": True,
        "synthetic_fixture": False,
        "target_check": {
            "run": True,
            "stages_passed": list(xd.STAGES),
            "result": "candidate",
        },
    }
    candidate.update(overrides)
    return candidate


def reverse_candidate(**overrides):
    candidate = valid_candidate(
        candidate_id="c_astraea_giza",
        source_domain="ASTRAEA",
        target_domain="GIZA_PRIME",
        invariant={
            "kind": "rank_order",
            "source_units": "ratio",
            "target_units": "m",
            "dimensionless": True,
            "conversion": None,
        },
    )
    candidate.update(overrides)
    return candidate


class ProtocolTests(unittest.TestCase):
    def test_manifest_is_paper_historical_only(self):
        manifest = xd.cross_domain_manifest()
        self.assertEqual(manifest["mode"], "paper")
        self.assertEqual(manifest["data_scope"], "historical")
        self.assertTrue(manifest["live_feed_forbidden"])
        self.assertTrue(manifest["auto_trade_forbidden"])
        self.assertEqual(manifest["verified_giza_sources"], 0)
        self.assertEqual(manifest["astraea_adapter_status"], "not_implemented")
        self.assertEqual(manifest["promotable_candidates"], 0)

    def test_manifest_is_deterministic(self):
        self.assertEqual(xd.cross_domain_manifest(), xd.cross_domain_manifest())
        self.assertEqual(xd.synthetic_pair(), xd.synthetic_pair())

    def test_required_stages_are_defined(self):
        self.assertEqual(len(xd.STAGES), 11)
        self.assertIn("target_domain_checked", xd.STAGES)


class CandidateTests(unittest.TestCase):
    def test_valid_candidate_passes(self):
        self.assertTrue(xd.validate_candidate(valid_candidate()))

    def test_live_mode_forbidden(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(valid_candidate(mode="live"))

    def test_streaming_scope_forbidden(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(valid_candidate(data_scope="streaming"))

    def test_auto_trade_forbidden(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(valid_candidate(auto_trade=True))

    def test_same_domain_forbidden(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(valid_candidate(target_domain="GIZA_PRIME"))

    def test_unit_mixing_requires_dimensionless(self):
        candidate = valid_candidate(invariant={
            "kind": "dimensionless_ratio", "source_units": "m",
            "target_units": "bit", "dimensionless": False, "conversion": None,
        })
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(candidate)

    def test_unit_conversion_forbidden(self):
        candidate = valid_candidate(invariant={
            "kind": "dimensionless_ratio", "source_units": "Hz",
            "target_units": "count", "dimensionless": True,
            "conversion": "J/bit",
        })
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(candidate)

    def test_mechanism_required(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(valid_candidate(mechanism_definition=""))

    def test_two_alternatives_required(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(valid_candidate(alternative_explanations=["chance"]))

    def test_null_model_required(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(valid_candidate(null_models=[]))

    def test_falsifier_required(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(valid_candidate(falsifier=""))

    def test_unknown_evidence_status_forbidden(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(valid_candidate(evidence_status="proven_truth"))

    def test_duplicate_stage_forbidden(self):
        candidate = valid_candidate(target_check={
            "run": True,
            "stages_passed": list(xd.STAGES) + [xd.STAGES[0]],
            "result": "candidate",
        })
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_candidate(candidate)


class PairTests(unittest.TestCase):
    def test_full_pair_is_promotable(self):
        result = xd.validate_pair(valid_candidate(), reverse_candidate())
        self.assertTrue(result["promotable"])
        self.assertEqual(result["status"], "promotable_candidate")
        self.assertEqual(result["reasons"], [])

    def test_pair_must_have_both_directions(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_pair(valid_candidate(), valid_candidate(candidate_id="c2"))

    def test_pair_requires_same_model(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_pair(valid_candidate(), reverse_candidate(model_id="MODEL_B"))

    def test_pair_requires_distinct_ids(self):
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_pair(valid_candidate(), reverse_candidate(candidate_id="c_giza_astraea"))

    def test_missing_target_check_is_not_promotable(self):
        forward = valid_candidate(target_check={
            "run": False, "stages_passed": list(xd.STAGES),
            "result": None, "reason": "adapter not implemented",
        })
        result = xd.validate_pair(forward, reverse_candidate())
        self.assertFalse(result["promotable"])
        self.assertEqual(result["status"], "incomplete_bidirectional_check")

    def test_negative_result_is_valid_evidence_not_promotion(self):
        forward = valid_candidate(claim="negative", target_check={
            "run": True, "stages_passed": list(xd.STAGES), "result": "negative",
        })
        result = xd.validate_pair(forward, reverse_candidate())
        self.assertFalse(result["promotable"])
        self.assertEqual(result["status"], "negative_result")

    def test_synthetic_fixture_never_promotes(self):
        pair = xd.synthetic_pair()
        self.assertEqual(pair["assessment"]["status"], "incomplete_bidirectional_check")
        self.assertFalse(pair["assessment"]["promotable"])
        self.assertTrue(any("synthetic" in reason
                            for reason in pair["assessment"]["reasons"]))

    def test_missing_holdout_blocks_promotion(self):
        result = xd.validate_pair(
            valid_candidate(holdout_checked=False), reverse_candidate())
        self.assertFalse(result["promotable"])
        self.assertTrue(any("holdout" in r for r in result["reasons"]))


class BridgeTests(unittest.TestCase):
    def test_world_bridge_validates(self):
        self.assertTrue(xd.validate_bridge(xd.WORLD_BRIDGE))

    def test_three_worlds_are_distinct_markers(self):
        manifest = xd.tri_pyramid_manifest()
        worlds = manifest["world_bridge"]["world_records"]
        self.assertEqual({w["id"] for w in worlds},
                         {"BITCOIN", "UNIVERSE", "EARTH_EAR"})
        self.assertTrue(all(w["distinct_energy_marker"] for w in worlds))

    def test_megabrain_only_coordinates(self):
        orchestrator = xd.tri_pyramid_manifest()["orchestrator"]
        self.assertEqual(orchestrator["authority"], "coordination_only")
        self.assertFalse(orchestrator["autonomous_goal_change"])
        self.assertFalse(orchestrator["owns_scientific_claim"])

    def test_bridge_rejects_world_reduction(self):
        bridge = copy.deepcopy(xd.WORLD_BRIDGE)
        bridge["no_world_reduced_to_another"] = False
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_bridge(bridge)

    def test_bridge_rejects_energy_transfer_claim(self):
        bridge = copy.deepcopy(xd.WORLD_BRIDGE)
        bridge["physical_energy_transfer_claimed"] = True
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_bridge(bridge)

    def test_bridge_rejects_missing_world(self):
        bridge = copy.deepcopy(xd.WORLD_BRIDGE)
        bridge["world_records"] = bridge["world_records"][:2]
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_bridge(bridge)

    def test_bridge_rejects_unit_equivalence(self):
        bridge = copy.deepcopy(xd.WORLD_BRIDGE)
        bridge["unit_equivalence_claimed"] = True
        with self.assertRaises(ce.CockpitContractError):
            xd.validate_bridge(bridge)

    def test_tri_pyramid_manifest_is_deterministic(self):
        self.assertEqual(xd.tri_pyramid_manifest(), xd.tri_pyramid_manifest())

    def test_pyramids_have_expected_roles(self):
        roles = {p["id"]: p["role"] for p in xd.PYRAMIDS}
        self.assertEqual(roles, {
            "ASTRAEA": "sensor", "COMPARATOR": "mathematical_model",
            "NATURAL_PHYSICS": "reference_system",
        })


class ManifestIntegrationTests(unittest.TestCase):
    def test_cockpit_manifest_exposes_cross_domain_sections(self):
        manifest = ce.cockpit_manifest()
        self.assertEqual(manifest["cross_domain_validation"]["mode"], "paper")
        self.assertEqual(manifest["tri_pyramid_architecture"]["world_bridge"]["bridge_id"],
                         "LOGICAL_BRIDGE_THREE_WORLDS")
        self.assertFalse(manifest["cross_domain_demonstration"]["assessment"]["promotable"])

    def test_honesty_assertion_covers_bridge(self):
        self.assertTrue(ce.assert_cockpit_honesty())


if __name__ == "__main__":
    unittest.main(verbosity=2)
