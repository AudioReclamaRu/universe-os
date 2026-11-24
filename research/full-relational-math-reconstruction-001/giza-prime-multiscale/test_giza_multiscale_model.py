"""Software/physics controls for the GIZA PRIME idealized multiscale twin.

These tests validate software and dimensional/energy invariants of an IDEALIZED
synthetic fixture. Passing tests are NOT archaeological evidence and are NOT
evidence of any historical Giza function or Giza-cosmos communication.
"""

from __future__ import annotations

import cmath
import json
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import giza_multiscale_model as g  # noqa: E402


class ArtifactValidationTests(unittest.TestCase):
    def test_schema_file_declares_contract(self):
        schema = g.scenario_schema()
        self.assertEqual(schema["schema_version"], "1.0")
        self.assertTrue(schema["required_fields"])
        self.assertIn("example_file", schema)
        self.assertEqual(set(schema["layer_taxonomy"].keys()), {str(i) for i in range(1, 10)})

    def test_evidence_classes_exact(self):
        schema = g.scenario_schema()
        self.assertEqual(tuple(schema["evidence_classes"]), g.EVIDENCE_CLASSES)
        self.assertEqual(len(g.EVIDENCE_CLASSES), 9)
        self.assertIn("unknown", g.EVIDENCE_CLASSES)
        self.assertIn("speculative_hypothesis", g.EVIDENCE_CLASSES)

    def test_example_scenario_validates(self):
        scenario = g.load_json("example_scenario_synthetic.json")
        self.assertTrue(g.validate_scenario(scenario))
        self.assertTrue(scenario["synthetic"])
        self.assertFalse(scenario["outbound_communication_claim"])

    def test_scenario_requires_fields(self):
        scenario = g.make_scenario("S0_CURRENT_OBSERVED")
        scenario.pop("falsifiers")
        with self.assertRaises(g.ValidationError):
            g.validate_scenario(scenario)

    def test_scenario_rejects_unknown_evidence_class(self):
        scenario = g.make_scenario("S0_CURRENT_OBSERVED")
        scenario["evidence_basis"] = ["measured_fact_from_nowhere"]
        with self.assertRaises(g.ValidationError):
            g.validate_scenario(scenario)

    def test_scenario_rejects_unknown_hypothesis(self):
        scenario = g.make_scenario("S0_CURRENT_OBSERVED")
        scenario["enabled_hypotheses"] = ["H_UNCONTROLLED_MEGA_SCENARIO"]
        with self.assertRaises(g.ValidationError):
            g.validate_scenario(scenario)

    def test_scenario_rejects_cosmic_claim(self):
        scenario = g.make_scenario("S5_ENVIRONMENTAL_DRIVERS")
        scenario["outbound_communication_claim"] = True
        with self.assertRaises(g.ValidationError):
            g.validate_scenario(scenario)

    def test_scenario_rejects_two_hypotheses_at_once(self):
        scenario = g.make_scenario("S4_ELASTIC")
        scenario["enabled_hypotheses"] = ["H_ELASTIC_SUBSTRATE", "H_ACOUSTIC_CAVITY"]
        with self.assertRaises(g.ValidationError):
            g.validate_scenario(scenario)

    def test_source_register_has_no_sources(self):
        register = g.source_register()
        self.assertTrue(g.validate_source_register(register))
        self.assertEqual(register["sources"], [])
        self.assertFalse(register["external_citations_attached"])

    def test_source_register_rejects_fabricated_source(self):
        register = g.source_register()
        register["sources"] = [{"citation": "invented paper"}]
        with self.assertRaises(g.ValidationError):
            g.validate_source_register(register)

    def test_parameter_registry_all_records_complete(self):
        registry = g.parameter_registry()
        self.assertTrue(g.validate_parameter_registry(registry))
        self.assertTrue(registry["parameters"])
        for record in registry["parameters"]:
            self.assertEqual(record["source_id"], "synthetic_reference_fixture")
            self.assertIn("No external citation attached", record["source_detail"])

    def test_parameter_registry_unknown_values_null(self):
        registry = g.parameter_registry()
        unresolved = [p for p in registry["parameters"] if p["value"] is None]
        self.assertTrue(unresolved)
        self.assertTrue(all(p["evidence_class"] == "unknown" for p in unresolved))
        self.assertTrue(all(p["activated"] is False for p in unresolved))
        self.assertTrue(all(p["discriminating_measurement"] for p in unresolved))

    def test_parameter_registry_rejects_null_without_unknown(self):
        registry = json.loads(json.dumps(g.parameter_registry()))
        registry["parameters"][0]["value"] = None
        with self.assertRaises(g.ValidationError):
            g.validate_parameter_registry(registry)

    def test_bridge_catalog_has_all_b4_fields(self):
        catalog = g.bridge_catalog()
        self.assertTrue(g.validate_bridge_catalog(catalog))
        for record in catalog["bridges"]:
            for key in g.BRIDGE_REQUIRED_FIELDS:
                self.assertIn(key, record)
            self.assertTrue(record["propagation_path"])
            self.assertTrue(record["interfaces"] or "no" in record["propagation_path"].lower())

    def test_bridge_catalog_statuses_and_directions(self):
        catalog = g.bridge_catalog()
        directions = {r["direction"] for r in catalog["bridges"]}
        self.assertEqual(directions, {"inbound", "outbound"})
        for record in catalog["bridges"]:
            self.assertIn(record["status"], g.BRIDGE_STATUSES)

    def test_bridge_catalog_rejects_bad_status(self):
        catalog = json.loads(json.dumps(g.bridge_catalog()))
        catalog["bridges"][0]["status"] = "historically_proven"
        with self.assertRaises(g.ValidationError):
            g.validate_bridge_catalog(catalog)

    def test_bridge_catalog_has_explicit_nonbridges(self):
        catalog = g.bridge_catalog()
        by_id = {record["bridge_id"]: record for record in catalog["bridges"]}
        self.assertEqual(by_id["B_NONBRIDGE_LOCAL_TO_COSMIC"]["status"], "bounded_negligible")
        self.assertEqual(by_id["B_NONBRIDGE_SCHUMANN_BAND_ANALOGY"]["status"], "analogy_only")
        self.assertIn("no_direct_cosmic_jump_rule", catalog)

    def test_no_external_citations_any_artifact(self):
        for loader in (g.source_register, g.parameter_registry, g.bridge_catalog):
            self.assertFalse(loader()["external_citations_attached"])


class SystemGraphTests(unittest.TestCase):
    def test_graph_builds_for_all_scenarios(self):
        for scenario_id, scenario in g.all_scenarios().items():
            graph = g.system_graph_for_scenario(scenario)
            self.assertGreaterEqual(len(graph.nodes), 12, scenario_id)
            self.assertTrue(graph.to_dict()["nodes"])

    def test_graph_nodes_cover_layers_and_core(self):
        graph = g.system_graph_for_scenario(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        for name in g.CORE_NODES:
            self.assertIn(name, graph.nodes)
        self.assertEqual(graph.nodes["bedrock"].layer, 7)
        layers = {node.layer for node in graph.nodes.values()}
        self.assertTrue({1, 2, 3, 4, 5, 6, 7, 8, 9}.issubset(layers))

    def test_edges_have_required_metadata(self):
        graph = g.system_graph_for_scenario(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        self.assertTrue(graph.edges)
        for edge in graph.edges:
            self.assertTrue(edge.carrier)
            self.assertTrue(edge.transfer_model)
            self.assertTrue(edge.uncertainty)
            self.assertTrue(edge.falsifier)
            self.assertIn(edge.status, g.BRIDGE_STATUSES)

    def test_no_core_to_cosmic_or_earth_edges(self):
        for scenario in g.all_scenarios().values():
            graph = g.system_graph_for_scenario(scenario)
            for edge in graph.edges:
                self.assertFalse(edge.source in g.CORE_NODES and edge.target in ("cosmic_domain", "earth_domain"))

    def test_null_graph_has_no_edges(self):
        graph = g.system_graph_for_scenario(g.make_scenario("S3_PASSIVE_NULL"))
        self.assertEqual(graph.edges, [])

    def test_hypothesis_graph_has_single_labelled_edge(self):
        graph = g.system_graph_for_scenario(g.make_scenario("S4_ACOUSTIC"))
        hypothesis_edges = [edge for edge in graph.edges if edge.id.startswith("E_HYPOTHESIS_")]
        self.assertEqual(len(hypothesis_edges), 1)
        self.assertEqual(hypothesis_edges[0].carrier, "acoustic")
        self.assertEqual(hypothesis_edges[0].status, "not_evaluable_missing_data")

    def test_role_hypotheses_preserved(self):
        graph = g.system_graph_for_scenario(g.make_scenario("S0_CURRENT_OBSERVED"))
        self.assertEqual(set(graph.nodes["khufu"].role_candidates), set(g.ROLE_HYPOTHESES))
        self.assertIn("passive_boundary", g.ROLE_HYPOTHESES)


class LinearAlgebraTests(unittest.TestCase):
    def test_jacobi_known_symmetric_matrix(self):
        values, vectors = g.jacobi_eigen([[2.0, 1.0], [1.0, 2.0]])
        self.assertAlmostEqual(values[0], 1.0, places=10)
        self.assertAlmostEqual(values[1], 3.0, places=10)
        result = g.matmul([[2.0, 1.0], [1.0, 2.0]], vectors)
        for column in range(2):
            self.assertAlmostEqual(result[0][column], values[column] * vectors[0][column], places=9)

    def test_jacobi_rejects_nonsymmetric(self):
        with self.assertRaises(ValueError):
            g.jacobi_eigen([[1.0, 2.0], [0.0, 1.0]])

    def test_spd_inverse_sqrt_reconstructs(self):
        matrix = [[4.0, 1.0], [1.0, 3.0]]
        inverse_root = g.symmetric_spd_inverse_sqrt(matrix)
        product = g.matmul(g.matmul(inverse_root, matrix), inverse_root)
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(product[i][j], 1.0 if i == j else 0.0, places=10)

    def test_spd_inverse_sqrt_rejects_nonspd(self):
        with self.assertRaises(ValueError):
            g.symmetric_spd_inverse_sqrt([[1.0, 0.0], [0.0, -1.0]])

    def test_complex_solve_known_system(self):
        answer = g.complex_solve([[2 + 1j, 0j], [0j, 3 + 0j]], [[1 + 0j], [2 + 0j]])
        self.assertAlmostEqual(abs(answer[0][0] - 1.0 / (2 + 1j)), 0.0, places=12)
        self.assertAlmostEqual(abs(answer[1][0] - 2.0 / 3.0), 0.0, places=12)

    def test_matmul_rectangular(self):
        result = g.matmul([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], [[1.0], [1.0]])
        self.assertEqual(result, [[3.0], [7.0], [11.0]])


class ReducedOrderPhysicsTests(unittest.TestCase):
    def setUp(self):
        self.model = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        self.frequencies = g.synthetic_frequency_grid(self.model, points=21)

    def test_matrices_shapes_symmetry(self):
        self.assertEqual((len(self.model.M), len(self.model.M[0])), (5, 5))
        for matrix in (self.model.M, self.model.C, self.model.K,
                       self.model.C_material, self.model.C_export):
            self.assertTrue(g.is_symmetric(matrix))
        self.assertEqual(len(self.model.B), 5)
        self.assertEqual(len(self.model.Cr[0]), 5)

    def test_mass_positive_and_coupling_nonnegative(self):
        for i in range(self.model.size):
            self.assertGreater(self.model.M[i][i], 0.0)
            self.assertGreaterEqual(self.model.C[i][i], 0.0)
            self.assertGreater(self.model.K[i][i], 0.0)
        for i in range(self.model.size):
            for j in range(self.model.size):
                if i != j:
                    self.assertGreaterEqual(self.model.K[i][j], 0.0)

    def test_stiffness_spd_all_scenarios(self):
        for scenario_id, scenario in g.all_scenarios().items():
            model = g.assemble_model(scenario)
            values, _ = g.jacobi_eigen(model.K)
            self.assertGreater(min(values), 0.0, scenario_id)
            modes = g.natural_modes(model)
            self.assertTrue(all(m["frequency_hz"] > 0.0 for m in modes), scenario_id)

    def test_damping_psd_all_scenarios(self):
        for scenario_id, scenario in g.all_scenarios().items():
            model = g.assemble_model(scenario)
            values, _ = g.jacobi_eigen(model.C)
            self.assertGreaterEqual(min(values), -g.NUMERIC_TOLERANCE, scenario_id)

    def test_modes_closed_form_single_dof(self):
        mass, stiffness = 1.0e9, 1.0e9
        fixture = g.single_dof_fixture(mass, stiffness)
        mode = g.natural_modes(fixture)[0]
        expected = math.sqrt(stiffness / mass) / (2.0 * math.pi)
        self.assertAlmostEqual(mode["frequency_hz"], expected, places=12)
        self.assertAlmostEqual(mode["omega_rad_per_s"], math.sqrt(stiffness / mass), places=12)
        self.assertIsNotNone(mode["quality_factor"])

    def test_mode_scales_with_mass(self):
        first = g.natural_modes(g.single_dof_fixture(1.0e9, 1.0e9))[0]["frequency_hz"]
        heavier = g.natural_modes(g.single_dof_fixture(4.0e9, 1.0e9))[0]["frequency_hz"]
        self.assertAlmostEqual(heavier, first / 2.0, places=12)

    def test_mode_scales_with_stiffness(self):
        first = g.natural_modes(g.single_dof_fixture(1.0e9, 1.0e9))[0]["frequency_hz"]
        stiffer = g.natural_modes(g.single_dof_fixture(1.0e9, 4.0e9))[0]["frequency_hz"]
        self.assertAlmostEqual(stiffer, 2.0 * first, places=12)

    def test_length_scaling_beam_like_fixture(self):
        mass, stiffness = 1.0e9, 1.0e9
        reference = g.natural_modes(g.single_dof_fixture(mass, stiffness))[0]["frequency_hz"]
        # k ~ EI/L^3 and m ~ L, hence f ~ L^-2 for this declared synthetic rod.
        doubled = g.natural_modes(g.single_dof_fixture(2.0 * mass, stiffness / 8.0))[0]["frequency_hz"]
        self.assertAlmostEqual(doubled, reference / 4.0, places=12)

    def test_modes_mass_orthonormal(self):
        modes = g.natural_modes(self.model)
        for a in modes:
            for b in modes:
                overlap = g.quadratic_form(a["mode_vector_mass_normalized"], self.model.M)
                # quadratic_form conjugates the first vector; use explicit real form.
                overlap = sum(a["mode_vector_mass_normalized"][i] * self.model.M[i][j] *
                              b["mode_vector_mass_normalized"][j]
                              for i in range(self.model.size) for j in range(self.model.size))
                expected = 1.0 if a["index"] == b["index"] else 0.0
                self.assertAlmostEqual(overlap, expected, places=9)

    def test_frequency_response_closed_form_sdof(self):
        fixture = g.single_dof_fixture(1.0e9, 1.0e9)
        for frequency in (0.05, 0.1, 0.2):
            omega = 2.0 * math.pi * frequency
            analytic = 1.0 / (1.0e9 - omega * omega * 1.0e9 + 1j * omega * 1.0)
            computed = g.frequency_response(fixture, [frequency])[0]["H"][0][0]
            self.assertLess(abs(computed - analytic), 1e-15)

    def test_phase_and_attenuation(self):
        for record in g.frequency_response(self.model, self.frequencies):
            value = record["H"][0][0]
            self.assertAlmostEqual(record["phase_rad"], cmath.phase(value), places=12)
            self.assertAlmostEqual(record["attenuation_db_re_1_m_per_N"],
                                   20.0 * math.log10(abs(value)), places=10)

    def test_transfer_peak_near_mode(self):
        fixture = g.single_dof_fixture(1.0e9, 1.0e9)
        grid = g.synthetic_frequency_grid(fixture, points=401)
        peak = max(g.frequency_response(fixture, grid), key=lambda item: item["magnitude_m_per_N"])
        expected = 1.0 / (2.0 * math.pi)
        self.assertLess(abs(peak["frequency_hz"] - expected), 0.01)

    def test_zero_coupling_independent_blocks(self):
        fixture = g.two_dof_block_fixture(coupling=0.0)
        result = g.zero_coupling_check(fixture, perturbed_index=1, stiffness_factor=3.0)
        self.assertTrue(result["independent_subsystems_reproduced"])
        self.assertEqual(result["max_off_diagonal_stiffness_N_per_m"], 0.0)
        coupled = g.two_dof_block_fixture(coupling=1.0e8)
        coupled_result = g.zero_coupling_check(coupled, perturbed_index=1, stiffness_factor=3.0)
        self.assertGreater(coupled_result["max_response_change_m_per_N"], 0.0)

    def test_zero_coupling_scenario_s3(self):
        null = g.assemble_model(g.make_scenario("S3_PASSIVE_NULL"))
        max_off_diagonal = max(abs(null.K[i][j]) for i in range(null.size)
                               for j in range(null.size) if i != j)
        self.assertEqual(max_off_diagonal, 0.0)
        result = g.zero_coupling_check(null, perturbed_index=4, stiffness_factor=2.0)
        self.assertTrue(result["independent_subsystems_reproduced"])

    def test_reciprocity_holds_symmetric(self):
        result = g.reciprocity_check(self.model, self.frequencies[5])
        self.assertTrue(result["symmetric_operators"])
        self.assertTrue(result["reciprocity_holds"])

    def test_reciprocity_fails_broken_assumption(self):
        result = g.reciprocity_check(self.model, self.frequencies[5], broken=True)
        self.assertFalse(result["reciprocity_holds"])
        self.assertGreater(result["relative_asymmetry"], 1e-6)

    def test_passivity_no_amplification(self):
        for scenario_id, scenario in g.all_scenarios().items():
            model = g.assemble_model(scenario)
            result = g.passivity_check(model, g.synthetic_frequency_grid(model, points=21))
            self.assertTrue(result["damping_nonnegative"], scenario_id)
            self.assertTrue(result["no_net_amplification"], scenario_id)
            self.assertTrue(result["all_energy_balances_closed"], scenario_id)

    def test_energy_balance_multiple_frequencies(self):
        for frequency in self.frequencies[::3]:
            budget = g.energy_budget(self.model, frequency)
            self.assertTrue(budget["conservation_closed"], frequency)
            self.assertLess(budget["relative_residual"], g.ENERGY_RELATIVE_TOLERANCE)
            self.assertGreaterEqual(budget["input_power_W"], 0.0)
            self.assertGreaterEqual(budget["material_dissipation_W"], 0.0)
            self.assertGreaterEqual(budget["exported_power_W"], 0.0)
            self.assertGreater(budget["stored_energy_J"], 0.0)

    def test_export_split_sums_to_total_damping(self):
        for i in range(self.model.size):
            for j in range(self.model.size):
                self.assertAlmostEqual(self.model.C_material[i][j] + self.model.C_export[i][j],
                                       self.model.C[i][j], places=12)

    def test_outbound_energy_bound(self):
        record = g.outbound_energy_bound(self.model, self.frequencies[5])
        self.assertGreaterEqual(record["total_input_upper_bound_W"], record["modelled_export_upper_bound_W"])
        self.assertEqual(record["any_unmodelled_channel_bound_W"], record["modelled_export_upper_bound_W"])
        self.assertFalse(record["outbound_communication_claim"])
        self.assertEqual(record["status"], "bounded_negligible")

    def test_natural_background_comparator(self):
        record = g.natural_background_comparator(self.model, self.frequencies[5])
        self.assertEqual(record["synthetic_background_power_W"], 1000.0)
        self.assertEqual(record["status"], "not_evaluable_missing_data")
        self.assertIn("No inbound or outbound attribution", record["interpretation"])

    def test_dimensional_checks(self):
        result = g.dimensional_checks(self.model)
        self.assertTrue(result["units_consistent"])
        self.assertTrue(result["k_over_m_has_inverse_time_squared"])
        self.assertTrue(result["frequency_scaling_consistent"])
        self.assertTrue(result["positive_masses"])
        self.assertTrue(result["nonnegative_diagonal_damping"])
        self.assertEqual(result["matrix_shapes"]["M"], [5, 5])

    def test_no_invented_cavity_geometry(self):
        registry = g.parameter_registry()
        cavity = [p for p in registry["parameters"] if p["name"] == "cavity_inventory"][0]
        self.assertIsNone(cavity["value"])
        self.assertIn("explicitly empty", cavity["description"])
        self.assertIn("do not infer cavities", cavity["limitations"])


class ScenarioAndHypothesisTests(unittest.TestCase):
    def test_all_six_families_created(self):
        scenarios = g.all_scenarios()
        for prefix in ("S0", "S1", "S2", "S3", "S4", "S5"):
            self.assertTrue(any(key.startswith(prefix) for key in scenarios), prefix)
        for scenario in scenarios.values():
            self.assertTrue(g.validate_scenario(scenario))

    def test_s4_variants_one_hypothesis_each(self):
        scenarios = g.all_scenarios()
        variants = {key: value for key, value in scenarios.items() if key.startswith("S4")}
        self.assertEqual(len(variants), 6)
        for key, scenario in variants.items():
            self.assertEqual(len(scenario["enabled_hypotheses"]), 1)
            self.assertNotIn("none", scenario["coupling_families"])
            self.assertIn(scenario["enabled_hypotheses"][0], g.HYPOTHESIS_FAMILY)
            self.assertEqual(g.HYPOTHESIS_FAMILY[scenario["enabled_hypotheses"][0]],
                             scenario["coupling_families"][0])

    def test_null_vs_hypothesis_differ(self):
        null = g.assemble_model(g.make_scenario("S3_PASSIVE_NULL"))
        elastic = g.assemble_model(g.make_scenario("S4_ELASTIC"))
        self.assertNotEqual(null.K, elastic.K)
        a = max(g.frequency_response(null, g.synthetic_frequency_grid(null, points=21)),
                key=lambda item: item["magnitude_m_per_N"])
        b = max(g.frequency_response(elastic, g.synthetic_frequency_grid(elastic, points=21)),
                key=lambda item: item["magnitude_m_per_N"])
        self.assertAlmostEqual(a["magnitude_m_per_N"], 0.0, places=15)
        self.assertGreater(b["magnitude_m_per_N"], 0.0)

    def test_null_is_passive_first(self):
        scenario = g.make_scenario("S3_PASSIVE_NULL")
        self.assertEqual(scenario["coupling_scale"], 0.0)
        self.assertEqual(scenario["enabled_hypotheses"], [])
        self.assertEqual(scenario["coupling_families"], ["none"])

    def test_s5_requires_background(self):
        scenario = g.make_scenario("S5_ENVIRONMENTAL_DRIVERS")
        self.assertTrue(scenario["natural_background_comparator_required"])
        scenario["natural_background_comparator_required"] = False
        with self.assertRaises(g.ValidationError):
            g.validate_scenario(scenario)

    def test_scenarios_deterministic(self):
        self.assertEqual(g.all_scenarios(), g.all_scenarios())


class SensitivityAndPrimeTests(unittest.TestCase):
    def setUp(self):
        self.model = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))

    def test_parameter_sweep_deterministic(self):
        first = g.parameter_sweep(self.model, "damping_ratio_zeta")
        second = g.parameter_sweep(self.model, "damping_ratio_zeta")
        self.assertEqual(first, second)
        self.assertFalse(first["random_sampling_used"])
        self.assertEqual([row["factor"] for row in first["records"]], [0.5, 0.75, 1.0, 1.25, 1.5])

    def test_sensitivity_changes_output(self):
        sweep = g.parameter_sweep(self.model, "khufu_vertical_stiffness_N_per_m")
        self.assertGreater(sweep["normalized_output_ranges"]["first_mode_hz"], 0.0)
        self.assertGreater(sweep["normalized_output_ranges"]["peak_response_m_per_N"], 0.0)

    def test_sensitivity_reports_dominant_unknown(self):
        report = g.sensitivity_report(self.model)
        self.assertIn(report["dominant_unknown"],
                      {"khufu_vertical_stiffness_N_per_m", "damping_ratio_zeta",
                       "sphinx_parent_mass_kg", "contact_khufu_bedrock_N_per_m"})
        self.assertGreaterEqual(report["dominant_unknown_normalized_peak_response_range"], 0.0)

    def test_pareto_frontier_nonempty(self):
        envelope = g.prime_envelope(self.model, points=41)
        self.assertTrue(envelope["pareto_frontier"])
        self.assertTrue(envelope["computed_candidate_frequencies_hz"])

    def test_prime_frequency_emerges_from_operators(self):
        baseline = g.prime_envelope(self.model, points=41)
        modified = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"),
                                    {"khufu_vertical_stiffness_N_per_m": 4.0 * 1.2e9})
        changed = g.prime_envelope(modified, points=41)
        self.assertNotEqual(baseline["computed_candidate_frequencies_hz"],
                            changed["computed_candidate_frequencies_hz"])
        self.assertFalse(baseline["robust_joint_optimum_identifiable"])

    def test_no_hardcoded_prime_frequency(self):
        with open(os.path.join(HERE, "giza_multiscale_model.py"), "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn("7.83", source)
        self.assertNotIn("PRIME_FREQUENCY", source)
        envelope = g.prime_envelope(self.model, points=21)
        self.assertIsNone(envelope["hardcoded_prime_frequency_hz"])

    def test_prime_objectives_have_units(self):
        envelope = g.prime_envelope(self.model, points=21)
        for key in ("min_triad_transfer_m_per_N", "triad_phase_coherence",
                    "export_efficiency", "material_loss_per_force2_W_per_N2"):
            self.assertIn(key, envelope["objective_definitions"])
        for row in envelope["pareto_frontier"]:
            self.assertIn("min_triad_transfer_m_per_N", row)
            self.assertIn("frequency_hz", row)


class ReportAndDeterminismTests(unittest.TestCase):
    def test_report_builds(self):
        report = g.build_deterministic_report()
        self.assertEqual(report["scientific_status"], "idealized_reference_model_not_historical_claim")
        self.assertFalse(report["external_citations_attached"])
        self.assertTrue(all(report["validation"].values()))

    def test_report_serializes_without_nan(self):
        report = g.build_deterministic_report()
        decoded = json.loads(g.deterministic_dumps(report))
        self.assertEqual(decoded["report_id"], "GIZA_PRIME_DETERMINISTIC_EXAMPLE_REPORT")

    def test_report_is_byte_deterministic(self):
        self.assertEqual(g.deterministic_dumps(g.build_deterministic_report()),
                         g.deterministic_dumps(g.build_deterministic_report()))

    def test_write_report_matches_dumps(self):
        path = os.path.join(HERE, "_tmp_report_roundtrip.json")
        try:
            g.write_deterministic_report(path)
            with open(path, "r", encoding="utf-8") as handle:
                written = handle.read()
            self.assertEqual(written, g.deterministic_dumps(g.build_deterministic_report()) + "\n")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_report_separates_computed_from_represented(self):
        report = g.build_deterministic_report()
        computed = report["computed"]
        represented = report["represented_only_not_computed"]
        self.assertIn("natural_modes", computed)
        self.assertIn("energy_budget_at_peak", computed)
        self.assertIn("acoustic_cavity_spectrum", represented)
        self.assertIn("earth_and_cosmic_outbound", represented)

    def test_report_scenario_comparison_rows(self):
        report = g.build_deterministic_report()
        rows = report["scenario_comparison"]["rows"]
        self.assertEqual(len(rows), len(g.scenario_family_ids()))
        self.assertTrue(all(not row["outbound_communication_claim"] for row in rows))

    def test_exported_model_json_is_machine_readable(self):
        model = g.assemble_model(g.make_scenario("S0_CURRENT_OBSERVED"))
        decoded = json.loads(g.deterministic_dumps(model.to_dict()))
        self.assertEqual(decoded["node_names"], list(g.CORE_NODES))
        self.assertEqual(len(decoded["M"]), 5)
        self.assertEqual(len(decoded["M"][0]), 5)
        self.assertIn("parameters", decoded)


class HonestyAndMissingDataTests(unittest.TestCase):
    def test_unresolved_parameters_reported(self):
        report = g.build_deterministic_report()
        unresolved = report["unresolved_parameters"]
        for name in ("sphinx_original_parent_geometry", "groundwater_table_depth_m",
                     "contact_friction_coefficient", "cavity_inventory"):
            self.assertIn(name, unresolved)

    def test_sphinx_parent_not_current_form(self):
        record = next(p for p in g.parameter_registry()["parameters"]
                      if p["name"] == "sphinx_parent_mass_kg")
        self.assertIn("not assumed original", record["limitations"].lower())
        scenario = g.make_scenario("S1_PARENT_GEOLOGY_RECONSTRUCTION")
        self.assertIn("no invented cavity", scenario["notes"])

    def test_no_measurement_evidence_classes_claimed(self):
        forbidden = {"measured_current", "published_measurement", "historical_record"}
        for record in g.parameter_registry()["parameters"]:
            self.assertNotIn(record["evidence_class"], forbidden)
        for record in g.bridge_catalog()["bridges"]:
            self.assertNotIn(record["evidence_class"], forbidden)

    def test_catalog_declares_energy_conservation_rule(self):
        catalog = g.bridge_catalog()
        self.assertIn("P_export", catalog["conservation_bound_rule"]["bound_for_unmodelled_channels"])
        for record in catalog["bridges"]:
            self.assertTrue(record["conservation_closure"])

    def test_missing_data_status_not_evaluable(self):
        catalog = g.bridge_catalog()
        statuses = {record["bridge_id"]: record["status"] for record in catalog["bridges"]}
        self.assertEqual(statuses["B_IN_ELF_GEOMAGNETIC_FORCING"], "not_evaluable_missing_data")
        self.assertEqual(statuses["B_OUT_HYDRAULIC_PATH_HYPOTHESIS"], "not_evaluable_missing_data")


if __name__ == "__main__":
    unittest.main(verbosity=2)
