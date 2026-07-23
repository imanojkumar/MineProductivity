"""``resolve_activation_order``: topologically order plugins so each
activates only after every plugin it declares a ``PluginDependency`` on --
and see a missing dependency and a dependency cycle both rejected as a
``Result.err`` rather than raising or hanging.

Run: python examples/plugins/02_activation_order.py
"""

from __future__ import annotations

from collections.abc import Sequence

from mineproductivity.plugins import PluginDependency, PluginManifest, resolve_activation_order
from mineproductivity.registry import EntryPointSpec, VersionRange

_CORE_RANGE = VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0")


def _manifest(name: str, *, deps: Sequence[str] = ()) -> PluginManifest:
    return PluginManifest(
        plugin_name=name,
        plugin_version="1.0.0",
        core_version_range=_CORE_RANGE,
        provides=(EntryPointSpec(group=f"mineproductivity.{name}", target_registry=name),),
        depends_on=tuple(
            PluginDependency(plugin_name=dep, version_range=_CORE_RANGE) for dep in deps
        ),
    )


def main() -> None:
    print("--- 1. Declared out of order; the resolver sorts by dependency ---")
    # site-pack depends on haulmetrics, which depends on base-metrics
    base = _manifest("base-metrics")
    haul = _manifest("haulmetrics", deps=("base-metrics",))
    site = _manifest("site-pack", deps=("haulmetrics",))
    ordered = resolve_activation_order([site, haul, base])
    print(f"is_ok={ordered.is_ok}, order={[m.plugin_name for m in ordered.value]}")

    print()
    print("--- 2. A dependency on a plugin not being resolved is rejected ---")
    orphan = resolve_activation_order([_manifest("orphan", deps=("not-installed",))])
    print(f"is_ok={orphan.is_ok}, error={type(orphan.error).__name__}")

    print()
    print("--- 3. A dependency cycle is detected, never hung on ---")
    a = _manifest("plugin-a", deps=("plugin-b",))
    b = _manifest("plugin-b", deps=("plugin-a",))
    cyclic = resolve_activation_order([a, b])
    print(f"is_ok={cyclic.is_ok}, error={type(cyclic.error).__name__}")


if __name__ == "__main__":
    main()
