"""The ``mineproductivity.plugins`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError

__all__ = ["PluginActivationError", "PluginDependencyError"]


class PluginActivationError(MineProductivityError):
    """``PluginLifecycle.activate()`` failed for a reason other than
    version incompatibility (e.g. the entry-point's target module raised
    on import)."""


class PluginDependencyError(PluginActivationError):
    """A declared :class:`~mineproductivity.plugins.manifest.PluginDependency`
    could not be satisfied."""
