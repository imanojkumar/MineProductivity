"""``BatchDecisionRunner``: runs one ``DecisionPipeline`` once over a
bounded, already-assembled ``DecisionContext`` -- the "normal,"
scheduled-report mode, in contrast to ``realtime.RealTimeDecisionSession``'s
live, event-driven mode (design spec §25, §26).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
The one thing this module needs -- "run one pipeline once over a
bounded input and produce a single result" -- is exactly what
``DecisionPipeline.run()`` (§9) already does. No new orchestration logic
is introduced: ``BatchDecisionRunner`` is a thin, named wrapper that
delegates ``run()`` verbatim, exactly mirroring
``analytics.BatchAnalyticsRunner``'s identical relationship to
``AnalyticsPipeline`` (spec 06 §28) one layer down. It exists as its own
class (rather than callers invoking ``DecisionPipeline.run`` directly)
purely so "batch" and "real-time" are two clearly-named, symmetrical
entry points in the public API (§7), matching how a reader of this
specification's table of contents (§25-§26) expects to find them -- not
because any new behavior is required.

The design spec's own §26 pseudocode constructor takes only
``pipeline``; an optional ``audit_trail: DecisionAuditTrail | None =
None`` keyword parameter is added here as the smallest compatible
extension, because §33's own anti-pattern list explicitly forbids
"Bypassing ``DecisionAuditTrail`` for any ``DecisionPipeline`` run whose
output could plausibly inform a real operational action" -- a rule this
class's own ``run()`` has no other way to honor, since a caller
constructing a ``BatchDecisionRunner`` from the spec's bare
``pipeline``-only pseudocode is still a valid, still-supported call
(the parameter is optional, not required); recording is simply skipped
when no trail is supplied, mirroring
``realtime.RealTimeDecisionSession``'s identical, disclosed extension.
"""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.core import Result

from mineproductivity.decision.abstractions import DecisionContext
from mineproductivity.decision.audit import DecisionAuditEntry, DecisionAuditTrail
from mineproductivity.decision.pipeline import DecisionPipeline
from mineproductivity.decision.result import DecisionResult

__all__ = ["BatchDecisionRunner"]


class BatchDecisionRunner:
    """Runs one ``DecisionPipeline`` once over a bounded,
    already-assembled ``DecisionContext`` -- the 'normal,' scheduled-
    report mode, in contrast to ``RealTimeDecisionSession``'s live,
    event-driven mode (§25). A thin, named wrapper over
    ``DecisionPipeline.run`` (§9), exactly mirroring
    ``analytics.BatchAnalyticsRunner``'s relationship to
    ``AnalyticsPipeline`` (spec 06 §28).

    Examples
    --------
    >>> from typing import ClassVar
    >>> from mineproductivity.decision.abstractions import DecisionModel
    >>> from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
    >>> from mineproductivity.decision.pipeline import ModelStage
    >>> from mineproductivity.kpis import KPIResult
    >>> class _Model(DecisionModel):
    ...     meta: ClassVar[DecisionMetadata] = DecisionMetadata(
    ...         code="STRATEGY.Doctest", category=DecisionCategory.STRATEGY, description="x",
    ...     )
    ...     def _decide(self, context):
    ...         return DecisionResult(model_code="TEST")
    >>> pipeline = DecisionPipeline(stages=(ModelStage(_Model()),))
    >>> runner = BatchDecisionRunner(pipeline=pipeline)
    >>> ctx = DecisionContext(kpi_results=(KPIResult(code="PROD.TPH", value=1.0, unit="t/h"),),
    ...                        analytics_results=(), scope={"pit": "north"})
    >>> runner.run(ctx).unwrap().model_code
    'TEST'
    """

    def __init__(
        self, *, pipeline: DecisionPipeline, audit_trail: DecisionAuditTrail | None = None
    ) -> None:
        self._pipeline = pipeline
        self._audit_trail = audit_trail

    def run(self, context: DecisionContext) -> Result[DecisionResult]:
        result = self._pipeline.run(context)
        if result.is_ok and self._audit_trail is not None:
            self._audit_trail.record(
                DecisionAuditEntry(
                    recorded_at=datetime.now(timezone.utc),
                    result=result.unwrap(),
                    context_scope=context.scope,
                    source_event_ids=(),
                )
            )
        return result

    def __repr__(self) -> str:
        return f"{type(self).__name__}(pipeline={self._pipeline!r})"
