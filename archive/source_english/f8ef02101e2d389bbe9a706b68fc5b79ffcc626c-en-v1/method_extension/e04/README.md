# E04 — degree normalization

E04-degree replaces W_ij by W_ij / sqrt((d_i + ε)(d_j + ε)) with ε = 1e-12. On a graph whose degrees are not all equal, this is not a global scale of γ.

E04-total divides every stored weight by the sum of stored weights. That is a global scale of W and therefore only a rescaling of γ. It is recorded as a control, not as a new mechanism.
