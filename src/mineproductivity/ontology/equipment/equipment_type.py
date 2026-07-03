"""``EquipmentType``: the abstract root for every machine in the mine."""

from __future__ import annotations

import dataclasses
from abc import ABC
from enum import Enum
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import BaseEntityType

__all__ = ["EquipmentType", "OperationalState"]


class OperationalState(Enum):
    """The four-state machine every equipment leaf type inherits.

    Declared here as descriptive metadata only -- tracking which state an
    instance is *currently* in is a future ``digital_twin`` concern,
    derived from the event stream, never mutable state on the entity
    itself (design spec AD-ON-04).
    """

    OPERATING = "operating"
    STANDBY = "standby"
    DOWN = "down"
    MAINTENANCE = "maintenance"


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class EquipmentType(BaseEntityType, ABC):
    """Abstract root for every machine in the mine.

    Common behaviour (the operational state machine, availability-KPI
    applicability) lives here; specifics (rated capacity, cycle-level
    KPIs) live in leaves -- the inheritance split demonstrated in
    Cookbook Part I, Ch. 8.
    """

    operational_states: ClassVar[tuple[OperationalState, ...]] = (
        OperationalState.OPERATING,
        OperationalState.STANDBY,
        OperationalState.DOWN,
        OperationalState.MAINTENANCE,
    )

    rated_capacity: float  # tonnes, or tonnes-per-pass for loaders

    def validate(self) -> None:
        if self.rated_capacity < 0:
            raise OntologyValidationError(f"{type(self).__name__}.rated_capacity must be >= 0")
