"""Tests for mineproductivity.core.serialization."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core.exceptions import SerializationError
from mineproductivity.core.serialization import (
    BaseSerializer,
    DataclassSerializer,
    SupportsFromDict,
    SupportsToDict,
    to_dict,
)


@dataclasses.dataclass(frozen=True, slots=True)
class Point:
    x: int
    y: int


class WithToDict:
    def to_dict(self) -> dict[str, int]:
        return {"a": 1}


class WithFromDict:
    @classmethod
    def from_dict(cls, data: dict[str, int]) -> WithFromDict:
        return cls()


class TestProtocols:
    def test_object_with_to_dict_satisfies_supports_to_dict(self) -> None:
        assert isinstance(WithToDict(), SupportsToDict)

    def test_object_without_to_dict_does_not_satisfy_protocol(self) -> None:
        assert not isinstance(object(), SupportsToDict)

    def test_class_with_from_dict_satisfies_supports_from_dict(self) -> None:
        assert isinstance(WithFromDict, SupportsFromDict)


class TestBaseSerializer:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseSerializer()  # type: ignore[abstract]


class TestDataclassSerializer:
    def test_serialize_returns_plain_dict(self) -> None:
        serializer = DataclassSerializer(Point)
        assert serializer.serialize(Point(1, 2)) == {"x": 1, "y": 2}

    def test_deserialize_reconstructs_instance(self) -> None:
        serializer = DataclassSerializer(Point)
        assert serializer.deserialize({"x": 1, "y": 2}) == Point(1, 2)

    def test_round_trip(self) -> None:
        serializer = DataclassSerializer(Point)
        original = Point(3, 4)
        assert serializer.deserialize(serializer.serialize(original)) == original

    def test_rejects_non_dataclass_target_type(self) -> None:
        with pytest.raises(SerializationError):
            DataclassSerializer(int)

    def test_serialize_rejects_non_dataclass_instance(self) -> None:
        serializer = DataclassSerializer(Point)
        with pytest.raises(SerializationError):
            serializer.serialize(object())  # type: ignore[arg-type]

    def test_deserialize_wraps_type_error(self) -> None:
        serializer = DataclassSerializer(Point)
        with pytest.raises(SerializationError):
            serializer.deserialize({"x": 1, "unknown_field": 2})


class TestToDict:
    def test_uses_to_dict_method_when_available(self) -> None:
        assert to_dict(WithToDict()) == {"a": 1}

    def test_falls_back_to_dataclasses_asdict(self) -> None:
        assert to_dict(Point(1, 2)) == {"x": 1, "y": 2}

    def test_raises_for_unsupported_object(self) -> None:
        with pytest.raises(SerializationError):
            to_dict(42)

    def test_raises_for_dataclass_type_not_instance(self) -> None:
        with pytest.raises(SerializationError):
            to_dict(Point)
