# Reconstruction tables

Generated from retained records by `python -m scripts.result_tables`. ACC/NMI are percentages; changes are percentage points.

## Fixed diagnostic (presentation 4.2)

E8 gamma=1, Y0, RANDOM, one minimum-SSE assignment from 50 starts in batch 0. A selected assignment has no across-start SD.

| Dataset | Fixed SC ACC / NMI (%) | Fixed SSC ACC / NMI (%) |
|---|---:|---:|
| ORL | 62.25 / 83.46 | 65.25 / 84.57 |
| JAFFE | 95.31 / 94.16 | 95.31 / 94.16 |
| YaleB cropped2414 | 19.97 / 26.89 | 19.68 / 26.86 |
| USPS | 65.50 / 81.00 | 65.63 / 81.24 |

## Joint mean matches (presentation 4.4)

Complete 50-start configurations selected retrospectively within declared pools. Both metrics and sample SD belong to the same configuration. MSRA uses the adapted native-16 source. Historical membership remains unverified.

| Dataset | Candidate | ACC ± SD (%) | NMI ± SD (%) | Equation / gamma / initializer | Solver |
|---|---|---:|---:|---|---|
| AR | AR_common_mask0092 | 51.21 ± 2.00 | 72.94 ± 1.05 | E13 / 1000 / SKLEARN_GREEDY_KMEANSPP | MAX_ITER_REACHED |
| JAFFE | JAFFE | 74.75 ± 8.37 | 85.60 ± 4.32 | E13 / 1e+06 / RANDOM | MAX_ITER_REACHED |
| ORL | ORL_att92 | 74.63 ± 0.64 | 89.71 ± 0.23 | E8 / 1000 / VANILLA_KMEANSPP | ITERATE_CONVERGED_UNCERTIFIED |
| UMIST | UMIST_LZUFE574_stratified_seed079 | 69.97 ± 2.27 | 85.17 ± 1.00 | E13 / 1000 / SKLEARN_GREEDY_KMEANSPP | MAX_ITER_REACHED |
| BinAlpha | BinAlpha_random_seed057 | 49.54 ± 2.71 | 63.46 ± 1.04 | E8 / 1e+06 / RANDOM | ITERATE_CONVERGED_UNCERTIFIED |
| MSRA50 | MSRA25_EBSA_16x16 | 49.25 ± 4.38 | 61.50 ± 3.89 | E13 / 1e+06 / VANILLA_KMEANSPP | MAX_ITER_REACHED |
| YaleB | YaleB_cropped2414_nearest_Y3 | 44.24 ± 0.82 | 52.61 ± 0.36 | E13 / 1000 / SKLEARN_GREEDY_KMEANSPP | MAX_ITER_REACHED |
| USPS | USPS | 66.26 ± 1.70 | 80.86 ± 1.20 | E13 / 1 / SKLEARN_GREEDY_KMEANSPP | ITERATE_CONVERGED_UNCERTIFIED |

No selected historical output has an optimality-gap certificate. These finite IRLS fits are distinct from the separately fitted extension SSC references.

## Initialization sensitivity (presentation 5.3)

Original v3_reproduction fixed-configuration means over 50 seeds; later subset-search coordinates are not substituted.

| Dataset | Method | RANDOM ACC (%) | Greedy++ ACC (%) | Change (pp) |
|---|---|---:|---:|---:|
| ORL | SC | 56.180 | 78.325 | +22.145 |
| ORL | SSC | 57.135 | 78.335 | +21.200 |
| JAFFE | SC | 68.526 | 95.305 | +26.779 |
| JAFFE | SSC | 68.432 | 95.099 | +26.667 |

## Baseline diagnostic (presentation 4.3)

Each cell is paper ACC/NMI → measured ACC/NMI (%). PCA uses d=40; SPLS uses d=50 and alpha=0.5. Fixed-objective rows use batch-0 native minimum-objective selection; LDA rows use the specified 50-run means. LDA→SC is the ridge adaptation, not recovered historical LDA-SC.

| Baseline | ORL | JAFFE | YaleB cropped2414 | USPS |
|---|---:|---:|---:|---:|
| K-means | 60.50/80.30 → 64.25/82.68 | 75.60/79.40 → 82.63/86.59 | 14.40/17.30 → 9.69/12.41 | 65.40/67.30 → 67.24/61.35 |
| SC | 72.70/85.80 → 62.25/83.46 | 76.10/80.20 → 95.31/94.16 | 34.80/55.60 → 19.97/26.89 | 64.30/69.50 → 65.50/81.00 |
| PCA→K-means | 64.50/80.60 → 65.50/83.72 | 75.80/79.80 → 86.85/88.62 | 24.90/26.70 → 9.65/12.46 | 69.40/73.10 → 67.29/61.39 |
| PCA→SC | 67.80/86.30 → 64.25/84.19 | 76.90/81.50 → 95.31/94.12 | 36.80/38.60 → 17.65/24.16 | 69.10/74.20 → 65.37/80.88 |
| LDA-Kmeans (mean) | 65.60/81.10 → 56.31/81.00 | 76.50/82.10 → 64.44/78.60 | 26.10/29.40 → 9.67/13.42 | 70.10/75.10 → 58.61/60.29 |
| Ridge LDA→SC (mean) | 68.30/86.80 → 49.19/75.66 | 77.40/81.90 → 59.38/73.72 | 38.20/39.90 → 35.85/50.58 | 70.40/75.40 → 57.79/61.10 |
| LLC | 71.50/84.90 → 81.50/89.78 | 78.60/82.50 → 94.84/93.76 | 38.20/34.10 → 28.13/35.60 | 63.90/67.50 → 63.11/73.99 |
| SPLS | 74.20/87.20 → 72.00/87.50 | 79.50/83.10 → 91.08/92.48 | 47.30/41.40 → 10.81/16.05 | 71.40/76.50 → 72.98/72.47 |
