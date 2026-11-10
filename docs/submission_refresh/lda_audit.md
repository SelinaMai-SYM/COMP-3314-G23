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
