# Novelty and donor audit

Audit date: 13 November 2026. Supplementary searches were bounded to 30 minutes. No equivalent construction was verified in this bounded review; this is not evidence of absolute novelty.

The six searches were: `leave-one-edge-out spectral clustering`, `edge deletion convex clustering`, `graph PRESS residual`, `cavity graph refinement`, `spectral shrunk clustering influence correction`, and `leverage-corrected graph total variation`. The audit reviewed primary research sources. Irrelevant uses of “cavity” do not establish algorithmic overlap or novelty.

| Primary source | Reviewed formulation | Relationship to this study |
|---|---|---|
| [Wang et al., ICML 2018](https://proceedings.mlr.press/v80/wang18m.html) | Approximate leave-one-out for penalized high-dimensional regression; primal and dual constructions | Donor of the leverage-corrected residual idea. Our quadratic graph edge-deletion identity is exact and is used to redistribute existing SSC coefficients. Neither leverage correction nor Sherman–Morrison is new. |
| [Karasuyama and Mamitsuka, NeurIPS 2013](https://proceedings.neurips.cc/paper/5001-manifold-based-similarity-adaptation-for-label-propagation.pdf) | Section 3, Eq. (2): local reconstruction-based graph weighting; Section 4.1, Eq. (3): leave-one-out prediction of node features under harmonic propagation | Establishes graph adaptation through cross-validation. Our deletion unit is one graph edge in a ridge pilot, with fixed diffusion strength and mass-matched SSC interventions. We do not claim the first graph cross-validation method. |
| [Afonso and Berton, 2022](https://arxiv.org/abs/2201.03456) | LGC semi-supervised classification, diagonal self-influence removal, diffusion-rate and label-reliability optimization | Nearby self-influence correction already exists. The current evidence is label-free, edge-specific and does not optimize a supervised leave-one-out loss. |
| [Li et al., Statistica Sinica 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC6813893/) | Bayesian areal boundary detection and spatial neighborhood dependence | Boundary-sensitive graph relations and spatial edge removal predate this work. Our primary intervention retains all positive edges and is a deterministic coefficient redistribution, without a Bayesian posterior. The PMC availability date is not the publication year. |

The actual donor code was inspected at commit [`a17ec1774cd0cceb4e748e9db076ee7cb2472504`](https://github.com/wendazhou/alocv-package/tree/a17ec1774cd0cceb4e748e9db076ee7cb2472504):

- `C/src/alo_lasso.cpp`, SHA256 `8fd2bac12d649dbc0a5fff4a59d298313a66699553700d2a5d322848deca8da8`: `lasso_compute_leverage_cholesky_d` and `compute_alo_fitted`; the latter divides the residual by `1 - leverage[i]`.
- `python-package/tests/test_lasso.py`, SHA256 `6e39eafddc825ae3d2269cfb5dd113787d88e2e40ca42b52d017f38d99342b48`: leverage and ALO checks.
- `R-package/LICENSE`: 2018 copyright-holder metadata naming Wenda Zhou. This metadata alone is not treated as permission to copy the implementation.

The package was not built or runtime-tested. No donor source was copied. NumPy/SciPy implementations were written independently, and the project MIT license covers the project implementation, subject to retained third-party notices.

The scoped contribution is a frozen exact edge-deletion signal and controlled comparison of three alternative insertion points in Spectral Shrunk Clustering. The three interventions share one hypothesis. Mathematical correctness, mechanism activity, improvement beyond a plain pilot, and improvement beyond SC/original SSC are four separate claims. The final results determine which of them are supported.
