"""Tests for mineproductivity.connectors.exceptions."""

from __future__ import annotations

import pytest

from mineproductivity.core import MineProductivityError
from mineproductivity.connectors.exceptions import (
    AuthenticationError,
    ConnectorError,
    ContractViolationError,
    MappingError,
    SourceUnavailableError,
)

_SUBCLASSES = [MappingError, AuthenticationError, SourceUnavailableError, ContractViolationError]


class TestExceptionHierarchy:
    def test_connector_error_is_a_mineproductivity_error(self) -> None:
        assert issubclass(ConnectorError, MineProductivityError)

    @pytest.mark.parametrize("exc_type", _SUBCLASSES)
    def test_is_a_connector_error(self, exc_type: type[ConnectorError]) -> None:
        assert issubclass(exc_type, ConnectorError)

    @pytest.mark.parametrize("exc_type", [ConnectorError, *_SUBCLASSES])
    def test_catchable_as_root(self, exc_type: type[MineProductivityError]) -> None:
        with pytest.raises(MineProductivityError):
            raise exc_type("boom")

    @pytest.mark.parametrize("exc_type", [ConnectorError, *_SUBCLASSES])
    def test_carries_message(self, exc_type: type[MineProductivityError]) -> None:
        err = exc_type("boom")
        assert err.message == "boom"
