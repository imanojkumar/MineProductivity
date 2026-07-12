"""Tests for mineproductivity.visualization.layout (design spec §10)."""

from __future__ import annotations

from pathlib import Path

import pytest

import mineproductivity.visualization.layout as layout_module
from mineproductivity.visualization.layout import Layout


class TestLayout:
    def test_carries_opaque_renderer_interpreted_slots(self) -> None:
        layout = Layout(code="handover_grid", slots={"tph_card": "row=1;col=1"})
        assert layout.slots["tph_card"] == "row=1;col=1"

    def test_empty_slots_raises(self) -> None:
        from mineproductivity.visualization.exceptions import VisualizationValidationError

        with pytest.raises(VisualizationValidationError, match="slots"):
            Layout(code="empty_grid")

    def test_slots_are_frozen_and_copied(self) -> None:
        slots = {"tph_card": "row=1;col=1"}
        layout = Layout(code="grid", slots=slots)
        slots["tph_card"] = "row=9;col=9"
        assert layout.slots["tph_card"] == "row=1;col=1"

    def test_this_package_never_parses_slots(self) -> None:
        """Design spec §10: stored and handed to a Renderer, never
        interpreted by this package's own code."""
        source = Path(layout_module.__file__).read_text(encoding="utf-8")
        for parsing_marker in (".split(", "re.compile", "eval(", "exec("):
            assert parsing_marker not in source
