# PHASE B — ARCHITECTURE

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
