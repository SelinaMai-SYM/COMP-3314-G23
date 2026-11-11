# Results and interpretation

The central question is whether SSC shrinkage improves the final partition
beyond an appropriately matched spectral-clustering baseline. The results
separate historical paper reconstruction, source/subset sensitivity, numerical
optimization and graph interventions. The [methods](methods.md) and
[experimental protocol](experimental_protocol.md) define each comparison.

ACC and NMI are percentages. Mean ± sample SD describes the same complete
50-seed configuration; differences are percentage points. A native-best
assignment is a different endpoint and has no across-run SD. Retrospective
paper matching and capability selection use labels after fitting; they are
neither unsupervised selection rules nor unseen-data estimates.

## Paper reconstruction and source sensitivity

All 72 method/benchmark targets in the paper's two tables have verified ACC/NMI
means and SDs. Historical scalar measurements retain their source and method
restrictions. New baseline or subset measurements do not silently replace an
unavailable historical method. Joint matching minimizes maximum ACC/NMI
discrepancy, then their mean discrepancy, using one complete configuration.

The [historical selection comparison](../results/submission_refresh/historical_selection_changes.csv) preserves the former ACC-only choices and both metrics from each configuration. Joint mean-endpoint matching changes 16 historical method/benchmark choices, including three SSC choices; it changes display selection rather than the underlying trials.

The [combined benchmark tables](../results/submission_refresh/per_benchmark/)
contain historical and newly measured endpoints for
[AR](../results/submission_refresh/per_benchmark/AR.md),
[JAFFE](../results/submission_refresh/per_benchmark/JAFFE.md),
[ORL](../results/submission_refresh/per_benchmark/ORL.md),
[UMIST](../results/submission_refresh/per_benchmark/UMIST.md),
[BinAlpha](../results/submission_refresh/per_benchmark/BinAlpha.md),
[MSRA50](../results/submission_refresh/per_benchmark/MSRA50.md),
[YaleB](../results/submission_refresh/per_benchmark/YaleB.md) and
[USPS](../results/submission_refresh/per_benchmark/USPS.md).

<!-- BEGIN SUBSET RESULTS -->

### Final source/subset results

The frozen release contains 74,436 complete physical SSC configurations and 3,721,800 scalar rounding trials. The catalogue also retains aliases and unevaluated hypotheses; a complete configuration requires all 50 declared seeds. Source/subset coverage is recorded in the [configuration coverage](../results/subset_search/execution_coverage.csv) and [fixed-protocol distributions](../results/subset_search/fixed_protocol_family_distributions.csv).

The [locked matches](../results/subset_search/closest_matches.csv) keep compatible and adapted pools, mean endpoints and native-best endpoints separate. Additional rounding completed for 18 of 18 locked winners, using the first unused 50-seed block at or above 1,000,000 without reselection. See [confirmation](../results/subset_search/rounding_confirmation.csv). These comparisons measure conditional rounding stability on the same fixed samples and representations; they do not identify historical membership or estimate unseen-data generalization.

<!-- END SUBSET RESULTS -->

Exact AR/UMIST/BinAlpha historical membership remains unresolved. The available
1,799-row MSRA matrix is native 16×16, whereas the paper describes 32×32 input.
YaleB cropped2414 and DengCai32 are distinct source sensitivities of one
benchmark. A closer table match does not resolve these identities.

## Numerical accuracy does not imply clustering gains

On one fixed current USPS F/W pair, the additional gamma-1 solve reaches a
relative primal–dual gap of 9.9996e-6 and satisfies the capacity tolerance. Its
ACC/NMI are 65.564 ± 2.520 / 80.228 ± 2.343, versus same-F SC's
65.597 ± 1.867 / 80.315 ± 2.128: changes of −0.033/−0.086 pp. Accurate solution
of this convex target therefore supplies no useful clustering improvement in
this setting.

The gamma-1000 numerical attempt remains uncertified at gap 0.342. Its fused
saved point has poor clustering, but this does not prove that the mathematical
optimum collapses. Historical-style IRLS completion, iterate stopping,
primal–dual certification and output identity remain separate. See the
[USPS numerical evaluations](../results/submission_refresh/usps_solver_evaluation.csv),
[additional-solve audit](../results/submission_refresh/usps_continuation_audit.csv)
and [additional-solve evaluations](../results/submission_refresh/usps_continuation_evaluation.csv).

## Representation and graph mechanisms

For fixed F, certified gamma-1 SSC changes ACC/NMI by +0.155/+0.014 pp on ORL
and −0.270/−0.276 pp on YaleB. The shrinkage is active in both cases. Cross-class
edges carry 4.6% of ORL W mass but 70.2% of YaleB W mass. YaleB's edge-length
AUROC is 0.380, so erroneous edges are not generally identified by being longer.
Upstream A contamination and shrinkage W contamination are different quantities.

Row normalization alone increases SC ACC by 1.850/4.016 pp on ORL/YaleB.
Angular-graph shrinkage at gamma 1 adds only 0.170/0.314 pp above that stronger
U-SC baseline. This distinguishes representation changes from extra shrinkage
benefits.

At the fixed 15%-addition/gamma-1000 oracle comparison, ORL completion improves
ACC by 10.415 pp over deletion and 24.863 pp over fixed oracle deletion plus
mean blind additions, while satisfying the NMI, fragmentation and conditional
interval criteria. YaleB's large raw gains remain unqualified because the
required solves are uncertified. The oracle uses labels and diagnoses graph
information; it is not an unsupervised algorithm result. Full evidence appears
in the [graph results](../results/submission_refresh/extension_results.csv),
[casebooks](../results/submission_refresh/casebook_summary.csv) and
[fixed-criterion record](../results/submission_refresh/extension_gate.json).


## Baseline and negative findings

The pinned ClustPy implementation makes no successful LDA update in any of the
50 ORL/JAFFE fits, producing explicit PCA–K-means degeneracies. This is an
implementation observation, not a theorem about LDA-Kmeans. Existing-project
limits 100 and 300 return identical per-seed ACC/NMI on all five tested sources.
The separately named ridge LDA-to-SC adaptation improves both means over raw
and PCA-p0 SC only on YaleB, and has capped YaleB fits. It does not recover the
paper's exact historical LDA-SC method.

Paired SLPS k=5/k=7 effects depend on source and alpha; k=7 lowers both means
for every primary ORL setting. Native-resolution MSRA PCA/LLC comparisons retain
all rows. The dense LLC eigensolver is identified separately from the
unsuccessful sparse ARPACK attempt. See the
[baseline comparison](../results/submission_refresh/baseline_diagnostics.csv).

Historical capped-fusion examples show damage avoidance and initialization
dependence, rather than a new penalty or general clustering improvement.
The five-point global objectives are 8 for linear fusion and 3 for capped
fusion; the local capped algorithm can retain objective 8 from the SSC start.
In an easy imbalanced-bridge synthetic setting, several controls avoid damage
while SC is already perfect. The [report appendix](../report/Group_23.pdf)
gives the mathematical scope and prior-art citations.

The supported conclusion is conditional: solver precision, representation
normalization, graph structure and rounding must be assessed separately.
Neither numerical closeness to a paper nor an optimal refinement objective
establishes a better clustering method. See [scientific limitations](limitations.md).
