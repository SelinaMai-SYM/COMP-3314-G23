# Experiment protocol

Prespecified before the extension measurements. Grids were not expanded after any pilot accuracy.

## Frozen baseline

`REPRODUCTION_FROZEN_V3` keeps Y0, E8 and E13, LLC Procrustes, LDA-Kmeans, and SLPS. The 72-cell table is reaggregated from `results/v3_reproduction/all_configurations.csv`. Primary SSC is gamma = 1 with RANDOM initialization and the per-run mean. Gamma = 1000 stays in the sensitivity table.

## Extension data

Primary tracks: ORL, JAFFE, USPS, and both YaleB versions at Y0. YaleB Y3 is a separate track and is never compared with an SSC run that used Y0. Supplemental BinAlpha candidate and UMIST 575 are loaded when present and are not historical cells. Two YaleB versions count as one benchmark in the dataset-level summary.

## Shared solver and clustering

`F` is the frozen spectral embedding (`k = 5`, union kNN, median bandwidth, symmetric normalized Laplacian). `W` is the kNN graph on that `F`, except where an extension explicitly replaces `W`. SSC comparisons use E8. K-means is greedy k-means++, seeds 0..49, `n_init = 1`, Lloyd. Min-inertia ACC is reported without a standard deviation. RANDOM initialization is only a sensitivity control on the primary contrasts.

## Five contrasts

1. X1: multiplier 1 (`gamma = gamma_0`) versus SSC E8 at gamma = 1.
2. X2: `beta = 1` versus `beta = 0`.
3. X3: mass-normalized `tau = 1` versus original gamma = 1. The equivalent-gamma control is an identity check.
4. X4: the fixed four-scale graph versus mass-matched `k = 5`.
5. X5: `alpha = 1` versus `alpha = 0`.

Seed-level 95% bootstrap intervals are conditional on the fixed `F` and `G`. Dataset-level intervals use ORL, JAFFE, USPS, and the average of the two YaleB Y0 versions. A Bonferroni 99% interval is reported across the five contrasts. One dataset moving up is not a significant result.

## Numerical acceptance

Each new convex objective was checked on a small problem with CVXPY. Real X1 runs are `OPTIMALITY_VERIFIED` only when the certified `G = F` region is confirmed or the independent ADMM objective matches. Otherwise they are `NUMERICALLY_UNCERTIFIED`. X2--X5 may be clustered when the validated IRLS update converges; nonconverged runs stay exploratory.
