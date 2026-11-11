# AR: SSC source and subset sensitivity

Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical membership. ACC/NMI and sample SD are percentages; differences and joint discrepancies are percentage points. Both metrics use one configuration and seed set. Native best-of-50 is one minimum-inertia assignment and has no across-run SD. Diagnostic parents do not compete in either eligible pool.

| Pool / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |
|---|---|---:|---:|---:|---:|---|
| Compatible / mean ± sample SD (50 seeds) | AR_LZUFE1680; n 840; classes 120; features 1024; membership family AR_common_mask; normalization Y0; target E13; gamma 1000.0; effective gamma 500.0; initialization SKLEARN_GREEDY_KMEANSPP | 51.300 ± 1.500 / 73.200 ± 1.400 | 51.210 ± 2.005 / 72.940 ± 1.047 | -0.090 / -0.260; +0.505 / -0.353 | 0.260 / 0.175 | Historical identity unverified; Solver max iter reached; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Compatible / native best of 50 | AR_LZUFE1680; n 840; classes 120; features 1024; membership family AR_common_mask; normalization Y0; target E8; gamma 1.0; effective gamma 1.0; initialization RANDOM | 51.300 ± 1.500 / 73.200 ± 1.400 | 51.190 (single assignment; SD NA) / 73.338 (single assignment; SD NA) | -0.110 / +0.138; NA / NA | 0.138 / 0.124 | Historical identity unverified; Solver max iter reached; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Adapted / mean ± sample SD (50 seeds) | Unavailable | 51.300 ± 1.500 / 73.200 ± 1.400 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |
| Adapted / native best of 50 | Unavailable | 51.300 ± 1.500 / 73.200 ± 1.400 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |

All settings use k=5 and one-start Lloyd rounding with seeds 0–49. Historical-style IRLS uses at most 300 updates, tolerance 1e-6 and epsilon 1e-8. Exact sample/configuration identities and hashes are in `closest_matches.csv` and the public registry; unsuccessful and unevaluated settings remain in coverage.

## Certified-search qualification

Comparable certified subset-search coverage is unavailable, so no certified closest winner is selected. The numerical USPS continuation is a separate saved output; its certificate does not certify a finite-iteration IRLS output, including when current F/W references match.

| Pool / endpoint | Historical complete configurations / canonical | Unique inputs | Certified closest |
|---|---:|---:|---|
| specification compatible / mean sample sd 50 | 41640 / 41520 | 1384 | Unavailable |
| specification compatible / native best of 50 | 41640 / 41520 | 1384 | Unavailable |

Machine-readable qualifications are in `certified_search_status.csv`; separate same-input numerical references and solver tables are in `../submission_refresh/`.
