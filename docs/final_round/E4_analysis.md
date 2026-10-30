# E4 — YaleB version and the spectral pipeline

Question: why are methods far below the published YaleB accuracies? Published Table 1, historical only: K-means 14.4%, SC 34.8%, SSC 49.8%. Our strict_paper cropped2414 SC is 0.1834 and E8 γ = 1 is 0.1762 (`20261021_222721__STRICT_PAPER__YALEB__SC_EQ4__c049ed51`, `20261021_222857__STRICT_PAPER__YALEB__SSC_E8_G1P0__2ba528ff`).

## Counts, scale, identity

Both matrices have 2414 images, 38 labels, 1024 columns, float range [0, 1] after division by 255, and no duplicate rows at 1e-10. Per-identity count vectors are identical, including the run 64×10, then 60, 59, 60, 63, 62, 63, 63, then 64s. Min 59, max 64. Checksums: Deng Cai mat `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99`; cropped zip `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573`.

Cropped images are 192×168 PGM files resized to 32×32. The mat is already 32×32 and has no subject names. Cropped folders omit yaleB14. Equal histograms do not identify people.

Sample matching: class means are assigned by Hungarian on Euclidean cost, then images inside each paired class. Orientations tried: C-order 32×32, transpose, three rotations, flip left-right, flip up-down. Best orientation against bilinear cropped is transpose (the MATLAB column-major layout noted in the loader). After that alignment, median matched image L2 is 1.92, max absolute pixel difference is 0.914, and the fraction of matched images with max-abs ≤ 1e-8 is 0. Stored row order matches on 0 images. Nearest and bicubic give the same negative result (median L2 2.08 and 1.96).

UNRESOLVED as pixel identity: the two releases are not the same matrix. CONFIRMED: they share n, K, dimension, [0, 1] scaling, and the per-identity count vector.

## Controlled comparison

Same `SpectralGraphConfig`: k = 5 (paper-explicit), median positive kNN squared distance (B, δ is not stated), union symmetrization (B), symmetric normalized Laplacian (paper-explicit for the spectral step), no row normalization, seeds 0..49, explicit random Lloyd. Only the matrix changes. The graph is rebuilt from each matrix. Copying one W onto the other would not be spectral clustering of the second matrix. Edge Jaccard of the two controlled graphs is 0.726.

The fresh cropped embedding matches the saved strict_paper SC F with max absolute error 4.2e-14. K-means(F) ACC:

| Version | ACC | sample SD | components | undirected edges |
| --- | --- | --- | --- | --- |
| cropped2414 bilinear | 0.1834 | 0.0128 | 1 | 8510 |
| dengcai32 | 0.2016 | 0.0124 | 1 | 8568 |

SUPPORTED: switching to the Deng Cai matrix raises K-means(F) ACC by about 1.8 percentage points. The published SC number is 34.8%. The version gap does not explain that distance. Both graphs are connected. Eigenvalue tables are in `E4_graph_diagnostics.csv`.

## Diagnostics that are not the paper method

Run after the controlled pair. The highest ACC is not adopted.

| Variant | Level | cropped ACC | dengcai ACC | Note |
| --- | --- | --- | --- | --- |
| mean kNN bandwidth | B | 0.1834 | 0.2016 | same edges as the median rule; ACC unchanged at this precision |
| mutual symmetrization | B | 0.2218 | 0.2607 | 179 and 197 connected components |
| row normalization | C | 0.2196 | 0.2655 | Ng–Jordan–Weiss; not stated for SSC |
| nearest resize | B | 0.2004 | — | kernel not stated |
| bicubic resize | B | 0.1948 | — | kernel not stated |

Mutual symmetrization raises ACC and disconnects the graph. That combination is not treated as the authors' construction. The best diagnostic on Deng Cai, row normalization at 0.2655, is still about 8 percentage points below published SC and about 23 points below published SSC, and it is Level C.

CONFIRMED implementation difference: cropped2414 and dengcai32 are different pixel matrices under every orientation we tried. SUPPORTED contributing factor: the matrix choice moves SC by ~2 points, and a few B/C graph choices move it by up to ~6 points on Deng Cai. UNRESOLVED: the remaining distance to 34.8% / 49.8%, including δ, which 32×32 crop the authors used, and the K-means protocol (E1: k-means++ reaches only 0.218 on cropped F).
