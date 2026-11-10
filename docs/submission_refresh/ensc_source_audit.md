# Conditional EnSC source and backend audit

This is implementation preparation for the preregistered G4 branch. It does
not authorize or record G4 benchmark execution. G3's completion gate must pass
first; an implementation test is not that gate.

The source is Chong You et al.'s
[elastic-net subspace-clustering repository](https://github.com/ChongYou/subspace-clustering/tree/55e330e38415951f140e74739c869306acdb7a98),
revision `55e330e38415951f140e74739c869306acdb7a98`, associated with
*Oracle Based Active Set Algorithm for Scalable Elastic Net Subspace
Clustering* (CVPR 2016). EnSC is distinct from Spectral Shrunk Clustering.
The original README, license and core Python source were retrieved using normal
public HTTPS and preserved under the external independent-data
`source-audits/ensc-55e330e38415951f140e74739c869306acdb7a98` directory.
The [source manifest](ensc_source_manifest.json) gives URLs, lengths and SHA256
values. Source retrieval does not install SPAMS or upgrade the main environment. The
original module imports SPAMS unconditionally; it has been inspected and
archived, rather than executed here. The helper is an attributed compatible
port, not a claim that the original SPAMS installation was reproduced.

The MIT notice, Copyright (c) 2019 Chong You, is retained unmodified at
[the third-party license](../../method_extension/submission_refresh/third_party/ensc/LICENSE).
Our small attributed adaptation is
[the backend helper](../../method_extension/submission_refresh/ensc.py).

## Actual source conventions

The public `lasso_lars` and `lasso_cd` branches force tau below one back to one.
They cannot serve as the declared tau=0.95 elastic-net prototype. The SPAMS
branch applies L1 weight `alpha*tau` and L2 weight `alpha*(1-tau)` to squared
reconstruction error. With `gamma_nz=True`, the implemented scale is

`alpha_i = max_{j != i} abs(x_j @ x_i) / (source_gamma * tau)`.

This is the executable convention, despite inconsistent inverse-alpha prose
in the source docstrings. The target checked by our helper is

`0.5*||x_i-c_i X||^2 + alpha_i*(tau*||c_i||_1 + (1-tau)*||c_i||_2^2/2)`.

The implementation excludes the self dictionary entry, so `c_ii=0` without
mutating the input matrix. Input rows are normalized to unit L2 norm, with zero
rows retained and recorded. The active-support defaults remain support size 100
and at most 40 updates. The source's residual-over-alpha screening and relative
objective stop are retained. Stable index tie-breaking is an explicit
determinism modification. Inner convergence warnings, objective histories,
iteration caps and measured KKT residuals remain visible.

Coefficient truncation changes the graph: save C before truncation, retain at
most the 50 largest absolute coefficients per row, then row-L2-normalize to Cn.
The affinity is exactly `0.5*(abs(Cn)+abs(Cn.T))`, with zero diagonal. Save C,
Cn, zero-coefficient rows and zero-input rows. A zero total affinity is a
degenerate result, without fallback. Mass matching to W0 is a later orchestration
step, rather than a hidden alteration in this helper.

The source native spectral-clustering code has an unseeded eigensolver and a
constructor default of 20 K-means initializations (its docstring says 10).
A matched native control must save a deterministically seeded eigenspace and
use the prescribed 50 one-start rounding seeds. The author-default 20-start
control, if run, belongs in a distinct budget-labelled track.

## True elastic-net replacement and validation status

The helper uses sklearn `ElasticNet` with `fit_intercept=False`, cyclic
coordinate descent, `l1_ratio=tau` and **`alpha=alpha_i/d`**, where d is the
number of pixel features. sklearn divides squared reconstruction error by the
number of observations, which here equals d. Multiplying its objective by d
recovers the intended original target. Using `alpha_i` directly would change
both regularization coefficients by d.

The prepared tests compare tau 0.95 and tau 1 objectives and KKT residuals against
independent CVXPY/CLARABEL convex problems, compare active/full dictionary
solutions, check truncation and row normalization, and check self exclusion and
zero-affinity handling. They contain no real benchmark labels.

**Current backend validation: focused validation v2 passed all five pinned
backend checks after the small-support repair.** The original v1 failure remains
preserved. The exact tested source, test file, JUnit and log hashes are recorded
in [the backend validation record](../../results/submission_refresh/ensc_backend_validation.json).
This verifies the backend implementation; G4 still requires the separate fixed
G3 gate. An inner KKT check does not certify the downstream
clustering result, and a top 50 truncated coefficient row is not claimed to be
the untruncated elastic-net optimizer. No additional parameter grid is introduced.

## Prepared G4/G5 adapter

`experiments/submission_refresh/ensc_campaign.py` supplies
`run_ensc(task, data_root, artifact_root)` for the shared scheduler. It refuses
to read real inputs unless `extension_gate.json` has `promotion_passed=true`
and `decision=PASSED`, and a backend validation record pins both the tested
backend and its test file. This record is expected at
`results/submission_refresh/ensc_backend_validation.json`, with fields `passed`,
`source_revision`, `backend_source_sha256` and `test_file_sha256`.

The fixed full ORL/JAFFE/cropped YaleB/USPS inputs are independent of subset
matching winners. Matching G3 inputs can be reused by exact X/y and scientific
behavior identities; distinct ambiguous saved F0 inputs cause a failure rather
than score-based selection. Every completed coefficient row is checkpointed
before the next row begins. The optional runtime profile uses a declared
one- or three-row prefix and never calls the evaluator. Profile records are
ineligible as headline results.

Per benchmark the prepared finite catalogue has 44 primary/control records:
15 original-SSC gamma values; five each for angular, tau 0.95, tau 1, wider-kNN
and count/mass-random control graphs; two fair-SC anchors; and two native EnSC
spectral controls. The wider-k control chooses its integer k by edge count,
without labels, and reports any unmatched count. The randomized control fixes
seed 400 and preserves the positive edge-weight multiset; it does not use labels.
These supplementary controls are counted separately from the proposed
five-configuration tau 0.95 search. The primary method is never replaced by
angular or tau 1 output if those controls score better.

The native spectral control follows the source's I-minus-normalized-L largest
eigenspace path with an explicit v0 generated from seed 20261108. It saves the
raw eigenspace and row-normalized representation and uses the same 50 greedy
one-start rounding seeds. The locked label-free point remains tau 0.95/source
factor 50/SSC gamma 1, while capability selection uses ACC, NMI, then stable ID.

The matched-movement diagnostic searches certified adjacent brackets in the
frozen original path, followed by at most six logarithmic bisections. It checks
actual normalized L21 displacement, with tolerance max(5% of target, 1e-6),
without assuming global monotonicity or interpolating embeddings. An unresolved
solver or absent bracket remains an explicit incomplete comparison.

Dedicated graph scientific fingerprints cover graph/embedding, PDHG, evaluator
and rounding behavior, together with environment versions. Exact project byte
hashes remain separate provenance. Comments, docstrings and unrelated report
orchestration do not invalidate a scientifically identical graph solve.

The adapter and its small gate/design/cache tests are prepared; no real G4/G5
jobs have been launched by this source-preparation work. The caller must record
actual triggered execution and any remaining resource-limited coverage.

## Focused-validation correction

The preserved `validation-focused-tests-v1.log` records a failed active-support
reference check with support size 3: the active objective was 0.4597447716 and the
full-dictionary objective 0.1674538289. The source growth rule rounds
`1.1*3` back to 3, leaving no new slot; the unchanged support can then trigger
the objective-stop condition before global KKT conditions hold.

The compatible backend now uses `min(n,max(size+1,round(1.1*max(active,size))))`
to guarantee at least one additional slot when growth is required. This is an
explicit deterministic small-support minimum-growth repair. At the declared
default support size 100, the source's 110-slot update is unchanged. Tau, alpha
scaling, the objective, 40-update cap and the independent convex-test tolerance
are unchanged. No G4 benchmark fits had run when the defect was found.
The failed test record remains available; it is not replaced by the repair.
