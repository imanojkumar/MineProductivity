"""Tests for mineproductivity.decision.alerting."""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.decision.alerting import AlertGenerator
from mineproductivity.decision.result import Recommendation, ThresholdBreach
from mineproductivity.decision.thresholds import Threshold


def _breach(*, limit: float = 0.65, observed_value: float = 0.58) -> ThresholdBreach:
    return ThresholdBreach(
        threshold=Threshold(field="value", comparator="<", limit=limit),
        observed_value=observed_value,
        breached_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _recommendation(*, severity: str = "high") -> Recommendation:
    return Recommendation(
        policy_code="AVAIL.LowFleetAvailability",
        triggered_rules=("low_oee",),
        summary="Investigate fleet availability",
        severity=severity,  # type: ignore[arg-type]
        evidence=("UTIL.OEE",),
    )


class TestAlertGeneratorFromBreach:
    def test_default_severity_is_high(self) -> None:
        alert = AlertGenerator().from_breach(_breach())
        assert alert.severity == "high"

    def test_custom_breach_severity_is_honored(self) -> None:
        alert = AlertGenerator(breach_severity="critical").from_breach(_breach())
        assert alert.severity == "critical"

    def test_triggered_by_carries_the_breach(self) -> None:
        breach = _breach()
        alert = AlertGenerator().from_breach(breach)
        assert alert.triggered_by == breach

    def test_message_mentions_field_and_observed_value(self) -> None:
        alert = AlertGenerator().from_breach(_breach(limit=0.65, observed_value=0.58))
        assert "value" in alert.message
        assert "0.58" in alert.message
        assert "0.65" in alert.message

    def test_scope_defaults_to_empty(self) -> None:
        alert = AlertGenerator().from_breach(_breach())
        assert dict(alert.scope) == {}

    def test_scope_is_passed_through(self) -> None:
        alert = AlertGenerator().from_breach(_breach(), scope={"pit": "north"})
        assert dict(alert.scope) == {"pit": "north"}


class TestAlertGeneratorFromRecommendation:
    def test_high_severity_produces_an_alert(self) -> None:
        alert = AlertGenerator().from_recommendation(_recommendation(severity="high"))
        assert alert is not None
        assert alert.severity == "high"

    def test_critical_severity_produces_an_alert(self) -> None:
        alert = AlertGenerator().from_recommendation(_recommendation(severity="critical"))
        assert alert is not None
        assert alert.severity == "critical"

    def test_medium_severity_returns_none(self) -> None:
        assert AlertGenerator().from_recommendation(_recommendation(severity="medium")) is None

    def test_low_severity_returns_none(self) -> None:
        assert AlertGenerator().from_recommendation(_recommendation(severity="low")) is None

    def test_message_equals_recommendation_summary(self) -> None:
        rec = _recommendation(severity="high")
        alert = AlertGenerator().from_recommendation(rec)
        assert alert is not None
        assert alert.message == rec.summary

    def test_triggered_by_is_none(self) -> None:
        alert = AlertGenerator().from_recommendation(_recommendation(severity="high"))
        assert alert is not None
        assert alert.triggered_by is None

    def test_scope_is_passed_through(self) -> None:
        alert = AlertGenerator().from_recommendation(
            _recommendation(severity="high"), scope={"pit": "south"}
        )
        assert alert is not None
        assert dict(alert.scope) == {"pit": "south"}


class TestAlertGeneratorRepr:
    def test_repr_includes_breach_severity(self) -> None:
        assert "critical" in repr(AlertGenerator(breach_severity="critical"))
