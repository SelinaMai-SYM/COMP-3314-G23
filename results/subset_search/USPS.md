# USPS: SSC source and subset sensitivity

Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical membership. ACC/NMI and sample SD are percentages; differences and joint discrepancies are percentage points. Both metrics use one configuration and seed set. Native best-of-50 is one minimum-inertia assignment and has no across-run SD. Diagnostic parents do not compete in either eligible pool.

| Pool / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |
|---|---|---:|---:|---:|---:|---|
| Compatible / mean ± sample SD (50 seeds) | USPS; n 9298; classes 10; features 256; membership family fixed_membership; normalization Y0; target E13; gamma 1.0; effective gamma 0.5; initialization SKLEARN_GREEDY_KMEANSPP | 75.500 ± 1.900 / 79.800 ± 1.600 | 66.263 ± 1.702 / 80.855 ± 1.199 | -9.237 / +1.055; -0.198 / -0.401 | 9.237 / 5.146 | Historical identity documented source; no pixel identity proof; Solver iterate converged uncertified; Source kind per configuration completion; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Compatible / native best of 50 | USPS; n 9298; classes 10; features 256; membership family fixed_membership; normalization Y0; target E8; gamma 1.0; effective gamma 1.0; initialization VANILLA_KMEANSPP | 75.500 ± 1.900 / 79.800 ± 1.600 | 65.627 (single assignment; SD NA) / 81.168 (single assignment; SD NA) | -9.873 / +1.368; NA / NA | 9.873 / 5.620 | Historical identity documented source; no pixel identity proof; Solver max iter reached; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Adapted / mean ± sample SD (50 seeds) | Unavailable | 75.500 ± 1.900 / 79.800 ± 1.600 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |
| Adapted / native best of 50 | Unavailable | 75.500 ± 1.900 / 79.800 ± 1.600 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |

All settings use k=5 and one-start Lloyd rounding with seeds 0–49. Historical-style IRLS uses at most 300 updates, tolerance 1e-6 and epsilon 1e-8. Exact sample/configuration identities and hashes are in `closest_matches.csv` and the public registry; unsuccessful and unevaluated settings remain in coverage.

## Certified-search qualification

Comparable certified subset-search coverage is unavailable, so no certified closest winner is selected. The numerical USPS continuation is a separate saved output; its certificate does not certify a finite-iteration IRLS output, including when current F/W references match.

| Pool / endpoint | Historical complete configurations / canonical | Unique inputs | Certified closest |
|---|---:|---:|---|
| specification compatible / mean sample sd 50 | 18 / 18 | 1 | Unavailable |
| specification compatible / native best of 50 | 18 / 18 | 1 | Unavailable |

Machine-readable qualifications are in `certified_search_status.csv`; separate same-input numerical references and solver tables are in `../submission_refresh/`.
