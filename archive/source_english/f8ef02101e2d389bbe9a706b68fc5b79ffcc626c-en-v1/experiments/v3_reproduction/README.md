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

Raw matrices are read from `data_root` in the campaign file (the v1 archives). Outputs are written only under this worktree. Historical v1/v2 ACC/NMI are not copied into v3 rows.

The historical matrix is 9 methods by 8 benchmarks. Extra versions, YaleB preprocessing tracks, and the E8/E13 pair are sub-experiments.
