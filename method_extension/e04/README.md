# E04: degree normalization and a scale control

`DegreeNormalizedSSC` distinguishes two graph transformations.

**E04-degree** replaces
\(W_{ij}\) by \(W_{ij}/\sqrt{(d_i+\varepsilon)(d_j+\varepsilon)}\),
where \(d_i=\sum_jW_{ij}\) and \(\varepsilon=10^{-12}\).
On an irregular graph this changes relative edge strengths, not merely
one global regularization coefficient.

**E04-total** divides every stored weight by their total sum. This is
a global rescaling of \(W\), equivalent to rescaling gamma for the
same objective. It is a scale control, not a new selective mechanism.

See the [adaptation index](../README.md),
[theory](../../docs/theory.md), [results](../../docs/results.md)
and [reproducibility](../../docs/reproducibility.md).
