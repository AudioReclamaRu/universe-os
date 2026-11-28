# 08 — H3, Q(sqrt(5)), D4 and Spin(8) triality

## H3 exact realization
Let phi=(1+sqrt(5))/2. A standard unit-root realization consists of the six axial roots (±1,0,0) and cyclic permutations, together with the 24 vectors one-half of (±1, ±phi, ±phi^-1) in even coordinate permutations. There are 30 roots; each has exact norm squared 1. Coordinates lie in Q(sqrt(5)), stored as pairs a+b sqrt(5) with rational a,b.

For a unit root alpha, reflection is s_alpha(x)=x-2<x,alpha>alpha. Exact arithmetic in Q(sqrt(5)) verifies closure of the 30 root reflections. The full reflection group has order 120: 60 elements with determinant +1 and 60 with determinant -1. The orientation-preserving subgroup has order 60. The root polytope has 30 vertices, 60 edges and 32 faces (20 triangles, 12 pentagons). Distinct root inner products are -1, -phi/2, -1/2, -1/(2phi), 0, 1/(2phi), 1/2, phi/2, 1.

These are mathematical properties of H3; the v2 label H3 does not itself implement root reflections.

## D4 / so(8)
Phi(D4)={±e_i±e_j : i<j} has 24 roots. The Lie algebra dimension is dim so(8)=8*7/2=28. The legacy octave label containing 28 is a numerical correspondence, not an implementation of the Lie algebra.

## Triality
Two exact orthogonal matrices preserve the D4 root set:
T2=1/2 [[1,1,1,-1],[1,1,-1,1],[1,-1,1,1],[-1,1,1,1]]
T3=1/2 [[1,1,1,1],[1,1,-1,-1],[1,-1,1,-1],[-1,1,1,-1]].
T2 has order 2; T3 has order 3; they generate six elements, S3. With the stated half-spin parity convention, T3 cycles 8v -> 8s- -> 8s+ -> 8v; T2 exchanges 8v and 8s- and fixes 8s+. The 28-dimensional adjoint representation is fixed by the outer permutation. Triality is the exceptional outer automorphism structure of so(8)/Spin(8); do not conflate global-form distinctions between Spin(8) and SO(8).

## Phi and musical ratios
3/2 is a Fibonacci convergent to phi, not equal to it: phi-3/2 is about 0.118034 (relative shortfall about 7.2949%). Twelve fifths versus seven octaves gives the exact Pythagorean comma p=(3/2)^12/2^7=3^12/2^19=1.0136432647705078125. This tuning identity does not imply a common physical or geometric invariant with Q7, H3, Giza or Richat.

Exact root checks establish finite mathematics only; they do not create a canonical embedding H3 -> Q7 or a physical interpretation for v2 mass labels.