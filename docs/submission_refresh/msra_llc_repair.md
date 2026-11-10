# Mandatory baseline completion and MSRA LLC numerical repair

This review inspected execution status, seed namespaces, settings and exceptions,
without consulting ACC/NMI to choose a continuation cohort.

The completed mandatory inventory includes all three existing-LDA limits on the
five main available baseline sources, all five adapted-LDA blocks and their
controls, and the reference LDA blocks. The original ORL reference block timed
out; its separate continuation retains complete external fits and finishes the
fixed fifty-seed endpoint. The earlier failed/time-limited records remain intact.
The paired SLPS block has twenty complete fifty-seed configurations on each YaleB
source, ORL and JAFFE, including the preregistered reported-setting additions.
The MSRA SLPS block has eighteen complete configurations.

`msra-other-v1` completed raw K-means and all fifteen PCA-Kmeans and fifteen PCA-SC
configurations with all fifty prescribed seeds. It then failed on the first LLC
configuration, ridge 0.1 and bandwidth factor 0.0625: ARPACK exhausted 17,991 iterations
with 11 of 12 requested eigenvectors converged. This is a project numerical
limitation, not missing MSRA data. The remaining LLC points were not attempted
because the old block exited on that exception. Completed PCA/Kmeans endpoints
are retained and are not rerun by the repair.

The separate `msra_llc_continuation.py` controller uses the existing LLC library's
public dense branch (`dense_threshold=n`) uniformly for all fifteen original
ridge/bandwidth pairs. It keeps the same sparse local regression matrix R,
operator `(I-R).T @ (I-R)`, twelve-dimensional eigenspace, row normalization,
fifty Yu-Shi seeds 0-49, a 300-step discretization cap and tolerance 1e-7. The numerical
backend is explicitly `numpy.linalg.eigh`. This does not relabel the failed
original sparse run as successful.

The choice follows an eigensolver failure before any LLC scores existed. No model
parameter, sample membership or scoring endpoint changes. The controller verifies
the exact original X/y objects, input shape 1799-by-256 with 12 classes, frozen fitting
library bytes, environment and recoverable source archive before starting. It
records eigenpair operator residuals and raw-eigenvector orthogonality for every
point. Acceptance thresholds are 1e-8 for normalized residual and orthogonality;
tiny negative eigenvalues must be no smaller than -1e-10. No extra ridge or spectral
clipping is introduced. R, the explicit dense Gram matrix, raw/normalized
eigenvectors, predictions, rotations and per-seed checkpoints remain recoverable
through the shared artifact store.

Run the separate fixed-first-configuration profile before the formal grid. It
performs no ACC/NMI evaluation and its outputs are ineligible. The full grid is
then rerun through the declared dense branch, with all fifteen points and all
fifty seeds retained. Per-configuration/seed failures remain explicit; a partial
successful-seed set is not promoted. The shared scheduler owns every CPU
reservation and worker. This controller does not launch another pool or ledger.

The ready queue files are:

- `configs/submission_refresh/msra_llc_profile_queue.json`: 120 CPU seconds;
- `configs/submission_refresh/msra_llc_continuation_queue.json`: 1,800 CPU seconds,
  after the profile status is terminal.

The root dispatcher routes kind `msra_llc_repair` to
`run_continuation(task,data_root,artifact_root)`. Its records remain in the existing
`baseline/<run_id>` layout and use the ordinary `llc` method identity with explicit
numerical-repair qualifications. Original sparse failure, completed PCA endpoints
and new dense results stay separately identifiable. The controller/queues are
prepared separately from execution. The shared root scheduler subsequently completed the profile and formal repair. A metadata-only check found all fifteen dense LLC configurations complete with the prescribed fifty seeds; all 31 earlier Kmeans/PCA endpoints and the original ARPACK failure remain retained. No ACC/NMI values were inspected to make this completion decision.
