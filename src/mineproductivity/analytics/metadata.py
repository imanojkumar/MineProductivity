"""``AnalyticsMetadata``: the minimal registration schema for a
discoverable :class:`~mineproductivity.analytics.abstractions.AnalyticsModel`.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseMetadata

from mineproductivity.analytics.exceptions import AnalyticsValidationError

__all__ = ["AnalyticsCategory", "AnalyticsMetadata"]


class AnalyticsCategory(Enum):
    """Closed enum -- adding a member is a governance-reviewed change,
    mirroring ``kpis.Aggregation``'s closed-enum rule."""

    TREND = "trend"
    BASELINE = "baseline"
    BENCHMARK = "benchmark"
    FORECASTING = "forecasting"
    ANOMALY = "anomaly"
    OUTLIER = "outlier"


@dataclasses.dataclass(frozen=True, slots=True)
class AnalyticsMetadata(BaseMetadata):
    """The minimal registration schema for a discoverable ``AnalyticsModel``
    -- deliberately not a copy of ``kpis.KPIMetadata``'s 29-field
    governance schema: an ``AnalyticsModel`` is a computational strategy,
    not an audited business metric.

    ``BaseMetadata.name`` has no default upstream and an ``AnalyticsModel``'s
    ``code`` (e.g. ``"TREND.Linear"``) already serves as its identifier, so
    ``name`` defaults to ``code`` (via :meth:`_normalize`) whenever a caller
    does not supply one explicitly.

    Examples
    --------
    >>> meta = AnalyticsMetadata(
    ...     code="TREND.Linear", category=AnalyticsCategory.TREND,
    ...     description="Ordinary least squares linear trend fit.",
    ... )
    >>> meta.code
    'TREND.Linear'
    >>> meta.name
    'TREND.Linear'
    >>> meta.min_observations
    2
    >>> AnalyticsMetadata(code="", category=AnalyticsCategory.TREND, description="x")
    Traceback (most recent call last):
        ...
    mineproductivity.analytics.exceptions.AnalyticsValidationError: AnalyticsMetadata.code must not be empty
    """

    name: str = dataclasses.field(default="", kw_only=True)
    code: str
    category: AnalyticsCategory = dataclasses.field(kw_only=True)
    description: str = dataclasses.field(kw_only=True)
    min_observations: int = dataclasses.field(default=2, kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)

    def _normalize(self) -> None:
        super(AnalyticsMetadata, self)._normalize()
        if not self.name:
            object.__setattr__(self, "name", self.code)

    def validate(self) -> None:
        if not self.code.strip():
            raise AnalyticsValidationError("AnalyticsMetadata.code must not be empty")
        super(AnalyticsMetadata, self).validate()
