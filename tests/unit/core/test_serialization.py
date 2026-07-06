"""Tests for mineproductivity.core.serialization."""

from __future__ import annotations

import dataclasses
from collections import namedtuple
from types import MappingProxyType

import pytest

from mineproductivity.core.exceptions import SerializationError
from mineproductivity.core.serialization import (
    BaseSerializer,
    DataclassSerializer,
    SupportsFromDict,
    SupportsToDict,
    to_dict,
)
from mineproductivity.core.value_object import BaseValueObject


@dataclasses.dataclass(frozen=True, slots=True)
class Point:
    x: int
    y: int


@dataclasses.dataclass(frozen=True, slots=True)
class ScopedValue(BaseValueObject):
    """Mirrors ``kpis.KPIResult``'s exact shape: a ``Mapping`` field frozen
    into a read-only ``MappingProxyType`` by ``_normalize()``, the pattern
    ``BaseValueObject``'s own docstring documents and encourages."""

    value: float
    scope: dict[str, str] = dataclasses.field(default_factory=dict)

    def _normalize(self) -> None:
        object.__setattr__(self, "scope", MappingProxyType(dict(self.scope)))


@dataclasses.dataclass(frozen=True, slots=True)
class Wrapper:
    inner: Point
    points: tuple[Point, ...]
    tags: list[str] = dataclasses.field(default_factory=list)


NamedPoint = namedtuple("NamedPoint", ["x", "y"])


@dataclasses.dataclass(frozen=True, slots=True)
class WithNamedTuple:
    point: NamedPoint


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


class TestMappingProxyTypeFields:
    """Regression coverage for the ``mappingproxy`` serialization defect:
    ``dataclasses.asdict`` only special-cases ``isinstance(obj, dict)``, so
    any ``BaseValueObject`` field frozen into ``MappingProxyType`` by
    ``_normalize()`` (a pattern ``BaseValueObject``'s own docstring
    documents and encourages) used to raise
    ``TypeError: cannot pickle 'mappingproxy' object``."""

    def test_to_dict_handles_populated_mappingproxy_field(self) -> None:
        obj = ScopedValue(value=1.0, scope={"pit": "north"})
        data = to_dict(obj)
        assert data == {"value": 1.0, "scope": {"pit": "north"}}
        assert type(data["scope"]) is dict

    def test_to_dict_handles_empty_mappingproxy_field(self) -> None:
        """Even an *empty* ``MappingProxyType({})`` fails under bare
        ``dataclasses.asdict`` -- ``copy.deepcopy`` cannot pickle a
        ``mappingproxy`` regardless of its contents."""
        obj = ScopedValue(value=1.0)
        assert to_dict(obj) == {"value": 1.0, "scope": {}}

    def test_dataclass_serializer_handles_mappingproxy_field(self) -> None:
        serializer = DataclassSerializer(ScopedValue)
        data = serializer.serialize(ScopedValue(value=2.0, scope={"shift": "A"}))
        assert data == {"value": 2.0, "scope": {"shift": "A"}}

    def test_round_trip_through_mappingproxy_field(self) -> None:
        serializer = DataclassSerializer(ScopedValue)
        original = ScopedValue(value=3.0, scope={"pit": "north", "shift": "A"})
        restored = serializer.deserialize(serializer.serialize(original))
        assert restored == original
        assert type(restored.scope) is MappingProxyType

    def test_nested_dataclass_tuple_and_list_fields_still_work(self) -> None:
        """Backward-compatibility check: fields ``dataclasses.asdict``
        already handled correctly (nested dataclasses, tuples of
        dataclasses, plain lists) must still work identically after
        routing through the ``Mapping``-aware recursive helper."""
        wrapper = Wrapper(inner=Point(1, 2), points=(Point(3, 4), Point(5, 6)), tags=["a", "b"])
        data = to_dict(wrapper)
        assert data == {
            "inner": {"x": 1, "y": 2},
            "points": ({"x": 3, "y": 4}, {"x": 5, "y": 6}),
            "tags": ["a", "b"],
        }
        assert type(data["tags"]) is list

    def test_namedtuple_field_still_works(self) -> None:
        """Backward-compatibility check: ``dataclasses.asdict`` special-cases
        namedtuples (reconstructing the same namedtuple type rather than a
        plain tuple); the ``Mapping``-aware recursive helper must preserve
        this exactly."""
        obj = WithNamedTuple(point=NamedPoint(x=1, y=2))
        data = to_dict(obj)
        assert data == {"point": NamedPoint(x=1, y=2)}
        assert type(data["point"]) is NamedPoint

    def test_real_kpi_result_with_populated_scope_serializes(self) -> None:
        """The exact reported failure: ``KPIResult`` with a populated
        ``scope`` used to raise ``TypeError: cannot pickle 'mappingproxy'
        object`` -- the platform's own flagship value object, not a
        synthetic fixture."""
        from mineproductivity.kpis import KPIResult

        result = KPIResult(code="PROD.TPH", value=1200.0, unit="t/h", scope={"pit": "north"})
        data = to_dict(result)
        assert data["scope"] == {"pit": "north"}
        assert type(data["scope"]) is dict

    def test_real_kpi_result_round_trips(self) -> None:
        from mineproductivity.kpis import KPIResult

        serializer = DataclassSerializer(KPIResult)
        original = KPIResult(code="PROD.TPH", value=1200.0, unit="t/h", scope={"pit": "north"})
        restored = serializer.deserialize(serializer.serialize(original))
        assert restored == original

    def test_hash_and_equality_semantics_are_unaffected_by_this_fix(self) -> None:
        """This fix touches only serialization -- it must not change
        equality (still value-based) or hashability (a ``Mapping`` field
        makes a ``BaseValueObject`` unhashable both before and after this
        fix; that is a separate, distinct, already-tracked defect, not
        something this fix addresses or regresses)."""
        first = ScopedValue(value=1.0, scope={"pit": "north"})
        second = ScopedValue(value=1.0, scope={"pit": "north"})
        assert first == second
        with pytest.raises(TypeError, match="unhashable"):
            hash(first)
