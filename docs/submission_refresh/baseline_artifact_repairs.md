# Paired SLPS controls and recoverable baseline state

Before the mandatory SLPS block starts, its queue includes the previously displayed alpha/dimension settings as additional paired k=5/k=7 controls. The primary 18 configurations remain alpha in {0.2,0.5,0.8}, dimension in {30,70,110}, and random one-start Lloyd rounding over seeds 0-49. The old displayed configurations used greedy K-means++, so their additional controls retain that exact initialization and remain separately labelled:

| Benchmark/version | Alpha | Dimension | Additional k | Rounding |
| --- | ---: | ---: | --- | --- |
| JAFFE | 0.95 | 70 | 5,7 | Greedy K-means++, n_init=1 |
| ORL att92 | 0.85 | 40 | 5,7 | Greedy K-means++, n_init=1 |
| YaleB DengCai32 | 0.2 | 70 | 5,7 | Greedy K-means++, n_init=1 |
| YaleB cropped2414 | 0.2 | 70 | 5,7 | Same setting transferred explicitly from DengCai32 |

These controls come from the preserved ACC-only `closest_to_paper` SPLS rows in `results/final/generated/selection_manifest.jsonl`. Their use does not redefine the new joint-selection rule or establish the authors' historical settings. MSRA has no old displayed setting and keeps the preregistered 18-configuration grid. USPS's old alpha 0.45 and dimension 70 record is retained historically; USPS is outside the prescribed new paired SLPS dataset block.

The adapter groups configurations by k and alpha, computes one one-shot representation and full SVD per group, and reuses that exact fitted state across dimensions and rounding protocols. Requested dimensions are clipped to valid distinct dimensions with aliases retained; the numerical-rank rule is the existing SLPS library's singular[0]*1e-10. It records shrunk patterns, original local-scaling affinity, Laplacian, coefficient matrix, PCA mean, singular values, and the exact projection. The optional `return_state=True` library argument observes state without changing the mathematical solution; omitted arguments preserve existing behavior.

The MSRA PCA-SC records retain the PCA mean/projection/scores, upstream graph, final spectral representation, and graph/spectral metadata. LLC similarly exposes its actual regression matrix, raw eigenspace, row norms, and normalized eigenspace through an optional observation-only state. Every rounding result saves its final rotation and returned-state diagnostics. Native best-of-50 uses the returned state's actual Procrustes objective within the same fixed representation; a missing objective now fails instead of silently becoming zero. Learned spaces are not selected by comparing their raw inertia. Partial rounding and fitted representations remain recoverable when a block stops before all 50 seeds.

The regression tests check that optional SLPS state returns the identical solution and its exact linear system, that LLC raw/normalized/rotation/labels/objective agree, and that all required old settings are present under both k values. These checks are implementation validation, not benchmark performance results.
