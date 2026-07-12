"""Tests for mineproductivity.simulation.executor -- design spec §10's
sequence diagram, including the cache-hit and cache-miss seeding paths
(§26) and the lifecycle transitions (§10's state diagram)."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from mineproductivity.core import InMemoryRepository, NotFoundError
from mineproductivity.digital_twin import TwinSnapshot, TwinState, TwinStatus
from mineproductivity.events import AsOf, CycleEvent
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.identifier import EventID
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.events.versioning import EventVersion
from mineproductivity.simulation import executor as executor_module
from mineproductivity.simulation._registry import register
from mineproductivity.simulation.abstractions import SimulationContext, SimulationModel
from mineproductivity.simulation.caching import SimulationStateCache
from mineproductivity.simulation.clock import SimulationClock, TimeProgressionMode
from mineproductivity.simulation.discrete_event import DiscreteEventModel
from mineproductivity.simulation.exceptions import (
    SimulationExecutionError,
    SimulationRunNotFoundError,
    SimulationValidationError,
)
from mineproductivity.simulation.executor import SimulationExecutor
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.montecarlo import MonteCarloModel
from mineproductivity.simulation.result import SimulationResult
from mineproductivity.simulation.run import RunStatus, SimulationRun
from mineproductivity.simulation.scenario import Scenario
from mineproductivity.simulation.state import SimulationState
from mineproductivity.simulation.system_dynamics import SystemDynamicsModel

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


@register
class _McModel(MonteCarloModel):
    meta = SimulationMetadata(
        code="MONTECARLO.ExecutorSeeded",
        category=SimulationCategory.MONTE_CARLO,
        description="Outcome is a pure function of the supplied seed.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        outcome = random.Random(random_seed).uniform(0.0, 100.0)
        return SimulationResult(
            final_state=SimulationState(attributes={"outcome": outcome}, simulated_time=_EPOCH)
        )


@register
class _McNoFinalState(MonteCarloModel):
    meta = SimulationMetadata(
        code="MONTECARLO.ExecutorNoFinal",
        category=SimulationCategory.MONTE_CARLO,
        description="Returns a warning-carrying result without a final state.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        return SimulationResult(warnings=("nothing to project",))


@register
class _McRaises(MonteCarloModel):
    meta = SimulationMetadata(
        code="MONTECARLO.ExecutorRaises",
        category=SimulationCategory.MONTE_CARLO,
        description="Raises for any trial.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        raise RuntimeError("model blew up")


@register
class _DesModel(DiscreteEventModel):
    meta = SimulationMetadata(
        code="DISCRETEEVENT.ExecutorQueue",
        category=SimulationCategory.DISCRETE_EVENT,
        description="Serves one queued event per advance, ten minutes apart.",
    )

    def _advance(
        self, state: SimulationState, *, context: SimulationContext
    ) -> tuple[SimulationState, timedelta]:
        served = int(state.attributes.get("served", 0)) + 1
        return (
            SimulationState(attributes={"served": served}, simulated_time=state.simulated_time),
            timedelta(minutes=10),
        )


@register
class _DesBadDelta(DiscreteEventModel):
    meta = SimulationMetadata(
        code="DISCRETEEVENT.ExecutorStuck",
        category=SimulationCategory.DISCRETE_EVENT,
        description="Returns a non-positive delta.",
    )

    def _advance(
        self, state: SimulationState, *, context: SimulationContext
    ) -> tuple[SimulationState, timedelta]:
        return state, timedelta(0)


@register
class _SdModel(SystemDynamicsModel):
    meta = SimulationMetadata(
        code="SYSTEMDYNAMICS.ExecutorStock",
        category=SimulationCategory.SYSTEM_DYNAMICS,
        description="Accumulates one unit per simulated minute.",
    )

    def _step(
        self, state: SimulationState, *, context: SimulationContext, dt: timedelta
    ) -> SimulationState:
        level = float(state.attributes.get("level", 0.0)) + dt.total_seconds() / 60.0
        return SimulationState(attributes={"level": level}, simulated_time=state.simulated_time)


@register
class _CalibrationCategory(SimulationModel):
    meta = SimulationMetadata(
        code="CALIBRATION.ExecutorFit",
        category=SimulationCategory.CALIBRATION,
        description="A calibration-category registration; not forward-executable.",
    )


class _FakeStore: ...


_TRIAL_CLOCK = SimulationClock(mode=TimeProgressionMode.TRIAL_BASED)
_EVENT_CLOCK = SimulationClock(mode=TimeProgressionMode.NEXT_EVENT)
_STEP_CLOCK = SimulationClock(mode=TimeProgressionMode.FIXED_TIMESTEP, dt=timedelta(minutes=10))


def _scenario(model_code: str = "MONTECARLO.ExecutorSeeded", **overrides: object) -> Scenario:
    fields: dict[str, object] = {
        "code": "TEST.ExecutorScenario",
        "model_code": model_code,
        "time_horizon": timedelta(minutes=30),
    }
    fields.update(overrides)
    return Scenario(**fields)  # type: ignore[arg-type]


def _provisioned(
    run_id: str = "RUN-1", *, status: RunStatus = RunStatus.SCHEDULED
) -> InMemoryRepository[SimulationRun, str]:
    repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    repository.add(
        SimulationRun(
            id=run_id,
            scenario_code="TEST.ExecutorScenario",
            state=SimulationState(attributes={"provisioned": True}, simulated_time=_EPOCH),
            status=status,
        )
    )
    return repository


def _context() -> SimulationContext:
    return SimulationContext(event_store=_FakeStore())


class TestMonteCarloDispatch:
    def test_happy_path_completes_the_run_with_the_trial_final_state(self) -> None:
        repository = _provisioned()
        executor = SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK)
        result = executor.execute("RUN-1", _scenario(), context=_context(), random_seed=42)
        assert result.run_id == "RUN-1"
        assert result.final_state is not None
        assert repository.get("RUN-1").status is RunStatus.COMPLETED
        assert repository.get("RUN-1").state == result.final_state

    def test_reproducible_across_identical_seeds(self) -> None:
        first_repo = _provisioned()
        second_repo = _provisioned()
        first = SimulationExecutor(repository=first_repo, clock=_TRIAL_CLOCK).execute(
            "RUN-1", _scenario(), context=_context(), random_seed=7
        )
        second = SimulationExecutor(repository=second_repo, clock=_TRIAL_CLOCK).execute(
            "RUN-1", _scenario(), context=_context(), random_seed=7
        )
        assert first.final_state == second.final_state

    def test_trial_without_final_state_falls_back_to_the_seeded_state(self) -> None:
        repository = _provisioned()
        executor = SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK)
        result = executor.execute(
            "RUN-1", _scenario("MONTECARLO.ExecutorNoFinal"), context=_context()
        )
        assert result.warnings == ("nothing to project",)
        assert result.final_state is not None
        assert result.final_state.attributes["provisioned"] is True

    def test_never_mutates_the_run_instance_it_read(self) -> None:
        repository = _provisioned()
        original = repository.get("RUN-1")
        SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK).execute(
            "RUN-1", _scenario(), context=_context()
        )
        assert original.status is RunStatus.SCHEDULED
        assert original.state.attributes == {"provisioned": True}


class TestLifecycle:
    def test_completed_is_terminal(self) -> None:
        repository = _provisioned(status=RunStatus.COMPLETED)
        result = SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK).execute(
            "RUN-1", _scenario(), context=_context()
        )
        assert "completed is terminal" in result.warnings[0]
        assert repository.get("RUN-1").status is RunStatus.COMPLETED

    def test_failed_is_terminal(self) -> None:
        repository = _provisioned(status=RunStatus.FAILED)
        result = SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK).execute(
            "RUN-1", _scenario(), context=_context()
        )
        assert "failed is terminal" in result.warnings[0]

    def test_paused_resumes_to_running_then_completes(self) -> None:
        repository = _provisioned(status=RunStatus.PAUSED)
        SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK).execute(
            "RUN-1", _scenario(), context=_context()
        )
        assert repository.get("RUN-1").status is RunStatus.COMPLETED

    def test_model_failure_marks_the_run_failed_and_raises(self) -> None:
        repository = _provisioned()
        executor = SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK)
        with pytest.raises(SimulationExecutionError, match="ExecutorRaises"):
            executor.execute("RUN-1", _scenario("MONTECARLO.ExecutorRaises"), context=_context())
        assert repository.get("RUN-1").status is RunStatus.FAILED


class TestValidationAndDispatchGuards:
    def test_unknown_run_id_raises(self) -> None:
        executor = SimulationExecutor(repository=_provisioned(), clock=_TRIAL_CLOCK)
        with pytest.raises(SimulationRunNotFoundError, match="NO-SUCH-RUN"):
            executor.execute("NO-SUCH-RUN", _scenario(), context=_context())

    def test_unregistered_model_code_raises(self) -> None:
        executor = SimulationExecutor(repository=_provisioned(), clock=_TRIAL_CLOCK)
        with pytest.raises(SimulationRunNotFoundError, match="No SimulationModel"):
            executor.execute("RUN-1", _scenario("MONTECARLO.NotRegistered"), context=_context())

    def test_calibration_category_is_not_forward_executable(self) -> None:
        executor = SimulationExecutor(repository=_provisioned(), clock=_TRIAL_CLOCK)
        with pytest.raises(SimulationValidationError, match="not forward-executable"):
            executor.execute("RUN-1", _scenario("CALIBRATION.ExecutorFit"), context=_context())

    def test_clock_mode_must_match_the_registered_category(self) -> None:
        executor = SimulationExecutor(repository=_provisioned(), clock=_EVENT_CLOCK)
        with pytest.raises(SimulationValidationError, match="requires a SimulationClock"):
            executor.execute("RUN-1", _scenario(), context=_context())


class TestSeeding:
    def test_snapshot_starting_condition_seeds_from_the_twin_snapshot(self) -> None:
        snapshot = TwinSnapshot(
            twin_id="FLEET-NORTH",
            state=TwinState(attributes={"trucks": 24}, captured_at=_EPOCH),
            status=TwinStatus.SYNCHRONIZED,
            as_of=AsOf(utc=_EPOCH + timedelta(hours=1)),
        )
        repository = _provisioned()
        result = SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK).execute(
            "RUN-1",
            _scenario("MONTECARLO.ExecutorNoFinal", initial_state=snapshot),
            context=_context(),
        )
        assert result.final_state is not None
        assert result.final_state.attributes["trucks"] == 24
        assert result.final_state.simulated_time == _EPOCH + timedelta(hours=1)

    def test_replay_seeding_caches_on_miss_and_reuses_on_hit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Design spec §26: a miss is the ordinary first-trial path;
        every subsequent trial sharing the key takes the hit branch."""
        store = _InMemoryEventStore()
        moment = _EPOCH
        envelope: EventEnvelope[CycleEvent] = EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=CycleEvent(
                equipment_id="HT-1",
                shift_id="A",
                queue_min=1.0,
                spot_min=0.5,
                load_min=2.0,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
            ),
            event_time_utc=moment,
            processing_time_utc=moment,
            ingestion_time_utc=moment,
            metadata=EventMetadata(name="cycle", source_system="test"),
        )
        assert store.append(envelope).is_ok

        calls = {"count": 0}
        real_seed = executor_module.seed_from_replay

        def _counting_seed(inner_store: Any, as_of: AsOf) -> SimulationState:
            calls["count"] += 1
            return real_seed(inner_store, as_of)

        monkeypatch.setattr(executor_module, "seed_from_replay", _counting_seed)

        cache = SimulationStateCache()
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        for run_id in ("RUN-A", "RUN-B"):
            repository.add(
                SimulationRun(
                    id=run_id,
                    scenario_code="TEST.ExecutorScenario",
                    state=SimulationState(attributes={"provisioned": True}, simulated_time=_EPOCH),
                )
            )
        executor = SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK, cache=cache)
        scenario = _scenario(
            "MONTECARLO.ExecutorNoFinal", as_of=AsOf(utc=_EPOCH + timedelta(hours=1))
        )
        context = SimulationContext(event_store=store)

        first = executor.execute("RUN-A", scenario, context=context)
        second = executor.execute("RUN-B", scenario, context=context)
        assert calls["count"] == 1  # miss then hit
        assert first.final_state == second.final_state
        assert first.final_state is not None
        assert first.final_state.attributes["events_replayed"] == 1

    def test_without_snapshot_or_as_of_the_provisioned_state_seeds(self) -> None:
        repository = _provisioned()
        result = SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK).execute(
            "RUN-1", _scenario("MONTECARLO.ExecutorNoFinal"), context=_context()
        )
        assert result.final_state is not None
        assert result.final_state.attributes == {"provisioned": True}


class TestDiscreteEventDispatch:
    def test_advances_until_the_time_horizon_is_reached(self) -> None:
        repository = _provisioned()
        executor = SimulationExecutor(repository=repository, clock=_EVENT_CLOCK)
        result = executor.execute(
            "RUN-1",
            _scenario("DISCRETEEVENT.ExecutorQueue", time_horizon=timedelta(minutes=30)),
            context=_context(),
        )
        assert result.final_state is not None
        assert result.final_state.attributes["served"] == 3  # 3 x 10min = 30min
        assert result.final_state.simulated_time == _EPOCH + timedelta(minutes=30)
        assert repository.get("RUN-1").status is RunStatus.COMPLETED

    def test_zero_horizon_is_a_warning_not_a_raise(self) -> None:
        repository = _provisioned()
        executor = SimulationExecutor(repository=repository, clock=_EVENT_CLOCK)
        result = executor.execute(
            "RUN-1",
            _scenario("DISCRETEEVENT.ExecutorQueue", time_horizon=timedelta(0)),
            context=_context(),
        )
        assert result.warnings == ("time_horizon produced zero steps; state unchanged",)
        assert repository.get("RUN-1").status is RunStatus.COMPLETED

    def test_non_positive_delta_fails_loudly(self) -> None:
        repository = _provisioned()
        executor = SimulationExecutor(repository=repository, clock=_EVENT_CLOCK)
        with pytest.raises(SimulationExecutionError, match="non-positive delta"):
            executor.execute("RUN-1", _scenario("DISCRETEEVENT.ExecutorStuck"), context=_context())
        assert repository.get("RUN-1").status is RunStatus.FAILED


class TestSystemDynamicsDispatch:
    def test_steps_the_fixed_timestep_until_the_horizon_is_covered(self) -> None:
        repository = _provisioned()
        executor = SimulationExecutor(repository=repository, clock=_STEP_CLOCK)
        result = executor.execute(
            "RUN-1",
            _scenario("SYSTEMDYNAMICS.ExecutorStock", time_horizon=timedelta(minutes=15)),
            context=_context(),
        )
        assert result.final_state is not None
        assert result.final_state.attributes["level"] == 20.0  # ceil(15/10) = 2 steps
        assert result.final_state.simulated_time == _EPOCH + timedelta(minutes=20)


class TestRepositoryConflictTranslation:
    class _VanishingRepository(InMemoryRepository[SimulationRun, str]):
        def remove(self, entity_id: str) -> None:
            raise NotFoundError(f"{entity_id!r} vanished mid-swap")

    def test_serialization_violation_becomes_execution_error(self) -> None:
        repository = self._VanishingRepository()
        InMemoryRepository.add(
            repository,
            SimulationRun(
                id="RUN-1",
                scenario_code="TEST.ExecutorScenario",
                state=SimulationState(attributes={"provisioned": True}, simulated_time=_EPOCH),
            ),
        )
        executor = SimulationExecutor(repository=repository, clock=_TRIAL_CLOCK)
        with pytest.raises(SimulationExecutionError, match="write serialization"):
            executor.execute("RUN-1", _scenario(), context=_context())


class TestRepr:
    def test_repr_names_the_collaborators(self) -> None:
        executor = SimulationExecutor(repository=_provisioned(), clock=_TRIAL_CLOCK)
        assert "SimulationExecutor" in repr(executor)
