"""Tests for mineproductivity.core.versioning."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core.exceptions import ValidationError
from mineproductivity.core.versioning import BaseVersionedObject


@dataclasses.dataclass(frozen=True, slots=True)
class Note(BaseVersionedObject):
    text: str


class TestDefaultVersion:
    def test_default_version_is_one(self) -> None:
        assert Note(text="draft").version == 1


class TestNextVersion:
    def test_next_version_increments(self) -> None:
        note = Note(text="draft")
        updated = note.next_version()
        assert updated.version == 2
        assert note.version == 1

    def test_next_version_preserves_other_fields(self) -> None:
        note = Note(text="draft")
        updated = note.next_version()
        assert updated.text == "draft"

    def test_next_version_returns_new_instance(self) -> None:
        note = Note(text="draft")
        assert note.next_version() is not note

    def test_repeated_next_version_calls_accumulate(self) -> None:
        note = Note(text="draft")
        assert note.next_version().next_version().version == 3


class TestValidation:
    def test_zero_version_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Note(text="draft", version=0)

    def test_negative_version_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Note(text="draft", version=-1)

    def test_explicit_valid_version_accepted(self) -> None:
        assert Note(text="draft", version=5).version == 5


class TestEquality:
    def test_same_version_and_fields_are_equal(self) -> None:
        assert Note(text="draft", version=2) == Note(text="draft", version=2)

    def test_different_version_are_not_equal(self) -> None:
        assert Note(text="draft", version=1) != Note(text="draft", version=2)
