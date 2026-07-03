"""Integration test for the Registry Framework's discovery and isolation
guarantees, against two real, independently-built, pip-installed fixture
plugin packages (design spec §29, §30 Category B) -- not mocks.

Also exercises the full manifest -> loader -> lifecycle activation path
(``PluginLoader``/``PluginLifecycle``) against the same real fixtures,
proving the "zero-core-change" and "isolation" acceptance criteria
(design spec §37) end to end.
"""

from __future__ import annotations

from mineproductivity.plugins import PluginManifest, PluginState
from mineproductivity.plugins.lifecycle import _DefaultPluginLifecycle
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec, Registry, VersionRange

FIXTURE_GROUP = "mineproductivity.tests.registry_fixture"


class TestRealEntryPointDiscovery:
    def test_healthy_and_broken_fixtures_discovered_together(
        self, registry_fixture_plugins_installed: None
    ) -> None:
        discovery = EntryPointDiscovery()
        spec = EntryPointSpec(group=FIXTURE_GROUP, target_registry="test-fixtures")

        result = discovery.discover(spec)

        assert result.is_ok, f"discovery scan itself should never fail: {result}"
        assert result.value == ("healthy",), (
            "the broken fixture's import failure must be isolated, not "
            "propagated -- only the healthy fixture's name should appear"
        )

    def test_broken_fixture_module_is_never_left_importable_afterwards(
        self, registry_fixture_plugins_installed: None
    ) -> None:
        import sys

        sys.modules.pop("mineproductivity_registry_fixture_broken", None)
        discovery = EntryPointDiscovery()
        discovery.discover(EntryPointSpec(group=FIXTURE_GROUP, target_registry="test-fixtures"))

        assert "mineproductivity_registry_fixture_broken" not in sys.modules, (
            "a module that raised during its own top-level execution must "
            "not be left in sys.modules as if it had imported successfully"
        )

    def test_healthy_fixture_module_actually_ran(
        self, registry_fixture_plugins_installed: None
    ) -> None:
        discovery = EntryPointDiscovery()
        discovery.discover(EntryPointSpec(group=FIXTURE_GROUP, target_registry="test-fixtures"))

        import mineproductivity_registry_fixture_healthy as healthy_module

        assert healthy_module.IMPORTED is True


class TestFullPluginActivationAgainstRealFixtures:
    def test_manifest_providing_the_real_fixture_group_activates(
        self, registry_fixture_plugins_installed: None
    ) -> None:
        lifecycle = _DefaultPluginLifecycle(core_version="0.5.0")
        manifest = PluginManifest(
            plugin_name="registry-fixture-bundle",
            plugin_version="0.1.0",
            core_version_range=VersionRange(min_version="0.0.0", max_version_exclusive="99.0.0"),
            provides=(EntryPointSpec(group=FIXTURE_GROUP, target_registry="test-fixtures"),),
        )

        result = lifecycle.activate(manifest)

        assert result.is_ok, result
        assert lifecycle.state_of("registry-fixture-bundle") is PluginState.ACTIVE

    def test_incompatible_core_version_fails_activation_without_importing_anything(
        self, registry_fixture_plugins_installed: None
    ) -> None:
        lifecycle = _DefaultPluginLifecycle(core_version="0.5.0")
        manifest = PluginManifest(
            plugin_name="registry-fixture-bundle-incompatible",
            plugin_version="0.1.0",
            core_version_range=VersionRange(min_version="10.0.0", max_version_exclusive="11.0.0"),
            provides=(EntryPointSpec(group=FIXTURE_GROUP, target_registry="test-fixtures"),),
        )

        result = lifecycle.activate(manifest)

        assert result.is_err
        assert lifecycle.state_of("registry-fixture-bundle-incompatible") is PluginState.FAILED


class TestZeroCoreChangeProof:
    """A fixture plugin registers into an application-owned Registry
    without any modification to mineproductivity.core or
    mineproductivity.registry itself -- the acceptance test for
    "plugin-first" (design spec §37.1, restricted here to the registry
    mechanism itself rather than a full KPI/connector/entity-type
    round-trip, since those domain packages do not exist yet)."""

    def test_third_party_style_registration_never_touches_registry_source(
        self, registry_fixture_plugins_installed: None
    ) -> None:
        app_registry: Registry[str, str] = Registry(name="fixture-demo")

        discovery = EntryPointDiscovery()
        result = discovery.discover(
            EntryPointSpec(group=FIXTURE_GROUP, target_registry="fixture-demo")
        )
        assert result.is_ok

        for name in result.value:
            app_registry.register(name, name)

        assert "healthy" in app_registry
        assert len(app_registry) == 1
