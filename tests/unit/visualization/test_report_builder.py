"""Tests for mineproductivity.visualization.report_builder (design
spec §14): composition over duplication, warning propagation, and the
core.BaseBuilder contract."""

from __future__ import annotations

from pathlib import Path

from mineproductivity.core import BaseBuilder
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


@register
class _ReportKpiCard(Visualization):
    meta = VisualizationMetadata(
        code="KPI_CARD.ReportFixture",
        category=VisualizationCategory.KPI_CARD,
        description="A KPI headline card for report tests.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        wanted = widget.binding.get("kpi_code", "")
        matched = [result for result in context.kpi_results if result.code == wanted]
        if not matched:
            return PresentationModel(
                category=type(self).meta.category,
                title=wanted,
                warnings=(f"no KPIResult for {wanted!r} in context",),
            )
        return PresentationModel(
            category=type(self).meta.category,
            title=wanted,
            series={"value": matched[0].value},
        )


@register_renderer
class _ReportRenderer(Renderer):
    meta = RendererMetadata(code="TEXT.ReportFixture", description="Renders a model to plain text.")

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(
            format="text",
            payload=f"{model.title}={model.series.get('value')}",
            warnings=model.warnings,
        )


class _RecordingPipeline(RenderingPipeline):
    def __init__(self) -> None:
        super().__init__(registry=REGISTRY, renderers=RENDERERS)
        self.calls: list[str] = []

    def render(
        self, widget: Widget, *, context: VisualizationContext, renderer_code: str
    ) -> RenderedOutput:
        self.calls.append(widget.code)
        return super().render(widget, context=context, renderer_code=renderer_code)


def _widget(code: str) -> Widget:
    return Widget(
        code=code,
        visualization_code="KPI_CARD.ReportFixture",
        binding={"kpi_code": "PROD.TPH"},
    )


def _context() -> VisualizationContext:
    return VisualizationContext(kpi_results=(KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),))


class TestComposition:
    def test_every_section_is_an_actual_pipeline_render_call(self) -> None:
        """Design spec §14: never a re-implementation of the
        pipeline's dispatch."""
        pipeline = _RecordingPipeline()
        report = (
            ReportBuilder(report_code="SHIFT.Handover", pipeline=pipeline)
            .with_section(_widget("s1"), context=_context(), renderer_code="TEXT.ReportFixture")
            .with_section(_widget("s2"), context=_context(), renderer_code="TEXT.ReportFixture")
            .build()
        )
        assert pipeline.calls == ["s1", "s2"]
        assert isinstance(report, Report)
        assert [section.payload for section in report.sections] == [
            "PROD.TPH=1212.1",
            "PROD.TPH=1212.1",
        ]

    def test_no_duplicated_dispatch_logic_in_the_source(self) -> None:
        import mineproductivity.visualization.report_builder as report_builder_module

        source = Path(report_builder_module.__file__).read_text(encoding="utf-8")
        assert "self._pipeline.render(" in source
        assert "REGISTRY" not in source  # dispatch stays the pipeline's job


class TestWarningPropagation:
    def test_a_section_warning_survives_onto_the_final_report(self) -> None:
        """Design spec §14, §30: preserved, never silently dropped."""
        report = (
            ReportBuilder(
                report_code="SHIFT.Handover",
                pipeline=RenderingPipeline(registry=REGISTRY, renderers=RENDERERS),
            )
            .with_section(
                _widget("s1"),
                context=VisualizationContext(),  # evidence deliberately missing
                renderer_code="TEXT.ReportFixture",
            )
            .build()
        )
        assert report.warnings == ("no KPIResult for 'PROD.TPH' in context",)
        assert report.sections[0].warnings == report.warnings


class TestBuilderContract:
    def test_is_a_concrete_core_base_builder_subclass(self) -> None:
        assert issubclass(ReportBuilder, BaseBuilder)
        assert "build_result" not in ReportBuilder.__dict__

    def test_build_result_ok(self) -> None:
        builder = ReportBuilder(
            report_code="R",
            pipeline=RenderingPipeline(registry=REGISTRY, renderers=RENDERERS),
        )
        assert builder.build_result().is_ok

    def test_reset_makes_the_builder_reusable(self) -> None:
        builder = ReportBuilder(
            report_code="R",
            pipeline=RenderingPipeline(registry=REGISTRY, renderers=RENDERERS),
        ).with_section(_widget("s1"), context=_context(), renderer_code="TEXT.ReportFixture")
        first = builder.build()
        second = builder.reset().build()
        assert len(first.sections) == 1
        assert second.sections == ()
        assert second.report_code == "R"  # construction-time identity survives reset
