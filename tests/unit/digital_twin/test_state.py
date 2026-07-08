"""Tests for mineproductivity.digital_twin.state."""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType

import pytest

from mineproductivity.core import BaseValueObject
from mineproductivity.core.serialization import DataclassSerializer, to_dict
from mineproductivity.digital_twin.exceptions import TwinValidationError
from mineproductivity.digital_twin.state import TwinState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestTwinState:
    def test_is_a_value_object_not_an_entity(self) -> None:
        assert issubclass(TwinState, BaseValueObject)

    def test_minimal_valid_construction(self) -> None:
        state = TwinState(attributes={"belt_speed_mps": 3.1}, captured_at=_EPOCH)
        assert state.attributes["belt_speed_mps"] == 3.1
        assert state.captured_at is _EPOCH

    def test_schema_version_defaults(self) -> None:
        state = TwinState(attributes={"x": 1}, captured_at=_EPOCH)
        assert state.schema_version == "1.0.0"

    def test_schema_version_travels_with_the_value(self) -> None:
        """Design spec §21's third versioning axis: per stored value,
        never inferred from ``TwinMetadata.version`` at read time."""
        state = TwinState(attributes={"x": 1}, captured_at=_EPOCH, schema_version="2.0.0")
        assert state.schema_version == "2.0.0"

    def test_attributes_are_frozen_into_a_read_only_mapping(self) -> None:
        state = TwinState(attributes={"x": 1}, captured_at=_EPOCH)
        assert isinstance(state.attributes, MappingProxyType)
        with pytest.raises(TypeError):
            state.attributes["y"] = 2  # type: ignore[index]

    def test_attributes_are_copied_from_the_caller_supplied_mapping(self) -> None:
        supplied = {"x": 1}
        state = TwinState(attributes=supplied, captured_at=_EPOCH)
        supplied["x"] = 999
        assert state.attributes["x"] == 1

    def test_empty_attributes_raises(self) -> None:
        with pytest.raises(TwinValidationError, match="attributes must not be empty"):
            TwinState(attributes={}, captured_at=_EPOCH)

    def test_value_equality(self) -> None:
        first = TwinState(attributes={"x": 1}, captured_at=_EPOCH)
        second = TwinState(attributes={"x": 1}, captured_at=_EPOCH)
        assert first == second
        assert first is not second


class TestSerialization:
    def test_to_dict_works_generically(self) -> None:
        state = TwinState(attributes={"x": 1}, captured_at=_EPOCH)
        data = to_dict(state)
        assert data["attributes"] == {"x": 1}
        assert data["schema_version"] == "1.0.0"

    def test_no_bespoke_to_dict_method(self) -> None:
        assert "to_dict" not in TwinState.__dict__

    def test_round_trips_via_dataclass_serializer(self) -> None:
        serializer = DataclassSerializer(TwinState)
        original = TwinState(attributes={"x": 1}, captured_at=_EPOCH)
        assert serializer.deserialize(serializer.serialize(original)) == original
