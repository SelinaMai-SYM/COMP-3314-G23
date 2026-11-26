# Scalar evidence archive

[scalars_and_metadata.tar.gz](scalars_and_metadata.tar.gz) contains 4,746 original
scalar and metadata files, with exact paths, lengths and SHA-256 hashes in the
[archive index](../../configs/final/evidence_archive.json). The archive and its
decompressed tar stream are also hash-locked. It contains no dataset images,
feature matrices, fitted embeddings or other numerical arrays.

| Evidence | Role |
|---|---|
| Complete candidate catalogue and 4,736 sample manifests | Original row IDs, ordering, exclusions, quotas, aliases, source fingerprints and all evaluated/unevaluated input hypotheses |
| Full execution coverage and fixed-protocol summaries | Complete, failed, timed-out and unrun combinations |
| Historical v2 and secondary trial records | Original measurements and confirmation-seed namespace checks |
| Joint configuration/native endpoint projections and baseline seed coverage | Separate metrics, sample SD, endpoints and complete seed identities |
| Historical configuration projection | Full grid behind the fixed and closest historical displays |
| State artifact inventory | Hashes and relative identities of separately held numerical objects; this inventory is not a public download of those objects |

## Verify or restore

From the checkout root:

```bash
python -m experiments.evidence verify
python -m experiments.evidence prepare
```

Preparation verifies the complete archive and every member before restoring any
missing file. Existing conflicting files are preserved and reported as errors.
Original paths and bytes are unchanged, so existing release manifests, dataset
locks and numerical source fingerprints retain their meanings. Full source/subset
and baseline CLI rebuilds prepare their required scalar evidence automatically.
Materialized files are ignored by Git.

The [pre-consolidation tag](https://github.com/SelinaMai-SYM/COMP-3314-G23/tree/submission-evidence-20261126)
retains the original scientific evidence boundary at commit
`e4d8b913e00926f30b61f164bc55cb725c72b54b`. The active archive is sufficient for
restoration; rebuilding does not read that tag or any old Git object.

The complete compressed SSC trial tables, compact final comparisons, both
extension panels and control records remain separately committed. See
[reproducibility](../../docs/reproducibility.md) for no-data rebuilding and the
availability of external provider-derived numerical states.
