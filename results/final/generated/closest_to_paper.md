# closest_to_paper

All scores are percent. Reported in Chang et al. (2015) and Our reproduction/adapted setting are distinct. Closest means post-hoc display selection, not unsupervised tuning.

| Benchmark | Method | Dataset | Paper ACC | Our ACC mean ± sample SD | NMI | Status / setting / solver |
|---|---|---|---:|---|---|---|
| AR | kmeans |  | 36.3 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| AR | sc |  | 41.6 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| AR | pca_kmeans |  | 39.8 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| AR | pca_sc |  | 43.2 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| AR | lda_kmeans |  | 40.4 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| AR | lda_sc |  | 44.5 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| AR | llc |  | 48.7 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| AR | spls |  | 49.2 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| AR | ssc |  | 51.3 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| JAFFE | kmeans | JAFFE | 75.6 | 73.192 ± 5.734 | 83.068 ± 3.452 | COMPLETED; NOT_APPLICABLE |
| JAFFE | sc | JAFFE | 76.1 | 68.526 ± 11.152 | 83.016 ± 5.724 | COMPLETED; NOT_APPLICABLE |
| JAFFE | pca_kmeans | JAFFE | 75.8 | 74.826 ± 7.714 | 83.106 ± 4.531 | COMPLETED; NOT_APPLICABLE |
| JAFFE | pca_sc | JAFFE | 76.9 | 80.028 ± 5.737 | 87.786 ± 2.965 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| JAFFE | lda_kmeans | JAFFE | 76.5 | 64.441 ± 9.187 | 78.602 ± 5.082 | COMPLETED; NOT_APPLICABLE |
| JAFFE | lda_sc | JAFFE | 77.4 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| JAFFE | llc | JAFFE | 78.6 | 91.549 ± 0.000 | 92.745 ± 0.000 | COMPLETED; NOT_APPLICABLE |
| JAFFE | spls | JAFFE | 79.5 | 80.854 ± 6.576 | 86.915 ± 3.582 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| JAFFE | ssc | JAFFE | 81.2 | 74.751 ± 8.371 | 85.600 ± 4.325 | TRUNCATED_EXECUTION; printed_E13_gamma_half; gamma_not_fixed_one; MAX_ITER_REACHED |
| ORL | kmeans | ORL_att92 | 60.5 | 61.455 ± 2.851 | 82.755 ± 1.166 | COMPLETED; NOT_APPLICABLE |
| ORL | sc | ORL_att92 | 72.7 | 72.725 ± 3.149 | 87.492 ± 1.223 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| ORL | pca_kmeans | ORL_att92 | 64.5 | 63.115 ± 3.275 | 83.585 ± 1.224 | COMPLETED; NOT_APPLICABLE |
| ORL | pca_sc | ORL_att92 | 67.8 | 67.570 ± 2.925 | 85.810 ± 1.274 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| ORL | lda_kmeans | ORL_att92 | 65.6 | 56.305 ± 4.142 | 81.003 ± 1.652 | COMPLETED; NOT_APPLICABLE |
| ORL | lda_sc | ORL_att92 | 68.3 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| ORL | llc | ORL_att92 | 71.5 | 81.070 ± 0.606 | 89.917 ± 0.270 | COMPLETED; NOT_APPLICABLE |
| ORL | spls | ORL_att92 | 74.2 | 74.195 ± 1.982 | 87.898 ± 0.866 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| ORL | ssc | ORL_att92 | 76.0 | 75.965 ± 1.367 | 90.008 ± 0.411 | TRUNCATED_EXECUTION; printed_E13_gamma_half; gamma_not_fixed_one; initialization_not_fixed_reference; MAX_ITER_REACHED |
| UMIST | kmeans |  | 41.3 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| UMIST | sc |  | 52.2 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| UMIST | pca_kmeans |  | 48.8 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| UMIST | pca_sc |  | 54.1 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| UMIST | lda_kmeans |  | 49.7 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| UMIST | lda_sc |  | 54.7 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| UMIST | llc |  | 63.3 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| UMIST | spls |  | 70.4 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| UMIST | ssc |  | 71.1 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| BinAlpha | kmeans |  | 41.7 | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED;  |
| BinAlpha | sc |  | 43.6 | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED;  |
| BinAlpha | pca_kmeans |  | 42.4 | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED;  |
| BinAlpha | pca_sc |  | 44.3 | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED;  |
| BinAlpha | lda_kmeans |  | 42.9 | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED;  |
| BinAlpha | lda_sc |  | 45.1 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| BinAlpha | llc |  | 40.7 | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED;  |
| BinAlpha | spls |  | 48.5 | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED;  |
| BinAlpha | ssc |  | 49.4 | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED;  |
| MSRA50 | kmeans |  | 46.2 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| MSRA50 | sc |  | 52.3 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| MSRA50 | pca_kmeans |  | 56.0 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| MSRA50 | pca_sc |  | 54.9 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| MSRA50 | lda_kmeans |  | 56.4 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| MSRA50 | lda_sc |  | 55.1 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| MSRA50 | llc |  | 48.1 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| MSRA50 | spls |  | 60.3 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| MSRA50 | ssc |  | 63.2 | BLOCKED_DATA | BLOCKED_DATA | BLOCKED_DATA;  |
| YaleB | kmeans | YaleB_dengcai32 | 14.4 | 9.741 ± 0.465 | 13.250 ± 0.585 | COMPLETED; alternate_dataset_version; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | sc | YaleB_cropped2414 | 34.8 | 34.362 ± 0.957 | 45.145 ± 0.731 | COMPLETED; input_l2_normalization; embedding_row_normalization; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | pca_kmeans | YaleB_dengcai32 | 24.9 | 9.848 ± 0.553 | 13.317 ± 0.662 | COMPLETED; alternate_dataset_version; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | pca_sc | YaleB_dengcai32 | 36.8 | 30.925 ± 0.543 | 38.859 ± 0.951 | COMPLETED; alternate_dataset_version; input_l2_normalization; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | lda_kmeans | YaleB_dengcai32 | 26.1 | 9.799 ± 0.847 | 13.786 ± 1.145 | COMPLETED; alternate_dataset_version; NOT_APPLICABLE |
| YaleB | lda_sc | YaleB_cropped2414 | 38.2 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| YaleB | llc | YaleB_dengcai32 | 38.2 | 38.241 ± 0.069 | 45.232 ± 0.093 | COMPLETED; alternate_dataset_version; NOT_APPLICABLE |
| YaleB | spls | YaleB_dengcai32 | 47.3 | 13.522 ± 0.776 | 19.438 ± 0.689 | COMPLETED; alternate_dataset_version; initialization_not_fixed_reference; NOT_APPLICABLE |
| YaleB | ssc | YaleB_dengcai32 | 49.8 | 43.583 ± 1.287 | 54.906 ± 0.826 | COMPLETED; alternate_dataset_version; input_l2_normalization; embedding_row_normalization; gamma_not_fixed_one; initialization_not_fixed_reference; ITERATE_CONVERGED_UNCERTIFIED |
| USPS | kmeans | USPS | 65.4 | 66.059 ± 2.175 | 61.042 ± 0.874 | COMPLETED; NOT_APPLICABLE |
| USPS | sc | USPS | 64.3 | 65.597 ± 1.867 | 80.315 ± 2.128 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| USPS | pca_kmeans | USPS | 69.4 | 66.288 ± 1.948 | 60.991 ± 0.668 | COMPLETED; NOT_APPLICABLE |
| USPS | pca_sc | USPS | 69.1 | 65.881 ± 2.278 | 80.761 ± 1.029 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| USPS | lda_kmeans | USPS | 70.1 | 58.613 ± 6.332 | 60.292 ± 4.215 | COMPLETED; NOT_APPLICABLE |
| USPS | lda_sc | USPS | 70.4 | BLOCKED_METHOD | BLOCKED_METHOD | BLOCKED_METHOD;  |
| USPS | llc | USPS | 63.9 | 63.108 ± 0.005 | 73.987 ± 0.002 | COMPLETED; NOT_APPLICABLE |
| USPS | spls | USPS | 71.4 | 71.358 ± 4.134 | 73.422 ± 1.411 | COMPLETED; initialization_not_fixed_reference; NOT_APPLICABLE |
| USPS | ssc | USPS | 75.5 | 76.844 ± 5.117 | 84.082 ± 2.957 | COMPLETED; gamma_not_fixed_one; initialization_not_fixed_reference; ITERATE_CONVERGED_UNCERTIFIED |
