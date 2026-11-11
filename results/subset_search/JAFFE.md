# JAFFE: SSC source and subset sensitivity

Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical membership. ACC/NMI and sample SD are percentages; differences and joint discrepancies are percentage points. Both metrics use one configuration and seed set. Native best-of-50 is one minimum-inertia assignment and has no across-run SD. Diagnostic parents do not compete in either eligible pool.

| Pool / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |
|---|---|---:|---:|---:|---:|---|
| Compatible / mean ± sample SD (50 seeds) | JAFFE; n 213; classes 10; features 676; membership family fixed_membership; normalization Y0; target E13; gamma 1000000.0; effective gamma 500000.0; initialization RANDOM | 81.200 ± 1.600 / 84.300 ± 1.600 | 74.751 ± 8.371 / 85.600 ± 4.325 | -6.449 / +1.300; +6.771 / +2.725 | 6.449 / 3.874 | Historical identity documented source; no pixel identity proof; Solver max iter reached; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Compatible / native best of 50 | JAFFE; n 213; classes 10; features 676; membership family fixed_membership; normalization Y0; target E8; gamma 1000000.0; effective gamma 1000000.0; initialization RANDOM | 81.200 ± 1.600 / 84.300 ± 1.600 | 95.305 (single assignment; SD NA) / 94.091 (single assignment; SD NA) | +14.105 / +9.791; NA / NA | 14.105 / 11.948 | Historical identity documented source; no pixel identity proof; Solver max iter reached; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Adapted / mean ± sample SD (50 seeds) | Unavailable | 81.200 ± 1.600 / 84.300 ± 1.600 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |
| Adapted / native best of 50 | Unavailable | 81.200 ± 1.600 / 84.300 ± 1.600 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |

All settings use k=5 and one-start Lloyd rounding with seeds 0–49. Historical-style IRLS uses at most 300 updates, tolerance 1e-6 and epsilon 1e-8. Exact sample/configuration identities and hashes are in `closest_matches.csv` and the public registry; unsuccessful and unevaluated settings remain in coverage.

## Certified-search qualification

Comparable certified subset-search coverage is unavailable, so no certified closest winner is selected. The numerical USPS continuation is a separate saved output; its certificate does not certify a finite-iteration IRLS output, including when current F/W references match.

| Pool / endpoint | Historical complete configurations / canonical | Unique inputs | Certified closest |
|---|---:|---:|---|
| specification compatible / mean sample sd 50 | 30 / 30 | 1 | Unavailable |
| specification compatible / native best of 50 | 30 / 30 | 1 | Unavailable |

Machine-readable qualifications are in `certified_search_status.csv`; separate same-input numerical references and solver tables are in `../submission_refresh/`.
