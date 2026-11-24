"""GIZA PRIME -- idealized multiscale digital twin (standard-library reference implementation).

SCIENTIFIC STATUS
-----------------
This module is an *idealized reference model* and a set of software/physics controls.
It is NOT a historical reconstruction, NOT a 3D FEM/CFD solution, and NOT evidence
that the Giza complex communicates with the Earth or the cosmos. Every numeric
parameter comes from ``source_register.json`` / ``parameter_registry.json`` and is
labelled ``idealized_design`` or ``assumption_for_sensitivity`` (or ``unknown``).
No external citation, survey coordinate, elevation, published measurement or unit
system from a real source is asserted anywhere in this package.

CORRECTED PHYSICS CONTRACT (revision 2)
---------------------------------------
Earlier revision 1 had four defects that are corrected here and guarded by tests:

  R1  A contact spring between two DOFs was assembled with POSITIVE off-diagonals
      (K_ij += k).  A two-node 1-D spring is k*[[1,-1],[-1,1]], so off-diagonals
      MUST be negative.  ``add_linear_spring`` / ``add_linear_dashpot`` now enforce
      this, and ``contact_mechanics_check`` rejects a positive off-diagonal even
      when the matrix is SPD.

  R2  N/m quantities were inserted into the damping matrix C (N s/m).  There is no
      dimensionless time scale that legitimises that substitution.  Hypothesis
      channels that have no constitutive equation and no N s/m coefficient are now
      INCOMPUTABLE (no operator term is added); channels that do carry a declared
      viscous dashpot coefficient use N s/m and the same [-1] two-node pattern.

  R3  Exported power was an arbitrary 0.3 * C bookkeeping split, and a synthetic
      1000 W comparator was used to justify "bounded_negligible".  Export is now a
      separate radiation port with a low-ka radiation resistance
      R_rad = 1/2 rho c A (ka)^2 [N s/m], evaluated per frequency, added to Z as
      i*omega*R_rad at the port DOF.  P_export = 1/2 R_rad omega^2 |u_port|^2.
      Efficiency is therefore frequency- and parameter-dependent.  No negligibility
      claim is made from the synthetic comparator.

  R4  Synthetic Sphinx values were labelled ``reconstructed_uncertain`` and a
      synthetic contact ``geologically_inferred`` although zero external sources are
      attached.  Classes that require provenance are rejected by the validators
      while ``external_citations_attached`` is false.

  R5  PRIME used a finite 81-point synthetic grid only.  A declared local continuous
      refinement of Pareto candidates is now reported separately, with
      ``continuous_global_optimality_claim = false``.

  R6  The ensemble is an OPEN set of functional objects (monuments, queens' pyramids,
      temple/causeway chains, parent massif, temple complex, active bedrock, plateau
      substrate), not three pyramids and one chosen stump.  Objects and contacts are
      registry-driven; arbitrary functional objects and combinations can be added.

GOVERNING EQUATIONS AND UNITS (reduced order, NOT full FEM)
-----------------------------------------------------------
    M u_dd + C u_d + K u + R_rad(omega) P_r u_d = B s(t)
      M : kg            (symmetric positive definite)
      C : N s/m = kg/s  (symmetric positive semidefinite; structural/material only)
      K : N/m  = kg/s^2 (symmetric positive definite; grounded spring network)
      R_rad : N s/m     (frequency-dependent radiation resistance at one port)
      P_r = e_r e_r^T   (radiation port projector, dimensionless)
      B : dimensionless force distribution; F phasor = B * F0, F0 in N
      u : m ; omega : rad/s ; f = omega/(2*pi) in Hz

    Z(omega) = K - omega^2 M + i omega (C + R_rad P_r)              [N/m]
    H(omega) = Cr^T Z(omega)^-1 B                                   [m/N] (receptance)
    For a generalized eigenpair (lambda_k, phi_k) of
        S = M^(-1/2) K M^(-1/2),  M^(-1/2) = (M^(1/2))^(-1),
    we have K phi_k = lambda_k M phi_k, phi_k^T M phi_j = delta_kj,
        omega_k = sqrt(lambda_k) [rad/s],  f_k = omega_k/(2*pi) [Hz].
    Modal damping: zeta_k = phi_k^T C phi_k / (2 omega_k),
        Q_k = 1/(2 zeta_k) = omega_k / (phi_k^T C phi_k) when positive.

HARMONIC STEADY-STATE ENERGY BUDGET (phasor convention Re[. e^(i omega t)])
--------------------------------------------------------------------------
    u = Z^-1 F
    P_in       = 1/2 Re( F^* . (i omega u) )               [W]
    P_material = 1/2 omega^2 u^* C u                       [W]  (structural)
    P_export   = 1/2 omega^2 R_rad |u_port|^2              [W]  (radiation port)
    P_stored   = 1/4 ( u^* K u + omega^2 u^* M u )         [J, time average]
    P_in - P_material - P_export = 0  (passive; dE/dt averages to zero)
    P_export <= P_in, so ANY unmodelled outbound channel obeys
    P_channel <= P_export <= P_in <= P_source_assumed.
    The synthetic background comparator is NOT a measured spectrum and cannot
    support a negligibility or attribution claim.

RECIPROCITY
-----------
H_ij = H_ji only when M, C, K are symmetric (Z therefore complex symmetric) and
output channels match input channels, i.e. Cr = B^T.  Not assumed for active,
nonreciprocal or unmodelled-radiation extensions.

PRIME
-----
PRIME is a Pareto envelope of objectives evaluated on the computed spectrum plus a
declared local continuous refinement.  No favourite frequency is hardcoded.

NUMERICAL METHOD
----------------
Real symmetric Jacobi eigendecomposition, complex Gaussian elimination with partial
pivoting, deterministic golden-section refinement.  Floating point with documented
tolerances; this is not exact Q algebra.  All algorithms are deterministic.
"""

from __future__ import annotations

import cmath
import copy
import json
import math
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import landscape_graph_engine as landscape

HERE = os.path.dirname(os.path.abspath(__file__))

EVIDENCE_CLASSES: Tuple[str, ...] = (
    "measured_current", "published_measurement", "historical_record",
    "geologically_inferred", "reconstructed_uncertain", "idealized_design",
    "assumption_for_sensitivity", "speculative_hypothesis", "unknown",
)
# Classes that may not be used while no external source is attached.
PROVENANCE_RESTRICTED_CLASSES: Tuple[str, ...] = (
    "measured_current", "published_measurement", "historical_record",
    "geologically_inferred", "reconstructed_uncertain",
)
BRIDGE_STATUSES: Tuple[str, ...] = (
    "measured", "literature_supported", "model_supported",
    "idealized_model_only", "conservation_bounded_not_attributed",
    "bounded_negligible", "analogy_only", "hypothesis_unverified",
    "not_evaluable_missing_data",
)
ROLE_HYPOTHESES: Tuple[str, ...] = (
    "source", "resonator", "waveguide", "filter", "transducer", "receiver",
    "indicator", "passive_boundary",
)
LAYERS: Dict[int, str] = {
    1: "material_and_microscopic_response",
    2: "blocks_masonry_interfaces_cavities",
    3: "monument_and_ensemble_mechanics",
    4: "acoustics_infrasound_gas_thermal",
    5: "hydrology_and_hydraulic_coupling",
    6: "electromagnetic_and_electrical_response",
    7: "site_environment_and_geosphere",
    8: "earth_scale_response",
    9: "planetary_solar_cosmic_context",
}
# Open functional-object ensemble.  Not limited to three pyramids and one stump.
FUNCTIONAL_OBJECT_IDS: Tuple[str, ...] = (
    "khufu", "khafre", "menkaure", "queens_pyramids",
    "khafre_temple_causeway", "sphinx_parent_massif", "sphinx_temple_complex",
    "bedrock", "plateau_substrate",
)
CORE_NODES: Tuple[str, ...] = FUNCTIONAL_OBJECT_IDS  # backward-compatible alias
SYMBOLIC_OBJECT_IDS: Tuple[str, ...] = (
    "material_domain", "interfaces_domain", "acoustic_domain", "hydrology_domain",
    "em_domain", "environment_domain", "earth_domain", "cosmic_domain",
)
COUPLING_FAMILIES: Tuple[str, ...] = (
    "none", "elastic", "acoustic", "gas_thermal", "hydrologic", "electromagnetic", "mixed",
)
HYPOTHESIS_FAMILY: Dict[str, str] = {
    "H_ELASTIC_SUBSTRATE": "elastic",
    "H_ACOUSTIC_CAVITY": "acoustic",
    "H_GAS_THERMAL_DRAFT": "gas_thermal",
    "H_HYDRAULIC_PATH": "hydrologic",
    "H_EM_TRANSDUCER": "electromagnetic",
    "H_MIXED_CONTROLLED": "mixed",
}
MATRIX_PARAMETER_NAMES: Tuple[str, ...] = (
    "khufu_mass_kg", "khafre_mass_kg", "menkaure_mass_kg", "queens_pyramids_mass_kg",
    "khafre_temple_causeway_mass_kg", "sphinx_parent_massif_mass_kg",
    "sphinx_temple_complex_mass_kg", "bedrock_fragment_mass_kg", "plateau_substrate_mass_kg",
    "khufu_vertical_stiffness_N_per_m", "khafre_vertical_stiffness_N_per_m",
    "menkaure_vertical_stiffness_N_per_m", "queens_pyramids_vertical_stiffness_N_per_m",
    "khafre_temple_causeway_vertical_stiffness_N_per_m",
    "sphinx_parent_massif_vertical_stiffness_N_per_m",
    "sphinx_temple_complex_vertical_stiffness_N_per_m",
    "bedrock_vertical_stiffness_N_per_m", "plateau_substrate_vertical_stiffness_N_per_m",
    "contact_khufu_khafre_N_per_m", "contact_khafre_menkaure_N_per_m",
    "contact_khufu_sphinx_N_per_m", "contact_sphinx_bedrock_N_per_m",
    "contact_khufu_bedrock_N_per_m", "contact_khafre_bedrock_N_per_m",
    "contact_menkaure_bedrock_N_per_m", "contact_khufu_queens_N_per_m",
    "contact_khafre_temple_causeway_N_per_m", "contact_sphinx_parent_temple_N_per_m",
    "contact_bedrock_plateau_N_per_m", "contact_khufu_plateau_N_per_m",
    "contact_khafre_plateau_N_per_m", "contact_menkaure_plateau_N_per_m",
    "dashpot_acoustic_khufu_sphinx_N_s_per_m",
    "dashpot_gas_thermal_khafre_sphinx_N_s_per_m",
    "dashpot_mixed_khufu_sphinx_N_s_per_m",
    "damping_ratio_zeta", "driver_force_amplitude_N",
    "radiation_aperture_area_m2", "radiation_medium_density_kg_per_m3",
    "radiation_medium_wave_speed_m_per_s", "radiation_ka_validity_max",
)
UNIT_EXPONENTS: Dict[str, Tuple[int, int, int]] = {
    "kg": (1, 0, 0), "m": (0, 1, 0), "m^2": (0, 2, 0), "s": (0, 0, 1),
    "N": (1, 1, -2), "N/m": (1, 0, -2), "N*s/m": (1, 0, -1), "kg/s": (1, 0, -1),
    "m/s": (0, 1, -1), "m/N": (-1, 0, 2), "W": (1, 2, -3), "J": (1, 2, -2),
    "rad/s": (0, 0, -1), "Hz": (0, 0, -1), "dimensionless": (0, 0, 0),
    "kg/m^3": (1, -3, 0), "count": (0, 0, 0),
}
NUMERIC_TOLERANCE = 1.0e-9
ENERGY_RELATIVE_TOLERANCE = 1.0e-8
EIGEN_TOLERANCE = 1.0e-12
MAX_JACOBI_SWEEPS = 200
REFINEMENT_ITERATIONS = 28


class ValidationError(ValueError):
    """Raised when a JSON artifact violates the declared package contract."""


class ConvergenceError(RuntimeError):
    """Raised when the deterministic eigensolver fails to converge."""


def load_json(filename: str) -> Dict[str, Any]:
    with open(os.path.join(HERE, filename), "r", encoding="utf-8") as handle:
        return json.load(handle)


def scenario_schema() -> Dict[str, Any]:
    return load_json("scenario_schema.json")


def source_register() -> Dict[str, Any]:
    return load_json("source_register.json")


def parameter_registry() -> Dict[str, Any]:
    return load_json("parameter_registry.json")


def bridge_catalog() -> Dict[str, Any]:
    return load_json("scale_bridge_catalog.json")


def functional_object_registry() -> Dict[str, Any]:
    return load_json("functional_objects.json")


def real_source_ingestion_contract() -> Dict[str, Any]:
    return load_json("real_source_ingestion_contract.json")


# ---------------------------------------------------------------------------
# Validation (no third-party schema dependency)
# ---------------------------------------------------------------------------

def validate_evidence_class(value: Any, path: str = "evidence_class") -> str:
    if value not in EVIDENCE_CLASSES:
        raise ValidationError("{0}: unknown evidence class {1!r}".format(path, value))
    return value


def validate_bridge_status(value: Any, path: str = "status") -> str:
    if value not in BRIDGE_STATUSES:
        raise ValidationError("{0}: unknown bridge status {1!r}".format(path, value))
    return value


def _reject_unprovenanced(value: Any, path: str, flag: bool) -> None:
    if not flag and value in PROVENANCE_RESTRICTED_CLASSES:
        raise ValidationError("{0}: class {1!r} needs attached sources".format(path, value))


def validate_scenario(scenario: Dict[str, Any]) -> bool:
    schema = scenario_schema()
    if not isinstance(scenario, dict):
        raise ValidationError("scenario must be a JSON object")
    for key in schema["required_fields"]:
        if key not in scenario:
            raise ValidationError("scenario missing required field {0!r}".format(key))
    if scenario["schema_version"] != "1.0":
        raise ValidationError("schema_version must be '1.0'")
    if not re.match(schema["scenario_id_pattern"], str(scenario["scenario_id"])):
        raise ValidationError("invalid scenario_id {0!r}".format(scenario["scenario_id"]))
    for key in ("label", "description", "notes"):
        if not isinstance(scenario[key], str):
            raise ValidationError("{0} must be a string".format(key))
    if scenario["synthetic"] is not True:
        raise ValidationError("bundled scenarios must be labelled synthetic=true")
    if not isinstance(scenario["evidence_basis"], list) or not scenario["evidence_basis"]:
        raise ValidationError("evidence_basis must be a nonempty list")
    for item in scenario["evidence_basis"]:
        validate_evidence_class(item, "evidence_basis")
        _reject_unprovenanced(item, "evidence_basis", False)
    if scenario["geometry_state"] not in schema["properties"]["geometry_state"]["enum"]:
        raise ValidationError("invalid geometry_state")
    if not isinstance(scenario["active_layers"], list) or not scenario["active_layers"]:
        raise ValidationError("active_layers must be a nonempty list")
    for layer in scenario["active_layers"]:
        if not isinstance(layer, int) or layer not in LAYERS:
            raise ValidationError("invalid layer number {0!r}".format(layer))
    if not isinstance(scenario["enabled_modules"], list):
        raise ValidationError("enabled_modules must be a list")
    if len(set(scenario["enabled_modules"])) != len(scenario["enabled_modules"]):
        raise ValidationError("enabled_modules contains duplicates")
    hypotheses = scenario["enabled_hypotheses"]
    if not isinstance(hypotheses, list) or len(hypotheses) > 1:
        raise ValidationError("enabled_hypotheses must contain at most one hypothesis")
    for hypothesis in hypotheses:
        if hypothesis not in HYPOTHESIS_FAMILY:
            raise ValidationError("unknown hypothesis {0!r}".format(hypothesis))
    families = scenario["coupling_families"]
    if not isinstance(families, list) or not families:
        raise ValidationError("coupling_families must be nonempty")
    for family in families:
        if family not in COUPLING_FAMILIES:
            raise ValidationError("unknown coupling family {0!r}".format(family))
    if scenario["driver_node"] not in FUNCTIONAL_OBJECT_IDS or scenario["receiver_node"] not in FUNCTIONAL_OBJECT_IDS:
        raise ValidationError("driver_node and receiver_node must be functional-object ids")
    if not isinstance(scenario["parameter_overrides"], dict):
        raise ValidationError("parameter_overrides must be an object")
    known_parameters = parameter_names()
    for name, value in scenario["parameter_overrides"].items():
        if name not in known_parameters:
            raise ValidationError("unknown overridden parameter {0!r}".format(name))
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError("parameter override {0!r} must be numeric".format(name))
        if not math.isfinite(float(value)):
            raise ValidationError("parameter override {0!r} must be finite".format(name))
    scale = scenario["coupling_scale"]
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not 0.0 <= float(scale) <= 1.0:
        raise ValidationError("coupling_scale must be in [0,1]")
    if not isinstance(scenario["falsifiers"], list) or not scenario["falsifiers"]:
        raise ValidationError("falsifiers must be a nonempty list")
    if scenario["outbound_communication_claim"] is not False:
        raise ValidationError("outbound_communication_claim must be false")
    if not isinstance(scenario["natural_background_comparator_required"], bool):
        raise ValidationError("natural_background_comparator_required must be boolean")
    prefix = str(scenario["scenario_id"])[:2]
    if prefix == "S3":
        if float(scale) != 0.0 or families != ["none"] or hypotheses:
            raise ValidationError("S3_PASSIVE_NULL requires zero coupling and no hypotheses")
    if prefix == "S4":
        if len(hypotheses) != 1 or "none" in families:
            raise ValidationError("S4 requires exactly one enabled hypothesis and a non-none family")
    if prefix == "S5" and scenario["natural_background_comparator_required"] is not True:
        raise ValidationError("S5 requires a natural background comparator")
    return True


def validate_source_register(register: Optional[Dict[str, Any]] = None) -> bool:
    register = register if register is not None else source_register()
    if register.get("external_citations_attached") is not False:
        raise ValidationError("source_register must declare no attached external citations")
    if register.get("sources") != []:
        raise ValidationError("no external sources may be fabricated")
    if "not" not in register.get("statement", "").lower():
        raise ValidationError("source_register must state the no-citation condition")
    return True


def validate_parameter_registry(registry: Optional[Dict[str, Any]] = None) -> bool:
    registry = registry if registry is not None else parameter_registry()
    attached = registry.get("external_citations_attached") is True
    if registry.get("external_citations_attached") is not False:
        raise ValidationError("parameter registry must have no attached external citations")
    seen = set()
    for record in registry["parameters"]:
        for key in ("name", "description", "unit", "value", "interval", "evidence_class",
                    "source_id", "frame", "vertical_datum", "epoch", "transformation",
                    "transformation_uncertainty", "uncertainty", "confidence", "activated",
                    "limitations", "discriminating_measurement"):
            if key not in record:
                raise ValidationError("parameter record missing {0!r}".format(key))
        if record["name"] in seen:
            raise ValidationError("duplicate parameter {0!r}".format(record["name"]))
        seen.add(record["name"])
        validate_evidence_class(record["evidence_class"], "parameter " + record["name"])
        _reject_unprovenanced(record["evidence_class"], "parameter " + record["name"], attached)
        if not record["unit"]:
            raise ValidationError("unit required for " + record["name"])
        if record["unit"] not in UNIT_EXPONENTS:
            raise ValidationError("unknown unit {0!r} for {1}".format(record["unit"], record["name"]))
        if record["value"] is None and record["evidence_class"] != "unknown":
            raise ValidationError("null value requires evidence class unknown: " + record["name"])
        if record["evidence_class"] == "unknown" and record["value"] is not None:
            raise ValidationError("unknown evidence class requires null value: " + record["name"])
        if record["value"] is not None:
            if isinstance(record["value"], bool) or not isinstance(record["value"], (int, float)):
                raise ValidationError("parameter value must be numeric: " + record["name"])
            if not math.isfinite(float(record["value"])):
                raise ValidationError("parameter value must be finite: " + record["name"])
            if record["source_id"] != "synthetic_reference_fixture":
                raise ValidationError("no fabricated source ids permitted")
        if not isinstance(record["activated"], bool):
            raise ValidationError("activated must be boolean: " + record["name"])
        if not record["limitations"] or not record["discriminating_measurement"]:
            raise ValidationError("limitations and discriminating_measurement required: " + record["name"])
    return True


BRIDGE_REQUIRED_FIELDS = (
    "bridge_id", "direction", "source_layer", "source_state", "target_layer",
    "target_state", "carrier", "propagation_path", "physical_medium", "interfaces",
    "receiver_layer", "measurable_output", "mode_shape_overlap", "coupling_coefficient",
    "phase_and_delay", "attenuation_quality_factor", "transfer_efficiency",
    "input_power_W", "output_power_W", "conservation_closure", "frequency_time_validity",
    "spatial_validity", "uncertainty", "evidence_class", "source_id",
    "competing_explanations", "falsifier", "status", "notes",
)


def validate_bridge_catalog(catalog: Optional[Dict[str, Any]] = None) -> bool:
    catalog = catalog if catalog is not None else bridge_catalog()
    if catalog.get("external_citations_attached") is not False:
        raise ValidationError("bridge catalog must have no attached external citations")
    statuses = set()
    directions = set()
    for record in catalog["bridges"]:
        for key in BRIDGE_REQUIRED_FIELDS:
            if key not in record:
                raise ValidationError("bridge record missing {0!r}".format(key))
        validate_bridge_status(record["status"], record["bridge_id"])
        validate_evidence_class(record["evidence_class"], record["bridge_id"])
        _reject_unprovenanced(record["evidence_class"], record["bridge_id"], False)
        if record["direction"] not in ("inbound", "outbound"):
            raise ValidationError("bridge direction must be inbound or outbound")
        for layer in (record["source_layer"], record["target_layer"], record["receiver_layer"]):
            if layer not in LAYERS:
                raise ValidationError("invalid bridge layer")
        if not record["falsifier"] or not record["conservation_closure"]:
            raise ValidationError("bridge needs falsifier and conservation closure")
        if record["source_id"] != "synthetic_reference_fixture":
            raise ValidationError("no fabricated bridge source ids")
        statuses.add(record["status"])
        directions.add(record["direction"])
    if "inbound" not in directions or "outbound" not in directions:
        raise ValidationError("both inbound and outbound records are required")
    if "conservation_bounded_not_attributed" not in statuses or "analogy_only" not in statuses:
        raise ValidationError("conservation-bounded and analogy-only non-bridges are required")
    if "bounded_negligible" in statuses:
        raise ValidationError("bounded_negligible needs a measured background; none is attached")
    if "no_direct_cosmic_jump_rule" not in catalog:
        raise ValidationError("catalog must declare the no-direct-cosmic-jump rule")
    return True


def validate_functional_object_registry(registry: Optional[Dict[str, Any]] = None) -> bool:
    registry = registry if registry is not None else functional_object_registry()
    units = {record["name"]: record["unit"] for record in parameter_registry()["parameters"]}
    if registry.get("external_citations_attached") is not False:
        raise ValidationError("functional-object registry must have no attached sources")
    objects = registry["objects"]
    if tuple(obj["id"] for obj in objects) != FUNCTIONAL_OBJECT_IDS:
        raise ValidationError("functional-object ids disagree with model constants")
    for obj in objects:
        if units.get(obj["mass_parameter"]) != "kg":
            raise ValidationError("object mass parameter must be kg: " + obj["id"])
        if units.get(obj["stiffness_parameter"]) != "N/m":
            raise ValidationError("object stiffness parameter must be N/m: " + obj["id"])
        if obj["layer"] not in LAYERS:
            raise ValidationError("invalid functional-object layer")
    known = set(FUNCTIONAL_OBJECT_IDS)
    for contact in registry["contacts"]:
        if contact["source"] not in known or contact["target"] not in known:
            raise ValidationError("contact references an unknown functional object")
        if contact.get("spring_parameter") and units.get(contact["spring_parameter"]) != "N/m":
            raise ValidationError("contact spring must be N/m: " + contact["id"])
    for coupling in registry["hypothesis_couplings"]:
        if coupling["family"] not in COUPLING_FAMILIES:
            raise ValidationError("unknown hypothesis coupling family")
        coefficient = coupling.get("coefficient_parameter")
        if coupling["evaluable"] and not (coefficient or coupling.get("spring_parameter")):
            raise ValidationError("evaluable coupling needs a viscous or spring coefficient parameter")
        if coefficient and units.get(coefficient) != "N*s/m":
            raise ValidationError("viscous coupling coefficient must be N*s/m")
        if not coupling["evaluable"] and coupling.get("status") != "not_evaluable_missing_data":
            raise ValidationError("incomputable coupling must be not_evaluable_missing_data")
    if registry["radiating_ports"][0]["object_id"] not in known:
        raise ValidationError("radiation port references an unknown object")
    for name in ("radiation_aperture_area_m2", "radiation_medium_density_kg_per_m3",
                 "radiation_medium_wave_speed_m_per_s", "radiation_ka_validity_max"):
        if name not in units:
            raise ValidationError("missing radiation parameter " + name)
    return True


def validate_real_source_contract(contract: Optional[Dict[str, Any]] = None) -> bool:
    contract = contract if contract is not None else real_source_ingestion_contract()
    if contract.get("sources") != []:
        raise ValidationError("no real source may be claimed before verification")
    if contract.get("ingestion_state") != "awaiting_verified_sources":
        raise ValidationError("ingestion_state must be awaiting_verified_sources")
    if not contract.get("required_source_fields"):
        raise ValidationError("real-source contract needs required_source_fields")
    if contract.get("external_citations_attached") is not False:
        raise ValidationError("real-source layer must start with no attached citations")
    return True


# ---------------------------------------------------------------------------
# Registries and scenario factory
# ---------------------------------------------------------------------------

def parameter_names() -> set:
    return {p["name"] for p in parameter_registry()["parameters"]}


def parameter_value(name: str) -> Optional[float]:
    for record in parameter_registry()["parameters"]:
        if record["name"] == name:
            return record["value"]
    raise KeyError(name)


def parameter_unit(name: str) -> str:
    for record in parameter_registry()["parameters"]:
        if record["name"] == name:
            return record["unit"]
    raise KeyError(name)


def base_parameters() -> Dict[str, float]:
    """Numerically activated values only; unresolved (null) parameters are excluded."""
    result = {}
    for record in parameter_registry()["parameters"]:
        if record["activated"] and record["value"] is not None:
            result[record["name"]] = float(record["value"])
    return result


def make_scenario(scenario_id: str, **overrides: Any) -> Dict[str, Any]:
    if scenario_id not in scenario_family_ids():
        raise KeyError("unknown scenario family " + str(scenario_id))
    scenario = copy.deepcopy(_scenario_templates()[scenario_id])
    scenario.update(overrides)
    validate_scenario(scenario)
    return scenario


def scenario_family_ids() -> Tuple[str, ...]:
    return (
        "S0_CURRENT_OBSERVED", "S1_PARENT_GEOLOGY_RECONSTRUCTION",
        "S2_IDEALIZED_REFERENCE_COMPLEX", "S3_PASSIVE_NULL",
        "S4_ELASTIC", "S4_ACOUSTIC", "S4_GAS_THERMAL", "S4_HYDROLOGIC",
        "S4_ELECTROMAGNETIC", "S4_MIXED", "S5_ENVIRONMENTAL_DRIVERS",
    )


def all_scenarios() -> Dict[str, Dict[str, Any]]:
    return {key: make_scenario(key) for key in scenario_family_ids()}


def _scenario_templates() -> Dict[str, Dict[str, Any]]:
    common_falsifier = "Synthetic matrices fail a passivity, contact-sign, energy or dimensional control."
    templates: Dict[str, Dict[str, Any]] = {}

    def base(scenario_id: str, label: str, description: str, geometry_state: str,
             evidence: Sequence[str], layers: Sequence[int], modules: Sequence[str]) -> Dict[str, Any]:
        return {
            "schema_version": "1.0", "scenario_id": scenario_id, "label": label,
            "description": description, "synthetic": True,
            "evidence_basis": list(evidence), "geometry_state": geometry_state,
            "active_layers": list(layers), "enabled_modules": list(modules),
            "enabled_hypotheses": [], "coupling_families": ["elastic"],
            "driver_node": "khufu", "receiver_node": "bedrock",
            "parameter_overrides": {}, "coupling_scale": 1.0,
            "falsifiers": [common_falsifier],
            "notes": "Synthetic reference fixture; no external citation or historical claim.",
            "natural_background_comparator_required": False,
            "outbound_communication_claim": False,
        }

    modules_core = ["L1_HOMOGENIZED_MATERIAL", "L2_LUMPED_INTERFACES",
                    "L3_REDUCED_ORDER_MECHANICS", "L7_SUBSTRATE_ENVIRONMENT"]
    templates["S0_CURRENT_OBSERVED"] = base(
        "S0_CURRENT_OBSERVED", "Synthetic stand-in for present-observed geometry",
        "Illustrates how a present-state scenario would be encoded; actual measured geometry is absent, so values remain synthetic.",
        "observed", ["unknown", "idealized_design"], [1, 2, 3, 7], modules_core)
    templates["S0_CURRENT_OBSERVED"]["notes"] += " No real damage survey is attached; 'observed' is a structural placeholder only."

    templates["S1_PARENT_GEOLOGY_RECONSTRUCTION"] = base(
        "S1_PARENT_GEOLOGY_RECONSTRUCTION", "P0/P1 parent-outcrop placeholder (synthetic)",
        "Separates a synthetic natural parent geometry G_0 from an anthropogenic residual G_1. No geological claim is made because no source is attached.",
        "reconstructed", ["idealized_design", "assumption_for_sensitivity", "unknown"],
        [1, 2, 3, 7], modules_core)
    templates["S1_PARENT_GEOLOGY_RECONSTRUCTION"]["notes"] += " Sphinx parent massif only; no invented cavity or original form."

    templates["S2_IDEALIZED_REFERENCE_COMPLEX"] = base(
        "S2_IDEALIZED_REFERENCE_COMPLEX", "Synthetic idealized functional-object ensemble",
        "Declared coherent layout of many functional objects exercising the equations; not a historical completion claim.",
        "idealized", ["idealized_design", "assumption_for_sensitivity", "unknown"],
        [1, 2, 3, 4, 7], modules_core + ["L4_IDEALIZED_ACOUSTIC_PLACEHOLDER"])
    templates["S2_IDEALIZED_REFERENCE_COMPLEX"]["notes"] += " Layer 4 is represented, not computed: no cavity volume is specified."

    templates["S3_PASSIVE_NULL"] = base(
        "S3_PASSIVE_NULL", "Passive-first null with zero engineered coupling",
        "All off-diagonal transfer terms are set to zero; functional-object DOFs reduce to independent subsystems.",
        "passive_null", ["idealized_design", "assumption_for_sensitivity"], [1, 3, 7], modules_core)
    templates["S3_PASSIVE_NULL"].update({
        "coupling_families": ["none"], "coupling_scale": 0.0,
        "notes": "Synthetic passive null; independent subsystems. Absence of a detected effect is not proof of absence.",
    })

    hypothesis_specs = (
        ("S4_ELASTIC", "H_ELASTIC_SUBSTRATE", "elastic", "L3_REDUCED_ORDER_MECHANICS"),
        ("S4_ACOUSTIC", "H_ACOUSTIC_CAVITY", "acoustic", "L4_IDEALIZED_ACOUSTIC_PLACEHOLDER"),
        ("S4_GAS_THERMAL", "H_GAS_THERMAL_DRAFT", "gas_thermal", "L4_IDEALIZED_ACOUSTIC_PLACEHOLDER"),
        ("S4_HYDROLOGIC", "H_HYDRAULIC_PATH", "hydrologic", "L5_SYMBOLIC_HYDROLOGY"),
        ("S4_ELECTROMAGNETIC", "H_EM_TRANSDUCER", "electromagnetic", "L6_SYMBOLIC_ELECTROMAGNETICS"),
        ("S4_MIXED", "H_MIXED_CONTROLLED", "mixed", "L4_IDEALIZED_ACOUSTIC_PLACEHOLDER"),
    )
    for scenario_id, hypothesis, family, module in hypothesis_specs:
        scenario = base(
            scenario_id, "Candidate coupling family " + family,
            "One hypothesis enabled at a time; compare against S3_PASSIVE_NULL for attribution.",
            "hypothesis", ["speculative_hypothesis", "assumption_for_sensitivity", "unknown"],
            [1, 2, 3, 4, 5, 6, 7], list(dict.fromkeys(modules_core + [module])))
        scenario.update({"enabled_hypotheses": [hypothesis], "coupling_families": [family]})
        scenario["notes"] += " Hypothesis is a test candidate, not a historical mechanism."
        templates[scenario_id] = scenario

    templates["S5_ENVIRONMENTAL_DRIVERS"] = base(
        "S5_ENVIRONMENTAL_DRIVERS", "External drivers with natural background comparator",
        "Inbound solar/tidal/seismic/geomagnetic forcing represented separately; outbound attribution is not claimed.",
        "observed", ["assumption_for_sensitivity", "unknown"], [1, 3, 7, 8, 9],
        modules_core + ["L8_EARTH_CONTEXT", "L9_COSMIC_CONTEXT", "NATURAL_BACKGROUND_COMPARATOR"])
    templates["S5_ENVIRONMENTAL_DRIVERS"].update({
        "natural_background_comparator_required": True,
        "notes": "Natural background comparator is synthetic; no measured ambient spectrum is attached.",
    })
    return templates


# ---------------------------------------------------------------------------
# Typed system graph
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GraphNode:
    id: str
    layer: int
    kind: str
    status: str
    evidence_class: str
    description: str
    role_candidates: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        payload = dict(self.__dict__)
        payload["role_candidates"] = list(self.role_candidates)
        return payload


@dataclass(frozen=True)
class GraphEdge:
    id: str
    source: str
    target: str
    carrier: str
    direction: str
    transfer_model: str
    uncertainty: str
    status: str
    falsifier: str
    evidence_class: str
    bridge_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SystemGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        if node.id in self.nodes:
            raise ValidationError("duplicate graph node " + node.id)
        if node.layer not in LAYERS:
            raise ValidationError("invalid graph node layer")
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValidationError("graph edge references unknown node")
        if edge.direction not in ("inbound", "outbound", "internal"):
            raise ValidationError("invalid edge direction")
        validate_bridge_status(edge.status, edge.id)
        validate_evidence_class(edge.evidence_class, edge.id)
        if not edge.falsifier:
            raise ValidationError("edge needs a falsifier")
        self.edges.append(edge)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [self.nodes[key].to_dict() for key in sorted(self.nodes)],
            "edges": [edge.to_dict() for edge in self.edges],
            "layer_taxonomy": {str(k): v for k, v in sorted(LAYERS.items())},
        }


def system_graph_for_scenario(scenario: Dict[str, Any]) -> SystemGraph:
    validate_scenario(scenario)
    graph = SystemGraph()
    registry = functional_object_registry()
    for obj in registry["objects"]:
        graph.add_node(GraphNode(
            id=obj["id"], layer=obj["layer"], kind=obj["object_class"],
            status="active" if obj["id"] in ("bedrock", "plateau_substrate") else "synthetic_placeholder",
            evidence_class=obj["evidence_class"], description=obj["description"],
            role_candidates=tuple(obj["role_candidates"])))
    for node_id, layer, kind, description, roles in (
        ("material_domain", 1, "material", "Homogenized material placeholder; no tensor resolved.", ("passive_boundary",)),
        ("interfaces_domain", 2, "interfaces", "Block/joint contacts; friction and cavities unresolved.", ("filter",)),
        ("acoustic_domain", 4, "field_domain", "No cavity volume specified; acoustic spectrum not evaluable.", ("resonator", "waveguide")),
        ("hydrology_domain", 5, "field_domain", "Water table and permeability unresolved.", ("filter",)),
        ("em_domain", 6, "field_domain", "Conductivity tensor and circuit unresolved.", ("transducer",)),
        ("environment_domain", 7, "boundary_domain", "Synthetic environmental boundary forcing.", ("source",)),
        ("earth_domain", 8, "boundary_domain", "Earth-scale context; no established Giza causal bridge.", ("receiver",)),
        ("cosmic_domain", 9, "context_domain", "External forcing context; no outbound communication claim.", ("source", "indicator")),
    ):
        graph.add_node(GraphNode(node_id, layer, kind, "represented_not_computed" if layer < 8 else "context_only",
                                 "unknown", description, roles))

    catalog = bridge_catalog()
    by_id = {record["bridge_id"]: record for record in catalog["bridges"]}
    if float(scenario["coupling_scale"]) > 0.0:
        for contact in registry["contacts"]:
            bridge_id = contact["bridge_id"]
            record = by_id[bridge_id]
            graph.add_edge(GraphEdge(
                id="E_" + contact["id"], source=contact["source"], target=contact["target"],
                carrier="elastic", direction="internal", transfer_model="grounded_two_node_spring",
                uncertainty=record["uncertainty"], status=record["status"],
                falsifier=record["falsifier"], evidence_class=record["evidence_class"],
                bridge_id=bridge_id))

    hypotheses = scenario["enabled_hypotheses"]
    if hypotheses:
        family = HYPOTHESIS_FAMILY[hypotheses[0]]
        coupling = next(item for item in registry["hypothesis_couplings"] if item["family"] == family)
        record = by_id[coupling["bridge_id"]]
        graph.add_edge(GraphEdge(
            id="E_HYPOTHESIS_" + family.upper(), source=coupling["source"], target=coupling["target"],
            carrier=family if family != "mixed" else "mixed_idealized",
            direction="internal",
            transfer_model=coupling["transfer_model"],
            uncertainty=coupling["reason"] if not coupling["evaluable"] else record["uncertainty"],
            status=coupling["status"], falsifier=record["falsifier"],
            evidence_class=record["evidence_class"], bridge_id=coupling["bridge_id"]))

    if scenario["scenario_id"].startswith("S5"):
        graph.add_edge(GraphEdge(
            id="E_INBOUND_ENVIRONMENT", source="environment_domain", target="bedrock",
            carrier="elastic_environmental", direction="inbound",
            transfer_model="external_forcing_on_active_bedrock",
            uncertainty="synthetic comparator only", status="not_evaluable_missing_data",
            falsifier="Co-located calibrated background monitoring exceeding declared synthetic bound.",
            evidence_class="assumption_for_sensitivity",
            bridge_id="B_IN_SEISMIC_SUBSTRATE_TO_MONUMENTS"))
    return graph


# ---------------------------------------------------------------------------
# Dense linear algebra (standard library only)
# ---------------------------------------------------------------------------

def matrix_zeros(rows: int, cols: Optional[int] = None) -> List[List[float]]:
    cols = rows if cols is None else cols
    return [[0.0 for _ in range(cols)] for _ in range(rows)]


def identity_matrix(size: int) -> List[List[float]]:
    result = matrix_zeros(size)
    for index in range(size):
        result[index][index] = 1.0
    return result


def is_symmetric(matrix: Sequence[Sequence[float]], tolerance: float = NUMERIC_TOLERANCE) -> bool:
    size = len(matrix)
    return all(len(row) == size for row in matrix) and all(
        abs(matrix[i][j] - matrix[j][i]) <= tolerance * max(1.0, abs(matrix[i][j]))
        for i in range(size) for j in range(i + 1, size))


def matmul(left: Sequence[Sequence[float]], right: Sequence[Sequence[float]]) -> List[List[float]]:
    rows, inner = len(left), len(left[0]) if left else 0
    cols = len(right[0]) if right else 0
    if inner and any(len(row) != inner for row in left):
        raise ValueError("left matrix is not rectangular")
    if right and len(right) != inner:
        raise ValueError("matrix dimensions do not agree")
    if right and any(len(row) != cols for row in right):
        raise ValueError("right matrix is not rectangular")
    return [[sum(left[i][k] * right[k][j] for k in range(inner)) for j in range(cols)]
            for i in range(rows)]


def transpose(matrix: Sequence[Sequence[float]]) -> List[List[float]]:
    return [list(row) for row in zip(*matrix)]


def jacobi_eigen(matrix: Sequence[Sequence[float]], tolerance: float = EIGEN_TOLERANCE,
                 max_sweeps: int = MAX_JACOBI_SWEEPS) -> Tuple[List[float], List[List[float]]]:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("jacobi_eigen expects a square matrix")
    if not is_symmetric(matrix, tolerance=1.0e-7):
        raise ValueError("jacobi_eigen expects a symmetric matrix")
    work = [list(row) for row in matrix]
    vectors = identity_matrix(size)
    for _ in range(max_sweeps):
        largest = 0.0
        for p in range(size - 1):
            for q in range(p + 1, size):
                largest = max(largest, abs(work[p][q]))
        if largest <= tolerance:
            break
        for p in range(size - 1):
            for q in range(p + 1, size):
                apq = work[p][q]
                if abs(apq) <= tolerance * 0.01:
                    continue
                tau = (work[q][q] - work[p][p]) / (2.0 * apq)
                if tau >= 0.0:
                    t = 1.0 / (tau + math.sqrt(1.0 + tau * tau))
                else:
                    t = -1.0 / (-tau + math.sqrt(1.0 + tau * tau))
                cosine = 1.0 / math.sqrt(1.0 + t * t)
                sine = t * cosine
                for k in range(size):
                    if k == p or k == q:
                        continue
                    akp, akq = work[k][p], work[k][q]
                    work[k][p] = work[p][k] = cosine * akp - sine * akq
                    work[k][q] = work[q][k] = sine * akp + cosine * akq
                app, aqq = work[p][p], work[q][q]
                work[p][p] = cosine * cosine * app - 2.0 * sine * cosine * apq + sine * sine * aqq
                work[q][q] = sine * sine * app + 2.0 * sine * cosine * apq + cosine * cosine * aqq
                work[p][q] = work[q][p] = 0.0
                for k in range(size):
                    vkp, vkq = vectors[k][p], vectors[k][q]
                    vectors[k][p] = cosine * vkp - sine * vkq
                    vectors[k][q] = sine * vkp + cosine * vkq
    else:
        raise ConvergenceError("Jacobi eigensolver did not converge")
    order = sorted(range(size), key=lambda index: work[index][index])
    eigenvalues = [work[index][index] for index in order]
    eigenvectors = [[vectors[row][index] for index in order] for row in range(size)]
    return eigenvalues, eigenvectors


def symmetric_spd_inverse_sqrt(matrix: Sequence[Sequence[float]]) -> List[List[float]]:
    eigenvalues, eigenvectors = jacobi_eigen(matrix)
    if any(value <= 0.0 for value in eigenvalues):
        raise ValueError("matrix is not positive definite")
    size = len(matrix)
    return [[sum(eigenvectors[i][q] * (1.0 / math.sqrt(eigenvalues[q])) * eigenvectors[j][q]
                 for q in range(size)) for j in range(size)] for i in range(size)]


def complex_solve(coefficients: Sequence[Sequence[complex]],
                  right_hand_side: Sequence[Sequence[complex]]) -> List[List[complex]]:
    size = len(coefficients)
    if size == 0 or any(len(row) != size for row in coefficients):
        raise ValueError("complex_solve expects a square matrix")
    port_count = len(right_hand_side[0]) if right_hand_side else 0
    augmented = [[complex(coefficients[i][j]) for j in range(size)] +
                 [complex(right_hand_side[i][j]) for j in range(port_count)]
                 for i in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1.0e-300:
            raise ValueError("singular dynamic stiffness matrix")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / pivot_value
            if factor == 0:
                continue
            for col in range(column, size + port_count):
                augmented[row][col] -= factor * augmented[column][col]
    solution = [[0j for _ in range(port_count)] for _ in range(size)]
    for row in range(size - 1, -1, -1):
        for col in range(port_count):
            total = augmented[row][size + col]
            for k in range(row + 1, size):
                total -= augmented[row][k] * solution[k][col]
            solution[row][col] = total / augmented[row][row]
    return solution


def quadratic_form(vector: Sequence[complex], matrix: Sequence[Sequence[float]]) -> complex:
    size = len(vector)
    return sum(vector[i].conjugate() * matrix[i][j] * vector[j]
               for i in range(size) for j in range(size))


# ---------------------------------------------------------------------------
# Physically signed two-node elements
# ---------------------------------------------------------------------------

def add_linear_spring(operator: List[List[float]], i: int, j: int, stiffness: float) -> None:
    """Add k*[[1,-1],[-1,1]]: off-diagonals are NEGATIVE for a physical spring."""
    if i == j or stiffness < 0.0:
        raise ValidationError("spring needs two distinct nodes and nonnegative stiffness")
    operator[i][i] += stiffness
    operator[j][j] += stiffness
    operator[i][j] -= stiffness
    operator[j][i] -= stiffness


def add_linear_dashpot(operator: List[List[float]], i: int, j: int, coefficient: float) -> None:
    """Add c*[[1,-1],[-1,1]] with c in N s/m; same sign convention as a spring."""
    if i == j or coefficient < 0.0:
        raise ValidationError("dashpot needs two distinct nodes and nonnegative coefficient")
    operator[i][i] += coefficient
    operator[j][j] += coefficient
    operator[i][j] -= coefficient
    operator[j][i] -= coefficient


# ---------------------------------------------------------------------------
# Reduced-order model assembly
# ---------------------------------------------------------------------------

@dataclass
class ReducedOrderModel:
    scenario: Dict[str, Any]
    node_names: Tuple[str, ...]
    M: List[List[float]]
    C: List[List[float]]
    K: List[List[float]]
    B: List[List[float]]
    Cr: List[List[float]]
    parameters: Dict[str, float]
    coupling_scale: float
    radiation_port: Optional[str] = None
    radiation_parameters: Dict[str, float] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.node_names)

    def radiation_resistance(self, omega: float) -> Optional[float]:
        """Low-ka radiation resistance R_rad in N s/m, or None if out of validity."""
        if self.radiation_port is None or not self.radiation_parameters:
            return 0.0
        p = self.radiation_parameters
        area = p["radiation_aperture_area_m2"]
        if area <= 0.0:
            return 0.0
        radius = math.sqrt(area / math.pi)
        ka = omega * radius / p["radiation_medium_wave_speed_m_per_s"]
        if ka > p["radiation_ka_validity_max"]:
            return None
        return 0.5 * p["radiation_medium_density_kg_per_m3"] * p["radiation_medium_wave_speed_m_per_s"] * area * ka * ka

    def damping_matrix_at(self, omega: float) -> Tuple[List[List[float]], Optional[float]]:
        resistance = self.radiation_resistance(omega)
        damping = [list(row) for row in self.C]
        if resistance and resistance > 0.0:
            port = self.node_names.index(self.radiation_port)
            damping[port][port] += resistance
        return damping, resistance

    def dynamic_stiffness(self, omega: float) -> List[List[float]]:
        damping, _ = self.damping_matrix_at(omega)
        size = self.size
        return [[complex(self.K[i][j] - omega * omega * self.M[i][j] +
                         1j * omega * damping[i][j]) for j in range(size)] for i in range(size)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario["scenario_id"],
            "node_names": list(self.node_names),
            "functional_object_count": len(self.node_names),
            "M": self.M, "C": self.C, "K": self.K, "B": self.B, "Cr": self.Cr,
            "coupling_scale": self.coupling_scale,
            "radiation_port": self.radiation_port,
            "radiation_parameters": dict(sorted(self.radiation_parameters.items())),
            "parameters": {key: self.parameters[key] for key in sorted(self.parameters)},
        }


def hypothesis_activation_report(model: ReducedOrderModel) -> Dict[str, Any]:
    """State which hypothesis family was numerically activated, with units."""
    hypotheses = model.scenario["enabled_hypotheses"]
    if not hypotheses:
        return {"family": "none", "evaluable": False, "operator_modified": False,
                "carrier_kind": "none", "unit": None, "status": "not_applicable"}
    family = HYPOTHESIS_FAMILY[hypotheses[0]]
    registry = functional_object_registry()
    coupling = next(item for item in registry["hypothesis_couplings"] if item["family"] == family)
    register = {record["name"]: record["unit"] for record in parameter_registry()["parameters"]}
    coefficient = coupling.get("coefficient_parameter")
    spring_parameter = coupling.get("spring_parameter")
    unit = register.get(coefficient or spring_parameter or "", None)
    return {
        "family": family,
        "evaluable": bool(coupling["evaluable"]),
        "operator_modified": bool(coupling["evaluable"]) and model.coupling_scale > 0.0,
        "carrier_kind": coupling["transfer_model"],
        "unit": unit,
        "coefficient_parameter": coefficient or spring_parameter,
        "status": coupling["status"],
        "reason": coupling.get("reason", ""),
    }


def assemble_model(scenario: Optional[Dict[str, Any]] = None,
                   overrides: Optional[Dict[str, float]] = None) -> ReducedOrderModel:
    """Assemble M, C, K, B, Cr from the functional-object registry.

    Contact springs and dashpots use the physically signed two-node element.
    Radiation is a separate frequency-dependent port, never a fraction of C.
    """
    if scenario is None:
        scenario = make_scenario("S0_CURRENT_OBSERVED")
    validate_scenario(scenario)
    registry_values = base_parameters()
    parameters = {name: registry_values.get(name, parameter_value(name))
                  for name in MATRIX_PARAMETER_NAMES}
    if overrides:
        for name, value in overrides.items():
            if name not in MATRIX_PARAMETER_NAMES:
                raise KeyError("not a numeric model parameter: " + str(name))
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValidationError("parameter override must be finite numeric: " + str(name))
            parameters[name] = float(value)
    for name, value in scenario["parameter_overrides"].items():
        if name in parameters:
            parameters[name] = float(value)

    scale = float(scenario["coupling_scale"])
    objects = functional_object_registry()
    masses = [parameters[obj["mass_parameter"]] for obj in objects["objects"]]
    stiffnesses = [parameters[obj["stiffness_parameter"]] for obj in objects["objects"]]
    if any(value <= 0.0 for value in masses + stiffnesses):
        raise ValidationError("mass and stiffness must be strictly positive")
    zeta = parameters["damping_ratio_zeta"]
    if not 0.0 <= zeta < 1.0:
        raise ValidationError("damping ratio must be in [0,1)")

    size = len(FUNCTIONAL_OBJECT_IDS)
    index_of = {name: index for index, name in enumerate(FUNCTIONAL_OBJECT_IDS)}
    M = matrix_zeros(size)
    C = matrix_zeros(size)
    K = matrix_zeros(size)
    for index in range(size):
        M[index][index] = masses[index]
        K[index][index] = stiffnesses[index]  # grounding stiffness to the synthetic reference
        C[index][index] = 2.0 * zeta * math.sqrt(stiffnesses[index] * masses[index])  # N s/m

    if scale > 0.0:
        for contact in objects["contacts"]:
            stiffness = scale * parameters[contact["spring_parameter"]]
            add_linear_spring(K, index_of[contact["source"]], index_of[contact["target"]], stiffness)

    hypotheses = scenario["enabled_hypotheses"]
    if hypotheses and scale > 0.0:
        family = HYPOTHESIS_FAMILY[hypotheses[0]]
        coupling = next(item for item in objects["hypothesis_couplings"] if item["family"] == family)
        if coupling["evaluable"]:
            i, j = index_of[coupling["source"]], index_of[coupling["target"]]
            coefficient = coupling.get("coefficient_parameter")
            if coefficient:
                if parameter_unit(coefficient) != "N*s/m":
                    raise ValidationError("hypothesis damping coefficient must be N s/m")
                add_linear_dashpot(C, i, j, scale * parameters[coefficient])
            elif coupling.get("spring_parameter"):
                if parameter_unit(coupling["spring_parameter"]) != "N/m":
                    raise ValidationError("hypothesis stiffness must be N/m")
                add_linear_spring(K, i, j, scale * parameters[coupling["spring_parameter"]])
        # Incomputable families add NO operator term: missing equation/parameter stays missing.

    driver = index_of[scenario["driver_node"]]
    receiver = index_of[scenario["receiver_node"]]
    B = matrix_zeros(size, 1)
    Cr = matrix_zeros(1, size)
    B[driver][0] = 1.0
    Cr[0][receiver] = 1.0
    port = objects["radiating_ports"][0]["object_id"]
    radiation_parameters = {name: parameters[name] for name in (
        "radiation_aperture_area_m2", "radiation_medium_density_kg_per_m3",
        "radiation_medium_wave_speed_m_per_s", "radiation_ka_validity_max")}
    return ReducedOrderModel(scenario, FUNCTIONAL_OBJECT_IDS, M, C, K, B, Cr,
                             parameters, scale, port, radiation_parameters)


def multiport_model(model: ReducedOrderModel) -> ReducedOrderModel:
    """Copy with B=I and Cr=I^T so reciprocity H_ij=H_ji can be tested."""
    return ReducedOrderModel(
        model.scenario, model.node_names, model.M, model.C, model.K,
        identity_matrix(model.size), identity_matrix(model.size),
        dict(model.parameters), model.coupling_scale,
        model.radiation_port, dict(model.radiation_parameters))


# ---------------------------------------------------------------------------
# Modal analysis and frequency response
# ---------------------------------------------------------------------------

def natural_modes(model: ReducedOrderModel) -> List[Dict[str, Any]]:
    minv_half = symmetric_spd_inverse_sqrt(model.M)
    weighted = matmul(matmul(minv_half, model.K), minv_half)
    eigenvalues, vectors = jacobi_eigen(weighted)
    if any(value <= 0.0 for value in eigenvalues):
        raise ValueError("stiffness is not positive definite")
    phi = matmul(minv_half, vectors)
    modes = []
    for index, eigenvalue in enumerate(eigenvalues):
        omega = math.sqrt(eigenvalue)
        column = [phi[row][index] for row in range(model.size)]
        modal_damping = quadratic_form(column, model.C).real
        modes.append({
            "index": index,
            "eigenvalue_s_minus2": eigenvalue,
            "omega_rad_per_s": omega,
            "frequency_hz": omega / (2.0 * math.pi),
            "mode_vector_mass_normalized": column,
            "modal_damping_kg_per_s": modal_damping,
            "damping_ratio": modal_damping / (2.0 * omega) if omega > 0 else None,
            "quality_factor": omega / modal_damping if modal_damping > 0.0 else None,
        })
    return modes


def synthetic_frequency_grid(model: ReducedOrderModel, points: int = 161) -> List[float]:
    modes = natural_modes(model)
    low = 0.2 * modes[0]["frequency_hz"]
    high = 1.8 * modes[-1]["frequency_hz"]
    if high <= low:
        raise ValueError("degenerate modal band")
    return [low + (high - low) * index / (points - 1) for index in range(points)]


def frequency_response(model: ReducedOrderModel, frequencies: Sequence[float]) -> List[Dict[str, Any]]:
    results = []
    for frequency in frequencies:
        omega = 2.0 * math.pi * frequency
        solution = complex_solve(model.dynamic_stiffness(omega), model.B)
        response = [[sum(model.Cr[out][i] * solution[i][port] for i in range(model.size))
                     for port in range(len(model.B[0]))] for out in range(len(model.Cr))]
        magnitude = abs(response[0][0])
        results.append({
            "frequency_hz": frequency, "omega_rad_per_s": omega, "H": response,
            "magnitude_m_per_N": magnitude, "phase_rad": cmath.phase(response[0][0]),
            "attenuation_db_re_1_m_per_N": 20.0 * math.log10(magnitude) if magnitude > 0 else float("-inf"),
        })
    return results


def phase_group_delay(responses: Sequence[Dict[str, Any]], index: int) -> Optional[float]:
    if index <= 0 or index >= len(responses) - 1:
        return None
    delta = responses[index + 1]["omega_rad_per_s"] - responses[index - 1]["omega_rad_per_s"]
    if delta == 0.0:
        return None
    return -(responses[index + 1]["phase_rad"] - responses[index - 1]["phase_rad"]) / delta


# ---------------------------------------------------------------------------
# Energy, passivity, conservation and bounds
# ---------------------------------------------------------------------------

def harmonic_displacement(model: ReducedOrderModel, omega: float) -> List[complex]:
    force = [[complex(model.parameters["driver_force_amplitude_N"] * model.B[i][0])
              for _ in range(1)] for i in range(model.size)]
    return [row[0] for row in complex_solve(model.dynamic_stiffness(omega), force)]


def energy_budget(model: ReducedOrderModel, frequency: float) -> Dict[str, Any]:
    omega = 2.0 * math.pi * frequency
    resistance = model.radiation_resistance(omega)
    force_amplitude = model.parameters["driver_force_amplitude_N"]
    force = [complex(force_amplitude * model.B[i][0]) for i in range(model.size)]
    displacement = harmonic_displacement(model, omega)
    velocity = [1j * omega * value for value in displacement]
    p_in = 0.5 * (sum(force[i].conjugate() * velocity[i] for i in range(model.size))).real
    p_material = 0.5 * omega * omega * quadratic_form(displacement, model.C).real
    if resistance is None or resistance <= 0.0 or model.radiation_port is None:
        p_export = 0.0
        export_evaluable = False if resistance is None else True
    else:
        port = model.node_names.index(model.radiation_port)
        p_export = 0.5 * resistance * omega * omega * abs(displacement[port]) ** 2
        export_evaluable = True
    p_stored = 0.25 * (quadratic_form(displacement, model.K).real +
                       omega * omega * quadratic_form(displacement, model.M).real)
    residual = p_in - p_material - p_export
    scale = max(abs(p_in), abs(p_material), abs(p_export), 1.0e-300)
    return {
        "frequency_hz": frequency,
        "input_power_W": p_in,
        "material_dissipation_W": p_material,
        "exported_power_W": p_export,
        "export_efficiency": p_export / p_in if p_in > 0.0 else None,
        "radiation_resistance_N_s_per_m": resistance,
        "export_evaluable": export_evaluable,
        "stored_energy_J": p_stored,
        "energy_residual_W": residual,
        "relative_residual": abs(residual) / scale,
        "conservation_closed": abs(residual) <= ENERGY_RELATIVE_TOLERANCE * scale,
        "export_status": "conservation_bounded_not_attributed" if export_evaluable else "not_evaluable_missing_data",
        "units": {"power": "W", "stored_energy": "J", "radiation_resistance": "N*s/m"},
    }


def passivity_check(model: ReducedOrderModel, frequencies: Sequence[float]) -> Dict[str, Any]:
    damping_eigenvalues, _ = jacobi_eigen(model.C)
    min_power = float("inf")
    worst_residual = 0.0
    all_closed = True
    all_evaluable = True
    for frequency in frequencies:
        budget = energy_budget(model, frequency)
        min_power = min(min_power, budget["input_power_W"])
        worst_residual = max(worst_residual, abs(budget["energy_residual_W"]))
        all_closed = all_closed and budget["conservation_closed"]
        all_evaluable = all_evaluable and budget["export_evaluable"]
    return {
        "min_damping_eigenvalue_kg_per_s": min(damping_eigenvalues),
        "damping_nonnegative": min(damping_eigenvalues) >= -NUMERIC_TOLERANCE,
        "min_input_power_W": min_power,
        "no_net_amplification": min_power >= -NUMERIC_TOLERANCE,
        "worst_absolute_residual_W": worst_residual,
        "all_energy_balances_closed": all_closed,
        "all_export_channels_evaluable": all_evaluable,
        "frequencies_evaluated": len(frequencies),
    }


def outbound_energy_bound(model: ReducedOrderModel, frequency: float) -> Dict[str, Any]:
    budget = energy_budget(model, frequency)
    catalog = bridge_catalog()
    background = catalog["natural_background_comparator"]["power_W"]
    exported = max(0.0, budget["exported_power_W"])
    input_power = max(0.0, budget["input_power_W"])
    return {
        "frequency_hz": frequency,
        "modelled_radiated_upper_bound_W": exported,
        "total_input_upper_bound_W": input_power,
        "any_unmodelled_channel_bound_W": exported if budget["export_evaluable"] else None,
        "synthetic_natural_background_W": background,
        "ratio_to_synthetic_background": exported / background,
        "outbound_communication_claim": False,
        "attribution_allowed": False,
        "status": budget["export_status"],
        "note": "Radiation impedance bound only. The synthetic comparator is not a measured background and cannot justify a negligibility claim.",
    }


def natural_background_comparator(model: ReducedOrderModel, frequency: float) -> Dict[str, Any]:
    catalog = bridge_catalog()
    comparator = catalog["natural_background_comparator"]
    bound = outbound_energy_bound(model, frequency)
    return {
        "synthetic_background_power_W": comparator["power_W"],
        "modelled_export_power_W": bound["modelled_radiated_upper_bound_W"],
        "ratio": bound["ratio_to_synthetic_background"],
        "evidence_class": comparator["evidence_class"],
        "status": comparator["status"],
        "negligibility_claim_allowed": False,
        "interpretation": "Synthetic comparator only. No attribution or negligibility conclusion is permitted until a measured co-located background exists.",
    }


# ---------------------------------------------------------------------------
# Physical-meaning controls (not merely SPD/PSD)
# ---------------------------------------------------------------------------

def reciprocity_check(model: ReducedOrderModel, frequency: float,
                      broken: bool = False) -> Dict[str, Any]:
    multiport = multiport_model(model)
    if broken:
        multiport.C = [list(row) for row in multiport.C]
        multiport.C[0][1] += 1.0e7
    response = frequency_response(multiport, [frequency])[0]["H"]
    size = model.size
    max_asymmetry = max(abs(response[i][j] - response[j][i])
                        for i in range(size) for j in range(size))
    scale = max(abs(response[i][j]) for i in range(size) for j in range(size))
    symmetric = is_symmetric(multiport.M) and is_symmetric(multiport.C) and is_symmetric(multiport.K)
    holds = max_asymmetry <= (1.0e-9 * scale if scale > 0.0 else NUMERIC_TOLERANCE)
    return {
        "frequency_hz": frequency,
        "max_absolute_asymmetry_m_per_N": max_asymmetry,
        "relative_asymmetry": max_asymmetry / scale if scale else 0.0,
        "symmetric_operators": symmetric, "reciprocity_holds": holds,
        "broken_assumption": broken,
    }


def zero_coupling_check(model: ReducedOrderModel, perturbed_index: Optional[int] = None,
                        stiffness_factor: float = 2.0,
                        frequencies: Optional[Sequence[float]] = None) -> Dict[str, Any]:
    grid = list(frequencies) if frequencies else synthetic_frequency_grid(model, points=11)
    base = [item["magnitude_m_per_N"] for item in frequency_response(model, grid)]
    perturbed = ReducedOrderModel(
        model.scenario, model.node_names, [list(row) for row in model.M],
        [list(row) for row in model.C], [list(row) for row in model.K],
        [list(row) for row in model.B], [list(row) for row in model.Cr],
        dict(model.parameters), model.coupling_scale, model.radiation_port,
        dict(model.radiation_parameters))
    target = perturbed_index if perturbed_index is not None else model.size - 1
    perturbed.K[target][target] *= stiffness_factor
    changed = [item["magnitude_m_per_N"] for item in frequency_response(perturbed, grid)]
    max_difference = max(abs(a - b) for a, b in zip(base, changed))
    off_diagonal_stiffness = max(abs(model.K[i][j]) for i in range(model.size)
                                 for j in range(model.size) if i != j)
    off_diagonal_damping = max(abs(model.C[i][j]) for i in range(model.size)
                               for j in range(model.size) if i != j)
    return {
        "max_response_change_m_per_N": max_difference,
        "max_off_diagonal_stiffness_N_per_m": off_diagonal_stiffness,
        "max_off_diagonal_damping_kg_per_s": off_diagonal_damping,
        "independent_subsystems_reproduced": max_difference <= NUMERIC_TOLERANCE * max(1.0, max(base)),
        "frequencies_evaluated": len(grid),
    }


def contact_mechanics_check(model: ReducedOrderModel) -> Dict[str, Any]:
    """SDP is not enough: verify the two-node spring/dashpot sign pattern directly."""
    size = model.size
    positive_k = max([model.K[i][j] for i in range(size) for j in range(size) if i != j] + [0.0])
    positive_c = max([model.C[i][j] for i in range(size) for j in range(size) if i != j] + [0.0])
    diagonally_dominant = all(model.K[i][i] >= sum(abs(model.K[i][j]) for j in range(size) if j != i)
                              - NUMERIC_TOLERANCE for i in range(size))
    registry = functional_object_registry()
    index_of = {name: i for i, name in enumerate(FUNCTIONAL_OBJECT_IDS)}
    expected_k = matrix_zeros(size)
    expected_c = matrix_zeros(size)
    if model.coupling_scale > 0.0:
        for contact in registry["contacts"]:
            value = model.coupling_scale * model.parameters[contact["spring_parameter"]]
            add_linear_spring(expected_k, index_of[contact["source"]], index_of[contact["target"]], value)
        activation = hypothesis_activation_report(model)
        if activation["operator_modified"]:
            family = activation["family"]
            coupling = next(item for item in registry["hypothesis_couplings"] if item["family"] == family)
            i, j = index_of[coupling["source"]], index_of[coupling["target"]]
            coefficient = coupling.get("coefficient_parameter")
            if coefficient:
                add_linear_dashpot(expected_c, i, j,
                                   model.coupling_scale * model.parameters[coefficient])
            elif coupling.get("spring_parameter"):
                add_linear_spring(expected_k, i, j,
                                  model.coupling_scale * model.parameters[coupling["spring_parameter"]])
    # Diagonals also carry grounding stiffness / proportional damping, so the
    # registry element pattern is verified on the OFF-DIAGONALS only.
    reconstructed = all(abs(model.K[i][j] - expected_k[i][j]) <= NUMERIC_TOLERANCE * max(1.0, abs(expected_k[i][j]))
                        and abs(model.C[i][j] - expected_c[i][j]) <= NUMERIC_TOLERANCE * max(1.0, abs(expected_c[i][j]))
                        for i in range(size) for j in range(size) if i != j)
    return {
        "max_positive_stiffness_off_diagonal_N_per_m": positive_k,
        "max_positive_damping_off_diagonal_N_s_per_m": positive_c,
        "spring_sign_convention_valid": positive_k <= NUMERIC_TOLERANCE,
        "dashpot_sign_convention_valid": positive_c <= NUMERIC_TOLERANCE,
        "grounded_spring_diagonal_dominance": diagonally_dominant,
        "operators_match_registry_two_node_elements": reconstructed,
        "contact_sign_physics_valid": positive_k <= NUMERIC_TOLERANCE and positive_c <= NUMERIC_TOLERANCE
                                       and diagonally_dominant and reconstructed,
    }


def dimensional_checks(model: ReducedOrderModel) -> Dict[str, Any]:
    units = {record["name"]: record["unit"] for record in parameter_registry()["parameters"]}
    expected = {name: "kg" for name in (
        "khufu_mass_kg", "khafre_mass_kg", "menkaure_mass_kg", "queens_pyramids_mass_kg",
        "khafre_temple_causeway_mass_kg", "sphinx_parent_massif_mass_kg",
        "sphinx_temple_complex_mass_kg", "bedrock_fragment_mass_kg", "plateau_substrate_mass_kg")}
    expected.update({name: "N/m" for name in units
                     if name.endswith("_stiffness_N_per_m") or
                     (name.startswith("contact_") and name.endswith("_N_per_m"))})
    expected.update({name: "N*s/m" for name in units if name.startswith("dashpot_")})
    expected.update({
        "damping_ratio_zeta": "dimensionless", "driver_force_amplitude_N": "N",
        "radiation_aperture_area_m2": "m^2", "radiation_medium_density_kg_per_m3": "kg/m^3",
        "radiation_medium_wave_speed_m_per_s": "m/s", "radiation_ka_validity_max": "dimensionless",
        "natural_background_power_W_synthetic": "W", "homogenized_density_kg_per_m3": "kg/m^3",
        "elastic_wave_speed_m_per_s": "m/s",
    })
    mismatches = {name: (units.get(name), unit) for name, unit in expected.items()
                  if units.get(name) != unit}
    k_over_m = tuple(UNIT_EXPONENTS["N/m"][i] - UNIT_EXPONENTS["kg"][i] for i in range(3))
    omega_exp = tuple(value / 2.0 for value in k_over_m)
    damping_used = [name for name in MATRIX_PARAMETER_NAMES
                    if name.startswith("dashpot_")] + ["damping_ratio_zeta"]
    damping_units_ok = all(units.get(name) in ("N*s/m", "dimensionless") for name in damping_used)
    no_force_per_metre_in_damping = all(units.get(name) != "N/m" for name in damping_used)
    radiation_unit = tuple(UNIT_EXPONENTS["kg/m^3"][i] + UNIT_EXPONENTS["m/s"][i] +
                           UNIT_EXPONENTS["m^2"][i] for i in range(3))
    return {
        "unit_mismatches": mismatches,
        "units_consistent": not mismatches,
        "k_over_m_exponents_kg_m_s": k_over_m,
        "frequency_exponents_kg_m_s": omega_exp,
        "radiation_resistance_exponents_kg_m_s": radiation_unit,
        "radiation_resistance_is_N_s_per_m": radiation_unit == UNIT_EXPONENTS["N*s/m"],
        "damping_parameters_use_N_s_per_m": damping_units_ok,
        "no_N_per_m_injected_into_damping": no_force_per_metre_in_damping,
        "matrix_shapes": {"M": [len(model.M), len(model.M[0])], "C": [len(model.C), len(model.C[0])],
                          "K": [len(model.K), len(model.K[0])], "B": [len(model.B), len(model.B[0])],
                          "Cr": [len(model.Cr), len(model.Cr[0])]},
        "positive_masses": all(model.M[i][i] > 0.0 for i in range(model.size)),
        "nonnegative_diagonal_damping": all(model.C[i][i] >= 0.0 for i in range(model.size)),
    }


# ---------------------------------------------------------------------------
# PRIME envelope, sensitivity and scenario comparison
# ---------------------------------------------------------------------------

def _objective_record(model: ReducedOrderModel, frequency: float) -> Dict[str, Any]:
    magnitudes, phases = [], []
    receiver = FUNCTIONAL_OBJECT_IDS.index("bedrock")
    for name in ("khufu", "khafre", "menkaure"):
        candidate = ReducedOrderModel(
            model.scenario, model.node_names, model.M, model.C, model.K,
            matrix_zeros(model.size, 1), matrix_zeros(1, model.size),
            model.parameters, model.coupling_scale, model.radiation_port,
            model.radiation_parameters)
        index = FUNCTIONAL_OBJECT_IDS.index(name)
        candidate.B[index][0] = 1.0
        candidate.Cr[0][receiver] = 1.0
        response = frequency_response(candidate, [frequency])[0]
        magnitudes.append(response["magnitude_m_per_N"])
        phases.append(response["phase_rad"])
    budget = energy_budget(model, frequency)
    input_power = budget["input_power_W"]
    force = model.parameters["driver_force_amplitude_N"]
    return {
        "frequency_hz": frequency,
        "min_triad_transfer_m_per_N": min(magnitudes),
        "triad_phase_coherence": abs(sum(cmath.exp(1j * phase) for phase in phases)) / 3.0,
        "export_efficiency": budget["export_efficiency"] if budget["export_efficiency"] is not None else 0.0,
        "material_loss_per_force2_W_per_N2": budget["material_dissipation_W"] / (force * force),
    }


def prime_objectives(model: ReducedOrderModel, frequencies: Sequence[float]) -> List[Dict[str, Any]]:
    """Multi-objective envelope. No target frequency is hardcoded."""
    return [_objective_record(model, frequency) for frequency in frequencies]


PARETO_KEYS: Tuple[str, ...] = (
    "min_triad_transfer_m_per_N", "triad_phase_coherence",
    "export_efficiency", "material_loss_per_force2_W_per_N2",
)


def pareto_frontier(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = [[float(record[key]) if record[key] is not None else 0.0 for key in PARETO_KEYS]
                  for record in records]
    if not normalized:
        return []
    ranges = [max(row[axis] for row in normalized) - min(row[axis] for row in normalized)
              for axis in range(len(PARETO_KEYS))]
    scores = [[(row[axis] - min(r[axis] for r in normalized)) / ranges[axis]
               if ranges[axis] > 0 else 0.0 for axis in range(len(PARETO_KEYS))] for row in normalized]
    scores = [[s[0], s[1], s[2], 1.0 - s[3]] for s in scores]
    frontier = []
    for index, candidate in enumerate(scores):
        dominated = any(all(other[axis] >= candidate[axis] for axis in range(4)) and
                        any(other[axis] > candidate[axis] for axis in range(4)) for other in scores)
        if not dominated:
            frontier.append(dict(records[index]))
    return frontier


def _scalar_objective(record: Dict[str, Any], ranges: Sequence[float],
                      lows: Sequence[float]) -> float:
    values = [float(record[key]) for key in PARETO_KEYS]
    scores = [(values[i] - lows[i]) / ranges[i] if ranges[i] > 0 else 0.0 for i in range(4)]
    return scores[0] + scores[1] + scores[2] + (1.0 - scores[3])


def refine_pareto_candidates(model: ReducedOrderModel,
                             frontier: Sequence[Dict[str, Any]],
                             grid: Sequence[float],
                             objectives: Sequence[Dict[str, Any]],
                             iterations: int = REFINEMENT_ITERATIONS) -> List[Dict[str, Any]]:
    """Local golden-section refinement of coarse Pareto frequencies.

    This is a declared continuous refinement of a synthetic scalarization. It is NOT
    a proof of a global or physical optimum.
    """
    if not frontier or not objectives:
        return []
    lows = [min(float(record[key]) for record in objectives) for key in PARETO_KEYS]
    highs = [max(float(record[key]) for record in objectives) for key in PARETO_KEYS]
    ranges = [high - low for low, high in zip(lows, highs)]
    golden = (math.sqrt(5.0) - 1.0) / 2.0
    refined = []
    for point in frontier:
        frequency = point["frequency_hz"]
        nearest = min(range(len(grid)), key=lambda k: abs(grid[k] - frequency))
        left = grid[max(0, nearest - 1)]
        right = grid[min(len(grid) - 1, nearest + 1)]
        if right <= left:
            continue
        a = right - golden * (right - left)
        b = left + golden * (right - left)
        fa = _scalar_objective(_objective_record(model, a), ranges, lows)
        fb = _scalar_objective(_objective_record(model, b), ranges, lows)
        for _ in range(iterations):
            if fa > fb:
                right, b, fb = b, a, fa
                a = right - golden * (right - left)
                fa = _scalar_objective(_objective_record(model, a), ranges, lows)
            else:
                left, a, fa = a, b, fb
                b = left + golden * (right - left)
                fb = _scalar_objective(_objective_record(model, b), ranges, lows)
        best_frequency = (a + b) / 2.0
        record = _objective_record(model, best_frequency)
        record["coarse_frequency_hz"] = frequency
        record["refinement_bracket_hz"] = [grid[max(0, nearest - 1)], grid[min(len(grid) - 1, nearest + 1)]]
        refined.append(record)
    refined.sort(key=lambda item: item["frequency_hz"])
    return refined


def prime_envelope(model: ReducedOrderModel, points: int = 81) -> Dict[str, Any]:
    frequencies = synthetic_frequency_grid(model, points=points)
    objectives = prime_objectives(model, frequencies)
    frontier = pareto_frontier(objectives)
    refined = refine_pareto_candidates(model, frontier, frequencies, objectives)
    efficiencies = [record["export_efficiency"] for record in objectives]
    return {
        "objective_definitions": {
            "min_triad_transfer_m_per_N": "min over Khufu/Khafre/Menkaure of |H_pyramid->bedrock|; maximize",
            "triad_phase_coherence": "|sum(exp(i phase_k))|/3; maximize",
            "export_efficiency": "P_radiated/P_in from the radiation-impedance port; maximize",
            "material_loss_per_force2_W_per_N2": "P_material/F0^2; minimize",
        },
        "computed_candidate_frequencies_hz": sorted({round(item["frequency_hz"], 12) for item in frontier}),
        "locally_refined_candidate_frequencies_hz": [round(item["frequency_hz"], 12) for item in refined],
        "locally_refined_candidates": refined,
        "pareto_frontier": frontier,
        "hardcoded_prime_frequency_hz": None,
        "robust_joint_optimum_identifiable": False,
        "continuous_global_optimality_claim": False,
        "finite_synthetic_discretization": True,
        "refinement_iterations_per_candidate": REFINEMENT_ITERATIONS,
        "export_efficiency_range": [min(efficiencies), max(efficiencies)],
        "export_efficiency_frequency_dependent": (max(efficiencies) - min(efficiencies)) > 1.0e-9,
        "reason": "All inputs are synthetic; the envelope is a discretized synthetic Pareto set with local refinement, not a global physical optimum.",
        "frequency_grid_hz": [frequencies[0], frequencies[-1]],
        "evaluated_points": len(frequencies),
    }


def parameter_sweep(model: ReducedOrderModel, parameter_name: str,
                    factors: Sequence[float] = (0.5, 0.75, 1.0, 1.25, 1.5),
                    frequencies: Optional[Sequence[float]] = None) -> Dict[str, Any]:
    grid = list(frequencies) if frequencies else synthetic_frequency_grid(model, points=81)
    baseline_value = model.parameters[parameter_name]
    records = []
    for factor in factors:
        candidate = assemble_model(model.scenario, {parameter_name: baseline_value * float(factor)})
        modes = natural_modes(candidate)
        responses = frequency_response(candidate, grid)
        peak = max(responses, key=lambda item: item["magnitude_m_per_N"])
        budget = energy_budget(candidate, peak["frequency_hz"])
        records.append({
            "factor": float(factor), "parameter_value": candidate.parameters[parameter_name],
            "first_mode_hz": modes[0]["frequency_hz"],
            "peak_response_hz": peak["frequency_hz"], "peak_response_m_per_N": peak["magnitude_m_per_N"],
            "radiated_power_W_at_peak": budget["exported_power_W"],
            "radiation_resistance_N_s_per_m_at_peak": budget["radiation_resistance_N_s_per_m"],
        })
    nominal = [row for row in records if abs(row["factor"] - 1.0) < 1e-12]
    nominal_row = nominal[0] if nominal else records[len(records) // 2]
    metric_ranges = {}
    for metric in ("first_mode_hz", "peak_response_m_per_N", "radiated_power_W_at_peak"):
        values = [row[metric] for row in records]
        reference = abs(nominal_row[metric])
        metric_ranges[metric] = (max(values) - min(values)) / reference if reference > 0 else 0.0
    return {
        "parameter_name": parameter_name,
        "parameter_unit": parameter_unit(parameter_name),
        "records": records, "normalized_output_ranges": metric_ranges,
        "sampling": "deterministic_one_at_a_time", "random_sampling_used": False,
    }


def sensitivity_report(model: ReducedOrderModel,
                       parameter_names_to_vary: Sequence[str] = (
                           "khufu_vertical_stiffness_N_per_m", "damping_ratio_zeta",
                           "sphinx_parent_massif_mass_kg", "contact_khufu_bedrock_N_per_m")) -> Dict[str, Any]:
    sweeps = {name: parameter_sweep(model, name) for name in parameter_names_to_vary}
    dominance = max(sweeps.items(), key=lambda item: item[1]["normalized_output_ranges"]["peak_response_m_per_N"])
    return {
        "sweeps": sweeps, "dominant_unknown": dominance[0],
        "dominant_unknown_normalized_peak_response_range": dominance[1]["normalized_output_ranges"]["peak_response_m_per_N"],
        "interpretation": "Dominance is with respect to this synthetic fixture only; it is not an archaeological result.",
    }


def scenario_comparison(models: Dict[str, ReducedOrderModel]) -> Dict[str, Any]:
    rows = []
    for scenario_id, model in sorted(models.items()):
        modes = natural_modes(model)
        frequencies = synthetic_frequency_grid(model, points=31)
        responses = frequency_response(model, frequencies)
        peak = max(responses, key=lambda item: item["magnitude_m_per_N"])
        budget = energy_budget(model, peak["frequency_hz"])
        rows.append({
            "scenario_id": scenario_id,
            "enabled_hypotheses": list(model.scenario["enabled_hypotheses"]),
            "coupling_scale": model.coupling_scale,
            "functional_object_count": model.size,
            "first_mode_hz": modes[0]["frequency_hz"],
            "peak_response_hz": peak["frequency_hz"], "peak_response_m_per_N": peak["magnitude_m_per_N"],
            "peak_phase_rad": peak["phase_rad"], "radiated_power_W_at_peak": budget["exported_power_W"],
            "hypothesis_activation": hypothesis_activation_report(model),
            "outbound_communication_claim": False,
        })
    return {"rows": rows, "null_scenario_id": "S3_PASSIVE_NULL"}


# ---------------------------------------------------------------------------
# Closed-form synthetic fixtures (software controls, not archaeological data)
# ---------------------------------------------------------------------------

def single_dof_fixture(mass_kg: float = 1.0e9,
                       stiffness_N_per_m: float = 1.0e9) -> ReducedOrderModel:
    scenario = make_scenario("S0_CURRENT_OBSERVED")
    return ReducedOrderModel(scenario, ("fixture",), [[mass_kg]], [[1.0]], [[stiffness_N_per_m]],
                             [[1.0]], [[1.0]], {"driver_force_amplitude_N": 1.0e6}, 0.0, None, {})


def two_dof_block_fixture(block_stiffness: float = 1.0e9,
                          coupling: float = 0.0) -> ReducedOrderModel:
    block_mass = 1.0e9
    damping = 2.0 * 0.02 * math.sqrt(block_stiffness * block_mass)
    return ReducedOrderModel(
        make_scenario("S3_PASSIVE_NULL"), ("block_A", "block_B"),
        [[block_mass, 0.0], [0.0, block_mass]],
        [[damping, 0.0], [0.0, damping]],
        [[block_stiffness, -coupling], [-coupling, block_stiffness]],
        [[1.0], [0.0]], [[1.0, 0.0]], {"driver_force_amplitude_N": 1.0e6},
        coupling, None, {})


# ---------------------------------------------------------------------------
# Deterministic export
# ---------------------------------------------------------------------------

def deterministic_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)


def build_deterministic_report(scenario_id: str = "S2_IDEALIZED_REFERENCE_COMPLEX") -> Dict[str, Any]:
    models = {key: assemble_model(scenario) for key, scenario in all_scenarios().items()}
    model = models[scenario_id]
    frequencies = synthetic_frequency_grid(model, points=41)
    modes = natural_modes(model)
    responses = frequency_response(model, frequencies)
    peak = max(responses, key=lambda item: item["magnitude_m_per_N"])
    peak_index = responses.index(peak)
    graph = system_graph_for_scenario(model.scenario)
    return {
        "schema_version": "1.0",
        "report_id": "GIZA_PRIME_DETERMINISTIC_EXAMPLE_REPORT",
        "scientific_status": "idealized_reference_model_not_historical_claim",
        "external_citations_attached": False,
        "source_id": "synthetic_reference_fixture",
        "scenario": model.scenario,
        "functional_object_registry": {
            "object_count": len(functional_object_registry()["objects"]),
            "object_ids": list(FUNCTIONAL_OBJECT_IDS),
            "symbolic_objects": list(SYMBOLIC_OBJECT_IDS),
        },
        "landscape_architecture": landscape.landscape_architecture_summary(),
        "graph_summary": {"node_count": len(graph.nodes), "edge_count": len(graph.edges)},
        "validation": {
            "scenario": validate_scenario(model.scenario),
            "source_register": validate_source_register(),
            "parameter_registry": validate_parameter_registry(),
            "bridge_catalog": validate_bridge_catalog(),
            "functional_object_registry": validate_functional_object_registry(),
            "real_source_ingestion_contract": validate_real_source_contract(),
            "functional_landscape_graph": landscape.validate_functional_landscape_graph(),
            "inventory_coverage_register": landscape.validate_inventory_coverage_register(),
        },
        "dimensional_checks": dimensional_checks(model),
        "physics_controls": {
            "contact_mechanics": contact_mechanics_check(model),
            "hypothesis_activation": hypothesis_activation_report(model),
            "revision": "physics_corrected_revision_2",
        },
        "computed": {
            "natural_modes": modes,
            "frequency_response_peak": {
                "frequency_hz": peak["frequency_hz"], "magnitude_m_per_N": peak["magnitude_m_per_N"],
                "phase_rad": peak["phase_rad"],
                "attenuation_db_re_1_m_per_N": peak["attenuation_db_re_1_m_per_N"],
                "group_delay_s": phase_group_delay(responses, peak_index),
            },
            "energy_budget_at_peak": energy_budget(model, peak["frequency_hz"]),
            "passivity": passivity_check(model, frequencies),
            "reciprocity": reciprocity_check(model, peak["frequency_hz"]),
            "zero_coupling": zero_coupling_check(assemble_model(make_scenario("S3_PASSIVE_NULL")),
                                                  frequencies=frequencies[::4]),
            "outbound_bound": outbound_energy_bound(model, peak["frequency_hz"]),
            "natural_background_comparator": natural_background_comparator(model, peak["frequency_hz"]),
            "prime_envelope": prime_envelope(model),
        },
        "represented_only_not_computed": {
            "acoustic_cavity_spectrum": "not_evaluable_missing_data no cavity geometry",
            "gas_thermal_draft": "not_evaluable_missing_data no temperature field",
            "hydrology": "not_evaluable_missing_data water table unresolved",
            "electromagnetic_radiation": "not_evaluable_missing_data no circuit or conductivity tensor",
            "earth_and_cosmic_outbound": "conservation_bounded_not_attributed / analogy_only / not_evaluable_missing_data; no direct bridge",
            "sphinx_original_form": "unknown no original geometry asserted",
        },
        "scenario_comparison": scenario_comparison(models),
        "sensitivity": sensitivity_report(model),
        "unresolved_parameters": [record["name"] for record in parameter_registry()["parameters"]
                                  if record["value"] is None],
        "no_hardcoded_prime_frequency": True,
    }


def write_deterministic_report(path: str,
                               scenario_id: str = "S2_IDEALIZED_REFERENCE_COMPLEX") -> str:
    payload = build_deterministic_report(scenario_id)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(deterministic_dumps(payload))
        handle.write("\n")
    return path


__all__ = [name for name in dir() if not name.startswith("_")]
