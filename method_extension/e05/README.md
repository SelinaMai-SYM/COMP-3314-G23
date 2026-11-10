# E05: input-space and embedding-space relations

`CrossSpaceSSC` distinguishes the control affinity \(W_F\) on the
spectral anchor from \(W_X\), constructed by the same neighbor rule on
input features.

**E05-fuse** uses \(0.5W_F+0.5W_X\).
**E05-bilateral** retains a \(W_F\) edge only when the input-space graph
also contains that edge. The mixture coefficient is fixed.

Input-space similarity is not assumed to identify the class correctly,
particularly under illumination changes. The two variants remain
separately named, and neither graph agreement nor reduced support proves
a clustering improvement.

See the [adaptation index](../README.md),
[methods](../../docs/methods.md), [results](../../docs/results.md)
and [reproducibility](../../docs/reproducibility.md).
