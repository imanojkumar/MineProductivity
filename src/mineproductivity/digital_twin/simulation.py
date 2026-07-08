"""``TwinSimulationModel``: interface-only extension point (design spec
§14) -- no concrete implementation ships in this package, by explicit
design.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``events.AsOf`` is reused verbatim for the point-in-time/scenario
reference (its ``scenario`` field was reserved by events spec 01
precisely for this scenario/what-if-forking use, and
``decision.WhatIfEngine`` -- spec 07 §19 -- already reuses it the same
way one layer down). No solver, forecasting model, or
optimization/reinforcement-learning algorithm is chosen or shipped:
choosing one is exactly the kind of algorithmic decision this package's
charter excludes (design spec §3.1, §3.5; ADR-0008's most seriously
debated alternative, rejected for the same three compounding reasons
ADR-0006/ADR-0007 recorded for their own interface-only capabilities).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from mineproductivity.events import AsOf

from mineproductivity.digital_twin.abstractions import Twin
from mineproductivity.digital_twin.result import TwinSimulationResult

__all__ = ["TwinSimulationModel"]


class TwinSimulationModel(ABC):
    """The contract a future ``simulation``/``optimization``/``agents``
    plugin implements to answer 'what would this twin look like under a
    hypothetical change.' THIS MODULE SHIPS NO CONCRETE SUBCLASS
    (design spec §14, §32's interface-purity proof).

    This interface is the digital-twin-layer counterpart of
    ``decision.WhatIfEngine`` (spec 07 §19), which was itself already
    designed with ``digital_twin`` named as its most direct anticipated
    implementer. A future concrete ``decision.WhatIfEngine``
    implementation is expected to be provided BY a
    ``digital_twin``-aware plugin that internally calls a concrete
    ``TwinSimulationModel`` and translates its ``TwinSimulationResult``
    into a ``decision.WhatIfResult`` -- this package defines the
    twin-state-level half of that bridge; spec 07 already defined the
    business-decision-level half. ``TwinSimulationModel`` operates on
    ``Twin``/``TwinState`` directly (a physical/operational-state
    question), while ``decision.WhatIfEngine`` operates on
    ``DecisionContext`` (a business-evidence question) -- related,
    potentially composed together, never collapsed into one interface
    (design spec §14).
    """

    @abstractmethod
    def _simulate(
        self, twin: Twin, hypothesis: Mapping[str, Any], *, as_of: AsOf
    ) -> TwinSimulationResult:
        """Pure contract: one ``Twin`` (current or snapshot-forked), a
        hypothesis (the attribute changes to explore), and the
        ``AsOf`` framing the scenario -> a predicted ``TwinState``
        wrapped in a ``TwinSimulationResult``. No default
        implementation exists or is intended here (design spec §14)."""
