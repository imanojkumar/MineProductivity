"""Tests for mineproductivity.analytics.windowing."""

from __future__ import annotations

from datetime import timedelta

import pytest

from mineproductivity.kpis import RollingWindow

from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.windowing import RollingSpec


def _rolling_window() -> RollingWindow:
    return RollingWindow(kind="day", span=timedelta(days=7), step=timedelta(days=1))


class TestRollingSpecConstruction:
    def test_periods_only_is_valid(self) -> None:
        spec = RollingSpec(periods=7)
        assert spec.periods == 7
        assert spec.time_window is None

    def test_time_window_only_is_valid(self) -> None:
        window = _rolling_window()
        spec = RollingSpec(time_window=window)
        assert spec.time_window is window
        assert spec.periods is None

    def test_min_periods_defaults_to_one(self) -> None:
        spec = RollingSpec(periods=7)
        assert spec.min_periods == 1

    def test_min_periods_is_overridable(self) -> None:
        spec = RollingSpec(periods=7, min_periods=3)
        assert spec.min_periods == 3


class TestRollingSpecValidate:
    def test_neither_time_window_nor_periods_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="exactly one"):
            RollingSpec()

    def test_both_time_window_and_periods_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="exactly one"):
            RollingSpec(time_window=_rolling_window(), periods=7)


class TestRollingSpecReplace:
    def test_replace_reruns_validate(self) -> None:
        spec = RollingSpec(periods=7)
        replaced = spec.replace(periods=14)
        assert replaced.periods == 14

    def test_replace_that_violates_invariant_raises(self) -> None:
        spec = RollingSpec(periods=7)
        with pytest.raises(AnalyticsValidationError):
            spec.replace(time_window=_rolling_window())
