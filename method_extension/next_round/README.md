# Certified SSC and secondary mechanism candidates

These modules operate on a fixed anchor \(F\) and graph \(W\). Their
mathematical properties are developed in [theory](../../docs/theory.md);
[methods](../../docs/methods.md) and
[results](../../docs/results.md) distinguish numerical guarantees from
observed clustering quality.

## Convex solver

```python
from method_extension.next_round.certified_solver import solve

fit = solve(F, W, gamma=1.0, preconditioned=True)
G = fit["G"]
q = fit["q"]
```

`solve` implements the fixed-graph primal–dual target with undirected
edge capacities \(2\gamma w_e\). Original SSC uses `fidelity="radial"`
and `delta=0`. Positive `delta` gives radial Huber fidelity; the
`fidelity="squared"` control has a distinct conjugate domain without
node-ball constraints. Optional positive row weights are supplied through
`a`.

A feasible initial dual is retained before iterations. Best actual primal
points and feasible dual bounds are saved separately, and diagonal
preconditioning maps \(K=\operatorname{diag}(\sqrt w)B\) back to the
original capacities. Reported certification requires relative gap at most
`1e-5` and capacity violations at most `1e-8`. An iteration limit or
solver agreement is a different status. `return_checkpoint=True` exposes
final states separately from best states for valid same-objective restarts.

The returned `q` is a feasible graph dual, not an IRLS fidelity-weight
array. Certificate interpretation is specific to the returned primal
point, fixed graph and objective.

## Capped fusion

`capped_fusion.fit` adapts the existing group-truncated penalty
\(\rho_\tau(r)=\min(r,\tau)\), with
[PRclust](https://jmlr.csail.mit.edu/papers/volume14/pan13a/pan13a.pdf)
as prior work and
[Shah–Koltun RCC](https://vladlen.info/publications/robust-continuous-clustering/)
as related robust-edge motivation.

One call follows one supplied `G_init` through active-edge convex
subproblems. A two-start comparison evaluates the F start and the
original-SSC start separately, choosing by the same capped objective,
without labels. Accepted updates cannot increase that objective beyond the
declared floating-point comparison tolerance.
A certified inner solve and fixed active set are not a general global
certificate for the nonconvex problem.

The verified five-point reference has linear/capped values eight/three
at the recorded precision, but SC already separates it. Initialization
dependence and the earlier 0/4 real-data mechanism result prevent an
accuracy-superiority claim. The tiny-graph exhaustive reference does not
extend to arbitrary five-point graphs.

## Radial Huber and heat geometry

`radial_huber` exposes the shared convex solver. Huber activation,
orthogonal equivariance and bounded fidelity gradients do not guarantee
better labels or transfer another estimator's breakdown theorem.

`heat_geometry.project_heat(L,t=4,r=128,seed=20261108)` returns projected
full-spectrum heat features and the Gaussian projection used. Exact
features \(e^{-tL/2}\) generate kernel \(e^{-tL}\); rows of \(e^{-tL}\)
instead correspond to doubled-time geometry. The scalable projection is
approximate and does not automatically inherit exact-distance bounds.

These are secondary candidates and controls. No new Huber, capped-fusion
or heat grid is part of the final graph-adaptation comparison.
See [reproducibility](../../docs/reproducibility.md) for the maintained
experiment and result-replay interfaces.
