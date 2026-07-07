"""Tests for mineproductivity.analytics.incremental."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.incremental import IncrementalAccumulator
from mineproductivity.analytics.result import StatisticalSummary
from mineproductivity.analytics.statistics import describe
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

from .conftest import assert_no_import_from

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestIncrementalAccumulatorBasics:
    def test_single_observation(self) -> None:
        accumulator = IncrementalAccumulator()
        accumulator.update(42.0)
        summary = accumulator.snapshot()
        assert isinstance(summary, StatisticalSummary)
        assert summary.n == 1
        assert summary.mean == 42.0
        assert summary.std == 0.0
        assert summary.minimum == 42.0
        assert summary.maximum == 42.0

    def test_hand_computed_reference_dataset(self) -> None:
        """[2, 4, 4, 4, 5, 5, 7, 9] is the classic worked example for
        population mean=5.0, population std=2.0 (Wikipedia's "Standard
        deviation" article)."""
        accumulator = IncrementalAccumulator()
        for value in (2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0):
            accumulator.update(value)
        summary = accumulator.snapshot()
        assert summary.n == 8
        assert summary.mean == pytest.approx(5.0)
        assert summary.std == pytest.approx(2.0)

    def test_all_identical_values_have_zero_std(self) -> None:
        accumulator = IncrementalAccumulator()
        for _ in range(10):
            accumulator.update(7.0)
        summary = accumulator.snapshot()
        assert summary.mean == 7.0
        assert summary.std == 0.0

    def test_updates_are_order_independent_for_min_max(self) -> None:
        accumulator = IncrementalAccumulator()
        for value in (5.0, 1.0, 9.0, 3.0, 7.0):
            accumulator.update(value)
        summary = accumulator.snapshot()
        assert summary.minimum == 1.0
        assert summary.maximum == 9.0

    def test_negative_and_positive_values(self) -> None:
        accumulator = IncrementalAccumulator()
        for value in (-10.0, -5.0, 0.0, 5.0, 10.0):
            accumulator.update(value)
        summary = accumulator.snapshot()
        assert summary.mean == pytest.approx(0.0)
        assert summary.minimum == -10.0
        assert summary.maximum == 10.0


class TestIncrementalAccumulatorEdgeCases:
    def test_snapshot_before_any_update_raises(self) -> None:
        accumulator = IncrementalAccumulator()
        with pytest.raises(AnalyticsValidationError):
            accumulator.snapshot()

    def test_snapshot_error_matches_describes_own_empty_input_contract(self) -> None:
        """Mirrors ``statistics.describe()``'s own "requires at least
        one observation" contract for the same degenerate input --
        reuses the same exception type, not a new one."""
        accumulator = IncrementalAccumulator()
        with pytest.raises(AnalyticsValidationError, match="at least one observation"):
            accumulator.snapshot()
        with pytest.raises(AnalyticsValidationError, match="at least one observation"):
            describe(TimeSeries(points=()))

    def test_percentiles_are_always_empty(self) -> None:
        """A genuine, disclosed limitation of O(1)-memory streaming
        computation (module docstring), not an oversight."""
        accumulator = IncrementalAccumulator()
        for value in range(100):
            accumulator.update(float(value))
        assert accumulator.snapshot().percentiles == {}

    def test_model_code_is_set(self) -> None:
        accumulator = IncrementalAccumulator()
        accumulator.update(1.0)
        assert accumulator.snapshot().model_code == "INCREMENTAL.Accumulator"

    def test_multiple_snapshots_do_not_mutate_state(self) -> None:
        """Two ``snapshot()`` calls with no intervening ``update()`` must
        report identical *statistical* state -- proving ``snapshot()``
        is a pure read that never mutates the accumulator.

        Deliberately does NOT assert ``first == second``: ``StatisticalSummary``
        is an ``AnalyticsResult``, whose ``computed_at`` field is
        freshly generated (``default_factory=lambda: datetime.now(...)``,
        see ``result.py``) on every construction, by design, the same as
        every other ``AnalyticsResult``-returning call in this package.
        Two back-to-back ``snapshot()`` calls therefore legitimately
        produce two objects with two different ``computed_at`` values
        whenever the two calls straddle a clock tick -- full dataclass
        equality is a wall-clock race, not a property of ``snapshot()``'s
        correctness (confirmed empirically: ~0.2% of trials on this
        machine, and evidently reliable enough to fail consistently on
        GitHub Actions' typically slower/more-loaded runners). Comparing
        the state-bearing fields individually instead verifies the one
        thing this test is actually about."""
        accumulator = IncrementalAccumulator()
        accumulator.update(1.0)
        accumulator.update(2.0)
        first = accumulator.snapshot()
        second = accumulator.snapshot()
        assert first.n == second.n
        assert first.mean == second.mean
        assert first.std == second.std
        assert first.minimum == second.minimum
        assert first.maximum == second.maximum
        assert first.percentiles == second.percentiles
        accumulator.update(3.0)
        third = accumulator.snapshot()
        assert third.n == 3
        assert third.n != first.n
        assert third.mean != first.mean


class TestStreamingBatchParity:
    """Mandatory per the Implementation Checklist (§29, §35, §36):
    ``IncrementalAccumulator``'s result and ``statistics.describe()``'s
    batch result must agree within floating-point tolerance over the
    same dataset."""

    def _series(self, values: list[float]) -> TimeSeries:
        return TimeSeries(
            points=tuple(
                TimeSeriesPoint(timestamp=DAY_1 + timedelta(seconds=i), value=v)
                for i, v in enumerate(values)
            )
        )

    def test_parity_over_a_small_hand_authored_dataset(self) -> None:
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        accumulator = IncrementalAccumulator()
        for value in values:
            accumulator.update(value)
        streaming = accumulator.snapshot()
        batch = describe(self._series(values))

        assert streaming.n == batch.n
        assert streaming.mean == pytest.approx(batch.mean, abs=1e-9)
        assert streaming.std == pytest.approx(batch.std, abs=1e-9)
        assert streaming.minimum == pytest.approx(batch.minimum, abs=1e-9)
        assert streaming.maximum == pytest.approx(batch.maximum, abs=1e-9)

    def test_parity_over_a_large_randomized_dataset(self) -> None:
        rng = random.Random(42)
        values = [rng.uniform(-500.0, 500.0) for _ in range(1000)]
        accumulator = IncrementalAccumulator()
        for value in values:
            accumulator.update(value)
        streaming = accumulator.snapshot()
        batch = describe(self._series(values))

        assert streaming.n == batch.n
        assert streaming.mean == pytest.approx(batch.mean, rel=1e-9)
        assert streaming.std == pytest.approx(batch.std, rel=1e-9)
        assert streaming.minimum == batch.minimum
        assert streaming.maximum == batch.maximum

    def test_parity_holds_for_single_observation(self) -> None:
        values = [123.456]
        accumulator = IncrementalAccumulator()
        accumulator.update(values[0])
        streaming = accumulator.snapshot()
        batch = describe(self._series(values))

        assert streaming.n == batch.n == 1
        assert streaming.mean == batch.mean
        assert streaming.std == batch.std == 0.0


class TestPublicApiValidation:
    def test_incrementalaccumulator_is_exported(self) -> None:
        import mineproductivity.analytics as analytics

        assert "IncrementalAccumulator" in analytics.__all__
        assert analytics.IncrementalAccumulator is IncrementalAccumulator

    def test_statisticalsummary_is_reused_not_duplicated(self) -> None:
        import mineproductivity.analytics.result as result_module

        assert StatisticalSummary.__module__ == result_module.__name__

    def test_incremental_module_public_api_matches_spec_exactly(self) -> None:
        import mineproductivity.analytics.incremental as incremental_module

        assert incremental_module.__all__ == ["IncrementalAccumulator"]

    def test_does_not_import_business_logic_modules(self) -> None:
        """Execution modules coordinate existing components rather than
        reimplement statistics/rolling/trend/baseline/benchmarking/
        quality logic -- mechanically verified, not merely asserted.
        ``incremental.py`` deliberately does *not* import ``statistics.py``
        at all (see its own module docstring's reuse audit: batch
        functions there all require a materialized ``Sequence[float]``,
        incompatible with O(1)-memory streaming)."""
        import mineproductivity.analytics.incremental as incremental_module

        assert_no_import_from(
            incremental_module,
            "statistics",
            "rolling",
            "trend",
            "baseline",
            "benchmarking",
            "quality",
        )
