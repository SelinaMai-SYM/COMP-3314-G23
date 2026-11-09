# E02 — unsupervised row weights

The objective is sum_i α_i ||g_i - f_i||_2 + γ sum_ij W_ij ||g_i - g_j||_2. α_i = 0.5 + 1.5 m_i, where m_i is the fraction of the k nearest neighbors of row i of F that list i back. The interval is [0.5, 2]. W and F stay on the original construction. α is frozen before IRLS.

α = 1 is the original E8 linear system and must match `shrink_embedding(..., variant="E8")`. A small nonuniform α is checked against CVXPY. The alpha-weighted value is not comparable to Equation (8) unless α = 1.
