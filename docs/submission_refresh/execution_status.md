# Execution checkpoint

The `--config` interface selects this frozen campaign contract. Both the supplied file and canonical `configs/submission_refresh/campaign.yaml` must match the pinned bytes before campaign inputs, artifacts or workers are accessed. A byte-identical copy is valid; unsupported settings, extra keys and formatting changes fail explicitly. The frontend does not claim to apply arbitrary resource or method-grid overrides. A different configuration requires a separately versioned campaign; the frozen scientific settings and cache identities remain unchanged.

The frozen candidate catalogue and shared adapters were committed as `219681d`. The working tree contains the English/editorial and report refresh in progress. Formal baseline jobs are active through the shared scheduler; the blinded USPS full-grid profile remains separately ineligible for selection.

Durable task status, exact seed checkpoints, pending queues and object references are in `ARTIFACT_ROOT/task_status`, `ARTIFACT_ROOT/queues`, `ARTIFACT_ROOT/baseline`, and `ARTIFACT_ROOT/subset`. The independent object root is the sibling `independent-data/scientific-artifacts/refresh-20261110` recorded in preflight. The ledger is `resource_ledger.json` at that root. Do not run a second campaign with a new budget ledger.

Resume mandatory work:

```bash
python -m experiments.submission_refresh run --config configs/submission_refresh/campaign.yaml --queue configs/submission_refresh/execution_queue.json --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT --resume
```

Then run the predeclared subset cohort. Graph diagnostics follow primary-family coverage; weak AR common masks come last. All selected means require 50 complete seeds, and subsequent confirmation does not reselect. Historical scalar selection has already rebuilt successfully from the immutable gzip release. Final tables/PDF/publication are pending actual campaign completion.

MSRA's first real repair task executes its preregistered K-means/SC/SSC block before LDA, PCA, LLC or SLPS. It uses the same native dataset candidate and exact shared subset protocol, then records that nested work as charged to its owning baseline task. The later subset queue reuses those recoverable objects. No second resource allowance is created.
