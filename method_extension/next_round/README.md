# Performance-driven SSC investigation

The main question is net ACC/NMI improvement from shrinkage on the same F and final clustering protocol. [Locked protocol](../../configs/next_round/protocol.yaml), [execution decisions](../../docs/next_round/execution_decisions.md), [actual results](../../results/next_round/all_results.md), [negative findings](../../results/next_round/negative_findings.md).

- `certified_solver.solve(F,W,gamma,...)`: fixed-graph convex PDHG, optional objective-accepted IRLS primal initialization, feasible dual lower bounds and actual stored primal upper bounds. Original E8 uses undirected capacity 2*gamma*w. Radial, radial Huber and scaled squared fidelity have separate domains. No labels are accepted.
- `capped_fusion.fit`: an adaptation of the existing truncated group penalty. Fixed active-edge subproblems receive convex certificates; local fixed points do not imply nonconvex global optimality. Two initializations are selected by the same objective, never labels. The real-data formal search requires the Stage-B gate; it is not automatically run.
- `radial_huber`: candidate anchor-loss mechanism; proven activation is not a label guarantee.
- `heat_geometry.project_heat`: full-spectrum exponential action followed by fixed Gaussian projection. Approximate distances must not be mistaken for exact heat geometry or an ACC guarantee. Secondary hard-dimension/W-only/SC ablations are required.

Every historical E/X adaptation remains separately named and retains its original records. New seeded F/W arrays are local-only artifacts with hashes; old scalar results do not establish their identity with historical representations.
