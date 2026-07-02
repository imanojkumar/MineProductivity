"""Tests for mineproductivity.events.snapshot."""

from __future__ import annotations

from mineproductivity.events.replay import AsOf
from mineproductivity.events.snapshot import EventSnapshot


class TestEventSnapshot:
    def test_empty_state(self) -> None:
        snapshot = EventSnapshot(as_of=AsOf(scenario="genesis"), state={})
        assert snapshot.state == {}

    def test_holds_envelopes_by_event_id(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        envelope = cycle_envelope_factory()
        snapshot = EventSnapshot(
            as_of=AsOf(scenario="genesis"), state={envelope.event_id.value: envelope}
        )
        assert snapshot.state[envelope.event_id.value] is envelope

    def test_equality_by_value(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        envelope = cycle_envelope_factory()
        as_of = AsOf(scenario="genesis")
        a = EventSnapshot(as_of=as_of, state={envelope.event_id.value: envelope})
        b = EventSnapshot(as_of=as_of, state={envelope.event_id.value: envelope})
        assert a == b
