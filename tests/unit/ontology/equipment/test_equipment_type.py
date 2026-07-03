"""Tests for mineproductivity.ontology.equipment.equipment_type."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

import pytest

from mineproductivity.ontology.entity_type import EntityTypeMetadata
from mineproductivity.ontology.equipment.equipment_type import EquipmentType, OperationalState
from mineproductivity.ontology.exceptions import OntologyValidationError


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class _TestMachine(EquipmentType):
    code: ClassVar[str] = "TEST_MACHINE"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(name="Test Machine", description="d")


class TestOperationalState:
    def test_has_four_states(self) -> None:
        assert len(list(OperationalState)) == 4

    def test_values(self) -> None:
        assert OperationalState.OPERATING.value == "operating"
        assert OperationalState.STANDBY.value == "standby"
        assert OperationalState.DOWN.value == "down"
        assert OperationalState.MAINTENANCE.value == "maintenance"


class TestEquipmentTypeAbstractRoot:
    def test_operational_states_classvar_shared_across_leaves(self) -> None:
        assert _TestMachine.operational_states == (
            OperationalState.OPERATING,
            OperationalState.STANDBY,
            OperationalState.DOWN,
            OperationalState.MAINTENANCE,
        )

    def test_valid_rated_capacity(self) -> None:
        machine = _TestMachine(id="m-1", rated_capacity=10.0)
        assert machine.rated_capacity == 10.0

    def test_zero_rated_capacity_accepted(self) -> None:
        machine = _TestMachine(id="m-2", rated_capacity=0.0)
        assert machine.rated_capacity == 0.0

    def test_negative_rated_capacity_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            _TestMachine(id="m-3", rated_capacity=-0.01)
