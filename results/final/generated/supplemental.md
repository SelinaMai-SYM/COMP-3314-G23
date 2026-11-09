# Supplemental versions - not historical subset reproduction

All scores are percent. Reported in Chang et al. (2015) and Our reproduction/adapted setting are distinct. Closest means post-hoc display selection, not unsupervised tuning.

| Benchmark | Method | Dataset | Paper ACC | Our ACC mean ± sample SD | NMI | Status / setting / solver |
|---|---|---|---:|---|---|---|
| UMIST | kmeans | UMIST_precropped575 | 41.3 | 41.537 ± 2.624 | 64.036 ± 1.770 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| UMIST | sc | UMIST_precropped575 | 52.2 | 56.129 ± 5.166 | 76.766 ± 2.373 | COMPLETED; NOT_APPLICABLE |
| UMIST | pca_kmeans | UMIST_precropped575 | 48.8 | 43.057 ± 2.034 | 65.497 ± 1.468 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| UMIST | pca_sc | UMIST_precropped575 | 54.1 | 54.285 ± 6.899 | 76.071 ± 3.993 | COMPLETED; NOT_APPLICABLE |
| UMIST | lda_kmeans | UMIST_precropped575 | 49.7 | 40.929 ± 3.531 | 62.590 ± 2.901 | COMPLETED; NOT_APPLICABLE |
| UMIST | llc | UMIST_precropped575 | 63.3 | 62.087 ± 0.000 | 80.833 ± 0.032 | COMPLETED; NOT_APPLICABLE |
| UMIST | spls | UMIST_precropped575 | 70.4 | 52.414 ± 3.200 | 75.144 ± 1.409 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| UMIST | ssc | UMIST_precropped575 | 71.1 | 63.489 ± 1.712 | 81.457 ± 1.001 | TRUNCATED_EXECUTION; gamma_not_fixed_one; initialization_not_fixed_reference; MAX_ITER_REACHED |
| BinAlpha | kmeans | BinAlpha_candidate26x30 | 41.7 | 43.867 ± 2.590 | 57.332 ± 1.487 | COMPLETED; NOT_APPLICABLE |
| BinAlpha | sc | BinAlpha_candidate26x30 | 43.6 | 44.008 ± 2.547 | 57.403 ± 1.238 | COMPLETED; NOT_APPLICABLE |
| BinAlpha | pca_kmeans | BinAlpha_candidate26x30 | 42.4 | 44.146 ± 2.749 | 57.404 ± 1.556 | COMPLETED; NOT_APPLICABLE |
| BinAlpha | pca_sc | BinAlpha_candidate26x30 | 44.3 | 44.315 ± 2.531 | 58.088 ± 1.170 | COMPLETED; NOT_APPLICABLE |
| BinAlpha | lda_kmeans | BinAlpha_candidate26x30 | 42.9 | 43.995 ± 2.685 | 57.677 ± 1.573 | COMPLETED; NOT_APPLICABLE |
| BinAlpha | llc | BinAlpha_candidate26x30 | 40.7 | 37.562 ± 0.123 | 54.564 ± 0.063 | COMPLETED; NOT_APPLICABLE |
| BinAlpha | spls | BinAlpha_candidate26x30 | 48.5 | 48.503 ± 2.089 | 60.552 ± 1.028 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| BinAlpha | ssc | BinAlpha_candidate26x30 | 49.4 | 47.505 ± 1.302 | 58.823 ± 0.873 | COMPLETED; printed_E13_gamma_half; initialization_not_fixed_reference; ITERATE_CONVERGED_UNCERTIFIED |
| YaleB | kmeans | YaleB_dengcai32 | 14.4 | 9.741 ± 0.465 | 13.250 ± 0.585 | COMPLETED; alternate_dataset_version; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | sc | YaleB_dengcai32 | 34.8 | 32.727 ± 0.563 | 41.191 ± 0.669 | COMPLETED; alternate_dataset_version; input_l2_normalization; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | pca_kmeans | YaleB_dengcai32 | 24.9 | 9.848 ± 0.553 | 13.317 ± 0.662 | COMPLETED; alternate_dataset_version; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | pca_sc | YaleB_dengcai32 | 36.8 | 30.925 ± 0.543 | 38.859 ± 0.951 | COMPLETED; alternate_dataset_version; input_l2_normalization; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | lda_kmeans | YaleB_dengcai32 | 26.1 | 9.799 ± 0.847 | 13.786 ± 1.145 | COMPLETED; alternate_dataset_version; NOT_APPLICABLE |
| YaleB | llc | YaleB_dengcai32 | 38.2 | 38.241 ± 0.069 | 45.232 ± 0.093 | COMPLETED; alternate_dataset_version; NOT_APPLICABLE |
| YaleB | spls | YaleB_dengcai32 | 47.3 | 13.522 ± 0.776 | 19.438 ± 0.689 | COMPLETED; alternate_dataset_version; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | ssc | YaleB_dengcai32 | 49.8 | 43.583 ± 1.287 | 54.906 ± 0.826 | COMPLETED; alternate_dataset_version; input_l2_normalization; embedding_row_normalization; gamma_not_fixed_one; initialization_not_fixed_reference; ITERATE_CONVERGED_UNCERTIFIED |
