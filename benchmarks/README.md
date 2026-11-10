# Benchmark datasets

This directory contains loaders, source manifests and the protocol for the eight
datasets in Chang et al., *A Convex Formulation for Spectral Shrunk Clustering*
(AAAI 2015). Synthetic data are used only for implementation checks. They never
stand in for AR, JAFFE, ORL, UMIST, BinAlpha, MSRA50, YaleB or USPS.

**Current status, 2026-11-10:** the
[submission refresh](../docs/submission_refresh/source_recovery.md) adds explicit
candidate subsets and a native 16x16 MSRA source. These are reproducible
reconstructions, with historical identity qualified separately. The older notes
below describe source recovery, rather than current experiment completion.
See the [candidate catalogue](../configs/subset_search/candidate_catalogue.json)
and current [campaign records](../results/subset_search/) for measured coverage.

Raw images and archives belong outside the checkout in an independent data root.
The corresponding `data/` directories are ignored by Git. JAFFE prohibits
redistribution; Extended Yale B and AT&T/ORL also restrict public redistribution.
Source hashes, licensing information and preprocessing are recorded in each
package's manifests. Download or copy the authorized sources using the current
[data setup instructions](../docs/final/data_setup.md); historical instructions
that mentioned a `v1` checkout are superseded. A versioned Python module name
does not require another branch.

## Loading

```python
from pathlib import Path
from benchmarks import DatasetUnavailable, load_dataset

root = Path("/path/to/benchmarks")
X, y, metadata = load_dataset("ORL", root=root / "orl/data", version="att92")
```

`X` is a float64 matrix of shape `(n,d)` and `y` contains integer labels.
Unavailable strict datasets raise `DatasetUnavailable`. Explicit `root` takes
priority over `COMP3314_DATA_ROOT`, the ignored local pointer and checkout data.
Most image loaders use grayscale pixels, declared resizing, vectorization and
scaling. Binary Alphadigits retains 0/1 values; USPS retains its native [-1,1]
range. There is no augmentation or learned neural representation.

## Sources and versions

| Dataset | Available explicit version | Samples/classes | Features | Qualification |
|---|---|---:|---:|---|
| ORL | `att92`; default `olivetti` is separate | 400/40 | 1024 | AT&T native 92x112 and Olivetti native 64x64 are distinct preparation sources |
| JAFFE | `zenodo` | 213/10 | 676 | Official release; bilinear interpolation is our choice |
| YaleB | `dengcai32`, `cropped2414` and resize alternatives | 2414/38 | 1024 | Source and interpolation uncertainty remain separate |
| USPS | `libsvm` | 9298/10 | 256 | All 7291 training rows followed by all 2007 test rows |
| AR | `lzuf_superset1680`; explicit candidate manifests | 1680/120 parent; 840/120 candidates | 1024 | Strict original 840-image identity remains unverified |
| UMIST | `lzuf574`, `precropped575`, `roweis575`, `figshare575`, `zenodo3634017` | Version-specific | Version-specific | Dedup564 and omission candidates do not prove historical membership |
| BinAlpha | `binaryalphadigs36`, `letters26x30_seed0` | 1404/36 parent; 780/26 candidate | 320 | Historical parent and sample indices unverified |
| MSRA | `MSRA25_EBSA_16x16` | 1799/12 | 256 | Native 16x16 adapted resolution; strict MSRA50 remains unavailable |

The default ORL loader still returns the Olivetti preparation and the default
YaleB loader still returns Deng Cai's matrix. Use explicit versions for other
sources. Strict AR, UMIST, BinAlpha and MSRA50 defaults do not silently return
inferred substitutes.

Each package README gives full file hashes, identity and licensing details.
Earlier source investigations remain in
[Round 1](../docs/repair_round1_dataset_recovery.md),
[Round 2](../docs/round2_source_of_truth.md),
[the request log](../docs/round2_missing_resources.md),
[the acquisition matrix](../docs/resource_acquisition_matrix.md) and
[Task 1](../docs/task1_resource_completion.md).
The [paper protocol](protocols/original_paper.yaml) separates explicit statements
from assumptions. The paper's combination of “50 repetitions,” “best objective”
and reported mean/SD remains ambiguous. Bandwidth, G initialization,
K-means `n_init` and the dimension-grid step are not fully specified by the paper.
