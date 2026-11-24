# PHASE B — SOURCE INVENTORY

Recursive, read-only inventory of the two owner-nominated directories.
No fallback search, no downloads, no writes to source files.

## Roots

- raw: `E:\GIZA_PRIME_LAB\gizalab\data\raw\dash_foundation`
- derived: `E:\GIZA_PRIME_LAB\gizalab\data\derived\phase2\kmz`

## Counts

| Quantity | Value |
| --- | --- |
| raw files | 15 |
| derived files | 8 |
| expected total | 12078 |
| observed total | 12078 |
| delta | 0 |

## Expected sets

| Set | Expected | Found | Parsed | Actual | Match |
| --- | --- | --- | --- | --- | --- |
| GDFS-2012-for-GE-21vii18.json | 1539 | True | True | 1539 | True |
| GDFS-2015-Master-25iii17-edited-child.json | 1100 | True | True | 1100 | True |
| GDFS-2016-23ix18.json | 4746 | True | True | 4746 | True |
| GDFS-2018-12xii18.json | 4569 | True | True | 4569 | True |
| GPMP-Control-Monuments.json | 41 | True | True | 41 | True |
| Giza-Corner-Points-2v17.json | 15 | True | True | 15 | True |
| Petries-Stations.json | 68 | True | True | 68 | True |

## Cryptographic identifiers (kept separate)

- raw-byte SHA-256, git blob SHA-1 and canonical-JSON SHA-256 are NOT interchangeable.
- canonical form: sorted keys, fixed separators, UTF-8, NaN/Infinity forbidden; independent of CRLF/LF.

| Derived file | raw SHA-256 | canonical SHA-256 |
| --- | --- | --- |
| GDFS-2012-for-GE-21vii18.json | `45c2987d2cd2e873` | `ce4a7566b002c05c` |
| GDFS-2015-Master-25iii17-edited-child.json | `ae2734f316bad558` | `71e36f748291716b` |
| GDFS-2016-23ix18.json | `fbf3471c453e6fcf` | `0348146ddf6d11ea` |
| GDFS-2018-12xii18.json | `4d0bd5cb9e11df4b` | `71e4525a4aaccd53` |
| GPMP-Control-Monuments.json | `7f9010f36c0b83a0` | `53bca1fc0b7e811d` |
| Giza-Corner-Points-2v17.json | `4036a83524338350` | `6fedd3e0f20028c7` |
| Petries-Stations.json | `d2694e640fcf76fd` | `f957edca2c329d57` |

## Warnings

- Petrie Stations descriptions carry no Elevation; height is UNKNOWN, not zero.
- GDFS 2016/2018 descriptions use the swapped label 'LongItude' for the latitude-like value; KML coordinate order stays [longitude, latitude, Z].
