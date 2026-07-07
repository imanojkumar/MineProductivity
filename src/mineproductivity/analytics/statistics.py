"""Stateless, deterministic statistical primitives -- the "verbs" every
concrete ``AnalyticsModel`` calls internally (§17, §21-24). ``core`` only;
no third-party numerical dependency (numpy/scipy) is required or used
(design spec §36).
"""

from __future__ import annotations

import bisect
import math
from collections.abc import Sequence
from statistics import NormalDist
from typing import Literal

from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.result import (
    ConfidenceInterval,
    DistributionSummary,
    Histogram,
    StatisticalSummary,
)
from mineproductivity.analytics.timeseries import TimeSeries

__all__ = ["confidence_interval", "describe", "distribution", "histogram", "percentile"]

#: The percentile keys every ``StatisticalSummary``/``DistributionSummary``
#: reports, matching the design spec's own worked example (§17: "e.g.
#: {50: ..., 90: ..., 99: ...}") -- ``describe``/``distribution`` take no
#: percentile-selection parameter, so this fixed set is the one, stable
#: default rather than an arbitrary per-call choice.
_DEFAULT_PERCENTILES: tuple[int, ...] = (50, 90, 99)


def _require_non_empty(values: Sequence[float], *, caller: str) -> None:
    if not values:
        raise AnalyticsValidationError(f"{caller} requires at least one observation")


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _population_variance(values: Sequence[float], *, mean: float) -> float:
    return sum((value - mean) ** 2 for value in values) / len(values)


def _population_stdev(values: Sequence[float], *, mean: float) -> float:
    return math.sqrt(_population_variance(values, mean=mean))


def _sample_stdev(values: Sequence[float], *, mean: float) -> float:
    """Sample standard deviation (Bessel's correction, ``ddof=1``) --
    distinct from :func:`_population_stdev`; used only by
    :func:`confidence_interval`, where estimating the standard error of
    the mean is the standard convention (see that function's own
    docstring)."""
    n = len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (n - 1))


def _skewness(values: Sequence[float], *, mean: float, std: float) -> float:
    """The Fisher-Pearson moment coefficient of skewness (population-based,
    matching this module's population-``std`` convention): 0.0 for a
    symmetric distribution (and, degenerately, for zero-variance data,
    where shape is undefined rather than divided-by-zero)."""
    if std == 0.0:
        return 0.0
    n = len(values)
    third_moment = sum((value - mean) ** 3 for value in values) / n
    return third_moment / std**3


def _kurtosis(values: Sequence[float], *, mean: float, std: float) -> float:
    """Excess kurtosis (Fisher's convention: 0.0 for a normal distribution),
    matching pandas'/SciPy's default -- 0.0, not 3.0, for zero-variance
    data, for the same degenerate reason as :func:`_skewness`."""
    if std == 0.0:
        return 0.0
    n = len(values)
    fourth_moment = sum((value - mean) ** 4 for value in values) / n
    return fourth_moment / std**4 - 3.0


def percentile(values: Sequence[float], q: float) -> float:
    """Linear-interpolation percentile (the same convention NumPy's
    default ``numpy.percentile`` and pandas' default ``.quantile`` use),
    named explicitly rather than left to a caller to discover which
    interpolation convention a third-party library defaults to.

    ``q`` is on the 0-100 percentile scale (``q=50`` is the median),
    matching ``StatisticalSummary.percentiles``' own integer keys.

    Examples
    --------
    >>> percentile([1.0, 2.0, 3.0, 4.0], 50)
    2.5
    >>> percentile([1.0, 2.0, 3.0, 4.0], 0)
    1.0
    >>> percentile([1.0, 2.0, 3.0, 4.0], 100)
    4.0
    """
    _require_non_empty(values, caller="percentile()")
    if not (0.0 <= q <= 100.0):
        raise AnalyticsValidationError("percentile() requires 0 <= q <= 100")
    ordered = sorted(values)
    n = len(ordered)
    if n == 1:
        return ordered[0]
    index = (q / 100.0) * (n - 1)
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[int(index)]
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def describe(series: TimeSeries) -> StatisticalSummary:
    """The Analytics-layer equivalent of a spreadsheet's "Descriptive
    Statistics" tool, over any ``TimeSeries`` -- raw event values or
    ``KPIResult`` series alike.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> from mineproductivity.analytics.timeseries import TimeSeriesPoint
    >>> series = TimeSeries(points=(
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1.0),
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc), value=2.0),
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, 3, tzinfo=timezone.utc), value=3.0),
    ... ))
    >>> summary = describe(series)
    >>> summary.n, summary.mean
    (3, 2.0)
    """
    values = series.values()
    _require_non_empty(values, caller="describe()")
    mean_ = _mean(values)
    return StatisticalSummary(
        n=len(values),
        mean=mean_,
        std=_population_stdev(values, mean=mean_),
        minimum=min(values),
        maximum=max(values),
        percentiles={q: percentile(values, q) for q in _DEFAULT_PERCENTILES},
    )


def histogram(values: Sequence[float], *, bins: int | Sequence[float] = 10) -> Histogram:
    """``bins`` as an int requests that many equal-width bins spanning
    ``[min(values), max(values)]``; ``bins`` as a ``Sequence[float]``
    requests caller-supplied edges (e.g. the site's own published
    benchmark bands, §13, when a histogram is being drawn against them).

    Examples
    --------
    >>> histogram([1.0, 2.0, 3.0, 4.0], bins=2).counts
    (2, 2)
    >>> histogram([1.0, 2.0, 3.0], bins=[1.0, 2.0, 3.0]).counts
    (1, 2)
    """
    _require_non_empty(values, caller="histogram()")
    if isinstance(bins, int):
        if bins < 1:
            raise AnalyticsValidationError("histogram() requires bins >= 1")
        low, high = min(values), max(values)
        width = (high - low) / bins
        edges = tuple(low + i * width for i in range(bins)) + (high,)
    else:
        edges = tuple(bins)
        if len(edges) < 2:
            raise AnalyticsValidationError("histogram() requires at least 2 bin edges")
        if any(edges[i] > edges[i + 1] for i in range(len(edges) - 1)):
            raise AnalyticsValidationError("histogram() bin edges must be non-decreasing")

    counts = [0] * (len(edges) - 1)
    last_bin = len(counts) - 1
    for value in values:
        if value <= edges[0]:
            counts[0] += 1
        elif value >= edges[-1]:
            counts[last_bin] += 1
        else:
            counts[bisect.bisect_right(edges, value) - 1] += 1
    return Histogram(bin_edges=edges, counts=tuple(counts))


def distribution(values: Sequence[float]) -> DistributionSummary:
    """A superset of :func:`describe` that adds shape descriptors
    (``skewness``, ``kurtosis``) that ``describe()`` deliberately omits,
    keeping ``describe()`` cheap and ``distribution()`` the more
    complete, slightly more expensive call for callers who explicitly
    need distribution shape.

    Examples
    --------
    >>> d = distribution([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> round(d.skewness, 4)
    0.0
    """
    _require_non_empty(values, caller="distribution()")
    mean_ = _mean(values)
    std_ = _population_stdev(values, mean=mean_)
    return DistributionSummary(
        mean=mean_,
        std=std_,
        skewness=_skewness(values, mean=mean_, std=std_),
        kurtosis=_kurtosis(values, mean=mean_, std=std_),
        percentiles={q: percentile(values, q) for q in _DEFAULT_PERCENTILES},
    )


def _student_t_quantile(p: float, df: float) -> float:
    """The Student's t distribution's inverse CDF (two-sided critical
    value support), via the exact relationship to the regularized
    incomplete beta function ``I_x(df/2, 1/2)`` and bisection -- pure
    Python, no third-party dependency, verified against published
    t-table reference values (e.g. ``t(0.975, df=10) = 2.228``) in this
    module's test suite."""

    def log_gamma(x: float) -> float:
        """Lanczos approximation to ``ln(Gamma(x))``.

        Only ever called with ``x >= 0.5`` in this module (``a=df/2.0``
        with ``df >= 1`` since :func:`confidence_interval` already
        requires at least 2 observations, and ``b=0.5``) -- the
        Lanczos formula's reflection-formula branch for ``x < 0.5`` is
        therefore deliberately omitted rather than shipped as dead,
        untestable-from-the-public-API code.
        """
        g = 7
        coefficients = (
            0.99999999999980993,
            676.5203681218851,
            -1259.1392167224028,
            771.32342877765313,
            -176.61502916214059,
            12.507343278686905,
            -0.13857109526572012,
            9.9843695780195716e-6,
            1.5056327351493116e-7,
        )
        x -= 1.0
        a = coefficients[0]
        t = x + g + 0.5
        for i in range(1, g + 2):
            a += coefficients[i] / (x + i)
        return 0.5 * math.log(2.0 * math.pi) + (x + 0.5) * math.log(t) - t + math.log(a)

    def log_beta(a: float, b: float) -> float:
        return log_gamma(a) + log_gamma(b) - log_gamma(a + b)

    def beta_continued_fraction(x: float, a: float, b: float) -> float:
        max_iter, eps, fpmin = 200, 1e-14, 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        d = 1.0 - qab * x / qap
        d = fpmin if abs(d) < fpmin else d
        d = 1.0 / d
        h = d
        for m in range(1, max_iter + 1):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d
            d = fpmin if abs(d) < fpmin else d
            c = 1.0 + aa / c
            c = fpmin if abs(c) < fpmin else c
            d = 1.0 / d
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d
            d = fpmin if abs(d) < fpmin else d
            c = 1.0 + aa / c
            c = fpmin if abs(c) < fpmin else c
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < eps:
                break
        return h

    def regularized_incomplete_beta(x: float, a: float, b: float) -> float:
        if x <= 0.0:  # pragma: no cover - defensive; x=df/(df+t*t) with df>0 is always > 0
            return 0.0
        if x >= 1.0:
            return 1.0
        front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - log_beta(a, b))
        if x < (a + 1.0) / (a + b + 2.0):
            return front * beta_continued_fraction(x, a, b) / a
        return 1.0 - front * beta_continued_fraction(1.0 - x, b, a) / b

    def student_t_cdf(t: float) -> float:
        x = df / (df + t * t)
        ib = regularized_incomplete_beta(x, df / 2.0, 0.5)
        return 1.0 - 0.5 * ib if t > 0.0 else 0.5 * ib

    lo, hi = -1000.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if student_t_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def confidence_interval(
    values: Sequence[float], *, confidence: float = 0.95, method: Literal["normal", "t"] = "t"
) -> ConfidenceInterval:
    """Closed-form only: normal-approximation or Student's t-interval
    around the sample mean. Resampling-based methods (e.g. bootstrap)
    are a documented future extension (§37), not shipped now, to keep
    the reference implementation's dependency footprint and determinism
    guarantees simple.

    Both methods use the *sample* standard deviation (Bessel's
    correction, ``ddof=1``) to estimate the standard error, the standard
    convention for confidence intervals -- distinct from, and not to be
    confused with, :func:`describe`/:func:`distribution`'s own
    population-``std`` (``ddof=0``) convention for plain descriptive
    statistics. Requires at least 2 observations for either method: a
    single observation cannot support a sample-based standard-error
    estimate.

    Examples
    --------
    >>> ci = confidence_interval([1.0, 2.0, 3.0, 4.0, 5.0], confidence=0.95, method="normal")
    >>> ci.method
    'normal'
    >>> ci.lower < 3.0 < ci.upper
    True
    """
    _require_non_empty(values, caller="confidence_interval()")
    if not (0.0 < confidence < 1.0):
        raise AnalyticsValidationError("confidence_interval() requires 0 < confidence < 1")
    n = len(values)
    if n < 2:
        raise AnalyticsValidationError("confidence_interval() requires at least 2 observations")
    mean_ = _mean(values)
    sample_std = _sample_stdev(values, mean=mean_)
    if method == "t":
        critical_value = _student_t_quantile((1.0 + confidence) / 2.0, df=n - 1)
    else:
        critical_value = NormalDist().inv_cdf((1.0 + confidence) / 2.0)
    margin = critical_value * sample_std / math.sqrt(n)
    return ConfidenceInterval(
        lower=mean_ - margin, upper=mean_ + margin, confidence=confidence, method=method
    )
