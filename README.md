# Spectral Shrunk Clustering

A Python implementation and experimental study of **Spectral Shrunk Clustering (SSC)**: refining a spectral embedding before assigning clusters. The project reproduces the objective in [*A Convex Formulation for Spectral Shrunk Clustering*, Chang et al., AAAI 2015](https://doi.org/10.1609/aaai.v29i1.9606), compares clustering baselines, and evaluates graph and geometric refinements with numerical certificates.

This is an independent implementation by **Han Jiale, Lu Sinan, Mahatharadol Vie and Mai Sheung Ying**, Group 23, The University of Hong Kong, COMP3314 Machine Learning.

[Methods](docs/methods.md) · [Experiments](docs/experimental_protocol.md) · [Data](docs/data.md) · [Results](docs/results.md) · [Reproducibility](docs/reproducibility.md) · [Report](report/Group_23.pdf)

## Method

An input-space graph **A** defines the spectral coordinates **F**. A second graph **W**, built from F, defines which representations shrink together. K-means then clusters the refined coordinates **G**. With each undirected edge stored once, the original Equation 8 objective is

$$
\min_G\;\sum_i\|g_i-f_i\|_2+2\gamma\sum_{(i,j)}w_{ij}\|g_i-g_j\|_2.
$$

The library exposes both the E8 stationary system and the printed E13 system; E13 at nominal γ corresponds to E8 at γ/2. Historical IRLS results and primal–dual certified results have separate records.

The retained refinements examine relative stopping distances, tangent constraints, relative-neighbor corrections, and movement-controlled quadratic fusion. The edge-deletion study uses one frozen ridge-pilot signal at three alternative locations: **E7** changes graph weights, **E1_v3** allocates edge tolerances, and **E5_v2** allocates triangle-slack guards. These methods are evaluated independently. Their objectives and controls are described in the [method guide](docs/methods.md) and [edge-deletion formulation](docs/extension_round3/method_design.md).

The diagram illustrates the two graphs and the unsquared-fidelity E1–E3 comparisons:

![Two-graph SSC pipeline and independent unsquared refinements](docs/figures/ssc_two_graph_pipeline.svg)

## Installation

CPython **3.13.3** is the checked environment. Install the pinned scientific dependencies and the project in a virtual environment:

```bash
git clone --single-branch --branch main https://github.com/SelinaMai-SYM/COMP-3314-G23.git
cd COMP-3314-G23
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r environment/requirements.lock.txt
python -m pip install --no-deps --no-build-isolation -e .
```

The dependency file includes pytest and CVXPY for the independent convex reference checks. The core SSC estimator uses NumPy, SciPy and scikit-learn. [Report building](report/README.md) additionally requires TeX Live and Poppler.

## Quick start

This example uses only generated data:

```python
import numpy as np
from sklearn.datasets import make_blobs
from SSC_method import SpectralShrunkClustering

X, _ = make_blobs(n_samples=90, centers=3, n_features=4,
                  cluster_std=0.6, random_state=7)
model = SpectralShrunkClustering(
    n_clusters=3, gamma=1.0, k=5, variant="E8", max_iter=100,
    kmeans_n_init=1, kmeans_random_state=0,
)
labels = model.fit_predict(X)
print("labels:", labels.shape)
print("F:", model.embedding_.shape, "G:", model.shrunk_.shape)
print("clusters:", np.unique(labels))
```

`labels` contains one integer assignment per sample. `embedding_` and `shrunk_` each have shape `(90, 3)`. Run the corresponding file with `python examples/ssc_blobs.py`. See the [SSC API guide](SSC_method/README.md) for estimator options and stored diagnostics.

## Datasets

The experiments use **AR, JAFFE, ORL, UMIST, BinAlpha, MSRA, Extended Yale B and USPS**. [Data setup](docs/data.md) provides source links, download commands, directory layout, preprocessing and dataset-specific terms. Restricted images are supplied separately. Runners accept `--data-root`; the same root can be selected with `COMP3314_DATA_ROOT`.

Dataset versions are explicit. The available MSRA25 EBSA file has 1,799 rows at native 16×16 resolution and is an adapted proxy for the paper's unresolved MSRA50 input. YaleB cropped2414 and DengCai32 are separate sources. AR, UMIST and BinAlpha subset hypotheses retain their original row indices.

## Reproducing experiments

Run a small end-to-end numerical example without benchmark files:

```bash
python -m experiments.v3_reproduction smoke --dataset synthetic
```

For the main SSC grid, place provider files in `local/data` according to the data guide. Each run writes its own records under `local/ssc-runs`:

```bash
python -m experiments.v3_reproduction run-experiments \
  --config configs/v3/campaign.yaml --data-root "$PWD/local/data" \
  --output "$PWD/local/ssc-runs" --resume
```

Baseline comparisons, subset sensitivity, extension fitting and exact-input replay have separate commands in [reproducibility](docs/reproducibility.md). The [experiment protocol](docs/experimental_protocol.md) defines grids, eligibility, seeds and selection.

Rebuild the historical tables and the edge-deletion comparisons from committed measurements, without raw data or fitting:

```bash
python -m experiments.v3_reproduction rebuild-results \
  --release-manifest configs/final/release_manifest.json --output local/tables/historical
python -m experiments.extension_round3 rebuild \
  --release-manifest results/extension_round3/release_manifest.json \
  --output local/tables/edge-deletion --figures
python -m scripts.result_tables --output local/tables/overview.md
```

The last command generates the compact result table below. The [reproducibility guide](docs/reproducibility.md) also covers the joint 72-cell comparison, source/subset selections and the other retained refinement tables.

## Results

The edge-deletion comparisons use **retrospectively selected report cohorts**, including the adapted MSRA source. Parameters use a fixed normalized movement target of 0.10. These results describe those fixed cohorts; cohort selection used labels and published targets. ACC and NMI are percentages, changes are percentage points, and each configuration contains the same **50** rounding seeds with sample SD recorded in the full tables.

<!-- BEGIN GENERATED RESULTS -->

| Method | Qualified cohorts | ΔACC / ΔNMI vs QSSC | ΔACC / ΔNMI vs plain pilot |
|---|---:|---:|---:|
| E7 graph | 8/8 | -0.022 / +0.013 | +0.004 / -0.001 |
| E1_v3 tube | 6/8 | +0.157 / +0.358 | -0.123 / -0.068 |
| E5_v2 guard | 7/8 | +0.235 / +0.204 | +0.061 / +0.045 |

<!-- END GENERATED RESULTS -->

Available-case means use the same qualified cohort mask for both metrics. Only E7 has complete eight-cohort primary coverage; the other full macros remain unavailable. The native panel generates greedy K-means++ starts on each output. The companion panel reuses row indices generated on the anchor.

The complete E7 comparison gives a small ACC decrease relative to quadratic SSC. Selective tubes improve on QSSC on their available cohorts but lose both mean metrics to plain-pilot tubes under native rounding. Guards show a small partial-cohort gain; shuffled controls and cohort regressions limit attribution to edge-deletion correction. [Full results](results/extension_round3/summary.md), [both panels and all controls](results/extension_round3/paired_differences.csv), and [interpretation](docs/extension_round3/interpretation.md) retain the negative and unqualified outcomes.

The wider study includes the [paper/baseline comparisons](results/submission_refresh/per_benchmark/), [source/subset sensitivity](results/subset_search/closest_matches.csv), and [unsquared-fidelity refinements](docs/extension_verification_results.md). Fixed-reference, retrospective matches, mean endpoints and native-best endpoints remain separate.

## Repository structure

```text
COMP-3314-G23/
├── SSC_method/                # SSC estimator, graphs, embedding and IRLS
├── method_extension/          # Certified solvers and independent refinements
│   ├── next_round/            # Primal–dual SSC and fusion/geometry controls
│   ├── extension_verification/# Relative, tangent and neighbor objectives
│   ├── extension_round2/      # Movement-controlled quadratic refinements
│   └── extension_round3/      # Edge-deletion evidence and selective objectives
├── baselines/                 # K-means, SC, PCA, LDA, LLC and SLPS
├── benchmarks/                # Source-aware loaders, preparation and metrics
├── configs/                   # Experiment grids, cohort locks and manifests
├── experiments/               # Fitting, evaluation and scalar reconstruction
├── examples/                  # Small generated-data examples
├── results/                   # Measurements and generated scientific tables
├── docs/                      # Methods, data, protocols and interpretation
├── report/                    # LaTeX source, figures and technical report
├── scripts/                   # Dataset retrieval and result/figure generation
├── tests/                     # Numerical, metric and reproducibility checks
└── environment/               # Checked dependency versions
```

Internal module identifiers remain stable across the fitting and reconstruction interfaces. The [documentation index](docs/README.md) maps them to the scientific comparisons.

## Citation and license

The original method is:

> Xiaojun Chang, Feiping Nie, Zhigang Ma, Yi Yang and Xiaofang Zhou. **A Convex Formulation for Spectral Shrunk Clustering.** AAAI, 2015, pp. 2532–2538. [DOI](https://doi.org/10.1609/aaai.v29i1.9606).

The report and method documentation cite the external methods used, including Chambolle–Pock primal–dual optimization, Ding–Li LDA-Kmeans, SLPS and leverage-adjusted leave-one-out residuals. The instrumented ClustPy reference retains its original BSD-3-Clause notice. See [references](report/references.bib) and [third-party attribution](NOTICE.md).

Project code is distributed under the [MIT License](LICENSE). Dataset and third-party material terms apply separately.
