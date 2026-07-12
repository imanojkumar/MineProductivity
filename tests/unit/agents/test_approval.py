"""Tests for mineproductivity.agents.approval (design spec §16)."""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.agents.approval import ApprovalRequest, ApprovalStatus
from mineproductivity.core.serialization import to_dict


class TestApprovalStatus:
    def test_exactly_the_three_members(self) -> None:
        assert {member.value for member in ApprovalStatus} == {
            "pending",
            "approved",
            "rejected",
        }


class TestApprovalRequest:
    def test_defaults(self) -> None:
        request = ApprovalRequest(task_id="TASK-1", requested_action="approve_shutdown")
        assert request.status is ApprovalStatus.PENDING
        assert request.approver is None
        assert request.resolved_at is None

    def test_resolution_is_a_new_instance(self) -> None:
        """Design spec §16: resolution is a caller action, expressed
        as a new value -- never an in-place edit."""
        pending = ApprovalRequest(task_id="TASK-1", requested_action="approve_shutdown")
        resolved = pending.replace(
            status=ApprovalStatus.APPROVED,
            approver="shift.supervisor@mine.example",
            resolved_at=datetime(2026, 7, 1, 7, 0, tzinfo=timezone.utc),
        )
        assert pending.status is ApprovalStatus.PENDING
        assert resolved.status is ApprovalStatus.APPROVED
        assert resolved.approver == "shift.supervisor@mine.example"

    def test_serializes_via_core_serialization(self) -> None:
        serialized = to_dict(ApprovalRequest(task_id="TASK-1", requested_action="approve_shutdown"))
        assert serialized["task_id"] == "TASK-1"
        assert serialized["requested_action"] == "approve_shutdown"
