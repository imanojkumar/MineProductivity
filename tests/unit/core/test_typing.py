"""Tests for mineproductivity.core.typing."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core.typing import Comparable, Identifiable, JSONValue


class TestComparable:
    def test_int_satisfies_protocol(self) -> None:
        assert isinstance(5, Comparable)

    def test_str_satisfies_protocol(self) -> None:
        assert isinstance("a", Comparable)

    def test_runtime_checkable_protocol_is_structural_not_behavioral(self) -> None:
        # object itself defines __lt__ (it returns NotImplemented), so a
        # runtime_checkable Protocol match is a structural (attribute
        # presence) check, not a guarantee the operation succeeds.
        class NoRealLt:
            pass

        assert isinstance(NoRealLt(), Comparable)
        with pytest.raises(TypeError):
            NoRealLt() < NoRealLt()  # type: ignore[operator]


class TestIdentifiable:
    def test_object_with_id_attribute_satisfies_protocol(self) -> None:
        @dataclasses.dataclass
        class Thing:
            id: str

        assert isinstance(Thing(id="1"), Identifiable)

    def test_object_without_id_attribute_does_not_satisfy_protocol(self) -> None:
        @dataclasses.dataclass
        class Thing:
            name: str

        assert not isinstance(Thing(name="x"), Identifiable)


class TestJSONValue:
    def test_accepts_nested_structure(self) -> None:
        value: JSONValue = {"a": [1, 2.5, "x", None, True, {"nested": []}]}
        assert isinstance(value, dict)
        assert value["a"] == [1, 2.5, "x", None, True, {"nested": []}]

    def test_accepts_primitive(self) -> None:
        value: JSONValue = "hello"
        assert value == "hello"
