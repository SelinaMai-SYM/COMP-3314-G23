# Experiment configs

YAML files in this directory are the inputs of `scripts/run_experiment.py`.
The orchestrator `scripts/run_all_stages.py` also writes one-off configs under
`configs/generated/` immediately before launching a job. Every run directory
stores the exact config that produced it as `config.yaml`.

Required keys: `track`, `method`, `dataset`, `n_trials`.
Optional: `params`, `perturbation`, `timeout_seconds`, `trial_seed_start`, `notes`.
