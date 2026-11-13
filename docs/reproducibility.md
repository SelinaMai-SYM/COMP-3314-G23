# Reproducibility

Install the project using the [README commands](../README.md#installation). All commands below run from the repository root. Statistical reconstruction reads committed measurements; fitting requires separately acquired provider data. Technical namespaces such as `v3_reproduction` identify Python modules and require no other branch or checkout.

## Rebuild statistical tables

Use fresh output directories. Each manifest verifies its inputs before publishing reconstructed output.

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

Compressed records carry stored-file and decompressed hashes where declared. CSV readers resolve a unique plain or gzip representation. Mean/sample SD, best-native assignment and independent repeatability batches remain separate endpoints. See [experimental protocol](experimental_protocol.md).

## Small examples

```bash
python examples/ssc_blobs.py
python -m experiments.v3_reproduction smoke --dataset synthetic
```

The first calls the public SSC estimator. The second checks a two-node primal–dual problem through the maintained experiment entry point.

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

## Figures, report and numerical checks

```bash
python -m scripts.result_tables --update-readme --report-output report/tables/edge_deletion_main.tex
python experiments/submission_refresh/reporting.py --root .
make -C report PYTHON=python
python -m pytest -q tests/extension_round3 tests/extension_round2 tests/extension_verification tests/next_round
```

The report build uses the same committed statistical records as the README and benchmark pages. The [build guide](../report/README.md) lists the TeX dependencies. The numerical tests include small independent convex references; fitting a real benchmark additionally requires its declared data source.
