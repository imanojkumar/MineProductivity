"""``SimulationExecutor``: orchestrates one ``SimulationRun`` (design
spec §10).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
Dispatch reads the registered model's ``SimulationCategory`` off
``Scenario.model_code`` (via ``REGISTRY``), never branching on the
model's concrete Python type (design spec §10). Seeding reuses
``seed_from_replay``/``SimulationStateCache`` (§12, §26) and, for a
snapshot-anchored scenario, ``digital_twin.TwinSnapshot``'s own state
directly -- nothing here re-derives a twin's condition (§3.2). The
``remove``-then-``add`` pair against ``SimulationRunRepository`` is
this package's own instance of the single, narrow mutable operation
every prior package concentrates its mutation into (§10);
``core.BaseRepository`` exposes no dedicated "replace" method, and a
conforming production repository makes the pair atomic per ``run_id``
(§32) -- a violation surfaces as ``SimulationExecutionError`` (§28).

Two small, disclosed resolutions beyond §10's bare pseudocode: (1)
``execute`` accepts an additive, defaulted ``random_seed`` keyword --
``MonteCarloModel._trial``'s own signature (§13) requires one, and
``ExperimentRunner`` (§17) is the party responsible for supplying a
distinct seed per trial *through* this method; (2) registered models
are instantiated with a no-argument constructor, the same convention
``kpis.KPIEngine`` applies to registered KPI classes -- a model's
tunable inputs arrive via ``Scenario.parameters``, never constructor
state (§29's statelessness rule).
"""

from __future__ import annotations

import math
from datetime import timedelta

from mineproductivity.core import DuplicateError, NotFoundError
from mineproductivity.registry import UnregisteredLookupError

from mineproductivity.simulation._registry import REGISTRY
from mineproductivity.simulation.abstractions import SimulationContext, SimulationModel
from mineproductivity.simulation.caching import SimulationStateCache
from mineproductivity.simulation.clock import SimulationClock, TimeProgressionMode
from mineproductivity.simulation.discrete_event import DiscreteEventModel
from mineproductivity.simulation.exceptions import (
    SimulationExecutionError,
    SimulationRunNotFoundError,
    SimulationValidationError,
)
from mineproductivity.simulation.metadata import SimulationCategory
from mineproductivity.simulation.montecarlo import MonteCarloModel
from mineproductivity.simulation.persistence import SimulationRunRepository
from mineproductivity.simulation.replay import seed_from_replay
from mineproductivity.simulation.result import SimulationResult
from mineproductivity.simulation.run import RunStatus, SimulationRun
from mineproductivity.simulation.scenario import Scenario
from mineproductivity.simulation.state import SimulationState
from mineproductivity.simulation.system_dynamics import SystemDynamicsModel

__all__ = ["SimulationExecutor"]

#: Which clock pacing each forward-executable category requires (§11):
#: the executor selects the applicable ``TimeProgressionMode`` from the
#: registered category and verifies the injected clock matches, never
#: inspecting the model's concrete type.
_MODE_BY_CATEGORY = {
    SimulationCategory.MONTE_CARLO: TimeProgressionMode.TRIAL_BASED,
    SimulationCategory.DISCRETE_EVENT: TimeProgressionMode.NEXT_EVENT,
    SimulationCategory.SYSTEM_DYNAMICS: TimeProgressionMode.FIXED_TIMESTEP,
}


class SimulationExecutor:
    """Orchestrates one ``SimulationRun``: fetches the current instance
    from a ``SimulationRunRepository``, seeds the initial
    ``SimulationState`` (snapshot, cached replay, or the run's own
    provisioned state), dispatches to the registered model's
    category-specific method, advances the ``SimulationClock``, and
    persists each produced state -- design spec §10's sequence diagram,
    exactly.
    """

    def __init__(
        self,
        *,
        repository: SimulationRunRepository,
        clock: SimulationClock,
        cache: SimulationStateCache | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._cache = cache

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(repository={self._repository!r}, "
            f"clock={self._clock!r}, cache={self._cache!r})"
        )

    def execute(
        self,
        run_id: str,
        scenario: Scenario,
        *,
        context: SimulationContext,
        random_seed: int = 0,
    ) -> SimulationResult:
        """Execute ``scenario`` for the run stored under ``run_id``.

        A run already ``Completed``/``Failed`` is terminal (design spec
        §10): execution is skipped and a warning-carrying
        ``SimulationResult`` returned, never a raise. A zero-length
        ``time_horizon`` is a legitimately incomplete input (§28):
        zero steps execute, the seeded state is final, and the result
        carries a warning.

        Raises
        ------
        SimulationRunNotFoundError
            If no run is stored under ``run_id``, or no
            ``SimulationModel`` is registered for
            ``scenario.model_code``.
        SimulationValidationError
            If the model's category is not forward-executable
            (``CALIBRATION``), or the injected clock's mode does not
            match the category's required ``TimeProgressionMode``.
        SimulationExecutionError
            If the model's category method raised for a structurally
            valid input (the run is marked ``Failed`` first, §10), a
            ``DiscreteEventModel`` returned a non-positive delta, or
            the repository's per-id write serialization contract was
            violated mid-swap (§32).
        """
        maybe_run = self._repository.find(run_id)
        if maybe_run.is_nothing:
            raise SimulationRunNotFoundError(f"No simulation run is stored under id {run_id!r}")
        run = maybe_run.unwrap()

        if run.status in (RunStatus.COMPLETED, RunStatus.FAILED):
            return SimulationResult(
                run_id=run_id,
                warnings=(
                    f"run is {run.status.value}; execution skipped "
                    f"({run.status.value} is terminal)",
                ),
                final_state=run.state,
            )

        try:
            model_cls = REGISTRY.get(scenario.model_code)
        except UnregisteredLookupError as exc:
            raise SimulationRunNotFoundError(
                f"No SimulationModel is registered for code {scenario.model_code!r}"
            ) from exc
        category = model_cls.meta.category
        if category not in _MODE_BY_CATEGORY:
            raise SimulationValidationError(
                f"SimulationModel {scenario.model_code!r} belongs to category "
                f"{category!r}, which is not forward-executable (§10 dispatches "
                f"only _trial/_advance/_step)"
            )
        if self._clock.mode is not _MODE_BY_CATEGORY[category]:
            raise SimulationValidationError(
                f"category {category!r} requires a SimulationClock in "
                f"{_MODE_BY_CATEGORY[category]!r} mode, got {self._clock.mode!r}"
            )

        state = self._seed(run, scenario, context)
        run = run.with_state(state, status=RunStatus.RUNNING)
        self._replace(run_id, run)

        model = model_cls()
        try:
            if category is SimulationCategory.MONTE_CARLO:
                assert isinstance(model, MonteCarloModel)
                result = model._trial(scenario, context=context, random_seed=random_seed)
                final_state = result.final_state if result.final_state is not None else state
                warnings = result.warnings
            else:
                final_state, warnings = self._run_timed(model, run_id, run, scenario, context)
        except SimulationExecutionError:
            self._replace(run_id, run.with_state(run.state, status=RunStatus.FAILED))
            raise
        except Exception as exc:
            self._replace(run_id, run.with_state(run.state, status=RunStatus.FAILED))
            raise SimulationExecutionError(
                f"SimulationModel {scenario.model_code!r} raised for a structurally "
                f"valid input on run {run_id!r}: {exc}"
            ) from exc

        self._replace(run_id, run.with_state(final_state, status=RunStatus.COMPLETED))
        return SimulationResult(run_id=run_id, warnings=warnings, final_state=final_state)

    def _seed(
        self, run: SimulationRun, scenario: Scenario, context: SimulationContext
    ) -> SimulationState:
        """The §10 seeding paths, in order of specificity: an explicit
        ``TwinSnapshot`` starting condition (§9), a cached or freshly
        replayed historical seed (§12, §26 -- a cache miss is the
        ordinary first-trial path, not an error), else the run's own
        provisioned state."""
        if scenario.initial_state is not None:
            snapshot = scenario.initial_state
            anchored = (
                snapshot.as_of.utc if snapshot.as_of.utc is not None else snapshot.state.captured_at
            )
            return SimulationState(
                attributes=dict(snapshot.state.attributes), simulated_time=anchored
            )
        if scenario.as_of is not None:
            if self._cache is not None:
                cached = self._cache.get(scenario.code, scenario.as_of)
                if cached is not None:
                    return cached
            seeded = seed_from_replay(context.event_store, scenario.as_of)
            if self._cache is not None:
                self._cache.put(scenario.code, scenario.as_of, seeded)
            return seeded
        return run.state

    def _run_timed(
        self,
        model: SimulationModel,
        run_id: str,
        run: SimulationRun,
        scenario: Scenario,
        context: SimulationContext,
    ) -> tuple[SimulationState, tuple[str, ...]]:
        """The stepping loop shared by the two continuous-time
        categories (§14, §15): each iteration produces a new state via
        the model, advances the clock, and persists via the repository
        swap -- never an in-place mutation."""
        current = run.state
        elapsed = timedelta(0)
        if scenario.time_horizon <= timedelta(0):
            return current, ("time_horizon produced zero steps; state unchanged",)

        if isinstance(model, DiscreteEventModel):
            while elapsed < scenario.time_horizon:
                next_state, delta = model._advance(current, context=context)
                if delta <= timedelta(0):
                    raise SimulationExecutionError(
                        f"DiscreteEventModel {scenario.model_code!r} returned a "
                        f"non-positive delta ({delta!r}); simulated time cannot advance"
                    )
                current = next_state.replace(
                    simulated_time=self._clock.advance(current.simulated_time, delta=delta)
                )
                elapsed += delta
                run = run.with_state(current)
                self._replace(run_id, run)
            return current, ()

        assert isinstance(model, SystemDynamicsModel)
        dt = self._clock.dt
        assert dt is not None  # guaranteed by SimulationClock's FIXED_TIMESTEP guard
        steps = math.ceil(scenario.time_horizon / dt)
        for _ in range(steps):
            next_state = model._step(current, context=context, dt=dt)
            current = next_state.replace(simulated_time=self._clock.advance(current.simulated_time))
            run = run.with_state(current)
            self._replace(run_id, run)
        return current, ()

    def _replace(self, run_id: str, replacement: SimulationRun) -> None:
        """The repository-mediated "current pointer" swap (§10, §32). A
        ``NotFoundError``/``DuplicateError`` here -- after the run was
        already found -- means a concurrent writer raced past the
        repository's per-id serialization contract."""
        try:
            self._repository.remove(run_id)
            self._repository.add(replacement)
        except (NotFoundError, DuplicateError) as exc:
            raise SimulationExecutionError(
                f"Concurrent execute() calls for run {run_id!r} raced past the "
                f"repository's per-id write serialization contract (design spec §32)"
            ) from exc
