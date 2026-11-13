# Frozen experiment protocol

The authoritative machine-readable specification, input lock, registry and finite queue are in [configs/extension_round3](../../configs/extension_round3). They were committed before new benchmark fitting or scores, at `3a3a41c`. There are 378 declared profiles, including separate reference and exact-alias rows. The registry maps the three candidate aliases to their full round-qualified method names.

The eight inputs are the unchanged round-two report cohorts, including the adapted native 16×16 MSRA proxy and the existing historical-identity qualifications. No membership, ordering, preprocessing, A0, H or W0 is selected anew. Labels are byte-verified opaque objects during freezing. They are loaded only after a terminal numeric freeze, including all eligibility decisions. No fit is allowed afterward.

The primary movement is 0.10; fixed secondary movements are 0.05 and 0.20. Each method/cohort path shares 32 distinct lambdas and 1,800 CPU seconds across targets. Individual convex fits have a 600-second ceiling. A finite unresolved endpoint remains visible and cannot establish mathematical unattainability. Paths use geometry-only bracketing and fixed clipped log-secant refinement. Saved old arrays may warm-start a path after input checks; no old scalar score is substituted for a new panel.

Both rounding panels use 50 seeds, 0–49, greedy k-means++, Lloyd, one start, 300 iterations and tolerance 10⁻⁴. The geometry panel generates initial row indices on H once; each G supplies the centers at those rows. The native panel generates fresh greedy starts on each G. G is fed directly to rounding. ACC uses Hungarian matching; NMI uses geometric entropy normalization. Both metrics and sample SD use the same complete seed set. Minimum-inertia starts are diagnostic, never score-selected winners.

The 32 core-hour and 24 wall-hour limits share all stages, including failures. At most two single-thread workers run; BLAS/OpenMP controls are inherited from the native resource guard. The last wall hour and 3,600 CPU seconds are reserved for closure. Evidence is exact and capped at 3,600 CPU seconds per cohort cumulatively across tau sensitivities. Primary and all remaining primary controls precede movement sensitivities. Optional development sensitivities require every primary candidate/control and exact alias to be qualified and matched. No score determines coverage expansion.

Confidence intervals use 10,000 paired bootstrap draws with seed 424242, conditional on the fixed cohort and embeddings. Fifty starts are not fifty independent datasets. Full macros require all eight qualified paired cohorts for the precise contrast, target and panel; otherwise available-case masks are explicit and identical for ACC/NMI. Different partial masks are not ranked.

Runtime source/environment hashes, exact initial indices, graph evidence, every finite output, dual, checkpoint and history are retained in the external content-addressed artifact store. The terminal manifest records the immutable numerical closure before label access. Committed scalar records support no-data table reconstruction.

Joint win/tie/loss summaries use a 10⁻¹² percentage-point numerical tie tolerance. A joint win has neither metric decreasing and at least one increasing; a joint loss has either metric decreasing. No metric or dataset is dropped to obtain a joint win. These summaries do not replace paired intervals.

Bootstrap intervals are pointwise and unadjusted across the many declared contrasts. They do not provide a familywise discovery guarantee. The verdict retains null and negative rows rather than selecting a favorable contrast.

## Numerical execution amendment 002

Before label access, the additional 200,000-iteration guard was replaced by a nonbinding 200,000,000 guard so the specified CPU caps control termination. Fixed-lambda continuation retains previous segments and their cumulative cost, with 570 solve seconds plus overhead within the original 600-second ceiling. Cached points are independently requalified for a stronger target. No objective, parameter, precision, movement or global resource gate changes. The initial protocol remains intact; [amendment 002](../../configs/extension_round3/amendments/002.json) records the effective override and source identities.

Resource totals measure additional execution in this round, including failed attempts. Reused round-two references and warm states have earlier generation costs recorded in that study; these totals are not a comparison of cold-start method runtimes.

## Numerical execution amendment 003

Strictly positive products w×anchor length can underflow before weighted ranking. Float64 log-domain sums now implement the same ranks in that case; no edge is dropped or objective weight changed. Unrepresentable raw masses retain their finite log values. Roundoff corrections to ranks are at most 10⁻¹² and recorded; the weighted-budget tolerance is unchanged. All previously stored allocations were checked for bit identity. The two pre-fit failures and their charges are retained. See [amendment 003](../../configs/extension_round3/amendments/003.json).

## Scheduling amendment 004

Secondary targets share each method/cohort's lambda path and cumulative caps. A completion barrier separates their existing target blocks, preserving the registered queue order while preventing concurrent writes to one path. Each block has unique paths. This orchestration repair preceded all secondary fits and terminal scores; no numerical source, completed output, parameter or resource limit changed. See [amendment 004](../../configs/extension_round3/amendments/004.json).

## Resource-accounting amendment 005 and deviations

A killed worker can consume CPU after its last committed path counter. A pre-scoring audit found cumulative native costs of 1,879.646 seconds for YaleB plain-pilot tubes and 1,859.512 seconds for MSRA shuffled-401 tubes, exceeding the 1,800-second path limit by 79.646 and 59.512 seconds. These are protocol deviations, not increased allowances. All outputs on both affected paths are conservatively excluded from qualified paired comparisons; arrays, separate numerical certificates and descriptive scores remain available. The global 32-core-hour budget includes every failed attempt and both overruns.

Remaining path allowances now use the complete native ledger across targets and attempts, rather than relying on a potentially stale internal path counter. Existing unaffected transition workers are stopped below the path cap if necessary. A regression check covers lost failed-work costs, target sharing and active reservations. No mathematical code, parameter, numerical gate, completed array or global deadline changes. [Amendment 005](../../configs/extension_round3/amendments/005.json) records the observed costs and exclusion policy before label access.
