# P0 YaleB root cause

This file is generated from `results/extension_research/P0_yaleb_diagnostics.csv` and the correctness checks in `results/extension_research/P0_correctness_checks.json`. It does not copy historical ACC/NMI into that CSV.

## Implementation check

Conclusion: `NO CONFIRMED IMPLEMENTATION BUG`.

Checked, without using the checks to retune the method: a global pixel permutation leaves Euclidean kNN unchanged; a global brightness scale cancels when delta^2 is the median of squared kNN distances and does not cancel when delta^2 is held numerically fixed; dense kNN matches SciPy distances; a three-point Gaussian kernel matches the hand value; union and mutual symmetrization do what those rules say; the normalized Laplacian and its smallest eigenvectors match the dense formula; ACC/NMI and Lloyd K-means run on a toy; n=6 E8 matches an independent CLARABEL solve of the ordered-pair objective. `SSC_method/` was not modified.

Best orientation of dengcai32 against cropped2414 is `transpose` with median matched L2 1.9222 and fraction of pairs with max-abs <= 1e-8 equal to 0.000000. The two 2414 x 1024 matrices are not the same pixels. Array SHA-256: cropped2414 `2d84a8955098837ba04121bd86652f3495c512f15c0592eb1a1956f23331b75b`, dengcai32 `8f04c47e3c4de85be09c40cce1d02716d46a1de91e884d675a755be77d8631f0`.

Chang et al. Table 1, historical published context only, not a measurement in this CSV: YaleB SC 34.8% and SSC 49.8%. A diagnostic ACC above D0 is `NON_PAPER_DIAGNOSTIC` and is not adopted as the original protocol.

## D0–D6

Each non-control row changes one pre-specified factor, or a combination named before the run. SC is K-means on F. SSC is E8, gamma=1, G0=F, K-means on G. Seeds 0..49, n_init=1. Sample standard deviation uses ddof=1.

| Version | ID | Factor | Tag | Status | SC ACC | SSC ACC | SC NMI | SSC NMI | W edges | W components | Iters | Converged |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cropped2414 | D0 | control_protocol | PAPER_CONSISTENT_UNVERIFIED | NONCONVERGED | 0.1834 ± 0.0128 | 0.1763 ± 0.0119 | 0.2690 ± 0.0067 | 0.2618 ± 0.0090 | 7957 | 13 | 300 | False |
| cropped2414 | D1 | bandwidth_only | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.1834 ± 0.0123 | 0.1756 ± 0.0130 | 0.2693 ± 0.0064 | 0.2616 ± 0.0091 | 7957 | 13 | 300 | False |
| cropped2414 | D2 | symmetrization_only | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.2254 ± 0.0143 | 0.2262 ± 0.0140 | 0.3538 ± 0.0088 | 0.3541 ± 0.0097 | 4331 | 203 | 300 | False |
| cropped2414 | D3 | row_normalization_only | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.2196 ± 0.0154 | 0.2218 ± 0.0151 | 0.3090 ± 0.0112 | 0.3090 ± 0.0103 | 8385 | 2 | 300 | False |
| cropped2414 | D4 | kmeans_init_only | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.2178 ± 0.0045 | 0.2155 ± 0.0047 | 0.2773 ± 0.0058 | 0.2749 ± 0.0056 | 7957 | 13 | 300 | False |
| cropped2414 | D5 | combo_mutual_and_row_normalization | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.2550 ± 0.0156 | 0.2559 ± 0.0150 | 0.3832 ± 0.0112 | 0.3842 ± 0.0108 | 3955 | 456 | 300 | False |
| cropped2414 | D6 | combo_mean_bandwidth_and_kmeanspp | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.2170 ± 0.0042 | 0.2137 ± 0.0051 | 0.2758 ± 0.0067 | 0.2733 ± 0.0056 | 7957 | 13 | 300 | False |
| dengcai32 | D0 | control_protocol | PAPER_CONSISTENT_UNVERIFIED | NONCONVERGED | 0.2016 ± 0.0124 | 0.1956 ± 0.0128 | 0.2966 ± 0.0081 | 0.2921 ± 0.0089 | 8060 | 13 | 300 | False |
| dengcai32 | D1 | bandwidth_only | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.2016 ± 0.0119 | 0.1935 ± 0.0125 | 0.2966 ± 0.0075 | 0.2902 ± 0.0091 | 8058 | 13 | 300 | False |
| dengcai32 | D2 | symmetrization_only | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.2568 ± 0.0133 | 0.2593 ± 0.0149 | 0.3967 ± 0.0109 | 0.3995 ± 0.0124 | 4342 | 220 | 300 | False |
| dengcai32 | D3 | row_normalization_only | NON_PAPER_DIAGNOSTIC | CONVERGED | 0.2655 ± 0.0156 | 0.2659 ± 0.0167 | 0.3741 ± 0.0095 | 0.3740 ± 0.0092 | 8456 | 1 | 289 | True |
| dengcai32 | D4 | kmeans_init_only | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.2536 ± 0.0048 | 0.2543 ± 0.0043 | 0.3128 ± 0.0056 | 0.3142 ± 0.0060 | 8060 | 13 | 300 | False |
| dengcai32 | D5 | combo_mutual_and_row_normalization | NON_PAPER_DIAGNOSTIC | CONVERGED | 0.3081 ± 0.0174 | 0.3060 ± 0.0182 | 0.4484 ± 0.0128 | 0.4467 ± 0.0124 | 3954 | 448 | 261 | True |
| dengcai32 | D6 | combo_mean_bandwidth_and_kmeanspp | NON_PAPER_DIAGNOSTIC | NONCONVERGED | 0.2531 ± 0.0052 | 0.2544 ± 0.0048 | 0.3120 ± 0.0053 | 0.3150 ± 0.0061 | 8058 | 13 | 300 | False |

## What the control supports

On the locked control, cropped2414 SC ACC is 0.1834 and SSC ACC is 0.1763. dengcai32 SC ACC is 0.2016 and SSC ACC is 0.1956. Both are far below the published 0.348 / 0.498 table entries. Switching the pixel matrix does not close that gap. The shrinkage step is not the first place the gap appears: K-means on F is already low.

Every completed D0–D6 cell, including the non-paper diagnostics, stays below the published YaleB SC and SSC table values. Those higher diagnostic numbers are still not the original protocol.

## What remains unresolved

The paper does not state delta, union versus mutual, the resize kernel, the eigenvector sign convention, or whether the solver was printed Equation (13) or the Equation (8) stationary system. This round keeps E8 as the control and does not pick a diagnostic by test ACC.
