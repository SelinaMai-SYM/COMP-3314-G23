# Reproduction interface

The stable `experiments.v3_reproduction` module supports synthetic examples, manifest-verified historical table reconstruction and new experiments with an explicit data root. It does not depend on a Git branch named v3.

From the checkout root:

```bash
python -m experiments.v3_reproduction smoke --dataset synthetic
python -m experiments.v3_reproduction rebuild-results --release-manifest configs/final/release_manifest.json --output local/rebuilt_historical
python -m experiments.v3_reproduction run-experiments --config configs/v3/campaign.yaml --data-root DATA_ROOT
```

The historical matrix contains nine methods and eight benchmarks. Source versions, YaleB normalization factors and the E8/E13 coefficient convention remain distinct configurations. Missing data or unresolved method identity is reported explicitly. See [protocol](../../docs/experimental_protocol.md), [data](../../docs/data.md), [results](../../docs/results.md) and [reproducibility](../../docs/reproducibility.md).
