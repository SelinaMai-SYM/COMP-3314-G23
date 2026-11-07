# 72-cell reproduction gap

Primary numbers use the frozen label-blind rule: Y0, report role `reference`, and RANDOM initialization for K-means, SC, and SSC. SSC reference is gamma=1. E8 and E13 are both shown. PCA, PCA-SC, and SLPS grids are not collapsed. LDA-SC stays blocked. AR 840, UMIST 564, and MSRA50 stay blocked. Gamma 1000 is not promoted.

| benchmark | method | status | primary ACC | paper ACC | ACC gap | primary NMI | paper NMI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AR | kmeans | BLOCKED_DATA |  | 36.3 |  |  | 68.7 |
| AR | sc | BLOCKED_DATA |  | 41.6 |  |  | 71.3 |
| AR | pca_kmeans | BLOCKED_DATA |  | 39.8 |  |  | 69.4 |
| AR | pca_sc | BLOCKED_DATA |  | 43.2 |  |  | 70.3 |
| AR | lda_kmeans | BLOCKED_DATA |  | 40.4 |  |  | 69.9 |
| AR | lda_sc | BLOCKED_METHOD |  | 44.5 |  |  | 70.8 |
| AR | llc | BLOCKED_DATA |  | 48.7 |  |  | 71.2 |
| AR | spls | BLOCKED_DATA |  | 49.2 |  |  | 72.4 |
| AR | ssc | BLOCKED_DATA |  | 51.3 |  |  | 73.2 |
| JAFFE | kmeans | PRIMARY_REFERENCE | 73.19 ± 5.73 | 75.6 | -2.4075117370892087 | 83.07 ± 3.45 | 79.4 |
| JAFFE | sc | PRIMARY_REFERENCE | 68.53 ± 11.15 | 76.1 | -7.574178403755866 | 83.02 ± 5.72 | 80.2 |
| JAFFE | pca_kmeans | GRID_NOT_COLLAPSED |  | 75.8 |  |  | 79.8 |
| JAFFE | pca_sc | GRID_NOT_COLLAPSED |  | 76.9 |  |  | 81.5 |
| JAFFE | lda_kmeans | PRIMARY_REFERENCE | 64.44 ± 9.19 | 76.5 | -12.058685446009392 | 78.60 ± 5.08 | 82.1 |
| JAFFE | lda_sc | BLOCKED_METHOD |  | 77.4 |  |  | 81.9 |
| JAFFE | llc | PRIMARY_REFERENCE | 94.69 ± 0.74 | 78.6 | 16.08544600938967 | 93.69 ± 0.37 | 82.5 |
| JAFFE | spls | GRID_NOT_COLLAPSED |  | 79.5 |  |  | 83.1 |
| JAFFE | ssc | MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED | E13:JAFFE:68.59 ± 11.33 ; E8:JAFFE:68.43 ± 11.08 | 81.2 |  | E13:JAFFE:83.04 ± 5.85 ; E8:JAFFE:83.05 ± 5.72 | 84.3 |
| ORL | kmeans | PRIMARY_REFERENCE | 61.46 ± 2.85 | 60.5 | 0.9550000000000054 | 82.76 ± 1.17 | 80.3 |
| ORL | sc | PRIMARY_REFERENCE | 56.18 ± 4.19 | 72.7 | -16.520000000000003 | 80.47 ± 2.29 | 85.8 |
| ORL | pca_kmeans | GRID_NOT_COLLAPSED |  | 64.5 |  |  | 80.6 |
| ORL | pca_sc | GRID_NOT_COLLAPSED |  | 67.8 |  |  | 86.3 |
| ORL | lda_kmeans | PRIMARY_REFERENCE | 56.31 ± 4.14 | 65.6 | -9.294999999999987 | 81.00 ± 1.65 | 81.1 |
| ORL | lda_sc | BLOCKED_METHOD |  | 68.3 |  |  | 86.8 |
| ORL | llc | PRIMARY_REFERENCE | 81.56 ± 0.70 | 71.5 | 10.060000000000002 | 89.99 ± 0.18 | 84.9 |
| ORL | spls | GRID_NOT_COLLAPSED |  | 74.2 |  |  | 87.2 |
| ORL | ssc | MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED | E13:ORL_att92:56.59 ± 4.07 ; E8:ORL_att92:57.14 ± 3.96 | 76.0 |  | E13:ORL_att92:80.78 ± 2.18 ; E8:ORL_att92:81.16 ± 2.20 | 88.6 |
| UMIST | kmeans | BLOCKED_DATA |  | 41.3 |  |  | 64.4 |
| UMIST | sc | BLOCKED_DATA |  | 52.2 |  |  | 72.1 |
| UMIST | pca_kmeans | BLOCKED_DATA |  | 48.8 |  |  | 68.2 |
| UMIST | pca_sc | BLOCKED_DATA |  | 54.1 |  |  | 72.9 |
| UMIST | lda_kmeans | BLOCKED_DATA |  | 49.7 |  |  | 68.8 |
| UMIST | lda_sc | BLOCKED_METHOD |  | 54.7 |  |  | 74.1 |
| UMIST | llc | BLOCKED_DATA |  | 63.3 |  |  | 77.3 |
| UMIST | spls | BLOCKED_DATA |  | 70.4 |  |  | 82.2 |
| UMIST | ssc | BLOCKED_DATA |  | 71.1 |  |  | 84.1 |
| BinAlpha | kmeans | SUBSET_UNVERIFIED |  | 41.7 |  |  | 58.6 |
| BinAlpha | sc | SUBSET_UNVERIFIED |  | 43.6 |  |  | 59.7 |
| BinAlpha | pca_kmeans | SUBSET_UNVERIFIED |  | 42.4 |  |  | 59.1 |
| BinAlpha | pca_sc | SUBSET_UNVERIFIED |  | 44.3 |  |  | 60.6 |
| BinAlpha | lda_kmeans | SUBSET_UNVERIFIED |  | 42.9 |  |  | 59.8 |
| BinAlpha | lda_sc | BLOCKED_METHOD |  | 45.1 |  |  | 61.3 |
| BinAlpha | llc | SUBSET_UNVERIFIED |  | 40.7 |  |  | 61.4 |
| BinAlpha | spls | SUBSET_UNVERIFIED |  | 48.5 |  |  | 63.6 |
| BinAlpha | ssc | SUBSET_UNVERIFIED |  | 49.4 |  |  | 64.1 |
| MSRA50 | kmeans | BLOCKED_DATA |  | 46.2 |  |  | 56.7 |
| MSRA50 | sc | BLOCKED_DATA |  | 52.3 |  |  | 70.0 |
| MSRA50 | pca_kmeans | BLOCKED_DATA |  | 56.0 |  |  | 60.3 |
| MSRA50 | pca_sc | BLOCKED_DATA |  | 54.9 |  |  | 72.4 |
| MSRA50 | lda_kmeans | BLOCKED_DATA |  | 56.4 |  |  | 61.1 |
| MSRA50 | lda_sc | BLOCKED_METHOD |  | 55.1 |  |  | 73.2 |
| MSRA50 | llc | BLOCKED_DATA |  | 48.1 |  |  | 66.2 |
| MSRA50 | spls | BLOCKED_DATA |  | 60.3 |  |  | 69.6 |
| MSRA50 | ssc | BLOCKED_DATA |  | 63.2 |  |  | 72.2 |
| YaleB | kmeans | MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED | YaleB_cropped2414:9.20 ± 0.58 ; YaleB_dengcai32:9.53 ± 0.71 | 14.4 |  | YaleB_cropped2414:12.41 ± 0.77 ; YaleB_dengcai32:13.01 ± 0.86 | 17.3 |
| YaleB | sc | MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED | YaleB_cropped2414:18.34 ± 1.28 ; YaleB_dengcai32:20.16 ± 1.24 | 34.8 |  | YaleB_cropped2414:26.90 ± 0.67 ; YaleB_dengcai32:29.66 ± 0.81 | 55.6 |
| YaleB | pca_kmeans | GRID_NOT_COLLAPSED |  | 24.9 |  |  | 26.7 |
| YaleB | pca_sc | GRID_NOT_COLLAPSED |  | 36.8 |  |  | 38.6 |
| YaleB | lda_kmeans | MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED | YaleB_cropped2414:9.67 ± 0.82 ; YaleB_dengcai32:9.80 ± 0.85 | 26.1 |  | YaleB_cropped2414:13.42 ± 1.06 ; YaleB_dengcai32:13.79 ± 1.15 | 29.4 |
| YaleB | lda_sc | BLOCKED_METHOD |  | 38.2 |  |  | 39.9 |
| YaleB | llc | MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED | YaleB_cropped2414:28.04 ± 0.13 ; YaleB_dengcai32:33.52 ± 0.17 | 38.2 |  | YaleB_cropped2414:35.37 ± 0.39 ; YaleB_dengcai32:40.71 ± 0.14 | 34.1 |
| YaleB | spls | GRID_NOT_COLLAPSED |  | 47.3 |  |  | 41.4 |
| YaleB | ssc | MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED | E13:YaleB_cropped2414:18.20 ± 1.22 ; E8:YaleB_cropped2414:17.63 ± 1.19 ; E13:YaleB_dengcai32:19.87 ± 1.25 ; E8:YaleB_dengcai32:19.55 ± 1.30 | 49.8 |  | E13:YaleB_cropped2414:26.67 ± 0.72 ; E8:YaleB_cropped2414:26.18 ± 0.90 ; E13:YaleB_dengcai32:29.31 ± 0.93 ; E8:YaleB_dengcai32:29.20 ± 0.92 | 46.8 |
| USPS | kmeans | PRIMARY_REFERENCE | 66.06 ± 2.17 | 65.4 | 0.6589374058937381 | 61.04 ± 0.87 | 67.3 |
| USPS | sc | PRIMARY_REFERENCE | 61.74 ± 8.09 | 64.3 | -2.5611314261131426 | 74.94 ± 4.49 | 69.5 |
| USPS | pca_kmeans | GRID_NOT_COLLAPSED |  | 69.4 |  |  | 73.1 |
| USPS | pca_sc | GRID_NOT_COLLAPSED |  | 69.1 |  |  | 74.2 |
| USPS | lda_kmeans | PRIMARY_REFERENCE | 58.61 ± 6.33 | 70.1 | -11.487395138739494 | 60.29 ± 4.21 | 75.1 |
| USPS | lda_sc | BLOCKED_METHOD |  | 70.4 |  |  | 75.4 |
| USPS | llc | PRIMARY_REFERENCE | 63.11 ± 0.00 | 63.9 | -0.7920197892019871 | 73.99 ± 0.00 | 67.5 |
| USPS | spls | GRID_NOT_COLLAPSED |  | 71.4 |  |  | 76.5 |
| USPS | ssc | MULTIPLE_REFERENCE_ROWS_NOT_COLLAPSED | E13:USPS:61.91 ± 8.36 ; E8:USPS:61.70 ± 8.09 | 75.5 |  | E13:USPS:74.88 ± 4.45 ; E8:USPS:75.23 ± 4.56 | 79.8 |
