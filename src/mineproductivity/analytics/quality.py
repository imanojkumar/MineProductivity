"""Data-quality scoring and missing-data handling (§25, §26).

``DataQualityScorer`` grades an arbitrary set of rows against a set of
required columns -- the Analytics-layer counterpart of
``kpis.BaseKPI._required_columns()``'s binary missing-column check
(kpis spec §10.3), generalized into a graded score. It never re-validates
what ``events.EventValidator``/``ontology.OntologyValidator`` already
validated; it scores what survived that validation against *this
analytical question's* required fields.

``MissingDataPolicy`` is a closed set of four deterministic, closed-form
policies -- none of them predicts or infers a missing value from other
fields (that would cross into modeling territory this package
deliberately avoids). ``DataQualityStage`` is the ``PipelineStage``
wrapper that composes ``DataQualityScorer`` (and a ``MissingDataPolicy``)
directly into an ``AnalyticsPipeline`` (§9), running before any
statistical or model stage.

Necessary, minimal, disclosed reconciliations
----------------------------------------------
``DataQualityScorer.score()`` is specified generically over
``Sequence[Mapping[str, Any]]`` rows -- it has no tie to ``TimeSeries``.
``DataQualityStage``, however, operates in the ``TimeSeries``-shaped
pipeline (§9), and ``TimeSeriesPoint`` exposes exactly one dict-shaped
surface (``scope: Mapping[str, str]``) plus one always-present numeric
field (``value: float``, never ``None`` per the "absent point, not
sentinel" convention already established by ``rolling.py``). This module
therefore builds each point's "row" as ``{**point.scope, "value":
point.value}``, with ``value`` treated as absent (``None``) exactly when
it is non-finite (``NaN``/``inf``) -- the one legitimate "missing-ish"
state a mandatory ``float`` field can actually be in. This is the same
"necessary, minimal, disclosed" bridging already applied to
``TimeSeries.from_kpi_results``' ``timestamps`` parameter and
``BandBenchmarkModel``'s constructor-supplied ``kpi_code``: it lets
``MissingDataPolicy.MEAN_FILL`` have one genuine, numerically meaningful
target (``value``) that reuses :func:`~mineproductivity.analytics.statistics._mean`
(no mean exists for the string-valued ``scope`` columns, so those degrade
to the same nearest-preceding-value fill as ``FORWARD_FILL``, disclosed
in :meth:`DataQualityStage._fill`'s own docstring).

``DataQualityStage`` gates a pipeline on ``min_score`` using the
already-established ``PipelineStage.process() -> TimeSeries |
AnalyticsResult`` union (design spec §9, reconciled in the Foundation
phase) and ``AnalyticsPipeline.run``'s already-existing rule that a
non-terminal stage yielding an ``AnalyticsResult`` short-circuits the
pipeline: below ``min_score``, this stage returns the ``DataQualityScore``
itself rather than inventing a new side-channel for propagating a
warning into a later stage's result -- ``TimeSeries``/``AnalyticsResult``
are frozen, locked Foundation types (Architecture Stability Rule) with no
field for "attached" metadata.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

from mineproductivity.core import BaseSpecification

from mineproductivity.analytics.abstractions import AnalyticsContext
from mineproductivity.analytics.pipeline import PipelineStage
from mineproductivity.analytics.result import AnalyticsResult, DataQualityScore
from mineproductivity.analytics.statistics import _mean
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

__all__ = ["DataQualityScorer", "DataQualityStage", "MissingDataPolicy"]

_MODEL_CODE = "QUALITY.DataQualityScorer"

#: Reserved row key referring to a ``TimeSeriesPoint``'s own ``value``
#: field -- see module docstring.
_VALUE_COLUMN = "value"


def _is_valid_value(value: object) -> bool:
    """Basic, generic sanity check -- present (not ``None``), finite if
    numeric, non-blank if a string. Deliberately not a domain-semantic
    check (kpis spec §10.3's own scope boundary): that already happened
    upstream, in ``events.EventValidator``/``ontology.OntologyValidator``.

    Safe to call with ``None`` directly (unlike a bare presence check),
    so both :class:`DataQualityScorer` (which pre-filters ``None`` for
    its own completeness/validity split) and :class:`DataQualityStage`
    (which uses this as its single "missing-for-cleaning-purposes"
    predicate) can share it without duplicating the null check."""
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, int | float):
        return math.isfinite(value)
    if isinstance(value, str):
        return bool(value.strip())
    return True


class _HasRequiredColumns(BaseSpecification[Mapping[str, Any]]):
    """Whether every required column is present *and* passes the same
    basic sanity check :class:`DataQualityScorer` uses for validity --
    the same reusable ``core.BaseSpecification`` primitive
    ``events.EventFilter`` already builds on (design spec §25's own
    dependency note), applied here to ``MissingDataPolicy.EXCLUDE``'s
    binary keep/drop decision (a blank ``scope`` value is exactly as
    unusable as an absent one)."""

    def __init__(self, required_columns: tuple[str, ...]) -> None:
        self._required_columns = required_columns

    def is_satisfied_by(self, candidate: Mapping[str, Any]) -> bool:
        return all(_is_valid_value(candidate.get(column)) for column in self._required_columns)


class MissingDataPolicy(Enum):
    """Closed enum, mirroring the closed-enum-change-requires-governance
    rule already established for ``kpis.Aggregation``. All four policies
    are deterministic, closed-form operations."""

    EXCLUDE = "exclude"
    FLAG_ONLY = "flag_only"
    FORWARD_FILL = "forward_fill"
    MEAN_FILL = "mean_fill"


class DataQualityScorer:
    """Produces a :class:`~mineproductivity.analytics.result.DataQualityScore`
    for a set of rows against a set of required columns -- the
    Analytics-layer counterpart of ``BaseKPI._required_columns()``'s
    missing-column check, generalized into a graded score rather than a
    binary present/absent warning.

    Examples
    --------
    >>> scorer = DataQualityScorer()
    >>> rows = [{"payload_t": 220.0, "operating_h": 8.0}, {"payload_t": None, "operating_h": 7.5}]
    >>> score = scorer.score(rows, required_columns=("payload_t", "operating_h"))
    >>> score.completeness
    0.75
    >>> score.overall_score
    0.75
    """

    def score(
        self, rows: Sequence[Mapping[str, Any]], *, required_columns: tuple[str, ...]
    ) -> DataQualityScore:
        if not required_columns:
            return DataQualityScore(
                model_code=_MODEL_CODE,
                completeness=1.0,
                validity=1.0,
                overall_score=1.0,
                reasons=("no required columns declared -- nothing to score",),
            )
        if not rows:
            return DataQualityScore(
                model_code=_MODEL_CODE,
                completeness=1.0,
                validity=1.0,
                overall_score=1.0,
                reasons=("no rows to score",),
            )

        total_slots = len(rows) * len(required_columns)
        present = 0
        valid = 0
        reasons: list[str] = []
        for index, row in enumerate(rows):
            for column in required_columns:
                value = row.get(column)
                if value is None:
                    reasons.append(f"row {index}: missing required column {column!r}")
                    continue
                present += 1
                if _is_valid_value(value):
                    valid += 1
                else:
                    reasons.append(f"row {index}: invalid value for required column {column!r}")

        completeness = present / total_slots
        validity = valid / present if present else 0.0
        return DataQualityScore(
            model_code=_MODEL_CODE,
            completeness=completeness,
            validity=validity,
            overall_score=completeness * validity,
            reasons=tuple(reasons),
        )


class DataQualityStage(PipelineStage):
    """The ``PipelineStage`` wrapper composing ``DataQualityScorer`` (and
    a ``MissingDataPolicy``) into an ``AnalyticsPipeline`` -- runs before
    any statistical or model stage.

    Below ``min_score``, :meth:`process` returns the computed
    ``DataQualityScore`` itself instead of a ``TimeSeries``, gating the
    pipeline via ``AnalyticsPipeline.run``'s existing non-terminal-result
    rule (see module docstring). At or above ``min_score``, it returns a
    ``TimeSeries`` cleaned per ``missing_data_policy``. The default
    ``min_score=0.0`` never gates (``overall_score`` is always ``>= 0``),
    matching design spec §9's own worked example, which passes
    ``DataQualityStage`` straight through to a following ``ModelStage``.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> from mineproductivity.events.store import _InMemoryEventStore
    >>> points = (
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1.0,
    ...                      scope={"pit": "north"}),
    ...     TimeSeriesPoint(timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc), value=2.0, scope={}),
    ... )
    >>> stage = DataQualityStage(required_columns=("pit",), missing_data_policy=MissingDataPolicy.FORWARD_FILL)
    >>> context = AnalyticsContext(event_store=_InMemoryEventStore())
    >>> cleaned = stage.process(TimeSeries(points=points), context=context)
    >>> isinstance(cleaned, TimeSeries)
    True
    >>> cleaned.points[1].scope["pit"]
    'north'
    """

    def __init__(
        self,
        *,
        required_columns: tuple[str, ...],
        missing_data_policy: MissingDataPolicy = MissingDataPolicy.FLAG_ONLY,
        min_score: float = 0.0,
    ) -> None:
        self._required_columns = required_columns
        self._missing_data_policy = missing_data_policy
        self._min_score = min_score
        self._scorer = DataQualityScorer()
        self._spec = _HasRequiredColumns(required_columns)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(required_columns={self._required_columns!r}, "
            f"missing_data_policy={self._missing_data_policy!r}, min_score={self._min_score!r})"
        )

    def process(
        self, series: TimeSeries, *, context: AnalyticsContext
    ) -> TimeSeries | AnalyticsResult:
        rows = [self._row_for(point) for point in series.points]
        score = self._scorer.score(rows, required_columns=self._required_columns)
        if score.overall_score < self._min_score:
            return score
        return self._apply_policy(series)

    def _row_for(self, point: TimeSeriesPoint) -> dict[str, Any]:
        row: dict[str, Any] = dict(point.scope)
        row[_VALUE_COLUMN] = point.value if math.isfinite(point.value) else None
        return row

    def _apply_policy(self, series: TimeSeries) -> TimeSeries:
        if self._missing_data_policy is MissingDataPolicy.FLAG_ONLY:
            return series
        if self._missing_data_policy is MissingDataPolicy.EXCLUDE:
            kept = tuple(
                point for point in series.points if self._spec.is_satisfied_by(self._row_for(point))
            )
            return TimeSeries(points=kept)
        fallback = (
            self._series_mean(series)
            if self._missing_data_policy is MissingDataPolicy.MEAN_FILL
            else None
        )
        return TimeSeries(points=self._fill(series, fallback=fallback))

    def _series_mean(self, series: TimeSeries) -> float | None:
        finite_values = tuple(value for value in series.values() if math.isfinite(value))
        return _mean(finite_values) if finite_values else None

    def _fill(self, series: TimeSeries, *, fallback: float | None) -> tuple[TimeSeriesPoint, ...]:
        """Single-pass fill shared by ``FORWARD_FILL`` (``fallback=None``,
        so a non-finite ``value`` is replaced by the nearest preceding
        finite ``value``) and ``MEAN_FILL`` (``fallback`` pre-computed as
        the series' own mean of finite values). A missing *or* blank
        required ``scope`` column is filled from the nearest preceding
        point with a valid one (``last_scope`` only ever records valid
        values, so a blank never poisons a later point's fill) --
        ``MEAN_FILL`` has no numeric mean for a string-valued ``scope``
        column, so it degrades to the same nearest-preceding-value
        behavior as ``FORWARD_FILL`` there, disclosed in the module
        docstring."""
        last_scope: dict[str, str] = {}
        last_value: float | None = None
        filled: list[TimeSeriesPoint] = []
        for point in series.points:
            new_scope = dict(point.scope)
            new_value = point.value
            if _VALUE_COLUMN in self._required_columns and not math.isfinite(point.value):
                substitute = fallback if fallback is not None else last_value
                if substitute is not None:
                    new_value = substitute
            for column in self._required_columns:
                if (
                    column != _VALUE_COLUMN
                    and not _is_valid_value(new_scope.get(column))
                    and column in last_scope
                ):
                    new_scope[column] = last_scope[column]
            for key, scope_value in new_scope.items():
                if _is_valid_value(scope_value):
                    last_scope[key] = scope_value
            if math.isfinite(new_value):
                last_value = new_value
            filled.append(
                TimeSeriesPoint(timestamp=point.timestamp, value=new_value, scope=new_scope)
            )
        return tuple(filled)
