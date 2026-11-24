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

P0/P1 PROTOCOL
--------------
G_0 = natural parent geology is reconstructed first; G_1 = anthropogenic residual
is separated from it. The Sphinx is represented only as an uncertain *parent
massif* DOF; its present head/body profile is not assumed original. No cavity,
neck, chamber or missing component is invented. Bedrock is an active dynamic
medium (a generalized DOF), never a rigid platform.

GOVERNING EQUATIONS AND UNITS (reduced order, NOT full FEM)
-----------------------------------------------------------
    M u_dd + C u_d + K u = B s(t)
      M : kg            (symmetric positive definite)
      C : N s/m = kg/s  (symmetric positive semidefinite for passive systems)
      K : N/m  = kg/s^2 (symmetric positive definite for a stable passive model)
      B : dimensionless force distribution; F phasor = B * F0, F0 in N
      u : m ; omega : rad/s ; f = omega/(2*pi) in Hz

    Z(omega) = K - omega^2 M + i omega C                       [N/m]
    H(omega) = Cr^T Z(omega)^-1 B                              [m/N] (receptance)
    For a generalized eigenpair (lambda_k, phi_k) of
        S = M^(-1/2) K M^(-1/2),  M^(-1/2) = (M^(1/2))^(-1),
    we have K phi_k = lambda_k M phi_k, phi_k^T M phi_j = delta_kj,
        omega_k = sqrt(lambda_k) [rad/s],  f_k = omega_k/(2*pi) [Hz].
    Modal damping: zeta_k = phi_k^T C phi_k / (2 omega_k),
        Q_k = 1/(2 zeta_k) = omega_k / (phi_k^T C phi_k) when positive.

HARMONIC STEADY-STATE ENERGY BUDGET (phasor convention Re[. e^(i omega t)])
--------------------------------------------------------------------------
    u = Z^-1 F
    P_in       = 1/2 Re( F^* . (i omega u) )          [W]
    P_material = 1/2 omega^2 u^* C_material u        [W]
    P_export   = 1/2 omega^2 u^* C_export u          [W]
    P_stored   = 1/4 ( u^* K u + omega^2 u^* M u )   [W s = J, time average]
    P_in - P_material - P_export = 0  (passive system; dE/dt averages to zero)
    Internal interface transfer terms cancel in the complete system.
    P_export <= P_in, so any unmodelled outbound channel obeys
    P_channel <= P_export <= P_in <= P_source_assumed.

RECIPROCITY
-----------
H_ij = H_ji only when M, C, K are symmetric (and Z is therefore complex
symmetric) and output channels match input channels, i.e. Cr = B^T. It is not
assumed for dissipative/nonreciprocal/active extensions.

PRIME
-----
PRIME is computed as a Pareto envelope of objectives evaluated on the computed
spectrum. No favourite frequency is hardcoded anywhere in this module.

NUMERICAL METHOD
----------------
Real symmetric Jacobi eigendecomposition (cyclic rotations) for M, K and the
mass-weighted stiffness; complex Gaussian elimination with partial pivoting
for Z^-1. Floating point is used deliberately with documented tolerances;
this is not exact Q algebra. All algorithms are deterministic.
"""

from __future__ import annotations

import cmath
import copy
import json
import math
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))

EVIDENCE_CLASSES: Tuple[str, ...] = (
    "measured_current", "published_measurement", "historical_record",
    "geologically_inferred", "reconstructed_uncertain", "idealized_design",
    "assumption_for_sensitivity", "speculative_hypothesis", "unknown",
)
BRIDGE_STATUSES: Tuple[str, ...] = (
    "measured", "literature_supported", "model_supported", "bounded_negligible",
    "analogy_only", "hypothesis_unverified", "not_evaluable_missing_data",
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
CORE_NODES: Tuple[str, ...] = (
    "khufu", "khafre", "menkaure", "sphinx_parent_massif", "bedrock",
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
NUMERIC_TOLERANCE = 1.0e-9
ENERGY_RELATIVE_TOLERANCE = 1.0e-8
EIGEN_TOLERANCE = 1.0e-12
MAX_JACOBI_SWEEPS = 200


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


def validate_scenario(scenario: Dict[str, Any]) -> bool:
    """Validate a scenario against scenario_schema.json. Returns True or raises."""
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
    if scenario["driver_node"] not in CORE_NODES or scenario["receiver_node"] not in CORE_NODES:
        raise ValidationError("driver_node and receiver_node must be core nodes")
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
        if not record["unit"]:
            raise ValidationError("unit required for " + record["name"])
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
    if "bounded_negligible" not in statuses or "analogy_only" not in statuses:
        raise ValidationError("explicit bounded and analogy-only non-bridges are required")
    if "no_direct_cosmic_jump_rule" not in catalog:
        raise ValidationError("catalog must declare the no-direct-cosmic-jump rule")
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


def base_parameters() -> Dict[str, float]:
    """Numerically activated values only; unresolved (null) parameters are excluded."""
    result = {}
    for record in parameter_registry()["parameters"]:
        if record["activated"] and record["value"] is not None:
            result[record["name"]] = float(record["value"])
    return result


MATRIX_PARAMETER_NAMES: Tuple[str, ...] = (
    "khufu_mass_kg", "khafre_mass_kg", "menkaure_mass_kg",
    "sphinx_parent_mass_kg", "bedrock_fragment_mass_kg",
    "khufu_vertical_stiffness_N_per_m", "khafre_vertical_stiffness_N_per_m",
    "menkaure_vertical_stiffness_N_per_m", "sphinx_parent_vertical_stiffness_N_per_m",
    "bedrock_vertical_stiffness_N_per_m",
    "contact_khufu_khafre_N_per_m", "contact_khafre_menkaure_N_per_m",
    "contact_khufu_sphinx_N_per_m", "contact_sphinx_bedrock_N_per_m",
    "contact_khufu_bedrock_N_per_m", "contact_khafre_bedrock_N_per_m",
    "contact_menkaure_bedrock_N_per_m", "damping_ratio_zeta",
    "radiation_export_fraction", "driver_force_amplitude_N",
)


def make_scenario(scenario_id: str, **overrides: Any) -> Dict[str, Any]:
    """Build one synthetic scenario. Hypotheses are enabled one at a time."""
    if scenario_id not in scenario_family_ids():
        raise KeyError("unknown scenario family " + str(scenario_id))
    templates = _scenario_templates()
    scenario = copy.deepcopy(templates[scenario_id])
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
    common_falsifier = "Synthetic matrices fail a passivity, energy-balance or dimensional control."
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
        "S1_PARENT_GEOLOGY_RECONSTRUCTION", "P0/P1 parent-outcrop reconstruction placeholder",
        "Separates synthetic natural parent geometry G_0 from anthropogenic residual G_1; Sphinx original form is left unresolved.",
        "reconstructed", ["geologically_inferred", "reconstructed_uncertain", "unknown"],
        [1, 2, 3, 7], modules_core)
    templates["S1_PARENT_GEOLOGY_RECONSTRUCTION"]["notes"] += " Sphinx parent massif only; no invented cavity or original form."

    templates["S2_IDEALIZED_REFERENCE_COMPLEX"] = base(
        "S2_IDEALIZED_REFERENCE_COMPLEX", "Synthetic idealized reference complex",
        "Declared coherent layout exercising the equations; not a historical completion claim.",
        "idealized", ["idealized_design", "assumption_for_sensitivity", "unknown"],
        [1, 2, 3, 4, 7], modules_core + ["L4_IDEALIZED_ACOUSTIC_PLACEHOLDER"])
    templates["S2_IDEALIZED_REFERENCE_COMPLEX"]["notes"] += " Layer 4 is represented, not computed: no cavity volume is specified."

    templates["S3_PASSIVE_NULL"] = base(
        "S3_PASSIVE_NULL", "Passive-first null with zero engineered coupling",
        "All off-diagonal transfer terms are set to zero; the five DOFs reduce to independent subsystems.",
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
    """Typed graph for one scenario; hypotheses add exactly one labelled edge."""
    validate_scenario(scenario)
    graph = SystemGraph()
    role_set = ROLE_HYPOTHESES
    for name in CORE_NODES:
        layer = 7 if name == "bedrock" else 3
        graph.add_node(GraphNode(
            id=name, layer=layer, kind="core_mass" if name != "bedrock" else "active_medium",
            status="active" if name == "bedrock" else "synthetic_placeholder",
            evidence_class="idealized_design" if name != "sphinx_parent_massif" else "reconstructed_uncertain",
            description="Synthetic reduced-order DOF; G0/G1 separation is explicit."
                        if name == "sphinx_parent_massif" else "Synthetic reduced-order DOF.",
            role_candidates=role_set))
    graph.add_node(GraphNode("material_domain", 1, "material", "represented_not_computed",
                             "idealized_design", "Homogenized material placeholder; no tensor resolved.",
                             ("passive_boundary",)))
    graph.add_node(GraphNode("interfaces_domain", 2, "interfaces", "represented_not_computed",
                             "unknown", "Block/joint contacts; friction and cavities unresolved.",
                             ("filter",)))
    graph.add_node(GraphNode("acoustic_domain", 4, "field_domain", "represented_not_computed",
                             "unknown", "No cavity volume specified; acoustic spectrum not evaluable.",
                             ("resonator", "waveguide")))
    graph.add_node(GraphNode("hydrology_domain", 5, "field_domain", "represented_not_computed",
                             "unknown", "Water table and permeability unresolved.", ("filter",)))
    graph.add_node(GraphNode("em_domain", 6, "field_domain", "represented_not_computed",
                             "unknown", "Conductivity tensor and circuit unresolved.", ("transducer",)))
    graph.add_node(GraphNode("environment_domain", 7, "boundary_domain", "active",
                             "assumption_for_sensitivity", "Synthetic environmental boundary forcing.",
                             ("source",)))
    graph.add_node(GraphNode("earth_domain", 8, "boundary_domain", "context_only",
                             "unknown", "Earth-scale context; no established Giza causal bridge.",
                             ("receiver",)))
    graph.add_node(GraphNode("cosmic_domain", 9, "context_domain", "context_only",
                             "unknown", "External forcing context; no outbound communication claim.",
                             ("source", "indicator")))

    catalog = bridge_catalog()
    by_id = {record["bridge_id"]: record for record in catalog["bridges"]}
    if float(scenario["coupling_scale"]) > 0.0:
        for source, target, bridge_id in (
            ("khufu", "bedrock", "B_OUT_KHUFU_TO_BEDROCK_ELASTIC"),
            ("khafre", "bedrock", "B_OUT_KHUFU_TO_BEDROCK_ELASTIC"),
            ("menkaure", "bedrock", "B_OUT_KHUFU_TO_BEDROCK_ELASTIC"),
            ("sphinx_parent_massif", "bedrock", "B_OUT_SPHINX_PARENT_TO_BEDROCK_ELASTIC"),
            ("khufu", "khafre", "B_IN_SEISMIC_SUBSTRATE_TO_MONUMENTS"),
            ("khafre", "menkaure", "B_IN_SEISMIC_SUBSTRATE_TO_MONUMENTS"),
        ):
            record = by_id[bridge_id]
            graph.add_edge(GraphEdge(
                id="E_" + source.upper() + "_TO_" + target.upper(), source=source, target=target,
                carrier="elastic", direction="internal", transfer_model="linear_contact_spring",
                uncertainty=record["uncertainty"], status=record["status"],
                falsifier=record["falsifier"], evidence_class=record["evidence_class"],
                bridge_id=bridge_id))

    hypotheses = scenario["enabled_hypotheses"]
    if hypotheses:
        family = HYPOTHESIS_FAMILY[hypotheses[0]]
        bridging = {
            "elastic": ("khufu", "sphinx_parent_massif", "B_OUT_SPHINX_PARENT_TO_BEDROCK_ELASTIC"),
            "acoustic": ("khufu", "sphinx_parent_massif", "B_OUT_ACOUSTIC_CAVITY_HYPOTHESIS"),
            "gas_thermal": ("khafre", "sphinx_parent_massif", "B_OUT_GAS_THERMAL_HYPOTHESIS"),
            "hydrologic": ("menkaure", "bedrock", "B_OUT_HYDRAULIC_PATH_HYPOTHESIS"),
            "electromagnetic": ("khufu", "khafre", "B_OUT_EM_TRANSDUCER_HYPOTHESIS"),
            "mixed": ("khufu", "sphinx_parent_massif", "B_OUT_ACOUSTIC_CAVITY_HYPOTHESIS"),
        }[family]
        source, target, bridge_id = bridging
        record = by_id[bridge_id]
        graph.add_edge(GraphEdge(
            id="E_HYPOTHESIS_" + family.upper(), source=source, target=target,
            carrier=family if family != "mixed" else "mixed_idealized",
            direction="internal", transfer_model="symmetric_linear_hypothesis_coupling",
            uncertainty=record["uncertainty"], status=record["status"],
            falsifier=record["falsifier"], evidence_class=record["evidence_class"],
            bridge_id=bridge_id))

    if scenario["scenario_id"].startswith("S5"):
        graph.add_edge(GraphEdge(
            id="E_INBOUND_ENVIRONMENT", source="environment_domain", target="bedrock",
            carrier="elastic_environmental", direction="inbound",
            transfer_model="external_forcing_on_active_bedrock",
            uncertainty="synthetic comparator only", status="not_evaluable_missing_data",
            falsifier="Co-located calibrated background monitoring exceeding declared synthetic bound.",
            evidence_class="assumption_for_sensitivity",
            bridge_id="B_IN_SEISMIC_SUBSTRATE_TO_MONUMENTS"))
    # Deliberate non-edges: no core node is connected to earth/cosmic domains.
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
    """Cyclic Jacobi eigendecomposition of a real symmetric matrix.

    Returns (ascending eigenvalues, columns=corresponding eigenvectors).
    """
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
    scaled = [[sum(eigenvectors[i][q] * (1.0 / math.sqrt(eigenvalues[q])) * eigenvectors[j][q]
                   for q in range(size)) for j in range(size)] for i in range(size)]
    return scaled


def complex_solve(coefficients: Sequence[Sequence[complex]],
                  right_hand_side: Sequence[Sequence[complex]]) -> List[List[complex]]:
    """Gaussian elimination with partial pivoting for A X = B (complex)."""
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
# Reduced-order model assembly
# ---------------------------------------------------------------------------

@dataclass
class ReducedOrderModel:
    scenario: Dict[str, Any]
    node_names: Tuple[str, ...]
    M: List[List[float]]
    C: List[List[float]]
    C_material: List[List[float]]
    C_export: List[List[float]]
    K: List[List[float]]
    B: List[List[float]]
    Cr: List[List[float]]
    parameters: Dict[str, float]
    coupling_scale: float

    @property
    def size(self) -> int:
        return len(self.node_names)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario["scenario_id"],
            "node_names": list(self.node_names),
            "M": self.M, "C": self.C, "C_material": self.C_material,
            "C_export": self.C_export, "K": self.K, "B": self.B, "Cr": self.Cr,
            "coupling_scale": self.coupling_scale,
            "parameters": {key: self.parameters[key] for key in sorted(self.parameters)},
        }

    def dynamic_stiffness(self, omega: float) -> List[List[complex]]:
        size = self.size
        result = [[0j for _ in range(size)] for _ in range(size)]
        for i in range(size):
            for j in range(size):
                value = self.K[i][j] - omega * omega * self.M[i][j]
                value += 1j * omega * self.C[i][j]
                result[i][j] = complex(value)
        return result


def assemble_model(scenario: Optional[Dict[str, Any]] = None,
                   overrides: Optional[Dict[str, float]] = None) -> ReducedOrderModel:
    """Assemble M, C, K, B, Cr for the five-DOF synthetic ensemble.

    ``overrides`` changes one or more numeric registry values without changing
    the scenario, enabling deterministic one-at-a-time sensitivity studies.
    """
    if scenario is None:
        scenario = make_scenario("S0_CURRENT_OBSERVED")
    validate_scenario(scenario)
    registry_values = base_parameters()
    # Hypothesis-only values (activated=false in the registry) are copied into the
    # parameter dict for controlled sensitivity studies but are NOT added to the
    # operators unless the corresponding S4 hypothesis is explicitly enabled.
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
    mass_names = ("khufu_mass_kg", "khafre_mass_kg", "menkaure_mass_kg",
                  "sphinx_parent_mass_kg", "bedrock_fragment_mass_kg")
    stiffness_names = ("khufu_vertical_stiffness_N_per_m", "khafre_vertical_stiffness_N_per_m",
                       "menkaure_vertical_stiffness_N_per_m",
                       "sphinx_parent_vertical_stiffness_N_per_m", "bedrock_vertical_stiffness_N_per_m")
    masses = [parameters[name] for name in mass_names]
    stiffnesses = [parameters[name] for name in stiffness_names]
    if any(value <= 0.0 for value in masses + stiffnesses):
        raise ValidationError("mass and stiffness must be strictly positive")
    zeta = parameters["damping_ratio_zeta"]
    export_fraction = parameters["radiation_export_fraction"]
    if not 0.0 <= zeta < 1.0 or not 0.0 <= export_fraction < 1.0:
        raise ValidationError("damping ratio and export fraction must be in [0,1)")

    size = len(CORE_NODES)
    M = matrix_zeros(size)
    K = matrix_zeros(size)
    C = matrix_zeros(size)
    for index in range(size):
        M[index][index] = masses[index]
        K[index][index] = stiffnesses[index]
        diagonal_damping = 2.0 * zeta * math.sqrt(stiffnesses[index] * masses[index])
        C[index][index] = diagonal_damping

    index_of = {name: index for index, name in enumerate(CORE_NODES)}

    def add_stiffness(first: str, second: str, value_name: str, enabled: bool = True) -> None:
        if not enabled:
            return
        value = scale * parameters[value_name]
        i, j = index_of[first], index_of[second]
        K[i][j] += value
        K[j][i] += value

    add_stiffness("khufu", "khafre", "contact_khufu_khafre_N_per_m")
    add_stiffness("khafre", "menkaure", "contact_khafre_menkaure_N_per_m")
    add_stiffness("sphinx_parent_massif", "bedrock", "contact_sphinx_bedrock_N_per_m")
    add_stiffness("khufu", "bedrock", "contact_khufu_bedrock_N_per_m")
    add_stiffness("khafre", "bedrock", "contact_khafre_bedrock_N_per_m")
    add_stiffness("menkaure", "bedrock", "contact_menkaure_bedrock_N_per_m")

    hypotheses = scenario["enabled_hypotheses"]
    if hypotheses:
        family = HYPOTHESIS_FAMILY[hypotheses[0]]
        coupling_magnitude = scale * parameters["contact_khufu_sphinx_N_per_m"]
        # Hypothesis channels are deliberately small, symmetric and passive.
        if family == "elastic":
            add_stiffness("khufu", "sphinx_parent_massif", "contact_khufu_sphinx_N_per_m")
        elif family == "acoustic":
            value = 0.02 * coupling_magnitude * 0.1
            i, j = index_of["khufu"], index_of["sphinx_parent_massif"]
            C[i][j] += value
            C[j][i] += value
        elif family == "gas_thermal":
            value = 0.02 * coupling_magnitude * 0.1
            i, j = index_of["khafre"], index_of["sphinx_parent_massif"]
            C[i][j] += value
            C[j][i] += value
        elif family == "hydrologic":
            value = 0.25 * coupling_magnitude
            i, j = index_of["menkaure"], index_of["bedrock"]
            K[i][j] += value
            K[j][i] += value
        elif family == "electromagnetic":
            value = 0.02 * coupling_magnitude * 0.1
            i, j = index_of["khufu"], index_of["khafre"]
            C[i][j] += value
            C[j][i] += value
        elif family == "mixed":
            for first, second in (("khufu", "sphinx_parent_massif"), ("khafre", "bedrock")):
                value = 0.01 * coupling_magnitude * 0.1
                i, j = index_of[first], index_of[second]
                C[i][j] += value
                C[j][i] += value

    C_export = [[export_fraction * C[i][j] for j in range(size)] for i in range(size)]
    C_material = [[C[i][j] - C_export[i][j] for j in range(size)] for i in range(size)]

    driver = index_of[scenario["driver_node"]]
    receiver = index_of[scenario["receiver_node"]]
    B = matrix_zeros(size, 1)
    Cr = matrix_zeros(1, size)
    B[driver][0] = 1.0
    Cr[0][receiver] = 1.0
    return ReducedOrderModel(scenario, CORE_NODES, M, C, C_material, C_export, K, B, Cr,
                             parameters, scale)


def multiport_model(model: ReducedOrderModel) -> ReducedOrderModel:
    """Return a copy with B=I and Cr=I^T so reciprocity H_ij=H_ji can be tested."""
    size = model.size
    return ReducedOrderModel(
        model.scenario, model.node_names, model.M, model.C, model.C_material,
        model.C_export, model.K, identity_matrix(size), identity_matrix(size),
        dict(model.parameters), model.coupling_scale)


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
        quality = omega / modal_damping if modal_damping > 0.0 else None
        modes.append({
            "index": index,
            "eigenvalue_s_minus2": eigenvalue,
            "omega_rad_per_s": omega,
            "frequency_hz": omega / (2.0 * math.pi),
            "mode_vector_mass_normalized": column,
            "modal_damping_kg_per_s": modal_damping,
            "damping_ratio": modal_damping / (2.0 * omega) if omega > 0 else None,
            "quality_factor": quality,
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
    """H(omega) = Cr^T (K - omega^2 M + i omega C)^-1 B."""
    results = []
    for frequency in frequencies:
        omega = 2.0 * math.pi * frequency
        solution = complex_solve(model.dynamic_stiffness(omega), model.B)
        response = [[sum(model.Cr[out][i] * solution[i][port] for i in range(model.size))
                     for port in range(len(model.B[0]))]
                    for out in range(len(model.Cr))]
        magnitude = abs(response[0][0])
        phase = cmath.phase(response[0][0])
        attenuation_db = 20.0 * math.log10(magnitude) if magnitude > 0.0 else float("-inf")
        results.append({
            "frequency_hz": frequency, "omega_rad_per_s": omega,
            "H": response, "magnitude_m_per_N": magnitude,
            "phase_rad": phase, "attenuation_db_re_1_m_per_N": attenuation_db,
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
    force_amplitude = model.parameters["driver_force_amplitude_N"]
    force = [complex(force_amplitude * model.B[i][0]) for i in range(model.size)]
    displacement = harmonic_displacement(model, omega)
    velocity = [1j * omega * value for value in displacement]
    p_in = 0.5 * (sum(force[i].conjugate() * velocity[i] for i in range(model.size))).real
    p_material = 0.5 * omega * omega * quadratic_form(displacement, model.C_material).real
    p_export = 0.5 * omega * omega * quadratic_form(displacement, model.C_export).real
    p_stored = 0.25 * (quadratic_form(displacement, model.K).real +
                       omega * omega * quadratic_form(displacement, model.M).real)
    residual = p_in - p_material - p_export
    scale = max(abs(p_in), abs(p_material), abs(p_export), 1.0e-300)
    return {
        "frequency_hz": frequency,
        "input_power_W": p_in,
        "material_dissipation_W": p_material,
        "exported_power_W": p_export,
        "stored_energy_J": p_stored,
        "energy_residual_W": residual,
        "relative_residual": abs(residual) / scale,
        "conservation_closed": abs(residual) <= ENERGY_RELATIVE_TOLERANCE * scale,
        "units": {"power": "W", "stored_energy": "J"},
    }


def passivity_check(model: ReducedOrderModel, frequencies: Sequence[float]) -> Dict[str, Any]:
    damping_eigenvalues, _ = jacobi_eigen(model.C)
    min_power = float("inf")
    worst_residual = 0.0
    all_closed = True
    for frequency in frequencies:
        budget = energy_budget(model, frequency)
        min_power = min(min_power, budget["input_power_W"])
        worst_residual = max(worst_residual, abs(budget["energy_residual_W"]))
        all_closed = all_closed and budget["conservation_closed"]
    return {
        "min_damping_eigenvalue_kg_per_s": min(damping_eigenvalues),
        "damping_nonnegative": min(damping_eigenvalues) >= -NUMERIC_TOLERANCE,
        "min_input_power_W": min_power,
        "no_net_amplification": min_power >= -NUMERIC_TOLERANCE,
        "worst_absolute_residual_W": worst_residual,
        "all_energy_balances_closed": all_closed,
        "frequencies_evaluated": len(frequencies),
    }


def outbound_energy_bound(model: ReducedOrderModel, frequency: float) -> Dict[str, Any]:
    """Conservation-based upper bound for ANY outbound channel at one frequency."""
    budget = energy_budget(model, frequency)
    catalog = bridge_catalog()
    background = catalog["natural_background_comparator"]["power_W"]
    exported = max(0.0, budget["exported_power_W"])
    input_power = max(0.0, budget["input_power_W"])
    return {
        "frequency_hz": frequency,
        "modelled_export_upper_bound_W": exported,
        "total_input_upper_bound_W": input_power,
        "any_unmodelled_channel_bound_W": exported,
        "synthetic_natural_background_W": background,
        "ratio_to_synthetic_background": exported / background,
        "outbound_communication_claim": False,
        "status": "bounded_negligible",
        "note": "Bound only; unmodelled paths remain not_evaluable_missing_data without measured source power.",
    }


def natural_background_comparator(model: ReducedOrderModel, frequency: float) -> Dict[str, Any]:
    catalog = bridge_catalog()
    comparator = catalog["natural_background_comparator"]
    bound = outbound_energy_bound(model, frequency)
    return {
        "synthetic_background_power_W": comparator["power_W"],
        "modelled_export_power_W": bound["modelled_export_upper_bound_W"],
        "ratio": bound["ratio_to_synthetic_background"],
        "evidence_class": comparator["evidence_class"],
        "status": comparator["status"],
        "interpretation": "No inbound or outbound attribution is permitted until a measured co-located background exists.",
    }


# ---------------------------------------------------------------------------
# Reciprocity, zero-coupling and dimensional controls
# ---------------------------------------------------------------------------

def reciprocity_check(model: ReducedOrderModel, frequency: float,
                      broken: bool = False) -> Dict[str, Any]:
    multiport = multiport_model(model)
    if broken:
        # Deliberately nonreciprocal damping to demonstrate the condition.
        multiport.C = [list(row) for row in multiport.C]
        multiport.C[0][1] += 1.0e7
        multiport.C_material = [list(row) for row in multiport.C_material]
        multiport.C_material[0][1] += 1.0e7
    response = frequency_response(multiport, [frequency])[0]["H"]
    size = model.size
    max_asymmetry = max(abs(response[i][j] - response[j][i])
                        for i in range(size) for j in range(size))
    scale = max(abs(response[i][j]) for i in range(size) for j in range(size))
    symmetric = (is_symmetric(multiport.M) and is_symmetric(multiport.C)
                 and is_symmetric(multiport.K))
    holds = max_asymmetry <= (1.0e-9 * scale if scale > 0.0 else NUMERIC_TOLERANCE)
    return {
        "frequency_hz": frequency,
        "max_absolute_asymmetry_m_per_N": max_asymmetry,
        "relative_asymmetry": max_asymmetry / scale if scale > 0 else 0.0,
        "symmetric_operators": symmetric,
        "reciprocity_holds": holds,
        "broken_assumption": broken,
    }


def zero_coupling_check(model: ReducedOrderModel,
                        perturbed_index: int = 4,
                        stiffness_factor: float = 2.0,
                        frequencies: Optional[Sequence[float]] = None) -> Dict[str, Any]:
    """With zero off-diagonals, perturbing one subsystem cannot affect another."""
    grid = list(frequencies) if frequencies else synthetic_frequency_grid(model, points=11)
    base = [item["magnitude_m_per_N"] for item in frequency_response(model, grid)]
    perturbed = ReducedOrderModel(
        model.scenario, model.node_names,
        [list(row) for row in model.M], [list(row) for row in model.C],
        [list(row) for row in model.C_material], [list(row) for row in model.C_export],
        [list(row) for row in model.K], [list(row) for row in model.B],
        [list(row) for row in model.Cr], dict(model.parameters), model.coupling_scale)
    perturbed.K[perturbed_index][perturbed_index] *= stiffness_factor
    changed = [item["magnitude_m_per_N"] for item in frequency_response(perturbed, grid)]
    max_difference = max(abs(a - b) for a, b in zip(base, changed))
    off_diagonal_stiffness = max(abs(model.K[i][j])
                                 for i in range(model.size) for j in range(model.size) if i != j)
    off_diagonal_damping = max(abs(model.C[i][j])
                               for i in range(model.size) for j in range(model.size) if i != j)
    return {
        "max_response_change_m_per_N": max_difference,
        "max_off_diagonal_stiffness_N_per_m": off_diagonal_stiffness,
        "max_off_diagonal_damping_kg_per_s": off_diagonal_damping,
        "independent_subsystems_reproduced": max_difference <= NUMERIC_TOLERANCE * max(1.0, max(base)),
        "frequencies_evaluated": len(grid),
    }


UNIT_EXPONENTS: Dict[str, Tuple[int, int, int]] = {
    "kg": (1, 0, 0), "m": (0, 1, 0), "s": (0, 0, 1), "N": (1, 1, -2),
    "N/m": (1, 0, -2), "N*s/m": (1, 0, -1), "kg/s": (1, 0, -1),
    "m/s": (0, 1, -1), "m/N": (-1, 0, 2), "W": (1, 2, -3), "J": (1, 2, -2),
    "rad/s": (0, 0, -1), "Hz": (0, 0, -1), "dimensionless": (0, 0, 0),
    "kg/m^3": (-2, -3, 0),
}


def dimensional_checks(model: ReducedOrderModel) -> Dict[str, Any]:
    registry = parameter_registry()
    used_units = {}
    for record in registry["parameters"]:
        if record["value"] is not None:
            # Hypothesis-only values are included so their units are checked too.
            used_units[record["name"]] = record["unit"]
    expected = {
        "khufu_mass_kg": "kg", "khafre_mass_kg": "kg", "menkaure_mass_kg": "kg",
        "sphinx_parent_mass_kg": "kg", "bedrock_fragment_mass_kg": "kg",
        "khufu_vertical_stiffness_N_per_m": "N/m", "khafre_vertical_stiffness_N_per_m": "N/m",
        "menkaure_vertical_stiffness_N_per_m": "N/m",
        "sphinx_parent_vertical_stiffness_N_per_m": "N/m",
        "bedrock_vertical_stiffness_N_per_m": "N/m",
        "contact_khufu_khafre_N_per_m": "N/m", "contact_khafre_menkaure_N_per_m": "N/m",
        "contact_khufu_sphinx_N_per_m": "N/m", "contact_sphinx_bedrock_N_per_m": "N/m",
        "contact_khufu_bedrock_N_per_m": "N/m", "contact_khafre_bedrock_N_per_m": "N/m",
        "contact_menkaure_bedrock_N_per_m": "N/m", "damping_ratio_zeta": "dimensionless",
        "radiation_export_fraction": "dimensionless",
        "driver_force_amplitude_N": "N", "homogenized_density_kg_per_m3": "kg/m^3",
        "elastic_wave_speed_m_per_s": "m/s",
        "natural_background_power_W_synthetic": "W",
    }
    mismatches = {name: (used_units.get(name), unit) for name, unit in expected.items()
                  if used_units.get(name) != unit}
    k_over_m = UNIT_EXPONENTS["N/m"]
    mass = UNIT_EXPONENTS["kg"]
    omega_squared_exponent = tuple(k_over_m[i] - mass[i] for i in range(3))
    omega_exponent = tuple(value / 2.0 for value in omega_squared_exponent)
    # 2*pi is dimensionless, so f = omega/(2*pi) has the same exponents as omega.
    frequency_exponent = omega_exponent
    return {
        "unit_mismatches": mismatches,
        "units_consistent": not mismatches,
        "k_over_m_exponents_kg_m_s": omega_squared_exponent,
        "omega_exponents_kg_m_s": omega_exponent,
        "frequency_exponents_kg_m_s": frequency_exponent,
        "expected_frequency_exponents_kg_m_s": UNIT_EXPONENTS["Hz"],
        "k_over_m_has_inverse_time_squared": omega_squared_exponent == (0, 0, -2),
        "frequency_scaling_consistent": omega_exponent == (0, 0, -1) and frequency_exponent == (0, 0, -1),
        "matrix_shapes": {
            "M": [len(model.M), len(model.M[0])], "C": [len(model.C), len(model.C[0])],
            "K": [len(model.K), len(model.K[0])], "B": [len(model.B), len(model.B[0])],
            "Cr": [len(model.Cr), len(model.Cr[0])],
        },
        "positive_masses": all(model.M[i][i] > 0.0 for i in range(model.size)),
        "nonnegative_diagonal_damping": all(model.C[i][i] >= 0.0 for i in range(model.size)),
    }


# ---------------------------------------------------------------------------
# PRIME envelope, sensitivity and scenario comparison
# ---------------------------------------------------------------------------

def prime_objectives(model: ReducedOrderModel,
                     frequencies: Sequence[float]) -> List[Dict[str, Any]]:
    """Multi-objective response envelope. No target frequency is hardcoded.

    Objectives (units given explicitly):
      min_triad_transfer [m/N]       : weakest of Khufu/Khafre/Menkaure -> bedrock
      triad_phase_coherence [1]      : |sum exp(i phase)|/3 over the triad
      export_efficiency [1]          : P_export/P_in
      material_loss_per_force2 [W/N^2]: P_material/F0^2 (minimize)
    """
    columns = []
    for name in ("khufu", "khafre", "menkaure"):
        driver_scenario = copy.deepcopy(model.scenario)
        driver_scenario["driver_node"] = name
        driver_scenario["receiver_node"] = "bedrock"
        candidate = ReducedOrderModel(
            driver_scenario, model.node_names, model.M, model.C, model.C_material,
            model.C_export, model.K, model.B, model.Cr, model.parameters, model.coupling_scale)
        index = CORE_NODES.index(name)
        receiver = CORE_NODES.index("bedrock")
        candidate.B = matrix_zeros(model.size, 1)
        candidate.Cr = matrix_zeros(1, model.size)
        candidate.B[index][0] = 1.0
        candidate.Cr[0][receiver] = 1.0
        columns.append(frequency_response(candidate, frequencies))
    records = []
    for index, frequency in enumerate(frequencies):
        magnitudes = [columns[channel][index]["magnitude_m_per_N"] for channel in range(3)]
        phases = [columns[channel][index]["phase_rad"] for channel in range(3)]
        coherence = abs(sum(cmath.exp(1j * phase) for phase in phases)) / 3.0
        budget = energy_budget(model, frequency)
        input_power = budget["input_power_W"]
        efficiency = budget["exported_power_W"] / input_power if input_power > 0 else None
        force = model.parameters["driver_force_amplitude_N"]
        loss_per_force2 = budget["material_dissipation_W"] / (force * force)
        records.append({
            "frequency_hz": frequency,
            "min_triad_transfer_m_per_N": min(magnitudes),
            "triad_phase_coherence": coherence,
            "export_efficiency": efficiency,
            "material_loss_per_force2_W_per_N2": loss_per_force2,
        })
    return records


def pareto_frontier(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalized Pareto nondominated set; maximize first three, minimize last."""
    keys = ("min_triad_transfer_m_per_N", "triad_phase_coherence",
            "export_efficiency", "material_loss_per_force2_W_per_N2")
    normalized = []
    for record in records:
        normalized.append([float(record[key]) if record[key] is not None else 0.0 for key in keys])
    if not normalized:
        return []
    ranges = []
    for axis in range(len(keys)):
        values = [row[axis] for row in normalized]
        low, high = min(values), max(values)
        ranges.append(high - low)
    scores = []
    for row in normalized:
        scores.append([(row[axis] - min(r[axis] for r in normalized)) / ranges[axis]
                       if ranges[axis] > 0 else 0.0 for axis in range(len(keys))])
    scores = [[s[0], s[1], s[2], 1.0 - s[3]] for s in scores]
    frontier = []
    for index, candidate in enumerate(scores):
        dominated = any(all(other[axis] >= candidate[axis] for axis in range(len(candidate))) and
                        any(other[axis] > candidate[axis] for axis in range(len(candidate)))
                        for other in scores)
        if not dominated:
            frontier.append(dict(records[index]))
    return frontier


def prime_envelope(model: ReducedOrderModel, points: int = 81) -> Dict[str, Any]:
    frequencies = synthetic_frequency_grid(model, points=points)
    objectives = prime_objectives(model, frequencies)
    frontier = pareto_frontier(objectives)
    return {
        "objective_definitions": {
            "min_triad_transfer_m_per_N": "min over Khufu/Khafre/Menkaure of |H_pyramid->bedrock|; maximize",
            "triad_phase_coherence": "|sum(exp(i phase_k))|/3; maximize",
            "export_efficiency": "P_export/P_in; maximize",
            "material_loss_per_force2_W_per_N2": "P_material/F0^2; minimize",
        },
        "computed_candidate_frequencies_hz": sorted({round(item["frequency_hz"], 12) for item in frontier}),
        "pareto_frontier": frontier,
        "hardcoded_prime_frequency_hz": None,
        "robust_joint_optimum_identifiable": False,
        "reason": "All inputs are synthetic and unresolved parameters dominate; competing objectives do not collapse to a unique robust optimum.",
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
            "factor": float(factor),
            "parameter_value": candidate.parameters[parameter_name],
            "first_mode_hz": modes[0]["frequency_hz"],
            "peak_response_hz": peak["frequency_hz"],
            "peak_response_m_per_N": peak["magnitude_m_per_N"],
            "exported_power_W_at_peak": budget["exported_power_W"],
        })
    nominal = [row for row in records if abs(row["factor"] - 1.0) < 1e-12]
    nominal_row = nominal[0] if nominal else records[len(records) // 2]
    metric_ranges = {}
    for metric in ("first_mode_hz", "peak_response_m_per_N", "exported_power_W_at_peak"):
        values = [row[metric] for row in records]
        reference = abs(nominal_row[metric])
        metric_ranges[metric] = (max(values) - min(values)) / reference if reference > 0 else 0.0
    return {
        "parameter_name": parameter_name,
        "parameter_unit": next(record["unit"] for record in parameter_registry()["parameters"]
                               if record["name"] == parameter_name),
        "records": records,
        "normalized_output_ranges": metric_ranges,
        "sampling": "deterministic_one_at_a_time",
        "random_sampling_used": False,
    }


def sensitivity_report(model: ReducedOrderModel,
                       parameter_names_to_vary: Sequence[str] = (
                           "khufu_vertical_stiffness_N_per_m", "damping_ratio_zeta",
                           "sphinx_parent_mass_kg", "contact_khufu_bedrock_N_per_m")) -> Dict[str, Any]:
    sweeps = {name: parameter_sweep(model, name) for name in parameter_names_to_vary}
    dominance = max(sweeps.items(), key=lambda item: item[1]["normalized_output_ranges"]["peak_response_m_per_N"])
    return {
        "sweeps": sweeps,
        "dominant_unknown": dominance[0],
        "dominant_unknown_normalized_peak_response_range": dominance[1]["normalized_output_ranges"]["peak_response_m_per_N"],
        "interpretation": "Dominance is with respect to this synthetic fixture only; it is not an archaeological result.",
    }


def scenario_comparison(models: Dict[str, ReducedOrderModel]) -> Dict[str, Any]:
    rows = []
    for scenario_id, model in sorted(models.items()):
        modes = natural_modes(model)
        frequencies = synthetic_frequency_grid(model, points=41)
        responses = frequency_response(model, frequencies)
        peak = max(responses, key=lambda item: item["magnitude_m_per_N"])
        budget = energy_budget(model, peak["frequency_hz"])
        rows.append({
            "scenario_id": scenario_id,
            "enabled_hypotheses": list(model.scenario["enabled_hypotheses"]),
            "coupling_scale": model.coupling_scale,
            "first_mode_hz": modes[0]["frequency_hz"],
            "peak_response_hz": peak["frequency_hz"],
            "peak_response_m_per_N": peak["magnitude_m_per_N"],
            "peak_phase_rad": peak["phase_rad"],
            "exported_power_W_at_peak": budget["exported_power_W"],
            "outbound_communication_claim": False,
        })
    return {"rows": rows, "null_scenario_id": "S3_PASSIVE_NULL"}


# ---------------------------------------------------------------------------
# Closed-form synthetic fixtures (software controls, not archaeological data)
# ---------------------------------------------------------------------------

def single_dof_fixture(mass_kg: float = 1.0e9,
                       stiffness_N_per_m: float = 1.0e9) -> ReducedOrderModel:
    scenario = make_scenario("S0_CURRENT_OBSERVED")
    return ReducedOrderModel(
        scenario, ("fixture",), [[mass_kg]], [[1.0]], [[0.5]], [[0.5]], [[stiffness_N_per_m]],
        [[1.0]], [[1.0]], {"driver_force_amplitude_N": 1.0e6}, 0.0)


def two_dof_block_fixture(block_stiffness: float = 1.0e9,
                          coupling: float = 0.0) -> ReducedOrderModel:
    """Two identical blocks; setting coupling=0 must reproduce independent blocks."""
    block_mass = 1.0e9
    damping = 2.0 * 0.02 * math.sqrt(block_stiffness * block_mass)
    return ReducedOrderModel(
        make_scenario("S3_PASSIVE_NULL"), ("block_A", "block_B"),
        [[block_mass, 0.0], [0.0, block_mass]],
        [[damping, 0.0], [0.0, damping]],
        [[0.5 * damping, 0.0], [0.0, 0.5 * damping]],
        [[0.5 * damping, 0.0], [0.0, 0.5 * damping]],
        [[block_stiffness, coupling], [coupling, block_stiffness]],
        [[1.0], [0.0]], [[1.0, 0.0]],
        {"driver_force_amplitude_N": 1.0e6}, coupling)


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
        "graph_summary": {"node_count": len(graph.nodes), "edge_count": len(graph.edges)},
        "validation": {
            "scenario": validate_scenario(model.scenario),
            "source_register": validate_source_register(),
            "parameter_registry": validate_parameter_registry(),
            "bridge_catalog": validate_bridge_catalog(),
        },
        "dimensional_checks": dimensional_checks(model),
        "computed": {
            "natural_modes": modes,
            "frequency_response_peak": {
                "frequency_hz": peak["frequency_hz"],
                "magnitude_m_per_N": peak["magnitude_m_per_N"],
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
            "earth_and_cosmic_outbound": "bounded_negligible / analogy_only / non-bridge",
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
