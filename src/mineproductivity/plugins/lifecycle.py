"""``PluginState``/``PluginLifecycle``: orchestrates a
:class:`~mineproductivity.plugins.manifest.PluginManifest` through its
discovery-to-active state machine.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum

from mineproductivity.core import NotFoundError, Result
from mineproductivity.registry import VersionCompatibility

from mineproductivity.plugins.exceptions import PluginActivationError, PluginDependencyError
from mineproductivity.plugins.loader import PluginLoader
from mineproductivity.plugins.manifest import PluginManifest

__all__ = ["PluginLifecycle", "PluginState"]

_logger = logging.getLogger(__name__)


class PluginState(Enum):
    """The five states a plugin passes through, per design spec §11."""

    DISCOVERED = "discovered"
    VALIDATED = "validated"
    ACTIVE = "active"
    FAILED = "failed"
    DEACTIVATED = "deactivated"


class PluginLifecycle(ABC):
    """Orchestrates a :class:`PluginManifest` through :class:`PluginState`,
    delegating the actual entry-point scanning to
    :class:`~mineproductivity.registry.EntryPointDiscovery` (via
    :class:`~mineproductivity.plugins.loader.PluginLoader`) and adding:
    inter-plugin dependency resolution, activation ordering, and
    graceful failure isolation (one bad plugin must not prevent others
    from loading).
    """

    @abstractmethod
    def activate(self, manifest: PluginManifest) -> Result[None]:
        """Move ``manifest`` from ``Discovered`` to ``Active`` (or
        ``Failed``, in isolation from every other plugin's activation)."""

    @abstractmethod
    def deactivate(self, plugin_name: str) -> Result[None]:
        """Move an active plugin to ``Deactivated``."""

    @abstractmethod
    def state_of(self, plugin_name: str) -> PluginState:
        """Return the current :class:`PluginState` of ``plugin_name``.

        Raises
        ------
        NotFoundError
            If ``plugin_name`` has never been passed to :meth:`activate`.
        """


class _DefaultPluginLifecycle(PluginLifecycle):
    """The reference :class:`PluginLifecycle` implementation: in-process,
    dict-backed state tracking, dependency checking against already-
    activated plugins, and version-gating via
    :class:`~mineproductivity.registry.VersionCompatibility`. Suitable
    for tests, examples, and single-process deployments; not part of the
    package's frozen public API (a custom `PluginLifecycle` remains a
    supported extension point per design spec §16).
    """

    def __init__(self, *, core_version: str, loader: PluginLoader | None = None) -> None:
        self._core_version = core_version
        self._loader = loader if loader is not None else PluginLoader()
        self._states: dict[str, PluginState] = {}

    def activate(self, manifest: PluginManifest) -> Result[None]:
        self._states[manifest.plugin_name] = PluginState.DISCOVERED

        for dependency in manifest.depends_on:
            if self._states.get(dependency.plugin_name) is not PluginState.ACTIVE:
                self._states[manifest.plugin_name] = PluginState.FAILED
                error = PluginDependencyError(
                    f"plugin {manifest.plugin_name!r} requires "
                    f"{dependency.plugin_name!r} to be active first"
                )
                _logger.warning(
                    "plugin %r failed to activate: unmet dependency on %r",
                    manifest.plugin_name,
                    dependency.plugin_name,
                )
                return Result.err(error)

        self._states[manifest.plugin_name] = PluginState.VALIDATED
        try:
            VersionCompatibility.check_or_raise(manifest.core_version_range, self._core_version)
        except Exception as exc:
            self._states[manifest.plugin_name] = PluginState.FAILED
            _logger.warning(
                "plugin %r failed to activate: version incompatible (%s)",
                manifest.plugin_name,
                exc,
            )
            return Result.err(exc)

        load_result = self._loader.load(manifest)
        if load_result.is_err:
            self._states[manifest.plugin_name] = PluginState.FAILED
            _logger.warning(
                "plugin %r failed to activate: %s",
                manifest.plugin_name,
                load_result.error,
            )
            return Result.err(PluginActivationError(str(load_result.error)))

        self._states[manifest.plugin_name] = PluginState.ACTIVE
        registered_counts = {group: len(names) for group, names in load_result.value.items()}
        _logger.info(
            "plugin %r (v%s) activated: %s",
            manifest.plugin_name,
            manifest.plugin_version,
            registered_counts,
        )
        return Result.ok(None)

    def deactivate(self, plugin_name: str) -> Result[None]:
        if plugin_name not in self._states:
            return Result.err(
                PluginActivationError(f"cannot deactivate unknown plugin {plugin_name!r}")
            )
        self._states[plugin_name] = PluginState.DEACTIVATED
        return Result.ok(None)

    def state_of(self, plugin_name: str) -> PluginState:
        try:
            return self._states[plugin_name]
        except KeyError as exc:
            raise NotFoundError(f"no plugin named {plugin_name!r} has been activated") from exc
