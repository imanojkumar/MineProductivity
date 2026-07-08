"""What-if interfaces (design spec §19) -- interface only.

``WhatIfEngine`` is the contract a future what-if/scenario-simulation
plugin implements. This module ships no concrete subclass: predicting
the outcome of a hypothetical change is a simulation/forecasting
problem, out of scope for this package (§3.4, §4) -- the same reasoning
``root_cause.py`` already applies to ``RootCauseAnalyzer`` one section
earlier (§18), and the same reasoning ``analytics.forecasting`` applies
to ``ForecastingModel`` one layer down (ADR-0006).

This interface deliberately reuses ``events.AsOf``'s ``scenario`` field
-- already reserved by the Event Framework specification "so a future
scenario/what-if-forking capability (Digital Twin) can extend this
type's usage without a breaking change" (events spec 01) -- rather than
inventing a second scenario concept. No new value type is introduced
either: ``WhatIfResult`` already exists in ``result.py`` (Phase 07.1,
ahead of schedule for the same reason ``RootCauseResult`` was).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from mineproductivity.events import AsOf

from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.result import WhatIfResult

__all__ = ["WhatIfEngine"]


class WhatIfEngine(DecisionModel, ABC):
    """The contract a future what-if/scenario-simulation plugin
    implements. THIS MODULE SHIPS NO CONCRETE SUBCLASS -- predicting the
    outcome of a hypothetical change is a simulation/forecasting problem
    this package's charter (§3.4) excludes.

    Leaves :meth:`~mineproductivity.decision.abstractions.DecisionModel._decide`
    abstract (inherited, unoverridden) exactly as ``RootCauseAnalyzer``
    does -- only a concrete subclass decides how its own ``_decide``
    relates to ``_simulate``, since no concrete subclass ships here to
    make that decision on a future plugin's behalf.
    """

    @abstractmethod
    def _simulate(
        self, context: DecisionContext, hypothesis: Mapping[str, Any], *, as_of: AsOf
    ) -> WhatIfResult:
        """Predict the outcome of ``hypothesis`` (an arbitrary,
        implementation-defined mapping of proposed changes) evaluated
        against ``context``, framed by ``as_of`` -- typically an
        ``AsOf(scenario=...)`` naming the hypothetical branch, per this
        module's own reuse of ``events.AsOf``. Returns a
        :class:`~mineproductivity.decision.result.WhatIfResult`
        (``hypothesis``, ``predicted_outcome``, ``confidence``)."""
