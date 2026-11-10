# Dataset-subset uncertainty and retrospective numerical matching

Original sample indices were unavailable. The catalogue fixes membership, row order, preprocessing and aliases before scoring. Joint ACC/NMI selection identifies a closest evaluated numerical match; it does not establish historical identity, generalization or unbiased superiority.

```bash
python -m experiments.subset_search catalogue --config configs/subset_search/protocol.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT
python -m experiments.subset_search run --config configs/subset_search/protocol.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT --resume
python -m experiments.subset_search aggregate --artifact-root ARTIFACT_ROOT
python -m experiments.subset_search confirm --artifact-root ARTIFACT_ROOT
```

The executable cohort is frozen after label-blind timing profiles. The full intended catalogue and all unrun entries remain visible. Random prefixes come from10,32,100. Large finite cohorts use permutation seed20261110. Diagnostic parents cannot compete as paper-compatible reconstructions. Aliases do not multiply independent observations.

Changed membership always rebuilds A,F,W,G. Fixed sensitivity uses Y0/E8/gamma1/random. Joint matching uses E8/E13, five nominal gamma values and three rounding protocols. Both metrics use all50 declared seeds; sample SD has ddof1. A native-best-of50 assignment has no across-run SD. Additional rounding uses saved arrays and never reselects.

The required trials.csv content is transported as trials.csv.gz to remain below Git file limits. Decompress with `gzip -dc results/subset_search/trials.csv.gz > trials.csv`. Complete summaries, top10 pools and fixed-protocol distributions retain both endpoints. Scientific objects live in a durable external store. Artifact manifests supply verified content addresses and regeneration commands.

All4736 intended candidates were fixed before scores. The initial executable cohort contains1202 canonical inputs, with complete100-seed random families and the full UMIST omission family. ARcommon masks are deferred until mandatory repairs, broader subset coverage and graph diagnostics have received their provision. A bounded full-USPS profiling attempt timed out; its cost and failure remain visible. Per-candidate caps are recorded before scoring, including the larger full-USPS cap.
