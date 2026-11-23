# UNIVERSE 2.0 — FULL RELATIONAL MATHEMATICAL RECONSTRUCTION 001

**Status:** foundational research dossier  
**Branch:** research/full-relational-math-reconstruction-001  
**Pinned baseline commit:** 6506a838be83f7092cee5b4a487b37a9669dd7c9  
**Legacy v2 source:** preserved unchanged

## Purpose

This directory preserves the mathematics, exact derivations, source-code facts, exploratory correspondences, nonlinear equations, validation rules and open questions developed around UNIVERSE 2.0 and GIZA PRIME / RSE.

The central research object is the **network of relations**, not a collection of absolute numbers.

## Phase 01 — foundational reconstruction

The foundational work defines binary states and the ternary face-state encoding of the Boolean hypercube. For a word length represented as

\[
m=\langle111_2\mid21_3\rangle,
\]

the project uses the corresponding binary state space and ternary face-state space. Earlier phase files preserve their original notation and exact historical contents.

## Phase 02 — full explicit reconstruction

The extended package is in [phase-02/README.md](phase-02/README.md). It adds:

- Complete hypercube face and inclusion tables, Hasse covers, same-dimensional adjacency and vertex incidence.
- Exact H3 root-system and reflection-group checks in Q(sqrt(5)); exact D4 / Spin(8) triality checks.
- Mass-matrix factorization, dimensional and relabelling audits.
- Scalar nonlinear parameter sweeps and reset-border analysis.
- The finding that the v2 XOR graph is used for visualization/readout, but no graph-neighbour coupling operator appears in the time-evolution equation.
- A geology-first Giza/Richat protocol and dimensionally explicit tests.

## Phase 03 — cross-domain universal patterns

The new phase is in [phase-03/README.md](phase-03/README.md). It establishes an exact bijection and order isomorphism between:

- the odd support of Pascal's triangle over a binary row block;
- digitwise subset pairs from Lucas' theorem;
- ternary coordinate states;
- the nonempty face-inclusion poset of a Boolean hypercube.

It also records exact self-similar and spectral scaling relations for the Sierpiński gasket, Fibonacci substitution/inflation, Feigenbaum renormalization universality classes, and conditional river-network scaling. All mathematical integer keys newly introduced in Phase 03 use paired binary/ternary notation.

The Phase 03 finite checker is [verify_pascal_cube_face_isomorphism.py](phase-03/verify_pascal_cube_face_isomorphism.py).

## Evidence policy

- Exact identities and combinatorial isomorphisms are distinguished from empirical regularities.
- Equations explicitly present in v2 are facts about the code.
- A numerical correspondence between independently defined structures is not proof of a common physical mechanism.
- Physical interpretation requires a dimensionally consistent model, independent measurements, alternatives, uncertainty analysis and a falsifier.
- No v2 source file has been modified by this dossier.

## Reproduce the existing checks

From Python 3 with only the standard library:

~~~powershell
python research/full-relational-math-reconstruction-001/verify_relations.py
~~~

The script enumerates the original finite structures and audits their invariants. It does not import or execute the graphical legacy application.

## Pinned source baseline

- Legacy source: build/UNIVERSE_2.0.py — Git blob SHA baedf4fab71d95cdca33743aaa5c1528adf74ee3.
- Existing factual audit: UNIVERSE_2_0_GRAPH_AUDIT.md — Git blob SHA 8ae16149fe5e7e67ec01ce230159332378b85f2c.
- Existing forward implementation brief: docs/OPENCODE_UNIVERSE_3_0_TASK.md — Git blob SHA 13f0c582fdfed87b56f5cce26b506dd0c20d4ae1.

Pinned baseline: https://github.com/AudioReclamaRu/universe-os/commit/6506a838be83f7092cee5b4a487b37a9669dd7c9

## Scope boundary

This is a research and preservation package. It is not an implementation of UNIVERSE 3.0, does not alter the v2 engine, and does not assert that mathematical correspondences prove physical functions or historical intent.
