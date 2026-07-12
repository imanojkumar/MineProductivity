"""Tests for mineproductivity.visualization.renderer (design spec
§16): interface-only ABC contract plus the RendererMetadata/
RenderedOutput value objects."""

from __future__ import annotations

import inspect

import pytest

import mineproductivity.visualization.renderer as renderer_module
from mineproductivity.visualization.exceptions import VisualizationValidationError
from mineproductivity.visualization.renderer import (
    RenderedOutput,
    Renderer,
    RendererMetadata,
)


class TestRendererMetadata:
    def test_name_defaults_to_code_and_version_defaults(self) -> None:
        meta = RendererMetadata(code="HTML.Standard", description="Renders to HTML.")
        assert meta.name == "HTML.Standard"
        assert meta.version == "1.0.0"

    def test_empty_code_raises(self) -> None:
        with pytest.raises(VisualizationValidationError, match="code"):
            RendererMetadata(code=" ", description="x")


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            Renderer()  # type: ignore[abstract]

    def test_render_is_the_one_abstract_method(self) -> None:
        assert Renderer.__abstractmethods__ == frozenset({"render"})

    def test_module_defines_no_concrete_subclass(self) -> None:
        """Design spec §33's interface-purity proof, module-local."""
        for _, obj in inspect.getmembers(renderer_module, inspect.isclass):
            if issubclass(obj, Renderer):
                assert inspect.isabstract(obj)


class TestRenderedOutput:
    def test_defaults(self) -> None:
        output = RenderedOutput(format="html", payload="<div/>")
        assert output.warnings == ()

    def test_value_equality(self) -> None:
        assert RenderedOutput(format="html", payload="x") == RenderedOutput(
            format="html", payload="x"
        )
        assert RenderedOutput(format="html", payload="x") != RenderedOutput(
            format="pdf", payload="x"
        )
