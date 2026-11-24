# PHASE B — FINAL REPORT (A–K)

## A — Start-of-phase state
Branch `research/full-relational-math-reconstruction-001`, HEAD
`0df8458d34b817c70f553573ad1e153c63208083`, in sync with remote, working tree
clean at start. PR #4 `https://github.com/AudioReclamaRu/universe-os/pull/4`:
OPEN / Draft / unmerged / CLEAN. No merge, base change, second PR, force-push,
reset, cherry-pick or history rewrite was performed.

## B — Inventory and identification
Only the two owner-nominated directories were scanned. Raw: 15 files. Derived:
8 files. Expected total 12078, observed total 12078, delta 0. Raw-byte SHA-256, git
blob SHA-1 and canonical-JSON SHA-256 are kept separate and are not
interchangeable. All seven derived sets match their declared raw archives.

## C — Semantics
12078 observations were normalized through seven campaign-specific adapters.
The original record is preserved verbatim in every case. Semantic typing is
`SOURCE_STRUCTURE_ONLY` or `SOURCE_LABEL_ONLY`; no pyramid, sphinx or temple
class was assigned. Control points, survey stations, building corners and
feature samples remain distinct roles.

## D — Coordinate systems
5 systems registered. Datum, ellipsoid, projection, origin and orientation are
unverified. GPMP and ARCE Sphinx Grid are separate. No Helmert, similarity or
affine transform was fitted. 9315 swapped-label records and 68 elevation-absent
records are reported, not corrected. KML Z is never elevation.

## E — Deduplication and identity
345 entity candidates generated from name, coordinate and documented Feature ID
signals. 0 identities confirmed. 5 remeasurement candidates and 54 documented
reshoot notes preserved. No observation was removed or merged; all 12078 original
records survive.

## F — Geometry
All source geometry is `Point`. No LineString, Polygon or MultiGeometry exists,
so no measured contour or connecting line was invented. Campaign extents are
observation coverage, not monument boundaries.

## G — Idealization
24 idealized models with full contracts, four per eligible campaign. Petrie is
withheld as UNKNOWN because height is absent. Ellipsoid scale 2.0 is a declared
choice, not a fitted parameter. Terrain mesh and monument surface are `None`.

## H — Relations
154 relation candidates with formula, units, dimensions, inputs, residual,
sensitivity, alternatives, independent check and falsifier. Cross-campaign
Euclidean relations: 0. No acoustic, hydraulic, electromagnetic or frequency
claim is made.

## I — Reports and provenance
Machine-readable registries plus `PHASE_B_EVIDENCE_AUDIT.md`,
`PHASE_B_REFUTATION_LOG.md`, `PHASE_B_SOURCE_INVENTORY.md`,
`PHASE_B_COORDINATE_SYSTEMS.md`, `PHASE_B_GEOMETRY_RECONSTRUCTION.md`,
`PHASE_B_IDEALIZATION_REPORT.md` and `PHASE_B_ARCHITECTURE.md` were generated
from the artifacts, not hand-typed. Source provenance, coordinate system and
independent corroboration remain unverified.

## J — Validation
Full test matrix: 155 tests OK. Inlined exact-Euclidean spacing path was proven
byte-identical to the kernel on the GPMP control set. Full artifact rebuild is
byte-identical. Atlas inline JS passes `node --check` on all 3 blocks. Headless
Chromium: 0 console errors, 7 campaign rows, 14 relation slots unchanged.

## K — Commit-ready state, not committed
All Phase B files are local working-tree changes. Commit and push are WITHHELD
pending a separate owner GO for Phase B. PR #4 remains OPEN / Draft / unmerged.
No CI run is claimed for these uncommitted files; the only CI results cited are
the Phase A runs `45462282897` and `45462269241`, both completed / success on
HEAD `0df8458`.
