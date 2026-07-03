"""``mineproductivity.plugins`` -- the plugin lifecycle layer built on
``registry``: manifests, version-gated activation, inter-plugin
dependency ordering, and graceful failure isolation.

Implements ``docs/architecture/03_Registry_Framework_Design_Specification.md``
exactly. ``plugins`` depends on ``core`` and ``registry`` -- see
``README.md`` for the full set of architectural rules this package must
satisfy.

Everything documented here is part of the public API and can be imported
directly from ``mineproductivity.plugins``, e.g.::

    from mineproductivity.plugins import PluginManifest, PluginLifecycle
"""

from __future__ import annotations

from mineproductivity.plugins.dependency import resolve_activation_order
from mineproductivity.plugins.exceptions import PluginActivationError, PluginDependencyError
from mineproductivity.plugins.lifecycle import PluginLifecycle, PluginState
from mineproductivity.plugins.loader import PluginLoader
from mineproductivity.plugins.manifest import PluginDependency, PluginManifest

__all__ = [
    "PluginActivationError",
    "PluginDependency",
    "PluginDependencyError",
    "PluginLifecycle",
    "PluginLoader",
    "PluginManifest",
    "PluginState",
    "resolve_activation_order",
]
