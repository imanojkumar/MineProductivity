"""``mineproductivity.simulation`` -- the platform's projection layer,
built directly on top of ``digital_twin``.

Answers a question none of the seven packages below it were ever meant
to answer: *given a scenario -- a hypothetical or historical starting
condition and a set of parameters -- how does this mining system
evolve over time, and how confident should we be in that projection?*
``digital_twin`` represents what a system currently looks like;
``decision`` defines a stable interface for reasoning about
hypothetical business outcomes; neither implements an actual
forward-projection algorithm, by design. ``simulation`` supplies that
missing algorithmic layer -- scenario management, time-stepped or
event-stepped execution, experiment orchestration, and calibration
against history -- while still declining to choose *which* Monte
Carlo, discrete-event, or system-dynamics algorithm is correct for any
given site, leaving that choice to pluggable, independently-versioned
models (design spec §1, §13-§16).

The complete package (design spec §6's twenty-one modules) is
implemented: ``SimulationModel``/``SimulationContext`` (§8, no shared
abstract execution method by design); ``SimulationMetadata``/
``SimulationCategory`` (§29); ``Scenario``/``ScenarioStatus`` as a
versioned, governed artifact (§9); ``SimulationRun`` (a
``core.BaseEntity[str]`` subclass, the second entity-shaped package in
the series)/``RunStatus``/``SimulationExecutor`` (§10);
``SimulationState`` (§10)/``SimulationClock``/``TimeProgressionMode``
(§11); ``seed_from_replay`` (§12); the four interface-only ABCs --
``MonteCarloModel``, ``DiscreteEventModel``, ``SystemDynamicsModel``,
``CalibrationModel`` -- with zero concrete subclasses by design
(§13-§16, ADR-0009); ``Experiment``/``ExperimentRunner`` (§17);
``ScenarioComparator``/``SensitivityAnalyzer``, which delegate every
statistical judgment to ``analytics`` (§19-§20);
``by_category``/``by_scope`` discovery (§22);
``SimulationRunRepository`` as a literal ``type`` alias over
``core.BaseRepository[SimulationRun, str]`` (§24);
``SimulationStateCache`` (§26); the
``SimulationResult``/``ExperimentResult`` family (§18);
``REGISTRY``/``register`` (§21); and the full exception hierarchy. It
holds no KPI formulas, no statistical computation of its own, no
business-decision logic, no optimization search, no AI-agent
reasoning, no rendering, and no telemetry ingestion (§3).

``simulation`` depends on ``core``, ``ontology``, ``events``,
``registry``, ``plugins``, ``connectors``, ``kpis``, ``analytics``,
``decision``, and ``digital_twin`` -- and MUST NEVER import
``optimization``, ``agents``, or ``visualization``, none of which this
package may see.
"""

from __future__ import annotations

from mineproductivity.simulation._registry import REGISTRY, register
from mineproductivity.simulation.abstractions import SimulationContext, SimulationModel
from mineproductivity.simulation.caching import SimulationStateCache
from mineproductivity.simulation.calibration import CalibrationModel
from mineproductivity.simulation.clock import SimulationClock, TimeProgressionMode
from mineproductivity.simulation.comparison import ScenarioComparator
from mineproductivity.simulation.discovery import by_category, by_scope
from mineproductivity.simulation.discrete_event import DiscreteEventModel
from mineproductivity.simulation.exceptions import (
    ScenarioConflictError,
    SimulationExecutionError,
    SimulationRunNotFoundError,
    SimulationValidationError,
    SimulationVersionConflictError,
)
from mineproductivity.simulation.executor import SimulationExecutor
from mineproductivity.simulation.experiment import Experiment, ExperimentRunner
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.montecarlo import MonteCarloModel
from mineproductivity.simulation.persistence import SimulationRunRepository
from mineproductivity.simulation.replay import seed_from_replay
from mineproductivity.simulation.result import ExperimentResult, SimulationResult
from mineproductivity.simulation.run import RunStatus, SimulationRun
from mineproductivity.simulation.scenario import Scenario, ScenarioStatus
from mineproductivity.simulation.sensitivity import SensitivityAnalyzer
from mineproductivity.simulation.state import SimulationState
from mineproductivity.simulation.system_dynamics import SystemDynamicsModel

__all__ = [
    "CalibrationModel",
    "DiscreteEventModel",
    "Experiment",
    "ExperimentResult",
    "ExperimentRunner",
    "MonteCarloModel",
    "REGISTRY",
    "RunStatus",
    "Scenario",
    "ScenarioComparator",
    "ScenarioConflictError",
    "ScenarioStatus",
    "SensitivityAnalyzer",
    "SimulationCategory",
    "SimulationClock",
    "SimulationContext",
    "SimulationExecutionError",
    "SimulationExecutor",
    "SimulationMetadata",
    "SimulationModel",
    "SimulationResult",
    "SimulationRun",
    "SimulationRunNotFoundError",
    "SimulationRunRepository",
    "SimulationState",
    "SimulationStateCache",
    "SimulationValidationError",
    "SimulationVersionConflictError",
    "SystemDynamicsModel",
    "TimeProgressionMode",
    "by_category",
    "by_scope",
    "register",
    "seed_from_replay",
]
