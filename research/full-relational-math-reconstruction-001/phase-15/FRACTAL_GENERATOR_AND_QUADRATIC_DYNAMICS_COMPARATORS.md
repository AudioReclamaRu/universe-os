# Phase 15 — fractal generator and quadratic dynamics comparators

## Purpose

Phase 14 added finite graph and recurrence comparisons. Phase 15 adds structural comparison at the generator/operator level for selected fractal families. It does not compare only approximate pictures, pixel masks or rounded dimensions.

Two families are implemented:
- affine iterated-function systems (IFS) for Cantor, Sierpinski gasket/carpet, Menger sponge and Koch curve;
- quadratic complex polynomial dynamics for the Mandelbrot parameter family and fixed-parameter Julia maps.

This is a finite, explicit structural Atlas subset. It does not close the entire fractal catalogue.

## A. Exact affine IFS representation

Each IFS supplies:
- ambient dimension;
- declared coordinate system;
- an exact radical field (the built-in Koch rotations use \(\mathbb Q(\sqrt3)\));
- affine maps \(F_i(x)=A_i x+b_i\).

Rational coefficients are parsed as exact fractions. Algebraic coefficients are represented as \(a+b\sqrt3\) and multiplied exactly in the quadratic field. Map order is ignored by sorting exact map signatures; the set of affine maps and the coordinate-system declaration must match.

Built-in generators:
- Cantor set: two contractions by \(1/3\), translations \(0\) and \(2/3\);
- Sierpinski gasket: three \(1/2\)-contractions in barycentric triangle coordinates;
- Sierpinski carpet: eight \(1/3\)-contractions, with the centre square omitted;
- Menger sponge: twenty \(1/3\)-contractions, with the seven central/face-centre cubes omitted;
- Koch curve: four \(1/3\)-similarities, including exact \(\pm60^\circ\) rotations represented in \(\mathbb Q(\sqrt3)\).

The coordinate convention is part of the fingerprint. The gasket maps use barycentric triangle coordinates, so the representation is affine-equivalent to the familiar equilateral construction; it is not silently compared with an unrelated Cartesian encoding.

### Contraction and similarity dimension

A sufficient infinity-norm contraction bound is checked for every affine map. A common similarity ratio is recovered exactly when each linear map has \(A_i^\mathsf{T}A_i=r^2I\) with the same rational-square root \(r\).

When all \(N\) maps share a contraction ratio \(r\), the similarity-dimension candidate is

\[
s_{\rm sim}=\frac{\ln N}{\ln(1/r)}.
\]

This equals the Hausdorff dimension only under suitable separation assumptions (for example, the open set condition). Otherwise it is a similarity-dimension value or upper-bound candidate, not automatically the Hausdorff dimension. Noncontractive maps do not receive a similarity-dimension value.

The comparator currently requires exact generator equality in the declared coordinates. General affine conjugacy, map weights, overlapping IFS theory, nonuniform contraction ratios and multifractal measures are not yet implemented.

## B. Quadratic complex dynamics: Mandelbrot and Julia

A quadratic polynomial is represented exactly as

\[
f(z)=a z^2+bz+c,
\]

with rational real and imaginary parts. For \(a\ne0\), the affine coordinate \(w=az+b/2\) conjugates the polynomial to

\[
w\mapsto w^2+C,\qquad
C=ac+\frac b2-\frac{b^2}{4}.
\]

The transformation and normalized parameter \(C\) are computed exactly in Gaussian rational arithmetic.

The input distinguishes:
- **variable parameter:** a family of maps with a free parameter \(c\), corresponding to the role used in the Mandelbrot parameter-space construction;
- **fixed parameter:** one specific quadratic map, the setting for a Julia-set construction.

The exact built-in checks recognize the canonical variable family \(z^2+c\), fixed Julia map \(z^2\), fixed Julia map \(z^2-1\), and arbitrary fixed quadratics after affine normalization to the \(z^2+C\) form.

This descriptor compares polynomial operators and parameter roles. It does not render the Mandelbrot set, compute Julia pixels, iterate critical orbits, decide parameter membership or estimate fractal boundaries. In particular, matching the family operator is not a claim that a particular parameter lies inside or outside the Mandelbrot set.

## C. Interpretation and evidence boundary

An exact generator match means that the supplied finite affine maps or polynomial operator coincide with a reference descriptor in the declared coordinates/normal form. It does not show that two physical objects have a common origin or that a physical process implements the same generator.

The numerical similarity dimension is secondary to the exact generator description. A familiar dimension value by itself is not used as an exact structural match.

## D. Validation

Fifteen standard-library tests pass locally. They cover exact Cantor, Sierpinski, carpet, Menger and Koch generator recognition; map-order invariance; coordinate-system separation; contraction checks; exact Mandelbrot/Julia parameter-role distinction; quadratic affine conjugacy; invalid degree/leading coefficient; and missing-candidate validation.

The synthetic input/output are generator descriptors and quadratic maps, not measurements from natural systems.

## E. Next increments

1. **Partly advanced in Phase 16:** exact affine-conjugacy detection now supports dimensions 1–3 over a common real quadratic field \\(\\mathbb Q(\\sqrt d)\\), where \\(d\\) is positive, squarefree and nonsquare. It is not yet a general arbitrary-number-field engine, and mixed-field composita remain unsupported.
2. **Partly advanced in Phase 16:** coordinate-invariant matching is implemented for finite affine IFS map families by solving \\(H\\circ F_i=G_{\\pi(i)}\\circ H\\) with an invertible affine map. The finite permutation search is capped and reports unresolved status when it cannot exhaust the search; similarity conjugacy is covered only when it is an affine coordinate change in the supported exact field.
3. Add nonuniform IFS, map weights, overlaps and multifractal spectra.
4. Add symbolic substitutions for Penrose/Ammann–Beenker tilings and other self-similar structures.
5. Add critical-orbit and parameter-plane tests for Mandelbrot/Julia families, with explicit finite-iteration limitations.
6. Add formal grammar descriptors for cellular automata, L-systems and other generator families from the full Atlas.

See also [Phase 16](../phase-16/AFFINE_IFS_CONJUGACY_AND_COORDINATE_INVARIANCE.md), which implements and tests the affine-conjugacy increment without claiming a physical origin or mechanism.
