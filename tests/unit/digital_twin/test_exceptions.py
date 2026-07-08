"""Tests for mineproductivity.digital_twin.exceptions."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.digital_twin.exceptions import (
    TwinNotFoundError,
    TwinStateConflictError,
    TwinSyncError,
    TwinValidationError,
    TwinVersionConflictError,
)
from mineproductivity.registry import RegistrationError


class TestHierarchy:
    """Design spec §6: each exception subclasses the matching ``core``
    (or ``registry``) exception, exactly as every other domain package's
    exceptions do."""

    def test_twin_validation_error(self) -> None:
        assert issubclass(TwinValidationError, ValidationError)

    def test_twin_not_found_error(self) -> None:
        assert issubclass(TwinNotFoundError, NotFoundError)

    def test_twin_sync_error(self) -> None:
        assert issubclass(TwinSyncError, MineProductivityError)

    def test_twin_version_conflict_error(self) -> None:
        assert issubclass(TwinVersionConflictError, RegistrationError)

    def test_twin_state_conflict_error(self) -> None:
        assert issubclass(TwinStateConflictError, MineProductivityError)

    def test_all_are_mineproductivity_errors(self) -> None:
        for exception_type in (
            TwinValidationError,
            TwinNotFoundError,
            TwinSyncError,
            TwinVersionConflictError,
            TwinStateConflictError,
        ):
            assert issubclass(exception_type, MineProductivityError)
