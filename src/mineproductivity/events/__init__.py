"""``mineproductivity.events`` -- the immutable, append-only event model
every derived state in the platform is computed from.

Implements Event Sourcing: the event log is the single system of record;
every other piece of derived state (a KPI value, a Digital Twin snapshot,
an analytics aggregate) is a pure function of the event log up to some
point in time.

``events`` depends on ``core`` and ``ontology`` (currently only
``ontology.DelayCategory`` -- see Documentation Governance Rule #005 and
``ontology/README.md``) and nothing else -- see ``README.md`` for the
full set of architectural rules this package must satisfy.

Everything documented here is part of the public API and can be imported
directly from ``mineproductivity.events``, e.g.::

    from mineproductivity.events import CycleEvent, EventEnvelope, EventID
"""

from __future__ import annotations

from mineproductivity.events.base_event import BaseEvent
from mineproductivity.events.bus import EventBus, Subscription
from mineproductivity.events.canonical import (
    ConsumptionEvent,
    CycleEvent,
    DelayEvent,
    MaintenanceEvent,
    ProductionEvent,
    ResourceType,
    SafetyEvent,
    SafetyEventType,
    SafetySeverity,
)
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.exceptions import (
    DuplicateEventError,
    EventNotFoundError,
    EventValidationError,
    EventVersionConflictError,
    ReplayError,
)
from mineproductivity.events.identifier import EventID
from mineproductivity.events.replay import AsOf, ReplayHandle
from mineproductivity.events.schema import EventSchema
from mineproductivity.events.snapshot import EventSnapshot
from mineproductivity.events.store import EventFilter, EventQuery, EventStore
from mineproductivity.events.validation import ConfidenceScore, EventValidator, ValidationOutcome
from mineproductivity.events.versioning import EventVersion

__all__ = [
    "AsOf",
    "BaseEvent",
    "ConfidenceScore",
    "ConsumptionEvent",
    "CycleEvent",
    "DelayEvent",
    "DuplicateEventError",
    "EventBus",
    "EventEnvelope",
    "EventFilter",
    "EventID",
    "EventMetadata",
    "EventNotFoundError",
    "EventQuery",
    "EventSchema",
    "EventSnapshot",
    "EventStore",
    "EventValidationError",
    "EventValidator",
    "EventVersion",
    "EventVersionConflictError",
    "MaintenanceEvent",
    "ProductionEvent",
    "ReplayError",
    "ReplayHandle",
    "ResourceType",
    "SafetyEvent",
    "SafetyEventType",
    "SafetySeverity",
    "Subscription",
    "ValidationOutcome",
]
