"""The canonical event type catalogue.

Every concrete :class:`~mineproductivity.events.base_event.BaseEvent`
subclass shipped by this package lives here. New event types are added
by extension -- a new module in this subpackage -- never by editing an
existing one.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from mineproductivity.events.canonical.consumption_event import ConsumptionEvent, ResourceType
from mineproductivity.events.canonical.cycle_event import CycleEvent
from mineproductivity.events.canonical.delay_event import DelayEvent
from mineproductivity.events.canonical.maintenance_event import MaintenanceEvent
from mineproductivity.events.canonical.production_event import ProductionEvent
from mineproductivity.events.canonical.safety_event import (
    SafetyEvent,
    SafetyEventType,
    SafetySeverity,
)

if TYPE_CHECKING:
    from mineproductivity.events.base_event import BaseEvent

__all__ = [
    "ConsumptionEvent",
    "CycleEvent",
    "DelayEvent",
    "MaintenanceEvent",
    "ProductionEvent",
    "ResourceType",
    "SafetyEvent",
    "SafetyEventType",
    "SafetySeverity",
    "canonical_event_types",
]

_REGISTRY: Mapping[str, type["BaseEvent"]] = {
    CycleEvent.event_type_code: CycleEvent,
    DelayEvent.event_type_code: DelayEvent,
    MaintenanceEvent.event_type_code: MaintenanceEvent,
    ProductionEvent.event_type_code: ProductionEvent,
    ConsumptionEvent.event_type_code: ConsumptionEvent,
    SafetyEvent.event_type_code: SafetyEvent,
}


def canonical_event_types() -> Mapping[str, type["BaseEvent"]]:
    """Return the built-in ``event_type_code -> BaseEvent subclass`` mapping.

    A static, hand-populated mapping of this package's own six canonical
    types -- not the generic, plugin-discoverable registry the future
    Registry Framework will provide (see Documentation Governance Rule
    #005). Used internally by the serialization codecs to reconstruct a
    payload's concrete type from its ``event_type_code``.
    """
    return _REGISTRY
