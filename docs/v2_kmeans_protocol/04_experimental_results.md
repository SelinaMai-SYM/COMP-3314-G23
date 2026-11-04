# Experimental results

Accuracies below are percent. Means are over seeds 0..49 with sample SD (`ddof=1`). A best-inertia cell is one selected trial and has no within-batch SD. Full precision is in `results/v2_kmeans_protocol/primary_2x4_matrix.csv`. The campaign recorded 17,500 completed K-means trials. Validation reported no integrity problems.

P1 on ORL `att92` and JAFFE `zenodo` matches the existing v1 random Lloyd metrics seed by seed (`pilot_diagnosis.json`). That check is a diagnostic. The trial CSV was produced by this run.

## Gamma = 1

SSC solver at gamma 1 reached the 300-iteration cap without convergence on ORL, JAFFE, both YaleB matrices, BinAlpha, and UMIST `precropped575`. Those G matrices are returned iterates, not certified optima. USPS converged at iteration 298.

| Version | Method | P1 mean | P2 selected | P3 mean | P4 selected |
| --- | --- | --- | --- | --- | --- |
| ORL att92 | SC | 56.18 ± 4.19 | 62.25 | 78.33 ± 1.31 | 79.00 |
| ORL att92 | SSC | 57.27 ± 3.80 | 62.25 | 78.39 ± 1.54 | 78.25 |
| JAFFE zenodo | SC | 68.53 ± 11.15 | 95.31 | 95.31 ± 0 | 95.31 |
| JAFFE zenodo | SSC | 68.43 ± 11.08 | 95.31 | 95.10 ± 1.46 | 95.31 |
| YaleB cropped2414 | SC | 18.34 ± 1.28 | 19.97 | 21.78 ± 0.45 | 22.08 |
| YaleB cropped2414 | SSC | 17.62 ± 1.19 | 19.72 | 21.55 ± 0.47 | 22.04 |
| YaleB dengcai32 | SC | 20.16 ± 1.24 | 21.54 | 25.36 ± 0.48 | 25.64 |
| YaleB dengcai32 | SSC | 19.55 ± 1.30 | 21.38 | 25.43 ± 0.43 | 25.10 |
| USPS libsvm | SC | 61.74 ± 8.09 | 65.50 | 65.60 ± 1.87 | 65.50 |
| USPS libsvm | SSC | 61.70 ± 8.09 | 65.63 | 65.80 ± 1.90 | 65.63 |

Greedy k-means++ raises absolute ACC relative to random means on ORL (about +21 points) and JAFFE (about +27 points). On YaleB the lift is about 3 to 5 points. On USPS it is about 4 points. Minimum-inertia selection also raises ACC relative to the random mean, sharply on JAFFE, and it does so on both F and G. It does not create an SSC advantage over SC.

NMI moves with ACC on ORL and JAFFE. On YaleB cropped, NMI stays near 27 for every protocol. The published YaleB NMI values are 55.6 (SC) and 46.8 (SSC).

## Repeatability

Ten complete best-of-50 batches were finished for every eligible version, including BinAlpha and UMIST `precropped575`. The SD below is across the ten selected trials.

ORL SSC random-best ACC is 65.70 ± 2.46. ORL SSC greedy-best is 79.50 ± 0.84. JAFFE greedy-best is 95.31 with a numerically zero SD. YaleB selected means stay between about 19.7 and 25.1. USPS selected means stay near 65.6. Ten batches do not turn a low YaleB or USPS cell into the published SSC number.
