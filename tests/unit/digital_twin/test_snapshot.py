"""Tests for mineproductivity.digital_twin.snapshot."""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.core import BaseValueObject
from mineproductivity.core.serialization import to_dict
from mineproductivity.digital_twin.lifecycle import TwinStatus
from mineproductivity.digital_twin.result import TwinResult
from mineproductivity.digital_twin.snapshot import TwinSnapshot
from mineproductivity.digital_twin.state import TwinState
from mineproductivity.events import AsOf
from mineproductivity.events.snapshot import EventSnapshot

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _snapshot() -> TwinSnapshot:
    return TwinSnapshot(
        twin_id="CONV-7",
        state=TwinState(attributes={"belt_speed_mps": 3.1}, captured_at=_EPOCH),
        status=TwinStatus.SYNCHRONIZED,
        as_of=AsOf(utc=_EPOCH),
    )


class TestTwinSnapshot:
    def test_pairs_state_with_the_as_of_it_was_captured_at(self) -> None:
        snapshot = _snapshot()
        assert snapshot.twin_id == "CONV-7"
        assert snapshot.state.attributes["belt_speed_mps"] == 3.1
        assert snapshot.status is TwinStatus.SYNCHRONIZED
        assert snapshot.as_of.utc == _EPOCH

    def test_reuses_events_as_of_directly(self) -> None:
        """Design spec §13, §3.4: no second 'moment in time' concept."""
        assert isinstance(_snapshot().as_of, AsOf)

    def test_is_not_a_twin_result(self) -> None:
        """Design spec §25: a snapshot represents the twin's condition
        itself, not the outcome of an orchestration call about it."""
        assert not issubclass(TwinSnapshot, TwinResult)

    def test_is_not_an_event_snapshot(self) -> None:
        """Design spec §13, §31: an ``EventSnapshot`` materializes the
        event store's state; a ``TwinSnapshot`` materializes one twin's
        already-derived state. Neither substitutes for the other."""
        assert not issubclass(TwinSnapshot, EventSnapshot)
        assert not issubclass(EventSnapshot, TwinSnapshot)

    def test_value_equality(self) -> None:
        assert _snapshot() == _snapshot()

    def test_is_a_value_object(self) -> None:
        assert issubclass(TwinSnapshot, BaseValueObject)


class TestSnapshotRoundTrip:
    """Design spec §32's snapshot round-trip proof: serialized via
    ``core.serialization`` and deserialized, a snapshot reproduces the
    original ``TwinState``/``status``/``as_of`` exactly."""

    def test_serializes_via_core_serialization_generically(self) -> None:
        data = to_dict(_snapshot())
        assert data["twin_id"] == "CONV-7"
        assert data["state"]["attributes"] == {"belt_speed_mps": 3.1}

    def test_no_bespoke_to_dict_method(self) -> None:
        assert "to_dict" not in TwinSnapshot.__dict__

    def test_round_trip_reproduces_state_status_and_as_of_exactly(self) -> None:
        original = _snapshot()
        data = to_dict(original)
        rebuilt = TwinSnapshot(
            twin_id=data["twin_id"],
            state=TwinState(**data["state"]),
            status=data["status"],
            as_of=AsOf(**data["as_of"]),
        )
        assert rebuilt == original
        assert rebuilt.state == original.state
        assert rebuilt.status is original.status
        assert rebuilt.as_of == original.as_of
