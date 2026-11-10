# E02: positive fidelity weights

`ReliabilityWeightedSSC` uses the objective

\[
\sum_i\alpha_i\|g_i-f_i\|_2+
2\gamma\sum_e w_e\|g_i-g_j\|_2.
\]

The reciprocal-neighbor fraction \(m_i\) in \(F\) defines
\(\alpha_i=0.5+1.5m_i\in[0.5,2]\). These weights are frozen before
IRLS; \(F\) and \(W\) retain the control construction.

Uniform \(\alpha=1\) recovers the E8 system. Nonuniform fidelity changes
the target, so its objective value is not directly comparable to original
Equation 8. Reciprocal neighbors are a label-free reliability heuristic,
not a guarantee of correct membership.

See the [adaptation index](../README.md), [theory](../../docs/theory.md),
[results](../../docs/results.md) and
[reproducibility](../../docs/reproducibility.md).
