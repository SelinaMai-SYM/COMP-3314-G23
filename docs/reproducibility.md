# Reproducibility and usage

The repository provides source code, exact parameter configurations, the
historical scalar release, completed flat statistical records and report sources.
Rebuilding published statistical tables is separate from fitting models on
provider data. Technical module names
such as `v3_reproduction` and `submission_refresh` are stable interfaces, not
dependencies on another Git branch.

## Install

Use Python 3.13 and the pinned dependency file from the checkout root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r environment/requirements.lock.txt
```

Project imports and `python -m` commands work from the checkout root. Report
table generation also supports direct script execution without an editable
installation. [Data setup](data.md) describes the independent data directory.

## Rebuild published scalar results

These commands rebuild the historical release and joint historical selection,
then generate report tables from the completed flat CSV/JSON records in this
edition. They require neither image archives nor a scientific artifact root:

```bash
python -m experiments.v3_reproduction rebuild-results --release-manifest configs/final/release_manifest.json --output local/rebuilt_historical
python -m experiments.submission_refresh rebuild --config configs/submission_refresh/campaign.yaml --output local/rebuilt_joint
python experiments/submission_refresh/reporting.py --root .
```

Historical reconstruction, completed baseline/numerical/graph comparisons and
final subset results are distinct views. The first two are published here; final
subset selections and their locked-rounding results have a
[reserved section](results.md#final-sourcesubset-results). The report generator
uses available completed records and preserves that reservation.

A historical rebuild validates primary keys, hashes, complete seed groups and
selection consistency before replacing its own recognized output. It does not
read old Git objects or substitute a regenerated embedding for a saved
measurement. Flat report generation preserves the supplied metrics and
qualifications; it is not a fresh model fit or independent optimality audit.

Large CSVs may be committed solely as `.csv.gz`. Supported readers resolve the
unique representation and reject simultaneous plain/gzip copies. Input manifests
record actual stored-file hashes; release manifests retain uncompressed
identities where required. Lossless transport does not change metrics or
selection, and rebuilt outputs may be ordinary CSV.

## Final release interfaces

The final subset/scalar-evidence release manifests are not supplied as completed
releases in this edition. The following interfaces are reserved for use with
their published, hash-verified final manifests; they are not current setup or
rebuild steps:

```bash
python -m experiments.submission_refresh.current_release rebuild --release-manifest configs/subset_search/release_manifest.json --output local/rebuilt_subsets
python -m experiments.submission_refresh rebuild-evidence --config configs/submission_refresh/campaign.yaml --release-manifest configs/submission_refresh/evidence_manifest.json --output local/rebuilt_methods
```

Each final release must identify its exact statistical inputs, source/parameter
inventory, trials and coverage. A public presentation marker or flat table is
not a substitute for a final release manifest.

## Synthetic example and experiments

```bash
python -m experiments.v3_reproduction smoke --dataset synthetic
```

For experiments, supply `DATA_ROOT` and a separate writable `ARTIFACT_ROOT`:

```bash
python -m experiments.submission_refresh run --config configs/submission_refresh/campaign.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT --resume
python -m experiments.subset_search run --config configs/subset_search/protocol.yaml --data-root DATA_ROOT --artifact-root ARTIFACT_ROOT --resume
```

Configuration files specify inputs, grids and rounding conventions. Resume
verifies data, parameters, code/environment identities and saved checkpoints;
it does not replace existing measurements under the same identity. Dataset
hashes and scientific output identities accompany the results. Resource limits
bound the evaluated design, and coverage records distinguish complete,
unsuccessful and unevaluated configurations. A complete endpoint requires every
declared seed.

Aggregation of a complete local scientific store is a separate source-data
operation. Final published subset/scalar releases must bind those outputs to
their final manifests before their reserved rebuild interfaces apply.

See [experimental protocol](experimental_protocol.md) before interpreting a
mean, native-best endpoint, oracle match or certified objective.

## Scientific artifacts

<!-- BEGIN ARTIFACT AVAILABILITY -->
### Archive availability

This edition publishes scalar records, source/configuration identities and data
preparation instructions. A downloadable scientific matrix/checkpoint archive
and its final recovery receipt are reserved for the final artifact release.
No archive download or completed recovery is claimed here.

The final availability statement must provide a distributable location and
verified member manifest, or an exact regeneration procedure where provider
terms restrict redistribution. Scientific artifacts include representations,
graphs, predictions, duals, projections and checkpoints. Their content-addressed
identities remain distinct from the scalar tables.

The exporter/recovery interfaces below are reserved for a complete local store
and its final verified archive; they are not current download instructions:

```bash
python -m experiments.submission_refresh.export_artifacts export --artifact-root ARTIFACT_ROOT --archive ARTIFACT_ARCHIVE.tar.gz
python -m experiments.submission_refresh.export_artifacts recover --archive ARTIFACT_ARCHIVE.tar.gz --output RECOVERED_ARTIFACT_ROOT
```

Recovery verifies member paths, declared members, sizes and hashes. Provider-data
conditions also apply to derived artifacts. Historical rebuilding and completed
flat report generation above require no such archive.
<!-- END ARTIFACT AVAILABILITY -->

## Source quality and report

```bash
python -m pytest tests/submission_refresh tests/next_round
make -C report
```

The source checks cover metric conventions, seed completeness, certificates,
baseline state consistency, source separation, deterministic selection and
artifact/CSV integrity. Data-dependent checks require the declared source files;
they are distinct from synthetic checks. Ordinary test source is included with
the implementation.

The [report](../report/Group_23.pdf), [report build guide](../report/README.md),
[results](results.md) and [benchmark tables](../results/submission_refresh/per_benchmark/)
provide the interpretation of the rebuilt records.
