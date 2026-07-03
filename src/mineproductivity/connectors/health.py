"""``HealthStatus``/``ConnectorHealth``: the externally-observable health
state every :class:`~mineproductivity.connectors.base.FMSConnector`
reports.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from enum import Enum

from mineproductivity.core import BaseValueObject

__all__ = ["ConnectorHealth", "HealthStatus"]


class HealthStatus(Enum):
    """The four health states a connector can report, updated after every
    pull attempt (design spec §12)."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclasses.dataclass(frozen=True, slots=True)
class ConnectorHealth(BaseValueObject):
    """A point-in-time snapshot of one connector's health."""

    status: HealthStatus
    last_successful_pull_utc: datetime | None = dataclasses.field(default=None, kw_only=True)
    detail: str = dataclasses.field(default="", kw_only=True)
