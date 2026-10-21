# Reliability-aware SSC (mutual kNN shrinkage weights)

This package is the one planned extension of Chang et al., AAAI 2015. It is
**not** original SSC. Original SSC lives in `SSC_method/` and is not modified
here.

## What changes

1. Compute the spectral embedding `F` exactly as original SSC (union kNN on
   the features, symmetric normalized Laplacian, `c` smallest eigenvectors).
2. On `F`, build a **mutual** kNN Gaussian affinity `W` (keep an edge only
   when each embedded point is among the other's `k` neighbors).
3. Freeze `W`. Run the original IRLS solver (`SSC_method.optimizer.shrink_embedding`),
   which solves Equation (13), not Algorithm 1 line 10.
4. Cluster the rows of `G` with K-means.

Ablation **A0** is original SSC (union kNN `W`). Ablation **A1** is this
module (mutual kNN `W` only). The optimizer, `G_0 = F`, bandwidth rule, and
metrics do not change.

## What this is not

Chi and Lange (2015) already use **union** kNN Gaussian weights, frozen
before convex clustering. Mutual kNN itself is older still (Brito et al.
1997; von Luxburg 2007). The combination "mutual kNN support on SSC's
shrinkage `W`" was not found in the literature check
(`docs/literature_review.md`). Call it an adaptation, not a new convexity
theorem. Equation (8) remains convex for the same reason whenever `W` is
nonnegative and held fixed.

Bandwidth: if omitted, `delta^2` is the median of positive *directed* kNN
squared distances, computed before the mutual filter, so the scale matches
original SSC and the only change is which edges remain.

## Round 2 result (JAFFE, n=50, Category C)

Same \(F\) as union E8. Mutual E8 ACC **68.4±11.2** vs union E8 **68.4±11.1**
(410 vs 655 edges; 20 vs 9 components). Negative: no ACC gain.
Run: `20261021_161924__ROUND2__JAFFE__EXT_JAFFE_MUTUAL_KNN__45fd1c1f`.
Union control: `20261021_161558__ROUND2__JAFFE__D12_JAFFE_E8__b643eae7`.
