# Table 1 style ACC. Blank is missing, not zero. SSC shows both variants in locked_display.

| benchmark | method | paper_acc_mean | paper_acc_sd | locked_display | v3_per_run_acc_mean_percent | acc_gap_per_run_minus_paper | execution_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AR | kmeans | 36.3 | 1.4 |  |  |  | BLOCKED_DATA |
| AR | sc | 41.6 | 2.1 |  |  |  | BLOCKED_DATA |
| AR | pca_kmeans | 39.8 | 1.8 |  |  |  | BLOCKED_DATA |
| AR | pca_sc | 43.2 | 1.7 |  |  |  | BLOCKED_DATA |
| AR | lda_kmeans | 40.4 | 1.5 |  |  |  | BLOCKED_DATA |
| AR | lda_sc | 44.5 | 1.3 |  |  |  | BLOCKED_METHOD |
| AR | llc | 48.7 | 1.6 |  |  |  | BLOCKED_DATA |
| AR | spls | 49.2 | 1.4 |  |  |  | BLOCKED_DATA |
| AR | ssc | 51.3 | 1.5 |  |  |  | BLOCKED_DATA |
| JAFFE | kmeans | 75.6 | 1.8 | 73.19 ± 5.73 | 73.19248826291079 | -2.4075117370892087 | COMPLETED |
| JAFFE | sc | 76.1 | 1.6 | 68.53 ± 11.15 | 68.52582159624413 | -7.574178403755866 | COMPLETED |
| JAFFE | pca_kmeans | 75.8 | 1.5 |  |  |  | COMPLETED |
| JAFFE | pca_sc | 76.9 | 1.8 |  |  |  | COMPLETED |
| JAFFE | lda_kmeans | 76.5 | 1.7 | 64.44 ± 9.19 | 64.44131455399061 | -12.058685446009392 | COMPLETED |
| JAFFE | lda_sc | 77.4 | 1.9 |  |  |  | BLOCKED_METHOD |
| JAFFE | llc | 78.6 | 1.5 | 94.69 ± 0.74 | 94.68544600938966 | 16.08544600938967 | COMPLETED |
| JAFFE | spls | 79.5 | 2.1 |  |  |  | COMPLETED |
| JAFFE | ssc | 81.2 | 1.6 | E13:68.59 ± 11.33 ; E8:68.43 ± 11.08 |  |  | COMPLETED |
| ORL | kmeans | 60.5 | 1.8 | 61.46 ± 2.85 | 61.455000000000005 | 0.9550000000000054 | COMPLETED |
| ORL | sc | 72.7 | 2.3 | 56.18 ± 4.19 | 56.18 | -16.520000000000003 | COMPLETED |
| ORL | pca_kmeans | 64.5 | 2.3 |  |  |  | COMPLETED |
| ORL | pca_sc | 67.8 | 2.1 |  |  |  | COMPLETED |
| ORL | lda_kmeans | 65.6 | 2.6 | 56.31 ± 4.14 | 56.30500000000001 | -9.294999999999987 | COMPLETED |
| ORL | lda_sc | 68.3 | 2.4 |  |  |  | BLOCKED_METHOD |
| ORL | llc | 71.5 | 2.2 | 81.56 ± 0.70 | 81.56 | 10.060000000000002 | COMPLETED |
| ORL | spls | 74.2 | 1.8 |  |  |  | COMPLETED |
| ORL | ssc | 76.0 | 1.6 | E13:56.59 ± 4.07 ; E8:57.14 ± 3.96 |  |  | COMPLETED |
| UMIST | kmeans | 41.3 | 1.6 |  |  |  | BLOCKED_DATA |
| UMIST | sc | 52.2 | 1.4 |  |  |  | BLOCKED_DATA |
| UMIST | pca_kmeans | 48.8 | 1.7 |  |  |  | BLOCKED_DATA |
| UMIST | pca_sc | 54.1 | 1.9 |  |  |  | BLOCKED_DATA |
| UMIST | lda_kmeans | 49.7 | 1.8 |  |  |  | BLOCKED_DATA |
| UMIST | lda_sc | 54.7 | 1.5 |  |  |  | BLOCKED_METHOD |
| UMIST | llc | 63.3 | 1.8 |  |  |  | BLOCKED_DATA |
| UMIST | spls | 70.4 | 1.6 |  |  |  | BLOCKED_DATA |
| UMIST | ssc | 71.1 | 1.8 |  |  |  | BLOCKED_DATA |
| BinAlpha | kmeans | 41.7 | 1.1 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | sc | 43.6 | 1.5 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | pca_kmeans | 42.4 | 1.5 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | pca_sc | 44.3 | 1.8 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | lda_kmeans | 42.9 | 1.7 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | lda_sc | 45.1 | 1.4 |  |  |  | BLOCKED_METHOD |
| BinAlpha | llc | 40.7 | 1.8 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | spls | 48.5 | 1.9 |  |  |  | SUBSET_UNVERIFIED |
| BinAlpha | ssc | 49.4 | 1.3 |  |  |  | SUBSET_UNVERIFIED |
| MSRA50 | kmeans | 46.2 | 1.7 |  |  |  | BLOCKED_DATA |
| MSRA50 | sc | 52.3 | 1.8 |  |  |  | BLOCKED_DATA |
| MSRA50 | pca_kmeans | 56.0 | 1.9 |  |  |  | BLOCKED_DATA |
| MSRA50 | pca_sc | 54.9 | 1.6 |  |  |  | BLOCKED_DATA |
| MSRA50 | lda_kmeans | 56.4 | 1.8 |  |  |  | BLOCKED_DATA |
| MSRA50 | lda_sc | 55.1 | 1.7 |  |  |  | BLOCKED_METHOD |
| MSRA50 | llc | 48.1 | 1.4 |  |  |  | BLOCKED_DATA |
| MSRA50 | spls | 60.3 | 1.3 |  |  |  | BLOCKED_DATA |
| MSRA50 | ssc | 63.2 | 1.1 |  |  |  | BLOCKED_DATA |
| YaleB | kmeans | 14.4 | 1.5 | YaleB_cropped2414:9.20 ± 0.58 ; YaleB_dengcai32:9.53 ± 0.71 |  |  | COMPLETED |
| YaleB | sc | 34.8 | 1.4 | YaleB_cropped2414:18.34 ± 1.28 ; YaleB_dengcai32:20.16 ± 1.24 |  |  | COMPLETED |
| YaleB | pca_kmeans | 24.9 | 1.8 |  |  |  | COMPLETED |
| YaleB | pca_sc | 36.8 | 2.0 |  |  |  | COMPLETED |
| YaleB | lda_kmeans | 26.1 | 1.8 | YaleB_cropped2414:9.67 ± 0.82 ; YaleB_dengcai32:9.80 ± 0.85 |  |  | COMPLETED |
| YaleB | lda_sc | 38.2 | 1.6 |  |  |  | BLOCKED_METHOD |
| YaleB | llc | 38.2 | 1.5 | YaleB_cropped2414:28.04 ± 0.13 ; YaleB_dengcai32:33.52 ± 0.17 |  |  | COMPLETED |
| YaleB | spls | 47.3 | 1.7 |  |  |  | COMPLETED |
| YaleB | ssc | 49.8 | 1.6 | E13:18.20 ± 1.22 ; E13:19.87 ± 1.25 ; E8:17.63 ± 1.19 ; E8:19.55 ± 1.30 |  |  | COMPLETED |
| USPS | kmeans | 65.4 | 1.7 | 66.06 ± 2.17 | 66.05893740589374 | 0.6589374058937381 | COMPLETED |
| USPS | sc | 64.3 | 1.4 | 61.74 ± 8.09 | 61.738868573886855 | -2.5611314261131426 | COMPLETED |
| USPS | pca_kmeans | 69.4 | 1.8 |  |  |  | COMPLETED |
| USPS | pca_sc | 69.1 | 1.5 |  |  |  | COMPLETED |
| USPS | lda_kmeans | 70.1 | 1.3 | 58.61 ± 6.33 | 58.6126048612605 | -11.487395138739494 | COMPLETED |
| USPS | lda_sc | 70.4 | 1.5 |  |  |  | BLOCKED_METHOD |
| USPS | llc | 63.9 | 1.7 | 63.11 ± 0.00 | 63.10798021079801 | -0.7920197892019871 | COMPLETED |
| USPS | spls | 71.4 | 1.6 |  |  |  | COMPLETED |
| USPS | ssc | 75.5 | 1.9 | E13:61.91 ± 8.36 ; E8:61.70 ± 8.09 |  |  | COMPLETED |
