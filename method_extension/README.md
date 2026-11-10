# SSC adaptations and numerical mechanisms

This library contains explicitly named adaptations of
[original SSC](../SSC_method/README.md). The scientific question is net
ACC/NMI improvement from shrinkage under matched input, representation and
rounding. A graph change, a different fidelity and a different rounding rule
are separate interventions.

| Components | Purpose |
|---|---|
| [`ReliabilityAwareSSC`](rssc.py) and [mutual graph helper](mutual_knn.py) | Mutual-neighbor support on the fusion graph |
| [E01–E09](#named-mechanism-controls) | Separately named graph, fidelity and rounding controls |
| [Convex solver and secondary candidates](next_round/README.md) | Feasible-dual certification, capped fusion, radial Huber and heat geometry |
| [EnSC graph adapter](submission_refresh/README.md) | Attributed elastic-net coefficients and affinity construction |
| [Earlier theory controls](v3_theory/README.md) | Threshold, calibration, perturbation and weighted-fidelity mechanisms |

## Mutual-neighbor adaptation

`ReliabilityAwareSSC` keeps the original union-neighbor input graph and
spectral anchor \(F\), but retains a fusion edge only when its endpoints
are mutual neighbors in \(F\). The bandwidth is computed from positive
directed-neighbor squared distances **before** mutual filtering. Thus the
support change does not silently change the bandwidth estimate.

The graph is frozen before the original IRLS solve, initialized at \(G=F\).
This class retains the E13 linear-system convention. Its control must use
that same convention; E01–E09 instead declare E8 controls explicitly.
Mutual support can remove useful within-class connections, so increased
sparsity is not itself evidence of better clustering.

Mutual nearest-neighbor graphs are established constructions. This package
does not claim a new graph family, a new convexity theorem or guaranteed
accuracy improvement. Fixed nonnegative graph weights preserve convexity
of the stated SSC target.

## Named mechanism controls

| Identifier | Modification |
|---|---|
| [E01](e01/README.md) | Perturbation recurrence reweights \(W\) |
| [E02](e02/README.md) | Positive fidelity weights from neighbor reciprocity |
| [E03](e03/README.md) | Local-scale affinity placed in \(A\), \(W\), or both |
| [E04](e04/README.md) | Degree normalization and a separate global-scale control |
| [E05](e05/README.md) | Combine input-space and embedding-space relations |
| [E06](e06/README.md) | Alternate graph construction and fixed-anchor shrinkage |
| [E07](e07/README.md) | Compare rounding rules on the same representation |
| [E08](e08/README.md) | Combine E01 recurrence with E02 fidelity weights |
| [E09](e09/README.md) | Combine recurrence with the E03-W local-scale graph |

Parameters and seed conventions are part of each named construction.
Different targets cannot be ranked by comparing their raw objective
values. Compatibility `y` arguments in the E01–E09 fitting adapter are
discarded; labels do not determine its graph or solver updates.

The main conclusions, including negative and numerically unresolved
comparisons, are in [results](../docs/results.md).
See [methods](../docs/methods.md), [theory](../docs/theory.md),
[limitations](../docs/limitations.md) and
[reproducibility](../docs/reproducibility.md).
