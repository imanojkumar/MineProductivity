"""Tests for mineproductivity.visualization.export (design spec §18):
shapes, the no-separate-mechanism rule, and the §19/§33 export
round-trip proof."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from mineproductivity.kpis import KPIResult
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
from mineproductivity.visualization.export import ExportRequest, ExportResult
from mineproductivity.visualization.pipeline import RenderingPipeline
from mineproductivity.visualization.presentation import PresentationModel
from mineproductivity.visualization.renderer import (
    RenderedOutput,
    Renderer,
    RendererMetadata,
)
from mineproductivity.visualization.report import Report
from mineproductivity.visualization.report_builder import ReportBuilder
from mineproductivity.visualization.widget import Widget

_WHEN = datetime(2026, 7, 6, tzinfo=timezone.utc)


@register
class _ExportKpiCard(Visualization):
    meta = VisualizationMetadata(
        code="KPI_CARD.ExportFixture",
        category=VisualizationCategory.KPI_CARD,
        description="A KPI headline card for export tests.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        wanted = widget.binding.get("kpi_code", "")
        matched = [result for result in context.kpi_results if result.code == wanted]
        if not matched:
            return PresentationModel(
                category=type(self).meta.category,
                title=wanted or widget.code,
                warnings=(f"no KPIResult for {wanted!r} in context",),
            )
        return PresentationModel(
            category=type(self).meta.category,
            title=wanted,
            series={"value": matched[0].value},
            evidence_refs=(wanted,),
        )


@register_renderer
class _ExportFileRenderer(Renderer):
    """A file-producing fixture renderer -- deterministic text
    payload, so the round-trip comparison is exact."""

    meta = RendererMetadata(
        code="FILE.ExportFixture", description="Renders to a downloadable text payload."
    )

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(
            format="text",
            payload=f"{model.title}={model.series.get('value')}",
            warnings=model.warnings,
        )


def _pipeline() -> RenderingPipeline:
    return RenderingPipeline(registry=REGISTRY, renderers=RENDERERS)


def _context() -> VisualizationContext:
    return VisualizationContext(kpi_results=(KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),))


def _widget() -> Widget:
    return Widget(
        code="tph_card",
        visualization_code="KPI_CARD.ExportFixture",
        binding={"kpi_code": "PROD.TPH"},
    )


class TestShapes:
    def test_export_request_defaults(self) -> None:
        request = ExportRequest(renderer_code="FILE.ExportFixture")
        assert request.dashboard_id is None
        assert request.report is None

    def test_export_result_fields(self) -> None:
        result = ExportResult(format="text", payload="x", exported_at=_WHEN)
        assert result.format == "text"

    def test_export_shares_no_code_with_connectors(self) -> None:
        """Design spec §18, §32: opposite-direction concerns."""
        import mineproductivity.visualization.export as export_module

        source = Path(export_module.__file__).read_text(encoding="utf-8")
        import ast

        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "connectors" not in node.module


class TestExportRoundTrip:
    def test_export_payload_matches_the_live_render_payload(self) -> None:
        """Design spec §18, §19, §33: exactly one rendering code path
        -- an export is an ordinary pipeline.render call wrapped in an
        ExportResult."""
        pipeline = _pipeline()
        context = _context()
        widget = _widget()

        live = pipeline.render(widget, context=context, renderer_code="FILE.ExportFixture")

        request = ExportRequest(renderer_code="FILE.ExportFixture")
        exported_output = pipeline.render(
            widget, context=context, renderer_code=request.renderer_code
        )
        export_result = ExportResult(
            format=exported_output.format,
            payload=exported_output.payload,
            exported_at=datetime.now(timezone.utc),
        )

        assert export_result.payload == live.payload == "PROD.TPH=1212.1"
        assert export_result.format == live.format

    def test_report_export_carries_the_report_by_value(self) -> None:
        """Design spec §19: the same widgets composed into an exported
        Report via ReportBuilder."""
        pipeline = _pipeline()
        report = (
            ReportBuilder(report_code=f"SHIFT.Handover.{uuid.uuid4().hex[:8]}", pipeline=pipeline)
            .with_section(_widget(), context=_context(), renderer_code="FILE.ExportFixture")
            .build()
        )
        request = ExportRequest(renderer_code="FILE.ExportFixture", report=report)
        assert isinstance(request.report, Report)
        assert request.report.sections[0].payload == "PROD.TPH=1212.1"
