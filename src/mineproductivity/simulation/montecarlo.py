"""``MonteCarloModel``: interface-only extension point (design spec
§13) -- no concrete implementation ships in this package, by explicit
design (ADR-0009's most seriously debated alternative, rejected for
the same three compounding reasons ADR-0006/0007/0008 recorded for
their own interface-only capabilities).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
No random-sampling methodology, trial-count heuristic, or
variance-reduction technique is chosen or shipped: choosing one is
exactly the kind of modeling decision this package's charter excludes
(design spec §3.1, §3.5). The ``random_seed`` parameter is the
concurrency contract's anchor (§33): each trial receives a distinct
seed from ``ExperimentRunner`` and the model itself is stateless, so
concurrent trials are reproducible independent of execution order.
The ``"MONTECARLO"`` code namespace follows design spec §29's own
example (``"MONTECARLO.HaulCycleVariability"``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from mineproductivity.simulation.abstractions import (
    SimulationContext,
    SimulationModel,
    _enforce_category,
)
from mineproductivity.simulation.metadata import SimulationCategory
from mineproductivity.simulation.result import SimulationResult
from mineproductivity.simulation.scenario import Scenario

__all__ = ["MonteCarloModel"]


class MonteCarloModel(SimulationModel, ABC):
    """The contract a future Monte Carlo plugin implements. THIS MODULE
    SHIPS NO CONCRETE SUBCLASS (design spec §13, §35's interface-purity
    proof).

    Each call to :meth:`_trial` is expected to be independent and
    reproducible given the same ``random_seed`` --
    ``ExperimentRunner`` (design spec §17) supplies a distinct seed per
    trial; the concrete model never manages its own seed state
    internally (§29's statelessness rule, §34's recorded anti-pattern).
    """

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "MONTECARLO", SimulationCategory.MONTE_CARLO)

    @abstractmethod
    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        """One independent trial of ``scenario``, all randomness derived
        solely from ``random_seed`` -- no default implementation exists
        or is intended here (design spec §13)."""
