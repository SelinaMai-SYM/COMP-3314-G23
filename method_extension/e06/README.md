# E06: alternating graph construction and shrinkage

`AlternatingGraphSSC` performs three outer iterations. Each builds a
nearest-neighbor graph on the current representation, freezes that graph,
and solves E8 with fidelity anchored at the **original** \(F\).
The next graph is constructed from the new \(G\).

Every fixed nonnegative-graph subproblem is convex. This does not establish
global convergence for the alternation or define a certified joint
objective. The final recorded objective belongs to the last frozen graph;
its raw value cannot be compared with a control objective on another graph.

See the [adaptation index](../README.md),
[theory](../../docs/theory.md), [results](../../docs/results.md)
and [reproducibility](../../docs/reproducibility.md).
