"""``BaseEvent``: the abstract root of every canonical event payload type."""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from typing import ClassVar

from mineproductivity.core import BaseValueObject

__all__ = ["BaseEvent"]


@dataclasses.dataclass(frozen=True, slots=True)
class BaseEvent(BaseValueObject, ABC):
    """Abstract root of every canonical event payload type.

    A ``BaseEvent`` carries only the business-domain fact; identity,
    version, and the three timestamps live one level up, on
    :class:`~mineproductivity.events.envelope.EventEnvelope`. This
    separation is deliberate: two envelopes with different ``event_id``\\ s
    can legitimately wrap payload instances that are field-for-field
    identical (e.g. two trucks completing structurally similar cycles) --
    ``BaseEvent`` equality is a :class:`~mineproductivity.core.value_object.BaseValueObject`\\ 's
    field equality, while :class:`~mineproductivity.events.envelope.EventEnvelope`
    equality is additionally scoped by ``EventID``.

    Every concrete event type declares ``equipment_id``/``shift_id``
    (references into the future Ontology Framework, held as plain
    strings -- see :class:`~mineproductivity.events.base_event.BaseEvent`'s
    module docstring and Documentation Governance Rule #005) and a class
    -level ``event_type_code`` registry key.
    """

    equipment_id: str
    shift_id: str

    event_type_code: ClassVar[str]

    @abstractmethod
    def duration_h(self) -> float:
        """Return this event's duration in hours, however duration is
        defined for the concrete type (a cycle's total time, a delay's
        span, an instantaneous reading's ``0.0``, ...)."""
