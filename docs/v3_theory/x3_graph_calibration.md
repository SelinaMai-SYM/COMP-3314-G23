# X3 graph-calibrated regularization

Two different calibrations are computed. They are not the same object.

Mass calibration. Under the ordered-pair convention,

    m(W) = (sum_ij W_ij) / n
    W_bar = W / max(m(W), epsilon)

The objective uses `tau * W_bar`. On the original `W` the same objective is exactly `gamma = tau / max(m(W), epsilon)`. If the solved embeddings match, the mass form is a rescaling, not an algorithmic improvement.

Threshold calibration. From the verified X1 threshold,

    gamma = tau * gamma_0
    tau_threshold = gamma / gamma_0

This expresses the penalty relative to the point where `G = F` stops being optimal. It does not divide by `m(W)`.

Both grids, and the original gamma grid, use `{1e-3, 1e-2, 1e-1, 1, 10, 100}`. The mandatory control solves the original `W` at the equivalent gamma.
