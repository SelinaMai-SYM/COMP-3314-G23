# Protocol map

| Choice | Paper specifies | Unresolved or our choice | Frozen sensitivity |
|---|---|---|---|
| Samples | Benchmark counts, class counts and stated image sizes | Original indices and several parent releases unavailable | Predeclared source/subset catalogue; strict identity statuses retained |
| Input affinity A | Gaussian kNN, k=5 for spectral methods | Union symmetrization; median positive directed-neighbor squared-distance bandwidth | Yale input normalization/source/resize factors kept separate |
| Embedding F | Smallest normalized-Laplacian eigenspace | Deterministic eigensolver start and column-sign convention | Y0--Y3; no parent embedding row reuse |
| Shrinkage W | Neighbors in spectral space | Same k=5, bandwidth and union conventions | Diagnostic angular graph independent of subset matching |
| Convex target | Equation 8 | E13 printed update has effective gamma=nominal/2 | Both variants and published five-gamma grid |
| Optimization | IRLS update | 300-step cap, epsilon1e-8, relative-iterate tolerance1e-6, initial zero-residual median floor | Finite historical-style and certified solver audits kept separate |
| Rounding | 50 random initializations; best native objective described | One Lloyd start, max300, tolerance1e-4; separate random/vanilla++/greedy++ | Mean/sample SD versus native best-of50, never mixed |
| NMI | Geometric entropy normalization | Explicit sklearn average_method=geometric | Permutation and degenerate-label tests |
| SLPS | SSC says k=5; Hou source uses k=7 | One-shot formulation, local scaling and PCA dimension | Paired k5/k7, alpha .2/.5/.8, dimensions30/70/110 |
| LDA | Named methods and dimension search | Exact historical LDA-SC algorithm remains unresolved | Existing30/100/300, pinned reference and separately named ridge adaptation |

The joint selection minimizes absolute ACC/NMI discrepancy to the paper. It uses labels and paper targets retrospectively. Different selected cells are a descriptive patchwork, not one uniform label-free algorithm. Published-grid gamma values are legitimate choices and do not count as explicit paper deviations. The paper does not resolve how the SD was formed after native-objective selection; our endpoints do not claim to resolve that ambiguity.
