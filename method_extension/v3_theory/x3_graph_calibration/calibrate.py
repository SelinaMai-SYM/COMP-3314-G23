"""Mass-normalized tau and threshold-relative tau are different calibrations."""

from __future__ import annotations

from method_extension.v3_theory.common.graphs import mass_normalized_affinity, mean_mass

__all__ = ["equivalent_gamma", "mass_normalized_affinity", "mean_mass", "threshold_gamma"]


def equivalent_gamma(tau: float, mass: float, epsilon: float = 1e-12) -> float:
    """gamma on the original W that matches tau * W_bar exactly."""
    return float(tau) / max(float(mass), float(epsilon))


def threshold_gamma(tau: float, gamma_0: float) -> float:
    """gamma = tau * gamma_0. This is not the mass calibration."""
    if not gamma_0 or gamma_0 == float("inf"):
        return float("inf")
    return float(tau) * float(gamma_0)
