# Experimental protocol

The study separates paper reconstruction, source/subset sensitivity, numerical
optimization and graph-mechanism experiments. [Methods](methods.md) defines the
objectives; [results](results.md) and the
[combined benchmark tables](../results/submission_refresh/per_benchmark/)
report the corresponding measured endpoints.

## Inputs and graph construction

The primary graph setting is Y0: neither input rows nor spectral rows are
L2-normalized. All standard graphs use five neighbors, union symmetrization,
median positive directed-neighbor squared-distance bandwidth and zero diagonal.
The spectral initialization seed is `20261108`.

| Factor | Input row L2 normalization | Spectral row L2 normalization |
|---|---|---|
| Y0 | No | No |
| Y1 | Yes | No |
| Y2 | No | Yes |
| Y3 | Yes | Yes |

Source version, resize interpolation and normalization are distinct factors.
Each changed subset rebuilds \(A,F,W,G\); rows of a parent embedding are not used
as the embedding of a subset. Class counts are supplied by the benchmark design.
Labels define evaluation metrics, class-balanced membership hypotheses and
explicit oracle controls; they do not enter unsupervised fitting.

The source catalogue includes four fixed AR seven-of-fourteen rules and
independent per-identity draws; exact-deduplication, omission and stratified UMIST
hypotheses; BinAlpha 30-per-letter draws; separate YaleB sources and resize
alternatives; full USPS; and native-resolution MSRA sources. ORL and JAFFE retain
their documented membership. Original row IDs, selected/excluded indices,
ordering, duplicate mappings and aliases are recorded in sample manifests.
The fixed permutation seed for finite candidate families is `20261110`.
Aliases are provenance entries rather than independent observations.

## Rounding and statistical endpoints

Every complete SSC subset or graph-rounding configuration contains seeds 0–49 with Lloyd K-means,
`n_init=1`, at most 300 iterations and tolerance `1e-4`. Three initialization
protocols remain distinct: RANDOM, vanilla K-means++ and sklearn greedy
K-means++. A fixed saved \(G\) is shared across its rounding seeds. LLC instead uses its declared Yu–Shi rounding; LDA endpoints refit their representations per external seed and retain the separately specified inner-start budget.

The primary descriptive endpoint is mean and sample SD (`ddof=1`) over all 50
trials, in percent. ACC uses optimal one-to-one label matching. NMI uses
geometric entropy normalization. Both metrics and both SDs come from the same
configuration and seed set. A missing or failed seed prevents a complete
50-trial claim.

Native best-of-50 selects one assignment by the declared objective within the
same fixed representation. For K-means rounding this is SSE; that selected
assignment has no across-run SD. Existing disjoint batches describe repeatability
separately. LDA inertia across independently learned subspaces is not a common
selection objective, so its primary native-best endpoint is unavailable.

Additional rounding uses the same locked winner and saved representation, with
the first unused aligned block of 50 seeds at or above 1,000,000. Winners are
not reselected from these additional results. These measurements concern
conditional rounding variation on fixed samples, not unseen-data performance.

## Reconstruction and selection

The historical-style SSC search uses E8/E13, nominal gamma values
\(\{10^{-6},10^{-3},1,10^3,10^6\}\), and all three rounding protocols. IRLS uses a
300-update cap, relative-iterate tolerance `1e-6` and smoothing epsilon `1e-8`.
Its initial zero-residual floor is based on the representation's median pairwise
distance. Iterate stopping and primal–dual certification are reported separately.

Fixed-protocol sensitivity uses Y0, E8, gamma 1 and RANDOM initialization. Joint
matching allows the declared candidate/configuration grid. For each statistical
endpoint, discrepancy to the paper is

\[
D_{\max}=\max(|\mathrm{ACC}-\mathrm{ACC}_p|,
                  |\mathrm{NMI}-\mathrm{NMI}_p|),\qquad
D_{\mathrm{mean}}=\tfrac12(d_{\mathrm{ACC}}+d_{\mathrm{NMI}}).
\]

Ranking minimizes those quantities in that order, with a `1e-12`
percentage-point tolerance. Ties favor fewer explicit paper deviations, fewer
additional preparation assumptions, the declared E8 target, then stable ID.
Published-grid gamma values are not penalized for differing from one.
Minimum-anchored tolerance groups avoid nontransitive pairwise comparisons.

This is retrospective label/paper-assisted numerical matching. Compatible,
adapted and diagnostic pools remain separate; diagnostic parents do not compete
as equivalent reconstructions. Certified-search availability is explicit and
does not transfer a numerical-audit certificate to a different IRLS output.

## Baseline controls

Existing LDA limits 30/100/300 use matched external seeds. The pinned reference
and ridge adaptation have separate names and state diagnostics. Ridge-adapted
SC has raw-SC, PCA_p0-SC and PCA_r-SC controls under the same external seed index.

SLPS uses paired neighbor counts 5 and 7, alpha in `{0.2,0.5,0.8}` and dimensions
`{30,70,110}`, clipped to valid distinct dimensions. Additional prior-display
settings retain their declared greedy initialization and are labelled separately.
Native MSRA PCA and LLC grids retain their source resolution. A dense LLC
eigensolver result is distinguished from an unsuccessful sparse ARPACK attempt.

## Graph-mechanism design

The fixed development inputs are full ORL att92 and YaleB cropped2414,
independent of subset-matching winners. Three diagnostic blocks distinguish
representation, graph and connectivity effects:

- G1 compares same-F SC and E8 gamma-1 SSC, with complete casebooks, pairwise
  errors, class-induced graph diagnostics and fixed seed-0 illustration IDs.
- G2 crosses anchors `{F0,U}` and graphs `{W0,Wa}` at matched undirected mass,
  with gamma `{0,0.001,1,10,1000,1000000}`. Exact zero rows stay zero and are
  isolated in the angular graph.
- G3 compares deletion, addition and their combination within a label-blind
  union of top-20 neighbors in raw F0, row-normalized input X and angular U.
  Budgets are 15% and 5% of original undirected edge count, rounded down, with
  at most two new incident edges per node. New weights use the median positive
  original weight before mass matching. Random controls use seeds 400–402.

The primary G3 criterion fixes the 15% budget and effective gamma 1000. It
requires certified active deletion/both solves, at least 1 pp paired ACC gain,
nondecreasing NMI, at least 20% fewer excess fragments, and positive lower
conditional bootstrap bounds against deletion and fixed oracle deletion plus
mean blind additions. Bootstrap uses 10,000 resamples and seed `424242` over
paired rounding seeds. Same-class random additions and fully random edits are
separate supplementary controls. The criterion is met if at least one development
benchmark qualifies; this does not validate an unsupervised method by itself.
