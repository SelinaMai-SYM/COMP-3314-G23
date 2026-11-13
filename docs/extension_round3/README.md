# Edge-deletion evidence for SSC

Three independent quadratic refinements use one frozen signal: the exact residual length when a pilot-smoothing edge is deleted at fixed diffusion strength. E7 redistributes graph weights, E1_v3 allocates relative stopping tubes, and E5_v2 allocates triangle-slack guards. Plain-pilot, anchor, uniform and shuffled controls distinguish the effect of the signal from the intervention itself.

[Formulation and bounds](method_design.md) · [Protocol](experiment_protocol.md) · [Results](../../results/extension_round3/summary.md) · [Interpretation](interpretation.md)

## Methods and inputs

| Configuration alias | Registered identifier |
|---|---|
| `R3_E7_CAVITY` | `R3_E7_CAVITY_GRAPH` |
| `R3_E1_V3_CAVITY` | `R3_E1_V3_SELECTIVE_TUBE` |
| `R3_E5_V2_CAVITY` | `R3_E5_V2_SELECTIVE_GUARD` |

The eight cohorts are fixed by [cohort_lock.json](../../configs/extension_round3/cohort_lock.json). They were selected retrospectively against paper targets; MSRA is the adapted native 16×16 EBSA source. Their H/W0 arrays are shared with the quadratic comparison. Current fitting verifies provider hashes, exact numerical objects, row IDs and dimensions before constructing evidence.

## Fitting and evaluation

Use the [project installation](../../README.md#installation). The commands below assume provider files in `local/data` and an exact input-provider store recovered at `local/recovered-edge-deletion`, as described in [reproducibility](../reproducibility.md#numerical-artifacts). A fresh output store is `local/artifacts/edge-deletion`.

```bash
python -m experiments.extension_round3 freeze \
  --config configs/extension_round3/protocol.yaml --data-root "$PWD/local/data" \
  --input-artifact-root "$PWD/local/recovered-edge-deletion" \
  --artifact-root "$PWD/local/artifacts/edge-deletion"
python -m experiments.extension_round3 run \
  --config configs/extension_round3/protocol.yaml --data-root "$PWD/local/data" \
  --input-artifact-root "$PWD/local/recovered-edge-deletion" \
  --artifact-root "$PWD/local/artifacts/edge-deletion" --phase all --resume
python -m experiments.extension_round3 evaluate \
  --config configs/extension_round3/protocol.yaml --artifact-root "$PWD/local/artifacts/edge-deletion"
python -m experiments.extension_round3 report \
  --config configs/extension_round3/protocol.yaml --artifact-root "$PWD/local/artifacts/edge-deletion" \
  --output local/edge-deletion-results
```

Phases are `evidence`, `primary`, `controls`, `secondary`, `optional` and `all`; preceding numerical stages and gates are enforced. Evaluation freezes numerical outputs and eligibility before reading labels. Each output retains G, duals, histories, source/environment identity and both complete rounding panels. Continuation uses the original cumulative path limits.

## Reconstruct tables and figures

```bash
python -m experiments.extension_round3 rebuild \
  --release-manifest results/extension_round3/release_manifest.json \
  --output local/tables/edge-deletion --figures
```

No benchmark files or numerical archive are required. The manifest verifies compressed/decompressed packet and trial identities, profile keys and complete seed sets before writing. Recomputed table values are checked against the release. The [archive receipt](../../results/extension_round3/artifact_receipt.json) identifies the separately held numerical arrays and continuation states.
