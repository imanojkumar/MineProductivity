"""Plugin activation-order resolution.

Dependency resolution is specified as an interface obligation only
(design spec §34, Known Constraints); topological sort is the obvious
choice and is what this module implements.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from mineproductivity.core import Result

from mineproductivity.plugins.exceptions import PluginDependencyError
from mineproductivity.plugins.manifest import PluginManifest

__all__ = ["resolve_activation_order"]


def resolve_activation_order(
    manifests: Sequence[PluginManifest],
) -> Result[Sequence[PluginManifest]]:
    """Order ``manifests`` so that every plugin appears after every
    plugin it declares a :class:`~mineproductivity.plugins.manifest.PluginDependency`
    on (a topological sort, via Kahn's algorithm).

    Returns
    -------
    Result[Sequence[PluginManifest]]
        ``Result.ok`` with the dependency-respecting order, or
        ``Result.err(PluginDependencyError)`` if a declared dependency
        names a plugin not present in ``manifests``, or if the
        dependency graph contains a cycle.
    """
    by_name = {manifest.plugin_name: manifest for manifest in manifests}

    for manifest in manifests:
        for dependency in manifest.depends_on:
            if dependency.plugin_name not in by_name:
                return Result.err(
                    PluginDependencyError(
                        f"plugin {manifest.plugin_name!r} depends on "
                        f"{dependency.plugin_name!r}, which is not among the "
                        f"manifests being resolved"
                    )
                )

    in_degree: dict[str, int] = {name: 0 for name in by_name}
    dependents: dict[str, list[str]] = {name: [] for name in by_name}
    for manifest in manifests:
        for dependency in manifest.depends_on:
            dependents[dependency.plugin_name].append(manifest.plugin_name)
            in_degree[manifest.plugin_name] += 1

    queue: deque[str] = deque(sorted(name for name, degree in in_degree.items() if degree == 0))
    ordered_names: list[str] = []
    while queue:
        name = queue.popleft()
        ordered_names.append(name)
        for dependent_name in sorted(dependents[name]):
            in_degree[dependent_name] -= 1
            if in_degree[dependent_name] == 0:
                queue.append(dependent_name)

    if len(ordered_names) != len(manifests):
        return Result.err(
            PluginDependencyError("circular plugin dependency detected among the given manifests")
        )
    return Result.ok(tuple(by_name[name] for name in ordered_names))
