# GIZA TRIAD — five-node geometry, half-faces and candidate dynamics

## Numeral convention

All integer quantities introduced in this phase are recorded as paired binary/ternary numerals:

\[
\langle n_2\mid n_3\rangle
\]

Both components denote the same integer. Fractions are fractions of paired integers. Metric units remain SI units; the numeral representation of the magnitudes is binary--ternary. Floating-point calculations are used only internally by the reproducibility script; its printed numerical outputs are paired.

This phase is a geometry and model-definition study. It does not assume that the five monuments form a physically coupled resonator.

## A. The five-node comparison set

The working geometric set is:

1. Pyramid of Khufu;
2. Pyramid of Khafre;
3. Pyramid of Menkaure;
4. Great Sphinx of Giza — a selected reference point at the head, not the centre of the whole monument;
5. Pyramid/tomb complex of Khentkaus I — a second comparison target selected in the project's five-node grouping.

**Terminological restriction:** Khentkaus I is an archaeological tomb/step-pyramid complex, not an archaeologically established second sculpted Sphinx. This phase treats it as the second geometric target only. The geometry must not convert the research label “second Sphinx” into an archaeological identification.

The Khentkaus tomb was carved from natural rock, with surrounding quarrying and an associated town. Nell and Ruggles discuss its orientation separately from the three main pyramids and note that its east--west alignment differs markedly from the main pyramid pattern. This makes it a useful comparison object, not a substitute Sphinx.

## B. What “eight facets” means in the model

For each pyramid, define four cardinal side sectors:

\[
S_i=\{N,E,S,W\}.
\]

Split each side into two ordered half-segments:

\[
S_{i,s}=\{s_{\rm CCW},s_{\rm CW}\}.
\]

The resulting eight model elements are

\[
\boxed{\mathcal H_i=
\{N_{\rm CCW},N_{\rm CW},
E_{\rm CCW},E_{\rm CW},
S_{\rm CCW},S_{\rm CW},
W_{\rm CCW},W_{\rm CW}\}.}
\]

This is the correct data structure for testing the user's “two halves per side” geometry. It does **not** assume that every half is a perfectly planar triangular facet. A shallow concave profile may be curved, stepped, course-dependent or represented by two best-fit half-lines. The actual shape must be reconstructed from 3D surface points.

### B.1. Published evidence is not identical for all three pyramids

| Pyramid | Published observation | Evidence status for an eight-half-face model |
|---|---|---|
| Khufu | The stone faces are described as having well-documented concavity. The survey distinguishes the face surfaces from the casing-foundation edges; several foundation edges have different curvature behaviour. | Four-side concavity is historically documented. A complete, comparable numerical profile for all eight half-segments is not supplied by this survey. |
| Khafre | The lower south course shows clear concavity; the west first course is slightly convex; the north also appears slightly convex; the east evidence is less clear. The authors conclude there is no clear evidence that the lower faces are generally concave. Some foundation-level concavity may occur on the west. | Do not assign eight identical concave facets. Preserve side- and course-specific states, including convex and unknown cases. |
| Menkaure | Total-station measurements compare best-fit azimuths of the two halves of selected courses. The sampled segments on courses 6--9 show concavity; the west course 11 is more complex and changes direction within its middle. | Direct paired-half measurements exist for selected side/course segments, but coverage is sparse and not a complete survey of all eight half-faces. |

For Menkaure, the reported difference between the best-fit azimuths of two half-segments ranges from

\[
\langle10101_2\mid210_3\rangle'
\quad\text{to}\quad
\langle111101_2\mid2021_3\rangle'
\]

for the listed sampled courses. The corresponding central inset relative to a flat-face construction is estimated at

\[
\frac{\langle10_2\mid2_3\rangle}
{\langle101_2\mid12_3\rangle}\ {\rm m}
\quad\text{to}\quad
\frac{\langle100_2\mid11_3\rangle}
{\langle101_2\mid12_3\rangle}\ {\rm m}.
\]

The paper explicitly warns that this estimate is based on two fitted straight lines per wall half and would need revision if the wall is curved rather than piecewise straight. The reported west-wall course with zero net half-line difference is not evidence of a flat surface: its quarter-segment analysis reveals a non-uniform central change in direction.

### B.2. Cardinal-side orientation data

The table below gives the mean deviation from cardinality (DFC) for each main side. These are **side orientation** values; they are not the half-face concavity angles.

All entries are in arcminutes.

| Pyramid | North | East | South | West | Source interpretation |
|---|---:|---:|---:|---:|---|
| Khufu | \(-\langle11_2\mid10_3\rangle'\) | \(-\langle100_2\mid11_3\rangle'\) | \(-\langle10001_2\mid122_3\rangle/\langle1010_2\mid101_3\rangle'\) | \(-\langle100_2\mid11_3\rangle'\) | Comparative survey mean by side |
| Khafre | \(-\langle10011_2\mid201_3\rangle/\langle101_2\mid12_3\rangle'\) | \(-\langle100_2\mid11_3\rangle'\) | \(-\langle11101_2\mid1002_3\rangle/\langle101_2\mid12_3\rangle'\) | \(-\langle10101_2\mid210_3\rangle/\langle101_2\mid12_3\rangle'\) | Casing-foundation base |
| Menkaure | \(+\langle10100_2\mid202_3\rangle'\) | \(+\langle1100_2\mid110_3\rangle'\) | \(+\langle100000_2\mid1012_3\rangle'\) | \(+\langle11001_2\mid221_3\rangle'\) | Course-based summary; data are sparse |

Nell and Ruggles caution against quoting orientation at a finer precision than the underlying preserved segments and survey method support. In particular, foundation edges, casing courses and core courses can give different results. The values above must therefore retain their source-level labels.

### B.3. Menkaure's measured half-wall differences

The measured difference between the counter-clockwise and clockwise half-segment best-fit azimuths is:

| Side / course / material | Half-line difference |
|---|---:|
| North, course 7, casing | \(+\langle110010_2\mid1212_3\rangle'\) |
| North, course 9, casing | \(+\langle111101_2\mid2021_3\rangle'\) |
| East, course 6, casing | \(+\langle10101_2\mid210_3\rangle'\) |
| South, course 7, internal | \(+\langle100100_2\mid1100_3\rangle'\) |
| West, course 9, internal | \(+\langle100101_2\mid1101_3\rangle'\) |
| West, course 11, internal, whole-half comparison | \(\langle0_2\mid0_3\rangle'\) |

In the paper's sign convention, a positive difference indicates concavity. The final zero entry is qualified by the paper's quarter-segment analysis; it must not be simplified into a claim that this wall is flat.

## C. Three-pyramid centre geometry

### C.1. Source coordinate basis

The triangle calculation uses the Giza Plateau Mapping Project (GPMP) local survey grid:

- Khufu's base centre is from the GDFS survey of its base;
- Khafre's and Menkaure's base centres are Petrie survey data transformed into the GPMP grid;
- the source author estimates better than one tenth of a metre for Khufu and better than one metre for the other two centres.

The GPMP coordinate system is a local, cardinally oriented survey grid. Distances below are computed from the source centre coordinates, not from decorative map pins.

### C.2. Centre-to-centre lengths

| Pair | Distance | Data tier |
|---|---:|---|
| Khufu--Khafre | \(\langle111100111_2\mid200001_3\rangle\ {\rm m}\) | GPMP centre coordinates |
| Khafre--Menkaure | \(\langle111000110_2\mid121211_3\rangle\ {\rm m}\) | GPMP centre coordinates |
| Khufu--Menkaure | \(\langle10010010010011_2\mid110211210_3\rangle/\langle1010_2\mid101_3\rangle\ {\rm m}\) | GPMP centre coordinates |

### C.3. Triangle angles

Interior angles, represented as exact rational arc-second counts over arcseconds per degree and reduced to paired integer fractions:

| Vertex | Interior angle |
|---|---:|
| Khufu | \(\langle11111000111_2\mid2201202_3\rangle/\langle101101000_2\mid111100_3\rangle^\circ\) |
| Khafre | \(\langle10010100001000001_2\mid10212000221_3\rangle/\langle111000010_2\mid121200_3\rangle^\circ\) |
| Menkaure | \(\langle10100110111001_2\mid112122121_3\rangle/\langle11100001000_2\mid2110200_3\rangle^\circ\) |

The triangle is highly elongated. Khafre's centre projects approximately

\[
\frac{\langle1001011101111_2\mid20122112_3\rangle}
{\langle1010_2\mid101_3\rangle}\ {\rm m}
\]

along the Khufu--Menkaure axis, and sits approximately

\[
\frac{\langle111010101_2\mid122101_3\rangle}
{\langle1010_2\mid101_3\rangle}\ {\rm m}
\]

to one side of it.

The baseline is shorter than the sum of the two adjacent centre distances by approximately

\[
-\frac{\langle101111_2\mid1202_3\rangle}
{\langle1010_2\mid101_3\rangle}\ {\rm m}.
\]

This establishes a near-collinear spatial chain with a nonzero lateral offset. It is not, by itself, evidence of an intended line, resonant path or construction sequence.

## D. Five-node distance network

### D.1. Reference-point definitions

The following distance matrix deliberately keeps three evidence tiers separate:

- **Tier A — GPMP:** survey-grid base centres for the three pyramids.
- **Tier B — Sphinx:** centre-to-selected-head-point distances from a map-derived coordinate set. These are not distances to the nearest Sphinx surface, body centroid or temple.
- **Tier C — Khentkaus I:** geodesic distances to a mapped point for the tomb/site, not a survey-verified centroid of the whole complex.

The exact choice of point matters. A pyramid has a base area; a Sphinx has a long body and a distinct head; Khentkaus I comprises a tomb, temple and associated town. These are not interchangeable point objects.

### D.2. Pairwise matrix

| Node pair | Distance | Source tier |
|---|---:|---|
| Khufu--Khafre | \(\langle111100111_2\mid200001_3\rangle\ {\rm m}\) | A |
| Khufu--Menkaure | \(\langle10010010010011_2\mid110211210_3\rangle/\langle1010_2\mid101_3\rangle\ {\rm m}\) | A |
| Khafre--Menkaure | \(\langle111000110_2\mid121211_3\rangle\ {\rm m}\) | A |
| Khufu--Great Sphinx head point | \(\langle100010011001_2\mid10000112_3\rangle/\langle100_2\mid11_3\rangle\ {\rm m}\) | B |
| Khafre--Great Sphinx head point | \(\langle1101001111101_2\mid100022011_3\rangle/\langle1010_2\mid101_3\rangle\ {\rm m}\) | B |
| Menkaure--Great Sphinx head point | \(\langle10010110011111_2\mid111012201_3\rangle/\langle1010_2\mid101_3\rangle\ {\rm m}\) | B |
| Khufu--Khentkaus I mapped site point | \(\langle110010100100_2\mid11102212_3\rangle/\langle101_2\mid12_3\rangle\ {\rm m}\) | C |
| Khafre--Khentkaus I mapped site point | \(\langle1010011110111_2\mid21100210_3\rangle/\langle1010_2\mid101_3\rangle\ {\rm m}\) | C |
| Menkaure--Khentkaus I mapped site point | \(\langle1011000001_2\mid222010_3\rangle\ {\rm m}\) | C |
| Great Sphinx head--Khentkaus I mapped site point | \(\langle10110111100_2\mid2000101_3\rangle/\langle101_2\mid12_3\rangle\ {\rm m}\) | C |

The matrix is a useful map of spatial relations, but it is not a homogeneous survey adjustment: the pyramid triangle has a stronger coordinate basis than the two target rows.

## E. The provisional cross-axis relation

Use the Khufu--Menkaure centre line as the reference axis. Project the two comparison targets into along-axis and cross-axis components in a local tangent plane.

| Point | Along-axis coordinate from Khufu | Absolute cross-axis offset |
|---|---:|---:|
| Khafre centre | \(\langle1001011101111_2\mid20122112_3\rangle/\langle1010_2\mid101_3\rangle\ {\rm m}\) | \(\langle111010101_2\mid122101_3\rangle/\langle1010_2\mid101_3\rangle\ {\rm m}\) |
| Great Sphinx head point | \(\langle1010100100_2\mid221001_3\rangle/\langle101_2\mid12_3\rangle\ {\rm m}\) | \(\langle1010011011111_2\mid21022220_3\rangle/\langle1010_2\mid101_3\rangle\ {\rm m}\) |
| Khentkaus I mapped site point | \(\langle100001001110_2\mid2220202_3\rangle/\langle101_2\mid12_3\rangle\ {\rm m}\) | \(\langle1111001111_2\mid1100010_3\rangle/\langle10_2\mid2_3\rangle\ {\rm m}\) |

**Coordinate-frame limitation:** the pyramid axis is derived from the GPMP local survey grid, while the two target points are map-derived geodetic coordinates. The current projection uses a local east/north approximation and does not yet apply a surveyed transformation between the GPMP grid and the target-point datum. Therefore the small residual below is an exploratory output of a mixed-frame calculation, not a valid precision match; a proper common-control transformation may change it materially.

The two target points differ along the axis by approximately

\[
\langle100100010_2\mid101202_3\rangle\ {\rm m},
\]

while their cross-axis separation is approximately

\[
\frac{\langle11101010_2\mid22200_3\rangle}
{\langle101_2\mid12_3\rangle}\ {\rm m}.
\]

That cross-axis separation is numerically close to Khafre's cross-axis offset in the present mixed-frame exploratory calculation. The current computed difference between the two rounded magnitudes is approximately

\[
\frac{\langle1_2\mid1_3\rangle}
{\langle101_2\mid12_3\rangle}\ {\rm m}.
\]

**Interpretation:** this is not yet a validated geometric relation. The target points come from different map sources, are not tied to the GPMP control grid through a common surveyed transformation, and have no joint uncertainty budget. The mapped Khentkaus point may not represent the geometric centre of its full complex; the selected Sphinx point represents the head, not the monument's centroid. The apparent sub-metre residual is below the uncertainty implied by this heterogeneous coordinate basis. The only defensible result at this stage is that the geometry suggests a testable candidate; the numerical match itself must be treated as an artifact until common-frame survey data confirm it.

## F. Where “dynamics” begins — and what is not yet known

The geometry yields a spatial network, not a time-evolution law. Distance alone does not tell us whether energy, vibration, pressure, sound or electromagnetic fields couple the nodes.

Define the five-node set

\[
V=\{P_K,P_{Kh},P_M,S,K_1\}.
\]

For each pyramid node, retain eight half-face patches and their measured geometry as node attributes. Do not replace missing half-face normals or curvatures with symmetric guesses.

For a specified carrier \(X\), a propagation-time candidate is

\[
\tau_{ij}^{(X)}=\frac{d_{ij}}{v_X}.
\]

The speed \(v_X\) must be measured or independently specified for the actual medium: air, bedrock, water or an electromagnetic path. The same geometric distance can imply very different delays for different carriers.

A generic mechanical network model could be written as

\[
M_i\ddot q_i+C_i\dot q_i+K_iq_i
+\sum_{j\ne i}K_{ij}(q_i-q_j)=F_i(t).
\]

The local masses, damping, stiffnesses and coupling terms remain unfilled until the physical mechanism and measurements define them. Setting \(K_{ij}\propto d_{ij}^{-1}\) or \(d_{ij}^{-2}\) merely because distance data are available would be an arbitrary modelling choice, not a discovered law.

A directional half-face coupling model can later use measured face normals \(\hat n_{i\alpha}\), the inter-node direction \(\hat r_{ij}\), and empirical transfer functions. One possible test form is

\[
G_{i\alpha,j\beta}(\omega)=
A_{i\alpha,j\beta}(\omega)
(\hat n_{i\alpha}\!\cdot\!\hat r_{ij})
(\hat n_{j\beta}\!\cdot\!-\hat r_{ij}).
\]

This is a proposed measurement-oriented parameterization, not a claim that such coupling has been observed.

## G. What must be measured next

1. **Three-dimensional half-face geometry:** scan each side at multiple elevations and courses; fit left/right half-surfaces; report curvature, normals, roughness, residuals and confidence intervals.
2. **Construction level:** distinguish surviving casing, casing foundations, core courses, pavement and reconstructed edges. Do not merge different physical levels into one ideal pyramid.
3. **Five-node reference frame:** one consistent geodetic survey of the three pyramid base centres, the Sphinx body/head reference points, and defined reference points or a geometric centre for the Khentkaus I complex.
4. **Bedrock and material boundaries:** map bedrock contact, fractures, cavities, lithology, weathering and possible connecting strata.
5. **Dynamic measurements:** synchronized triaxial vibration, acoustic/infrasound, ground motion and environmental controls; impulse responses and transfer functions must be measured at defined source and receiver positions.
6. **Null models:** test the apparent cross-axis match against random point selections within the real site, alternative target centroids, shifted reference axes, coordinate perturbations and randomized half-face assignments.
7. **Uncertainty propagation:** repeat every ratio and apparent alignment under the full coordinate and surface-fit uncertainty ranges.

## H. Current findings and falsifiers

| Finding | Present status | What could weaken or falsify it |
|---|---|---|
| The three pyramid base centres form a highly elongated triangle | Derived from survey-grid centre coordinates | New survey adjustment changes the triangle beyond the source uncertainty |
| Khafre is offset from the Khufu--Menkaure axis | Derived from centre coordinates | A revised base-centre reconstruction materially changes the offset |
| The three pyramids have equivalent eight-concave-half-face geometry | **Not established** | Current survey evidence already indicates non-identical curvature; complete 3D scans may further contradict equivalence |
| The two target points have a cross-axis separation close to Khafre's offset | Exploratory map-point correspondence | Survey-grade points and uncertainty propagation may remove the match |
| The five nodes form a dynamically coupled physical system | **Not established** | Absence of coherent, repeatable transfer/coupling after controls; successful explanation by uncoupled geology/ordinary propagation |

The retracted Biondi--Malanga SAR article is not used as evidence for any external face geometry or internal pyramid structure. The publisher's retraction note records serious methodological and statistical errors. The primary geometric evidence considered here is the ground-based survey literature.

## I. Sources

### Pyramid centres and survey grid

- Glen Dash, *Where, Precisely, are the Three Pyramids of Giza?* — coordinate table, conversion of Petrie's observations into the GPMP control grid, and the stated difference in positional confidence between Khufu and the other two centres: https://www.academia.edu/32879091/Where_Precisely_are_the_Three_Pyramids_of_Giza
- Glen Dash Foundation survey data inventory; includes the Giza pyramid corners and centres and the GPMP control grid: https://dashfoundation.com/archaeology/survey.html

### Four sides and half-wall geometry

- Erin Nell and Clive Ruggles, *The Orientations of the Giza Pyramids and Associated Structures* — independent Total Station measurements of the four sides, side/course differences, Khafre's non-uniform curvature evidence, and Menkaure's half-wall fits: https://doi.org/10.1177/0021828614533065
- Accessible copy of the paper, including Tables 1a, 3b, 5b and 5c: https://piramidasunca.ba/images/2019/03/1302.5622v1.pdf

### Great Sphinx and Khentkaus I target references

- AERA Sphinx mapping and survey archive: https://aeraweb.org/
- Henk Reints' map-based Giza geometry page gives selected centre-to-head distances and explicitly warns that points were placed from Google Maps imagery and that oblique satellite perspective may distort locations; these are low-confidence cross-checks, not survey control: https://henk-reints.nl/pyramidsAnalysis.html
- Mapcarta / OpenStreetMap reference point for the Pyramid of Khentkaus I: https://mapcarta.com/32903442
- Nell and Ruggles' discussion of Khentkaus I's tomb, quarry context, town and distinct orientation is in the paper cited above.
- A current report quoting Egyptologists on the lack of archaeological evidence for a second sculpted Sphinx: https://english.ahram.org.eg/

### Excluded evidence

- Publisher's retraction record for Biondi and Malanga's SAR paper: https://www.mdpi.com/2072-4292/18/16/2679/notes

## J. Reproduction

Run from Python with the standard library:

~~~powershell
python analyze_giza_geometric_network.py
~~~

The driver prints the centre distances, triangle angles, five-node distance matrix, target projections, cardinal-side DFC values and recorded Menkaure half-wall differences using paired binary/ternary numerals. Floating-point values are internal calculation values only.

No physical coupling law, resonant mode or historical function is inferred by the script.


## K. Canonical ideal design relation — pairwise distance invariant

The reconstruction adopts the following as a **design-intent axiom of the ideal Giza model**:

\[
\boxed{
d(P_{\rm Khufu},M_{\rm Great\ Sphinx})
=
d(P_{\rm Khafre},M_{\rm Khentkaus})
=
L^*.
}
\]

This is not treated as a “possible coincidence”. It is the intended cross-pair relation whose geometric implementation we are reconstructing.

### K.1. What is fixed, and what is reconstructed

- The present survey/map observations remain immutable in the raw-data layer, including their coordinate source and uncertainty.
- The exact equality belongs to the ideal-design layer.
- The reconstructed variables include the original reference point within each parent rock mass, the parent-mass envelope, removed/quarried volumes, sculpted surfaces, pyramid base-centre definitions, and survey-frame transformations.
- The ideal length \(L^*\) is a common parameter, not a value forced from one low-confidence map pin.

The first symmetric initial estimate is the geometric mean of the two present estimated distances:

\[
L_0^*=\sqrt{D_A D_B},
\quad
D_A=d_{\rm map}(P_{\rm Khufu},M_{\rm Sphinx}),
\quad
D_B=d_{\rm map}(P_{\rm Khafre},M_{\rm Khentkaus}).
\]

This is only an initial ideal parameter. The complete reconstruction must jointly fit the full five-node network, each pyramid's eight half-faces, and the two parent-mass envelopes.

### K.2. Optimisation statement

Let \(\theta\) contain the unmeasured ideal reference points, parent-mass dimensions and allowed geometric transformations. The ideal reconstruction solves

\[
\theta^*=
\arg\min_{\theta}
\left[
w_1\big(d(P_{\rm Khufu}(\theta),M_{\rm Sphinx}(\theta))-L\big)^2
+w_2\big(d(P_{\rm Khafre}(\theta),M_{\rm Khentkaus}(\theta))-L\big)^2
+\mathcal R(\theta)
\right]
\]

subject to the exact design constraint

\[
d(P_{\rm Khufu}(\theta),M_{\rm Sphinx}(\theta))
=
d(P_{\rm Khafre}(\theta),M_{\rm Khentkaus}(\theta))
=L.
\]

Here \(\mathcal R(\theta)\) penalises unsupported deformation and violations of measured bedrock, quarry, stratigraphic, architectural and survey constraints. The weights are not to be chosen to manufacture a match; they must come from measurement uncertainty or be reported as explicit modelling choices.

The same ideal geometry must then be tested against independent relations: cross-axis offsets, object orientations, pyramid sections, eight half-face profiles, the Sphinx parent massif, the Khentkaus parent outcrop and the retained western-plateau alternative.

### K.3. Status language

- The **intended ideal design relation** is fixed as a reconstruction premise.
- Its exact physical reference points and construction mechanism remain to be reconstructed.
- The current map-distance residual is a property of imperfect present-day reference points, not a reason to demote the ideal relation.
- A better model must explain the measurements without silently rewriting them.


## L. Historical context — human measuring and aiming over millennia

The Giza investigation takes place within the real, long history of human activity on this planet. **People have been observing, measuring, surveying, aiming, laying out axes, checking distances/angles/proportions, building, correcting and transmitting geometric knowledge for millennia.** This is not merely a speculative feature of our model.

Accordingly, Giza is investigated as a cumulative human design and measurement landscape. The primary line of inquiry is to reconstruct successive predecessor states and operations: landscape observation; selection and transfer of reference points; baselines and sight lines; orientation; distance and proportion checks; setting-out; quarrying and shaping; construction; correction; reuse; and the transmission of knowledge between generations.

Do not reduce Giza by default to one isolated construction episode. The exact chronology, number of stages, communities involved and continuity of particular techniques are to be investigated; they do not need to be assumed in advance. That unresolved detail is not a reason to demote the established long history of human measuring and aiming to an optional fantasy.

This historical framework applies to all nodes: the three pyramids and their eight half-face geometries; the Great Sphinx and its parent outcrop; the Khentkaus bedrock mass; the retained western-plateau alternative; and the surrounding terrain, quarry surfaces and geological transformations.

The reconstruction must now search for the actual traces and mathematical consequences of that cumulative work: predecessor alignments, repeated axes, inherited baselines, geometric corrections, construction phases, reused reference points and relationships that become more exact as the layout develops.
