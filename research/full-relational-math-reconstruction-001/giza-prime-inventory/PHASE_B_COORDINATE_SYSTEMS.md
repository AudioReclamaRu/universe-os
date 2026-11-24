# PHASE B — COORDINATE SYSTEMS

## Registered systems

| System | Type | Datum | Confirmation |
| --- | --- | --- | --- |
| ARCE_Sphinx_GRID_SEPARATE | local archaeological grid | unverified | HISTORICAL_DESCRIPTION_ONLY_NO_TRANSFORM |
| GPMP_CONTROL_GRID | geodetic control network local grid | unverified | DOCUMENTED_IN_DESCRIPTION_ONLY |
| KML_GEOGRAPHIC_PAIR | geographic longitude/latitude | unverified | AXIS_ORDER_OBSERVED_DATUM_UNVERIFIED |
| LOCAL_GRID_UNVERIFIED | local projected-like planar grid | unverified | DOCUMENTED_IN_DESCRIPTION_ONLY |
| PETRIE_LOCAL_GRID_UNRESOLVED | historical local station grid | unverified | UNRESOLVED_HISTORICAL_GRID |

## Separation

- `gdfs_2012_vs_2015_vs_2016_vs_2018`: separately registered; numeric-range similarity is not proof of a shared mathematical system
- `gpmp_to_arce_transform`: not_performed
- `gpmp_vs_arce_sphinx_grid`: separate
- `local_grid_vs_geographic_pair`: relation_unresolved
- `petrie_historical_vs_local_grid`: relation_unresolved

## Transformations

Performed: none. Reason: no verified common control points with documented coordinate compatibility; 2D/3D similarity, Helmert and affine fits are withheld to avoid fabricating a datum relationship

## Observed anomalies

- elevation_absent_records: 68
- kml_z_nonzero_records: 0
- swapped_longitude_label_records: 9315

No datum was promoted. No Helmert, similarity or affine transform was fitted: there are no verified common control points with documented compatibility.
