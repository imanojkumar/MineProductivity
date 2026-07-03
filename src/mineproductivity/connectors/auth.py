"""``AuthProvider``/``Credentials``: isolates credential acquisition and
refresh from connector I/O logic.
"""

from __future__ import annotations

import dataclasses
import threading
from abc import ABC, abstractmethod
from datetime import datetime

from mineproductivity.core import BaseValueObject, Result, ValidationError

__all__ = ["AuthProvider", "Credentials"]


@dataclasses.dataclass(frozen=True, slots=True)
class Credentials(BaseValueObject):
    """A bearer token and its (optional) expiry."""

    token: str
    expires_at_utc: datetime | None = dataclasses.field(default=None, kw_only=True)

    def validate(self) -> None:
        if not self.token.strip():
            raise ValidationError("Credentials.token must not be empty")


class AuthProvider(ABC):
    """Isolates credential acquisition/refresh from connector I/O logic.

    :meth:`refresh` MUST be safe to call concurrently without acquiring
    duplicate tokens or corrupting the cached :class:`Credentials` (design
    spec §24) -- this is the one thread-safety guarantee this contract
    makes mandatory rather than merely documented, since concurrent
    401-triggered refreshes are a realistic, common failure mode for any
    multi-threaded ingestion pipeline.
    """

    @abstractmethod
    def credentials(self) -> Credentials:
        """Return the current, possibly cached, credentials."""

    @abstractmethod
    def refresh(self) -> Result[Credentials]:
        """Force acquisition of a fresh :class:`Credentials`, replacing
        whatever is cached. Safe to call concurrently (see class
        docstring)."""


class _StaticAuthProvider(AuthProvider):
    """Reference :class:`AuthProvider`: returns a fixed token, "refreshing"
    by incrementing a counter suffix -- suitable for tests, examples, and
    sources authenticated by a single long-lived static token. Not part
    of the public API (mirrors ``events._InMemoryEventStore``'s status as
    a reference implementation, not a mandated production one).

    Thread safety for :meth:`refresh` is provided by a single lock
    guarding the read-modify-write of the cached token.
    """

    def __init__(self, *, base_token: str) -> None:
        self._base_token = base_token
        self._generation = 0
        self._lock = threading.Lock()

    def credentials(self) -> Credentials:
        with self._lock:
            return Credentials(token=f"{self._base_token}-gen{self._generation}")

    def refresh(self) -> Result[Credentials]:
        with self._lock:
            self._generation += 1
            return Result.ok(Credentials(token=f"{self._base_token}-gen{self._generation}"))
