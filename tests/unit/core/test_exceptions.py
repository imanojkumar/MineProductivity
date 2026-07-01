"""Tests for mineproductivity.core.exceptions."""

from __future__ import annotations

import pytest

from mineproductivity.core.exceptions import (
    BuilderError,
    ConfigurationError,
    DuplicateError,
    MineProductivityError,
    NotFoundError,
    SerializationError,
    ValidationError,
)

SUBCLASSES = [
    ValidationError,
    ConfigurationError,
    NotFoundError,
    DuplicateError,
    SerializationError,
    BuilderError,
]


class TestMineProductivityError:
    def test_message_stored(self) -> None:
        err = MineProductivityError("boom")
        assert err.message == "boom"
        assert str(err) == "boom"

    def test_default_details_is_empty_mapping(self) -> None:
        err = MineProductivityError("boom")
        assert err.details == {}

    def test_details_stored(self) -> None:
        err = MineProductivityError("boom", details={"field": "x"})
        assert err.details == {"field": "x"}

    def test_repr_includes_message_and_details(self) -> None:
        err = MineProductivityError("boom", details={"a": 1})
        text = repr(err)
        assert "MineProductivityError" in text
        assert "boom" in text
        assert "'a': 1" in text

    def test_is_an_exception(self) -> None:
        assert issubclass(MineProductivityError, Exception)

    def test_raisable(self) -> None:
        with pytest.raises(MineProductivityError, match="boom"):
            raise MineProductivityError("boom")


@pytest.mark.parametrize("exc_type", SUBCLASSES)
class TestExceptionHierarchy:
    def test_subclasses_root(self, exc_type: type[MineProductivityError]) -> None:
        assert issubclass(exc_type, MineProductivityError)

    def test_catchable_as_root(self, exc_type: type[MineProductivityError]) -> None:
        with pytest.raises(MineProductivityError):
            raise exc_type("failure")

    def test_carries_message_and_details(self, exc_type: type[MineProductivityError]) -> None:
        err = exc_type("failure", details={"k": "v"})
        assert err.message == "failure"
        assert err.details == {"k": "v"}
