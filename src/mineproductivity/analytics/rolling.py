"""Rolling-window statistical functions over a ``TimeSeries`` (§20).

``rolling_mean``/``rolling_std`` are the two named, ready-made
reductions; ``rolling_apply`` is the escape hatch for any other
reduction a caller needs (e.g. a rolling percentile) without this
package growing an unbounded number of named ``rolling_*`` functions.
Both named reductions are thin wrappers around ``rolling_apply`` --
the sliding-window mechanics (grouping, absent-point handling) live in
exactly one place, and the arithmetic itself reuses
:mod:`mineproductivity.analytics.statistics`'s own ``_mean``/
``_population_stdev`` helpers rather than recomputing it.

The design spec's own prose says each function "returns a new
``TimeSeries`` of the same length as the input," then, in the same
sentence, that points below ``spec.min_periods`` are "represented as
absent points rather than a sentinel value." These two statements
cannot both be literally true: ``TimeSeriesPoint.value`` is a required
``float`` (no ``None``/``NaN`` variant exists anywhere in this
package), so representing a point as *absent* necessarily means the
output ``TimeSeries`` is shorter than the input whenever the leading
window has not yet filled -- not merely "same length with a sentinel
in some points," which would need a sentinel this package deliberately
does not have. This module implements the literal, twice-emphasized
"absent point" rule; "same length" is read as the loose case (an
already-full-window input, where every point does have enough trailing
history), not a separate, competing requirement.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from mineproductivity.analytics.statistics import _mean, _population_stdev
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint
from mineproductivity.analytics.windowing import RollingSpec

__all__ = ["rolling_apply", "rolling_mean", "rolling_std"]


def _window_values(
    points: tuple[TimeSeriesPoint, ...], index: int, spec: RollingSpec
) -> tuple[float, ...]:
    """The trailing window of values ending at ``points[index]``, per
    ``spec`` -- the last ``spec.periods`` observations for a count-based
    spec, or every observation within ``spec.time_window.span`` of
    ``points[index].timestamp`` for a time-based one. Returns an empty
    tuple if fewer than ``spec.min_periods`` observations are available,
    the caller's signal to omit this point entirely (§20's "absent
    point, not a sentinel value" rule)."""
    if spec.periods is not None:
        start = max(0, index - spec.periods + 1)
        window = points[start : index + 1]
    else:
        assert spec.time_window is not None  # RollingSpec.validate() already guarantees this
        span = spec.time_window.span
        current = points[index].timestamp
        window = tuple(point for point in points[: index + 1] if current - point.timestamp <= span)
    if len(window) < spec.min_periods:
        return ()
    return tuple(point.value for point in window)


def rolling_apply(
    series: TimeSeries, spec: RollingSpec, fn: Callable[[Sequence[float]], float]
) -> TimeSeries:
    """Apply ``fn`` over a sliding ``spec``-shaped window ending at each
    observation in ``series``, in timestamp order. Points before
    ``spec.min_periods`` observations are available are omitted from
    the result entirely -- represented as an absent point rather than a
    sentinel value (e.g. ``NaN``), so a caller cannot mistake "not yet
    enough data" for a computed zero (mirroring ``kpis.KPIResult``'s
    "never silently returns zero" rule).

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> points = tuple(
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, i, tzinfo=timezone.utc), value=float(i))
    ...     for i in range(1, 5)
    ... )
    >>> series = TimeSeries(points=points)
    >>> spec = RollingSpec(periods=2, min_periods=2)
    >>> result = rolling_apply(series, spec, sum)
    >>> len(result)
    3
    >>> result.values()
    (3.0, 5.0, 7.0)
    """
    points = series.points
    result_points = []
    for index in range(len(points)):
        window = _window_values(points, index, spec)
        if not window:
            continue
        current = points[index]
        result_points.append(
            TimeSeriesPoint(timestamp=current.timestamp, value=fn(window), scope=current.scope)
        )
    return TimeSeries(points=tuple(result_points))


def rolling_mean(series: TimeSeries, spec: RollingSpec) -> TimeSeries:
    """The rolling arithmetic mean over ``spec``'s sliding window.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> points = tuple(
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, i, tzinfo=timezone.utc), value=float(i))
    ...     for i in range(1, 5)
    ... )
    >>> rolling_mean(TimeSeries(points=points), RollingSpec(periods=2, min_periods=2)).values()
    (1.5, 2.5, 3.5)
    """
    return rolling_apply(series, spec, _mean)


def rolling_std(series: TimeSeries, spec: RollingSpec) -> TimeSeries:
    """The rolling population standard deviation (``ddof=0``, matching
    :func:`~mineproductivity.analytics.statistics.describe`'s own
    convention) over ``spec``'s sliding window.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> points = tuple(
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, i, tzinfo=timezone.utc), value=v)
    ...     for i, v in enumerate([1.0, 2.0, 3.0, 4.0], start=1)
    ... )
    >>> result = rolling_std(TimeSeries(points=points), RollingSpec(periods=2, min_periods=2))
    >>> result.values()
    (0.5, 0.5, 0.5)
    """

    def _std(values: Sequence[float]) -> float:
        return _population_stdev(values, mean=_mean(values))

    return rolling_apply(series, spec, _std)
