# UNIVERSE 2.0 — FULL RELATIONAL MATHEMATICAL RECONSTRUCTION 001

**Status:** foundational research dossier  
**Branch:** research/full-relational-math-reconstruction-001  
**Pinned baseline commit:** 6506a838be83f7092cee5b4a487b37a9669dd7c9  
**Legacy v2 source:** preserved unchanged

## Purpose

This directory preserves the mathematics, exact derivations, source-code facts, exploratory correspondences, nonlinear equations, validation rules and open questions developed around UNIVERSE 2.0 and GIZA PRIME / RSE.

The central research object is the **network of relations**, not a collection of absolute numbers.

The strongest combinatorial result is:

\[
2^7=128,\qquad 3^7=2187.
\]

The 128 binary states are vertices of the seven-dimensional Boolean hypercube Q7. The 2187 ternary states can be identified exactly with all faces of Q7: at each of seven coordinates choose fixed-0, free, or fixed-1. The candidate comparator sends both signs to binary 1 and CENTER to binary 0; every binary mask with k ones has exactly 2^k ternary preimages.

This dossier also preserves the exact 42/85 arithmetic, antipodal gates, Hamming shells, H3 / SO(8) / golden-ratio / Mackay-shell correspondences, Pythagorean comma, legacy mass matrix, projector equations, nonlinear recurrence, implementation defects and cross-domain hypotheses.

## Index

1. Scope, source baseline and evidence policy — 00_SCOPE_AND_EVIDENCE.md
2. Q7, ternary states and complete face lattice — 01_Q7_BINARY_TERNARY_FACE_LATTICE.md
3. Gates 42/85, division by three and Hamming geometry — 02_GATES_42_85_AND_HAMMING_GEOMETRY.md
4. H3, SO(8), triality, phi and Mackay shells — 03_H3_SO8_PHI_MACKAY_KEYS.md
5. Legacy v2 equations, ratios and nonlinear dynamics — 04_LEGACY_V2_FORMULAS_AND_NONLINEAR_DYNAMICS.md
6. Giza, Rishat and open-scale relational hypotheses — 05_CROSS_DOMAIN_RELATION_REGISTER.md
7. Validation protocol and next research — 06_VALIDATION_AND_NEXT_RESEARCH.md
8. Machine-readable relation register — RELATION_REGISTER.csv
9. Reproducible standard-library checks — verify_relations.py

## Read this before interpreting any correspondence

- Arithmetic identities and graph-theoretic results are exact.
- Equations explicitly present in v2 are facts about the code.
- A numerical correspondence between independently defined structures is not proof of a common physical mechanism.
- Physical interpretation requires a dimensionally consistent model, independent measurements, alternatives, uncertainty analysis and a falsifier.
- The current v2 does not implement the 2187-state ternary layer, comparator mapping, H3 group operations, SO(8) triality, a physical Möbius bundle, or a validated physical model of Giza/Rishat.
- No v2 source file has been modified by this dossier.

## Reproduce the exact checks

From Python 3 with only the standard library:

~~~powershell
python research/full-relational-math-reconstruction-001/verify_relations.py
~~~

The script enumerates Q7, its faces, ternary states and fibres, gates, exact ratios, legacy numerical constants and seven-position cyclic combinatorics. It does not import or execute the graphical legacy application.

## Pinned source baseline

- Legacy source: build/UNIVERSE_2.0.py — Git blob SHA baedf4fab71d95cdca33743aaa5c1528adf74ee3.
- Existing factual audit: UNIVERSE_2_0_GRAPH_AUDIT.md — Git blob SHA 8ae16149fe5e7e67ec01ce230159332378b85f2c.
- Existing forward implementation brief: docs/OPENCODE_UNIVERSE_3_0_TASK.md — Git blob SHA 13f0c582fdfed87b56f5cce26b506dd0c20d4ae1.

Pinned baseline: https://github.com/AudioReclamaRu/universe-os/commit/6506a838be83f7092cee5b4a487b37a9669dd7c9

## Scope boundary

This is a research and preservation package. It is not an implementation of UNIVERSE 3.0, does not alter the v2 engine, and does not assert that numerical correspondences prove physical functions or historical intent.

## Phase 02 — full explicit reconstruction

The extended package is in [phase-02/README.md](phase-02/README.md). It adds:

- Complete Q7 geometric face and inclusion tables, Hasse covers, same-dimensional adjacency and vertex incidence.
- Exact H3 root-system and reflection-group checks in Q(sqrt(5)); exact D4 / Spin(8) triality checks.
- Mass-matrix factorization, dimensions and relabelling audit.
- Scalar nonlinear parameter sweeps and reset-border analysis.
- A critical implementation finding: the v2 XOR graph is used for visualization/readout, but no graph-neighbour coupling operator appears in the time-evolution equation.
- Giza/Richat geology-first validation protocol and dimensionally explicit tests.

The phase-02 data directory includes all 75,938 strict inclusions between nonempty Q7 faces. The empty face is counted separately in the abstract face lattice.
