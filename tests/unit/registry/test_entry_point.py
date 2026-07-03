"""Tests for mineproductivity.registry.entry_point."""

from __future__ import annotations

import importlib.metadata
import sys
import types

import pytest

from mineproductivity.core import ValidationError
from mineproductivity.registry.entry_point import EntryPointDiscovery, EntryPointSpec

GROUP = "mineproductivity.tests.unit_fixture_group"


def _install_fake_module(name: str) -> None:
    """Register a trivial, already-importable module in ``sys.modules``
    under ``name`` -- ``EntryPoint.load()`` finds it via the import
    system's own module cache, no real installed package required."""
    module = types.ModuleType(name)
    module.LOADED = True  # type: ignore[attr-defined]
    sys.modules[name] = module


@pytest.fixture
def fake_entry_points(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """Return a helper that makes ``importlib.metadata.entry_points(group=...)``
    return a caller-supplied sequence of real ``EntryPoint`` objects for
    ``GROUP`` only, leaving every other group's real result untouched."""
    real_entry_points = importlib.metadata.entry_points

    def install(entry_points: tuple[importlib.metadata.EntryPoint, ...]) -> None:
        def fake(*, group: str):  # type: ignore[no-untyped-def]
            if group == GROUP:
                return entry_points
            return real_entry_points(group=group)

        monkeypatch.setattr(importlib.metadata, "entry_points", fake)

    return install


class TestEntryPointSpec:
    def test_valid_construction(self) -> None:
        spec = EntryPointSpec(group="mineproductivity.kpis", target_registry="kpis")
        assert spec.group == "mineproductivity.kpis"
        assert spec.target_registry == "kpis"

    def test_empty_group_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EntryPointSpec(group="", target_registry="kpis")

    def test_empty_target_registry_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EntryPointSpec(group="mineproductivity.kpis", target_registry="")

    def test_is_hashable_for_cache_keying(self) -> None:
        a = EntryPointSpec(group="g", target_registry="t")
        b = EntryPointSpec(group="g", target_registry="t")
        assert hash(a) == hash(b)
        assert {a, b} == {a}


class TestEntryPointDiscovery:
    def test_empty_group_returns_empty_ok(self) -> None:
        discovery = EntryPointDiscovery()
        spec = EntryPointSpec(
            group="mineproductivity.tests.definitely_empty_group", target_registry="x"
        )
        result = discovery.discover(spec)
        assert result.is_ok
        assert result.value == ()

    def test_successful_entry_point_is_reported_loaded(self, fake_entry_points) -> None:  # type: ignore[no-untyped-def]
        module_name = "mineproductivity_test_fixture_healthy_unit"
        _install_fake_module(module_name)
        ep = importlib.metadata.EntryPoint(name="healthy", value=module_name, group=GROUP)
        fake_entry_points((ep,))

        discovery = EntryPointDiscovery()
        result = discovery.discover(EntryPointSpec(group=GROUP, target_registry="x"))

        assert result.is_ok
        assert result.value == ("healthy",)

    def test_entry_points_are_returned_in_name_order(self, fake_entry_points) -> None:  # type: ignore[no-untyped-def]
        _install_fake_module("mineproductivity_test_fixture_b")
        _install_fake_module("mineproductivity_test_fixture_a")
        eps = (
            importlib.metadata.EntryPoint(
                name="bravo", value="mineproductivity_test_fixture_b", group=GROUP
            ),
            importlib.metadata.EntryPoint(
                name="alpha", value="mineproductivity_test_fixture_a", group=GROUP
            ),
        )
        fake_entry_points(eps)

        discovery = EntryPointDiscovery()
        result = discovery.discover(EntryPointSpec(group=GROUP, target_registry="x"))

        assert result.value == ("alpha", "bravo")

    def test_discover_isolates_one_failing_entry_point(  # type: ignore[no-untyped-def]
        self, fake_entry_points, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        broken_module_path = tmp_path / "mineproductivity_test_fixture_broken_unit.py"
        broken_module_path.write_text("raise RuntimeError('boom')\n", encoding="utf-8")
        monkeypatch.syspath_prepend(str(tmp_path))

        healthy_module_name = "mineproductivity_test_fixture_healthy_unit2"
        _install_fake_module(healthy_module_name)

        eps = (
            importlib.metadata.EntryPoint(
                name="broken", value="mineproductivity_test_fixture_broken_unit", group=GROUP
            ),
            importlib.metadata.EntryPoint(name="healthy", value=healthy_module_name, group=GROUP),
        )
        fake_entry_points(eps)

        discovery = EntryPointDiscovery()
        result = discovery.discover(EntryPointSpec(group=GROUP, target_registry="x"))

        assert result.is_ok, "one bad entry-point must not fail the whole discovery call"
        assert result.value == ("healthy",)
        sys.modules.pop("mineproductivity_test_fixture_broken_unit", None)

    def test_discover_result_type_is_tuple(self, fake_entry_points) -> None:  # type: ignore[no-untyped-def]
        fake_entry_points(())
        discovery = EntryPointDiscovery()
        result = discovery.discover(EntryPointSpec(group=GROUP, target_registry="x"))
        assert isinstance(result.value, tuple)
