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

### Numerical objects and historical lineage

Current result manifests identify saved numerical objects or an independently
runnable regeneration procedure. Restricted source-derived arrays stay outside
Git. The current public source-lineage receipts preserve opaque identities from
an earlier verified private recovery; they do not advertise a downloadable
archive or assert that an earlier package contains the current filtered project.
Original and filtered public-payload hashes are distinct.

Retained baseline, subset, numerical and oracle-diagnostic measurements rebuild
from their versioned committed scalar inputs. Obtain exact provider files from
[data setup](data.md) before regenerating arrays. The fixed graph diagnostic queue
is `configs/submission_refresh/graph_queue.json`, consumed by the existing
experiment command with `--queue`. New refinement fits use the independently
registered campaign below. New artifacts include optimized G, actual rounding Q,
duals, predictions, histories and continuation state. Resume checks the frozen
input, graph, objective, parameter, code and environment identities.

```bash
python -m experiments.extension_verification report --config configs/extension_verification/protocol.yaml --artifact-root ARTIFACT_ROOT --output results/extension_verification
python -m experiments.extension_verification rebuild --release-manifest configs/extension_verification/release_manifest.json --output local/rebuilt_extensions
```



## Source quality and report

```bash
python -m pytest tests/submission_refresh tests/extension_verification tests/next_round
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

## Scientific state and archive recovery

The current clean inventories cover retained baseline states, G1–G3, USPS,
subset numerical objects and the independent refinements. Original numerical
object identities are preserved; original mixed source-body packages and
execution logs are outside the advertised closure. The full subset inventory is
available as a durable local content-addressed store, separately from the scoped
refinement/state archive. Provider-derived arrays remain outside Git.

```bash
python -m experiments.submission_refresh.export_artifacts export --artifact-root ARTIFACT_ROOT --archive ARCHIVE --manifest results/submission_refresh/artifact_manifest.json --manifest results/submission_refresh/state_artifact_manifest.v2.json --manifest results/extension_verification/artifact_manifest.json
python -m experiments.submission_refresh.export_artifacts recover --archive ARCHIVE --output RECOVERED_ARTIFACT_ROOT
python -m experiments.extension_verification run --config configs/extension_verification/protocol.yaml --artifact-root RECOVERED_ARTIFACT_ROOT --resume
```

Recovery verifies every archive member before publishing the destination. It
restores input registration, predictions, duals, step sizes, best feasible points,
continuation identities and typed scientific metadata. A recovered resource ledger
preserves a conservative charge against the existing allowance. It is not a new
compute allocation. The release's scalar rebuild requires neither the archive nor
the provider arrays; a self-contained release manifest is also generated beside
the compressed scalar packet.
