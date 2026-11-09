# YaleB

All scores are percent. Reported in Chang et al. (2015) and Our reproduction/adapted setting are distinct. Closest means post-hoc display selection, not unsupervised tuning.

| Benchmark | Method | Dataset | Paper ACC | Our ACC mean ± sample SD | NMI | Status / setting / solver |
|---|---|---|---:|---|---|---|
| YaleB | kmeans | YaleB_dengcai32 | 14.4 | 9.741 ± 0.465 | 13.250 ± 0.585 | COMPLETED; alternate_dataset_version; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | kmeans | YaleB_cropped2414 | 14.4 | 9.199 ± 0.580 | 12.413 ± 0.772 | COMPLETED; NOT_APPLICABLE |
| YaleB | sc | YaleB_cropped2414 | 34.8 | 34.362 ± 0.957 | 45.145 ± 0.731 | COMPLETED; input_l2_normalization; embedding_row_normalization; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | sc | YaleB_cropped2414 | 34.8 | 18.340 ± 1.284 | 26.903 ± 0.672 | COMPLETED; NOT_APPLICABLE |
| YaleB | pca_kmeans | YaleB_dengcai32 | 24.9 | 9.848 ± 0.553 | 13.317 ± 0.662 | COMPLETED; alternate_dataset_version; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | pca_kmeans | YaleB_cropped2414 | 24.9 | GRID_NOT_COLLAPSED | GRID_NOT_COLLAPSED | GRID_NOT_COLLAPSED;  |
| YaleB | pca_sc | YaleB_dengcai32 | 36.8 | 30.925 ± 0.543 | 38.859 ± 0.951 | COMPLETED; alternate_dataset_version; input_l2_normalization; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | pca_sc | YaleB_cropped2414 | 36.8 | GRID_NOT_COLLAPSED | GRID_NOT_COLLAPSED | GRID_NOT_COLLAPSED;  |
| YaleB | lda_kmeans | YaleB_dengcai32 | 26.1 | 9.799 ± 0.847 | 13.786 ± 1.145 | COMPLETED; alternate_dataset_version; NOT_APPLICABLE |
| YaleB | lda_kmeans | YaleB_cropped2414 | 26.1 | 9.672 ± 0.823 | 13.416 ± 1.065 | COMPLETED; NOT_APPLICABLE |
| YaleB | lda_sc | YaleB_cropped2414 | 38.2 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| YaleB | lda_sc | YaleB_cropped2414 | 38.2 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| YaleB | llc | YaleB_dengcai32 | 38.2 | 38.241 ± 0.069 | 45.232 ± 0.093 | COMPLETED; alternate_dataset_version; NOT_APPLICABLE |
| YaleB | llc | YaleB_cropped2414 | 38.2 | 28.037 ± 0.127 | 35.369 ± 0.393 | COMPLETED; NOT_APPLICABLE |
| YaleB | spls | YaleB_dengcai32 | 47.3 | 13.522 ± 0.776 | 19.438 ± 0.689 | COMPLETED; alternate_dataset_version; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | spls | YaleB_cropped2414 | 47.3 | GRID_NOT_COLLAPSED | GRID_NOT_COLLAPSED | GRID_NOT_COLLAPSED;  |
| YaleB | ssc | YaleB_dengcai32 | 49.8 | 43.583 ± 1.287 | 54.906 ± 0.826 | COMPLETED; alternate_dataset_version; input_l2_normalization; embedding_row_normalization; gamma_not_fixed_one; initialization_not_fixed_reference; ITERATE_CONVERGED_UNCERTIFIED |
| YaleB | ssc | YaleB_cropped2414 | 49.8 | 17.629 ± 1.190 | 26.184 ± 0.900 | COMPLETED; iteration_budget_not_300; ITERATE_CONVERGED_UNCERTIFIED |
