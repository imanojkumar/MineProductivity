"""Tests for mineproductivity.plugins.dependency."""

from __future__ import annotations

from mineproductivity.plugins.dependency import resolve_activation_order
from mineproductivity.plugins.exceptions import PluginDependencyError
from mineproductivity.plugins.manifest import PluginDependency, PluginManifest
from mineproductivity.registry import VersionRange

_ANY_RANGE = VersionRange(min_version="0.0.0", max_version_exclusive="99.0.0")


def make_manifest(name: str, *, depends_on: tuple[PluginDependency, ...] = ()) -> PluginManifest:
    return PluginManifest(
        plugin_name=name,
        plugin_version="1.0.0",
        core_version_range=_ANY_RANGE,
        provides=(),
        depends_on=depends_on,
    )


def dep_on(name: str) -> PluginDependency:
    return PluginDependency(plugin_name=name, version_range=_ANY_RANGE)


class TestNoDependencies:
    def test_independent_plugins_ordered_alphabetically(self) -> None:
        b, a, c = make_manifest("b"), make_manifest("a"), make_manifest("c")
        result = resolve_activation_order([b, a, c])
        assert result.is_ok
        assert [m.plugin_name for m in result.value] == ["a", "b", "c"]

    def test_empty_input(self) -> None:
        result = resolve_activation_order([])
        assert result.is_ok
        assert result.value == ()

    def test_single_manifest(self) -> None:
        result = resolve_activation_order([make_manifest("solo")])
        assert result.is_ok
        assert [m.plugin_name for m in result.value] == ["solo"]


class TestLinearDependencies:
    def test_dependency_ordered_before_dependent(self) -> None:
        base = make_manifest("base")
        dependent = make_manifest("dependent", depends_on=(dep_on("base"),))
        result = resolve_activation_order([dependent, base])
        assert result.is_ok
        assert [m.plugin_name for m in result.value] == ["base", "dependent"]

    def test_three_level_chain(self) -> None:
        a = make_manifest("a")
        b = make_manifest("b", depends_on=(dep_on("a"),))
        c = make_manifest("c", depends_on=(dep_on("b"),))
        result = resolve_activation_order([c, b, a])
        assert result.is_ok
        assert [m.plugin_name for m in result.value] == ["a", "b", "c"]


class TestDiamondDependencies:
    def test_diamond_shaped_graph_resolves(self) -> None:
        base = make_manifest("base")
        left = make_manifest("left", depends_on=(dep_on("base"),))
        right = make_manifest("right", depends_on=(dep_on("base"),))
        top = make_manifest("top", depends_on=(dep_on("left"), dep_on("right")))
        result = resolve_activation_order([top, left, right, base])
        assert result.is_ok
        order = [m.plugin_name for m in result.value]
        assert order.index("base") < order.index("left")
        assert order.index("base") < order.index("right")
        assert order.index("left") < order.index("top")
        assert order.index("right") < order.index("top")


class TestFailureModes:
    def test_missing_dependency_rejected(self) -> None:
        dependent = make_manifest("dependent", depends_on=(dep_on("ghost"),))
        result = resolve_activation_order([dependent])
        assert result.is_err
        assert isinstance(result.error, PluginDependencyError)

    def test_direct_cycle_rejected(self) -> None:
        a = make_manifest("a", depends_on=(dep_on("b"),))
        b = make_manifest("b", depends_on=(dep_on("a"),))
        result = resolve_activation_order([a, b])
        assert result.is_err
        assert isinstance(result.error, PluginDependencyError)

    def test_self_dependency_rejected(self) -> None:
        a = make_manifest("a", depends_on=(dep_on("a"),))
        result = resolve_activation_order([a])
        assert result.is_err
        assert isinstance(result.error, PluginDependencyError)

    def test_longer_cycle_rejected(self) -> None:
        a = make_manifest("a", depends_on=(dep_on("c"),))
        b = make_manifest("b", depends_on=(dep_on("a"),))
        c = make_manifest("c", depends_on=(dep_on("b"),))
        result = resolve_activation_order([a, b, c])
        assert result.is_err
        assert isinstance(result.error, PluginDependencyError)
