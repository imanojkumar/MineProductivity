"""Contextual event validation and confidence scoring."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

from mineproductivity.core import BaseValidator, BaseValueObject, ValidationResult

from mineproductivity.events.base_event import BaseEvent
from mineproductivity.events.exceptions import EventValidationError

__all__ = ["ConfidenceScore", "EventValidator", "ValidationOutcome", "score_confidence"]


@dataclasses.dataclass(frozen=True, slots=True)
class ConfidenceScore(BaseValueObject):
    """How much a downstream consumer should trust one event, in ``[0.0, 1.0]``.

    Examples
    --------
    >>> ConfidenceScore(value=1.0).value
    1.0
    >>> ConfidenceScore(value=0.5, reasons=("missing operator_id",)).reasons
    ('missing operator_id',)
    """

    value: float
    reasons: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)

    def validate(self) -> None:
        if not (0.0 <= self.value <= 1.0):
            raise EventValidationError("ConfidenceScore.value must be in [0.0, 1.0]")


@dataclasses.dataclass(frozen=True, slots=True)
class ValidationOutcome(BaseValueObject):
    """The complete result of validating one event: structural/contextual
    validation combined with a confidence score.

    Examples
    --------
    >>> outcome = ValidationOutcome(result=ValidationResult.success(), confidence=ConfidenceScore(1.0))
    >>> outcome.is_valid
    True
    """

    result: ValidationResult
    confidence: ConfidenceScore

    @property
    def is_valid(self) -> bool:
        return self.result.is_valid


def score_confidence(result: ValidationResult) -> ConfidenceScore:
    """Derive a :class:`ConfidenceScore` from a :class:`~mineproductivity.core.validator.ValidationResult`.

    A valid result scores ``1.0``. Each accumulated error subtracts
    ``0.1``, floored at ``0.1`` -- an event that failed contextual
    validation is never treated as fully untrustworthy (``0.0``), since a
    single unresolved reference is a data-quality signal, not proof the
    whole event is fabricated.
    """
    if result.is_valid:
        return ConfidenceScore(value=1.0)
    penalty = min(0.1 * len(result.errors), 0.9)
    return ConfidenceScore(value=round(1.0 - penalty, 2), reasons=result.errors)


class EventValidator(BaseValidator[BaseEvent]):
    """Contextual validation for a constructed :class:`~mineproductivity.events.base_event.BaseEvent`.

    Separate from the structural validation every ``BaseEvent`` already
    enforces on construction (its own ``validate()``, inherited from
    :class:`~mineproductivity.core.value_object.BaseValueObject`).
    ``EventValidator`` checks cross-cutting concerns that do not depend
    on any single event type's fields: that identity references are
    present, and -- via the optional ``entity_resolver`` hook -- that
    they resolve against the (future) Ontology Framework's entity
    registry. Per Documentation Governance Rule #005, this package does
    not implement that registry itself; ``entity_resolver`` lets a caller
    inject real resolution once it exists, without ``events`` depending
    on it.

    Examples
    --------
    >>> validator = EventValidator()
    >>> from mineproductivity.events.canonical import CycleEvent
    >>> event = CycleEvent(
    ...     equipment_id="HT-214", shift_id="A-2026-06-25",
    ...     queue_min=1.5, spot_min=0.5, load_min=2.5,
    ...     haul_min=8.0, dump_min=1.0, return_min=6.0, payload_t=220.0,
    ... )
    >>> validator.validate(event).is_valid
    True
    """

    def __init__(self, *, entity_resolver: Callable[[str], bool] | None = None) -> None:
        self._entity_resolver = entity_resolver

    def validate(self, candidate: BaseEvent) -> ValidationResult:
        errors: list[str] = []
        if not candidate.equipment_id.strip():
            errors.append("equipment_id must not be empty")
        if not candidate.shift_id.strip():
            errors.append("shift_id must not be empty")
        if self._entity_resolver is not None and candidate.equipment_id.strip():
            if not self._entity_resolver(candidate.equipment_id):
                errors.append(
                    f"equipment_id {candidate.equipment_id!r} does not resolve to a known entity"
                )
        return ValidationResult.success() if not errors else ValidationResult.failure(*errors)

    def validate_with_confidence(self, candidate: BaseEvent) -> ValidationOutcome:
        """Validate ``candidate`` and derive its :class:`ConfidenceScore` in one call."""
        result = self.validate(candidate)
        return ValidationOutcome(result=result, confidence=score_confidence(result))
