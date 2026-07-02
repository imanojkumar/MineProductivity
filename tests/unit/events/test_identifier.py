"""Tests for mineproductivity.events.identifier."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.events.identifier import EventID, _encode_crockford_base32, _generate_ulid


class TestEventIDGenerate:
    def test_generates_26_character_value(self) -> None:
        assert len(EventID.generate().value) == 26

    def test_generates_unique_values(self) -> None:
        assert EventID.generate() != EventID.generate()

    def test_generated_values_are_lexicographically_time_sortable(self) -> None:
        earlier = _generate_ulid(_timestamp_ms=1_000_000)
        later = _generate_ulid(_timestamp_ms=2_000_000)
        assert earlier < later

    def test_same_timestamp_still_produces_distinct_values(self) -> None:
        a = _generate_ulid(_timestamp_ms=1_000_000)
        b = _generate_ulid(_timestamp_ms=1_000_000)
        assert a != b


class TestEventIDConstruction:
    def test_direct_construction_from_string(self) -> None:
        identifier = EventID(value="csv-0001")
        assert identifier.value == "csv-0001"
        assert str(identifier) == "csv-0001"

    def test_equal_values_are_equal(self) -> None:
        assert EventID(value="a") == EventID(value="a")

    def test_different_values_are_not_equal(self) -> None:
        assert EventID(value="a") != EventID(value="b")

    def test_is_hashable(self) -> None:
        assert hash(EventID(value="a")) == hash(EventID(value="a"))

    def test_is_frozen(self) -> None:
        identifier = EventID(value="a")
        with pytest.raises(dataclasses.FrozenInstanceError):
            identifier.value = "b"  # type: ignore[misc]


class TestCrockfordBase32Encoding:
    def test_encodes_zero_bytes_to_all_zero_characters(self) -> None:
        encoded = _encode_crockford_base32(b"\x00" * 16)
        assert encoded == "0" * 26

    def test_encoded_length_is_always_26_for_16_bytes(self) -> None:
        assert len(_encode_crockford_base32(b"\xff" * 16)) == 26

    def test_uses_only_crockford_alphabet_characters(self) -> None:
        encoded = _encode_crockford_base32(b"\xab\xcd\xef" * 5 + b"\x01")
        assert set(encoded) <= set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
