# Research findings - combined refresh

Execution snapshot: **10 November 2026, 12:19 UTC**. This is an execution-stage record. The final coverage, selected values and resource use must be read together; a completed execution is not proof of numerical reproduction. EnSC G4 is running. Final subset winners, isolated acceptance and publication remain outside this note's claims.

The frozen historical release supports a balanced joint ACC/NMI display selection. It changes several SC/SSC choices compared with ACC-only matching while preserving every underlying historical trial. Both means, both sample SDs and the complete configuration remain linked. This selection is retrospective and uses paper targets and labels.

The new native MSRA source is a 16-by-16, 1,799-row EBSA matrix. All duplicate rows remain. Its resolution and historical-identity status are separate: a good metric match cannot turn it into the unknown native 32-by-32 source. The Fast-CD public download remained rate limited in bounded requests; this does not prove permanent deletion or an authentication requirement.

The mandatory baseline block has **190 complete scalar endpoints**, each with
all 50 declared seeds. This endpoint count is separate from coverage declarations,
aliases, interrupted attempts and continuation records. Their successful scalar
rebuild checks do not establish historical dataset identity or turn a failed fit
into a successful baseline. The original sparse LLC failure remains recorded
beside its separately named dense repair.

The completed LDA block now covers ORL att92, JAFFE, YaleB cropped2414, full USPS
and native MSRA25 EBSA16. Each discussed configuration has all 50 external seeds;
the [baseline diagnostics](../../results/submission_refresh/baseline_diagnostics.csv)
preserve means, sample SDs, stopping counts and exact scalar source paths. These
source/settings comparisons do not establish historical dataset or LDA-SC
identity. Full details are in the [LDA audit](lda_audit.md).

For the existing LDA implementation, every seed's ACC/NMI pair at limit 100
matches its pair at limit 300 on all five sources. ORL, JAFFE and YaleB already
reach label stability within 30 updates. At 30, MSRA has one capped fit and USPS
has 38; raising the limit to 100 changes their mean ACC/NMI by +0.006/+0.020 pp
and -0.323/-0.363 pp respectively. More outer updates therefore do not supply a
general performance repair. YaleB's roughly 9.672% ACC / 13.416% NMI persists
across all three caps and cannot be attributed to the tested cap alone.

The pinned ClustPy reference has a different limitation on ORL and JAFFE: every
one of their 50 fits has zero successful LDA updates, with 15,000 and 625 recorded
`LinAlgError` updates respectively. ORL reaches the 300-update cap in all fits;
JAFFE stops under the source NMI rule despite failed LDA updates. These executions
are explicitly degenerate PCA/K-means behavior, not successful LDA learning.
MSRA16, USPS and YaleB instead execute successful updates without recorded
failures, so the same explanation must not be imposed on YaleB. All 250 benchmark
reference fits report consistent returned state. The source return-state defect
remains established by a separate cap regression fixture, not as an observed
benchmark inconsistency. Its scoped PCA seeding modification remains disclosed.

The PCA-preconditioned ridge LDA-Kmeans -> SC adaptation is separately named and
has complete matched raw SC, PCA_p0 SC and PCA_r SC controls. It improves both
means over raw/PCA_p0 SC on YaleB, reaching 35.848% ACC / 50.579% NMI, but loses
both metrics against those controls on each of ORL, JAFFE, USPS and MSRA16.
YaleB still has 32 capped fits at 300 updates; the other four sources reach
partition stability in all 50 fits. Direct learned-label clustering scores higher
than downstream SC on both metrics for every source, under their prescribed
ten-start inner versus one-start downstream rounding rules. This comparison is a
net pipeline observation, not an isolated spectral-step effect or SSC shrinkage
gain. USPS also illustrates why NMI is necessary: against PCA_r SC the adaptation
raises ACC by 1.860 pp while lowering NMI by 4.876 pp. No cross-subspace inertia
selection or recovered historical LDA-SC claim follows.

The prescribed SLPS block contains 98 complete 50-seed configurations: nine
primary k=5/k=7 pairs on each of five source versions, plus four separately
labelled prior-display pairs. YaleB cropped and DengCai32 remain two source
sensitivities of one benchmark. Each pair holds alpha, dimension, initialization
and seeds fixed; the primary grid uses RANDOM rounding, while the added historical
display controls retain greedy K-means++. This is a controlled neighbor-count
sensitivity, not a new best-setting search or a claim to recover author settings.

The k=7 change has no universal direction. On ORL it lowers both means in all nine
primary pairs (ACC changes -2.205 to -0.295 pp). On JAFFE it raises NMI in all
nine but lowers ACC in three; on native MSRA16 it raises NMI in all nine but
lowers ACC in two. Both YaleB versions show alpha-dependent signs: alpha 0.2
loses both metrics, alpha 0.8 gains both, and DengCai32 at alpha 0.5 gains ACC
while losing NMI. In all four added prior-display pairs, k=7 lowers both means.
These observed interactions do not support a blanket replacement of k=5 by k=7
as the explanation for historical discrepancies. Source-native preparation,
paired controls and complete SDs remain visible in the baseline records and
[baseline implementation notes](baseline_artifact_repairs.md). These descriptive
mean contrasts are not new uncertainty intervals or unseen-data estimates.

Whole-graph component coverage was an incorrect proxy for class-induced fragmentation. The repaired diagnostic counts each class-induced subgraph, including isolates, excess components and largest-component fractions. Edge deletion can destroy force cancellation: the eight-cycle counterexample disproves a universal no-movement-preservation claim. The separate incident-mass sufficient bound remains valid.

The same-current-input USPS audit separates numerical quality from clustering
quality. The gamma 1 continuation meets the 1e-5 relative-gap criterion with zero
recorded capacity violations, but gives 65.564% ACC / 80.228% NMI versus same-F SC
at 65.597% / 80.315%: increments of -0.033/-0.086 pp. Certification came from a
better feasible lower bound on the saved primal point, not improved clustering.
Gamma 1000 still has relative gap 0.341772 after 300,000 updates. Its fused saved
point's 16.703% ACC / 0.000% NMI cannot establish that fusion is optimal. Neither
the original incomplete IRLS300 attempts nor these continuations replace locked
finite-iteration subset outputs. See the [USPS continuation evidence](usps_continuations.md).

All **362 frozen G1–G3 controllers are terminal with COMPLETED status**: two
casebooks, 48 angular-anchor points and 312 completion points. Controller
completion, complete 50-seed rounding and solver certification remain separate.
In [G1](g1_casebook_findings.md), certified active gamma-1 shrinkage changes ORL
ACC/NMI by only +0.155/+0.014 pp and cropped YaleB by -0.270/-0.276 pp relative
to same-F SC. A and W0 have different contamination and class-connectivity
patterns; YaleB W0 edge-length AUROC 0.380 does not support treating its longest
edges as the erroneous relations.

The [G2 factorial](g2_angular_findings.md) shows larger gains before shrinkage:
U-SC exceeds F0-SC by +1.850/+1.016 pp on ORL and +4.016/+4.864 pp on cropped
YaleB. At fixed U/Wa, certified gamma-1 shrinkage adds only +0.170/+0.077 and
+0.314/+0.089 pp respectively. Thus the total normalized-pipeline gain cannot
be credited entirely to shrinkage. Thirty-two of 48 G2 rows are certified;
large-gamma uncertified rows keep their numerical qualifications. Angular
construction does not generally repair within-class fragmentation.

The first validation pass caught a small-support EnSC active-set growth defect before any G4/G5 benchmark execution. Its objective and tau were not replaced to make the test pass. The minimum-growth repair and independent convex-reference checks are recorded separately from the source pin and real-data execution status.

The original wrong-edge gate remains **0/4**. The separate fixed G3 completion
gate now passes on ORL at gamma 1000 and addition fraction 0.15. Completion
exceeds deletion-only ACC by 10.415 pp (paired conditional bootstrap interval
9.920–10.915) and fixed Oracle deletion plus mean blind additions by 24.863 pp
(24.557–25.170), with nondecreasing NMI and a 93.75% reduction in excess
fragments. The involved ORL points are certified. Cropped YaleB's primary
contrast is **NOT_EVALUABLE_UNCERTIFIED**, despite favorable descriptive scores.
The [fixed gate record](../../results/submission_refresh/extension_gate.json)
does not retrospectively change the old gate or establish a label-free result:
Oracle edits use labels, and intervals describe rounding on fixed development
data rather than unseen-dataset uncertainty.

This ORL promotion authorizes the preregistered EnSC adaptation. Its full
four-benchmark G4 campaign is running on the fixed development inputs,
independently of subset winners. Capability, the locked operating point and the
four-benchmark ACC/NMI target remain pending; no extension gain is asserted.

Two final evidence-path defects have implementation repairs awaiting focused
validation: current-v2 EnSC aggregation now checks current adapter identities and
compares backend identities within EnSC families, while the scientific archive
manifest now registers confirmation predictions and the seed namespace. The
prior aggregation failure remains visible. Prepared regression fixtures are not yet
reported as passed checks or final archive recovery.

Authoritative outputs are [baseline diagnostics](../../results/submission_refresh/baseline_diagnostics.csv), [joint historical selection](../../results/submission_refresh/joint_metric_selection.csv), [subset coverage](../../results/subset_search/execution_coverage.csv), [subset matches](../../results/subset_search/closest_matches.csv), and the [extension gate](../../results/submission_refresh/extension_gate.json). Detailed failures and source qualifications belong beside their results, rather than being reclassified as external data restrictions.
