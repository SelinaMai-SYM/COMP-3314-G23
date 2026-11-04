# What the 2015 paper states about the final clustering step

Chang et al. (AAAI 2015) evaluate spectral clustering and spectral shrunk clustering with accuracy and normalized mutual information. The published tables report a mean and a standard deviation. The paper also refers to choosing a repeated run by the clustering objective.

Those two statements do not identify a single modern implementation:

- Uniform random Lloyd, summarized by the mean and sample SD of 50 runs (our P1).
- The same 50 runs, summarized by the one partition with minimum K-means inertia (our P2). One selected run does not have a within-batch SD.
- scikit-learn's greedy k-means++ (`SKLEARN_GREEDY_KMEANSPP`), mean of 50 runs (our P3).
- The minimum-inertia run inside that same greedy batch (our P4).

A one-candidate k-means++ seeding (`VANILLA_KMEANSPP`, `n_local_trials=1`) is recorded separately. It is not merged into P3 or P4.

The paper does not release code that would decide among these readings. A higher accuracy on one dataset is not evidence that the authors used that initializer. The informative comparison is whether SC and SSC, under the same protocol, reproduce the published SC-to-SSC gap on more than one benchmark.

Gamma is not fixed at 1 for every dataset in the paper. The grid `{1e-6, 1e-3, 1, 1e3, 1e6}` is therefore reported in full. The maximum labeled accuracy on that grid is named `ORACLE_BEST_TEST_ACC` and is not a fair unsupervised result.

Published YaleB is a counterexample to "SSC improves both scores": SSC accuracy is higher than SC accuracy, while SSC NMI is lower than SC NMI. The reference values are in `configs/paper_2015_reference.yaml`.
