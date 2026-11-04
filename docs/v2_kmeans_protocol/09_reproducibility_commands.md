# Commands

From the v2 repository root, with `DATA_ROOT` unset (the sibling v1 tree) or set to that tree:

```bash
python -m pytest tests/v2
python -m experiments.v2_kmeans_protocol probe
python -m experiments.v2_kmeans_protocol pilot
python -m experiments.v2_kmeans_protocol primary --benchmark ORL --version att92
python -m experiments.v2_kmeans_protocol gamma --benchmark ORL --version att92
python -m experiments.v2_kmeans_protocol vanilla --benchmark ORL --version att92
python -m experiments.v2_kmeans_protocol repeat --benchmark ORL --version att92
python -m experiments.v2_kmeans_protocol aggregate
```

`pilot` runs the gamma=1 matrix on ORL `att92` and JAFFE `zenodo`, then compares P1, seed by seed, with the v1 random Lloyd metrics. Those historical files are a diagnostic. They are not written into `all_trial_results.csv`.

`campaign` runs primary, gamma, vanilla, and repeatability for every eligible version, with a per-stage timeout. A timeout is stored as `TIMEOUT` and is not filled from an older run.

Thread limits default to 8 for OpenMP and OpenBLAS, matching the v1 strict-paper environment.
The code commit recorded in each trial row is `git rev-parse HEAD` at runtime.
