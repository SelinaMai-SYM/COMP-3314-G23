# Reproducibility and usage

The repository provides source code, exact parameter configurations,
historical and final scalar releases, artifact identities and report sources.
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
then generate report tables from the published scalar records. They require
neither image archives nor a scientific artifact root:

```bash
python -m experiments.v3_reproduction rebuild-results --release-manifest configs/final/release_manifest.json --output local/rebuilt_historical
python -m experiments.submission_refresh rebuild --config configs/submission_refresh/campaign.yaml --output local/rebuilt_joint
python experiments/submission_refresh/reporting.py --root .
```

Historical reconstruction, baseline/numerical/graph comparisons and final
source/subset selections remain distinct views. The [results](results.md)
retain separate eligibility pools, endpoints and locked-rounding outcomes.
The report generator reads the authoritative scalar records without selecting
new configurations or changing numerical qualifications.

A historical rebuild validates primary keys, hashes, complete seed groups and
selection consistency before replacing its own recognized output. It does not
read old Git objects or substitute a regenerated embedding for a saved
measurement. Report generation preserves the supplied metrics and
qualifications; it is not a fresh model fit or independent optimality audit.

Large CSVs may be committed solely as `.csv.gz`. Supported readers resolve the
unique representation and reject simultaneous plain/gzip copies. Input manifests
record actual stored-file hashes; release manifests retain uncompressed
identities where required. Lossless transport does not change metrics or
selection, and rebuilt outputs may be ordinary CSV.

## Rebuild final scalar releases

The final subset and scientific-evidence manifests bind the exact published
scalar inputs. These commands rebuild their statistical views without image
data, model fitting, an external object store or old Git objects:

```bash
python -m experiments.submission_refresh.current_release rebuild --release-manifest configs/subset_search/release_manifest.json --output local/rebuilt_subsets
python -m experiments.submission_refresh rebuild-evidence --config configs/submission_refresh/campaign.yaml --release-manifest configs/submission_refresh/evidence_manifest.json --output local/rebuilt_methods
```

The final releases identify their statistical inputs, source/parameter
inventories, trials and coverage. Manifest hashes distinguish original records
from public projections, including compressed and uncompressed identities
where declared.

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

Aggregation of a local scientific store is separate from scalar rebuilding.
The published final manifests bind the released statistical views; rebuilding
those views does not load scientific arrays or rerun models.

See [experimental protocol](experimental_protocol.md) before interpreting a
mean, native-best endpoint, oracle match or certified objective.

## Scientific artifacts

<!-- BEGIN ARTIFACT AVAILABILITY -->

### Verified archive and regeneration

The complete scientific archive is retained outside Git because it includes provider-restricted source-derived arrays. Its [verified public receipt](../results/submission_refresh/public_archive_receipt.v1.json) identifies the recovered bytes and object inventory. The committed public source/record projections retain separate original and public-payload hashes. Scalar rebuilding requires no private archive.

To regenerate arrays, obtain the exact provider files and prepared parent versions in [data setup](data.md), use the committed candidate manifests, and run the baseline and subset commands above with independent data/artifact roots. The additional fixed graph and EnSC designs are declared in `configs/submission_refresh/graph_queue.json` and `configs/submission_refresh/ensc_formal_queue.json`; pass each file to the same experiment command with `--queue`. Their oracle diagnostic and coefficient-validation qualifications are part of the protocol. Restricted data availability and source-identity limitations remain explicit rather than being replaced by inferred substitutes.

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
