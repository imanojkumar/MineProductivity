"""Tests for mineproductivity.core.identifier."""

from __future__ import annotations

import dataclasses
import uuid

import pytest

from mineproductivity.core.identifier import BaseIdentifier, UUIDIdentifier


@dataclasses.dataclass(frozen=True, slots=True)
class TruckId(BaseIdentifier[str]):
    pass


class TestBaseIdentifier:
    def test_equal_values_are_equal(self) -> None:
        assert TruckId("T-1") == TruckId("T-1")

    def test_different_values_are_not_equal(self) -> None:
        assert TruckId("T-1") != TruckId("T-2")

    def test_str_returns_underlying_value(self) -> None:
        assert str(TruckId("T-1")) == "T-1"

    def test_is_hashable(self) -> None:
        assert hash(TruckId("T-1")) == hash(TruckId("T-1"))

    def test_is_frozen(self) -> None:
        identifier = TruckId("T-1")
        with pytest.raises(dataclasses.FrozenInstanceError):
            identifier.value = "T-2"  # type: ignore[misc]


class TestUUIDIdentifier:
    def test_generate_produces_uuid(self) -> None:
        identifier = UUIDIdentifier.generate()
        assert isinstance(identifier.value, uuid.UUID)

    def test_generate_produces_unique_values(self) -> None:
        assert UUIDIdentifier.generate() != UUIDIdentifier.generate()

    def test_from_string_round_trips(self) -> None:
        original = UUIDIdentifier.generate()
        parsed = UUIDIdentifier.from_string(str(original))
        assert original == parsed

    def test_str_is_canonical_uuid_form(self) -> None:
        identifier = UUIDIdentifier.generate()
        assert str(identifier) == str(identifier.value)

    def test_from_string_rejects_malformed_input(self) -> None:
        with pytest.raises(ValueError):
            UUIDIdentifier.from_string("not-a-uuid")
