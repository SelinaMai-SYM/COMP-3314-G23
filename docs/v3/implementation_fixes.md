> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# v3 implementation fixes

Inherited commit `c217836e7ca7bf5264399e8bb176522d7f721917`. v1/v2 measurements are historical. LLC numbers from those branches are `PRE_FIX_LEGACY` and are not copied into v3 tables.

## LLC Procrustes

`baselines/llc/llc.py` used `R = U @ Vt` after `svd(Y.T @ P)`. The fixed-target problem `min_R ||Y - P R||_F` with `R.T R = I` uses `R = V @ U.T`, which is `Vt.T @ U.T` in NumPy. Returned labels are recomputed from that rotation, and the logged objective uses the same pair. The correction is not assumed to raise ACC.

## Parameters

`prepare_llc_embedding` passes ridge, kernel, and kernel bandwidth into the local regression matrix. Each v3 job stores `requested_config` and `effective_config`. A requested key that is absent from the effective config raises.

Names are distinct: `ssc_gamma`, `affinity_delta_squared`, `llc_ridge`, `llc_kernel_bandwidth`.

## LDA-Kmeans

Ding and Li alternation: center, PCA initialization, K-means pseudo-labels, scatter matrices, generalized eigenproblem, `K-1` columns, no padding to 150. Each seed calls the whole fit. Ground-truth `y` is rejected. Inertia is not compared across different subspaces. The logged objective is the ratio of traces. Under `U.T S_w U = I` that ratio is the mean retained generalized eigenvalue, not `Tr(S_w^{-1} S_b)`.

## SSC

`E8` uses `S + 2 gamma Ltilde`. `E13` uses `S + gamma Ltilde`. They are two reconstructions of one method. A 300-iteration checkpoint is stored separately when a priority solve continues. ADMM/CVXPY check Equation (8); they do not replace the IRLS matrix that is clustered.

## SLPS

Hou et al., IPM 2013, is on disk as a 13-page PDF (not committed). The experiments in that paper use one-shot Eqs. (18)--(19) with local scaling and `k=7`, then K-means. That is what v3 runs. Ncut-on-SLPS and the `beta>0` loop are not substituted under the same name. Alpha and dimension are not chosen by test ACC.

## LDA-SC

Still blocked. Chang et al. name it and do not define it.
