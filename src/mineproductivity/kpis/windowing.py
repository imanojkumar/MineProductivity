"""``Window``/``RollingWindow``/``CumulativeWindow``: time-bounded scopes
for KPI computation.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta
from typing import Literal

from mineproductivity.core import BaseValueObject, ValidationError

__all__ = ["CumulativeWindow", "RollingWindow", "Window"]


@dataclasses.dataclass(frozen=True, slots=True)
class Window(BaseValueObject):
    """A time-bounded scope for KPI computation -- ``"shift"``, ``"day"``,
    ``"week"``, ``"month"``, or a custom ``[since_utc, until_utc)``.

    Examples
    --------
    >>> from datetime import timezone
    >>> window = Window(
    ...     kind="custom",
    ...     since_utc=datetime(2026, 6, 25, tzinfo=timezone.utc),
    ...     until_utc=datetime(2026, 6, 26, tzinfo=timezone.utc),
    ... )
    >>> window.kind
    'custom'
    """

    kind: Literal["shift", "day", "week", "month", "custom"]
    since_utc: datetime | None = dataclasses.field(default=None, kw_only=True)
    until_utc: datetime | None = dataclasses.field(default=None, kw_only=True)

    def validate(self) -> None:
        if self.kind == "custom" and (self.since_utc is None or self.until_utc is None):
            raise ValidationError("Window(kind='custom') requires both since_utc and until_utc")
        if (
            self.since_utc is not None
            and self.until_utc is not None
            and self.until_utc <= self.since_utc
        ):
            raise ValidationError("Window.until_utc must be after since_utc")


@dataclasses.dataclass(frozen=True, slots=True)
class RollingWindow(Window):
    """A moving window of fixed span, re-evaluated at each step (e.g. a
    7-day rolling TPH trend)."""

    span: timedelta = dataclasses.field(kw_only=True)
    step: timedelta = dataclasses.field(kw_only=True)

    def validate(self) -> None:
        super(RollingWindow, self).validate()
        if self.span <= timedelta(0):
            raise ValidationError("RollingWindow.span must be positive")
        if self.step <= timedelta(0):
            raise ValidationError("RollingWindow.step must be positive")


@dataclasses.dataclass(frozen=True, slots=True)
class CumulativeWindow(Window):
    """Accumulates from a fixed start (e.g. month-to-date production)."""

    start_utc: datetime = dataclasses.field(kw_only=True)
