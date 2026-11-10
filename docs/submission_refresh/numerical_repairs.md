# Numerical repairs and corrected graph diagnostics

The historical experiment records and the old 0/4 gate remain unchanged. Current diagnostics use schema 2; the old field `within_class_components_mean` counted how many whole-graph components covered each class. That quantity did not measure connectivity within a class. The replacement computes connected components of `W[idx][:, idx]` for every class, including isolated vertices, and records class counts, mean counts, total excess fragments, largest-component fractions, and isolate counts. The former quantity is retained as `whole_graph_components_covering_class_mean`.

The regression graph 0--1--2 with labels [0,1,0] has one whole-graph component, but class-induced counts [2,1], mean 1.5, and one excess fragment. A hash-verified correction can be generated without refitting or rewriting measurements:

```bash
python -m experiments.submission_refresh.correct_graph_diagnostics \
  --cache-root /path/to/recovered/next_round/cache \
  --jobs-root results/next_round/jobs \
  --output results/submission_refresh
```

The command checks recovered F, W, labels, and each reconstructed fitted graph against historical job hashes before writing a new schema-2 table. It also audits upstream A once per recovered cache folder after checking A, input X, labels, and saved metadata hashes. A rows explicitly use edge lengths in X; W rows use edge lengths in F. Their graph roles, pollution rates, and geometry remain separate. Missing or mismatching artifacts remain explicit failures. Original schema-1 records retain their original hashes.

## Edge deletion can destroy force cancellation

For eight equally spaced points on the unit circle and an eight-cycle graph with unit weights, no incident edge has zero length. At G=F, the largest norm of the summed unit-edge directions gives an exact unsquared-fidelity threshold

`gamma0 = 1 / (4 sin(pi/8)) = 0.6532814824381882`.

Delete edge (0,1). Each of its former endpoints has one incident unit direction, and the threshold becomes 0.5. Thus at gamma 0.6, G=F is certified for the full cycle but is not optimal after deletion. An independently converged convex solve of the edited problem lowers its objective. The prior universal deletion claim was false and has been corrected in the historical interpretation documents; the old measured gate result is not changed.

A different sufficient bound remains valid: `2 gamma max_i sum_j w_ij <= 1`. The triangle inequality bounds the total possible edge-cost reduction by the fidelity cost. Deleting edges preserves this sufficient bound when it held initially. This bound does not establish the false universal implication, because it need not hold for an original graph whose incident forces cancel.

## Feasible dual retention and diagonal PDHG

The solver now evaluates a supplied initial dual with the existing feasible-certificate routine before any update. It keeps the better of its bound and the zero bound, together with the actual feasible q. The iteration-zero history records this lower bound. A lower bound is retained even when the subsequent solver is interrupted or returns no better dual.

The optional diagonal formulation uses `K = diag(sqrt(w)) B`. Its p capacities are `2 gamma sqrt(w)`, and the original dual is `q = diag(sqrt(w)) p`, with capacities `2 gamma w`. Set `T_i = 0.99 / sum_e |K_ei|` and `Sigma_e = 0.99 / sum_i |K_ei|`; an isolated node uses T_i=1. The Schur bound gives `||Sigma^(1/2) K T^(1/2)|| <= 0.99`. In original q coordinates this is exactly `q += (0.99 sqrt(w)/2) * B Gbar`. Both formulations use the same original primal objective and feasible lower bound. Small weighted-chain problems with unsquared, Huber, and squared fidelity are checked against independent CLARABEL convex solutions. This is a numerical optimizer repair, not a change to SSC or a guarantee of improved ACC/NMI.

`solve(..., return_checkpoint=True)` exposes actual final primal/dual iterates separately from the best primal and feasible dual. Passing a saved same-objective primal/dual back is a valid warm restart; it is not represented as an identical continuation of an uninterrupted accelerated trajectory. The optional `cpu_time_limit` is checked alongside the existing wall limit. Certified status still requires relative gap <=1e-5 and edge/node capacity violations <=1e-8.

## Bounded USPS audit

`experiments.submission_refresh.usps_audit.audit_pair` freezes one exact F/W pair. For each effective E8 gamma in {1,1000}, it records IRLS with 300 updates, uniform PDHG, diagonal PDHG, a componentwise weighted-Laplacian dual-flow candidate, and a diagonal same-objective warm restart. IRLS instrumentation observes the existing solver and its actual CG calls without changing accepted steps. It records relative residuals, CG return codes and iteration counts, symmetry, and diagonal/Gershgorin diagnostics. Positive diagonal S plus a nonnegative-weight Laplacian establishes the linear subproblem's positive definiteness; a rounded Gershgorin lower bound alone is not an SPD test.

The componentwise flow solves `B.T diag(w) B z = target`, forms `q = diag(w) B z`, and checks its actual edge capacities and node norm constraints. Targets are balanced within components because graph divergence sums to zero. A failed flow or a large gap does not prove that no feasible certificate exists. A component-consensus primal is an upper bound; only the measured feasible primal-dual gap can certify it. Unsquared fidelity is not strictly convex, so certification of a fused candidate does not prove uniqueness or stable rounding of nearby solutions.

Each full attempt is capped at 1,800 CPU seconds, the flow at 300 CPU seconds, and the full local block at six CPU hours, subject to the caller's shared ledger. Reduced limits must be fixed before evaluation and remain visible in the output. The module accepts no true labels and saves arrays, checkpoints, scalar histories, exact F/W identities, and failure statuses. It does not replace locked historical-style candidate winners with improved outputs.

## Verification performed

The focused numerical and existing certificate suite passed 15 tests in 1.57 seconds with one BLAS/OpenMP thread. A small synthetic end-to-end audit completed all five stages in 0.023 process-CPU seconds. These are implementation checks, not real USPS results. The orchestrator records subsequent real-data attempts and their resource use separately.
