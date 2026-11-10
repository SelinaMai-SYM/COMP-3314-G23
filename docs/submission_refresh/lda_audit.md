# LDA implementation audit

The historical LDA-SC method remains unresolved. The three implementations below
are named separately in the current campaign; none is presented as recovered
original SSC-paper LDA-SC code.

The existing project LDA-Kmeans now exposes `fit_state` in addition to its
backward-compatible `fit_predict` entry point. The default still checks literal
label equality and reuses the same integer K-means seed at each update. The state
records the projection actually used, input mean, labels, centers, projected SSE,
Fisher trace diagnostics, ridge, update attempts, and stopping reason. A separately
requested `permutation_invariant_stop=True` changes convergence to equality of
partitions up to a permutation of cluster names. It is not silently enabled for
historical-style runs. The documented outer caps are 30, 100 and 300 updates.
`audit_limits` executes these limits independently and checks all overlapping
projection, label, center and SSE states before permitting trajectory-prefix reuse.
The campaign does not assume that a matching final score proves a matching prefix.

The reference is ClustPy commit
`4ac9d00685efc7432800684f5bfac0f01af59172`, core Git blob
`e2d952694a20ccabe0d38bd54ba9e5b5c5d4b846`. Unmodified source and helper files,
the BSD-3-Clause license and exact hashes are stored under
`baselines/lda_kmeans/vendor/clustpy/`. The executable `reference.py` is a minimal
attributed port. It retains the source's unregularized generalized eigensolver,
failed-update continuation, mutable RandomState, ten-start inner K-means and
arithmetic-NMI equality stopping test. The source clusters `X @ rotation`, using
a centered covariance only for the eigensolver. The port preserves this distinction.
One determinism change is explicit: a scoped global NumPy seed controls the
otherwise unseeded source PCA, after which the former global RNG state is restored.
The outer seed draw also matches the source wrapper's `choice(10000,1)`.

Each reference record contains both the rotation actually used and the rotation
returned by the source. The latter can be one update ahead when the iteration cap
is reached. This inconsistency remains visible. Its labels are evaluated with the
rotation actually used; a mismatched rotation is not used as a clean representation.
If no LDA update succeeds, the state is labelled `DEGENERATED_TO_PCA_KMEANS`.
Failed and degenerate states are retained, and scientific qualification remains
beside the execution endpoint. Native projected SSE is not a common selection
objective across the fifty learned subspaces. The primary best-objective-of-50
endpoint is therefore unavailable for these LDA configurations.

The separately named **PCA-preconditioned ridge LDA-Kmeans -> SC (adapted)** uses
centered float64 input and deterministic full-SVD PCA. Its numerical-rank tolerance
is `eps * max(n,p) * sigma_max`, with
`p0=min(100,p,n-K,numerical_rank)` and `r=min(K-1,p0)`. Within the PCA coordinates,
scatter matrices are covariances divided by `n-1`, matching the pinned reference's
normalization. The fixed ridge is `eta=1e-6*trace(St)/p0`. The first projection uses
the leading PCA axes. There is one outer fit, ten greedy K-means++ starts per
clustering step, a maximum of 300 outer iterations, and exact partition-equivalence
stopping. No true labels enter a fitter. No row normalization is added. At a cap,
the last projection actually clustered is returned. The saved representation is
`(X-training_mean) @ P_p0 @ R` with its generalized-eigenvector scale preserved.

The adapted block includes raw SC, PCA_p0 -> SC and PCA_r -> SC controls, using one
RANDOM Lloyd start with the same external seed index as the learned fit. Fifty
external seeds mean fifty learned representations and fifty downstream rounds;
they do not mean fifty downstream rounds for each learned representation. Exact
control affinities, eigenspaces, projection matrices, mutable RNG states,
trajectories and predictions are saved through the shared content-addressed store.
Each final external-seed checkpoint can be resumed independently. Failed seeds
remain in the ledger and disqualify a complete fifty-seed claim.

Small synthetic checks verify exact agreement with the unmodified pinned core,
including its returned state, reveal a deliberately singular update failure, and
show the cap inconsistency. A matched full-rank eigenproblem confirms the scale
factor `sqrt(n-1)` between covariance-normalized reference eigenvectors and the
project's unnormalized-scatter eigenvectors. On the fixed 60-row, three-group
synthetic fixture, the converged reference projected SSE is 118, equal to
`(n-1)*r=59*2`; it is a normalization consequence, not evidence of superior
clustering. The fixture is an implementation check, not a benchmark result.

Runtime profiles are strictly label-blind. They fit external seed zero, retain
unsupervised state and timing, and do not invoke ACC/NMI or select configurations.
Profile artifacts are explicitly ineligible. Actual benchmark coverage, statuses
and CPU costs are recorded by the shared campaign rather than inferred from these
small checks.

## Complete benchmark findings, 10 November 2026

The current [baseline diagnostics](../../results/submission_refresh/baseline_diagnostics.csv)
and [seed coverage](../../results/submission_refresh/baseline_seed_coverage.csv)
contain complete seeds 0–49 for each result discussed here. Their `source_record`
paths identify the saved scalar trials and fit diagnostics in the recoverable
external store. The five sources are ORL att92, JAFFE, YaleB cropped2414, full USPS
and native MSRA25 EBSA16. They are current source/settings experiments, not newly
established historical identities. Means and sample SDs remain in the CSV; the
contrasts below are descriptive differences of complete matched-seed means, not
new confidence intervals or significance tests.

### Existing implementation: 30, 100 and 300 updates

All 15 dataset/limit configurations completed 50 seeds, with no recorded LDA
update failures. The three limits were compared on matched external seed indices.
At limit 100, all 50 fits on every source reached `LABELS_STABLE`; their ACC/NMI
pairs are identical to limit 300 for every seed. Raising the cap to 300 therefore
adds no metric improvement in this block.

| Source | At the 30-update cap | Change in mean ACC/NMI from 30 to 100 (pp) |
|---|---|---:|
| ORL att92 | 50 label-stable fits | 0.000 / 0.000 |
| JAFFE | 50 label-stable fits | 0.000 / 0.000 |
| YaleB cropped2414 | 50 label-stable fits | 0.000 / 0.000 |
| MSRA25 EBSA16 | 49 label-stable; one reached the cap | +0.006 / +0.020 |
| USPS | 12 label-stable; 38 reached the cap | -0.323 / -0.363 |

Only one MSRA seed and the 38 capped USPS seeds change their ACC/NMI pair between
30 and 100. The USPS decline shows that further algorithmic convergence need not
improve label metrics. YaleB remains about 9.672% ACC and 13.416% NMI at all three
limits; an inadequate outer cap does not explain that result in this tested
implementation. Equal endpoint metrics alone do not prove equal trajectories or
authorize arbitrary prefix reuse. The timer-interrupted YaleB attempt remains
separate; complete whole-fit checkpoints were adopted only through the recorded
source/environment/input verification.

### Pinned reference: actual update failures and returned state

All five reference configurations have 50 evaluated executions, but their
scientific status differs:

- **JAFFE:** all 50 fits have zero successful LDA updates and are labelled
  `DEGENERATED_TO_PCA_KMEANS`. Across them, 625 updates record `LinAlgError`.
  Source NMI stopping occurs in every fit, despite the failed LDA updates.
- **ORL:** all 50 fits likewise have zero successful LDA updates, with 15,000
  `LinAlgError` updates in total; every fit reaches the 300-update cap. Their
  retained PCA projections and repeated inner K-means runs must not be described
  as successful discriminant learning.
- **MSRA25 EBSA16, USPS and YaleB cropped2414:** all 50 fits on each source perform
  successful LDA updates, report no update failures and stop at source NMI
  stability. Singular-update failure is therefore not the observed YaleB
  mechanism in these records.

Every completed benchmark reference record reports a consistent returned state.
The source's one-update-ahead rotation behavior is demonstrated by the separate
cap regression fixture; it was not observed as an inconsistent return in these
250 benchmark fits. In particular, ORL's cap was reached with every LDA update
failing, so its unchanged rotation does not exhibit that discrepancy. The audit
keeps both actual-used and source-returned projections and retains the scoped
PCA determinism modification. It does not silently repair the pinned reference
or use its respectable degenerate-case scores as proof of working LDA.

### Ridge adaptation and matched SC controls

The separately named adaptation and each of its four output/control endpoints
completed 50 external seeds on all five sources. The direct learned-label result
uses the method's ten-start inner K-means. Downstream SC and its raw/PCA controls
use one RANDOM Lloyd start per matched external seed. Thus direct learned labels
versus downstream SC measure the complete prescribed pipeline change; they do
not isolate a change in spectral geometry from a change in rounding budget.

| Source | Adapted SC minus raw SC: ACC/NMI (pp) | Adapted SC minus PCA_p0 SC: ACC/NMI (pp) |
|---|---:|---:|
| ORL att92 | -6.990 / -4.815 | -6.250 / -4.465 |
| JAFFE | -9.146 / -9.291 | -9.615 / -9.292 |
| YaleB cropped2414 | +17.508 / +23.676 | +18.103 / +24.205 |
| USPS | -3.949 / -13.837 | -4.991 / -14.416 |
| MSRA25 EBSA16 | -5.531 / -8.114 | -5.937 / -8.159 |

YaleB is the clear positive control-relative case: adapted SC reaches
35.848% ACC / 50.579% NMI, while directly clustering the learned representation
reaches 42.119% / 51.323%. It nevertheless has 32 capped fits and only 18
partition-stable fits at 300 updates. All fits on the other four sources reach
partition stability, and no adapted update failures are recorded. The adaptation
is neither uniformly converged nor uniformly beneficial.

The lower-dimensional PCA_r control also matters: adapted SC improves both means
over it on JAFFE and MSRA16, loses both on ORL, and raises USPS ACC by 1.860 pp
while lowering NMI by 4.876 pp. A positive ACC comparison to one weaker control
cannot replace the raw/PCA_p0 comparisons or conceal the NMI loss. Downstream SC
lowers both means relative to the direct learned-label endpoint on every source
under the declared differing rounding rules.

These are upstream baseline/adaptation findings, not evidence of beneficial SSC
shrinkage or recovered historical LDA-SC. Cross-subspace native-objective
selection remains unavailable. The matched SLPS k=5/k=7 findings are summarized
in [research findings](research_findings.md); final subset and graph conclusions
remain pending.
