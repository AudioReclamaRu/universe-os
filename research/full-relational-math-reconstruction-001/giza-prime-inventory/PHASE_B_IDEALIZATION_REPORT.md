# PHASE B — IDEALIZATION REPORT

Idealized models: 24.

| model_id | type | points | status |
| --- | --- | --- | --- |
| IDEAL-B-GDFS-2012-FRAME-001 | network_principal_axis_frame | 1539 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2012-HULL-001 | plan_convex_envelope | 1539 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2012-SPACING-001 | sampling_spacing_distribution | 1539 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2012-ELLIPSOID-001 | descriptive_ellipsoidal_envelope | 1539 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2015-FRAME-001 | network_principal_axis_frame | 1100 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2015-HULL-001 | plan_convex_envelope | 1100 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2015-SPACING-001 | sampling_spacing_distribution | 1100 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2015-ELLIPSOID-001 | descriptive_ellipsoidal_envelope | 1100 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2016-FRAME-001 | network_principal_axis_frame | 4746 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2016-HULL-001 | plan_convex_envelope | 4746 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2016-SPACING-001 | sampling_spacing_distribution | 4746 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2016-ELLIPSOID-001 | descriptive_ellipsoidal_envelope | 4746 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2018-FRAME-001 | network_principal_axis_frame | 4569 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2018-HULL-001 | plan_convex_envelope | 4569 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2018-SPACING-001 | sampling_spacing_distribution | 4569 | IDEALIZED_MODEL |
| IDEAL-B-GDFS-2018-ELLIPSOID-001 | descriptive_ellipsoidal_envelope | 4569 | IDEALIZED_MODEL |
| IDEAL-B-GIZA_CORNER-FRAME-001 | network_principal_axis_frame | 15 | IDEALIZED_MODEL |
| IDEAL-B-GIZA_CORNER-HULL-001 | plan_convex_envelope | 15 | IDEALIZED_MODEL |
| IDEAL-B-GIZA_CORNER-SPACING-001 | sampling_spacing_distribution | 15 | IDEALIZED_MODEL |
| IDEAL-B-GIZA_CORNER-ELLIPSOID-001 | descriptive_ellipsoidal_envelope | 15 | IDEALIZED_MODEL |
| IDEAL-B-GPMP-FRAME-001 | network_principal_axis_frame | 41 | IDEALIZED_MODEL |
| IDEAL-B-GPMP-HULL-001 | plan_convex_envelope | 41 | IDEALIZED_MODEL |
| IDEAL-B-GPMP-SPACING-001 | sampling_spacing_distribution | 41 | IDEALIZED_MODEL |
| IDEAL-B-GPMP-ELLIPSOID-001 | descriptive_ellipsoidal_envelope | 41 | IDEALIZED_MODEL |

## Skipped

- PETRIE: no elevation: 3D idealization inputs are unavailable; 2D-only structures withheld until vertical datum is known (UNKNOWN)

## Boundary

- Every model has the full contract: model_id, model_type, source_ids, input_geometry_ids, method, parameters, parameter_units, assumptions, fit_residual, uncertainty, validity_domain, model_status, limitations, falsification_conditions.
- Idealized geometry is not measured geometry.
- `IDEAL-B-*-ELLIPSOID-001` uses a declared factor 2.0, not a fitted confidence region; outside points are retained as residuals.
- No terrain mesh and no monument surface were generated.
