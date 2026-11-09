"""Shared interface for SSC extensions. Original SSC stays in SSC_method."""

from method_extension.common.fitting import ExtensionConfig, FitState, fit_named_method

__all__ = ["ExtensionConfig", "FitState", "fit_named_method"]
