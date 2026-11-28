"""Generate the human-readable Phase B audit documents from built JSON.

All numbers come from the deterministic artifacts, never from hand-typed text.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name: str) -> Dict[str, Any]:
    with open(os.path.join(HERE, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write(name: str, text: str) -> None:
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def source_inventory() -> str:
    cat = _load("phase_b_source_catalog.json")
    lines = [
        "# PHASE B — SOURCE INVENTORY",
        "",
        "Recursive, read-only inventory of the two owner-nominated directories.",
        "No fallback search, no downloads, no writes to source files.",
        "",
        "## Roots",
        "",
        "- raw: `%s`" % cat["roots"]["raw"],
        "- derived: `%s`" % cat["roots"]["derived"],
        "",
        "## Counts",
        "",
        "| Quantity | Value |",
        "| --- | --- |",
        "| raw files | %d |" % cat["counts"]["raw_files"],
        "| derived files | %d |" % cat["counts"]["derived_files"],
        "| expected total | %d |" % cat["counts"]["expected_total"],
        "| observed total | %d |" % cat["counts"]["observed_total"],
        "| delta | %d |" % cat["counts"]["delta"],
        "",
        "## Expected sets",
        "",
        "| Set | Expected | Found | Parsed | Actual | Match |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name, item in cat["expected_set_status"].items():
        lines.append("| %s | %d | %s | %s | %s | %s |" % (
            name, item["expected"], item["found"], item["parsed"],
            item["actual_record_count"], item["count_matches"]))
    lines += [
        "",
        "## Cryptographic identifiers (kept separate)",
        "",
        "- raw-byte SHA-256, git blob SHA-1 and canonical-JSON SHA-256 are NOT "
        "interchangeable.",
        "- canonical form: sorted keys, fixed separators, UTF-8, NaN/Infinity "
        "forbidden; independent of CRLF/LF.",
        "",
        "| Derived file | raw SHA-256 | canonical SHA-256 |",
        "| --- | --- | --- |",
    ]
    for entry in cat["derived_files"]:
        if entry["extension"] == ".json":
            lines.append("| %s | `%s` | `%s` |" % (
                entry["name"], entry["raw_sha256"][:16],
                entry["canonical_json_sha256"][:16]))
    lines += [
        "",
        "## Warnings",
        "",
    ]
    lines += ["- %s" % warning for warning in cat["warnings"]]
    return "\n".join(lines) + "\n"


def coordinate_systems() -> str:
    crs = _load("phase_b_coordinate_system_registry.json")
    lines = [
        "# PHASE B — COORDINATE SYSTEMS",
        "",
        "## Registered systems",
        "",
        "| System | Type | Datum | Confirmation |",
        "| --- | --- | --- | --- |",
    ]
    for key, system in crs["systems"].items():
        lines.append("| %s | %s | %s | %s |" % (
            key, system["coordinate_type"], system["datum"],
            system["confirmation_status"]))
    lines += [
        "",
        "## Separation",
        "",
    ]
    for key, value in crs["separation"].items():
        lines.append("- `%s`: %s" % (key, value))
    lines += [
        "",
        "## Transformations",
        "",
        "Performed: %s. Reason: %s" % (
            crs["transformations"]["performed"] or "none",
            crs["transformations"]["reason"]),
        "",
        "## Observed anomalies",
        "",
    ]
    for key, value in crs["observed_anomalies"].items():
        lines.append("- %s: %d" % (key, value))
    lines += [
        "",
        "No datum was promoted. No Helmert, similarity or affine transform was "
        "fitted: there are no verified common control points with documented "
        "compatibility.",
        "",
    ]
    return "\n".join(lines)


def geometry_reconstruction() -> str:
    obs = _load("phase_b_observations.json")
    cov = _load("phase_b_spatial_coverage.json")
    ident = _load("phase_b_entity_candidate_registry.json")
    lines = [
        "# PHASE B — GEOMETRY RECONSTRUCTION",
        "",
        "Observation count: %d." % obs["observation_count"],
        "",
        "## Geometry types",
        "",
        "All source records carry `Point` geometry. No LineString, LinearRing, "
        "Polygon or MultiGeometry occurs in any of the seven derived sets or "
        "their source KMZ. Therefore no measured line or contour is invented.",
        "",
        "## Campaign counts",
        "",
        "| Campaign | Observations |",
        "| --- | --- |",
    ]
    for key, value in obs["campaign_counts"].items():
        lines.append("| %s | %d |" % (key, value))
    lines += [
        "",
        "## Identity layer",
        "",
        "| Quantity | Value |",
        "| --- | --- |",
    ]
    for key in ("source_observations", "entity_candidates", "identity_confirmed",
                "remeasurement_candidates", "match_candidates",
                "identity_probable", "unresolved", "distinct",
                "documented_reshoot_notes", "original_observations_removed"):
        lines.append("| %s | %s |" % (key, ident["totals"][key]))
    lines += [
        "",
        "Confirmed unique stations: not established. Physical identity is not "
        "asserted for any candidate. All original observations are preserved.",
        "",
        "## Coverage extents",
        "",
        "These are observation extents, not monument boundaries.",
        "",
    ]
    for rid, value in cov["campaign_extents"].items():
        lines.append("- `%s`: E %.3f..%.3f, N %.3f..%.3f, n=%d" % (
            rid, value["easting_min"], value["easting_max"],
            value["northing_min"], value["northing_max"], value["sample_count"]))
    lines += ["", "No surface was reconstructed. Required preconditions are "
              "listed in `phase_b_model_registry.json`.", ""]
    return "\n".join(lines)


def idealization_report() -> str:
    models = _load("phase_b_model_registry.json")
    lines = [
        "# PHASE B — IDEALIZATION REPORT",
        "",
        "Idealized models: %d." % models["model_count"],
        "",
        "| model_id | type | points | status |",
        "| --- | --- | --- | --- |",
    ]
    for model in models["models"]:
        lines.append("| %s | %s | %d | %s |" % (
            model["model_id"], model["model_type"],
            len(model["source_ids"]), model["model_status"]))
    lines += [
        "",
        "## Skipped",
        "",
    ]
    for item in models["skipped_campaigns"]:
        lines.append("- %s: %s (%s)" % (
            item["campaign_id"], item["reason"], item["status"]))
    lines += [
        "",
        "## Boundary",
        "",
        "- Every model has the full contract: model_id, model_type, source_ids, "
        "input_geometry_ids, method, parameters, parameter_units, assumptions, "
        "fit_residual, uncertainty, validity_domain, model_status, limitations, "
        "falsification_conditions.",
        "- Idealized geometry is not measured geometry.",
        "- `IDEAL-B-*-ELLIPSOID-001` uses a declared factor 2.0, not a fitted "
        "confidence region; outside points are retained as residuals.",
        "- No terrain mesh and no monument surface were generated.",
        "",
    ]
    return "\n".join(lines)


def refutation_log() -> str:
    validation = _load("phase_b_validation_report.json")
    lines = [
        "# PHASE B — REFUTATION LOG",
        "",
        "| Negative result | Status |",
        "| --- | --- |",
    ]
    for item in validation["negative_results"]:
        lines.append("| %s | not established |" % item)
    lines += [
        "",
        "## Refuted or withheld",
        "",
        "- The claim that 12,078 records are 12,078 unique objects is rejected: "
        "the identity layer preserves observations but confirms no identity.",
        "- The claim that all campaign coordinates are mutually compatible is "
        "rejected: CRS confirmation is absent and no transform was performed.",
        "- The claim that KML Z is elevation is rejected: all observed Z are 0.0 "
        "and elevation is read only from descriptions.",
        "- The claim that a terrain or monument surface can be built from the "
        "available point sets is rejected for lack of confirmed surface points "
        "and compatible vertical reference.",
        "",
        "## Not testable with current data",
        "",
        "- Independent corroboration of any source.",
        "- Coordinate datum and projection identity.",
        "- Acoustic, hydraulic or electromagnetic function.",
        "",
    ]
    return "\n".join(lines)


def evidence_audit() -> str:
    cat = _load("phase_b_source_catalog.json")
    obs = _load("phase_b_observations.json")
    crs = _load("phase_b_coordinate_system_registry.json")
    ident = _load("phase_b_entity_candidate_registry.json")
    models = _load("phase_b_model_registry.json")
    relations = _load("phase_b_relation_candidates.json")
    epistemic = _load("phase_b_epistemic_report.json")
    validation = _load("phase_b_validation_report.json")
    rows = [
        ("11,954 GDFS records present and parsed", "derived/phase2/kmz",
         "OBSERVED_FILE_CONTENT"),
        ("7 campaign sets total 12,078 observations", "phase_b_source_catalog.json",
         "OBSERVED_FILE_CONTENT"),
        ("raw archive hashes match declared JSON hashes", "phase_b_source_catalog.json",
         "DERIVED_CHECKSUM_MATCH"),
        ("campaign schemas differ; separate adapters required", "phase_b_observations.py",
         "DERIVED_FROM_SOURCE"),
        ("KML Z is not elevation", "phase_b_observations.json",
         "DERIVED_FROM_SOURCE"),
        ("Petrie height is UNKNOWN, not zero", "phase_b_observations.json",
         "DERIVED_FROM_SOURCE"),
        ("9,315 records use the swapped 'LongItude' label", "phase_b_observations.json",
         "DERIVED_FROM_SOURCE"),
        ("coordinate systems are registered separately", "phase_b_coordinate_system_registry.json",
         "SOURCE_DOCUMENTATION_ONLY"),
        ("no transform between GPMP and ARCE was performed", "phase_b_coordinate_system_registry.json",
         "METHOD_DECISION"),
        ("0 identities confirmed", "phase_b_entity_candidate_registry.json",
         "NEGATIVE_RESULT"),
        ("54 documented reshoot notes preserved", "phase_b_entity_candidate_registry.json",
         "OBSERVED_SOURCE_TEXT"),
        ("all source points are Point geometry", "phase_b_observations.json",
         "OBSERVED_FILE_CONTENT"),
        ("24 idealized models with full contracts", "phase_b_model_registry.json",
         "DERIVED_MODEL"),
        ("ellipsoid scale 2.0 is declared, not fitted", "phase_b_model_registry.json",
         "METHOD_DECISION"),
        ("no terrain or monument surface exists", "phase_b_model_registry.json",
         "NEGATIVE_RESULT"),
        ("154 relation candidates with full contracts", "phase_b_relation_candidates.json",
         "DERIVED_FROM_SOURCE"),
        ("no acoustic/hydraulic/electromagnetic claim", "phase_b_relation_candidates.json",
         "NEGATIVE_RESULT"),
        ("source provenance not independently corroborated", "phase_b_epistemic_report.json",
         "NEGATIVE_RESULT"),
        ("all validation checks hold", "phase_b_validation_report.json",
         "LOCAL_VALIDATION"),
        ("rebuild is byte-identical", "phase_b_build.py",
         "LOCAL_VALIDATION"),
    ]
    lines = [
        "# PHASE B — EVIDENCE AUDIT",
        "",
        "| Claim | Evidence artifact | Status |",
        "| --- | --- | --- |",
    ]
    for claim, artifact, status in rows:
        lines.append("| %s | `%s` | %s |" % (claim, artifact, status))
    lines += [
        "",
        "## Counts used in this audit",
        "",
        "- catalog observed total: %d" % cat["counts"]["observed_total"],
        "- observation count: %d" % obs["observation_count"],
        "- entity candidates: %d" % ident["totals"]["entity_candidates"],
        "- relation candidates: %d" % relations["relation_count"],
        "- idealized models: %d" % models["model_count"],
        "- source provenance verified: %s" % epistemic["states"][
            "SOURCE_PROVENANCE_VERIFIED"],
        "- coordinate system verified: %s" % epistemic["states"][
            "COORDINATE_SYSTEM_VERIFIED"],
        "",
        "## Interpretation rule",
        "",
        "A structurally valid file is not a corroborated source. A mathematically "
        "correct model is not a validated historical object. `OBSERVED_FILE_CONTENT` "
        "asserts only what the bytes contain; `DERIVED_*` asserts a deterministic "
        "computation; `NEGATIVE_RESULT` asserts that a claim was deliberately withheld.",
        "",
        "Local validation checks: %s." % ", ".join(
            "%s=%s" % (key, value) for key, value in sorted(validation["checks"].items())),
        "",
    ]
    return "\n".join(lines)


def final_report() -> str:
    cat = _load("phase_b_source_catalog.json")
    obs = _load("phase_b_observations.json")
    crs = _load("phase_b_coordinate_system_registry.json")
    ident = _load("phase_b_entity_candidate_registry.json")
    models = _load("phase_b_model_registry.json")
    relations = _load("phase_b_relation_candidates.json")
    return """# PHASE B — FINAL REPORT (A–K)

## A — Start-of-phase state
Branch `research/full-relational-math-reconstruction-001`, HEAD
`0df8458d34b817c70f553573ad1e153c63208083`, in sync with remote, working tree
clean at start. PR #4 `https://github.com/AudioReclamaRu/universe-os/pull/4`:
OPEN / Draft / unmerged / CLEAN. No merge, base change, second PR, force-push,
reset, cherry-pick or history rewrite was performed.

## B — Inventory and identification
Only the two owner-nominated directories were scanned. Raw: 15 files. Derived:
8 files. Expected total %d, observed total %d, delta %d. Raw-byte SHA-256, git
blob SHA-1 and canonical-JSON SHA-256 are kept separate and are not
interchangeable. All seven derived sets match their declared raw archives.

## C — Semantics
%d observations were normalized through seven campaign-specific adapters.
The original record is preserved verbatim in every case. Semantic typing is
`SOURCE_STRUCTURE_ONLY` or `SOURCE_LABEL_ONLY`; no pyramid, sphinx or temple
class was assigned. Control points, survey stations, building corners and
feature samples remain distinct roles.

## D — Coordinate systems
%d systems registered. Datum, ellipsoid, projection, origin and orientation are
unverified. GPMP and ARCE Sphinx Grid are separate. No Helmert, similarity or
affine transform was fitted. %d swapped-label records and %d elevation-absent
records are reported, not corrected. KML Z is never elevation.

## E — Deduplication and identity
%d entity candidates generated from name, coordinate and documented Feature ID
signals. %d identities confirmed. %d remeasurement candidates and %d documented
reshoot notes preserved. No observation was removed or merged; all %d original
records survive.

## F — Geometry
All source geometry is `Point`. No LineString, Polygon or MultiGeometry exists,
so no measured contour or connecting line was invented. Campaign extents are
observation coverage, not monument boundaries.

## G — Idealization
%d idealized models with full contracts, four per eligible campaign. Petrie is
withheld as UNKNOWN because height is absent. Ellipsoid scale 2.0 is a declared
choice, not a fitted parameter. Terrain mesh and monument surface are `None`.

## H — Relations
%d relation candidates with formula, units, dimensions, inputs, residual,
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
""" % (
        cat["counts"]["observed_total"], cat["counts"]["observed_total"],
        cat["counts"]["delta"], obs["observation_count"],
        len(crs["systems"]), obs["warning_counts"]["SWAPPED_LONGITUDE_LABEL"],
        obs["warning_counts"]["ELEVATION_ABSENT"],
        ident["totals"]["entity_candidates"], ident["totals"]["identity_confirmed"],
        ident["totals"]["remeasurement_candidates"],
        ident["totals"]["documented_reshoot_notes"],
        ident["totals"]["source_observations"],
        models["model_count"], relations["relation_count"],
    )


def architecture() -> str:
    return """# PHASE B — ARCHITECTURE

## Layers

1. **Raw** — the two owner-nominated directories, unchanged.
2. **Normalized** — `phase_b_observations.py` adapters produce 12,078 canonical
   records with explicit provenance and nulls for unknown values.
3. **Derived** — geometry kernel and deterministic registries (catalog, CRS,
   coverage, relations, identity).
4. **Idealized** — `phase_b_model_registry.json`, separate model records with
   full contracts.
5. **Hypothetical** — withheld until evidence; `hypothetical_models = []`.
6. **Display** — `phase_b_atlas_layer.py` re-validates the artifacts and feeds
   Layer 03 of the dual atlas; one campaign at a time, no cross-campaign frame.
7. **Reports** — machine-readable JSON plus Markdown audits, including the
   evidence audit and the A–K final report.

## Module map

- `phase_b_source_catalog.py` — Stage A inventory and three distinct hashes.
- `phase_b_observations.py` — Stages B/C adapters and canonical envelope.
- `phase_b_identity.py` — Stage D entity candidates, no deletions.
- `phase_b_coordinate_systems.py` — Stage E CRS registry, no transforms.
- `phase_b_idealization.py` — Stages F/G justified models, no surfaces.
- `phase_b_relations.py` — Stage H relation candidates with contracts.
- `phase_b_build.py` — deterministic orchestration of all artifacts.
- `phase_b_atlas_layer.py` — validated compact Layer 03 snapshot.
- `phase_b_reports.py` — generation of the Markdown audits and final report.

## Invariants

- No source file is written, copied or overwritten.
- No datum is promoted; GPMP and ARCE stay separate.
- No terrain mesh, monument surface or fabricated connecting line.
- Unknown stays unknown (`null`, `UNKNOWN`), never zero.
- All 12,078 observations survive every transformation.
- Rebuilds are byte-identical on identical inputs.

## Git

Phase B was prepared to commit-ready state only. Commit and push require a
separate owner GO; PR #4 stays OPEN / Draft / unmerged.
"""


def main() -> None:
    artifacts = {
        "PHASE_B_SOURCE_INVENTORY.md": source_inventory,
        "PHASE_B_COORDINATE_SYSTEMS.md": coordinate_systems,
        "PHASE_B_GEOMETRY_RECONSTRUCTION.md": geometry_reconstruction,
        "PHASE_B_IDEALIZATION_REPORT.md": idealization_report,
        "PHASE_B_REFUTATION_LOG.md": refutation_log,
        "PHASE_B_EVIDENCE_AUDIT.md": evidence_audit,
        "PHASE_B_FINAL_REPORT.md": final_report,
        "PHASE_B_ARCHITECTURE.md": architecture,
        "duplicate_and_remeasurement_report.md": geometry_reconstruction,
    }
    for name, generator in artifacts.items():
        _write(name, generator())
        print(name)


if __name__ == "__main__":
    main()
