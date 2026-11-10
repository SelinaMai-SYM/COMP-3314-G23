# E05 — feature graph and embedding graph

W_F is the control kNN affinity on F. W_X is the same rule on the original features. E05-fuse uses 0.5 W_F + 0.5 W_X. E05-bilateral keeps a W_F edge only when W_X also has that edge. λ = 0.5 is fixed.

On YaleB the pixel-space graph is not assumed to be reliable. Both variants are still run, and a negative result is kept.
