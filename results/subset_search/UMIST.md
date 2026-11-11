# UMIST: SSC source and subset sensitivity

Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical membership. ACC/NMI and sample SD are percentages; differences and joint discrepancies are percentage points. Both metrics use one configuration and seed set. Native best-of-50 is one minimum-inertia assignment and has no across-run SD. Diagnostic parents do not compete in either eligible pool.

| Pool / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |
|---|---|---:|---:|---:|---:|---|
| Compatible / mean ± sample SD (50 seeds) | UMIST_LZUFE574; n 564; classes 20; features 10304; membership family UMIST_LZUFE574_stratified564; normalization Y0; target E13; gamma 1000.0; effective gamma 500.0; initialization SKLEARN_GREEDY_KMEANSPP | 71.100 ± 1.800 / 84.100 ± 1.500 | 69.968 ± 2.271 / 85.165 ± 1.000 | -1.132 / +1.065; +0.471 / -0.500 | 1.132 / 1.098 | Historical identity unverified; Solver max iter reached; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Compatible / native best of 50 | UMIST_LZUFE574; n 564; classes 20; features 10304; membership family UMIST_LZUFE574_stratified564; normalization Y0; target E8; gamma 0.001; effective gamma 0.001; initialization RANDOM | 71.100 ± 1.800 / 84.100 ± 1.500 | 70.922 (single assignment; SD NA) / 84.364 (single assignment; SD NA) | -0.178 / +0.264; NA / NA | 0.264 / 0.221 | Historical identity unverified; Solver iterate converged uncertified; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Adapted / mean ± sample SD (50 seeds) | Unavailable | 71.100 ± 1.800 / 84.100 ± 1.500 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |
| Adapted / native best of 50 | Unavailable | 71.100 ± 1.800 / 84.100 ± 1.500 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |

All settings use k=5 and one-start Lloyd rounding with seeds 0–49. Historical-style IRLS uses at most 300 updates, tolerance 1e-6 and epsilon 1e-8. Exact sample/configuration identities and hashes are in `closest_matches.csv` and the public registry; unsuccessful and unevaluated settings remain in coverage.

## Certified-search qualification

Comparable certified subset-search coverage is unavailable, so no certified closest winner is selected. The numerical USPS continuation is a separate saved output; its certificate does not certify a finite-iteration IRLS output, including when current F/W references match.

| Pool / endpoint | Historical complete configurations / canonical | Unique inputs | Certified closest |
|---|---:|---:|---|
| specification compatible / mean sample sd 50 | 31980 / 28980 | 966 | Unavailable |
| specification compatible / native best of 50 | 31980 / 28980 | 966 | Unavailable |

Machine-readable qualifications are in `certified_search_status.csv`; separate same-input numerical references and solver tables are in `../submission_refresh/`.
