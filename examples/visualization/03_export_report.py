"""Exporting a multi-section ``Report`` (design spec §14, §18, §19):
``ReportBuilder`` composes ``RenderingPipeline`` once per section, and
an export is an ordinary ``pipeline.render`` call wrapped in an
``ExportResult`` — proving there is exactly one rendering code path for
both live and exported output (§33), never a second export renderer.

The concrete visualization and file renderer are example-local.

Run: python examples/visualization/03_export_report.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.kpis import KPIResult
from mineproductivity.visualization import (
    REGISTRY,
    RENDERERS,
    ExportRequest,
    ExportResult,
    PresentationModel,
    RenderedOutput,
    Renderer,
    RendererMetadata,
    RenderingPipeline,
    ReportBuilder,
    Visualization,
    VisualizationCategory,
    VisualizationContext,
    VisualizationMetadata,
    Widget,
    register,
    register_renderer,
)


@register
class KpiCard(Visualization):
    meta = VisualizationMetadata(
        code="KPI_CARD.Export",
        category=VisualizationCategory.KPI_CARD,
        description="A KPI headline card for export.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        wanted = widget.binding.get("kpi_code", "")
        matched = [r for r in context.kpi_results if r.code == wanted]
        if not matched:
            return PresentationModel(
                category=type(self).meta.category, title=wanted, warnings=("no evidence",)
            )
        return PresentationModel(
            category=type(self).meta.category,
            title=wanted,
            series={"value": matched[0].value},
            evidence_refs=(wanted,),
        )


@register_renderer
class FileRenderer(Renderer):
    """Deterministic file payload so the round-trip is exact (example-local)."""

    meta = RendererMetadata(code="FILE.Export", description="Renders to a downloadable payload.")

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(
            format="text",
            payload=f"{model.title}={model.series.get('value')}",
            warnings=model.warnings,
        )


def main() -> None:
    pipeline = RenderingPipeline(registry=REGISTRY, renderers=RENDERERS)
    context = VisualizationContext(
        kpi_results=(
            KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),
            KPIResult(code="UTIL.OEE", value=0.78, unit="ratio"),
        )
    )

    print("--- 1. A live render of one widget ---")
    tph_widget = Widget(
        code="tph", visualization_code="KPI_CARD.Export", binding={"kpi_code": "PROD.TPH"}
    )
    live = pipeline.render(tph_widget, context=context, renderer_code="FILE.Export")
    print(f"live payload: {live.payload!r}")

    print()
    print("--- 2. Compose the same widgets into a Report via ReportBuilder ---")
    report = (
        ReportBuilder(report_code="SHIFT.Handover", pipeline=pipeline)
        .with_section(tph_widget, context=context, renderer_code="FILE.Export")
        .with_section(
            Widget(
                code="oee", visualization_code="KPI_CARD.Export", binding={"kpi_code": "UTIL.OEE"}
            ),
            context=context,
            renderer_code="FILE.Export",
        )
        .build()
    )
    print(f"report {report.report_code!r}: {len(report.sections)} sections")
    for section in report.sections:
        print(f"  section payload: {section.payload!r}")

    print()
    print("--- 3. Export is the same code path, wrapped in an ExportResult (sec. 33) ---")
    request = ExportRequest(renderer_code="FILE.Export", report=report)
    exported = pipeline.render(tph_widget, context=context, renderer_code=request.renderer_code)
    result = ExportResult(
        format=exported.format, payload=exported.payload, exported_at=datetime.now(timezone.utc)
    )
    print(
        f"export payload matches live render: {result.payload == live.payload} ({result.payload!r})"
    )
    assert request.report is not None
    print(f"exported report section 0: {request.report.sections[0].payload!r}")


if __name__ == "__main__":
    main()
