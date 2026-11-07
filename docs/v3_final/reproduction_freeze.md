# Reproduction freeze

The executable v3 reconstruction is frozen as `REPRODUCTION_FROZEN_V3`.
This round does not rerun the historical trial grid and does not change LLC Procrustes, parameter forwarding, LDA-Kmeans, SLPS, or the E8/E13 split.

Configuration rows were read from `results/v3_reproduction/all_configurations.csv`.
Source commits present on those rows: 962e6d51b9b7b171d0efd283796c1258ab72d2a8, f8ef02101e2d389bbe9a706b68fc5b79ffcc626c.
Cells with a frozen execution status other than a hard block: 32 of 72.

Primary SSC is gamma=1. The gamma=1000 USPS point remains a sensitivity row.
Y0 remains the locked YaleB input. Y1--Y3 are diagnostics.
New extensions use separate method ids X1--X5.
