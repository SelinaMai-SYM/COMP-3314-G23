# K-means protocol comparison on fixed E8 representations

This package clusters two representations that are solved once:

- `F`: spectral embedding, reported as SC
- `G`: E8 shrunk patterns (`A = S + 2 gamma Ltilde`, `G0 = F`), reported as SSC

P1 and P2 summarize one batch of random Lloyd trials, seeds 0..49.
P3 and P4 summarize one batch of scikit-learn greedy k-means++ trials with the same seed ids.
Vanilla k-means++ (`n_local_trials=1`) is a separate control.

`DATA_ROOT` points at the v1 worktree. It is read-only. Restricted images are not copied.

```bash
python -m experiments.v2_kmeans_protocol probe
python -m experiments.v2_kmeans_protocol pilot
python -m experiments.v2_kmeans_protocol primary --benchmark ORL --version att92
python -m experiments.v2_kmeans_protocol gamma --benchmark ORL --version att92
python -m experiments.v2_kmeans_protocol vanilla --benchmark ORL --version att92
python -m experiments.v2_kmeans_protocol repeat --benchmark ORL --version att92
python -m experiments.v2_kmeans_protocol aggregate
python -m pytest tests/v2
```

Labels are used only after Lloyd returns, for Hungarian ACC and geometric-mean NMI.
The selected trial is the minimum inertia inside that representation.
Inertia is not compared across F and G.
A nonconverged SSC status is a returned iterate, not a certified global optimum.
