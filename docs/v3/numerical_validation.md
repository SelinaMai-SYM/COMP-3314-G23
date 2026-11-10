> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# Numerical validation

Equation (8) is the nonsmooth objective `sum_i ||g_i - f_i|| + gamma * sum_{i,j} W_ij ||g_i - g_j||`, using stored ordered pairs.

Statuses:

- `CONVERGED_BY_ITERATE_CRITERION`: relative Frobenius step of IRLS fell under the declared tolerance. This is not an optimality certificate.
- `OPTIMALITY_VERIFIED`: an independent ADMM or CVXPY solve of the same objective is within the declared relative gap, or the unique subgradient is small because no residual is fused.
- `MAX_ITER_REACHED`: the iteration budget ended first. The 300-iteration checkpoint is stored even if a priority solve continues.
- `NUMERICALLY_UNCERTIFIED`: a zero residual or fused edge blocks a unique subgradient, and no independent gap is available.
- `FAILED` / `TIMEOUT`: the job record contains the exception or the unfinished reason.

Priority continuations after 300 iterations: ORL `ssc_gamma=1`, YaleB `ssc_gamma=1`, USPS `ssc_gamma=1000`. A small step is not treated as optimality. ADMM patterns are not substituted for the IRLS patterns that enter K-means.
