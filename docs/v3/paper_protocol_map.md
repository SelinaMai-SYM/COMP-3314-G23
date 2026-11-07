# Paper protocol map

Source PDF checked for this campaign: AAAI 2015, 7 pages, Chang, Nie, Ma, Yang, Zhou, *A Convex Formulation for Spectral Shrunk Clustering*. Tables 1 and 2 were read from that PDF. Printed means and SDs are in `configs/v3/paper_reference.yaml`.

| Requirement | Source | Implementation | Config key | Test | Status |
| --- | --- | --- | --- | --- | --- |
| k = 5 for spectral methods | Chang et al., experimental setting | `SpectralGraphConfig.k` | `spectral_k` | `test_spectral_pipeline.py` | Used for SC, SSC, PCA-SC |
| gamma in {1e-6, 1e-3, 1, 1e3, 1e6} | Chang et al. comparison grid | SSC tradeoff only | `ssc_gamma` | solver tests | Not reused as LLC bandwidth or ridge |
| 50 repeats and a mean ± SD | Tables 1--2 | P1 random Lloyd, sample SD | `n_runs: 50` | `test_protocol_selection.py` | SD is not attached to the selected run |
| Best objective language | Paper text plus tables that also print SD | P2 min inertia inside one batch | `selection_rule: min_inertia` | protocol test | Separate from P1 |
| ACC Hungarian, NMI geometric | Eqs. (19)--(21) | `benchmarks.metrics` | — | `test_metrics.py` | Same prediction vector |
| PCA/LDA dimension 10--150 | Experimental range | Grid step 10 | `pca_dimensions` | rank recorded as INFEASIBLE | Step 10 is our assumption. Classical LDA stays at K-1 |
| LLC discretization | Wu and Schölkopf; Yu and Shi | Procrustes `Vt.T @ U.T` | `llc_ridge`, `llc_kernel_bandwidth` | `test_llc_procrustes.py` | Not replaced by K-means |
| SLPS | Hou et al. 2013 experiments | One-shot Eq. 18--19, k=7, local scaling | `slps_alpha` | `baselines/spls/test_spls.py` | Alpha/dimension selection in the source paper is not a stated label-blind rule |
| LDA-SC | Name only in Chang et al. | Not run under this name | — | coverage test | `BLOCKED_METHOD` |
| YaleB 2414 × 38 × 32×32 | Paper dataset paragraph | dengcai32 and cropped2414, both kept | `yaleb_diagnostics.yaml` | loaders | Y0 is locked. Y1--Y3 are diagnostics |

Ten disjoint batches use seeds `50*b .. 50*b+49` for reference configs only. That batch design is ours, not a claim about the authors.

Labels do not choose seeds, gamma, dimension, YaleB preprocessing, or which SSC variant is "the" result.
