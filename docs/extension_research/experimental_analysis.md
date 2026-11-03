# Experimental analysis

All ACC/NMI values below are read from `results/extension_research/extension_matrix.csv` and the matching `runs/extension_research/full/*/metrics.json`. Historical `runs/strict_paper` files are cited only as a cross-check. They were not copied into the new CSV. Sample standard deviations use ddof=1 over K-means seeds on one fixed representation. A blank standard deviation is one assignment (`COMPLETE_SINGLE_ASSIGNMENT`).

The matrix has 492 unique rows and 0 duplicate keys. Counts: `CONVERGED` 309, `NONCONVERGED` 164, `COMPLETE_SINGLE_ASSIGNMENT` 14, `FAILED` 3, `BLOCKED_DATA` 1, `BLOCKED` 1. Missing shrink, E07, and auxiliary cells: none. Pilot rows in `pilot_matrix.csv` use seeds `{0,1,2}` and are not the numbers in this file.

## Control at gamma = 1

SC is K-means on F. SSC is K-means on G. Both use the same seed list unless the row says otherwise.

| Dataset | Version | Eligibility | Status | Iters | SC ACC | SSC ACC | SC NMI | SSC NMI | W edges | W components |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORL | att92 | PAPER_RECONSTRUCTION | NONCONVERGED | 300 | 0.5618 ± 0.0419 | 0.57265 ± 0.0380 | 0.8047 | 0.8113 | 1217 | 16 |
| JAFFE | zenodo | VERIFIED_SOURCE | NONCONVERGED | 300 | 0.6853 ± 0.1115 | 0.6843 ± 0.1108 | 0.8302 | 0.8305 | 655 | 9 |
| YaleB | cropped2414 | PRIMARY_YALEB_VERSION | NONCONVERGED | 300 | 0.1834 ± 0.0128 | 0.1763 ± 0.0119 | 0.2690 | 0.2618 | 7957 | 13 |
| YaleB | dengcai32 | alternate matrix | NONCONVERGED | 300 | 0.2016 ± 0.0124 | 0.1955 ± 0.0130 | 0.2966 | 0.2920 | 8060 | 13 |
| USPS | libsvm | VERIFIED_SOURCE | CONVERGED | 298 | 0.6174 ± 0.0809 | 0.6170 ± 0.0809 | 0.7494 | 0.7523 | 30437 | 1 |
| BinAlpha | CANDIDATE_BIN_ALPHA | NON_EXACT_DATASET | NONCONVERGED | 300 | 0.4401 ± 0.0255 | 0.4162 ± 0.0275 | 0.5740 | 0.5641 | 2523 | 1 |
| UMIST | precropped575 | NON_EXACT_DATASET | NONCONVERGED | 300 | 0.5613 ± 0.0517 | 0.5472 ± 0.0504 | 0.7677 | 0.7529 | 1761 | 11 |

Exact means are in the CSV. ORL SSC ACC is 0.57265. JAFFE SSC ACC is 0.6843192488. YaleB cropped SSC ACC is 0.1762551781. dengcai32 SSC ACC is 0.1955343828. USPS SSC ACC is 0.6169821467.

Cross-check against the committed strict-paper metrics, same protocol: ORL 0.57265, JAFFE 0.6843192488, and USPS 0.6169821467 match those files. YaleB cropped in `runs/strict_paper/20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff/metrics.json` is 0.1762220381. The fresh cell is 0.1762551781. The fourth digit moved. The file was not overwritten, and the new CSV keeps the fresh value. USPS at gamma `1000.0` is 0.7386126049 in this CSV. The earlier note of 0.7369 is the older run. USPS at gamma `1000000.0` is 0.3880640998, in line with the older grid point that collapses USPS.

Paired bootstrap of mean ACC(G) − ACC(F), 2000 resamples, seed 0, fixed representations: ORL +0.0109 [+0.0027, +0.0181]. YaleB cropped −0.0071 [−0.0096, −0.0049]. dengcai32 −0.0061 [−0.0080, −0.0040]. BinAlpha −0.0239 [−0.0319, −0.0162]. UMIST −0.0141 [−0.0258, −0.0028]. JAFFE and USPS intervals for the control include 0. These intervals cover K-means noise on one G. They do not cover a new draw of images.

## Extensions at gamma = 1

Delta is SSC ACC minus the E8 control SSC ACC on the same version. `d(G−F)` is SSC ACC minus that method's own SC ACC. Full seeds and NMI are in `primary_matrix.md` and `ablation.md`.

### ORL att92

| Method | Status | SSC ACC | NMI | Delta vs E8 | G−F |
| --- | --- | --- | --- | --- | --- |
| E01 | NONCONVERGED | 0.57335 | 0.8118 | +0.0007 | +0.0116 |
| E02 | NONCONVERGED | 0.56455 | 0.8078 | −0.0081 | +0.0028 |
| E03-A | CONVERGED | 0.58845 | 0.8196 | +0.0158 | +0.0040 |
| E03-W | CONVERGED | 0.5606 | 0.8082 | −0.0121 | −0.0012 |
| E03-AW | CONVERGED | 0.5779 | 0.8173 | +0.0052 | −0.0066 |
| E04-degree | NONCONVERGED | 0.56265 | 0.8080 | −0.0100 | +0.0009 |
| E04-total | CONVERGED | 0.5618 | 0.8047 | −0.0109 | 0 |
| E05-fuse | NONCONVERGED | 0.57915 | 0.8155 | +0.0065 | +0.0174 |
| E05-bilateral | NONCONVERGED | 0.57045 | 0.8081 | −0.0022 | +0.0087 |
| E06 | NONCONVERGED | 0.5792 | 0.8144 | +0.0066 | +0.0174 |
| E08 | NONCONVERGED | 0.5654 | 0.8087 | −0.0072 | +0.0036 |
| E09 | NONCONVERGED | 0.56115 | 0.8079 | −0.0115 | −0.0006 |
| mutual-kNN E8 | NONCONVERGED | 0.5729 | 0.8091 | +0.0002 | +0.0111 |

E03-A's own SC ACC is about 0.5845, against the control SC of 0.5618. The paired G−F interval for E03-A includes 0. The higher SSC number is the local-scale embedding. E04-total has relative move `1.09e-9` and reproduces SC. E05-fuse has 1633 edges and 2 components, against the control's 1217 edges and 16 components. Its G−F interval is +0.0173 [+0.0093, +0.0243], and its interval against E8 is +0.0065 [+0.0011, +0.0122]. E06 matches that G−F gain; its interval against E8 includes 0.

### JAFFE zenodo

Control SSC ACC 0.6843192488, NMI 0.8305. E01 0.6892, E02 0.6885, E03-A 0.7167, E03-W 0.6642, E03-AW 0.7029, E04-degree 0.6781, E04-total 0.6853, E05-fuse 0.6818, E05-bilateral 0.6795, E06 0.6857, E08 0.6929, E09 0.6596. Auxiliary mutual-kNN 0.6836619718, the same value as `runs/round2/20261021_161924__ROUND2__JAFFE__EXT_JAFFE_MUTUAL_KNN__45fd1c1f`.

Intervals against E8 that exclude 0: E03-A +0.0324 [+0.0075, +0.0579], E03-W −0.0201 [−0.0341, −0.0069], E09 −0.0247 [−0.0402, −0.0102], mutual-kNN −0.0007 [−0.0016, −0.0000]. E03-A's G−F interval includes 0, and its SC is already 0.7160. E03-W and E09 have G−F intervals below 0. No extension has a G−F interval above 0 on JAFFE.

### YaleB

These cells are the same E8 family as D0. They are not a recovery of Table 1. Published context remains SC 34.8% and SSC 49.8%. Every gamma=1 extension on both matrices is below both of those figures. The highest cropped graph-extension SSC ACC is E03-A at 0.1879. The highest cropped cell of any kind is E07 k-means++ at 0.2155, which changes the initializer and is still below 0.348. dengcai32 E03-A is 0.2077. dengcai32 E07 k-means++ is 0.2543. Higher diagnostic ACC from D2–D6 remains `NON_PAPER_DIAGNOSTIC` and is still below 0.348 / 0.498. The highest of those, dengcai32 D5, is SC 0.3081 and SSC 0.3060.

On cropped2414, intervals against E8 that sit above 0 are a few thousandths to about one point: E02 +0.0031, E03-A +0.0116, E04-degree +0.0063, E04-total +0.0071, E05-fuse +0.0065, E05-bilateral +0.0053, E08 +0.0038, mutual-kNN +0.0029. E03-W and E09 sit below 0. Every G−F interval that excludes 0 on cropped2414 sits below 0, including E03-A and E05-fuse. E04-total's relative move is `4.5e-10`, so its SSC ACC equals SC ACC 0.1834. The positive delta against E8 is the removal of a shrinkage step that lowered ACC.

dengcai32 repeats that pattern. E03-A +0.0122 and E03-AW +0.0088 against E8 come with G−F intervals below 0. E04-total again equals SC (move `5.0e-10`). E05-fuse reaches one connected component (13571 edges) and +0.0062 against E8, with a G−F interval that includes 0. E05-bilateral has 365 components.

### USPS libsvm

Control SSC ACC 0.6169821467, NMI 0.7523, CONVERGED, one component, 30437 edges. E01 0.6147, E02 0.6170, E03-A 0.6531, E03-W 0.6094, E03-AW 0.6434, E04-degree 0.6189, E04-total 0.6174, E05-fuse 0.6393, E05-bilateral 0.6165, E06 0.6141, E08 0.6172, E09 0.6136, mutual-kNN 0.6147.

E03-A's SC is 0.6605. Its G−F interval is not above 0. E03-AW's G−F interval is −0.0171 [−0.0327, −0.0041]. E05-fuse is the graph change whose G−F interval is above 0: +0.0219 [+0.0085, +0.0350], and against E8 +0.0223 [+0.0086, +0.0357]. It keeps one component and 62125 edges. E05-bilateral has 6546 components and ACC 0.6165. E06 has 4484 components and ACC 0.6141.

Three USPS cells at gamma `1000000.0` are `FAILED`, notes `TimeoutError: fit exceeded 180s`: E06, E08, and E09. Their ACC fields are blank. They are not zeros and they are not the historical 0.388 control value. The control itself at that gamma is `NONCONVERGED` with SSC ACC 0.3880640998.

### BinAlpha and UMIST

Both versions are `NON_EXACT_DATASET`. Absolute ACC is not a paper-table comparison.

BinAlpha control SSC ACC 0.4162 against SC 0.4401. G−F is −0.0239 [−0.0319, −0.0162]. Methods with an interval against E8 above 0: E02 +0.0067, E03-A +0.0078, E04-degree +0.0175, E04-total +0.0239, E05-fuse +0.0316, E05-bilateral +0.0159, mutual-kNN +0.0085. E04-total equals SC (move `9e-11`). E05-fuse is the one whose G−F interval is also above 0: +0.0077 [+0.0009, +0.0148]. E03-W, E03-AW, E06, and E09 have intervals against E8 below 0.

UMIST control SSC ACC 0.5472 against SC 0.5613. G−F is −0.0141 [−0.0258, −0.0028]. E04-total again equals SC, delta against E8 +0.0141 [+0.0028, +0.0258], relative move `1.8e-10`. E01, E03-W, E06, and E09 have intervals against E8 below 0. No UMIST extension has a G−F interval above 0.

## E07, same F and same G

E07 does not build a new representation. Random Lloyd reproduces the control. k-means++ changes the level of both SC and SSC. Inertia-best and consensus are one assignment each, so they have no seed standard deviation.

| Dataset | Version | Random SSC | k-means++ SC | k-means++ SSC | Inertia-best SSC | Consensus SSC |
| --- | --- | --- | --- | --- | --- | --- |
| ORL | att92 | 0.57265 | 0.78325 | 0.7839 | 0.6225 | 0.6525 |
| JAFFE | zenodo | 0.6843 | 0.9531 | 0.9510 | 0.9531 | 0.9531 |
| YaleB | cropped2414 | 0.1763 | 0.2178 | 0.2155 | 0.1972 | 0.1819 |
| YaleB | dengcai32 | 0.1955 | 0.2536 | 0.2543 | 0.2138 | 0.2071 |
| USPS | libsvm | 0.6170 | 0.6560 | 0.6579 | 0.6563 | 0.6565 |
| BinAlpha | CANDIDATE_BIN_ALPHA | 0.4162 | 0.4727 | 0.4714 | 0.4590 | 0.4679 |
| UMIST | precropped575 | 0.5472 | 0.6149 | 0.6180 | 0.5965 | 0.5843 |

On ORL the k-means++ G−F gap is +0.00065, and the interval of k-means++ against random-Lloyd E8 is +0.2112 [+0.1999, +0.2228]. The same split holds on JAFFE (+0.2667 against E8, G−F slightly negative). YaleB k-means++ raises the level and leaves G at or below F. On UMIST, the single inertia-best and consensus assignments score higher on F (0.6748 and 0.6783) than on G (0.5965 and 0.5843).

## Gamma grid

The operating point is gamma=1. Other values are recorded. Selecting the maximum would be the oracle file, label `ORACLE_UPPER_BOUND`.

Control SSC ACC by gamma:

| Dataset | Version | 1e-6 | 1e-3 | 1 | 1e3 | 1e6 |
| --- | --- | --- | --- | --- | --- | --- |
| ORL | att92 | 0.5618 | 0.5618 | 0.57265 | 0.55815 | 0.51085 |
| JAFFE | zenodo | 0.6853 | 0.6853 | 0.6843 | 0.7222 | 0.7189 |
| YaleB | cropped2414 | 0.1834 | 0.1834 | 0.1763 | 0.1698 | 0.1282 |
| YaleB | dengcai32 | 0.2016 | 0.2016 | 0.1955 | 0.2009 | 0.1507 |
| USPS | libsvm | 0.6174 | 0.6174 | 0.6170 | 0.7386 | 0.3881 |
| BinAlpha | CANDIDATE_BIN_ALPHA | 0.4401 | 0.4401 | 0.4162 | 0.4295 | 0.4298 |
| UMIST | precropped575 | 0.5613 | 0.5613 | 0.5472 | 0.5212 | 0.4800 |

At 1e-6 and 1e-3 the control relative move is numerically zero and ACC equals SC. USPS at 1e3 is higher than at gamma=1 and is the grid point already discussed in `docs/final_round/scientific_findings.md`. It was not chosen by test ACC. USPS at 1e6 falls to 0.3881. YaleB declines across the grid on both matrices.

## Fragmentation, optimizer, combinations

- E05-bilateral deletes edges. Cropped YaleB goes from 13 components to 379. USPS goes from 1 component to 6546. ACC stays near the control or falls. The bilateral rule does not repair YaleB.
- E05-fuse adds pixel-space support. ORL goes to 2 components, both YaleB matrices go to 1, USPS stays at 1 with about twice the edges. This is the only graph edit whose G−F interval is above 0 on more than one dataset (ORL, USPS, BinAlpha). The ORL gain against E8 is about 0.7 points. The USPS gain is about 2.2 points. YaleB's gain against E8 is a few thousandths and the G−F interval still includes 0 or sits below it.
- E06 refits W three times. On ORL its G−F interval matches the fuse gain and its interval against E8 includes 0. On USPS it fragments W to 4484 components and ACC falls to 0.6141. The three USPS gamma=1e6 alternations, plus E08 and E09 at that gamma, hit the 180s SuperLU timeout and are `FAILED`.
- E08 (recurrence plus reliability) tracks E02 and does not beat the better of E01 and E02 by a stable margin. On ORL its interval against E8 is −0.0073 [−0.0135, −0.0005].
- E09 (recurrence on local-scale W) tracks E03-W. Intervals against E8 are below 0 on ORL, JAFFE, both YaleB matrices, BinAlpha, and UMIST.

## What the intervals do not say

A 95% interval that excludes 0 is still an interval over 50 K-means seeds on one embedding. E07 inertia-best and consensus have one assignment, so they are outside that bootstrap. `NONCONVERGED` means the relative step had not met `tol=1e-6` at iteration 300. The scored G is the returned iterate. Different objective names are different functions. BinAlpha and UMIST are non-exact versions. dengcai32 is the same benchmark counted twice as a pixel check, not a second independent dataset.
