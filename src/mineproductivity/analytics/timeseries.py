"""``TimeSeries``/``TimeSeriesPoint``: the one ordered-observations shape
every rolling/trend/distribution/benchmark computation in this package
operates over.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from datetime import datetime
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject
from mineproductivity.events import EventQuery, EventStore
from mineproductivity.kpis import KPIResult

from mineproductivity.analytics.exceptions import AnalyticsValidationError

__all__ = ["TimeSeries", "TimeSeriesPoint"]


@dataclasses.dataclass(frozen=True, slots=True)
class TimeSeriesPoint(BaseValueObject):
    """One observation: a timestamp and a value, plus the originating
    scope (mirrors ``KPIResult.scope``).

    Examples
    --------
    >>> TimeSeriesPoint(timestamp=datetime(2026, 1, 1), value=1200.0, scope={"pit": "north"}).value
    1200.0
    """

    timestamp: datetime
    value: float
    scope: Mapping[str, str] = dataclasses.field(default_factory=dict, kw_only=True)

    def _normalize(self) -> None:
        super(TimeSeriesPoint, self)._normalize()
        object.__setattr__(self, "scope", MappingProxyType(dict(self.scope)))


@dataclasses.dataclass(frozen=True, slots=True)
class TimeSeries(BaseValueObject):
    """An ordered (by timestamp) sequence of :class:`TimeSeriesPoint`\\ s
    -- the one series shape every statistical primitive, rolling
    function, and category model in this package operates on; there is
    no second, parallel "just a list of floats" convention anywhere in
    the public API.

    Examples
    --------
    >>> ts = TimeSeries(points=(
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, 2), value=2.0),
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, 1), value=1.0),
    ... ))
    >>> len(ts)
    2
    >>> ts.values()
    (1.0, 2.0)
    """

    points: tuple[TimeSeriesPoint, ...]

    def _normalize(self) -> None:
        super(TimeSeries, self)._normalize()
        object.__setattr__(
            self, "points", tuple(sorted(self.points, key=lambda point: point.timestamp))
        )

    def __len__(self) -> int:
        return len(self.points)

    def values(self) -> tuple[float, ...]:
        """The plain numeric values, in timestamp order -- the shape
        several statistical primitives (``percentile``, ``histogram``,
        ``distribution``) need, since they have no meaningful use for
        the timestamp dimension."""
        return tuple(point.value for point in self.points)

    @classmethod
    def from_kpi_results(
        cls, results: Sequence[KPIResult], *, timestamps: Sequence[datetime]
    ) -> TimeSeries:
        """Wrap a ``Sequence[KPIResult]`` into a ``TimeSeries``.
        ``KPIResult`` itself carries no timestamp field, so the caller
        assembling a ``TimeSeries`` from KPI results must supply
        ``timestamps`` alongside the ``results`` being wrapped, one per
        result, in the same order."""
        if len(results) != len(timestamps):
            raise AnalyticsValidationError(
                "from_kpi_results requires exactly one timestamp per KPIResult"
            )
        return cls(
            points=tuple(
                TimeSeriesPoint(timestamp=timestamp, value=result.value or 0.0, scope=result.scope)
                for result, timestamp in zip(results, timestamps, strict=True)
            )
        )

    @classmethod
    def from_event_query(
        cls, store: EventStore[Any], query: EventQuery, *, value_field: str
    ) -> TimeSeries:
        """Wrap the result of ``EventStore.query(query)`` into a
        ``TimeSeries``, reading ``value_field`` off each envelope's
        payload -- for direct statistical description of raw event data
        without going through a KPI at all. Requests only ``value_field``
        (plus the ``equipment_id``/``shift_id`` fields every
        ``BaseEvent`` already carries, used to populate each point's
        ``scope``), never the full envelope payload."""
        points: list[TimeSeriesPoint] = []
        for envelope in store.query(query):
            payload = envelope.payload
            value = getattr(payload, value_field)
            scope: dict[str, str] = {}
            equipment_id = getattr(payload, "equipment_id", None)
            if equipment_id is not None:
                scope["equipment_id"] = str(equipment_id)
            shift_id = getattr(payload, "shift_id", None)
            if shift_id is not None:
                scope["shift_id"] = str(shift_id)
            points.append(
                TimeSeriesPoint(timestamp=envelope.event_time_utc, value=float(value), scope=scope)
            )
        return cls(points=tuple(points))
