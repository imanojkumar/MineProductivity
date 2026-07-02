"""``AsOf`` and ``ReplayHandle``: the replay/time-travel contract."""

from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any, Generic, TypeVar

from mineproductivity.core import BaseValueObject

from mineproductivity.events.envelope import EventEnvelope
from mineproductivity.events.exceptions import EventValidationError

__all__ = ["AsOf", "ReplayHandle"]

TEnvelope = TypeVar("TEnvelope", bound=EventEnvelope[Any])


@dataclasses.dataclass(frozen=True, slots=True)
class AsOf(BaseValueObject):
    """A point-in-time (or named-scenario) reference for replay.

    Exactly one of ``utc``/``scenario`` is expected to be meaningful for
    a given replay call; both are optional so a future
    scenario/what-if-forking capability (Digital Twin) can extend this
    type's usage without a breaking change.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> AsOf(utc=datetime(2026, 6, 18, 6, tzinfo=timezone.utc)).utc.year
    2026
    """

    utc: datetime | None = dataclasses.field(default=None, kw_only=True)
    scenario: str | None = dataclasses.field(default=None, kw_only=True)

    def validate(self) -> None:
        if self.utc is None and self.scenario is None:
            raise EventValidationError("AsOf requires at least one of utc or scenario")


@dataclasses.dataclass(frozen=True, slots=True)
class ReplayHandle(BaseValueObject, Generic[TEnvelope]):
    """The materialized result of an :meth:`~mineproductivity.events.store.EventStore.replay` call:
    the highest-version envelope per ``EventID`` as of ``as_of``.

    Examples
    --------
    >>> handle: ReplayHandle[EventEnvelope] = ReplayHandle(as_of=AsOf(scenario="genesis"), envelopes=())
    >>> handle.envelopes
    ()
    """

    as_of: AsOf
    envelopes: tuple[TEnvelope, ...]

    def get(self, event_id: str) -> TEnvelope | None:
        """Return the envelope for ``event_id`` in this replayed state, or ``None``."""
        for envelope in self.envelopes:
            if envelope.event_id.value == event_id:
                return envelope
        return None
