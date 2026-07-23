"""Extension point: implement the interface-only ForecastingModel.

analytics ships ZERO forecasters (ADR-0006) -- choosing an algorithm
(exponential smoothing, ARIMA, ...) is a modelling decision the package
deliberately refuses to make for you. Here a naive linear-drift forecaster
implements the stable contract and registers, producing a ForecastResult:
`horizon` future points, each a point estimate plus an uncertainty band.

Run: python examples/analytics/03_plugin_forecasting_model.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import fmean, pstdev
from typing import ClassVar

from mineproductivity.analytics import (
    REGISTRY,
    AnalyticsCategory,
    AnalyticsContext,
    AnalyticsMetadata,
    AnalyticsResult,
    ConfidenceInterval,
    ForecastingModel,
    ForecastResult,
    TimeSeries,
    TimeSeriesPoint,
    register,
)
from mineproductivity.events.store import _InMemoryEventStore

_SHIFT_START = datetime(2026, 6, 12, 6, tzinfo=timezone.utc)
_TPH = (1310, 1300, 1295, 1288, 1276, 1265, 1258, 1249, 1240, 1232, 1220, 1205, 1180, 1150)


@register
class DriftForecaster(ForecastingModel):
    """Extrapolates the last value along the mean step, with a std-based band."""

    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="FORECAST.Drift",
        name="Linear Drift Forecaster",
        category=AnalyticsCategory.FORECASTING,
        description="Naive drift forecast: last value + mean step, +/- 2 std band.",
        min_observations=2,
    )

    def _forecast(
        self, series: TimeSeries, *, horizon: int, context: AnalyticsContext
    ) -> ForecastResult:
        values = series.values()
        deltas = [later - earlier for earlier, later in zip(values, values[1:], strict=False)]
        drift = fmean(deltas) if deltas else 0.0
        spread = pstdev(values) if len(values) > 1 else 0.0
        last = values[-1]
        predicted = tuple(last + drift * (step + 1) for step in range(horizon))
        intervals = tuple(
            ConfidenceInterval(
                model_code=self.meta.code,
                lower=point - 2 * spread,
                upper=point + 2 * spread,
                confidence=0.95,
                method="normal",
            )
            for point in predicted
        )
        return ForecastResult(
            model_code=self.meta.code, horizon=horizon, predicted=predicted, intervals=intervals
        )

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        # The concrete subclass decides how analyze() relates to forecasting.
        return self._forecast(series, horizon=1, context=context)


def main() -> None:
    print("--- analytics ships zero forecasters; this plugin implements the contract ---")
    print(f"'FORECAST.Drift' in REGISTRY: {'FORECAST.Drift' in REGISTRY}")

    series = TimeSeries(
        points=tuple(
            TimeSeriesPoint(timestamp=_SHIFT_START + timedelta(hours=12 * i), value=float(v))
            for i, v in enumerate(_TPH)
        )
    )
    model = DriftForecaster()
    forecast = model._forecast(
        series, horizon=3, context=AnalyticsContext(event_store=_InMemoryEventStore())
    )

    print()
    print("--- Forecast the next 3 shifts, each a point estimate + 95% band ---")
    for step, (point, band) in enumerate(
        zip(forecast.predicted, forecast.intervals, strict=True), 1
    ):
        print(
            f"  shift +{step}: {point:.0f} t/h  [{band.lower:.0f}, {band.upper:.0f}] ({band.method})"
        )

    print()
    print("--- analyze() inherits the qualify-don't-coerce guard for short series ---")
    short = TimeSeries(points=(TimeSeriesPoint(timestamp=_SHIFT_START, value=1300.0),))
    result = model.analyze(short, context=AnalyticsContext(event_store=_InMemoryEventStore()))
    print(f"1-point series -> warnings={result.warnings}")


if __name__ == "__main__":
    main()
