"""Tests for mineproductivity.digital_twin.result."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mineproductivity.core.serialization import DataclassSerializer, to_dict
from mineproductivity.digital_twin.lifecycle import TwinStatus
from mineproductivity.digital_twin.result import SyncResult, TwinResult, TwinSimulationResult
from mineproductivity.digital_twin.snapshot import TwinSnapshot
from mineproductivity.digital_twin.state import TwinState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _state() -> TwinState:
    return TwinState(attributes={"belt_speed_mps": 3.1}, captured_at=_EPOCH)


def _sync_result() -> SyncResult:
    return SyncResult(
        twin_id="CONV-7",
        previous_status=TwinStatus.PROVISIONED,
        new_status=TwinStatus.SYNCHRONIZED,
        events_applied=3,
    )


def _simulation_result() -> TwinSimulationResult:
    return TwinSimulationResult(
        twin_id="CONV-7",
        hypothesis={"belt_speed_mps": 3.5},
        predicted_state=_state(),
    )


class TestTwinResult:
    def test_defaults(self) -> None:
        result = TwinResult()
        assert result.twin_id == ""
        assert result.warnings == ()
        assert result.computed_at.tzinfo is timezone.utc

    def test_warnings_carry_the_why_didnt_state_change_signal(self) -> None:
        result = TwinResult(twin_id="CONV-7", warnings=("no events to apply",))
        assert result.warnings == ("no events to apply",)


class TestSyncResult:
    def test_carries_the_lifecycle_transition_and_batch_size(self) -> None:
        result = _sync_result()
        assert result.previous_status is TwinStatus.PROVISIONED
        assert result.new_status is TwinStatus.SYNCHRONIZED
        assert result.events_applied == 3

    def test_is_a_twin_result(self) -> None:
        assert issubclass(SyncResult, TwinResult)


class TestTwinSimulationResult:
    def test_carries_hypothesis_and_predicted_state(self) -> None:
        result = _simulation_result()
        assert result.hypothesis["belt_speed_mps"] == 3.5
        assert result.predicted_state == _state()

    def test_hypothesis_is_frozen(self) -> None:
        result = _simulation_result()
        with pytest.raises(TypeError):
            result.hypothesis["new_key"] = 1  # type: ignore[index]

    def test_is_a_twin_result(self) -> None:
        assert issubclass(TwinSimulationResult, TwinResult)


class TestStateAndSnapshotAreNotResults:
    """Design spec §25: ``TwinState``/``TwinSnapshot`` represent the
    twin's condition itself, never the outcome of one orchestration call
    about it."""

    def test_twin_state_is_not_a_twin_result(self) -> None:
        assert not issubclass(TwinState, TwinResult)

    def test_twin_snapshot_is_not_a_twin_result(self) -> None:
        assert not issubclass(TwinSnapshot, TwinResult)


class TestSerialization:
    """Design spec §19: every result type serializes via
    ``core.serialization`` with no bespoke per-type serializer."""

    _INSTANCES = (
        TwinResult(twin_id="CONV-7"),
        _sync_result(),
        _simulation_result(),
    )

    @pytest.mark.parametrize("instance", _INSTANCES)
    def test_to_dict_works_generically_for_every_result_type(self, instance: object) -> None:
        data = to_dict(instance)
        assert isinstance(data, dict)
        assert data

    @pytest.mark.parametrize("instance", _INSTANCES)
    def test_no_result_type_defines_its_own_to_dict_method(self, instance: object) -> None:
        assert "to_dict" not in type(instance).__dict__

    def test_twin_result_round_trips(self) -> None:
        serializer = DataclassSerializer(TwinResult)
        original = TwinResult(twin_id="CONV-7", warnings=("no events to apply",))
        assert serializer.deserialize(serializer.serialize(original)) == original
