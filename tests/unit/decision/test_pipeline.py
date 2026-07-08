"""Tests for mineproductivity.decision.pipeline."""

from __future__ import annotations

from typing import ClassVar

import pytest

from mineproductivity.kpis import KPIResult

from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.exceptions import DecisionValidationError
from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
from mineproductivity.decision.pipeline import DecisionPipeline, ModelStage, PipelineStage
from mineproductivity.decision.result import DecisionResult


class _StubModel(DecisionModel):
    meta: ClassVar[DecisionMetadata] = DecisionMetadata(
        code="STRATEGY.Stub", category=DecisionCategory.STRATEGY, description="test-only"
    )

    def _decide(self, context: DecisionContext) -> DecisionResult:
        return DecisionResult(model_code=self.meta.code)


class _PassThroughStage(PipelineStage):
    """A minimal non-terminal stage: returns its input context unchanged."""

    def process(self, context: DecisionContext) -> DecisionContext:
        return context


def _context() -> DecisionContext:
    return DecisionContext(
        kpi_results=(KPIResult(code="PROD.TPH", value=1.0, unit="t/h"),),
        analytics_results=(),
        scope={},
    )


class TestPipelineStage:
    def test_cannot_instantiate_abstract_base_directly(self) -> None:
        with pytest.raises(TypeError):
            PipelineStage()  # type: ignore[abstract]


class TestModelStage:
    def test_process_delegates_to_the_wrapped_models_decide(self) -> None:
        stage = ModelStage(_StubModel())
        result = stage.process(_context())
        assert isinstance(result, DecisionResult)
        assert result.model_code == "STRATEGY.Stub"

    def test_repr_includes_the_wrapped_model(self) -> None:
        stage = ModelStage(_StubModel())
        assert "_StubModel" in repr(stage)


class TestDecisionPipelineRun:
    def test_single_model_stage_yields_ok_result(self) -> None:
        pipeline = DecisionPipeline(stages=(ModelStage(_StubModel()),))
        outcome = pipeline.run(_context())
        assert outcome.is_ok
        assert outcome.unwrap().model_code == "STRATEGY.Stub"

    def test_pass_through_stage_then_model_stage(self) -> None:
        pipeline = DecisionPipeline(stages=(_PassThroughStage(), ModelStage(_StubModel())))
        outcome = pipeline.run(_context())
        assert outcome.is_ok
        assert outcome.unwrap().model_code == "STRATEGY.Stub"

    def test_empty_pipeline_returns_err(self) -> None:
        pipeline = DecisionPipeline(stages=())
        outcome = pipeline.run(_context())
        assert outcome.is_err
        assert isinstance(outcome.error, DecisionValidationError)

    def test_non_terminal_stage_only_returns_err(self) -> None:
        """A pipeline whose last stage never yields a ``DecisionResult``
        (only a ``DecisionContext``-returning stage) must fail, per the
        design spec's own explicit rule."""
        pipeline = DecisionPipeline(stages=(_PassThroughStage(),))
        outcome = pipeline.run(_context())
        assert outcome.is_err
        assert isinstance(outcome.error, DecisionValidationError)

    def test_model_stage_before_the_end_returns_err(self) -> None:
        """A ``ModelStage`` placed before the pipeline's end -- yielding a
        ``DecisionResult`` too early -- is a configuration error, not
        something the next stage should be forced to (mis)interpret as a
        ``DecisionContext``."""
        pipeline = DecisionPipeline(stages=(ModelStage(_StubModel()), _PassThroughStage()))
        outcome = pipeline.run(_context())
        assert outcome.is_err
        assert isinstance(outcome.error, DecisionValidationError)

    def test_stages_run_in_declared_order(self) -> None:
        calls: list[str] = []

        class _RecordingStage(PipelineStage):
            def __init__(self, name: str) -> None:
                self._name = name

            def process(self, context: DecisionContext) -> DecisionContext:
                calls.append(self._name)
                return context

        pipeline = DecisionPipeline(
            stages=(_RecordingStage("first"), _RecordingStage("second"), ModelStage(_StubModel()))
        )
        pipeline.run(_context())
        assert calls == ["first", "second"]

    def test_repr_includes_stages(self) -> None:
        pipeline = DecisionPipeline(stages=(ModelStage(_StubModel()),))
        assert "DecisionPipeline" in repr(pipeline)

    def test_an_exception_raised_by_a_stage_propagates_unwrapped(self) -> None:
        """``run`` only ``Result``-wraps the one documented validation
        failure (last stage not yielding a ``DecisionResult``) --
        mirroring ``analytics.AnalyticsPipeline.run``'s own precedent of
        not blanket-catching arbitrary exceptions from collaborators."""

        class _BrokenStage(PipelineStage):
            def process(self, context: DecisionContext) -> DecisionContext:
                raise ValueError("boom")

        pipeline = DecisionPipeline(stages=(_BrokenStage(), ModelStage(_StubModel())))
        with pytest.raises(ValueError, match="boom"):
            pipeline.run(_context())
