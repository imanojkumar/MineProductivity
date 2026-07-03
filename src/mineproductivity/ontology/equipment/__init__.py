"""Equipment ontology: the machines a mine operates.

``EquipmentType`` is the abstract root; every concrete leaf registers
itself via ``register_equipment`` (an alias of
:func:`~mineproductivity.ontology.entity_type.register_entity_type`) on
import.
"""

from __future__ import annotations

from mineproductivity.ontology.entity_type import register_entity_type as register_equipment
from mineproductivity.ontology.equipment.ancillary import Dozer, Grader, WaterTruck
from mineproductivity.ontology.equipment.drill import BlastholeDrill
from mineproductivity.ontology.equipment.equipment_type import EquipmentType, OperationalState
from mineproductivity.ontology.equipment.fixed_plant import Conveyor, Crusher, Mill
from mineproductivity.ontology.equipment.haul_truck import ArticulatedHaulTruck, RigidHaulTruck
from mineproductivity.ontology.equipment.loading_unit import LHD, HydraulicShovel, WheelLoader

__all__ = [
    "LHD",
    "ArticulatedHaulTruck",
    "BlastholeDrill",
    "Conveyor",
    "Crusher",
    "Dozer",
    "EquipmentType",
    "Grader",
    "HydraulicShovel",
    "Mill",
    "OperationalState",
    "RigidHaulTruck",
    "WaterTruck",
    "WheelLoader",
    "register_equipment",
]
