"""``EventEnvelope`` and ``EventMetadata``: the stored/transmitted unit."""

from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Generic, TypeVar

from mineproductivity.core import BaseMetadata, BaseValueObject

from mineproductivity.events.base_event import BaseEvent
from mineproductivity.events.exceptions import EventValidationError
from mineproductivity.events.identifier import EventID
from mineproductivity.events.versioning import EventVersion

__all__ = ["EventEnvelope", "EventMetadata"]

TEvent = TypeVar("TEvent", bound=BaseEvent)


@dataclasses.dataclass(frozen=True, slots=True)
class EventMetadata(BaseMetadata):
    """Descriptive and provenance metadata attached to every envelope.

    Deliberately kept out of :class:`~mineproductivity.events.base_event.BaseEvent`'s
    own fields so an event's business payload never mixes with its
    trust/provenance data.
    """

    confidence: float = dataclasses.field(default=1.0, kw_only=True)
    source_system: str = dataclasses.field(default="unknown", kw_only=True)
    late_arrival: bool = dataclasses.field(default=False, kw_only=True)

    def validate(self) -> None:
        # NOTE: bare super() is unsafe here -- @dataclass(slots=True)
        # rebuilds the class object, which breaks the implicit __class__
        # cell a zero-arg super() relies on. Use the explicit two-arg form.
        super(EventMetadata, self).validate()
        if not (0.0 <= self.confidence <= 1.0):
            raise EventValidationError("EventMetadata.confidence must be in [0.0, 1.0]")


@dataclasses.dataclass(frozen=True, slots=True)
class EventEnvelope(BaseValueObject, Generic[TEvent]):
    """The stored/transmitted unit: identity + version + times + payload.

    Implements the three-time-concept temporal model mandated by the
    Learning & Benchmark Suite v1.0 ("Temporal Data Philosophy"):
    ``event_time_utc`` (when it happened -- the canonical calculation
    basis), ``processing_time_utc`` (when the source system processed it
    -- diagnostic only, never a calculation basis), and
    ``ingestion_time_utc`` (when this platform accepted it -- the audit
    trail). In normal operation ``event_time_utc <= processing_time_utc
    <= ingestion_time_utc``, and that ordering is enforced here.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> from mineproductivity.events.canonical import CycleEvent
    >>> now = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)
    >>> envelope = EventEnvelope(
    ...     event_id=EventID.generate(), version=EventVersion(),
    ...     payload=CycleEvent(
    ...         equipment_id="HT-214", shift_id="A-2026-06-25",
    ...         queue_min=1.5, spot_min=0.5, load_min=2.5,
    ...         haul_min=8.0, dump_min=1.0, return_min=6.0, payload_t=220.0,
    ...     ),
    ...     event_time_utc=now, processing_time_utc=now, ingestion_time_utc=now,
    ... )
    >>> envelope.payload.payload_t
    220.0
    """

    event_id: EventID
    version: EventVersion
    payload: TEvent
    event_time_utc: datetime
    processing_time_utc: datetime
    ingestion_time_utc: datetime
    metadata: EventMetadata = dataclasses.field(
        default_factory=lambda: EventMetadata(name="event"), kw_only=True
    )

    def validate(self) -> None:
        if not (self.event_time_utc <= self.processing_time_utc <= self.ingestion_time_utc):
            raise EventValidationError(
                "EventEnvelope violates event_time_utc <= processing_time_utc <= ingestion_time_utc"
            )
