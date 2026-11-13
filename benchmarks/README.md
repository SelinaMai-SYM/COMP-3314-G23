# Benchmark datasets

This directory provides loaders, source manifests and preparation conventions
for the eight benchmarks in Chang et al., *A Convex Formulation for Spectral
Shrunk Clustering* (AAAI 2015). Synthetic data are separate examples and never
substitute for a named benchmark.

The [data guide](../docs/data.md), [source inventory](../results/submission_refresh/dataset_inventory.csv)
and [experimental protocol](../docs/experimental_protocol.md) distinguish
verified source bytes from historical sample identity. Measured comparisons are
in [results](../docs/results.md). Reproducible candidate subsets do not establish
which rows the paper's authors used.

## Data root and loading

Keep provider archives and prepared images in an independent data root, with
subdirectories such as `orl/data`, `jaffe/data` and `usps/data`. Command-line
`--data-root` takes precedence over `COMP3314_DATA_ROOT`, the ignored
`local/data_root.txt` pointer, and checkout-local `benchmarks/`. A direct loader's
`root` argument instead names that dataset's **data directory**:

```python
from pathlib import Path
from benchmarks import load_dataset

root = Path("local/data")
X, y, metadata = load_dataset("ORL", root=root / "orl/data", version="att92")
```

`X` is a float64 sample-by-feature matrix and `y` contains integer class labels.
Unavailable strict datasets raise `DatasetUnavailable`; an explicit candidate
version is never silently returned under a strict historical name. No neural
features or augmentation are used. Image preparation is source-specific;
Binary Alphadigits keeps binary values and USPS keeps its native `[-1,1]` range.

## Sources and explicit versions

| Benchmark | Explicit version | Samples / classes | Features | Scientific qualification |
|---|---|---:|---:|---|
| [ORL](orl/README.md) | `att92`; default `olivetti` is separate | 400 / 40 | 1024 | Native 112×92 PGM and 64×64 MAT are distinct preparations |
| [JAFFE](jaffe/README.md) | `zenodo` | 213 / 10 | 676 | Official source; bilinear 26×26 interpolation is explicit |
| [YaleB](yaleb/README.md) | `dengcai32`, `cropped2414` and resize alternatives | 2414 / 38 | 1024 | Source and interpolation alternatives remain separate |
| [USPS](usps/README.md) | `libsvm` | 9298 / 10 | 256 | Full training file followed by full test file |
| [AR](ar/README.md) | `lzuf_superset1680`; manifest-defined candidates | 1680 / 120 parent; 840 / 120 candidates | 1024 | Historical 840-image membership and pixel geometry unverified |
| [UMIST](umist/README.md) | `lzuf574`, `precropped575`, `roweis575`, `figshare575`, `zenodo3634017` | Source-specific | Source-specific | Deduplication/omission hypotheses do not identify historical membership |
| [BinAlpha](binalpha/README.md) | `binaryalphadigs36`, `letters26x30_seed0` | 1404 / 36 parent; 780 / 26 candidate | 320 | Parent identity and paper's selected indices unverified |
| [MSRA](msra50/README.md) | `MSRA25_EBSA_16x16` | 1799 / 12 | 256 | Native16 adaptation; historical native32 source unresolved |

Default ORL means Olivetti and default YaleB means DengCai32. Strict AR, UMIST,
BinAlpha and MSRA50 defaults reject inferred substitutes. Use the exact version
and sample manifest stated by an experiment. The [candidate catalogue](../configs/subset_search/candidate_catalogue.json)
records selected/excluded original rows, quotas, ordering and aliases. Each
changed subset rebuilds its own graphs and representation.

## Preparation and terms

Follow [deterministic data preparation](../docs/data.md#deterministic-preparation)
for ORL and YaleB; the shared preparation command verifies the archive identity
and creates the three declared interpolation versions. MSRA has a pinned
retrieval command. Each dataset README lists its expected paths, hashes and
source-specific transformations.

Provider conditions remain separate from the project's software license. JAFFE
prohibits redistribution; YaleB restricts redistribution of its images; AR has
its own access/use conditions. Other mirrors do not override original terms.
Raw archives and private matrices are excluded from Git. Preserve attribution
and verify expected file hashes before loading an acquired source.

The [paper protocol map](protocols/original_paper.yaml) separates explicit paper
statements from unspecified settings. In particular, source membership,
bandwidth, initialization and the reported SD hierarchy cannot all be inferred
from a close ACC/NMI match.
