"""Tests for mineproductivity.ontology.safety.hazard."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.safety.hazard import HazardZone, SafetyEventType, SpeedLimitMap


class TestSafetyEventType:
    def test_has_four_kinds(self) -> None:
        assert len(list(SafetyEventType)) == 4

    def test_values(self) -> None:
        assert SafetyEventType.SPEED_VIOLATION.value == "speed-violation"
        assert SafetyEventType.FATIGUE.value == "fatigue"
        assert SafetyEventType.PROXIMITY.value == "proximity"
        assert SafetyEventType.SEATBELT.value == "seatbelt"


class TestHazardZone:
    def test_valid_construction(self) -> None:
        zone = HazardZone(id="B7N_CR1", zone_id="B7N_CR1", speed_limit_kmh=45.0)
        assert zone.speed_limit_kmh == 45.0

    def test_supported_kpis(self) -> None:
        assert HazardZone.meta.supported_kpis == ("SAFE.SpeedViolationRate",)

    def test_negative_speed_limit_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            HazardZone(id="x", zone_id="B7N_CR1", speed_limit_kmh=-1.0)


class TestSpeedLimitMap:
    def test_valid_construction(self) -> None:
        limits = SpeedLimitMap(
            id="SLM-1", mine_id="bingham-west", zone_limits_kmh={"B7N_CR1": 45.0}
        )
        assert limits.zone_limits_kmh["B7N_CR1"] == 45.0

    def test_zone_limits_defaults_to_empty_dict(self) -> None:
        limits = SpeedLimitMap(id="SLM-2", mine_id="bingham-west")
        assert limits.zone_limits_kmh == {}

    def test_empty_mine_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            SpeedLimitMap(id="x", mine_id="")

    def test_negative_zone_limit_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            SpeedLimitMap(id="x", mine_id="bingham-west", zone_limits_kmh={"Z1": -5.0})
