# Earlier analytical mechanism controls

These modules retain separately named analytical controls for the fixed-graph
SSC objective. Their presence does not establish ACC/NMI improvement.

| Module | Role |
|---|---|
| `x1_certified_path` | Ordered-pair G=F subgradient threshold and fusion summaries |
| `x2_stability_graph` | Declared image/feature perturbations for graph stability |
| `x3_graph_calibration` | Distinct mass-normalized and threshold-relative parameter scales |
| `x4_multiscale_consensus` | Fixed four-scale affinity average, without label-fitted weights |
| `x5_adaptive_fidelity` | Fixed positive fidelity weights and uniform/inverse/permutation controls |
| `common` | Shared graph, objective, optimization and rounding helpers |

A G=F threshold is an objective-specific condition, with coincident-edge
qualifications; it is not a label-free performance selector. Deleting edges
need not preserve G=F because incident forces can cancel. The separately
valid incident-mass sufficient bound is explained in
[theory](../../docs/theory.md).

For objective certification, use the feasible dual and gap interfaces in
[the certified-solver documentation](../next_round/README.md).
Solver agreement and iterate stopping are not equivalent certificates.

Image perturbations require an explicit data domain. USPS uses [-1,1];
zero perturbation must preserve the input. The earlier robustness table
did not rerun perturbed SSC and used the wrong USPS clipping range,
so those historical stability values do not establish clustering
robustness. Corrected complete-method evaluations are separately qualified.

See [methods](../../docs/methods.md),
[results](../../docs/results.md), [limitations](../../docs/limitations.md)
and [reproducibility](../../docs/reproducibility.md).
