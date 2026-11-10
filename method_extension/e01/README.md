# E01: edge recurrence on the fusion graph

`EdgeRecurrenceSSC` keeps the original spectral anchor \(F\).
Ten isotropic Gaussian perturbations of \(F\), relative scale 0.02 and
seed 20260311, define \(p_{ij}\), the fraction of union-neighbor graphs
containing an undirected edge. Fusion weights become
\(W'_{ij}=W_{ij}p_{ij}^{\beta}\), with fixed \(\beta=1\), before E8
shrinkage. Only \(W\) changes.

At zero perturbation scale, the repeated graphs recover the original
support, giving \(W'=W\) and the corresponding E8 control within numerical
tolerance. Recurrence is not a class-label oracle, and stability does not
guarantee useful edges. Parameters are not chosen by test ACC.

See the [adaptation index](../README.md), [methods](../../docs/methods.md),
[theory](../../docs/theory.md) and [results](../../docs/results.md).
