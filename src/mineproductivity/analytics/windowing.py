"""``RollingSpec``: the one genuinely new windowing idea Analytics needs
beyond what ``kpis.Window``/``RollingWindow``/``CumulativeWindow`` already
express -- a count-based rolling window over the last *N* observations,
for irregularly-sampled series.
"""

from __future__ import annotations

import dataclasses

from mineproductivity.core import BaseValueObject
from mineproductivity.kpis import RollingWindow

from mineproductivity.analytics.exceptions import AnalyticsValidationError

__all__ = ["RollingSpec"]


@dataclasses.dataclass(frozen=True, slots=True)
class RollingSpec(BaseValueObject):
    """Either a time-based rolling window (delegates to
    :class:`~mineproductivity.kpis.RollingWindow` directly) or a
    count-based window over the last ``periods`` observations of a
    :class:`~mineproductivity.analytics.timeseries.TimeSeries`, regardless
    of how much wall-clock time they span -- which matters for
    irregularly-sampled series (e.g. shift-level ``KPIResult`` s, which do
    not arrive at a fixed cadence). Exactly one of ``time_window``/
    ``periods`` is set.

    Examples
    --------
    >>> RollingSpec(periods=7).periods
    7
    >>> RollingSpec(time_window=None, periods=None)
    Traceback (most recent call last):
        ...
    mineproductivity.analytics.exceptions.AnalyticsValidationError: RollingSpec requires exactly one of time_window or periods
    """

    time_window: RollingWindow | None = dataclasses.field(default=None, kw_only=True)
    periods: int | None = dataclasses.field(default=None, kw_only=True)
    min_periods: int = dataclasses.field(default=1, kw_only=True)

    def validate(self) -> None:
        if (self.time_window is None) == (self.periods is None):
            raise AnalyticsValidationError(
                "RollingSpec requires exactly one of time_window or periods"
            )
