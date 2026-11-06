# 72 historical cells

| benchmark | method | execution_status | blocker | locked_acc | locked_nmi |
| --- | --- | --- | --- | --- | --- |
| AR | kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  |
| AR | sc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| AR | pca_kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  |
| AR | pca_sc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| AR | lda_kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  |
| AR | lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  |
| AR | llc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| AR | spls | BLOCKED_DATA | BLOCKED_DATA |  |  |
| AR | ssc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| JAFFE | kmeans | COMPLETED |  | 73.19 ± 5.73 | 83.07 ± 3.45 |
| JAFFE | sc | COMPLETED |  | 68.53 ± 11.15 | 83.02 ± 5.72 |
| JAFFE | pca_kmeans | COMPLETED |  |  |  |
| JAFFE | pca_sc | COMPLETED |  |  |  |
| JAFFE | lda_kmeans | COMPLETED |  | 64.44 ± 9.19 | 78.60 ± 5.08 |
| JAFFE | lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  |
| JAFFE | llc | COMPLETED |  | 94.69 ± 0.74 | 93.69 ± 0.37 |
| JAFFE | spls | COMPLETED |  |  |  |
| JAFFE | ssc | COMPLETED |  | E13:68.59 ± 11.33 ; E8:68.43 ± 11.08 | E13:83.04 ± 5.85 ; E8:83.05 ± 5.72 |
| ORL | kmeans | COMPLETED |  | 61.46 ± 2.85 | 82.76 ± 1.17 |
| ORL | sc | COMPLETED |  | 56.18 ± 4.19 | 80.47 ± 2.29 |
| ORL | pca_kmeans | COMPLETED |  |  |  |
| ORL | pca_sc | COMPLETED |  |  |  |
| ORL | lda_kmeans | COMPLETED |  | 56.31 ± 4.14 | 81.00 ± 1.65 |
| ORL | lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  |
| ORL | llc | COMPLETED |  | 81.56 ± 0.70 | 89.99 ± 0.18 |
| ORL | spls | COMPLETED |  |  |  |
| ORL | ssc | COMPLETED |  | E13:56.59 ± 4.07 ; E8:57.14 ± 3.96 | E13:80.78 ± 2.18 ; E8:81.16 ± 2.20 |
| UMIST | kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  |
| UMIST | sc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| UMIST | pca_kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  |
| UMIST | pca_sc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| UMIST | lda_kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  |
| UMIST | lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  |
| UMIST | llc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| UMIST | spls | BLOCKED_DATA | BLOCKED_DATA |  |  |
| UMIST | ssc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| BinAlpha | kmeans | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  |
| BinAlpha | sc | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  |
| BinAlpha | pca_kmeans | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  |
| BinAlpha | pca_sc | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  |
| BinAlpha | lda_kmeans | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  |
| BinAlpha | lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  |
| BinAlpha | llc | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  |
| BinAlpha | spls | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  |
| BinAlpha | ssc | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  |
| MSRA50 | kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  |
| MSRA50 | sc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| MSRA50 | pca_kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  |
| MSRA50 | pca_sc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| MSRA50 | lda_kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  |
| MSRA50 | lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  |
| MSRA50 | llc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| MSRA50 | spls | BLOCKED_DATA | BLOCKED_DATA |  |  |
| MSRA50 | ssc | BLOCKED_DATA | BLOCKED_DATA |  |  |
| YaleB | kmeans | COMPLETED |  | YaleB_cropped2414:9.20 ± 0.58 ; YaleB_dengcai32:9.53 ± 0.71 | YaleB_cropped2414:12.41 ± 0.77 ; YaleB_dengcai32:13.01 ± 0.86 |
| YaleB | sc | COMPLETED |  | YaleB_cropped2414:18.34 ± 1.28 ; YaleB_dengcai32:20.16 ± 1.24 | YaleB_cropped2414:26.90 ± 0.67 ; YaleB_dengcai32:29.66 ± 0.81 |
| YaleB | pca_kmeans | COMPLETED |  |  |  |
| YaleB | pca_sc | COMPLETED |  |  |  |
| YaleB | lda_kmeans | COMPLETED |  | YaleB_cropped2414:9.67 ± 0.82 ; YaleB_dengcai32:9.80 ± 0.85 | YaleB_cropped2414:13.42 ± 1.06 ; YaleB_dengcai32:13.79 ± 1.15 |
| YaleB | lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  |
| YaleB | llc | COMPLETED |  | YaleB_cropped2414:28.04 ± 0.13 ; YaleB_dengcai32:33.52 ± 0.17 | YaleB_cropped2414:35.37 ± 0.39 ; YaleB_dengcai32:40.71 ± 0.14 |
| YaleB | spls | COMPLETED |  |  |  |
| YaleB | ssc | COMPLETED |  | E13:18.20 ± 1.22 ; E13:19.87 ± 1.25 ; E8:17.63 ± 1.19 ; E8:19.55 ± 1.30 | E13:26.67 ± 0.72 ; E13:29.31 ± 0.93 ; E8:26.18 ± 0.90 ; E8:29.20 ± 0.92 |
| USPS | kmeans | COMPLETED |  | 66.06 ± 2.17 | 61.04 ± 0.87 |
| USPS | sc | COMPLETED |  | 61.74 ± 8.09 | 74.94 ± 4.49 |
| USPS | pca_kmeans | COMPLETED |  |  |  |
| USPS | pca_sc | COMPLETED |  |  |  |
| USPS | lda_kmeans | COMPLETED |  | 58.61 ± 6.33 | 60.29 ± 4.21 |
| USPS | lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  |
| USPS | llc | COMPLETED |  | 63.11 ± 0.00 | 73.99 ± 0.00 |
| USPS | spls | COMPLETED |  |  |  |
| USPS | ssc | COMPLETED |  | E13:61.91 ± 8.36 ; E8:61.70 ± 8.09 | E13:74.88 ± 4.45 ; E8:75.23 ± 4.56 |
