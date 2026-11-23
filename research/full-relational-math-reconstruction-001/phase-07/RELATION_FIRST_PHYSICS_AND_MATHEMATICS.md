# UNIVERSE / GIZA PRIME / RSE — Phase 07
# Relation-first physics and mathematics across all spatial and temporal scales

## Status and purpose

This phase establishes the next common mathematical layer after the Canonical Pattern Atlas and the Phase 06 multiscale resonance architecture.

**The primary research object is a relation, not a scale.** Spatial and temporal scales are unrestricted: every spatial extent, separation, wavelength, resolution, duration, period, delay, lifetime and memory interval remains in scope. No finite ladder of scales is treated as complete.

The task is to identify:
- relations that remain invariant under transformations;
- relations that transform predictably (covariants);
- relations that emerge only collectively;
- relations that change regime, break, bifurcate or cross over;
- relations that recur in different mathematical and physical domains;
- relations between relations, including ratios of ratios, operator correspondences and network-level invariants.

The phase does not assume universal scale invariance. It searches both for invariance and for the precise ways invariance fails.

## I. The relation-first object

Let a system be represented by a state space \(\mathcal X\), with a state \(x\in\mathcal X\). A relation is not merely a numerical ratio. It may be a map, constraint, ordering, interaction, dependence, transformation, correlation, causal coupling, geometric incidence, operator or correspondence.

Write a general relation as

\[
R_\alpha:\mathcal X^{p_\alpha}\longrightarrow\mathcal Y_\alpha,
\]

where \(p_\alpha\) is its arity and \(\mathcal Y_\alpha\) is its output space. Examples include:
- a metric \(d(x_i,x_j)\);
- a ratio \(q_i/q_j\);
- a field relation \(F(x)\);
- a constitutive law \(\sigma=\mathsf C:\epsilon\);
- a transfer operator \(\mathcal T_{j\leftarrow i}\);
- a graph adjacency or hyperedge;
- a probability or conditional dependence;
- a symmetry action or conservation constraint;
- a temporal response kernel \(G(t,t')\).

The relation network is

\[
\mathfrak R=(\mathcal X,\{R_\alpha\},\{\mathcal S_\beta\},\mathcal G),
\]

where \(\mathcal S_\beta\) are admissible transformations and \(\mathcal G\) records composition, compatibility, incidence and dependence between relations.

The object of reconstruction is the structure of \(\mathfrak R\), including relations that are only partially observed.

## II. Transformations: space and time are independent coordinates of the search

Do not collapse spatial and temporal transformations into one scale parameter. Begin with independent transformations:

\[
\mathbf x\mapsto \lambda\,\mathbf x,\qquad
t\mapsto \tau\,t,
\]

with \(\lambda>0\) and \(\tau>0\) independent. Generalize to anisotropic, nonlinear and local transformations:

\[
x^a\mapsto \lambda_a x^a,\qquad
t\mapsto f(t),\qquad
(\mathbf x,t)\mapsto\Phi(\mathbf x,t).
\]

A relation may respond differently to each transformation. For example, a dynamic scaling regime may obey

\[
\tau_c(\ell)\propto \ell^z,
\]

but this is a property to test, not a universal axiom. Anisotropic systems may instead have

\[
\tau_c\propto \ell_\parallel^{z_\parallel}
\propto \ell_\perp^{z_\perp}
\]

or multiple coupled characteristic times. Multiscaling may require a spectrum of exponents rather than one \(z\).

For any candidate relation, test:
1. spatial rescaling alone;
2. temporal rescaling alone;
3. joint rescaling;
4. anisotropic rescaling;
5. translations and rotations where meaningful;
6. nonlinear coordinate changes;
7. changes of resolution, coarse-graining and observation window;
8. changes of boundary conditions and environment.

This prevents a false conclusion that a relation is scale-invariant merely because space and time were rescaled together in one chosen way.

## III. Invariant, covariant, relevant and broken relations

Let \(g\) be an admissible transformation acting on the system. A relation \(R\) is invariant if

\[
R(gx_1,\ldots,gx_p)=R(x_1,\ldots,x_p).
\]

It is covariant if there is a corresponding representation \(\rho(g)\) such that

\[
R(gx_1,\ldots,gx_p)=\rho(g)R(x_1,\ldots,x_p).
\]

It may also be invariant only in a limit, within a regime, or after normalization. Record these as distinct statuses.

For a scale transformation \(g_s\), a quantity may transform with a scaling dimension \(\Delta\):

\[
R(g_s x)=s^\Delta R(x).
\]

A dimensionless ratio can remain invariant even when its constituent quantities change. Conversely, a relation between dimensionless quantities may still drift with scale because of running couplings, finite-size effects, changing boundary conditions or crossover between regimes.

Use the following classifications:
- **exact invariant:** proven under explicitly stated transformations;
- **conditional invariant:** holds under specified assumptions or within a defined class;
- **covariant:** transforms by a known law;
- **asymptotic invariant:** approached in a limit;
- **effective invariant:** stable only over a finite observational or physical window;
- **broken relation:** a declared transformation changes it;
- **crossover relation:** one law gives way to another;
- **unresolved:** insufficient data or theory to classify.

Do not force every relation into the invariant category.

## IV. Relation of relations

The research must go beyond comparing isolated constants. For a set of measured or derived quantities \(q_i\), inspect:

\[
\frac{q_i}{q_j},\quad
\frac{q_i-q_j}{q_k},\quad
\frac{q_iq_j}{q_kq_l},\quad
\frac{R_a}{R_b},
\]

where dimensions permit. Compare ratios of ratios, cross-ratios, recurrence coefficients, normalized spectra, eigenvalue ratios, phase differences, correlation ratios, transfer efficiencies and composition laws.

For four points on a line or a projective coordinate, the cross-ratio is

\[
(a,b;c,d)=\frac{(a-c)(b-d)}{(a-d)(b-c)}.
\]

For general relations, use composition:

\[
R_{c\leftarrow a}
\stackrel{?}{=}
R_{c\leftarrow b}\circ R_{b\leftarrow a}.
\]

Failure of this composition law is informative: it may reveal hidden intermediate states, memory, non-Markovianity, path dependence, hysteresis, unobserved variables or nonlinear interactions.

The atlas comparison must include \(\varphi,\pi,e\), metallic means, algebraic roots, recurrence constants, Feigenbaum constants, fractal dimensions, critical exponents, physical dimensionless constants, special-function values, symmetry invariants and every other relevant family. Compare exact symbolic forms before decimal approximations.

## V. Dimensional analysis: derive admissible relations without mistaking them for unique laws

For variables \(q_1,\ldots,q_n\) built from \(k\) independent base dimensions, form the dimension matrix \(D\). Dimensionless groups correspond to vectors in its null space:

\[
D\mathbf a=0,\qquad
\Pi=\prod_i q_i^{a_i}.
\]

This is the Buckingham-\(\Pi\) construction. It identifies dimensionless combinations compatible with the chosen variables and base dimensions. It does **not**, by itself:
- identify the correct physical variables;
- prove a causal mechanism;
- select a unique basis of dimensionless groups;
- determine the functional relation among groups;
- guarantee similarity when boundary conditions or constitutive laws differ.

Record the variable set, units, dimension matrix, rank, null-space basis and alternative bases. Compare the resulting \(\Pi\)-groups against the Canonical Pattern Atlas, but do not privilege one basis when several are mathematically equivalent.

For fields, tensors, nonlocal operators and systems with multiple time dimensions or characteristic velocities, extend the dimensional model explicitly rather than forcing them into a simplistic length-mass-time table.

## VI. Renormalization and coarse-graining: relations that survive changing resolution

Let \(X\) be a microscopic or fine-resolution description and let \(\mathcal C_b\) be a coarse-graining map with factor \(b\). A renormalization map acts on the effective description or its couplings:

\[
\mathbf g'=\mathcal R_b(\mathbf g).
\]

A fixed point satisfies

\[
\mathcal R_b(\mathbf g^*)=\mathbf g^*.
\]

Near a fixed point, linearize:

\[
\delta\mathbf g'=\mathsf J_b\,\delta\mathbf g,
\]

where eigenvalues of \(\mathsf J_b\) classify perturbations as relevant, irrelevant or marginal under the specified convention and direction of flow.

This provides a rigorous question: which relations persist when details are removed, and which details control the large-scale behaviour?

Important distinctions:
- coarse-graining is not merely resizing an image;
- a fixed point is not proof that all systems share the same microphysics;
- universality applies to defined classes with shared relevant structure;
- different microscopic systems may share exponents or scaling functions while retaining different amplitudes, boundaries and observables;
- a finite system may display only an approximate scaling window;
- hidden variables and nonlocal couplings can invalidate an overly simple coarse-graining.

Track both the fixed-point structure and the path by which a system approaches or leaves it.

## VII. Continuous and discrete scale relations

Test continuous scale invariance:

\[
F(\lambda x)=\lambda^\Delta F(x)
\]

and discrete scale invariance, where the relation holds only for a preferred scaling factor \(\lambda_0\):

\[
F(\lambda_0 x)=\lambda_0^\Delta F(x).
\]

Discrete scale invariance can produce log-periodic modulation, for example

\[
F(x)=x^\Delta P\!\left(\frac{\ln x}{\ln\lambda_0}\right),
\]

where \(P\) is periodic. This creates a direct comparison target for recurrence ratios, substitution systems, complex scaling exponents, hierarchical networks and fractal constructions.

Do not identify log-periodicity from a short noisy sequence without testing alternative models, sampling effects, finite-size effects and multiple-comparison bias.

## VIII. Space-time relations without a privileged scale

Represent spatial and temporal structure jointly, but retain their distinct roles. A general two-point relation may depend on

\[
C(\mathbf r,\Delta t)
=
\langle A(\mathbf x,t)B(\mathbf x+\mathbf r,t+\Delta t)\rangle,
\]

or on a retarded response kernel

\[
G(\mathbf x,t;\mathbf x',t').
\]

Investigate:
- propagation cones and finite signal speeds;
- dispersion relations \(\omega(\mathbf k)\);
- phase and group velocities;
- correlation lengths and correlation times;
- dynamic exponents and multiple dynamic exponents;
- memory kernels and non-Markovian response;
- space-time anisotropy;
- causal order and relativistic invariants;
- systems in which time is emergent, discrete, cyclic or multi-timescale in the effective model.

A shared numerical ratio between a spatial length and temporal duration is meaningless until a conversion law or characteristic velocity is specified. Preserve units and identify the physical bridge.

## IX. Emergence: when the whole has relations absent from its parts

A collective relation may not be reducible to the properties of one component. Candidate mechanisms include:
- synchronization and phase locking;
- percolation and connectivity transitions;
- collective eigenmodes and mode hybridization;
- nonlinear feedback and self-organization;
- criticality and bifurcation;
- frustration and competing constraints;
- network topology and spectral gaps;
- collective memory and hysteresis;
- geometric constraint and rigidity transitions;
- information integration and distributed control.

For each emergent property, compare:
1. isolated-component model;
2. uncoupled ensemble;
3. coupled linear model;
4. nonlinear coupled model;
5. model with memory and hidden states;
6. alternative graph or geometry;
7. null model with matched marginals but destroyed relational structure.

The key test is whether the collective property disappears when the relevant relations are removed or randomized.

## X. The whole-atlas comparison protocol

Every new candidate relation receives a comparison record with these fields:

| Field | Required content |
|---|---|
| Candidate | Exact symbolic relation or operator |
| Domain | Physical, mathematical, geometric, biological, geological, cosmological or mixed |
| Inputs | Variables, definitions, units, source and measurement method |
| Transformation set | Spatial, temporal, anisotropic, nonlinear, coarse-graining and boundary transformations tested |
| Relation class | Invariant, covariant, asymptotic, effective, broken, crossover or unresolved |
| Atlas matches | All relevant constant, recurrence, fractal, symmetry, topology, spectrum and dynamics families compared |
| Match type | Exact identity, structural isomorphism, conditional universality, numerical candidate, exploratory resemblance or rejected under a stated test |
| Dimensional audit | Units, dimension matrix, admissible dimensionless groups |
| Mechanism | Source, receiver, path, interface, operator and energy/information budget where physical |
| Alternatives | Competing relations, hidden variables, null models and independent explanations |
| Uncertainty | Measurement, model, parameter, resolution and selection uncertainty |
| Falsifier | Observation or calculation that would distinguish the candidate from alternatives |
| Status | Measured, source-reported, derived, reconstructed, idealized, assumed or unknown |

A relation must be compared with the entire atlas even if the first apparent match is compelling. Record both positive matches and informative mismatches.

### Candidate strength is multidimensional

Do not compress all confidence into one score. Maintain separate axes:
- mathematical exactness;
- empirical repeatability;
- physical mechanism;
- causal identification;
- predictive performance;
- historical interpretation, where relevant.

An exact mathematical identity can have no known physical realization. A strong empirical scaling law can have no exact symbolic identity. A physically plausible mechanism can remain unmeasured. These are different states, not a single ladder.

## XI. Null models and coincidence discipline

A candidate relation is not discarded merely because many comparisons were possible. Instead, quantify how surprising it is under explicit alternatives.

For numerical relations:
- define the search interval and precision before interpreting a match;
- account for the number of constants, exponents, transforms and data windows tested;
- compare against shuffled, phase-randomized, surrogate and structure-preserving nulls as appropriate;
- test out-of-sample and independent datasets;
- preserve the original candidate and its provenance even if it fails a declared test.

For structural relations:
- compare degree-preserving or spectrum-preserving graph nulls where appropriate;
- randomize labels while preserving geometry or incidence when that is the relevant control;
- compare against alternative generators and boundary conditions;
- test whether the correspondence survives perturbation.

A failed candidate is retained as a documented negative result, not silently erased. The canonical principle remains: **«Отсутствие доказательства не является доказательством отсутствия».** Equally, failure to reject a candidate is not proof that it is true.

## XII. Application to Phase 06 and GIZA PRIME

Phase 06 supplies the physical bridge grammar \(\mathcal T_{j\leftarrow i}(\omega)\). Phase 07 generalizes it beyond oscillations and beyond a scale ladder.

For GIZA PRIME, use the same relation-first protocol to investigate:
- geometry-to-geometry relations;
- parent-outcrop and transformed-remnant relations;
- material, boundary and interface relations;
- mechanical, acoustic, fluid and electromagnetic operators;
- spatial registration and temporal succession;
- local and collective modes;
- energy and information transfer;
- invariants and controlled deviations across the whole arrangement.

The ideal cross-pair relation already defined in the Giza canon remains an ideal design invariant in its ideal layer. Its raw observations, coordinate uncertainties and reconstruction assumptions remain separately recorded. The relation-first method asks what other geometric, material, dynamical or organizational relations are jointly compatible with it.

No direct Giza-to-Earth, Giza-to-ionosphere or Giza-to-cosmological causal bridge is asserted by this framework. Such bridges require their own transfer operator, measurements, energy budget and falsifiable predictions.

## XIII. Immediate research programme

Proceed in this order, without restricting the scope to a predetermined list of scales:

1. **Relation ontology:** enumerate relation types and their compositions across geometry, dynamics, fields, networks, probability, information and topology.
2. **Transformation atlas:** define independent spatial, temporal, anisotropic, nonlinear and coarse-graining transformations.
3. **Invariant search:** identify exact and conditional invariants, covariants and dimensionless groups.
4. **Scale-flow search:** identify fixed points, relevant/irrelevant directions, crossovers, broken scaling and discrete scale invariance.
5. **Relation-of-relations search:** compare ratios of ratios, operator compositions, spectra, recurrence maps and network invariants.
6. **Whole-atlas comparison:** compare every candidate with the full Canonical Pattern Atlas.
7. **Physical realization:** for candidates with physical meaning, specify carriers, sources, receivers, mechanisms, energy/information budgets and falsifiers.
8. **Negative-result retention:** preserve mismatches, failed tests and unresolved candidates with their declared test conditions.

This order is a workflow, not a claim that nature follows a single hierarchy. New evidence may send the investigation back to any earlier step.

## XIV. Canonical conclusion

The research does not ask which scale is fundamental. It asks which relations are fundamental, which are emergent, which are invariant, which transform, which recur, which break, and how relations compose into larger networks.

All spatial and temporal scales remain open simultaneously. The same candidate relation is examined in its exact mathematical form, its transformations, its empirical realizations and its possible physical mechanisms. The Canonical Pattern Atlas is the mandatory comparison base.

**No scale is privileged. No relation is accepted by resemblance alone. No candidate is erased merely because evidence is missing.**
