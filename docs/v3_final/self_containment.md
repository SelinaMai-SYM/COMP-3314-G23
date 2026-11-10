> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# Self-containment

Runtime Python and YAML no longer embed a sibling `v1` or `v2` path.

- Benchmark files are read from `COMP3314_DATA_ROOT` or the untracked pointer `local/data_root.txt`.
- The v2 K-means loader reads `DATA_ROOT` or the untracked pointer `local/v1_worktree.txt`, and still appends `benchmarks/<name>/data`.
- `configs/v3/campaign.yaml` leaves `data_root` and `slps_pdf` blank.
- `configs/v3/resource_sources.yaml` does not point the SLPS PDF at another worktree.
- Loader errors no longer tell the user to run a script in another worktree.
- `method_extension/v3_theory` and `experiments/v3_theory` do not import another worktree.

Licensed images and the publisher PDF stay outside git. Their checksums are in `external_data_manifest.csv`. A checkout without the pointer fails with `FileNotFoundError` instead of searching a sibling directory.

Historical markdown under `docs/` still names earlier rounds. Those sentences are not import paths. `runs/` JSON from older rounds records the machine path that produced them; those artifacts are not the current loader.

`docs/v3/resource_probe.json` was locally modified before this round and still contains absolute paths. It is not part of the scientific commit.
