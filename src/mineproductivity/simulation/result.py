"""``SimulationResult``: the shared envelope every concrete simulation
outcome composes, and ``ExperimentResult`` built on it (design spec
§18).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseValueObject`` is reused verbatim as the base -- no new
envelope concept is introduced; ``SimulationResult`` mirrors
``digital_twin.TwinResult``'s role (spec 08 §25) one layer up
(``run_id`` substituting for ``twin_id`` as the traceability key).
``SimulationState`` is deliberately **not** a ``SimulationResult``
subclass, for the same reason ``digital_twin.TwinState`` is not a
``TwinResult`` subclass (spec 08 §25): it represents the run's
condition itself, not the outcome of an orchestration call about it.
``ExperimentResult`` is an aggregation only -- the actual
descriptive/inferential treatment of ``trial_results`` is
``analytics``' job (design spec §19-§20), never this type's.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

from mineproductivity.core import BaseValueObject

from mineproductivity.simulation.state import SimulationState

__all__ = ["ExperimentResult", "SimulationResult"]


@dataclasses.dataclass(frozen=True, slots=True)
class SimulationResult(BaseValueObject):
    """The shared envelope every concrete simulation outcome composes
    -- mirrors ``digital_twin.TwinResult``'s role (spec 08 §25), one
    layer up.

    Examples
    --------
    >>> SimulationResult(run_id="RUN-1").run_id
    'RUN-1'
    >>> SimulationResult(warnings=("zero trials requested",)).warnings
    ('zero trials requested',)
    """

    run_id: str = dataclasses.field(default="")
    computed_at: datetime = dataclasses.field(default_factory=lambda: datetime.now(timezone.utc))
    warnings: tuple[str, ...] = dataclasses.field(default=())
    final_state: SimulationState | None = dataclasses.field(default=None, kw_only=True)


@dataclasses.dataclass(frozen=True, slots=True)
class ExperimentResult(SimulationResult):
    """The outcome of one ``Experiment`` -- an aggregation, not a
    statistical characterization; the actual descriptive/inferential
    treatment of ``trial_results`` is ``analytics``' job (design spec
    §19-§20), not this type's.

    Examples
    --------
    >>> result = ExperimentResult(trial_results=(SimulationResult(run_id="RUN-1"),))
    >>> len(result.trial_results)
    1
    """

    trial_results: tuple[SimulationResult, ...] = dataclasses.field(default=(), kw_only=True)
