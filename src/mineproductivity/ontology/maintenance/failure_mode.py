"""``FailureMode`` and ``MaintenanceWorkOrder``: maintenance reference entities."""

from __future__ import annotations

import dataclasses
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["FailureMode", "MaintenanceWorkOrder"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class FailureMode(BaseEntityType):
    """A classified equipment failure mode (e.g. ``HYD-001`` for a
    hydraulic failure), the reference taxonomy
    :class:`~mineproductivity.events.canonical.maintenance_event.MaintenanceEvent`
    instances point at.

    Examples
    --------
    >>> mode = FailureMode(id="HYD-001", failure_mode_code="HYD-001", system="hydraulic")
    >>> mode.system
    'hydraulic'
    """

    code: ClassVar[str] = "FAILURE_MODE"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Failure Mode",
        description="A classified equipment failure mode.",
        supported_kpis=("MAINT.MTBF", "MAINT.MTTR", "MAINT.Ai"),
    )

    failure_mode_code: str  # e.g. "HYD-001"
    system: str  # "hydraulic", "tyre", "electrical", ...

    def validate(self) -> None:
        if not self.failure_mode_code.strip():
            raise OntologyValidationError("FailureMode.failure_mode_code must not be empty")
        if not self.system.strip():
            raise OntologyValidationError("FailureMode.system must not be empty")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class MaintenanceWorkOrder(BaseEntityType):
    """A maintenance work order's structural shape -- identity, the
    equipment it targets, and whether it is planned. Scheduling logic
    (assignment, prioritisation, execution) is explicitly out of scope
    for this package (design spec §2); this entity exists purely so
    other packages have a stable structural reference to point at.
    """

    code: ClassVar[str] = "MAINTENANCE_WORK_ORDER"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Maintenance Work Order",
        description="The structural shape of a maintenance work order (no scheduling logic).",
    )

    equipment_id: str
    failure_mode_code: str | None = dataclasses.field(default=None, kw_only=True)
    is_planned: bool = dataclasses.field(default=False, kw_only=True)

    def validate(self) -> None:
        if not self.equipment_id.strip():
            raise OntologyValidationError("MaintenanceWorkOrder.equipment_id must not be empty")
