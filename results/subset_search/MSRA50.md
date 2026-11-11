# MSRA50: SSC source and subset sensitivity

Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical membership. ACC/NMI and sample SD are percentages; differences and joint discrepancies are percentage points. Both metrics use one configuration and seed set. Native best-of-50 is one minimum-inertia assignment and has no across-run SD. Diagnostic parents do not compete in either eligible pool.

| Pool / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |
|---|---|---:|---:|---:|---:|---|
| Compatible / mean ± sample SD (50 seeds) | Unavailable | 63.200 ± 1.100 / 72.200 ± 1.400 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |
| Compatible / native best of 50 | Unavailable | 63.200 ± 1.100 / 72.200 ± 1.400 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |
| Adapted / mean ± sample SD (50 seeds) | MSRA25_EBSA_16x16; n 1799; classes 12; features 256; membership family fixed_membership; normalization Y0; target E13; gamma 1000000.0; effective gamma 500000.0; initialization VANILLA_KMEANSPP | 63.200 ± 1.100 / 72.200 ± 1.400 | 49.252 ± 4.377 / 61.505 ± 3.888 | -13.948 / -10.695; +3.277 / +2.488 | 13.948 / 12.322 | Historical identity unverified; Solver max iter reached; Source, resolution or method adaptation; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Adapted / native best of 50 | MSRA25_EBSA_16x16; n 1799; classes 12; features 256; membership family fixed_membership; normalization Y0; target E8; gamma 1000.0; effective gamma 1000.0; initialization RANDOM | 63.200 ± 1.100 / 72.200 ± 1.400 | 56.253 (single assignment; SD NA) / 64.567 (single assignment; SD NA) | -6.947 / -7.633; NA / NA | 7.633 / 7.290 | Historical identity unverified; Solver iterate converged uncertified; Source, resolution or method adaptation; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |

All settings use k=5 and one-start Lloyd rounding with seeds 0–49. Historical-style IRLS uses at most 300 updates, tolerance 1e-6 and epsilon 1e-8. Exact sample/configuration identities and hashes are in `closest_matches.csv` and the public registry; unsuccessful and unevaluated settings remain in coverage.

## Certified-search qualification

Comparable certified subset-search coverage is unavailable, so no certified closest winner is selected. The numerical USPS continuation is a separate saved output; its certificate does not certify a finite-iteration IRLS output, including when current F/W references match.

| Pool / endpoint | Historical complete configurations / canonical | Unique inputs | Certified closest |
|---|---:|---:|---|
| adapted / mean sample sd 50 | 30 / 30 | 1 | Unavailable |
| adapted / native best of 50 | 30 / 30 | 1 | Unavailable |

Machine-readable qualifications are in `certified_search_status.csv`; separate same-input numerical references and solver tables are in `../submission_refresh/`.
