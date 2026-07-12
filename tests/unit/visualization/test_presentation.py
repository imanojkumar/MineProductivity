"""Tests for mineproductivity.visualization.presentation (design spec
§9)."""

from __future__ import annotations

from typing import Any

import pytest

from mineproductivity.core.serialization import to_dict
from mineproductivity.visualization.abstractions import VisualizationCategory
from mineproductivity.visualization.presentation import PresentationModel


def _model(**overrides: object) -> PresentationModel:
    kwargs: dict[str, object] = {
        "category": VisualizationCategory.KPI_CARD,
        "title": "Tonnes per hour",
    }
    kwargs.update(overrides)
    return PresentationModel(**kwargs)  # type: ignore[arg-type]


class TestPresentationModel:
    def test_defaults(self) -> None:
        model = _model()
        assert dict(model.series) == {}
        assert model.evidence_refs == ()
        assert model.warnings == ()

    def test_series_is_frozen_and_copied(self) -> None:
        source: dict[str, Any] = {"value": 1212.1}
        model = _model(series=source)
        source["value"] = 0.0
        assert model.series["value"] == 1212.1
        with pytest.raises(TypeError):
            model.series["value"] = 0.0  # type: ignore[index]

    def test_carries_no_rendered_bytes_html_or_pixels_field(self) -> None:
        """Design spec §9: rendering is exclusively the Renderer's
        responsibility."""
        import dataclasses

        field_names = {field.name for field in dataclasses.fields(PresentationModel)}
        assert field_names == {"category", "title", "series", "evidence_refs", "warnings"}

    def test_evidence_refs_carry_lower_package_shaped_references(self) -> None:
        model = _model(evidence_refs=("PROD.TPH", "OPT-2026-041"))
        assert model.evidence_refs == ("PROD.TPH", "OPT-2026-041")

    def test_serializes_via_core_serialization(self) -> None:
        serialized = to_dict(_model(series={"value": 1.0}))
        assert serialized["title"] == "Tonnes per hour"
        assert serialized["series"] == {"value": 1.0}
