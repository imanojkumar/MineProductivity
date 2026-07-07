"""Tests for mineproductivity.analytics.batch."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar

from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.batch import BatchAnalyticsRunner
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.pipeline import AnalyticsPipeline, ModelStage
from mineproductivity.analytics.result import AnalyticsResult
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

from .conftest import assert_no_import_from

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _EchoModel(AnalyticsModel):
    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="TREND.Echo", category=AnalyticsCategory.TREND, description="x", min_observations=0
    )

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        return AnalyticsResult(model_code=self.meta.code, warnings=(f"n={len(series)}",))


def _context() -> AnalyticsContext:
    return AnalyticsContext(event_store=_InMemoryEventStore())


def _series() -> TimeSeries:
    return TimeSeries(points=(TimeSeriesPoint(timestamp=DAY_1, value=1.0),))


class TestBatchAnalyticsRunnerIsAThinWrapper:
    def test_run_delegates_verbatim_to_analyticspipeline_run(self) -> None:
        """The exact same series/context, run through the pipeline
        directly vs. through the runner, must produce an equivalent
        result -- proof no new orchestration logic exists. Compares
        ``model_code``/``warnings`` rather than full dataclass equality:
        ``AnalyticsResult.computed_at`` defaults to ``datetime.now()`` at
        construction time, so two independently-computed results (one
        per ``_analyze()`` call) are never bit-for-bit equal by design,
        even when produced by the exact same code path."""
        pipeline = AnalyticsPipeline(stages=(ModelStage(_EchoModel()),))
        context = _context()
        series = _series()

        direct = pipeline.run(series, context=context)
        via_runner = BatchAnalyticsRunner(pipeline=pipeline, context=context).run(series)

        assert direct.is_ok
        assert via_runner.is_ok
        assert direct.unwrap().model_code == via_runner.unwrap().model_code
        assert direct.unwrap().warnings == via_runner.unwrap().warnings

    def test_run_returns_a_result_wrapping_analyticsresult(self) -> None:
        pipeline = AnalyticsPipeline(stages=(ModelStage(_EchoModel()),))
        runner = BatchAnalyticsRunner(pipeline=pipeline, context=_context())
        result = runner.run(_series())
        assert result.is_ok
        assert isinstance(result.unwrap(), AnalyticsResult)
        assert result.unwrap().model_code == "TREND.Echo"

    def test_pipeline_errors_propagate_unchanged(self) -> None:
        """An empty pipeline is a configuration error AnalyticsPipeline.run
        itself detects (§9) -- BatchAnalyticsRunner must not swallow or
        alter it."""
        pipeline = AnalyticsPipeline(stages=())
        context = _context()
        series = _series()

        direct = pipeline.run(series, context=context)
        via_runner = BatchAnalyticsRunner(pipeline=pipeline, context=context).run(series)

        assert direct.is_err
        assert via_runner.is_err
        assert type(direct.error) is type(via_runner.error)
        assert str(direct.error) == str(via_runner.error)

    def test_bounded_series_can_be_empty(self) -> None:
        """A 'bounded' input per §28 may legitimately have zero points --
        the generic min_observations gate handles this, not a special
        case in the runner itself."""
        pipeline = AnalyticsPipeline(stages=(ModelStage(_EchoModel()),))
        runner = BatchAnalyticsRunner(pipeline=pipeline, context=_context())
        result = runner.run(TimeSeries(points=()))
        assert result.is_ok
        assert result.unwrap().warnings == ("n=0",)


class TestBatchAnalyticsRunnerMetadata:
    def test_repr_includes_pipeline_and_context(self) -> None:
        pipeline = AnalyticsPipeline(stages=(ModelStage(_EchoModel()),))
        context = _context()
        runner = BatchAnalyticsRunner(pipeline=pipeline, context=context)
        text = repr(runner)
        assert "AnalyticsPipeline" in text
        assert "AnalyticsContext" in text


class TestPublicApiValidation:
    def test_batchanalyticsrunner_is_exported(self) -> None:
        import mineproductivity.analytics as analytics

        assert "BatchAnalyticsRunner" in analytics.__all__
        assert analytics.BatchAnalyticsRunner is BatchAnalyticsRunner

    def test_batch_module_public_api_matches_spec_exactly(self) -> None:
        import mineproductivity.analytics.batch as batch_module

        assert batch_module.__all__ == ["BatchAnalyticsRunner"]

    def test_no_new_result_type_introduced(self) -> None:
        """BatchAnalyticsRunner.run() returns Result[AnalyticsResult] --
        both types already existed (core.Result, result.AnalyticsResult);
        neither is redefined in this module."""
        import inspect

        import mineproductivity.analytics.batch as batch_module

        classes_defined_here = [
            name
            for name, member in inspect.getmembers(batch_module, inspect.isclass)
            if member.__module__ == batch_module.__name__
        ]
        assert classes_defined_here == ["BatchAnalyticsRunner"]

    def test_does_not_import_business_logic_modules(self) -> None:
        """Execution modules coordinate existing components rather than
        reimplement statistics/rolling/trend/baseline/benchmarking/
        quality logic -- mechanically verified, not merely asserted."""
        import mineproductivity.analytics.batch as batch_module

        assert_no_import_from(
            batch_module,
            "statistics",
            "rolling",
            "trend",
            "baseline",
            "benchmarking",
            "quality",
        )
