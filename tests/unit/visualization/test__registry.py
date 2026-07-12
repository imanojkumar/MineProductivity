"""Tests for mineproductivity.visualization._registry (design spec
§20, §28): two orthogonal registries, never merged, plus the
entry-point plugin path for both groups."""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

import pytest

import mineproductivity.visualization as visualization
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec, UnregisteredLookupError
from mineproductivity.visualization._registry import (
    REGISTRY,
    RENDERERS,
    register,
    register_renderer,
)
from mineproductivity.visualization.abstractions import (
    Visualization,
    VisualizationCategory,
    VisualizationContext,
    VisualizationMetadata,
)
from mineproductivity.visualization.exceptions import (
    VisualizationValidationError,
    VisualizationVersionConflictError,
)
from mineproductivity.visualization.presentation import PresentationModel
from mineproductivity.visualization.renderer import (
    RenderedOutput,
    Renderer,
    RendererMetadata,
)
from mineproductivity.visualization.widget import Widget


def _viz_meta(code: str) -> VisualizationMetadata:
    return VisualizationMetadata(
        code=code, category=VisualizationCategory.KPI_CARD, description="x"
    )


def _unique_viz_code() -> str:
    return f"KPI_CARD.RegistryFixture{uuid.uuid4().hex}"


class _FixtureVisualization(Visualization):
    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        return PresentationModel(category=VisualizationCategory.KPI_CARD, title=widget.code)


class _FixtureRenderer(Renderer):
    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(format="text", payload=model.title)


class TestNoBuiltInTypesShipped:
    def test_no_module_in_the_package_registers_anything(self) -> None:
        """Design spec §8, §16: interface-only throughout."""
        package_dir = Path(visualization.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "_registry.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            assert "@register" not in source, f"{py_file.name} registers a built-in"


class TestTwoOrthogonalRegistries:
    def test_registry_and_renderers_are_distinct_instances(self) -> None:
        """Design spec §20: never merged into one."""
        assert REGISTRY is not RENDERERS

    def test_a_visualization_registration_never_appears_in_renderers(self) -> None:
        code = _unique_viz_code()

        class _AViz(_FixtureVisualization):
            meta = _viz_meta(code)

        register(_AViz)
        assert REGISTRY.get(code) is _AViz
        with pytest.raises(UnregisteredLookupError):
            RENDERERS.get(code)

    def test_a_renderer_registration_never_appears_in_registry(self) -> None:
        code = f"HTML.RegistryFixture{uuid.uuid4().hex}"

        class _ARenderer(_FixtureRenderer):
            meta = RendererMetadata(code=code, description="x")

        register_renderer(_ARenderer)
        assert RENDERERS.get(code) is _ARenderer
        with pytest.raises(UnregisteredLookupError):
            REGISTRY.get(code)


class TestRegisterDecorators:
    def test_register_returns_the_class_unchanged(self) -> None:
        code = _unique_viz_code()

        class _AViz(_FixtureVisualization):
            meta = _viz_meta(code)

        assert register(_AViz) is _AViz
        assert REGISTRY.metadata_for(code).unwrap() is _AViz.meta

    def test_empty_visualization_code_raises(self) -> None:
        class _FakeMeta:
            code = ""

        class _AViz(_FixtureVisualization):
            meta = _FakeMeta()  # type: ignore[assignment]

        with pytest.raises(VisualizationValidationError):
            register(_AViz)

    def test_empty_renderer_code_raises(self) -> None:
        class _FakeMeta:
            code = ""

        class _ARenderer(_FixtureRenderer):
            meta = _FakeMeta()  # type: ignore[assignment]

        with pytest.raises(VisualizationValidationError):
            register_renderer(_ARenderer)

    def test_duplicate_visualization_code_raises_version_conflict(self) -> None:
        shared = _viz_meta(_unique_viz_code())

        class _First(_FixtureVisualization):
            meta = shared

        register(_First)

        class _Second(_FixtureVisualization):
            meta = shared

        with pytest.raises(VisualizationVersionConflictError):
            register(_Second)

    def test_duplicate_renderer_code_raises_version_conflict(self) -> None:
        shared = RendererMetadata(code=f"HTML.Conflict{uuid.uuid4().hex}", description="x")

        class _First(_FixtureRenderer):
            meta = shared

        register_renderer(_First)

        class _Second(_FixtureRenderer):
            meta = shared

        with pytest.raises(VisualizationVersionConflictError):
            register_renderer(_Second)


_VIZ_PLUGIN_SOURCE = '''\
"""A third-party presentation-type plugin -- importing this module
registers it, exactly as a pip-installed entry-point scan would
(spec 12 §28)."""

from mineproductivity.visualization import (
    PresentationModel,
    Visualization,
    VisualizationCategory,
    VisualizationContext,
    VisualizationMetadata,
    Widget,
    register,
)


@register
class SitePackKpiCard(Visualization):
    """A site pack KPI-card presentation fixture."""

    meta = VisualizationMetadata(
        code="KPI_CARD.SitePackVizFixture",
        category=VisualizationCategory.KPI_CARD,
        description="A site pack KPI-card presentation fixture.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        return PresentationModel(category=type(self).meta.category, title=widget.code)
'''

_RENDERER_PLUGIN_SOURCE = '''\
"""A third-party rendering-backend plugin (spec 12 §28)."""

from mineproductivity.visualization import (
    PresentationModel,
    RenderedOutput,
    Renderer,
    RendererMetadata,
    VisualizationContext,
    register_renderer,
)


@register_renderer
class SitePackHtmlRenderer(Renderer):
    """A site pack HTML rendering-backend fixture."""

    meta = RendererMetadata(
        code="HTML.SitePackRendererFixture",
        description="A site pack HTML rendering-backend fixture.",
    )

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(format="html", payload=f"<h1>{model.title}</h1>")
'''


def _discover_with_fixture(module_name: str, source: str, group: str, target: str) -> Any:
    with tempfile.TemporaryDirectory() as tmp_dir:
        plugin_path = Path(tmp_dir) / f"{module_name}.py"
        plugin_path.write_text(source, encoding="utf-8")
        sys.path.insert(0, tmp_dir)
        try:
            real_entry_points = importlib.metadata.entry_points
            wanted_group = group

            def _fake_entry_points(*, group: str = "", **kwargs: Any) -> Any:
                if group == wanted_group:
                    return (
                        importlib.metadata.EntryPoint(
                            name="sitepack", value=module_name, group=group
                        ),
                    )
                return real_entry_points(group=group, **kwargs)

            importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
            try:
                return EntryPointDiscovery().discover(
                    EntryPointSpec(group=group, target_registry=target)
                )
            finally:
                importlib.metadata.entry_points = real_entry_points
        finally:
            sys.path.remove(tmp_dir)
            sys.modules.pop(module_name, None)


class TestPluginEntryPointPaths:
    def test_visualization_plugin_registered_via_real_entry_point_discovery(self) -> None:
        result = _discover_with_fixture(
            "_visualization_plugin_fixture",
            _VIZ_PLUGIN_SOURCE,
            "mineproductivity.visualization",
            "visualization",
        )
        assert result.is_ok
        assert "KPI_CARD.SitePackVizFixture" in REGISTRY

    def test_renderer_plugin_discoverable_independently_of_the_viz_fixture(self) -> None:
        result = _discover_with_fixture(
            "_visualization_renderer_fixture",
            _RENDERER_PLUGIN_SOURCE,
            "mineproductivity.visualization.renderers",
            "visualization.renderers",
        )
        assert result.is_ok
        assert "HTML.SitePackRendererFixture" in RENDERERS
        assert "HTML.SitePackRendererFixture" not in REGISTRY
