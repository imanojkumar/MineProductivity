"""Tests for mineproductivity.agents.communication (design spec §18):
message/delegation shapes, and the §35 delegation-transport proof --
published via ``events.EventBus.publish``, never a competing
transport."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Any

from mineproductivity.agents.communication import AgentMessage, DelegationRequest
from mineproductivity.core import PredicateSpecification
from mineproductivity.core.serialization import to_dict
from mineproductivity.events import BaseEvent, EventEnvelope, EventID, EventVersion
from mineproductivity.events.bus import _InMemoryEventBus

_WHEN = datetime(2026, 7, 1, 6, 0, tzinfo=timezone.utc)


def _delegation() -> DelegationRequest:
    return DelegationRequest(
        task_id="TASK-1",
        from_agent_code="SHIFT_SUPERVISOR.NightShift",
        to_agent_code="FLEET.ReassignmentAdvisor",
        reason="fleet expertise required",
    )


def _message(content: dict[str, Any]) -> AgentMessage:
    return AgentMessage(
        from_agent_code="SHIFT_SUPERVISOR.NightShift",
        to_agent_code="FLEET.ReassignmentAdvisor",
        task_id="TASK-1",
        content=content,
        sent_at=_WHEN,
    )


class TestAgentMessage:
    def test_content_is_frozen_and_copied(self) -> None:
        source: dict[str, Any] = {"kind": "status"}
        message = _message(source)
        source["kind"] = "mutated"
        assert message.content["kind"] == "status"

    def test_serializes_via_core_serialization(self) -> None:
        assert to_dict(_message({"kind": "status"}))["task_id"] == "TASK-1"


class TestDelegationRequest:
    def test_carries_the_reason_for_the_audit_trail(self) -> None:
        assert _delegation().reason == "fleet expertise required"


@dataclasses.dataclass(frozen=True, slots=True)
class _AgentMessageEvent(BaseEvent):
    """Test-local envelope payload wrapping one serialized
    ``AgentMessage`` -- the composition seam design spec §18
    prescribes: this package defines the message shape; ``events``
    provides the transport, unchanged."""

    message: dict[str, Any] = dataclasses.field(default_factory=dict, kw_only=True)

    event_type_code = "agents.message.fixture"

    def duration_h(self) -> float:
        return 0.0


class TestDelegationTransportProof:
    def test_delegation_is_published_via_events_event_bus(self) -> None:
        """Design spec §18, §35: delegation is an ordinary
        AgentMessage whose content carries a DelegationRequest,
        published through ``EventBus.publish`` -- no second message
        bus exists in this package (§34)."""
        message = _message({"kind": "delegation", "delegation": to_dict(_delegation())})
        bus = _InMemoryEventBus()
        received: list[EventEnvelope[Any]] = []
        bus.subscribe(PredicateSpecification(lambda envelope: True), received.append)

        bus.publish(
            EventEnvelope(
                event_id=EventID.generate(),
                version=EventVersion(),
                payload=_AgentMessageEvent(
                    equipment_id="",
                    shift_id="A-2026-07-01",
                    message=dict(to_dict(message)),
                ),
                event_time_utc=_WHEN,
                processing_time_utc=_WHEN,
                ingestion_time_utc=_WHEN,
            )
        )

        assert len(received) == 1
        delivered = received[0].payload.message
        assert delivered["content"]["delegation"]["to_agent_code"] == ("FLEET.ReassignmentAdvisor")

    def test_no_competing_transport_is_defined_in_communication_py(self) -> None:
        import mineproductivity.agents.communication as communication_module

        defined_classes = {
            name
            for name in dir(communication_module)
            if isinstance(obj := getattr(communication_module, name), type)
            and obj.__module__ == communication_module.__name__
        }
        assert defined_classes == {"AgentMessage", "DelegationRequest"}
