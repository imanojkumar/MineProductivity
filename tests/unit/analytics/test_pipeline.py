"""Tests for mineproductivity.analytics.pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar

import pytest

from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.pipeline import AnalyticsPipeline, ModelStage, PipelineStage
from mineproductivity.analytics.result import AnalyticsResult
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
DAY_2 = datetime(2026, 1, 2, tzinfo=timezone.utc)


class _StubModel(AnalyticsModel):
    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="TREND.Stub",
        category=AnalyticsCategory.TREND,
        description="test-only",
        min_observations=0,
    )

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        return AnalyticsResult(model_code=self.meta.code)


class _PassThroughStage(PipelineStage):
    """A minimal non-terminal stage: returns its input series unchanged."""

    def process(self, series: TimeSeries, *, context: AnalyticsContext) -> TimeSeries:
        return series


def _context() -> AnalyticsContext:
    return AnalyticsContext(event_store=_InMemoryEventStore())


def _series() -> TimeSeries:
    return TimeSeries(
        points=(
            TimeSeriesPoint(timestamp=DAY_1, value=1.0),
            TimeSeriesPoint(timestamp=DAY_2, value=2.0),
        )
    )


class TestPipelineStage:
    def test_cannot_instantiate_abstract_base_directly(self) -> None:
        with pytest.raises(TypeError):
            PipelineStage()  # type: ignore[abstract]


class TestModelStage:
    def test_process_delegates_to_the_wrapped_models_analyze(self) -> None:
        stage = ModelStage(_StubModel())
        result = stage.process(_series(), context=_context())
        assert isinstance(result, AnalyticsResult)
        assert result.model_code == "TREND.Stub"

    def test_repr_includes_the_wrapped_model(self) -> None:
        stage = ModelStage(_StubModel())
        assert "_StubModel" in repr(stage)


class TestAnalyticsPipelineRun:
    def test_single_model_stage_yields_ok_result(self) -> None:
        pipeline = AnalyticsPipeline(stages=(ModelStage(_StubModel()),))
        outcome = pipeline.run(_series(), context=_context())
        assert outcome.is_ok
        assert outcome.unwrap().model_code == "TREND.Stub"

    def test_pass_through_stage_then_model_stage(self) -> None:
        pipeline = AnalyticsPipeline(stages=(_PassThroughStage(), ModelStage(_StubModel())))
        outcome = pipeline.run(_series(), context=_context())
        assert outcome.is_ok
        assert outcome.unwrap().model_code == "TREND.Stub"

    def test_empty_pipeline_returns_err(self) -> None:
        pipeline = AnalyticsPipeline(stages=())
        outcome = pipeline.run(_series(), context=_context())
        assert outcome.is_err
        assert isinstance(outcome.error, AnalyticsValidationError)

    def test_non_terminal_stage_only_returns_err(self) -> None:
        """A pipeline whose last stage never yields an ``AnalyticsResult``
        (only a ``TimeSeries``-returning stage) must fail, per the design
        spec's own explicit rule."""
        pipeline = AnalyticsPipeline(stages=(_PassThroughStage(),))
        outcome = pipeline.run(_series(), context=_context())
        assert outcome.is_err
        assert isinstance(outcome.error, AnalyticsValidationError)

    def test_model_stage_before_the_end_returns_err(self) -> None:
        """A ``ModelStage`` placed before the pipeline's end -- yielding
        an ``AnalyticsResult`` too early -- is a configuration error, not
        something the next stage should be forced to (mis)interpret as a
        ``TimeSeries``."""
        pipeline = AnalyticsPipeline(stages=(ModelStage(_StubModel()), _PassThroughStage()))
        outcome = pipeline.run(_series(), context=_context())
        assert outcome.is_err
        assert isinstance(outcome.error, AnalyticsValidationError)

    def test_stages_run_in_declared_order(self) -> None:
        calls: list[str] = []

        class _RecordingStage(PipelineStage):
            def __init__(self, name: str) -> None:
                self._name = name

            def process(self, series: TimeSeries, *, context: AnalyticsContext) -> TimeSeries:
                calls.append(self._name)
                return series

        pipeline = AnalyticsPipeline(
            stages=(_RecordingStage("first"), _RecordingStage("second"), ModelStage(_StubModel()))
        )
        pipeline.run(_series(), context=_context())
        assert calls == ["first", "second"]

    def test_repr_includes_stages(self) -> None:
        pipeline = AnalyticsPipeline(stages=(ModelStage(_StubModel()),))
        assert "AnalyticsPipeline" in repr(pipeline)

    def test_an_exception_raised_by_a_stage_propagates_unwrapped(self) -> None:
        """``run`` only ``Result``-wraps the one documented validation
        failure (last stage not yielding an ``AnalyticsResult``) --
        mirroring ``KPIEngine.execute``'s own precedent of not
        blanket-catching arbitrary exceptions from collaborators."""

        class _BrokenStage(PipelineStage):
            def process(self, series: TimeSeries, *, context: AnalyticsContext) -> TimeSeries:
                raise ValueError("boom")

        pipeline = AnalyticsPipeline(stages=(_BrokenStage(), ModelStage(_StubModel())))
        with pytest.raises(ValueError, match="boom"):
            pipeline.run(_series(), context=_context())
