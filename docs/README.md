# Documentation

- [Methods](methods.md): SSC, graph construction, baselines and the retained refinement families.
- [Mathematical foundations](theory.md): objectives, duals, certificates and limiting cases.
- [Experimental protocol](experimental_protocol.md): data preparation, rounding, endpoints and retrospective selection.
- [Data setup](data.md): providers, source identities, expected paths and preprocessing.
- [Reproducibility](reproducibility.md): fitting, scalar reconstruction and report commands.
- [Results](results.md): measured effects, coverage and limitations.
- [Technical report](../report/Group_23.pdf) and [build instructions](../report/README.md).

## Refinement comparisons

| Scientific comparison | Implementation namespace | Documentation |
|---|---|---|
| Unsquared relative stopping, tangent constraints and neighbor hinges (E1–E3) | `extension_verification` | [Protocol](unsquared_refinements.md), [theory](extension_verification_theory.md), [results](extension_verification_results.md) |
| Quadratic relative tubes, graph-band repair, triangle-slack guard and singular floor | `extension_round2` | [Methods and inputs](extension_round2/README.md), [formulations](extension_round2/methods.md), [results](../results/extension_round2/summary.md) |
| Exact edge-deletion evidence with graph, tube or guard insertion | `extension_round3` | [Guide](extension_round3/README.md), [formulation](extension_round3/method_design.md), [protocol](extension_round3/experiment_protocol.md), [results](../results/extension_round3/summary.md) |

The namespaces identify executable modules. Each comparison retains its own objective, input lock, operating point and statistical endpoint.
