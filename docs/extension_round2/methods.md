# Refinement models and numerical bounds

Let B contain one oriented row per undirected edge, with entries +1 and −1. Weights remain outside B, and `TV_W(G) = Σe we ||(BG)e||2`. All lambdas below are single-edge coefficients. Historical SSC's ordered-pair coefficient maps to `lambda_old = 2 gamma_effective`; equal numerical lambda across different penalties does not imply equal movement.

## QSSC: the quadratic control

The objective is `½||G−H||F² + lambda TV_W0(G)`. For edge duals `||qe|| ≤ lambda we`, a lower bound is `⟨H,Bᵀq⟩ − ½||Bᵀq||F²`. Strong convexity gives embedding error at most `sqrt(2 gap)`, hence movement uncertainty at most `sqrt(2 gap)/S_H`, where `S_H = ||H−mean(H)||F`.

This model is classical [quadratic convex clustering](https://www.ericchi.com/ec_papers/1304.0499v1.pdf), following Chi and Lange. It is not a new project method. The existing non-squared [SSC objective](https://arxiv.org/pdf/1411.6308) and its finite-iteration historical replay are separate reference points, fitted once at their locked historical parameter; their potentially nonunique paths are not treated as quadratic movement paths.

## E1_v2: relative stopping distance

With `ae = eta ||(BH)e||`, eta=.25, minimize

`½||G−H||F² + lambda Σe we max(||(BG)e||−ae, 0)`.

The dual adds `−Σe ae||qe||` to the QSSC dual with the same edge balls. Its dual proximal map first applies vector soft thresholding at `sigma ae`, then projects onto the ball of radius `lambda we`.

For eta<1, positive TV(H) and lambda>0, H is not optimal. The exact optimum has total centered dispersion at least `eta S_H`. With feasible gap epsilon, the numerical lower bound is `S_H − sqrt((1−eta)² S_H² + 2 epsilon)`. This protects total dispersion, not individual edge lengths or class separation. Only activated tubes test the proposed stopping mechanism. Coincident anchor edges and gap-dependent activation uncertainty are reported separately.

In the two-node model H=(−1,1), w=1, the optimal edge length is `max(2 eta, 2−2 lambda)`. At eta=0 the model is exactly QSSC. Nonzero movement and dispersion preservation do not establish ACC/NMI gains.

For the dispersion bound, `eta H+(1−eta)mean(H)` has zero stopping-tube penalty, giving an objective upper reference `½(1−eta)² S_H²`. Compare the optimal objective with this reference, then use the reverse triangle inequality on centered matrices. For a feasible numerical point with primal–dual gap epsilon, add epsilon to that reference to obtain the displayed approximate bound. Nonstationarity of H follows by moving an arbitrarily small amount toward its mean: when TV(H)>0, the penalty decreases to first order while quadratic fidelity grows only to second order.

## E4: a frozen, degree-preserving graph correction

Candidate edges are the union of W0 and deterministic 20-nearest neighbors in H. Edges incident to original isolates are excluded. The auxiliary geometry comprises the next K raw eigenvectors outside the frozen raw U0 subspace of the normalized Laplacian of A0. A shifted sparse operator `L_A + 4 U0 U0ᵀ` is solved for smallest algebraic eigenvalues; residuals, orthogonality and spectral-cutoff ambiguity are recorded. Auxiliary eigenvectors are neither concatenated to H nor row normalized.

On this fixed edge set, a and b are squared distances in H and the auxiliary band, respectively, each divided by its own positive median. A missing positive median is explicitly diagnosed. Let

`r_raw = max(exp(−a), 1e−6)`, `r = r_raw sum(w0)/sum(r_raw)`,

and let M be the unsigned incidence matrix, `d=Mw0`, `C=1.05 aᵀw0`. For beta=1 solve the strictly convex QP

`min_t≥0 ½ Σe (te−w0e)²/re + beta bᵀt`, subject to `Mt=d`, `aᵀt≤C`.

Then `Wnew = .75 W0 + .25 t`, and run QSSC on Wnew. The graph preserves original degrees and total mass, keeps at least .75 of every original edge, and has H-cost at most `1.0125 aᵀw0`. The beta=0 solution is exactly W0.

For equality multiplier v and budget multiplier theta≥0, set `c=beta b+Mᵀv+theta a`, `s=max(w0−rc,0)`. The independent dual is

`−vᵀd−theta C + Σe (w0e²−se²)/(2re)`.

The full primal includes the constant omitted from OSQP's native objective. The stable piecewise dual expression avoids subtractive cancellation. Tiny negative returned weights are explicitly projected to zero, followed by degree, budget and gap checks. Such values are numerical feasible candidates, not exact primal bounds; exact W0 remains a safe feasible upper reference. A failed QP falls back to W0 and is disqualified as an E4 intervention.

All three row-permuted auxiliary-band controls use seeds 400–402. They preserve E,a,r,d,C and recompute only b. Exchange mass and post-fit within/between-class changes accompany ACC/NMI; labels never enter the QP. Adjacent work includes [doubly stochastic normalization](https://proceedings.neurips.cc/paper/2006/hash/4fa177df22864518b2d7818d4db5db2d-Abstract.html) and [SDSGC](https://github.com/NianWang-HJJGCDX/SDSGC). E4 retains nonuniform original degrees, a frozen anchor, an old-geometry budget and an original-edge floor; it does not learn a doubly stochastic K-component graph or alternate graph and embedding updates. Graph projection itself is established prior art. The implementation uses the [official OSQP interface](https://osqp.org/docs/interfaces/python.html).

## E5: an anchor-relative TV-TV guard

For alpha=1, define `kappa_e(G)=||BG_e||+||B(G−H)_e||−||BH_e||≥0` and minimize

`½||G−H||F² + lambda TV(G) + alpha lambda Σe we kappa_e(G)`.

Equivalently, the penalty is `lambda(1+alpha) TV(G) + lambda alpha TV(G−H) − lambda alpha TV(H)`. Two dual blocks have radii `lambda(1+alpha)w` and `lambda alpha w`. The lower bound is

`⟨BH,q⟩ − ½||Bᵀ(q+p)||F² − lambda alpha TV(H)`.

PDHG uses the stacked operator [B;B], accounting for both blocks in its step bound. At alpha=0 the model is QSSC. The guard allows collinear contraction; large alpha can leave nearly uniform scale/translation, which does not improve an ideal k-means partition. Diagnostics therefore include triangle slack, nonuniform residuals, edge reversal/expansion and permutation-invariant partition changes.

TV-TV and related prior-guided TV are established methods: [Vella and Mota, IEEE TIP 2021](https://jmota.eps.hw.ac.uk/documents/Vella21-RobustSingleImageSuperResolutionViaCNNsAndTVTVMinimization.pdf), and [PICCS](https://pmc.ncbi.nlm.nih.gov/articles/PMC3257752/). The reference [TVTV_Solver_CPU.m](https://github.com/marijavella/sr-via-CNNs-and-tvtv/blob/7c6f2b7a318a8e1a72dffc1a32e8a8076b98fcae/code/TVTV_Solver_CPU.m) was inspected at commit `7c6f2b7a318a8e1a72dffc1a32e8a8076b98fcae` to verify the two-TV structure. Its image FFT/ADMM code was not copied; this project implements sparse graph-vector operators.

## E6: an anchor-relative directional contraction floor

Center H and take `Hc=U Sigma Vᵀ`, retaining **all** singular values above the standard float64 tolerance `max(n,K) epsilon sigma_max`. No tuned PCA threshold is used. Set `Y=U Sigma`, retain centering, and minimize

`½||Z−Y||F² + lambda TV_W0(Z)`, subject to `sym(YᵀZ) ≥ eta_dir Sigma²`, eta_dir=.5.

The exactly equivalent whitened constraint is `sym(UᵀZ Sigma⁻¹) ≥ eta_dir I`. Reconstruct `G=mean(H)+ZVᵀ`; movement includes the discarded numerical residual relative to the original H. For PSD S, set `A=Bᵀq−YS`. The dual is

`⟨Y,A⟩ − ½||A||F² + eta_dir⟨Sigma²,S⟩`, with `||qe||≤lambda we`.

PDHG uses `tau(sigma_B||B||² + sigma_T sigma_max(Y)²)<1`. PSD projection is a small symmetric eigendecomposition. The feasible primal is centered and, when needed, mixed with Y using the minimum **whitened** eigenvalue and margin `1e−10`. The repaired primal and feasible dual produce the stable gap; raw infeasible iterates do not supply upper bounds. The conditioning indicator, retained rank, spectrum, repair fraction and whitened feasibility remain explicit. Weak directions are never silently discarded to obtain certification.

For every retained b, `⟨Yb,Zb⟩≥eta_dir||Yb||²`, hence `||Zb||≥eta_dir||Yb||`; equivalently the reconstructed centered Gram matrix dominates `eta_dir² HcᵀHc` on the retained row space. This is a directional-scale guarantee, not a class-separation or ACC guarantee. When `rho S_H < (1−eta_dir) sigma_min(Y)`, the guard is necessarily inactive throughout that movement ball. Actual LMI slack, PSD-dual norm and the matched-QSSC directional scale distinguish inactivity from protected contraction. Preserving weak directions may retain noise.

The LMI and singular-value guarantee adapt [Kovalsky et al., SIGGRAPH 2014](https://shaharkov.github.io/ContSingVal.html); they are published prior art. No graphics optimization code is incorporated.

For post-fit attribution, a QSSC embedding with strong-convexity error bound e can change its whitened symmetric matrix by at most `e/sigma_min(Y)` in operator norm. Subtracting that quantity from its observed minimum eigenvalue gives a lower bound for the retained projection of the QSSC optimum. When this lower bound exceeds eta_dir, a difference between separately calibrated E6 and QSSC scores cannot be attributed to protection of a violated direction at the QSSC lambda. Matching permits a finite movement tolerance, and k-means can change after small numerical or calibration differences.

## Scope of the contribution

These are specific SSC extension candidates designed and tested in this project; E5 and E6 explicitly adapt tools from other fields. Our scoped search did not identify an equivalent published spectral-clustering construction, but it does not prove absolute novelty. The empirical contribution is the controlled comparison, activation/failure analysis and reproducible evidence. Smaller objectives, geometric guarantees or changed partitions alone do not demonstrate improved clustering.
