"""Incremental computation (§29): the O(1)-update numerical primitive
``streaming.py`` (§27) and, optionally, ``batch.py`` (§28, for very
large row counts that should not be held in memory at once) use to
avoid an O(n) re-scan on every update.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``statistics.py``'s ``_mean``/``_population_variance``/``_population_stdev``
were the first candidates considered for computing ``IncrementalAccumulator``'s
running mean/standard-deviation -- they were **not appropriate**: every one
of them takes a materialized ``Sequence[float]`` and recomputes over the
*entire* sequence on every call. Calling any of them from ``update()``
would require (a) storing every observation ever seen, and (b)
re-scanning that whole history on every single new value -- exactly the
O(n) memory and O(n) per-update cost design spec §29 states this class
exists to avoid ("O(1) update per new observation, O(1) memory,
regardless of how many observations have been seen"). Reusing them here
would not merely be suboptimal, it would silently defeat the one
requirement this class has. Welford's online algorithm (Welford, 1962;
Knuth, TAOCP vol. 2, §4.2.2) is therefore implemented directly: a
well-known, deterministic, closed-form numerical method -- not a
statistical model and not machine learning, and not a duplication of
anything ``statistics.py`` already provides, since no O(1)-memory
streaming variant exists anywhere else in this package. This is
architecturally correct because it does not move any responsibility out
of ``statistics.py`` (batch descriptive statistics remains there,
untouched) -- it adds the one capability neither `statistics.py` nor
``rolling.py`` (windowed, not unbounded-streaming) can provide.

``running minimum``/``maximum`` are also tracked (trivially O(1) each)
so ``snapshot()`` can populate ``StatisticalSummary.minimum``/``.maximum``
honestly. ``percentiles`` cannot be computed this way at all -- exact
order statistics fundamentally require either materializing every
observation or an approximation/sketch algorithm this specification
does not call for -- so ``snapshot()`` always returns an empty
``percentiles`` mapping, a genuine, disclosed limitation of O(1)-memory
streaming computation, not an oversight.
"""

from __future__ import annotations

import math

from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.result import StatisticalSummary

__all__ = ["IncrementalAccumulator"]

_MODEL_CODE = "INCREMENTAL.Accumulator"


class IncrementalAccumulator:
    """Welford's online algorithm for numerically-stable, streaming mean
    and variance: O(1) update per new observation, O(1) memory,
    regardless of how many observations have been seen. This is the
    algorithmic primitive both ``StreamingAnalyticsSession`` (§27) and,
    optionally, ``BatchAnalyticsRunner`` (§28, for very large row counts
    that should not be held in memory at once) use to avoid an O(n)
    re-scan on every update. A well-known, deterministic, closed-form
    numerical method -- not a statistical model and not machine
    learning.

    **Thread safety.** Unlike every ``AnalyticsModel`` subclass (which
    MUST be stateless), ``IncrementalAccumulator`` is deliberately,
    visibly mutable -- ``update()`` changes internal running-mean/
    running-variance state. It is therefore **not** safe to share a
    single instance across threads without external synchronization.
    ``StreamingAnalyticsSession`` (§27) owns exactly one
    ``IncrementalAccumulator`` per tracked key and is responsible for
    serializing concurrent ``update()`` calls to the same key; this
    class does not synchronize itself.

    Examples
    --------
    >>> accumulator = IncrementalAccumulator()
    >>> for value in (2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0):
    ...     accumulator.update(value)
    >>> summary = accumulator.snapshot()
    >>> summary.n, summary.mean
    (8, 5.0)
    >>> round(summary.std, 4)
    2.0
    """

    def __init__(self) -> None:
        self._n = 0
        self._mean = 0.0
        self._m2 = 0.0
        self._minimum = math.inf
        self._maximum = -math.inf

    def update(self, value: float) -> None:
        """Fold ``value`` into the running mean/variance/min/max in O(1)
        time -- never re-reads any prior observation."""
        self._n += 1
        delta = value - self._mean
        self._mean += delta / self._n
        delta2 = value - self._mean
        self._m2 += delta * delta2
        if value < self._minimum:
            self._minimum = value
        if value > self._maximum:
            self._maximum = value

    def snapshot(self) -> StatisticalSummary:
        """The current ``StatisticalSummary``, computed in O(1) time
        from the running state -- never re-scans prior observations.
        ``percentiles`` is always empty (see module docstring).

        Raises
        ------
        AnalyticsValidationError
            If no observation has been recorded yet -- mirrors
            ``statistics.describe()``'s own "requires at least one
            observation" contract for the same degenerate input.
        """
        if self._n == 0:
            raise AnalyticsValidationError("snapshot() requires at least one observation")
        return StatisticalSummary(
            model_code=_MODEL_CODE,
            n=self._n,
            mean=self._mean,
            std=math.sqrt(self._m2 / self._n),
            minimum=self._minimum,
            maximum=self._maximum,
            percentiles={},
        )
