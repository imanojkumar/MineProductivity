"""Aggregation semantics enforcement -- the engine, not each ``_compute``,
decides how already-computed sub-period/sub-group results MAY be
combined, directly implementing the RATIO-never-averaged rule (design
spec AD-KP-02, §19, §29).
"""

from __future__ import annotations

from collections.abc import Sequence

from mineproductivity.kpis.exceptions import KPIAggregationError
from mineproductivity.kpis.metadata import Aggregation
from mineproductivity.kpis.result import KPIResult

__all__ = ["combine_results"]

_NEVER_COMBINE_ALREADY_COMPUTED = frozenset(
    {Aggregation.RATIO, Aggregation.AVERAGE, Aggregation.WEIGHTED_AVERAGE}
)


def combine_results(
    results: Sequence[KPIResult], aggregation: Aggregation, *, code: str, unit: str
) -> KPIResult:
    """Combine several already-computed :class:`KPIResult`\\ s into one,
    per ``aggregation``.

    ``RATIO``, ``AVERAGE``, and ``WEIGHTED_AVERAGE`` results MUST NOT be
    combined this way -- a mathematically correct combination requires
    the underlying raw numerator/denominator rows, not already-divided
    values (the "averaging shift TPHs" mistake this whole mechanism
    exists to make structurally impossible). Re-derive by calling
    :meth:`~mineproductivity.kpis.base_kpi.BaseKPI.compute` over the
    union of rows for the wider window instead.

    ``DERIVED`` KPIs are combined via
    :meth:`~mineproductivity.kpis.composite.CompositeKPI.combine`, not
    this function.

    Raises
    ------
    KPIAggregationError
        If ``aggregation`` is one of the kinds above.
    """
    if aggregation in _NEVER_COMBINE_ALREADY_COMPUTED:
        raise KPIAggregationError(
            f"{code}: {aggregation.value} KPIs cannot be combined by averaging "
            f"already-computed results -- re-derive from the union of raw rows instead"
        )
    if aggregation is Aggregation.DERIVED:
        raise KPIAggregationError(
            f"{code}: DERIVED KPIs are combined via CompositeKPI.combine, not combine_results"
        )

    total_n = sum(result.n for result in results)
    values = [result.value for result in results if result.value is not None]
    if not values:
        return KPIResult(
            code=code, value=None, unit=unit, n=total_n, warnings=("no combinable values",)
        )

    # ADDITIVE, CUMULATIVE, ROLLING: summed across the given results.
    return KPIResult(code=code, value=sum(values), unit=unit, n=total_n)
