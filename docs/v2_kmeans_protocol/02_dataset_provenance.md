# Dataset provenance

Images are read from the v1 worktree through `DATA_ROOT`. They are not stored on `v2`.

| Benchmark | Version we run | Paper target | Status |
| --- | --- | --- | --- |
| ORL | `att92` | 400 images, 40 subjects | Obtained AT&T release, bilinear 32×32. Interpolation is an assumption, so paper gaps are exploratory. |
| JAFFE | `zenodo` | 213 images, 10 subjects | Zenodo archive resized to 26×26. Not the authors' unpublished copy. |
| YaleB | `cropped2414` and `dengcai32` | 2414 images, 38 subjects | Two matrices of one benchmark. They are not averaged and are not counted as two benchmarks. |
| USPS | `libsvm` | 9298 digits, 10 classes | Standard LIBSVM train+test split. The paper publishes no checksum. |
| BinAlpha | `CANDIDATE_BIN_ALPHA` | 780 images, 26 classes | `NON_EXACT`. Author sample indices were not recovered. Paper gap is `NOT_COMPARABLE`. |
| UMIST | `precropped575` | 564 images, 20 subjects | `NON_EXACT`. The 564-image subset (`sheffield564`) stays blocked. No image was removed by accuracy. |
| AR | none | 840 images, 120 subjects | `BLOCKED`. License, labels, and the 840/120 subset are not jointly verified. A 100-identity archive is not labeled as the paper AR. |
| MSRA50 | none | 1799 images, 12 classes | `BLOCKED_DATA`. No substitute corpus is used. |

Loader checksums and sample counts are written to `results/v2_kmeans_protocol/dataset_status.csv` when the campaign probes the files.
