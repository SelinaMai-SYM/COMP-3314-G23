# Exact edge-deletion evidence for Spectral Shrunk Clustering

This independent study tests whether correcting an edge's own smoothing influence improves selective contraction. Three convex refinements use the same frozen evidence at alternative insertion points: graph weights, stopping distances, or triangle-slack guards. They are compared with mass-matched plain-pilot, uniform and shuffled controls. No interventions are stacked.

The inputs are the eight unchanged, retrospectively selected round-two report cohorts. This is conditional development evidence. The MSRA input is the native 16×16 EBSA proxy and retains its source-identity qualification. Earlier result tables, the submission report and presentation are unchanged.

| Registered candidate | Table/configuration alias |
|---|---|
| `R3_E7_CAVITY_GRAPH` | `R3_E7_CAVITY` |
| `R3_E1_V3_SELECTIVE_TUBE` | `R3_E1_V3_CAVITY` |
| `R3_E5_V2_SELECTIVE_GUARD` | `R3_E5_V2_CAVITY` |

[Method and proofs](method_design.md) · [Protocol](experiment_protocol.md) · [Novelty audit](novelty_audit.md) · [Excluded candidates](rejected_candidates.md) · [Results](../../results/extension_round3/summary.md) · [Scientific interpretation](interpretation.md)

## Installation and inputs

Use Python 3.13 and the recorded dependencies in [requirements.lock.txt](../../configs/extension_round3/requirements.lock.txt):

```bash
git clone --single-branch --branch extension_round3 https://github.com/SelinaMai-SYM/COMP-3314-G23.git ssc-round3
cd ssc-round3
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r configs/extension_round3/requirements.lock.txt
python -m pip install --no-deps -e .
```

The delivered environment and exact package versions are recorded in the scalar release. Keep the independent data root and durable numerical artifact store outside the checkout. Exact round-two input objects are required for the frozen-input replay; they are verified against the committed lock, rather than regenerated with a potentially different spectral basis.

Set `DATA_ROOT` to the independent benchmark directory, `ROUND2_STORE` to the recovered round-two numerical store, and `ROUND3_STORE` to a fresh durable directory for this study. Paths containing spaces must be quoted. The following commands preserve the round's 32 core-hour/24 wall-hour clock and shared ledger; resume never resets either limit.

```bash
python -m experiments.extension_round3 freeze \
  --config configs/extension_round3/protocol.yaml \
  --data-root "$DATA_ROOT" --artifact-root "$ROUND3_STORE" \
  --input-artifact-root "$ROUND2_STORE"

python -m experiments.extension_round3 run \
  --config configs/extension_round3/protocol.yaml \
  --data-root "$DATA_ROOT" --artifact-root "$ROUND3_STORE" \
  --input-artifact-root "$ROUND2_STORE" --phase all --resume

python -m experiments.extension_round3 evaluate \
  --config configs/extension_round3/protocol.yaml \
  --artifact-root "$ROUND3_STORE"

python -m experiments.extension_round3 report \
  --config configs/extension_round3/protocol.yaml \
  --artifact-root "$ROUND3_STORE" --output results/extension_round3
```

`run --phase` accepts `evidence`, `primary`, `controls`, `secondary`, `optional`, or `all`. The registered order is evidence, primary, all remaining primary controls, then sensitivities. Before terminal evaluation, all numerical outputs and independent eligibility checks are frozen. Evaluation closes fitting permanently for that store. An interrupted terminal evaluation can resume without changing numeric outputs. Retained failures and missing rows are explicit; a new study requires a separate root and registration, not extension of this clock.

## Scalar reconstruction without private data

```bash
python -m experiments.extension_round3 rebuild \
  --release-manifest results/extension_round3/release_manifest.json \
  --output /tmp/ssc-round3-rebuilt
```

The destination must be fresh. Compressed and uncompressed record hashes, unique profile keys and complete seed sets are checked before writing. Tables are reconstructed in a temporary directory and compared with the release hashes before replacement. Restricted data and matrices are not needed for this command.

Numerical arrays, feasible duals, incremental histories, initial row indices, predictions and checkpoints live in a content-addressed external store. Input objects are retained by verified hardlinks where possible, so independent replay does not depend on another checkout. See the final artifact inventory for recovery identities and the scope of retained objects.

## Durable numerical archive

The final archive retains the exact input objects and imported original reference/warm states, including every referenced numerical object. Its `endpoints/` directory is a provider view of those earlier states; new results remain separately in `profiles/`. Thus a recovered round-three archive can itself serve as `ROUND2_STORE` for a separately authorized fresh replay. It does not require an old checkout. Reference qualification flags are independently recomputed, not inherited.

Archive creation and streaming verification run under the existing resource ledger:

```bash
python -m experiments.extension_verification.resources \
  --artifact-root "$ROUND3_STORE" --run-id numerical-archive \
  --cpu-limit 1200 --wall-limit 2400 --phase aggregation --cwd . -- \
  python -m experiments.extension_round3.artifacts \
    --artifact-root "$ROUND3_STORE" --input-artifact-root "$ROUND2_STORE" \
    --output "$ROUND3_ARCHIVE"
```

The archive includes an inventory with content hashes. Mutable resource accounting is supplied in a final separate receipt so an active reservation is never represented as completed accounting. Restore that receipt when replaying resource totals. The data and numerical archive remain outside Git; the public scalar release reconstructs the tables independently.

The [archive receipt](../../results/extension_round3/artifact_receipt.json) identifies the verified external archive and compressed public inventory. Full recovery verified 78,056 files, followed by an independent saved-ORL certificate replay. The [acceptance record](../../results/extension_round3/acceptance.json) identifies the exact tested commit: a new checkout in a path containing spaces, an isolated environment, 14 mathematical/resource checks, all three scalar rebuilds, panel/alias consistency and corrupt-input rejection. Later publication metadata does not change the numerical source or scientific tables.

The public resource snapshot includes completed native job costs and conservative administrative charges. A separately identified 300-second upper envelope covers final publication, remote-checkout validation and temporary-environment cleanup; it is not a measured method runtime. The final actual publication receipt is retained externally with the closed ledger.

Verify and recover into a fresh directory, keeping the original fitting clock:

```bash
python -m experiments.extension_round3.artifacts recover \
  --archive "$ROUND3_ARCHIVE" --output "$ROUND3_RECOVERED" \
  --ledger "$ROUND3_FINAL_LEDGER"
```

Recovery validates every member before extraction and every extracted payload before replacement. It requires five GiB of additional disk headroom. Completed command records are archived; final archive/accounting and later acceptance records are included in the closing receipt. The preserved numeric-freeze marker continues to prohibit benchmark fitting after terminal evaluation.
