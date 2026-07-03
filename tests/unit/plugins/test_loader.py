"""Tests for mineproductivity.plugins.loader."""

from __future__ import annotations

from collections.abc import Sequence

from mineproductivity.core import Result
from mineproductivity.plugins.loader import PluginLoader
from mineproductivity.plugins.manifest import PluginManifest
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec, VersionRange

_ANY_RANGE = VersionRange(min_version="0.0.0", max_version_exclusive="99.0.0")


class _StubDiscovery(EntryPointDiscovery):
    def __init__(self, results: dict[str, Result[Sequence[str]]]) -> None:
        self._results = results

    def discover(self, spec: EntryPointSpec) -> Result[Sequence[str]]:
        return self._results[spec.group]


class TestLoad:
    def test_single_group_all_loaded(self) -> None:
        discovery = _StubDiscovery({"g1": Result.ok(("a", "b"))})
        loader = PluginLoader(discovery=discovery)
        manifest = PluginManifest(
            plugin_name="p",
            plugin_version="1.0.0",
            core_version_range=_ANY_RANGE,
            provides=(EntryPointSpec(group="g1", target_registry="t1"),),
        )

        result = loader.load(manifest)

        assert result.is_ok
        assert result.value == {"g1": ("a", "b")}

    def test_multiple_groups_aggregated(self) -> None:
        discovery = _StubDiscovery({"g1": Result.ok(("a",)), "g2": Result.ok(("b", "c"))})
        loader = PluginLoader(discovery=discovery)
        manifest = PluginManifest(
            plugin_name="p",
            plugin_version="1.0.0",
            core_version_range=_ANY_RANGE,
            provides=(
                EntryPointSpec(group="g1", target_registry="t1"),
                EntryPointSpec(group="g2", target_registry="t2"),
            ),
        )

        result = loader.load(manifest)

        assert result.is_ok
        assert result.value == {"g1": ("a",), "g2": ("b", "c")}

    def test_no_provides_yields_empty_mapping(self) -> None:
        loader = PluginLoader(discovery=_StubDiscovery({}))
        manifest = PluginManifest(
            plugin_name="p", plugin_version="1.0.0", core_version_range=_ANY_RANGE, provides=()
        )

        result = loader.load(manifest)

        assert result.is_ok
        assert result.value == {}

    def test_one_group_failing_short_circuits(self) -> None:
        discovery = _StubDiscovery({"g1": Result.ok(("a",)), "g2": Result.err("scan failed")})
        loader = PluginLoader(discovery=discovery)
        manifest = PluginManifest(
            plugin_name="p",
            plugin_version="1.0.0",
            core_version_range=_ANY_RANGE,
            provides=(
                EntryPointSpec(group="g1", target_registry="t1"),
                EntryPointSpec(group="g2", target_registry="t2"),
            ),
        )

        result = loader.load(manifest)

        assert result.is_err

    def test_default_discovery_used_when_none_supplied(self) -> None:
        loader = PluginLoader()
        manifest = PluginManifest(
            plugin_name="p",
            plugin_version="1.0.0",
            core_version_range=_ANY_RANGE,
            provides=(
                EntryPointSpec(group="mineproductivity.tests.empty_group_xyz", target_registry="t"),
            ),
        )

        result = loader.load(manifest)

        assert result.is_ok
        assert result.value == {"mineproductivity.tests.empty_group_xyz": ()}
