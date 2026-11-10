# E03: placement of a local-scale affinity

`LocalScaleSSC` uses an established Zelnik-Manor local-scale affinity
at explicitly different points in the pipeline:

- **E03-A:** local scaling defines upstream \(A\); the resulting \(F\)
  and matched SC change. \(W\) retains the median-bandwidth rule.
- **E03-W:** the control \(F\) is fixed, and only \(W\) uses local scaling.
- **E03-AW:** both graph constructions use local scaling.

The variants are separate configurations, not three newly invented
affinity methods. E03-W permits a fixed-representation graph contrast;
E03-A requires its own matched SC baseline. A change in \(F\) cannot be
credited solely to fusion.

See the [adaptation index](../README.md),
[methods](../../docs/methods.md), [results](../../docs/results.md)
and [reproducibility](../../docs/reproducibility.md).
