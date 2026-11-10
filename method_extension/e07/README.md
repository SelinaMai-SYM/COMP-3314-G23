# E07: rounding one fixed representation

`cluster_fixed_representation` changes neither \(F\), \(W\), nor \(G\).
It accepts an explicit seed list. The declared comparison uses seeds 0–49
for the following partitions on the same saved representation:

1. RANDOM Lloyd, one start per seed, seeds 0–49.
2. sklearn greedy K-means++, one start per seed, seeds 0–49.
3. The single RANDOM assignment with minimum K-means inertia.
4. Consensus after aligning RANDOM partitions to that minimum-inertia
   assignment, with smallest-label tie breaking.

Inertia, not ACC, selects the third partition and the consensus reference.
The third and fourth endpoints contain one assignment each, so they receive
no across-run SD. They do not replace the 50-seed mean endpoint. Keeping
rounding fixed is necessary when attributing a gain to shrinkage.

See the [adaptation index](../README.md),
[experimental protocol](../../docs/experimental_protocol.md),
[results](../../docs/results.md) and
[reproducibility](../../docs/reproducibility.md).
