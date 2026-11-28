# GIZA PRIME — Real Landscape Inventory and Relation Discovery

**Stage:** `REAL_LANDSCAPE_INVENTORY_AND_RELATION_DISCOVERY`
**Status:** ingestion framework, **zero verified objects** — not a reconstruction of Giza
**Architecture:** `real_landscape_inventory_revision_1`

## Principle

The study object remains the whole accessible functional landscape. No object is a
core by size, fame, beauty, historical significance or traditional classification.
A catalogue gap is never converted into a claim that something did not exist.

Because `inventory_source_contract.json` has `attached_sources: []`, the only
honest state of the real registers is empty. This package builds the instrument
for filling them; it does not fabricate a filled inventory.

## The five results

### 1. Object registry

`object_registry.json` declares 14 inventory slots and a per-record field
contract. Every real record must carry:

- unique `object_id`;
- `coordinates` and `coordinate_system` (datum and units declared);
- `geometry` and `elevations`;
- `material`, `preservation_state`, `temporal_intervals`;
- `source_ids` resolving to sources that passed the contract.

Slots cover large pyramid complexes **as ordinary records**, small/satellite/
unfinished pyramids, mastabas and necropolis fields, mortuary and valley temples,
platforms/enclosures/walls, the Sphinx complex **as ordinary records**, causeways,
roads, ramps, embankments and passages, boat pits/shafts/wells/chambers/galleries,
quarries/workshops/settlements/storage, ancient channels and hydrogeology,
bedrock massifs/fractures/faults, natural processes, destroyed/buried/ambiguous
objects, and interfaces/boundaries.

Current state: `objects: []`, `verified_source_count: 0`, all 14 slots
`not_inventoried`.

### 2. Natural-structure registry

`natural_structures` is a separate register. Bedrock massifs, escarpments,
fractures and faults, palaeo-channels, aquifers, filtration paths, relief, wind,
thermal gradients and interface boundaries are first-class slots, not background
context for monuments. Current state: empty, with four slots marked
`natural_structure: true`.

### 3. Relation graph

`relation_graph.json` separates nine typed relation families — `spatial`,
`geological`, `mechanical`, `acoustic`, `hydraulic`, `thermal`, `gas_dynamic`,
`electromagnetic`, `functional`. Each relation carries an epistemic status:
`established_documented`, `inferred_indirect` or `hypothesized_unverified`.
The separation rule forbids merging established relations with inferred or
hypothesized ones. A synthetic relation may never become `established`, an
inferred relation cannot be promoted without new evidence, and no direct
pyramid-local → planetary/cosmic bridge is permitted.

Current state: `relations: []`.

### 4. Automatic ensemble discovery

`inventory_engine.discover_ensembles()` derives connected components from
declared relations of one feature. It never seeds an object by prominence.
`discover_all_ensembles()` repeats this across every typed relation family and
reports objects belonging to more than one ensemble.

The capability demonstration in `SYNTHETIC_DEMONSTRATION` uses clearly synthetic
IDs and explicitly sets `physical_claim: false`. It shows a bedrock fracture
participating in hydraulic, geological and mechanical ensembles, while a large
pyramid and the Sphinx receive no starting privilege. It proves the mechanism;
it provides no Giza evidence. `discover_real_ensembles()` applied to the empty
verified registers correctly returns zero ensembles.

### 5. Incompleteness map

`incompleteness_map.json` records five states — `surveyed`, `source_known`,
`indirectly_detected`, `hidden_or_destroyed`, `unknown` — for every slot with a
named next survey step. All 14 slots are currently `unknown`. The map is a map
of what is missing, not a claim of absence.

## Adaptive modelling

| Tier | Condition | Permitted analysis |
|---|---|---|
| `numeric` | All required fields present from a verified source | Numerical calculation |
| `interval` | Explicit bounds from a verified source | Interval analysis |
| `symbolic` | No verified data, or partial unresolved data | Symbolic representation only |
| `rejected` | `source_ids` not in the verified set | No analysis |

A missing value is never replaced by a plausible number. With zero sources, all
14 slots are `symbolic`, `real_numeric_records = 0` and
`fabricated_parameters = 0`.

## Verification

`$env:OPENBLAS_NUM_THREADS='1'; C:\Python314\python.exe -m unittest discover -q -p "test_*.py"` in this directory → **Ran 47 tests … OK**.

The deterministic artifact `inventory_report_example.json` contains all five
results, adaptive-tier summary, capability demonstration, validation flags
(`no_fabricated_parameters: true`, `no_preselected_core: true`,
`giza_cosmos_claim: false`) and no callbacks to the synthetic mechanics fixture.

## What is needed next

Populate the registers. A verified source must supply datum, coordinate system,
geometry, elevations, material, preservation state, temporal interval and a
bibliographic reference. Until such sources pass the contract, this package will
continue to report an empty landscape with an explicit incompleteness map.
