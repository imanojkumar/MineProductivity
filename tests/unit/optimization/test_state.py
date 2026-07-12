"""Tests for mineproductivity.optimization.state."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from mineproductivity.core.serialization import DataclassSerializer, to_dict
from mineproductivity.optimization.exceptions import OptimizationValidationError
from mineproductivity.optimization.result import OptimizationResult
from mineproductivity.optimization.state import OptimizationState


class TestOptimizationState:
    def test_attributes_are_frozen_and_copied(self) -> None:
        supplied = {"incumbent": 42.0}
        state = OptimizationState(attributes=supplied)
        supplied["incumbent"] = 0.0
        assert isinstance(state.attributes, MappingProxyType)
        assert state.attributes["incumbent"] == 42.0
        with pytest.raises(TypeError):
            state.attributes["x"] = 1  # type: ignore[index]

    def test_empty_attributes_raises(self) -> None:
        with pytest.raises(OptimizationValidationError, match="attributes must not be empty"):
            OptimizationState(attributes={})

    def test_is_not_an_optimization_result(self) -> None:
        """Design spec §18: the state is the run's condition, not the
        outcome of an orchestration call about it."""
        assert not issubclass(OptimizationState, OptimizationResult)

    def test_serializes_generically_and_round_trips(self) -> None:
        state = OptimizationState(attributes={"incumbent": 42.0})
        assert to_dict(state)["attributes"] == {"incumbent": 42.0}
        serializer = DataclassSerializer(OptimizationState)
        assert serializer.deserialize(serializer.serialize(state)) == state
