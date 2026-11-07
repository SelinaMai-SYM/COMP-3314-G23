# Experiment records

Each subdirectory is one job. Do not overwrite completed runs.

| Tree | What it is |
| --- | --- |
| `runs/` dated folders | Phase 1 Track A/B and related jobs |
| `runs/repair_round1/` | Repair-round 1 math and transfer jobs |
| `runs/round2/` | Round 2 D1–D12 diagnostics and shortlists |

Typical files: `config.yaml`, `metrics.json`, `status.json`, `metadata.json`, `environment.json`, logs, and optional `embedding_F.npy` / `embedding_G.npy`. Aggregation: `results/round2/experiment_registry.csv`.
