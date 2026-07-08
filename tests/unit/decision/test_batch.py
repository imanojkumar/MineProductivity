"""Tests for mineproductivity.decision.batch."""

from __future__ import annotations

from typing import ClassVar

from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.audit import DecisionAuditTrail
from mineproductivity.decision.batch import BatchDecisionRunner
from mineproductivity.decision.exceptions import DecisionValidationError
from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
from mineproductivity.decision.pipeline import DecisionPipeline, ModelStage
from mineproductivity.decision.result import DecisionResult
from mineproductivity.kpis import KPIResult


class _Model(DecisionModel):
    meta: ClassVar[DecisionMetadata] = DecisionMetadata(
        code="STRATEGY.BatchDoctest", category=DecisionCategory.STRATEGY, description="x"
    )

    def _decide(self, context: DecisionContext) -> DecisionResult:
        return DecisionResult(model_code="TEST")


def _context() -> DecisionContext:
    return DecisionContext(
        kpi_results=(KPIResult(code="PROD.TPH", value=1.0, unit="t/h"),),
        analytics_results=(),
        scope={"pit": "north"},
    )


class TestBatchDecisionRunnerRun:
    def test_delegates_to_pipeline_run(self) -> None:
        pipeline = DecisionPipeline(stages=(ModelStage(_Model()),))
        runner = BatchDecisionRunner(pipeline=pipeline)
        result = runner.run(_context())
        assert result.is_ok
        assert result.unwrap().model_code == "TEST"

    def test_propagates_pipeline_error(self) -> None:
        pipeline = DecisionPipeline(stages=())
        runner = BatchDecisionRunner(pipeline=pipeline)
        result = runner.run(_context())
        assert result.is_err
        assert isinstance(result.error, DecisionValidationError)

    def test_repr_includes_pipeline(self) -> None:
        pipeline = DecisionPipeline(stages=())
        runner = BatchDecisionRunner(pipeline=pipeline)
        assert "BatchDecisionRunner" in repr(runner)


class TestBatchDecisionRunnerAuditTrail:
    def test_no_audit_trail_is_a_valid_default(self) -> None:
        pipeline = DecisionPipeline(stages=(ModelStage(_Model()),))
        runner = BatchDecisionRunner(pipeline=pipeline)
        assert runner.run(_context()).is_ok

    def test_successful_run_is_recorded(self) -> None:
        pipeline = DecisionPipeline(stages=(ModelStage(_Model()),))
        trail = DecisionAuditTrail()
        runner = BatchDecisionRunner(pipeline=pipeline, audit_trail=trail)
        runner.run(_context())
        entries = trail.query()
        assert len(entries) == 1
        assert entries[0].result.model_code == "TEST"

    def test_recorded_entry_carries_context_scope(self) -> None:
        pipeline = DecisionPipeline(stages=(ModelStage(_Model()),))
        trail = DecisionAuditTrail()
        runner = BatchDecisionRunner(pipeline=pipeline, audit_trail=trail)
        runner.run(_context())
        assert dict(trail.query()[0].context_scope) == {"pit": "north"}

    def test_failed_run_is_not_recorded(self) -> None:
        pipeline = DecisionPipeline(stages=())
        trail = DecisionAuditTrail()
        runner = BatchDecisionRunner(pipeline=pipeline, audit_trail=trail)
        runner.run(_context())
        assert trail.query() == ()
