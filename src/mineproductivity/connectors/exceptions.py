"""The ``mineproductivity.connectors`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError

__all__ = [
    "AuthenticationError",
    "ConnectorError",
    "ContractViolationError",
    "MappingError",
    "SourceUnavailableError",
]


class ConnectorError(MineProductivityError):
    """Root of connector-specific errors."""


class MappingError(ConnectorError):
    """A raw record could not be normalized -- e.g. an unrecognized vendor
    reason code with no :class:`~mineproductivity.connectors.normalization.ReasonCodeMap`
    entry, or a malformed numeric field."""


class AuthenticationError(ConnectorError):
    """An :class:`~mineproductivity.connectors.auth.AuthProvider` could not
    obtain or refresh valid credentials."""


class SourceUnavailableError(ConnectorError):
    """The source is unreachable (network, file-not-found, ...) -- the
    default retryable exception type."""


class ContractViolationError(ConnectorError):
    """A connector implementation failed the shared contract test suite --
    e.g. it returned a list instead of a lazy ``Iterable``, or yielded an
    event outside the requested ``[since, until)`` window."""
