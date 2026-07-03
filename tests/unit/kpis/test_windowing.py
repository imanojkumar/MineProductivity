"""Tests for mineproductivity.kpis.windowing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.core import ValidationError

from mineproductivity.kpis.windowing import CumulativeWindow, RollingWindow, Window

SINCE = datetime(2026, 6, 25, tzinfo=timezone.utc)
UNTIL = datetime(2026, 6, 26, tzinfo=timezone.utc)


class TestWindow:
    @pytest.mark.parametrize("kind", ["shift", "day", "week", "month"])
    def test_named_kinds_do_not_require_bounds(self, kind: str) -> None:
        window = Window(kind=kind)  # type: ignore[arg-type]
        assert window.kind == kind
        assert window.since_utc is None

    def test_custom_kind_with_both_bounds_is_valid(self) -> None:
        window = Window(kind="custom", since_utc=SINCE, until_utc=UNTIL)
        assert window.since_utc == SINCE
        assert window.until_utc == UNTIL

    def test_custom_kind_without_bounds_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires both"):
            Window(kind="custom")

    def test_custom_kind_with_only_since_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires both"):
            Window(kind="custom", since_utc=SINCE)

    def test_custom_kind_with_only_until_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires both"):
            Window(kind="custom", until_utc=UNTIL)

    def test_until_before_since_raises(self) -> None:
        with pytest.raises(ValidationError, match="after"):
            Window(kind="custom", since_utc=UNTIL, until_utc=SINCE)

    def test_until_equal_to_since_raises(self) -> None:
        with pytest.raises(ValidationError, match="after"):
            Window(kind="custom", since_utc=SINCE, until_utc=SINCE)


class TestRollingWindow:
    def test_valid_construction(self) -> None:
        window = RollingWindow(
            kind="custom",
            since_utc=SINCE,
            until_utc=UNTIL,
            span=timedelta(days=7),
            step=timedelta(days=1),
        )
        assert window.span == timedelta(days=7)
        assert window.step == timedelta(days=1)

    def test_inherits_window_validation(self) -> None:
        with pytest.raises(ValidationError, match="requires both"):
            RollingWindow(kind="custom", span=timedelta(days=7), step=timedelta(days=1))

    def test_non_positive_span_raises(self) -> None:
        with pytest.raises(ValidationError, match="span must be positive"):
            RollingWindow(
                kind="custom",
                since_utc=SINCE,
                until_utc=UNTIL,
                span=timedelta(0),
                step=timedelta(days=1),
            )

    def test_non_positive_step_raises(self) -> None:
        with pytest.raises(ValidationError, match="step must be positive"):
            RollingWindow(
                kind="custom",
                since_utc=SINCE,
                until_utc=UNTIL,
                span=timedelta(days=7),
                step=timedelta(0),
            )


class TestCumulativeWindow:
    def test_valid_construction(self) -> None:
        window = CumulativeWindow(kind="month", start_utc=SINCE)
        assert window.start_utc == SINCE
