"""Tests for mineproductivity.events.exceptions."""

from __future__ import annotations

import pytest

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.events.exceptions import (
    DuplicateEventError,
    EventNotFoundError,
    EventValidationError,
    EventVersionConflictError,
    ReplayError,
)


class TestExceptionHierarchy:
    def test_event_validation_error_is_a_validation_error(self) -> None:
        assert issubclass(EventValidationError, ValidationError)

    def test_event_not_found_error_is_a_not_found_error(self) -> None:
        assert issubclass(EventNotFoundError, NotFoundError)

    def test_event_version_conflict_error_is_a_mineproductivity_error(self) -> None:
        assert issubclass(EventVersionConflictError, MineProductivityError)

    def test_duplicate_event_error_is_a_mineproductivity_error(self) -> None:
        assert issubclass(DuplicateEventError, MineProductivityError)

    def test_replay_error_is_a_mineproductivity_error(self) -> None:
        assert issubclass(ReplayError, MineProductivityError)

    @pytest.mark.parametrize(
        "exc_type",
        [
            EventValidationError,
            EventNotFoundError,
            EventVersionConflictError,
            DuplicateEventError,
            ReplayError,
        ],
    )
    def test_catchable_as_root(self, exc_type: type[MineProductivityError]) -> None:
        with pytest.raises(MineProductivityError):
            raise exc_type("boom")

    @pytest.mark.parametrize(
        "exc_type",
        [
            EventValidationError,
            EventNotFoundError,
            EventVersionConflictError,
            DuplicateEventError,
            ReplayError,
        ],
    )
    def test_carries_message(self, exc_type: type[MineProductivityError]) -> None:
        err = exc_type("boom")
        assert err.message == "boom"
