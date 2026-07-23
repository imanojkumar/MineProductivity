"""A plugin's declared identity (``PluginManifest``) driven through its
lifecycle state machine (Discovered -> Validated -> Active), plus version
gating and graceful, isolated failure.

``plugins`` ships the ``PluginLifecycle`` *contract*; the reference
in-process implementation used here (``_DefaultPluginLifecycle``) is
private, exactly as ``events`` keeps its reference ``EventStore`` private.

Run: python examples/plugins/01_manifest_and_lifecycle.py
"""

from __future__ import annotations

from mineproductivity.plugins import PluginManifest, PluginState
from mineproductivity.plugins.lifecycle import _DefaultPluginLifecycle
from mineproductivity.registry import EntryPointSpec, VersionRange


def main() -> None:
    lifecycle = _DefaultPluginLifecycle(core_version="1.2.0")

    print("--- 1. A manifest is a plugin's declared identity ---")
    manifest = PluginManifest(
        plugin_name="haulmetrics",
        plugin_version="1.0.0",
        core_version_range=VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0"),
        provides=(EntryPointSpec(group="mineproductivity.kpis", target_registry="kpis"),),
    )
    print(
        f"{manifest.plugin_name} v{manifest.plugin_version} "
        f"provides -> {[spec.target_registry for spec in manifest.provides]}"
    )

    print()
    print("--- 2. Activation walks the state machine to Active ---")
    result = lifecycle.activate(manifest)
    print(f"activate().is_ok={result.is_ok}, state={lifecycle.state_of('haulmetrics').value}")

    print()
    print("--- 3. Version gating: a plugin built for an older core is failed, in isolation ---")
    legacy = PluginManifest(
        plugin_name="legacy-pack",
        plugin_version="0.9.0",
        core_version_range=VersionRange(min_version="0.1.0", max_version_exclusive="1.0.0"),
        provides=(EntryPointSpec(group="mineproductivity.analytics", target_registry="analytics"),),
    )
    legacy_result = lifecycle.activate(legacy)
    print(
        f"legacy-pack activate().is_ok={legacy_result.is_ok}, state={lifecycle.state_of('legacy-pack').value}"
    )
    print(
        f"haulmetrics still: {lifecycle.state_of('haulmetrics').value} (unaffected by legacy-pack's failure)"
    )

    print()
    print("--- 4. Deactivation moves an active plugin to Deactivated ---")
    lifecycle.deactivate("haulmetrics")
    print(f"haulmetrics after deactivate: {lifecycle.state_of('haulmetrics').value}")
    print(f"all five states exist: {[s.value for s in PluginState]}")


if __name__ == "__main__":
    main()
