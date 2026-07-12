"""Tests for mineproductivity.agents.audit (design spec §21, §32)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from mineproductivity.agents.audit import AgentAuditEntry, AgentAuditTrail
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.tool import ToolInvocation
from mineproductivity.core.serialization import to_dict
from mineproductivity.decision import Explanation

_WHEN = datetime(2026, 7, 1, 6, 0, tzinfo=timezone.utc)


def _entry(agent_code: str = "FLEET.AuditFixture", **scope: str) -> AgentAuditEntry:
    return AgentAuditEntry(
        recorded_at=_WHEN,
        result=AgentResult(task_id="TASK-1"),
        agent_code=agent_code,
        scope=scope or {"pit": "north"},
    )


class TestRecordAndQuery:
    def test_record_appends_and_query_returns_everything(self) -> None:
        trail = AgentAuditTrail()
        trail.record(_entry())
        trail.record(_entry(pit="south"))
        assert len(trail.query()) == 2

    def test_scope_filtering(self) -> None:
        trail = AgentAuditTrail()
        trail.record(_entry(pit="north"))
        trail.record(_entry(pit="south"))
        matched = trail.query(scope={"pit": "north"})
        assert len(matched) == 1
        assert matched[0].scope["pit"] == "north"
        assert trail.query(scope={"pit": "east"}) == ()

    def test_repr(self) -> None:
        trail = AgentAuditTrail()
        trail.record(_entry())
        assert "entries=1" in repr(trail)


class TestVerbatimPreservation:
    def test_explanation_and_tool_invocations_are_never_summarized(self) -> None:
        """Design spec §21: an agent's audit record is never a
        summary, always the full, structured outcome."""
        explanation = Explanation(premises=("OEE below 0.65",), evidence_refs=("UTIL.OEE",))
        invocation = ToolInvocation(
            tool_code="TOOL.DispatchQuery",
            arguments={"pit": "north"},
            result={"trucks": 12},
            invoked_at=_WHEN,
        )
        result = AgentResult(
            task_id="TASK-1", explanation=explanation, tool_invocations=(invocation,)
        )
        trail = AgentAuditTrail()
        trail.record(
            AgentAuditEntry(
                recorded_at=_WHEN, result=result, agent_code="FLEET.AuditFixture", scope={}
            )
        )
        recorded = trail.query()[0]
        assert recorded.result is result
        assert recorded.result.explanation is explanation
        assert recorded.result.tool_invocations == (invocation,)


class TestConcurrency:
    def test_concurrent_records_serialize_with_no_lost_entry(self) -> None:
        """Design spec §32: record() serializes concurrent appends
        internally; no entry is lost under concurrent load."""
        trail = AgentAuditTrail()
        per_thread, threads = 50, 8

        def _record_many(thread_index: int) -> None:
            for i in range(per_thread):
                trail.record(_entry(agent_code=f"FLEET.Concurrent{thread_index}", n=str(i)))

        with ThreadPoolExecutor(max_workers=threads) as pool:
            list(pool.map(_record_many, range(threads)))
        assert len(trail.query()) == per_thread * threads

    def test_query_never_blocks_on_a_concurrent_record(self) -> None:
        trail = AgentAuditTrail()
        trail.record(_entry())
        with ThreadPoolExecutor(max_workers=2) as pool:
            record_future = pool.submit(lambda: [trail.record(_entry()) for _ in range(200)])
            query_future = pool.submit(lambda: [len(trail.query()) for _ in range(200)])
            record_future.result(timeout=10)
            counts = query_future.result(timeout=10)
        assert all(1 <= count <= 201 for count in counts)


class TestSerialization:
    def test_entry_serializes_via_core_serialization(self) -> None:
        serialized = to_dict(_entry())
        assert serialized["agent_code"] == "FLEET.AuditFixture"
        assert serialized["scope"] == {"pit": "north"}
