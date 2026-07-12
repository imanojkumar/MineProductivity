"""``Experiment``/``ExperimentRunner``: experiment management (design
spec §17).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``ExperimentRunner`` composes ``SimulationExecutor`` for each
individual run rather than duplicating its dispatch/persistence logic
(design spec §17). Trial concurrency uses the standard library's
``ThreadPoolExecutor`` -- independent runs (distinct ``id``\\ s) never
contend on a repository key (§33), which is what makes a 500-trial
Monte Carlo experiment practical; per-trial reproducibility is
anchored by supplying each trial its own distinct ``random_seed``
(§13, §33), the responsibility §13 places on this class, never on the
concrete model. Run ids embed the scenario code, the trial index, and
a uniquifying suffix so run order is recoverable and re-running the
same experiment never collides with an earlier run's ids.
"""

from __future__ import annotations

import dataclasses
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from mineproductivity.core import BaseValueObject

from mineproductivity.simulation.abstractions import SimulationContext
from mineproductivity.simulation.executor import SimulationExecutor
from mineproductivity.simulation.persistence import SimulationRunRepository
from mineproductivity.simulation.run import SimulationRun
from mineproductivity.simulation.scenario import Scenario
from mineproductivity.simulation.state import SimulationState

__all__ = ["Experiment", "ExperimentRunner"]


@dataclasses.dataclass(frozen=True, slots=True)
class Experiment(BaseValueObject):
    """A named collection of ``SimulationRun``\\ s produced from one
    ``Scenario`` -- many independent Monte Carlo trials, or one run per
    point in a sensitivity sweep (design spec §17, §20).

    Examples
    --------
    >>> from datetime import timedelta
    >>> scenario = Scenario(
    ...     code="FLEET.NightShiftSurge", model_code="MONTECARLO.HaulCycleVariability",
    ...     time_horizon=timedelta(hours=12),
    ... )
    >>> Experiment(name="surge-x2", scenario=scenario, run_ids=("RUN-1", "RUN-2")).run_ids
    ('RUN-1', 'RUN-2')
    """

    name: str
    scenario: Scenario
    run_ids: tuple[str, ...]


class ExperimentRunner:
    """Runs a ``Scenario`` across many trials (Monte Carlo, design spec
    §13) or many parameter values (a sensitivity sweep, §20),
    collecting the resulting runs into one ``Experiment``. Trials are
    dispatched concurrently in this reference implementation (§33);
    ``run_ids`` preserve trial order regardless of completion order.
    Zero trials is a legitimately incomplete input (§28): an empty
    ``Experiment`` is returned, never a raise.
    """

    def __init__(
        self, *, executor: SimulationExecutor, repository: SimulationRunRepository
    ) -> None:
        self._executor = executor
        self._repository = repository

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(executor={self._executor!r}, repository={self._repository!r})"
        )

    def run_trials(
        self, scenario: Scenario, *, trials: int, context: SimulationContext
    ) -> Experiment:
        """Provision and execute ``trials`` independent runs of
        ``scenario``, each with its own distinct ``random_seed`` (the
        trial index -- §13's reproducibility anchor), returning the
        ``Experiment`` naming them in trial order."""
        name = f"{scenario.code}@{scenario.version}"
        if trials <= 0:
            return Experiment(name=name, scenario=scenario, run_ids=())

        suffix = uuid.uuid4().hex[:8]
        run_ids = tuple(f"{scenario.code}::trial-{index:04d}-{suffix}" for index in range(trials))
        provisioned_at = (
            scenario.as_of.utc
            if scenario.as_of is not None and scenario.as_of.utc is not None
            else datetime.now(timezone.utc)
        )
        for run_id in run_ids:
            self._repository.add(
                SimulationRun(
                    id=run_id,
                    scenario_code=scenario.code,
                    state=SimulationState(
                        attributes={"provisioned": True}, simulated_time=provisioned_at
                    ),
                )
            )

        def _one_trial(indexed: tuple[int, str]) -> None:
            index, run_id = indexed
            self._executor.execute(run_id, scenario, context=context, random_seed=index)

        with ThreadPoolExecutor() as pool:
            list(pool.map(_one_trial, enumerate(run_ids)))

        return Experiment(name=name, scenario=scenario, run_ids=run_ids)
