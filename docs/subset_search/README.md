# Dataset-subset uncertainty and retrospective numerical matching

Original sample indices were unavailable. The catalogue fixes membership, row order, preprocessing and aliases before scoring. Joint ACC/NMI selection identifies a closest evaluated numerical match; it does not establish historical identity, generalization or unbiased superiority.

```bash
python -m experiments.subset_search catalogue --config configs/subset_search/protocol.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT
python -m experiments.subset_search run --config configs/subset_search/protocol.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT --resume
python -m experiments.subset_search aggregate --artifact-root ARTIFACT_ROOT
python -m experiments.subset_search confirm --artifact-root ARTIFACT_ROOT
```

The executable cohort is frozen after label-blind timing profiles. The full intended catalogue and all unrun entries remain visible. Random prefixes come from 10, 32 or 100. Large finite cohorts use permutation seed 20261110. Diagnostic parents cannot compete as paper-compatible reconstructions. Aliases do not multiply independent observations.

Changed membership always rebuilds A, F, W and G. Fixed sensitivity uses Y0/E8/gamma 1/random. Joint matching uses E8/E13, five nominal gamma values and three rounding protocols. Both metrics use all 50 declared seeds; sample SD uses ddof=1. A native-best-of-50 assignment has no across-run SD. Additional rounding uses saved arrays and never reselects.

The required trials.csv content is transported as trials.csv.gz to remain below Git file limits. Decompress with `gzip -dc results/subset_search/trials.csv.gz > trials.csv`. The two endpoints remain separate in summaries and top-ten lists; fixed-protocol distributions are also retained. Scientific objects live in a durable external store. Artifact manifests supply verified content addresses and regeneration commands.

All 4,736 intended candidates were fixed before scores. The initial executable cohort contains 1,202 canonical inputs, with all 100 predefined seeds in each random family and the full UMIST omission family. AR common masks are deferred until resources have been allocated to mandatory repairs, broader subset coverage and graph diagnostics. A bounded full-USPS profiling attempt timed out; its cost and failure remain visible. Per-candidate caps are recorded before scoring, including the larger full-USPS cap.

The additional-rounding seed namespace is frozen before the first confirmation
fit. Its audit scans current tracked historical result CSV/gzip, JSONL and JSON
records for actual ACC/NMI rows with rounding-seed fields, including the v2,
v3 reproduction, next-round and v3-theory raw trials. The audit records source
hashes, observed columns, counts and ranges. Static sample manifests and this
campaign's own confirmation files are excluded. The first unused aligned
50-seed block at or above 1,000,000 is bound to the exact winner-lock hash and
persisted in both the durable artifact store and committed scalar outputs.
Resume reuses that block, verifies the frozen historical source hashes and
rejects a changed winner lock; existing confirmation results never trigger a
new seed choice.
