"""Tests for mineproductivity.events.validation."""

from __future__ import annotations

import pytest

from mineproductivity.events.canonical import CycleEvent
from mineproductivity.events.exceptions import EventValidationError
from mineproductivity.events.validation import (
    ConfidenceScore,
    EventValidator,
    ValidationOutcome,
    score_confidence,
)
from mineproductivity.core import ValidationResult


def make_cycle(equipment_id: str = "HT-214", shift_id: str = "A-2026-06-25") -> CycleEvent:
    return CycleEvent(
        equipment_id=equipment_id,
        shift_id=shift_id,
        queue_min=1.5,
        spot_min=0.5,
        load_min=2.5,
        haul_min=8.0,
        dump_min=1.0,
        return_min=6.0,
        payload_t=220.0,
    )


class TestConfidenceScore:
    def test_boundary_values_accepted(self) -> None:
        assert ConfidenceScore(value=0.0).value == 0.0
        assert ConfidenceScore(value=1.0).value == 1.0

    def test_out_of_range_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            ConfidenceScore(value=1.1)
        with pytest.raises(EventValidationError):
            ConfidenceScore(value=-0.1)

    def test_default_reasons_is_empty(self) -> None:
        assert ConfidenceScore(value=1.0).reasons == ()


class TestScoreConfidence:
    def test_valid_result_scores_full_confidence(self) -> None:
        score = score_confidence(ValidationResult.success())
        assert score.value == 1.0

    def test_each_error_reduces_confidence(self) -> None:
        one_error = score_confidence(ValidationResult.failure("a"))
        two_errors = score_confidence(ValidationResult.failure("a", "b"))
        assert one_error.value > two_errors.value

    def test_confidence_floors_at_point_one(self) -> None:
        many_errors = score_confidence(ValidationResult.failure(*[f"err{i}" for i in range(20)]))
        assert many_errors.value == pytest.approx(0.1)

    def test_reasons_carry_through(self) -> None:
        score = score_confidence(ValidationResult.failure("bad field"))
        assert score.reasons == ("bad field",)


class TestValidationOutcome:
    def test_is_valid_reflects_result(self) -> None:
        valid = ValidationOutcome(
            result=ValidationResult.success(), confidence=ConfidenceScore(1.0)
        )
        invalid = ValidationOutcome(
            result=ValidationResult.failure("x"), confidence=ConfidenceScore(0.9)
        )
        assert valid.is_valid is True
        assert invalid.is_valid is False


class TestEventValidator:
    def test_valid_event_passes(self) -> None:
        result = EventValidator().validate(make_cycle())
        assert result.is_valid

    def test_empty_equipment_id_rejected(self) -> None:
        result = EventValidator().validate(make_cycle(equipment_id=""))
        assert not result.is_valid
        assert "equipment_id" in result.errors[0]

    def test_empty_shift_id_rejected(self) -> None:
        result = EventValidator().validate(make_cycle(shift_id=""))
        assert not result.is_valid

    def test_whitespace_only_ids_rejected(self) -> None:
        result = EventValidator().validate(make_cycle(equipment_id="   "))
        assert not result.is_valid

    def test_no_resolver_skips_entity_resolution(self) -> None:
        result = EventValidator().validate(make_cycle(equipment_id="anything"))
        assert result.is_valid

    def test_resolver_accepts_known_entity(self) -> None:
        validator = EventValidator(entity_resolver=lambda eid: eid == "HT-214")
        result = validator.validate(make_cycle(equipment_id="HT-214"))
        assert result.is_valid

    def test_resolver_rejects_unknown_entity(self) -> None:
        validator = EventValidator(entity_resolver=lambda eid: eid == "HT-214")
        result = validator.validate(make_cycle(equipment_id="UNKNOWN"))
        assert not result.is_valid

    def test_resolver_not_called_for_empty_equipment_id(self) -> None:
        calls: list[str] = []

        def resolver(eid: str) -> bool:
            calls.append(eid)
            return True

        validator = EventValidator(entity_resolver=resolver)
        validator.validate(make_cycle(equipment_id=""))
        assert calls == []

    def test_call_delegates_to_validate(self) -> None:
        validator = EventValidator()
        assert validator(make_cycle()).is_valid

    def test_validate_with_confidence_valid_event(self) -> None:
        outcome = EventValidator().validate_with_confidence(make_cycle())
        assert outcome.is_valid
        assert outcome.confidence.value == 1.0

    def test_validate_with_confidence_invalid_event(self) -> None:
        outcome = EventValidator().validate_with_confidence(make_cycle(equipment_id=""))
        assert not outcome.is_valid
        assert outcome.confidence.value < 1.0
