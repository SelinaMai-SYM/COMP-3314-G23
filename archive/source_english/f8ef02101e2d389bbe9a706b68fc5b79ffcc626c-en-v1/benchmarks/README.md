# Benchmark datasets

> English editorial replacement of the frozen historical source snapshot.
> The recovery statuses below apply to the dated investigation, not subsequent
> candidate experiments. See the current submission refresh for later work.

This directory contains the datasets, loaders and protocol for Chang et al.,
*A Convex Formulation for Spectral Shrunk Clustering* (AAAI 2015). Synthetic data
are never substituted for the eight named real datasets. Each dataset has its
own package: `ar`, `jaffe`, `orl`, `umist`, `binalpha`, `msra50`, `yaleb` and
`usps`. Shared ACC/NMI functions are in `metrics`; paper statements and explicit
reconstruction assumptions are in `protocols`.

Raw images and archives belong in the corresponding ignored `data` directory.
JAFFE prohibits redistribution; Extended Yale B and AT&T/ORL restrict public
redistribution. Their sources, hashes and licensing information are recorded in
package manifests. In the historical checkout, `python scripts/download_datasets.py`
acquired permitted sources and skipped files whose hashes already matched.
JAFFE's official Zenodo URL returned curl HTTP 403 on 2026-10-20; the saved file
came from that same URL and its SHA256 is recorded. No image archive is committed.

```python
from benchmarks import DatasetUnavailable, load_dataset
X, y, metadata = load_dataset("ORL")
```

Features are float64 `(n,d)` arrays and labels int64. Unavailable strict datasets
raise `DatasetUnavailable`. Image preparation consists of grayscale conversion,
declared bilinear resizing, vectorization and pixel scaling, without augmentation
or neural embeddings. Binary Alphadigits and USPS retain their documented native
scales. The ORL default remains Olivetti 64x64 to 32x32; YaleB remains Deng Cai's
32x32 matrix. Other source versions require explicit `version` arguments.
BinAlpha's `letters26x30_seed0` is an explicit candidate, while its default
strict paper endpoint remains unavailable.

| Dataset | Historical source status | Rows/classes | Prepared features | Qualification |
|---|---|---:|---:|---|
| ORL | approximate default | 400/40 | 1024 | Figshare 5976027, native Olivetti64; explicit AT&T92 source separate |
| JAFFE | verified source | 213/10 | 676 | Zenodo14974867, noncommercial research; no redistribution |
| YaleB | approximate default | 2414/38 | 1024 | Deng Cai32; explicit cropped2414 is not claimed pixel-identical |
| USPS | verified source | 9298/10 | 256 | LIBSVM train/test concatenation, native16x16 |
| AR | unavailable strict subset | unverified | unverified | Official access requires an application/password; 840/120 indices unknown |
| UMIST | unavailable strict564 | auxiliary1012/575 sources | version-specific | Wayback/Figshare source versions differ from the stated564 |
| BinAlpha | unavailable strict identity | unverified | unverified | Explicit26x30 candidate is not identified as the historical set |
| MSRA50 | unavailable | unverified | unverified | No1799-row,12-class source obtained in this historical round |

Exact source SHA256 values and legal qualifications are in the package READMEs
and manifests. Paper-stated counts were not reported as locally verified counts
where no corresponding sample set had been obtained. ORL64 is not asserted to
be the same pixel source as AT&T92. The paper's 50-repetition/best-objective/SD
hierarchy remains ambiguous; bandwidth, G initialization, K-means `n_init` and
the dimension-grid step are not fully specified. Assumptions remain labelled.

See `docs/repair_round1_dataset_recovery.md`, `docs/round2_source_of_truth.md`,
`docs/round2_missing_resources.md`, `docs/resource_acquisition_matrix.md` and
`docs/task1_resource_completion.md` in the corresponding historical project.
