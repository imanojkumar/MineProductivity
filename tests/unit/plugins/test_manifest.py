"""Tests for mineproductivity.plugins.manifest."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core import ValidationError
from mineproductivity.plugins.manifest import PluginDependency, PluginManifest
from mineproductivity.registry import EntryPointSpec, VersionRange


def make_manifest(**overrides: object) -> PluginManifest:
    defaults: dict[str, object] = dict(
        plugin_name="haulmetrics",
        plugin_version="1.0.0",
        core_version_range=VersionRange(min_version="0.5.0", max_version_exclusive="1.0.0"),
        provides=(EntryPointSpec(group="mineproductivity.kpis", target_registry="kpis"),),
    )
    defaults.update(overrides)
    return PluginManifest(**defaults)  # type: ignore[arg-type]


class TestPluginDependency:
    def test_valid_construction(self) -> None:
        dep = PluginDependency(
            plugin_name="core-kpis",
            version_range=VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0"),
        )
        assert dep.plugin_name == "core-kpis"

    def test_empty_plugin_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PluginDependency(
                plugin_name="",
                version_range=VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0"),
            )


class TestPluginManifest:
    def test_valid_construction(self) -> None:
        manifest = make_manifest()
        assert manifest.plugin_name == "haulmetrics"
        assert manifest.plugin_version == "1.0.0"

    def test_depends_on_defaults_to_empty_tuple(self) -> None:
        manifest = make_manifest()
        assert manifest.depends_on == ()

    def test_depends_on_settable(self) -> None:
        dep = PluginDependency(
            plugin_name="core-kpis",
            version_range=VersionRange(min_version="1.0.0", max_version_exclusive="2.0.0"),
        )
        manifest = make_manifest(depends_on=(dep,))
        assert manifest.depends_on == (dep,)

    def test_empty_plugin_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_manifest(plugin_name="")

    def test_empty_plugin_version_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_manifest(plugin_version="")

    def test_is_frozen(self) -> None:
        manifest = make_manifest()
        with pytest.raises(dataclasses.FrozenInstanceError):
            manifest.plugin_name = "other"  # type: ignore[misc]

    def test_structural_equality(self) -> None:
        a = make_manifest()
        b = make_manifest()
        assert a == b
