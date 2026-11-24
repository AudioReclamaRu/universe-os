# UNIVERSE OS — Extended Section 18: Epistemic Core Specification

**Status:** finalized principle layer, framework only.
**Evidence state:** `not_evaluable` for every real cross-case (Richat / Giza / ASTRAEA). 0 verified sources, 0 real objects, 0 live adapters, 0 promotable claims.
**Scope discipline:** this delivery formalises **principles with machine-checkable consequences**. It deliberately does **not** add new panels and does **not** expand the class taxonomy beyond what cross-case tests have proven necessary.

> A green structural check is not physical confirmation. Every principle result carries `evidentiary_status = "not_evaluable"` until real primary sources are ingested.

---

## 1. Why this is not "six graphs"

The six-graph list dropped `Agency & Action`. The corrected meta-architecture is **seven representations of one typed core**, not seven databases:

| # | Representation | Scope |
| --- | --- | --- |
| R0 | ONTOLOGY & SEMANTIC GRAPH | types, definitions, relations, dimensions, logic, inference rules |
| R1 | REALITY GRAPH | physical objects, fields, processes, events, states, media, interactions |
| R2 | OBSERVATION & REPRESENTATION GRAPH | observations, instruments, data, images, maps, digital twins, artefacts |
| R3 | KNOWLEDGE & CLAIMS GRAPH | hypotheses, claims, arguments, evidence, conflicts, errors, assessments |
| R4 | CAUSAL & EXPERIMENT GRAPH | mechanisms, interventions, tests, predictions, simulations, replications |
| R5 | NORMATIVE & VALUE GRAPH | goals, values, priorities, risks, cost, legal limits, ethics, choice criteria |
| R6 | AGENCY & ACTION GRAPH | people, agents, institutions, authority, decisions, tasks, actions, accountability |

**META-REASONING & RESEARCH STRATEGY** is deliberately *not* an eighth world. It is a cross-cutting mechanism that analyses all seven, is itself modelled, verifiable and versioned (`must_be_versioned = True`, `is_eighth_world = False`).

All seven share one identifier space, one version chain and one provenance model (`shared_core_ids`, `shared_versions`, `shared_provenance` all `True`).

---

## 2. Observer Non-Privilege — a methodological commitment

Reality does not need an observer to exist. Knowledge of reality needs a channel of access — which need not be human, conscious, or even living (a physical trace, an instrument, an automatic algorithm, a comparison of processes).

| Sub-principle | Statement |
| --- | --- |
| ONP-1 Reality Independence | Existence and evolution do not depend on being observed. |
| ONP-2 Observer Non-Privilege | Human, instrument, algorithm and reference frame have no prior advantage. |
| ONP-3 Observation as Physical Relation | Observation is an interaction/trace with conditions and possible impact. |
| ONP-4 Representation Non-Identity | Map, model, image, measurement, twin are not the object. |
| ONP-5 Perspective Invariance | Check what is preserved or lawfully transformed across perspectives. |
| ONP-6 Epistemic Humility | Unknown stays unknown; absence of knowledge is not absence of phenomenon. |

**Reality Independence is NOT an empirical claim and not necessarily a formal axiom.** It is recorded as a `metaphysical_commitment` with a secondary `methodological_commitment`. No theorem about the Sphinx, Richat or Giza follows from it automatically: `model_to_world_bridge_required = True`, and the bridge itself is inspectable.

### Ten substitutions the system refuses

 discovering → existing · measured → intrinsic nature · seen now → always was · decomposed by us → nature is decomposed so · named system → nature has these boundaries · perceived noise → meaningless · temporal coincidence → causation · our mathematics → reality's structure · not detected → non-existent · important to us → objectively primary.

### Boundaries and primacy

Natural boundary (confirmed physical/material transition) and analytical boundary (chosen control volume) are distinct and may cross. Objects, processes, relations, fields, states and events are **equal representation types**; none is declared primitive. Observation is modelled as an information-access relation, not a mandatory human observer.

---

## 3. The 15 principles and their machine-checkable consequences

| ID | Principle | Machine-checkable consequence | Test |
| --- | --- | --- | --- |
| PR-01 | Reality Independence | Existence assertion must reference source-backed evidence; `grounding='graph_record'` rejected | negative + positive |
| PR-02 | Observer Non-Privilege | Perspective comparison needs ≥2 perspectives with conditions; no unearned preferred perspective | negative + positive |
| PR-03 | Observation as Physical Relation | Observation context records conditions; non-neutral impact requires before/during/after | recorder guard |
| PR-04 | Representation Non-Identity | A representation cannot be typed as the represented Entity/EntityState | negative + positive |
| PR-05 | Perspective Invariance | Transformation set frozen before test; one of three explicit outcomes | negative + positive |
| PR-06 | Epistemic Humility | Non-fact data modes never verified; absence-inference events rejected | negative |
| PR-07 | Self-Application | Model/Implementation/Execution/Capability/Limitation/Blind Spot distinct; green test ≠ physical confirmation | negative + positive |
| PR-08 | Trace Survival | Formation/preservation/detection/selection stages recorded; no-trace ≠ no-phenomenon | negative + positive |
| PR-09 | Classification Is a Claim | Classification change references a claim revision; physical entity_id unchanged | negative + positive |
| PR-10 | Ontology Evolution | Seven typed concept relations; reality_changed declared; no silent Entity mutation | recorder guard |
| PR-11 | Paraconsistent Isolation | Registered isolation events and propagation stay within disputed claims; direct contract violations and explicit explosion events are rejected | negative + positive (contract only) |
| PR-12 | Bitemporal Honesty | valid_time and transaction_time both present and declared distinct | negative + positive |
| PR-13 | Computational Reproducibility | code/env/deps/checksums/params/algorithm/solver/convergence/discretisation/outputs/replayable + distinction | recorder guard |
| PR-14 | Future Research Option Value | Option loss recorded structurally (lost methods, irreversibility, damage, limits), never one number | recorder guard |
| PR-15 | Ontology Insufficient | Declared reason, raw data preserved, no forced classification, extension not self-accepted | negative + positive |

`core.check_principles(graph)` returns all 15 results; `core.assert_principles(graph, require_evaluated=True)` refuses to accept unexercised/vacuous results as completion. Every result reports `evidentiary_status: "not_evaluable"`.

### PR-11 enforcement boundary — contract is implemented; inference engine is not

The machine-readable `principles_manifest()` explicitly reports `inference_engine_status = "not_implemented"` and lists the paraconsistent inference engine under `not_implemented`.

The current PR-11 validator checks the **registered isolation contract**:
- the event-contract registry validates `inference_isolation` records, including records inserted directly through the graph API;
- propagation outside the conflict's declared disputed-claim set is rejected;
- explicit conflict-explosion events are rejected.

This does **not** implement or verify the semantics of a paraconsistent inference engine. There is currently no inference engine whose derivation behavior can be tested. Therefore a passing PR-11 check establishes only that the registered contract and event records satisfy the declared structural constraints; it does not establish semantic non-explosion, proof-theoretic soundness or complete paraconsistent reasoning.

Future engine acceptance must test, at minimum: a consistent control case; a contradiction confined to a declared scope; proof that the contradiction does not entail arbitrary unrelated propositions; direct and transitive derivations; isolation of independent branches; and replayable derivation traces tied to a versioned rule set. Until that work exists, the status must remain `not_implemented`.

### Vocabulary details

- **Statement statuses** (do not conflate): `empirical_claim`, `mathematical_theorem`, `formal_axiom`, `methodological_commitment`, `metaphysical_commitment`, `definition`, `convention`, `prescription`.
- **Invariance types**: `invariant`, `covariant`, `equivariant`. **Outcomes**: `invariance_detected`, `invariance_not_detected_in_declared_class`, `check_not_performed_or_insufficient`. `not_found` is never encoded as `false`. Transformation sets are frozen before testing.
- **Concept evolution relations**: `refined_into`, `replaced_by`, `split_into`, `merged_into`, `partially_overlaps`, `rejected_as`, `reinterpreted_as`. Concept evolution is not reality evolution, and vice versa.
- **Trace stages**: `process_or_event → trace_formation → preservation_or_destruction → exposure_or_access → detection → selection_and_recording → publication_and_transfer → archive_survival`. The first four are mandatory in a trace record.
- **Self-application kinds**: `system_model`, `system_implementation`, `system_execution`, `system_capability`, `system_limitation`, `system_blind_spot`. Declared function ≠ working function; green test ≠ confirmed physical result.
- **`ONTOLOGY_INSUFFICIENT`** reasons: `new_phenomenon_outside_classes`, `definitions_conflict`, `relation_not_describable`, `missing_required_dimension`, `identity_not_establishable`, `inference_rules_ambiguous`. Raw data is preserved, classification is not forced, and a proposed extension stays `proposed` until a separate approval event exists. Extension checks: necessity, consistency, compatibility, backward impact.
- **Future Research Option Value** fields: `lost_future_methods`, `irreversibility`, `physical_damage`, `original_state_loss`, `legal_cultural_limits`. A preserved structure can be more valuable for future knowledge than today's destructive experiment.

---

## 4. Trace, self-application and reconstruction

The path from reality to evidence is not `reality → observation → data`. It is:

```
process → trace formation → preservation/destruction → exposure → detection
        → selection → publication → archive survival
```

Each stage can delete evidence. The accessible archaeological picture can be biased toward durable materials. We do **not** know how much vanished, so we do not invent a count.

Self-application separates what the system is *meant* to be, what is *implemented*, what actually *executed*, what it can *do*, what it *cannot* do and what it systematically *ignores*.

Reconstruction of a previous state is not physical restoration of it. `State Transition`, `Transformation History` and `Reconstruction Hypothesis` keep distinct statuses and uncertainties.

---

## 5. Reproducibility and irreversibility

A `Computational Experiment` must record code version, environment, dependencies, input checksums, parameters, boundary conditions, algorithm version, seed (if stochastic), solver settings, convergence, discretisation/rounding error, outputs and replayability. It must be distinguishable from a synthetic model and from a reconstruction of a real object. *(Specified here; not yet a first-class node type — see §7.)*

Irreversibility is graded: physically irreversible, practically irreversible, information loss, destruction of original structure, irreversible historical intervention, theoretically reversible but requiring unavailable resources. Intervention evaluation includes physical damage, loss of original state, loss of future methods, restoration cost and legal/heritage limits.

---

## 6. Acceptance scenarios

### Existing §18.12 scenarios (16, implemented and tested)

`shared_source_collapse` · `transitive_dependency` · `critical_node_removal` · `source_conflict` · `scoped_resolution` · `destroy_condition` · `no_post_hoc_rescue` · `ontology_typing` · `lazy_passport` · `shared_canonical_value` · `identity_temporal` · `independent_review` · `covariance_inheritance` · `cache_invalidation` · `approximation_disclosure` · `immutable_history`

### Principle consequences (15, implemented with negative controls)

`PR-01 … PR-15` in §3. `assert_principles(require_evaluated=True)` prevents a suite of vacuous checks from being reported as finished work.

### Three cross-cases — specified, NOT evaluated

| Case | Required path | Current state |
| --- | --- | --- |
| A — Richat | natural object → alternative origin hypotheses → geological epochs → geometric representations → sources → conflicts → next experiment | `not_evaluable_no_primary_sources` |
| B — Giza | artificial + natural structures → temporal states → identity → relations → physical mechanisms → measurement limits → competing reconstructions | `not_evaluable_no_verified_objects` |
| C — ASTRAEA | time series → correlations → null models → dependent sources → computational experiments → causality check → trading-limit constraints | `not_evaluable_no_adapter` |

Single check for all three: can we travel from raw observation to decision and back to inspectable grounds **without mixing physical facts, interpretations, computations, assumptions and actions**? With no primary sources available, the honest answer is that the traversal has not been performed. No image caption, search thumbnail or analogy is treated as a source.

---

## 7. Class expansion policy

The following are **specified but not implemented** because the cross-cases have not yet shown an existing representation to be insufficient:

- `Relation Instance` as a first-class entity (type, direction, mechanism, valid time, spatial scale, physical channel, conditions, sources, uncertainty, alternatives, refutation conditions); `N-ary Relation` / hyperedge for multi-participant relations. A geometric correspondence, a past interaction and a present absence are three distinct characteristics, not one `connected_to` edge.
- `Computational Experiment` as a first-class node type.
- `Irreversible Transformation`, `State Transition`, `Transformation History`, `Reconstruction Hypothesis` as first-class classes.
- `Institution`, `Research Community`, `Methodological Standard`, `Peer Review`, `Reviewer Assessment`, `Conflict of Interest`, `Publication Event`, `Citation Dependency`, `Knowledge Transfer`, `Reassessment`.
- `Methodological Standard` is institution/discipline/time dependent; ten publications from one primary measurement remain one basis.

New classes appear only after a cross-case reveals that the current model genuinely cannot describe an aspect of reality.

---

## 8. Two-time model

`Valid Time` = when a statement/event/state pertains to the real world. `Transaction Time` = when the information appeared or changed in the knowledge system. Example: geological event 100 Ma; measurement 2020; publication 2023; entry into UNIVERSE OS 2026; revision 2028. These are different axes; the knowledge date is never recorded as the event date.

---

## 9. Maturity criterion

> UNIVERSE OS must be able to detect not only errors in its claims, but errors in the ways it defines what counts as reality, observation, evidence, object and knowledge — and must retain the ability to say: "Our categories are insufficient. We do not yet know how to describe this correctly."

This is a methodological obligation, not a claim of achieved all-knowingness.

## 10. Commands

```powershell
$env:OPENBLAS_NUM_THREADS='1'
python -m unittest discover -v -p "test_*.py"     # 88 tests, OK
python -c "import epistemic_core as ec; ec.write_epistemic_manifest('epistemic_manifest.json')"
git diff --exit-code -- epistemic_manifest.json
```

No GUI, network, exchange connection or live ASTRAEA feed is used. All fixtures are synthetic and marked.
