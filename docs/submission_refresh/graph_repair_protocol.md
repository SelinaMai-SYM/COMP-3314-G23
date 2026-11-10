# Fixed-representation graph diagnostics

This module implements the predeclared G1-G3 diagnostics. It does not replace the
historical capped-fusion mechanism gate, whose 0/4 result remains unchanged. Its
inputs are the full ORL and cropped2414 YaleB development benchmarks under Y0,
independent of retrospective subset-search winners. The configuration is frozen
in `configs/submission_refresh/extension_protocol.yaml`.

`experiments.submission_refresh.graph_repair.intended_tasks()` enumerates 362
configuration records: one G1 casebook, 24 G2 rows and 156 G3 rows for each of the
two benchmarks. Gamma-zero graph-arm rows reuse the same SC solution on the
corresponding anchor. Other identical mathematical problems share a
content-addressed fit rather than being solved again. This is a catalogue count,
not a statement that those configurations have been executed.

The root scheduler calls `run_graph(task, data_root, artifact_root)` after obtaining
a reservation from the shared ledger. A task specifies `phase`, `dataset` and
`cpu_limit`, and can restrict G2 to one `anchor`, `graph` and `gamma`, or G3 to one
`addition_fraction`, `arm` and `gamma`. Omitting selectors runs the full frozen
phase and remains subject to the caller's process CPU allocation. No worker pool
or separate compute budget exists inside this adapter. Profiles fit without
invoking ACC/NMI or an oracle edit function and are ineligible for selection.

Fixed inputs are keyed by source implementation hash and the exact processed X/y
object hashes. Every cached mathematical problem also includes anchor, fitted
shrinkage graph, gamma, solver settings and CPU cap. Metadata and arrays remain
outside Git in the shared artifact store. Expensive convex fits are checkpointed
before rounding. Each of the fifty paired greedy Lloyd rounds has a checkpoint,
including predictions and centers, so an interruption during rounding does not
require solving SSC again. Raw and mass-matched graphs, anchor, G, dual, last and
best solver states and scalar histories are recoverable.

G1 uses gamma 1 on the same F0/W0 as matched SC. The full casebook retains every
sample and paired seed, class confusions and per-class accuracy, pairwise false
merge/split rates, row norms, weighted and count degrees, wrong-edge counts and
mass, and nearest neighbors in raw/angular spectral coordinates. Row-norm and
weighted-degree quintiles use fixed 20/40/60/80 percent quantiles with a declared
tie convention. Illustrative sample IDs are the first source row in each seed-zero
correctness category. The upstream A and shrinkage W diagnostics are separate.

G2 crosses anchor F0 or row-normalized U with graph W0 or angular Wa, with gamma
`[0,.001,1,10,1000,1e6]`. Exactly zero F0 rows remain zero and are isolated in Wa.
Graphs are matched to W0's undirected total mass, with raw mass and scaling
reported. A zero total affinity is retained as `DEGENERATE_AFFINITY`; it is not
replaced by another graph. Equal mass does not imply equal force or movement.
SC is evaluated on both anchors.

G3 freezes the label-blind union of top-20 neighborhoods in raw F0, row-L2 input
features and angular U. Ties use source-row indices. Self pairs and existing W0
edges are excluded from additions. The pool's exact pairs, angular distances,
space-membership masks and hash are saved before oracle construction. Addition
caps are floor(15% or 5% of original undirected edge count), with at most two new
incident edges per node and the median positive W0 weight on each addition.
The oracle adds only same-class pairs joining different components of the graph
after cross-class deletion. That exact addition set is reused in the add-only
arm. Graphs are mass-matched, and failed matched controls are explicitly infeasible.

The gate comparator is **fixed Oracle deletion plus blind random additions**,
averaged over seeds 400-402 within each rounding seed. Same-class random additions
without component preference and fully randomized deletion/addition are reported
as separate diagnostics. Each random control matches the actual Oracle addition
count and the declared degree/weight constraints, with at most 100 generation
attempts. They cannot silently substitute a smaller edit set.

Only the 15% budget and effective gamma 1000 enter the promotion gate. Both the
delete and delete+completion solutions must be certified and have normalized L21
movement above `1e-6`. Completion must add at least one ACC percentage point,
not decrease mean NMI, reduce class-induced excess fragments by at least 20%, and
have positive lower paired ACC interval endpoints versus deletion and versus the
mean blind-addition control. Blind-control solver statuses are reported beside the
gate; their certification is not an additional hidden pass condition. Intervals
use 10,000 percentile bootstrap resamples with seed 424242 over the fifty paired
rounding seeds. They concern fixed data and representations, not independent
benchmark draws. Missing rows, infeasible controls and uncertified primary
contrasts remain distinct from a measured gate failure.

A passed gate in at least one development benchmark is necessary for the frozen
EnSC G4/G5 study. This implementation does not invent another performance gate or
launch Huber, capped-fusion or heat grids. Actual execution and reasons for any
unrun rows belong in the shared coverage, gate and resource outputs. The presence
of an implementation alone provides no evidence that graph repair improves ACC.
