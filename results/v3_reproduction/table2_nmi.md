# Table 2 style NMI. Blank is missing, not zero.

| benchmark | method | paper_nmi_mean | paper_nmi_sd | locked_display | v3_per_run_nmi_mean_percent | nmi_gap_per_run_minus_paper | execution_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AR | kmeans | 68.7 | 3.0 |  |  |  | BLOCKED_DATA |
| AR | sc | 71.3 | 2.6 |  |  |  | BLOCKED_DATA |
| AR | pca_kmeans | 69.4 | 2.8 |  |  |  | BLOCKED_DATA |
| AR | pca_sc | 70.3 | 2.4 |  |  |  | BLOCKED_DATA |
| AR | lda_kmeans | 69.9 | 1.9 |  |  |  | BLOCKED_DATA |
| AR | lda_sc | 70.8 | 1.5 |  |  |  | BLOCKED_METHOD |
| AR | llc | 71.2 | 2.4 |  |  |  | BLOCKED_DATA |
| AR | spls | 72.4 | 1.7 |  |  |  | BLOCKED_DATA |
| AR | ssc | 73.2 | 1.4 |  |  |  | BLOCKED_DATA |
| JAFFE | kmeans | 79.4 | 0.8 | 83.07 ± 3.45 | 83.06840422157458 | 3.6684042215745762 | COMPLETED |
| JAFFE | sc | 80.2 | 0.9 | 83.02 ± 5.72 | 83.01621267255504 | 2.8162126725550394 | COMPLETED |
| JAFFE | pca_kmeans | 79.8 | 0.8 |  |  |  | COMPLETED |
| JAFFE | pca_sc | 81.5 | 1.3 |  |  |  | COMPLETED |
| JAFFE | lda_kmeans | 82.1 | 1.4 | 78.60 ± 5.08 | 78.60174464402239 | -3.498255355977605 | COMPLETED |
| JAFFE | lda_sc | 81.9 | 0.9 |  |  |  | BLOCKED_METHOD |
| JAFFE | llc | 82.5 | 1.7 | 93.69 ± 0.37 | 93.68697795204216 | 11.186977952042156 | COMPLETED |
| JAFFE | spls | 83.1 | 2.1 |  |  |  | COMPLETED |
| JAFFE | ssc | 84.3 | 1.6 | E13:83.04 ± 5.85 ; E8:83.05 ± 5.72 |  |  | COMPLETED |
| ORL | kmeans | 80.3 | 1.8 | 82.76 ± 1.17 | 82.75530037751312 | 2.455300377513126 | COMPLETED |
| ORL | sc | 85.8 | 1.9 | 80.47 ± 2.29 | 80.47054198827273 | -5.329458011727269 | COMPLETED |
| ORL | pca_kmeans | 80.6 | 1.6 |  |  |  | COMPLETED |
| ORL | pca_sc | 86.3 | 1.4 |  |  |  | COMPLETED |
| ORL | lda_kmeans | 81.1 | 2.1 | 81.00 ± 1.65 | 81.00271581562136 | -0.09728418437863695 | COMPLETED |
| ORL | lda_sc | 86.8 | 1.7 |  |  |  | BLOCKED_METHOD |
| ORL | llc | 84.9 | 1.5 | 89.99 ± 0.18 | 89.99303431942562 | 5.0930343194256125 | COMPLETED |
| ORL | spls | 87.2 | 1.8 |  |  |  | COMPLETED |
| ORL | ssc | 88.6 | 1.5 | E13:80.78 ± 2.18 ; E8:81.16 ± 2.20 |  |  | COMPLETED |
| UMIST | kmeans | 64.4 | 1.5 |  |  |  | BLOCKED_DATA |
| UMIST | sc | 72.1 | 1.7 |  |  |  | BLOCKED_DATA |
| UMIST | pca_kmeans | 68.2 | 1.8 |  |  |  | BLOCKED_DATA |
| UMIST | pca_sc | 72.9 | 1.5 |  |  |  | BLOCKED_DATA |
| UMIST | lda_kmeans | 68.8 | 1.5 |  |  |  | BLOCKED_DATA |
| UMIST | lda_sc | 74.1 | 2.0 |  |  |  | BLOCKED_METHOD |
| UMIST | llc | 77.3 | 1.8 |  |  |  | BLOCKED_DATA |
| UMIST | spls | 82.2 | 1.6 |  |  |  | BLOCKED_DATA |
| UMIST | ssc | 84.1 | 1.5 |  |  |  | BLOCKED_DATA |
| BinAlpha | kmeans | 58.6 | 1.4 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | sc | 59.7 | 1.6 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | pca_kmeans | 59.1 | 1.8 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | pca_sc | 60.6 | 1.9 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | lda_kmeans | 59.8 | 1.6 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | lda_sc | 61.3 | 1.7 |  |  |  | BLOCKED_METHOD |
| BinAlpha | llc | 61.4 | 1.9 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | spls | 63.6 | 1.8 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | ssc | 64.1 | 1.4 |  |  |  | SUBSET_UNVERIFIED |
| MSRA50 | kmeans | 56.7 | 1.8 |  |  |  | BLOCKED_DATA |
| MSRA50 | sc | 70.0 | 1.6 |  |  |  | BLOCKED_DATA |
| MSRA50 | pca_kmeans | 60.3 | 1.5 |  |  |  | BLOCKED_DATA |
| MSRA50 | pca_sc | 72.4 | 1.8 |  |  |  | BLOCKED_DATA |
| MSRA50 | lda_kmeans | 61.1 | 1.9 |  |  |  | BLOCKED_DATA |
| MSRA50 | lda_sc | 73.2 | 1.6 |  |  |  | BLOCKED_METHOD |
| MSRA50 | llc | 66.2 | 1.6 |  |  |  | BLOCKED_DATA |
| MSRA50 | spls | 69.6 | 1.8 |  |  |  | BLOCKED_DATA |
| MSRA50 | ssc | 72.2 | 1.4 |  |  |  | BLOCKED_DATA |
| YaleB | kmeans | 17.3 | 1.5 | YaleB_cropped2414:12.41 ± 0.77 ; YaleB_dengcai32:13.01 ± 0.86 |  |  | COMPLETED |
| YaleB | sc | 55.6 | 1.6 | YaleB_cropped2414:26.90 ± 0.67 ; YaleB_dengcai32:29.66 ± 0.81 |  |  | COMPLETED |
| YaleB | pca_kmeans | 26.7 | 1.8 |  |  |  | COMPLETED |
| YaleB | pca_sc | 38.6 | 1.5 |  |  |  | COMPLETED |
| YaleB | lda_kmeans | 29.4 | 1.6 | YaleB_cropped2414:13.42 ± 1.06 ; YaleB_dengcai32:13.79 ± 1.15 |  |  | COMPLETED |
| YaleB | lda_sc | 39.9 | 1.4 |  |  |  | BLOCKED_METHOD |
| YaleB | llc | 34.1 | 1.3 | YaleB_cropped2414:35.37 ± 0.39 ; YaleB_dengcai32:40.71 ± 0.14 |  |  | COMPLETED |
| YaleB | spls | 41.4 | 1.6 |  |  |  | COMPLETED |
| YaleB | ssc | 46.8 | 1.3 | E13:26.67 ± 0.72 ; E13:29.31 ± 0.93 ; E8:26.18 ± 0.90 ; E8:29.20 ± 0.92 |  |  | COMPLETED |
| USPS | kmeans | 67.3 | 1.8 | 61.04 ± 0.87 | 61.04152958981792 | -6.258470410182078 | COMPLETED |
| USPS | sc | 69.5 | 1.6 | 74.94 ± 4.49 | 74.93987825103389 | 5.439878251033889 | COMPLETED |
| USPS | pca_kmeans | 73.1 | 1.9 |  |  |  | COMPLETED |
| USPS | pca_sc | 74.2 | 1.8 |  |  |  | COMPLETED |
| USPS | lda_kmeans | 75.1 | 1.6 | 60.29 ± 4.21 | 60.291827504520704 | -14.80817249547929 | COMPLETED |
| USPS | lda_sc | 75.4 | 1.7 |  |  |  | BLOCKED_METHOD |
| USPS | llc | 67.5 | 1.5 | 73.99 ± 0.00 | 73.9873702444986 | 6.4873702444986066 | COMPLETED |
| USPS | spls | 76.5 | 1.8 |  |  |  | COMPLETED |
| USPS | ssc | 79.8 | 1.6 | E13:74.88 ± 4.45 ; E8:75.23 ± 4.56 |  |  | COMPLETED |
