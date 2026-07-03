"""``PluginManifest``/``PluginDependency``: the declared identity of one
installed plugin package.
"""

from __future__ import annotations

import dataclasses

from mineproductivity.core import BaseValueObject, ValidationError
from mineproductivity.registry import EntryPointSpec, VersionRange

__all__ = ["PluginDependency", "PluginManifest"]


@dataclasses.dataclass(frozen=True, slots=True)
class PluginDependency(BaseValueObject):
    """One other plugin, by name, that a plugin requires to already be
    active before it can itself activate."""

    plugin_name: str
    version_range: VersionRange

    def validate(self) -> None:
        if not self.plugin_name.strip():
            raise ValidationError("PluginDependency.plugin_name must not be empty")


@dataclasses.dataclass(frozen=True, slots=True)
class PluginManifest(BaseValueObject):
    """The declared identity of one installed plugin package -- richer
    than a single entry-point, since one plugin package can register
    into multiple registries (e.g. a site pack registering both KPIs and
    equipment types).

    Examples
    --------
    >>> manifest = PluginManifest(
    ...     plugin_name="haulmetrics",
    ...     plugin_version="1.0.0",
    ...     core_version_range=VersionRange(min_version="0.5.0", max_version_exclusive="1.0.0"),
    ...     provides=(EntryPointSpec(group="mineproductivity.kpis", target_registry="kpis"),),
    ... )
    >>> manifest.plugin_name
    'haulmetrics'
    """

    plugin_name: str
    plugin_version: str
    core_version_range: VersionRange
    provides: tuple[EntryPointSpec, ...]
    depends_on: tuple[PluginDependency, ...] = dataclasses.field(default=(), kw_only=True)

    def validate(self) -> None:
        if not self.plugin_name.strip():
            raise ValidationError("PluginManifest.plugin_name must not be empty")
        if not self.plugin_version.strip():
            raise ValidationError("PluginManifest.plugin_version must not be empty")
