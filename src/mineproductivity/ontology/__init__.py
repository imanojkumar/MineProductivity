"""``mineproductivity.ontology`` -- the typed, machine-readable model of
the mining world.

Implements the ten sub-ontology families (equipment, material, location,
organization, production, maintenance, cost, quality, safety,
environmental) plus the cross-cutting entity-type root, relationships,
reference data, and the Knowledge Graph projection contract, per
``docs/architecture/02_Ontology_Framework_Design_Specification.md``.

``ontology`` depends only on ``core`` -- see ``README.md`` for the full
set of architectural rules this package must satisfy.

Everything documented here is part of the public API and can be imported
directly from ``mineproductivity.ontology``, e.g.::

    from mineproductivity.ontology import RigidHaulTruck, Pit, Bench, Shift
"""

from __future__ import annotations

from mineproductivity.ontology.cost import CostCategory, CostCenter
from mineproductivity.ontology.entity_type import BaseEntityType, EntityTypeMetadata
from mineproductivity.ontology.entity_type import register_entity_type as register_equipment
from mineproductivity.ontology.environmental import EmissionFactor, MonitoringPoint
from mineproductivity.ontology.equipment import (
    LHD,
    ArticulatedHaulTruck,
    BlastholeDrill,
    Conveyor,
    Crusher,
    Dozer,
    EquipmentType,
    Grader,
    HydraulicShovel,
    Mill,
    OperationalState,
    RigidHaulTruck,
    WaterTruck,
    WheelLoader,
)
from mineproductivity.ontology.exceptions import (
    OntologyValidationError,
    RelationshipError,
    UnknownEntityTypeError,
)
from mineproductivity.ontology.graph_projection import (
    GraphEdge,
    GraphNode,
    KnowledgeGraphProjection,
)
from mineproductivity.ontology.location import Bench, Drive, Level, Mine, Pit, Route, Stope, Zone
from mineproductivity.ontology.maintenance import FailureMode, MaintenanceWorkOrder
from mineproductivity.ontology.material import Commodity, MaterialType
from mineproductivity.ontology.organization import BusinessUnit, Contractor, Crew, Fleet, Operator
from mineproductivity.ontology.production import Shift, ShiftCalendar, ShiftPattern
from mineproductivity.ontology.quality import GradeAttribute, QualitySpecification
from mineproductivity.ontology.reference import DelayCategory
from mineproductivity.ontology.relationship import Relationship, RelationshipKind
from mineproductivity.ontology.safety import HazardZone, SafetyEventType, SpeedLimitMap
from mineproductivity.ontology.validation import OntologyValidator

__all__ = [
    "ArticulatedHaulTruck",
    "BaseEntityType",
    "Bench",
    "BlastholeDrill",
    "BusinessUnit",
    "Commodity",
    "Contractor",
    "Conveyor",
    "CostCategory",
    "CostCenter",
    "Crew",
    "Crusher",
    "DelayCategory",
    "Dozer",
    "Drive",
    "EmissionFactor",
    "EntityTypeMetadata",
    "EquipmentType",
    "FailureMode",
    "Fleet",
    "GradeAttribute",
    "Grader",
    "GraphEdge",
    "GraphNode",
    "HazardZone",
    "HydraulicShovel",
    "KnowledgeGraphProjection",
    "LHD",
    "Level",
    "MaintenanceWorkOrder",
    "MaterialType",
    "Mill",
    "Mine",
    "MonitoringPoint",
    "OntologyValidationError",
    "OntologyValidator",
    "OperationalState",
    "Operator",
    "Pit",
    "QualitySpecification",
    "Relationship",
    "RelationshipError",
    "RelationshipKind",
    "RigidHaulTruck",
    "Route",
    "SafetyEventType",
    "Shift",
    "ShiftCalendar",
    "ShiftPattern",
    "SpeedLimitMap",
    "Stope",
    "UnknownEntityTypeError",
    "WaterTruck",
    "WheelLoader",
    "Zone",
    "register_equipment",
]
