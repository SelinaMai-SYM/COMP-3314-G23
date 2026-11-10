# E08: recurrence with weighted fidelity

`CombinedRecurrenceReliabilitySSC` combines the fixed recurrence
probabilities of [E01](../e01/README.md) and the positive fidelity weights
of [E02](../e02/README.md). Both are computed from \(F\) before fitting.

The weighted E8 solve is compared with SSC, E01 and E02 on the same anchor.
Its modified fidelity means raw objective values are not comparable to
original Equation 8 as a method ranking. A combined score cannot isolate
the contribution of either component without the separate controls.

See the [adaptation index](../README.md),
[theory](../../docs/theory.md), [results](../../docs/results.md)
and [reproducibility](../../docs/reproducibility.md).
