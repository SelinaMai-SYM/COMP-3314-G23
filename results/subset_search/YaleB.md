# YaleB: SSC source and subset sensitivity

Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical membership. ACC/NMI and sample SD are percentages; differences and joint discrepancies are percentage points. Both metrics use one configuration and seed set. Native best-of-50 is one minimum-inertia assignment and has no across-run SD. Diagnostic parents do not compete in either eligible pool.

| Pool / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |
|---|---|---:|---:|---:|---:|---|
| Compatible / mean ± sample SD (50 seeds) | YaleB_cropped2414_nearest; n 2414; classes 38; features 1024; membership family YaleB_source_preparation; normalization Y3; target E13; gamma 1000.0; effective gamma 500.0; initialization SKLEARN_GREEDY_KMEANSPP | 49.800 ± 1.600 / 46.800 ± 1.300 | 44.239 ± 0.816 / 52.608 ± 0.364 | -5.561 / +5.808; -0.784 / -0.936 | 5.808 / 5.685 | Historical identity documented source; no pixel identity proof; Solver max iter reached; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Compatible / native best of 50 | YaleB_cropped2414_nearest; n 2414; classes 38; features 1024; membership family YaleB_source_preparation; normalization Y3; target E13; gamma 1000.0; effective gamma 500.0; initialization VANILLA_KMEANSPP | 49.800 ± 1.600 / 46.800 ± 1.300 | 44.739 (single assignment; SD NA) / 52.283 (single assignment; SD NA) | -5.061 / +5.483; NA / NA | 5.483 / 5.272 | Historical identity documented source; no pixel identity proof; Solver max iter reached; Source kind original candidate source; Finite historical-style IRLS; no transferred numerical-audit certificate |
| Adapted / mean ± sample SD (50 seeds) | Unavailable | 49.800 ± 1.600 / 46.800 ± 1.300 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |
| Adapted / native best of 50 | Unavailable | 49.800 ± 1.600 / 46.800 ± 1.300 | NA / NA | NA / NA; NA / NA | NA / NA | No complete eligible configuration |

All settings use k=5 and one-start Lloyd rounding with seeds 0–49. Historical-style IRLS uses at most 300 updates, tolerance 1e-6 and epsilon 1e-8. Exact sample/configuration identities and hashes are in `closest_matches.csv` and the public registry; unsuccessful and unevaluated settings remain in coverage.

## Certified-search qualification

Comparable certified subset-search coverage is unavailable, so no certified closest winner is selected. The numerical USPS continuation is a separate saved output; its certificate does not certify a finite-iteration IRLS output, including when current F/W references match.

| Pool / endpoint | Historical complete configurations / canonical | Unique inputs | Certified closest |
|---|---:|---:|---|
| specification compatible / mean sample sd 50 | 480 / 480 | 16 | Unavailable |
| specification compatible / native best of 50 | 480 / 480 | 16 | Unavailable |

Machine-readable qualifications are in `certified_search_status.csv`; separate same-input numerical references and solver tables are in `../submission_refresh/`.
