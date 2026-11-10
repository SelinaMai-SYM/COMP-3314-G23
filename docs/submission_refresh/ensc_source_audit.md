# EnSC formulation and source attribution

The graph adapter follows Chong You et al., *Oracle Based Active Set Algorithm for Scalable Elastic Net Subspace Clustering* (CVPR 2016), using source revision `55e330e38415951f140e74739c869306acdb7a98`. Its [MIT notice](../../method_extension/submission_refresh/third_party/ensc/LICENSE) and pinned source are retained.

The independent coordinate-descent backend solves the true elastic-net objective at tau 0.95; tau 1 is the separate sparse-only control. Coefficient scaling, self-exclusion, active-support behavior, top-coefficient truncation, row normalization and symmetrization follow the declared conventions in [methods](../methods.md). Independent small convex references verify the implemented objective and scaling. The [source-bound verification record](../../results/submission_refresh/ensc_backend_validation.json) qualifies that scope. The original SPAMS backend was inspected rather than used for the reported benchmark fits.

Small-reference agreement does not establish coefficient accuracy for every benchmark row. Recorded KKT residuals, source stopping and downstream SSC primal–dual gaps are distinct qualifications. See [results](../results.md), [limitations](../limitations.md) and [reproducibility](../reproducibility.md). This is an adaptation of an existing method, with no claim to have invented elastic-net clustering.
