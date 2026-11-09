Current standalone commands and reconstruction are in the [root README](../../README.md). New performance experiments are separate under `experiments/next_round`; historical numbers are not overwritten.

# v3 reproduction campaign

Commands, from the v3 worktree:

```bash
python -m experiments.v3_reproduction resources --config configs/v3/campaign.yaml
python -m experiments.v3_reproduction plan --config configs/v3/campaign.yaml
python -m pytest tests/v3
python -m experiments.v3_reproduction campaign --config configs/v3/campaign.yaml --resume
python -m experiments.v3_reproduction aggregate --config configs/v3/campaign.yaml
python -m experiments.v3_reproduction validate --config configs/v3/campaign.yaml
```

Raw matrices are read from the explicit CLI data root, environment or local pointer (see `docs/final/data_setup.md`). Outputs are written only under this worktree. Historical v1/v2 ACC/NMI are not copied into v3 rows.

The historical matrix is 9 methods by 8 benchmarks. Extra versions, YaleB preprocessing tracks, and the E8/E13 pair are sub-experiments.
