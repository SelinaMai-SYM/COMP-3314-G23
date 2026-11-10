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
