# Reproducibility

Install the project using the [README commands](../README.md#installation). All commands below run from the repository root. Statistical reconstruction reads committed measurements; fitting requires separately acquired provider data. Technical namespaces such as `v3_reproduction` identify Python modules and require no other branch or checkout.

## Rebuild statistical tables

Use fresh output directories. Each manifest verifies its inputs before publishing reconstructed output.
The full source/subset and baseline rebuild interfaces restore archived scalar
metadata automatically, byte-for-byte at its original paths. The restored files
are ignored by Git; no old branch or external numerical store is needed.

```bash
python -m experiments.evidence verify
python -m experiments.evidence prepare
```

The explicit preparation command is useful before direct Python access to the
complete candidate catalogue, sample manifests or historical trial inventories.
The [archive guide](../results/evidence/README.md) describes its scope and checks.

```bash
python -m experiments.v3_reproduction rebuild-results \
  --release-manifest configs/final/release_manifest.json --output local/tables/historical
python -m experiments.submission_refresh rebuild \
  --config configs/submission_refresh/campaign.yaml --output local/tables/joint-historical
python -m experiments.submission_refresh.current_release rebuild \
  --release-manifest configs/subset_search/release_manifest.json --output local/tables/subsets
python -m experiments.submission_refresh rebuild-evidence \
  --config configs/submission_refresh/campaign.yaml \
  --release-manifest configs/submission_refresh/evidence_manifest.json --output local/tables/baselines-graphs
python -m experiments.extension_verification rebuild \
  --release-manifest configs/extension_verification/release_manifest.json --output local/tables/unsquared
python -m experiments.extension_round2.release \
  --release-manifest results/extension_round2/release_manifest.json --output local/tables/quadratic
python -m experiments.extension_round3 rebuild \
  --release-manifest results/extension_round3/release_manifest.json \
  --output local/tables/edge-deletion --figures
python -m scripts.result_tables --output local/tables/overview.md
```

The historical release preserves both fixed references and the ACC-only closest-display endpoint. The joint reconstruction computes ACC/NMI discrepancy using the declared tie breaks. The subset release recomputes matched selections, fixed-protocol distributions and coverage from trial records. The refinement releases retain their distinct operating points, qualified masks and paired intervals. No reconstruction requires image archives, an external artifact store or old Git objects.

The matched-SC summary is stored losslessly as `matched_sc_summary.csv.gz`; its
release entry pins both transport and uncompressed identities. Earlier audit
hashes in frozen cohort locks describe the release at input registration.

Compressed records carry stored-file and decompressed hashes where declared. CSV readers resolve a unique plain or gzip representation. Mean/sample SD, best-native assignment and independent repeatability batches remain separate endpoints. See [experimental protocol](experimental_protocol.md).

## Small examples

```bash
python examples/ssc_blobs.py
```

This calls the public SSC estimator on a generated dataset.

## Main SSC and baseline experiments

Place provider files under `local/data` using [data setup](data.md). These commands use independent artifact/output directories:

```bash
python -m experiments.v3_reproduction run-experiments \
  --config configs/v3/campaign.yaml --data-root "$PWD/local/data" \
  --output "$PWD/local/ssc-runs" --resume
python -m experiments.submission_refresh run \
  --config configs/submission_refresh/campaign.yaml --data-root "$PWD/local/data" \
  --artifact-root "$PWD/local/artifacts/baselines" --output local/baseline-results --resume
```

The first grid covers the historical methods and SSC E8/E13 settings. The second queue contains the named LDA, SLPS and MSRA controls. Graph ablations use the same runner with `--queue configs/submission_refresh/graph_queue.json`. Source/subset sensitivity uses the frozen catalogue and executable cohort:

```bash
python -m experiments.subset_search run \
  --config configs/subset_search/protocol.yaml --data-root "$PWD/local/data" \
  --artifact-root "$PWD/local/artifacts/subsets" --resume
```

The catalogue fixes sample membership and original row IDs. Each changed subset rebuilds its graphs and representation. Coverage, failed points and all unrun hypotheses remain in the released configuration records. Resume verifies identities and cumulative limits; a new directory does not turn an archived finite trajectory into a newly measured historical result.

## Refinement experiments

Unsquared E1–E3 use their own frozen dataset registration and mechanism gates:

```bash
python -m experiments.extension_verification freeze \
  --config configs/extension_verification/protocol.yaml --data-root "$PWD/local/data" \
  --artifact-root "$PWD/local/artifacts/unsquared"
python -m experiments.extension_verification verify \
  --config configs/extension_verification/protocol.yaml --artifact-root "$PWD/local/artifacts/unsquared"
python -m experiments.extension_verification run \
  --config configs/extension_verification/protocol.yaml --data-root "$PWD/local/data" \
  --artifact-root "$PWD/local/artifacts/unsquared" --resume
```

The [quadratic comparison guide](extension_round2/README.md) provides the E1_v2/E4/E5/E6 phases. The [edge-deletion guide](extension_round3/README.md) provides E7/E1_v3/E5_v2 fitting and controls. Exact replay uses the arrays identified by each input lock, including storage layout. Rebuilding an eigenspace from raw data can change its numerical representation and receives a new run identity.

## Numerical artifacts

Scalar measurements and sample manifests are committed. Provider-derived matrices, predictions, feasible duals, histories and continuation checkpoints are held in content-addressed external stores because their data terms can restrict redistribution. The [edge-deletion archive receipt](../results/extension_round3/artifact_receipt.json), [quadratic inventory](../results/extension_round2/artifact_manifest.json) and [baseline/refinement receipt](../results/submission_refresh/scientific_archive.v2.json) identify their separate scopes. These are integrity records for externally held objects, not download links.

With a legally obtained edge-deletion archive at `local/edge-deletion.scientific.tar.gz`, recover its exact inputs and states:

```bash
python -m experiments.extension_round3.artifacts recover \
  --archive local/edge-deletion.scientific.tar.gz --output local/recovered-edge-deletion
```

The archive includes the earlier input-provider endpoints and their recursive numerical objects. It can supply the `--input-artifact-root` required for a fresh edge-deletion replay. Recovery verifies each member before replacing the destination. Scalar table reproduction remains independent of archive availability. Cumulative fitting ledgers and numerical-freeze markers remain attached to recovered studies.

## Generated displays and numerical checks

```bash
python -m scripts.result_tables --update-readme \
  --historical-output docs/reconstruction_tables.md \
  --development-output docs/development_summary.md
python -m pytest -q tests/test_ssc.py tests/test_shared_spectral_embedding.py \
  tests/test_metrics.py tests/extension_round3 tests/extension_round2 \
  tests/extension_verification tests/next_round
```

The exact slide 6.2 PNG is retained in `docs/figures/`; no redraw is required.
The selected table and reconstruction displays are generated from committed
scientific measurements. The historical seed inventory also retains
`results/v3_theory/all_trials.csv` to verify that confirmation seeds are unused;
this historical record is not selected-extension evidence.
