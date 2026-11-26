# References and implementation attribution

## Methods and software

- Chang, X., Nie, F., Ma, Z., Yang, Y. and Zhou, X. (2015). *A Convex Formulation for Spectral Shrunk Clustering*. AAAI, 2532–2538. [DOI](https://doi.org/10.1609/aaai.v29i1.9606). This project is an independent reconstruction.
- Hou, C., Nie, F., Jiao, Y., Zhang, C. and Wu, Y. (2013). *Learning a Subspace for Clustering via Pattern Shrinking*. Information Processing and Management, 49(4), 871–883. [DOI](https://doi.org/10.1016/j.ipm.2013.01.004). SLPS is called SPLS in the SSC paper; the one-shot SLPS/PsKm reconstruction is explicitly qualified.
- Ding, C. and Li, T. (2007). *Adaptive Dimension Reduction Using Discriminant Analysis and K-means Clustering*. ICML, 521–528. [DOI](https://doi.org/10.1145/1273496.1273562). The ridge LDA→SC adaptation remains separately named from historical LDA-SC.
- Arthur, D. and Vassilvitskii, S. (2007). *k-means++: The Advantages of Careful Seeding*. SODA, 1027–1035. Random, vanilla++ and scikit-learn greedy++ starts remain distinct protocols.
- Pedregosa, F. et al. (2011). *Scikit-learn: Machine Learning in Python*. JMLR, 12, 2825–2830. [Paper](https://jmlr.org/papers/v12/pedregosa11a.html).
- Chi, E. C. and Lange, K. (2015). *Splitting Methods for Convex Clustering*. JCGS, 24(4), 994–1013. [DOI](https://doi.org/10.1080/10618600.2014.948181). Quadratic graph fusion/QSSC is an established convex-clustering control.
- Chambolle, A. and Pock, T. (2011). *A First-Order Primal-Dual Algorithm for Convex Problems with Applications to Imaging*. JMIV, 40, 120–145. [DOI](https://doi.org/10.1007/s10851-010-0251-1). The project applies primal–dual optimization and independently checks feasible certificates.
- Wang, S., Zhou, W., Lu, H., Maleki, A. and Mirrokni, V. (2018). *Approximate Leave-One-Out for Fast Parameter Tuning in High Dimensions*. ICML, 5228–5237. [Paper](https://proceedings.mlr.press/v80/wang18m.html). This supplies regression leave-one-out inspiration; the fixed graph rank-one identity is derived in the method guide.
- Vella, M. and Mota, João F. C. (2021). *Robust Single-Image Super-Resolution via CNNs and TV-TV Minimization*. IEEE TIP, 30, 7830–7841. [DOI](https://doi.org/10.1109/TIP.2021.3108907). TV-TV is related regularization, not a claim of reused clustering code.
- Leiber, C., Miklautz, L., Plant, C. and Böhm, C. (2023). *Benchmarking Deep Clustering Algorithms With ClustPy*. ICDMW, 625–632. [DOI](https://doi.org/10.1109/ICDMW60847.2023.00087). The instrumented reference reuses ClustPy commit `4ac9d00685efc7432800684f5bfac0f01af59172`; its [BSD-3-Clause license](../baselines/lda_kmeans/vendor/clustpy/LICENSE) and [provenance](../baselines/lda_kmeans/vendor/clustpy/PROVENANCE.json) remain intact.

## JAFFE attribution

The [official v2 dataset record](https://zenodo.org/records/14974867) is dated
1997 and was deposited in 2025, DOI
[10.5281/zenodo.14974867](https://doi.org/10.5281/zenodo.14974867). Its terms
require these two references:

- Lyons, M. J., Kamachi, M. and Gyoba, J. (2020). *Coding Facial Expressions with Gabor Wavelets (IVC Special Issue)*. [arXiv:2009.05938](https://arxiv.org/abs/2009.05938).
- Lyons, M. J. (2021). *“Excavating AI” Re-excavated: Debunking a Fallacious Account of the JAFFE Dataset*. [arXiv:2107.13998](https://arxiv.org/abs/2107.13998).

The noncommercial research and nonredistribution terms apply to JAFFE independently
of this project's MIT license. Dataset and numerical-artifact availability is
described in [data setup](data.md).
