# BinAlpha: SSC source and subset sensitivity

Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical membership. ACC/NMI and sample SD are percentages; differences and joint discrepancies are percentage points. Both metrics use one configuration and seed set. Native best-of-50 is one minimum-inertia assignment and has no across-run SD. Diagnostic parents do not compete in either eligible pool.

| Pool / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |
|---|---|---:|---:|---:|---:|---|
| Compatible / mean ± sample SD (50 seeds) | BinAlpha_parent36; n 780; classes 26; features 320; membership family BinAlpha_random30; normalization Y0; target E8; gamma 1000000.0; effective gamma 1000000.0; initialization RANDOM | 49.400 ± 1.300 / 64.100 ± 1.400 | 49.544 ± 2.707 / 63.459 ± 1.038 | +0.144 / -0.641; +1.407 / -0.362 | 0.641 / 0.392 | Historical identity unverified; Solver iterate converged uncertified; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Compatible / native best of 50 | BinAlpha_parent36; n 780; classes 26; features 320; membership family BinAlpha_random30; normalization Y0; target E13; gamma 1000.0; effective gamma 500.0; initialization VANILLA_KMEANSPP | 49.400 ± 1.300 / 64.100 ± 1.400 | 49.359 (single assignment; SD NA) / 64.112 (single assignment; SD NA) | -0.041 / +0.012; NA / NA | 0.041 / 0.026 | Historical identity unverified; Solver iterate converged uncertified; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Adapted / mean ± sample SD (50 seeds) | BinAlpha_parent36; n 780; classes 26; features 320; membership family BinAlpha_order_sensitivity; normalization Y0; target E8; gamma 1.0; effective gamma 1.0; initialization SKLEARN_GREEDY_KMEANSPP | 49.400 ± 1.300 / 64.100 ± 1.400 | 50.131 ± 1.387 / 61.943 ± 1.068 | +0.731 / -2.157; +0.087 / -0.332 | 2.157 / 1.444 | Historical identity unverified; Solver max iter reached; Source, resolution or method adaptation; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Adapted / native best of 50 | BinAlpha_parent36; n 780; classes 26; features 320; membership family BinAlpha_order_sensitivity; normalization Y0; target E8; gamma 1000.0; effective gamma 1000.0; initialization SKLEARN_GREEDY_KMEANSPP | 49.400 ± 1.300 / 64.100 ± 1.400 | 48.333 (single assignment; SD NA) / 62.966 (single assignment; SD NA) | -1.067 / -1.134; NA / NA | 1.134 / 1.100 | Historical identity unverified; Solver iterate converged uncertified; Source, resolution or method adaptation; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |

All settings use k=5 and one-start Lloyd rounding with seeds 0–49. Historical-style IRLS uses at most 300 updates, tolerance 1e-6 and epsilon 1e-8. Exact sample/configuration identities and hashes are in `closest_matches.csv` and the public registry; unsuccessful and unevaluated settings remain in coverage.

## Certified-search qualification

Comparable certified subset-search coverage is unavailable, so no certified closest winner is selected. The numerical USPS continuation is a separate saved output; its certificate does not certify a finite-iteration IRLS output, including when current F/W references match.

| Pool / endpoint | Historical complete configurations / canonical | Unique inputs | Certified closest |
|---|---:|---:|---|
| adapted / mean sample sd 50 | 60 / 60 | 2 | Unavailable |
| adapted / native best of 50 | 60 / 60 | 2 | Unavailable |
| specification compatible / mean sample sd 50 | 3000 / 3000 | 100 | Unavailable |
| specification compatible / native best of 50 | 3000 / 3000 | 100 | Unavailable |

Machine-readable qualifications are in `certified_search_status.csv`; separate same-input numerical references and solver tables are in `../submission_refresh/`.
