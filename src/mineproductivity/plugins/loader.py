"""``PluginLoader``: loads every entry-point group one
:class:`~mineproductivity.plugins.manifest.PluginManifest` declares.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mineproductivity.core import Result
from mineproductivity.registry import EntryPointDiscovery

from mineproductivity.plugins.manifest import PluginManifest

__all__ = ["PluginLoader"]


class PluginLoader:
    """Loads every :class:`~mineproductivity.registry.EntryPointSpec` a
    :class:`PluginManifest` declares in ``provides``, delegating each to
    :class:`~mineproductivity.registry.EntryPointDiscovery` -- the
    mechanism :class:`~mineproductivity.plugins.lifecycle.PluginLifecycle`
    implementations use to complete the ``Validated -> Active``
    transition (design spec §15).

    Import-time failure within any one entry-point is already isolated
    by :class:`~mineproductivity.registry.EntryPointDiscovery` itself
    (that entry-point is simply absent from its result); this class
    additionally treats a systemic failure of one ``provides`` group's
    scan (e.g. corrupted package metadata) as fatal to loading the whole
    manifest, since a manifest that cannot even be scanned has provided
    nothing.
    """

    def __init__(self, *, discovery: EntryPointDiscovery | None = None) -> None:
        self._discovery = discovery if discovery is not None else EntryPointDiscovery()

    def load(self, manifest: PluginManifest) -> Result[Mapping[str, Sequence[str]]]:
        """Discover every ``EntryPointSpec`` in ``manifest.provides``.

        Returns
        -------
        Result[Mapping[str, Sequence[str]]]
            ``Result.ok`` mapping each provided entry-point group to the
            entry-point names that loaded successfully within it, or the
            first ``Result.err`` encountered while scanning a group.
        """
        loaded: dict[str, Sequence[str]] = {}
        for spec in manifest.provides:
            result = self._discovery.discover(spec)
            if result.is_err:
                return Result.err(result.error)
            loaded[spec.group] = result.value
        return Result.ok(loaded)
