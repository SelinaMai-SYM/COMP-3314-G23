# ORL: SSC source and subset sensitivity

Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical membership. ACC/NMI and sample SD are percentages; differences and joint discrepancies are percentage points. Both metrics use one configuration and seed set. Native best-of-50 is one minimum-inertia assignment and has no across-run SD. Diagnostic parents do not compete in either eligible pool.

| Pool / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |
|---|---|---:|---:|---:|---:|---|
| Compatible / mean ± sample SD (50 seeds) | ORL_att92; n 400; classes 40; features 1024; membership family fixed_membership; normalization Y0; target E8; gamma 1000.0; effective gamma 1000.0; initialization VANILLA_KMEANSPP | 76.000 ± 1.600 / 88.600 ± 1.500 | 74.630 ± 0.635 / 89.714 ± 0.229 | -1.370 / +1.114; -0.965 / -1.271 | 1.370 / 1.242 | Historical identity documented source; no pixel identity proof; Solver iterate converged uncertified; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Compatible / native best of 50 | ORL_att92; n 400; classes 40; features 1024; membership family fixed_membership; normalization Y0; target E8; gamma 0.001; effective gamma 0.001; initialization VANILLA_KMEANSPP | 76.000 ± 1.600 / 88.600 ± 1.500 | 75.000 (single assignment; SD NA) / 88.605 (single assignment; SD NA) | -1.000 / +0.005; NA / NA | 1.000 / 0.502 | Historical identity documented source; no pixel identity proof; Solver iterate converged uncertified; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Adapted / mean ± sample SD (50 seeds) | Unavailable | 76.000 ± 1.600 / 88.600 ± 1.500 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |
| Adapted / native best of 50 | Unavailable | 76.000 ± 1.600 / 88.600 ± 1.500 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |

All settings use k=5 and one-start Lloyd rounding with seeds 0–49. Historical-style IRLS uses at most 300 updates, tolerance 1e-6 and epsilon 1e-8. Exact sample/configuration identities and hashes are in `closest_matches.csv` and the public registry; unsuccessful and unevaluated settings remain in coverage.

## Certified-search qualification

Comparable certified subset-search coverage is unavailable, so no certified closest winner is selected. The numerical USPS continuation is a separate saved output; its certificate does not certify a finite-iteration IRLS output, including when current F/W references match.

| Pool / endpoint | Historical complete configurations / canonical | Unique inputs | Certified closest |
|---|---:|---:|---|
| specification compatible / mean sample sd 50 | 30 / 30 | 1 | Unavailable |
| specification compatible / native best of 50 | 30 / 30 | 1 | Unavailable |

Machine-readable qualifications are in `certified_search_status.csv`; separate same-input numerical references and solver tables are in `../submission_refresh/`.
