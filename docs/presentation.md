# Presentation: when does SSC shrinkage improve clustering?

**Group 23 — Han Jiale, Lu Sinan, Mahatharadol Vie, Mai Sheung Ying**  
**The University of Hong Kong**

This outline supports a nine-minute presentation and a three-minute discussion.
Its central argument follows the performance question, controlled diagnosis,
graph adaptation and observed limits. The [report](../report/Group_23.pdf),
[results](results.md), [methods](methods.md) and [theory](theory.md) provide the
full scientific evidence.

## 1. Question and two-graph model — 0:00–0:45

**Question:** Does SSC's shrinkage improve the final partition beyond matched
spectral clustering, and what limits that improvement?

Display the [editable two-graph diagram](../report/figures/ssc_two_graph_pipeline.tikz):
\(X\xrightarrow{A}F\xrightarrow{W,\,\mathrm{SSC}}G\), with matched SC rounding
the same \(F\). Explain that \(A\) creates the initial representation, while
\(W\) controls fusion. An erroneous relation in \(W\) is a different issue
from a poor upstream representation.

**Takeaway:** Attribute a gain to the component that changed. Row normalization,
graph replacement and additional shrinkage require separate controls.

## 2. Objective and guarantee — 0:45–1:40

Display Equation 8 with each undirected edge counted once:

\[
\min_G\sum_i\|g_i-f_i\|_2+
2\gamma\sum_{\{i,j\}\in E}w_{ij}\|g_i-g_j\|_2.
\]

The first term keeps the initial representation; the second attracts connected
points. For fixed \(F,W\), the target is convex. The coefficient two matches
the paper's ordered sum. E13 nominal gamma corresponds to half that gamma in
the E8 target. Neither convexity nor exact solution promises better K-means
labels, and unsquared fidelity does not guarantee uniqueness.

**Takeaway:** A valid optimization guarantee answers whether a target was solved;
ACC/NMI answer whether its refinement helped clustering.

## 3. Reconstructing the reported evidence — 1:40–2:40

Use one row from the [combined benchmark tables](../results/submission_refresh/per_benchmark/)
to show paper and measured ACC/NMI, both sample SDs, and the exact statistical
endpoint. All 72 method/benchmark targets have verified means and SDs.

Explain the joint discrepancy:

\[
D_{\max}=\max(|\mathrm{ACC}-\mathrm{ACC}_p|,
                  |\mathrm{NMI}-\mathrm{NMI}_p|),\qquad
D_{\mathrm{mean}}=(d_{\mathrm{ACC}}+d_{\mathrm{NMI}})/2.
\]

The same complete configuration supplies both metrics. A 50-trial mean, a
single native-best assignment and independent-batch repeatability are separate
endpoints. The native-best assignment receives no across-run SD. LDA inertia
across different learned subspaces is not a common selection objective.

Place this qualification beside the displayed result:

> Closest evaluated reconstruction; retrospective matching does not establish
> historical sample membership or unsupervised parameter selection.

**Takeaway:** A closer numerical match does not identify the original samples or
recover an unavailable historical implementation.

## 4. Source and subset sensitivity — 2:40–3:30

Summarize the distinct membership questions: AR seven-of-fourteen rules and
per-identity draws; UMIST deduplication, omission and stratification hypotheses;
BinAlpha thirty-per-letter samples; separate YaleB sources and resize factors.
ORL/JAFFE retain their valid membership, and full USPS retains all 9,298 rows.
The available 1,799-row MSRA source is native 16×16, a resolution adaptation
relative to the paper's 32×32 description.

For every changed subset, \(A,F,W,G\) are recomputed. Taking rows from a parent
embedding would answer a different question. Distinguish candidate changes
from parameter-grid changes through the four reference/candidate and
fixed/grid contrasts. Additional rounding evaluates a locked winner on new
rounding seeds; it does not reselect that winner or test unseen samples.

**Takeaway:** Source identity, membership, resolution, parameters and rounding
are separate experimental factors. All incomplete or failed configurations
remain visible in the scientific coverage.

## 5. Numerical accuracy and the stronger baseline — 3:30–4:45

Show the primal upper bound, feasible dual lower bound and relative-gap rule:

\[
D(q)\leq\min P\leq P(G),\qquad
\frac{P-D}{\max(1,|P|,|D|)}\leq10^{-5}.
\]

Edge/node violations must also be at most \(10^{-8}\). An iterate stop, solver
agreement or a low objective alone is insufficient. A numerical certificate
belongs to its own output; it cannot be transferred to a different IRLS result.

On one fixed current USPS F/W pair, the certified gamma-one numerical reference
has ACC/NMI **65.564 ± 2.520 / 80.228 ± 2.343**, versus matched SC
**65.597 ± 1.867 / 80.315 ± 2.128**. The large-gamma numerical reference remains
uncertified, so its poor fused point does not characterize the optimum.

Then show the geometry control: row normalization alone raises SC ACC by
**1.850 pp on ORL** and **4.016 pp on YaleB**. Gamma-one angular-graph shrinkage
adds only **0.170/0.314 pp** above its own normalized-anchor SC baseline.

**Takeaway:** More accurate optimization need not improve clustering. A stronger
representation baseline can explain gains that would otherwise be attributed
to shrinkage.

## 6. What does the graph intervention establish? — 4:45–6:00

Use the [graph results](../results/submission_refresh/extension_results.csv) and
[fixed-criterion record](../results/submission_refresh/extension_gate.json).
Class fragmentation is measured on each true class's induced graph, including
isolates; whole-graph connectivity is a different statistic. Upstream \(A\)
and fusion \(W\) contamination are reported separately.

The connectivity experiment compares deletion, addition and their combination
from a label-blind candidate-edge pool. Its primary setting fixes 15% additions
and effective gamma 1000. The key comparator is **fixed oracle deletion plus
blind random additions**, not fully randomized deletion and addition.

On ORL, oracle completion improves ACC by **10.415 pp** over deletion
(conditional 95% interval **[9.920, 10.915]**) and **24.863 pp** over the mean
blind-addition control (**[24.557, 25.170]**), while satisfying the fixed NMI,
fragmentation, certificate and activity criteria. YaleB's large descriptive
gains remain unqualified because the required solves are uncertified. The
earlier capped-fusion deletion gate's **0/4** result is a separate experiment.

**Takeaway:** The intervention supports useful missing connectivity on ORL within
this pool. Its label use makes it a mechanism diagnosis, not an unsupervised
algorithm score. The intervals concern paired rounding on fixed data.

## 7. EnSC affinity plus SSC: all four benchmarks — 6:00–7:45

The primary adaptation keeps \(F_0\) and uses the tau-0.95 EnSC affinity as its
fusion graph. Source coefficient 50, top-50 truncation and graph-mass matching
are fixed. Capability chooses gamma within the five-point grid using ACC, then
NMI; label-free operation fixes gamma one. Native EnSC uses its own spectral
space and remains an attribution control.

Values below are percentages, mean ± sample SD of the same 50 one-start greedy
K-means++/Lloyd seeds. C/U refers to downstream **fusion** certification.

| Benchmark / primary track | Gamma | ACC ± SD | NMI ± SD | Fusion |
|---|---:|---:|---:|---|
| ORL / capability = locked | 1 | 78.980 ± 1.261 | 91.396 ± 0.433 | C |
| JAFFE / capability = locked | 1 | 96.413 ± 0.364 | 96.078 ± 0.542 | C |
| YaleB / capability = locked | 1 | 27.659 ± 0.741 | 36.989 ± 0.556 | C |
| USPS / capability | 0.001 | 65.597 ± 1.867 | 80.315 ± 2.128 | C; G=F |
| USPS / locked | 1 | 52.274 ± 3.948 | 69.734 ± 1.547 | U |

Fair SC selects normalized \(U\) on all four inputs, with ACC/NMI means
**80.175/90.890**, **96.714/96.392**, **25.797/32.595** and **68.360/83.436**.
Native tau-0.95 EnSC gives **81.675/91.684**, **99.061/98.336**,
**61.089/66.487** and **49.507/60.822**, respectively. Its strong first-three
results cannot be credited to the fixed-anchor SSC adaptation.

Every benchmark has all 44 declared endpoints, but 5/6/14/21 required configurations
are unqualified on ORL/JAFFE/YaleB/USPS. **Both formal four-benchmark targets and
the parameter-selection-gap flag remain NA.** The locked USPS point is
uncertified, and its capability winner has zero movement. Coefficient KKT
accuracy is a separate limitation: 969/9,298 tau-0.95 USPS rows fail the
declared diagnostic, with maximum residual 8.6962e-5. Matched movement lacks a
certified bracket on the first three inputs; USPS matches zero movement only.

**Takeaway:** The final study does not establish the requested net shrinkage
improvement. It identifies representation, graph and numerical limitations
without replacing the primary method by a better-scoring control.

## 8. Contribution and limits — 7:45–9:00

Close with three claims supported at different levels:

1. **Reproducibility:** explicit objectives, source/subset hypotheses, complete
   seed sets and distinct statistical endpoints make the comparisons auditable.
2. **Diagnosis:** representation normalization and missing graph connectivity
   matter in the observed controls; numerical optimality alone is insufficient.
3. **Research outcome:** the learned-graph adaptation has mixed results and
   unresolved required configurations. Formal macro success is unavailable, rather
   than inferred from selected favorable rows.

Capped fusion is an adaptation of existing penalties, not a new penalty family.
Its five-point objectives are eight versus three, and its local solution depends
on initialization. Because SC is already perfect in that example, it shows
damage avoidance. Radial Huber activation and heat-kernel stability are useful
mathematical properties, but remain secondary candidates rather than evidence
of a general clustering gain.

The predeclared two-percentage-point average ACC goal with nondecreasing NMI is
a research target, not a mathematical guarantee. The supported outcome explains
what improved, what did not, and which conclusions remain numerically or
historically unidentified.

## Discussion and backup material

- **Can edge deletion preserve G=F automatically?** No. On the eight-cycle at
  gamma 0.6, deletion destroys force cancellation and makes F nonoptimal. The
  separately valid incident-mass sufficient bound is preserved when it held.
- **What is proved by the two-group fusion model?** Under fixed weights and
  group-constant representatives, linear fusion has minimum
  \(d\min(m,\lambda)\); capped fusion for \(d>\tau\) has
  \(\min(md,\lambda\tau)\). At equality, multiple optima prevent strict
  separation claims. The verified five-point graph is not an arbitrary-graph
  theorem. See [the derivation](theory.md#4-two-representatives-explain-one-fusion-failure).
- **Why are certificate and coefficient accuracy separate?** SSC's gap applies
  to fusion on a fixed graph. EnSC coefficient KKT diagnostics apply upstream,
  before truncation. Neither certifies final labels.
- **Why keep both capability and locked operation?** The first uses label-assisted
  selection within the declared grid; the second uses a fixed parameter without
  labels. USPS demonstrates why they cannot substitute for each other.
- **Why is the macro NA after all configurations completed?** The formal design
  also requires qualified comparisons. Completed rounding and feasible dual
  capacities do not resolve a gap above tolerance.
- **What does new rounding establish?** Conditional stability on the same
  samples and saved representation, without winner reselection. It does not
  establish unseen-data generalization or original subset identity.

The [experimental protocol](experimental_protocol.md) gives the complete grids
and selection rules. The [theory](theory.md) gives proofs, equality cases and
prior-art attribution; [scientific limitations](limitations.md) separates
numerical uncertainty from historical source restrictions.
