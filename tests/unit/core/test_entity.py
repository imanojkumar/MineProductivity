"""Tests for mineproductivity.core.entity."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core.entity import BaseEntity


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Truck(BaseEntity[str]):
    model: str


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Shovel(BaseEntity[str]):
    model: str


class TestIdentityEquality:
    def test_same_id_same_type_are_equal_even_with_different_fields(self) -> None:
        assert Truck(id="T-1", model="CAT 793") == Truck(id="T-1", model="Komatsu 930E")

    def test_different_id_same_type_are_not_equal(self) -> None:
        assert Truck(id="T-1", model="CAT 793") != Truck(id="T-2", model="CAT 793")

    def test_same_id_different_type_are_not_equal(self) -> None:
        assert Truck(id="X-1", model="CAT 793") != Shovel(id="X-1", model="CAT 793")

    def test_not_equal_to_unrelated_type(self) -> None:
        assert Truck(id="T-1", model="CAT 793") != "T-1"
        assert (Truck(id="T-1", model="CAT 793") == "T-1") is False

    def test_equality_is_reflexive(self) -> None:
        truck = Truck(id="T-1", model="CAT 793")
        assert truck == truck


class TestHashing:
    def test_equal_entities_hash_equal(self) -> None:
        a = Truck(id="T-1", model="CAT 793")
        b = Truck(id="T-1", model="Komatsu 930E")
        assert hash(a) == hash(b)

    def test_usable_in_a_set(self) -> None:
        a = Truck(id="T-1", model="CAT 793")
        b = Truck(id="T-1", model="Komatsu 930E")
        c = Truck(id="T-2", model="CAT 793")
        assert {a, b, c} == {a, c}


class TestImmutability:
    def test_field_assignment_raises(self) -> None:
        truck = Truck(id="T-1", model="CAT 793")
        with pytest.raises(dataclasses.FrozenInstanceError):
            truck.model = "different"  # type: ignore[misc]


class TestRepr:
    def test_repr_shows_all_fields(self) -> None:
        truck = Truck(id="T-1", model="CAT 793")
        text = repr(truck)
        assert "T-1" in text
        assert "CAT 793" in text


class TestGenericIdTypes:
    def test_entity_with_int_id(self) -> None:
        @dataclasses.dataclass(frozen=True, slots=True, eq=False)
        class Numbered(BaseEntity[int]):
            label: str

        assert Numbered(id=1, label="a") == Numbered(id=1, label="b")
        assert Numbered(id=1, label="a") != Numbered(id=2, label="a")
