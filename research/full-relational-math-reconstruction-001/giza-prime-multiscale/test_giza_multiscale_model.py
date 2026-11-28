"""Software/physics controls for the GIZA PRIME idealized multiscale twin.

These tests validate software and dimensional/energy invariants of an IDEALIZED
synthetic fixture. Passing tests are NOT archaeological evidence and are NOT
evidence of any historical Giza function or Giza-cosmos communication.

Revision 2 adds physical-MEANING controls (spring sign pattern, dimensional
consistency of damping, radiation-port energy separation, status semantics and
evidence-class provenance), not only SPD/PSD/passivity checks.
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


def _assert_json_data_equal(testcase, bundled, generated, path="report"):
    """Compare two parsed JSON trees, tolerating cross-version float repr.

    Python 3.14 and 3.12 can serialize the same float with a different number
    of digits, and libm can differ by an ULP across platforms.  The committed
    report's DATA is the determinism contract; byte-level determinism inside a
    single interpreter is covered by test_report_is_byte_deterministic and
    test_write_report_matches_dumps.
    """
    if isinstance(bundled, dict) or isinstance(generated, dict):
        testcase.assertIsInstance(bundled, dict, path)
        testcase.assertIsInstance(generated, dict, path)
        testcase.assertEqual(set(bundled), set(generated), path)
        for key in sorted(bundled):
            _assert_json_data_equal(testcase, bundled[key], generated[key], path + "." + key)
    elif isinstance(bundled, (list, tuple)) or isinstance(generated, (list, tuple)):
        testcase.assertIsInstance(bundled, (list, tuple), path)
        testcase.assertIsInstance(generated, (list, tuple), path)
        testcase.assertEqual(len(bundled), len(generated), path)
        for index, (left, right) in enumerate(zip(bundled, generated)):
            _assert_json_data_equal(testcase, left, right, "%s[%d]" % (path, index))
    elif isinstance(bundled, bool) or isinstance(generated, bool):
        testcase.assertEqual(bundled, generated, path)
    elif isinstance(bundled, (int, float)) and isinstance(generated, (int, float)):
        testcase.assertTrue(
            math.isclose(bundled, generated, rel_tol=1e-9, abs_tol=1e-12),
            "%s: %r != %r" % (path, bundled, generated),
        )
    else:
        testcase.assertEqual(bundled, generated, path)


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

    def test_bridge_statuses_include_new_conservation_states(self):
        schema = g.scenario_schema()
        self.assertIn("conservation_bounded_not_attributed", schema["bridge_statuses"])
        self.assertIn("idealized_model_only", schema["bridge_statuses"])
        self.assertTrue(schema["bounded_negligible_rule"])

    def test_example_scenario_validates(self):
        scenario = g.load_json("example_scenario_synthetic.json")
        self.assertTrue(g.validate_scenario(scenario))
        self.assertTrue(scenario["synthetic"])
        self.assertFalse(scenario["outbound_communication_claim"])

    def test_example_scenario_has_no_removed_export_fraction(self):
        scenario = g.load_json("example_scenario_synthetic.json")
        self.assertNotIn("radiation_export_fraction", scenario["parameter_overrides"])

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

    def test_scenario_rejects_unprovenanced_evidence_class(self):
        scenario = g.make_scenario("S0_CURRENT_OBSERVED")
        scenario["evidence_basis"] = ["geologically_inferred"]
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

    def test_scenario_rejects_unknown_parameter_override(self):
        scenario = g.make_scenario("S0_CURRENT_OBSERVED")
        scenario["parameter_overrides"] = {"radiation_export_fraction": 0.3}
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

    def test_source_register_declares_restricted_classes(self):
        register = g.source_register()
        self.assertEqual(set(register["restricted_evidence_classes_without_sources"]),
                         set(g.PROVENANCE_RESTRICTED_CLASSES))

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

    def test_parameter_registry_rejects_provenance_class_without_sources(self):
        registry = json.loads(json.dumps(g.parameter_registry()))
        registry["parameters"][0]["evidence_class"] = "reconstructed_uncertain"
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

    def test_bridge_catalog_rejects_bounded_negligible(self):
        catalog = json.loads(json.dumps(g.bridge_catalog()))
        catalog["bridges"][0]["status"] = "bounded_negligible"
        with self.assertRaises(g.ValidationError):
            g.validate_bridge_catalog(catalog)

    def test_bridge_catalog_has_explicit_nonbridges(self):
        catalog = g.bridge_catalog()
        by_id = {record["bridge_id"]: record for record in catalog["bridges"]}
        self.assertEqual(by_id["B_NONBRIDGE_LOCAL_TO_COSMIC"]["status"],
                         "conservation_bounded_not_attributed")
        self.assertEqual(by_id["B_NONBRIDGE_SCHUMANN_BAND_ANALOGY"]["status"], "analogy_only")
        self.assertIn("no_direct_cosmic_jump_rule", catalog)

    def test_no_external_citations_any_artifact(self):
        for loader in (g.source_register, g.parameter_registry, g.bridge_catalog,
                       g.functional_object_registry, g.real_source_ingestion_contract):
            self.assertFalse(loader()["external_citations_attached"])

    def test_real_source_contract_is_empty_and_valid(self):
        contract = g.real_source_ingestion_contract()
        self.assertTrue(g.validate_real_source_contract(contract))
        self.assertEqual(contract["sources"], [])
        self.assertEqual(contract["ingestion_state"], "awaiting_verified_sources")
        self.assertTrue(contract["required_source_fields"])

    def test_real_source_contract_rejects_claimed_source(self):
        contract = json.loads(json.dumps(g.real_source_ingestion_contract()))
        contract["sources"] = [{"source_id": "invented"}]
        with self.assertRaises(g.ValidationError):
            g.validate_real_source_contract(contract)


class FunctionalObjectRegistryTests(unittest.TestCase):
    def test_registry_validates(self):
        self.assertTrue(g.validate_functional_object_registry())

    def test_open_ensemble_covers_more_than_three_pyramids(self):
        objects = g.functional_object_registry()["objects"]
        self.assertGreaterEqual(len(objects), 9)
        ids = {obj["id"] for obj in objects}
        for name in ("queens_pyramids", "khafre_temple_causeway", "sphinx_temple_complex",
                     "plateau_substrate", "sphinx_parent_massif"):
            self.assertIn(name, ids)
        self.assertEqual(tuple(obj["id"] for obj in objects), g.FUNCTIONAL_OBJECT_IDS)

    def test_every_object_has_mass_stiffness_and_roles(self):
        units = {p["name"]: p["unit"] for p in g.parameter_registry()["parameters"]}
        for obj in g.functional_object_registry()["objects"]:
            self.assertEqual(units[obj["mass_parameter"]], "kg", obj["id"])
            self.assertEqual(units[obj["stiffness_parameter"]], "N/m", obj["id"])
            self.assertTrue(obj["role_candidates"], obj["id"])
            self.assertEqual(obj["evidence_class"], "idealized_design", obj["id"])

    def test_contacts_reference_known_objects_and_springs(self):
        registry = g.functional_object_registry()
        known = {obj["id"] for obj in registry["objects"]}
        units = {p["name"]: p["unit"] for p in g.parameter_registry()["parameters"]}
        for contact in registry["contacts"]:
            self.assertIn(contact["source"], known)
            self.assertIn(contact["target"], known)
            self.assertEqual(units[contact["spring_parameter"]], "N/m")

    def test_incomputable_hypotheses_have_no_coefficient(self):
        for coupling in g.functional_object_registry()["hypothesis_couplings"]:
            if not coupling["evaluable"]:
                self.assertIsNone(coupling["coefficient_parameter"])
                self.assertIsNone(coupling["spring_parameter"])
                self.assertEqual(coupling["status"], "not_evaluable_missing_data")

    def test_evaluable_viscous_coefficients_are_N_s_per_m(self):
        units = {p["name"]: p["unit"] for p in g.parameter_registry()["parameters"]}
        for coupling in g.functional_object_registry()["hypothesis_couplings"]:
            coefficient = coupling["coefficient_parameter"]
            if coupling["evaluable"] and coefficient:
                self.assertEqual(units[coefficient], "N*s/m", coefficient)

    def test_registry_rejects_N_per_m_viscous_coefficient(self):
        registry = json.loads(json.dumps(g.functional_object_registry()))
        coupling = next(c for c in registry["hypothesis_couplings"] if c["family"] == "acoustic")
        coupling["coefficient_parameter"] = "contact_khufu_khafre_N_per_m"
        with self.assertRaises(g.ValidationError):
            g.validate_functional_object_registry(registry)

    def test_radiation_port_is_declared(self):
        port = g.functional_object_registry()["radiating_ports"][0]
        self.assertIn(port["object_id"], g.FUNCTIONAL_OBJECT_IDS)
        self.assertIn("R_rad", port["formula"])


class SystemGraphTests(unittest.TestCase):
    def test_graph_builds_for_all_scenarios(self):
        for scenario_id, scenario in g.all_scenarios().items():
            graph = g.system_graph_for_scenario(scenario)
            self.assertGreaterEqual(len(graph.nodes), 16, scenario_id)
            self.assertTrue(graph.to_dict()["nodes"])

    def test_graph_nodes_cover_layers_and_all_functional_objects(self):
        graph = g.system_graph_for_scenario(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        for name in g.FUNCTIONAL_OBJECT_IDS:
            self.assertIn(name, graph.nodes)
        self.assertEqual(graph.nodes["bedrock"].layer, 7)
        layers = {node.layer for node in graph.nodes.values()}
        self.assertTrue({1, 2, 3, 4, 5, 6, 7, 8, 9}.issubset(layers))

    def test_sphinx_core_node_no_longer_claims_reconstructed_uncertain(self):
        graph = g.system_graph_for_scenario(g.make_scenario("S1_PARENT_GEOLOGY_RECONSTRUCTION"))
        self.assertEqual(graph.nodes["sphinx_parent_massif"].evidence_class, "idealized_design")

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
                self.assertFalse(edge.source in g.FUNCTIONAL_OBJECT_IDS and
                                 edge.target in ("cosmic_domain", "earth_domain"))

    def test_null_graph_has_no_edges(self):
        graph = g.system_graph_for_scenario(g.make_scenario("S3_PASSIVE_NULL"))
        self.assertEqual(graph.edges, [])

    def test_hypothesis_graph_has_single_labelled_edge(self):
        graph = g.system_graph_for_scenario(g.make_scenario("S4_ACOUSTIC"))
        hypothesis_edges = [edge for edge in graph.edges if edge.id.startswith("E_HYPOTHESIS_")]
        self.assertEqual(len(hypothesis_edges), 1)
        self.assertEqual(hypothesis_edges[0].carrier, "acoustic")
        self.assertEqual(hypothesis_edges[0].status, "hypothesis_unverified")

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


class ContactMechanicsSignTests(unittest.TestCase):
    """Physical-meaning controls: SPD alone does not catch a wrong spring sign."""

    def test_two_node_spring_exact_pattern(self):
        operator = g.matrix_zeros(2)
        g.add_linear_spring(operator, 0, 1, 7.0)
        self.assertEqual(operator, [[7.0, -7.0], [-7.0, 7.0]])

    def test_two_node_dashpot_exact_pattern(self):
        operator = g.matrix_zeros(2)
        g.add_linear_dashpot(operator, 0, 1, 3.0)
        self.assertEqual(operator, [[3.0, -3.0], [-3.0, 3.0]])

    def test_spring_row_sums_vanish(self):
        operator = g.matrix_zeros(3)
        g.add_linear_spring(operator, 0, 2, 5.0)
        self.assertEqual(sum(operator[0]), 0.0)
        self.assertEqual(sum(operator[2]), 0.0)

    def test_spring_rejects_same_node(self):
        with self.assertRaises(g.ValidationError):
            g.add_linear_spring(g.matrix_zeros(2), 0, 0, 1.0)

    def test_spring_rejects_negative_stiffness(self):
        with self.assertRaises(g.ValidationError):
            g.add_linear_spring(g.matrix_zeros(2), 0, 1, -1.0)

    def test_dashpot_rejects_N_per_m_misuse(self):
        # The API itself cannot read units, but a negative coefficient is rejected;
        # dimensional_checks separately rejects an N/m parameter inside damping.
        with self.assertRaises(g.ValidationError):
            g.add_linear_dashpot(g.matrix_zeros(2), 0, 1, -1.0)

    def test_assembled_off_diagonals_are_negative(self):
        model = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        for i in range(model.size):
            for j in range(model.size):
                if i != j:
                    self.assertLessEqual(model.K[i][j], g.NUMERIC_TOLERANCE)
                    self.assertLessEqual(model.C[i][j], g.NUMERIC_TOLERANCE)

    def test_registry_two_node_elements_reproduce_off_diagonals(self):
        model = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        self.assertTrue(g.contact_mechanics_check(model)["operators_match_registry_two_node_elements"])
        self.assertTrue(g.contact_mechanics_check(model)["contact_sign_physics_valid"])

    def test_positive_off_diagonal_is_rejected_even_if_spd(self):
        model = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        model.K[0][1] = model.K[1][0] = abs(model.K[0][1]) + 1.0e7
        self.assertGreater(min(g.jacobi_eigen(model.K)[0]), 0.0)  # still SPD
        check = g.contact_mechanics_check(model)
        self.assertGreater(check["max_positive_stiffness_off_diagonal_N_per_m"], 0.0)
        self.assertFalse(check["spring_sign_convention_valid"])
        self.assertFalse(check["contact_sign_physics_valid"])


class ReducedOrderPhysicsTests(unittest.TestCase):
    def setUp(self):
        self.model = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        self.frequencies = g.synthetic_frequency_grid(self.model, points=21)

    def test_matrices_shapes_symmetry(self):
        size = len(g.FUNCTIONAL_OBJECT_IDS)
        self.assertEqual((len(self.model.M), len(self.model.M[0])), (size, size))
        for matrix in (self.model.M, self.model.C, self.model.K):
            self.assertTrue(g.is_symmetric(matrix))
        self.assertEqual(len(self.model.B), size)
        self.assertEqual(len(self.model.Cr[0]), size)

    def test_mass_positive_damping_nonnegative(self):
        for i in range(self.model.size):
            self.assertGreater(self.model.M[i][i], 0.0)
            self.assertGreaterEqual(self.model.C[i][i], 0.0)
            self.assertGreater(self.model.K[i][i], 0.0)

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
        doubled = g.natural_modes(g.single_dof_fixture(2.0 * mass, stiffness / 8.0))[0]["frequency_hz"]
        self.assertAlmostEqual(doubled, reference / 4.0, places=12)

    def test_modes_mass_orthonormal(self):
        modes = g.natural_modes(self.model)
        for a in modes:
            for b in modes:
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
        result = g.zero_coupling_check(null, perturbed_index=null.size - 1, stiffness_factor=2.0)
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


class RadiationAndEnergyTests(unittest.TestCase):
    def setUp(self):
        self.model = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        self.frequencies = g.synthetic_frequency_grid(self.model, points=21)

    def test_energy_balance_multiple_frequencies(self):
        for frequency in self.frequencies[::3]:
            budget = g.energy_budget(self.model, frequency)
            self.assertTrue(budget["conservation_closed"], frequency)
            self.assertLess(budget["relative_residual"], g.ENERGY_RELATIVE_TOLERANCE)
            self.assertGreaterEqual(budget["input_power_W"], 0.0)
            self.assertGreaterEqual(budget["material_dissipation_W"], 0.0)
            self.assertGreaterEqual(budget["exported_power_W"], 0.0)
            self.assertGreater(budget["stored_energy_J"], 0.0)

    def test_export_is_not_a_fraction_of_material_damping(self):
        with open(os.path.join(HERE, "parameter_registry.json"), "r", encoding="utf-8") as handle:
            registry_text = handle.read()
        self.assertNotIn("radiation_export_fraction", registry_text)
        self.assertFalse(hasattr(self.model, "C_export"))
        self.assertFalse(hasattr(self.model, "C_material"))

    def test_radiation_resistance_matches_declared_formula(self):
        budget = g.energy_budget(self.model, self.frequencies[5])
        p = self.model.radiation_parameters
        omega = 2.0 * math.pi * self.frequencies[5]
        area = p["radiation_aperture_area_m2"]
        ka = omega * math.sqrt(area / math.pi) / p["radiation_medium_wave_speed_m_per_s"]
        expected = 0.5 * p["radiation_medium_density_kg_per_m3"] * \
            p["radiation_medium_wave_speed_m_per_s"] * area * ka * ka
        self.assertAlmostEqual(budget["radiation_resistance_N_s_per_m"], expected, places=6)

    def test_radiation_resistance_units_are_N_s_per_m(self):
        checks = g.dimensional_checks(self.model)
        self.assertTrue(checks["radiation_resistance_is_N_s_per_m"])
        self.assertEqual(checks["radiation_resistance_exponents_kg_m_s"], (1, 0, -1))

    def test_radiation_added_to_dynamic_stiffness(self):
        omega = 2.0 * math.pi * self.frequencies[5]
        damping, resistance = self.model.damping_matrix_at(omega)
        port = self.model.node_names.index(self.model.radiation_port)
        self.assertGreater(resistance, 0.0)
        self.assertAlmostEqual(damping[port][port], self.model.C[port][port] + resistance, places=6)
        z = self.model.dynamic_stiffness(omega)
        self.assertAlmostEqual(z[port][port].imag, omega * damping[port][port], places=6)

    def test_export_efficiency_frequency_dependent_not_constant(self):
        efficiencies = [g.energy_budget(self.model, f)["export_efficiency"]
                        for f in self.frequencies]
        self.assertGreater(max(efficiencies) - min(efficiencies), 1.0e-9)
        self.assertNotAlmostEqual(sum(efficiencies) / len(efficiencies), 0.3, places=6)

    def test_exported_power_never_exceeds_input(self):
        for frequency in self.frequencies:
            budget = g.energy_budget(self.model, frequency)
            self.assertLessEqual(budget["exported_power_W"], budget["input_power_W"] + 1e-12)

    def test_out_of_validity_band_export_incomputable(self):
        original = self.model.radiation_parameters["radiation_ka_validity_max"]
        self.model.radiation_parameters["radiation_ka_validity_max"] = 1.0e-9
        budget = g.energy_budget(self.model, self.frequencies[5])
        self.assertIsNone(budget["radiation_resistance_N_s_per_m"])
        self.assertFalse(budget["export_evaluable"])
        self.assertEqual(budget["export_status"], "not_evaluable_missing_data")
        self.model.radiation_parameters["radiation_ka_validity_max"] = original

    def test_outbound_bound_has_no_negligibility_claim(self):
        record = g.outbound_energy_bound(self.model, self.frequencies[5])
        self.assertEqual(record["status"], "conservation_bounded_not_attributed")
        self.assertFalse(record["attribution_allowed"])
        self.assertFalse(record["outbound_communication_claim"])
        self.assertGreaterEqual(record["total_input_upper_bound_W"],
                                record["modelled_radiated_upper_bound_W"])

    def test_synthetic_background_cannot_justify_negligibility(self):
        record = g.natural_background_comparator(self.model, self.frequencies[5])
        self.assertEqual(record["synthetic_background_power_W"], 1000.0)
        self.assertFalse(record["negligibility_claim_allowed"])
        self.assertIn("No attribution or negligibility conclusion", record["interpretation"])


class DimensionalAndConstitutiveTests(unittest.TestCase):
    def setUp(self):
        self.model = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))

    def test_dimensional_checks(self):
        result = g.dimensional_checks(self.model)
        self.assertTrue(result["units_consistent"])
        self.assertEqual(result["unit_mismatches"], {})
        self.assertTrue(result["positive_masses"])
        self.assertTrue(result["nonnegative_diagonal_damping"])

    def test_no_N_per_m_injected_into_damping(self):
        result = g.dimensional_checks(self.model)
        self.assertTrue(result["damping_parameters_use_N_s_per_m"])
        self.assertTrue(result["no_N_per_m_injected_into_damping"])

    def test_frequency_exponents_are_inverse_time(self):
        result = g.dimensional_checks(self.model)
        self.assertEqual(result["k_over_m_exponents_kg_m_s"], (0, 0, -2))
        self.assertEqual(result["frequency_exponents_kg_m_s"], (0, 0, -1))

    def test_matrix_shapes_follow_functional_object_count(self):
        result = g.dimensional_checks(self.model)
        size = len(g.FUNCTIONAL_OBJECT_IDS)
        self.assertEqual(result["matrix_shapes"]["M"], [size, size])
        self.assertEqual(result["matrix_shapes"]["C"], [size, size])
        self.assertEqual(result["matrix_shapes"]["K"], [size, size])

    def test_incomputable_hypotheses_add_no_operator_term(self):
        baseline = g.assemble_model(g.make_scenario("S2_IDEALIZED_REFERENCE_COMPLEX"))
        for scenario_id in ("S4_HYDROLOGIC", "S4_ELECTROMAGNETIC"):
            candidate = g.assemble_model(g.make_scenario(scenario_id))
            self.assertEqual(candidate.K, baseline.K, scenario_id)
            self.assertEqual(candidate.C, baseline.C, scenario_id)
            report = g.hypothesis_activation_report(candidate)
            self.assertFalse(report["evaluable"])
            self.assertFalse(report["operator_modified"])

    def test_viscous_hypotheses_use_signed_N_s_per_m_dashpots(self):
        for scenario_id in ("S4_ACOUSTIC", "S4_GAS_THERMAL", "S4_MIXED"):
            model = g.assemble_model(g.make_scenario(scenario_id))
            report = g.hypothesis_activation_report(model)
            self.assertTrue(report["evaluable"], scenario_id)
            self.assertEqual(report["unit"], "N*s/m", scenario_id)
            self.assertTrue(report["operator_modified"], scenario_id)
            self.assertTrue(g.contact_mechanics_check(model)["dashpot_sign_convention_valid"], scenario_id)

    def test_elastic_hypothesis_uses_signed_N_per_m_spring(self):
        model = g.assemble_model(g.make_scenario("S4_ELASTIC"))
        report = g.hypothesis_activation_report(model)
        self.assertEqual(report["unit"], "N/m")
        self.assertTrue(report["operator_modified"])
        self.assertTrue(g.contact_mechanics_check(model)["spring_sign_convention_valid"])


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
                       "sphinx_parent_massif_mass_kg", "contact_khufu_bedrock_N_per_m"})
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

    def test_discrete_grid_scope_declared(self):
        envelope = g.prime_envelope(self.model, points=21)
        self.assertTrue(envelope["finite_synthetic_discretization"])
        self.assertFalse(envelope["continuous_global_optimality_claim"])
        self.assertEqual(envelope["evaluated_points"], 21)

    def test_local_continuous_refinement_is_separate(self):
        envelope = g.prime_envelope(self.model, points=21)
        self.assertTrue(envelope["locally_refined_candidates"])
        self.assertTrue(envelope["locally_refined_candidate_frequencies_hz"])
        for row in envelope["locally_refined_candidates"]:
            self.assertIn("coarse_frequency_hz", row)
            self.assertIn("refinement_bracket_hz", row)

    def test_export_efficiency_is_a_computed_objective(self):
        envelope = g.prime_envelope(self.model, points=21)
        self.assertTrue(envelope["export_efficiency_frequency_dependent"])
        low, high = envelope["export_efficiency_range"]
        self.assertLess(low, high)


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

    def test_bundled_report_matches_generated(self):
        with open(os.path.join(HERE, "deterministic_report_example.json"), "r", encoding="utf-8") as handle:
            bundled = json.load(handle)
        generated = g.build_deterministic_report()
        _assert_json_data_equal(self, bundled, generated)
        self.assertEqual(bundled["report_id"], generated["report_id"])

    def test_report_separates_computed_from_represented(self):
        report = g.build_deterministic_report()
        computed = report["computed"]
        represented = report["represented_only_not_computed"]
        self.assertIn("natural_modes", computed)
        self.assertIn("energy_budget_at_peak", computed)
        self.assertIn("acoustic_cavity_spectrum", represented)
        self.assertIn("earth_and_cosmic_outbound", represented)

    def test_report_records_physics_revision_and_controls(self):
        report = g.build_deterministic_report()
        self.assertEqual(report["physics_controls"]["revision"], "physics_corrected_revision_2")
        self.assertTrue(report["physics_controls"]["contact_mechanics"]["contact_sign_physics_valid"])

    def test_report_includes_open_landscape_architecture(self):
        report = g.build_deterministic_report()
        architecture = report["landscape_architecture"]
        self.assertTrue(architecture["open_world"])
        self.assertTrue(architecture["no_primordial_core"])
        self.assertEqual(architecture["prime_definition"]["scope"],
                         "emergent_property_of_interaction_ensemble")
        self.assertTrue(all(architecture["validation"].values()))

    def test_report_validation_covers_landscape_artifacts(self):
        report = g.build_deterministic_report()
        self.assertTrue(report["validation"]["functional_landscape_graph"])
        self.assertTrue(report["validation"]["inventory_coverage_register"])

    def test_report_mechanics_projection_is_not_whole_landscape(self):
        report = g.build_deterministic_report()
        projection = report["landscape_architecture"]["mechanics_projection"]
        self.assertEqual(projection["projection_scope"], "synthetic_fixture_only")
        self.assertFalse(projection["general_landscape_model_claim"])
        self.assertFalse(projection["primordial_core_claim"])

    def test_report_scenario_comparison_rows(self):
        report = g.build_deterministic_report()
        rows = report["scenario_comparison"]["rows"]
        self.assertEqual(len(rows), len(g.scenario_family_ids()))
        self.assertTrue(all(not row["outbound_communication_claim"] for row in rows))

    def test_exported_model_json_is_machine_readable(self):
        model = g.assemble_model(g.make_scenario("S0_CURRENT_OBSERVED"))
        decoded = json.loads(g.deterministic_dumps(model.to_dict()))
        self.assertEqual(decoded["node_names"], list(g.CORE_NODES))
        size = len(g.FUNCTIONAL_OBJECT_IDS)
        self.assertEqual(len(decoded["M"]), size)
        self.assertEqual(len(decoded["M"][0]), size)
        self.assertEqual(decoded["functional_object_count"], size)
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
                      if p["name"] == "sphinx_parent_massif_mass_kg")
        self.assertIn("not assumed original", record["limitations"].lower())
        scenario = g.make_scenario("S1_PARENT_GEOLOGY_RECONSTRUCTION")
        self.assertIn("no invented cavity", scenario["notes"])

    def test_synthetic_sphinx_values_are_idealized_design(self):
        names = {"sphinx_parent_massif_mass_kg", "sphinx_parent_massif_vertical_stiffness_N_per_m",
                 "contact_sphinx_bedrock_N_per_m"}
        classes = {p["name"]: p["evidence_class"] for p in g.parameter_registry()["parameters"]}
        for name in names:
            self.assertEqual(classes[name], "idealized_design", name)

    def test_no_measurement_evidence_classes_claimed(self):
        forbidden = set(g.PROVENANCE_RESTRICTED_CLASSES)
        for loader in (g.parameter_registry, g.bridge_catalog, g.functional_object_registry):
            artifact = loader()
            records = artifact.get("parameters") or artifact.get("bridges") or artifact.get("objects")
            for record in records:
                self.assertNotIn(record["evidence_class"], forbidden)

    def test_catalog_declares_energy_conservation_rule(self):
        catalog = g.bridge_catalog()
        self.assertIn("P_export", catalog["conservation_bound_rule"]["bound_for_unmodelled_channels"])
        self.assertIn("not_evaluable_missing_data",
                      catalog["conservation_bound_rule"]["bound_for_unmodelled_channels"])
        for record in catalog["bridges"]:
            self.assertTrue(record["conservation_closure"])

    def test_missing_data_status_not_evaluable(self):
        catalog = g.bridge_catalog()
        statuses = {record["bridge_id"]: record["status"] for record in catalog["bridges"]}
        self.assertEqual(statuses["B_IN_ELF_GEOMAGNETIC_FORCING"], "not_evaluable_missing_data")
        self.assertEqual(statuses["B_OUT_HYDRAULIC_PATH_HYPOTHESIS"], "not_evaluable_missing_data")
        self.assertEqual(statuses["B_OUT_EM_TRANSDUCER_HYPOTHESIS"], "not_evaluable_missing_data")

    def test_no_bounded_negligible_status_anywhere(self):
        statuses = {record["status"] for record in g.bridge_catalog()["bridges"]}
        self.assertNotIn("bounded_negligible", statuses)
        report = g.build_deterministic_report()
        self.assertNotIn("bounded_negligible", g.deterministic_dumps(report))

    def test_no_invented_cavity_geometry(self):
        registry = g.parameter_registry()
        cavity = [p for p in registry["parameters"] if p["name"] == "cavity_inventory"][0]
        self.assertIsNone(cavity["value"])
        self.assertIn("explicitly empty", cavity["description"])
        self.assertIn("do not infer cavities", cavity["limitations"])

    def test_real_source_layer_prepared_not_attached(self):
        contract = g.real_source_ingestion_contract()
        self.assertTrue(contract["first_layer_targets"])
        self.assertTrue(any(t["target"] == "monument_geometry" for t in contract["first_layer_targets"]))
        self.assertFalse(contract["external_citations_attached"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
