"""Tests for mineproductivity.simulation.discovery."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from mineproductivity.core import InMemoryRepository
from mineproductivity.simulation._registry import register
from mineproductivity.simulation.abstractions import SimulationContext
from mineproductivity.simulation.discovery import by_category, by_scope
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.montecarlo import MonteCarloModel
from mineproductivity.simulation.result import SimulationResult
from mineproductivity.simulation.run import RunStatus, SimulationRun
from mineproductivity.simulation.scenario import Scenario, publish_scenario
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


@register
class _DiscoveryMcModel(MonteCarloModel):
    meta = SimulationMetadata(
        code="MONTECARLO.DiscoveryModel",
        category=SimulationCategory.MONTE_CARLO,
        description="A Monte Carlo model for discovery tests.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        return SimulationResult()


def _published_scenario_code() -> str:
    code = f"TEST.DiscoveryScenario.{uuid.uuid4().hex}"
    publish_scenario(
        Scenario(
            code=code,
            model_code="MONTECARLO.DiscoveryModel",
            time_horizon=timedelta(hours=1),
        )
    )
    return code


def _run(run_id: str, scenario_code: str, **attributes: object) -> SimulationRun:
    return SimulationRun(
        id=run_id,
        scenario_code=scenario_code,
        state=SimulationState(
            attributes=attributes or {"provisioned": True}, simulated_time=_EPOCH
        ),
    )


class TestByCategory:
    def test_matches_runs_whose_published_scenario_model_is_in_category(self) -> None:
        code = _published_scenario_code()
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", code))
        matched = repository.list(by_category(SimulationCategory.MONTE_CARLO))
        assert [run.id for run in matched] == ["RUN-1"]

    def test_wrong_category_matches_nothing(self) -> None:
        code = _published_scenario_code()
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", code))
        assert list(repository.list(by_category(SimulationCategory.SYSTEM_DYNAMICS))) == []

    def test_unpublished_scenario_never_matches_and_never_raises(self) -> None:
        """Design spec §22: an empty sequence is a legitimate answer."""
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", "TEST.NeverPublished"))
        assert list(repository.list(by_category(SimulationCategory.MONTE_CARLO))) == []

    def test_published_scenario_with_an_unregistered_model_never_matches(self) -> None:
        scenario_code = f"TEST.DiscoveryUnregistered.{uuid.uuid4().hex}"
        publish_scenario(
            Scenario(
                code=scenario_code,
                model_code=f"MONTECARLO.NeverRegistered{uuid.uuid4().hex}",
                time_horizon=timedelta(hours=1),
            )
        )
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", scenario_code))
        assert list(repository.list(by_category(SimulationCategory.MONTE_CARLO))) == []

    def test_non_simulation_metadata_registration_never_matches(self) -> None:
        """A registry entry carrying plain ``BaseMetadata`` (not
        ``SimulationMetadata``) cannot resolve to a category -- the
        run simply does not match, never raises (§22)."""
        from mineproductivity.core import BaseMetadata
        from mineproductivity.simulation._registry import REGISTRY

        odd_code = f"MONTECARLO.OddMeta{uuid.uuid4().hex}"
        REGISTRY.register(odd_code, _DiscoveryMcModel, metadata=BaseMetadata(name=odd_code))
        scenario_code = f"TEST.DiscoveryOdd.{uuid.uuid4().hex}"
        publish_scenario(
            Scenario(code=scenario_code, model_code=odd_code, time_horizon=timedelta(hours=1))
        )
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", scenario_code))
        assert list(repository.list(by_category(SimulationCategory.MONTE_CARLO))) == []


class TestByScope:
    def test_matches_on_scenario_code(self) -> None:
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", "TEST.ScopeA"))
        repository.add(_run("RUN-2", "TEST.ScopeB"))
        matched = repository.list(by_scope({"scenario_code": "TEST.ScopeA"}))
        assert [run.id for run in matched] == ["RUN-1"]

    def test_matches_on_status_value(self) -> None:
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", "TEST.ScopeA"))
        repository.add(
            _run("RUN-2", "TEST.ScopeA").with_state(
                SimulationState(attributes={"provisioned": True}, simulated_time=_EPOCH),
                status=RunStatus.COMPLETED,
            )
        )
        matched = repository.list(by_scope({"status": "completed"}))
        assert [run.id for run in matched] == ["RUN-2"]

    def test_matches_on_state_attributes(self) -> None:
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", "TEST.ScopeA", pit="north"))
        repository.add(_run("RUN-2", "TEST.ScopeA", pit="south"))
        matched = repository.list(by_scope({"pit": "north"}))
        assert [run.id for run in matched] == ["RUN-1"]

    def test_every_requested_key_must_match(self) -> None:
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", "TEST.ScopeA", pit="north"))
        assert list(repository.list(by_scope({"pit": "north", "scenario_code": "OTHER"}))) == []

    def test_composes_with_the_core_operators(self) -> None:
        code = _published_scenario_code()
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", code, pit="north"))
        repository.add(_run("RUN-2", code, pit="south"))
        matched = repository.list(
            by_category(SimulationCategory.MONTE_CARLO) & by_scope({"pit": "north"})
        )
        assert [run.id for run in matched] == ["RUN-1"]

    def test_requested_scope_is_copied_not_aliased(self) -> None:
        wanted = {"pit": "north"}
        specification = by_scope(wanted)
        wanted["pit"] = "south"
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", "TEST.ScopeA", pit="north"))
        assert [run.id for run in repository.list(specification)] == ["RUN-1"]
