"""Classify a ``KPIResult`` against its own ``KPIMetadata.benchmark_bands``
(§13). Distinct from ``baseline.py`` (§15), which compares against a
self-referential historical norm: a ``BenchmarkResult`` answers "how does
this compare to the published band," never "is this normal for this
asset, historically."

``KPIMetadata.benchmark_bands`` (kpis spec §10.1 field 19) is a
``Mapping[str, str]`` from a band name (e.g. ``"top_quartile"``) to a
comparison expression (e.g. ``">1200"``) -- the one real, tested example
in this codebase (``tests/unit/kpis/test_metadata.py``) is
``{"good": ">0.9"}``. No second, parallel band schema is introduced here;
every classification traces back to an existing ``benchmark_bands`` entry
read via ``Registry.metadata_for``.

``KPIMetadata`` carries no numeric ``target`` field for
``Direction.TARGET_IS_BEST`` KPIs (only ``benchmark_bands``/``direction``
exist). This module's necessary, minimal, disclosed reconciliation:
a ``TARGET_IS_BEST`` KPI's ``benchmark_bands`` MUST include a reserved
``"target"`` entry holding the bare numeric target (e.g. ``{"target":
"1200", "near_target": "<=50", "off_target": ">50"}``); every other entry
is then classified against *distance from that target* rather than raw
magnitude, exactly as design spec §13 describes.
"""

from __future__ import annotations

import operator
import re
from abc import ABC
from collections.abc import Callable, Mapping
from typing import ClassVar, cast

from mineproductivity.kpis import REGISTRY, BaseKPI, Direction, KPIMetadata, KPIResult
from mineproductivity.registry import Registry

from mineproductivity.analytics._registry import register
from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.result import AnalyticsResult, BenchmarkResult
from mineproductivity.analytics.timeseries import TimeSeries

__all__ = ["BandBenchmarkModel", "BenchmarkModel"]

#: Matches a ``benchmark_bands`` comparison expression, e.g. ``">0.9"``,
#: ``"<=100"``, ``"==0"`` -- the one real, tested band-value shape in this
#: codebase.
_BAND_PATTERN = re.compile(r"^\s*(>=|<=|==|>|<)\s*(-?\d+(?:\.\d+)?)\s*$")

_COMPARATORS: Mapping[str, Callable[[float, float], bool]] = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
}

#: ``Direction.LOWER_IS_BETTER`` inverts each band's authored comparison
#: (design spec §13) rather than requiring every KPI author to re-author
#: their bands' operators per direction.
_INVERTED_OPERATOR = {">": "<", "<": ">", ">=": "<=", "<=": ">=", "==": "=="}

#: Reserved ``benchmark_bands`` key holding a ``TARGET_IS_BEST`` KPI's
#: numeric target -- see module docstring.
_TARGET_KEY = "target"


class BenchmarkModel(AnalyticsModel, ABC):
    """Category base for benchmarking strategies -- classify a value
    against an externally published target/band, distinct from
    ``BaselineModel`` (§15)'s self-referential historical norm.
    """


@register
class BandBenchmarkModel(BenchmarkModel):
    """The default, concrete benchmarking strategy: classify a
    ``KPIResult``'s value against its own ``KPIMetadata.benchmark_bands``,
    respecting ``KPIMetadata.direction`` -- ``HIGHER_IS_BETTER`` and
    ``LOWER_IS_BETTER`` invert the comparison; ``TARGET_IS_BEST`` compares
    distance-from-target rather than raw magnitude (design spec §13).

    Registered into ``analytics.REGISTRY`` at import time (§32-33),
    mirroring how ``kpis.standard_library`` self-registers.

    :meth:`benchmark` is the primary entry point, matching the design
    spec's own signature exactly: it operates on a single ``KPIResult``
    plus an explicit ``registry``, not a ``TimeSeries``, since benchmarking
    is a point-in-time classification rather than a series computation.
    ``_analyze`` (the ``AnalyticsModel`` contract every concrete model
    must satisfy) is a thin adapter over the same classification logic:
    it benchmarks the series' most recent point against the KPI code this
    instance was constructed with, via the module-level ``kpis.REGISTRY``
    -- a bare ``TimeSeries`` carries no KPI code of its own (``scope``
    only), so the constructor must supply the one otherwise-unavailable
    piece of information, the same "necessary, minimal, disclosed"
    correction already applied to ``TimeSeries.from_kpi_results``'
    ``timestamps`` parameter and ``AggregationEngine.reduce_kpi_results``'
    ``window`` parameter in earlier Analytics phases.

    Examples
    --------
    >>> from mineproductivity.registry import Registry
    >>> registry: Registry[str, type] = Registry(name="doctest")
    >>> meta = KPIMetadata(
    ...     name="PROD.TPH", code="PROD.TPH", official_name="Tonnes Per Hour",
    ...     business_purpose="x", operational_question="x", business_meaning="x",
    ...     formula="x", unit="t/h", dimensions=("Shift",), required_events=("CYCLE",),
    ...     direction=Direction.HIGHER_IS_BETTER,
    ...     benchmark_bands={"top_quartile": ">1200", "below_average": "<1000"},
    ... )
    >>> _ = registry.register("PROD.TPH", object, metadata=meta)
    >>> model = BandBenchmarkModel(kpi_code="PROD.TPH")
    >>> result = KPIResult(code="PROD.TPH", value=1250.0, unit="t/h")
    >>> classified = model.benchmark(result, registry=registry)
    >>> classified.band
    'top_quartile'
    """

    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="BENCHMARK.Band",
        category=AnalyticsCategory.BENCHMARK,
        description="Classify a KPIResult's value against its own KPIMetadata.benchmark_bands.",
        min_observations=1,
    )

    def __init__(self, *, kpi_code: str) -> None:
        self._kpi_code = kpi_code

    def __repr__(self) -> str:
        return f"{type(self).__name__}(kpi_code={self._kpi_code!r})"

    def benchmark(
        self, result: KPIResult, *, registry: Registry[str, type[BaseKPI]]
    ) -> AnalyticsResult:
        """Classify ``result`` against its own registered
        ``KPIMetadata.benchmark_bands``/``direction``.

        Returns a plain ``AnalyticsResult`` (never raising) rather than
        the more specific ``BenchmarkResult`` when classification is
        genuinely impossible -- no registered metadata for ``result.code``,
        or ``result.value is None`` (legitimately uncomputable, kpis spec
        §10.1) -- since ``BenchmarkResult.value``/``.direction`` are
        mandatory fields with no honest value to put there. This is the
        same "qualify, don't coerce" widening ``AnalyticsModel.analyze``
        itself performs for insufficient-data series.
        """
        metadata_lookup = registry.metadata_for(result.code)
        if metadata_lookup.is_nothing:
            return AnalyticsResult(
                model_code=self.meta.code,
                warnings=(f"no registered KPI metadata for code {result.code!r}",),
            )
        metadata = cast(KPIMetadata, metadata_lookup.unwrap())
        return self._classify(result, metadata)

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        last = series.points[-1]
        result = KPIResult(code=self._kpi_code, value=last.value, unit="", scope=last.scope)
        return self.benchmark(result, registry=REGISTRY)

    def _classify(self, result: KPIResult, metadata: KPIMetadata) -> AnalyticsResult:
        if result.value is None:
            return AnalyticsResult(
                model_code=self.meta.code,
                warnings=(f"KPIResult {result.code!r} has no computable value to benchmark",),
            )
        if not metadata.benchmark_bands:
            return self._build_result(
                result,
                metadata,
                value=result.value,
                band="",
                unmatched_warning=f"no benchmark bands defined for KPI {result.code!r}",
            )
        if metadata.direction is Direction.TARGET_IS_BEST:
            return self._classify_target(result, metadata)
        return self._classify_band(result, metadata)

    def _classify_band(self, result: KPIResult, metadata: KPIMetadata) -> BenchmarkResult:
        value = cast(float, result.value)
        invert = metadata.direction is Direction.LOWER_IS_BETTER
        band = self._best_match(value, metadata.benchmark_bands, invert=invert)
        return self._build_result(
            result,
            metadata,
            value=value,
            band=band,
            unmatched_warning=f"value {value!r} does not fall within any defined benchmark band",
        )

    def _classify_target(self, result: KPIResult, metadata: KPIMetadata) -> AnalyticsResult:
        bands = metadata.benchmark_bands
        target = self._parse_number(bands.get(_TARGET_KEY, ""))
        if target is None:
            return AnalyticsResult(
                model_code=self.meta.code,
                warnings=(
                    f"TARGET_IS_BEST KPI {result.code!r} has no numeric "
                    f"{_TARGET_KEY!r} entry in benchmark_bands",
                ),
            )
        value = cast(float, result.value)
        distance = abs(value - target)
        distance_bands = {name: expr for name, expr in bands.items() if name != _TARGET_KEY}
        band = self._best_match(distance, distance_bands, invert=False)
        return self._build_result(
            result,
            metadata,
            value=value,
            band=band,
            unmatched_warning=f"distance-from-target {distance!r} does not fall within any defined band",
        )

    def _build_result(
        self,
        result: KPIResult,
        metadata: KPIMetadata,
        *,
        value: float,
        band: str,
        unmatched_warning: str,
    ) -> BenchmarkResult:
        return BenchmarkResult(
            model_code=self.meta.code,
            warnings=() if band else (unmatched_warning,),
            kpi_code=result.code,
            value=value,
            band=band,
            direction=metadata.direction,
        )

    @staticmethod
    def _best_match(value: float, bands: Mapping[str, str], *, invert: bool) -> str:
        """Return the name of the first band (in ``bands``' own iteration
        order) whose parsed comparison ``value`` satisfies, or ``""`` if
        none matches. Malformed expressions are skipped, never raised
        (``benchmark_bands`` is caller-authored metadata, not validated
        input). For overlapping bands, the first-authored match wins --
        a well-formed ``benchmark_bands`` mapping is expected to define
        disjoint ranges, so this only matters as a deterministic
        tie-break for a misauthored overlap."""
        for name, expression in bands.items():
            match = _BAND_PATTERN.match(expression)
            if match is None:
                continue
            op_symbol, threshold_text = match.group(1), match.group(2)
            if invert:
                op_symbol = _INVERTED_OPERATOR[op_symbol]
            if _COMPARATORS[op_symbol](value, float(threshold_text)):
                return name
        return ""

    @staticmethod
    def _parse_number(text: str) -> float | None:
        try:
            return float(text)
        except ValueError:
            return None
