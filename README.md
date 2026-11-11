# Spectral Shrunk Clustering

Research software and a technical report on **Spectral Shrunk Clustering**
([Chang et al., AAAI 2015](https://doi.org/10.1609/aaai.v29i1.9606)). The project
studies whether refining a spectral representation improves clustering, and how
the answer depends on graph construction, numerical solution and data identity.

**Han Jiale · Lu Sinan · Mahatharadol Vie · Mai Sheung Ying**
Group 23, The University of Hong Kong — COMP3314 Machine Learning.

## What the project provides

- An array-based SSC implementation with explicit E8/E13 parameter conventions.
- Primal–dual solvers with objective gaps and capacity diagnostics.
- Spectral, PCA, LDA, LLC and SLPS baselines, plus separately named graph and
  fidelity adaptations, including an attributed EnSC affinity.
- Source-aware benchmark loaders, published ACC/NMI records and scalar-result
  reconstruction tools.
- A technical report, mathematical derivations and editable method figures.

## Two graphs, two roles

![The input graph A defines F; the shrinkage graph W refines F into G](docs/figures/ssc_two_graph_pipeline.svg)

The input affinity **A** determines the spectral representation **F**. A second
graph **W**, constructed from F, controls refinement into **G**. Matched spectral
clustering clusters F; SSC clusters G. Convex refinement and improved clustering
are distinct claims. The [methods](docs/methods.md) explain the objective,
parameter mapping and numerical qualifications.

## Install and use

Use Python 3.13 from the repository root:

```bash
git clone --single-branch --branch main https://github.com/SelinaMai-SYM/COMP-3314-G23.git
cd COMP-3314-G23
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r environment/requirements.lock.txt
```

For a numeric sample-by-feature matrix `X` and a chosen cluster count:

```python
from SSC_method import SpectralShrunkClustering

model = SpectralShrunkClustering(
    n_clusters=3, gamma=1.0, k=5, variant="E8", max_iter=300,
    kmeans_n_init=1, kmeans_random_state=0,
)
labels = model.fit_predict(X)
F, G = model.embedding_, model.shrunk_
```

This is an illustrative configuration. The [library guide](SSC_method/README.md)
documents its options; the [experimental protocol](docs/experimental_protocol.md)
defines the benchmark settings and statistical endpoints. Provider files and
independent data roots are described in [data setup](docs/data.md).

Reconstruct the published historical tables without image archives:

```bash
python -m experiments.v3_reproduction rebuild-results --release-manifest configs/final/release_manifest.json --output local/rebuilt_historical
```

## Report and results

Read the [technical report](report/Group_23.pdf), [results summary](docs/results.md)
and [benchmark comparisons](results/submission_refresh/per_benchmark/).
Both ACC and NMI remain attached to one configuration and statistical endpoint.
Closest paper matches are retrospective selections using labels and published
targets; they do not identify historical sample membership or provide label-free
parameter selection. Scientific restrictions and negative findings are retained
in [limitations](docs/limitations.md).

Final source/subset selections and additional-rounding outcomes are reported
in [the results summary](docs/results.md), with separate statistical endpoints,
eligibility pools and numerical qualifications. Scientific-archive availability is documented separately
in the [reproducibility guide](docs/reproducibility.md#verified-archive-and-regeneration).

See [theory](docs/theory.md) for derivations,
[reproducibility](docs/reproducibility.md) for release interfaces and
[report sources](report/README.md) for the preprint and figure build.

## License and attribution

Original project code is available under the [MIT License](LICENSE). See
[NOTICE.md](NOTICE.md) for third-party attribution.

Dataset and provider-material terms are separate from the software license.
Restricted image archives are not redistributed; source attribution and
conditions are retained in the [data documentation](docs/data.md).
