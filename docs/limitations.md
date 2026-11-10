# Scientific limitations

The conclusions apply to the explicitly recorded sources, inputs, objectives,
parameters and statistical endpoints. The [results](results.md) and
[benchmark tables](../results/submission_refresh/per_benchmark/) retain the
qualifications below alongside the measurements.

## Historical identity and paper specification

The original paper does not fully specify sample indices, several source
versions, graph bandwidth/symmetrization or the SD hierarchy after native
objective selection. Reproducible AR, UMIST and BinAlpha candidates are
membership hypotheses. A close ACC/NMI match does not establish the authors'
historical inputs.

The available MSRA25 EBSA matrix is native 16×16, whereas the paper describes
32×32 input. Its complete 1,799-row source remains a separately named adaptation.
Upsampling cannot recover missing native pixels. Two YaleB sources are
sensitivities of one benchmark, not two independent datasets. Source geometry
marked unverified in the inventory is not inferred from feature count alone.

## Selection and statistical uncertainty

Joint paper matching and capability selection use true labels after fitting.
They are retrospective oracles rather than unsupervised parameter-selection
rules. ACC/NMI and SD remain attached to the same chosen configuration.
Additional rounding checks a locked representation on the same samples;
it does not supply an unseen-data test or remove selection bias.

Mean/sample-SD, a single native-best assignment and repeatability across batches
are different statistical objects. A selected assignment has no across-run SD.
Conditional paired intervals do not become unbiased confidence intervals for a
selection process merely because they use common seeds. Missing datasets are
not omitted from a formal four-benchmark average to obtain a favorable result.

## Numerical objectives and clustering

Convexity and primal–dual certification concern the fixed representation
subproblem. They do not certify final clustering accuracy, uniqueness or stable
rounding of all near-optimal representations. Finite IRLS stopping is not proof
of optimality. The USPS gamma-1000 numerical comparison retains an unresolved
gap; its poorly clustering fused saved point does not establish optimal collapse.

Certificates cannot be transferred between different outputs merely because
their F/W inputs agree. Historical outputs whose exact arrays are unavailable
cannot be certified by solving a newly generated problem. A failed componentwise
flow provides no proof that all feasible-dual constructions would fail.

## Baselines and learned graphs

The pinned ClustPy implementation performs no successful LDA update on the
recorded ORL/JAFFE experiments, producing explicit PCA/K-means degeneracies.
That implementation observation is not a general theorem about LDA-Kmeans.
The separately named ridge adaptation does not recover historical LDA-SC, is
not uniformly beneficial across controls, and has capped YaleB fits. Native
inertia across learned subspaces is not a defensible common selection objective.

The EnSC coefficient solver's KKT diagnostic and SSC's fusion gap certify
different targets. Screening/source stopping does not imply a small KKT
residual. Uncertified required original-SSC/control configurations prevent a
formally qualified four-benchmark comparison, even where a selected primary
point is certified. Consequently, the formal capability and fixed-operation
macro target decisions remain unavailable under the specified qualification
rules; this is not an automatically failed performance target. The
parameter-selection-gap conclusion is likewise undefined without both formal
tracks.

Native EnSC is a distinct method control. It has higher ACC/NMI means than the
primary EnSC–SSC adaptation on ORL, JAFFE and YaleB. USPS differs: its primary
capability point selects gamma 0.001 and is exactly G=F, while the locked gamma-1
point is uncertified and substantially worse. The higher primary means than
native EnSC on USPS therefore supply no evidence of beneficial shrinkage.

ORL, JAFFE and YaleB have no certified original-SSC movement bracket. The USPS
match has zero target and zero matched movement, so it does not establish a
topology-specific benefit at equal nonzero shrinkage. Source stopping is also
insufficient for coefficient accuracy: 969/9,298 USPS tau-0.95 rows fail the
declared KKT diagnostic, with maximum residual 8.6962e-5. These are retained
numerical limitations, independently of downstream ACC/NMI.

## Mechanism and scope

Cross-class edge mass, class fragmentation and error-stratified associations are
diagnostics, not causal attribution by themselves. Wrong edges are not
universally longer, and deleting edges can destroy force cancellation. Oracle
deletion/completion uses labels and does not establish an unsupervised repair.
Passing its criterion does not establish EnSC adaptation performance.

The benchmark design and finite compute budget delimit evaluated configurations.
Complete, unsuccessful and unevaluated points remain distinguishable; neither
source ambiguity nor resource limits erase numerical or implementation failures.
The project evaluates and adapts established components rather than claiming
invention of convex fusion, PDHG, elastic-net clustering or truncated penalties.
