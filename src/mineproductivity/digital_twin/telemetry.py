"""``TelemetryReading``: the twin-local shape continuous sensor-style
readings are adapted into (design spec §16).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
Deliberately **not** a second ingestion-transport abstraction competing
with ``connectors.FMSConnector`` -- spec 04's own vendor-neutrality
principle ("the only place in the codebase permitted to know that a
specific vendor or file format exists"), restated at this layer (design
spec §3.4, §16, ADR-0008's own recorded trade-off). Any telemetry
source is ingested through a ``connectors.FMSConnector``
implementation, normalized into ``events.BaseEvent`` subtypes, and
appended to ``events.EventStore``; this module only defines the shape a
reading takes once a concrete ``Twin._apply`` reads it out of an
already-ingested, already-event-sourced payload. Accordingly this
module imports nothing from ``connectors`` -- mechanically confirmed by
the package's forbidden-dependency test suite.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime

from mineproductivity.core import BaseValueObject

__all__ = ["TelemetryReading"]


@dataclasses.dataclass(frozen=True, slots=True)
class TelemetryReading(BaseValueObject):
    """The twin-local shape one already-ingested, already-event-sourced
    telemetry observation takes once ``_apply`` reads it out of an
    event's payload -- not a new ingestion contract (design spec §16).

    Examples
    --------
    >>> from datetime import timezone
    >>> reading = TelemetryReading(
    ...     sensor_id="CONV-7.belt_speed", value=3.1, unit="m/s",
    ...     observed_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
    ... )
    >>> reading.value, reading.unit
    (3.1, 'm/s')
    """

    sensor_id: str
    value: float
    unit: str
    observed_at: datetime
