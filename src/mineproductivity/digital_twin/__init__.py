"""``mineproductivity.digital_twin`` -- the platform's stateful
representation layer, built directly on top of ``decision``.

Answers a question none of the six packages below it were ever meant to
answer: *what is the current, holistic condition of this physical
asset, operation, or process, and how do we keep that understanding
synchronized with reality over time?* ``kpis`` computes a single
metric's value; ``analytics`` characterizes a series statistically;
``decision`` turns a statistical judgment into a recommended action --
all point-in-time or series-oriented computations over
already-recorded facts. ``digital_twin`` holds a continuously-updated
virtual counterpart of a mine, a piece of equipment, a plant, a
conveyor, a fleet, or another real-world system, synchronized from the
immutable event stream ``events`` already owns, and exposes that
representation -- plus an interface for simulating hypothetical futures
over it -- to whatever consumes it next (design spec §1).

The complete package (design spec §6's fifteen modules) is implemented:
``Twin`` (a ``core.BaseEntity[str]`` subclass -- the first package in
the series whose central abstraction is entity-shaped rather than
stateless, §8)/``TwinContext``; ``TwinMetadata``/``TwinCategory``
(§26); the eleven category base classes (§9); ``TwinStatus`` (§10);
``TwinState`` (§12)/``TwinSnapshot`` (§13); ``TwinSynchronizer``/
``SyncPolicy`` (§11, §15); ``TelemetryReading`` (§16); the
interface-only ``TwinSimulationModel`` with zero concrete subclasses by
design (§14, ADR-0008); ``by_category``/``by_scope`` discovery
factories (§18); ``TwinRepository`` as a literal ``type`` alias over
``core.BaseRepository[Twin, str]`` (§20); ``TwinStateCache`` (§22);
the ``TwinResult``/``SyncResult``/``TwinSimulationResult`` family
(§25); ``REGISTRY``/``register`` (§17); and the full exception
hierarchy. It holds no KPI formulas, no statistical computation, no
business-decision logic, no optimization search, and no AI-agent
reasoning -- all of those already exist, one or more layers down, and
are consumed rather than re-implemented (§3).

``digital_twin`` depends on ``core``, ``ontology``, ``events``,
``registry``, ``plugins``, ``connectors``, ``kpis``, ``analytics``, and
``decision`` -- and MUST NEVER import ``simulation``, ``optimization``,
``agents``, or ``visualization``, none of which this package may see.
"""

from __future__ import annotations

from mineproductivity.digital_twin._registry import REGISTRY, register
from mineproductivity.digital_twin.abstractions import Twin, TwinContext
from mineproductivity.digital_twin.caching import TwinStateCache
from mineproductivity.digital_twin.categories import (
    ConveyorTwin,
    EquipmentTwin,
    FleetTwin,
    GeologicalTwin,
    HaulageTwin,
    MineTwin,
    PlantTwin,
    ProcessingPlantTwin,
    ProductionTwin,
    StockpileTwin,
    VentilationTwin,
)
from mineproductivity.digital_twin.discovery import by_category, by_scope
from mineproductivity.digital_twin.exceptions import (
    TwinNotFoundError,
    TwinStateConflictError,
    TwinSyncError,
    TwinValidationError,
    TwinVersionConflictError,
)
from mineproductivity.digital_twin.lifecycle import TwinStatus
from mineproductivity.digital_twin.metadata import TwinCategory, TwinMetadata
from mineproductivity.digital_twin.persistence import TwinRepository
from mineproductivity.digital_twin.result import SyncResult, TwinResult, TwinSimulationResult
from mineproductivity.digital_twin.simulation import TwinSimulationModel
from mineproductivity.digital_twin.snapshot import TwinSnapshot
from mineproductivity.digital_twin.state import TwinState
from mineproductivity.digital_twin.synchronization import SyncPolicy, TwinSynchronizer
from mineproductivity.digital_twin.telemetry import TelemetryReading

__all__ = [
    "ConveyorTwin",
    "EquipmentTwin",
    "FleetTwin",
    "GeologicalTwin",
    "HaulageTwin",
    "MineTwin",
    "PlantTwin",
    "ProcessingPlantTwin",
    "ProductionTwin",
    "REGISTRY",
    "StockpileTwin",
    "SyncPolicy",
    "SyncResult",
    "TelemetryReading",
    "Twin",
    "TwinCategory",
    "TwinContext",
    "TwinMetadata",
    "TwinNotFoundError",
    "TwinRepository",
    "TwinResult",
    "TwinSimulationModel",
    "TwinSimulationResult",
    "TwinSnapshot",
    "TwinState",
    "TwinStateCache",
    "TwinStateConflictError",
    "TwinStatus",
    "TwinSyncError",
    "TwinSynchronizer",
    "TwinValidationError",
    "TwinVersionConflictError",
    "VentilationTwin",
    "by_category",
    "by_scope",
    "register",
]
