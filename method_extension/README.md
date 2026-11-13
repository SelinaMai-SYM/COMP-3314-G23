# SSC refinements and numerical solvers

The modules implement fixed-graph objectives and explicitly named adaptations of [Spectral Shrunk Clustering](../SSC_method/README.md). Fitting functions operate on feature or anchor arrays and do not use class labels.

| Package | Purpose |
|---|---|
| `next_round/certified_solver` | Sparse primal–dual SSC, feasible lower bounds and capacity checks |
| `next_round/capped_fusion`, `radial_huber`, `heat_geometry` | Fidelity/fusion and representation controls for the corresponding retained experiments |
| `extension_verification` | Unsquared E1 relative stopping, E2 tangent constraints and E3 relative-neighbor hinges |
| `extension_round2` | Quadratic QSSC, uniform relative tubes, graph-band adaptation, triangle-slack guards and a singular-direction floor |
| `extension_round3` | Exact deleted-edge pilot evidence, weighted midranks and three selective quadratic refinements |
| `mutual_knn`, `rssc` | Mutual-neighbor adaptation with a fixed spectral anchor |
| `v3_theory` | Operators and perturbation mechanisms used by the recorded geometry/robustness controls |

[Methods](../docs/methods.md) defines the objectives and coefficients. [Experiments](../docs/experimental_protocol.md) defines comparisons, operating points and metric aggregation. Numerical certification concerns the specified convex objective; clustering effects are measured separately.
