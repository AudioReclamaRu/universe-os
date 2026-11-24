# GIZA PRIME — Idealized Multiscale Digital Twin (Track B, Issue #6)

**Status:** corrected first software version (`physics_corrected_revision_2`) with an **open functional-landscape architecture** (`landscape_graph_revision_1`). It is an **idealized synthetic reference model**, not a historical reconstruction, not a 3D FEM/CFD solution, and not evidence that the Giza complex communicates with the Earth or the cosmos. The 9-DOF mechanics package is one synthetic projection of the open graph, never the whole Giza landscape or a privileged core.

**Worktree / branch:** `E:\GIZA_PRIME_LAB\universe-os-phase32`, `research/full-relational-math-reconstruction-001`. Accepted pre-correction delivery HEAD was `9fb207d5e7c407093aeef10582c48f6624a721ce`; the final corrected HEAD and push/CI URLs are recorded in the delivery audit.

**Evidence policy:** no external citation, survey value, coordinate, elevation, published measurement, URL or datum is attached. `synthetic_reference_fixture` is an internal placeholder, **not** a source. No source was fabricated. Activated numbers are `idealized_design`, `assumption_for_sensitivity` or declared synthetic controls; unresolved quantities are `unknown` and stored as `null`. `functional_objects.json` is an open registry of synthetic functional objects, not a claim about historical assigned functions.

**Verification (actual run):** `$env:OPENBLAS_NUM_THREADS='1'; C:\Python314\python.exe -m unittest discover -q -p "test_*.py"` from this directory → **Ran 159 tests … OK** (159 passes, 0 failures, 0 errors). Standard library only; no installs, no downloads, no network.

---

## 0. Package contents and reproduction

| File | Role |
|---|---|
| `giza_multiscale_model.py` | Standard-library reference model: validation, typed graph, Jacobi eigensolver, complex response solver, signed two-node springs/dashpots, radiation-impedance energy budget, PRIME envelope, sensitivity, deterministic export |
| `test_giza_multiscale_model.py` | 129 software/physics controls, including physical-meaning, dimensional and landscape-integration tests |
| `landscape_graph_engine.py` | Open graph engine for \\(\\mathcal G=(V,E,I,P,T,\\Theta)\\): validation, topology-only ensemble discovery, model projections and coverage gaps |
| `test_landscape_graph_engine.py` | 30 architecture controls for open-world semantics, interfaces, processes, temporal states, PRIME scope and inventory gaps |
| `functional_landscape_graph.json` | 10 object/interface classes, 9 synthetic seed instances, 22 relations, 6 interface classes, 8 process families, 9 temporal states, 7 model projections |
| `inventory_coverage_register.json` | Zero catalogued real objects; explicit `not_inventoried` status and known gap for every category |
| `scenario_schema.json` | Required scenario fields, evidence classes, bridge statuses, layer taxonomy and conditional rules |
| `example_scenario_synthetic.json` | One explicitly labelled synthetic scenario (`S2_IDEALIZED_REFERENCE_COMPLEX`) |
| `source_register.json` | Zero sources; `external_citations_attached: false` |
| `parameter_registry.json` | 48 records with unit, value/interval, evidence class, frame/datum/epoch, transformation, uncertainty, confidence, activation, limitations and discriminating measurement |
| `functional_objects.json` | 9 synthetic functional objects, 13 registry-driven contacts, 6 hypothesis couplings and 1 radiating port |
| `real_source_ingestion_contract.json` | Empty future source layer (`sources: []`, `awaiting_verified_sources`); prepared, not attached |
| `scale_bridge_catalog.json` | 19 structured inbound/outbound bridge and non-bridge records with B4 fields, conservation closure and explicit no-cosmic-jump rule |
| `deterministic_report_example.json` | Deterministic JSON export produced by `write_deterministic_report()` |

Reproduce the report and tests:

```powershell
Set-Location 'E:\GIZA_PRIME_LAB\universe-os-phase32\research\full-relational-math-reconstruction-001\giza-prime-multiscale'
$env:OPENBLAS_NUM_THREADS='1'
& C:\Python314\python.exe -m unittest discover -q -p "test_*.py"
& C:\Python314\python.exe -c "import giza_multiscale_model as g; g.write_deterministic_report('deterministic_report_example.json')"
```

Tolerances are floating-point controls, not exact Q algebra: eigen convergence `1e-12`, matrix symmetry `1e-9` relative, energy-balance relative residual `1e-8`, reciprocity relative `1e-9`.

---

## 0A. Open functional-landscape architecture

The target object is the whole accessible functional landscape, not a shortlist of prominent monuments. `landscape_graph_engine.py` stores and validates the formal object

```
G = (V, E, I, P, T, Theta)
```

with 10 first-class categories (`monumental`, `architectural`, `linear`, `subsurface`, `geological`, `hydrological`, `infrastructural`, `natural`, `nonobvious`, `interface`), E relations, I interfaces, P processes carrying energy/mass/momentum, T diachronous states, and Θ uncertainties and coverage limits. Interfaces are first-class: a structure–bedrock contact, water–channel boundary or airflow–cavity boundary may matter more than the adjacent object.

The architecture has no primordial core. The current nine synthetic objects are seed instances in an open registry, not an axiomatic set. `discover_candidate_ensembles()` derives topology-only candidate groups from declared relations; it permits multi-membership and overlapping ensembles, assigns no priority by size, fame, beauty or traditional classification, and makes no physical or historical claim. `model_projection_summary()` exposes mechanical, acoustic, hydraulic, thermal, gas-dynamic, electromagnetic and combined projections; only the synthetic mechanical projection is currently evaluable. `coverage_gap_report()` records that all ten categories remain `not_inventoried` with `catalogued_real_objects = 0`. Absence from a catalogue is never treated as absence from the ancient system.

PRIME is therefore defined as an emergent property of discovered interaction ensembles. The 9-DOF results in the next sections are a bounded synthetic projection that exercises the physical controls; they do not select the ensemble to which PRIME applies.

## 1. Scale map and functional-object ensemble

| Layer | Domain | Declared status | Numerics |
|---|---|---|---|
| 1 | Material / microscopic | homogenized continuum, no lattice resolution | density/wave speed in dimensional checks and bridge bounds only |
| 2 | Blocks, joints, interfaces | lumped contact points | 13 signed linear contact springs; friction, slip, gaps and cavities disabled |
| 3 | Monument & ensemble mechanics | 9 generalized vertical DOFs | computed modes and receptance from `M`, `C`, `K`, `B`, `Cr` |
| 4 | Acoustics / gas / thermal | placeholder only; no cavity volume or temperature field | not evaluable |
| 5 | Hydrology | no aquifer geometry or water table | symbolic only |
| 6 | EM / electrical | no conductivity tensor or circuit | symbolic only |
| 7 | Site environment / substrate | active bedrock and plateau-substrate DOFs plus radiation port | computed for the synthetic fixture; real impedance missing |
| 8 | Earth scale | not discretized | conservation-bounded context only |
| 9 | Planetary / solar / cosmic | not discretized | inbound context in S5; no outbound bridge |

The open synthetic core is: `khufu`, `khafre`, `menkaure`, `queens_pyramids`, `khafre_temple_causeway`, `sphinx_parent_massif`, `sphinx_temple_complex`, `bedrock`, `plateau_substrate`. Symbolic domains are represented, not computed: material, interfaces, acoustic, hydrology, EM, environment, Earth and cosmic contexts. The **mechanics projection graph** contains **17 nodes and 13 edges** for a coupled scenario; this is distinct from the open landscape graph signature (19 graph nodes: 10 classes + 9 synthetic seeds; 22 relations). No core object is connected directly to `earth_domain` or `cosmic_domain`.

Temporal ordering remains explicit: geology G0 → anthropogenic residual G1 → present damaged state S0 → idealized reference S2 → passive null S3 → one-hypothesis S4 families → environmental drivers S5. No historical completion state is implied. The Sphinx node is the *parent massif*; its present head/body profile is not assumed original, and `cavity_inventory` is `null` and explicitly empty.

## 2. Corrected physics contract

The revision-1 arbitrary fixed export split was removed. There is no `radiation_export_fraction`, no `C_export`, and no synthetic `1000 W` competitor used to declare negligibility.

Every two-node mechanical element uses the same physical sign pattern:

```
k[[1,-1],[-1,1]]   k in N/m, added to K
c[[1,-1],[-1,1]]   c in N s/m, added to C
```

Positive off-diagonal coupling terms are therefore rejected even if the matrix remains SPD. Registry validation rejects an N/m parameter used as a viscous dashpot coefficient. Incomputable hypothesis channels add **no operator term** and remain `not_evaluable_missing_data`; they are not silently given a fabricated coefficient.

The real radiative channel is a frequency-dependent low-`ka` resistance:

```
ka      = omega * sqrt(A/pi) / c_medium
R_rad   = 0.5 * rho * c_medium * A * ka^2              [N s/m]
C_dyn   = C + R_rad at the declared radiation port only   [N s/m]
Z(omega)= K - omega^2 M + i omega C_dyn                  [N/m]
H(omega)= Cr^T Z(omega)^-1 B                             [m/N]
```

If `ka` exceeds the declared validity bound, `R_rad` is `None`, the radiation port adds nothing, and the export channel is incomputable rather than approximated.

Harmonic energy separation:

```
P_in       = 1/2 Re( F^* . (i omega u) )
P_material = 1/2 omega^2 u^* C u
P_export   = 1/2 R_rad omega^2 |u_port|^2
P_stored   = 1/4 ( u^* K u + omega^2 u^* M u )
P_in - P_material - P_export = 0
```

`P_export` is computed from radiation impedance, not from an arbitrary fraction of `P_material`. The exported fraction varies with the computed response and frequency.

Controls added in revision 2 include exact two-node spring/dashpot sign patterns, zero row sums, rejection of N/m in `C`, off-diagonal sign checks after assembly, radiation-resistance dimensional exponent `(kg,m,s) = (1,0,-1)`, frequency-dependent export efficiency, conservation closure, bridge-status semantics, provenance restrictions, open-ensemble object checks, and the empty real-source ingestion contract.

## 3. Evidence and provenance

- `source_register.json`: `sources: []`, `external_citations_attached: false`. No reference is fabricated.
- `real_source_ingestion_contract.json`: `sources: []`, `ingestion_state: awaiting_verified_sources`. It defines required source fields and first-layer targets (geometry, geology, material properties) for a later verified ingestion pass. It is a contract only.
- Parameter classes requiring provenance are rejected unless sources exist. No record claims `measured_current`, `published_measurement`, `historical_record`, `reconstructed_uncertain` or `geologically_inferred`.
- Synthetic Sphinx and Sphinx-bedrock values are explicitly `idealized_design`, not reconstructions.
- Unresolved and inactive (`null`, `unknown`): `sphinx_original_parent_geometry`, `groundwater_table_depth_m`, `contact_friction_coefficient`, `cavity_inventory`.
- Layer 4, 5, 6, 8 and 9 quantities remain symbolic or `not_evaluable_missing_data`.

## 4. Computed results — synthetic fixture only

All numbers in this section are from `S2_IDEALIZED_REFERENCE_COMPLEX`, driver `khufu`, receiver `bedrock`, 9 DOF, declared synthetic parameters. They describe **this fixture only**.

### 4.1 Natural modes

| Mode | f (Hz) | omega (rad/s) | Q |
|---:|---:|---:|---:|
| 1 | 0.07968124 | 0.50065197 | 27.44 |
| 2 | 0.08114982 | 0.50987939 | 28.20 |
| 3 | 0.08708272 | 0.54715686 | 30.05 |
| 4 | 0.09252230 | 0.58133476 | 30.06 |
| 5 | 0.10402810 | 0.65362780 | 26.79 |
| 6 | 0.10995043 | 0.69083891 | 26.84 |
| 7 | 0.11850156 | 0.74456725 | 26.53 |
| 8 | 0.12086109 | 0.75939260 | 26.91 |
| 9 | 0.12644170 | 0.79445663 | 28.24 |

Matrix shapes are `M: [9,9]`, `C: [9,9]`, `K: [9,9]`, `B: [9,1]`, `Cr: [1,9]`. Dimensional checks report `units_consistent = true`, `no_N_per_m_injected_into_damping = true`, `radiation_resistance_is_N_s_per_m = true`, `k_over_m_exponents_kg_m_s = [0,0,-2]`, and `frequency_exponents_kg_m_s = [0,0,-1]`.

### 4.2 Frequency-response peak

`f = 0.0794338908 Hz`, `|H| = 1.12323169e-9 m/N`, phase `-1.26320752 rad`, attenuation `-178.9906 dB` relative to 1 m/N, group delay `40.7327 s`.

Closed-form controls recover `f = sqrt(k/m)/(2*pi)`, mass scaling `f ∝ m^-1/2`, stiffness scaling `f ∝ k^1/2`, and the declared beam-like `f ∝ L^-2` fixture. Reciprocity holds for symmetric operators with relative asymmetry `3.12e-16`; deliberately breaking symmetry fails the control.

### 4.3 Energy budget at the peak

| Quantity | Value | Unit |
|---|---:|---|
| Input power `P_in` | 1518.637047 | W |
| Material dissipation `P_material` | 1518.180198 | W |
| Radiated/exported power `P_export` | 0.456849 | W |
| Export efficiency `P_export/P_in` | 0.00030083 | 1 |
| Radiation resistance `R_rad` | 2.90732087e6 | N s/m |
| Time-averaged stored energy | 84587.472558 | J |
| Residual `P_in - P_material - P_export` | -3.52e-13 | W (relative 2.32e-16) |

Passivity over 41 frequencies: minimum damping eigenvalue `1.13137e7 kg/s`, minimum input power `0.21266 W`, all energy balances closed. Out-of-validity radiation states are tested separately and return `not_evaluable_missing_data` with no operator term.

### 4.4 PRIME envelope

`prime_envelope()` evaluates **81 synthetic grid points**, returns a **58-point discrete synthetic Pareto set** and **58 separately locally refined candidates**, with computed export-efficiency range `[2.3227313e-6, 0.01273449]`. Export efficiency is frequency-dependent (`true`). There is no hardcoded PRIME frequency (`hardcoded_prime_frequency_hz: null`), no continuous global physical optimum claim, and `robust_joint_optimum_identifiable = false`.

Objectives are computed from the operators: minimum triad transfer `[m/N]`, triad phase coherence `[1]`, export efficiency `[1]`, and material loss per force squared `[W/N^2]`. Local refinement is a separate numerical bracket around coarse Pareto candidates, not a new physical claim.

### 4.5 Scenario comparison

| Scenario | Hypothesis activation | First mode (Hz) | Peak |H| (m/N) | Radiated power at peak (W) |
|---|---|---:|---:|---:|
| S0_CURRENT_OBSERVED | none | 0.07968124 | 1.12323e-9 | 0.456849 |
| S1_PARENT_GEOLOGY_RECONSTRUCTION | none | 0.07968124 | 1.12323e-9 | 0.456849 |
| S2_IDEALIZED_REFERENCE_COMPLEX | none | 0.07968124 | 1.12323e-9 | 0.456849 |
| S3_PASSIVE_NULL | none, zero couplings | 0.07117625 | 0.0 | 0.0 |
| S4_ACOUSTIC | evaluable synthetic dashpot, unverified | 0.07968124 | 1.12890e-9 | 0.461470 |
| S4_ELASTIC | evaluable synthetic spring, unverified | 0.07984524 | 1.26528e-9 | 0.580393 |
| S4_ELECTROMAGNETIC | incomputable, no operator term | 0.07968124 | 1.12323e-9 | 0.456849 |
| S4_GAS_THERMAL | evaluable synthetic dashpot, unverified | 0.07968124 | 1.12576e-9 | 0.458906 |
| S4_HYDROLOGIC | incomputable, no operator term | 0.07968124 | 1.12323e-9 | 0.456849 |
| S4_MIXED | evaluable combined-control dashpot, unverified | 0.07968124 | 1.12664e-9 | 0.459628 |
| S5_ENVIRONMENTAL_DRIVERS | none, inbound context only | 0.07968124 | 1.12323e-9 | 0.456849 |

S0–S2 and S5 coincide numerically because the same declared fixture is used while their evidence meaning differs; this is intentional and highlights that no real data were inserted. S3's zero response is a passive-null control, **not** proof of absence in the real site.

### 4.6 Sensitivity

One-at-a-time deterministic sweeps use factors `0.5, 0.75, 1.0, 1.25, 1.5` with no random sampling. Dominant parameter for this fixture: `khufu_vertical_stiffness_N_per_m`, normalized peak-response range `1.40734`. Other normalized peak-response ranges: `damping_ratio_zeta` `0.99252`, `contact_khufu_bedrock_N_per_m` `0.20660`, `sphinx_parent_massif_mass_kg` `0.07021`. Dominance is synthetic-only and not archaeological.

## 5. Represented only, not computed

| Item | Status |
|---|---|
| Acoustic cavity spectrum | `not_evaluable_missing_data` — no cavity geometry |
| Gas/thermal draft | `not_evaluable_missing_data` — no temperature field |
| Hydrology | `not_evaluable_missing_data` — water table unresolved |
| Electromagnetic radiation | `not_evaluable_missing_data` — no circuit or conductivity tensor |
| Sphinx original form | `unknown` — no original geometry asserted |
| Earth and cosmic outbound | `conservation_bounded_not_attributed` / `analogy_only` / `not_evaluable_missing_data`; no direct bridge |

The synthetic `1000 W` natural-background comparator is an `assumption_for_sensitivity`. At the peak, modelled export is `0.456849 W`, ratio `4.56849e-4` to that synthetic comparator. `negligibility_claim_allowed = false`, `attribution_allowed = false`, and `outbound_communication_claim = false`. No negligibility, detection or attribution conclusion may be drawn from this comparator.

Bridge records separate inbound and outbound paths and include explicit non-bridges: shared bands are `analogy_only`; local-to-cosmic transfer is `conservation_bounded_not_attributed`; unmodelled channels remain `not_evaluable_missing_data`. There is no direct pyramid-local → Earth/cosmic bridge.

## 6. Alternatives, falsifiers and limits

Alternatives include ordinary ambient seismic/cultural noise, wind and thermal movement, local site response, unrelated shared frequency bands, selection bias, numerical coincidence, instrument artefacts, and failure to reject the passive null. A discriminating measurement requires datum-controlled geometry, sourced material properties, a demonstrable interface/path, measured forcing and receiver response, and a closed energy budget.

Not calculable: 3D geometry, cavities, anisotropy, roughness and damage; acoustic/gas/thermal spectra; hydrology; EM source/circuit/radiation; Earth and cosmic response; real natural background; historical function; historical PRIME target. Absence of evidence is not proof of absence, and lack of disproof is not proof of existence.

Revision-1 numbers (5-DOF modes near `0.067–0.114 Hz`, `339.91 W` exported, `24-point` Pareto set) are **superseded** and must not be reported as corrected results. All final numeric statements above come from the regenerated `deterministic_report_example.json` on the corrected core.

## Final limitations summary

No real citations, survey values, coordinates, external units, published measurements or dates were introduced. The evaluated mechanics model is a 9-DOF, linear, passive, deterministic synthetic projection; unresolved quantities stay symbolic. The open landscape graph has zero catalogued real objects, ten uncovered categories and no synchrony assumption. All 159 GIZA tests pass on the specified Python and OpenBLAS setting. The package adds files only under `research/full-relational-math-reconstruction-001/giza-prime-multiscale/` plus the shared README/CI integration; Phase 33 remains unchanged.
