# Phase 14 — structural Atlas comparators: graphs and recurrence operators

## Purpose

Phases 08–13 primarily work with numerical relations, dimensional groups, scaling laws and propagated uncertainties. Phase 14 adds structural comparisons that cannot be reduced to comparing isolated decimal constants.

Two initial structural families are implemented:
1. finite simple graphs and their exact combinatorial/spectral fingerprints;
2. finite observed sequences and exact rational linear recurrence operators.

This is a machine-readable starter subset of the Canonical Pattern Atlas, not an implementation of every structural family in the Atlas.

## A. Finite graph comparator

### Input

A graph is supplied as a node-label list and an undirected edge list. The comparator accepts simple graphs only: no self-loops, duplicate edges or undeclared endpoints. Node labels are identifiers; their literal names do not affect the structural comparison.

### Exact invariants

The comparator calculates:
- vertex and edge counts;
- descending degree sequence;
- connected-component sizes;
- cycle rank \(m-n+c\), where \(c\) is the number of connected components;
- bipartiteness and connected-graph diameter;
- triangle count;
- adjacency spectral moments \(\operatorname{tr}(A^k)\);
- exact adjacency characteristic polynomial.

The characteristic polynomial is reconstructed from the traces of powers of the integer adjacency matrix using Newton identities. Its coefficients are exact integers and are written in paired binary/ternary notation. No floating-point eigenvalue approximation is required.

Equal adjacency characteristic polynomials mean the graphs are adjacency-cospectral; they do not prove graph isomorphism.

### Isomorphism check

A joint one-dimensional Weisfeiler–Leman color-refinement pass supplies a necessary partition check. A bounded backtracking search then tests exact graph isomorphism using degree, refined colors and adjacency consistency.

The default exact-search limit is twenty-four vertices and a bounded number of recursive search nodes. If the limit is exceeded, the output says that exact isomorphism was not completed; it does not turn the incomplete search into a negative result.

The current finite graph reference subset is:
- hypercubes \(Q_3\) and \(Q_4\);
- cycles \(C_5\) and \(C_6\);
- path \(P_5\);
- complete graph \(K_4\);
- star \(S_4\).

The generator helpers can create small \(Q_n\), \(C_n\), \(P_n\), \(K_n\) and star graphs, but the automated reference registry remains the finite list above.

## B. Linear recurrence comparator

For a declared or observed finite sequence, the comparator searches for the lowest order \(k\) with a unique exact rational solution to

\[
a_n=c_1a_{n-1}+c_2a_{n-2}+\cdots+c_ka_{n-k}.
\]

It uses exact Fraction arithmetic and rational Gaussian elimination. The returned recurrence coefficients, characteristic polynomial coefficients and initial state are exact. Integer numerators/denominators use the paired numeral convention.

The initial-state vector is kept separate from the recurrence operator:
- **operator match:** recurrence coefficient vectors agree;
- **exact initial-state match:** both operator and initial state agree;
- **projective initial-state match:** initial states differ by one exact scalar factor.

This distinction is necessary because Fibonacci and Lucas sequences share the same second-order recurrence operator but have different initial states. A scaled Fibonacci sequence has the same operator and a projectively scaled initial state, not the same exact initial state.

The current recurrence reference subset contains Fibonacci/Lucas, Pell, Jacobsthal, Tribonacci and Padovan operators.

A finite list can fit more than one recurrence if the search order or observed window is too broad. The engine only reports a unique minimal-order solution within the declared maximum order. It does not claim that a finite recurrence continues indefinitely without independent evidence.

## C. What is and is not compared

The graph comparator compares finite graph structure and adjacency spectra. The sequence comparator compares recurrence operators and initial states. It does not yet compare:
- graph Laplacian spectra, directed/multiplex/hypergraphs or weighted graphs;
- full graph automorphism groups, embeddings or graph limits;
- Mandelbrot/Julia/IFS generators, Penrose tiling substitutions or fractal dimensions;
- nonlinear dynamical operators, differential equations or symmetry representations;
- arbitrary algebraic numbers and exact identities beyond the declared rational recurrence/graph computations.

Those remain distinct structural-comparator tasks. They are not silently represented by a numerical constant list.

## D. Validation

Fifteen standard-library tests pass locally. They cover exact \(Q_3\) and relabelled \(C_5\) isomorphism, graph cycle rank/diameter/triangle count and paired spectral moments, input graph validation, Fibonacci/Lucas/Tribonacci operator and initial-state distinctions, projective scaling, finite-data recurrence rejection and paired count output.

The synthetic input/output are demonstrations using generated graph structures and well-known constructed sequences, not physical measurements or evidence of shared historical origin.

## E. Next increments

1. Add graph Laplacian, normalized Laplacian, signless Laplacian and directed/weighted graph comparators.
2. Add exact graph isomorphism certificates and automorphism group generators for bounded graphs.
3. Add substitution tilings, symbolic dynamics, finite automata and recurrence-matrix conjugacy.
4. Add fractal generator comparison through affine IFS descriptors, incidence rules and dimension spectra.
5. Add null models preserving selected graph invariants and sequence marginals.
6. Connect structural signatures to source-backed physical, archaeological, geological and sensor datasets without replacing their provenance or uncertainty.
