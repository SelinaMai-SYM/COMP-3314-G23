# Prior art

The five calculations reuse known devices. They are not claimed as new theorems or as a new convex formulation.

- The ordered-pair objective is the printed SSC objective of Chang, Nie, Ma, Yang, and Zhou (AAAI 2015). Convex clustering and its ADMM splitting are those of Chi and Lange and of Hocking, Joulin, Bach, and Vert.
- IRLS for an l2,1-style row penalty follows the same majorization used for the frozen E8 system, with the fidelity weight put into the diagonal. Nie, Huang, Cai, and Ding (2010) is the usual source for that majorization.
- Local scaling of a neighborhood graph is the self-tuning idea of Zelnik-Manor and Perona. X2 instead multiplies an existing weight by a perturbation frequency. That frequency is not a class label.
- Robust reweighting of a data term by a residual or neighbor scale is standard M-estimation (Huber; also the l2,1 literature). X5 fixes the weights before optimizing `G`.
- Multi-scale graphs and averaging several kNN graphs are standard in spectral clustering. The weights here are fixed at one quarter.

Nothing in this directory asserts that a literature search proved these combinations to be unpublished.
