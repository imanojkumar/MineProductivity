"""``Normalizer``/``FieldMapper``/``ReasonCodeMap``: translate one raw
source record into a canonical event, independently of any live
connector I/O (design spec AD-CN-02).
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject, Maybe, ValidationError
from mineproductivity.events import CycleEvent, DelayEvent
from mineproductivity.ontology import DelayCategory

__all__ = ["FieldMapper", "Normalizer", "ReasonCodeMap"]


class Normalizer(ABC):
    """Applies :class:`FieldMapper` + :class:`ReasonCodeMap` to translate
    one raw source record into a canonical :class:`~mineproductivity.events.base_event.BaseEvent`.

    Separated from :class:`~mineproductivity.connectors.base.FMSConnector`
    itself so mapping logic is independently unit-testable without a
    live/fixture source connection.
    """

    @abstractmethod
    def normalize_cycle(self, raw: Mapping[str, Any]) -> CycleEvent:
        """Translate one raw cycle record into a :class:`CycleEvent`.

        Raises
        ------
        MappingError
            If ``raw`` cannot be translated (a missing required field, a
            non-numeric value where a number is required, ...).
        """

    @abstractmethod
    def normalize_delay(self, raw: Mapping[str, Any]) -> DelayEvent:
        """Translate one raw delay record into a :class:`DelayEvent`.

        Raises
        ------
        MappingError
            If ``raw`` cannot be translated.
        """


@dataclasses.dataclass(frozen=True, slots=True)
class FieldMapper(BaseValueObject):
    """Declarative field-name mapping: vendor field name -> canonical
    field name. Fields absent from ``mapping`` pass through unchanged.

    Examples
    --------
    >>> mapper = FieldMapper(mapping={"TruckID": "equipment_id"})
    >>> mapper.apply({"TruckID": "HT-214", "PayloadTonnes": 220.0})
    {'equipment_id': 'HT-214', 'PayloadTonnes': 220.0}
    """

    mapping: Mapping[str, str]

    def _normalize(self) -> None:
        object.__setattr__(self, "mapping", MappingProxyType(dict(self.mapping)))

    def apply(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Return a new dict with every key in ``raw`` renamed per
        :attr:`mapping` (keys absent from the mapping are copied as-is)."""
        return {self.mapping.get(key, key): value for key, value in raw.items()}


@dataclasses.dataclass(frozen=True, slots=True)
class ReasonCodeMap(BaseValueObject):
    """Vendor delay-reason code -> canonical ``(DelayCategory, reason)``.

    Cookbook Part I, Ch. 7: "The hardest part of a real connector is the
    reason-code map... Get this mapping right and every downstream delay
    analysis becomes comparable."

    Examples
    --------
    >>> reason_map = ReasonCodeMap(
    ...     vendor_name="minestar",
    ...     mapping={"MECH_FAIL": (DelayCategory.EQUIPMENT, "mechanical failure")},
    ... )
    >>> resolved = reason_map.resolve("MECH_FAIL")
    >>> resolved.unwrap()
    (<DelayCategory.EQUIPMENT: 'Equipment'>, 'mechanical failure')
    >>> reason_map.resolve("UNKNOWN_CODE").is_nothing
    True
    """

    vendor_name: str
    mapping: Mapping[str, tuple[DelayCategory, str]]

    def _normalize(self) -> None:
        object.__setattr__(self, "mapping", MappingProxyType(dict(self.mapping)))

    def validate(self) -> None:
        if not self.vendor_name.strip():
            raise ValidationError("ReasonCodeMap.vendor_name must not be empty")

    def resolve(self, vendor_code: str) -> Maybe[tuple[DelayCategory, str]]:
        """Non-raising lookup of ``vendor_code``."""
        found = self.mapping.get(vendor_code)
        return Maybe.nothing() if found is None else Maybe.some(found)
