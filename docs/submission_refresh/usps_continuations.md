# Separate bounded USPS numerical continuations

The original ten same-F/W audit attempts remain unchanged. Their numerical gap
evidence motivates exactly two additional attempts, at E8 gamma 1 and gamma 1000.
This is a solver-quality continuation, not another parameter or label-assisted
performance search. Neither ACC nor NMI chooses initialization or stopping.

`usps_continuation.load_problem` reads the exact original frozen F/W objects and
checks the solver NPZ, terminal task manifest, stage metadata and array hashes.
It never dereferences the label object. All available stored primal points are
compared using the exact same E8 objective, and stored dual candidates are checked
through the feasible-dual routine with original capacities 2*gamma*w. Initialization
uses the lowest actual primal and highest independently feasible dual bound.
The selected primal and dual may come from different earlier iterates; both
sources and their actual values/hashes remain explicit. This does not mix the
objective or clustering metrics of different primal points.

Both targets use the existing diagonal preconditioned solver unchanged, a maximum
of 300,000 PDHG updates and at most 1,800 process CPU seconds per additional job.
The gap threshold remains 1e-5, with the original capacity tolerance. The
initialization is a same-objective warm restart; it is not claimed to reproduce
one uninterrupted PDHG trajectory. A numerical success is not an ACC guarantee,
and failure to certify remains an internal numerical limitation.

New fit records, exact G/q arrays, final/last/best checkpoints and scalar histories
are saved under `ARTIFACT_ROOT/usps_continuations/<run_id>`, outside the original
audit directory. Existing attempt directories cannot be overwritten. Every
original input/stage file hash is checked again after a fit. Actual cumulative
USPS charges and other active reservations are deducted from the shared six-hour
repair allowance; the broader 36-hour ledger and two-worker limit also apply.
No new ledger or worker pool is created here.

The separate rounding task runs only after both fits are terminal. It verifies
all additional arrays before using the existing `evaluate_verified` interface
for the same greedy K-means++/Lloyd seeds 0-49. Additional results stay under
`usps_continuation_evaluation`, with separate scalar exports; they do not replace
the original audit evaluation, finite 300-step historical output, subset winners
or any historical selected configuration. Missing G remains explicitly
`NOT_EVALUATED_MISSING_G`.

Ready queues and dispatcher targets:

- `configs/submission_refresh/usps_continuation_queue.json`, kind
  `usps_continuation` -> `run_continuation(task,data_root,artifact_root)`;
- `configs/submission_refresh/usps_continuation_evaluation_queue.json`, kind
  `usps_continuation_evaluate` -> `run_rounding(task,data_root,artifact_root)`.

`export_results(artifact_root,output)` produces
`usps_continuation_audit.csv`, `usps_continuation_evaluation.csv` and
`usps_continuation_trials.csv.gz` from saved scalar records. A single native-best
assignment receives no across-run SD. Additional rounding measures conditional
randomness on the same fixed samples and point, rather than unseen-data
performance. Preparation of these controllers/queues launches no scientific job;
actual status and CPU use must be taken from the shared ledger and exported rows.

## Actual results as of 10 November 2026, 09:40 UTC

These are interim exported measurements from
[continuation fits](../../results/submission_refresh/usps_continuation_audit.csv),
[continuation rounding](../../results/submission_refresh/usps_continuation_evaluation.csv)
and the [original audit evaluation](../../results/submission_refresh/usps_solver_evaluation.csv).
Both additional fit jobs and all their declared rounding seeds completed. A
completed job is distinct from a certified solution. The inputs are the frozen
current 9,298-row USPS F/W pair, not recovered historical selected F/G arrays.

| E8 gamma | Returned solver status | Primal | Feasible dual | Relative gap | PDHG updates | Full attempt CPU (s) |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `PRIMAL_DUAL_GAP_CERTIFIED` | 13.5771210603 | 13.5769852942 | 0.000009999619 | 82,800 | 269.399 |
| 1000 | `MAX_ITER_REACHED`, uncertified | 267.9597177678 | 176.3786572603 | 0.341771746 | 300,000 | 811.375 |

The gamma 1 gap meets the 1e-5 criterion; recorded edge and node capacity
violations are both zero. Its returned best G has the same recorded array hash
as the saved gamma 1 IRLS diagnostic point. The restart improved the feasible
lower bound enough to certify that saved primal; it did not improve that point's
ACC/NMI. The gamma 1000 gap decreased from the earlier warm restart's 0.551191351
to 0.341771746, but remains far above tolerance. These attempts used 1,080.774
CPU seconds in total, including their controller checks and I/O; this is not the
total cost of the original audit, rounding or the combined campaign.

Clustering values below are percentages, mean plus sample SD over the same 50
greedy K-means++/Lloyd seeds 0–49. Both metrics refer to the same saved G and seed
set. Deltas subtract SC on that exact F and are percentage points.

| Saved representation | ACC mean +/- SD | NMI mean +/- SD | Delta ACC vs SC (pp) | Delta NMI vs SC (pp) |
|---|---:|---:|---:|---:|
| Same-F SC | 65.597 +/- 1.867 | 80.315 +/- 2.128 | — | — |
| Gamma 1 continuation, certified | 65.564 +/- 2.520 | 80.228 +/- 2.343 | -0.033 | -0.086 |
| Gamma 1000 continuation, uncertified | 16.703 +/- 0.000 | 0.000 +/- 0.000 | -48.895 | -80.315 |

The gamma 1 result supports a small negative shrinkage increment at this fixed
operating point, not a claim that SSC lacks useful parameters. The gamma 1000
returned G has one distinct row and poor clustering, but the unresolved gap means
it cannot establish that fusion is optimal for the mathematical objective. Its
measured zeros and near-zero rounding SD are actual results on that saved point,
not filled missing values. None of these conditional rounding measurements is a
generalization estimate or a certified closest subset-search result.

The original audit's unsuccessful attempts remain diagnostic evidence:

- Gamma 1 `IRLS300` stopped at `CPU_LIMIT` after 228 reported steps. Gamma 1000
  `IRLS300` reports `FAILED` after one reported step. Both have
  `historical_300_protocol_complete=False`; evaluating a saved G on all 50 seeds
  does not make either fit a completed historical-style 300-step execution.
- Both componentwise dual-flow constructions report `INCOMPLETE_LINEAR_SOLVE`.
  Failure of these particular constructions does not prove that a feasible
  certificate is unavailable.
- The original uniform, diagonal and warm-restart PDHG attempts reached their
  iteration caps. The additional certified gamma 1 point does not certify those
  different returned points or replace any locked historical-style winner.

Original stage failures, exact arrays, duals and histories are preserved. The
generated same-current-input identity view remains separately scoped: matching
F/W references never transfer a continuation certificate to an IRLS G. Final
campaign aggregation, report validation and publication are still pending.
