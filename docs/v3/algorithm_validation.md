# Algorithm validation

- LLC: corrected Procrustes rotation is orthogonal, matches the analytic minimum when `P` has orthonormal columns, and does not increase the fixed-`Y` objective. Final labels match the returned rotation.
- Parameter forwarding: changing `llc_ridge` / kernel bandwidth changes the local regression matrix. Ignored YAML keys raise.
- LDA: `n_components > K-1` raises. Passing `y` raises. Each call refits PCA initialization, pseudo-labels, and the generalized eigenproblem.
- Spectral: kNN diagonal is zero, the affinity is symmetric, and E8 vs E13 does not change the shared embedding `F`.
- SSC: on a 16-point problem, ADMM and CVXPY agree on Equation (8), and the E8 IRLS objective matches that value. E13 keeps coefficient 1 and is not described as the same linear system.
- SLPS: one-shot shrinkage is finite and changes with alpha. Ground-truth labels are rejected.
- Metrics: a label permutation scores ACC = NMI = 1. Missing results are blank, not 0.
