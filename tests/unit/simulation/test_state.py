"""Tests for mineproductivity.simulation.state."""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType

import pytest

from mineproductivity.core import BaseValueObject
from mineproductivity.core.serialization import DataclassSerializer, to_dict
from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.result import SimulationResult
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestSimulationState:
    def test_is_a_value_object_not_a_result(self) -> None:
        """Design spec §18: a state represents the run's condition
        itself, never the outcome of an orchestration call about it."""
        assert issubclass(SimulationState, BaseValueObject)
        assert not issubclass(SimulationState, SimulationResult)

    def test_minimal_valid_construction(self) -> None:
        state = SimulationState(attributes={"queue_len": 4}, simulated_time=_EPOCH)
        assert state.attributes["queue_len"] == 4
        assert state.simulated_time is _EPOCH

    def test_attributes_are_frozen_into_a_read_only_mapping(self) -> None:
        state = SimulationState(attributes={"x": 1}, simulated_time=_EPOCH)
        assert isinstance(state.attributes, MappingProxyType)
        with pytest.raises(TypeError):
            state.attributes["y"] = 2  # type: ignore[index]

    def test_attributes_are_copied_from_the_caller_supplied_mapping(self) -> None:
        supplied = {"x": 1}
        state = SimulationState(attributes=supplied, simulated_time=_EPOCH)
        supplied["x"] = 999
        assert state.attributes["x"] == 1

    def test_empty_attributes_raises(self) -> None:
        with pytest.raises(SimulationValidationError, match="attributes must not be empty"):
            SimulationState(attributes={}, simulated_time=_EPOCH)

    def test_value_equality(self) -> None:
        first = SimulationState(attributes={"x": 1}, simulated_time=_EPOCH)
        second = SimulationState(attributes={"x": 1}, simulated_time=_EPOCH)
        assert first == second
        assert first is not second


class TestSerialization:
    def test_to_dict_works_generically(self) -> None:
        state = SimulationState(attributes={"x": 1}, simulated_time=_EPOCH)
        assert to_dict(state)["attributes"] == {"x": 1}

    def test_no_bespoke_to_dict_method(self) -> None:
        assert "to_dict" not in SimulationState.__dict__

    def test_round_trips_via_dataclass_serializer(self) -> None:
        serializer = DataclassSerializer(SimulationState)
        original = SimulationState(attributes={"x": 1}, simulated_time=_EPOCH)
        assert serializer.deserialize(serializer.serialize(original)) == original
