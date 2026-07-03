"""A compatible and an incompatible plugin, side by side: version-gating
via VersionRange/VersionCompatibility, and the isolation rule -- one
incompatible plugin's rejection never blocks a compatible plugin from
activating.

Run: python examples/registry/02_version_compatibility.py
"""

from __future__ import annotations

from mineproductivity.plugins import PluginManifest, PluginState
from mineproductivity.plugins.lifecycle import _DefaultPluginLifecycle
from mineproductivity.registry import EntryPointSpec, VersionCompatibility, VersionRange


def main() -> None:
    installed_core_version = "0.5.0"
    print(f"--- Installed core version: {installed_core_version} ---")

    print()
    print("--- Two plugins with different declared compatibility ranges ---")
    compatible_range = VersionRange(min_version="0.4.0", max_version_exclusive="1.0.0")
    incompatible_range = VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0")
    print(
        f"compatible_range:   [{compatible_range.min_version}, {compatible_range.max_version_exclusive})"
    )
    print(
        f"incompatible_range: [{incompatible_range.min_version}, {incompatible_range.max_version_exclusive})"
    )

    print()
    print("--- VersionCompatibility.is_compatible() ---")
    print(
        f"compatible?   {VersionCompatibility.is_compatible(compatible_range, installed_core_version)}"
    )
    print(
        f"incompatible? {VersionCompatibility.is_compatible(incompatible_range, installed_core_version)}"
    )

    print()
    print("--- Full PluginLifecycle.activate(), both plugins, isolation proven ---")
    lifecycle = _DefaultPluginLifecycle(core_version=installed_core_version)

    good_manifest = PluginManifest(
        plugin_name="haulmetrics",
        plugin_version="1.0.0",
        core_version_range=compatible_range,
        provides=(EntryPointSpec(group="mineproductivity.kpis", target_registry="kpis"),),
    )
    bad_manifest = PluginManifest(
        plugin_name="legacy-analytics-pack",
        plugin_version="1.0.0",
        core_version_range=incompatible_range,
        provides=(EntryPointSpec(group="mineproductivity.analytics", target_registry="analytics"),),
    )

    bad_result = lifecycle.activate(bad_manifest)
    good_result = lifecycle.activate(good_manifest)

    print(
        f"legacy-analytics-pack: activate().is_ok={bad_result.is_ok}, state={lifecycle.state_of('legacy-analytics-pack').value}"
    )
    print(
        f"haulmetrics:           activate().is_ok={good_result.is_ok}, state={lifecycle.state_of('haulmetrics').value}"
    )

    assert lifecycle.state_of("legacy-analytics-pack") is PluginState.FAILED
    assert lifecycle.state_of("haulmetrics") is PluginState.ACTIVE
    print()
    print("The incompatible plugin's failure never touched the compatible plugin's activation.")


if __name__ == "__main__":
    main()
