"""Tests for mineproductivity.registry.exceptions."""

from __future__ import annotations

import pytest

from mineproductivity.core import MineProductivityError, NotFoundError
from mineproductivity.registry.exceptions import (
    DuplicateRegistrationError,
    RegistrationError,
    UnregisteredLookupError,
    VersionIncompatibleError,
)


class TestExceptionHierarchy:
    def test_registration_error_is_a_mineproductivity_error(self) -> None:
        assert issubclass(RegistrationError, MineProductivityError)

    def test_duplicate_registration_error_is_a_registration_error(self) -> None:
        assert issubclass(DuplicateRegistrationError, RegistrationError)

    def test_unregistered_lookup_error_is_a_not_found_error(self) -> None:
        assert issubclass(UnregisteredLookupError, NotFoundError)

    def test_version_incompatible_error_is_a_registration_error(self) -> None:
        assert issubclass(VersionIncompatibleError, RegistrationError)

    @pytest.mark.parametrize(
        "exc_type",
        [
            RegistrationError,
            DuplicateRegistrationError,
            UnregisteredLookupError,
            VersionIncompatibleError,
        ],
    )
    def test_catchable_as_root(self, exc_type: type[MineProductivityError]) -> None:
        with pytest.raises(MineProductivityError):
            raise exc_type("boom")

    @pytest.mark.parametrize(
        "exc_type",
        [
            RegistrationError,
            DuplicateRegistrationError,
            UnregisteredLookupError,
            VersionIncompatibleError,
        ],
    )
    def test_carries_message(self, exc_type: type[MineProductivityError]) -> None:
        err = exc_type("boom")
        assert err.message == "boom"
